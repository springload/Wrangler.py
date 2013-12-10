from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='wrangler',
	version='0.1',
	description='A Jinja2 and JSON static site generator',
	long_description=readme(),
	url='http://github.com/springload/Wrangler.py',
	author='Springload',
	author_email='hello@springload.co.nz',
	license='MIT',
	packages=['wrangler'],
	install_requires=[
		'markdown',
		'jinja2',
		'argparse',
		'docutils'
	],
	scripts=['bin/wrangler'],
	zip_safe=False)