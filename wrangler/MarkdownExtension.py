"""
Jinja2 extensions for use Markdown in templates.
"""

import jinja2
import jinja2.ext
import markdown


class MarkdownExtension(jinja2.ext.Extension):
    """
    Block tag for direct code generation from markdown language.

    Original: http://www.silassewell.com/blog/2010/05/10/jinja2-markdown-extension/
    Author: Silas Sewell
    """

    tags = set(['markdown'])

    def __init__(self, environment):
        """
        Jinja2 environvent initialozation.

        :param environment: - page environment;
        :return:            - None.
        """
        super(MarkdownExtension, self).__init__(environment)

    def parse(self, parser):
        """
        Parse template code.

        :param parser:  - Jinja2 parser;
        :return:        - markdown result.
        """
        return False

        if hasattr(self.environment, 'mkdargs'):
            self.environment.extend(
                markdowner=markdown.Markdown(**self.environment.mkdargs))
        else:
            self.environment.extend(
                markdowner=markdown.Markdown())

        lineno = parser.stream.next().lineno
        body = parser.parse_statements(
            ['name:endmarkdown'],
            drop_needle=True
        )
        return jinja2.nodes.CallBlock(
            self.call_method('_markdown_support'),
            [],
            [],
            body
        ).set_lineno(lineno)

    def _markdown_support(self, caller):
        """
        Parse template with markdown.

        :param caller:  - caller of method;
        :return:        - parsed template.
        """
        return self.environment.markdowner.convert(caller()).strip()