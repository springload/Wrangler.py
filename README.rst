Wrangler
--------

Wrangler is a static site generator for people who aren't building blogs.

At Springload, we often need to whip up static sites, but we've struggled to find a tool that, well..
lets us get on with it. Enter the Wrangler. It won't expect your content to be formatted as a
series of blog posts. It doesn't copy static assets or process SaSS or make coffee.

It does one thing, and it does that one thing pretty well.

We hope you like it.


Documentation
-------------

Full documentation lives over here at `GitHub <https://github.com/springload/Wrangler.py>`_.


Install the wrangler with::
	>>> pip install wrangler


Setup
-----

To get started, wrangler can generate a project for you.


In your terminal::
	>>> wrangler create .
	>>> wrangler build content www


To automatically watch files for changes::
	>>> wrangler watch content www


To start a simple HTTP server::
	>>> wrangler serve www



That's all for now, folks!

Documentation `https://github.com/springload/Wrangler.py <https://github.com/springload/Wrangler.py>`_.

Springload `http://springload.co.nz <http://springload.co.nz>`_.