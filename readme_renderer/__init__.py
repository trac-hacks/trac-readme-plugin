from genshi.filters import Transformer
from genshi.core import Stream
from trac.core import Component, implements
from trac.mimeview.api import (
    IHTMLPreviewRenderer, Mimeview, content_to_unicode)
from trac.util.text import to_unicode
from trac.util.html import Markup, html as tag
from trac.web.api import ITemplateStreamFilter
from trac.web.chrome import ITemplateProvider, add_script, add_stylesheet


class ReadmeRendererPlugin(Component):
    implements(ITemplateStreamFilter, ITemplateProvider, IHTMLPreviewRenderer)

    # http://tools.ietf.org/html/draft-ietf-appsawg-text-markdown-01
    # http://tools.ietf.org/html/draft-seantek-text-markdown-media-type-00
    def get_quality_ratio(self, mimetype):
        if mimetype in ('text/markdown', 'text/x-markdown',
                        'text/x-web-markdown',
                        'text/vnd.daringfireball.markdown'):
            return 8
        return 0

    def render(self, context, mimetype, content, filename=None, url=None):
        self.log.debug("Using Markdown Mimeviewer")
        req = context.req
        add_stylesheet(req, 'readme/readme.css')
        content = content_to_unicode(self.env, content, mimetype)
        # for some insane reason genshi will only preserve whitespace of
        # <pre> elements, trac calls Stream.render() inappropriately.
        return tag.pre(content.encode('utf-8'))

    def filter_stream(self, req, method, template, stream, data):
        if template != 'browser.html':
            return stream
        dir_listing = bool(data.get('dir'))
        if dir_listing or data['path'].endswith('.md'):
            add_script(req, 'readme/marked.js')
            add_script(req, 'readme/readme.js')
        if dir_listing:
            stream = self._render_readme(req, stream, data)
        return stream

    def get_templates_dirs(self):
        return []

    def get_htdocs_dirs(self):
        from pkg_resources import resource_filename
        return [('readme', resource_filename(__name__, 'htdocs'))]

    def _render_readme(self, req, stream, data):
        add_stylesheet(req, 'common/css/code.css')

        repos = data.get('repos') or self.env.get_repository()
        rev = req.args.get('rev', None)

        # Rendering all READMEs in a directory preview
        for entry in data['dir']['entries']:
            try:
                if not entry.isdir and entry.name.lower().startswith('readme'):
                    node = repos.get_node(entry.path, rev)
                    req.perm(data['context'].resource).require('FILE_VIEW')
                    mimeview = Mimeview(self.env)
                    content = node.get_content()
                    mimetype = node.content_type
                    divclass = 'searchable'
                    if entry.name.lower().endswith('.wiki'):
                        mimetype = 'text/x-trac-wiki'
                        divclass = 'searchable wiki'
                    elif entry.name.lower().endswith('.md'):
                        mimetype = 'text/x-markdown'
                        divclass = 'searchable markdown'
                    if not mimetype or mimetype == 'application/octet-stream':
                        mimetype = mimeview.get_mimetype(
                            node.name, content.read(4096)) or \
                            mimetype or 'text/plain'
                    del content
                    self.log.debug(
                        "ReadmeRenderer: rendering node %s@%s as %s",
                        node.name, rev, mimetype)
                    output = mimeview.preview_data(
                        data['context'],
                        node.get_content(),
                        node.get_content_length(),
                        mimetype,
                        node.created_path,
                        '',
                        annotations=[],
                        force_source=False)

                    if output:
                        if isinstance(output['rendered'], Stream):
                            content = output['rendered'].select('.')
                        else:
                            content = output['rendered']
                        insert = tag.div(
                            tag.h1(entry.name,
                                   tag.a(Markup(' &para;'),
                                         class_="anchor",
                                         href='#' + entry.name,
                                         title='Link to file'),
                                   id_=entry.name),
                            tag.div(content,
                                    class_=divclass,
                                    title=entry.name),
                            class_="readme",
                            style="padding-top: 1em;"
                        )
                        xpath = "//div[@id='content']/div[@id='help']"
                        stream |= Transformer(xpath).before(insert)
            except Exception, e:
                self.log.debug(to_unicode(e))
        return stream
