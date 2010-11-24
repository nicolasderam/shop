# -*- coding: UTF-8 -*-
# Copyright (C) 2010 Sylvain Taverne <sylvain@itaapy.com>
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
from itools.datatypes import Integer, String
from itools.gettext import MSG
from itools.stl import stl
from itools.web import ERROR, INFO
from itools.xapian import PhraseQuery

# Import from ikaaro
from ikaaro.forms import SelectWidget, TextWidget
from ikaaro.registry import register_resource_class

# Import from shop
from shop.products.declination import Declination
from shop.products.enumerate import CategoriesEnumerate, ProductModelsEnumerate
from shop.modules import ShopModule
from shop.utils_views import SearchTableFolder_View


class Stock_FillStockOut(SearchTableFolder_View):

    access = 'is_allowed_to_edit'
    title = MSG(u'Fill stock')
    template = '/ui/modules/stock/fill_stock_out.xml'


    search_widgets = [TextWidget('reference', title=MSG(u'Reference')),
                      SelectWidget('abspath', title=MSG(u'Category')),
                      SelectWidget('product_model', title=MSG(u'Product model'))]

    search_schema = {'reference': String,
                     'abspath': CategoriesEnumerate,
                     'product_model': ProductModelsEnumerate}

    def get_schema(self, resource, context):
        references_number = context.get_form_value('references_number',
                              type=Integer) or 0
        schema = {'references_number': Integer}
        for i in range(1, references_number+1):
            schema.update(
              {'reference_%s' % i: String,
               'nb_declinations_%s' % i: Integer,
               'new_stock_%s' % i: Integer})
            nb_declinations = context.get_form_value('nb_declinations_%s' % i,
                                type=Integer) or 0
            for j in range(1, nb_declinations+1):
                schema['name_%s_%s' % (i, j)] = String
                schema['new_stock_%s_%s' % (i, j)] = Integer
        return schema


    def get_namespace(self, resource, context):
        namespace = {'lines': []}
        # Search
        search_template = resource.get_resource(self.search_template)
        search_namespace = self.get_search_namespace(resource, context)
        namespace['search'] = stl(search_template, search_namespace)
        # Is a research ?
        if context.uri.query.has_key('search') is False:
            return namespace
        # Get all declinations (for optimization purpose)
        all_declinations =  context.root.search(format=Declination.class_id)
        # Do
        root = context.root
        items = self.get_items(resource, context)
        for i, brain in enumerate(items):
            declinations = all_declinations.search(parent_path=brain.abspath).get_documents()
            nb_declinations = len(declinations)
            kw = {'id': i+1,
                  'reference': brain.reference,
                  'title': brain.title,
                  'href': '/' + '/'.join(brain.abspath.split('/')[2:]), # XXX Hack
                  'declinations': [],
                  'has_declination': nb_declinations > 0,
                  'nb_declinations': nb_declinations,
                  'stock_quantity': brain.stock_quantity}
            for j, declination in enumerate(declinations):
                d = {'id': j+1,
                     'name': declination.name,
                     'title': declination.declination_title,
                     'stock_quantity': declination.stock_quantity}
                kw['declinations'].append(d)
            namespace['lines'].append(kw)
            namespace['references_number'] = len(namespace['lines'])
        return namespace


    def get_items(self, resource, context, query=[]):
        query = [PhraseQuery('format', 'product')]
        return SearchTableFolder_View.get_items(self, resource, context, query)


    def action(self, resource, context, form):
        root = context.root
        references_number = form['references_number']
        for i in range(1, references_number+1):
            reference = form['reference_%s' % i]
            if not reference:
                context.message = ERROR(u'[Error] Line number %s has no reference' % i)
                context.commit = False
                return
            new_stock = form['new_stock_%s' % i]
            search = root.search(reference=reference)
            results = search.get_documents()
            if not results:
                context.message = ERROR(u'[Error] Unknow reference %s' % reference)
                context.commit = False
                return
            if len(results) > 1:
                context.message = ERROR(u'[Error] Reference %s is used %s times.' %
                                      (reference, len(results)))
                context.commit = False
                return
            product = root.get_resource(results[0].abspath)
            if new_stock:
                product.set_property('stock-quantity', new_stock)
            nb_declinations = form['nb_declinations_%s' % i]
            if nb_declinations == 0:
                continue
            declinations = list(product.search_resources(cls=Declination))
            for j in range(1, nb_declinations+1):
                suffix = '_%s_%s' % (i, j)
                name_declination = form['name'+ suffix]
                stock_declination = form['new_stock'+ suffix]
                if stock_declination:
                    declination = product.get_resource(name_declination)
                    declination.set_property('stock-quantity', stock_declination)
        context.message = INFO(u'Stock quantity has been updated')



class ShopModule_Stock(ShopModule):

    class_id = 'shop_module_stock'
    class_title = MSG(u'Manage stock')
    class_views = ['view']
    class_description = MSG(u'Manage stock')

    view = Stock_FillStockOut()


# XXX Obsolete Mechanism
#from shop.listeners import register_listener
#    def register_listeners(self):
#        register_listener('product', 'stock-quantity', self)
#        register_listener('product-declination', 'stock-quantity', self)
#
#
#    def alert(self, action, resource, class_id, property_name, old_value, new_value):
#        print 'resource', resource
#        print 'action', action
#        print 'class_id', class_id
#        print 'Property_name', property_name
#        print 'old_value', old_value
#        print 'new_value', new_value
#        operations = self.get_resource('operations')
#        operations.handler.add_record({'reference': resource.get_property('reference'),
#                                       'quantity': old_value - new_value})


register_resource_class(ShopModule_Stock)
