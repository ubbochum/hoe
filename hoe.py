import logging
import uuid
import base64
import datetime
import re
import requests
import pickle
import simplejson as json
import wtforms_json
import secrets
from flask import Flask, render_template, redirect, request, jsonify, flash, url_for, Markup
from flask.ext.babel import Babel
from flask.ext.bootstrap import Bootstrap
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required, make_secure_token, AnonymousUserMixin
from flask.ext.paginate import Pagination
from flask_humanize import Humanize
from flask_wtf.csrf import CsrfProtect
from urllib import parse
from solr_handler import Solr
from datadiff import diff_dict

from forms import *
from config import *

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

CsrfProtect(app)

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


@babel.localeselector
def get_locale():
    #return request.accept_languages.best_match(LANGUAGES.keys())
    return 'de'

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
            flash(gettext("You haven't registered any records with us yet. Please do so now..."), 'danger')

    return render_template('index.html', header=gettext('Home'), site=theme(request.access_route), numFound=numFound, records=records)

@app.route('/contact')
def contact():
    return redirect('mailto:bibliographie-ub.rub.de')

def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash('Error in the %s field: %s' % (getattr(form, field).label.text, error), 'error')

SOURCE_CLASS_MAP = {
    'Codex': 'primary',
    'Print': 'primary',
    'Catalogue': 'primary',
    'Edition': 'primary',
    'Translation': 'primary',
    'ArticleJournal': 'secondary',
    'Chapter': 'secondary',
    'Monograph': 'secondary',
    'Conference': 'secondary',
    'Collection': 'secondary',
    'Series': 'secondary',
    'Journal': 'secondary',
    'InternetDocument': 'secondary',
    'Lecture': 'secondary',
    'Other': 'secondary',
}

def _record2solr(form):
    solr_data = {}
    wtf = json.dumps(form.data)
    solr_data.setdefault('wtf_json', wtf)
    for field in form.data:
        #logging.info('%s => %s' % (field, form.data.get(field)))
        if field == 'id':
            solr_data.setdefault('id', form.data.get(field))
        if field == 'created':
            solr_data.setdefault('created', form.data.get(field).replace(' ', 'T') + 'Z')
        if field == 'changed':
            solr_data.setdefault('changed', form.data.get(field).replace(' ', 'T') + 'Z')
        if field == 'owner':
            solr_data.setdefault('owner', form.data.get(field))
        if field == 'pubtype':
            solr_data.setdefault('pubtype', form.data.get(field))
            solr_data.setdefault('source_class', SOURCE_CLASS_MAP.get(form.data.get(field)))
        if field == 'genre' and form.data.get(field):
            solr_data.setdefault('subtype', form.data.get(field))
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
        if field == 'provenance' and form.data.get(field):
            solr_data.setdefault('provenance', form.data.get(field).strip())
        if field == 'note' and form.data.get(field):
            solr_data.setdefault('note', form.data.get(field).strip())
        if field == 'issued':
            year = form.data.get(field)[0:4].strip()
            solr_data.setdefault('date', form.data.get(field).strip())
            if SOURCE_CLASS_MAP.get(form.data.get('pubtype')) == 'primary':
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
                    solr_data.setdefault('language', []).append(lang)
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
        if field == 'container_title' and form.data.get(field):
            solr_data.setdefault('container_title', form.data.get(field).strip())
        if field == 'series_title' and form.data.get(field):
            solr_data.setdefault('series_title', form.data.get(field).strip())
        # if field == 'is_part_of' and len(form.data.get(field)) > 0:
        #     for idx, ipo in enumerate(form.data.get(field)):
        #         if ipo.get('is_part_of'):
        #             ipo_solr = Solr(query='id:%s' % ipo.get('is_part_of'), facet='false')
        #             ipo_solr.request()
        #             if ipo_solr.results[0]:
        #                 solr_data.setdefault('container_title', ipo_solr.results[0].get('title'))
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

    logging.info(solr_data)
    record_solr = Solr(core='hoe', data=[solr_data])
    record_solr.update()

