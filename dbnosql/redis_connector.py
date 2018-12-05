import redis
from sql_ast import *
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
		if stmt_attrs == "*":
			stmt_attrs = table_attrs

		if [i for i in stmt_attrs if i not in table_attrs]:
			raise ValueError("SemanticError, Cannot select non-existent attribute")

		print("=================")
		for attr in [i for i in stmt_attrs if i in table_attrs]:
			print(attr, end="|")
		print()
		print("=================")
		for i in range(table_cell//table_col):
			for j in [table_attrs.index(i) for i in stmt_attrs if i in table_attrs]:
				element = self.connector.lindex(table_name, table_col*i+j)
				element = element.decode()
				print(element, end="|")
			print()
		print("=================")

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

		for i in range(table_cell//table_col):
			j = table_attrs.index(stmt_attr)
			self.connector.lset(table_name, table_col*i+j, stmt_literal)

		print("UPDATE SUCCESS: TABLE {0} has been updated.".format(table_name))

	def deleteCommand(self, stmt):
		meta_table_name = stmt.getMetaTableName()
		table_name = stmt.getTableName()

		delete_key = [meta_table_name, table_name] 
		self.connector.delete(*delete_key) # in redis, DEL key

		print("DELETE SUCCESS: TABLE {0} has been deleted.".format(table_name))

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
		else:
			raise ValueError("SyntaxError, invalid stmt is entered")