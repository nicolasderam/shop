# -*- coding: UTF-8 -*-
# Copyright (C) 2008 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Integer
from itools.gettext import MSG
from itools.xml import XMLParser
from itools.web import BaseView, BaseForm, ERROR, FormError
from itools.web.views import process_form

# Import from ikaaro
from ikaaro.views import BrowseForm

# Import from shop
from shop.utils import get_shop
from enumerates import PaymentWaysEnumerate
from payment_way import PaymentWay


class Payments_ViewPayment(BaseView):

    access = 'is_admin'

    query_schema = {'payment_way': PaymentWaysEnumerate,
                    'id_payment': Integer}

    def GET(self, resource, context):
        query = context.query
        payment_way = resource.get_resource(query['payment_way'])
        payment_way_table = payment_way.get_resource('payments')
        view = payment_way.order_view
        if view is None:
            return context.come_back(ERROR(u'Unavailable view'))
        payment_table = payment_way.get_resource('payments').handler
        record = payment_table.get_record(query['id_payment'])
        return view(payment_way=payment_way,
                    payment_table=payment_table,
                    record=record,
                    id_payment=query['id_payment']).GET(resource, context)



class Payments_EditPayment(BaseForm):

    access = 'is_admin'

    query_schema = {'payment_way': PaymentWaysEnumerate,
                    'id_payment': Integer}

    def GET(self, resource, context):
        query = context.query
        payment_way = resource.get_resource(query['payment_way'])
        payment_way_table = payment_way.get_resource('payments')
        view = payment_way.order_edit_view
        if view is None:
            return context.come_back(ERROR(u'Unavailable view'))
        payment_table = payment_way.get_resource('payments').handler
        record = payment_table.get_record(query['id_payment'])
        return view(payment_way=payment_way,
                    payment_table=payment_table,
                    record=record,
                    id_payment=query['id_payment']).GET(resource, context)


    action_edit_payment_schema = {'payment_way': PaymentWaysEnumerate(mandatory=True),
                                  'id_payment': Integer(mandatory=True)}
    def action_edit_payment(self, resource, context, form):
        shop = get_shop(resource)
        # We get shipping way
        payment_way = shop.get_resource('payments/%s/' % form['payment_way'])
        # We get order_edit_view
        view = payment_way.order_edit_view
        # We get schema
        schema = view.schema
        # We get form
        try:
            form = process_form(context.get_form_value, schema)
        except FormError, error:
            context.form_error = error
            return self.on_form_error(resource, context)
        # Instanciate view
        payment_table = payment_way.get_resource('payments').handler
        record = payment_table.get_record(form['id_payment'])
        view = view(payment_way=payment_way,
                    payment_table=payment_table,
                    record=record,
                    id_payment=form['id_payment'])
        # Do actions
        return view.action_edit_payment(resource, context, form)



class Payments_History_View(BrowseForm):
    """
    View that list history payments.
    """

    title = MSG(u'Payments history')
    access = 'is_admin'

    batch_msg1 = MSG(u"There is 1 payment.")
    batch_msg2 = MSG(u"There are {n} payments.")


    table_columns = [
        ('state', u' '),
        ('complete_id', MSG(u'Id')),
        ('ts', MSG(u'Date')),
        ('ref', MSG(u'Ref')),
        ('user_title', MSG(u'Customer')),
        ('user_email', MSG(u'Customer email')),
        ('payment_name', MSG(u'Payment mode')),
        ('advance_state', MSG(u'State')),
        ('amount', MSG(u'Amount')),
        ('buttons', None),
        ]

    def get_items(self, resource, context):
        return resource.get_payments_items(context)


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



    buttons_template = """
              <a href=";view_payment?payment_way={way}&amp;id_payment={id}">
                <img src="/ui/icons/16x16/view.png"/>
              </a>
              <a href=";edit_payment?payment_way={way}&amp;id_payment={id}">
                <img src="/ui/icons/16x16/edit.png"/>
              </a>
                       """

    def get_item_value(self, resource, context, item, column):
        if column == 'buttons':
            kw = {'id': item['id'],
                  'way': item['payment_name']}
            return XMLParser(self.buttons_template.format(**kw))
        return item[column]


class Payments_View(BrowseForm):

    title = MSG(u'View')
    access = 'is_admin'

    batch_msg1 = MSG(u"There is 1 payment mode.")
    batch_msg2 = MSG(u"There are {n} payments mode.")


    table_columns = [
        ('logo', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('description', MSG(u'Description')),
        ('enabled', MSG(u'Enabled ?')),
        ]

    def get_items(self, resource, context):
        """ Here we concatanate payments off all payment's mode """
        items = []
        for payment_way in resource.search_resources(cls=PaymentWay):
            name = payment_way.name
            logo = payment_way.get_property('logo')
            kw = {'name': (name, name),
                  'title': (payment_way.get_title(), name),
                  'description': payment_way.get_property('description'),
                  'logo': XMLParser('<img src="%s"/>' % logo),
                  'enabled': payment_way.get_property('enabled')}
            items.append(kw)
        return items


    def sort_and_batch(self, resource, context, items):
        # Batch
        start = context.query['batch_start']
        size = context.query['batch_size']
        return items[start:start+size]


    def get_item_value(self, resource, context, item, column):
        return item[column]
