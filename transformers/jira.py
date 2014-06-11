from base_transformer import BaseTransformer

class JiraTransformer(BaseTransformer):
    def __init__(self):
        BaseTransformer.__init__(self)
        self.baseurl = 'http://jira.mongodb.org/browse/'

    def transform(self, obj):
        base = BaseTransformer.transform(self, obj)
        num_comments = obj.get('fields', {}).get('comment', {}).get('total', 0),

        com_list = obj.get('fields', {}).get('comment', {}).get('comments', [])
# TODO what is with that [0]??
        if num_comments[0] > 0 and len(com_list) == num_comments[0]:
            author = com_list[num_comments[0]-1]['author']
            last_com_name = author['displayName']
            last_com_avatar = author['avatarUrls']['32x32'] 
            last_com_un = author['name']
            last_com_body = com_list[num_comments[0]-1]['body']
            last_comment = {
                'name': last_com_name,
                'avatar': last_com_avatar,
                'user': last_com_un,
                'body': last_com_body
            }
        else:
            last_comment = None
        base.update({
            'id': obj['_id'],
            'status': obj.get('fields', {}).get('status', None),
            'comments': num_comments[0],
            'url': self.baseurl + obj['_id'],
            'title': obj['fields'].get('summary', ''),
            'snippet': obj['fields'].get('description', '')
        })
        if last_comment:
            base.update({'last_comment': last_comment})
        return base
            
