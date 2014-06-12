from base_transformer import BaseTransformer
import re

class StackOverflowTransformer(BaseTransformer):
    def __init__(self):
        BaseTransformer.__init__(self)

    def transform(self, obj):
        base = BaseTransformer.transform(self, obj)
        base.update({
            'id': obj['_id'],
            'score': obj['score'],
            'answered': obj['is_answered'],
            'answers': obj['answer_count'],
            'url': obj['link'],
            'title': obj['title'],
            'snippet': re.sub('<[^<]+?>', '', obj['body'])
        })
        return base
