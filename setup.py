from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='wrangler',
	version='0.1.8.4',
	description='A pythonic static site generator',
	long_description=readme(),
	url='http://github.com/springload/Wrangler.py',
	author='Springload',
	author_email='hello@springload.co.nz',
	license='MIT',
	packages=['wrangler'],
	package_dir={'wrangler': 'wrangler'},
	package_data={'wrangler': ['defaults/*']},
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