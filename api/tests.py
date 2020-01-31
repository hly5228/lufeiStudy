from django.test import TestCase

# Create your tests here.
a = '{"xx":"1", "yy":"cc"}'
a2 = a.encode('utf-8')  # b'{"xx":"1", "yy":"cc"}'
print(a2)
a3 = a2.decode('utf-8')  # '{"xx":"1", "yy":"cc"}'
print(a3)
print(type(a3))  # str
print("xx".encode('utf-8'))
b = {b'xx':b'1',b'yy':b'cc'}
print(type(b))  # dict
b2 = str(b).encode('utf-8')
print(b2)  # b"{b'xx': b'1', b'yy': b'cc'}"
b3 = b2.decode('utf-8')
print(b3)  # {b'xx': b'1', b'yy': b'cc'}
print(type(b3))  # <class 'str'>

