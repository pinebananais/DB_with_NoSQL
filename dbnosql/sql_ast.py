class CreateStmt:
	def __init__(self, table_name, table_informations):
		self.table_name = table_name
		self.table_informations = table_informations

class ShowStmt:
	def __init__(self):
		self.stmt = "SHOW TABLES;"

class InsertStmt:
	def __init__(self, table_name, values):
		self.table_name = table_name
		self.values = values

class SelectStmt:
	def __init__(self, table_attributes, table_name, conditions):
		self.table_attributes = table_attributes
		self.table_name = table_name
		self.conditions = conditions

class UpdateStmt:
	def __init__(self, table_name, table_attribute, value, conditions):
		self.table_name = table_name
		self.table_attribute = table_attribute
		self.value = value
		self.conditions = conditions

class DeleteStmt:
	def __init__(self, table_name, conditions):
		self.table_name = table_name
		self.values = conditions

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