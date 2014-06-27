from fabric.api import local, cd, run, env, settings

requirements = [
    'git',
    'python-dev',
    'python-pip',
    'htop',
    'nginx'
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

def pull():
    with cd(code_dir):
        run('git pull')

def install_reqs():
    run('sudo apt-get install ' + ' '.join(requirements).strip()) 
    # install mongodb 2.6
    run('sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 7F0CEB10')
    run("echo 'deb http://downloads-distro.mongodb.org/repo/ubuntu-upstart dist 10gen' | sudo tee /etc/apt/sources.list.d/mongodb.list")
    run('sudo apt-get update')
    run('sudo apt-get install mongodb-org')

def install_libs():
    with settings(warn_only=True):
        if not run('test -d %s' % code_dir).failed:
            with cd(code_dir):
                run('git pull')
                run('sudo pip install -r requirements.txt')

def start_mongo():
    with settings(warn_only=True):
        run('mkdir /home/ubuntu/data')
        run('mkdir /home/ubuntu/logs')
    run('sudo mongod --port 27017 --dbpath /home/ubuntu/data --logpath /home/ubuntu/logs/search.log --fork --smallfiles')

def start_nginx():
    run('sudo service nginx start')

def stop_nginx():
    run('sudo service nginx stop')

def install_config():
    if run('test -d /etc/init').failed:
        run('sudo mkdir /etc/init')
    run('sudo cp %s/init/search.conf /etc/init/search.conf' % code_dir)
    run('sudo cp %s/config/nginx.conf /etc/nginx/' % code_dir)
    if run('test -d /etc/nginx/conf.d').failed:
        run('sudo mkdir /etc/nginx/conf.d')
    run('sudo cp %s/config/search.conf /etc/nginx/conf.d/' % code_dir)

def deploy():
    with settings(warn_only=True):
        if run('test -d %s' % code_dir).failed:
            run('mkdir %s' % code_dir)
            install_reqs()
            run('git clone https://github.com/10gen/search %s' % code_dir)
            install_libs()
    with cd(code_dir):
        run("git pull")
        #copy config
        local('scp -i %s ~/dev/search/config/duckduckmongo.py ubuntu@%s:%s/config/' % (env.key_filename, hostname, code_dir))
        install_config()
        with settings(warn_only=True):
            start_mongo()
            start_nginx()
        run('sudo start search')
