from fabric.api import local, cd, run, env, settings
import os
import time

appname = 'search'
environment = 'staging'
user = appname+'-'+environment

appdir = '/opt/10gen/'+user
current = os.path.join(appdir, 'current')
releases = os.path.join(appdir, 'releases')

hostname = 'ec2-54-88-195-164.compute-1.amazonaws.com'

env.hosts = [hostname]
env.use_ssh_config = True
env.forward_agent = True

datefmt = '%Y%m%d%H%M%S'

def commit():
    local("git add -p && git commit")

def push():
    local("git push")

def prepare_deploy():
    commit()
    push()

def deploy():
    deploydir = os.path.join(releases, time.strftime(datefmt))
    venvdir = os.path.join(appdir, 'venv')
    venv_pip = os.path.join(venvdir, 'bin/pip')
    req_file = os.path.join(deploydir, 'requirements.txt')

    # set up directories
    run('git clone {0} {1}'.format('https://github.com/10gen/search', deploydir))
    run('chmod 2775 {0}'.format(deploydir))
    run('ln -sfn {0} {1}'.format(deploydir, current))

    # set up virtual environment
    run('virtualenv {0}'.format(venvdir))
    run('source {0}/bin/activate'.format(venvdir))
    run('{0} install -r {1}'.format(venv_pip, req_file))

    # start services
    with cd(deploydir):
        # copy over the config file
        local('scp -i %s ~/dev/search/config/duckduckmongo.py %s@%s:%s/config/' % (env.key_filename, user, hostname, deploydir))
        run('sudo restart search')
