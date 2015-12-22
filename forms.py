from flask import Markup
from flask.ext.babel import gettext, ngettext, lazy_gettext
from flask.ext.wtf import Form, RecaptchaField
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, FileField, HiddenField, FieldList, FormField, PasswordField
from wtforms.validators import DataRequired, UUID, URL, Email, Optional
from wtforms.widgets import TextInput

LICENSES = (
    ('', 'Select a License'),
    ('cc_zero', 'Creative Commons Zero - Public Domain'),
    ('cc_by', 'Creative Commons Attribution'),
    ('cc_by_sa', 'Creative Commons Attribution Share Alike'),
    ('cc_by_nd', 'Creative Commons Attribution No Derivatives')
)

class CustomTextInput(TextInput):
    '''Enable both placeholder and help text descriptions.'''
    def __init__(self, **kwargs):
        self.params = kwargs
        super(CustomTextInput, self).__init__()

    def __call__(self, field, **kwargs):
        for param, value in self.params.items():
            kwargs.setdefault(param, value)
        return super(CustomTextInput, self).__call__(field, **kwargs)

class PersonForm(Form):
    name = StringField(gettext('Name'), widget=CustomTextInput(placeholder=gettext('Family name, given name')))
    role = SelectField('Role', choices=[]) #  Use this as an interface: Roles are dependent on the publication type
    uri = StringField(gettext('URI'), validators=[URL(), Optional()])

class PrintedWorkPersonForm(PersonForm):
    role = SelectField(gettext('Role'), choices=[
        ('', 'Select a Role'),
        ('aut', gettext('Author')),
        ('edt', gettext('Editor')),
        ('trl', gettext('Translator')),
        ('hnr', gettext('Honoree')),
        ('ive', gettext('Interviewee')),
        ('ivr', gettext('Interviewer')),
    ])

class PrimaryPersonForm(PersonForm):
    birth_date = StringField(gettext('Birth Date'))
    death_date = StringField(gettext('Death Date'))
    role = SelectField(gettext('Role'), choices=[
        ('', 'Select a Role'),
        ('ann', gettext('Annotator')),
        ('aut', gettext('Author')),
        ('ato', gettext('Autographer')),
        ('bnd', gettext('Binder')),
        ('dte', gettext('Dedicatee')),
        ('dto', gettext('Dedicator')),
        ('fmo', gettext('Former Owner')),
        ('ilu', gettext('Illuminator')),
        ('pat', gettext('Patron')),
        ('scr', gettext('Scribe')),
    ])

class KeywordForm(Form):
    label = StringField(gettext('Keyword'))
    uri = StringField(gettext('URI'))

class WorkForm(Form):
    title = StringField(gettext('Title'), validators=[DataRequired()])
    subtitle = StringField(gettext('Subtitle'))
    person = FieldList(FormField(PersonForm))
    corporation = StringField(gettext('Corporation'))
    issued = StringField(gettext('Publication Date'))
    accessed = StringField(gettext('Last Seen'))
    circa = BooleanField(gettext('Estimated'))
    language = SelectField(gettext('Language'), choices=[
        ('', 'Select a Language'),
        ('alb', gettext('Albanian')),
        ('ara', gettext('Arabic')),
        ('bos', gettext('Bosnian')),
        ('bul', gettext('Bulgarian')),
        ('hrv', gettext('Croatian')),
        ('dut', gettext('Dutch')),
        ('eng', gettext('English')),
        ('fre', gettext('French')),
        ('ger', gettext('German')),
        ('gre', gettext('Greek')),
        ('ita', gettext('Italian')),
        ('lat', gettext('Latin')),
        ('peo', gettext('Persian')),
        ('pol', gettext('Polish')),
        ('rum', gettext('Romanian')),
        ('rus', gettext('Russian')),
        ('srp', gettext('Serbian')),
        ('spa', gettext('Spanish')),
        ('tur', gettext('Turkish'))
    ])
    keyword = FieldList(FormField(KeywordForm))
    number_of_pages = StringField(gettext('Extent'))
    genre = SelectField(gettext('Genre'), choices=[
        ('', 'Select a Genre'),
        ('legend', gettext('Legend')),
        ('chronicle', gettext('Chronicle')),
        ('threnody', gettext('Threnody')),
        ('hagiography', gettext('Hagiography')),
        ('church_chronicle', gettext('Church Chronicle')),
        ('encomium', gettext('Encomium')),
        ('other', gettext('Other'))
    ])
    url = StringField(gettext('URL'), validators=[URL(), Optional()])
    DOI = StringField(gettext('DOI'))
    description = TextAreaField(gettext('Description'))
    note = TextAreaField(gettext('Notes'))
    #submit = SubmitField('Submit')
    id = StringField(gettext('UUID'), validators=[UUID()])
    created = StringField(gettext('Record Creation Date'))
    changed = StringField(gettext('Record Change Date'))
    owner = StringField(gettext('Owner'), validators=[DataRequired()],
                        widget=CustomTextInput(readonly='readonly', admin_only='admin_only'))

    #multiples = ('person', 'birth_date', 'death_date', 'keyword', 'person_uri', 'keyword_uri', 'role')
    #date_fields = ('issued', 'accessed', 'birth_date', 'death_date', 'created', 'changed')



