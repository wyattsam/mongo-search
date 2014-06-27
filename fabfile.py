from fabric.api import local, cd, run, env, settings

requirements = [
    'git',
    'python-dev',
    'python-pip',
    'mongodb'
    ]
code_dir = '/home/ubuntu/search'
hostname = 'ec2-54-85-5-163.compute-1.amazonaws.com'

env.user = 'ubuntu'
env.hosts = [hostname]
env.key_filename = '~/.ssh/mongodb-search.pem'

def commit():
    local("git add -p && git commit")

def push():
    local("git push")

def prepare_deploy():
    commit()
    push()

def install_reqs():
    run('sudo apt-get install ' + ' '.join(requirements).strip()) 

def install_libs():
    with settings(warn_only=True):
        if not run('test -d %s' % code_dir).failed:
            with cd(code_dir):
                run('git pull')
                run('sudo pip install -r requirements.txt')

def deploy():
    with settings(warn_only=True):
        if run('test -d %s' % code_dir).failed:
            run('mkdir %s' % code_dir)
            install_reqs()
            run('git clone https://github.com/10gen/search %s' % code_dir)
            install_libs()
    with cd(code_dir):
        run("git pull")
        local('scp -i %s ~/dev/search/config/duckduckmongo.py ubuntu@%s:%s/config/' % (env.key_filename, hostname, code_dir))
        run('sudo restart search')
