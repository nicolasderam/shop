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

from copy import deepcopy

# Import from itools
from itools.datatypes import String, Unicode
from itools.gettext import MSG
from itools.uri import Path, get_reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.file import Image
from ikaaro.folder_views import GoToSpecificDocument, Folder_Orphans
from ikaaro.folder_views import Folder_BrowseContent, Folder_PreviewContent
from ikaaro.forms import ImageSelectorWidget
from ikaaro.future.order import ResourcesOrderedTable
from ikaaro.registry import register_resource_class
from ikaaro.resource_views import DBResource_AddImage
from ikaaro.revisions_views import DBResource_LastChanges
from ikaaro.table import OrderedTableFile

# Import from shop
from images_views import PhotoOrderedTable_View, PhotoOrderedTable_AddRecord
from images_views import PhotoOrderedTable_EditRecord
from shop.utils import ShopFolder



class PhotoOrderedTableFile(OrderedTableFile):

    record_schema = {'title': Unicode,
                     'description': Unicode,
                     'image': String,
                     'name': String}



class PhotoAddImage(DBResource_AddImage):

    def get_root(self, context):
        return context.resource.parent.get_resource('images')


    # XXX to avoid to start on a parent of root resource
    def get_start(self, resource):
        return resource.parent.get_resource('images')



class PhotoOrderedTable(ResourcesOrderedTable):

    class_id = 'gallery-ordered-table'
    class_title = MSG(u'Photo Ordered Table')
    class_handler = PhotoOrderedTableFile
    class_views = ['view', 'back']

    orderable_classes = (Image,)
    order_root_path = '../images'

    form = [ImageSelectorWidget('name', title=MSG(u'Name'))]

    # Views
    view = PhotoOrderedTable_View()
    add_image = PhotoAddImage()
    add_record = PhotoOrderedTable_AddRecord()
    edit_record = PhotoOrderedTable_EditRecord()
    back = GoToSpecificDocument(specific_document='..',
                                title=MSG(u'See product'))


    def get_links(self):
        # Use the canonical path instead of the abspath
        base = self.get_canonical_path()
        handler = self.handler
        get_value = handler.get_record_value
        links = []

        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            links.append(str(base.resolve2(name)))

        return links


    def update_links(self, old_path, new_path):
        # Use the canonical path instead of the abspath
        base = self.get_canonical_path()
        handler = self.handler
        get_value = handler.get_record_value

        for record in handler.get_records_in_order():
            name = get_value(record, 'name')
            path = base.resolve2(name)
            if str(path) == old_path:
                # Hit the old name
                new_path2 = base.get_pathto(Path(new_path))
                handler.update_record(record.id, **{'name': str(new_path2)})

        get_context().server.change_resource(self)


    def update_relative_links(self, source):
        site_root = self.get_site_root()
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new

        handler = self.handler
        get_value = handler.get_record_value
        for record in handler.get_records():
            path = get_value(record, 'name')
            if not path:
                continue
            ref = get_reference(str(path))
            if ref.scheme:
                continue
            path = str(ref.path)
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Check if the target path has not been moved
            new_abs_path = resources_old2new.get(old_abs_path,
                                                 old_abs_path)
            # Build the new reference with the right path
            # Absolute path allow to call get_pathto with the target
            new_ref = deepcopy(ref)
            new_ref.path = str(target.get_pathto(new_abs_path))
            # Update the record
            handler.update_record(record.id, **{'name': str(new_ref)})



class ImagesFolder(ShopFolder):

    class_id = 'images-folder'
    class_title = MSG(u'Images folder')

    # Views
    browse_content = Folder_BrowseContent(access='is_admin')
    preview_content = Folder_PreviewContent(access='is_admin')
    last_changes = DBResource_LastChanges(access='is_admin')
    orphans = Folder_Orphans(access='is_admin')


    def get_document_types(self):
        return [Image]



register_resource_class(PhotoOrderedTable)
register_resource_class(ImagesFolder)
