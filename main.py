import _scanner
import my_token
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
	print("my input: " + input_string)
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
			code += ch
		elif ch == "'":
			single_quote_flag = True
			code += ch
		elif ch == '"':
			double_quote_flag = True
			code += ch
		elif ch == ';':
			code += ch
			try:
				Parser.parse(code)
			except ValueError as err:
				print(err)
			code = ""
		else:
			code += ch 

