from base_transformer import BaseTransformer
from flask import request
import md5

CORP_URL = "https://corp.10gen.com/"
def corp_url():
    if request.referrer and 'mongodb' in request.referrer:
        return CORP_URL.replace('10gen', 'mongodb')
    return CORP_URL

class ProfilesTransformer(BaseTransformer):
    def __init__(self):
        BaseTransformer.__init__(self)

    def transform(self, obj):
        base = BaseTransformer.transform(self, obj)
        base.update({
            'id': obj['crowd_id'],
            'full_name': obj['full_name'],
            'url': corp_url() + 'employees/' + obj['crowd_id'],
            'team': obj['team']['name'],
            'office': obj['office'],
            'email': obj['primary_email'],
            'github': obj['github'],
            'title': obj['title'],
            'md5': md5.new(obj['primary_email'].strip().lower()).hexdigest()
        })
        return base
