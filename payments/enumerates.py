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

# Import from itools
from itools.datatypes import Enumerate
from itools.gettext import MSG

# Import from payment
from payment_way import PaymentWay

# Import from shop
from shop.datatypes import DynamicEnumerate



# XXX We have to use devises
class Devises(Enumerate):
    """ ISO 4217 """

    options = [
      {'name': '978', 'value': MSG(u'Euro'),   'code': 'EUR', 'symbol': '€'},
      {'name': '840', 'value': MSG(u'Dollar'), 'code': 'USD', 'symbol': '$'},
      ]


class PaymentWaysEnumerate(DynamicEnumerate):

    path = 'shop/payments/'
    format = None
