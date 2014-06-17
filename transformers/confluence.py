from base_transformer import BaseTransformer

class ConfluenceTransformer(BaseTransformer):
    def __init__(self):
        BaseTransformer.__init__(self)

    def transform(self, obj):
        base = BaseTransformer.transform(self, obj)
        base.update({
            'id': obj['_id'],
            'title': obj['title'],
            'snippet': obj['body'],
            'url': obj['url'],
            'space': obj['subsource'],
            'source': 'confluence'
        })
        return base
