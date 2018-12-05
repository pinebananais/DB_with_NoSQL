import redis
from sql_ast import *
import sql_parser

class RedisConnector:
	def __init__(self):
		self.parser = sql_parser.Parser()
		self.connector = redis.Redis(host='localhost', port=6379, db=0) # redis connector

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
			self.connector.hmset(stmt.table_name+":metadata", stmt.table_informations) # in redis, HMSET key field value [field value ...]
			output = self.connector.scan(match="*:metadata")
			print(output[1])
		elif type(stmt) is ShowStmt:
			output = self.connector.scan(match="*:metadata")
			print(output[1])
		elif type(stmt) is InsertStmt:
			self.connector.rpush(stmt.table_name, *stmt.values) # in redis, RPUSH key value [value ...]
			col_nr = self.connector.hlen(stmt.table_name+":metadata")
			cell_nr = self.connector.llen(stmt.table_name)
			print("INSERT SUCCESS: TABLE {0} has {1} rows.".format(stmt.table_name, cell_nr//col_nr))
		elif type(stmt) is SelectStmt:
			if stmt.table_attributes == "*":
				col_nr = self.connector.hlen(stmt.table_name+":metadata")
				cell_nr = self.connector.llen(stmt.table_name)
				print(col_nr, cell_nr)
				for i in range(cell_nr//col_nr):
					output = self.connector.lrange(stmt.table_name, col_nr*i, col_nr*(i+1)-1) # in redis, LRANGE key start stop
					print(output)
		elif type(stmt) is UpdateStmt:
			print("update complete")
		elif type(stmt) is DeleteStmt:
			delete_key = [stmt.table_name, stmt.table_name+":metadata"] 
			self.connector.delete(*delete_key) # in redis, DEL key
			print("delete complete")
		else:
			raise ValueError("SyntaxError, invalid stmt is entered")