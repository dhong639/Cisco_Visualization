# process csv file headers
import re

# directory manipulation
import os

# reading csv files
import csv

# read/write json files
import json

# save files are timestamps
import datetime

# creating zipped files
from zipfile import ZipFile

from app import app
from flask import request, redirect, render_template, url_for, send_file
from paths import PATH_CUSTOMER
from paths import PATH_SAVES
from paths import PATH_CUSTOMER_SAVE
from paths import PATH_CUSTOMER_SAVE_HARDWARE
from paths import PATH_CUSTOMER_SAVE_DETAILS
from paths import PATH_CUSTOMER_SAVE_SERVICE
from paths import PATH_CUSTOMER_TIMESTAMP_NAME
from paths import PATH_CUSTOMER_LOGS
from paths import PATH_CUSTOMER_PRESCAN
from paths import PATH_CUSTOMER_PRIMARY
from paths import PATH_CURRENT_PREVIEW
from paths import PATH_DOWNLOAD_DUMP
from .ns_scan_captures import Sections
from .ns_scan_captures import prescan
from .ns_scan_captures import primary_scan
from .generate_import_csv import load_service_import
from .generate_import_csv import load_site_import
from .generate_import_csv import load_servicePort_import
from .generate_import_csv import load_ethPort_import
from .generate_import_csv import load_portSettings_import
from .generate_import_csv import load_endpoints_import
from .generate_import_csv import load_lags_import
from .generate_import_csv import load_deviceSettings_import
from .generate_import_csv import load_bundles_import
from .generate_import_csv import load_controllers_import

@app.route('/', methods=['GET'])
def redirect_login():
	return redirect('/login')


@app.route('/login', methods=['GET'])
def get_login():
	dict_saveFiles = {}
	for customer in os.listdir(PATH_SAVES):
		if os.path.isdir(os.path.join(PATH_SAVES, customer)):
			dict_saveFiles[customer] = []
			list_saves = os.listdir(PATH_CUSTOMER.format(customer))
			timestamp_name = {}
			if 'timestamp-name.json' in list_saves:
				with open(PATH_CUSTOMER_TIMESTAMP_NAME.format(customer), 'r') as file:
					timestamp_name = json.load(file)
			for save_time in os.listdir(PATH_CUSTOMER.format(customer)):
				if os.path.isdir(os.path.join(PATH_CUSTOMER.format(customer), save_time)):
					dict_save = {
						'timestamp': save_time,
						'save_name': None
					}
					if save_time in timestamp_name:
						dict_save['save_name'] = timestamp_name[save_time]
					dict_saveFiles[customer].append(dict_save)

	return render_template('login.html', dict_saveFiles=dict_saveFiles)


@app.route('/login/load-customer', methods=['POST'])
def post_loadSave():
	if request.method == 'POST':
		customer = request.form['customer']
		timestamp = request.form['timestamp']
		flag_new = 1 if request.form['flag_new'] else 0
		# note to self: only make new directories if customer actually uploads something
		# after making directories, generate the prescan files
		if flag_new:
			timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')
			if not customer:
				customer = 'default_name'
			if not os.path.exists(PATH_CUSTOMER.format(customer)):
				os.mkdir(PATH_CUSTOMER.format(customer))
			if not os.path.exists(PATH_CUSTOMER_TIMESTAMP_NAME.format(customer, timestamp)):
				with open(PATH_CUSTOMER_TIMESTAMP_NAME.format(customer), 'w') as file:
					json.dump({}, file, indent=4)
			if not os.path.exists(PATH_CUSTOMER_SAVE.format(customer, timestamp)):
				os.mkdir(PATH_CUSTOMER_SAVE.format(customer, timestamp))
				os.mkdir(PATH_CUSTOMER_LOGS.format(customer, timestamp))
				os.mkdir(PATH_CUSTOMER_PRESCAN.format(customer, timestamp))
				os.mkdir(PATH_CUSTOMER_PRIMARY.format(customer, timestamp))
		return redirect(url_for('get_network_files', customer=customer, timestamp=timestamp, flag_new=flag_new))


