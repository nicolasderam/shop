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
from itools.xml import XMLParser

# Import from ikaaro
from ikaaro.forms import SelectRadio, Widget, stl_namespaces


class SelectRadioList(SelectRadio):

    template = list(XMLParser("""
        <ul>
          <li stl:if="has_empty_option">
            <input type="radio" name="${name}" value="" checked="checked"
              stl:if="none_selected"/>
            <input type="radio" name="${name}" value=""
              stl:if="not none_selected"/>
            <stl:block stl:if="not is_inline"><br/></stl:block>
          </li>
          <li stl:repeat="option options">
            <input type="radio" id="${id}-${option/name}" name="${name}"
              value="${option/name}" checked="checked"
              stl:if="option/selected"/>
            <input type="radio" id="${id}-${option/name}" name="${name}"
              value="${option/name}" stl:if="not option/selected"/>
            <label for="${id}-${option/name}">${option/value}</label>
            <stl:block stl:if="not is_inline"><br/></stl:block>
          </li>
        </ul>
        """, stl_namespaces))


class SelectRadioImages(SelectRadio):

    template = list(XMLParser("""
        <ul style="list-style-type:none;margin:0;padding:0;">
          <li stl:if="has_empty_option" style="width:110px;height=110px;float:left;">
            <input id="${id}" type="radio" name="${name}" value="" checked="checked"
              stl:if="none_selected"/>
            <input id="${id}" type="radio" name="${name}" value=""
              stl:if="not none_selected"/>
            <label for="${id}"
              style="width:60px;height:60px;display:block;border:1px dashed gray;
                    padding:20px;">
              No picture
            </label>
          </li>
          <li style="float:left;width:110px;height=110px;" stl:repeat="option options">
            <input type="radio" id="${id}-${option/name}" name="${name}"
              value="${option/name}" checked="checked"
              stl:if="option/selected"/>
            <input type="radio" id="${id}-${option/name}" name="${name}"
              value="${option/name}" stl:if="not option/selected"/>
            <label for="${id}-${option/name}">
              <img src="${option/link}/;thumb?width=100&amp;height=100" title=" ${option/value}"/>
            </label>
          </li>
        </ul>
        """, stl_namespaces))


class SelectRadioColor(SelectRadio):

    template = list(XMLParser("""
        <ul class="select-radio-color">
          <li stl:repeat="option options" class="${id}-opt-color">
            <div id="opt-${id}-${option/name}"
              style="background-color:${option/color}"
              title="${option/value}" stl:omit-tag="option/selected">
            <div id="opt-${id}-${option/name}"
              style="background-color:${option/color}"
              title="${option/value}" stl:omit-tag="not option/selected" class="selected">
              <input
                type="radio" id="${id}-${option/name}" name="${name}"
                value="${option/name}" checked="checked"
                stl:if="option/selected"/>
              <input
                type="radio" id="${id}-${option/name}" name="${name}"
                value="${option/name}" stl:if="not option/selected"/>
              <span>${option/value}</span>
            </div>
            </div>
          </li>
        </ul>
        <script>
          $(document).ready(function() {
            $(".${id}-opt-color div").each(function(){
              $(this).click(function(){
                $(".${id}-opt-color div").removeClass('selected');
                $(this).addClass('selected');
                $(this).children('input').attr('checked', 'checked');
              })
            });
          });
        </script>
        """, stl_namespaces))



class RangeSlider(Widget):

    template = list(XMLParser("""
          <input type="text" id="${id}-amount" style="border:0; color:#f6931f; font-weight:bold;" />
          <div id="${id}"/>
          <script type="text/javascript" src="/ui/shop/js/jquery.slider.js"/>
          <script type="text/javascript">
          $(function() {
            $("#${id}").slider({
              range: true,
              min: 0,
              max: 5000,
              values: [0, 10],
              slide: function(event, ui) {
                $("#${id}-amount").val(ui.values[0] + ' - ' + ui.values[1]);
              }
            });
          });
          </script>
        """, stl_namespaces))

    def get_namespace(self, datatype, value):
        namespace = Widget.get_namespace(self, datatype, value)
        namespace['title'] = self.title
        return namespace
