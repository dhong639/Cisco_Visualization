import os
import json
from .ScannerDevice import ScannerDevice
from .ScannerNeighbor import ScannerNeighbor
from .Graph import Graph
from paths import PATH_CUSTOMER_LOGS
from paths import PATH_CUSTOMER_PRESCAN
from paths import PATH_CUSTOMER_SAVE_DETAILS
from paths import PATH_CUSTOMER_SAVE_SERVICE
from paths import PATH_CUSTOMER_PRIMARY


def get_dict_device(sections):
	list_ = [
		'running-config',
		'lacp sys-id',
		'interface config',
		'interface | inc Ethernet|Vlan',
		'unique vlans found',
		'total vlans found'
	]
	dict_ = {}
	for section in sections:
		if section in list_:
			dict_[section] = sections[section]
	return dict_


def get_dict_neighbor(sections):
	list_ = ['cdp neig', 'lldp nei de', 'lldp neighbors']
	dict_ = {}
	for section in sections:
		if section in list_:
			dict_[section] = sections[section]
	return dict_


# set_intf_portType
#		input:
#			device_id		string	hostname of device
#			intf_id			string	name of port
#			type_			string	eth_port, service_up, service_down, layer3, or crosslink
#			capture_devices	dict	object containing device and port information
#		function:
#			by default, 'port_type' is not a field when creating port objects
#			if 'port_type' does not already exist or is 'fabric', set as the given type
def set_intf_portType(device_id, intf_id, type_, capture_devices):
	interface = capture_devices[device_id]['ivn_port'][intf_id]
	if 'port_type' not in interface or interface['port_type'] == 'fabric':
		capture_devices[device_id]['ivn_port'][intf_id]['port_type'] = type_

# set_intf_portType
#		input:
#			device_id		string	hostname of device
#			intf_id			string	name of port
#			capture_devices	dict	object containing device and port information
#		output:
#			count			int		number of vlans in device
#		function: 
#			count number of access and trunk vlans configured on port
#			count number of vlans that traversed the port
def count_vlan(device_id, intf_id, capture_devices):
	dict_port = capture_devices[device_id]['ivn_port'][intf_id]
	count = 0
	if dict_port['access_vlan'] != None:
		count += 1
	if dict_port['trunk_native_vlan'] != None:
		count += 1
	count += len(dict_port['trunk_list'])
	count += len(dict_port['list_foundMAC'])
	return count

def get_setVLAN(dict_):
	set_vlan = set()
	if 'voice_vlan' in dict_:
		set_vlan.add(dict_['voice_vlan'])
	if 'native_vlan' in dict_:
		set_vlan.add(dict_['native_vlan'])
	if 'trunk_list' in dict_:
		for vlan in dict_['trunk_list']:
			set_vlan.add(vlan)
	if 'list_existing' in dict_:
		for vlan in dict_['list_existing']:
			set_vlan.add(vlan)
	if None in set_vlan:
		set_vlan.remove(None)
	return set_vlan

