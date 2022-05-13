import csv


# format_provisioning
#		input:
#			provisioning		string	content from provisioning json file
#			listDevice			list	list of dictionaries containing device information
#			dictService			dict	mapping of service numbers to service names
#			default				string	default value for generating names
#		output:
#			listProvisioning	list	list of dictionaries containing provisioning info
#		function:
#			provisioning input contains information for profiles and settings
#			both are stored as a list of column names and several lists of data
#			transform input to dictionary of column names to list of data
#			works for both profiles and settings
def format_provisioning(list_provisioning, dict_device, dict_service, default=''):
	for provisioning in list_provisioning:
		set_provisioningName(provisioning, dict_service, default)
		set_portCount(provisioning, dict_device)


# get_id_provisioning
#		input:
#			provisioning	dictionary	list of dictionaries containing provisioning info
#		output:
#			idKey			int			key value of provisioning
#		function:
#			return value under "port_profile_id" or "port_setting_id"
def get_id_provisioning(provisioning):
	listKeys = [key for key in provisioning.keys()]
	idKey = None
	for key in listKeys:
		if 'port' in key and 'id' in key:
			idKey = key
			break
	return idKey


# set_portCount
#		input:
#			provisioning	dictionary	list of dictionaries containing provisioning info
#			listDevice		dictionary	list of dictionaries containing device information
#		output:
#			none
#		function:
#			count number of interfaces on all devices containing given provisioning id
#			append number to provisioning dictionary
def set_portCount(provisioning, dict_device):
	provisioning['port_count'] = 0
	idKey = get_id_provisioning(provisioning)
	idValue = provisioning[idKey]
	for device_id in dict_device:
		for port_id in dict_device[device_id]['ivn_port']:
			port = dict_device[device_id]['ivn_port'][port_id]
			if idKey in port:
				if port[idKey] == idValue:
					provisioning['port_count'] += 1


# set_provisioningName
#		input:
#			provisioning	dictionary	list of dictionaries containing provisioning info
#			dictService		dictionary	mapping of service numbers to service names
#			default			string		default value for generating names
#		output:
#			none
#		function:
#			set name for provisioning unit
#				by default, name each profile with concatenation of "PortProfile" and id
#				by default, name each setting with concatenation of "SettingsNAME" and id
#				if only one vlan is present, append name of vlan to name
def set_provisioningName(provisioning, dictService, default):
	idKey = get_id_provisioning(provisioning)
	name = ''
	if 'profile' in idKey:
		site = provisioning['site_id']
		name = 'port_profile_name'
		if name not in provisioning.keys() or is_none(provisioning[name]):
			provisioning[name] = default + 'PortProfile' + str(provisioning[idKey])
			if provisioning['port_type'] != 'eth_port':
				provisioning[name] = provisioning[name] + ' - ' + provisioning['port_type']
			listVLAN = get_list_vlan(provisioning)
			print(listVLAN)
			if len(listVLAN) == 1:
				print('\tthis applies')
				if site in dictService:
					vlan_id = str(listVLAN[0])
					if vlan_id in dictService[site]:
						provisioning[name] += ' - '
						provisioning[name] += list(dictService[site][vlan_id].keys())[0]
			print('\t' + provisioning[name])
		else:
			print('\tNaming: Profile %d name exists, skip default name' % provisioning[idKey])
	elif 'setting' in idKey:
		name = 'port_setting_name'
		if name not in provisioning or is_none(provisioning[name]):
			provisioning[name] = default + 'SettingsNAME' + str(provisioning[idKey])
			listVLAN = get_list_vlan(provisioning)
			if len(listVLAN) == 1:
				site = listVLAN[0][0]
				if site in dictService:
					vlan_id = str(listVLAN[0][1])
					provisioning[name] += ' - '
					provisioning[name] += list(dictService[site][vlan_id].keys())[0]
		else:
			print('\tNaming: Setting %d name exists, skip default name' % provisioning[idKey])


# get_count_maxPort
#		input:
#			listDevice		dictionary	list of dictionaries containing device information
#		output:
#			maxPortCount	int			largest number of interfaces on one single device
#		function:
#			find and return largest number of interfaces on a single device
def get_count_maxPort(dict_device):
	maxPortCount = 0
	for device_id in dict_device:
		portCount = len(dict_device[device_id]['ivn_port'])
		maxPortCount = portCount if portCount > maxPortCount else maxPortCount
	return maxPortCount


# get_count_maxService
#		input:
#			listProfile		list[dict]	list of dictionaries containing profile information
#			type			string		either 'service' or 'eth'
#		output:
#			maxService		int			largest number of vlans in list of profiles
#		function:
#			count number of services (VLANs) available on port profile
def get_count_maxService(listProfile, portType):
	maxServiceCount = 0
	for profile in listProfile:
		if profile['port_type'] == portType:
			serviceCount = len(get_list_vlan(profile))
			if serviceCount > maxServiceCount:
				maxServiceCount = serviceCount
	return maxServiceCount


