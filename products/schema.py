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
from decimal import Decimal as decimal

# Import from itools
from itools.datatypes import DateTime, Decimal, Unicode, Boolean
from itools.datatypes import String, Integer

# Import from shop
from enumerate import CategoriesEnumerate, States, StockOptions
from shop.datatypes import ImagePathDataType
from taxes import TaxesEnumerate



#############################################
# Product schema
#############################################


product_schema = {# General informations
                  'state': States(mandatory=True, default='public'),
                  'reference': String,
                  'product_model': String,
                  'title': Unicode(multilingual=True),
                  'description': Unicode(multilingual=True),
                  'subject': Unicode(multilingual=True),
                  'cover': ImagePathDataType(mandatory=True),
                  'weight': Decimal(default=decimal(0), mandatory=True),
                  # Categories
                  'categories': CategoriesEnumerate(multiple=True, mandatory=True),
                  # Stock
                  'stock-quantity': Integer(default=0, mandatory=True),
                  'stock-option': StockOptions(mandatory=True, default='accept'),
                  # Price
                  'is_buyable': Boolean(default=True),
                  'purchase-price': Decimal,
                  'pre-tax-price': Decimal(default=decimal(0), mandatory=True),
                  'tax': TaxesEnumerate(mandatory=True),
                  # ctime,
                  'ctime': DateTime}
