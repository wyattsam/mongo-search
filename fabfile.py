from fabric.api import local, cd, run, env

env.user = 'ec2-user'
env.hosts = ['search.10gen.cc']
env.key_filename = '~/.ssh/aws-test-dev.pem'

def commit():
    local("git add -p && git commit")

def push():
    local("git push")

def prepare_deploy():
    commit()
    push()

def deploy():
    code_dir = '/home/ec2-user/playground/duckduckmongo'
    with cd(code_dir):
        run("git pull")
        run("sudo reload duckduckmongo")