@app.route('/<customer>/<timestamp>/load-network/<flag_new>')
def get_network_files(customer, timestamp, flag_new):
	return render_template('load-files.html', customer=customer, timestamp=timestamp, flag_new=flag_new)


@app.route('/<customer>/<timestamp>/convert-logs', methods=['POST'])
def post_network_files(customer, timestamp):
	if request.method == 'POST':
		# denotes whether or not a prescan is required
		#		by default, required on new customer configurations
		#		required on existing configurations if
		#			hardware is uploaded
		#			additional log files are loaded
		flag_prescan = False
		# if this is a new save file, create time-stamp to save_name mapping
		# otherwise, ignore and move on
		if int(request.form['flag_new']):
			flag_prescan = True
			# get name of save, set as "unknown_save" by default
			save_name = request.form['save_name']
			save_name = save_name if save_name else 'unknown_save'

			# read current timestamp to name mappings
			timestamp_name = {}
			with open(PATH_CUSTOMER_TIMESTAMP_NAME.format(customer), 'r') as file:
				timestamp_name = json.load(file)
			if timestamp not in timestamp_name:
				timestamp_name[timestamp] = save_name
			
			# write mappings to customer save
			with open(PATH_CUSTOMER_TIMESTAMP_NAME.format(customer), 'w') as file:
				json.dump(timestamp_name, file, indent=4)
		
			# update details.json to remember how customer wants to generate files
			# only done if this is a new save configuration
			dict_details = {
				'privileged': request.form['privileged'],
				'tor_count': request.form['tor_count'],
				'tor_weight': request.form['tor_weight'],
				'list_tor': [],
				'list_unmanaged': [],
				'list_site_gateway': [],
				'list_site_ignored': [],
				'dict_serviceUp': {},
				'sdlc': request.form['sdlc'],
				'enable': request.form['enable'],
				'ssh_username': request.form['ssh_username'],
				'ssh_password': request.form['ssh_password']
			}
			with open(PATH_CUSTOMER_SAVE_DETAILS.format(customer, timestamp), 'w') as file:
				json.dump(dict_details, file, indent=4)

		# convert services list into json format keyed by id
		# ignore if input is empty
		#		only occurs for new customers
		#		results will be overriden by a service import if one is found
		# 'input_service' is not the same as 'import_service'
		dict_services = {}
		path_services = PATH_CUSTOMER_SAVE_SERVICE.format(customer, timestamp)
		if os.path.exists(path_services):
			with open(path_services, 'r') as file:
				dict_services = json.load(file)
		if request.files['input_service']:
			file_services = request.files['input_service']
			string_services = file_services.read().decode('utf-8')
			for row in csv.DictReader(string_services.splitlines(), skipinitialspace=True):
				dict_ = {k.lower().replace(' ', '_'): v.strip() for k, v in row.items()}
				# determine if vlan belongs to a site
				#		some customers will upload services on a site-by-site basis
				#		other customers will upload services that apply for all sites
				# information used for names
				# information used to determine context of vlan
				site_id = dict_['site_id'].strip() if 'site_id' in dict_ else 'GLOBAL'
				if site_id not in dict_services:
					dict_services[site_id] = {}
				vlan = int(dict_['vlan'].strip())
				if vlan not in dict_services:
					dict_services[site_id][vlan] = {}
				if dict_['name'] not in dict_services[site_id][vlan]:
					dict_services[site_id][vlan][dict_['name']] = {}
				dict_services[site_id][vlan][dict_['name']]['base'] = True
				if 'management' in dict_:
					is_management = json.loads(dict_['management'].lower())
					dict_services[site_id][vlan][dict_['name']]['management'] = is_management

		# convert service import into json format keyed by id and name
		# either 'input_service' or 'import_service' must be present
		list_service = []
		if request.files['import_service']:
			# reset dict_services even if a new service input was provided
			dict_services = {}
			# start reading for real
			file_services = request.files['import_service']
			string_services = file_services.read().decode('utf-8').splitlines()[1:]
			for row in csv.DictReader(string_services, skipinitialspace=True):
				list_service.append(row)

		# check for existing profiles, requires service export from existing site
		# create blank files if empty
		# load existing file contents if applicable
		output_portProfiles = []
		path_primary = PATH_CUSTOMER_PRIMARY.format(customer, timestamp)
		if os.path.exists(os.path.join(path_primary, 'port-profiles.json')):
			with open(os.path.join(path_primary, 'port-profiles.json'), 'r') as file:
				output_portProfiles = json.load(file)
		# service import and eth port import are not differentiated in 'port-profiles.json'
		#		the order in which they are uploaded does not actually matter
		# this section guesses which services are associated with the profiles
		for input_portProfiles in ['import_portProfiles_service', 'import_portProfiles_eth']:
			if request.files[input_portProfiles] and list_service:
				file_portProfiles = request.files[input_portProfiles]
				string_portProfiles = file_portProfiles.read().decode('utf-8').splitlines()
				readCSV = csv.reader(string_portProfiles, delimiter=',')
				contents = list(readCSV)
				# import file contains two headers
				#		1st header marks where each service occurs
				#		2nd header marks information specific to each service
				# get each index that marks a new service
				is_indexService = re.compile(r'SERVICE (\d+)')
				list_indexService = []
				for i in range(len(contents[0])):
					cell = contents[0][i]
					match_indexService = re.match(is_indexService, str(cell))
					if match_indexService:
						list_indexService.append(i)
				index_serviceDirection = None
				if 'SERVICE DIRECTION' in contents[1]:
					index_serviceDirection = contents[1].index('SERVICE DIRECTION')
				index_name = contents[1].index('NAME')
				for i in range(2, len(contents)):
					row = contents[i]
					name = contents[i][index_name]
					# determine port type
					#		names determined by previous version of ns_scan_capture
					#		may be ideal to change to match csv import file headers
					port_type = 'eth_port'
					if index_serviceDirection:
						if row[index_serviceDirection] == 'cross':
							port_type = 'crosslink'
						elif row[index_serviceDirection] == 'up':
							port_type = 'service_up'
						elif row[index_serviceDirection] == 'down':
							port_type = 'service_down'
						elif row[index_serviceDirection] == 'no_switchport':
							port_type = 'layer3'
					# determine services used in the profiles
					#		make assumption that all services will eventually be used
					#		guess that each service name is mapped to some vlan id
					#		attempt to avoid duplicate vlan ids (mutliple names per vlan)
					# each time a service is found, add to list of services on given profile
					list_existing_serviceID = []
					for index in list_indexService:
						index_service = index
						if input_portProfiles == 'import_portProfiles_eth':
							index_service += 1 
						if row[index_service]:
							for service in list_service:
								service_name = service['NAME']
								service_id = int(service['VLAN'])
								if service_name == row[index_service]:
									# by default, only 'GLOBAL' services are possible
									# site-specific services only allowed for new imports
									# would require a 'site_id' column in GUI export csv files
									list_existing_serviceID.append(int(service_id))
									if 'GLOBAL' not in dict_services:
										dict_services['GLOBAL'] = {}
									if service_id not in dict_services['GLOBAL']:
										dict_services['GLOBAL'][service_id] = {}
									if service_name not in dict_services['GLOBAL'][service_id]:
										dict_services['GLOBAL'][service_id][service_name] = {}
									dict_services['GLOBAL'][service_id][service_name]['base'] = True
									for key in service:
										value = service[key]
										dict_services['GLOBAL'][service_id][service_name][key] = value
					output_portProfiles.append({
						'port_profile_id': i - 1,
						'site_id': 'GLOBAL',
						'port_profile_name': name,
						'port_type': port_type,
						'list_existing': list_existing_serviceID,
						'voice_vlan': None,
						'trunk_count': 0,
						'trunk_list': [],
						'native_vlan': None,
					})
		with open(os.path.join(path_primary, 'port-profiles.json'), 'w') as file:
			json.dump(output_portProfiles, file, indent=4)

		# results for port settings
		# load existing file contents if applicable
		output_portSettings = []
		if os.path.exists(os.path.join(path_primary, 'port-settings.json')):
			with open(os.path.join(path_primary, 'port-settings.json'), 'r') as file:
				output_portSettings = json.load(file)
		if request.files['import_portSettings'] and list_service:
			file_portSettings = request.files['import_portSettings']
			string_portSettings = file_portSettings.read().decode('utf-8')
			port_setting_id = 0
			for row in csv.DictReader(string_portSettings.splitlines()[1:], skipinitialspace=True):
				port_setting_id += 1
				# these are the last two columns in a port settings export
				# get rid of them, not needed and will otherwise causes errors
				if 'DO NOT EDIT PAST HERE' in row:
					del row['DO NOT EDIT PAST HERE']
				if 'OVERRIDDEN OBJECT' in row:
					del row['OVERRIDDEN OBJECT']
				if '' in row:
					del row['']
				# as with other services, search for voice vlan by name
				# only exists as a 'GLOBAL' service
				lldp_voice_vlan = None
				if row['LLDP MED SERVICE NAME']:
					service_name = row['LLDP MED SERVICE NAME']
					for service in list_service:
						service_id = int(service['VLAN'])
						if service_name == service['NAME']:
							if 'GLOBAL' not in dict_services:
								dict_services['GLOBAL'] = {}
							if service_id not in dict_services['GLOBAL']:
								dict_services['GLOBAL'][service_id] = {}
							if service_name not in dict_services['GLOBAL'][service_id]:
								dict_services['GLOBAL'][service_id][service_name] = {}
							for key in service:
								value = service[key]
								dict_services['GLOBAL'][service_id][service_name][key] = value
							dict_services['GLOBAL'][service_id][service_name]['base'] = True
							lldp_voice_vlan = int(service['VLAN'])
				output_portSettings.append({
					"voice_vlan": ['GLOBAL', lldp_voice_vlan] if lldp_voice_vlan else None,
					"stp_portfast": True if row['STP ENABLED'] == 'TRUE' else False,
					"stp_bpdufilter": row['BPDU FILTER'],
					"stp_bpduguard": True if row['BPDU GUARD'] == 'TRUE' else False,
					"stp_guardloop": True if row['GUARD LOOP'] == 'TRUE' else False,
					"poe_enabled": True if row['POE ENABLED'] == 'TRUE' else False,
					"port_security_mode": row['MAC SECURITY MODE'],
					"port_security_maximum": row['MAC LIMIT'],
					"violation_mode": row['MAC VIOLATION ACTION'],
					"aging_type": row['MAC AGING TYPE'],
					"aging_time": row['MAC AGING TIME'],
					"duplex": row['DUPLEX MODE'],
					"speed": int(row['MAX BITRATE']),
					"port_setting_id": port_setting_id,
					"port_setting_name": row['NAME']
				})
		with open(os.path.join(path_primary, 'port-settings.json'), 'w') as file:
			json.dump(output_portSettings, file, indent=4)

		# to try and intelligently choose services, services already in use are added first
		# however, not all services are inherently used in the given import files
		# in that situation, choose the first available service for a vlan ID and add to import
		# for obvious reason, requires 'import_service'
		if request.files['import_service']:
			for service in list_service:
				if 'GLOBAL' not in dict_services:
					dict_services['GLOBAL'] = {}
				vlan_id = int(service['VLAN'])
				# only the first recorded service for the number is added
				# 'GLOBAL' is the only possible site_id for existing service imports
				if vlan_id not in dict_services['GLOBAL']:
					service_name = service['NAME']
					dict_services['GLOBAL'][vlan_id] = {}
					dict_services['GLOBAL'][vlan_id][service_name] = {}
					for key in service:
						dict_services['GLOBAL'][vlan_id][service_name][key] = service[key]
					dict_services['GLOBAL'][vlan_id][service_name]['base'] = True

		# convert hardware list into dictionary for later use
		# note that each device log must have a corresponding hardware row
		# ignore if empty
		dict_hardware = {}
		path_hardware = PATH_CUSTOMER_SAVE_HARDWARE.format(customer, timestamp)
		if os.path.exists(path_hardware):
			with open(path_hardware, 'r') as file:
				dict_hardware = json.load(file)
		if request.files['input_hardware']:
			flag_prescan = True
			file_hardware = request.files['input_hardware']
			string_hardware = file_hardware.read().decode('utf-8')
			for row in csv.DictReader(string_hardware.splitlines(), skipinitialspace=True):
				hardware = {k.lower().replace(' ', '_'): v.strip() for k, v in row.items()}
				hardware['site_id'] = hardware['site_id']
				key = hardware['hostname'].upper()
				dict_hardware[key] = hardware

			# write new rows to 'hardware-list.json'
			with open(path_hardware, 'w') as file:
				json.dump(dict_hardware, file, indent=4)

		# store missing services
		# each service should only be recorded once per vlan id
		# names will be determined by the what type the service is (access, trunk, voice)
		dict_missing = {}
		# convert log files into json format keyed by device id, include hardware information
		# if not possible, treat site as 'GLOBAL', which is a default site id
		for file in request.files.getlist('input_listLogs'):
			if file:
				flag_prescan = True
				section = Sections(file, request.form['privileged'])
				device_id = section.get_deviceID()
				if device_id.upper() in dict_hardware:
					section.add_hardware(dict_hardware[device_id.upper()])
				else:
					dict_ = {
						'site_id': 'GLOBAL',
						'location': '',
						'ip_address': ''
					}
					section.add_hardware(dict_)
				filename = "{}.json".format(device_id)
				path_file = os.path.join(PATH_CUSTOMER_LOGS.format(customer, timestamp), filename)
				site_id = section.get_siteID()
				if set(dict_services.keys()) == set(['GLOBAL']):
					site_id = 'GLOBAL'
				dict_missing_current = section.get_vlanMissing(dict_services)
				for site_id in dict_missing_current:
					if site_id not in dict_missing:
						dict_missing[site_id] = {}
					for vlan_id in dict_missing_current[site_id]:
						if vlan_id not in dict_missing[site_id]:
							dict_missing[site_id][vlan_id] = []
						for type_ in dict_missing_current[site_id][vlan_id]:
							if type_ not in dict_missing[site_id][vlan_id]:
								dict_missing[site_id][vlan_id].append(type_)
						dict_missing[site_id][vlan_id].sort()
				# will overwrite files if already exist
				with open(path_file, 'w') as file:
					json.dump(section.get_dict_all(), file, indent=4)
		
		#print(json.dumps(dict_missing, indent=4))
		for site_id in dict_missing:
			if site_id not in dict_services:
				dict_services[site_id] = {}
			for vlan_id in dict_missing[site_id]:
				# by definition, missing services don't exist
				# therefore, no need to check for service_names
				if vlan_id not in dict_services[site_id]:
					name = str(vlan_id) + '_' + site_id
					if len(dict_missing[site_id][vlan_id]) == 1:
						name += ' - ' + dict_missing[site_id][vlan_id][0]
					dict_services[site_id][vlan_id] = {}
					dict_services[site_id][vlan_id][name] = {
						'name': name,
						'vlan': vlan_id,
						'type': dict_missing[site_id][vlan_id],
						'site': site_id,
						'base': False
					}

		# write to dict_services after everything is done
		with open(path_services, 'w') as file:
			json.dump(dict_services, file, indent=4)

		return redirect(url_for('get_service_confirm', customer=customer, timestamp=timestamp, flag_prescan=flag_prescan))


