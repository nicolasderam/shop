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

# Import from standard library
from datetime import datetime
from decimal import Decimal as decimal

# Import from itools
from itools.csv import Table as BaseTable
from itools.datatypes import Boolean, DateTime
from itools.datatypes import ISODateTime, Decimal, Integer, String, Unicode
from itools.gettext import MSG
from itools.i18n import format_date
from itools.pdf import stl_pmltopdf
from itools.uri import get_reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import PDF, Image
from ikaaro.forms import TextWidget
from ikaaro.registry import register_resource_class, register_field
from ikaaro.table import Table
from ikaaro.workflow import WorkflowAware, WorkflowError

# Import from shop
from shop.addresses import Addresses, BaseAddresses
from shop.payments.enumerates import PaymentWaysEnumerate
from shop.shipping.shipping_way import ShippingWaysEnumerate
from shop.utils import get_shop

# Import from shop.orders
from messages import Messages_TableResource
from orders_views import Order_Manage, OrdersView
from orders_views import ShopPayments_EndViewTop
from workflow import order_workflow
from shop.csv_views import Export
from shop.datatypes import Users_Enumerate
from shop.products.taxes import TaxesEnumerate
from shop.folder import ShopFolder
from shop.utils import format_price, format_for_pdf


#############################################
# Email de confirmation de commande client  #
#############################################
mail_confirmation_title = MSG(u'Order confirmation')

mail_confirmation_body = MSG(u"""Hi,
Your order number {order_name} in our shop has been recorded.
You can found details on our website:\n
  {order_uri}\n
""")

#############################################
# Email de confirmation de commande client  #
#############################################

mail_notification_title = MSG(u'New order in your shop')

mail_notification_body = MSG(u"""
Hi,
A new order has been done in your shop.
You can found details here:\n
  {order_uri}\n
""")

#############################################
# Message notification
#############################################

new_message_subject = MSG(u'New message concerning order number {n}')
new_message_footer = MSG(u'\n\nSee details here : \n\n {uri}')


#############################################
# Message notification shipped
#############################################

order_shipped_subject = MSG(u'Your order has been shipped.')
order_shipped_text = MSG(u"""
Hi {firstname} {lastname},
Your order number {order_reference} has been shipped.
You can found details here:\n
  {order_uri}\n
""")

###################################################################
###################################################################



class BaseOrdersProducts(BaseTable):

    record_properties = {
      'name': String(mandatory=True),
      'reference': String,
      'title': Unicode,
      'declination': String,
      'quantity': Integer,
      'weight': Decimal,
      'pre-tax-price': Decimal(mandatory=True),
      'tax': Decimal(mandatory=True),
      }



class OrdersProducts(Table):

    class_id = 'orders-products'
    class_title = MSG(u'Products')
    class_handler = BaseOrdersProducts

    class_views = ['view']

    form = [
        TextWidget('name', title=MSG(u'Product name')),
        TextWidget('reference', title=MSG(u'Reference')),
        TextWidget('title', title=MSG(u'Title')),
        TextWidget('weight', title=MSG(u'Weight')),
        TextWidget('declination', title=MSG(u'Declination')),
        TextWidget('pre-tax-price', title=MSG(u'Unit price (pre-tax)')),
        TextWidget('tax', title=MSG(u'Tax')),
        TextWidget('quantity', title=MSG(u'Quantity'))]



