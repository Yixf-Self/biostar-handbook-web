"""
Biostar Handbook specific template tags.
"""
from __future__ import print_function, unicode_literals, absolute_import, division
from django import template
from pyblue.templatetags.pytags import markdown

import sys, re, logging, textwrap

try:
    import CommonMark
except ImportError as exc:
    print ("*** Please install CommonMark: pip install commonmark")
    sys.exit()

logger = logging.getLogger('pyblue')

import bleach
from pyblue.templatetags.pytags import load
register = template.Library()

print ("loading template library")

#
# We added a customized Django template tag
# called md anchor that will wraps
# markdown content into
# an html anchor and a back to top link
#
# {% md hello %}
# Hello
# {% endmd %}
# will produce:
#
# <a name="hello">&nbsp</a>
# <p>Hello</p>
# <a href="#top">&laquo; back to top</a>


#
# Based on http://jamie.curle.io/blog/minimal-markdown-template-tag-django/
#

def top_level_only(attrs, new=False):

    if not new:
        return attrs

    text = attrs['_text']
    if not text.startswith(('http:', 'https:')):
        return None

    return attrs

ANCHOR_PATTERN = '<a name="%s"></a>'
TOP_LINK = '<a class="btn btn-default btn-xs btn-info" href="#top">&laquo; back to top</a>'
BACK_LINK = '<a class="btn btn-default btn-xs btn-success" href="javascript: history.go(-1)">&laquo; Go Back</a>'

BOOK_COVER = '''
<a href="https://leanpub.com/biostarhandbook"><img src="../img/cover.png" class="img-responsive {css} col-sm-{size}" alt="book cover"></a>
'''

@register.simple_tag
def top():
    return TOP_LINK

@register.simple_tag
def back():
    return BACK_LINK

@register.simple_tag
def anchor(name):
    return '<a name="%s">&nbsp;</a>' % name

@register.simple_tag
def clearfix():
    return '<div class="clearfix visible-xs-block"></div>'

@register.simple_tag
def cover(size=4, css="pull-right"):
    return BOOK_COVER.format(size=size, css=css)

@register.simple_tag(takes_context=True)
def simplecode(context, pattern):
    text = load(context=context, pattern=pattern)
    html = markdown("```\n{}\n```").format(text)
    return html

@register.simple_tag(takes_context=True)
def path(context, word, text=None):
    start = context['page']
    files = context['files']
    items = filter(lambda x: re.search(word, x.fname, re.IGNORECASE), files)
    items = list(items)
    if not items:
        f = files[0]
        logger.error("link '%s' does not match" % word)
        rpath = "#"
    else:
        f = items[0]
        if len(items) > 1:
            logger.warn("link '%s' matches more than one item: %s" % (word, items))
        rpath = f.relpath(start=start)

    return rpath


class MarkDownNode(template.Node):
    CALLBACKS = [ top_level_only ]
    def __init__(self, nodelist, anchor, title=''):
        self.nodelist = nodelist
        self.anchor = anchor
        self.title = title.replace("'", "")

    def render(self, context):
        text = self.nodelist.render(context)
        if self.title:
            text = "### %s\n\n%s" % (self.title, text)
        #text = markdown(text)
        text = CommonMark.commonmark(text)
        link_anchor = ANCHOR_PATTERN % self.anchor
        text = bleach.linkify(text, callbacks=self.CALLBACKS, skip_pre=True)
        text = link_anchor + text + TOP_LINK
        return text

@register.tag('md')
def markdown_tag(parser, token):
    """
    Enables an extended block of markdown text to be used in a template.

    Syntax::

            {% md anchor title %}
            ## Markdown

            Now you can write markdown in your templates. This is good because:

            * markdown is awesome
            * markdown is less verbose than writing html by hand

            {% endmd %}
    """
    nodelist = parser.parse(('endmd',))
    # need to do this otherwise we get big fail
    elems = token.split_contents()
    anchor = elems[1]
    title = " ".join(elems[2:])
    parser.delete_first_token()
    return MarkDownNode(nodelist, anchor, title)