Wrangler
--------

Install the wrangler with::
	>>> pip install wrangler


Setup
--------

Expects this project structure::

	content/
		some-file.json
		some-other-file.json

	templates/
		base.j2

	www/
		[output-files-here]
	var/

	config.json


Run it via::
	>>> wrangler content www