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

import logging
import uuid
import base64
import datetime
import re
import requests
import simplejson as json
import wtforms_json
import time

try:
    import site_secrets as secrets
except ImportError:
    import secrets

from flask import Flask, render_template, redirect, request, jsonify, flash, url_for, Markup, Response, send_file
from flask.ext.babel import Babel, lazy_gettext, refresh, gettext
from flask.ext.bootstrap import Bootstrap
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required, make_secure_token, AnonymousUserMixin
from flask.ext.paginate import Pagination
from flask_humanize import Humanize
from flask_wtf.csrf import CsrfProtect
from urllib import parse
from solr_handler import Solr
from datadiff import diff_dict
from multiprocessing import Pool
from io import BytesIO
#from werkzeug import secure_filename

from forms import *
from config import LANGUAGES

logging.basicConfig (level=logging.INFO,
    format='%(asctime)s %(levelname)-4s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
)

app = Flask(__name__)
app.debug = True
app.testing = True
app.secret_key = secrets.secret

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'

babel = Babel(app)
humanize_filter = Humanize(app)

bootstrap = Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

csrf = CsrfProtect(app)

wtforms_json.init()

FORM_COUNT_RE = re.compile('-\d+$')

PUBTYPE2FORM = {
    'ArticleJournal': ArticleJournalForm,
    'Monograph': MonographForm,
    'Print': PrintForm,
    'Chapter': ChapterForm,
    'Translation': TranslationForm,
    'Conference': ConferenceForm,
    'Collection': CollectionForm,
    'Other': OtherForm,
    'Catalogue': CatalogueForm,
    'Edition': EditionForm,
    'InternetDocument': InternetDocumentForm,
    'Journal': JournalForm,
    'Lecture': LectureForm,
    'Codex': CodexForm,
    'Series': SeriesForm,
    'CodexChapter': CodexChapterForm,
    'PrintChapter': PrintChapterForm,
}

@app.template_filter('rem_form_count')
def rem_form_count_filter(mystring):
    '''Remove trailing form counts to display only categories in FormField/FieldList combinations.'''
    return FORM_COUNT_RE.sub('', mystring)

@app.template_filter('mk_time')
def mk_time_filter(mytime):
    return datetime.datetime.strptime(mytime, '%Y-%m-%d %H:%M:%S.%f')

@app.template_filter('last_split')
def last_split_filter(category):
    return category.rsplit('-', 1)[1]

@app.template_filter('deserialize_json')
def deserialize_json_filter(thejson):
    return json.loads(thejson)

def theme(ip):
    # logging.info(ip[0])
    site = ''
    # For the moment we only use the Bochum theme
    site = 'bochum'
    # if ip[0].startswith('127.0.0.1' or ip[0].startswith('134.147')):
    #     site = 'bochum'
    # elif ip[0].startswith('129.217'):
    #     site = 'dortmund'
    # logging.info(site)
    return site

def _diff_struct(a, b):
    diffs = ''
    for line in str(diff_dict(a, b)).split('\n'):
        if line.startswith('-'):
            line = line.lstrip('-')
            try:
                cat, val = line.split(': ')
                if val != "''," and cat != "'changed'":
                    diffs += Markup('<b>%s</b>: %s<br/>' % (cat.strip("'"), val.rstrip(',').strip("'")))
            except ValueError:
                pass
    return diffs

@humanize_filter.localeselector
@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES)


@app.route('/')
@app.route('/index')
def index():
    #logging.error(current_user)
    resp = {}
    numFound = 0
    records = []
    if current_user.is_authenticated:
        #resp = requests.get(
            #'http://127.0.0.1:8983/solr/hb2/query?q=*:*&fq=owner:%s&wt=json&json.nl=arrmap' % current_user.id).json()
        index_solr = Solr(core='hoe', sort='created desc')
        index_solr.request()

        #logging.info(resp)
        numFound = index_solr.count()
        records = index_solr.results
        if numFound == 0:
            flash(lazy_gettext("You haven't registered any records with us yet. Please do so now..."), 'danger')

    return render_template('index.html', header=lazy_gettext('Home'), site=theme(request.access_route), numFound=numFound, records=records)

@app.route('/contact')
def contact():
    return redirect('mailto:%s' % secrets.contact_mail)

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash('Error in the %s field: %s' % (getattr(form, field).label.text, error), 'error')

PUBTYPE2TEXT = {
    'ArticleJournal': lazy_gettext('Article in Journal'),
    'Catalogue': lazy_gettext('Catalogue'),
    'Chapter': lazy_gettext('Chapter'),
    'CodexChapter': lazy_gettext('Chapter in Codex'),
    'PrintChapter': lazy_gettext('Chapter in Print'),
    'Codex': lazy_gettext('Codex'),
    'Collection': lazy_gettext('Collection'),
    'Conference': lazy_gettext('Conference'),
    'Edition': lazy_gettext('Edition'),
    'InternetDocument': lazy_gettext('Internet Document'),
    'Journal': lazy_gettext('Journal'),
    'Lecture': lazy_gettext('Lecture'),
    'Monograph': lazy_gettext('Monograph'),
    'Print': lazy_gettext('Print'),
    'Series': lazy_gettext('Series'),
    'Translation': lazy_gettext('Translation'),
    'Other': lazy_gettext('Other'),
}

SUBTYPE2TEXT = {
    'facsimile': lazy_gettext('Facsimile'),
    'festschrift': lazy_gettext('Festschrift'),
    'lexicon': lazy_gettext('Lexicon'),
    'afterword': lazy_gettext('Afterword'),
    'introduction': lazy_gettext('Introduction'),
    'lexicon_article': lazy_gettext('Article in Lexicon'),
    'review': lazy_gettext('Review'),
    'translation': lazy_gettext('Translation'),
}

