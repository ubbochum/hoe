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
from flask import Flask, request, render_template, redirect, request, jsonify, flash, url_for, Markup
from flask.ext.babel import Babel
from flask.ext.bootstrap import Bootstrap
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required, make_secure_token
from flask.ext.paginate import Pagination
from flask_debugtoolbar import DebugToolbarExtension
from flask_wtf.csrf import CsrfProtect
from flask_redis import Redis
from urllib import parse
#from lxml import etree
from solr_handler import Solr

#from processors import mods_processor
from forms import *
from config import *

logging.basicConfig (level=logging.INFO,
    format='%(asctime)s %(levelname)-4s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
)

app = Flask(__name__)
app.debug = True
app.testing = True
app.secret_key = 'goidheuhfgreo'
toolbar = DebugToolbarExtension(app)

app.config['REDIS_HOST'] = '/tmp/redis.sock'
redis_store = Redis(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = 'strong'

babel = Babel(app)

bootstrap = Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True

CsrfProtect(app)

wtforms_json.init()

FORM_COUNT_RE = re.compile('-\d+$')

@app.template_filter('rem_form_count')
def rem_form_count_filter(mystring):
    '''Remove trailing form counts to display only categories in FormField/FieldList combinations.'''
    return FORM_COUNT_RE.sub('', mystring)

@app.template_filter('mk_time')
def mk_time_filter(mytime):
    return datetime.datetime.strptime(mytime, '%Y-%m-%dT%H:%M:%S.%fZ')

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

def solr_converter(form, action):
    if action == 'delete':
        resp = requests.get('http://127.0.0.1:8983/solr/hoe/update?commit=true&stream.body=%3Cdelete%3E%3Cid%3E' + form.data.get('id') + '%3C/id%3E%3C/delete%3E')
        #logging.info(resp)
        return True
    solr_data = {}
    wtf = json.dumps(form.data)
    solr_data.setdefault('wtf_json', wtf)
    for field in form.data:
        #logging.info('%s => %s' % (field, form.data.get(field)))
        if field == 'created':
            solr_data.setdefault('recordCreationDate', form.data.get(field).replace(' ', 'T') + 'Z')
        elif field == 'changed':
            solr_data.setdefault('recordChangeDate', form.data.get(field).replace(' ', 'T') + 'Z')
        elif field == 'title':
            solr_data.setdefault('title', form.data.get(field))
            solr_data.setdefault('exacttitle', form.data.get(field))
        elif field == 'person':
            for person in form.data.get(field):
                solr_data.setdefault('person', person.get('name'))
                solr_data.setdefault('fperson', person.get('name'))
        elif field == 'keyword':
            for keyword in form.data.get(field):
                solr_data.setdefault('keyword', keyword.get('label'))
                solr_data.setdefault('fkeyword', keyword.get('label'))
        else:
            if form.data.get(field):
                solr_data.setdefault(field, form.data.get(field))

    solr = requests.post('http://127.0.0.1:8983/solr/hoe/update/json?commit=true', data=json.dumps([solr_data]),
                         headers={'Content-type': 'application/json'})

@app.route('/dashboard')
@login_required
def dashboard():
    page = int(request.args.get('page', 1))
    mystart = 0
    query = '*:*'
    filterquery = request.values.getlist('filter')
    # Solr(start=(page - 1) * 10, query=query, fquery=filterquery, sort=sorting)
    dashboard_solr = Solr(start=(page - 1) * 10, query=query, sort='created asc',
                          facet_fields=['pubtype', 'genre', 'language', 'fkeyword', 'issued', 'library_place', 'fperson'],
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

    return render_template('dashboard.html', records=dashboard_solr.results, facet_data=dashboard_solr.facets,
                           header=gettext('Dashboard'), site=theme(request.access_route),
                           offset=mystart - 1, query=query, filterquery=filterquery, pagination=pagination,
                           now=datetime.datetime.now()
                           )

@app.route('/create/<pubtype>', methods=['GET', 'POST'])
@login_required
def new_record(pubtype='article-journal', primary_id=''):
    PUBTYPE_MAP = {
        'manuscript': PrimaryForm(),
        'print': PrimaryForm(),
        'article-journal': ArticleForm(),
        'book': MonographForm(),
    }
    form = PUBTYPE_MAP.get(pubtype)
    #logging.info(form)
    if form.validate_on_submit():
        if form.errors:
            flash_errors(form)
            return render_template('test_form.html', form=form, header=gettext('New Record'),
                                   site=theme(request.access_route), action='create', pubtype=pubtype)
        solr_converter(form, action='create')
        return redirect(url_for('dashboard'))


    form.id.data = str(uuid.uuid4())
    form.created.data = datetime.datetime.now()
    form.changed.data = datetime.datetime.now()
    form.owner.data = current_user.id
    form.pubtype.data = pubtype
    form.keyword.append_entry()
    form.person.append_entry()
    form.person.append_entry()
    #form.corporation.append_entry()

    return render_template('test_form.html', form=form, header=gettext('New Record'), site=theme(request.access_route), pubtype=pubtype, action='create')

@app.route('/retrieve/<pubtype>/<record_id>')
def show_record(pubtype, record_id=''):
    show_record_solr = Solr(query='id:%s' % record_id)
    show_record_solr.request()

    thedata = json.loads(show_record_solr.results[0].get('wtf_json'))
    form = ''
    if pubtype == 'manuscript' or pubtype == 'print':
        form = PrimaryForm.from_json(thedata)
    elif pubtype == 'book':
        form = MonographForm.from_json(thedata)

    return render_template('record.html', record=form, header=form.data.get('title'), site=theme(request.access_route),
                           action='retrieve', record_id=record_id)

@app.route('/update/<pubtype>/<record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(record_id='', pubtype=''):
    form = ''
    if request.method == 'POST':
        if pubtype == 'manuscript' or pubtype == 'print':
            form = PrimaryForm()
        elif pubtype == 'book':
            form = MonographForm()
        if form.validate_on_submit():
            if form.errors:
                flash_errors(form)
                return render_template('test_form.html', form=form,
                                       header=gettext('Edit: %(title)s', title=form.data.get('title')),
                                       site=theme(request.access_route), action='update', pubtype=pubtype)
            solr_converter(form, action='update')
            return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        edit_record_solr = Solr(query='id:%s' % record_id)
        edit_record_solr.request()

        thedata = json.loads(edit_record_solr.results[0].get('wtf_json'))
        if pubtype == 'manuscript' or pubtype == 'print':
            form = PrimaryForm.from_json(thedata)
        elif pubtype == 'book':
            form = MonographForm.from_json(thedata)
        form.changed.data = datetime.datetime.now()

        return render_template('test_form.html', form=form, header=gettext('Edit: %(title)s', title=form.data.get('title')),
                           site=theme(request.access_route), action='update', pubtype=pubtype)

@app.route('/delete/<record_id>')
def delete_record(record_id=''):
    class DeleteDummy:
        data = {'id': record_id}

    form = DeleteDummy()
    solr_converter(form, action='delete')

    # return redirect(url_for('dashboard'))
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
        if redis_store.exists(id):
            _user = redis_store.hgetall(id)
            tmp = json.dumps(_user)
            _user = json.loads(tmp)
            self.name = _user.get('name')
            self.role = _user.get('role')
            self.email = _user.get('email')
            self.accesstoken = _user.get('accesstoken')

    def __repr__(self):
        return '<User %s: %s>' % (self.id, self.name)

    @classmethod
    def get_user(self_class, id):
        return redis_store.hgetall(id)

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
            if not redis_store.exists(request.form.get('username')):
                accesstoken = make_secure_token(
                    base64.b64encode(request.form.get('username').encode('ascii')) + base64.b64encode(
                        request.form.get('password').encode('ascii')))
                redis_store.hset(request.form.get('username'), 'name', '%s %s' % (authuser.get('given_name'), authuser.get('last_name')))
                redis_store.hset(request.form.get('username'), 'email', authuser.get('email'))
                redis_store.hset(request.form.get('username'), 'role', 'user')
                redis_store.hset(request.form.get('username'), 'accesstoken', accesstoken)
                user.name = '%s %s' % (authuser.get('given_name'), authuser.get('last_name'))
                user.email = authuser.get('email')
                user.accesstoken = accesstoken
            login_user(user)

            return redirect(next or url_for('index'))
        else:
            flash("Username and Password Don't Match", 'danger')
            return redirect('login')

    form = LoginForm()
    next = get_redirect_target()
    #return render_template('login.html', form=form, header='Sign In', next=next, orcid_sandbox_client_id=orcid_sandbox_client_id)
    return render_template('login.html', form=form, header='Sign In', next=next, site=theme(request.access_route))

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

@app.route('/edit/user/<loginid>',methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def register(loginid=None):
    form = UserForm()
    if form.validate_on_submit():
        if ORCID_RE.match(form.loginid.data):
            # TODO: Check with ORCID OAUTH
            pass
        else:
            # TODO: This isn't right yet...
            if current_user.role != 'admin' and not loginid and form.password.data.encode('ascii') != 'admin':
                response = requests.post('https://api-test.ub.rub.de/ldap/authenticate/',
                                         data={'nocheck': 'true',
                                               'userid': base64.b64encode(form.loginid.data.encode('ascii')),
                                               'passwd': base64.b64encode(form.password.data.encode('ascii'))})
                if str(response.status_code).startswith('4') or str(response.status_code).startswith('5'):
                    if response.status_code == 401:
                        flash('Invalid password. Please try agein...', 'danger')
                        #flash('%s (%s)' % (response.reason, response.status_code))
                    else:
                        flash('%s (%s)' % (response.reason, response.status_code))
                    return render_template('register.html', form=form, header='User Registration')

                hash = make_secure_token(
                    base64.b64encode(form.loginid.data.encode('ascii')) + base64.b64encode(form.password.data.encode('ascii')))
                redis_store.hset(form.loginid.data, 'auth_token', hash)

            redis_store.hset(form.loginid.data, 'email', form.email.data)
            redis_store.hset(form.loginid.data, 'name', form.name.data)
            redis_store.hset(form.loginid.data, 'role', form.role.data)

    if loginid:
        edit_user = redis_store.hgetall(loginid)
        tmp = json.dumps(edit_user)
        edit_user = json.loads(tmp)
        form.loginid.data = loginid
        form.name.data = edit_user.get('name')
        form.email.data = edit_user.get('email')
        form.role.data = edit_user.get('role')
    flash_errors(form)
    return render_template('register.html', form=form, header='User Registration', edit_user=loginid)

@app.route('/search')
def search():
    pagination = ''
    page = int(request.args.get('page', 1))
    #mypage = page
    query = request.args.get('q', '')#.decode('utf-8')
    logging.info(query)
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
        return render_template('resultlist.html', records=search_solr.results, pagination=pagination, facet_data=search_solr.facets, header=gettext('Resultlist'), site=theme(request.access_route), offset=mystart - 1, query=query, filterquery=filterquery)

if __name__ == '__main__':
    app.run()
