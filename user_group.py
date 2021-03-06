# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, Unicode
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.buttons import RemoveButton, RenameButton
from ikaaro.folder_views import Folder_BrowseContent, GoToSpecificDocument
from ikaaro.forms import BooleanRadio, MultilineWidget, TextWidget, XHTMLBody
from ikaaro.forms import RTEWidget
from ikaaro.webpage import WebPage

# Import from itws
from itws.views import AutomaticEditView

# Import from shop
from folder import ShopFolder
from shop_views import Shop_Register
from user import CustomerSchema


class Group_Register(Shop_Register):

    def get_group(self, context):
        return context.resource


class ShopUser_Group(ShopFolder):

    class_id = 'user-group'
    class_views = ['edit', 'goto_categories', 'register', 'schema', 'welcome']
    class_version = '20100719'
    class_title = MSG(u'User group')

    edit = AutomaticEditView()
    schema = GoToSpecificDocument(specific_document='schema',
                                  title=MSG(u'Schema'))
    welcome = GoToSpecificDocument(specific_document='welcome',
                                  title=MSG(u'Edit welcome page'))
    goto_categories = GoToSpecificDocument(
            specific_document='../../../categories',
            title=MSG(u'Revenir aux catégories'))
    register = Group_Register()

    edit_schema = {'register_title': Unicode(multilingual=True),
                   'register_body': XHTMLBody(multilingual=True),
                   'register_mail_subject': Unicode(multilingual=True),
                   'register_mail_body': Unicode(multilingual=True),
                   'validation_mail_subject': Unicode(multilingual=True),
                   'validation_mail_body': Unicode(multilingual=True),
                   'invalidation_mail_subject': Unicode(multilingual=True),
                   'invalidation_mail_body': Unicode(multilingual=True),
                   'hide_address_on_registration': Boolean,
                   'user_is_enabled_when_register': Boolean,
                   'use_default_price': Boolean,
                   'show_ht_price': Boolean,
                   'phone_is_mandatory_on_registration': Boolean,
                   'lastname_is_mandatory_on_registration': Boolean}

    edit_widgets = [TextWidget('register_title', title=MSG(u'Register view title ?')),
                    RTEWidget('register_body', title=MSG(u'Register body')),
                    TextWidget('register_mail_subject', title=MSG(u'Register mail subject')),
                    MultilineWidget('register_mail_body', title=MSG(u'Register mail body')),
                    TextWidget('validation_mail_subject', title=MSG(u'Validation mail subject')),
                    MultilineWidget('validation_mail_body', title=MSG(u'Validation mail body')),
                    TextWidget('invalidation_mail_subject', title=MSG(u'Invalidation mail subject')),
                    MultilineWidget('invalidation_mail_body', title=MSG(u'Invalidation mail body')),
                    BooleanRadio('hide_address_on_registration', title=MSG(u'Hide address on registration')),
                    BooleanRadio('user_is_enabled_when_register', title=MSG(u'User is enabled ?')),
                    BooleanRadio('use_default_price', title=MSG(u'Use default price ?')),
                    BooleanRadio('show_ht_price', title=MSG(u'Show HT price ?')),
                    BooleanRadio('lastname_is_mandatory_on_registration', title=MSG(u'Lastname is mandatory on registration ?')),
                    BooleanRadio('phone_is_mandatory_on_registration', title=MSG(u'Phone is mandatory on registration ?'))]



    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['welcome']


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        # Create group
        ShopFolder._make_resource(cls, folder, name, *args, **kw)
        # Group schema
        cls = CustomerSchema
        cls._make_resource(cls, folder, '%s/schema' % name)
        # Welcome Page
        cls = WebPage
        cls._make_resource(cls, folder, '%s/welcome' % name,
                                title={'en': u'Welcome'},
                                state='public')

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(),
                           cls.edit_schema)


    def get_dynamic_schema(self):
        schema = self.get_resource('schema')
        return schema.get_model_schema()


    def get_dynamic_widgets(self):
        schema = self.get_resource('schema')
        return schema.get_model_widgets()


    def get_register_mail_subject(self):
        subject = self.get_property('register_mail_subject')
        if subject:
            return subject
        return MSG(u"Inscription confirmation.").gettext()


    def get_register_mail_body(self):
        body = self.get_property('register_mail_body')
        if body:
            return body
        return MSG(u"Your inscription has been validated").gettext()


    def get_prefix(self):
        # Price prefix
        # XXX for future we should add group property to price
        if self.name == 'default':
            return ''
        return '%s-' % self.name



class Groups_View(Folder_BrowseContent):

    search_template = None

    table_actions = [RemoveButton, RenameButton]
    table_columns = [
        ('checkbox', None),
        ('icon', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ]



class ShopUser_Groups(ShopFolder):

    class_id = 'user-groups'
    class_title = MSG(u'User groups')
    class_version = '20100720'
    class_views = ['view']

    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['default']

    view = Groups_View()

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        ShopFolder._make_resource(cls, folder, name, *args, **kw)
        ShopUser_Group._make_resource(ShopUser_Group, folder, '%s/default' % name)


    def get_document_types(self):
        return [ShopUser_Group]
