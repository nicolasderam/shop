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

# Import from standard library
from decimal import Decimal as decimal
from os import popen
from re import match, DOTALL
from sys import prefix

# Import from itools
from itools.core import get_abspath
from itools.datatypes import Boolean, Decimal, Integer, Unicode, String
from itools.gettext import MSG
from itools.handlers import ConfigFile
from itools.html import HTMLFile
from itools.uri import get_reference, Path
from itools.web import BaseForm, STLView, FormError

# Import from ikaaro
from ikaaro import messages
from ikaaro.table_views import Table_View
from ikaaro.forms import ImageSelectorWidget
from ikaaro.forms import STLForm, TextWidget, BooleanCheckBox
from ikaaro.resource_views import DBResource_Edit

# Import from shop
from enumerates import PBXState, PayboxCGIErrors
from shop.datatypes import StringFixSize
from shop.shop_utils_views import Shop_Progress


class Paybox_View(Table_View):
    """ View that list history of paybox payments """

    access = 'is_admin'

    search_template = None
    table_actions = []

    def get_table_columns(self, resource, context):
        columns = [
            ('complete_id', MSG(u'Id')),
            ('ts', MSG(u'Date'))]
        # From the schema
        for widget in self.get_widgets(resource, context):
            column = (widget.name, getattr(widget, 'title', widget.name))
            columns.append(column)
        return columns


    def get_items(self, resource, context):
        items = []
        for item in Table_View.get_items(self, resource, context):
            ns = resource.get_record_namespace(context, item)
            items.append(ns)
        return items


    def get_item_value(self, resource, context, item, column):
        return item[column]



class Paybox_Configure(DBResource_Edit):
    """ View that allow to configure paybox :
          - User account
          - ...
    """

    title = MSG(u'Configure Paybox')
    access = 'is_admin'

    schema = {'PBX_SITE': StringFixSize(size=7),
              'PBX_RANG': StringFixSize(size=2),
              'PBX_IDENTIFIANT': String,
              'PBX_DIFF': StringFixSize(size=2),
              'logo': String,
              'enabled': Boolean}

    widgets = [
        BooleanCheckBox('enabled', title=MSG(u'Enabled ?')),
        ImageSelectorWidget('logo',  title=MSG(u'Logo')),
        TextWidget('PBX_SITE', title=MSG(u'Paybox Site')),
        TextWidget('PBX_RANG', title=MSG(u'Paybox Rang')),
        TextWidget('PBX_IDENTIFIANT', title=MSG(u'Paybox Identifiant')),
        TextWidget('PBX_DIFF', title=MSG(u'Diff days (On two digits ex: 04)'),
                   size=2)]

    submit_value = MSG(u'Edit configuration')


    def action(self, resource, context, form):
        for key in self.schema.keys():
            resource.set_property(key, form[key])
        return context.come_back(messages.MSG_CHANGES_SAVED, goto='./')



