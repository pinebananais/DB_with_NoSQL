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
		self.connector.hmset(stmt.getMetaTableName(), stmt.getTableinfo()) # in redis, HMSET key field value [field value ...]
		self.printTableList()

	def insertCommand(self, stmt):
		col_nr = self.connector.hlen(stmt.getMetaTableName())
		if col_nr == 0:
			raise ValueError("SemanticError, Can not insert into nonexistent table")

		literal_nr = len(stmt.literals)
		if col_nr != literal_nr:
			raise ValueError("SemanticError, the number of literals and attributes doesn't match")

		data_types = self.connector.hvals(stmt.getMetaTableName())
		for i in range(len(data_types)):
			if stmt.literals[i].data_type.getToStr() != data_types[i].decode():
				raise ValueError("SemanticError, the type of literal and attribute doesn't match in index {0}".format(i))

		self.connector.rpush(stmt.getTableName(), *stmt.getLiterals())
		cell_nr = self.connector.llen(stmt.getTableName())
		print("INSERT SUCCESS: TABLE {0} has {1} rows.".format(stmt.getTableName(), cell_nr//col_nr))

	def selectCommand(self, stmt):
		if stmt.table_attributes == "*":
			col_nr = self.connector.hlen(stmt.getMetaTableName())
			if col_nr == 0:
				raise ValueError("SemanticError, Can not select from nonexistent table")
			cell_nr = self.connector.llen(stmt.getTableName())

			print("=================")
			attributes = self.connector.hkeys(stmt.getMetaTableName())
			for attribute in attributes:
				print(attribute.decode()+"|", end="")
			print()
			print("=================")
			for i in range(cell_nr//col_nr):
				record = self.connector.lrange(stmt.getTableName(), col_nr*i, col_nr*(i+1)-1) # in redis, LRANGE key start stop
				for element in record:
					print(element.decode()+"|", end="")
				print()
			print("=================")
		else:
			print("SystemError, your query is perfect but we only support 'select * from <table_name>' now.")

	def updateCommand(self, stmt):
		print("SystemError, your query is perfect but we doesn't Support UPDATE query yet.")

	def deleteCommand(self, stmt):
		delete_key = [stmt.getMetaTableName(), stmt.getTableName()] 
		self.connector.delete(*delete_key) # in redis, DEL key
		print("DELETE SUCCESS: TABLE {0} has been deleted.".format(stmt.getTableName()))

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