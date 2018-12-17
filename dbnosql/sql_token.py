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
SET 		,
WHERE		,
DELETE		,		
SUM			,
COUNT		,
GROUP		,
BY			,
HAVING		,		# 46

# data types:
CHAR		,		# 47
VARCHAR		,
INT 		,
FLOAT 		,
DECIMAL		,		# 51

# punctuation:
LEFTBRACE 	,	# { 52
RIGHTBRACE	,	# }
LEFTBRACKET	,	# [
RIGHTBRACKET	,	# ]
LEFTPAREN	,	# (
RIGHTPAREN	,	# )
COMMA		,	# ,
SEMICOLON	,	# ; 59

# special tokens:
ERROR		,
EOF)		= range(62)   # end-of-file

token_list = [
"ID", 		# identifier 0
"BITOR",		# |
"BITAND",		# &
"BITXOR",		# ^
"EQ",			# =
"NOTEQ",		# <>
"LESSEQ",		# <=
"LESS",			# <
"GREATER",		# >
"GREATEREQ",		# >=
"PLUS",			# +
"MINUS",		# -
"ASTER",		# *
"DIV",			# /
"MOD",			# %
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
"SET",
"WHERE"	,
"DELETE",
"SUM",
"COUNT",
"GROUP",
"BY",
"HAVING",		# 46

# data types:
"CHAR",		# 47
"VARCHAR",
"INT",
"FLOAT",
"DECIMAL",		# 51

# punctuation:
"LEFTBRACE" ,	# { 52
"RIGHTBRACE",	# }
"LEFTBRACKET",	# [
"RIGHTBRACKET",	# ]
"LEFTPAREN",	# (
"RIGHTPAREN",	# )
"COMMA",	# ,
"SEMICOLON",	# ; 59

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
			"SET" : SET,
			"WHERE" : WHERE,
			"CHAR" : CHAR,
			"VARCHAR" : VARCHAR,
			"INT" : INT,
			"FLOAT" : FLOAT,
			"DECIMAL" : DECIMAL,
			"DELETE" : DELETE,
			"SUM" : SUM,
			"COUNT" : COUNT,
			"GROUP" : GROUP,
			"BY" : BY,
			"HAVING" : HAVING}
