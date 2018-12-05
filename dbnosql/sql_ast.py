class Stmt:
	def __init__(self, table_name):
		self.table_name = table_name # ID

	def getTableName(self):
		return self.table_name.getToStr()

class CreateStmt(Stmt):
	def __init__(self, table_name, table_informations):
		super().__init__(table_name)
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
		super().__init__(table_name)
		self.literals = literals # list of Literal

class SelectStmt(Stmt):
	def __init__(self, table_attributes, table_name, clauses):
		super().__init__(table_name)
		self.table_attributes = table_attributes # list of ID
		self.clauses = clauses  # Clauses

class UpdateStmt(Stmt):
	def __init__(self, table_name, table_attribute, literal, clauses):
		super().__init__(table_name)
		self.table_attribute = table_attribute # ID
		self.literal = literal # Literal
		self.clauses = clauses # Clauses

class DeleteStmt(Stmt):
	def __init__(self, table_name, clauses):
		super().__init__(table_name)
		self.clauses = clauses # Clauses

class Clauses:
	def __init__(self, left, and_or, right): # binary tree structure
		self.left = left # Clause
		self.and_or = and_or # string ("and" | "or") or None
		self.right = right # Clause or None

class Clause:
	def __init__(self, table_attribute, operator, literal):
		self.table_attribute = table_attribute # ID
		self.operator = operator # Operator
		self.literal = literal # Literal

class VarDecl:
	def __init__(self, attribute_name, attribute_type):
		self.attribute_name = attribute_name # ID
		self.attribute_type = attribute_type # Datatype

class Literal:
	def __init__(self, value, data_type):
		self.value = value # string (INTLITERAL or STRINGLITERAL)
		self.data_type = data_type # Datatype

class ID:
	def __init__(self, value):
		self.value = value # string ( identifier )

	def getToStr(self):
		return self.value

class DataType:
	def __init__(self, type_):
		self.type = type_ # string ("INT" or "VARCHAR")

	def getToStr(self):
		return self.type

class Operator:
	def __init__(self, operator_type):
		self.operator_type = operator_type # string (">"|"="|"<"|">="|"!="|"<=")