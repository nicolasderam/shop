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

# Import from standard library
from operator import itemgetter

# Import from itools
from itools.core import merge_dicts
from itools.datatypes import Boolean, String
from itools.gettext import MSG
from itools.i18n import format_datetime, format_date
from itools.stl import stl
from itools.xapian import PhraseQuery
from itools.xml import XMLParser
from itools.web import STLView

# Import from ikaaro
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.forms import stl_namespaces
from ikaaro.table_views import Table_View
from ikaaro.views import BrowseForm

# Import from shop
from shop.datatypes import Civilite
from shop.utils import get_shop



class OrdersProductsView(Table_View):

    columns = [
        ('checkbox', None),
        ('name', MSG(u'Product')),
        ('unit_price', MSG(u'Unit price')),
        ('quantity', MSG(u'Quantity')),
        ('total_price', MSG(u'Total price')),
        ]

    def get_table_columns(self, resource, context):
        return self.columns


    def get_item_value(self, resource, context, item, column):
        value = Table_View.get_item_value(self, resource, context, item, column)
        if column == 'name':
            shop = get_shop(resource)
            ref = item.get_value('name')
            produit = shop.get_resource('products/%s' % ref, soft=True)
            if not produit:
                return ref
            return (produit.name, resource.get_pathto(produit))
        elif column == 'unit_price':
            return u'%s €' % value
        elif column == 'total_price':
            total_price = item.get_value('quantity') * item.get_value('unit_price')
            return u'%s €' % total_price
        return value


class OrderView(STLView):

    access = True#'is_admin'

    title = MSG(u'Commande')

    template = '/ui/shop/orders/order_view.xml'

    def get_namespace(self, resource, context, query=None):
        root = context.root
        shop = get_shop(resource)
        # Build namespace
        namespace = {}
        # General informations
        namespace['order_number'] = resource.name
        # Bill
        has_bill = resource.get_resource('bill.pdf', soft=True) is not None
        namespace['has_bill'] = has_bill
        # Order creation date time
        creation_datetime = resource.get_property('creation_datetime')
        namespace['creation_datetime'] = format_datetime(creation_datetime,
                                              context.accept_language)
        # Customer informations
        users = root.get_resource('users')
        customer_id = resource.get_property('customer_id')
        customer = users.get_resource(customer_id)
        gender = customer.get_property('gender')
        namespace['customer'] = {'gender': Civilite.get_value(gender),
                                 'title': customer.get_title(),
                                 'email': customer.get_property('email'),
                                 'href': resource.get_pathto(customer)}
        # Order state
        state = resource.get_state()
        namespace['state'] = {'name': resource.get_statename(),
                              'title': state['title']}
        # Addresses
        addresses = shop.get_resource('addresses').handler
        namespace['delivery_address'] = addresses.get_record_namespace(0)
        namespace['bill_address'] = addresses.get_record_namespace(1)
        # Products
        products = resource.get_resource('products')
        namespace['products'] = products.get_namespace(context)
        # Payments
        payments = shop.get_resource('payments')
        namespace['payments'] = payments.get_payments_items(context, resource.name)
        # Shipping
        shippings = shop.get_resource('shippings')
        namespace['shippings'] = shippings.get_shippings_items(context, resource.name)
        # Prices
        for key in ['shipping_price', 'total_price']:
            namespace[key] = resource.get_property(key)
        return namespace



class Order_PaymentsView(BrowseForm):

    access = 'is_admin'
    title = MSG(u'Order payments')

    table_columns = [
        ('state', u' '),
        ('complete_id', MSG(u'Id')),
        ('ref', MSG(u'Ref')),
        ('payment_name', MSG(u'Payment mode')),
        ('advance_state', MSG(u'State')),
        ('amount', MSG(u'Amount')),
        ]

    def get_items(self, resource, context):
        payments = get_shop(resource).get_resource('payments')
        return payments.get_payments_items(context, resource.name)


    def get_item_value(self, resource, context, item, column):
        return item[column]


    def sort_and_batch(self, resource, context, items):
        # Sort
        sort_by = context.query['sort_by']
        reverse = context.query['reverse']
        if sort_by:
            items.sort(key=itemgetter(sort_by), reverse=reverse)

        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