# get_list_vlan
#		input:
#			provisioning	dictionary	list of dictionaries containing provisioning info
#		output:
#			listVLAN		list		list of vlan numbers (int)
#		function:
#			find and return all vlans in a single provisioning
#			vlans listed in order they are found
def get_list_vlan(provisioning):
	listVLAN = []
	if 'native_vlan' in provisioning.keys():
		nativeVLAN = provisioning['native_vlan']
		if nativeVLAN is not None:
			listVLAN.append(nativeVLAN)
	if 'voice_vlan' in provisioning.keys():
		voiceVLAN = provisioning['voice_vlan']
		if voiceVLAN is not None:
			listVLAN.append(voiceVLAN)
	if 'trunk_list' in provisioning.keys():
		listTrunk = provisioning['trunk_list']
		if listTrunk is not None:
			listVLAN = listVLAN + listTrunk
	if 'list_existing' in provisioning.keys():
		list_existing = provisioning['list_existing']
		if list_existing:
			listVLAN = listVLAN + list_existing
	return listVLAN


# is_none
#		input:
#			data		any			value
#		output:
#						boolean		whether or not the data is empty
#		function:
#			determine if data is equal to empty string or None type
def is_none(data):
	return data == '' or data is None


# make_dict_service
#		input:
#			df_service	dataframe		csv input containing service/vlan information
#		output:
#			dictService dictionary		dictionary containing service/vlan information
#		function:
#			read csv and store as dictionary with vlan number as key and name as value
def make_dict_service(file_servicesInput):
	dictService = {}

	reader = csv.DictReader(file_servicesInput)
	for row in reader:
		row = {key.lower().replace(' ', '_'): row[key] for key in row}
		site_id = 'global'
		if 'site_id' in row:
			site_id = row['site_id'].strip()#.replace('\u00a0', '')
		if site_id not in dictService:
			dictService[site_id] = {}
		vlan = int(row['vlan'])
		name = row['name'].strip().replace('/', '-')
		name = str(vlan) + ' - ' + site_id + ' - ' + name
		dictService[site_id][vlan] = name

	return dictService


def make_dict_management(file_servicesInput, dict_devices):
	reader = csv.DictReader(file_servicesInput)
	dictManagement = {}
	# if management vlans are not specified, return None and figure it out later
	if 'management' not in [field.lower().replace(' ', '_') for field in reader.fieldnames]:
		for device_id in dict_devices:
			site_id = dict_devices[device_id]['site_id']
			if 'site_id' not in [field.lower().replace(' ', '_') for field in reader.fieldnames]:
				site_id = 'global'
			if site_id not in dictManagement:
				dictManagement[site_id] = set()
			mgmt_vlan = dict_devices[device_id]['mgmt_vlan']
			if mgmt_vlan != None:
				dictManagement[site_id].add(int(mgmt_vlan))
	# otherwise, continue as normal
	# there is an assumption that user entered management VLANs correctly
	# management VLANs will still be drawn from capture-devices where applicable
	else:
		for row in reader:
			row = {key.lower().replace(' ', '_'): row[key] for key in row}
			site_id = row['site_id'].strip()#.replace('\u00a0', '')
			if site_id not in dictManagement:
				dictManagement[site_id] = set()
			if str(row['management']).capitalize() == 'True':
				dictManagement[site_id].add(int(row['vlan']))
	
	return dictManagement


# fill_header1
#		input:
#			listHeader1 list		list of values in header 1
#			column		string		value to be added to header 1
#			padding	 int			how much padding follows the provided column
#			count		int			number of repetitions
#		output:
#						none
#		function:
#			add values to header 1 that must be generated dynamically (such as new columns per port)
def fill_header1(listHeader1, column, padding, count):
	for i in range(count):
		listHeader1.append(column + str(i + 1))
		for j in range(padding):
			listHeader1.append('')
	#print(listHeader1)


# fill_header2
#		input:
#			listHeader2 list		list of values in header 2
#			listColumn	list		list of values to be added to header 2
#			count		int		 number of repetitions
#		output:
#						none
#		function:
#		 add values to header 2 that must be generated dynamically (such as new columns per port)
def fill_header2(listHeader2, listColumn, count):
	length = len(listColumn)
	for i in range(count):
		for j in range(length):
			listHeader2.append(listColumn[j])


# pad_header1
#		input:
#			listHeader1 list		list of values in header 1
#			listHeader2 list		list of values in header 2
#		output:
#						none
#		function:
#			add '' to listHeader1 until listHeader1 is the same length as listHeader2
def pad_header1(listHeader1, listHeader2):
	for i in range(len(listHeader2) - len(listHeader1)):
		listHeader1.append('')


# output_csv
#		input:
#			listHeader1 list		list of values in header 1
#			listHeader2 list		list of values in header 2
#			data		list[list]	values in dataframe
#			fileName	string		name of output file
#		output:
#			none
#		function:
#			write processed values to csv
def output_csv(listHeader1, listHeader2, data, fileName):
	with open(fileName, 'w') as csvFile:
		csvWriter = csv.writer(csvFile)
		csvWriter.writerow(listHeader1)
		csvWriter.writerow(listHeader2)
		for row in data:
			csvWriter.writerow(row)


# format_endpointName
#		input:
#			device	object			object representing switch device
#		output:
#			name	string			name of device endpoint
#		function:
#			create name for device endpoint
#				by default, it's just the hostname
#				if device location is present, append location string to name
#				otherwise, if site is present, append name to site id
def format_endpointName(device):
	name = str(device['hostname'])
	if 'location' in device.keys() and device['location'] != '':
		name = name + ' - ' + str(device['location'].replace('/', '-'))
	elif 'site_id' in device.keys():
		name = str(device['site_id']) + '_EP_' + name
	else:
		print('\tWarning: location and site were not detected (%s)' % device['hostname'])
	return name