class PrintedWorkForm(WorkForm):
    publisher = StringField(gettext('Publisher'))
    publisher_place = StringField(gettext('Place'))
    person = FieldList(FormField(PrintedWorkPersonForm))

class PrimaryForm(WorkForm):
    person = FieldList(FormField(PrimaryPersonForm))
    incipit = TextAreaField(gettext('Incipit'))
    explicit = TextAreaField(gettext('Explicit'))
    frontispiece = StringField(gettext('Frontispiece'))
    #frontispiece_img = FileField(gettext('Frontispiece Image'))
    #frontispiece_img_license = SelectField(gettext('License'), choices=LICENSES)
    vignette = StringField(gettext('Vignette'))
    #vignette_img = FileField(gettext('Vignette Image'))
    #vignette_img_license = SelectField(gettext('License'), choices=LICENSES)
    number_of_lines = StringField(gettext('Number of Lines'))
    origin_place = StringField(gettext('Place of Origin'))
    pubtype = SelectField(gettext('Type'), validators=[DataRequired()], choices=[
        ("manuscript", gettext('Manuscript')),
        ('print', gettext('Print'))
    ])
    library = StringField(gettext('Library'))
    library_place = StringField(gettext('Library Place'))
    call_number = StringField(gettext('Call Number'))
    provenance = StringField(gettext('Provenance'))
    printers_mark = StringField(gettext('Printers Mark'))
    #printers_mark_img = FileField(gettext('Printers Mark Image'))
    #printers_mark_img_license = SelectField(gettext('License'), choices=LICENSES)
    printing_place = StringField(gettext('Place of Printing'))
    printing_patent = StringField(gettext('Printing Patent'))

class TranslationEditionForm(PrintedWorkForm):
    ISBN = StringField(gettext('ISBN'))
    number_of_volumes = StringField(gettext('Number of Volumes'))
    translated_title = StringField(gettext('Translated Title'))
    edition = StringField(gettext('Edition'))
    series_title = StringField(gettext('Series'))
    volume_in_series = StringField(gettext('Volume in the Series'))
    pubtype = SelectField(gettext('Type'), validators=[DataRequired()], choices=[
        ("translation", gettext('Translation')),
        ('edition', gettext('Edition'))
    ])

class ContainerForm(PrintedWorkForm):
    container_title = StringField(gettext('Parent Title'), validators=[DataRequired()])
    container_subtitle = StringField(gettext('Parent Subtitle'))
    container_translated_title = StringField(gettext('Parent Translated Title'))
    ISSN = StringField(gettext('ISSN'))
    ZDBID = StringField(gettext('ZDB ID'))
    journalAbbreviation = StringField(gettext('Journal Abbreviation'))
    pubtype = SelectField(gettext('Type'), validators=[DataRequired()], choices=[
        ('journal', gettext('Journal')),
        ('collection', gettext('Collection')),
        ('conference', gettext('Conference'))
    ])

class ArticleForm(ContainerForm):
    volume = StringField(gettext('Volume'))
    number_of_volumes = StringField(gettext('Number of Volumes'))
    number = StringField(gettext('Issue'))
    page_first = StringField(gettext('First Page'))
    page_last = StringField(gettext('Last Page'))
    number_of_pages = StringField(gettext('Extent'))
    pubtype = HiddenField('article-journal')

class MonographForm(PrintedWorkForm):
    ISBN = StringField(gettext('ISBN'))
    translated_title = StringField(gettext('Translated Title'))
    number_of_volumes = StringField(gettext('Number of Volumes'))
    edition = StringField(gettext('Edition'))
    series_title = StringField(gettext('Series'))
    volume_in_series = StringField(gettext('Volume in the Series'))
    pubtype = HiddenField('book')

class CollectionForm(ContainerForm):
    series_title = StringField(gettext('Series'))
    volume_in_series = StringField(gettext('Volume in the Series'))
    number_of_volumes = StringField(gettext('Number of Volumes'))
    ISBN = StringField(gettext('ISBN'))
    edition = StringField(gettext('Edition'))
    pubtype = HiddenField('collection')
    translated_title = StringField(gettext('Translated Title'))

class ConferenceForm(CollectionForm):
    date = StringField(gettext('Date'))
    event = StringField(gettext('Conference'))
    place = StringField(gettext('Place'))
    pubtype = HiddenField('conference')

class ChapterForm(CollectionForm):
    page_first = StringField(gettext('First Page'))
    page_last = StringField(gettext('Last Page'))
    number_of_pages = StringField(gettext('Extent'))

########################################################################
class UserForm(Form):
    loginid = StringField(Markup('<i class="fa fa-user"></i> LoginID'), validators=[DataRequired(),])
    password = PasswordField(gettext('Password'))
    name = StringField(gettext('Name'), description=gettext('First Name Last Name'))
    email = StringField(gettext('Email'), validators=[Email(),])
    role = SelectField(gettext('Role'), choices=[('user', gettext('User')), ('admin', gettext('Admin'))], default='user')
    recaptcha = RecaptchaField()
    #submit = SubmitField(Markup('<i class="fa fa-user-plus"></i> Register'))