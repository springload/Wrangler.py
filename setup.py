from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='wrangler',
	version='0.1.4.8',
	description='A Jinja2 and YAML static site generator',
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
		'pyyaml'
	],
	scripts=['bin/wrangler'],
	zip_safe=False)