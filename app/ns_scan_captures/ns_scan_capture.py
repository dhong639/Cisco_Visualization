import os
import csv
import json
from .ScannerDevice import ScannerDevice
from .Graph import Graph
from paths import PATH_CUSTOMER_SAVE_HARDWARE
from paths import PATH_CUSTOMER_LOGS
from paths import PATH_CUSTOMER_PRESCAN
from paths import PATH_CUSTOMER_SAVE_DETAILS


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
	#capture_devices[device_id]['ivn_port'][intf_id]['port_type'] = type_

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
					'list_router': [],
					'list_tor': [],
					'list_node': [],
					'list_all': []
				}
			# get total number of vlans found in 'show mac address-table'
			# for layer 3 switches, multiply the number by a given weight
			count_vlanTotal = scannerDevice.get_count_vlanTotal()
			if scannerDevice.get_layer3():
				count_vlanTotal = count_vlanTotal * tor_weight

			# if no VLANs have been found, treat the device as a router
			if count_vlanTotal == 0:
				dict_site2device[site_id]['list_router'].append(device_id)
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
		#print(dict_site2device[site_id]['list_tor'])
		for device_id in dict_site2device[site_id]['list_tor']:
			dict_devices[site_id][device_id]['is_tor'] = True
		# every thing before the TOR devices in 'list_node' are normal devices
		dict_site2device[site_id]['list_node'] = [item['hostname'] for item in list_[:-length]]
		# remove 'list_all' for readability
		del dict_site2device[site_id]['list_all']
	
	# process neighbor information and create topology
	graph = Graph(dict_site2device, dict_neighbors)
	# remove redundant links if possible
	graph.clean_edges()
	print(json.dumps(graph.get_weights(), indent=4))

	# links within network
	#		'sourceID' denotes source device
	#			'targetID' denotes target device
	#				'capability' denotes type of device (switch, router, etc.)
	#			'pairs' denotes source/target interface pairs
	dict_edgeFabric = graph.get_edgesFabric()
	# links to outside network
	#		layer3		link to some router that allows for internet access
	#		eth_port	link to some edge device that isn't a router
	dict_edgesOther = graph.get_edgesOther()

	# write results to static javascript resources
	with open(os.path.join(output_prescan, 'device.json'), 'w') as file:
		json.dump(dict_devices, file, indent=4)
	with open(os.path.join(output_prescan, 'interface.json'), 'w') as file:
		json.dump(dict_interfaces, file, indent=4)
	with open(os.path.join(output_prescan, 'graph_fabric.json'), 'w') as file:
		json.dump(dict_edgeFabric, file, indent=4)
	with open(os.path.join(output_prescan, 'graph_other.json'), 'w') as file:
		json.dump(dict_edgesOther, file, indent=4)


