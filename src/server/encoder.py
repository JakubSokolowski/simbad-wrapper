from flask import json
from sqlalchemy.ext.declarative import DeclarativeMeta


def to_camel_case(snake_str):
    components = snake_str.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class AlchemyEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o.__class__, DeclarativeMeta):
            data = {}
            fields = o.__json__() if hasattr(o, '__json__') else dir(o)
            for field in [f for f in fields if not f.startswith('_') and f not in ['metadata', 'query', 'query_class']]:
                value = o.__getattribute__(field)
                camel_field = to_camel_case(field)
                try:
                    json.dumps(value)
                    data[camel_field] = value
                except TypeError:
                    data[camel_field] = None
            return data
        return json.JSONEncoder.default(self, o)