GENRE2TEXT = {
    #, , , chronicle,
    'apocalypse': lazy_gettext('Apocalypse'),
    'artifact': lazy_gettext('Artifact'),
    'autobiography': lazy_gettext('Autobiography'),
    'cartulary': lazy_gettext('Cartulary'),
    'chronicle': lazy_gettext('Chronicle'),
    'church_chronicle': lazy_gettext('Church Chronicle'),
    'chronograph': lazy_gettext('Chronograph'),
    'cosmography': lazy_gettext('Cosmography'),
    'encomium': lazy_gettext('Encomium'),
    'false_document': lazy_gettext('False Document'),
    'hagiography': lazy_gettext('Hagiography'),
    'history': lazy_gettext('History'),
    'hoe': lazy_gettext('History of the Ottoman Emperors'),
    'legend': lazy_gettext('Legend'),
    'letter': lazy_gettext('Letter'),
    'memoirs': lazy_gettext('Memoirs'),
    'memorandum': lazy_gettext('Memorandum'),
    'mirror': lazy_gettext('Mirror of princes'),
    'panegyric': lazy_gettext('Panegyric'),
    'parenesis': lazy_gettext('Parenesis'),
    'poem': lazy_gettext('Poem'),
    'polemic': lazy_gettext('Polemic'),
    'prophesy': lazy_gettext('Prophesy'),
    'proskynetarion': lazy_gettext('Proskynetarion'),
    'psalter': lazy_gettext('Psalter'),
    'threnody': lazy_gettext('Threnody'),
    'verse_chronicle': lazy_gettext('Verse Chronicle'),
    'vita': lazy_gettext('Vita'),
    'other': lazy_gettext('Other')
}

SOURCE_CLASS_MAP = {
    'Codex': lazy_gettext('Primary Literature'),
    'Print': lazy_gettext('Primary Literature'),
    'CodexChapter': lazy_gettext('Primary Literature'),
    'PrintChapter': lazy_gettext('Primary Literature'),
    'Catalogue': lazy_gettext('Primary Literature'),
    'Edition': lazy_gettext('Primary Literature'),
    'Translation': lazy_gettext('Primary Literature'),
    'ArticleJournal': lazy_gettext('Secondary Literature'),
    'Chapter': lazy_gettext('Secondary Literature'),
    'Monograph': lazy_gettext('Secondary Literature'),
    'Conference': lazy_gettext('Secondary Literature'),
    'Collection': lazy_gettext('Secondary Literature'),
    'Series': lazy_gettext('Secondary Literature'),
    'Journal': lazy_gettext('Secondary Literature'),
    'InternetDocument': lazy_gettext('Secondary Literature'),
    'Lecture': lazy_gettext('Secondary Literature'),
    'Other': lazy_gettext('Secondary Literature'),
}

ROLE_MAP = {
    'ann': lazy_gettext('Annotator'),
    'aut': lazy_gettext('Author'),
    'aft': lazy_gettext('Author of Afterword'),
    'aui': lazy_gettext('Author of Introduction'),
    'ato': lazy_gettext('Autographer'),
    'bnd': lazy_gettext('Binder'),
    'dte': lazy_gettext('Dedicatee'),
    'dto': lazy_gettext('Dedicator'),
    'edt': lazy_gettext('Editor'),
    'fmo': lazy_gettext('Former Owner'),
    'hnr': lazy_gettext('Honoree'),
    'his': lazy_gettext('Host institution'),
    'ill': lazy_gettext('Illuminator'),
    'ive': lazy_gettext('Interviewee'),
    'ivr': lazy_gettext('Interviewer'),
    'pat': lazy_gettext('Patron'),
    'prt': lazy_gettext('Printer'),
    'scr': lazy_gettext('Scribe'),
    'spk': lazy_gettext('Speaker'),
    'trl': lazy_gettext('Translator'),
}

LANGUAGE_MAP = {
    'alb': lazy_gettext('Albanian'),
    'ara': lazy_gettext('Arabic'),
    'bos': lazy_gettext('Bosnian'),
    'bul': lazy_gettext('Bulgarian'),
    'hrv': lazy_gettext('Croatian'),
    'dut': lazy_gettext('Dutch'),
    'eng': lazy_gettext('English'),
    'fre': lazy_gettext('French'),
    'ger': lazy_gettext('German'),
    'grc': lazy_gettext('Ancient Greek'),
    'gre': lazy_gettext('Modern Greek'),
    'ita': lazy_gettext('Italian'),
    'lat': lazy_gettext('Latin'),
    'peo': lazy_gettext('Persian'),
    'pol': lazy_gettext('Polish'),
    'rum': lazy_gettext('Romanian'),
    'rus': lazy_gettext('Russian'),
    'srp': lazy_gettext('Serbian'),
    'spa': lazy_gettext('Spanish'),
    'tur': lazy_gettext('Turkish'),
}

NO_TR_PUBTYPE2TEXT = {
    'ArticleJournal': 'Article in Journal',
    'Catalogue': 'Catalogue',
    'Chapter': 'Chapter',
    'CodexChapter': 'Chapter in Codex',
    'PrintChapter': 'Chapter in Print',
    'Codex': 'Codex',
    'Collection': 'Collection',
    'Conference': 'Conference',
    'Edition': 'Edition',
    'InternetDocument': 'Internet Document',
    'Journal': 'Journal',
    'Lecture': 'Lecture',
    'Monograph': 'Monograph',
    'Print': 'Print',
    'Series': 'Series',
    'Translation': 'Translation',
    'Other': 'Other',
}

NO_TR_SUBTYPE2TEXT = {
    'facsimile': 'Facsimile',
    'festschrift': 'Festschrift',
    'lexicon': 'Lexicon',
    'afterword': 'Afterword',
    'introduction': 'Introduction',
    'lexicon_article': 'Article in Lexicon',
    'review': 'Review',
    'translation': 'Translation',
}

