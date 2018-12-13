import sys
import redis_connector

print("\n\n")
print("-------------------------------------")
print("| Welcome to DB Simulation Program! |")
print("-------------------------------------")
print("\n\n")
print("Enter SQL Statements:")
conn = redis_connector.RedisConnector()
# Parser = sql_parser.Parser()
code = ""
single_quote_flag = False
double_quote_flag = False
result = None
while True:
	try:
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
				code += ch
			elif ch == "'":
				single_quote_flag = True
				code += ch
			elif ch == '"':
				double_quote_flag = True
				code += ch
			elif ch == ';':
				code += ch
				conn.connect(code)
				print()
				code = ""
			else:
				code += ch 
	except ValueError as err:
		print(err)
		# modified by YIS 12-10
		code = ""
		# end
	except KeyboardInterrupt:
		print("\nDB Simulation program would be terminated. Good Bye!")
		sys.exit()
