# examples.py
import wrangler.Core as Core
from wrangler.Core import extension, before_render, after_render, load_item, save_item, render_item, template_filter
from jinja2 import contextfilter


# Parser 

# class RestructuredTextParser(Core.Parser):
#     accepts = ["rst"]

#     def interpret(self, file_contents):
#         return rst.load(file_contents)


# Page subclass (assumes you've set a class: MyPage in your page meta)

# class MyPage(Page):
#     def get_content(self):
#         return self.data["data"]
#     def get_metadata(self):
#         return self.data["meta"]



# Hooks

# @before_render
# def before(**kw):
#     nodes = kw['nodes']
#     config = kw['config']
#     renderer = kw['renderer']
#     reporter = kw['reporter']
#     print "Hey, I'm a hook!"
#     return "foo!"

# @after_render
# def after(**kw):
#     nodes = kw['nodes']
#     config = kw['config']
#     renderer = kw['renderer']
#     reporter = kw['reporter']
#     print "Hey, I'm a hook!"
#     return ""


# Extension

# @extension
# def my_extension(sender, **kwargs):
#     # Add some config to your wrangler.yaml file and access it here: 
#     config = kwargs['config']['extensions']['my_extension']
#     return "This is my basic extension!"



# Filters

# @template_filter
# def my_filter(value):
#     return value.lower()

# Filter with jinja2 context

# @template_filter
# @contextfilter
# def my_filter(context, value):
#     print context
#     return value
