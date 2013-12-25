## -*- coding: utf-8 -*-


## OpenFisca -- A versatile microsimulation software
## By: OpenFisca Team <contact@openfisca.fr>
##
## Copyright (C) 2011, 2012, 2013 OpenFisca Team
## https://github.com/openfisca
##
## This file is part of OpenFisca.
##
## OpenFisca is free software; you can redistribute it and/or modify
## it under the terms of the GNU Affero General Public License as
## published by the Free Software Foundation, either version 3 of the
## License, or (at your option) any later version.
##
## OpenFisca is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Affero General Public License for more details.
##
## You should have received a copy of the GNU Affero General Public License
## along with this program.  If not, see <http://www.gnu.org/licenses/>.

<%!
import pprint
%>


<%inherit file="/site.mako"/>


<%def name="breadcrumb_content()" filter="trim">
            <%parent:breadcrumb_content/>
            <li class="active">${title}</li>
</%def>


<%def name="container_content()" filter="trim">
        <div class="alert alert-block alert-error">
            <h2 class="alert-heading">${title}</h2>
            <p>${explanation}</p>
    % if comment:
            <p>${comment}</p>
    % endif
    % if message:
            <p>${message}</p>
    % endif
    % if dump:
        % if isinstance(dump, basestring):
            <pre class="break-word">${dump}</pre>
        % else:
            <pre class="break-word">${pprint.pformat(dump).decode('utf-8')}</pre>
        % endif
    % endif
        </div>
</%def>


<%def name="title_content()" filter="trim">
${title} - ${parent.title_content()}
</%def>

