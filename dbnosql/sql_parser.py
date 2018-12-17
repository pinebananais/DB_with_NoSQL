import redis
from sql_ast import *
import sql_token
import sql_scanner

## modified by JYH
class Parser:
	def __init__(self):
		self.scanner = sql_scanner.Scanner()

	def acceptIt(self): # alway accept token
		self.current_token = self.scanner.get_next_token()

	def accept(self, expected_token_kind):
		if self.current_token.kind == expected_token_kind:
			self.current_token = self.scanner.get_next_token()
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format(sql_token.token_list[expected_token_kind], self.current_token.content))

	def parse(self, source):
		self.scanner.set_source(source)
		self.current_token = self.scanner.get_next_token()
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
		elif self.current_token.kind == sql_token.DROP:
			result = self.parseDropstmt()
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
		self.accept(sql_token.TABLES)
		self.accept(sql_token.SEMICOLON)

		return ShowStmt()

	# insert-stmt := INSERT INTO identifier VALUES "(" literals ")" ";"
	def parseInsertstmt(self):
		self.accept(sql_token.INSERT)
		self.accept(sql_token.INTO)
		table_name = self.parseIdentifier()
		self.accept(sql_token.VALUES)
		self.accept(sql_token.LEFTPAREN)
		values = self.parseLiterals()
		self.accept(sql_token.RIGHTPAREN)
		self.accept(sql_token.SEMICOLON)

		return InsertStmt(table_name, values)

	# select-stmt := SELECT ( "*" | identifiers ) FROM identifier ( Where clauses )? ";"
	def parseSelectstmt(self):
		self.accept(sql_token.SELECT)
		if self.current_token.kind == sql_token.ASTER:
			table_attributes = self.current_token.content
			self.acceptIt()
		# modified by HJY 2018-12-16
		elif self.current_token.kind == sql_token.SUM or self.current_token.kind == sql_token.COUNT:
			table_attributes = self.parseAggregation()
		else:
			table_attributes = self.parseIdentifiers()
		self.accept(sql_token.FROM)
		table_name = self.parseIdentifier()
		clauses = []
		if self.current_token.kind == sql_token.WHERE:
			self.acceptIt()
			clauses = self.parseClauses()
		# modified by HJY 2018-12-16
		group = None
		if self.current_token.kind == sql_token.GROUP:
			self.acceptIt()
			if self.current_token.kind == sql_token.BY:
				self.acceptIt()
				group = self.parseIdentifier()
			else:
				raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("BY", self.current_token.content))
		having_clause = None
		if self.current_token.kind == sql_token.HAVING:
			self.acceptIt()
			having_clause = self.parseHavingClause()
		self.accept(sql_token.SEMICOLON)

		return SelectStmt(table_attributes, table_name, clauses, group, having_clause)

	# update-stmt := UPDATE identifier SET identifier "=" literal ( WHERE clauses )? ";"
	def parseUpdatestmt(self):
		self.accept(sql_token.UPDATE)
		table_name = self.parseIdentifier()
		self.accept(sql_token.SET) # sql_token.SET doen't exist !!!!!!!!!!!
		table_attribute = self.parseIdentifier()
		self.accept(sql_token.EQ) # ASSIGN?, EQ?
		literal = self.parseLiteral()
		clauses = []
		if self.current_token.kind == sql_token.WHERE:
			self.acceptIt()
			clauses = self.parseClauses()
		self.accept(sql_token.SEMICOLON)

		return UpdateStmt(table_name, table_attribute, literal, clauses)

	# delete-stmt := DELETE FROM identifier ( WHERE clauses )? ";"
	def parseDeletestmt(self):
		self.accept(sql_token.DELETE)
		self.accept(sql_token.FROM)
		table_name = self.parseIdentifier()
		clauses = []
		if self.current_token.kind == sql_token.WHERE:
			self.acceptIt()
			clauses = self.parseClauses()
		self.accept(sql_token.SEMICOLON)

		return DeleteStmt(table_name, clauses)
	
	# drop-stmt := DROP TABLE identifier ";"
	def parseDropstmt(self):
		self.accept(sql_token.DROP)
		self.accept(sql_token.TABLE)
		table_name = self.parseIdentifier()
		self.accept(sql_token.SEMICOLON)
		
		return DropStmt(table_name)
	# modified by YIS 12 - 13
	# clauses := orclauses
	def parseClauses(self):
		return self.parseOrclauses()

	# or-clauses := and-clauses ("or" or-clauses)?
	def parseOrclauses(self):
		lclauses = self.parseAndclauses()
		and_or = None
		rclauses = None
		if self.current_token.kind == sql_token.OR:
			self.acceptIt()
			and_or = "OR"
			rclauses = self.parseOrclauses()
		return Clauses(lclauses, and_or, rclauses)

	# and-clauses := primary-clause ("and" and-clauses)?
	def parseAndclauses(self):
		lclauses = self.parsePrimaryclause()
		and_or = None
		rclauses = None
		if self.current_token.kind == sql_token.AND:
			self.acceptIt()
			and_or = "AND"
			rclauses = self.parseAndclauses()
		return Clauses(lclauses, and_or, rclauses)
	
	# primary-clause := "(" clauses ")" | clause
	def parsePrimaryclause(self):
		if self.current_token.kind == sql_token.LEFTPAREN:
			self.acceptIt()
			clauses = self.parseClauses()
			self.accept(sql_token.RIGHTPAREN)
			return clauses
		else :
			clause = self.parseClause()
			return Clauses(clause, None, None)

	# clause := identifier filter literal
	def parseClause(self):
		table_attribute = self.parseIdentifier()
		operator = self.parseOperator()
		literal = self.parseLiteral()
		
		return Clause(table_attribute, operator, literal)


	# end 12 - 13

	# vardecls := vardecl ( "," vardecl )*
	def parseVardecls(self):
		vardecls = list()
		vardecl = self.parseVardecl()
		vardecls.append(vardecl)
		while self.current_token.kind == sql_token.COMMA:
			self.acceptIt()
			vardecl = self.parseVardecl()
			vardecls.append(vardecl)

		return vardecls

	# vardecl := identifier data-type
	def parseVardecl(self):
		identifier = self.parseIdentifier()
		data_type = self.parseDatatype()

		return VarDecl(identifier, data_type)

	# literals := literal ( "," literal )*
	def parseLiterals(self):
		literals = list()
		literal = self.parseLiteral()
		literals.append(literal)
		while self.current_token.kind == sql_token.COMMA:
			self.acceptIt()
			literal = self.parseLiteral()
			literals.append(literal)

		return literals

	# literal := INTLITERAL | STRINGLITERAL
	def parseLiteral(self):
		if self.current_token.kind == sql_token.INTLITERAL:
			data_type = DataType("INT")
		elif self.current_token.kind == sql_token.STRINGLITERAL:
			data_type = DataType("VARCHAR")
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("INTLITERAL or STRINGLITERAL", self.current_token.content))
		value = self.current_token.content
		self.acceptIt()

		return Literal(value, data_type)


	# identifiers := identifier ( "," identifier )*
	def parseIdentifiers(self):
		identifiers = list()
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
			value = self.current_token.content
			self.acceptIt()

			return ID(value)
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("ID", self.current_token.content))

	# data-type := INT | VARCHAR
	def parseDatatype(self):
		if self.current_token.kind == sql_token.VARCHAR or self.current_token.kind == sql_token.INT:
			type_ = self.current_token.content
			self.acceptIt()

			return DataType(type_)
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("INT or VARCHAR", self.current_token.content))

	# operator := ">"|"="|"<"|">="|"!="|"<="|LIKE
	# sql_token.NOTEQ is "<>" or "!=" ?
	def parseOperator(self):
		if self.current_token.kind == sql_token.GREATER or \
		self.current_token.kind == sql_token.EQ or \
		self.current_token.kind == sql_token.LESS or \
		self.current_token.kind == sql_token.GREATEREQ or \
		self.current_token.kind == sql_token.NOTEQ or \
		self.current_token.kind == sql_token.LESSEQ or \
		self.current_token.kind == sql_token.LIKE:
			operator_type = self.current_token.content
			self.acceptIt()

			return Operator(operator_type)
		else:
			raise ValueError('SyntaxError, Expected Token is \"{0}\" but entered Token is \"{1}\"'.format("operator", self.current_token.content))

	# modified by HJY 2018-12-16
	# aggregation := SUM "(" identifier ")" | COUNT "(" identifier ")"
	def parseAggregation(self):
		aggregation = list()
		if self.current_token.kind == sql_token.SUM:
			aggregation.append(self.current_token.content)
			self.acceptIt()
			self.accept(sql_token.LEFTPAREN)
			identifier = self.parseIdentifier()
			aggregation.append(identifier)
			self.accept(sql_token.RIGHTPAREN)
		elif self.current_token.kind == sql_token.COUNT:
			aggregation.append(self.current_token.content)
			self.acceptIt()
			self.accept(sql_token.LEFTPAREN)
			identifier = None
			if self.current_token.kind == sql_token.ID:
				identifier = self.parseIdentifier()
			elif self.current_token.kind == sql_token.ASTER:
				identifier = self.current_token.content
				self.acceptIt()
			aggregation.append(identifier)
			self.accept(sql_token.RIGHTPAREN)

		return aggregation

	def parseHavingClause(self):
		aggregation = self.parseAggregation()
		operator = self.parseOperator()
		literal = self.parseLiteral()

		return HavingClause(aggregation, operator, literal)
