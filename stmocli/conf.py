import json
import os

import attr

default_path = './.stmocli.conf'


class Conf(object):
    def __init__(self, path=default_path):
        self.path = os.path.abspath(path)

        if not os.path.isfile(self.path):
            self.contents = {}
        else:
            with open(path, 'r') as conf_file:
                self.contents = json.loads(conf_file.read())

    def init_file(self):
        if os.path.exists(self.path):
            return False
        with open(self.path, 'w') as conf_file:
            conf_file.write(json.dumps({}))
        return True

    def save(self):
        with open(self.path, 'w') as conf_file:
            conf_file.write(json.dumps(self.contents, sort_keys=True,
                                       indent=2, separators=(',', ': ')))

    def add_query(self, file_name, query_metadata):
        if file_name in self.contents:
            print('Query, "{}" already tracked!'.format(file_name))
        else:
            self.contents[file_name] = query_metadata.to_dict()
            self.save()

    def get_query(self, file_name):
        return QueryInfo.from_dict(self.contents[file_name])

    def get_filenames(self):
        return self.contents.keys()


@attr.s
class QueryInfo(object):
    id = attr.ib(converter=str)
    data_source_id = attr.ib()
    name = attr.ib()
    description = attr.ib()
    schedule = attr.ib()
    options = attr.ib()

    @id.validator
    def id_is_not_none(instance, attribute, value):
        if value is None:
            raise ValueError("id may not be None")

    @classmethod
    def from_dict(cls, d):
        """Instantiate a QueryInfo from a dictionary.

        Different from QueryInfo(**d) because this ignores missing keys or extra values in d."""
        fields = [field.name for field in attr.fields(cls)]
        return cls(**{k: d.get(k, None) for k in fields})

    def to_dict(self):
        return attr.asdict(self)
