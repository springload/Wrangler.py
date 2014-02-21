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
        - "wow, so much content! "
```

#### JSON (.js, .json)

```json
{
    "meta": {
        "title": "My title"
        "template": "template.j2"
        "description": "My cool page!"
    },
    "data": {
        content: "Here's some page content!"
        blocks: [
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
meta:
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


## Metadata options

Use the metadata for anything related to the page. You can throw whatever you like in here,
but there's a few reserved words:

```
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
**mtile**               The modified time. You could use this to build a blog timestamp, for instance.
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
when you're dealing with more structured data. For YAML and JSON files, access parts of the `data` dictionary:

```jinja
<div class="content">
{{ data.content }}
{% for block in data.blocks %}
    <p>{{ block }}</p>
{% endfor %}
</div>
```




## Configuration

The editable options for the wrangler are saved in the `wrangler.yaml` file in your project root.

Crack it open, and you'll find three nodes: `wrangler`, `site` and `extensions`

### wrangler
This contains the core configuration. The heavy lifting. The hard-core stuff.


### extensions
Configure any extensions you've set up here. Extensions let you run any python function you want, and inject
the results into your templates. Read more in the extensions section.



```jinja
{{ extensions.cachebuster }}
```

Some default extensions are included: `sitemap`, `fileinfo`, and `cachebuster`


### site
Site vars are available inside your templates as children of the `site` object. For instance, to get the 
images path, you can call `{{ site.paths.images }}` and save yourself some typing. 

```jinja
{# Hey, it's those handy vars I set in my site_vars #}
{{ site.paths.css }}
```

The yaml file documents all the options and what they do. 



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

TODO: make these better

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



