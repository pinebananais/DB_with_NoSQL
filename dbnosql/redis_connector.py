import redis
from sql_ast import *
from collections import OrderedDict
import sql_parser

class RedisConnector:
	def __init__(self):
		self.parser = sql_parser.Parser()
		self.connector = redis.Redis(host='localhost', port=6379, db=0) # redis connector

	def showCommand(self):
		self.printTableList()

	def createCommand(self, stmt):
		meta_table_name = stmt.getMetaTableName()
		table_info = stmt.getTableinfo()
		
		# modified by YIS 12-11
		table_col = self.connector.hlen(meta_table_name)
		if table_col != 0:
			raise ValueError("SemanticError, Cannot create already exist table")
		# end

		self.connector.hmset(meta_table_name, table_info) # in redis, HMSET key field value [field value ...]
		
		self.printTableList()

	def insertCommand(self, stmt):
		meta_table_name = stmt.getMetaTableName()
		table_name = stmt.getTableName()

		table_col = self.connector.hlen(meta_table_name)
		if table_col == 0:
			raise ValueError("SemanticError, Cannot insert into non-existent table")

		stmt_col = len(stmt.getLiterals())
		if table_col != stmt_col:
			raise ValueError("SemanticError, the number of literals and table attributes doesn't match")

		table_types = self.connector.hvals(meta_table_name)
		table_types = [i.decode() for i in table_types]
		stmt_types = stmt.getLiteralTypes()
		if table_types != [i for i,j in zip(table_types, stmt_types) if i == j]:
			raise ValueError("SemanticError, the type of literal and attribute doesn't match")

		self.connector.rpush(table_name, *stmt.getLiterals())
		table_cell = self.connector.llen(table_name)

		print("INSERT SUCCESS: TABLE {0} has {1} rows.".format(table_name, table_cell//table_col))

	def selectCommand(self, stmt):
		meta_table_name = stmt.getMetaTableName()
		table_name = stmt.getTableName()

		table_col = self.connector.hlen(meta_table_name)
		if table_col == 0:
			raise ValueError("SemanticError, Cannot select from non-existent table")
		table_cell = self.connector.llen(table_name)

		table_attrs = self.connector.hkeys(meta_table_name)
		table_attrs = [i.decode() for i in table_attrs]

		stmt_attrs = stmt.getAttributes()
		print(stmt_attrs)
		is_agg_attr = False
		if stmt_attrs == "*":
			stmt_attrs = table_attrs
		elif stmt_attrs[0] == "SUM" or stmt_attrs[0] == "COUNT":
			agg_function = stmt_attrs[0]
			target_attr = stmt_attrs[1].getToStr()
			is_agg_attr = True
		if is_agg_attr == False and [i for i in stmt_attrs if i not in table_attrs]:
			raise ValueError("SemanticError, Cannot select non-existent attribute")
		
		# modified by YIS 12-11
		# modified by HJY 12-16
		# WHERE
		table_row = [i for i in range(table_cell // table_col)]
		if stmt.clauses:
			print(stmt.clauses.getToList())
			table_row = self.connector.execute_command('mylrange', meta_table_name, table_name, *stmt.clauses.getToList())

		# GROUP BY
		group = stmt.getGroupName()
		group_dict = dict()
		if group:
			group_idx = table_attrs.index(group)
			for i in table_row:
				group_element = self.connector.lindex(table_name, table_col*i+group_idx)
				group_element = group_element.decode()
				if not group_element in group_dict:
					group_dict[group_element] = list()
				group_dict[group_element].append(i)
		else:
			group_dict["_ALL_"] = table_row

		print(group_dict)

		# having = stmt.getHavingClause()
		# if having:
		# 	having_agg_function = having.aggregation[0]
		# 	having_target_attr = having.aggregation[1].getToStr()
			
		# 	sub_result = dict()

		# 	for group_row in group_dict.values():
		# 		sub_result = 0
		# 		j = table_attrs.index(having_target_attr)
		# 		for i in group_row:
		# 			if having_agg_function == "SUM":
		# 				sub_result


		# # HAVING
		# having_clause = stmt.having_clause
		# if having_clause:
		# 	having_agg_function = having_clause.aggregation[0]
		# 	having_target_attr = having_clause.aggregation[1]
		# 	having_idx = table_attrs.index(having_target_attr)
		# 	for element in group_elements:
		# 		for i in table_row:
		# 			if element == self.connector.lindex(table_name, table_col*i+group_idx):

		print(table_row)

		if is_agg_attr:
			print("=================", end = "")
			print()
			# attribute
			attr = agg_function + "(" + target_attr + ")"
			print("%15s" % (attr), end = " |")
			print()
			print("=================", end = "")
			print()
			# record
			for group_row in group_dict.values():
				my_result = 0
				for i in group_row:
					j = table_attrs.index(target_attr)
					element = self.connector.lindex(table_name, table_col*i+j)
					element = element.decode()
					if agg_function == "SUM":
						my_result += int(element)
					elif agg_function == "COUNT":
						my_result += 1
					else:
						print("What the fuckkkkkkkkkk")
				print("%15d" % (my_result), end = " |")
				print()
			print("=================", end = "")
			print()
		else:
			for i in stmt_attrs : print("=================", end = "")
			print()
			# attribute
			for attr in [i for i in stmt_attrs if i in table_attrs]:
				print("%15s" % (attr), end = " |")
			print()
			for i in stmt_attrs : print("=================", end = "")
			print()
			# record
			for i in table_row:
				for j in [table_attrs.index(i) for i in stmt_attrs if i in table_attrs]:
					element = self.connector.lindex(table_name, table_col*i+j)
					element = element.decode()
					print("%15s" % (element), end = " |")
				print()
			for i in stmt_attrs : print("=================", end = "")
			print()

	def updateCommand(self, stmt):
		meta_table_name = stmt.getMetaTableName()
		table_name = stmt.getTableName()

		table_col = self.connector.hlen(meta_table_name)
		if table_col == 0:
			raise ValueError("SemanticError, Cannot select from non-existent table")
		table_cell = self.connector.llen(table_name)

		table_attrs = self.connector.hkeys(meta_table_name)
		table_attrs = [i.decode() for i in table_attrs]

		stmt_attr = stmt.getAttribute()
		stmt_literal = stmt.getLiteral()

		table_row = [i for i in range(table_cell // table_col)]
		if stmt.clauses:
			print(stmt.clauses.getToList())
			table_row = self.connector.execute_command('mylrange', meta_table_name, table_name, *stmt.clauses.getToList())

		for i in table_row:
			j = table_attrs.index(stmt_attr)
			self.connector.lset(table_name, table_col*i+j, stmt_literal)

		print("UPDATE SUCCESS: TABLE {0} record".format(table_name), end=" ")
		for i in table_row:
			print(i, end=" ")
		print("has been updated.")

	def deleteCommand(self, stmt):
		meta_table_name = stmt.getMetaTableName()
		table_name = stmt.getTableName()

		table_col = self.connector.hlen(meta_table_name)
		if table_col == 0:
			raise ValueError("SemanticError, Cannot select from non-existent table")
		table_cell = self.connector.llen(table_name)

		table_attrs = self.connector.hkeys(meta_table_name)
		table_attrs = [i.decode() for i in table_attrs]

		table_row = [i for i in range(table_cell // table_col)]
		if stmt.clauses:
			print(stmt.clauses.getToList())
			table_row = self.connector.execute_command('mylrange', meta_table_name, table_name, *stmt.clauses.getToList())

		for i in table_row:
			for j in [table_attrs.index(i) for i in table_attrs]:
				self.connector.lset(table_name, table_col*i+j, "_TBD_")

		self.connector.lrem(table_name, 0, "_TBD_")

		print("DELETE SUCCESS: TABLE {0} record".format(table_name), end=" ")
		for i in table_row:
			print(i, end=" ")
		print("has been deleted.")

	def dropCommand(self, stmt):
		meta_table_name = stmt.getMetaTableName()
		table_name = stmt.getTableName()

		table_col = self.connector.hlen(meta_table_name)
		if table_col == 0:
			raise ValueError("SemanticError, Cannot drop non-existent table")
		delete_key = [meta_table_name, table_name] 
		self.connector.delete(*delete_key) # in redis, DEL key

		print("DROP SUCCESS: TABLE {0} has been deleted.".format(table_name))

	def printTableList(self):
		output = self.connector.scan(match="*:metadata")
		tables = output[1]

		print("=================")
		print("Table list")
		print("=================")
		for table in tables:
			print(table.split(b':')[0].decode())
		print("=================")

	####################################################
	# in redis, I defined KEY string format as shown below
	# KEY of the container including table records = table_name
	# KEY of the container including table metadatas = table_name:metadata
	####################################################
	# for example, if we define table "student" in redis,
	# KEY "student" -> list container including records
	# KEY "stduent:metadata" -> hash container including table metadatas such as field:value = name:VARCHAR, age:INT
	####################################################
	def connect(self, source):
		stmt = self.parser.parse(source)

		if type(stmt) is CreateStmt:
			self.createCommand(stmt)
		elif type(stmt) is ShowStmt:
			self.showCommand()
		elif type(stmt) is InsertStmt:
			self.insertCommand(stmt)
		elif type(stmt) is SelectStmt:
			self.selectCommand(stmt)
		elif type(stmt) is UpdateStmt:
			self.updateCommand(stmt)
		elif type(stmt) is DeleteStmt:
			self.deleteCommand(stmt)
		elif type(stmt) is DropStmt:
			self.dropCommand(stmt)
		else:
			raise ValueError("SyntaxError, invalid stmt is entered")