NO_TR_GENRE2TEXT = {
    'apocalypse': 'Apocalypse',
    'artifact': 'Artifact',
    'autobiography': 'Autobiography',
    'cartulary': 'Cartulary',
    'chronicle': 'Chronicle',
    'church_chronicle': 'Church Chronicle',
    'chronograph': 'Chronograph',
    'cosmography': 'Cosmography',
    'encomium': 'Encomium',
    'false_document': 'False Document',
    'hagiography': 'Hagiography',
    'history': 'History',
    'hoe': 'History of the Ottoman Emperors',
    'legend': 'Legend',
    'letter': 'Letter',
    'memoirs': 'Memoirs',
    'memorandum': 'Memorandum',
    'mirror': 'Mirror of princes',
    'panegyric': 'Panegyric',
    'parenesis': 'Parenesis',
    'poem': 'Poem',
    'polemic': 'Polemic',
    'prophesy': 'Prophesy',
    'proskynetarion': 'Proskynetarion',
    'psalter': 'Psalter',
    'threnody': 'Threnody',
    'verse_chronicle': 'Verse Chronicle',
    'vita': 'Vita',
    'other': 'Other'
}

NO_TR_SOURCE_CLASS_MAP = {
    'Codex': 'Primary Literature',
    'Print': 'Primary Literature',
    'CodexChapter': 'Primary Literature',
    'PrintChapter': 'Primary Literature',
    'Catalogue': 'Primary Literature',
    'Edition': 'Primary Literature',
    'Translation': 'Primary Literature',
    'ArticleJournal': 'Secondary Literature',
    'Chapter': 'Secondary Literature',
    'Monograph': 'Secondary Literature',
    'Conference': 'Secondary Literature',
    'Collection': 'Secondary Literature',
    'Series': 'Secondary Literature',
    'Journal': 'Secondary Literature',
    'InternetDocument': 'Secondary Literature',
    'Lecture': 'Secondary Literature',
    'Other': 'Secondary Literature',
}

NO_TR_ROLE_MAP = {
    'ann': 'Annotator',
    'aut': 'Author',
    'aft': 'Author of Afterword',
    'aui': 'Author of Introduction',
    'ato': 'Autographer',
    'bnd': 'Binder',
    'dte': 'Dedicatee',
    'dto': 'Dedicator',
    'edt': 'Editor',
    'fmo': 'Former Owner',
    'hnr': 'Honoree',
    'his': 'Host institution',
    'ill': 'Illuminator',
    'ive': 'Interviewee',
    'ivr': 'Interviewer',
    'pat': 'Patron',
    'prt': 'Printer',
    'scr': 'Scribe',
    'spk': 'Speaker',
    'trl': 'Translator',
}

NO_TR_LANGUAGE_MAP = {
    'alb': 'Albanian',
    'ara': 'Arabic',
    'bos': 'Bosnian',
    'bul': 'Bulgarian',
    'hrv': 'Croatian',
    'dut': 'Dutch',
    'eng': 'English',
    'fre': 'French',
    'ger': 'German',
    'grc': 'Ancient Greek',
    'gre': 'Modern Greek',
    'ita': 'Italian',
    'lat': 'Latin',
    'peo': 'Persian',
    'pol': 'Polish',
    'rum': 'Romanian',
    'rus': 'Russian',
    'srp': 'Serbian',
    'spa': 'Spanish',
    'tur': 'Turkish',
}

