import re
import os
import tempfile
from fabric.api import sudo, settings, put, run, lcd, local, prefix, cd
from fabric.colors import green, blue, red, yellow
from contextlib import nested
from contextlib import contextmanager as _contextmanager
from git import Repo


def success(text, bold=True):
    print green(text, bold=bold)


def info(text, bold=True):
    print blue(text, bold=bold)


def error(text, bold=True):
    print red(text, bold=bold)


def warning(text, bold=True):
    print yellow(text, bold=bold)


def install_system_requirements(requirements, system_services=[], os="debian"):
    """ Install required packages system wide. """

    info("Installing system wide dependencies")

    installers = {'debian': 'apt-get -y install',
                  'centos': 'yum -y install'}

    installer = installers.get(os)

    if not installer:
        error("No installer found for %s" % os)
        return False

    for req in requirements:
        sudo("%s %s" % (installer, req))

    if os == "centos":
        with settings(warn_only=True):

            for service in system_services:
                sudo('systemctl enable %s' % service)

    success("System dependencies installed")


def _system_services_action(services, action, system="upstart"):
    with settings(warn_only=True):

        for service in services:

            if system == "upstart":
                sudo('service %s start' % service)
            else:
                sudo('/etc/init.d/%s %s' % (service, action))


def start_system_services(services, system="upstart"):
    info("Starting services")

    _system_services_action(services, "start")

    success("All services started")


def stop_system_services(services, system="upstart"):
    info("Stopping services")

    _system_services_action(services, "stop")

    success("All services stopped")


def restart_system_services(services, system="upstart"):
    info("Restarting services")

    _system_services_action(services, "restart")

    success("All services restarted")


def check_sanity(env, tag=None):
    """ Check local GIT for uncommited stuff """

    info("Checking sanity...")

    repo = Repo(".")

    branch = repo.active_branch

    if repo.is_dirty(untracked_files=True):
        error("Your GIT repository for this buildout is dirty")
        return False

    if tag:

        if tag not in [t.name for t in repo.tags]:
            error("No such tag exist on repository!")
            return False

    if env == "prd":

        if not tag:
            error("No tag specified. Can only release tags to PRD")
            return False

        if branch.name != "master":
            error("Your GIT repository is on branch '%s'.\n"
                  "To release on PRD, it should be on 'master'!" % branch)
            return False

    if env == "acc":

        if not tag:
            error("No tag specified. Can only release tags to ACC")
            return False

        if branch.name != "master" and not branch.name.startswith("release"):
            error("Your GIT repository is on branch '%s'.\n"
                  "To release on ACC, it should be on 'master "
                  "or on a release branch." % branch)
            return False

    success("sane!")
    return True


def get_version(tag=None):
    """ Either use tag from command line, or use short version
    of latest commit. """

    repo = Repo(".")

    if tag:
        version = tag
    else:
        version = repo.git.describe(always=True)

    info("Found version %s" % version)

    return version


def generate_egg_info(eggs):
    info = {}

    for egg in eggs:
        with lcd("/tmp/%s" % egg):
            version = local('python setup.py --version', capture=True)
            name = local('python setup.py --name', capture=True)

            info[name] = version

    return info


def upload_buildout_cfg(env, env_user, env_home, eggs, dist):
    TPL = """[buildout]
extends = buildout-%s.cfg

[versions]
%s
    """

    versions = []
    info = generate_egg_info(eggs)

    for egg in info.keys():
        versions.append("%s = %s" % (egg, info[egg]))

    cfg = TPL % (env, "\n".join(versions))

    fh = tempfile.NamedTemporaryFile(delete=False)

    fh.write(cfg)
    fh.close()

    fh_base = os.path.basename(fh.name)

    put(fh.name, "/tmp/%s" % fh_base)
    sudo("cp /tmp/%s %s/buildout-%s/buildout.cfg" % (fh_base, env_home, dist),
         user=env_user)
    sudo("rm /tmp/%s" % fh_base)

    fh.unlink


def create_buildout_dist(buildout_path=".", tag=None):
    repo = Repo(buildout_path)

    dist_dir = tempfile.mkdtemp()
    dist_file = os.path.join(dist_dir, 'buildout.tar')

    repo.archive(open(dist_file, 'wb'), treeish=tag,
                 prefix="buildout-%s/" % get_version(tag=tag))

    return dist_file


def upload_buildout(dist, dest, env_user):
    """ upload the buildout git archive """

    info("Uploading buildout %s" % dist)

    put(dist, '/tmp')

    dist_file = os.path.basename(dist)

    run('chmod a+rx /tmp/%s' % dist_file)

    sudo('tar -C %s -xf /tmp/%s' % (dest, dist_file), user=env_user)

    success('uploaded buildout')


def prepare_eggs(eggs, env):
    """
    Locally prepare the eggs using the branches found in autocheckout buildout
    files like autocheckout-tst.cfg
    :param eggs: eggs to prepare
    :param env: either tst, acc or prd etc.
    :return:
    """
    for egg in eggs:
        regex = re.compile("%s\s=\s(\S*)\s(\S*)\srev=(.*)$" % egg)

        with open("autocheckout-%s.cfg" % env) as f:
            for line in f:
                result = regex.search(line)
                if result:
                    break

        repo_url = result.group(2)
        branch = result.group(3)
        repo = None

        if os.path.isdir("/tmp/%s" % egg):
            repo = Repo("/tmp/%s" % egg)
        if not repo:
            info("Cloning %s, branch=%s" % (egg, branch))
            repo = Repo().clone_from(repo_url, "/tmp/%s" % egg, branch=branch)

        gitcmd = repo.git
        gitcmd.checkout(result.group(3))

        success("Prepared %s, branch=%s" % (egg, branch))


def upload_eggs(eggs, dest, py_version, env_user):
    for egg in eggs:
        name, version = generate_egg_info(["/tmp/%s" % egg]).items()[0]

        name = name.replace("-", "_")

        with lcd("/tmp/%s" % egg):
            local("python setup.py bdist_egg")

            egg_name = "%s-%s-py%s.egg" % (name, version, py_version)

            put("./dist/%s" % egg_name, "/tmp")

            sudo("mkdir -p %s/%s" % (dest, egg_name), user=env_user)
            sudo("unzip -o /tmp/%s -d %s/%s" % (egg_name, dest, egg_name),
                 user=env_user)


def summarize(version, eggs):
    lines = ["***********************************"]
    lines.append("Installed version %s" % version)
    lines.append("Eggs:")

    egg_info = generate_egg_info(eggs)

    for egg in egg_info.keys():
        lines.append("  %s: %s" % (egg, egg_info[egg]))

    success("\n".join(lines))


@_contextmanager
def virtualenv(user):
    activate_cmd = 'source ~%s/bin/activate' % user

    with nested(cd('~%s/' % user), prefix(activate_cmd)):
        yield
