class token:
	kind = None
	content = None
	def __init__(self, kind, content):
		self.kind = kind
		self.content = content

	def __str__(self):
		return "Token : {}\t\t, Kind : {}".format(self.content, self.kind)

(ID			, 		# identifier 0
BITOR		,		# |
BITAND		,		# &
BITXOR		,		# ^
EQ			,		# =
NOTEQ		,		# <>
LESSEQ		,		# <=
LESS		,		# <
GREATER		,		# >
GREATEREQ	,		# >=
PLUS		,		# +
MINUS		,		# -
ASTER		,		# *
DIV			,		# /
MOD			,		# %
INTLITERAL	,
FLOATLITERAL,
STRINGLITERAL,		# 17

# keywords:
ALL			,		# 18
AND			,
ANY			,
BETWEEN		,
EXISTS		,
IN			,
LIKE		,
NOT			,
OR			,
SOME		,
CREATE		,
TABLE		,
DROP		,
FROM		,
INSERT		,
INTO		,
VALUES		,
SELECT		,
SHOW		,
TABLES		,
UPDATE		,
WHERE		,
DELETE		,		# 40

# data types:
CHAR		,		# 41
VARCHAR		,
INT 		,
FLOAT 		,
DECIMAL		,		# 45

# punctuation:
LEFTBRACE 	,	# { 46
RIGHTBRACE	,	# }
LEFTBRACKET	,	# [
RIGHTBRACKET,	# ]
LEFTPAREN	,	# (
RIGHTPAREN	,	# )
COMMA		,	# ,
SEMICOLON	,	# ; 53

# special tokens:
ERROR		,
EOF)		= range(56)   # end-of-file

token_list = [
"ID", 		# identifier 0
"BITOR",		# |
"BITAND",		# &
"BITXOR",		# ^
"EQ",		# =
"NOTEQ",		# <>
"LESSEQ",		# <=
"LESS",		# <
"GREATER",		# >
"GREATEREQ",		# >=
"PLUS",		# +
"MINUS",		# -
"ASTER",		# *
"DIV",		# /
"MOD",		# %
"INTLITERAL",
"FLOATLITERAL",
"STRINGLITERAL",		# 17

# keywords:
"ALL",		# 18
"AND",
"ANY",
"BETWEEN",
"EXISTS",
"IN",
"LIKE",
"NOT",
"OR",
"SOME",
"CREATE",
"TABLE",
"DROP",
"FROM",
"INSERT",
"INTO",
"VALUES",
"SELECT",
"SHOW",
"TABLES",
"UPDATE",
"WHERE"	,
"DELETE",		# 40

# data types:
"CHAR",		# 41
"VARCHAR",
"INT",
"FLOAT",
"DECIMAL",		# 45

# punctuation:
"LEFTBRACE" ,	# { 46
"RIGHTBRACE",	# }
"LEFTBRACKET",	# [
"RIGHTBRACKET",	# ]
"LEFTPAREN",	# (
"RIGHTPAREN",	# )
"COMMA",	# ,
"SEMICOLON",	# ; 53

# special tokens:
"ERROR",
"EOF"
]

keywords = {"ALL" : ALL,
			"AND" : AND,
			"ANY" : ANY,
			"BETWEEN" : BETWEEN,
			"EXISTS" : EXISTS,
			"IN" : IN,
			"LIKE" : LIKE,
			"NOT" : NOT,
			"OR" : OR,
			"SOME" : SOME,
			"CREATE" : CREATE,
			"TABLE" : TABLE,
			"DROP" : DROP,
			"FROM" : FROM,
			"INSERT" : INSERT,
			"INTO" : INTO,
			"VALUES" : VALUES,
			"SELECT" : SELECT,
			"SHOW" : SHOW,
			"TABLES" : TABLES,
			"UPDATE" : UPDATE,
			"WHERE" : WHERE,
			"CHAR" : CHAR,
			"VARCHAR" : VARCHAR,
			"INT" : INT,
			"FLOAT" : FLOAT,
			"DECIMAL" : DECIMAL,
			"DELETE" : DELETE}