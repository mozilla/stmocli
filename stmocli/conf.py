import json
import os

default_path = './.stmocli.conf'

class Conf(object):
    def __init__(self, path = default_path):
        self.path = os.path.abspath(path)

        if not os.path.isfile(self.path):
            self.contents = {}
        else:
            with open(path, 'r') as conf_file:
                self.contents = json.loads(conf_file.read())

    def init_file(self):
        with open(self.path, 'a') as conf_file:
            conf_file.write(json.dumps({}))

    def save(self):
        print(self.path)
        with open(self.path, 'w') as conf_file:
            conf_file.write(json.dumps(self.contents))

    def add_query(self, file_name, query_metadata):
        if file_name in self.contents:
            print('Query, "{}" already tracked!'.format(file_name))
        else:
            self.contents[file_name] = query_metadata
            self.save()

    def get_query(self, file_name):
        return self.contents[file_name].copy()
