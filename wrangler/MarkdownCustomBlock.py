from markdown.extensions import Extension
from markdown import inlinepatterns

from markdown.blockprocessors import BlockProcessor, ListIndentProcessor
from markdown.util import etree

DEL_RE = r'(--)(.*?)--'


class MarkdownCustom(BlockProcessor):

    def test(self, parent, block):
        return bool(self.RE.search(block))

    # def run(self, parent, blocks):
        

class MarkdownCustomBlock(Extension):
    def extendMarkdown(self, md, md_globals):
        """ Add an instance of DefListProcessor to BlockParser. """
        md.parser.blockprocessors.add('deflist', 
                                      MarkdownCustom(md.parser),
                                      '>ulist')


# The markdown library expects this to be here to register the ext.
def makeExtension(configs=None):
    return MarkdownCustomBlock(configs=configs)