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

from fabric.api import local, run, settings, cd, env, put, prefix
import os
import time

appname = 'search'
environment = 'prod'
user = appname+'-'+environment

appdir = '/opt/10gen/'+user
current = os.path.join(appdir, 'current')
releases = os.path.join(appdir, 'releases')

statedir = '/srv/10gen/search-prod'

hostname = user+'-1.vpc3.10gen.cc'

env.hosts = [hostname]
env.use_ssh_config = True
env.forward_agent = True
env.user = 'aestep'

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

def scrape():
    magic('python current/scrape.py')

def deploy():
    deploydir = os.path.join(releases, time.strftime(datefmt))
    req_file = os.path.join(deploydir, 'requirements.txt')

    venvdir = os.path.join(appdir, 'venv')
    venv_pip = os.path.join(venvdir, 'bin/pip')
    venv_gunicorn = os.path.join(venvdir, 'bin/gunicorn')
    venv_celery = os.path.join(venvdir, 'bin/celery')

    # set up directories
    run('git clone {0} {1}'.format('git@github.com:10gen/search', deploydir))
    run('chmod 2775 {0}'.format(deploydir))
    run('ln -sfn {0} {1}'.format(deploydir, current))

    # kill old services
    run('sudo /etc/init.d/search-web stop')

    # set up virtual environment
    # if it doesn't work, most likely the virtualenv was already in use by celery
    with settings(warn_only=True):
        run("scl enable python27 'virtualenv {0}'".format(venvdir)) # we need to use python27
        run("scl enable python27 '{0} install -r {1}'".format(venv_pip, req_file))

    # copy over the config file
    put('~/dev/search/config/search.py', '{0}/config/'.format(deploydir))

    # copy over celery files
    run('echo CELERY_BIN="\'{0}/bin/celery\'" >> {1}/config/celery.py'.format(venvdir, deploydir))
    #run('echo CELERY_CHDIR="\'{0}\'" >> {0}/config/celery.py'.format(deploydir))

    # restart services
    run('sudo /etc/init.d/search-web start')
