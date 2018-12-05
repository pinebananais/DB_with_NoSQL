import redis
from sql_ast import *
import sql_token
import sql_scanner

## modified by JYH
class Parser:
	def __init__(self):
		self.Scanner = sql_scanner.scanner()
		# self.my_redis = redis.Redis(host='localhost', port=6379, db=0) # redis connector
		return

	def acceptIt(self): # alway accept token
		self.current_token = self.Scanner.get_next_token()

	def accept(self, expected_token_kind):
		if self.current_token.kind == expected_token_kind:
			self.current_token = self.Scanner.get_next_token()
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format(sql_token.token_list[expected_token_kind], self.current_token.content))

	def parse(self, source):
		self.Scanner.set_source(source)
		self.current_token = self.Scanner.get_next_token()
		result = None
		if self.current_token.kind == sql_token.CREATE:
			result = self.parseCreatestmt()
		elif self.current_token.kind == sql_token.SHOW:
			result = self.parseShowstmt()
		elif self.current_token.kind == sql_token.INSERT:
			result = self.parseInsertstmt()
		elif self.current_token.kind == sql_token.SELECT:
			result = self.parseSelectstmt()
		elif self.current_token.kind == sql_token.UPDATE:
			result = self.parseUpdatestmt()
		elif self.current_token.kind == sql_token.DELETE:
			result = self.parseDeletestmt()
		else:
			raise ValueError("SyntaxError, invalid keyword token \"{}\" is entered".format(self.current_token.content))

		return result

	# create-stmt := CREATE TABLE identifier "(" vardecls ")" ";"
	def parseCreatestmt(self):
		self.accept(sql_token.CREATE)
		self.accept(sql_token.TABLE)
		table_name = self.parseIdentifier()
		self.accept(sql_token.LEFTPAREN)
		table_informations = self.parseVardecls()
		self.accept(sql_token.RIGHTPAREN)
		self.accept(sql_token.SEMICOLON)

		return CreateStmt(table_name, table_informations)

	# show-stmt := SHOW TABLES ";"
	def parseShowstmt(self):
		self.accept(sql_token.SHOW)
		self.accept(sql_token.TABLES) # sql_token.TABLES doesn't exist
		self.accept(sql_token.SEMICOLON)

		return ShowStmt()

	# insert-stmt := INSERT INTO identifier VALUES "(" values ")" ";"
	def parseInsertstmt(self):
		self.accept(sql_token.INSERT)
		self.accept(sql_token.INTO) # sql_token.INTO doesn't exist
		table_name = self.parseIdentifier()
		self.accept(sql_token.VALUES) # sql_token.INTO doesn't exist
		self.accept(sql_token.LEFTPAREN)
		values = self.parseValues()
		self.accept(sql_token.RIGHTPAREN)
		self.accept(sql_token.SEMICOLON)

		return InsertStmt(table_name, values)

	# select-stmt := SELECT ( "*" | identifiers ) FROM identifier ( Where conditions )? ";"
	def parseSelectstmt(self):
		self.accept(sql_token.SELECT)
		if self.current_token.kind == sql_token.ASTER:
			table_attributes = self.current_token.content
			self.acceptIt()
		else:
			table_attributes = self.parseIdentifiers()
		self.accept(sql_token.FROM)
		table_name = self.parseIdentifier()
		conditions = []
		if self.current_token.kind == sql_token.WHERE:
			self.acceptIt()
			conditions = self.parseConditions()
		self.accept(sql_token.SEMICOLON)

		return SelectStmt(table_attributes, table_name, conditions)

	# update-stmt := UPDATE identifier SET identifier "=" value ( WHERE conditions )? ";"
	def parseUpdatestmt(self):
		self.accept(sql_token.UPDATE)
		table_name = self.parseIdentifiers()
		self.accept(sql_token.SET) # sql_token.SEt doen't exist
		table_attribute = self.parseIdentifiers()
		self.accept(sql_token.EQ) # ASSIGN?, EQ?
		value = self.parseValue()
		conditions = []
		if self.current_token.kind == sql_token.WHERE:
			self.acceptIt()
			conditions = self.parseConditions()
		self.accept(sql_token.SEMICOLON)

		return UpdateStmt(table_name, table_attribute, value, conditions)

	# delete-stmt := DELETE FROM identifier ( WHERE conditions )? ";"
	def parseDeletestmt(self):
		self.accept(sql_token.DELETE)
		self.accept(sql_token.FROM)
		table_name = self.parseIdentifier()
		conditions = []
		if self.current_token.kind == sql_token.WHERE:
			self.acceptIt()
			conditions = self.parseConditions()
		self.accept(sql_token.SEMICOLON)

		return DeleteStmt(table_name, conditions)

	# conditions := condition ( ("and"|"or") condition )*
	def parseConditions(self):
		conditions = Conditions()
		r_condition = parseCondition(conditions)
		conditions.right = r_condition
		while self.current_token.kind == sql_token.AND or self.current_token.kind == sql_token.OR:
			conditions.operator = self.current_token.content
			self.acceptIt()
			l_condition = parseCondition(conditions)
			conditions.left = l_condition

		return conditions

	# condition := identifier filter value | "(" conditions ")"
	def parseCondition(self, parent_conditions):
		if self.current_token.kind == sql_token.ID:
			table_attribute = parseIdentifier()
			operator = parseOperator()
			value = parseValue()

			return Condition(table_attribute, operator, value)
		elif self.current_token.kind == sql_token.LEFTPAREN:
			self.acceptIt()
			conditions = parseConditions()
			conditions.parent = parent_conditions
			self.accept(sql_token.RIGHTPAREN)

			return conditions

	# vardecls := vardecl ( "," vardecl )*
	def parseVardecls(self):
		var_decls = {}
		var_decl = self.parseVardecl()
		var_decls[var_decl[0]] = var_decl[1]
		while self.current_token.kind == sql_token.COMMA:
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
		while self.current_token.kind == sql_token.COMMA:
			self.acceptIt()
			value = self.parseValue()
			values.append(value)

		return values

	# value := INTLITERAL | STRINGLITERAL
	def parseValue(self):
		if self.current_token.kind == sql_token.INTLITERAL or self.current_token.kind == sql_token.STRINGLITERAL:
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
		while self.current_token.kind == sql_token.COMMA:
			self.acceptIt()
			identifier = self.parseIdentifier()
			identifiers.append(identifier)

		return identifiers

	# identifier :=  alphabet ( alphabet | digit )*
	def parseIdentifier(self):
		if self.current_token.kind == sql_token.ID:
			identifier = self.current_token.content
			self.acceptIt()

			return identifier
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("ID", self.current_token.content))

	# data-type := INT | VARCHAR
	def parseDatatype(self):
		if self.current_token.kind == sql_token.VARCHAR or self.current_token.kind == sql_token.INT:
			data_type = self.current_token.content
			self.acceptIt()

			return data_type
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("INT or VARCHAR", self.current_token.content))

	# operator := ">"|"="|"<"|">="|"!="|"<="
	# sql_token.NOTEQ is "<>" or "!=" ?
	def parseOperator(self):
		if self.current_token.kind == sql_token.GREATER or \
		self.current_token.kind == sql_token.EQ or \
		self.current_token.kind == sql_token.LESS or \
		self.current_token.kind == sql_token.GREATEREQ or \
		self.current_token.kind == sql_token.NOTEQ or \
		self.current_token.kind == sql_token.LESSEQ:
			operator = self.current_token.content
			self.acceptIt()

			return operator
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("operator", self.current_token.content))


