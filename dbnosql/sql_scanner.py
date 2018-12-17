import sql_token

space_char = {' ', '\t', '\n', '\r'}

def isDigit(x):
	return '0' <= x <= '9'

def isAlpha(x):
	return ('a' <= x <= 'z') or ('A' <= x <= 'Z') or x == '_'

class Scanner:
	def __init__(self):
		self.source = None
		self.cur_token = ""
		self.cur_char = ""
		self.cur_kind = None
		return

	def set_source(self, source):
		self.source = source
		self.get_next_char()

	def get_next_char(self):
		if self.source == "":
			self.cur_char = "$"
			return
		self.cur_char = self.source[0]
		self.source = self.source[1:]

	def push_char(self):
		self.cur_token += self.cur_char
		self.get_next_char()

	def send_cur_token(self):
		ret = sql_token.token(self.cur_kind, self.cur_token)
		self.cur_token = ""
		return ret

	def get_next_token(self):
		while self.cur_char in space_char :
			self.get_next_char()
		self.cur_kind = self.scan()
		return self.send_cur_token()

	def scan(self):
		if self.cur_char == "$":
			self.push_char()
			return sql_token.EOF
		if self.cur_char == "+":
			self.push_char()
			return sql_token.PLUS
		if self.cur_char == "-":
			self.push_char()
			return sql_token.MINUS
		if self.cur_char == "*":
			self.push_char()
			return sql_token.ASTER
		if self.cur_char == "/":
			self.push_char()
			return sql_token.DIV
		if self.cur_char == "%":
			self.push_char()
			return sql_token.MOD
		if self.cur_char == "&":
			self.push_char()
			return sql_token.BITAND
		if self.cur_char == "|":
			self.push_char()
			return sql_token.BITOR
		if self.cur_char == "^":
			self.push_char()
			return sql_token.BITXOR
		if self.cur_char == ",":
			self.push_char()
			return sql_token.COMMA
		if self.cur_char == ";":
			self.push_char()
			return sql_token.SEMICOLON
		if self.cur_char == ">":
			self.push_char()
			if self.cur_char == "=":
				self.push_char()
				return sql_token.GREATEREQ
			return sql_token.GREATER
		if self.cur_char == "<":
			self.push_char()
			if self.cur_char == "=":
				self.push_char()
				return sql_token.LESSEQ
			# if self.cur_char == ">":
			# 	self.push_char()
			# 	return sql_token.NOTEQ
			return sql_token.LESS
		if self.cur_char == "!":
			self.push_char()
			if self.cur_char == "=":
				self.push_char()
				return sql_token.NOTEQ
			return sql_token.ERROR
		if self.cur_char == "=":
			self.push_char()
			return sql_token.EQ
		if self.cur_char == "{":
			self.push_char()
			return sql_token.LEFTBRACE
		if self.cur_char == "}":
			self.push_char()
			return sql_token.RIGHTBRACE
		if self.cur_char == "(":
			self.push_char()
			return sql_token.LEFTPAREN
		if self.cur_char == ")":
			self.push_char()
			return sql_token.RIGHTPAREN
		if self.cur_char == "[":
			self.push_char()
			return sql_token.LEFTBRACKET
		if self.cur_char == "]":
			self.push_char()
			return sql_token.RIGHTBRACKET
		if isDigit(self.cur_char):
			while isDigit(self.cur_char):
				self.push_char()
			if self.cur_char == ".":
				self.push_char()
				while isDigit(self.cur_char):
					self.push_char()
				return sql_token.FLOATLITERAL
			return sql_token.INTLITERAL
		if isAlpha(self.cur_char):
			while isDigit(self.cur_char) or isAlpha(self.cur_char):
				self.push_char()
			if self.cur_token.upper() in sql_token.keywords:
				# modified YIS 12-10
				self.cur_token = self.cur_token.upper()
				# end
				return sql_token.keywords[self.cur_token.upper()]
			return sql_token.ID
		if self.cur_char == '"':
			self.get_next_char()
			while self.cur_char != '"':
				if self.cur_char == "$":
					cur_token = "Not Terminated String"
					return sql_token.ERROR
				self.push_char()
			# modified by JYH
			self.get_next_char()
			return sql_token.STRINGLITERAL

		self.cur_token = "Unexpected Token" + " " + self.cur_char
		return sql_token.ERROR
		
