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

from fabric.api import local, run, sudo, settings, cd, env, put
import os
import time

appname = 'search'
appdir = '/opt/10gen/'

env.roledefs = {
    'staging': ['search-staging-1.vpc3.10gen.cc'],
    'prod': ['search-prod-1.vpc3.10gen.cc']
}

env.use_ssh_config = True

datefmt = '%Y%m%d%H%M%S'

def commit():
    local("git add -p && git commit")

def push():
    local("git push")

def prepare_deploy():
    commit()
    push()

def magic(command):
    with cd(appdir):
        run("scl enable python27 'source venv/bin/activate; {0}'".format(command))

def build_index():
    magic('python current/util/indexes.py')

def scrape(*vargs):
    role = env.roles[0]
    user = appname + '-' + role

    global appdir
    appdir = '/opt/10gen/' + user

    magic('python current/scrape.py {0}'.format(' '.join(vargs)))

def deploy(refspec):
    role = env.roles[0]
    user = appname + '-' + role

    global appdir
    appdir = '/opt/10gen/' + user

    current = os.path.join(appdir, 'current')
    releases = os.path.join(appdir, 'releases')

    deploydir = os.path.join(releases, time.strftime(datefmt))

    # set up directories
    run('git clone {0} {1}'.format('git@github.com:10gen-labs/mongo-search', deploydir))
    with cd(deploydir):
        run('git checkout {0}'.format(refspec))

    run('chmod 2775 {0}'.format(deploydir))
    run('ln -sfn {0} {1}'.format(deploydir, current))

    # kill old services
    sudo('/etc/init.d/search-web stop', shell=False)

    # set up virtual environment
    # if it doesn't work, most likely the virtualenv was already in use by celery
    with cd(appdir):
        run("scl enable python27 'source venv/bin/activate; pip install -r current/requirements.txt'") # we need to use python27

    private_config_file = os.path.join(appdir, 'private.py')
    configdir = os.path.join(current, 'config')
    run('cp {0} {1}'.format(private_config_file, configdir))

    if role == 'staging':
        gunicorn_conf_path = os.path.join(configdir, 'gunicorn.conf')
        run('sed -i \'s/prod/staging/g\' {0}'.format(gunicorn_conf_path))

    # copy over the config file
    # put('~/dev/search/config/duckduckmongo.py', '{0}/config/search.py'.format(deploydir))

    # copy over celery files
    # run('echo CELERY_BIN="\'{0}/bin/celery\'" >> {1}/config/celery.py'.format(venvdir, deploydir))
    #run('echo CELERY_CHDIR="\'{0}\'" >> {0}/config/celery.py'.format(deploydir))

    # restart services
    # with cd(appdir):
    #     run('crontab -r')
    #     run('crontab -e')
    sudo('/etc/init.d/search-web start', shell=False)
