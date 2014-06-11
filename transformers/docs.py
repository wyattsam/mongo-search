from base_transformer import BaseTransformer

class DocsTransformer(BaseTransformer):
    def __init__(self):
        BaseTransformer.__init__(self)

    def transform(self, obj):
        base = BaseTransformer.transform(self, obj)
        base.update({
            'id': obj['_id'],
            'url': obj['url'],
            'title': obj['title'],
            'snippet': obj['text']
        })
        return base