class Order_ShippingsView(BrowseForm):

    access = 'is_admin'
    title = MSG(u'Order shippings')

    table_columns = [
        ('complete_id', MSG(u'Id')),
        ('ts', MSG(u'Date')),
        ('shipping_mode', MSG(u'Shipping mode')),
        ('state', MSG(u'State')),
        ]

    def get_items(self, resource, context):
        shippings = get_shop(resource).get_resource('shippings')
        return shippings.get_shippings_items(context, resource.name)


    def get_item_value(self, resource, context, item, column):
        return item[column]


    def sort_and_batch(self, resource, context, items):
        # Sort
        sort_by = context.query['sort_by']
        reverse = context.query['reverse']
        if sort_by:
            items.sort(key=itemgetter(sort_by), reverse=reverse)

        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]



class OrdersView(Folder_BrowseContent):

    access = 'is_admin'
    title = MSG(u'Orders')

    # Configuration
    table_actions = []
    search_template = None

    table_columns = [
        ('checkbox', None),
        ('numero', MSG(u'Order id')),
        ('customer', MSG(u'Customer')),
        ('state', MSG(u'State')),
        ('total_price', MSG(u'Total price')),
        ('creation_datetime', MSG(u'Date and Time')),
        ('actions', MSG(u'Actions'))]

    query_schema = merge_dicts(Folder_BrowseContent.query_schema,
                               sort_by=String(),
                               reverse=Boolean(default=True))


    batch_msg1 = MSG(u"There's one order.")
    batch_msg2 = MSG(u"There are {n} orders.")

    actions_html = list(XMLParser("""
        <a href="${order_name}/${action/link}"
            stl:repeat="action actions">
          <img src="${action/img}"/>
        </a>
        """,
        stl_namespaces))

    def get_item_value(self, resource, context, item, column):
        item_brain, item_resource = item
        if column == 'numero':
            return (item_brain.name, item_brain.name)
        elif column == 'customer':
            users = context.root.get_resource('users')
            customer_id = item_resource.get_property('customer_id')
            customer = users.get_resource(customer_id)
            gender = Civilite.get_value(customer.get_property('gender'))
            return '%s %s' % (gender.gettext(), customer.get_title())
        elif column == 'total_price':
            return '%s € ' % item_resource.get_property(column)
        elif column == 'creation_datetime':
            value = item_resource.get_property(column)
            accept = context.accept_language
            return format_datetime(value, accept=accept)
        elif column == 'state':
            state = item_resource.get_state()
            state = '<strong class="wf-order-%s">%s</strong>' % (
                        item_resource.get_statename(),
                        state['title'].gettext())
            return XMLParser(state.encode('utf-8'))
        elif column == 'actions':
            actions = [{'link': ';view', 'img': '/ui/icons/16x16/view.png'},
                       {'link': ';edit', 'img': '/ui/icons/16x16/edit.png'}]
            namespace = {'order_name': item_brain.name,
                         'actions': actions}
            return stl(events=self.actions_html, namespace=namespace)
        return Folder_BrowseContent.get_item_value(self, resource, context,
                                                   item, column)


class MyOrdersView(OrdersView):

    access = 'is_authenticated'
    title = MSG(u'Order history')

    table_columns = [
        ('numero', MSG(u'Order id')),
        ('state', MSG(u'State')),
        ('total_price', MSG(u'Total price')),
        ('creation_datetime', MSG(u'Date and Time'))]


    def get_items(self, resource, context, *args):
        args = PhraseQuery('customer_id', str(context.user.name))
        return Folder_BrowseContent.get_items(self, resource, context, args)
