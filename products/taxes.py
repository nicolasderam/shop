# -*- coding: UTF-8 -*-
# Copyright (C) 2009 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Enumerate, Decimal, Boolean
from itools.gettext import MSG
from itools.uri import get_uri_name
from itools.web import get_context

# Import from ikaaro
from ikaaro.forms import SelectWidget, Widget
from ikaaro.registry import register_resource_class
from ikaaro.table import OrderedTableFile, OrderedTable
from ikaaro.table_views import OrderedTable_View
from ikaaro.buttons import OrderUpButton, OrderDownButton
from ikaaro.buttons import OrderBottomButton, OrderTopButton

# Import from shop
from shop.datatypes import UserGroup_Enumerate
from shop.enumerates import Devises
from shop.utils import get_shop


class TaxesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        if get_context().resource is None:
            return []
        shop = get_shop(get_context().resource)
        taxes = shop.get_resource('taxes').handler
        return [
            {'name': str(x.id),
             'value': taxes.get_record_value(x, 'value')}
            for x in taxes.get_records_in_order()]



class Taxes_TableHandler(OrderedTableFile):

    record_properties = {'value': Decimal}



class Taxes_TableResource(OrderedTable):

    class_id = 'shop-taxes'
    class_title = MSG(u'Taxes')
    class_handler = Taxes_TableHandler

    table_actions = [OrderUpButton, OrderDownButton, OrderTopButton,
                     OrderBottomButton]
    view = OrderedTable_View(table_actions=table_actions)


class PriceWidget(Widget):

    template = 'ui/backoffice/widgets/taxes.xml'
    prefix = ''

    def get_template(self, datatype, value):
        context = get_context()
        handler = context.root.get_resource(self.template)
        return handler.events


    def get_namespace(self, datatype, value):
        # XXX Hack to get tax value (and keep it when submit form)
        context = get_context()
        submit = (context.method == 'POST')
        prefix = self.prefix
        if submit:
            tax_value = context.get_form_value('%stax' % prefix, type=TaxesEnumerate)
            has_reduction = context.get_form_value('%shas_reduction' % prefix, type=Boolean)
            reduce_pre_tax_price = context.get_form_value('%sreduce-pre-tax-price' % prefix)
        else:
            tax_value = context.resource.get_property('%stax' % prefix)
            has_reduction = context.resource.get_property('%shas_reduction' % prefix)
            reduce_pre_tax_price = context.resource.get_property('%sreduce-pre-tax-price' % prefix)
        taxes = SelectWidget('%stax' % prefix, css='tax-widget', has_empty_option=False)
        # Devise
        shop = get_shop(context.resource)
        devise = shop.get_property('devise')
        symbol = Devises.get_symbol(devise)
        # Return namespace
        return {'widget_name': self.name,
                'pre-tax-price': value,
                'prefix': prefix,
                'devise': symbol,
                'reduce-pre-tax-price': reduce_pre_tax_price,
                'has_reduction': has_reduction,
                'taxes': taxes.to_html(TaxesEnumerate, tax_value)}


class PricesWidget(Widget):

    template = 'ui/backoffice/widgets/prices.xml'

    def get_template(self, datatype, value):
        context = get_context()
        handler = context.root.get_resource(self.template)
        return handler.events


    def get_namespace(self, datatype, value):
        context = get_context()
        namespace = {'groups': []}
        is_product = context.resource.class_id == 'product'
        if is_product:
            not_buyable_by_groups = context.resource.get_property('not_buyable_by_groups')
        else:
            not_buyable_by_groups = []
        for group in UserGroup_Enumerate.get_options():
            prefix = ''
            group['id'] = get_uri_name(group['name'])
            if group['id'] != 'default':
                prefix = '%s-' % group['id']
            group['not_buyable'] = group['name'] in not_buyable_by_groups
            widget_name = '%spre-tax-price' % prefix
            if is_product:
                value = context.resource.get_property(widget_name)
            else:
                value = None
            group['widget'] = PriceWidget(widget_name,
                                prefix=prefix).to_html(None, value)
            namespace['groups'].append(group)
        return namespace





register_resource_class(Taxes_TableResource)
