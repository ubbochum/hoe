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

from flask import Markup
from flask.ext.babel import gettext, ngettext, lazy_gettext
from flask.ext.wtf import Form, RecaptchaField
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, FileField, HiddenField, FieldList, FormField, PasswordField, SelectMultipleField
from wtforms.validators import DataRequired, UUID, URL, Email, Optional, Regexp, ValidationError
from wtforms.widgets import TextInput
from re import IGNORECASE
import pyisbn

LICENSES = (
    ('', gettext('Select a License')),
    ('cc_zero', gettext('Creative Commons Zero - Public Domain')),
    ('cc_by', gettext('Creative Commons Attribution')),
    ('cc_by_sa', gettext('Creative Commons Attribution Share Alike')),
    ('cc_by_nd', gettext('Creative Commons Attribution No Derivatives'))
)

LANGUAGES = [
    ('', gettext('Select a Language')),
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
        ('tur', gettext('Turkish')),
]

def Isbn(form, field):
    theisbn = pyisbn.Isbn(field.data)
    if theisbn.validate() == False:
        raise ValidationError(gettext('Not a valid ISBN!'))

class CustomTextInput(TextInput):
    '''Enable both placeholder and help text descriptions.'''
    def __init__(self, **kwargs):
        self.params = kwargs
        super(CustomTextInput, self).__init__()

    def __call__(self, field, **kwargs):
        for param, value in self.params.items():
            kwargs.setdefault(param, value)
        return super(CustomTextInput, self).__call__(field, **kwargs)

class URIForm(Form):
    label = StringField(gettext('Label'), validators=[Optional()])
    uri = StringField(gettext('URI'), validators=[URL(), Optional()])

class PersonForm(Form):
    name = StringField(gettext('Name'), widget=CustomTextInput(placeholder=gettext('Family name, given name')))
    role = SelectMultipleField('Role', choices=[]) #  Use this as an interface: Roles are dependent on the publication type
    uri = StringField(gettext('URI'), validators=[URL(), Optional()])
    viaf = StringField(gettext('VIAF'), validators=[Optional()], description=Markup(gettext('<a href="http://www.viaf.org" target="_blank">Find in VIAF</a>')))
    isni = StringField(gettext('ISNI'), validators=[Optional()], description=Markup(gettext('<a href="http://www.isni.org" target="_blank">Find in ISNI</a>')))

    admin_only = ['viaf', 'isni']

class AdvancedPrintPersonForm(PersonForm):
    role = SelectMultipleField(gettext('Role'), choices=[
        ('', gettext('Select one or more Roles')),
        ('aut', gettext('Author')),
        ('aft', gettext('Author of Afterword')),
        ('aui', gettext('Author of Introduction')),
        ('edt', gettext('Editor')),
        ('trl', gettext('Translator')),
        ('hnr', gettext('Honoree')),
        ('ive', gettext('Interviewee')),
        ('ivr', gettext('Interviewer')),
        ('spk', gettext('Speaker')),
    ])

class PrintPersonForm(PersonForm):
    name_other = StringField(gettext('Name Variant'), widget=CustomTextInput(placeholder=gettext('Name variant for the person')))
    birth_date = StringField(gettext('Birth Date'))
    death_date = StringField(gettext('Death Date'))
    role = SelectMultipleField(gettext('Role'), choices=[
        ('', gettext('Select one or more Roles')),
        ('ann', gettext('Annotator')),
        ('aut', gettext('Author')),
        ('ato', gettext('Autographer')),
        ('bnd', gettext('Binder')),
        ('dte', gettext('Dedicatee')),
        ('dto', gettext('Dedicator')),
        ('fmo', gettext('Former Owner')),
        ('ilu', gettext('Illuminator')),
        ('pat', gettext('Patron')),
        ('prt', gettext('Printer')),
    ])

