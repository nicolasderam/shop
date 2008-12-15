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
import decimal
import os
import re

# Import from itools
from itools.handlers import ConfigFile
from itools.datatypes import Decimal, Email, URI, Unicode, String, Boolean
from itools.gettext import MSG
from itools.web import BaseForm, INFO, ERROR
from itools.i18n import format_datetime
from itools.html import HTMLFile

# Import from ikaaro
from ikaaro.table_views import Table_View
from ikaaro.forms import STLForm, BooleanCheckBox, SelectWidget, TextWidget
from ikaaro.resource_views import DBResource_Edit


# Import from package
from enumerates import Devises, ModeAutorisation, PayboxAccount, PayboxStatus


class Paybox_View(Table_View):

    access = 'is_admin'

    def get_table_columns(self, resource, context):
        columns = [
            ('checkbox', None),
            ('id', MSG(u'id')),
            ('ts', MSG(u'Date'))]
        # From the schema
        for widget in self.get_widgets(resource, context):
            column = (widget.name, getattr(widget, 'title', widget.name))
            columns.append(column)
        return columns


    def get_item_value(self, resource, context, item, column):
        handler = resource.handler
        value = Table_View.get_item_value(self, resource, context, item, column)
        if column=='ts':
            accept = context.accept_language
            value = handler.get_record_value(item, column)
            return format_datetime(value,  accept)
        elif column=='amount':
            devise = handler.get_record_value(item, 'devise')
            symbol = Devises.get_value(devise, 'symbol')
            return '%s %s' % (value, symbol)
        return value



class Paybox_Configure(DBResource_Edit):

    title = MSG(u'Configure Paybox payment')
    access = 'is_admin'

    schema = {
              #'account': PayboxAccount,
              'PBX_cgi_path': URI,
              'PBX_SITE': String,
              'PBX_RANG': String,
              'PBX_IDENTIFIANT': String,
              #'PBX_AUTOSEULE': ModeAutorisation,
              'PBX_EFFECTUE': URI,
              'PBX_REFUSE': URI,
              'PBX_ERREUR': URI,
              'PBX_ANNULE': URI,
              'PBX_DIFF': String,
              'devise': Devises}
              #'is_open': Boolean

    widgets = [
        TextWidget('PBX_cgi_path', title=MSG(u'CGI Path')),
        TextWidget('PBX_SITE', title=MSG(u'Paybox Site')),
        TextWidget('PBX_RANG', title=MSG(u'Paybox Rang')),
        TextWidget('PBX_IDENTIFIANT', title=MSG(u'Paybox Identifiant')),
        TextWidget('PBX_DIFF',
                   title=MSG(u'Nombre de jour de différé (sur deux chiffres ex: 04)'),
                   size=2),
        TextWidget('PBX_EFFECTUE', title=MSG(u'PBX_EFFECTUE')),
        TextWidget('PBX_REFUSE', title=MSG(u'PBX_REFUSE')),
        TextWidget('PBX_ERREUR', title=MSG(u'PBX_ERREUR')),
        TextWidget('PBX_ANNULE', title=MSG(u'PBX_ANNULE')),
        SelectWidget('devise', title=MSG(u'Devise'))]
        # XXX Futur ?
        #SelectWidget('PBX_AUTOSEULE', title=MSG(u"Autorisation Mode")),
        #SelectWidget('account', title=MSG(u'Paybox account')),
        #BooleanCheckBox('is_open', title=MSG(u'Paybox is open'))]

    submit_value = MSG(u'Edit configuration')


    def action(self, resource, context, form):
        for key in self.schema.keys():
            resource.set_property(key, form[key])
        context.message = MSG(u'Modification ok')
        return



class Paybox_Pay(STLForm):


    def GET(self, resource, context, conf):
        # We get the paybox CGI path on serveur
        cgi_path = resource.get_property('PBX_cgi_path')
        # Get configuration
        configuration_uri = resource.get_configuration_uri()
        configuration = ConfigFile(configuration_uri)
        # Configuration
        kw = {}
        kw['PBX_CMD'] = conf['cmd']
        kw['PBX_TOTAL'] = int(conf['price'] * 100)
        #kw.update(form)
        for key in configuration.values.keys():
            kw[key] = configuration.get_value(key)
        for key in ['PBX_EFFECTUE', 'PBX_ERREUR',
                    'PBX_REFUSE', 'PBX_ANNULE']:
            kw[key] = '"%s"' % resource.get_property(key)
        for key in ['PBX_SITE', 'PBX_IDENTIFIANT',
                    'PBX_RANG', 'PBX_DIFF', 'PBX_AUTOSEULE']:
            kw[key] = resource.get_property(key)
        kw['PBX_DEVISE'] = resource.get_property('devise')
        # PBX_PORTEUR
        user = context.user
        kw['PBX_PORTEUR'] = user.get_property('email')
        # Attributes
        attributes = ['%s=%s' % (x[0], x[1]) for x in kw.items()]
        # Build cmd
        cmd = '%s %s' % (cgi_path, ' '.join(attributes))
        # Call the CGI
        file = os.popen(cmd)
        # Check if all is ok
        result = file.read()
        html = re.match ('.*?<HEAD>(.*?)</HTML>', result, re.DOTALL)
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
        remote_ip = context.request.get_remote_ip()
        if remote_ip not in self.authorized_ip:
            msg = 'IP %s invalide (Ref commande = %s)'
            raise ValueError, msg % (remote_ip, form['ref'])
        # Get form values
        amount = form['amount'] / decimal.Decimal('100')
        # Check signature XXX todo
        # Create a new command
        kw = {'payment_ok': bool(form['autorisation']),
              'devise': resource.get_property('devise')}
        for key in ['ref', 'transaction', 'autorisation', 'status']:
            kw[key] = form[key]
        kw['amount'] = amount
        record = resource.handler.add_record(kw)
        # Do traitement
        self.do_treatment(resource, context, record)
        # Return a blank page
        response = context.response
        response.set_header('Content-Type', 'text/plain')
        return


    def do_treatment(self, resource, context, record):
        pass
