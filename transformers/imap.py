from base_transformer import BaseTransformer

class IMAPTransformer(BaseTransformer):
    def __init__(self):
        BaseTransformer.__init__(self)
        self.baseurl = "http://www.google.com/search?q=site:groups.google.com "

    def transform(self, obj):
        base = BaseTransformer.transform(self, obj)
        base.update({
            'url': self.baseurl + obj['subject'] + '&btnI',
            'title': obj['subject'],
            'snippet': obj['body'],
            'group': obj['group'],
            'sender': obj['sender'],
            'from': obj['from']
        })
        return base
