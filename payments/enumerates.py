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


class Devises(Enumerate):
    """ ISO 4217 """

    options = [
      {'name': '978', 'value': MSG(u'Euro'),   'code': 'EUR', 'symbol': '€'},
      {'name': '840', 'value': MSG(u'Dollar'), 'code': 'USD', 'symbol': '$'},
      ]


class PaymentSuccessState(Enumerate):

    options = [
      {'name': '1',  'value': MSG(u'Payment successfull')},
      {'name': '0', 'value': MSG(u'Payment error')},
      ]


class PaymentWayList(Enumerate):

    options = [
      #{'name': 'paypal', 'value': u'Paypal'},
      {'name': 'paybox', 'value': u'Paybox'},
      ]