def prescan(customer, timestamp, tor_count, tor_weight):
	# number of tors to automatically generate
	tor_count = 2 if tor_count == '' else int(tor_count)
	#print(tor_count)
	# how likely it is for a layer3 switch to be a ToR
	tor_weight = 1.25 if tor_weight == '' else float(tor_weight)

	# prelimary information for devices
	#		only the device_id is strictly necessary
	#		everything else is for display purposes only
	dict_devices = {}

	# prelimary information for ivn_ports
	#		maps interface name to VLANs set for and encountered by port
	dict_interfaces = {}

	# lldp and cdp sections from input logs
	dict_neighbors = {}

	# total list of all file names
	input_logs = PATH_CUSTOMER_LOGS.format(customer, timestamp)
	list_files = sorted(os.listdir(input_logs))

	# categorize device hostnames based on site id
	# further categorize into subcategories:
	#		router, no vlans in mac address table
	#		tor, most vlans in mac address table
	#		nodes, all other devices
	dict_site2device = {}

	# write to output for preview webpage
	output_prescan = PATH_CUSTOMER_PRESCAN.format(customer, timestamp)

	for filename in list_files:
		with open(os.path.join(input_logs, filename), 'r') as file:
			# convert file contents into sections
			sections = json.load(file)
			# get device_id as hostname of device
			#		must be done first to set identify hardware information
			device_id = sections['device_id']

			scannerDevice = ScannerDevice(sections)
			# use site_id to key information for dict_site2device
			site_id = scannerDevice.get_siteID()
			if site_id not in dict_site2device:
				# 'list_router' denotes all devices that never encountered VLANs, define now
				# 'list_tor' denotes devices that encountered the most VLANs, define later
				# 'list_node' denotes all other devices, define later
				# 'list_all' is all fabric devices, define now, used to determine tors and nodes
				dict_site2device[site_id] = {
					'list_tor': [],
					'list_node': [],
					'list_all': [],
					'list_unmanaged': {
						'router': [],
						'other': []
					}
				}
			# get total number of vlans found in 'show mac address-table'
			# for layer 3 switches, multiply the number by a given weight
			count_vlanTotal = scannerDevice.get_count_vlanTotal()
			if scannerDevice.get_layer3():
				count_vlanTotal = count_vlanTotal * tor_weight

			# if no VLANs have been found, treat the device as a router
			if count_vlanTotal == 0:
				#dict_site2device[site_id]['list_router'].append(device_id)
				dict_site2device[site_id]['list_unmanaged']['router'].append(device_id)
			# otherwise, the device is either a ToR or a fabric switch
			else:
				dict_site2device[site_id]['list_all'].append({
					'hostname': device_id,
					'count_vlan': count_vlanTotal
				})

			if site_id not in dict_devices:
				dict_devices[site_id] = {}
			dict_devices[site_id][device_id] = scannerDevice.get_dictPreview_device()
			dict_interfaces[device_id] = scannerDevice.get_dictPreview_interface()
			dict_neighbors[device_id] = get_dict_neighbor(sections)

	# determine ToRs and fabric devices from 'list_all'
	#		by default, ToRs are the two devices with the most mac address-table entries
	#			layer 3 switches are preferred and given higher weights
	#		fabric switches are everything else
	# delete 'list_all' afterwards for sake of simplicity
	for site_id in dict_site2device:
		length = len(dict_site2device[site_id])
		# if customer inputs tor_count greater than actual number of devices in site
		#		set tor_count for this specific site to that of the length
		#		otherwise, use given tor_count as normal
		length = length if tor_count > length else tor_count
		# get sorted list of all devices in current site
		list_ = dict_site2device[site_id]['list_all']
		list_ = sorted(list_, key=lambda i: (i['count_vlan'], i['hostname']))
		# last elements in list are the TORs, set 'is_tor' on those devices to True
		dict_site2device[site_id]['list_tor'] = [item['hostname'] for item in list_[-length:]]
		for device_id in dict_site2device[site_id]['list_tor']:
			dict_devices[site_id][device_id]['is_tor'] = True
		# every thing before the TOR devices in 'list_node' are normal devices
		dict_site2device[site_id]['list_node'] = [item['hostname'] for item in list_[:-length]]
		# remove 'list_all' for readability
		del dict_site2device[site_id]['list_all']

	# process neighbor information and create topology
	scannerNeighbor = ScannerNeighbor(dict_site2device, dict_neighbors)
	# remove redundant links if possible
	scannerNeighbor.clean_edges()

	# links within network
	#		'sourceID' denotes source device
	#			'targetID' denotes target device
	#				'capability' denotes type of device (switch, router, etc.)
	#			'pairs' denotes source/target interface pairs
	dict_edgeFabric = scannerNeighbor.get_edgesFabric()
	# links to outside network
	#		layer3		link to some router that allows for internet access
	#		eth_port	link to some edge device that isn't a router
	dict_edgesOther = scannerNeighbor.get_edgesOther()

	# write results to static javascript resources
	with open(os.path.join(output_prescan, 'device.json'), 'w') as file:
		json.dump(dict_devices, file, indent=4)
	with open(os.path.join(output_prescan, 'interface.json'), 'w') as file:
		json.dump(dict_interfaces, file, indent=4)
	with open(os.path.join(output_prescan, 'graph_fabric.json'), 'w') as file:
		json.dump(dict_edgeFabric, file, indent=4)
	with open(os.path.join(output_prescan, 'graph_other.json'), 'w') as file:
		json.dump(dict_edgesOther, file, indent=4)


