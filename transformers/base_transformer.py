

class BaseTransformer(object):
    def __init__(self):
        pass

    def transform(self, obj):
        """Transform an object to a desired schema
           before inserting it into the database.
           """
        return {
            'source': obj['source'],
            'subsource': obj['subsource'] if 'subsource' in obj else None
        }
