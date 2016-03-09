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
from flask.ext.babel import lazy_gettext
from flask.ext.wtf import Form, RecaptchaField
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, FileField, HiddenField, FieldList, FormField, PasswordField, SelectMultipleField
from wtforms.validators import DataRequired, UUID, URL, Email, Optional, Regexp, ValidationError
from wtforms.widgets import TextInput
from re import IGNORECASE
import pyisbn

LICENSES = (
    ('', lazy_gettext('Select a License')),
    ('cc_zero', lazy_gettext('Creative Commons Zero - Public Domain')),
    ('cc_by', lazy_gettext('Creative Commons Attribution')),
    ('cc_by_sa', lazy_gettext('Creative Commons Attribution Share Alike')),
    ('cc_by_nd', lazy_gettext('Creative Commons Attribution No Derivatives'))
)

LANGUAGES = [
    ('', lazy_gettext('Select a Language')),
        ('alb', lazy_gettext('Albanian')),
        ('ara', lazy_gettext('Arabic')),
        ('bos', lazy_gettext('Bosnian')),
        ('bul', lazy_gettext('Bulgarian')),
        ('hrv', lazy_gettext('Croatian')),
        ('dut', lazy_gettext('Dutch')),
        ('eng', lazy_gettext('English')),
        ('fre', lazy_gettext('French')),
        ('ger', lazy_gettext('German')),
        ('gre', lazy_gettext('Greek')),
        ('ita', lazy_gettext('Italian')),
        ('lat', lazy_gettext('Latin')),
        ('peo', lazy_gettext('Persian')),
        ('pol', lazy_gettext('Polish')),
        ('rum', lazy_gettext('Romanian')),
        ('rus', lazy_gettext('Russian')),
        ('srp', lazy_gettext('Serbian')),
        ('spa', lazy_gettext('Spanish')),
        ('tur', lazy_gettext('Turkish')),
]