class Order(WorkflowAware, ShopFolder):

    class_id = 'order'
    class_title = MSG(u'Order')
    class_views = ['view', 'manage']
    class_version = '20091123'

    __fixed_handlers__ = ShopFolder.__fixed_handlers__ + ['addresses',
                          'messages', 'products']

    workflow = order_workflow

    # Views
    manage = Order_Manage()
    end_view_top = ShopPayments_EndViewTop()


    @classmethod
    def get_metadata_schema(cls):
        schema = ShopFolder.get_metadata_schema()
        schema.update(WorkflowAware.get_metadata_schema())
        schema['total_price'] = Decimal(title=MSG(u'Total price'))
        schema['shipping_price'] = Decimal
        schema['total_weight'] = Decimal
        schema['creation_datetime'] = ISODateTime(title=MSG(u'Creation date'))
        schema['customer_id'] = Users_Enumerate
        schema['payment_mode'] = PaymentWaysEnumerate
        schema['shipping'] = ShippingWaysEnumerate
        schema['delivery_address'] = Integer
        schema['bill_address'] = Integer
        # States
        schema['is_payed'] = Boolean(default=False)
        schema['is_sent'] = Boolean(default=False)
        return schema


    @staticmethod
    def make_resource(cls, container, name, *args, **kw):
        order = ShopFolder.make_resource(cls, container, name, *args, **kw)
        # XXX Workflow (Should be done in ikaaro)
        order.onenter_open()
        return order


    @staticmethod
    def _make_resource(cls, folder, name, *args, **kw):
        context = get_context()
        shop = kw['shop']
        user = kw['user']
        shop_uri = kw['shop_uri']
        cart = kw['cart']
        # Email
        user_email = user.get_property('email')
        # Build metadata/order
        metadata = {}
        for key in ['payment_mode', 'shipping_price', 'total_price', 'total_weight']:
            metadata[key] = kw[key]
        # Has tax ?
        id_zone = cart.id_zone
        zones = shop.get_resource('countries-zones').handler
        zone_record = zones.get_record(int(id_zone))
        has_tax = zones.get_record_value(zone_record, 'has_tax')
        # Addresses
        metadata['delivery_address'] = cart.addresses['delivery_address']
        metadata['bill_address'] = cart.addresses['bill_address'] or \
            cart.addresses['delivery_address']
        metadata['customer_id'] = user.name
        metadata['creation_datetime'] = datetime.now()
        metadata['shipping'] = cart.shipping
        ShopFolder._make_resource(cls, folder, name, *args, **metadata)
        # Save products
        handler = BaseOrdersProducts()
        for product_cart in cart.products:
            product = context.root.get_resource(product_cart['name'])
            declination = product_cart['declination']
            if has_tax:
                tax = TaxesEnumerate.get_value(product.get_property('tax'))
            else:
                tax = decimal(0)
            handler.add_record(
              {'name': str(product.get_abspath()),
               'reference': product.get_reference(declination),
               'title': product.get_title(),
               'declination': declination,
               'pre-tax-price': product.get_price_without_tax(declination),
               'tax': tax,
               'weight': product.get_weight(declination),
               'quantity': product_cart['quantity']})
        metadata = OrdersProducts.build_metadata(title={'en': u'Products'})
        folder.set_handler('%s/products.metadata' % name, metadata)
        folder.set_handler('%s/products' % name, handler)
        # Get bill and delivery addresses
        addresses = shop.get_resource('addresses').handler
        delivery_record = addresses.get_record_kw(cart.addresses['delivery_address'])
        bill_record = addresses.get_record_kw(cart.addresses['bill_address'] or 0)
        # Save addresses
        handler = BaseAddresses()
        handler.add_record(delivery_record)
        handler.add_record(bill_record)
        metadata = Addresses.build_metadata(title={'en': u'Addresses'})
        folder.set_handler('%s/addresses.metadata' % name, metadata)
        folder.set_handler('%s/addresses' % name, handler)
        # Add messages resource
        Messages_TableResource._make_resource(Messages_TableResource, folder,
                                '%s/messages' % name,
                                **{'title': {'en': u'Messages'}})
        # Generate barcode
        from shop.utils import generate_barcode
        order = shop.get_resource('orders/%s' % name)
        barcode = generate_barcode(shop.get_property('barcode_format'), name)
        metadata =  {'title': {'en': u'Barcode'},
                     'filename': 'barcode.png',
                     'format': 'image/png'}
        Image.make_resource(Image, order, 'barcode', body=barcode, **metadata)


    def _get_catalog_values(self):
        values = ShopFolder._get_catalog_values(self)
        for key in ['customer_id', 'creation_datetime', 'is_payed']:
            values[key] = self.get_property(key)
        return values



    ##################################################
    # Get namespace
    ##################################################
    def get_namespace(self, context):
        # Get some resources
        shop = get_shop(self)
        order_products = self.get_resource('products')
        # Get creation date
        accept = context.accept_language
        creation_date = self.get_property('creation_datetime')
        creation_date = format_date(creation_date, accept=accept)
        # Build namespace
        namespace = {'products': [],
                     'reference': self.get_reference(),
                     'creation_date': creation_date,
                     'price': {'shippings': {'with_tax': decimal(0),
                                             'without_tax': decimal(0)},
                               'products': {'with_tax': decimal(0),
                                            'without_tax': decimal(0)},
                               'total': {'with_tax': decimal(0),
                                         'without_tax': decimal(0)}}}
        # Build order products namespace
        get_value = order_products.handler.get_record_value
        for record in order_products.handler.get_records():
            kw = {'id': record.id,
                  'href': None,
                  'category': None}
            for key in BaseOrdersProducts.record_properties.keys():
                kw[key] = get_value(record, key)
            name = get_value(record, 'name')
            product_resource = context.root.get_resource(name, soft=True)
            if product_resource:
                kw['href'] = context.get_link(product_resource)
                kw['key'] = product_resource.handler.key
                kw['cover'] = product_resource.get_cover_namespace(context)
                kw['category'] = product_resource.parent.get_title()
                # Declination
                if kw['declination']:
                    declination = product_resource.get_resource(
                                    str(kw['declination']), soft=True)
                    if declination:
                        kw['declination'] = declination.get_declination_title()
            else:
                kw['cover'] = None

            # Get product prices
            unit_price_with_tax = kw['pre-tax-price'] * ((kw['tax']/100)+1)
            unit_price_without_tax = kw['pre-tax-price']
            total_price_with_tax = unit_price_with_tax * kw['quantity']
            total_price_without_tax = unit_price_without_tax * kw['quantity']
            kw['price'] = {
              'unit': {'with_tax': format_price(unit_price_with_tax),
                       'without_tax': format_price(unit_price_without_tax)},
              'total': {'with_tax': format_price(total_price_with_tax),
                        'without_tax': format_price(total_price_without_tax)}}
            namespace['products'].append(kw)
            # Calcul order price
            namespace['price']['products']['with_tax'] += total_price_with_tax
            namespace['price']['products']['without_tax'] += total_price_without_tax
        # Format price
        shipping_price = self.get_property('shipping_price')
        namespace['price']['total']['with_tax'] = format_price(
            namespace['price']['products']['with_tax'] + shipping_price)
        namespace['price']['products']['with_tax'] = format_price(
            namespace['price']['products']['with_tax'])
        namespace['price']['products']['without_tax'] = format_price(
            namespace['price']['products']['without_tax'])
        namespace['price']['shippings']['with_tax'] = format_price(
            shipping_price)
        # Customer
        customer_id = self.get_property('customer_id')
        user = context.root.get_user(customer_id)
        namespace['customer'] = {'id': customer_id,
                                 'title': user.get_title(),
                                 'email': user.get_property('email'),
                                 'phone1': user.get_property('phone1'),
                                 'phone2': user.get_property('phone2')}
        # Addresses
        addresses = shop.get_resource('addresses').handler
        get_address = addresses.get_record_namespace
        bill_address = self.get_property('bill_address')
        delivery_address = self.get_property('delivery_address')
        namespace['delivery_address'] = get_address(delivery_address)
        namespace['bill_address'] = get_address(bill_address)
        # Carrier
        namespace['carrier'] = u'xxx'
        namespace['payment_way'] = u'xxx'
        return namespace


    ##################################################
    # Workflow
    ##################################################
    def onenter_open(self):
        context = get_context()
        shop = get_shop(self)
        root = context.root
        # Remove product from stock
        order_products = self.get_resource('products')
        get_value = order_products.handler.get_record_value
        for record in order_products.handler.get_records():
            name = get_value(record, 'name')
            product_resource = context.root.get_resource(name, soft=True)
            if product_resource is None:
                continue
            quantity = get_value(record, 'quantity')
            id_declination = get_value(record, 'declination')
            product_resource.remove_from_stock(quantity, id_declination)
        # E-Mail confirmation / notification -> Order creation
        customer_email = self.get_customer_email(context)
        # Build email informations
        kw = {'order_name': self.name}
        # Send confirmation to client
        kw['order_uri'] = self.get_frontoffice_uri()
        subject = mail_confirmation_title.gettext()
        body = mail_confirmation_body.gettext(**kw)
        root.send_email(customer_email, subject, text=body)
        # Send confirmation to the shop
        subject = mail_notification_title.gettext()
        kw['order_uri'] = self.get_backoffice_uri()
        body = mail_notification_body.gettext(**kw)
        for to_addr in shop.get_property('order_notification_mails'):
            root.send_email(to_addr, subject, text=body)


    def onenter_payment_ok(self):
        context = get_context()
        shop = get_shop(self)
        # We set payment as payed
        self.set_property('is_payed', True)
        # We generate PDF
        order = None
        try:
            bill = self.generate_pdf_bill(context)
            order = self.generate_pdf_order(context)
            order.handler.name = 'Order.pdf'
            attachment = order.handler
        except Exception:
            # PDF generation is dangerous
            attachment = None
        # We send email confirmation to administrator
        subject = MSG(u'New order validated').gettext()
        text = MSG(u'New order has been validated').gettext()
        for to_addr in shop.get_property('order_notification_mails'):
            context.root.send_email(to_addr, subject,
                                    text=text, attachment=attachment)


    def onenter_preparation(self):
        # TODO:
        # We have to send email to inform customer ?
        pass


    def onenter_delivery(self):
        # Set order as sent
        self.set_property('is_sent', True)
        # Send email to inform customer
        self.order_send_email(order_shipped_subject,
                              order_shipped_text)



    def onenter_cancel(self):
        # XXX We have to send email to inform customer ?
        # Update products stock values
        context = get_context()
        order_products = self.get_resource('products')
        get_value = order_products.handler.get_record_value
        for record in order_products.handler.get_records():
            name = get_value(record, 'name')
            product_resource = context.resource.get_resource(name, soft=True)
            if product_resource is None:
                continue
            quantity = get_value(record, 'quantity')
            id_declination = get_value(record, 'declination')
            product_resource.add_on_stock(quantity, id_declination)


    ##################################################
    # Update order states
    # XXX We have to delete it ?
    ##################################################
    def set_payment_as_ok(self, payment_way, id_record, context):
        # XXX Partial payment
        payments = payment_way.get_resource('payments').handler
        record = payments.get_record(id_record)
        amount = payments.get_record_value(record, 'amount')
        if amount < self.get_property('total_price'):
            self.make_transition('open_to_partial_payment')
        else:
            self.set_as_payed(context)


    def set_as_payed(self, context):
        try:
            self.make_transition('open_to_payment_ok')
        except WorkflowError:
            self.set_workflow_state('payment_ok')


    def set_as_sent(self, context):
        try:
            self.make_transition('preparation_to_delivery')
        except WorkflowError:
            self.set_workflow_state('delivery')


    ###################################################
    # API
    ###################################################
    def get_reference(self):
        return '%.6d' % int(self.name)


    def get_customer_email(self, context):
        root = context.root
        customer_id = self.get_property('customer_id')
        user = root.get_user(customer_id)
        return user.get_property('email')


    def order_send_email(self, subject, body):
        context = get_context()
        root = context.root
        customer_id = self.get_property('customer_id')
        user = root.get_user(customer_id)
        kw = {'firstname': user.get_property('firstname'),
              'lastname': user.get_property('lastname'),
              'order_reference': self.get_reference(),
              'order_uri': self.get_frontoffice_uri()}
        customer_email = user.get_property('email')
        context.root.send_email(customer_email,
            subject.gettext(), text=body.gettext(**kw))


    def get_frontoffice_uri(self):
        shop = get_shop(self)
        base_uri = shop.get_property('shop_uri')
        customer_id = self.get_property('customer_id')
        end_uri = '/users/%s/;order_view?id=%s' % (customer_id, self.name)
        return get_reference(base_uri).resolve(end_uri)


    def get_backoffice_uri(self):
        shop = get_shop(self)
        base_uri = shop.get_property('shop_backoffice_uri')
        end_uri = '/shop/orders/%s' % self.name
        return get_reference(base_uri).resolve(end_uri)


    def notify_new_message(self, message, context):
        shop = get_shop(self)
        root = context.root
        customer_id = self.get_property('customer_id')
        customer = context.root.get_resource('/users/%s' % customer_id)
        contact = customer.get_property('email')
        subject = new_message_subject.gettext(n=self.name)
        # Send mail to customer
        text = message + new_message_footer.gettext(uri=self.get_frontoffice_uri())
        root.send_email(contact, subject, text=text, subject_with_host=False)
        # Send mail to administrators
        text = message + new_message_footer.gettext(uri=self.get_backoffice_uri())
        for to_addr in shop.get_property('order_notification_mails'):
            root.send_email(to_addr, subject, text=text, subject_with_host=False)


    ########################################################
    # PDF Generation
    ########################################################

    def generate_pdf_order(self, context):
        shop = get_shop(self)
        # Delete old pdf
        if self.get_resource('order', soft=True):
            self.del_resource('order')
        # Get template
        document = self.get_resource('/ui/backoffice/orders/order_pdf.xml')
        # Build namespace
        path = context.database.fs.get_absolute_path(self.handler.key)
        namespace = self.get_namespace(context)
        for product in namespace['products']:
            product['key'] = context.database.fs.get_absolute_path(product['key'])
            product['cover']['key'] = context.database.fs.get_absolute_path(
                                           product['cover']['key'])
        namespace['logo'] = shop.get_pdf_logo_key(context)
        namespace['pdf_signature'] = format_for_pdf(shop.get_property('pdf_signature'))
        barcode = self.get_resource('barcode', soft=True)
        if barcode:
            key = barcode.handler.key
            path = context.database.fs.get_absolute_path(key)
            namespace['order_barcode'] = path
        else:
            namespace['order_barcode'] = None
        # Build pdf
        body = stl_pmltopdf(document, namespace=namespace)
        metadata =  {'title': {'en': u'Bill'},
                     'filename': 'order.pdf'}
        return PDF.make_resource(PDF, self, 'order', body=body, **metadata)


    def generate_pdf_bill(self, context):
        shop = get_shop(self)
        # Delete old bill
        if self.get_resource('bill', soft=True):
            self.del_resource('bill')
        # Get template
        document = self.get_resource('/ui/backoffice/orders/order_facture.xml')
        # Build namespace
        namespace = self.get_namespace(context)
        namespace['logo'] = shop.get_pdf_logo_key(context)
        namespace['pdf_signature'] = format_for_pdf(shop.get_property('pdf_signature'))
        barcode = self.get_resource('barcode', soft=True)
        if barcode:
            key = barcode.handler.key
            path = context.database.fs.get_absolute_path(key)
            namespace['order_barcode'] = path
        else:
            namespace['order_barcode'] = None
        # Build pdf
        pdf = stl_pmltopdf(document, namespace=namespace)
        metadata =  {'title': {'en': u'Bill'},
                     'filename': 'bill.pdf'}
        return PDF.make_resource(PDF, self, 'bill', body=pdf, **metadata)

    ###################################################
    ## Computed fields
    ###################################################
    computed_schema = {'nb_msg': Integer(title=MSG(u'Nb messages'))}

    @property
    def nb_msg(self):
        messages = self.get_resource('messages').handler
        nb_messages = messages.get_n_records() - len(messages.search(seen=True))
        return nb_messages or None


    ###################################################
    ## Update methods
    ###################################################

    #def update_20091123(self):
    #    """
    #    Fix barcode
    #    """
    #    from shop.utils import generate_barcode
    #    shop = get_shop(self)
    #    barcode = generate_barcode(shop.get_property('barcode_format'), self.name)
    #    metadata =  {'title': {'en': u'Barcode'},
    #                 'filename': 'barcode.png'}
    #    self.del_resource('barcode', soft=True)
    #    Image.make_resource(Image, self, 'barcode', body=barcode, **metadata)
    #    # Generate PDF
    #    from itools.web import get_context
    #    context = get_context()
    #    context.resource = self
    #    bill = self.generate_pdf_bill(context)
    #    order = self.generate_pdf_order(context)



class Orders(ShopFolder):

    class_id = 'orders'
    class_title = MSG(u'Orders')
    class_views = ['view'] # 'export']
    class_version = '20091127'

    # Views
    view = OrdersView()


    def get_document_types(self):
        return [Order]

    #############################
    # Export
    #############################
    export = Export(
        export_resource=Order,
        access='is_allowed_to_edit',
        file_columns=['name', 'state', 'total_price', 'creation_datetime'])


# Register catalog fields
register_field('customer_id', String(is_indexed=True))
register_field('is_payed', Boolean(is_stored=True))
register_field('creation_datetime', DateTime(is_stored=True, is_indexed=True))

# Register resources
register_resource_class(Order)
register_resource_class(Orders)
register_resource_class(OrdersProducts)
