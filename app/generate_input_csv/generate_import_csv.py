import json
import os
from .processInput import get_count_maxPort
from .processInput import format_provisioning
from .processInput import format_timestamp
from paths import PATH_CUSTOMER_SAVE
from paths import PATH_CUSTOMER_PRIMARY
from paths import PATH_CUSTOMER_PRESCAN
from .makeImport_service import makeImport_service
from .makeImport_site import makeImport_site
from .makeImport_servicePortProfile import makeImport_servicePortProfile
from .makeImport_ethPortProfile import makeImport_ethPortProfile
from .makeImport_ethPortSetting import makeImport_ethPortSetting
from .makeImport_endpoint import makeImport_endpoint
from .makeImport_lag import makeImport_lag
from .makeImport_deviceSetting import makeImport_deviceSetting
from .makeImport_bundle import makeImport_bundle
from .makeImport_controller import makeImport_controller

def get_dict_service(customer, timestamp):
	dict_service = {}
	# open 'service-import.csv' for reading
	path = PATH_CUSTOMER_SAVE.format(customer, timestamp)
	path_servicesInput = os.path.join(path, 'service.json')
	with open(path_servicesInput, 'r') as file:
		dict_service = json.load(file)
	# return object
	return dict_service

def get_dict_device(customer, timestamp):
	dict_device = {}
	# open 'capture-devices.csv' for reading
	path = PATH_CUSTOMER_PRIMARY.format(customer, timestamp)
	path_captureDevice = os.path.join(path, 'capture-devices.json')
	with open(path_captureDevice, 'r') as file:
		dict_device = json.load(file)
	# return object
	return dict_device

def get_list_provisioning(dict_device, dict_service, customer, timestamp, file_name):
	if not file_name.endswith('.json'):
		file_name += '.json'
	# open 'port_profiles.json' or 'port_profiles.json' for reading
	path = PATH_CUSTOMER_PRIMARY.format(customer, timestamp)
	path_provisioning = os.path.join(path, file_name)
	list_provisioning = []
	with open(path_provisioning, 'r') as file:
		list_provisioning = json.load(file)
	"""# add names and port counts to provisioning (default settings, no name found)
	format_provisioning(list_provisioning, dict_device, dict_service)"""
	return list_provisioning

def get_list_portProfile(dict_device, dict_service, customer, timestamp):
	return get_list_provisioning(dict_device, dict_service, customer, timestamp, 'port-profiles')

def get_list_portSetting(dict_device, dict_service, customer, timestamp):
	return get_list_provisioning(dict_device, dict_service, customer, timestamp, 'port-settings')

def load_service_import(customer, timestamp, path_out, incremental):
	# create and download '1. Service Import.csv'
	dict_service = get_dict_service(customer, timestamp)
	if incremental:
		dict_ = {}
		for site_id in dict_service:
			for service_id in dict_service[site_id]:
				for service_name in dict_service[site_id][service_id]:
					if not dict_service[site_id][service_id][service_name]['base']:
						service = dict_service[site_id][service_id][service_name]
						if site_id not in dict_:
							dict_[site_id] = {}
						if service_id not in dict_[site_id]:
							dict_[site_id][service_id] = {}
						dict_[site_id][service_id][service_name] = service
		dict_service = dict_
	makeImport_service(dict_service, path_out, 'v0.2', format_timestamp(timestamp))

def load_site_import(customer, timestamp, path_out):
	# create and download '2. Sites Import.csv'
	dict_device = get_dict_device(customer, timestamp)
	dict_service = get_dict_service(customer, timestamp)
	makeImport_site(dict_device, dict_service, path_out, 'v0.2', timestamp)

def load_servicePort_import(customer, timestamp, path_out, incremental):
	# create and download '3. Service Ports Import.csv'
	dict_device = get_dict_device(customer, timestamp)
	dict_service = get_dict_service(customer, timestamp)
	list_portProfile = get_list_portProfile(dict_device, dict_service, customer, timestamp)
	if incremental:
		list_portProfile = [profile for profile in list_portProfile if not profile['port_profile_name']]
	# add names and port counts to provisioning (default settings, no name found)
	format_provisioning(list_portProfile, dict_device, dict_service)
	makeImport_servicePortProfile(dict_service, list_portProfile, path_out, 'v0.2', format_timestamp(timestamp))

