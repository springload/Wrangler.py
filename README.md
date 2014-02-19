# Wrangler

Wrangler is the static site generator for people who aren't building blogs.

Features:
* Deadly stack of awesomeness: Python, YAML, and Jinja2.
* Supports Markdown and RST out of the box, plus custom filters
* Really quick (200 pages, 88 templates in < 3.75 seconds).
* Smart caching, so only the pages you change are re-rendered
* Friendly CLI
* Scalable (will build a 10,000 page site without complaining)
* Used in the real-world 



# Quickstart

Install the wrangler via pip:

```
pip install wrangler
```

Generate a new project

```
wrangler create .
```

Build the little auto-generated blank site:

```
wrangler build content www
```

Serve your sit via an engine of your choice:

```
wrangler serve www
```


# Okay, what did we just do?


## File setup

Wrangler follows a pretty standard filesystem convention:

```bash
my-site/
|--content
|----index.yaml
|--lib
|--templates
|----template.j2
|--var
|--www

```

Check that the `var` directory is writeable, as this is where Wrangler will store the cache. 

To get started, fetch the files out of the `demo` directory. Or, if you can't wait, the obligatory one-liner:


## Options

Save some defaults into your `wrangler.json` config:

Whatever you assign to `site_vars` will be available in the template on the `site` dictionary:

```jinja
{# Hey, it's those handy vars I set in my_custom_site_vars #}
{{ site.paths.css }}
```


## CLI options

```
wrangler build content www
```

### Command line options 

positional arguments:

input_dir             Input directory such as `site/content`
output_dir            Output directory such as `www`

optional arguments:
  -h, --help            show the help message and exits
  -t TEMPLATES_DIR, --templates_dir TEMPLATES_DIR
                        Template directory such as `templates`
  -c CONFIG, --config CONFIG
                        Path to `config.json`
  -o OUTPUT_FILE_EXTENSION, --output_file_extension OUTPUT_FILE_EXTENSION
                        Type of files to output such as `html`
  -d DATA_FORMAT, --data_format DATA_FORMAT
                        Type of files to match in input_dir, such as
                        `json`
  -v, --verbose         Print all the plumbing
  -f, --force           Smash out all the templates regardless of
                        mtime
  -n, --nocache         Turn off data persistence



# Low level stuff

Loads everything from `lib` directory...

## Changing the page object

## Hooks

Hooking is handy for reporting, or modifying elements as they're being
passed around


```python
from blinker import signal

before_render = signal('wranglerBeforeRender')
after_render = signal('wranglerAfterRender')
extension = signal('wranglerExtension')

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

## Extensions

```python
from blinker import signal

extension = signal('wranglerExtension')

@extension.connect
def my_extension(sender, **kwargs):
    return "This is my basic extension!"

```

