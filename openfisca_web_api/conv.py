# -*- coding: utf-8 -*-


# OpenFisca -- A versatile microsimulation software
# By: OpenFisca Team <contact@openfisca.fr>
#
# Copyright (C) 2011, 2012, 2013, 2014 OpenFisca Team
# https://github.com/openfisca
#
# This file is part of OpenFisca.
#
# OpenFisca is free software; you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# OpenFisca is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


"""Conversion functions"""


import json

from openfisca_core.conv import *  # noqa

from . import model


def json_to_cached_tax_benefit_system_instance(value, state = None):
    instance = model.tax_benefit_system_instance_by_json.get(value)
    if instance is None:
        instance = check(model.TaxBenefitSystem.json_to_instance)(value)
        model.tax_benefit_system_instance_by_json[value] = instance
    return instance, None


def make_json_to_cached_scenario(cache_dir, repair, tax_benefit_system):
    def json_to_cached_scenario_instance(value, state):
        json_str = json.dumps(value, separators=(',', ':'))
        scenario_instance = model.scenario_by_json_str.get(json_str)
        if scenario_instance is None:
            scenario_instance = check(
                tax_benefit_system.Scenario.make_json_to_instance(cache_dir, repair, tax_benefit_system),
                )(value)
            model.scenario_by_json_str[json_str] = scenario_instance
        return scenario_instance, None
    return json_to_cached_scenario_instance