def _record2solr_doc(form):
    solr_data = {}
    wtf = json.dumps(form.data)
    solr_data.setdefault('wtf_json', wtf)
    for field in form.data:
        #logging.info('%s => %s' % (field, form.data.get(field)))
        if field == 'id':
            #delete_record_solr = Solr(del_id=form.data.get(field))
            #delete_record_solr.delete()
            solr_data.setdefault('id', form.data.get(field))
        if field == 'created':
            solr_data.setdefault('created', form.data.get(field).replace(' ', 'T') + 'Z')
        if field == 'changed':
            solr_data.setdefault('changed', form.data.get(field).replace(' ', 'T') + 'Z')
        if field == 'owner':
            solr_data.setdefault('owner', form.data.get(field))
        if field == 'pubtype':
            solr_data.setdefault('pubtype', form.data.get(field))
            solr_data.setdefault('fpubtype', NO_TR_PUBTYPE2TEXT.get(form.data.get(field)))
            solr_data.setdefault('source_class', NO_TR_SOURCE_CLASS_MAP.get(form.data.get(field)))
        if field == 'subtype' and form.data.get(field) != None:
            solr_data.setdefault('subtype', NO_TR_SUBTYPE2TEXT.get(form.data.get(field)))
        if field == 'genre' and form.data.get(field):
            solr_data.setdefault('genre', NO_TR_GENRE2TEXT.get(form.data.get(field)))
        if field == 'title':
            solr_data.setdefault('title', form.data.get(field).strip())
            solr_data.setdefault('exacttitle', form.data.get(field).strip())
            solr_data.setdefault('sorttitle', form.data.get(field).strip())
        if field == 'subtitle' and form.data.get(field):
            solr_data.setdefault('subtitle', form.data.get(field).strip())
        if field == 'translated_title' and form.data.get(field):
            solr_data.setdefault('translated_title', form.data.get(field).strip())
        if field == 'incipit' and form.data.get(field):
            solr_data.setdefault('incipit', form.data.get(field).strip())
        if field == 'explicit' and form.data.get(field):
            solr_data.setdefault('explicit', form.data.get(field).strip())
        if field == 'vignette' and form.data.get(field):
            solr_data.setdefault('vignette', form.data.get(field).strip())
        if field == 'frontispiece' and form.data.get(field):
            solr_data.setdefault('frontispiece', form.data.get(field).strip())
        if field == 'autograph_text' and form.data.get(field):
            solr_data.setdefault('autograph', form.data.get(field).strip())
        if field == 'provenance' and form.data.get(field):
            solr_data.setdefault('provenance', form.data.get(field).strip())
        if field == 'note' and form.data.get(field):
            solr_data.setdefault('note', form.data.get(field).strip())
        if field == 'issued' and form.data.get(field):
            year = form.data.get(field)[0:4].strip()
            solr_data.setdefault('date', form.data.get(field).strip())
            if NO_TR_SOURCE_CLASS_MAP.get(form.data.get('pubtype')) == 'Primary Literature' and year:
                if int(year) >= 1400 and int(year) < 1500:
                    solr_data.setdefault('issued_primary', '1400-1500')
                elif int(year) >= 1500 and int(year) < 1600:
                    solr_data.setdefault('issued_primary', '1500-1600')
                elif int(year) >= 1600 and int(year) < 1700:
                    solr_data.setdefault('issued_primary', '1600-1700')
                elif int(year) >= 1700 and int(year) < 1800:
                    solr_data.setdefault('issued_primary', '1700-1800')
            else:
                solr_data.setdefault('issued_secondary', year)
            if len(form.data.get(field).strip()) == 4:
                solr_data.setdefault('date_boost', '%s-01-01T00:00:00Z' % form.data.get(field).strip())
            elif len(form.data.get(field).strip()) == 7:
                solr_data.setdefault('date_boost', '%s-01T00:00:00Z' % form.data.get(field).strip())
            else:
                solr_data.setdefault('date_boost', '%sT00:00:00Z' % form.data.get(field).strip())
            solr_data.setdefault('issued', year)
        if field == 'publisher' and form.data.get(field):
            solr_data.setdefault('publisher', form.data.get(field).strip())
        if field == 'language' and len(form.data.get(field)) > 0:
            for lang in form.data.get(field):
                if lang != '':
                    solr_data.setdefault('language', []).append(NO_TR_LANGUAGE_MAP.get(lang))
        if field == 'person' and len(form.data.get(field)) > 0:
            FACET_ROLES = {'aut', 'edt', 'trl'}
            for idx, person in enumerate(form.data.get(field)):
                if person.get('name'):
                    solr_data.setdefault('person', []).append(person.get('name').strip())
                    if set(person.get('role')) & FACET_ROLES:
                        solr_data.setdefault('fperson', []).append(person.get('name').strip())
        if field == 'corporation' and len(form.data.get(field)) > 0:
            for idx, corporation in enumerate(form.data.get(field)):
                if corporation.get('name'):
                    solr_data.setdefault('corporation', []).append(corporation.get('name').strip())
        if field == 'abstract' and form.data.get(field):
            solr_data.setdefault('description', form.data.get(field).strip())
        # if field == 'container_title' and form.data.get(field):
        #     solr_data.setdefault('container_title', form.data.get(field).strip())
        # if field == 'series_title' and form.data.get(field):
        #     solr_data.setdefault('series_title', form.data.get(field).strip())
        if field == 'is_part_of' and len(form.data.get(field)) > 0:
            ipo_ids = []
            ipo_solr = ''
            try:
                for ipo in form.data.get(field):
                    if ipo:
                        #logging.info(ipo)
                        if 'is_part_of' in ipo:
                            #logging.info('POOP')
                            if ipo.get('is_part_of'):
                                ipo_ids.append(ipo.get('is_part_of'))
                        else:
                            #logging.info('PEEP')
                            ipo_ids.append(ipo)
                query = '{!terms f=id}%s' % ','.join(ipo_ids)
                if len(ipo_ids) == 1:
                    query = 'id:%s' % ipo_ids[0]
                if len(ipo_ids) > 0:
                    ipo_solr = Solr(query=query, facet='false', fields=['wtf_json'])
                    ipo_solr.request()
                    if len(ipo_solr.results) == 0:
                        flash(gettext('Not all IDs from relation "is part of" could be found! Ref: %s' % form.data.get('id')), 'warning')
                    for idx, doc in enumerate(ipo_solr.results):
                        myjson = json.loads(doc.get('wtf_json'))
                        #solr_data.setdefault('is_part_of', []).append('<a href="/retrieve/%s/%s">%s</a>' % (myjson.get('pubtype'), myjson.get('id'), myjson.get('title')))
                        solr_data.setdefault('is_part_of', []).append(json.dumps({'pubtype': myjson.get('pubtype'),
                                                                       'id': myjson.get('id'),
                                                                       'title': myjson.get('title'),
                                                                       'page_first': form.data.get(field)[idx].get('page_first', ''),
                                                                       'page_last': form.data.get(field)[idx].get('page_last', ''),
                                                                       'volume': form.data.get(field)[idx].get('volume', ''),
                                                                       'issue': form.data.get(field)[idx].get('issue', '')}))
            except AttributeError as e:
                logging.error(e)
        if field == 'has_part' and len(form.data.get(field)) > 0:
            #for myhp in form.data.get(field):
                #logging.info('HP ' + myhp)
            hp_ids = []
            hp_solr = ''
            try:
                for hp in form.data.get(field):
                    if hp:
                        hp_ids.append(hp)
                query = '{!terms f=id}%s' % ','.join(hp_ids)
                if len(hp_ids) == 1:
                    query = 'id:%s' % hp_ids[0]
                if len(hp_ids) > 0:
                    hp_solr = Solr(query=query, facet='false', fields=['wtf_json'])
                    hp_solr.request()
                    if len(hp_solr.results) == 0:
                        flash(
                            gettext('Not all IDs from relation "has part" could be found! Ref: %s' % form.data.get('id')), 'warning')
                    for doc in hp_solr.results:
                        myjson = json.loads(doc.get('wtf_json'))
                        #solr_data.setdefault('has_part', []).append('<a href="/retrieve/%s/%s">%s</a>' % (myjson.get('pubtype'), myjson.get('id'), myjson.get('title')))
                        solr_data.setdefault('has_part', []).append(json.dumps({'pubtype': myjson.get('pubtype'),
                                                                     'id': myjson.get('id'),
                                                                     'title': myjson.get('title'),}))
            except AttributeError as e:
                logging.error(e)
        if field == 'other_version' and len(form.data.get(field)) > 0:
            #for myov in form.data.get(field):
                #logging.info('OV ' + myov)
            ov_ids = []
            ov_solr = ''
            try:
                for version in form.data.get(field):
                    if version:
                        ov_ids.append(version)
                query = '{!terms f=id}%s' % ','.join(ov_ids)
                if len(ov_ids) == 1:
                    query = 'id:%s' % ov_ids[0]
                if len(ov_ids) > 0:
                    ov_solr = Solr(query=query, facet='false', fields=['wtf_json'])
                    ov_solr.request()
                    if len(ov_solr.results) == 0:
                        flash(
                            gettext('Not all IDs from relation "other version" could be found! Ref: %s' % form.data.get('id')),
                            'warning')
                    for doc in ov_solr.results:
                        #logging.info(json.loads(doc.get('wtf_json')))
                        myjson = json.loads(doc.get('wtf_json'))
                        #solr_data.setdefault('other_version', []).append('<a href="/retrieve/%s/%s">%s</a>' % (myjson.get('pubtype'), myjson.get('id'), myjson.get('title')))
                        solr_data.setdefault('other_version', []).append(json.dumps({'pubtype': myjson.get('pubtype'),
                                                                     'id': myjson.get('id'),
                                                                     'title': myjson.get('title'),}))
            except AttributeError as e:
                logging.error(e)
        if field == 'relation' and len(form.data.get(field)) > 0:
            #for myrel in form.data.get(field):
                #logging.info('REL ' + myrel)
            rel_ids = []
            rel_solr = ''
            try:
                for related in form.data.get(field):
                    if related:
                        rel_ids.append(related)
                query = '{!terms f=id}%s' % ','.join(rel_ids)
                if len(rel_ids) == 1:
                    query = 'id:%s' % rel_ids[0]
                if len(rel_ids) > 0:
                    rel_solr = Solr(query=query, facet='false', fields=['wtf_json'])
                    rel_solr.request()
                    if len(rel_solr.results) == 0:
                        flash(
                            gettext('Not all IDs from relation "related item" could be found! Ref: %s' % form.data.get('id')),
                            'warning')
                    for doc in rel_solr.results:
                        myjson = json.loads(doc.get('wtf_json'))
                        #solr_data.setdefault('related_item', []).append('<a href="/retrieve/%s/%s">%s</a>' % (myjson.get('pubtype'), myjson.get('id'), myjson.get('title')))
                        solr_data.setdefault('related_item', []).append(json.dumps({'pubtype': myjson.get('pubtype'),
                                                                     'id': myjson.get('id'),
                                                                     'title': myjson.get('title'),}))
            except AttributeError as e:
                logging.error(e)
        if field == 'ISSN' and len(form.data.get(field)) > 0:
            for issn in form.data.get(field):
                solr_data.setdefault('issn', []).append(issn.strip())
                solr_data.setdefault('issn', []).append(issn.strip().replace('-', ''))
        if field == 'ISBN' and len(form.data.get(field)) > 0:
            for isbn in form.data.get(field):
                solr_data.setdefault('isbn', []).append(isbn.strip())
                solr_data.setdefault('isbn', []).append(isbn.strip().replace('-', ''))
        if field == 'keyword' and len(form.data.get(field)) > 0:
            for idx, keyword in enumerate(form.data.get(field)):
                if keyword.get('label'):
                    solr_data.setdefault('keyword', []).append(keyword.get('label').strip())
                    solr_data.setdefault('fkeyword', []).append(keyword.get('label').strip())
        if field == 'keyword_temporal' or field == 'keyword_geographic':
            for keyword in form.data.get(field):
                if keyword:
                    solr_data.setdefault('keyword', []).append(keyword.strip())
                    solr_data.setdefault('fkeyword', []).append(keyword.strip())
        if field == 'key_publication':
            solr_data.setdefault('key_publication', form.data.get(field))
        if field == 'library' and len(form.data.get(field)) > 0:
            for library in form.data.get(field):
                if library.get('latitude'):
                    solr_data.setdefault('library', []).append(json.dumps(library))
                    solr_data.setdefault('flibrary', []).append(library.get('label'))
        if field == 'origin' and form.data.get(field):
            solr_data.setdefault('origin_place', form.data.get(field))

    #logging.info(solr_data)
    return solr_data

