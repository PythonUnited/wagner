Wagner - The Art of Deploying
=============================

Utils and base stuff for buildout, fabric and other app
deployments. This stuff incorporates gitflow and semver in it's
concepts. As we see it, deploying is like conducting an orchestra, the
deployment setup is like a symphony...

Prerequisites
-------------

* GIT
* Gitflow
* Fabric
* Setuptools
* Buildout

Introduction
------------

### Environments

We distinguish the following environments: DVL, TST, ACC and PRD.
Development is your local working environment, so that's really
entirely up to you...

TST is for testing purposes, so for a new feature, a concept, a fix,
etc. TST should be considered somewhat volatile.

ACC is for end-user acceptance: what is released here and accepted
should to to PRD in exactely the same shape. On ACC, only tagged stuff
should be deployed. Wagner enforces this.

PRD is production. Only for stable software. Release must be tagged
and merged into master.


### Versioning

Use semantic versioning, including release candidate descriptors like
rc1, rc2, etc. This has been described thouroughly on
http://semver/org/.


### Deployment process

1. Use fabfile from a buildout dir
2. fab does:
   - check whether buildout git repo is not dirty, all changes are
     publicly available
   - check eggs, and upload all eggs to dist server


Django
------

You may use the buildout config base file __django.cfg__. If you need
a version, specify this in your own etended config, under the version
section, so i.g.:

    [versions]
    django => 1.8.0