@app.route('/<customer>/<timestamp>/confirm-services/<flag_prescan>', methods=['GET'])
def get_service_confirm(customer, timestamp, flag_prescan):
	list_missing = []
	dict_services = {}

	path_services = PATH_CUSTOMER_SAVE_SERVICE.format(customer, timestamp)
	with open(path_services, 'r') as file:
		dict_services = json.load(file)

	list_missing = []
	for site_id in dict_services:
		for vlan_id in dict_services[site_id]:
			for vlan_name in dict_services[site_id][vlan_id]:
				if not dict_services[site_id][vlan_id][vlan_name]['base']:
					dict_services[site_id][vlan_id][vlan_name]['site'] = site_id
					list_missing.append(dict_services[site_id][vlan_id][vlan_name])
	with open(path_services, 'w') as file:
		json.dump(dict_services, file, indent=4)
	list_missing = sorted(list_missing, key = lambda i: (i['vlan'], i['site'], i['type']))

	return render_template('confirm-services.html', customer=customer, timestamp=timestamp, list_missing=list_missing, flag_prescan=flag_prescan)

@app.route('/<customer>/<timestamp>/generate-preview', methods=['POST'])
def post_preview_topology(customer, timestamp):
	if request.method == 'POST':
		flag_prescan = json.loads(request.form['flag_prescan'].lower())

		tor_count = 2
		tor_weight = 1.25
		set_tor = set()
		set_unmanaged = set()
		set_site_gateway = set()
		set_site_ignored = set()
		with open(PATH_CUSTOMER_SAVE_DETAILS.format(customer, timestamp), 'r') as file:
			dict_details = json.load(file)
			tor_count = dict_details['tor_count']
			tor_weight = dict_details['tor_weight']
			set_tor = set(dict_details['list_tor'])
			set_unmanaged = set(dict_details['list_unmanaged'])
			set_site_gateway = set(dict_details['list_site_gateway'])
			set_site_ignored = set(dict_details['list_site_ignored'])
			dict_serviceUp = dict_details['dict_serviceUp']
		
		dict_devices = {}
		path_prescan = PATH_CUSTOMER_PRESCAN.format(customer, timestamp)
		
		if flag_prescan:
			prescan(customer, timestamp, tor_count, tor_weight)
			with open(os.path.join(path_prescan, 'device.json'), 'r') as file:
				dict_devices = json.load(file)
		else:
			with open(os.path.join(path_prescan, 'device.json'), 'r') as file:
				dict_devices = json.load(file)
			# after saving a configuration, at least one set must contain elements
			#		each network must have at least one TOR
			# a newly generated configuration will skip what happens below
			# existing saves will attempt to override the prescan values to match
			for site_id in dict_devices:
				for device_id in dict_devices[site_id]:
					if len(set_tor) > 0:
						if device_id in set_tor:
							dict_devices[site_id][device_id]['is_tor'] = True
						else:
							dict_devices[site_id][device_id]['is_tor'] = False
					if len(set_unmanaged) > 0:
						if device_id in set_unmanaged:
							dict_devices[site_id][device_id]['is_managed'] = False
						else:
							dict_devices[site_id][device_id]['is_managed'] = True

		with open(os.path.join(PATH_CURRENT_PREVIEW, 'device.js'), 'w') as file:
			string = json.dumps(dict_devices, indent=4)
			string = 'var dict_devices = ' + string
			file.write(string)

		dict_interfaces = {}
		with open(os.path.join(path_prescan, 'interface.json'), 'r') as file:
			dict_interfaces = json.load(file)
		with open(os.path.join(PATH_CURRENT_PREVIEW, 'interface.js'), 'w') as file:
			string = json.dumps(dict_interfaces, indent=4)
			string = 'var dict_interfaces = ' + string
			file.write(string)

		dict_edgeFabric = {}
		with open(os.path.join(path_prescan, 'graph_fabric.json'), 'r') as file:
			dict_edgeFabric = json.load(file)
		with open(os.path.join(PATH_CURRENT_PREVIEW, 'graph_fabric.js'), 'w') as file:
			string = json.dumps(dict_edgeFabric, indent=4)
			string = 'var dict_edgeFabric = ' + string
			file.write(string)

		dict_edgesOther = {}
		with open(os.path.join(path_prescan, 'graph_other.json'), 'r') as file:
			dict_edgesOther = json.load(file)
		with open(os.path.join(PATH_CURRENT_PREVIEW, 'graph_other.js'), 'w') as file:
			string = json.dumps(dict_edgesOther, indent=4)
			string = 'var dict_edgeOther = ' + string
			file.write(string)

		dict_details = {}
		with open(os.path.join(path_prescan, 'details.json'), 'r') as file:
			dict_details = json.load(file)
		with open(os.path.join(PATH_CURRENT_PREVIEW, 'details.js'), 'w') as file:
			string = json.dumps(dict_details, indent=4)
			string = 'var dict_details = ' + string
			file.write(string)


		return redirect(url_for('get_preview_topology', customer=customer, timestamp=timestamp))


