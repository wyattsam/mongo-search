from fabric.api import local, cd, run, env, settings

env.user = 'ubuntu'
env.hosts = ['ec2-54-85-5-163.compute-1.amazonaws.com']
env.key_filename = '~/.ssh/mongodb-search.pem'

requirements = [
    'git',
    'python-dev',
    'python-pip',
    'mongodb'
    ]

code_dir = '/home/ubuntu/search'

def commit():
    local("git add -p && git commit")

def push():
    local("git push")

def prepare_deploy():
    commit()
    push()

def install_reqs():
    run('sudo apt-get install ' + ' '.join(requirements).strip()) 
    with settings(warn_only=True):
        if not run('test -d %s' % code_dir).failed:
            with cd(code_dir):
                run('sudo pip install -r requirements.txt')

def deploy():
    with settings(warn_only=True):
        if run('test -d %s' % code_dir).failed:
            run('mkdir %s' % code_dir)
            install_reqs()
            run('git clone https://github.com/10gen/search %s' % code_dir)
    with cd(code_dir):
        run("git pull")
        #run("sudo restart search")
        run("gunicorn app:app")
