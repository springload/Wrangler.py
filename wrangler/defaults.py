defaults = {
    "generator_config": {
        "build_cache_file": "var/build.cache",
        "default_template": "base.j2",
        "templates_dir": "templates",
        "compiled_templates_file": "var/jinja",
        "compiled_templates_log": "var/jinja.log",
        "output_file_extension": "html",
        "output_dir": "www",
        "input_dir": "site",
        "data_format": "yaml",
        "ignore": [".", "_"],
        "site_vars":"site_vars",
        "verbose": "false",
        "force": "false",
        "nocache": "false",
        "item_class": "Page",
        "lib_path": "lib",
        "extensions": {
            "sitemap": {
                "webroot":"/"
            },
            "cachebuster": {
            },
            "fileinfo": {
                "directory": "www/assets",
                "filetypes": ["pdf"],
                "webroot": "www"
            }
        }
    },
    "site_vars": {
        "paths": {
            "css": "assets/css",
            "js": "assets/js",
            "assets": "assets",
            "images": "assets/images",
            "webroot": "www",
            "app": "app",
            "content": "content"
        }
    }
}

yaml = """meta:
    title: 'Hello, world!'
    alias: 'Yo, dawg!'
    template: 'template.j2'
    weight: 0
    hide_from_nav: false

data:
    content: "# Hey its some markdown!

        ### All looks good in here


        Just remember to double space everything, since a single
        carriage return means things belong to the same block.


        ---- 


        Features:


        * Markdown parsing

        * More markdown parsing!

        
        ---- 

        Foo

        [I\'m an inline-style link](https://www.google.com)

        ![alt text](https://github.com/adam-p/markdown-here/raw/master/src/common/images/icon48.png \'Logo Title Text 1\')
        "
"""

template = """<!doctype html>
<html>
<head>
    <title>{{ meta.title }}</title>
    <style>
        
        body {
            margin: 0;
            font-family: sans-serif;
            color: #333;
        }

        .content {
            max-width: 38em;
            margin-left: auto;
            margin-right: auto;
            padding-top: 2em;
            padding-bottom: 2em;
            overflow: hidden;
        }
        .data {
            background: #eee;
            color: #444;
            padding: .5em 1em;
        }

        dl dl {
            padding-left: 2em;
        }
    </style>
</head>
<body>
    <div class="content">
        <h1>{{ meta.title }}</h1>

        {% macro iterate(data) %}
            {% for key, val in data.iteritems() recursive %}
                {% if loop.firsrt %}<dl>{% endif %}
                <dt>{{ key }}:</dt>
                <dd>
                    {% if val is mapping %}
                        <dl>
                            {{ loop(val.iteritems()) }}
                        </dl>
                    {% else %}
                        {{ val }}
                    {% endif %}
                </dd>
                {% if loop.last %}</dl>{% endif %}
            {% endfor %}
        {% endmacro %}

        {{ data.content|markdown }}

        <div class="data">
            <h5>These things are available in your templates:</h5>
            <h3>meta</h3>
            {{ iterate(meta) }}
            <h3>data</h3>
            {{ iterate(data) }}
            <h3>site</h3>
            {{ iterate(site) }}
        </div>
        
    </div>
</body>
</html>
"""
