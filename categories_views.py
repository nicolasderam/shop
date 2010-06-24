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
from itools.core import merge_dicts
from itools.datatypes import Boolean, String, Integer
from itools.gettext import MSG
from itools.stl import stl
from itools.web import STLView, get_context
from itools.xapian import PhraseQuery, AndQuery, RangeQuery
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.buttons import RemoveButton
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.utils import get_base_path_query

# Import from itws
from itws.views import BrowseFormBatchNumeric

# Import from shop
from utils import get_skin_template, get_shop



class Category_View(BrowseFormBatchNumeric):

    access = True
    title = MSG(u'View category')

    search_schema = {}
    search_template = None

    def get_template(self, resource, context):
        return get_skin_template(context, 'virtualcategory_view.xml') # XXX category_view


    def get_namespace(self, resource, context):
        shop = get_shop(resource)
        batch = None
        # Batch
        items = self.get_items(resource, context)
        if self.batch_template is not None:
            template = resource.get_resource(self.batch_template)
            namespace = self.get_batch_namespace(resource, context, items)
            batch = stl(template, namespace)
        items = self.sort_and_batch(resource, context, items)
        # Build namespace
        namespace = {'batch': list(batch),
                     'title': resource.get_title(),
                     'categories': self.get_sub_categories_namespace(resource, context),
                     'products': [],
                     'description': None}
        # Get products view box
        product_models = []
        for item_resource in items:
            # XXX Hack for cross selling
            # Cross selling return only resource not brain
            if type(item_resource) is tuple:
                 item_brain, item_resource = item_resource
            viewbox = item_resource.viewbox
            namespace['products'].append({'name': item_resource.name,
                                          'abspath': str(item_resource.get_abspath()),
                                          'box': viewbox.GET(item_resource, context)})
        # Categorie description (not for categories folder)
        namespace['description'] = resource.get_property('data')
        return namespace



    def get_sub_categories_namespace(self, resource, context):
        from categories import Category
        namespace = []
        for cat in resource.search_resources(cls=Category):
            nb_products = cat.get_nb_products(only_public=True)
            if nb_products == 0:
                continue
            img = cat.get_property('image_category')
            path_cat = resource.get_pathto(cat)
            namespace.append(
                {'name': cat.name,
                 'link': context.get_link(cat),
                 'title': cat.get_title(),
                 'css': None,
                 'nb_products': nb_products,
                 'img': str(path_cat.resolve2(img)) if img else None})
        if namespace:
            namespace[0]['css'] = 'start'
            namespace[-1]['css'] = 'end'
        return namespace



    def get_items(self, resource, context):
        site_root = context.resource.get_site_root()
        shop = get_shop(resource)
        abspath = resource.get_canonical_path()
        query = [
            get_base_path_query(str(abspath)),
            PhraseQuery('format', shop.product_class.class_id),
            PhraseQuery('workflow_state', 'public')]
        # Add query of filter
        for key, datatype in self.get_query_schema().items():
            value = context.query[key]
            if key == 'range_price' and value:
                query.append(RangeQuery('stored_price', value[0], value[1]))
            # TODO Add other filters
        return context.root.search(AndQuery(*query))


    def get_search_schema(self):
        from datatypes import IntegerRange
        return {'range_price': IntegerRange}


    def get_query_schema(self):
        shop = get_shop(get_context().resource)
        return merge_dicts(BrowseFormBatchNumeric.get_query_schema(self),
                self.get_search_schema(),
                batch_size=Integer(default=shop.get_property('categories_batch_size')),
                sort_by=String(default=shop.get_property('shop_sort_by')),
                reverse=Boolean(default=shop.get_property('shop_sort_reverse')))




##########################################################
# Comparateur
##########################################################
class Category_Comparator(STLView):

    access = True

    template = '/ui/shop/virtualcategory_comparator.xml'

    query_schema = {'products': String(multiple=True)}


    def get_namespace(self, resource, context):
        namespace = {'category': resource.get_title()}
        shop = get_shop(resource)
        # Check resources
        if len(context.query['products'])>3:
            return {'error': MSG(u'Too many products to compare')}
        if len(context.query['products'])<1:
            return {'error': MSG(u'Please select products to compare')}
        # Get real product resources
        products_to_compare = []
        products_models = []
        products = shop.get_resource('products')
        for product in context.query['products']:
            try:
                product_resource = products.get_resource(product)
            except LookupError:
                product_resource = None
            if not product_resource:
                return {'error': MSG(u'Error: product invalid')}
            products_to_compare.append(product_resource)
            product_model = product_resource.get_property('product_model')
            products_models.append(product_model)
        # Check if products models are the same
        if len(set(products_models))!=1:
            return {'error': MSG(u"You can't compare this products.")}
        # Build comparator namespace
        namespace['error'] = None
        namespace['products'] = []
        namespace['nb_products'] = len(products_to_compare)
        namespace['nb_products_plus_1'] = len(products_to_compare) +1
        abspath = context.resource.get_abspath()
        for product in products_to_compare:
            # Base products namespace
            ns = product.get_small_namespace(context)
            namespace['products'].append(ns)
        # Comporator model schema
        model = products_to_compare[0].get_product_model()
        if model:
            # Get model schema
            keys = []
            comparator = {}
            schema_resource = model.get_resource('schema').handler
            get_value = schema_resource.get_record_value
            for record in schema_resource.get_records_in_order():
                if get_value(record, 'visible') is False:
                    continue
                name = get_value(record, 'name')
                title = get_value(record, 'title')
                keys.append(name)
                comparator[name] = {'name': name,
                                    'title': title,
                                    'values': []}
            for product in products_to_compare:
                model_ns = model.get_model_namespace(product)
                kw = []
                for d in model_ns['specific_list']:
                    comparator[d['name']]['values'].append(d['value'])
            # fetch info keys in order
            namespace['comparator'] = [comparator[key] for key in keys]
        else:
            namespace['comparator'] = []
        return namespace



class Category_BackofficeView(Folder_BrowseContent):

    access = 'is_allowed_to_edit'
    title = MSG(u'View categories')

    batch_msg1 = MSG(u"There is 1 category")
    batch_msg2 = MSG(u"There are {n} categories")

    context_menus = []

    search_template = '/ui/backoffice/category_view.xml'

    table_actions = [RemoveButton(
        title=MSG(u'Remove category, sub-categories, and associated products'))]

    table_columns = [
        ('checkbox', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title')),
        ('nb_sub_categories', MSG(u'Nb sub categories'), None),
        ('nb_products', MSG(u'Nb products'), None),
        ('actions', MSG(u'Actions'), None),
        ]

    def get_items(self, resource, context, *args):
        args = list(args)
        args.append(PhraseQuery('format', 'category'))
        return Folder_BrowseContent.get_items(self, resource, context, *args)


    def get_item_value(self, resource, context, item, column):
        brain, item_resource = item
        if column == 'name':
            return brain.name, './%s/;view_categories' % brain.name
        elif column == 'nb_sub_categories':
            return item_resource.get_nb_categories()
        elif column == 'nb_products':
            nb_products = item_resource.get_nb_products()
            uri = '/categories/;browse_content?abspath=%s' % brain.abspath
            return nb_products, uri
        elif column == 'actions':
            return XMLParser("""
                <a href="./%s/" title="View category">
                  <img src="/ui/icons/16x16/view.png"/>
                </a>
                <a href="./%s/;edit" title="Edit category">
                  <img src="/ui/icons/16x16/edit.png"/>
                </a>
                """ % (brain.name, brain.name))
        return Folder_BrowseContent.get_item_value(self,
                 resource, context, item, column)
