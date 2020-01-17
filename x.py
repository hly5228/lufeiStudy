import json

v = {
    1:'db',
    2:'sb',
    3:{1:1}
}

s = json.dumps(v)
print(json.loads(s))