def _record2solr(form):
    record_solr = Solr(core='hoe', data=[_record2solr_doc(form)])
    record_solr.update()

@app.route('/dashboard')
@login_required
def dashboard():
    page = int(request.args.get('page', 1))
    mystart = 0
    query = '*:*'
    filterquery = request.values.getlist('filter')
    rows = secrets.SOLR_ROWS
    # Solr(start=(page - 1) * 10, query=query, fquery=filterquery, sort=sorting)
    dashboard_solr = Solr(start=(page - 1) * int(rows), query=query, sort='created asc', rows=rows,
                          json_facet=secrets.SOLR_FACETS, fquery=filterquery)
    dashboard_solr.request()

    num_found = dashboard_solr.count()

    if num_found == 0:
        flash(gettext('There Are No Records Yet!'))
        return render_template('dashboard.html', records=dashboard_solr.results, facet_data=dashboard_solr.facets,
                               header=lazy_gettext('Dashboard'), site=theme(request.access_route), pagination=None)
    else:
        pagination = Pagination(page=page, total=num_found, found=num_found, bs_version=3, search=True,
                                record_name=lazy_gettext('titles'), per_page=int(rows),
                                search_msg=lazy_gettext('Showing {start} to {end} of {found} {record_name}'))
        mystart = 1 + (pagination.page - 1) * pagination.per_page
        # myend = mystart + pagination.per_page - 1

    flibraries = {}
    for flib in dashboard_solr.facets.get('flibrary').get('buckets'):
        flibraries.setdefault(flib.get('val'), flib.get('count'))
    libraries = []
    for lib in dashboard_solr.facets.get('library').get('buckets'):
        libraries.append({'library': eval(lib.get('val'))})
    return render_template('dashboard.html', records=dashboard_solr.results, facet_data=dashboard_solr.facets,
                           header=lazy_gettext('Dashboard'), site=theme(request.access_route),
                           offset=mystart - 1, query=query, filterquery=filterquery, pagination=pagination,
                           now=datetime.datetime.now(), flibraries=flibraries, libraries=libraries, target='dashboard',
                           del_redirect='dashboard', pubtype_map=PUBTYPE2TEXT)

