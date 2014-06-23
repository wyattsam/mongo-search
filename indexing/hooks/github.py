from base_hook import BaseHook
from Crypto.Hash import SHA
from Crypto.Hash import HMAC

class GithubHook(BaseHook):
    def __init__(self):
        BaseHook.__init__(self, 'http://github.com')
        #self.needs_auth = True

        self.authtype = 'X-Hub-Signature'
        self.sha1 = SHA.new()

    def authenticate(self, msg, h)
        # TODO: how much is auth necessary? JIRA can't even use it
        pass
        """
        token = str(user['auth']) # cannot be unicode
        hasher = HMAC.new(token, digestmod=self.sha1)
        hasher.update(msg)
        return result, (h == hasher.hexdigest()) # secure compare I suppose
        """

    @self.celery.task
    def handle(self, msg):
        name = msg['repository']['name']
        org = msg['repository']['owner']['name']
        head_sha = msg['head_commit']['id']
        _id = org + '/' + name + '-' + head_sha
        msg.update({
            '_id': _id,
            'source': 'github',
            'subsource': name
        })
        self.combined.update(dict(_id=_id), msg, True)
