# Wrangler

Wrangler is a static site generator for people who aren't building blogs.

Features:
* Deadly stack of awesomeness: Python, YAML, and Jinja2.
* Supports Markdown and RST out of the box, plus custom filters
* Really quick (200 pages, 88 templates in < 4 seconds).
* Smart caching, so only the pages you change are re-rendered
* Friendly CLI
* Scalable (will happily build a 10,000 page site without complaining)
* Used in the real-world 


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

Serve your site via an engine of your choice, or the handy built-in server:

```
wrangler serve www
```

Want to watch your content and templates for changes and automatically re-build them?
Easy, just call `watch`. The watch task takes all the same options as `build`. 

```
wrangler watch content www
```


# Okay, that works, but what did we just do?

## Files

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


## Configuration

The editable options for the wrangler are saved in the `wrangler.json` file in your project root.

Crack it open, and you'll find three nodes: `wrangler`, `site` and `extensions`

### wrangler
This contains the core configuration. The heavy lifting. The hard-core stuff.



### extensions
Configures any extensions you've got set up. Three default extensions are included, `sitemap`, `fileinfo`, and `cachebuster`


### site
Site vars are available inside your templates as children of the `site` object. For instance, to get the 
images path, you can call `{{ site.paths.images }}` and save yourself some typing. 

```jinja
{# Hey, it's those handy vars I set in my site_vars #}
{{ site.paths.css }}
```



# Command line options

## wrangler create

Takes a single positional argument, the path in which to create your new project:
```bash
cd my-sweet-site && wrangler create .

# or 
wrangler create my-sweet-site

```


## wrangler build

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


## wrangler watch

Has all the same options as `wrangler build`

Print all the plumbing every time a file changes:

```bash
wrangler watch content www --verbose
```


## wrangler serve

Accepts one positional argument (the directory to serve) and an optional `--port` (default 8000).

```bash
wrangler serve www --port 8001
```


## wrangler clean

Remove the template cache and the object cache from the 'var' directory.

```bash
wrangler clean
```

# Working with your content

Setting up page metadata

Nav options, etc




# Under the hood

## The page class

Wrangler loads all the python modules found in your project's `lib` directory. This lets you do things like
replace the default `Page` object with one of your own:

```python
# lib/Page.py
import wrangler.Core as wrangler

class Page(wrangler.Page):
  def get_properties(self):
    print "Hey, I'm a custom page instance!"
    return {

    }

```


## Content parsers
If you look in your `wrangler.yaml` file, you'll notice it accepts three file types: `["yaml", "json", "md"]`

Wrangler includes three parsers by default, `Yaml`, `Markdown` and `Json`, which consume the input files and
represent them as meaningful data.

What's meaningful to wrangler? Any dict with a `meta` and `data` key:
```
data = {
  "meta": {
    "title": "A page"
    "template": "content.j2"
  },
  "data": {
    "content": "page content here..."
  }
}
```


## Hooks and extensions

Wrangler uses [blinker](http://blinker.pypi.org)'s signals for processing hooks and extensions.

### Hooks

Hooks are signals that are fired at critical points in the render process.
They're proccessed in the order they appear in your modules, and can modify the
incoming objects directly. They've also got access to wrangler's `config`, `renderer` and `reporter`. 



```python
from blinker import signal

before_render = signal('wranglerBeforeRender')
after_render = signal('wranglerAfterRender')

# More hooks:
# wranglerLoadItem
# wranglerBeforeSaveItem
# wranglerOnSaveItem
# wranglerRenderItem

@before_render.connect
def my_hook(sender, **kwargs):
    nodes = kw['nodes']
    config = kw['config']
    renderer = kw['renderer']
    reporter = kw['reporter']
    return "This is my basic hook!"

```

### Extensions

Extensions are python scripts that return handy data to your templates `extensions` dictionary in your templates.

For instance, this banal script:

```python
# lib/my_extensions.py
from blinker import signal

extension = signal('wranglerExtension')

@extension.connect
def my_extension(sender, **kwargs):
    return "This is my basic extension!"

```
Lets you do this in your template:

```jinja
<em class="extension">
  {{ extensions.my_extension }}
</em>
```

Which results in this output:
```html
<i>"This is my basic extension!"</i>
```


### Filters

Wrangler allows you to extend Jinja2 with custom Filters. 

Filters can should go in any file in your lib directory, `lib/`.
They're hooked up via a decorator, aptly named `template_filter`

```
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

```
#lib/filters.py
from wrangler.Core import template_filter
from jinja2 import contextfilter

@template_filter
@contextfilter
def my_filter(context, value):
    print context
    return value
```



