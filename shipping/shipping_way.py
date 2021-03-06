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
from copy import deepcopy
from decimal import Decimal as decimal

# Import from itools
from itools.fs import lfs
from itools.core import get_abspath, merge_dicts
from itools.csv import Table as BaseTable, CSVFile
from itools.datatypes import Decimal, Enumerate, String, Unicode, Integer
from itools.gettext import MSG
from itools.handlers import ro_database
from itools.i18n import format_datetime
from itools.web import get_context
from itools.xapian import PhraseQuery

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder_views import GoToSpecificDocument
from ikaaro.forms import SelectWidget, TextWidget
from ikaaro.registry import register_resource_class
from ikaaro.table import Table

# Import from shop
from shop.cart import ProductCart
from shop.enumerates import CountriesZonesEnumerate
from shop.folder import ShopFolder
from shop.utils import format_price, get_shop
from shop.utils_views import SearchTable_View

# Import from shipping
from enumerates import ShippingStates
from schema import delivery_schema
from shipping_way_views import ShippingWay_Configure, ShippingWay_RecordAdd
from shipping_way_views import ShippingWay_RecordEdit, ShippingWay_RecordView


class ShippingWayBaseTable(BaseTable):

    record_properties = {
        'ref': String(unique=True, is_indexed=True),
        'state': ShippingStates,
        'price': Decimal,
        'weight': Decimal,
        'number': String,
        'description': Unicode}



class ShippingWayTable(Table):

    class_id = 'shipping-way-table'
    class_handler = ShippingWayBaseTable

    form = [
        TextWidget('ref', title=MSG(u'Facture number')),
        SelectWidget('state', title=MSG(u'State')),
        TextWidget('price', title=MSG(u'Price')),
        TextWidget('weight', title=MSG(u'Weight')),
        TextWidget('number', title=MSG(u'Numéro')),
        TextWidget('description', title=MSG(u'Description')),
        ]

    def get_record_namespace(self, context, record):
        namespace = {}
        # Id
        namespace['id'] = record.id
        namespace['shipping_mode'] = self.parent.get_title()
        # Complete id
        namespace['complete_id'] = '%s-%s' % (self.parent.name, record.id)
        # Base namespace
        for key in self.handler.record_properties.keys():
            namespace[key] = self.handler.get_record_value(record, key)
        # State
        namespace['state'] = ShippingStates.get_value(namespace['state'])
        # Timestamp
        accept = context.accept_language
        value = self.handler.get_record_value(record, 'ts')
        namespace['ts'] = format_datetime(value,  accept)
        return namespace


class ShippingPricesCSV(CSVFile):

    columns = ['zone', 'max-weight', 'price']

    schema = {'zone': Unicode,
              'max-weight': Decimal,
              'price': Decimal}


class ShippingPricesTable(BaseTable):

    record_properties = {
      'zone': CountriesZonesEnumerate(mandatory=True, is_indexed=True),
      'max-weight': Decimal(is_indexed=True),
      'max-quantity': Integer(is_indexed=True),
      'price': Decimal(mandatory=True)}



class ShippingPrices(Table):

    class_id = 'shipping-prices'
    class_title = MSG(u'Shipping Prices')
    class_handler = ShippingPricesTable

    class_views = ['view', 'add_record']

    form = [
        SelectWidget('zone', title=MSG(u'Zone')),
        TextWidget('price', title=MSG(u'Price'))]

    quantity_widget = TextWidget('max-quantity', title=MSG(u'Max quantity'))
    weight_widget = TextWidget('max-weight', title=MSG(u'Max Weight (Kg)'))

    def get_form(self):
        if self.parent.get_property('mode') == 'quantity':
            return self.form + [self.quantity_widget]
        return self.form + [self.weight_widget]

    view = SearchTable_View(search_widgets=[SelectWidget('zone', title=MSG(u'Zone'))],
                            search_schema={'zone': CountriesZonesEnumerate})



