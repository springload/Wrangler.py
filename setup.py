from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='wrangler',
	version='0.1.7.0',
	description='A pythonic static site generator',
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
		'docutils',
		'pyyaml',
		'watchdog',
		'blinker'
	],
	scripts=['bin/wrangler'],
	zip_safe=False)