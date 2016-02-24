#!/usr/bin/env python
# encoding: utf-8

# The MIT License
#
#  Copyright 2015-2016 University Library Bochum <ottomanhistoriography@ruhr-uni-bochum.de>.
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#  IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#  FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#  AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#  LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#  OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#  THE SOFTWARE.

import urllib
import requests
import secrets
from werkzeug import iri_to_uri
import simplejson as json
import logging
#import time

logging.basicConfig (level=logging.INFO,
    format='%(asctime)s %(levelname)-4s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
)

class Solr(object):
    def __init__(self, host=secrets.SOLR_HOST, port=secrets.SOLR_PORT, application='solr', handler='select',
                 query='*:*', fquery=[], fields=[], writer='python', start='0', rows='10', facet='false',
                 facet_fields=secrets.SOLR_FACETS, facet_mincount=0, facet_limit=10, facet_offset=0, sort='score desc',
                 terms_fl='', terms_limit=10, terms_prefix='', terms_sort='count', mlt=False, mlt_fields=[],
                 omitHeader='false', query_field='', sort_facet_by_index={}, fuzzy='false',
                 compress=False, facet_sort='count', facet_tree=(), spellcheck='false', spellcheck_collate='false',
                 spellcheck_count=5, suggest_query='', group='false', group_field='', group_limit=1,
                 group_sort='score desc', group_ngroups='true', coordinates='0,0', json_nl='arrmap',# cursor='',
                 boost_most_recent='false', csv_separator='\t', core=secrets.SOLR_CORE, stats='false', stats_fl=[],
                 data='', del_id='', export_field='', json_facet={}):
        self.host = host
        self.port = port
        self.application = application
        self.handler = handler
        self.query = query
        self.fquery = fquery
        self.fields = fields
        self.writer = writer
        self.start = start
        self.rows = rows
        self._count = None
        self.sort = sort
        self.facet = facet
        self.facet_fields = facet_fields
        self.facet_mincount = facet_mincount
        self.facet_limit = facet_limit
        self.facet_offset = facet_offset
        self.facet_sort = facet_sort
        self.facet_tree = facet_tree
        self.sort_facet_by_index = sort_facet_by_index
        self.spellcheck = spellcheck
        self.spellcheck_collate = spellcheck_collate
        self.spellcheck_count = spellcheck_count
        self.suggest_query = suggest_query
        self.group = group,
        self.group_field = group_field,
        self.group_limit = group_limit,
        self.group_sort = group_sort,
        self.group_ngroups = group_ngroups,
        self.terms_fl = terms_fl
        self.terms_limit = terms_limit
        self.terms_prefix = terms_prefix
        self.terms_sort = terms_sort
        self.json_nl = json_nl
        self.mlt = mlt
        self.mlt_fields = mlt_fields
        self.omitHeader = omitHeader
        self.compress = compress
        self.coordinates = coordinates
        self.defType = 'edismax'
        self.queryField = query_field
        self.fuzzy = fuzzy
        #self.cursor = cursor
        self.boost_most_recent = boost_most_recent
        self.csv_separator = csv_separator
        self.request_url = ''
        self.core = core
        self.stats = stats
        self.stats_fl = stats_fl
        self.data = data
        self.del_id = del_id
        self.export_field = export_field
        #self.export_dir = export_dir
        self.json_facet = json_facet

    def request(self):
        params = ''
        url = 'http://%s:%s/%s/' % (self.host, self.port, self.application)
        if self.core != '':
            url += '%s/' % self.core
        fuzzy_tilde= ''
        if self.fuzzy == 'true':
            fuzzy_tilde = '~'
        if self.facet == 'true': # Old-style facetting...
            facets = '&facet.field='.join(self.facet_fields)
            params = '%s?q=%s%s&wt=%s&start=%s&rows=%s&facet.limit=%s&facet.mincount=%s&facet.offset=%s&facet.field=%s&json.nl=%s&facet=%s&facet.sort=%s&omitHeader=%s&defType=%s&facet.threads=-1' % (
                self.handler, self.query, fuzzy_tilde, self.writer, self.start, self.rows, self.facet_limit,
                self.facet_mincount, self.facet_offset, facets, self.json_nl, self.facet, self.facet_sort,
                self.omitHeader, self.defType)
            if self.boost_most_recent == 'true':
                params += '&boost=recip(ms(NOW/YEAR,year_boost),3.16e-11,1,1)'
            # params = '%s/%s?q=%s%s&wt=%s&start=%s&rows=%s&facet.limit=%s&facet.mincount=%s&facet.offset=%s&facet.field=%s&json.nl=%s&facet=%s&facet.sort=%s&omitHeader=%s&defType=%s' % (
            #     self.application, self.handler, self.query, fuzzy_tilde, self.writer, self.start, self.rows, self.facet_limit,
            #     self.facet_mincount, self.facet_offset, facets, self.json_nl, self.facet, self.facet_sort,
            #     self.omitHeader, self.defType)
            if len(self.sort_facet_by_index) > 0:
                for sortfield in self.sort_facet_by_index:
                    params += '&f.%s.facet.sort=homepage&f.%s.facet.limit=-1' % (
                        sortfield, sortfield)# Stupid hack until SOLR-1672 gets fixed
            # Pivot needs a mincount of 0 for empty categories. Build mincounts of 1 for normal facets...
            for myfacet in self.facet_fields:
                params += '&f.%s.facet.mincount=1' % myfacet
            if len(self.facet_tree) > 0:
                params += '&facet.pivot='
                for field in self.facet_tree:
                    #params += '&facet.pivot=%s,%s' % (self.facet_tree[0], self.facet_tree[1])
                    params += '%s,' % field
                params = params[:-1]
        else:
            params = '%s?q=%s%s&wt=%s&start=%s&rows=%s&json.nl=%s&omitHeader=%s&defType=%s' % (
                self.handler, self.query, fuzzy_tilde, self.writer, self.start, self.rows, self.json_nl,
                self.omitHeader, self.defType)
            if self.boost_most_recent == 'true':
                params += '&boost=recip(ms(NOW/YEAR,year_boost),3.16e-11,1,1)'
            if self.writer == 'csv':
                params += '&csv.separator=%s' % self.csv_separator
            #logging.info(self.json_facet)
            if self.json_facet:
                params += '&json.facet=%s' % (json.dumps(self.json_facet))
        if len(self.fquery) > 0:
            for fq in (self.fquery):
                try:
                    #params += '&fq=%s' % urllib.parse.unquote(fq.encode('utf8'))
                    params += '&fq=%s' % urllib.parse.unquote(fq)
                except UnicodeDecodeError:
                    params += '&fq=%s' % urllib.parse.unquote(fq)
        if self.sort:
            #if self.cursor:
                #params += '&sort=katkey+asc&cursorMark=%s' % self.cursor
            #elif self.sort != 'score desc':
            if self.sort != 'score desc':
                params += '&sort=%s' % self.sort
        if len(self.fields) > 0:
            if self.application == 'elevate':
                self.fields.append('[elevated]')
            params += '&fl=%s' % '+'.join(self.fields)
        if self.mlt is True:
            self.facet = 'false'
            mparams = '%s?q=%s&mlt=true&mlt.fl=%s&mlt.count=10&fl=%s&wt=%s&defType=%s' % (
                self.handler, self.query, '+'.join(self.mlt_fields), '+'.join(self.fields),
                self.writer, self.defType)
            # if self.boost_most_recent == 'true':
            #     params += '&boost=recip(ms(NOW/YEAR,year_boost),3.16e-11,1,1)'
            #self.response = eval(urllib.request.urlopen('%s%s' % (url, mparams)).read())
            #logging.info(url)
            #logging.info(mparams)
            self.response = eval(requests.get('%s%s' % (url, mparams)).text)
            for mlt in self.response.get('moreLikeThis'):
                self.mlt_results = self.response.get('moreLikeThis').get(mlt).get('docs')
        if self.spellcheck == 'true':
            params += '&spellcheck=true&spellcheck.collate=%s&spellcheck.count=%s' % (
                self.spellcheck_collate, self.spellcheck_count)
        if self.group[0] == 'true':
            params += '&group=true&group.field=%s&group.limit=%s&group.sort=%s&group.ngroups=%s' % (
                self.group_field[0], self.group_limit[0], self.group_sort[0], self.group_ngroups[0])
        if self.coordinates != '0,0':
            try:
                params += '&pt=%s&sfield=geolocation&fl=*+dist_:geodist()' % self.coordinates
            except UnicodeDecodeError:
                params += '&pt=%s&sfield=geolocation&fl=*+dist_:geodist()' % self.coordinates.decode('utf8')
        if self.queryField:
            params += '&qf=%s' % self.queryField
        if self.stats == 'true':
            params += '&stats=true&stats.field=' + '&stats.field='.join(self.stats_fl)
        params += '&q.op=AND'

        self.request_url = '%s%s' % (url, params)
        #logging.fatal(iri_to_uri(self.request_url))
        if self.compress == True:
            import urllib2
            import StringIO
            import gzip

            request = urllib2.Request(iri_to_uri(self.request_url))
            request.add_header('Accept-encoding', 'gzip')
            opener = urllib2.build_opener()
            compresseddata = opener.open(request).read()
            compressedstream = StringIO.StringIO(compresseddata)
            gzipper = gzip.GzipFile(fileobj=compressedstream)

            self.response = eval(gzipper.read())
        else:
            #logging.error(self.request_url)
            try:
                #self.response = eval(urllib.request.urlopen(iri_to_uri(self.request_url)).read())
                self.response = eval(requests.get(iri_to_uri(self.request_url)).text)
            except NameError:
                #self.response = urllib.request.urlopen(iri_to_uri(self.request_url)).read()
                self.response = requests.get(iri_to_uri(self.request_url)).text
            except SyntaxError:
                #self.response = urllib.request.urlopen(iri_to_uri(self.request_url)).read()
                self.response = requests.get(iri_to_uri(self.request_url)).text
            #self.response = eval(urllib.request.urlopen(self.request_url).read())
        #logging.error(self.response)
        try:
            self.results = self.response.get('response').get('docs')
        except AttributeError: # Grouped results...
            #logging.fatal(e)
            #logging.error(self.response)
            try:
                if self.response.get('grouped'):
                    self.results = self.response.get('grouped').get(self.group_field[0]).get('groups')
            except AttributeError:
                pass
        if self.facet == 'true':
            self.facets = self.response.get('facet_counts').get('facet_fields')
        if len(self.facet_tree) > 0:
            self.tree = self.response.get('facet_counts').get('facet_pivot')
        if self.json_facet:
            #logging.info(self.response.get('facets'))
            self.facets = self.response.get('facets')
        if self.spellcheck == 'true' or self.handler.endswith('suggest'):
            try:
                self.suggestions = self.response.get('spellcheck').get('suggestions')
            except AttributeError:
                pass
        if self.omitHeader != 'true':
            self.qtime = float(self.response.get('responseHeader').get('QTime')) / 1000
            #logging.error(self.qtime)

    def suggest(self):
        url = 'http://%s:%s/%s/' % (self.host, self.port, self.application)
        if self.core != '':
            url += '%s/' % self.core
        params = '%s?spellcheck.q=%s&wt=%s&json.nl=%s&omitHeader=%s' % (self.handler,
                                                                           urllib.urlencode(
                                                                               self.suggest_query),
                                                                           self.writer, self.json_nl, self.omitHeader)
        self.request_url = '%s%s' % (url, params)
        #self.response = eval(urllib.request.urlopen(iri_to_uri(self.request_url)).read())
        self.response = eval(requests.get(iri_to_uri(self.request_url)).text)
        self.suggestions = self.response.get('spellcheck').get('suggestions')

    def terms(self):
        url = 'http://%s:%s/%s/' % (self.host, self.port, self.application)
        if self.core != '':
            url += '%s/' % self.core
        params = '%s?terms.fl=%s&terms.limit=%s&terms.sort=%s&wt=%s&json.nl=%s&omitHeader=%s' % (
            self.handler, self.terms_fl, self.terms_limit, self.terms_sort, self.writer, self.json_nl,
            self.omitHeader)
        if self.terms_prefix:
            params += '&terms.prefix=%s' % self.terms_prefix
        self.request_url = '%s%s' % (url, params)
        #self.response = eval(urllib.request.urlopen(self.request_url).read())
        self.response = eval(requests.get(self.request_url).text)
        self.results = self.response.get('terms').get(self.terms_fl)

    def count(self):
        if self._count is None:
            try:
                self._count = int(self.response.get('response').get('numFound'))
            except AttributeError:
                self._count = int(self.response.get('grouped').get(self.group_field[0]).get('ngroups'))
                #logging.error(self._count)
        return self._count

    def update(self):
        url = 'http://%s:%s/%s/%s/update/?commit=true&versions=true' % (self.host, self.port, self.application, self.core)
        resp = requests.post(url, headers={'Content-type': 'application/json'}, data=json.dumps(self.data))
        return resp

    def delete(self):
        url = 'http://%s:%s/%s/%s/update?commit=true' % (self.host, self.port, self.application, self.core)
        resp = requests.post(url, headers={'Content-type': 'application/json'}, data=json.dumps({'delete': {'id': self.del_id}}))
        return resp.status_code

    def export(self):
        done = False
        cm = '*'
        export_docs = []
        while not done:
            resp = requests.get('http://%s:%s/%s/%s/query?q=*:*&sort=id asc&fl=%s&cursorMark=%s' % (self.host, self.port, self.application, self.core, self.export_field, cm)).json()
            for doc in resp.get('response').get('docs'):
                export_docs.append(json.loads(doc.get(self.export_field)))
            if cm == resp.get('nextCursorMark'):
                done = True
            cm = resp.get('nextCursorMark')

        #with open('%s/%s_%s.json' % (self.export_dir, self.core, int(time.time())), 'w') as dumpfile:
            #json.dump(export_docs, dumpfile, indent=4)

        #return '%s/%s_%s.json' % (self.export_dir, self.core, int(time.time()))
        return export_docs

    def __len__(self):
        return len(self.results)

    def __repr__(self):
        myrepr = 'REQUEST_URL: %s' % self.request_url
        if self.response:
            import pprint

            pretty_result = pprint.PrettyPrinter(indent=2)
            pretty_result.pformat(self.response)
            myrepr += 'RESPONSE: %s' % pretty_result
        return myrepr