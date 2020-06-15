from pyignite import Client
from pyignite import Client, datatypes, GenericObjectMeta
from collections import OrderedDict

# DB mock
data = {}
data['/'] = {'contents': ['a', 'b', 'c'], 'directory': True}
data['/a'] = {'contents': ['c', 'd', 'f'], 'directory': True}
data['/a/c'] = {'contents': ['e'], 'directory': True}
data['/a/c/e'] = {'size': 42, 'directory': False}
data['/a/d'] = {'size': 8, 'directory': False}
data['/b'] = {'size': 1333, 'directory': False}
data['/c'] = {'contents': [], 'directory': True}
data['/a/f'] = {'contents': [], 'directory': True}

client = Client()
client.connect('10.0.3.10', 10800)
fileCache = client.get_or_create_cache("files")
metadataCache = client.get_or_create_cache("metadata")

class DBEntry(metaclass=GenericObjectMeta, schema=OrderedDict([
    ('directory', datatypes.BoolObject),
    ('name', datatypes.String),
    ('size', datatypes.LongObject),
    ('contents', datatypes.StringArrayObject)
    ])):
    pass

def mkDBEntry(path):
    entry = data[path]
    return DBEntry(entry.get('directory'),
            path[path.rfind('/') + 1:],
            entry.get('size', 0),
            entry.get('contents', []))

for k, v in data.items():
    if not v['directory']:
        fileCache.put(k, 'Contents of %s' % k)

    entry = mkDBEntry(k)
    print(entry)
    metadataCache.put(k, entry)

client.close()