@app.route('/create/<pubtype>', methods=['GET', 'POST'])
@login_required
def new_record(pubtype='article-journal', primary_id=''):
    form = PUBTYPE2FORM.get(pubtype)()

    if request.is_xhr:
        #logging.info(request.form)
        form.formdata = request.form
        # Do we have any data already?
        if not form.title.data:
            solr_data = {}
            wtf = json.dumps(form.data)
            solr_data.setdefault('wtf_json', wtf)
            for field in form.data:
                # logging.info('%s => %s' % (field, form.data.get(field)))
                if field == 'id':
                    solr_data.setdefault('id', form.data.get(field).strip())
                if field == 'created':
                    solr_data.setdefault('created', form.data.get(field).strip().replace(' ', 'T') + 'Z')
                if field == 'changed':
                    solr_data.setdefault('changed', form.data.get(field).strip().replace(' ', 'T') + 'Z')
                if field == 'owner':
                    solr_data.setdefault('owner', form.data.get(field).strip())
                if field == 'pubtype':
                    solr_data.setdefault('pubtype', form.data.get(field).strip())

            record_solr = Solr(core='hoe', data=[solr_data])
            record_solr.update()
        else:
            _record2solr(form)
        return jsonify({'status': 200})

    if form.validate_on_submit():
        if form.errors:
            flash_errors(form)
            return render_template('tabbed_form.html', form=form, header=lazy_gettext('New Record'),
                                   site=theme(request.access_route), action='create', pubtype=pubtype,
                                   record_id=form.id.data)
        _record2solr(form)
        return redirect(url_for('dashboard'))

    if request.args.get('subtype'):
        form.subtype.data = request.args.get('subtype')
    form.id.data = str(uuid.uuid4())
    form.created.data = datetime.datetime.now()
    form.changed.data = datetime.datetime.now()
    form.owner.data = current_user.id
    form.pubtype.data = pubtype

    return render_template('tabbed_form.html', form=form, header=lazy_gettext('New Record'), site=theme(request.access_route),
                           pubtype=pubtype, action='create', record_id=form.id.data)

@app.route('/retrieve/<pubtype>/<record_id>')
def show_record(pubtype, record_id=''):
    show_record_solr = Solr(query='id:%s' % record_id, core='hoe', mlt=True, mlt_fields=['title', 'description', 'keyword'])
    show_record_solr.request()

    is_part_of = show_record_solr.results[0].get('is_part_of')
    has_part = show_record_solr.results[0].get('has_part')
    other_version = show_record_solr.results[0].get('other_version')
    related_item = show_record_solr.results[0].get('related_item')
    thedata = json.loads(show_record_solr.results[0].get('wtf_json'))
    form = PUBTYPE2FORM.get(pubtype).from_json(thedata)

    return render_template('record.html', record=form, header=form.data.get('title'), site=theme(request.access_route),
                           action='retrieve', record_id=record_id, del_redirect='dashboard', pubtype=pubtype,
                           role_map=ROLE_MAP, lang_map=LANGUAGE_MAP, pubtype_map=PUBTYPE2TEXT, subtype_map=SUBTYPE2TEXT,
                           genre_map=GENRE2TEXT, mlt=show_record_solr.mlt_results, is_part_of=is_part_of,
                           has_part=has_part, other_version=other_version, related_item=related_item)

@csrf.exempt
@app.route('/update/json', methods=['GET', 'POST'])
def json_edit_record():
    form = PUBTYPE2FORM.get(request.form.get('pubtype'))()
    form.formdata = request.form
    _record2solr(form)
    return jsonify({'poop': 'poop'})