"""def primary_scan(customer, privileged, set_tor, set_router, set_gatewaySite, is_debug=False):
	# determine if site_id is included in services-import.csv
	# affects how port profiles and settings are counted
	is_service_bySite = False
	with open(os.path.join(PATH_INPUT.format(customer), 'service-import.csv'), 'r') as file:
		reader = csv.reader(file)
		header = [item.lower().replace(' ', '_') for item in next(reader)]
		if 'site_id' in header:
			is_service_bySite = True

	# store complete device information
	capture_devices = {}

	# lldp and cdp sections from input logs
	dict_neighbors = {}

	# see if logs were properly processed
	dict_sections = {}

	# total list of all file names
	input_logs = 'customers/{}/input/logs'.format(customer)
	list_files = sorted(os.listdir(input_logs))

	# physical location information for devices
	input_hardware = 'customers/{}/input/hardware-list.csv'.format(customer)
	list_hardware = format_hardware(input_hardware)

	# categorize device hostnames based on site id
	# further categorize into subcategories:
	#		router, no vlans in mac address table
	#		tor, most vlans in mac address table
	#		nodes, all other devices
	dict_site2device = {}

	# output location of capture-devices.json, provisioning_state.json, and the import csv files
	output_customer = 'customers/{}/output'.format(customer)
	
	for filename in list_files:
		with open(input_logs + '/' + filename) as file:
			# convert file contents into sections
			sections = Sections(file, privileged)
			# get device_id as hostname of device
			#		must be done first to set identify hardware information
			device_id = sections.get_deviceID()
			hardware = None
			for row in list_hardware:
				if row['hostname'].lower() == device_id.lower():
					hardware = row
					break
			# scan device for necessary configuration details
			scannerDevice = ScannerDevice(sections.get_dict_device(), hardware)
			# use site_id to key information for dict_site2device
			site_id = scannerDevice.get_siteID()
			if site_id not in dict_site2device:
				# 'list_router' denotes all devices that never encountered VLANs, define now
				# 'list_tor' denotes devices that encountered the most VLANs, define later
				# 'list_node' denotes all other devices, define later
				# 'list_all' is all fabric devices, define now, used to determine tors and nodes
				dict_site2device[site_id] = {
					'list_router': [],
					'list_tor': [],
					'list_node': [],
				}
			# determine what kind of device the given node is
			#		since prescan has been done, the role of each device is known
			#		check if device id is in respective set, then append and set field
			if device_id in set_tor:
				dict_site2device[site_id]['list_tor'].append(device_id)
				scannerDevice.set_isTOR()
			elif device_id in set_router:
				dict_site2device[site_id]['list_router'].append(device_id)
				scannerDevice.set_isRouter()
			else:
				dict_site2device[site_id]['list_node'].append(device_id)
			# still need neighbor information to get link information later on
			dict_neighbors[device_id] = sections.get_dict_neighbor()
			# debug if needed
			if is_debug == True:
				dict_sections[device_id] = sections.get_dict_all()
			# store complete device information
			if device_id not in set_router:
				capture_devices[device_id] = scannerDevice.get_dict()

	# create Graph
	graph = Graph(dict_site2device, dict_neighbors)
	dict_edgesFabric = graph.get_edgesFabric()
	dict_edgesOther = graph.get_edgesOther()
	list_path_gatewaySite = []
	for source_site in dict_site2device:
		if source_site not in set_gatewaySite:
			shortest_path = []
			length = float('inf')
			for target_site in set_gatewaySite:
				path = graph.get_path_site2site(source_site, target_site)
				if len(path) < length:
					shortest_path = path
			list_path_gatewaySite.append(shortest_path)
	
	#for path in list_path_gatewaySite:
	#	print(path)

	# print debug if needed
	if is_debug == True:
		with open(output_customer + '/map.json', 'w') as file:
			json.dump(dict_edgesFabric, file, indent=4)
		with open(output_customer + '/edges_other.json', 'w') as file:
			json.dump(dict_edgesOther, file, indent=4)
		with open(output_customer + '/site2device.json', 'w') as file:
			json.dump(dict_site2device, file, indent=4)

	# based on path to TOR, set parent of node
	for device_id in capture_devices:
		if capture_devices[device_id]['is_tor'] != True:
			path = graph.get_path_node2TOR(device_id)
			if path != None:
				capture_devices[device_id]['expected_parent_id'] = path[1]
				list_intfPair = graph.get_list_intfPair(device_id, path[1])
				capture_devices[device_id]['expected_parent_intf'] = list_intfPair

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
	for sourceID in dict_edgesFabric:
		for targetID in dict_edgesFabric[sourceID]:
			list_intfPair = graph.get_list_intfPair(sourceID, targetID)
			# note that links are bidirectional
			# for link target to source, will set port types again, but nothing will change
			for pair in list_intfPair:
				if pair[0] != None:
					set_intf_portType(sourceID, pair[0], 'fabric', capture_devices)
				if targetID in capture_devices and pair[1] != None:
					set_intf_portType(targetID, pair[1], 'fabric', capture_devices)

	# set crosslinks for lags
	#		check if there is a direct link between two ToRs
	#		if there is, set all interface pairs between the two to 'crosslink'
	dict_tor = graph.get_tor()
	for site_id in dict_tor:
		list_tor = list(dict_tor[site_id])
		length = len(list_tor)
		for i in range(length):
			tor_i = list_tor[i]
			# note that links are bidirectional
			for j in range(i+1, length):
				tor_j = list_tor[j]
				# if tors have no direct link, no port_types are set
				list_intfPair = graph.get_list_intfPair(tor_i, tor_j)
				# note that the graph has not been cleaned
				#		represents more accurate view of graph
				#		some pairs will contain None instead of interface names
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
			list_intfPair = graph.get_list_intfPair(source_id, target_id)
			for pair in list_intfPair:
				# set source port type
				if pair[0] != None:
					if(count_vlan(source_id, pair[0], capture_devices) > 0):
						set_intf_portType(source_id, pair[0], 'service_up', capture_devices)
					else:
						set_intf_portType(source_id, pair[0], 'layer3', capture_devices)
				# set target port type
				if pair[1] != None:
					if(count_vlan(target_id, pair[1], capture_devices) > 0):
						set_intf_portType(target_id, pair[1], 'service_down', capture_devices)
					else:
						set_intf_portType(target_id, pair[1], 'layer3', capture_devices)

	# set service ports
	#		if a device is connected to a known layer3 device, set interface to 'layer3'
	#		if neighbor information for port reports connection to router, set as 'service_up'
	# set eth ports
	#		if neighbor information reports connection to non-layer3 and access_vlan exists,
	#			set as eth_port
	for device_id in dict_edgesOther:
		for intf in dict_edgesOther[device_id]['layer3']:
			if count_vlan(device_id, intf, capture_devices) == 0:
				set_intf_portType(device_id, intf, 'layer3', capture_devices)
			else:
				set_intf_portType(device_id, intf, 'service_up', capture_devices)
		for intf in dict_edgesOther[device_id]['eth_port']:
			access_vlan = capture_devices[device_id]['ivn_port'][intf]['access_vlan']
			if access_vlan != None:
				set_intf_portType(device_id, intf, 'eth_port', capture_devices)

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

	# define port settings
	list_portSetting = []
	for device_id in capture_devices:
		site_id = capture_devices[device_id]['site_id']
		if is_service_bySite == False:
			site_id = None
		for port_id in capture_devices[device_id]['ivn_port']:
			port = capture_devices[device_id]['ivn_port'][port_id]
			voice_pair = None
			voice_vlan = port['voice_vlan']
			if voice_vlan != None:
				voice_pair = [site_id, voice_vlan]
			setting = {
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
			if setting not in list_portSetting:
				list_portSetting.append(setting)
			# set setting number in device port
			number = list_portSetting.index(setting) + 1
			port['port_setting_id'] = number
	for i in range(len(list_portSetting)):
		list_portSetting[i]['port_setting_id'] = i + 1
		list_portSetting[i]['port_setting_name'] = None

	# define port profiles
	list_portProfile = []
	for device_id in capture_devices:
		for port_id in capture_devices[device_id]['ivn_port']:
			port = capture_devices[device_id]['ivn_port'][port_id]
			if 'port_type' in port and port['port_type'] != 'fabric':
				site_id = capture_devices[device_id]['site_id']
				site_id = site_id if port['port_type'] != 'layer3' else None
				if is_service_bySite == False:
					site_id = None
				profile = {
					"site_id": site_id, 
					"port_type": port["port_type"], 
					"native_vlan": port["native_vlan"], 
					"voice_vlan": port["voice_vlan"], 
					"trunk_count": len(port["trunk_list"]), 
					"trunk_list": port["trunk_list"], 
				}
				if profile not in list_portProfile:
					list_portProfile.append(profile)
				# set profile number in device port
				number = list_portProfile.index(profile) + 1
				port['port_profile_id'] = number
	for i in range(len(list_portProfile)):
		list_portProfile[i]['port_profile_id'] = i + 1
		list_portProfile[i]['port_profile_name'] = None

	# output device information to file
	with open(output_customer + '/capture-devices.json', 'w') as file:
		json.dump(capture_devices, file, indent=4)
	# output port settings to file
	with open(output_customer + '/port-settings.json', 'w') as file:
		json.dump(list_portSetting, file, indent=4)
	# output port profiles to file
	with open(output_customer + '/port-profiles.json', 'w') as file:
		json.dump(list_portProfile, file, indent=4)
"""