@app.route('/dashboard')
@login_required
def dashboard():
    page = int(request.args.get('page', 1))
    mystart = 0
    query = '*:*'
    filterquery = request.values.getlist('filter')
    # Solr(start=(page - 1) * 10, query=query, fquery=filterquery, sort=sorting)
    dashboard_solr = Solr(start=(page - 1) * 10, query=query, sort='created asc',
                          facet_fields=secrets.SOLR_FACETS,
                          fquery=filterquery)
    dashboard_solr.request()

    num_found = dashboard_solr.count()

    if num_found == 0:
        flash(gettext('There Are No Records Yet!'))
        return render_template('dashboard.html', records=dashboard_solr.results, facet_data=dashboard_solr.facets,
                               header=gettext('Dashboard'), site=theme(request.access_route), pagination=None)
    else:
        pagination = Pagination(page=page, total=num_found, found=num_found, bs_version=3, search=True,
                                record_name=gettext('titles'),
                                search_msg=gettext('Showing {start} to {end} of {found} {record_name}'))
        mystart = 1 + (pagination.page - 1) * pagination.per_page
        # myend = mystart + pagination.per_page - 1

    flibraries = {}
    for flib in dashboard_solr.facets.get('flibrary'):
        flibraries.setdefault(list(flib.keys())[0], list(flib.values())[0])
    #logging.info(flibraries)
    libraries = []
    for lib_facet in dashboard_solr.facets.get('library'):
        for library in lib_facet:
            libraries.append({'library': eval(library)})
    return render_template('dashboard.html', records=dashboard_solr.results, facet_data=dashboard_solr.facets,
                           header=gettext('Dashboard'), site=theme(request.access_route),
                           offset=mystart - 1, query=query, filterquery=filterquery, pagination=pagination,
                           now=datetime.datetime.now(), flibraries=flibraries, libraries=libraries, target='dashboard',
                           )

@app.route('/create/<pubtype>', methods=['GET', 'POST'])
@login_required
def new_record(pubtype='article-journal', primary_id=''):
    form = PUBTYPE2FORM.get(pubtype)()

    if form.validate_on_submit():
        if form.errors:
            flash_errors(form)
            return render_template('test_form.html', form=form, header=gettext('New Record'),
                                   site=theme(request.access_route), action='create', pubtype=pubtype)
        _record2solr(form)
        return redirect(url_for('dashboard'))


    form.id.data = str(uuid.uuid4())
    form.created.data = datetime.datetime.now()
    form.changed.data = datetime.datetime.now()
    form.owner.data = current_user.id
    form.pubtype.data = pubtype

    return render_template('tabbed_form.html', form=form, header=gettext('New Record'), site=theme(request.access_route), pubtype=pubtype, action='create')

