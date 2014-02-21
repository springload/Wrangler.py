# Wrangler

Wrangler is a static site generator for people who aren't building blogs.

Features:
* Write your content in YAML, JSON or Markdown
* Build your templates with the awesome [Jinja2](http://jinja.pocoo.org/docs/templates/) library. If you know Twig, it'll be instantly familiar.
* Really quick (well, it's relative, but 200 pages, 88 templates in < 4 seconds).
* Smart caching, so only the pages you change are re-rendered
* Simple CLI gets you up and running in a few seconds
* Built-in basic HTTP server and file watching
* Extensible with custom filters, extensions, hooks, and parsers


At Springload, we often need to whip up static sites, but we've struggled to find a tool that, well..
lets us get on with it. Enter the Wrangler. It won't expect your content to be formatted as a
series of blog posts. It doesn't copy static assets or process SaSS or make coffee.

It does one thing, and it does that one thing pretty well.

We hope you like it.


# Quickstart

Install the wrangler via pip:

```
pip install wrangler
```

Generate a new project in the current directory `.`

```
wrangler create .
```

This will create a bunch of directories. To check it works, build the little auto-generated site:

```
wrangler build content www
```

Serve your site via an engine of your choice, or the handy built-in server at `http://127.0.0.1:8000/`:

```
wrangler serve www
```

Want to watch your content and templates for changes and automatically re-build them?
There's an app for that. The watch task takes all the same options as `build`. 

```
wrangler watch content www
```


# Okay, that works, what now?

## Wrangler's file structure

Wrangler follows a pretty simple filesystem convention:

```bash
my-site/
|--content
|----index.yaml
|--lib
|--templates
|----template.j2
|--var
|--wrangler.yaml
|--www
```

* `content` - the content directory. Your site structure will mirror this directory. If you've got `content/index.yaml`, you'll get `www/index.html`
* `templates` - where your jinja2 `.j2` templates live
* `www` - the web root folder. Really, you can output to anywhere, we just picked www as a sensible default.
* `lib` - custom extensions, classes, hooks, etc go in here. Write some python modules and pass the results back to wrangler
* `var` - holds the template cache and the file objects cache (wrangler uses the out-of-the-box Pickle and Shelve combo)

All these paths can be changed in `wrangler.yaml`


# Working with content

Wrangler assumes you're working with some kind of structured data, and you want to translate
those data files out to HTML (or even classic ASP, if that's your thing).  

Three parsers are included in the package: json, yaml and markdown (with yaml front-matter). They
operate on a per-file basis, so this is perfectly valid:

```bash
my-site/
|--content
|----index.yaml
|----page-2.json
|----page-3.md
```

#### YAML (.yml, .yaml)

```yaml
meta:
    title: My title
    template: template.j2
    description: "My cool page!"
data:
    content: "Here's some page content!"
    blocks:
        - "Lots of content"
        - "even more content"
        - "wow, so much content!"
```

#### JSON (.js, .json)

```json
{
    "meta": {
        "title": "My title",
        "template": "template.j2",
        "description": "My cool page!"
    },
    "data": {
        "content": "Here's some page content!",
        "blocks": [
            "Lots of content",
            "even more content",
            "wow, so much content! "
        ]
    }
}
```

#### Markdown (.md, .markdown)

```markdown
---
title: My title
template: template.j2
description: "Markdown uses yaml front-matter"
---
# A heading!
Some paragraph text

## Another heading! 
Even more text

---
Nice HR you got there.

* A list
* with some
* list items

```

Here's a nice [markdown cheatsheet](https://github.com/adam-p/markdown-here/wiki/Markdown-Cheatsheet)

## Metadata options

Use the metadata for anything related to the page. You can throw whatever you like in here,
but there's a few reserved words:

```yaml
meta:
    title: "Musings on the pronounciation of doge"
    alias: "Doge"
    template: "template.j2"
    class: DogePage
    hide_from_nav: true
    description: "Is it dog-e, doog, douge, douche? How do I properly refer to this meme?"
    keywords: ["much", "analytics", "such", "SEO"]
    output_file_extension: asp
    weight: 1
    thumbnail: /assets/images/thumb/doge-100x100.jpg
    related:
        - content/other-page.yaml
        - content/pages/this-page-here.yaml
```

**title**           The page name in the navigation (and probably your title tag too) 

**template**        Template path, relative to your wrangler.yaml's `templates_dir`

**alias**           Shorthand for the title, which can be used in the navigation instead

**class**           Attempts to replace the Python class for the page object. Must be subclass of `wrangler.Core.Page` 

**hide_from_nav**   Hide this page from the navigation tree.

**description**     What it says on the tin

**keywords**        A List of keywords

**output_file_extension**   Override the default `output_file_extension` from wrangler.yaml. The page will be rendered with this extension.

**weight**          Handy for ordering pages, from low to high. By default, wrangler will use the filesystem's alphabetical sorting.  

**thumbnail**       Path to a thumbnail image

**related**         A list of related pages. In your template, this will let you get some basic info about other pages (like the title and description).


### Generated metadata

The wrangler adds some things to your metadata automatically, in your templates you can access:

```jinja

{{ meta.url }}
{{ meta.segments }}
{{ meta.filepath }}
{{ meta.mtime }}

{{ meta.children }}
{{ meta.parents }}
{{ meta.parents_siblings }}


```

**url**                 The path to the built file, relative to the `output_dir`, for instance `/`

**segments**            A list of all the url segments: `["sub-directory", "index.html"]`      

**filepath**            The name of the input file

**mtime**               The modified time. You could use this to build a blog timestamp, for instance.

**children**            Any direct children of the current directory

**parents**             All the nodes between the current file and `/`

**parents_siblings**    The siblings of the parent directory.



## Page data

Page data is entirely optional.

Let's look at this little page, `custom-page.yaml` You can throw wrangler a page with no data, and hard-code everything in the template,
`custom-page.j2` if you want. 

```yaml
meta:
    title: No content!
    template: custom-page.j2
    output_file_extension: txt
```

This will build `www/custom-page.txt`. 


### Accessing data

Wrangler ships with a jinja2 markdown filter. If you're using a markdown file, the markdown is available at `data.content`.
Pipe the content to the markdown filter, and you're done.

```jinja
<div class="content">
    {{ data.content|markdown }}
</div>
```

Markdown is a fantastic writing format, but it can present some limitations
when you're dealing with more structured data. For YAML and JSON files, access parts of the `data` dictionary and wire them up
as you see fit:

```jinja
<div class="content">
{{ data.content }}
{% for block in data.blocks %}
    <p>{{ block }}</p>
{% endfor %}
</div>
```

---


## Configuration

The editable options for the wrangler are saved in the `wrangler.yaml` file in your project root.

Crack it open, and you'll find three nodes: `wrangler`, `site` and `extensions`


#### wrangler

This is the core config, the hard-core stuff. It looks a little something like this:

```yaml
wrangler: 

    # Template directory relative to your project root
    templates_dir: templates

    # Default template to load if no template is specified for a page
    default_template: template.j2

    # Default output file extension. Note this can be overwritten in the content
    # by specifying 'output_file_extension' in the 'meta' area
    output_file_extension: html

    # Supported data formats. Ensure a parser is registered for each type.
    # More information about parsers can be found in the link at the top of the file.
    data_formats: ['yaml', 'yml', 'json', 'js', 'md', 'markdown']

    # Ignore hidden files, and files starting with underscores
    ignore: ['.','_']

    # Prints all the internal plumbing output to stdout
    verbose: false

    # Always force all pages to be rendered
    force: false

    # Run without the cache (useful for developing custom page classes, to prevent them
    # from being cached each run).
    nocache: false

    # The location of the template cache zip file. 
    # Ensure the var path exists and is writeable by the user
    build_cache_file: var/build.cache
    compiled_templates_file: var/jinja
    compiled_templates_log: var/jinja.log

    # Custom methods/classes go in the lib directory, for instance
    # lib/Page.py or lib/Extensions.py or lib/Filters.py
    lib_path: lib

# file continues....
```

#### extensions
Configure any extensions you've set up here. Extensions let you run any python function you want, and inject
the results into your templates.


```yaml
# wrangler.yaml continued...
extensions:
    # Sitemap generates a tree structure of your entire site, relative to the
    # webroot specified here 
    # 
    #   {{ extensions.sitemap }}
    # 
    # We leave it up to you to iterate over the sitemap and print everything in
    # a pretty manner, but this gist might get you started:
    # https://gist.github.com/joshbarr/111

    sitemap: 
        webroot: /
```


```jinja
{{ extensions.cachebuster }}
```

Some default extensions are included: `sitemap`, `fileinfo`, and `cachebuster`


#### site
Site vars are site-wide variables, available inside your templates as children of the `site` object.

For instance, to get the images path, you can call `{{ site.paths.images }}` and save yourself some typing. 

```yaml
# wrangler.yaml continued...
site:
    paths: 
        css: assets/css
        js: assets/js
        assets: assets
```

```jinja
{# Hey, it's those handy vars I set in my site_vars #}
{{ site.paths.css }}
```

All this documentation is in the `wrangler.yaml` file as well, so you won't get lost! 

---

# Command line options

### wrangler create

Takes a single positional argument, the path in which to create your new project:
```bash
cd my-sweet-site && wrangler create .

# or 
wrangler create my-sweet-site

```


### wrangler build

`input_dir`     Input directory such as `site/content`
`output_dir`    Output directory such as `www`

```bash
wrangler build content www
```

Force rendering regardless of when your content was last modified:

```bash
wrangler build content www --force
```

Re-cache all the page objects 

```bash
wrangler build content www --nocache
```

Change the output file extension for all pages to classic `asp`.(Why would anyone do that?)

```
wrangler build content www -o ".asp"
```

Change the data format to search for in the `input_dir` to `json`
```
wrangler build content www -d 'json'
```

Change the location of the templates directory
```
wrangler build content www -t other-templates-dir
```

Change the location of the config file
```
wrangler build content www -c site/config/wrangler.yaml
```


### wrangler watch

Has all the same options as `wrangler build`

Print all the plumbing every time a file changes:

```bash
wrangler watch content www --verbose
```


### wrangler serve

Accepts one positional argument (the directory to serve) and an optional `--port` (default 8000).

```bash
wrangler serve www --port 8001
```


### wrangler clean

Remove the template cache and the object cache from the 'var' directory.

```bash
wrangler clean
```

---


# Under the hood

Wrangler loads all the python modules found in your project's `lib` directory when it boots.

This gives you the power to extend the core functions and manipulate page data - for instance you could
load some values from a database and make them available in your templates. 


## Internal structure

When you call `build`, wrangler builds a representation of the tree structure in your `content/` directory.

It's using a doubly linked list of `Node` objects, which get mashed into a `NodeGraph`, a handy container
for dealing with the nodes.

```yaml

# Pseudocode
NodeGraph:
    # The nodes in their hierarchical structure, eg:
    tree:        
        Node:
            children:
                - Node:
                    children:
                        - Node
                - Node:
                    children:
                        - Node
                        - Node
                        - Node
   
    # The 'all' dictionary is the same nodes represented in a flat structure.
    # This can be much quicker to iterate over than the tree, and you can
    # access both from within your hooks and extensions.
    # The filepath is used as the unique key.
    all:
        
        content/index.md:
            Node:
                # node's data...

        content/other-page.md:
            Node:
                # node's data...
```

Nodes can access their children, and also their parents:

```yaml
# More pseudocode
Node:
    path: "content/index.md"
    children:
        - Node:
        - Node:
        - Node:
    parent:
        Node:
```

To keep things tidy, the Node object doesn't hold a representation of the page data directly on it – 
nodes are just containers.

Following the ideas in [this discussion](http://stackoverflow.com/questions/280243/python-linked-list),
the Node has a __cargo__ property that holds the _real_ page class:


```python
from wrangler.Core import Node

class GoldBullion(object):
    price = 1200

the_node = Node("index", "content/index.md", parent=None, cargo=None)

the_node.add_cargo(GoldBullion())

cargo = the_node.get_cargo()

print cargo.price

```

## The page class

Pages hold a `dict` representation of your source file's data, and provide
a consistent way for the `Renderer` to access the data. To create a custom page,
just sub-class `wrangler.Core.Page` and it'll be auto-loaded. 

**Handy tip:** If your custom class has the name of `Page`, it'll overwrite the 
default `Page` object for all pages.


```python
# lib/Page.py
import wrangler.Core as wrangler

class Page(wrangler.Page):
    def get_content(self):
        return self.data["data"]

    def get_metadata(self):
        return self.data["meta"]

    def get_properties(self):
        print "Hey, I'm a custom page instance!"
        return {
            "title": self.get_title(),
            "alias": self.get_short_title(),
            "description": self.get_meta_description(),
            "url": self.get_tidy_url(),
            "show_in_navigation": self.show_in_navigation(),
            "weight": self.get_weight(),
            "thumbnail": self.get_thumbnail()
        }

```

In our example above, we're modifying the three main page methods, `get_content()`, `get_metadata()`, and `get_properties()`

##### get_content()

Called when the when the Page is rendered, this is available in your template as the `data` object:

```jinja
<!doctype html>
    <div class='dump-of-data-object'>
        {{ data.content }}
    </div>
```

##### get_metadata()

Called when the when the Page is rendered, this is the `meta` object:

```jinja
<!doctype html>
    <title>{{ meta.title }}
```

##### get_properties()

A little trickier to explain, but still awesome. When a `Node` is rendered, it requests 
certain information about pages related to the current page, such as the children, siblings,
parents, and manually-related pages. 

Rather than share _everything_ with _everything else_, each `Page` class describes the
basic information that it's happy to share with other pages.

```python
    def get_properties(self):
        return {
            "title": self.get_title(),
            "alias": self.get_short_title(),
            "url": self.get_tidy_url(),
            "show_in_navigation": self.show_in_navigation(),
            "weight": self.get_weight(),
            
            # Let's add the modified time, so our theoretical parent
            # page could know when we last saved the file. 
            "mtime": self.getmtime()
        }
``` 

### Custom page classes

Let's look at a really simple example, a custom page class which reverses
all the text on the page. Very practical. 

Firstly, set the `class` property in your page meta to tell wrangler which class
to load:

content/custom.md:
```markdown
---
class: RightToLeft
---
# My custom page

With its custom content.
```

Then create a new class somewhere in your `lib/` directory that subclasses `Page`.
It doesn't matter where inside your `lib/` directory it ends up, the only rule is that
it has to subclass the `Page` object:

lib/pages.py
```python
import wrangler.Core as wrangler

class RightToLeft(wrangler.Page)
    def get_content(self):
        for key, val in self.data["data"]:
            self.data["data"][key] = val[::-1]
        return self.data["data"]

```

Great! Our page will be printed with right-to-left text.



## Content parsers
If you look in your `wrangler.yaml` file, you'll notice it accepts three file types: `["yaml", "json", "md"]`

Wrangler includes three parsers by default, `Yaml`, `Markdown` and `Json`, which consume the input files and
represent them as meaningful data.


#### Rolling your own

The auto-loader looks for anything that sublcasses `wrangler.Core.Parser`. 

For instance, you could do this somewhere in your `lib/Parsers.py` to support text format

```python
from wrangler.Core import Parser
from lxml import objectify
from collections import defaultdict

class XmlParser(Parser):
    accepts = ["xml", "robotlanguage"]

    def interpret(self, file_contents):
        return root = objectify.fromstring(file_contents)


```



## Hooks and extensions

Wrangler uses [blinker](http://blinker.pypi.org)'s signals for processing hooks and extensions.

### Hooks

Hooks are signals that are fired at critical points in the render process.
They're proccessed in the order they appear in your modules, and can modify the
incoming objects directly. They've also got access to wrangler's `config`, `renderer` and `reporter`. 


```python

from wrangler.Core import before_render, after_render, load_item, save_item, render_item

@before_render
def before(**kw):
    nodes = kw['nodes']
    config = kw['config']
    renderer = kw['renderer']
    reporter = kw['reporter']
    print "Hey, I'm a hook!"
    return "foo!"

@after_render
def after(**kw):
    nodes = kw['nodes']
    config = kw['config']
    renderer = kw['renderer']
    reporter = kw['reporter']
    print "Hey, I'm a hook!"
    return ""
```

### Extensions

Extensions are python scripts that return handy data to your templates' `extensions` dictionary.

Let's take this little script:

```python
# lib/my_extensions.py
from wrangler.Core import extension

@extension
def my_extension(sender, **kwargs):
    # Add some config to your YAML file and access it here: 
    config = kwargs['config']['extensions']['my_extension']
    return config["string_to_print"]

```

Will be accessible from your template at `extensions.YOUR_EXTENSION_NAME`:

```jinja
<em class="extension">
  {{ extensions.my_extension }}
</em>
```

Which results in this output:
```html
<i>"This is my basic extension!"</i>
```


#### Configuring extensions

In your `wrangler.yaml` there's a section for managing your extensions:

```yaml
    # My extension just prints a string... not very exciting!
    my_extension:
        string_to_print: "This is my basic extension!" 
```



### Filters

Wrangler allows you to extend Jinja2 with custom Filters. 

Filters can should go in any file in your lib directory, `lib/`.
They're hooked up via a decorator, aptly named `template_filter`

```python
#lib/filters.py
from wrangler.Core import template_filter
from jinja2 import contextfilter

@template_filter
def my_filter(value):
    return value.lower()
```

If you need access to jinja's `contextfilter` or `envcontextfilter` you
can import them and apply them to your function as well: 

Read more about [jinja2's context filters](http://jinja.pocoo.org/docs/api/#writing-filters)

```python
#lib/filters.py
from wrangler.Core import template_filter
from jinja2 import contextfilter

@template_filter
@contextfilter
def my_filter(context, value):
    print context
    return value
```



