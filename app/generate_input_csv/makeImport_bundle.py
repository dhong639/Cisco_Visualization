# user defined python files
#		processInput
#			fill_header1	 append header1 with repeating values
#			pad_header1		append header1 with blank spaces
#			output_csv		write to csv file
#			is_none			check if value is '' or None
from .processInput import fill_header1
from .processInput import pad_header1
from .processInput import fill_header2
from .processInput import output_csv
from .processInput import is_none


# makeImport_bundle
#		input:
#			dict_device			list[dict]	list of dictionaries containing device information
#			list_portProfile	list[dict]	list of dictionaries containing profile info
#			list_portSetting	list[dict]	list of dictionaries containing setting info
#			maxPortCount		int			largest number of interfaces on one single device
#			version		 		string		version of vnc
#			link				string		link to vnc
#			date				string		current timestamp
#			fileOut				string		output location of csv file
#	 output:
#			None
#	 function:
#			create headers for output file
#				row 1 is for vnc versioning and indexing of row 2 columns
#				row 2 is for general device information followed by info per interface
#			fill in data columns
#			output results to csv file and place in given output location
def makeImport_bundle(dict_device, list_portProfile, list_portSetting, maxPortCount, path_out, version, date, link=None):
	if version == 'v':
		version = 'v0.2'
	# set vnc information
	listHeader1 = [
		'Bundles Import',
		'Version Number:',
		version,
		link,
		date
	]
	# set headers for device bundles information
	listHeader2 = [
		'NAME',
		'ENABLED',
		'PROTOCOL',
		'DEVICE SETTINGS',
		'DEVICE VOICE SETTINGS',
		'IS FOR SWITCH',
		'IS PUBLIC',
		'CLI COMMANDS'
	]
	# pad listHeader1 until it's the same length as listHeader2
	pad_header1(listHeader1, listHeader2)

	# start setting information for RG SERVICE
	fill_header1(listHeader1, 'RG SERVICE ', 2, 5)
	# listRG contents
	#		'RG SERVICE ENABLED'	whether or not service is on
	#		'RG SERVICE TYPE'		lan, rf_return, iptv, voip, or radius
	#		'RG SERVICE NAME'		name of service
	listRG = [
		'RG SERVICE ENABLED',
		'RG SERVICE TYPE',
		'RG SERVICE NAME'
	]
	fill_header2(listHeader2, listRG, 5)

	# start setting information for ports
	fill_header1(listHeader1, '', 2, maxPortCount)
	# listEth contents
	#		'ETH-PORT TYPE'				type, either eth, service, or crosslink
	#		'ETH-PORT NAME'				port name, usually "gigabit" or "fastethernet"
	#		'ETH-PORT SETTINGS NAME'	name of port setting'''
	listEth = [
		'ETH-PORT TYPE',
		'ETH-PORT NAME',
		'ETH-PORT SETTINGS NAME'
	]
	fill_header2(listHeader2, listEth, maxPortCount)

	# this section is not used
	fill_header1(listHeader1, 'USER SERVICE ', 2, 1)
	listUser = [
		'USER SERVICE ENABLED',
		'USER SERVICE NAME',
		'USER SERVICE CLI COMMANDS'
	]
	fill_header2(listHeader2, listUser, 1)

	# list of profile IDs, used for indexing to find names
	list_portProfileID = [profile['port_profile_id'] for profile in list_portProfile]
	# list of setting IDs, used for indexing to find names
	list_portSettingID = [setting['port_setting_id'] for setting in list_portSetting]

	# empty list of data
	data = []

	for device_id in dict_device:
		device = dict_device[device_id]
		# each row is filled with None value by default
		row = [None] * len(listHeader2)
		# set non-port dependent device information

		#	name
		#		concatenate device hostname and "_Bundle"
		indexName = listHeader2.index('NAME')
		row[indexName] = device['hostname'] + '_Bundle'
		#	enabled
		#		default 'TRUE'
		indexEnabled = listHeader2.index('ENABLED')
		row[indexEnabled] = 'TRUE'
		#	device settings
		#		default '(Default)'
		indexDeviceSettings = listHeader2.index('DEVICE SETTINGS')
		row[indexDeviceSettings] = '(Default)'
		#	is for switch
		#		default 'TRUE'
		indexIsForSwitch = listHeader2.index('IS FOR SWITCH')
		row[indexIsForSwitch] = 'TRUE'
		#	is public
		#		default 'FALSE'
		indexIsPublic = listHeader2.index('IS PUBLIC')
		row[indexIsPublic] = 'FALSE'

		# this section is all default values
		for i in range(5):
			header = 'RG SERVICE ' + str(i + 1)
			index = listHeader1.index(header)
			if i + 1 == 1:
				row[index] = 'FALSE'
				row[index + 1] = 'LAN'
			elif i + 1 == 2:
				row[index] = 'FALSE'
				row[index + 1] = 'rf_return'
			elif i + 1 == 3:
				row[index] = 'FALSE'
				row[index + 1] = 'IPTV'
			elif i + 1 == 4:
				row[index] = 'FALSE'
				row[index + 1] = 'VoIP'
			elif i + 1 == 5:
				row[index] = 'FALSE'
				row[index + 1] = 'radius'
		# set port dependent information
		listPort = device['ivn_port']
		for port_id in listPort:
			port = listPort[port_id]
			#	get port information from each row
			#		port	number	for each port found, increment by 1
			#		port	type		eth, service, or crosslink
			#		isLAG bool		check port is crosslink and has channel group
			portID = str(port['port_number'])
			index = listHeader1.index(portID)
			portType = None if 'port_type' not in port else port['port_type']
			isLAG = port['channel_group'] != None # and is_none(port['channel_group']) is False
			#	port type
			#		if port has channel group and is a cross link
			#			set equal to 'lagg_group'
			#	otherwise, set to value found in portType
			if isLAG:
				row[index] = 'lagg_group'
			else:
				if portType == None or portType == 'fabric':
					row[index] = None
				elif portType == 'eth_port':
					row[index] = 'eth_port'
				else:
					row[index] = 'service_port'
			#	port profile id
			#		if port has a channel group and is a corss link
			#			set equal to 'TOR Pair'
			#		if profile id exists
			#			find profile and set to given name
			if isLAG:
				if 'site_id' in device.keys():
					if 'port_type' in port and port['port_type'] == 'crosslink':
						site_id = device['site_id']
						if site_id != None:
							row[index + 1] = site_id.upper() + ' TOR Pair'
						else:
							row[index + 1] = 'unknown TOR Pair'
					else:
						channel_id = str(port['channel_group'])
						site_id = device['site_id']
						if site_id != None:
							row[index + 1] = site_id.upper() + ' port-channel' + channel_id
						else:
							row[index + 1] = 'unknown port-channel' + channel_id
				else:
					print('\tWarning: site ID not found (%s)' % device['hostname'])
					row[index + 1] = 'unknown TOR Pair'
			elif 'port_profile_id' in port.keys():
				profileID = port['port_profile_id']
				if is_none(profileID) is False:
					indexProfile = list_portProfileID.index(profileID)
					row[index + 1] = list_portProfile[indexProfile]['port_profile_name']
				else:
					print('\tWarning: profile ID missing (%s)' % device['hostname'])
			#	port setting id
			#		if setting id exists, find setting and set to given name
			if 'port_setting_id' in port.keys():
				settingID = port['port_setting_id']
				if is_none(settingID) is False:
					indexSetting = list_portSettingID.index(settingID)
					if list_portSetting[indexSetting]['poe_enabled'] == True:
						row[indexDeviceSettings] = 'PoE Device Default'
					row[index + 2] = list_portSetting[indexSetting]['port_setting_name']
				else:
					print('\tWarning: setting ID missing (%s)' % device['hostname'])
		# this section is all default values, unused
		index = listHeader1.index('USER SERVICE 1')
		row[index] = 'FALSE'
		# finish, append device information to data
		data.append(row)
	# output information to csv
	output_csv(listHeader1, listHeader2, data, path_out)