class ShippingWay(ShopFolder):

    class_id = 'shipping'
    class_title = MSG(u'Shipping')
    class_description = MSG(u'Allow to define your own shipping way')
    class_views = ['view', 'configure', 'history', 'prices']
    class_version = '20090918'

    img = '../ui/shop/images/shipping.png'

    shipping_history_cls = ShippingWayTable

    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        ShopFolder._make_resource(cls, folder, name, *args, **kw)
        # Image
        body = lfs.open(get_abspath(cls.img)).read()
        img = Image._make_resource(Image, folder,
                                   '%s/logo.png' % name, body=body,
                                   **{'state': 'public'})
        # Load zones
        shop = get_context().resource.parent
        zones = []
        handler = shop.get_resource('countries-zones').handler
        for record in handler.get_records():
            zones.append(handler.get_record_value(record, 'title'))
        # Create history
        cls.shipping_history_cls._make_resource(cls.shipping_history_cls,
                              folder, '%s/history' % name)
        # Import CSV with prices
        ShippingPrices._make_resource(ShippingPrices, folder,
                                      '%s/prices' % name)
        if getattr(cls, 'csv', None):
            table = ShippingPricesTable()
            csv = ro_database.get_handler(get_abspath(cls.csv), ShippingPricesCSV)
            for row in csv.get_rows():
                table.add_record(
                  {'zone': str(zones.index(row.get_value('zone'))),
                   'max-weight': row.get_value('max-weight'),
                   'price': row.get_value('price')})
            folder.set_handler('%s/prices' % name, table)


    @classmethod
    def get_metadata_schema(cls):
        return merge_dicts(ShopFolder.get_metadata_schema(), delivery_schema)


    def get_price(self, country, list_weight):
        list_weight = deepcopy(list_weight)
        shop = get_shop(self)
        # Is Free ?
        if self.get_property('is_free'):
            return decimal(0)
        # Transform country to zone
        countries = shop.get_resource('countries').handler
        country_record = countries.get_record(int(country))
        if countries.get_record_value(country_record, 'enabled') is False:
            return None
        zone = countries.get_record_value(country_record, 'zone')
        # XXX to refactor
        # Max value
        mode = self.get_property('mode')
        if mode == 'weight':
            list_weight.sort(reverse=True)
            list_values = list_weight
        elif mode == 'quantity':
            list_values = [1] * len(list_weight)
        # XXX limit by models
        only_this_models = self.get_property('only_this_models')
        if only_this_models:
            cart = ProductCart(get_context())
            for product_cart in cart.products:
                product = shop.get_resource(product_cart['name'], soft=True)
                if product.get_property('product_model') not in only_this_models:
                    return None

        # Get corresponding weight/quantity in table of price
        list_price_ok = {}
        prices = self.get_resource('prices').handler
        min_value = 0
        for record in prices.search(PhraseQuery('zone', zone),
                                    sort_by='max-%s' % mode):
            max_value = prices.get_record_value(record, 'max-%s' % mode)
            price = prices.get_record_value(record, 'price')
            list_price_ok[max_value] = {'min': min_value,
                                        'max': max_value,
                                        'price': price}
            min_value = max_value
        # No price ?
        if len(list_price_ok.keys()) == 0:
            return None
        # Check all weigh if < max_weight
        if mode == 'weight':
            max_value = max(list_price_ok.keys())
            for key in list_weight:
                if key > max_value:
                    return None
        # On crée une partition de poids
        current_value = decimal(0)
        partition = []
        list_values.sort(reverse=True)
        while list_values:
            if current_value + list_values[-1] <= max_value:
                current_value += list_values.pop()
            else:
                partition.append(current_value)
                current_value = decimal(0)
            if len(list_values) == 0:
                partition.append(current_value)
        # Calcul total price
        total_price = decimal(0)
        for p in partition:
            for value in list_price_ok.values():
                if p >= value['min'] and p <= value['max']:
                    total_price += value['price']
                    break
        # Add insurance
        if self.get_property('insurance') > decimal(0):
            context = get_context()
            cart = ProductCart(context)
            products_price = cart.get_total_price(shop,
                                with_delivery=False, pretty=False)
            percent = self.get_property('insurance') / 100
            total_price += products_price['with_tax'] * percent
        return total_price



    def get_logo(self, context):
        logo = self.get_property('logo')
        resource = self.get_resource(logo, soft=True)
        if resource is None or logo == '.':
            return
        return context.get_link(resource)


    def get_shipping_option(self, context):
        return None


    def get_namespace(self, context):
        language = self.get_content_language(context)
        return  {'name': self.name,
                 'description': self.get_property('description', language),
                 'logo': self.get_logo(context),
                 'title': self.get_title(language)}



    def get_widget_namespace(self, context, country, list_weight):
        # Is enabled ?
        if not self.get_property('enabled'):
            return None
        # For good group ?
        shipping_groups = self.get_property('only_this_groups')
        if (shipping_groups and
           context.user.get_property('user_group') not in shipping_groups):
            return None
        # Get price of shipping
        price = self.get_price(country, list_weight)
        if price is None:
            return None
        language = self.get_content_language(context)
        ns = {'name': self.name,
              'img': self.get_logo(context),
              'title': self.get_title(language),
              'pretty_price': format_price(price),
              'price': price}
        for key in ['description', 'enabled']:
            ns[key] = self.get_property(key, language)
        return ns



    # Views
    configure = ShippingWay_Configure()
    history = GoToSpecificDocument(specific_document='history',
                                  title=MSG(u'History'))
    prices = GoToSpecificDocument(specific_document='prices',
                                  title=MSG(u'Prices'))

    # Backoffice order views
    order_view = ShippingWay_RecordView()
    order_add_view = ShippingWay_RecordAdd()
    order_edit_view = ShippingWay_RecordEdit()




class ShippingWaysEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        options = []
        context = get_context()
        shop = get_shop(context.resource)
        shippings = shop.get_resource('shippings')
        for way in shippings.search_resources(cls=ShippingWay):
            shipping_groups = way.get_property('only_this_groups')
            if context.user.get_property('user_group') not in shipping_groups:
                continue
            options.append({'name': way.name,
                            'value': way.get_title(),
                            'enabled': way.get_property('enabled')})
        return options


register_resource_class(ShippingWay)
register_resource_class(ShippingWayTable)
register_resource_class(ShippingPrices)
