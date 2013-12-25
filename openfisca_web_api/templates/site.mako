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

<%doc>
    Site template inherited by each page
</%doc>


<%!
import urlparse

from openfisca_web_api import conf, urls
%>


<%def name="body_content()" filter="trim">
    <div class="container"><div class="row">
        <%self:breadcrumb/>
        <%self:container_content/>
        <%self:footer/>
    </div></div>
</%def>


<%def name="brand()" filter="trim">
${conf['realm']}
</%def>


<%def name="breadcrumb()" filter="trim">
        <ul class="breadcrumb">
            <%self:breadcrumb_content/>
        </ul>
</%def>


<%def name="breadcrumb_content()" filter="trim">
            <li><a href="${urls.get_url(ctx)}">${_('Home')}</a></li>
</%def>


<%def name="container_content()" filter="trim">
</%def>


<%def name="css()" filter="trim">
##    % for url in conf['assets']['site-css'].urls():
##    <link href="${url}" media="screen" rel="stylesheet">
##    % endfor
</%def>


<%def name="error_alert()" filter="trim">
    % if errors:
                <div class="alert alert-block alert-error">
                    <h4 class="alert-heading">${_('Error!')}</h4>
        % if '' in errors:
<%
            error = unicode(errors[''])
%>\
            % if u'\n' in error:
                    <pre class="break-word">${error}</error>
            % else:
                    ${error}
            % endif
        % else:
                    ${_(u"Please, correct the informations below.")}
        % endif
                </div>
    % endif
</%def>


<%def name="feeds()" filter="trim">
</%def>


<%def name="footer()" filter="trim">
        <footer class="footer">
            <%self:footer_service/>
            <p>
                ${_('{0}:').format(_('Software'))}
                <a href="https://github.com/openfisca" rel="external">OpenFisca</a>
                &mdash;
                <span>Copyright © 2011, 2012, 2013 OpenFisca Team</span>
                &mdash;
                <a href="http://www.gnu.org/licenses/agpl.html" rel="external">${_(
                    'GNU Affero General Public License')}</a>
            </p>
        </footer>
</%def>


<%def name="footer_service()" filter="trim">
</%def>


<%def name="hidden_fields()" filter="trim">
</%def>


<%def name="ie_scripts()" filter="trim">
##    <!--[if lt IE 9]>
##    % for url in conf['assets']['site-ie-js'].urls():
##        <script src="${url}"></script>
##    % endfor
##    <![endif]-->
</%def>


<%def name="metas()" filter="trim">
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    ## Make sure Internet Explorer can't use Compatibility Mode, as this will break Persona.
    <meta http-equiv="X-UA-Compatible" content="IE=Edge">
</%def>


<%def name="scripts()" filter="trim">
##    % for url in conf['assets']['site-js'].urls():
##    <script src="${url}"></script>
##    % endfor
##    ## You must include this on every page which uses navigator.id functions. Because Persona is still in development,
##    ## you should not self-host the include.js file.
##    <script src="https://login.persona.org/include.js"></script>
##    <script>
<%
##    user = model.get_user(ctx)
%>\
##var currentUser = ${user.email if user is not None else None | n, js};


##navigator.id.watch({
##    loggedInUser: currentUser,
##    onlogin: function (assertion) {
##        $.ajax({
##            type: 'POST',
##            url: '/login',
##            data: {
##                assertion: assertion
##            },
##            success: function(res, status, xhr) {
##                window.location.reload();
##            },
##            error: function(xhr, status, err) {
##                navigator.id.logout();
##                alert(${_(u"Login failure: ") | n, js} + err);
##            }
##        });
##    },
##    onlogout: function () {
##        $.ajax({
##            type: 'POST',
##            url: '/logout',
##            success: function(res, status, xhr) {
##                window.location.reload();
##            },
##            error: function(xhr, status, err) {
##                alert(${_(u"Logout failure: ") | n, js} + err);
##            }
##        });
##    }
##});