def primary_scan(customer, timestamp):
	# items below are used for device-to-site mapping
	set_tor = set()
	set_unmanaged = set()
	set_siteGateway = set()
	with open(PATH_CUSTOMER_SAVE_DETAILS.format(customer, timestamp), 'r') as file:
		dict_details = json.load(file)
		set_tor = set(dict_details['list_tor'])
		set_unmanaged = set(dict_details['list_unmanaged'])
		set_siteGateway = set(dict_details['list_site_gateway'])
	
	# items below are used for topology information
	path_prescan = PATH_CUSTOMER_PRESCAN.format(customer, timestamp)
	dict_edgeFabric = {}
	path_graph_fabric = os.path.join(path_prescan, 'graph_fabric.json')
	with open(path_graph_fabric, 'r') as file:
		dict_edgeFabric = json.load(file)
	dict_edgeOther = {}
	path_graph_other = os.path.join(path_prescan, 'graph_other.json')
	with open(path_graph_other, 'r') as file:
		dict_edgeOther = json.load(file)

	# store complete device information
	capture_devices = {}

	# categorize device hostnames based on site id
	# further categorize into subcategories:
	#		router, no vlans in mac address table
	#		tor, most vlans in mac address table
	#		nodes, all other devices
	dict_site2device = {}
	set_site = set()
	count = 0

	dir_files = PATH_CUSTOMER_LOGS.format(customer, timestamp)
	list_files = os.listdir(dir_files)
	for filename in list_files:
		sections = {}
		device_id = None
		site_id = None
		with open(os.path.join(dir_files, filename), 'r') as file:
			sections = json.load(file)
			device_id = sections['device_id']
			site_id = sections['site_id']
			if site_id not in set_siteGateway:
				set_site.add(site_id)
			if site_id not in dict_site2device:
				# all devices in this section have been defined earlier
				# fill in the fields as they are encountered
				dict_site2device[site_id] = {
					'list_tor': [],
					'list_node': [],
					'list_unmanaged': {
						'router': [],
						'other': []
					}
				}
			scanner_device = ScannerDevice(sections)
			# overwrite TOR status with preview results
			scanner_device.set_isTOR(device_id in set_tor)
			if device_id in set_tor:
				scanner_device.set_isTOR(True)
				dict_site2device[site_id]['list_tor'].append(device_id)
			# overwrite is_managed with preview results, depends on layer3 capabilities
			scanner_device.set_isManaged(device_id not in set_unmanaged)
			if device_id in set_unmanaged:
				if scanner_device.get_layer3() == True:
					dict_site2device[site_id]['list_unmanaged']['router'].append(device_id)
				else:
					dict_site2device[site_id]['list_unmanaged']['other'].append(device_id)
			if device_id not in set_tor and device_id not in set_unmanaged:
				dict_site2device[site_id]['list_node'].append(device_id)
			if device_id not in set_unmanaged:
				count += 1
				capture_devices[device_id] = scanner_device.get_dict()

	# create graph
	graph = Graph(count, set_siteGateway, dict_site2device, dict_edgeFabric, dict_edgeOther)

	# set parent nodes
	# in regards to path from node to ToR
	# save ports used on path from source to ToR for crosslink purposes
	dict_path = {}
	for device_id in capture_devices:
		if capture_devices[device_id]['is_tor'] == False:
			site_id = capture_devices[device_id]['site_id']
			path = graph.path_toTOR(site_id, device_id)
			if path != None and len(path) >= 2:
				source_id = path[0]
				target_id = path[1]
				list_pairs = graph.get_pairs_fabric(source_id, target_id)
				capture_devices[device_id]['expected_parent_id'] = target_id
				capture_devices[device_id]['expected_parent_intf'] = list_pairs
				for i in range(len(path) - 1):
					source_id = path[i]
					target_id = path[i + 1]
					if source_id not in dict_path:
						dict_path[source_id] = set()
					if target_id not in dict_path:
						dict_path[target_id] = set()
					list_pairs = graph.get_pairs_fabric(source_id, target_id)
					for pair in list_pairs:
						dict_path[source_id].add(pair[0])
						dict_path[target_id].add(pair[1])
			#print(graph.path_toTOR(site_id, device_id))
	
	"""print('test')
	print(dict_path)
	for device_id in dict_path:
		dict_path[device_id] = sorted(dict_path[device_id])
	print(json.dumps(dict_path, indent=4))"""

	# determine paths from noRoute to gateway sites
	list_path_gatewaySite = []
	for site_id in set_site:
		#path = graph.path_toGateway(site_id)
		#list_path_gatewaySite.append(path)
		list_path_gatewaySite.append(graph.path_toGateway(site_id))
		#print(site_id)
		#print(path)

	##############################################################################
	# set port types
	#		1.	determine fabric ports
	#			2.	all links between ToRs are crosslink
	#				any path from a noRoute to gateway site is a service path
	#				3.	for path up to gateway site, set ports as service_up
	#				4.	for path down to noRoute site, set ports as service_down
	#		for non-fabric ports
	#		5.	any link to a known or unknown router is a service_up
	#		6.	any port with non-fabric neighbor is an eth_port
	#		7.	any port connected to something with an access vlan is an eth_port
	##############################################################################

	# set fabric ports
	for sourceID in dict_edgeFabric:
		for targetID in dict_edgeFabric[sourceID]:
			list_intfPair = graph.get_pairs_fabric(sourceID, targetID)
			# note that links are bidirectional
			# for link target to source, will set port types again, but nothing will change
			if list_intfPair != None:
				for pair in list_intfPair:
					if pair[0] != None:
						set_intf_portType(sourceID, pair[0], 'fabric', capture_devices)
					if targetID in capture_devices and pair[1] != None:
						set_intf_portType(targetID, pair[1], 'fabric', capture_devices)

	# set crosslinks for lags
	#		check if there is a direct link between two ToRs
	#		if there is, set all interface pairs between the two to 'crosslink'
	for site_id in dict_site2device:
		list_tor = dict_site2device[site_id]['list_tor']
		length = len(list_tor)
		for i in range(length):
			tor_i = list_tor[i]
			# note that links are bidirectional
			for j in range(i+1, length):
				tor_j = list_tor[j]
				# if tors have no direct link, no port_types are set
				list_intfPair = graph.get_pairs_fabric(tor_i, tor_j)
				# note that the graph has not been cleaned
				#		represents more accurate view of graph
				#		some pairs will contain None instead of interface names
				if list_intfPair:
					for pair in list_intfPair:
						if pair[0] != None:
							set_intf_portType(tor_i, pair[0], 'crosslink', capture_devices)
						if pair[1] != None:
							set_intf_portType(tor_j, pair[1], 'crosslink', capture_devices)

	# set service ports for paths to gateway site(s)
	for path in list_path_gatewaySite:
		# note that paths are not bidirectional
		# paths will be shared among sites
		# shouldn't be possible for ports on different paths to overlap
		for i in range(len(path) - 1):
			source_id = path[i]
			target_id = path[i+1]
			list_intfPair = graph.get_pairs_fabric(source_id, target_id)
			for pair in list_intfPair:
				# set source port type
				if pair[0] != None:
					if count_vlan(source_id, pair[0], capture_devices) > 0:
						set_intf_portType(source_id, pair[0], 'service_up', capture_devices)
					else:
						set_intf_portType(source_id, pair[0], 'layer3', capture_devices)
				# set target port type
				if pair[1] != None:
					if count_vlan(target_id, pair[1], capture_devices) > 0:
						set_intf_portType(target_id, pair[1], 'service_down', capture_devices)
					else:
						set_intf_portType(target_id, pair[1], 'layer3', capture_devices)

	# set service ports
	#		if a device is connected to a known layer3 device, set interface to 'layer3'
	#		if neighbor information for port reports connection to router, set as 'service_up'
	# set eth ports
	#		if neighbor information reports connection to non-layer3 and access_vlan exists,
	#			set as eth_port
	for device_id in dict_edgeOther:
		list_intf_eth = graph.get_intf_eth(device_id)
		if list_intf_eth != None:
			for intf in list_intf_eth:
				access_vlan = capture_devices[device_id]['ivn_port'][intf]['access_vlan']
				if access_vlan != None:
					set_intf_portType(device_id, intf, 'eth_port', capture_devices)
		list_intf_layer3 = graph.get_intf_layer3(device_id)
		if list_intf_layer3:
			for intf in list_intf_layer3:
				if count_vlan(device_id, intf, capture_devices) == 0:
					set_intf_portType(device_id, intf, 'layer3', capture_devices)
				else:
					set_intf_portType(device_id, intf, 'service_up', capture_devices)

	# set eth_ports not reported by neighbor discovery
	#		access vlan must exist
	#		port must be on and connected to something
	for device_id in capture_devices:
		for port_id in capture_devices[device_id]['ivn_port']:
			port = capture_devices[device_id]['ivn_port'][port_id]
			access_vlan = port['access_vlan']
			connected = port['connected']
			if access_vlan != None and connected == True and 'port_type' not in port:
				set_intf_portType(device_id, port_id, 'eth_port', capture_devices)

	# after everything is done, set crosslinks
	#		port must be a fabric port
	#		port has is not in the list of paths
	for device_id in capture_devices:
		for port_id in capture_devices[device_id]['ivn_port']:
			port = capture_devices[device_id]['ivn_port'][port_id]
			if device_id in dict_path and port_id not in dict_path[device_id]:
				if 'port_type' in port and port['port_type'] == 'fabric':
					set_intf_portType(device_id, port_id, 'crosslink', capture_devices)

	# if vlans are not unique per site, then vlans are applied everywhere
	# in this situation, the site_id is always considered "GLOBAL"
	dict_services = {}
	is_service_bySite = True
	with open(PATH_CUSTOMER_SAVE_SERVICE.format(customer, timestamp), 'r') as file:
		dict_services = json.load(file)
		if set(dict_services.keys()) == set(['GLOBAL']):
			is_service_bySite = False
	# customers should define whether or not a service is management
	# if they don't determine by matching VLAN numbers and IP addresses
	# if the IP address of a vlan is same as IP address of device, that vlan is management
	for site_id in dict_services:
		for service_id in dict_services[site_id]:
			for service_name in dict_services[site_id][service_id]:
				base = dict_services[site_id][service_id][service_name]['base']
				if 'management' not in dict_services[site_id][service_id][service_name] or not base:
					# even services not previously defined by a customer input
					# shall now considered part of the input and saved as such
					# regardless of whether not not a management vlan is found
					dict_services[site_id][service_id][service_name]['management'] = False
					# determine if vlan should be considered a management vlan
					for device_id in capture_devices:
						device = capture_devices[device_id]
						if device['site_id'] == site_id or site_id == 'GLOBAL':
							if int(service_id) in device['vlans']:
								device_ip = device['ip_address']
								vlan_ip = device['vlans'][int(service_id)]['ip_address']
								flag = device_ip == vlan_ip
								dict_services[site_id][service_id][service_name]['management'] = flag
	with open(PATH_CUSTOMER_SAVE_SERVICE.format(customer, timestamp), 'w') as file:
		json.dump(dict_services, file, indent=4)

	# define port settings
	list_portSetting = []
	#list_existingSetting = []
	path_existing = PATH_CUSTOMER_PRIMARY.format(customer, timestamp)
	index_portSetting = 1
	with open(os.path.join(path_existing, 'port-settings.json'), 'r') as file:
		list_portSetting = json.load(file)
		if len(list_portSetting) > 0:
			index_portSetting = list_portSetting[-1]['port_setting_id']
	for device_id in capture_devices:
		site_id = capture_devices[device_id]['site_id']
		if is_service_bySite == False:
			site_id = 'GLOBAL'
		for port_id in capture_devices[device_id]['ivn_port']:
			port_setting_id = None
			port = capture_devices[device_id]['ivn_port'][port_id]
			voice_pair = None
			voice_vlan = port['voice_vlan']
			if voice_vlan != None:
				voice_pair = [site_id, voice_vlan]
			
			for setting in list_portSetting:
				is_match = True
				for key in setting.keys():
					if key == 'voice_vlan':
						if setting[key] != voice_pair:
							is_match = False
					elif key != 'port_setting_id' and key != 'port_setting_name':
						if setting[key] != port[key]:
							is_match = False
				if is_match == True:
					port_setting_id = setting['port_setting_id']
			
			if not port_setting_id:
				port_setting_id = len(list_portSetting) + index_portSetting
				list_portSetting.append(
					{
						"port_setting_id": port_setting_id,
						"port_setting_name": None,
						"voice_vlan": voice_pair,
						"stp_portfast": port["stp_portfast"],
						"stp_bpdufilter": port["stp_bpdufilter"], 
						"stp_bpduguard": port["stp_bpduguard"], 
						"stp_guardloop": port["stp_guardloop"], 
						"poe_enabled": port["poe_enabled"], 
						"port_security_mode": port["port_security_mode"], 
						"port_security_maximum": port["port_security_maximum"], 
						"violation_mode": port["violation_mode"], 
						"aging_type": port["aging_type"], 
						"aging_time": port["aging_time"], 
						"duplex": port["duplex"], 
						"speed": port["speed"]
					}
				)
			capture_devices[device_id]['ivn_port'][port_id]['port_setting_id'] = port_setting_id

	# define and get port profiles (existing and new)
	list_portProfile = []
	path_existing = PATH_CUSTOMER_PRIMARY.format(customer, timestamp)
	index_portProfile = 1
	with open(os.path.join(path_existing, 'port-profiles.json'), 'r') as file:
		# at this point, all profiles that previously existed will be present
		# existing profiles are sorted in ascending order of 'port_profile_id'
		#		set port_profile_id as last profile_id found in list
		#		any new port_profile_id increments from this value 
		list_portProfile = json.load(file)
		if len(list_portProfile) > 0:
			index_portProfile = list_portProfile[-1]['port_profile_id']
	for device_id in capture_devices:
		for port_id in capture_devices[device_id]['ivn_port']:
			port = capture_devices[device_id]['ivn_port'][port_id]
			if 'port_type' in port and port['port_type'] != 'fabric':
				# information to check if port profile exists
				#		port_type 
				#		site_id is from device, unless services are global or port_type is layer3
				#		set_vlanCurrent is all vlans on port
				#		port_profile_id is None for now
				#			use an existing id if port_type, site_id, and set_vlanCurrent match
				#			otherwise, count up from last known port_profile_id
				#				last known is count of total previously known port profile ids
				port_type = port['port_type']
				site_id = capture_devices[device_id]['site_id']
				if is_service_bySite == False:
					site_id = 'GLOBAL'
				site_id = site_id if port['port_type'] != 'layer3' else None
				set_vlanCurrent = get_setVLAN(port)
				if port['port_type'] == 'crosslink':
					set_vlanCurrent = set()
				#print(set_vlanCurrent)
				port_profile_id = None
				# compare site_id, port_type, vlans against all profiles that currently exist
				# if found, use vlan id of that existing profile
				# otherwise, create new profile and increment port_profile_id
				for profile in list_portProfile:
					#set_vlanExist = get_setVLAN(profile)
					same_type = profile['port_type'] == port_type
					same_vlan = get_setVLAN(profile) == set_vlanCurrent
					same_site = profile['site_id'] == site_id
					if same_type and same_vlan and same_site:
						port_profile_id = profile['port_profile_id']
						#print('\t', str(port_profile_id), '\t', str(get_setVLAN(profile)))
				if not port_profile_id:
					port_profile_id = len(list_portProfile) + index_portProfile
					#print('\t\t', str(port_profile_id))
					list_portProfile.append({
						"port_profile_id": port_profile_id,
						"port_profile_name": None,
						"site_id": site_id, 
						"port_type": port["port_type"], 
						"native_vlan": port["native_vlan"], 
						"voice_vlan": port["voice_vlan"], 
						"trunk_count": len(port["trunk_list"]), 
						"trunk_list": port["trunk_list"], 
						"list_existing": []
					})
				capture_devices[device_id]['ivn_port'][port_id]['port_profile_id'] = port_profile_id

	path_primary = PATH_CUSTOMER_PRIMARY.format(customer, timestamp)
	# output device information to file
	with open(os.path.join(path_primary, 'capture-devices.json'), 'w') as file:
		json.dump(capture_devices, file, indent=4)
	# output port settings to file
	with open(os.path.join(path_primary, 'port-settings.json'), 'w') as file:
		json.dump(list_portSetting, file, indent=4)
	# output port profiles to file
	with open(os.path.join(path_primary, 'port-profiles.json'), 'w') as file:
		json.dump(list_portProfile, file, indent=4)