def load_ethPort_import(customer, timestamp, path_out, incremental):
	# create and download '4. Eth-Port Profiles Import.csv'
	dict_device = get_dict_device(customer, timestamp)
	dict_service = get_dict_service(customer, timestamp)
	list_portProfile = get_list_portProfile(dict_device, dict_service, customer, timestamp)
	if incremental:
		list_portProfile = [profile for profile in list_portProfile if not profile['port_profile_name']]
	# add names and port counts to provisioning (default settings, no name found)
	format_provisioning(list_portProfile, dict_device, dict_service)
	makeImport_ethPortProfile(dict_service, list_portProfile, path_out, 'v0.2', format_timestamp(timestamp))

def load_portSettings_import(customer, timestamp, path_out, incremental):
	# create and download '5. Eth-Port Settings Import.csv'
	dict_device = get_dict_device(customer, timestamp)
	dict_service = get_dict_service(customer, timestamp)
	list_portSetting = get_list_portSetting(dict_device, dict_service, customer, timestamp)
	if incremental:
		list_portSetting = [setting for setting in list_portSetting if not setting['port_setting_name']]
	# add names and port counts to provisioning (default settings, no name found)
	format_provisioning(list_portSetting, dict_device, dict_service)
	makeImport_ethPortSetting(dict_service, list_portSetting, path_out, 'v0.2', format_timestamp(timestamp))

def load_endpoints_import(customer, timestamp, path_out):
	# create and download '6. Switch Endpoints Import.csv'
	dict_device = get_dict_device(customer, timestamp)
	port_count = get_count_maxPort(dict_device)
	makeImport_endpoint(dict_device, port_count, path_out, 'v0.2', format_timestamp(timestamp))

def load_lags_import(customer, timestamp, path_out):
	# create and download '7. LAGs Import.csv'
	dict_device = get_dict_device(customer, timestamp)
	dict_service = get_dict_service(customer, timestamp)
	list_portProfile = get_list_portProfile(dict_device, dict_service, customer, timestamp)
	dict_edgesFabric = {}
	path_prescan = PATH_CUSTOMER_PRESCAN.format(customer, timestamp)
	with open(os.path.join(path_prescan, 'graph_fabric.json'), 'r') as file:
		dict_edgesFabric = json.load(file)
	format_provisioning(list_portProfile, dict_device, dict_service)
	makeImport_lag(dict_device, list_portProfile, dict_edgesFabric, path_out, 'v0.2', format_timestamp(timestamp))

def load_deviceSettings_import(customer, timestamp, path_out):
	# create and download '8. Device Settings Import.csv'
	makeImport_deviceSetting(path_out, 'v0.2', timestamp, link=None)

def load_bundles_import(customer, timestamp, path_out):
	# create and download '9. Bundles Import.csv'
	dict_device = get_dict_device(customer, timestamp)
	dict_service = get_dict_service(customer, timestamp)
	list_portProfile = get_list_portProfile(dict_device, dict_service, customer, timestamp)
	format_provisioning(list_portProfile, dict_device, dict_service)
	list_portSetting = get_list_portSetting(dict_device, dict_service, customer, timestamp)
	format_provisioning(list_portSetting, dict_device, dict_service)
	port_count = get_count_maxPort(dict_device)
	makeImport_bundle(dict_device, list_portProfile, list_portSetting, port_count, path_out, 'v0.2', format_timestamp(timestamp))

def load_controllers_import(customer, timestamp, path_out, sdlc, enable, ssh_username, ssh_password):
	# create and download '10. Controllers Import.csv'
	dict_device = get_dict_device(customer, timestamp)
	dict_service = get_dict_service(customer, timestamp)
	makeImport_controller(dict_device, dict_service, sdlc, enable, ssh_username, ssh_password, path_out, 'v0.10', format_timestamp(timestamp))