##$(function () {
##    $('.dropdown-toggle').dropdown();

##    $('.sign-in').click(function() {
##        navigator.id.request();
##    });

##    $('.sign-out').click(function() {
##        navigator.id.logout();
##    });
##});
##    </script>
</%def>


##<%def name="scripts_bootstrap()" filter="trim">
##    <script src="${urlparse.urljoin(conf['bootstrap'], 'js/bootstrap.min.js')}"></script>
##</%def>


<%def name="title_content()" filter="trim">
<%self:brand/>
</%def>


<%def name="topbar()" filter="trim">
    <nav class="navbar navbar-default navbar-fixed-default navbar-inverse" role="navigation">
        <div class="navbar-header">
            <button type="button" class="navbar-toggle" data-toggle="collapse" data-target=".navbar-topbar-collapse">
            <span class="sr-only">${_(u'Toggle navigation')}</span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            <span class="icon-bar"></span>
            </button>
            <a class="navbar-brand" href="/"><%self:brand/> <span class="label label-warning">pre-alpha</span></a>
        </div>
        <div class="collapse navbar-collapse navbar-topbar-collapse">
            <ul class="nav navbar-nav">
                <%self:topbar_dropdown_admin/>
##                <li><a href="${model.Formula.get_admin_class_url(ctx)}">${_('Formulas')}</a></li>
##                <li><a href="${model.Parameter.get_admin_class_url(ctx)}">${_('Parameters')}</a></li>
            </ul>
            <%self:topbar_user/>
        </div>
    </nav>
</%def>


<%def name="topbar_dropdown_admin()" filter="trim">
##<%
##    is_admin = model.is_admin(ctx)
##    user = model.get_user(ctx)
##%>\
##    % if is_admin or user is not None:
##                <li class="dropdown">
##                    <a class="dropdown-toggle" data-toggle="dropdown" href="#">${_('Administration')} <b class="caret"></b></a>
##                    <ul class="dropdown-menu">
##        % if is_admin:
##                        <li><a href="${model.Account.get_admin_class_url(ctx)}">${_('Accounts')}</a></li>
##        % endif
##                        <li><a href="${model.Formula.get_admin_class_url(ctx)}">${_('Formulas')}</a></li>
##        % if is_admin:
##                        <li><a href="${model.Session.get_admin_class_url(ctx)}">${_('Sessions')}</a></li>
##        % endif
##                        <li><a href="${model.Parameter.get_admin_class_url(ctx)}">${_('Parameters')}</a></li>
##                    </ul>
##                </li>
##    % endif
</%def>


<%def name="topbar_user()" filter="trim">
##            <ul class="nav navbar-nav navbar-right">
##<%
##    user = model.get_user(ctx)
##%>\
##    % if user is None:
##                <li><a class="sign-in" href="#" title="${_(u'Sign in with Persona')}">${_(u'Sign in')}</a></li>
##    % else:
##                <li class="active"><a href="${user.get_admin_url(ctx)}"><span class="glyphicon glyphicon-user"></span> ${
##                        user.email}</a></li>
####                <li class="active"><a href=""><span class="glyphicon glyphicon-user"></span> ${user.get_title(ctx)}</a></li>
##                <li><a class="sign-out" href="#" title="${_(u'Sign out from Persona')}">${_(u'Sign out')}</a></li>
##    % endif
##            </ul>
</%def>


<%def name="trackers()" filter="trim">
</%def>


<!DOCTYPE html>
<html lang="${ctx.lang[0][:2]}">
<head>
    <%self:metas/>
    <title>${self.title_content()}</title>
    <%self:css/>
    <%self:feeds/>
    <%self:ie_scripts/>
</head>
<body>
    <%self:topbar/>
    <%self:body_content/>
    <%self:scripts/>
    <%self:trackers/>
</body>
</html>

