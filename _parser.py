import token
import _scanner

class parser:
	Scanner = _scanner.scanner()
	result = []
	def __init__(self):
		return

	def accept(self, expected_token_kind):
		if self.current_token.kind == expected_token_kind:
			self.result.append(self.current_token)
			self.current_token = self.Scanner.get_next_token()
		else:
			raise ValueError('Error : Expected Token Type : {}'.format(expected_token_kind), 'Instead : {}'.format(self.current_token.content))

	def parse(self, source):
		self.Scanner.set_source(source)
		self.current_token = self.Scanner.get_next_token()
		if self.current_token.kind == token.CREATE:
			self.parseCreatestmt()
		return self.result


	def parseCreatestmt(self):
		self.accept(token.CREATE)
		self.accept(token.TABLE)
		self.accept(token.ID)
		self.accept(token.LEFTPAREN)
		self.parseVardecl()
		while self.current_token.kind == token.COMMA:
			self.accept(token.COMMA)
			self.parseVardecl()
		self.accept(token.RIGHTPAREN)
		self.accept(token.SEMICOLON)

	def parseVardecl(self):
		self.parseDatatype()
		self.accept(token.ID)

	def parseDatatype(self):
		if self.current_token.kind == token.CHAR:
			self.accept(token.CHAR)
			self.accept(token.LEFTPAREN)
			self.accept(token.INTLITERAL)
			self.accept(token.RIGHTPAREN)
		elif self.current_token.kind == token.VARCHAR:
			self.accept(token.VARCHAR)
			self.accept(token.LEFTPAREN)
			self.accept(token.INTLITERAL)
			self.accept(token.RIGHTPAREN)
		elif self.current_token.kind == token.FLOAT:
			self.accept(token.FLOAT)
		elif self.current_token.kind == token.INT:
			self.accept(token.INT)
		elif self.current_token.kind == token.DECIMAL:
			self.accept(token.DECIMAL)
			self.accept(token.LEFTPAREN)
			self.accept(token.INTLITERAL)
			self.accept(token.COMMA)
			self.accept(token.INTLITERAL)
			self.accept(token.RIGHTPAREN)
		else:
			raise ValueError('Error : Expect token type : {}'.format('data_type'))
