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
from itools.datatypes import Enumerate
from itools.gettext import MSG
from itools.web import get_context

# Import from shop
from utils import get_shop


class BarcodesFormat(Enumerate):

    none = [{'name': '0', 'value': MSG(u'None')}]

    codes = [
      'auspost',
      'azteccode',
      'rationalizedCodabar',
      'code11',
      'code128',
      'code2of5',
      'code39',
      'code93',
      'datamatrix',
      'ean13',
      'isbn',
      'ean8',
      'ean5',
      'ean2',
      'interleaved2of5',
      'japanpost',
      'kix',
      'maxicode',
      'msi',
      'onecode',
      'pdf417',
      'pharmacode',
      'plessey',
      'postnet',
      'qrcode',
      'raw',
      'royalmail',
      'rss14',
      'rsslimited',
      'rssexpanded',
      'symbol',
      'upca',
      'upce']

    @classmethod
    def get_options(cls):
        return cls.none + [{'name': x, 'value': x} for x in cls.codes]



class SortBy_Enumerate(Enumerate):

    options = [
      {'name': 'title', 'value': MSG(u'Product title')},
      {'name': 'mtime', 'value': MSG(u'Modification date')},
      {'name': 'ctime', 'value': MSG(u'Creation date')},
      {'name': 'stored_price', 'value': MSG(u'Price')}]



class TagsList(Enumerate):

    site_root = None

    @staticmethod
    def decode(value):
        if not value:
            return None
        return str(value)


    @staticmethod
    def encode(value):
        if value is None:
            return ''
        return str(value)


    @classmethod
    def get_options(cls):
        tags_folder = cls.site_root.get_resource('tags', soft=True)
        if tags_folder is None:
            return []
        options = [{'name': tag.name, 'value': tag.get_title()}
                   for tag in tags_folder.search_resources(format='tag') ]
        options.sort()
        return options


class CountriesZonesEnumerate(Enumerate):

    @classmethod
    def get_options(cls):
        context = get_context()
        # Search shop
        shop = get_shop(context.resource)
        # Get options
        resource = shop.get_resource('countries-zones').handler
        return [{'name': str(record.id),
                 'value': resource.get_record_value(record, 'title')}
                    for record in resource.get_records()]