@app.route('/<customer>/<timestamp>/topology-preview')
def get_preview_topology(customer, timestamp):
	return render_template('preview.html', customer=customer, timestamp=timestamp)


@app.route('/<customer>/<timestamp>/save-edits/<flag>', methods=['POST'])
def save_topology_edits(customer, timestamp, flag):
	if request.method == 'POST':
		print(request.form['pending_serviceUp'])
		flag = int(flag)
		# customer wants to delete their current topology
		# remove all files within customer save subdirectory
		# if customer folder has no save subfolders, delete main customer folder
		if flag == 2:
			return

		# regardless of what happens, write the results to details.json
		dict_details = {}
		with open(PATH_CUSTOMER_SAVE_DETAILS.format(customer, timestamp), 'r') as file:
			dict_details = json.load(file)
		for key in ['list_tor', 'list_unmanaged', 'list_site_gateway', 'list_site_ignored']:
			if request.form[key]:
				dict_details[key] = json.loads(request.form[key])
			else:
				dict_details[key] = []
		dict_details['dict_serviceUp'] = json.loads(request.form['pending_serviceUp'])
		with open(PATH_CUSTOMER_SAVE_DETAILS.format(customer, timestamp), 'w') as file:
			json.dump(dict_details, file, indent=4)
		if flag:
			return redirect(url_for('get_login'))
		else:
			path_prescan = PATH_CUSTOMER_PRESCAN.format(customer, timestamp)
			dict_serviceUp = dict_details['dict_serviceUp']
			dict_edgesOther = {}
			with open(os.path.join(path_prescan, 'graph_other.json'), 'r') as file:
				dict_edgesOther = json.load(file)
			for device_id in dict_serviceUp:
				for interface_id in dict_serviceUp[device_id]:
					dict_edgesOther[device_id]['layer3'].append([
						'undefined_serviceUplink',
						interface_id
					])
			with open(os.path.join(path_prescan, 'graph_other.json'), 'w') as file:
				json.dump(dict_edgesOther, file, indent=4)
			primary_scan(customer, timestamp)
			return redirect(url_for('get_provisioning_confirm', customer=customer, timestamp=timestamp))


