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

# Import from itools
from itools.datatypes import Boolean
from itools.gettext import MSG

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.registry import register_resource_class

# Import from payments
from payments_views import Payments_View, Payments_Configure
from payments_views import Payments_History_View
from paybox import Paybox
from check import CheckPayment

# Import from shop
from payment_way import PaymentWay
from shop.utils import get_shop


class Payments(Folder):
    """
    This table contains the history of attempted or successful payments.
    They can be done by several ways (Paybox, paypal ...)
    """

    class_id = 'payments'
    class_title = MSG(u'Payment Module')

    # Views
    class_views = ['view', 'history', 'configure']

    # XXX We have to secure
    # Fixed handlers
    __fixed_handlers__ = []


    # List of views
    view = Payments_View()
    history = Payments_History_View()
    configure = Payments_Configure()


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        Folder._make_resource(cls, folder, name, *args, **kw)
        # Add paybox Payment way
        Paybox._make_resource(Paybox, folder, '%s/paybox' % name)
        # Add check Payment way
        CheckPayment._make_resource(CheckPayment, folder, '%s/check' % name)


    @classmethod
    def get_metadata_schema(cls):
        schema = Folder.get_metadata_schema()
        schema['enabled'] = Boolean
        return schema


    def get_payments_records(self, ref=None):
        records = []
        for payment_way in self.search_resources(cls=PaymentWay):
            payments = payment_way.get_resource('payments')
            if ref is None:
                payments_records = (payment_way, payments.handler.get_records())
            else:
                payments_records = (payment_way, payments.handler.search(ref=ref))
            records.append(payments_records)
        return records


    def get_payments_namespace(self, context, ref=None):
        payments = []
        for payment_way, records in self.get_payments_records(ref):
            table = payment_way.get_resource('payments')
            # XXX sylvain
            #img = context.get_link(payment_way.get_property('logo'))
            img = None
            for record in records:
                ns = table.get_record_namespace(context, record)
                ns['title'] = payment_way.get_title()
                ns['img']= img
                payments.append(ns)
        return payments


    ######################
    # Public API
    ######################

    def is_in_test_mode(self):
        return not self.get_property('enabled')


    def show_payment_form(self, context, payment):
        """
           payment must be a dictionnary with order's identifiant
           and order price.
           For example:
           payment = {'id': 'A250',
                      'total_price': 250,
                      'email': 'toto@example.fr',
                      'mode': 'paybox'}
        """
        # We check that payment dictionnary is correctly fill.
        for key in ['id', 'total_price', 'email', 'mode']:
            if key not in payment:
                raise ValueError, u'Invalid order'
        # We check mode is valid and active
        payment_module = self.get_resource(payment['mode'])
        # Check if enabled
        if not payment_module.get_property('enabled'):
            raise ValueError, u'Invalid payment mode'
        # All is ok: We show the payment form
        return payment_module._show_payment_form(context, payment)


register_resource_class(Payments)
