import redis

r = redis.Redis(host='localhost', port=6379, db=0)

print("===test started====")
print(r.get('foo'))
print("===test finished===")