def Isbn(form, field):
    theisbn = pyisbn.Isbn(field.data)
    if theisbn.validate() == False:
        raise ValidationError(lazy_gettext('Not a valid ISBN!'))

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
    label = StringField(lazy_gettext('Label'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The label of the keyword')))
    uri = StringField(lazy_gettext('URI'), validators=[URL(), Optional()], widget=CustomTextInput(placeholder=lazy_gettext('A valid URL starting with https:// or http://')))

class KeywordGeographicForm(URIForm):
    latitude = StringField(lazy_gettext('Latitude'), widget=CustomTextInput(placeholder=lazy_gettext('The north-south position of a place, e.g. 41.8919300')))
    longitude = StringField(lazy_gettext('Longitude'), widget=CustomTextInput(placeholder=lazy_gettext('The east-west position of a place, e.g. 12.5113300')))

class PersonForm(Form):
    name = StringField(lazy_gettext('Name'), widget=CustomTextInput(placeholder=lazy_gettext('Family name, given name')))
    role = SelectMultipleField('Role', choices=[]) #  Use this as an interface: Roles are dependent on the publication type
    uri = StringField(lazy_gettext('URI'), validators=[URL(), Optional()], widget=CustomTextInput(placeholder=lazy_gettext("e.g. https://en.wikipedia.org/wiki/Constantine_Lascaris")))
    viaf = StringField(lazy_gettext('VIAF'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext("ID in the Virtual International Authority File, e.g. 103841990")), description=Markup(lazy_gettext('<a href="http://www.viaf.org" target="_blank">Find in VIAF</a>')))
    isni = StringField(lazy_gettext('ISNI'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext("International Standard Name Identifier (0000000121238649)")), description=Markup(lazy_gettext('<a href="http://www.isni.org" target="_blank">Find in ISNI</a>')))

    admin_only = ['viaf', 'isni']

class AdvancedPrintPersonForm(PersonForm):
    role = SelectMultipleField(lazy_gettext('Role'), choices=[
        ('', lazy_gettext('Select one or more Roles')),
        ('aut', lazy_gettext('Author')),
        ('aft', lazy_gettext('Author of Afterword')),
        ('aui', lazy_gettext('Author of Introduction')),
        ('edt', lazy_gettext('Editor')),
        ('trl', lazy_gettext('Translator')),
        ('hnr', lazy_gettext('Honoree')),
        ('ive', lazy_gettext('Interviewee')),
        ('ivr', lazy_gettext('Interviewer')),
        ('spk', lazy_gettext('Speaker')),
    ])

class PrintPersonForm(PersonForm):
    name_other = StringField(lazy_gettext('Name Variant'), widget=CustomTextInput(placeholder=lazy_gettext('Name variant for the person')))
    birth_date = StringField(lazy_gettext('Birth Date'), widget=CustomTextInput(placeholder=lazy_gettext('The year the person was born, e.g. 1434')))
    death_date = StringField(lazy_gettext('Death Date'), widget=CustomTextInput(placeholder=lazy_gettext('The year the person died, e.g. 1501')))
    role = SelectMultipleField(lazy_gettext('Role'), choices=[
        ('', lazy_gettext('Select one or more Roles')),
        ('ann', lazy_gettext('Annotator')),
        ('aut', lazy_gettext('Author')),
        ('ato', lazy_gettext('Autographer')),
        ('bnd', lazy_gettext('Binder')),
        ('dte', lazy_gettext('Dedicatee')),
        ('dto', lazy_gettext('Dedicator')),
        ('fmo', lazy_gettext('Former Owner')),
        ('ilu', lazy_gettext('Illuminator')),
        ('pat', lazy_gettext('Patron')),
        ('prt', lazy_gettext('Printer')),
    ])

class CodexPersonForm(PrintPersonForm):
    role = SelectMultipleField(lazy_gettext('Role'), choices=[
        ('', lazy_gettext('Select one or more Roles')),
        ('ann', lazy_gettext('Annotator')),
        ('aut', lazy_gettext('Author')),
        ('ato', lazy_gettext('Autographer')),
        ('bnd', lazy_gettext('Binder')),
        ('dte', lazy_gettext('Dedicatee')),
        ('dto', lazy_gettext('Dedicator')),
        ('fmo', lazy_gettext('Former Owner')),
        ('ilu', lazy_gettext('Illuminator')),
        ('pat', lazy_gettext('Patron')),
        ('scr', lazy_gettext('Scribe')),
    ])

class CorporationForm(Form):
    name = StringField(lazy_gettext('Name'), widget=CustomTextInput(placeholder=lazy_gettext('The name of the corporation')))
    role = SelectMultipleField(lazy_gettext('Role'), choices=[
        ('', lazy_gettext('Select one or more Roles')),
        ('edt', lazy_gettext('Editor')),
        ('his', lazy_gettext('Host institution')),
        ('fmo', lazy_gettext('Former Owner')),
    ])
    #gnd = StringField(lazy_gettext('GND'), validators=[Optional(), Regexp('(1|10)\d{7}[0-9X]|[47]\d{6}-\d|[1-9]\d{0,7}-[0-9X]|3\d{7}[0-9X]')])
    viaf = StringField(lazy_gettext('VIAF'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext("ID in the Virtual International Authority File, e.g. 128484390")))
    isni = StringField(lazy_gettext('ISNI'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext("International Standard Name Identifier (0000000110337334)")))

    admin_only = ['viaf', 'isni']

class HasPartForm(Form):
    has_part = StringField(lazy_gettext('Has Part'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the record that is part of this record')))
    pass

class IsPartOfForm(Form):
    is_part_of = StringField(lazy_gettext('Is Part of'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the record this record is part of')))

class OtherVersionForm(Form):
    other_version = StringField(lazy_gettext('Other Version'))
    pass

class CodexChapterRelationForm(IsPartOfForm):
    page_first = StringField(lazy_gettext('First Page or Folio'), widget=CustomTextInput(placeholder=lazy_gettext("The first page or folio of the text, e.g. 7 or 7v")))
    page_last = StringField(lazy_gettext('Last Page or Folio'), widget=CustomTextInput(placeholder=lazy_gettext("The last page or folio of the text, e.g. 100 or 100r")))

class PrintChapterRelationForm(CodexChapterRelationForm):
    volume = StringField(lazy_gettext('Volume'), widget=CustomTextInput(placeholder=lazy_gettext("The number of the volume this chapter is part of")))

class ContainerRelationForm(IsPartOfForm):
    volume = StringField(lazy_gettext('Volume'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext("The number of the volume this work is part of")))

class MonographRelationForm(ContainerRelationForm):
    pass

class TranslatedTitleForm(Form):
    translated_title = StringField(lazy_gettext('Translated Title'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The translated title of the work')))
    language = SelectField(lazy_gettext('Language'), validators=[Optional()], choices=LANGUAGES)

class WorkForm(Form):
    pubtype = SelectField(lazy_gettext('Type'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Publication Type')),
        ('ArticleJournal', lazy_gettext('Article in Journal')),
        ('Catalogue', lazy_gettext('Catalogue')),
        ('Chapter', lazy_gettext('Chapter')),
        ('CodexChapter', lazy_gettext('Chapter in Codex')),
        ('PrintChapter', lazy_gettext('Chapter in Print')),
        ('Codex', lazy_gettext('Codex')),
        ('Collection', lazy_gettext('Collection')),
        ('Conference', lazy_gettext('Conference')),
        ('Edition', lazy_gettext('Edition')),
        ('InternetDocument', lazy_gettext('Internet Document')),
        ('Journal', lazy_gettext('Journal')),
        ('Lecture', lazy_gettext('Lecture')),
        ('Monograph', lazy_gettext('Monograph')),
        ('Print', lazy_gettext('Print')),
        ('Series', lazy_gettext('Series')),
        ('Translation', lazy_gettext('Translation')),
        ('Other', lazy_gettext('Other')),
    ])
    title = StringField(lazy_gettext('Title'), validators=[DataRequired()], widget=CustomTextInput(placeholder=lazy_gettext('The title of the work')))
    subtitle = StringField(lazy_gettext('Subtitle'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The subtitle of the work')))
    title_supplement = StringField(lazy_gettext('Title Supplement'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Additions to the title of the work')))
    title_translated = FieldList(FormField(TranslatedTitleForm), min_entries=1)
    transliterated_title = FieldList(StringField(lazy_gettext('Transliterated Title'), widget=CustomTextInput(placeholder=lazy_gettext('The transliterated title of the work'))), min_entries = 1)
    person = FieldList(FormField(PersonForm), min_entries=1)
    corporation = FieldList(FormField(CorporationForm), min_entries=1)
    uri = FieldList(StringField(lazy_gettext('URL'), validators=[URL(), Optional()], widget=CustomTextInput(placeholder=lazy_gettext('A valid URL starting with https:// or http://'))), min_entries=1)
    language = FieldList(SelectField(lazy_gettext('Language'), validators=[Optional()], choices=LANGUAGES), min_entries=1)
    note = TextAreaField(lazy_gettext('Notes'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Additional information about the work')))
    accessed = StringField(lazy_gettext('Last Seen'), validators=[Optional(), Regexp('[12]\d{3}(?:-[01]\d)?(?:-[0123]\d)?')], widget=CustomTextInput(placeholder=lazy_gettext('YYYY-MM-DD')), description=lazy_gettext("Enter the year (YYYY) if month and/or day are unknown"))
    id = StringField(lazy_gettext('UUID'), validators=[UUID(), Optional()], widget=CustomTextInput(readonly='readonly', admin_only='admin_only'))
    created = StringField(lazy_gettext('Record Creation Date'), widget=CustomTextInput(readonly='readonly', admin_only='admin_only'))
    changed = StringField(lazy_gettext('Record Change Date'), widget=CustomTextInput(readonly='readonly', admin_only='admin_only'))
    owner = StringField(lazy_gettext('Owner'), validators=[DataRequired()], widget=CustomTextInput(readonly='readonly'))
    #deskman = StringField(lazy_gettext('Deskman'), validators=[Optional()])
    license = SelectField(lazy_gettext('License'), choices=LICENSES)
    is_part_of = FieldList(StringField(lazy_gettext('Is Part of'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the record this record is part of'))), min_entries=1)
    has_part = FieldList(StringField(lazy_gettext('Has Part'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the record that is part of this record'))), min_entries=1)
    other_version = FieldList(StringField(lazy_gettext('Other Version'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the record this record is a different version of')), description=lazy_gettext("Other versions usually are translations and editions")), min_entries=1)
    relation = FieldList(StringField(lazy_gettext('Is related to')), min_entries=1)
    key_publication = BooleanField(lazy_gettext('Key Publication'),
                                   description=lazy_gettext('A very important title to be included on a special publication list.'))
    DOI = StringField(lazy_gettext('DOI'), validators=[Optional(), Regexp('^10.\d{4}/.+', IGNORECASE)], widget=CustomTextInput(placeholder=lazy_gettext('e.g. 10.1163/156852006777502081')))
    issued = StringField(lazy_gettext('Date'), validators=[Optional(), Regexp('[12]\d{3}(?:-[01]\d)?(?:-[0123]\d)?')], widget=CustomTextInput(placeholder=lazy_gettext('YYYY-MM-DD')), description=lazy_gettext("Enter the year (YYYY) if month and/or day are unknown"))
    circa = BooleanField(lazy_gettext('Estimated'), description=lazy_gettext("If the date is estimated please tick this box"))
    additions = StringField(lazy_gettext('Additions'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Additions to the work (graphic representations etc.)')))
    keyword = FieldList(FormField(URIForm), min_entries=1)
    #keyword_temporal = FieldList(StringField(lazy_gettext('Temporal'), validators=[Optional()]), min_entries=1)
    geographic = FieldList(FormField(KeywordGeographicForm), min_entries=1)
    abstract = TextAreaField(lazy_gettext('Abstract'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('An abstract of the work')))
    number_of_pages = StringField(lazy_gettext('Extent'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The number of the pages of the work, e.g. 20')))

    #admin_only = ['id', 'created', 'changed', 'owner', 'deskman','viaf', 'isni']
    #user_only = ['role']

class LibraryForm(URIForm):
    label = StringField(lazy_gettext('Library'), validators=[Optional()],
                          widget=CustomTextInput(placeholder=lazy_gettext('The library holding the work')))
    place = StringField(lazy_gettext('Place of the library'), validators=[Optional()],
                                widget=CustomTextInput(placeholder=lazy_gettext('Where the library is situated')))
    latitude = StringField(lazy_gettext('Latitude'), widget=CustomTextInput(placeholder=lazy_gettext('The north-south position of a place, e.g. 41.8919300')))
    longitude = StringField(lazy_gettext('Longitude'), widget=CustomTextInput(placeholder=lazy_gettext('The east-west position of a place, e.g. 12.5113300')))
    call_number = StringField(lazy_gettext('Call Number'), validators=[Optional()], widget=CustomTextInput(
        placeholder=lazy_gettext('The string indicating the location of the work in the library')))

class BasicPrintForm(WorkForm):
    publisher = StringField(lazy_gettext('Publisher'), widget=CustomTextInput(placeholder=lazy_gettext('The publisher of the work, e.g. Springer')))
    publisher_place = StringField(lazy_gettext('Place'), widget=CustomTextInput(placeholder=lazy_gettext('Where was the work published?')))
    library = FieldList(FormField(LibraryForm), min_entries=1)

class AdvancedPrintForm(BasicPrintForm):
    person = FieldList(FormField(AdvancedPrintPersonForm), min_entries=1)
    edition = StringField('Edition', validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Information on the edition of the work, e.g. "2nd revised ed."')))
    table_of_contents = StringField('Table of Contents', validators=[URL(), Optional()], widget=CustomTextInput(placeholder=lazy_gettext('e.g. http://d-nb.info/1035670232/04')))
    hbz_id = StringField(lazy_gettext('HBZ-ID'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The ID given the work by the HBZ, e.g. HT018536436')))
    relation = FieldList(StringField(lazy_gettext('Primary Literature'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the related primary literature'))), min_entries=1)

    admin_only = ['hbz_id']

class ContainerForm(AdvancedPrintForm):
    number_of_volumes = StringField(lazy_gettext('Number of Volumes'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('How many volumes does the work consist of?')))
    is_part_of = FieldList(FormField(ContainerRelationForm), min_entries=1)
    ISBN = FieldList(StringField(lazy_gettext('ISBN'), validators=[Optional(), Isbn], widget=CustomTextInput(placeholder=lazy_gettext('The ISBN of the work, e.g. 978-1-107-09077-4'))), min_entries=1)

class CatalogueForm(ContainerForm):

    def groups(self):
        yield [
            {'group': [self.pubtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI, self.ISBN, self.hbz_id], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': lazy_gettext('Content')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class CollectionForm(ContainerForm):
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('facsimile', lazy_gettext('Facsimile')),
        ('festschrift', lazy_gettext('Festschrift')),
        ('lexicon', lazy_gettext('Lexicon')),
    ])

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI, self.ISBN, self.hbz_id], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': lazy_gettext('Content')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class ConferenceForm(CollectionForm):
    event_name = StringField(lazy_gettext('Name of the event'), widget=CustomTextInput(placeholder=lazy_gettext('e.g. "Congresso Nazionale di Studi Bizantini"')), validators=[Optional()])
    startdate_conference = StringField(lazy_gettext('First day of the event'), validators=[Optional(), Regexp('[12]\d{3}(?:-[01]\d)?(?:-[0123]\d)?')], widget=CustomTextInput(placeholder=lazy_gettext('YYYY-MM-DD')), description=lazy_gettext("Enter the year (YYYY) if month and/or day are unknown"))
    enddate_conference = StringField(lazy_gettext('Last day of the event'), validators=[Optional(), Regexp('[12]\d{3}(?:-[01]\d)?(?:-[0123]\d)?')], widget=CustomTextInput(placeholder=lazy_gettext('YYYY-MM-DD')), description=lazy_gettext("Enter the year (YYYY) if month and/or day are unknown"))
    place = StringField(lazy_gettext('Location of the event'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('e.g. "Paris"')))
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('facsimile', lazy_gettext('Facsimile')),
        ('festschrift', lazy_gettext('Festschrift')),
    ])

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI, self.ISBN, self.hbz_id], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.event_name, self.startdate_conference, self.enddate_conference, self.place], 'label': lazy_gettext('Event')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': lazy_gettext('Content')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class EditionForm(CollectionForm):
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('facsimile', lazy_gettext('Facsimile')),
        ('festschrift', lazy_gettext('Festschrift')),
    ])

class TranslationForm(EditionForm):
    pass

class MonographForm(AdvancedPrintForm):
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('facsimile', lazy_gettext('Facsimile')),
        ('festschrift', lazy_gettext('Festschrift')),
    ])
    ISBN = FieldList(StringField(lazy_gettext('ISBN'), validators=[Optional(), Isbn], widget=CustomTextInput(placeholder=lazy_gettext('The ISBN of the work, e.g. 978-1-107-09077-4'))), min_entries=1)
    number_of_volumes = StringField('Number of Volumes', validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('How many volumes does the work consist of?')))
    is_part_of = FieldList(FormField(MonographRelationForm), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI, self.ISBN, self.hbz_id], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': lazy_gettext('Content')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class PrintForm(BasicPrintForm):
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('translation', lazy_gettext('Translation')),
    ])
    genre = SelectField(lazy_gettext('Genre'), choices=[
        ('', lazy_gettext('Select a Genre')),
        ('apocalypse', lazy_gettext('Apocalypse')),
        ('artifact', lazy_gettext('Artifact')),
        ('autobiography', lazy_gettext('Autobiography')),
        ('cartulary', lazy_gettext('Cartulary')),
        ('chronicle', lazy_gettext('Chronicle')),
        ('church_chronicle', lazy_gettext('Church Chronicle')),
        ('chronograph', lazy_gettext('Chronograph')),
        ('cosmography', lazy_gettext('Cosmography')),
        ('encomium', lazy_gettext('Encomium')),
        ('false_document', lazy_gettext('False Document')),
        ('hagiography', lazy_gettext('Hagiography')),
        ('history', lazy_gettext('History')),
        ('hoe', lazy_gettext('History of the Ottoman Emperors')),
        ('legend', lazy_gettext('Legend')),
        ('letter', lazy_gettext('Letter')),
        ('memoirs', lazy_gettext('Memoirs')),
        ('memorandum', lazy_gettext('Memorandum')),
        ('mirror', lazy_gettext('Mirror of princes')),
        ('panegyric', lazy_gettext('Panegyric')),
        ('parenesis', lazy_gettext('Parenesis')),
        ('poem', lazy_gettext('Poem')),
        ('polemic', lazy_gettext('Polemic')),
        ('prophesy', lazy_gettext('Prophesy')),
        ('proskynetarion', lazy_gettext('Proskynetarion')),
        ('psalter', lazy_gettext('Psalter')),
        ('threnody', lazy_gettext('Threnody')),
        ('verse_chronicle', lazy_gettext('Verse Chronicle')),
        ('vita', lazy_gettext('Vita')),
        ('other', lazy_gettext('Other'))
    ])
    person = FieldList(FormField(PrintPersonForm), min_entries=1)
    frontispiece = StringField(lazy_gettext('Frontispiece'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The text contained in the frontispiece of the book')))
    #frontispiece_img = FileField(lazy_gettext('Frontispiece Image'))
    #frontispiece_img_license = SelectField(lazy_gettext('License'), choices=LICENSES)
    incipit = TextAreaField(lazy_gettext('Incipit'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The first words of the book')))
    explicit = TextAreaField(lazy_gettext('Explicit'), validators=[Optional()],
                             widget=CustomTextInput(placeholder=lazy_gettext('The last words of the book')))
    origin = StringField(lazy_gettext('Place of Origin'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The place the work originated in')))
    vignette = TextAreaField(lazy_gettext('Vignette'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext("Please describe the book's vignette here")))
    #vignette_img = FileField(lazy_gettext('Vignette Image'))
    #vignette_img_license = SelectField(lazy_gettext('License'), choices=LICENSES)
    printers_mark = StringField(lazy_gettext("Printer's Mark"), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext("Please put the text contained in the printer's mark here")))
    #printers_mark_img = FileField(lazy_gettext('Printers Mark Image'))
    #printers_mark_img_license = SelectField(lazy_gettext('License'), choices=LICENSES)
    printing_patent = StringField(lazy_gettext('Printing Patent'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Information on the right to print the work')))
    publisher = StringField(lazy_gettext('Printer'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Who printed the work?')))
    provenance = TextAreaField(lazy_gettext('Provenance'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Who owned the work before?')))
    autograph_text = TextAreaField(lazy_gettext('Autograph'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Please put the text of the autograph here')))
    relation = FieldList(StringField(lazy_gettext('Secondary Literature'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the related secondary literature'))), min_entries=1)
    date_range = StringField(lazy_gettext('Date Range'), widget=CustomTextInput(placeholder=lazy_gettext('YYYY-YYYY')))

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.genre, self.title, self.subtitle, self.title_supplement,
                       self.title_translated, self.transliterated_title, self.issued, self.circa, self.date_range,
                       self.language, self.accessed, self.number_of_pages, self.origin, self.provenance, self.additions,
                       self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                       ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.incipit, self.explicit, self.autograph_text, self.vignette, self.frontispiece], 'label': lazy_gettext('Content')},
            {'group': [self.publisher, self.publisher_place, self.printing_patent, self.printers_mark], 'label': lazy_gettext('Printer')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class CodexForm(WorkForm):
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('translation', lazy_gettext('Translation')),
    ])
    genre = SelectField(lazy_gettext('Genre'), choices=[
        ('', lazy_gettext('Select a Genre')),
        ('apocalypse', lazy_gettext('Apocalypse')),
        ('artifact', lazy_gettext('Artifact')),
        ('autobiography', lazy_gettext('Autobiography')),
        ('cartulary', lazy_gettext('Cartulary')),
        ('chronicle', lazy_gettext('Chronicle')),
        ('church_chronicle', lazy_gettext('Church Chronicle')),
        ('chronograph', lazy_gettext('Chronograph')),
        ('cosmography', lazy_gettext('Cosmography')),
        ('encomium', lazy_gettext('Encomium')),
        ('false_document', lazy_gettext('False Document')),
        ('hagiography', lazy_gettext('Hagiography')),
        ('history', lazy_gettext('History')),
        ('hoe', lazy_gettext('History of the Ottoman Emperors')),
        ('legend', lazy_gettext('Legend')),
        ('letter', lazy_gettext('Letter')),
        ('memoirs', lazy_gettext('Memoirs')),
        ('memorandum', lazy_gettext('Memorandum')),
        ('mirror', lazy_gettext('Mirror of princes')),
        ('panegyric', lazy_gettext('Panegyric')),
        ('parenesis', lazy_gettext('Parenesis')),
        ('poem', lazy_gettext('Poem')),
        ('polemic', lazy_gettext('Polemic')),
        ('prophesy', lazy_gettext('Prophesy')),
        ('proskynetarion', lazy_gettext('Proskynetarion')),
        ('psalter', lazy_gettext('Psalter')),
        ('threnody', lazy_gettext('Threnody')),
        ('verse_chronicle', lazy_gettext('Verse Chronicle')),
        ('vita', lazy_gettext('Vita')),
        ('other', lazy_gettext('Other'))
    ])
    person = FieldList(FormField(CodexPersonForm), min_entries=1)
    incipit = TextAreaField(lazy_gettext('Incipit'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The first words of the codex')))
    explicit = TextAreaField(lazy_gettext('Explicit'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The last words of the codex')))
    #vignette = TextAreaField(lazy_gettext('Vignette'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext("A description of the work's vignette")))
    #vignette_img = FileField(lazy_gettext('Vignette Image'))
    #vignette_img_license = SelectField(lazy_gettext('License'), choices=LICENSES)
    number_of_lines = StringField(lazy_gettext('Number of Lines'),  validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The number of lines the codex consists of')))
    library = FieldList(FormField(LibraryForm), min_entries=1)
    origin = StringField(lazy_gettext('Place of Origin'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The place the codex originated in')))
    provenance = TextAreaField(lazy_gettext('Provenance'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Who owned the codex before?')))
    autograph_text = TextAreaField(lazy_gettext('Autograph'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Please put the text of the autograph here')))
    relation = FieldList(StringField(lazy_gettext('Secondary Literature'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the related secondary literature'))), min_entries=1)
    date_range = StringField(lazy_gettext('Date Range'), widget=CustomTextInput(placeholder=lazy_gettext('YYYY-YYYY')))

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.genre, self.title, self.subtitle, self.title_supplement,
                       self.title_translated, self.transliterated_title, self.issued, self.circa, self.date_range,
                       self.language, self.accessed, self.number_of_pages, self.number_of_lines, self.origin,
                       self.provenance, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                       ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.incipit, self.explicit, self.autograph_text], 'label': lazy_gettext('Content')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class CodexChapterForm(WorkForm):
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('translation', lazy_gettext('Translation')),
    ])
    genre = SelectField(lazy_gettext('Genre'), choices=[
        ('', lazy_gettext('Select a Genre')),
        ('apocalypse', lazy_gettext('Apocalypse')),
        ('artifact', lazy_gettext('Artifact')),
        ('autobiography', lazy_gettext('Autobiography')),
        ('cartulary', lazy_gettext('Cartulary')),
        ('chronicle', lazy_gettext('Chronicle')),
        ('church_chronicle', lazy_gettext('Church Chronicle')),
        ('chronograph', lazy_gettext('Chronograph')),
        ('cosmography', lazy_gettext('Cosmography')),
        ('encomium', lazy_gettext('Encomium')),
        ('false_document', lazy_gettext('False Document')),
        ('hagiography', lazy_gettext('Hagiography')),
        ('history', lazy_gettext('History')),
        ('hoe', lazy_gettext('History of the Ottoman Emperors')),
        ('legend', lazy_gettext('Legend')),
        ('letter', lazy_gettext('Letter')),
        ('memoirs', lazy_gettext('Memoirs')),
        ('memorandum', lazy_gettext('Memorandum')),
        ('mirror', lazy_gettext('Mirror of princes')),
        ('panegyric', lazy_gettext('Panegyric')),
        ('parenesis', lazy_gettext('Parenesis')),
        ('poem', lazy_gettext('Poem')),
        ('polemic', lazy_gettext('Polemic')),
        ('prophesy', lazy_gettext('Prophesy')),
        ('proskynetarion', lazy_gettext('Proskynetarion')),
        ('psalter', lazy_gettext('Psalter')),
        ('threnody', lazy_gettext('Threnody')),
        ('verse_chronicle', lazy_gettext('Verse Chronicle')),
        ('vita', lazy_gettext('Vita')),
        ('other', lazy_gettext('Other'))
    ])
    person = FieldList(FormField(CodexPersonForm), min_entries=1)
    incipit = TextAreaField(lazy_gettext('Incipit'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The first words of the chapter')))
    explicit = TextAreaField(lazy_gettext('Explicit'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The last words of the chapter')))
    is_part_of = FieldList(FormField(CodexChapterRelationForm), min_entries=1)
    relation = FieldList(StringField(lazy_gettext('Secondary Literature'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the related secondary literature'))), min_entries=1)
    library = FieldList(FormField(LibraryForm), min_entries=1)
    date_range = StringField(lazy_gettext('Date Range'), widget=CustomTextInput(placeholder=lazy_gettext('YYYY-YYYY')))

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.genre, self.title, self.subtitle, self.title_supplement,
                       self.title_translated, self.transliterated_title, self.issued, self.date_range, self.language,
                       self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.incipit, self.explicit], 'label':lazy_gettext('Content')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class PrintChapterForm(CodexChapterForm):
    person = FieldList(FormField(PrintPersonForm), min_entries=1)
    vignette = TextAreaField(lazy_gettext('Vignette'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext("Please describe the chapter's vignette here")))
    is_part_of = FieldList(FormField(PrintChapterRelationForm), min_entries=1)
    date_range = StringField(lazy_gettext('Date Range'), widget=CustomTextInput(placeholder=lazy_gettext('YYYY-YYYY')))

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.genre, self.title, self.subtitle, self.title_supplement,
                       self.title_translated, self.transliterated_title, self.issued, self.date_range, self.language,
                       self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.incipit, self.explicit, self.vignette], 'label':lazy_gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class ChapterRelationForm(IsPartOfForm):
    page_first = StringField(lazy_gettext('First Page'), widget=CustomTextInput(placeholder=lazy_gettext('Please put the first page of the text here')))
    page_last = StringField(lazy_gettext('Last Page'), widget=CustomTextInput(placeholder=lazy_gettext('Please put the last page of the text here')))
    volume = StringField(lazy_gettext('Volume'), widget=CustomTextInput(placeholder=lazy_gettext("The number of the volume this chapter is part of")))

class ArticleRelationForm(ChapterRelationForm):
    volume = StringField(lazy_gettext('Volume'), widget=CustomTextInput(placeholder=lazy_gettext("The number of the volume this article is part of")))
    issue = StringField(lazy_gettext('Issue'), widget=CustomTextInput(placeholder=lazy_gettext("The number of the issue this article is part of")))

class ContributionForm(WorkForm):
    #parent_title = StringField(lazy_gettext('Parent Title'), validators=[DataRequired()], widget=CustomTextInput(placeholder=lazy_gettext('The Title of the Parent Reference')))
    #parent_subtitle = StringField(lazy_gettext('Parent Subtitle'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The Subtitle of the Parent Reference')))
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('afterword', lazy_gettext('Afterword')),
        ('facsimile', lazy_gettext('Facsimile')),
        ('festschrift', lazy_gettext('Festschrift')),
        ('introduction', lazy_gettext('Introduction')),
        ('lexicon_article', lazy_gettext('Article in Lexicon')),
        ('review', lazy_gettext('Review')),
        ('translation', lazy_gettext('Translation')),
    ])
    person = FieldList(FormField(AdvancedPrintPersonForm), min_entries=1)
    relation = FieldList(StringField(lazy_gettext('Primary Literature'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the related primary literature'))), min_entries=1)

    #user_only = ['parent_title', 'parent_subtitle']

class ChapterForm(ContributionForm):
    is_part_of = FieldList(FormField(ChapterRelationForm), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract], 'label':lazy_gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class ArticleJournalForm(ContributionForm):
    is_part_of = FieldList(FormField(ArticleRelationForm), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of], 'label': lazy_gettext('Journal')},
            {'group': [self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract], 'label':lazy_gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class SerialForm(AdvancedPrintForm):
    ISSN = FieldList(StringField(lazy_gettext('ISSN'), widget=CustomTextInput(placeholder=lazy_gettext('e.g. 1932-6203'))), min_entries=1)
    ZDBID = StringField(lazy_gettext('ZDB-ID'), widget=CustomTextInput(placeholder=lazy_gettext('e.g. 2267670-3')))

class SeriesForm(SerialForm):
    number_of_volumes = StringField(lazy_gettext('Number of Volumes'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Please put the number of volumes of the series here')))

    def groups(self):
        yield [
            {'group': [self.pubtype, self.title, self.subtitle, self.title_supplement, self.language, self.title_translated,
                       self.transliterated_title, self.issued, self.number_of_volumes, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.ISSN, self.ZDBID, self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': lazy_gettext('Content')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class JournalForm(SerialForm):
    journal_abbreviation = FieldList(StringField(lazy_gettext('Journal Abbreviation'), widget=CustomTextInput(placeholder=lazy_gettext('Please put the abbreviated title of the journal here'))), min_entries=1)
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('facsimile', lazy_gettext('Facsimile')),
        ('festschrift', lazy_gettext('Festschrift')),
    ])

    def groups(self):
        yield [
            {'group': [self.pubtype, self.title, self.subtitle, self.journal_abbreviation, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.publisher, self.publisher_place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.ISSN, self.ZDBID, self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract, self.table_of_contents], 'label': lazy_gettext('Content')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class InternetDocumentForm(WorkForm):
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('lexicon_article', lazy_gettext('Article in Lexicon')),
        ('review', lazy_gettext('Review')),
    ])
    #uri = FieldList(StringField(lazy_gettext('URL'), widget=CustomTextInput(placeholder=lazy_gettext('A valid URL starting with https:// or http://')), validators=[URL(), DataRequired()]), min_entries=1)
    last_update = StringField(lazy_gettext('Last update'), validators=[Optional(), Regexp('[12]\d{3}(?:-[01]\d)?(?:-[0123]\d)?')], widget=CustomTextInput(placeholder=lazy_gettext('YYYY-MM-DD'), description=lazy_gettext("Enter the year (YYYY) if month and/or day are unknown")))
    place = StringField(lazy_gettext('Place'), widget=CustomTextInput(placeholder=lazy_gettext('Where was the document published?'), validators=[Optional()]))
    number = FieldList(StringField(lazy_gettext('Number'), widget=CustomTextInput(placeholder=lazy_gettext('Does the document have a number?'), validators=[Optional()])), min_entries=1)
    relation = FieldList(StringField(lazy_gettext('Primary Literature'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the related primary literature'))), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.place, self.number_of_pages, self.number, self.accessed, self.last_update, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract], 'label':lazy_gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class LectureForm(WorkForm):
    lecture_title = StringField(lazy_gettext('Lecture Series'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('The title of the lecture series')))
    event_name = StringField(lazy_gettext('Name of the event'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('e.g. "Congresso Nazionale di Studi Bizantini"')))
    startdate_conference = StringField(lazy_gettext('First day of the event'), validators=[Optional(), Regexp('[12]\d{3}-[01]\d-[0123]\d')], widget=CustomTextInput(placeholder=lazy_gettext('YYYY-MM-DD')), description=lazy_gettext("Enter the year (YYYY) if month and/or day are unknown"))
    enddate_conference = StringField(lazy_gettext('Last day of the event'), validators=[Optional(), Regexp('[12]\d{3}-[01]\d-[0123]\d')], widget=CustomTextInput(placeholder=lazy_gettext('YYYY-MM-DD')), description=lazy_gettext("Enter the year (YYYY) if month and/or day are unknown"))
    place = StringField(lazy_gettext('Location of the event'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('e.g. "Paris"')))
    relation = FieldList(StringField(lazy_gettext('Primary Literature'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the related primary literature'))), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.title, self.subtitle, self.title_supplement, self.title_translated, self.lecture_title,
                       self.transliterated_title, self.issued, self.language, self.place, self.number_of_pages, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.event_name, self.startdate_conference, self.enddate_conference, self.place], 'label': lazy_gettext('Event')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract], 'label':lazy_gettext('Content')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class OtherForm(WorkForm):
    subtype = SelectField(lazy_gettext('Subtype'), validators=[Optional()], choices=[
        ('', lazy_gettext('Select a Subtype')),
        ('lexicon_article', lazy_gettext('Article in Lexicon')),
        ('festschrift', lazy_gettext('Festschrift')),
        ('review', lazy_gettext('Review')),
    ])
    place = StringField(lazy_gettext('Place'), validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('e.g. "Paris"')))
    edition = StringField('Edition', validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Information on the edition of the work, e.g. "2nd revised ed."')))
    number = FieldList(StringField('Number', validators=[Optional()], widget=CustomTextInput(placeholder=lazy_gettext('Does the document have a number?'))), min_entries=1)
    library = FieldList(FormField(LibraryForm), min_entries=1)
    relation = FieldList(StringField(lazy_gettext('Primary Literature'), widget=CustomTextInput(placeholder=lazy_gettext('The ID of the related primary literature'))), min_entries=1)

    def groups(self):
        yield [
            {'group': [self.pubtype, self.subtype, self.title, self.subtitle, self.title_supplement, self.title_translated,
                       self.transliterated_title, self.issued, self.language, self.edition, self.place, self.number_of_pages, self.number, self.accessed, self.additions, self.note, self.license
                       ],
             'label': lazy_gettext('Basic')},
            {'group': [self.uri, self.DOI], 'label': lazy_gettext('ID')},
            {'group': [self.person], 'label': lazy_gettext('Person')},
            {'group': [self.corporation], 'label': lazy_gettext('Corporation')},
            {'group': [self.is_part_of, self.has_part, self.other_version, self.relation], 'label': lazy_gettext('Relations')},
            {'group': [self.keyword, self.geographic
                        ],
             'label': lazy_gettext('Keyword')},
            {'group': [self.abstract], 'label':lazy_gettext('Content')},
            {'group': [self.library], 'label':lazy_gettext('Library')},
            {'group': [self.id, self.created, self.changed, self.owner, self.key_publication],
             'label': lazy_gettext('Administrative')},
        ]

class FileUploadForm(Form):
    file = FileField(lazy_gettext('Solr Dump'))
    submit = SubmitField(lazy_gettext('Send File'))

########################################################################
class UserForm(Form):
    loginid = StringField(Markup('<i class="fa fa-user"></i> LoginID'), validators=[DataRequired(),])
    password = PasswordField(lazy_gettext('Password'))
    name = StringField(lazy_gettext('Name'), description=lazy_gettext('First Name Last Name'))
    email = StringField(lazy_gettext('Email'), validators=[Email(),])
    role = SelectField(lazy_gettext('Role'), choices=[
        ('', lazy_gettext('Select a Role')),
        ('user', lazy_gettext('User')),
        ('admin', lazy_gettext('Admin'))], default='user')
    recaptcha = RecaptchaField()
    #submit = SubmitField(Markup('<i class="fa fa-user-plus"></i> Register'))