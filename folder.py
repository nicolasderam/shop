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
from itools.core import merge_dicts
from itools.datatypes import PathDataType, String
from itools.stl import rewrite_uris
from itools.uri import Path, Reference, get_reference
from itools.web import get_context

# Import from ikaaro
from ikaaro.folder import Folder
from ikaaro.folder_views import Folder_Orphans, Folder_BrowseContent
from ikaaro.folder_views import Folder_PreviewContent
from ikaaro.forms import XHTMLBody
from ikaaro.registry import register_field
from ikaaro.resource_views import DBResource_Backlinks
from ikaaro.revisions_views import DBResource_CommitLog
from ikaaro.webpage import _get_links, _change_link

# Import from itws
from itws.tags import TagsAware

# Import from shop
from datatypes import AbsolutePathDataTypeEnumerate
from utils import get_parent_paths



class ShopFolder(Folder):
    """
    ShopFolder add:
      - Automatic implementation of get_links / update_links to PathDatatype
        and XHTMLBody
      - Guest user cannot access to some views of ShopFolder
    """
    browse_content = Folder_BrowseContent(access='is_allowed_to_edit')
    preview_content = Folder_PreviewContent(access='is_allowed_to_edit')
    orphans = Folder_Orphans(access='is_allowed_to_edit')
    commit_log = DBResource_CommitLog(access='is_allowed_to_edit')
    backlinks = DBResource_Backlinks(access='is_allowed_to_edit')

    def _get_catalog_values(self):
        return merge_dicts(
                super(ShopFolder, self)._get_catalog_values(),
                parent_paths=get_parent_paths(self.get_abspath()))


    def get_links(self):
        links = Folder.get_links(self)
        # General informations
        base = self.get_canonical_path()
        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        # We update XHTMLBody links
        for key, datatype in self.get_metadata_schema().items():
            multilingual = getattr(datatype, 'multilingual', False)
            langs = languages if multilingual is True else [None]
            if issubclass(datatype, XHTMLBody):
                for lang in langs:
                    events = self.get_property(key, language=lang)
                    if not events:
                        continue
                    links.extend(_get_links(base, events))
            elif issubclass(datatype, PathDataType):
                # Relative path
                for lang in langs:
                    path = self.get_property(key, language=lang)
                    if path is None:
                        continue
                    links.append(str(base.resolve2(path)))
            elif issubclass(datatype, AbsolutePathDataTypeEnumerate):
                # Absolute path
                for lang in langs:
                    path = self.get_property(key, language=lang)
                    if path is None:
                        continue
                    links.append(str(path))
        # Tagaware ?
        if isinstance(self, TagsAware):
            links.extend(TagsAware.get_links(self))
        return links


    def update_links(self, source, target):
        base = self.get_canonical_path()
        resources_new2old = get_context().database.resources_new2old
        base = str(base)
        old_base = resources_new2old.get(base, base)
        old_base = Path(old_base)
        new_base = Path(base)

        site_root = self.get_site_root()
        languages = site_root.get_property('website_languages')
        links = []
        for key, datatype in self.get_metadata_schema().items():
            multilingual = getattr(datatype, 'multilingual', False)
            langs = languages if multilingual is True else [None]
            if issubclass(datatype, XHTMLBody):
                for lang in langs:
                    events = self.get_property(key, language=lang)
                    if not events:
                        continue
                    events = _change_link(source, target, old_base, new_base,
                                          events)
                    events = list(events)
                    self.set_property(key, events, language=lang)
            elif issubclass(datatype, PathDataType):
                # Relative path
                for lang in langs:
                    path = self.get_property(key, language=lang)
                    if path is None:
                        continue
                    path = str(old_base.resolve2(path))
                    if path == source:
                        # Hit the old name
                        new_path = str(new_base.get_pathto(target))
                        self.set_property(key, new_path, language=lang)
            elif issubclass(datatype, AbsolutePathDataTypeEnumerate):
                # Absolute path
                for lang in langs:
                    path = self.get_property(key, language=lang)
                    if path is None:
                        continue
                    path = str(path)
                    path = resources_new2old.get(path, path)
                    if path == source:
                        # Hit the old name
                        self.set_property(key, str(target), language=lang)
        # Tagaware ?
        if isinstance(self, TagsAware):
            TagsAware.update_links(self, source, target)

        # Change resource
        get_context().database.change_resource(self)


    def update_relative_links(self, source):
        target = self.get_canonical_path()
        resources_old2new = get_context().database.resources_old2new
        resources_new2old = get_context().database.resources_new2old

        def my_func(value):
            # Skip empty links, external links and links to '/ui/'
            uri = get_reference(value)
            if uri.scheme or uri.authority or uri.path.is_absolute():
                return value
            path = uri.path
            if not path or path.is_absolute() and path[0] == 'ui':
                return value

            # Strip the view
            name = path.get_name()
            if name and name[0] == ';':
                view = '/' + name
                path = path[:-1]
            else:
                view = ''

            # Resolve Path
            # Calcul the old absolute path
            old_abs_path = source.resolve2(path)
            # Get the 'new' absolute parth
            new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)

            path = str(target.get_pathto(new_abs_path)) + view
            value = Reference('', '', path, uri.query.copy(), uri.fragment)
            return str(value)

        languages = self.get_site_root().get_property('website_languages')
        for key, datatype in self.get_metadata_schema().items():
            multilingual = getattr(datatype, 'multilingual', False)
            langs = languages if multilingual is True else [None]
            if issubclass(datatype, XHTMLBody):
                for lang in langs:
                    events = self.get_property(key, language=lang)
                    if not events:
                        continue
                    events = rewrite_uris(events, my_func)
                    events = list(events)
                    self.set_property(key, events, language=lang)
            elif issubclass(datatype, PathDataType):
                # Relative path
                for lang in langs:
                    path = self.get_property(key, language=lang)
                    if path is None:
                        continue
                    # Calcul the old absolute path
                    old_abs_path = source.resolve2(path)
                    # Check if the target path has not been moved
                    new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)
                    # Build the new path
                    # Absolute path allow to call get_pathto with the target
                    new_path = str(target.get_pathto(new_abs_path))
                    self.set_property(key, new_path, language=lang)
            elif issubclass(datatype, AbsolutePathDataTypeEnumerate):
                # Absolute path
                for lang in langs:
                    path = self.get_property(key, language=lang)
                    if path is None:
                        continue
                    # Calcul the old absolute path
                    path = str(path)
                    old_abs_path = resources_new2old.get(path, path)
                    # Check if the target path has not been moved
                    new_abs_path = resources_old2new.get(old_abs_path, old_abs_path)
                    self.set_property(key, new_abs_path, language=lang)


register_field('parent_paths', String(is_indexed=True, multiple=True))
