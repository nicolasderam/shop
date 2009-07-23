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

# Import from itools
from itools.csv import Table as BaseTable
from itools.datatypes import Boolean, Enumerate, String, Decimal
from itools.gettext import MSG
from itools.i18n import format_datetime
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import TextWidget, SelectWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from shop.utils import get_shop, ShopFolder

class PaymentWayBaseTable(BaseTable):

    record_schema = {
        'ref': String(Unique=True, is_indexed=True),
        'user': String,
        'state': Boolean,
        'amount': Decimal}



class PaymentWayTable(Table):

    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        TextWidget('user', title=MSG(u'User id')),
        SelectWidget('state', title=MSG(u'State')),
        TextWidget('amount', title=MSG(u'Amount'))]

    record_order_view = None

    def get_record_namespace(self, context, record):
        get_value = self.handler.get_record_value
        namespace = {'id': record.id,
                     'complete_id': '%s-%s' % (self.parent.name, record.id),
                     'payment_name': self.parent.name}
        # Base namespace
        for key in self.handler.record_schema.keys():
            namespace[key] = get_value(record, key)
        # Amount
        namespace['amount'] = '%s €' % get_value(record, 'amount')
        # User
        users = context.root.get_resource('users')
        user = users.get_resource(get_value(record, 'user') or '0')
        namespace['user_title'] = user.get_title()
        namespace['user_email'] = user.get_property('email')
        # State
        namespace['advance_state'] = None
        # HTML
        if self.record_order_view:
            view = self.record_order_view()
            view.record = record
            namespace['html'] = view.GET(self, context)
        else:
            namespace['html'] = None
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        namespace['ts'] = format_datetime(value,  accept)
        return namespace


class PaymentWay(ShopFolder):

    class_id = 'payment_way'

    payments = GoToSpecificDocument(specific_document='payments',
                                    title=MSG(u'Payments'))

    # Backoffice views
    order_edit_view = None

    @classmethod
    def get_metadata_schema(cls):
        schema = ShopFolder.get_metadata_schema()
        schema['enabled'] = Boolean(default=True)
        schema['logo'] = String
        return schema


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        # Create resource
        kw['title'] = {'en': cls.class_title.gettext()}
        kw['description'] = {'en': cls.class_description.gettext()}
        kw['logo'] = cls.logo
        ShopFolder._make_resource(cls, folder, name, *args, **kw)


    ######################
    # XXX Confirmation
    ######################

    mail_ok = MSG(u"""
    Bonjour, voici les détails de votre paiement sur la boutique XXX.
    Status: Votre paiement a été accepté. \n\n
    ------------------------
    Référence commande: {ref}
    Montant commande: {price} €
    ------------------------
    \n\n
    """)

    mail_erreur = MSG(u"Votre paiement a été refusé\n\n")
    def send_confirmation_mail(self):
        # TODO
        pass


class PaymentWaysEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        context = get_context()
        shop = get_shop(context.resource)
        payments = shop.get_resource('payments')
        for mode in payments.search_resources(cls=PaymentWay):
            options.append({'name': mode.name,
                            'value': mode.get_title(),
                            'enabled': mode.get_property('enabled')})
        return options



register_resource_class(PaymentWay)
