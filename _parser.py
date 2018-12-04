import redis
import my_token
import _scanner

## written by JYH
class CreateStmt:
	def __init__(self, table_name, table_informations):
		self.table_name = table_name
		self.table_informations = table_informations

class InsertStmt:
	def __init__(self, table_name, values):
		self.table_name = table_name
		self.values = values

class SelectStmt:
	def __init__(self, table_attributes, table_name, conditions):
		self.table_attributes = table_attributes
		self.table_name = table_name
		self.conditions = conditions

class DeleteStmt:
	def __init__(self, table_name, conditions):
		self.table_name = table_name
		self.values = conditions

class UpdateStmt:
	def __init__(self, table_name, table_attribute, value, conditions):
		self.table_name = table_name
		self.table_attribute = table_attribute
		self.value = value
		self.conditions = conditions

class Conditions:
	def __init__(self):
		self.parent = None

	def __init__(self, operator, parent, left, right): # binary tree structure
		self.operator = operator
		self.parent = parent
		self.left = left
		self.right = right

class Condition:
	def __init__(self, table_attribute, operator, value):
		self.table_attribute = table_attribute
		self.operator = operator
		self.value = value

## modified by JYH
class parser:
	def __init__(self):
		self.Scanner = _scanner.scanner()
		self.my_redis = redis.Redis(host='localhost', port=6379, db=0) # redis connector
		return

	def acceptIt(self): # alway accept my_token
		self.current_token = self.Scanner.get_next_token()

	def accept(self, expected_token_kind):
		if self.current_token.kind == expected_token_kind:
			self.current_token = self.Scanner.get_next_token()
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format(my_token.token_list[expected_token_kind], self.current_token.content))

	####################################################
	# in redis, I defined KEY string format as shown below
	# KEY of the container including table records = table_name
	# KEY of the container including table metadatas = table_name:metadata
	####################################################
	# for example, if we define table "student" in redis,
	# KEY "student" -> list container including records
	# KEY "stduent:metadata" -> hash container including table metadatas such as field:value = name:VARCHAR, age:INT
	####################################################
	def parse(self, source):
		self.Scanner.set_source(source)
		self.current_token = self.Scanner.get_next_token()
		if self.current_token.kind == my_token.CREATE:
			result = self.parseCreatestmt()
			self.my_redis.hmset(result.table_name+":metadata", result.table_informations) # in redis, HMSET key field value [field value ...]
			print("create complete")
		elif self.current_token.kind == my_token.SHOW:
			self.parseShowstmt()
			# there must be some redis commands...
		elif self.current_token.kind == my_token.INSERT:
			result = self.parseInsertstmt()
			self.my_redis.rpush(result.table_name, *result.values) # in redis, RPUSH key value [value ...]
			print("insert complete")
		elif self.current_token.kind == my_token.SELECT:
			result = self.parseSelectstmt()

			if result.table_attributes == "*":
				col_nr = self.my_redis.hlen(result.table_name+":metadata")
				cell_nr = self.my_redis.llen(result.table_name)
				for i in range(cell_nr//col_nr):
					output = self.my_redis.lrange(result.table_name, col_nr*i, col_nr*(i+1)-1) # in redis, LRANGE key start stop
					print(output)

			print("select complete")
			# there must be some redis commands...
		elif self.current_token.kind == my_token.UPDATE:
			result = self.parseUpdatestmt()
			# there must be some redis commands...
		elif self.current_token.kind == my_token.DELETE:
			result = self.parseDeletestmt()
			self.my_redis.delete(*result.table_name) # in redis, DEL key
			print("delete complete")
			# there must be some redis commands...
		else:
			raise ValueError("SyntaxError, invalid keyword token \"{}\" is entered".format(self.current_token.content))


	# create-stmt := CREATE TABLE identifier "(" vardecls ")" ";"
	def parseCreatestmt(self):
		self.accept(my_token.CREATE)
		self.accept(my_token.TABLE)
		table_name = self.parseIdentifier()
		self.accept(my_token.LEFTPAREN)
		table_informations = self.parseVardecls()
		self.accept(my_token.RIGHTPAREN)
		self.accept(my_token.SEMICOLON)

		return CreateStmt(table_name, table_informations)

	# show-stmt := SHOW TABLES ";"
	def parseShowstmt(self):
		self.accept(my_token.SHOW)
		self.accept(my_token.TABLES) # my_token.TABLES doesn't exist
		self.accept(my_token.SEMICOLON)

	# insert-stmt := INSERT INTO identifier VALUES "(" values ")" ";"
	def parseInsertstmt(self):
		self.accept(my_token.INSERT)
		self.accept(my_token.INTO) # my_token.INTO doesn't exist
		table_name = self.parseIdentifier()
		self.accept(my_token.VALUES) # my_token.INTO doesn't exist
		self.accept(my_token.LEFTPAREN)
		values = self.parseValues()
		self.accept(my_token.RIGHTPAREN)
		self.accept(my_token.SEMICOLON)

		return InsertStmt(table_name, values)

	# select-stmt := SELECT ( "*" | identifiers ) FROM identifier ( Where conditions )? ";"
	def parseSelectstmt(self):
		self.accept(my_token.SELECT)
		if self.current_token.kind == my_token.ASTER:
			table_attributes = self.current_token.content
			self.acceptIt()
		else:
			table_attributes = self.parseIdentifiers()
		self.accept(my_token.FROM)
		table_name = self.parseIdentifier()
		conditions = []
		if self.current_token.kind == my_token.WHERE:
			self.acceptIt()
			conditions = self.parseConditions()
		self.accept(my_token.SEMICOLON)

		return SelectStmt(table_attributes, table_name, conditions)

	# update-stmt := UPDATE identifier SET identifier "=" value ( WHERE conditions )? ";"
	def parseUpdatestmt(self):
		self.accept(my_token.UPDATE)
		table_name = self.parseIdentifiers()
		self.accept(my_token.SET) # my_token.SEt doen't exist
		table_attribute = self.parseIdentifiers()
		self.accept(my_token.EQ) # ASSIGN?, EQ?
		value = self.parseValue()
		conditions = []
		if self.current_token.kind == my_token.WHERE:
			self.acceptIt()
			conditions = self.parseConditions()
		self.accept(my_token.SEMICOLON)

		return UpdateStmt(table_name, table_attribute, value, conditions)

	# delete-stmt := DELETE FROM identifier ( WHERE conditions )? ";"
	def parseDeletestmt(self):
		self.accept(my_token.DELETE)
		self.accept(my_token.FROM)
		table_name = self.parseIdentifiers()
		conditions = []
		if self.current_token.kind == my_token.WHERE:
			self.acceptIt()
			conditions = self.parseConditions()
		self.accept(my_token.SEMICOLON)

		return DeleteStmt(table_name, conditions)

	# conditions := condition ( ("and"|"or") condition )*
	def parseConditions(self):
		conditions = Conditions()
		r_condition = parseCondition(conditions)
		conditions.right = r_condition
		while self.current_token.kind == my_token.AND or self.current_token.kind == my_token.OR:
			conditions.operator = self.current_token.content
			self.acceptIt()
			l_condition = parseCondition(conditions)
			conditions.left = l_condition

		return conditions

	# condition := identifier filter value | "(" conditions ")"
	def parseCondition(self, parent_conditions):
		if self.current_token.kind == my_token.ID:
			table_attribute = parseIdentifier()
			operator = parseOperator()
			value = parseValue()

			return Condition(table_attribute, operator, value)
		elif self.current_token.kind == my_token.LEFTPAREN:
			self.acceptIt()
			conditions = parseConditions()
			conditions.parent = parent_conditions
			self.accept(my_token.RIGHTPAREN)

			return conditions

	# vardecls := vardecl ( "," vardecl )*
	def parseVardecls(self):
		var_decls = {}
		var_decl = self.parseVardecl()
		var_decls[var_decl[0]] = var_decl[1]
		while self.current_token.kind == my_token.COMMA:
			self.acceptIt()
			var_decl = self.parseVardecl()
			var_decls[var_decl[0]] = var_decl[1]

		return var_decls

	# vardecl := identifier data-type
	def parseVardecl(self):
		identifier = self.parseIdentifier()
		data_type = self.parseDatatype()

		return (identifier, data_type)

	# values := value ( "," value )*
	def parseValues(self):
		values = []
		value = self.parseValue()
		values.append(value)
		while self.current_token.kind == my_token.COMMA:
			self.acceptIt()
			value = self.parseValue()
			values.append(value)
		return values

	# value := INTLITERAL | STRINGLITERAL
	def parseValue(self):
		if self.current_token.kind == my_token.INTLITERAL or self.current_token.kind == my_token.STRINGLITERAL:
			value = self.current_token.content
			self.acceptIt()

			return value
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("INTLITERAL or STRINGLITERAL", self.current_token.content))

	# identifiers := identifier ( "," identifier )*
	def parseIdentifiers(self):
		identifiers = []
		identifier = self.parseIdentifier()
		identifiers.append(identifier)
		while self.current_token.kind == my_token.COMMA:
			self.acceptIt()
			identifier = self.parseIdentifier()
			identifiers.append(identifier)

		return identifiers

	# identifier :=  alphabet ( alphabet | digit )*
	def parseIdentifier(self):
		if self.current_token.kind == my_token.ID:
			identifier = self.current_token.content
			self.acceptIt()

			return identifier
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("ID", self.current_token.content))

	# data-type := INT | VARCHAR
	def parseDatatype(self):
		if self.current_token.kind == my_token.VARCHAR or self.current_token.kind == my_token.INT:
			data_type = self.current_token.content
			self.acceptIt()

			return data_type
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("INT or VARCHAR", self.current_token.content))

	# operator := ">"|"="|"<"|">="|"!="|"<="
	# my_token.NOTEQ is "<>" or "!=" ?
	def parseOperator(self):
		if self.current_token.kind == my_token.GREATER or \
		self.current_token.kind == my_token.EQ or \
		self.current_token.kind == my_token.LESS or \
		self.current_token.kind == my_token.GREATEREQ or \
		self.current_token.kind == my_token.NOTEQ or \
		self.current_token.kind == my_token.LESSEQ:
			operator = self.current_token.content
			self.acceptIt()

			return operator
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("operator", self.current_token.content))


