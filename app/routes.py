import os
import csv
import json
import datetime
from app import app
from flask import make_response, request, redirect, render_template, url_for
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
from .ns_scan_captures import Sections
from .ns_scan_captures import prescan
from .ns_scan_captures import primary_scan


@app.route('/', methods=['GET'])
def redirect_login():
	return redirect('/login')


@app.route('/login', methods=['GET'])
def get_login():
	dict_saveFiles = {}
	print(PATH_SAVES)
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
			timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S.%f')
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
				'list_site_ignored': []
			}
			with open(PATH_CUSTOMER_SAVE_DETAILS.format(customer, timestamp), 'w') as file:
				json.dump(dict_details, file, indent=4)

		# convert services list into json format keyed by id
		# ignore if input is empty
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

				site_id = dict_['site_id'].strip() if 'site_id' in dict_ else 'GLOBAL'
				if site_id not in dict_services:
					dict_services[site_id] = {}
				
				# do not replace existing vlans
				vlan = int(dict_['vlan'].strip())
				#if vlan not in dict_services[site_id]:
				service = {
					'vlan': int(dict_['vlan'].strip()),
					'name': dict_['name'].strip(),
					'base': True
				}
				if 'management' in dict_:
					service['management'] = json.loads(dict_['management'].lower())
				dict_services[site_id][int(dict_['vlan'].strip())] = service

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
				for vlan in section.get_vlanMissing(dict_services):
					vlan_id = vlan['vlan']
					if site_id not in dict_services:
						dict_services[site_id] = {}
					if int(vlan_id) not in dict_services[site_id] and str(vlan_id) not in dict_services[site_id]:
						dict_services[site_id][vlan_id] = vlan

				# will overwrite files if already exist
				with open(path_file, 'w') as file:
					json.dump(section.get_dict_all(), file, indent=4)
		with open(path_services, 'w') as file:
			json.dump(dict_services, file, indent=4)

		#if int(request.form['flag_new']):
		#	flag_prescan = False

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
			if not dict_services[site_id][vlan_id]['base']:
				dict_services[site_id][vlan_id]['site'] = site_id
				list_missing.append(dict_services[site_id][vlan_id])
	with open(path_services, 'w') as file:
		json.dump(dict_services, file, indent=4)
	list_missing = sorted(list_missing, key = lambda i: (i['vlan'], i['site'], i['type']))

	return render_template('confirm-services.html', customer=customer, timestamp=timestamp, list_missing=list_missing, flag_prescan=flag_prescan)

@app.route('/<customer>/<timestamp>/generate-preview', methods=['POST'])
def post_preview_topology(customer, timestamp):
	if request.method == 'POST':
		print(request.form['flag_prescan'])
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
		
		dict_devices = {}
		path_prescan = PATH_CUSTOMER_PRESCAN.format(customer, timestamp)
		
		if flag_prescan:
			print('recalculating topology, please wait...')
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
							print('this is a tor: %s' % device_id)
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
		print(json.dumps(request.form, indent=4))
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
				dict_details[key] = request.form[key].split('|')
			else:
				dict_details[key] = []
		with open(PATH_CUSTOMER_SAVE_DETAILS.format(customer, timestamp), 'w') as file:
			json.dump(dict_details, file, indent=4)
		if flag:
			return redirect(url_for('get_login'))
		else:
			primary_scan(customer, timestamp)
			return redirect(url_for('get_output', customer=customer, timestamp=timestamp))

@app.route('/<customer>/<timestamp>/output', methods=['GET'])
def get_output(customer, timestamp):
	return render_template('output.html', customer=customer, timestamp=timestamp)
