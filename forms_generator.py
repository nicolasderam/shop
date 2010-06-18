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
from itools.datatypes import Unicode, Boolean, String
from itools.gettext import MSG
from itools.web import get_context

# Import from ikaaro
from ikaaro.forms import AutoForm, SelectWidget, TextWidget, BooleanCheckBox
from ikaaro.table import OrderedTable, OrderedTableFile

# Import from shop
from cross_selling_views import AddProduct_View
from products.models import get_real_datatype, get_default_widget_shop
from products.enumerate import Datatypes
from utils_views import AutomaticEditView


class ShopForm_Display(AutoForm):

    access = True


    def get_submit_value(self):
        context = get_context()
        return context.resource.get_property('submit_value')

    submit_value = property(get_submit_value, None, None, '')



    def get_title(self, context):
        return context.resource.get_title()


    def get_value(self, resource, context, name, datatype):
        return context.query.get(name) or datatype.get_default()


    def get_schema(self, resource, context):
        schema = {}
        handler = resource.handler
        get_value = handler.get_record_value
        for record in handler.get_records():
            name = get_value(record, 'name')
            datatype = get_real_datatype(handler, record)
            datatype.name = name
            schema[name] = datatype
        return schema


    def get_query_schema(self):
        context = get_context()
        resource = context.resource
        schema = {}
        for key, datatype in self.get_schema(resource, context).items():
            datatype.mandatory = False
            schema[key] = datatype
        return schema


    def get_widgets(self, resource, context):
        widgets = []
        handler = resource.handler
        get_value = handler.get_record_value
        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            datatype = get_real_datatype(handler, record)
            datatype.name = name
            widget = get_default_widget_shop(datatype)
            title = get_value(record, 'title')
            widget = widget(name, title=title, has_empty_option=False)
            widgets.append(widget)
        return widgets


    def action(self, resource, context):
        return 'ok'



class ShopFormTable(OrderedTableFile):

    record_properties = {
        'name': String,
        'title': Unicode(mandatory=True, multiple=True),
        'mandatory': Boolean,
        'multiple': Boolean,
        'datatype': Datatypes(mandatory=True, index='keyword'),
        }


class ShopForm(OrderedTable):

    class_id = 'shop-form'
    class_title = MSG(u'Shop form')
    class_version = '20090609'
    class_handler = ShopFormTable
    class_views = ['display', 'view', 'add_record'] #XXX We hide for instant

    display = ShopForm_Display()
    edit = AutomaticEditView()

    #PathSelectorWidget('name', title=MSG(u'Product'), action='add_product')
    add_product = AddProduct_View()

    form = [
        TextWidget('title', title=MSG(u'Title')),
        BooleanCheckBox('mandatory', title=MSG(u'Mandatory')),
        BooleanCheckBox('multiple', title=MSG(u'Multiple')),
        SelectWidget('datatype', title=MSG(u'Data Type')),
        ]

    edit_widgets = [TextWidget('submit_value', title=MSG(u'Submit value'))]
    edit_schema = {'submit_value': Unicode(multilingual=True)}

    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(OrderedTable.get_metadata_schema(),
                           cls.edit_schema)