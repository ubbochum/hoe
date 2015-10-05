from flask import Flask, render_template, redirect, request, jsonify, flash, url_for
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from flask.ext.login import LoginManager, UserMixin, current_user, login_user, logout_user
from flask_wtf.csrf import CsrfProtect
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, DateField, DateTimeField, PasswordField
from wtforms.validators import DataRequired, UUID, URL
from datetime import datetime
from elasticsearch import Elasticsearch
import uuid
import base64
import requests
import logging

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)-4s %(message)s',
                    datefmt='%a, %d %b %Y %H:%M:%S',
)
app = Flask(__name__)
app.secret_key = '6a7ccf65-a3e8-4cf2-9061-1f1cdfc09e84'
app.debug = True

login_manager = LoginManager()
login_manager.init_app(app)

bootstrap = Bootstrap(app)
app.config['BOOTSTRAP_SERVE_LOCAL'] = True
CsrfProtect(app)

es = Elasticsearch()

class UserNotFoundError(Exception):
    pass

class User(UserMixin):
    USERS = {
        'hagenaz1': {'role': 'admin', 'name': 'Andre Hagenbruch'}
    }

    def __init__(self, id):
        if not id in self.USERS:
            raise UserNotFoundError()
        self.id = id
        self.role = self.USERS.get(id).get('role')
        self.name = self.USERS.get(id).get('name')

    @classmethod
    def get(self_class, id):
        try:
            return self_class(id)
        except UserNotFoundError:
            return None

class LoginForm(Form):
    username = StringField('Username')
    password = PasswordField('Password')

@login_manager.user_loader
def load_user(id):
    return User.get(id)

@app.route('/login')
def login():
    form = LoginForm()
    return render_template('login.html', form=form, header='Sign In')

@app.route('/login/check', methods=('post',))
def login_check():
    user = User.get(request.form.get('username'))
    logging.info(request.form.get('username'))
    logging.info('hier: %s' % user)
    if not user:
        flash('Username Unknown')
    authuser = requests.post('https://api-test.ub.rub.de/ldap/authenticate/',
                  data={'nocheck': 'true', 'userid': base64.b64encode(request.form.get('username').encode('ascii')),
                        'passwd': base64.b64encode(request.form.get('password').encode('ascii'))}).json()
    logging.info(authuser)
    if authuser.get('email'):
        login_user(user)
    else:
        flash("Username and Password Don't Match")

    return redirect(url_for('index'))

class WorkForm(Form):
    url = StringField('URL', validators=[URL()])
    DOI = StringField('DOI') # TODO: Own validator?
    title = StringField('Title', validators=[DataRequired()])
    person = StringField('Person')
    person_uri = StringField('URI')
    corporation = StringField('Corporation')
    language = StringField('Language')
    issued = DateField('Publication Date')
    accessed = DateField('Last Seen')
    circa = BooleanField('Estimated')
    keyword = StringField('Keyword')
    keyword_uri = StringField('URI')
    description = TextAreaField('Description')

    type = SelectField('Type', validators=[DataRequired()], choices=[
        ("article-journal", 'Journal Article'),
        ("article-newspaper", 'Newspaper Article'),
        ("book", 'Book'),
        ("chapter", 'Chapter'),
        ("entry-encyclopedia", 'Entry in Encyclopedia'),
        ("manuscript", 'Manuscript'),
        ("map", 'Map'),
        ("paper-conference", 'Conference Paper'),
        ("personal_communication", 'Personal Communication'),
        ("review-book", 'Book Review'),
        ("thesis", 'Thesis'),
        ("treaty", 'Treaty'),
        ('print', 'Print')
    ])

    genre = SelectField('Genre', choices=[
        ('legend', 'Legend'),
        ('chronicle', 'Chronicle'),
        ('threnody', 'Threnody'),
        ('hagiography', 'Hagiography'),
        ('church_chronicle', 'Church Chronicle'),
        ('encomium', 'Encomium'),
        ('other', 'Other')
    ])

    note = TextAreaField('Notes')
    submit = SubmitField('Submit')
    id = StringField('UUID', validators=[UUID()])
    created = DateTimeField('Record Creation Date')
    changed = DateTimeField('Record Change Date')

    multiples = ('person', 'birth_date', 'death_date', 'keyword', 'person_uri', 'keyword_uri', 'role')
    date_fields = ('issued', 'accessed', 'birth_date', 'death_date', 'created', 'changed')

class PrintedWorkForm(WorkForm):
    publisher = StringField('Publisher')
    publisher_place = StringField('Place')

class ManuscriptForm(WorkForm):
    incipit = TextAreaField('Incipit')
    explicit = TextAreaField('Explicit')
    birth_date = DateField('Birth Date')
    death_date = DateField('Death Date')
    role = SelectField('Role', choices=[
        ('ann', 'Annotator'),
        ('aut', 'Author'),
        ('ato', 'Autographer'),
        ('bnd', 'Binder'),
        ('dte', 'Dedicatee'),
        ('dto', 'Dedicator'),
        ('fmo', 'Former Owner'),
        ('ilu', 'Illuminator'),
        ('pat', 'Patron'),
        ('scr', 'Scribe'),
    ])
    number_of_pages = StringField('Extent')
    number_of_lines = StringField('Number of Lines')
    library = StringField('Library')
    library_place = StringField('Library Place')
    call_number = StringField('Call Number')
    frontispiece = StringField('Frontispiece')
    provenance = StringField('Provenance')
    vignette = StringField('Vignette')
    origin_place = StringField('Place of Origin')