@app.route('/update/<pubtype>/<record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(record_id='', pubtype=''):
    edit_record_solr = Solr(core='hoe', query='id:%s' % record_id)
    edit_record_solr.request()

    thedata = json.loads(edit_record_solr.results[0].get('wtf_json'))

    if request.method == 'POST':
        form = PUBTYPE2FORM.get(pubtype)()
    elif request.method == 'GET':
        form = PUBTYPE2FORM.get(pubtype).from_json(thedata)

    if thedata.get('pubtype') != pubtype:
        flash(Markup(gettext(
            '<p><i class="fa fa-exclamation-triangle fa-3x"></i> <h3>The following data are incompatible with this publication type</h3></p>')) + _diff_struct(
            thedata, form.data), 'error')
        form.pubtype.data = pubtype

    if form.validate_on_submit():
        if form.errors:
            flash_errors(form)
            return render_template('tabbed_form.html', form=form,
                                   header=lazy_gettext('Edit: %(title)s', title=form.data.get('title')),
                                   site=theme(request.access_route), action='update', pubtype=pubtype)
        _record2solr(form)
        return redirect(url_for('dashboard'))

    form.changed.data = datetime.datetime.now()

    return render_template('tabbed_form.html', form=form, header=lazy_gettext('Edit: %(title)s',
                                                                         title=form.data.get('title')),
                           site=theme(request.access_route), action='update', pubtype=pubtype, record_id=record_id)

@app.route('/make_admin/<user_id>')
@login_required
def make_admin(user_id=''):
    if user_id:
        ma_solr = Solr(core='hoe_users', data=[{'id': user_id, 'role': {'set': 'admin'}}])
        ma_solr.update()
        flash(gettext('%s upgraded to admin!' % user_id), 'success')
        return redirect(url_for('index'))
    else:
        flash(gettext('You did not supply an ID!'), 'danger')
        return redirect(url_for('index'))

@app.route('/delete/<record_id>')
def delete_record(record_id=''):
    delete_record_solr = Solr(del_id=record_id)
    delete_record_solr.delete()

    return jsonify({'deleted': True})

@app.route('/add/file')
def add_file():
    pass

@app.errorhandler(401)
def unauthorized(e):
    return render_template('401.html'), 401
########################################################################################################################
class UserNotFoundError(Exception):
    pass

class User(UserMixin):
    def __init__(self, id, role='', name='', email='', accesstoken=''):
        self.id = id
        self.name = name
        self.role = role
        self.email = email
        self.accesstoken = accesstoken
        user_solr = Solr(core='hoe_users', query='id:%s' % id, facet='false')
        user_solr.request()
        if user_solr.count() > 0:
            _user = user_solr.results[0]
            self.name = _user.get('name')
            self.role = _user.get('role')
            self.email = _user.get('email')
            self.accesstoken = _user.get('accesstoken')

    def __repr__(self):
        return '<User %s: %s>' % (self.id, self.name)

    @classmethod
    def get_user(self_class, id):
        user_solr = Solr(core='hoe_users', query='id:%s' % id)
        user_solr.request()
        return user_solr.results[0]

    @classmethod
    def get(self_class, id):
        try:
            return self_class(id)
        except UserNotFoundError:
            return None

class LoginForm(Form):
    username = StringField(lazy_gettext('Username'))
    password = PasswordField(lazy_gettext('Password'))
    wayf = HiddenField(lazy_gettext('Where Are You From?'))

def is_safe_url(target):
    ref_url = parse.urlparse(request.host_url)
    test_url = parse.urlparse(parse.urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

def get_redirect_target():
    for target in request.values.get('next'), request.referrer:
        if not target:
            continue
        if is_safe_url(target):
            return target

def redirect_back(endpoint, **values):
    target = request.form['next']
    if not target or not is_safe_url(target):
        target = url_for(endpoint, **values)
    return redirect(target)

@login_manager.user_loader
def load_user(id):
    return User.get(id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    next = get_redirect_target()
    if request.method == 'POST':
        user = User(request.form.get('username'))
        #user_info = user.get_user(request.form.get('username'))

        authuser = requests.post('https://api.ub.rub.de/ldap/authenticate/',
                                 data={'nocheck': 'true',
                                       'userid': base64.b64encode(request.form.get('username').encode('ascii')),
                                       'passwd': base64.b64encode(request.form.get('password').encode('ascii'))}).json()
        #logging.info(authuser)
        if authuser.get('email'):
            user_solr = Solr(core='hoe_users', query='id:%s' % authuser.get('id'), facet='false')
            user_solr.request()
            if user_solr.count() == 0:
                tmp = {}
                accesstoken = make_secure_token(
                    base64.b64encode(request.form.get('username').encode('ascii')) + base64.b64encode(
                        request.form.get('password').encode('ascii')))
                tmp.setdefault('id', request.form.get('username').encode('ascii'))
                tmp.setdefault('name', '%s %s' % (authuser.get('given_name'), authuser.get('last_name')))
                tmp.setdefault('email', authuser.get('email'))
                tmp.setdefault('role', 'user')
                tmp.setdefault('accesstoken', accesstoken)
                user.name = '%s %s' % (authuser.get('given_name'), authuser.get('last_name'))
                user.email = authuser.get('email')
                user.accesstoken = accesstoken
                new_user_solr = Solr(core='hoe_users', data=[tmp], facet='false')
                new_user_solr.update()
            login_user(user)

            return redirect(next or url_for('index'))
        else:
            flash(gettext("Username and Password Don't Match"), 'danger')
            return redirect('login')

    if 'code' in request.args:
        orcid_auth = requests.post('https://orcid.org/oauth/token', headers={'Accept': 'application/json'}, data={
            'client_id': secrets.orcid_client_id, 'client_secret': secrets.orcid_client_secret,
            'code': request.args.get('code'), 'grant_type': 'authorization_code',
            'redirect_uri': 'https://hoe-test.ub.rub.de/login?hoe_next=%s' % request.args.get('hoe_next')
        }).json()
        if 'orcid' in orcid_auth:
            user_solr = Solr(core='hoe_users', query='id:%s' % orcid_auth.get('orcid'), facet='false')
            user_solr.request()
            if user_solr.count() == 0:
                tmp = {}
                tmp.setdefault('id', orcid_auth.get('orcid'))
                tmp.setdefault('name', orcid_auth.get('name'))
                tmp.setdefault('email', orcid_auth.get('email', ''))
                tmp.setdefault('role', 'user')
                tmp.setdefault('accesstoken', orcid_auth.get('access_token'))
                new_user_solr = Solr(core='hoe_users', data=[tmp], facet='false')
                new_user_solr.update()
            user = User(orcid_auth.get('orcid'))
            user.name = orcid_auth.get('name')
            user.email = orcid_auth.get('email', '')
            user.accesstoken = orcid_auth.get('accesstoken')
            login_user(user)

            return redirect(request.args.get('hoe_next') or url_for('index'))
    else:
        form = LoginForm()
        next = get_redirect_target()
        #return render_template('login.html', form=form, header='Sign In', next=next, orcid_sandbox_client_id=orcid_sandbox_client_id)
        return render_template('login.html', form=form, header=lazy_gettext('Sign In'), next=next,
                               orcid_client_id=secrets.orcid_client_id, site=theme(request.access_route))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

ORCID_RE = re.compile('\d{4}-\d{4}-\d{4}-\d{4}')

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash('Error in the %s field: %s' % (getattr(form, field).label.text, error), 'error')

# @app.route('/edit/user/<loginid>',methods=['GET', 'POST'])
# @app.route('/register', methods=['GET', 'POST'])
# def register(loginid=None):
#     form = UserForm()
#     if form.validate_on_submit():
#         if ORCID_RE.match(form.loginid.data):
#             # TODO: Check with ORCID OAUTH
#             pass
#         else:
#             # TODO: This isn't right yet...
#             if current_user.role != 'admin' and not loginid and form.password.data.encode('ascii') != 'admin':
#                 response = requests.post('https://api-test.ub.rub.de/ldap/authenticate/',
#                                          data={'nocheck': 'true',
#                                                'userid': base64.b64encode(form.loginid.data.encode('ascii')),
#                                                'passwd': base64.b64encode(form.password.data.encode('ascii'))})
#                 if str(response.status_code).startswith('4') or str(response.status_code).startswith('5'):
#                     if response.status_code == 401:
#                         flash('Invalid password. Please try agein...', 'danger')
#                         #flash('%s (%s)' % (response.reason, response.status_code))
#                     else:
#                         flash('%s (%s)' % (response.reason, response.status_code))
#                     return render_template('register.html', form=form, header='User Registration')
#
#                 hash = make_secure_token(
#                     base64.b64encode(form.loginid.data.encode('ascii')) + base64.b64encode(form.password.data.encode('ascii')))
#                 redis_store.hset(form.loginid.data, 'auth_token', hash)
#
#             redis_store.hset(form.loginid.data, 'email', form.email.data)
#             redis_store.hset(form.loginid.data, 'name', form.name.data)
#             redis_store.hset(form.loginid.data, 'role', form.role.data)
#
#     if loginid:
#         edit_user = redis_store.hgetall(loginid)
#         tmp = json.dumps(edit_user)
#         edit_user = json.loads(tmp)
#         form.loginid.data = loginid
#         form.name.data = edit_user.get('name')
#         form.email.data = edit_user.get('email')
#         form.role.data = edit_user.get('role')
#     flash_errors(form)
#     return render_template('register.html', form=form, header='User Registration', edit_user=loginid)

@app.route('/search')
def search():
    pagination = ''
    page = int(request.args.get('page', 1))
    #mypage = page
    query = request.args.get('q', '')#.decode('utf-8')
    #logging.info(query)
    if query == '':
        query = '*:*'

    filterquery = request.values.getlist('filter')
    # if len(filterquery) > 1:
    #     filters = '&amp;filter='.join(filterquery)
    # elif filterquery:
    #     filters = '&amp:filter=%s' % filterquery[0]#.get('filter')
    sorting = request.args.get('sort', 'relevance')
    if sorting == 'relevance':
        sorting = ''
    else:
        sorting = 'issued desc'

    rows = secrets.SOLR_ROWS
    search_solr = Solr(start=(page - 1) * int(rows), query=query, fquery=filterquery, sort=sorting,
                       json_facet=secrets.SOLR_FACETS, rows=rows)
    search_solr.request()
    num_found = search_solr.count()
    if num_found == 1:
        return redirect(url_for('show_record', record_id=search_solr.results[0].get('id'), pubtype=search_solr.results[0].get('pubtype')))
    elif num_found == 0:
        flash(gettext('Your Search Found no Results'))
        return redirect(url_for('index'))
    else:
        pagination = Pagination(page=page, total=num_found, found=num_found, bs_version=3, search=True,
                                record_name=lazy_gettext('titles'), per_page=int(rows),
                                search_msg=lazy_gettext('Showing {start} to {end} of {found} {record_name}'))
        mystart = 1 + (pagination.page - 1) * pagination.per_page
        #myend = mystart + pagination.per_page - 1
        flibraries = {}
        for flib in search_solr.facets.get('flibrary').get('buckets'):
            flibraries.setdefault(flib.get('val'), flib.get('count'))
        libraries = []
        for lib in search_solr.facets.get('library').get('buckets'):
            libraries.append({'library': eval(lib.get('val'))})
        return render_template('resultlist.html', records=search_solr.results, pagination=pagination,
                               facet_data=search_solr.facets, header=query, site=theme(request.access_route),
                               offset=mystart - 1, query=query, filterquery=filterquery, flibraries=flibraries,
                               libraries=libraries, target='search', pubtype_map=PUBTYPE2TEXT)

@login_required
@app.route('/export/solr_dump')
def export_solr_dump():
    '''
    Export the wtf_json field of every doc in the index to a new document in the users core and to the user's local file
    system. Uses the current user's ID and a timestamp as the document ID and file name.
    '''
    filename = '%s_%s.json' % (current_user.id, int(time.time()))
    export_solr = Solr(export_field='wtf_json')
    export_docs = export_solr.export()
    target_solr = Solr(core='hoe_users', data=[{'id': filename, 'dump': json.dumps(export_docs)}])
    target_solr.update()

    return send_file(BytesIO(str.encode(json.dumps(export_docs))), attachment_filename=filename, as_attachment=True,
                     cache_timeout=1, add_etags=True)

@login_required
@app.route('/import/solr_dumps')
def import_solr_dumps():
    '''
    Import Solr dumps either from the users core or from the local file system.
    '''
    page = int(request.args.get('page', 1))
    solr_dumps = Solr(core='hoe_users', query='id:*.json', facet='false', start=(page - 1) * 10)
    solr_dumps.request()
    num_found = solr_dumps.count()
    pagination = Pagination(page=page, total=num_found, found=num_found, bs_version=3, search=True,
                                record_name=lazy_gettext('dumps'),
                                search_msg=lazy_gettext('Showing {start} to {end} of {found} {record_name}'))
    mystart = 1 + (pagination.page - 1) * pagination.per_page
    form = FileUploadForm()
    return render_template('solr_dumps.html', records=solr_dumps.results, offset=mystart - 1, pagination=pagination,
                           header=lazy_gettext('Import Dump'), del_redirect='import/solr_dumps', form=form)

def _import_data(doc):
    form = PUBTYPE2FORM.get(doc.get('pubtype')).from_json(doc)
    return _record2solr_doc(form)

@login_required
@app.route('/import/solr_dump/<filename>', methods=['GET', 'POST'])
def import_solr_dump(filename=''):
    thedata = ''
    solr_data = []
    if request.method == 'GET':
        if filename:
            import_solr = Solr(core='hoe_users', query='id:%s' % filename, facet='false')
            import_solr.request()

            thedata = json.loads(import_solr.results[0].get('dump')[0])
    elif request.method == 'POST':
        form = FileUploadForm()
        if form.validate_on_submit():
            thedata = json.loads(form.file.data.stream.read())

    pool = Pool(4)
    solr_data.append(pool.map(_import_data, thedata))
    import_solr = Solr(core='hoe', data=solr_data[0])
    import_solr.update()

    flash(gettext('%(records)s records imported!', records=len(thedata)), 'success')

    return redirect('dashboard')

@app.route('/delete/solr_dump/<record_id>')
def delete_dump(record_id=''):
    delete_record_solr = Solr(core='hoe_users', del_id=record_id)
    delete_record_solr.delete()

    return jsonify({'deleted': True})

@app.route('/retrieve/related_items/<relation>/<record_ids>')
def show_related_item(relation='', record_ids=''):
    query = query='{!terms f=id}%s' % record_ids
    if ',' not in record_ids:
        query = 'id:%s' % record_ids
    relation_solr = Solr(query=query, facet='false')
    relation_solr.request()

    return jsonify({'relation': relation, 'docs': relation_solr.results})


if __name__ == '__main__':
    app.run(port=5001)
