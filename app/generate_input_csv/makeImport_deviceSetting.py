# WARNING: expected parents cannot be calculated at the moment

# user defined python files
#       processInput
#           fill_header1     append header1 with repeating values
#           fill_header2     append header2 with repeating values
#           pad_header1      append header1 with blank spaces
#           output_csv       write to csv file
#           is_none          check if value is '' or None
from .processInput import format_endpointName
from .processInput import fill_header1
from .processInput import fill_header2
from .processInput import pad_header1
from .processInput import output_csv


# makeImport_endpoint
#       input:
#           dict_device      list[dict]  list of dictionaries containing device information
#           maxPortCount    int         largest number of interfaces on one single device
#           version         string      version of vnc
#           link            string      link to vnc
#           date            string      current timestamp
#           fileOut         string      output location of csv file
#     output:
#                           None
#     function:
#           create headers for output file
#               row 1 is for vnc versioning and indexing of row 2 columns
#               row 2 is for general device information followed by info per interface
#           fill in data columns
#               output results to csv file and place in given output location
def makeImport_endpoint(dict_device, maxPortCount, path_out, version, date, link=None):
	if version == 'v':
		version = 'v0.2'
	# set vnc information
	listHeader1 = [
		'Switch Endpoints Import',
		'Version Number:',
		version,
		link,
		date
	]
	# set headers for device endpoints information
	listHeader2 = [
		'ENDPOINT',
		'ENABLED',
		'DEVICE',
		'BUNDLE',
		'BADGES',
		'EXPECTED PARENT',
		'EXPECTED SITE',
		'READ ONLY MODE',
		'DISABLED PORTS',
		'DRAW AS EDGE',
		'AGGREGATE SWITCHES',
		'MULTIPORT PORT COUNT',
		'ETH COUNT',
	]
	pad_header1(listHeader1, listHeader2)
	listHeader1 = listHeader1 + [
		"CHILD 1"
	]
	listHeader2 = listHeader2 + [
		'CHILD ENDPOINT',
		'CHILD DEVICE SN'
	]
	pad_header1(listHeader1, listHeader2)

	# start setting information for ETH PORTs
	#fill_header1(listHeader1, 'ETH', 2, maxPortCount)
	fill_header1(listHeader1, 'ETH', 1, maxPortCount)
	#   listEth
	#       'ETH ENABLED'   whether or not port is present, on, or off
	#       'ETH LABEL'     given port description
	#       'ETH ICON'      port picture
	#listEth = ['ETH ENABLED', 'ETH LABEL', 'ETH ICON']
	listEth = ['ETH LABEL', 'ETH ICON']
	fill_header2(listHeader2, listEth, maxPortCount)

	# empty list of data
	data = []

	for device_id in dict_device:
		device = dict_device[device_id]
		# each row is filled with None value by default
		row = [None] * len(listHeader2)
		# set non-port dependent device information

		#   endpoint
		#       set to hostname
		#       append location if found
		#       otherwise, use convention site + '_EP_' + hostname
		indexEndpoint = listHeader2.index('ENDPOINT')
		row[indexEndpoint] = format_endpointName(device)
		#   enabled
		#       default 'TRUE'
		indexEnabled = listHeader2.index('ENABLED')
		row[indexEnabled] = 'TRUE'
		#   device id
		#       set to chassis_id of device
		indexDeviceID = listHeader2.index('DEVICE')
		row[indexDeviceID] = device['hostname']
		if device['domain_name'] != None:
			row[indexDeviceID] = device['hostname'] + '.' + device['domain_name']
		#   bundle
		#       set to concatenation of hostname and 'Bundle'
		indexBundle = listHeader2.index('BUNDLE')
		row[indexBundle] = device['hostname'] + '_' + 'Bundle'
		#   expected site
		#       set to site_id of device
		indexExpectedID = listHeader2.index('EXPECTED SITE')
		if 'site_id' in device.keys():
			row[indexExpectedID] = device['site_id']
		else:
			print('\tWarning: site not found (%s)' % device['hostname'])
		#   expected parent
		#       set to value of "expected_parent_id"
		indexExpectedParent = listHeader2.index('EXPECTED PARENT')
		expected_parent_id = device['expected_parent_id']
		if expected_parent_id != None:
			for parent_id in dict_device:
				if expected_parent_id == parent_id:
					row[indexExpectedParent] = format_endpointName(dict_device[parent_id])
		#   read only mode
		#       set to 'FALSE'
		indexReadOnlyMode = listHeader2.index('READ ONLY MODE')
		row[indexReadOnlyMode] = 'FALSE'
		#   disabled ports
		#       list of all disabled ports separated by '|' delimiter
		indexDisabledPorts = listHeader2.index('DISABLED PORTS')
		list_disabledPorts = []
		for port_id in device['ivn_port']:
			port = device['ivn_port'][port_id]
			if port['enabled'] == False:
				list_disabledPorts.append(port['port_number'])
		list_disabledPorts = ['0.' + str(item) for item in list_disabledPorts]
		row[indexDisabledPorts] = '|'.join(list_disabledPorts) if list_disabledPorts != [] else None
		#   draw as edge
		#       default 'FALSE'
		indexDrawAsEdge = listHeader2.index('DRAW AS EDGE')
		row[indexDrawAsEdge] = 'FALSE'
		#   aggregate switches
		#       default 'FALSE'
		indexAggregateSwitches = listHeader2.index('AGGREGATE SWITCHES')
		row[indexAggregateSwitches] = 'FALSE'
		#   multiport port count
		#       default to '0'
		indexMultiportPortCount = listHeader2.index('MULTIPORT PORT COUNT')
		row[indexMultiportPortCount] = '0'
		#   eth count
		#       set to number of ports on device
		indexEthCount = listHeader2.index('ETH COUNT')
		row[indexEthCount] = len(device['ivn_port'])

		# set port dependent information
		dict_port = device['ivn_port']
		for port_id in dict_port:
			port = dict_port[port_id]
			#   set information on per-port basis
			#       get port number
			#       get column name
			#       get index of column name
			portID = port['port_number']
			header = 'ETH' + str(portID)
			index = listHeader1.index(header)
			#   if port is not present, leave all three fields blank
			#   if port is on or off
			#       set 'ETH LABEL' to description of port
			#       set 'ETH ICON' to laptop
			#       set 'ETH ENABLE' to uppercase string value of boolean for port enabled status
			#row[index] = None if is_none(port['enabled']) else str(port['enabled']).upper()
			#row[index + 1] = port['description']
			#row[index + 2] = 'laptop'
			row[index] = port['description']
			row[index + 1] = 'laptop'
		data.append(row)
	# output information to csv
	output_csv(listHeader1, listHeader2, data, path_out)
