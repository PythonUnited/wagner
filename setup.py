import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [
    'gitpython',
    'fabric'
    ]

setup(name='wagner',
      version="1.0.0",
      description='Tools for fabric, buildout etc.',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
          "Development Status :: 3 - Development/Alpha",
          "Intended Audience :: Developers",
          "License :: Freely Distributable",
          "Programming Language :: Python",
          "Topic :: Internet :: WWW/HTTP :: Site Management",
          "Topic :: Software Development :: Libraries :: "
          "Application Frameworks"
      ],
      author='PythonUnited',
      author_email='info@pythonunited.com',
      license='proprietary',
      url='',
      keywords='Fabric Buildout',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=requires,
      setup_requires=["setuptools-git"],
      entry_points="""\
      """
      )