class Paybox_Pay(STLForm):
    """This view load the paybox cgi. That script redirect on paybox serveur
       to show the payment form.
       It must be call via the method show_payment_form() of payment resource.
    """

    test_configuration = {'PBX_SITE': 1999888,
                          'PBX_RANG': 99,
                          'PBX_IDENTIFIANT': 2}


    def GET(self, resource, context, conf):
        # We get the paybox CGI path on serveur
        cgi_path = Path(prefix).resolve2('bin/paybox.cgi')
        # Get configuration
        configuration_uri = get_abspath('paybox.cfg')
        configuration = ConfigFile(configuration_uri)
        # Configuration
        kw = {}
        kw['PBX_CMD'] = conf['id']
        kw['PBX_TOTAL'] = int(conf['total_price'] * 100)
        # Basic configuration
        for key in configuration.values.keys():
            kw[key] = configuration.get_value(key)
        # PBX Retour uri
        for option in PBXState.get_options():
            key = option['pbx']
            state = option['name']
            base_uri = context.uri.resolve(context.get_link(resource))
            uri = '%s/;end?state=%s' % (base_uri, state)
            kw[key] = '"%s"' % uri
        # Configuration
        for key in ['PBX_SITE', 'PBX_IDENTIFIANT',
                    'PBX_RANG', 'PBX_DIFF', 'PBX_AUTOSEULE']:
            kw[key] = resource.get_property(key)
        # XXX Euro par défaut
        kw['PBX_DEVISE'] = '978'
        # PBX_PORTEUR
        kw['PBX_PORTEUR'] = conf['email']
        # En mode test:
        payments = resource.parent
        if payments.is_in_test_mode():
            kw.update(self.test_configuration)
        # Attributes
        attributes = ['%s=%s' % (x[0], x[1]) for x in kw.items()]
        # Build cmd
        cmd = '%s %s' % (cgi_path, ' '.join(attributes))
        # Call the CGI
        file = popen(cmd)
        # Check if all is ok
        result = file.read()
        html = match ('.*?<HEAD>(.*?)</HTML>', result, DOTALL)
        if html is None:
            raise ValueError, u"Error, payment module can't be load"
        # We return the payment widget
        html = html.group(1)
        return HTMLFile(string=html).events




class Paybox_ConfirmPayment(BaseForm):
    """The paybox server send a POST request to say if the payment was done
    """
    access = True

    authorized_ip = ['195.101.99.76', '194.2.122.158']

    schema = {'ref': String,
              'transaction': Unicode,
              'autorisation': Unicode,
              'amount': Decimal,
              'status': String}

    # XXX Why that ?
    def POST(self, resource, context):
        # (1) Find out which button has been pressed, if more than one
        self._get_action(resource, context)

        # (2) Automatically validate and get the form input (from the schema).
        try:
            form = self._get_form(resource, context)
        except FormError, error:
            context.form_error = error
            return self.on_form_error(resource, context)
        return self.action(resource, context, form)


    def action(self, resource, context, form):
        # Ensure that remote ip address belongs to Paybox
        # return get_abspath('paybox.cfg')

        remote_ip = context.request.get_remote_ip()
        if remote_ip not in self.authorized_ip:
            msg = 'IP %s invalide (Ref commande = %s)'
            raise ValueError, msg % (remote_ip, form['ref'])
        # Get form values
        amount = form['amount'] / decimal('100')
        # TODO Check signature
        # Add a line into payments history
        kw = {'success': bool(form['autorisation']),
              'devise': resource.get_property('devise')}
        for key in ['ref', 'transaction', 'autorisation', 'status']:
            kw[key] = form[key]
        kw['amount'] = amount
        payment_record = resource.handler.add_record(kw)
        # Maybe we have to do a specific traitement ?
        self.do_treatment(resource, context, payment_record)
        # Send an email of confirmation
        self.send_mail_confirmation(context, payment_record)
        # Return a blank page to payment
        response = context.response
        response.set_header('Content-Type', 'text/plain')
        # Confirm_payment
        if bool(form['autorisation']):
            resource.set_payment_as_ok(context, form['ref'])



class Paybox_End(STLView):
    """The customer is redirect on this page after payment"""

    access = "is_authenticated"

    query_schema = {'state': Integer,
                    'ref': String,
                    'NUMERR': String}

    template = '/ui/shop/payments/paybox/paybox_end.xml'

    def get_namespace(self, resource, context):
        erreur = context.query['NUMERR']
        if erreur:
            # Send mail
            root = context.root
            server = context.server
            from_addr = server.smtp_from
            subject = u'Paybox problem'
            body = 'Paybox error: %s' % PayboxCGIErrors.get_value(erreur)
            root.send_email(from_addr, subject, from_addr, body)
        state = PBXState.get_value(context.query['state']).gettext()
        ns = {
          'progress': Shop_Progress(index=6).GET(resource, context),
          'state': state,
          'ref': context.query['ref']}
        return ns