@app.route('/<customer>/<timestamp>/confirm-provisioning', methods=['GET'])
def get_provisioning_confirm(customer, timestamp):
	path_primary = PATH_CUSTOMER_PRIMARY.format(customer, timestamp)
	list_profiles = []
	with open(os.path.join(path_primary, 'port-profiles.json'), 'r') as file:
		list_profiles = [profile for profile in json.load(file) if not profile['port_profile_name']]
	list_settings = []
	with open(os.path.join(path_primary, 'port-settings.json'), 'r') as file:
		list_settings = [setting for setting in json.load(file) if not setting['port_setting_name']]
	return render_template('confirm-provisioning.html', customer=customer, timestamp=timestamp, list_profiles=list_profiles, list_settings=list_settings)


@app.route('/<customer>/<timestamp>/output', methods=['GET'])
def get_output(customer, timestamp):
	return render_template('output.html', customer=customer, timestamp=timestamp)


@app.route('/<customer>/<timestamp>/output/get_captureOutput', methods=['POST'])
def get_captureOutput(customer, timestamp):
	if request.method == 'POST':
		# path to json files
		path = PATH_CUSTOMER_PRIMARY.format(customer, timestamp)
		capture_devices = os.path.join(path, 'capture-devices.json')
		port_profiles = os.path.join(path, 'port-profiles.json')
		port_settings = os.path.join(path, 'port-settings.json')
		# create and download '0. ns_scan_capture.zip'
		path_zip = PATH_DOWNLOAD_DUMP.format('0. ns_scan_capture.zip')
		with ZipFile(path_zip, 'w') as zip:
			zip.write(capture_devices, os.path.basename(capture_devices))
			zip.write(port_profiles, os.path.basename(port_profiles))
			zip.write(port_settings, os.path.basename(port_settings))
		return send_file(path_zip, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_service_import', methods=['POST'])
def get_service_import(customer, timestamp):
	if request.method == 'POST':
		incremental = bool(request.form.get('incremental_service'))
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('1. Service Import.csv')
		# create and download '1. Service Import.csv'
		load_service_import(customer, timestamp, path_out, incremental)
		return send_file(path_out, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_site_import', methods=['POST'])
def get_site_import(customer, timestamp):
	if request.method == 'POST':
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('2. Sites Import.csv')
		# create and download '2. Sites Import.csv'
		load_site_import(customer, timestamp, path_out)
		return send_file(path_out, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_servicePort_import', methods=['POST'])
def get_servicePort_import(customer, timestamp):
	if request.method == 'POST':
		print('running {} get_servicePort_import...'.format(customer))
		incremental = bool(request.form.get('incremental_servicePort'))
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('3. Service Ports Import.csv')
		# create and download '3. Service Ports Import.csv'
		load_servicePort_import(customer, timestamp, path_out, incremental)
		return send_file(path_out, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_ethPort_import', methods=['POST'])
def get_ethPort_import(customer, timestamp):
	if request.method == 'POST':
		print('running {} get_ethPort_import...'.format(customer))
		incremental = bool(request.form.get('incremental_ethPort'))
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('4. Eth-Port Profiles Import.csv')
		# create and download '4. Eth-Port Profiles Import.csv'
		load_ethPort_import(customer, timestamp, path_out, incremental)
		return send_file(path_out, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_portSettings_import', methods=['POST'])
def get_portSettings_import(customer, timestamp):
	if request.method == 'POST':
		print('running {} get_portSettings_import...'.format(customer))
		incremental = bool(request.form.get('incremental_settings'))
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('5. Eth-Port Settings Import.csv')
		# create and download '5. Eth-Port Settings Import.csv'
		load_portSettings_import(customer, timestamp, path_out, incremental)
		return send_file(path_out, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_endpoints_import', methods=['POST'])
def get_endpoints_import(customer, timestamp):
	if request.method == 'POST':
		print('running {} get_endpoints_import...'.format(customer))
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('6. Switch Endpoints Import.csv')
		# create and download '6. Switch Endpoints Import.csv'
		load_endpoints_import(customer, timestamp, path_out)
		return send_file(path_out, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_lags_import', methods=['POST'])
def get_lags_import(customer, timestamp):
	if request.method == 'POST':
		print('running {} get_lags_import...'.format(customer))
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('7. LAGs Import.csv')
		# create and download '7. LAGs Import.csv'
		load_lags_import(customer, timestamp, path_out)
		return send_file(path_out, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_deviceSettings_import', methods=['POST'])
def get_deviceSettings_import(customer, timestamp):
	if request.method == 'POST':
		print('running {} get_deviceSettings_import...'.format(customer))
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('8. Device Settings Import.csv')
		# create and download '8. Device Settings Import.csv'
		load_deviceSettings_import(customer, timestamp, path_out)
		return send_file(path_out, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_bundles_import', methods=['POST'])
def get_bundles_import(customer, timestamp):
	if request.method == 'POST':
		print('running {} get_bundles_import...'.format(customer))
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('9. Bundles Import.csv')
		# create and download '9. Bundles Import.csv'
		load_bundles_import(customer, timestamp, path_out)
		return send_file(path_out, as_attachment=True)


@app.route('/<customer>/<timestamp>/output/get_controllers_import', methods=['POST'])
def get_controllers_import(customer, timestamp):
	if request.method == 'POST':
		print('running {} get_controllers_import...'.format(customer))

		dict_details = {}
		path_prescan = PATH_CUSTOMER_PRESCAN.format(customer, timestamp)
		with open(os.path.join(path_prescan, 'details.json'), 'r') as file:
			dict_details = json.load(file)
		# get controller name
		sdlc = dict_details['sdlc']
		# get enable password
		enable = dict_details['enable']
		# get ssh login information
		ssh_username = dict_details['ssh_username']
		ssh_password = dict_details['ssh_password']
		# path to file for writing
		path_out = PATH_DOWNLOAD_DUMP.format('10. Controllers Import.csv')
		# create and download '10. Controllers Import.csv'
		load_controllers_import(customer, timestamp, path_out, sdlc, enable, ssh_username, ssh_password)
		return send_file(path_out, as_attachment=True)
