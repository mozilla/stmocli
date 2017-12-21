import json
import os

default_path = './.stmocli.conf'

class Conf(object):
    def __init__(self, path = default_path):
        self.path = os.path.abspath(path)

        if not os.path.isfile(self.path):
            self.init_file()

        with open(path, 'r') as conf_file:
            self.contents = json.loads(conf_file.read())

    def init_file(self):
        with open(self.path, 'a') as conf_file:
            conf_file.write(json.dumps({}))

    def save(self):
        print(self.path)
        with open(self.path, 'w') as conf_file:
            conf_file.write(json.dumps(self.contents))

    def add_query(self, name, redash_id, filename):
        if name in self.contents:
            print('Query, "{}" already tracked!'.format(name))
        else:
            self.contents[name] = {
                'redash_id': redash_id,
                'filename': filename,
            }
            self.save()
