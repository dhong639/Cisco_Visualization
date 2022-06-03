# user defined python files
# 		processInput
# 			pad_header1		append header1 with blank spaces
# 			output_csv		write to csv file
# 			is_none			check if value is '' or None
from .processInput import pad_header1
from .processInput import output_csv
from .processInput import is_none


# makeImport_controller
# 		input:
# 			dict_device		list[dict]          list of dictionaries containing device information
# 			dict_service	dict{int:string}    dictionary containing service/vlan information
# 			listSetting		list[dict]          list of dictionaries containing setting info
# 			version			string              version of vnc
# 			link			string              link to vnc
# 			date			string              current timestamp
# 			fileOut			string              output location of csv file
# 			sdlc			string              name of controller, used in controllers import
# 			ssh_username	string              ssh_username used to telnet/ssh to device
# 			password		string              password used to ssh to device
# 		output:
# 			None
# 		function:
# 			create headers for output file
# 				row 1 is for vnc versioning and indexing of row 2 columns
# 				row 2 is for general device information
# 			fill in data columns
# 			output results to csv file and place in given output location
def makeImport_controller(dict_device, dict_service, sdlc, enable, ssh_username, ssh_password, path_out, version, date, link=None):
	if version == 'v':
		version = 'v0.10'
	# set vnc information
	listHeader1 = [
		'Device Controller Import',
		'Version Number:',
		version,
		link,
		date
	]
	# set headers for device controllers information
	listHeader2 = [
		'NAME',
		'ENABLED',
		'SWITCH MODE',
		'SDLC HOSTNAME',
		'LOCATED BY',
		'LLDP CHASSIS ID',
		'LOCATION',
		'PORT NUMBER',
		'EXPECTED SITE',
		'USE NATIVE VLAN',
		'SERVICE',
		'CONTROLLER IP/MASK',
		'SWITCH IP',
		'SNMP TYPE',
		'READ ONLY MODE',
		'TARGET MODEL',
		'COMMUNITY STRING',
		'CLI ACCESS MODE',
		'USERNAME',
		'TELNET PASSWORD',
		'ENABLE PASSWORD',
		'SSH KEY',
		'SFP MAC OR SN',
		'CO-LOCATED VNFs',
		'GATEWAY',
		'IP SOURCE',
		'TAGGED DIRECT INTERFACE',
		'POWERED OFF'
	]
	# pad listHeader1 until it's the same length as listHeader2
	pad_header1(listHeader1, listHeader2)

	# empty list of data
	data = []

	for device_id in dict_device:
		device = dict_device[device_id]
		# each row is filled with None value by default
		row = [None] * len(listHeader2)
		# set information

		# 	name
		# 		default device hostname
		# 		add site and "DC_" if possible
		indexName = listHeader2.index('NAME')
		row[indexName] = device['hostname']
		if 'site_id' in device.keys():
			#row[indexName] = device['site_id'] + '_DC_' + row[indexName]
			row[indexName] = row[indexName] + '_DC' 
		else:
			print('\tWarning: site id not found (%s)' % device['hostname'])
		# 	enabled
		# 		default FALSE
		indexEnabled = listHeader2.index('ENABLED')
		row[indexEnabled] = 'TRUE'
		# 	switch mode
		# 		always switch
		indexSwitchMode = listHeader2.index('SWITCH MODE')
		row[indexSwitchMode] = 'switch'
		# 	sdlc hostname
		# 		provided by command line argument
		# 		default ""
		indexHostnameSDLC = listHeader2.index('SDLC HOSTNAME')
		row[indexHostnameSDLC] = sdlc
		# 	located by
		# 		default LLDP
		# 		if device has port channels, set to LAG
		# 		if device is a TOI, set to as_site
		indexLocatedBY = listHeader2.index('LOCATED BY')
		row[indexLocatedBY] = 'as_site' if device['is_tor'] == True else 'LLDP'
		#if len(device['port_channels']) > 0:
		# 	 row[indexLocatedBY] = 'LAG'
		#if 'is_tor' in device.keys():
		# 	 if str(device['is_tor']).upper() == 'TRUE':
		# 		 row[indexLocatedBY] = 'as_site'
		#if 'lldp_enabled' in device.keys():
		# 	 if str(device['lldp_enabled']).upper() == 'FALSE':
		# 		 row[indexLocatedBY] = 'Static Port'
		#else:
		# 	 print('\tDeivce (%s) has no lldp information' % device['hostname'])
		# 	lldp chassis id
		# 		set to chassis_id of device
		indexChassisID_LLDP = listHeader2.index('LLDP CHASSIS ID')
		row[indexChassisID_LLDP] = device['hostname']
		if device['domain_name'] != None:
			row[indexChassisID_LLDP] = device['hostname'] + '.' + device['domain_name']
		# 	expected site
		# 		set to site_id of device, found in hardware csv
		indexExpectedSite = listHeader2.index('EXPECTED SITE')
		if 'site_id' in device.keys():
			row[indexExpectedSite] = device['site_id']
		# 	use native vlan
		# 		default None
		# 		TRUE or FALSE if boolean provided
		indexUseNativeVLAN = listHeader2.index('USE NATIVE VLAN')
		mgmt_vlan_native = device['mgmt_vlan_native']
		row[indexUseNativeVLAN] = None if is_none(mgmt_vlan_native) else str(mgmt_vlan_native).upper()
		# 	service
		# 		default None
		# 		otherwise name of management VLAN
		indexService = listHeader2.index('SERVICE')
		mgmt_vlan = device['mgmt_vlan']
		if 'mgmt_vlan' in device.keys() and is_none(device['mgmt_vlan']) is False:
			site_id = device['site_id']
			#vlan_id = int(mgmt_vlan)
			if site_id in dict_service:
				if str(mgmt_vlan) in dict_service[site_id]:
					row[indexService] = dict_service[site_id][str(mgmt_vlan)]['name']
				else:
					print('\tWarning: %s vlan %s not in service import' % (site_id, mgmt_vlan))
			elif 'GLOBAL' in dict_service:
				if str(mgmt_vlan) in dict_service['GLOBAL']:
					row[indexService] = list(dict_service['GLOBAL'][str(mgmt_vlan)].keys())[0]
				else:
					print('\tWarning: %s vlan %s not in service import' % (site_id, mgmt_vlan))
			else:
				row[indexService] = str(mgmt_vlan) + ' - no site'
		# 	switch ip
		# 		ip address of device
		indexSwitchIP = listHeader2.index('SWITCH IP')
		row[indexSwitchIP] = device['ip_address']
		# 	snmp type
		# 		default snmp_v2
		indexTypeSNMP = listHeader2.index('SNMP TYPE')
		row[indexTypeSNMP] = 'snmp_v2'
		# 	read only mode
		# 		default to 'TRUE'
		indexReadOnlyMode = listHeader2.index('READ ONLY MODE')
		row[indexReadOnlyMode] = 'TRUE'
		# 	target model
		# 		default to 'generic_advanced_snmp'
		indexTargetModel = listHeader2.index('TARGET MODEL')
		row[indexTargetModel] = 'generic_advanced_snmp'
		# 	community string
		# 		set to community_string of device
		indexCommunityString = listHeader2.index('COMMUNITY STRING')
		if 'community_string' in device.keys():
			row[indexCommunityString] = device['community_string']
		# 	cli access mode
		# 		default to 'SSH'
		indexAccessModeCLI = listHeader2.index('CLI ACCESS MODE')
		row[indexAccessModeCLI] = 'SSH'
		# 	ssh_username
		# 		default ''
		# 		provided by command line argument
		indexUsername = listHeader2.index('USERNAME')
		row[indexUsername] = ssh_username
		#	enable
		#		default ''
		#		provided by command line argument
		indexEnable = listHeader2.index('ENABLE PASSWORD')
		row[indexEnable] = enable
		# 	ssh key
		# 		default ''
		# 		provided by command line argument
		indexKeySSH = listHeader2.index('SSH KEY')
		row[indexKeySSH] = ssh_password
		# 	co-located cnfs
		# 		default 'router'
		indexCoLcatedVNF = listHeader2.index('CO-LOCATED VNFs')
		row[indexCoLcatedVNF] = 'routed'
		# 	ip source
		# 		default 'dhcp'
		indexSourceIP = listHeader2.index('IP SOURCE')
		row[indexSourceIP] = 'dhcp'
		# 	tagged direct interface
		# 		default 'FALSE'
		indexTaggedDirectInterface = listHeader2.index('TAGGED DIRECT INTERFACE')
		row[indexTaggedDirectInterface] = 'FALSE'
		# 	powered off
		# 		default 'FALSE'
		indexPoweredOff = listHeader2.index('POWERED OFF')
		row[indexPoweredOff] = 'FALSE'
		# append row to list
		data.append(row)
	# output information to csv
	output_csv(listHeader1, listHeader2, data, path_out)
