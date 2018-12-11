class Stmt:
	def __init__(self, table_name):
		self.table_name = table_name # ID

	def getTableName(self):
		return self.table_name.getToStr()

	def getMetaTableName(self):
		return self.table_name.getToStr() + ":metadata"

class CreateStmt(Stmt):
	def __init__(self, table_name, table_informations):
		super().__init__(table_name) # ID
		self.table_informations = table_informations # list of VarDecl

	def getTableinfo(self):
		result = dict()
		for table_info in self.table_informations:
			result[table_info.attribute_name.getToStr()] = table_info.attribute_type.getToStr()
		return result

class ShowStmt(Stmt):
	def __init__(self):
		super().__init__("SHOW TABLES;")

class InsertStmt(Stmt):
	def __init__(self, table_name, literals):
		super().__init__(table_name) # ID
		self.literals = literals # list of Literal

	def getLiterals(self):
		result = list()
		for literal in self.literals:
			result.append(literal.getToStr())
		return result

	def getLiteralTypes(self):
		result = list()
		for literal in self.literals:
			result.append(literal.data_type.getToStr())
		return result

class SelectStmt(Stmt):
	def __init__(self, table_attributes, table_name, clauses):
		super().__init__(table_name) # ID
		self.table_attributes = table_attributes # list of ID or "*"
		self.clauses = clauses  # Clauses

	def getAttributes(self):
		if self.table_attributes == '*':
			return str("*")
		else:
			result = list()
			for attribute in self.table_attributes:
				result.append(attribute.getToStr())
			return result

class UpdateStmt(Stmt):
	def __init__(self, table_name, table_attribute, literal, clauses):
		super().__init__(table_name) # ID
		self.table_attribute = table_attribute # ID
		self.literal = literal # Literal
		self.clauses = clauses # Clauses

	def getAttribute(self):
		return self.table_attribute.getToStr()

	def getLiteral(self):
		return self.literal.getToStr()

class DeleteStmt(Stmt):
	def __init__(self, table_name, clauses):
		super().__init__(table_name) # ID
		self.clauses = clauses # Clauses

class DropStmt(Stmt):
	def __init__(self, table_name):
		super().__init__(table_name)

class Clauses:
	def __init__(self, left, and_or, right): # binary tree structure
		self.left = left # Clause
		self.and_or = and_or # string ("and" | "or") or None
		self.right = right # Clause or None
	
	def getToList(self):
		if self.and_or == "AND":
			return self.left.getToList() + self.right.getToList() + [self.and_or]
		elif self.and_or == "OR":
			return self.left.getToList() + self.right.getToList() + [self.and_or]
		else :
			return self.left.getToList()

class Clause:
	def __init__(self, table_attribute, operator, literal):
		self.table_attribute = table_attribute # ID
		self.operator = operator # Operator
		self.literal = literal # Literal

	def getToList(self):
		return [self.table_attribute.getToStr(), self.operator.getToStr(), self.literal.getToStr()]

class VarDecl:
	def __init__(self, attribute_name, attribute_type):
		self.attribute_name = attribute_name # ID
		self.attribute_type = attribute_type # Datatype

class Terminal:
	def __init__(self, value):
		self.value = value # string

	def getToStr(self):
		return self.value

class Literal(Terminal):
	def __init__(self, value, data_type):
		super().__init__(value) # string (INTLITERAL or STRINGLITERAL)
		self.data_type = data_type # Datatype

class ID(Terminal):
	def __init__(self, value):
		super().__init__(value) # string ( identifier )

class DataType(Terminal):
	def __init__(self, value):
		super().__init__(value) # string ("INT" or "VARCHAR")

class Operator(Terminal):
	def __init__(self, value):
		super().__init__(value) # string (">"|"="|"<"|">="|"!="|"<=")