@app.route('/retrieve/<pubtype>/<record_id>')
def show_record(pubtype, record_id=''):
    ROLE_MAP = {
        'aut': gettext('Author'),
        'edt': gettext('Editor'),
        'his': gettext('Host institution'),
        'fmo': gettext('Former Owner'),
    }
    LANGUAGE_MAP = {
        'alb': gettext('Albanian'),
        'ara': gettext('Arabic'),
        'bos': gettext('Bosnian'),
        'bul': gettext('Bulgarian'),
        'hrv': gettext('Croatian'),
        'dut': gettext('Dutch'),
        'eng': gettext('English'),
        'fre': gettext('French'),
        'ger': gettext('German'),
        'gre': gettext('Greek'),
        'ita': gettext('Italian'),
        'lat': gettext('Latin'),
        'peo': gettext('Persian'),
        'pol': gettext('Polish'),
        'rum': gettext('Romanian'),
        'rus': gettext('Russian'),
        'srp': gettext('Serbian'),
        'spa': gettext('Spanish'),
        'tur': gettext('Turkish'),
    }
    show_record_solr = Solr(query='id:%s' % record_id, core='hoe', mlt=True, mlt_fields=['title', 'description', 'keyword'])
    show_record_solr.request()

    thedata = json.loads(show_record_solr.results[0].get('wtf_json'))
    form = PUBTYPE2FORM.get(pubtype).from_json(thedata)

    return render_template('record.html', record=form, header=form.data.get('title'), site=theme(request.access_route),
                           action='retrieve', record_id=record_id, del_redirect='dashboard', pubtype=pubtype,
                           role_map=ROLE_MAP, lang_map=LANGUAGE_MAP, mlt=show_record_solr.mlt_results)

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
                                   header=gettext('Edit: %(title)s', title=form.data.get('title')),
                                   site=theme(request.access_route), action='update', pubtype=pubtype)
        _record2solr(form, action='update')
        return redirect(url_for('dashboard'))

    form.changed.data = datetime.datetime.now()

    return render_template('tabbed_form.html', form=form, header=gettext('Edit: %(title)s',
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
    delete_record_solr = Solr(core='hoe', del_id=record_id)
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
    username = StringField(gettext('Username'))
    password = PasswordField(gettext('Password'))
    wayf = HiddenField(gettext('Where Are You From?'))

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
    if request.method == 'POST':
        user = User(request.form.get('username'))
        #user_info = user.get_user(request.form.get('username'))
        next = get_redirect_target()

        authuser = requests.post('https://api-test.ub.rub.de/ldap/authenticate/',
                                 data={'nocheck': 'true',
                                       'userid': base64.b64encode(request.form.get('username').encode('ascii')),
                                       'passwd': base64.b64encode(request.form.get('password').encode('ascii'))}).json()
        logging.info(authuser)
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
            flash("Username and Password Don't Match", 'danger')
            return redirect('login')

    form = LoginForm()
    next = get_redirect_target()
    #return render_template('login.html', form=form, header='Sign In', next=next, orcid_sandbox_client_id=orcid_sandbox_client_id)
    return render_template('login.html', form=form, header=gettext('Sign In'), next=next, site=theme(request.access_route))

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

    search_solr = Solr(start=(page - 1) * 10, query=query, fquery=filterquery, sort=sorting, facet='true', facet_fields=secrets.SOLR_FACETS)
    search_solr.request()
    num_found = search_solr.count()
    if num_found == 1:
        return redirect(url_for('show_record', record_id=search_solr.results[0].get('id'), pubtype=search_solr.results[0].get('pubtype')))
    elif num_found == 0:
        flash(gettext('Your Search Found no Results'))
        return redirect(url_for('index'))
    else:
        pagination = Pagination(page=page, total=num_found, found=num_found, bs_version=3, search=True, record_name=gettext('titles'), search_msg=gettext('Showing {start} to {end} of {found} {record_name}'))
        mystart = 1 + (pagination.page - 1) * pagination.per_page
        #myend = mystart + pagination.per_page - 1
        logging.info(query)
        return render_template('resultlist.html', records=search_solr.results, pagination=pagination, facet_data=search_solr.facets, header=query, site=theme(request.access_route), offset=mystart - 1, query=query, filterquery=filterquery, target='search')

@app.route('/export/solr_dump')
def export_solr_dump():
    export_solr = Solr(export_field='wtf_json')
    filename = export_solr.export()
    target_solr = Solr(core='hoe_users', data=[{'id': '%s_%s' % (current_user.id, filename.split('_')[1]), 'dump': open(filename).read()}])
    target_solr.update()
    flash(gettext('Exported internal format to %s' % filename), 'success')

    return redirect('dashboard')

@app.route('/import/solr_dumps')
def import_solr_dumps():
    page = int(request.args.get('page', 1))
    solr_dumps = Solr(core='hoe_users', query='id:*.json', facet='false', start=(page - 1) * 10)
    solr_dumps.request()
    num_found = solr_dumps.count()
    pagination = Pagination(page=page, total=num_found, found=num_found, bs_version=3, search=True,
                                record_name=gettext('dumps'),
                                search_msg=gettext('Showing {start} to {end} of {found} {record_name}'))
    mystart = 1 + (pagination.page - 1) * pagination.per_page
    return render_template('solr_dumps.html', records=solr_dumps.results, offset=mystart - 1, pagination=pagination, header=gettext('Import Dump'), del_redirect='dashboard')

@app.route('/import/solr_dump/<filename>')
def import_solr_dump(filename=''):
    if filename:

        import_solr = Solr(core='hoe_users', query='id:%s' % filename, facet='false')
        import_solr.request()

        thedata = json.loads(import_solr.results[0].get('dump')[0])
        for doc in thedata:
            form = PUBTYPE2FORM.get(doc.get('pubtype')).from_json(doc)
            _record2solr(form)
        flash('%s records imported!' % len(thedata), 'success')

        return redirect('dashboard')

@app.route('/delete/solr_dump/<record_id>')
def delete_dump(record_id=''):
    delete_record_solr = Solr(core='hoe_users', del_id=record_id)
    delete_record_solr.delete()

    return jsonify({'deleted': True})

if __name__ == '__main__':
    app.run()