class CodexPersonForm(PrintPersonForm):
    role = SelectMultipleField(gettext('Role'), choices=[
        ('', gettext('Select one or more Roles')),
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

class CorporationForm(Form):
    name = StringField(gettext('Name'))
    role = SelectMultipleField(gettext('Role'), choices=[
        ('', gettext('Select one or more Roles')),
        ('edt', gettext('Editor')),
        ('his', gettext('Host institution')),
        ('fmo', gettext('Former Owner')),
    ])
    gnd = StringField(gettext('GND'), validators=[Optional(), Regexp('(1|10)\d{7}[0-9X]|[47]\d{6}-\d|[1-9]\d{0,7}-[0-9X]|3\d{7}[0-9X]')])
    viaf = StringField(gettext('VIAF'), validators=[Optional()])
    isni = StringField(gettext('ISNI'), validators=[Optional()])

    admin_only = ['gnd', 'viaf', 'isni']

class HasPartForm(Form):
    has_part = StringField(gettext('Has Part'))
    pass

class IsPartOfForm(Form):
    is_part_of = StringField(gettext('Is Part of'))

class OtherVersionForm(Form):
    other_version = StringField(gettext('Other Version'))
    pass

class CodexChapterRelationForm(IsPartOfForm):
    page_first = StringField(gettext('First Page or Folio'))
    page_last = StringField(gettext('Last Page or Folio'))

class PrintChapterRelationForm(CodexChapterRelationForm):
    volume = StringField(gettext('Volume'))

class ContainerRelationForm(IsPartOfForm):
    volume = StringField(gettext('Volume'), validators=[Optional()])

class MonographRelationForm(ContainerRelationForm):
    pass

class TranslatedTitleForm(Form):
    translated_title = StringField(gettext('Translated Title'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The translated title of the work')))
    language = SelectField(gettext('Language'), validators=[Optional()], choices=LANGUAGES)

class WorkForm(Form):
    pubtype = SelectField(gettext('Type'), validators=[Optional()], choices=[
        ('', gettext('Select a Publication Type')),
        ('ArticleJournal', gettext('Article in Journal')),
        ('Catalogue', gettext('Catalogue')),
        ('Chapter', gettext('Chapter')),
        ('CodexChapter', gettext('Chapter in Codex')),
        ('PrintChapter', gettext('Chapter in Print')),
        ('Codex', gettext('Codex')),
        ('Collection', gettext('Collection')),
        ('Conference', gettext('Conference')),
        ('Edition', gettext('Edition')),
        ('InternetDocument', gettext('Internet Document')),
        ('Journal', gettext('Journal')),
        ('Lecture', gettext('Lecture')),
        ('Monograph', gettext('Monograph')),
        ('Print', gettext('Print')),
        ('Series', gettext('Series')),
        ('Translation', gettext('Translation')),
        ('Other', gettext('Other')),
    ])
    title = StringField(gettext('Title'), validators=[DataRequired()], widget=CustomTextInput(placeholder=gettext('The title of the work')))
    subtitle = StringField(gettext('Subtitle'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The subtitle of the work')))
    title_supplement = StringField(gettext('Title Supplement'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('Additions to the title of the work')))
    title_translated = FieldList(FormField(TranslatedTitleForm), min_entries=1)
    transliterated_title = FieldList(StringField(gettext('Transliterated Title')), min_entries = 1)
    person = FieldList(FormField(PersonForm), min_entries=1)
    corporation = FieldList(FormField(CorporationForm), min_entries=1)
    uri = FieldList(StringField(gettext('URL'), validators=[URL(), Optional()]), min_entries=1)
    language = FieldList(SelectField(gettext('Language'), validators=[Optional()], choices=LANGUAGES), min_entries=1)
    note = TextAreaField(gettext('Notes'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('Additional information about the work')))
    accessed = StringField(gettext('Last Seen'), validators=[Optional(), Regexp('[12]\d{3}(?:-[01]\d)?(?:-[0123]\d)?')], widget=CustomTextInput(placeholder=gettext('YYYY-MM-DD')), description=gettext("If you don't know the month and/or day please use 01"))
    id = StringField(gettext('UUID'), validators=[UUID(), Optional()], widget=CustomTextInput(readonly='readonly', admin_only='admin_only'))
    created = StringField(gettext('Record Creation Date'), widget=CustomTextInput(readonly='readonly', admin_only='admin_only'))
    changed = StringField(gettext('Record Change Date'), widget=CustomTextInput(readonly='readonly', admin_only='admin_only'))
    owner = StringField(gettext('Owner'), validators=[DataRequired()], widget=CustomTextInput(readonly='readonly'))
    #deskman = StringField(gettext('Deskman'), validators=[Optional()])
    license = SelectField(gettext('License'), choices=LICENSES)
    is_part_of = FieldList(StringField(gettext('Is Part of')), min_entries=1)
    has_part = FieldList(StringField(gettext('Has Part')), min_entries=1)
    other_version = FieldList(StringField(gettext('Other Version')), min_entries=1)
    relation = FieldList(StringField(gettext('Is related to')), min_entries=1)
    key_publication = BooleanField(gettext('Key Publication'),
                                   description='A very important title to be included on a special publication list.')
    DOI = StringField(gettext('DOI'), validators=[Optional(), Regexp('^10.\d{4}/.+', IGNORECASE)])
    issued = StringField(gettext('Date'), validators=[Optional(), Regexp('[12]\d{3}(?:-[01]\d)?(?:-[0123]\d)?')], widget=CustomTextInput(placeholder=gettext('YYYY-MM-DD')), description=gettext("If you don't know the month and/or day please use 01"))
    circa = BooleanField(gettext('Estimated'))
    additions = StringField(gettext('Additions'), validators=[Optional()])
    keyword = FieldList(FormField(URIForm), min_entries=1)
    keyword_temporal = FieldList(StringField(gettext('Temporal'), validators=[Optional()]), min_entries=1)
    keyword_geographic = FieldList(StringField(gettext('Geographic'), validators=[Optional()]), min_entries=1)
    abstract = TextAreaField(gettext('Abstract'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('An abstract of the work')))
    number_of_pages = StringField(gettext('Extent'), validators=[Optional()])

    #admin_only = ['id', 'created', 'changed', 'owner', 'deskman','viaf', 'isni']
    #user_only = ['role']

class LibraryForm(URIForm):
    label = StringField(gettext('Library'), validators=[Optional()],
                          widget=CustomTextInput(placeholder=gettext('The library holding the work')))
    place = StringField(gettext('Place of the library'), validators=[Optional()],
                                widget=CustomTextInput(placeholder=gettext('Where the library is situated')))
    latitude = StringField(gettext('Latitude'))
    longitude = StringField(gettext('Longitude'))
    call_number = StringField(gettext('Call Number'), validators=[Optional()], widget=CustomTextInput(
        placeholder=gettext('The string indicating the location of the work in the library')))

class BasicPrintForm(WorkForm):
    publisher = StringField(gettext('Publisher'))
    publisher_place = StringField(gettext('Place'))
    library = FieldList(FormField(LibraryForm), min_entries=1)

class AdvancedPrintForm(BasicPrintForm):
    person = FieldList(FormField(AdvancedPrintPersonForm), min_entries=1)
    edition = StringField('Edition', validators=[Optional()])
    table_of_contents = StringField('Table of Contents', validators=[URL(), Optional()], widget=CustomTextInput(placeholder=gettext('e.g. http://d-nb.info/1035670232/04')))
    hbz_id = StringField(gettext('HBZ-ID'), validators=[Optional()])
    relation = FieldList(StringField(gettext('Primary Literature')), min_entries=1)

class ContainerForm(AdvancedPrintForm):
    number_of_volumes = StringField(gettext('Number of Volumes'), validators=[Optional()])
    is_part_of = FieldList(FormField(ContainerRelationForm), min_entries=1)
    ISBN = FieldList(StringField(gettext('ISBN'), validators=[Optional(), Isbn]), min_entries=1)

class CatalogueForm(ContainerForm):

    def groups(self):
        yield [
            {'group': [self.pubtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI, self.ISBN, self.hbz_id], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': gettext('Content')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class CollectionForm(ContainerForm):
    subtype = SelectField(gettext('Subtype'), validators=[Optional()], choices=[
        ('', gettext('Select a Subtype')),
        ('facsimile', gettext('Facsimile')),
        ('festschrift', gettext('Festschrift')),
        ('lexicon', gettext('Lexicon')),
    ])

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI, self.ISBN, self.hbz_id], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': gettext('Content')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class ConferenceForm(CollectionForm):
    event_name = StringField(gettext('Name of the event'), validators=[Optional()])
    startdate_conference = StringField(gettext('First day of the event'), validators=[Optional(), Regexp('[12]\d{3}(?:-[01]\d)?(?:-[0123]\d)?')], widget=CustomTextInput(placeholder=gettext('YYYY-MM-DD')), description=gettext("If you don't know the month and/or day please use 01"))
    enddate_conference = StringField(gettext('Last day of the event'), validators=[Optional(), Regexp('[12]\d{3}(?:-[01]\d)?(?:-[0123]\d)?')], widget=CustomTextInput(placeholder=gettext('YYYY-MM-DD')), description=gettext("If you don't know the month and/or day please use 01"))
    place = StringField(gettext('Location of the event'), validators=[Optional()])
    subtype = SelectField(gettext('Subtype'), validators=[Optional()], choices=[
        ('', gettext('Select a Subtype')),
        ('facsimile', gettext('Facsimile')),
        ('festschrift', gettext('Festschrift')),
    ])

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI, self.ISBN, self.hbz_id], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.event_name, self.startdate_conference, self.enddate_conference, self.place], 'label': gettext('Event')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword,self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': gettext('Content')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class EditionForm(CollectionForm):
    subtype = SelectField(gettext('Subtype'), validators=[Optional()], choices=[
        ('', gettext('Select a Subtype')),
        ('facsimile', gettext('Facsimile')),
        ('festschrift', gettext('Festschrift')),
    ])

class TranslationForm(EditionForm):
    pass

class MonographForm(AdvancedPrintForm):
    subtype = SelectField(gettext('Subtype'), validators=[Optional()], choices=[
        ('', gettext('Select a Subtype')),
        ('facsimile', gettext('Facsimile')),
        ('festschrift', gettext('Festschrift')),
    ])
    ISBN = FieldList(StringField(gettext('ISBN'), validators=[Optional(), Isbn]), min_entries=1)
    number_of_volumes = StringField('Number of Volumes', validators=[Optional()])
    is_part_of = FieldList(FormField(MonographRelationForm), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI, self.ISBN, self.hbz_id], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': gettext('Content')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class PrintForm(BasicPrintForm):
    genre = SelectField(gettext('Genre'), choices=[
        ('', gettext('Select a Genre')),
        ('apocalypse', gettext('Apocalypse')),
        ('artifact', gettext('Artifact')),
        ('chronicle', gettext('Chronicle')),
        ('church_chronicle', gettext('Church Chronicle')),
        ('chronograph', gettext('Chronograph')),
        ('cosmography', gettext('Cosmography')),
        ('encomium', gettext('Encomium')),
        ('hagiography', gettext('Hagiography')),
        ('history', gettext('History')),
        ('legend', gettext('Legend')),
        ('letter', gettext('Letter')),
        ('memoirs', gettext('Memoirs')),
        ('memorandum', gettext('Memorandum')),
        ('mirror', gettext('Mirror of princes')),
        ('panegyric', gettext('Panegyric')),
        ('parenesis', gettext('Parenesis')),
        ('poem', gettext('Poem')),
        ('polemic', gettext('Polemic')),
        ('prophesy', gettext('Prophesy')),
        ('proskynetarion', gettext('Proskynetarion')),
        ('psalter', gettext('Psalter')),
        ('threnody', gettext('Threnody')),
        ('verse_chronicle', gettext('Verse Chronicle')),
        ('vita', gettext('Vita')),
        ('other', gettext('Other'))
    ])
    person = FieldList(FormField(PrintPersonForm), min_entries=1)
    frontispiece = StringField(gettext('Frontispiece'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The text contained in the frontispiece of the book')))
    #frontispiece_img = FileField(gettext('Frontispiece Image'))
    #frontispiece_img_license = SelectField(gettext('License'), choices=LICENSES)
    incipit = TextAreaField(gettext('Incipit'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The first words of the work')))
    explicit = TextAreaField(gettext('Explicit'), validators=[Optional()],
                             widget=CustomTextInput(placeholder=gettext('The last words of the codex')))
    origin = StringField(gettext('Place of Origin'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The place the work originates in')))
    vignette = TextAreaField(gettext('Vignette'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext("A description of the book's vignette")))
    #vignette_img = FileField(gettext('Vignette Image'))
    #vignette_img_license = SelectField(gettext('License'), choices=LICENSES)
    printers_mark = StringField(gettext("Printer's Mark"), validators=[Optional()], widget=CustomTextInput(placeholder=gettext("The text contained in the printer's mark")))
    #printers_mark_img = FileField(gettext('Printers Mark Image'))
    #printers_mark_img_license = SelectField(gettext('License'), choices=LICENSES)
    printing_patent = StringField(gettext('Printing Patent'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The right to print a work')))
    publisher = StringField(gettext('Printer'))
    provenance = TextAreaField(gettext('Provenance'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('Information on the ownership of the work')))
    autograph_text = TextAreaField(gettext('Autograph'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The text of the autograph')))
    relation = FieldList(StringField(gettext('Secondary Literature')), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.genre, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.circa, self.language, self.accessed, self.number_of_pages, self.origin, self.provenance, self.additions,
                       self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                       ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.incipit, self.explicit, self.autograph_text, self.vignette, self.frontispiece], 'label': gettext('Content')},
            {'group': [self.publisher, self.publisher_place, self.printing_patent, self.printers_mark], 'label': gettext('Printer')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class CodexForm(WorkForm):
    genre = SelectField(gettext('Genre'), choices=[
        ('', gettext('Select a Genre')),
        ('apocalypse', gettext('Apocalypse')),
        ('artifact', gettext('Artifact')),
        ('chronicle', gettext('Chronicle')),
        ('church_chronicle', gettext('Church Chronicle')),
        ('chronograph', gettext('Chronograph')),
        ('cosmography', gettext('Cosmography')),
        ('encomium', gettext('Encomium')),
        ('hagiography', gettext('Hagiography')),
        ('history', gettext('History')),
        ('legend', gettext('Legend')),
        ('letter', gettext('Letter')),
        ('memoirs', gettext('Memoirs')),
        ('memorandum', gettext('Memorandum')),
        ('mirror', gettext('Mirror of princes')),
        ('panegyric', gettext('Panegyric')),
        ('parenesis', gettext('Parenesis')),
        ('poem', gettext('Poem')),
        ('polemic', gettext('Polemic')),
        ('prophesy', gettext('Prophesy')),
        ('proskynetarion', gettext('Proskynetarion')),
        ('psalter', gettext('Psalter')),
        ('threnody', gettext('Threnody')),
        ('verse_chronicle', gettext('Verse Chronicle')),
        ('vita', gettext('Vita')),
        ('other', gettext('Other'))
    ])
    person = FieldList(FormField(CodexPersonForm), min_entries=1)
    incipit = TextAreaField(gettext('Incipit'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The first words of the codex')))
    explicit = TextAreaField(gettext('Explicit'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The last words of the codex')))
    #vignette = TextAreaField(gettext('Vignette'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext("A description of the work's vignette")))
    #vignette_img = FileField(gettext('Vignette Image'))
    #vignette_img_license = SelectField(gettext('License'), choices=LICENSES)
    number_of_lines = StringField(gettext('Number of Lines'),  validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The number of the lines that the codex consists of')))
    library = FieldList(FormField(LibraryForm), min_entries=1)
    origin = StringField(gettext('Place of Origin'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The place the codex originated in')))
    provenance = TextAreaField(gettext('Provenance'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('Information on the ownership of the codex')))
    autograph_text = TextAreaField(gettext('Autograph'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The text of the autograph')))
    relation = FieldList(StringField(gettext('Secondary Literature')), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.genre, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.circa, self.language, self.accessed, self.number_of_pages, self.number_of_lines, self.origin, self.provenance, self.additions,
                       self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                       ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.incipit, self.explicit, self.autograph_text], 'label': gettext('Content')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class CodexChapterForm(WorkForm):
    genre = SelectField(gettext('Genre'), choices=[
        ('', gettext('Select a Genre')),
        ('apocalypse', gettext('Apocalypse')),
        ('artifact', gettext('Artifact')),
        ('chronicle', gettext('Chronicle')),
        ('church_chronicle', gettext('Church Chronicle')),
        ('chronograph', gettext('Chronograph')),
        ('cosmography', gettext('Cosmography')),
        ('encomium', gettext('Encomium')),
        ('hagiography', gettext('Hagiography')),
        ('history', gettext('History')),
        ('legend', gettext('Legend')),
        ('letter', gettext('Letter')),
        ('memoirs', gettext('Memoirs')),
        ('memorandum', gettext('Memorandum')),
        ('mirror', gettext('Mirror of princes')),
        ('panegyric', gettext('Panegyric')),
        ('parenesis', gettext('Parenesis')),
        ('poem', gettext('Poem')),
        ('polemic', gettext('Polemic')),
        ('prophesy', gettext('Prophesy')),
        ('proskynetarion', gettext('Proskynetarion')),
        ('psalter', gettext('Psalter')),
        ('threnody', gettext('Threnody')),
        ('verse_chronicle', gettext('Verse Chronicle')),
        ('vita', gettext('Vita')),
        ('other', gettext('Other'))
    ])
    person = FieldList(FormField(CodexPersonForm), min_entries=1)
    incipit = TextAreaField(gettext('Incipit'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The first words of the chapter')))
    explicit = TextAreaField(gettext('Explicit'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The last words of the chapter')))
    is_part_of = FieldList(FormField(CodexChapterRelationForm), min_entries=1)
    relation = FieldList(StringField(gettext('Secondary Literature')), min_entries=1)
    library = FieldList(FormField(LibraryForm), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.genre, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.incipit, self.explicit], 'label':gettext('Content')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class PrintChapterForm(CodexChapterForm):
    person = FieldList(FormField(PrintPersonForm), min_entries=1)
    vignette = TextAreaField(gettext('Vignette'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext("A description of the chapter's vignette")))
    is_part_of = FieldList(FormField(PrintChapterRelationForm), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.genre, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.incipit, self.explicit, self.vignette], 'label':gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class ChapterRelationForm(IsPartOfForm):
    page_first = StringField(gettext('First Page'))
    page_last = StringField(gettext('Last Page'))
    volume = StringField(gettext('Volume'))

class ArticleRelationForm(ChapterRelationForm):
    volume = StringField(gettext('Volume'))
    issue = StringField(gettext('Issue'))

class ContributionForm(WorkForm):
    #parent_title = StringField(gettext('Parent Title'), validators=[DataRequired()], widget=CustomTextInput(placeholder=gettext('The Title of the Parent Reference')))
    #parent_subtitle = StringField(gettext('Parent Subtitle'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The Subtitle of the Parent Reference')))
    subtype = SelectField(gettext('Subtype'), validators=[Optional()], choices=[
        ('', gettext('Select a Subtype')),
        ('afterword', gettext('Afterword')),
        ('facsimile', gettext('Facsimile')),
        ('festschrift', gettext('Festschrift')),
        ('introduction', gettext('Introduction')),
        ('lexicon_article', gettext('Article in Lexicon')),
        ('review', gettext('Review')),
        ('translation', gettext('Translation')),
    ])
    person = FieldList(FormField(AdvancedPrintPersonForm), min_entries=1)
    relation = FieldList(StringField(gettext('Primary Literature')), min_entries=1)

    #user_only = ['parent_title', 'parent_subtitle']

class ChapterForm(ContributionForm):
    is_part_of = FieldList(FormField(ChapterRelationForm), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract], 'label':gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class ArticleJournalForm(ContributionForm):
    is_part_of = FieldList(FormField(ArticleRelationForm), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of], 'label': gettext('Journal')},
            {'group': [self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract], 'label':gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class SerialForm(AdvancedPrintForm):
    ISSN = FieldList(StringField(gettext('ISSN'), widget=CustomTextInput(placeholder=gettext('e.g. 1932-6203'))), min_entries=1)
    ZDBID = StringField(gettext('ZDB-ID'), widget=CustomTextInput(placeholder=gettext('e.g. 2267670-3')))

class SeriesForm(SerialForm):
    number_of_volumes = StringField(gettext('Number of Volumes'), validators=[Optional()])

    def groups(self):
        yield [
            {'group': [self.pubtype, self.title, self.subtitle, self.title_supplement, self.language, self.title_translated,
                       self.transliterated_title, self.issued, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.ISSN, self.ZDBID, self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': gettext('Content')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class JournalForm(SerialForm):
    journal_abbreviation = FieldList(StringField(gettext('Journal Abbreviation'), widget=CustomTextInput(placeholder=gettext('The Abbreviated Title of the Journal'))), min_entries=1)
    subtype = SelectField(gettext('Subtype'), validators=[Optional()], choices=[
        ('', gettext('Select a Subtype')),
        ('facsimile', gettext('Facsimile')),
        ('festschrift', gettext('Festschrift')),
    ])

    def groups(self):
        yield [
            {'group': [self.pubtype, self.title, self.subtitle, self.journal_abbreviation, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.ISSN, self.ZDBID, self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': gettext('Content')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class InternetDocumentForm(WorkForm):
    subtype = SelectField(gettext('Subtype'), validators=[Optional()], choices=[
        ('', gettext('Select a Subtype')),
        ('lexicon_article', gettext('Article in Lexicon')),
        ('review', gettext('Review')),
    ])
    uri = FieldList(StringField(gettext('URL'), validators=[URL(), DataRequired()]), min_entries=1)
    last_update = StringField(gettext('Last update'), validators=[Optional(), Regexp('[12]\d{3}-[01]\d-[0123]\d')], widget=CustomTextInput(placeholder=gettext('YYYY-MM-DD'), description=gettext("If you don't know the month and/or day please use 01")))
    place = StringField(gettext('Place'), validators=[Optional()])
    number = FieldList(StringField('Number', validators=[Optional()]), min_entries=1)
    relation = FieldList(StringField(gettext('Primary Literature')), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.place, self.number_of_pages, self.number, self.accessed, self.last_update, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract], 'label':gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class LectureForm(WorkForm):
    lecture_title = StringField(gettext('Lecture Series'), validators=[Optional()], widget=CustomTextInput(placeholder=gettext('The Title of the Lecture Series')))
    event_name = StringField(gettext('Name of the event'), validators=[Optional()])
    startdate_conference = StringField(gettext('First day of the event'), validators=[Optional(), Regexp('[12]\d{3}-[01]\d-[0123]\d')], widget=CustomTextInput(placeholder=gettext('YYYY-MM-DD')), description=gettext("If you don't know the month and/or day please use 01"))
    enddate_conference = StringField(gettext('Last day of the event'), validators=[Optional(), Regexp('[12]\d{3}-[01]\d-[0123]\d')], widget=CustomTextInput(placeholder=gettext('YYYY-MM-DD')), description=gettext("If you don't know the month and/or day please use 01"))
    place = StringField(gettext('Location of the event'), validators=[Optional()])
    relation = FieldList(StringField(gettext('Primary Literature')), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.title, self.subtitle, self.title_supplement, self.title_translated, self.lecture_title,
                       self.transliterated_title, self.issued, self.language, self.place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.event_name, self.startdate_conference, self.enddate_conference, self.place], 'label': gettext('Event')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract], 'label':gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]

class OtherForm(WorkForm):
    subtype = SelectField(gettext('Subtype'), validators=[Optional()], choices=[
        ('', gettext('Select a Subtype')),
        ('lexicon_article', gettext('Article in Lexicon')),
        ('festschrift', gettext('Festschrift')),
        ('review', gettext('Review')),
    ])
    place = StringField(gettext('Place'), validators=[Optional()])
    edition = StringField('Edition', validators=[Optional()])
    number = FieldList(StringField('Number', validators=[Optional()]), min_entries=1)
    library = FieldList(FormField(LibraryForm), min_entries=1)
    relation = FieldList(StringField(gettext('Primary Literature')), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.place, self.number_of_pages, self.number, self.accessed, self.additions, self.note, self.license
                       ],
             'label': gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': gettext('ID')},
            {'group': [self.person], 'label': gettext('Person')},
            {'group': [self.corporation], 'label': gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': gettext('Relations')},
            {'group': [self.keyword, self.keyword_temporal, self.keyword_geographic
                        ],
             'label': gettext('Keyword')},
            {'group': [self.abstract], 'label':gettext('Content')},
            {'group': [self.library], 'label':gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': gettext('Administrative')},
        ]


########################################################################
class UserForm(Form):
    loginid = StringField(Markup('<i class="fa fa-user"></i> LoginID'), validators=[DataRequired(),])
    password = PasswordField(gettext('Password'))
    name = StringField(gettext('Name'), description=gettext('First Name Last Name'))
    email = StringField(gettext('Email'), validators=[Email(),])
    role = SelectField(gettext('Role'), choices=[
        ('', gettext('Select a Role')),
        ('user', gettext('User')),
        ('admin', gettext('Admin'))], default='user')
    recaptcha = RecaptchaField()
    #submit = SubmitField(Markup('<i class="fa fa-user-plus"></i> Register'))