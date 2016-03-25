# -*- coding: utf-8 -*-


conf = {}  # Dictionary updated by environment.load_environment

def start(rel_path_to_config_file = 'resources/default-config.ini'):
	import os
	path_to_config_file = os.path.join(os.path.dirname(__file__), rel_path_to_config_file)
	os.system('paster serve ' + path_to_config_file)
