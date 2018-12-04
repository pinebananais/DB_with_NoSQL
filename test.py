import redis

r = redis.Redis(host='localhost', port=6379, db=0)

r.lpush("student", [
	'june', 24, 'com.c', 
	'Amy', 21, 'math', 
	'Emil', 22, 'com.c',
	'watson', 21, 'art',
	'james', 27, 'music'])

r.mset({"student:row": 5, "student:col": 3})


print("===test started====")
print(r.get('foo'))
print("===test finished===")
