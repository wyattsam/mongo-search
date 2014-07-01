# Copyright 2014 MongoDB Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from fabric.api import local, cd, run, env, settings

requirements = [
    'git',
    'gcc',
    'python-devel',
    'python-pip',
    'htop',
    'nginx'
    ]
code_dir = '/home/ec2-user/search'
hostname = 'ec2-54-88-195-164.compute-1.amazonaws.com'

env.user = 'ec2-user'
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
    run('sudo yum install ' + ' '.join(requirements).strip()) 
    # install mongodb 2.6
    run('echo -e "[mongodb]\nname=MongoDB Repository\nbaseurl=http://downloads-distro.mongodb.org/repo/redhat/os/x86_64\ngpgcheck=0\nenabled=1" | sudo tee /etc/yum.repos.d/mongodb.repo')
    run('sudo yum install mongodb-org')

def install_libs():
    with settings(warn_only=True):
        if not run('test -d %s' % code_dir).failed:
            with cd(code_dir):
                run('git pull')
                run('sudo pip install -r requirements.txt')

def start_mongo():
    with settings(warn_only=True):
        run('mkdir /home/ec2-user/data')
        run('mkdir /home/ec2-user/logs')
    run('sudo mongod --port 27017 --dbpath /home/ec2-user/data --logpath /home/ec2-user/logs/search.log --fork --smallfiles &')

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

def deploy_new():
    with settings(warn_only=True):
        if run('test -d %s' % code_dir).failed:
            run('mkdir %s' % code_dir)
            install_reqs()
            run('git clone https://github.com/10gen/search %s' % code_dir)
            install_libs()
    with cd(code_dir):
        #copy config
        local('scp -i %s ~/dev/search/config/duckduckmongo.py ec2-user@%s:%s/config/' % (env.key_filename, hostname, code_dir))
        install_config()
        with settings(warn_only=True):
            start_mongo()
            start_nginx()
        run('sudo start search')

def deploy():
    with cd(code_dir):
        run("git pull")
        run('sudo restart search')
