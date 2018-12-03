import _scanner
import token
import _parser

print("\n\n")
print("--------------------------------------")
print("| Welcome to DB Stimulation Program! |")
print("--------------------------------------")
print("\n\n")
print("Enter SQL Statements:")
Parser = _parser.parser()
code = ""
single_quote_flag = False
double_quote_flag = False
result = None
while True:

	input_string = input(">> ")
	for ch in input_string:
		if single_quote_flag and ch == "'":
			single_quote_flag = False
			code += ch
		elif single_quote_flag:
			code += ch
		elif double_quote_flag and ch =='"':
			double_quote_flag = False
			code += ch
		elif double_quote_flag:
			cpde += ch
		elif ch == "'":
			single_quote_flag = True
			code += ch
		elif ch == '"':
			double_quote_flag = True
			code += ch
		elif ch == ';':
			code += ch
			try:
				result = Parser.parse(code)
				for x in result:
					print(x)
			except ValueError as err:
				print(err.args)
			code = ""
		else:
			code += ch 

