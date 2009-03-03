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
from itools.gettext import MSG
from itools.handlers import checkid
from itools.web import STLView

# Import from ikaaro
from ikaaro import messages
from ikaaro.buttons import RemoveButton
from ikaaro.forms import AutoForm, RTEWidget, TextWidget, ImageSelectorWidget
from ikaaro.views import CompositeForm
from ikaaro.folder_views import Folder_BrowseContent
from ikaaro.table_views import Table_AddRecord

# Import from shop
from schema import product_schema


class ProductModels_View(Folder_BrowseContent):

    table_actions = [RemoveButton]
    search_template = None

    title = MSG(u'View')
    batch_msg1 = MSG(u"There is 1 product model.")
    batch_msg2 = MSG(u"There are ${n} models.")


    table_columns = [
        ('checkbox', None),
        ('name', MSG(u'Name')),
        ('title', MSG(u'Title'))
        ]

    # XXX We can't delete model if it is used



class ProductEnumAttribute_AddRecord(Table_AddRecord):

    title = MSG(u'Add Record')
    submit_value = MSG(u'Add')


    def action_add_or_edit(self, resource, context, record):
        record['name'] = checkid(record['title'])
        resource.handler.add_record(record)