class PrintForm(ManuscriptForm):
    printers_mark = StringField("Printer's Mark")
    printing_place = StringField('Place of Printing')
    printing_patent = StringField('Printing Patent')

class TranslationForm(PrintedWorkForm):
    pass

class ArticleForm(PrintedWorkForm):
    container_title = StringField('Journal Title', validators=[DataRequired()])
    ISSN = StringField('ISSN')
    ZDBID = StringField('ZDB ID')
    volume = StringField('Volume')
    number = StringField('Issue')
    page_first = StringField('First Page')
    page_last = StringField('Last Page')
    role = SelectField('Role', choices=[
        ('aut', 'Author'),
        ('edt', 'Editor'),
        ('trl', 'Translator'),
        ('hnr', 'Honoree'),
        ('ive', 'Interviewee'),
        ('ivr', 'Interviewer'),
    ])

class CollectionForm(PrintedWorkForm):
    collection_title = StringField('Collection Title', validators=[DataRequired()])
    series_title = StringField('Series')
    page_first = StringField('First Page')
    page_last = StringField('Last Page')

class ConferenceForm(CollectionForm):
    date = StringField('Date')
    event = StringField('Conference')
    place = StringField('Place')

@app.route('/')
def index():
    return render_template('index.html', header='Project Description')

@app.route('/records', methods=('GET', 'POST'))
def records():
    resp = es.search(index='hoe', doc_type='record')
    #logging.info(resp.get('hits'))
    #return jsonify(resp.get('hits'))
    #logging.info(type(resp.get('hits')))
    return render_template('records.html', records=resp.get('hits'), header='Dashboard')

@app.route('/search', methods=('GET',))
def search():
    q = request.args.get('q')
    logging.info(q)
    # TODO...
    resp = es.search(index='hoe', doc_type='record', q=q)
    return render_template('resultlist.html', records=resp.get('hits'), header=q)

@app.route('/record/<record_id>', methods=('GET',))
def record(record_id=None):
    resp = es.get('hoe', record_id, doc_type='record')
    return render_template('record.html', record=resp.get('_source'), header=resp.get('_source').get('title'))

@app.route('/new/<primary_id>/article-journal/<record_id>', methods=('POST',))
@app.route('/new/<primary_id>/article-journal', methods=('GET',))
def article(primary_id=None, record_id=None):
    form = ArticleForm()
    if record_id:
        pass
    else:
        form.id = str(uuid.uuid4())
        form.accessed.data = datetime.today().strftime('%Y-%m-%d')
        form.role.default = 'aut'
        form.process()
        return render_template('article_form.html', form=form, header='New Record')

@app.route('/new/<record_id>', methods=('GET', 'POST'))
@app.route('/new', methods=('GET', 'POST'))
def new(record_id=None):
    form = ManuscriptForm()
    if record_id:
        multiple_cats = {}
        for cat in form.multiples:
            multiple_cats.setdefault(cat, request.form.getlist(cat))
            #del request.form[cat]
        myjson = {}
        myjson.setdefault('id', record_id)
        for mykey in request.form:
            #logging.info(mykey)
            #logging.info(request.form.getlist(mykey))
            if not mykey == 'csrf_token':
                if mykey not in form.multiples:
                    myvalue = request.form.getlist(mykey)
                    myvalue = myvalue[0]
                    if myvalue:
                        if mykey in form.date_fields:
                            date_parts = myvalue.split('-')
                            myvalue = {}
                            myvalue.setdefault('date-parts', date_parts)
                            if request.form.getlist('circa'):
                                myvalue.setdefault('circa', True)
                                del request.form['circa']
                        mykey = mykey.replace('_', '-')
                        myjson.setdefault(mykey, myvalue)

        for mykey in multiple_cats:
            myvalue = multiple_cats.get(mykey)
            if mykey == 'person':
                for name in myvalue:
                    logging.info(name)
                    # tmp = {}
                    first = ''
                    last = ''
                    uri = ''
                    role = ''
                    first, last = name.split(', ')

                    if multiple_cats.get('person_uri')[myvalue.index(name)]:
                        uri = multiple_cats.get('person_uri')[myvalue.index(name)]
                    if multiple_cats.get('role')[myvalue.index(name)]:
                        role = multiple_cats.get('role')[myvalue.index(name)]
                        logging.info(multiple_cats.get('role')[myvalue.index(name)])
                    if role == 'aut':
                        myjson.setdefault('author', []).append({'literal': name, 'family': last, 'given': first, 'uri': uri})
            elif mykey == 'keyword':
                for keyword in myvalue:
                    uri = ''

                    if multiple_cats.get('keyword_uri')[myvalue.index(keyword)]:
                        uri = multiple_cats.get('keyword_uri')[myvalue.index(keyword)]
                    myjson.setdefault('keywords', []).append({'label': keyword, 'uri': uri})

        logging.info(myjson)
        # indexed = {
        #     'date-parts': [
        #         datetime.now()[0],
        #         datetime.now()[1],
        #         datetime.now()[2],
        #     ]
        # }
        es.index(index='hoe', doc_type='record', id=record_id, body=myjson)

        return jsonify(myjson)
    else:
        form.id = str(uuid.uuid4())
        form.accessed.data = datetime.today().strftime('%Y-%m-%d')
        form.type.default = 'manuscript'
        form.role.default = 'aut'
        form.process()
        return render_template('primary_form.html', form=form, header='New Record')


if __name__ == '__main__':
    app.run()
