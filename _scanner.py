import token

space_char = {' ', '\t', '\n', '\r'}

def isDigit(x):
	return '0' <= x <= '9'

def isAlpha(x):
	return ('a' <= x <= 'z') or ('A' <= x <= 'Z') or x == '_'


class scanner:
	source = None
	cur_token = ""
	cur_char = " "
	cur_kind = None
	def __init__(self):
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
		ret = token.token(self.cur_kind, self.cur_token)
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
			return token.EOF
		if self.cur_char == "+":
			self.push_char()
			return token.PLUS
		if self.cur_char == "-":
			self.push_char()
			return token.MINUS
		if self.cur_char == "*":
			self.push_char()
			return token.ASTER
		if self.cur_char == "/":
			self.push_char()
			return token.DIV
		if self.cur_char == "%":
			self.push_char()
			return token.MOD
		if self.cur_char == "&":
			self.push_char()
			return token.BITAND
		if self.cur_char == "|":
			self.push_char()
			return token.BITOR
		if self.cur_char == "^":
			self.push_char()
			return token.BITXOR
		if self.cur_char == ",":
			self.push_char()
			return token.COMMA
		if self.cur_char == ";":
			self.push_char()
			return token.SEMICOLON
		if self.cur_char == ">":
			self.push_char()
			if self.cur_char == "=":
				self.push_char()
				return token.GREATEREQ
			return token.GREATER
		if self.cur_char == "<":
			self.push_char()
			if self.cur_char == "=":
				self.push_char()
				return token.LESSEQ
			if self.cur_char == ">":
				self.push_char()
				return token.NOTEQ
			return token.LESS
		if self.cur_char == "=":
			self.push_char()
			return token.EQ
		if self.cur_char == "{":
			self.push_char()
			return token.LEFTBRACE
		if self.cur_char == "}":
			self.push_char()
			return token.RIGHTBRACE
		if self.cur_char == "(":
			self.push_char()
			return token.LEFTPAREN
		if self.cur_char == ")":
			self.push_char()
			return token.RIGHTPAREN
		if self.cur_char == "[":
			self.push_char()
			return token.LEFTBRACKET
		if self.cur_char == "]":
			self.push_char()
			return token.RIGHTBRACKET
		if isDigit(self.cur_char):
			while isDigit(self.cur_char):
				self.push_char()
			if self.cur_char == ".":
				self.push_char()
				while isDigit(self.cur_char):
					self.push_char()
				return token.FLOATLITERAL
			return token.INTLITERAL
		if isAlpha(self.cur_char):
			while isDigit(self.cur_char) or isAlpha(self.cur_char):
				self.push_char()
			if self.cur_token.upper() in token.keywords:
				return token.keywords[self.cur_token.upper()]
			return token.ID
		if self.cur_char == '"':
			self.push_char()
			while self.cur_char != '"':
				if self.cur_char == "$":
					cur_token = "Not Terminated String"
					return token.ERROR
				self.push_char()
			return token.STRINGLITERAL

		self.cur_token = "Unexpected Token" + " " + self.cur_char
		return token.ERROR
		
