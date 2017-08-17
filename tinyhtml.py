#!/usr/bin/env python
#
# https://github.com/nochkin/tinyhtml
#

VERSION = '0.3'

import re, sys, os, shutil
import xml.dom.pulldom as pulldom

try:
    import Queue as queue
    import HTMLParser as htmlparser
except ImportError:
    import queue
    import html.parser as htmlparser

HTML_EXTS = ('', 'tpl', 'html', 'htm')

class THTML(htmlparser.HTMLParser):
    def __init__(self):
        htmlparser.HTMLParser.__init__(self)
        self._output = []
        self._short_tag = False
        self._tag_attr = False
        self._data = ''
        self._current_tag = queue.LifoQueue()

    def _add_data(self):
        if self._data:
            if self._current_tag.qsize() and (not self._current_tag.queue[-1] in ('script','pre','textarea','style')):
                self._data = re.sub('\s{2,}', ' ', self._data)
                self._data = self._data.rstrip('\n')
            if self._data and (not self._data in ('\n', ' ')):
                self._output.append(self._data)
            self._data = ''

    def handle_starttag(self, tag, attrs):
        self._short_tag = True
        self._tag_attr = len(attrs)
        self._add_data()
        self._current_tag.put(tag)
        if tag in ('script', 'div'):
            self._short_tag = False
        tag_attrs = []
        for attr_key, attr_val in attrs:
            if attr_val and (' ' in attr_val or '=' in attr_val):
                attr_val = re.sub('\s{2,}', ' ', attr_val)
                attr_val = '"%s"' % attr_val
            if attr_val is None:
                tag_attrs.append(attr_key)
            else:
                if attr_val == '':
                    attr_val='""'
                tag_attrs.append('%s=%s' % (attr_key, attr_val))
        tag_string = '<%s' % tag
        if tag_attrs:
            tag_string += ' %s' % ' '.join(tag_attrs)
        tag_string += '>'
        self._output.append(tag_string)

    def handle_endtag(self, tag):
        data_empty = True
        if self._data: data_empty = False
        self._add_data()
        self._current_tag.get()
        if self._short_tag:
            tag_end = '/>'
            if self._tag_attr and (not self._output[-1][-2] == '"'):
                tag_end = ' />'
            self._output[-1] = self._output[-1][:-1] + tag_end
        else:
            if data_empty:
                self._output[-1] += '</%s>' % tag
            else:
                self._output.append('</%s>' % tag)
        self._short_tag = False
        self._tag_attr = False

    def handle_data(self, data):
        self._short_tag = False
        self._data += data

    def close(self):
        self._raw = ''
        for out in self._output:
            if not out.startswith('<'):
                self._raw = self._raw.rstrip('\n')
                self._raw += out
            else:
                self._raw += out + '\n'
        return self._raw

class AllEntities:
    def __getitem__(self, key):
        return key

def usage():
    print("""%(prg)s version %(version)s
Usage: %(prg)s filein.htm fileout.htm""" % {'version': VERSION, 'prg': os.path.basename(sys.argv[0])})
    return 2

if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(usage())

    (html_file_in, html_file_out) = sys.argv[1:3]
    if not os.path.isfile(html_file_in):
        sys.exit(1)

    if os.path.splitext(html_file_in)[1][1:] in HTML_EXTS:
        f1 = open(html_file_in, 'r')
        html_data = f1.read()
        f1.close()

        parser = THTML()
        parser.feed(html_data)
        html = parser.close()

        f1 = open(html_file_out, 'w')
        f1.write(html)
        f1.close()
    else:
        shutil.copy(html_file_in, html_file_out)

