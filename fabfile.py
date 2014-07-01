from fabric.api import local, cd, run, env, settings

appname = 'search'
environment = 'staging'
user = appname+'-'+environment

appdir = '/opt/10gen/'+user
statedir = '/srv/10gen/'+user
logdir = '/var/log/10gen/'+user
lockdir = '/var/run/10gen/'+user

hostname = 'ec2-54-88-195-164.compute-1.amazonaws.com'

env.user = 'ec2-user'
env.hosts = [hostname]
env.key_filename = '~/.ssh/mongodb-search.pem'

### Local prepare
def commit():
    local("git add -p && git commit")

def push():
    local("git push")

def prepare_deploy():
    commit()
    push()

### Do the fresh deploy
def pull():
    with cd(appdir):
        run('git pull')

def install_libs():
    with settings(warn_only=True):
        with cd(appdir):
            run('sudo pip install -r requirements.txt')

def setup_dirs():
    with settings(warn_only=True):
        run('mkdir -p '+appdir)
        run('chmod 2775 '+appdir)
        run('mkdir -p '+statedir)
        run('mkdir -p '+logdir)
        run('mkdir -p '+lockdir)
    with cd(appdir):
        run('mkdir -p releases')

def deploy_new():
    with settings(warn_only=True):
        setup_dirs()
        run('git clone https://github.com/10gen/search '+appdir)
    with cd(appdir):
        # copy config
        local('scp -i %s ~/dev/search/config/duckduckmongo.py ec2-user@%s:%s/config/' % (env.key_filename, hostname, appdir))
        run('sudo start search')

def deploy():
    with cd(appdir):
        run("git pull")
        run('sudo restart search')
