# user defined python files
#     processInput
#         pad_header1               append header1 with blank spaces
#         output_csv                write to csv file
from .processInput import pad_header1
from .processInput import output_csv


# makeImport_lag
#       input:
#           dict_device      list[dict]  list of dictionaries containing device information
#           list_portProfile     list[dict]  list of dictionaries containing profile info
#           version         string      version of vnc
#           link            string      link to vnc
#           date            string      current timestamp
#           fileOut         string      output location of csv file
#       output:
#                           None
#       function:
#           create headers for output file
#               row 1 is for vnc versioning and indexing of row 2 columns
#               row 2 is for general device information followed by info per interface
#           fill in data columns
#               output results to csv file and place in given output location
def makeImport_lag(dict_device, list_portProfile, path_out, version, date, link=None):
	if version == 'v':
		version = 'v0.2'
	# define headers
	listHeader1 = ['LAGs Import', 'Version Number:', version, link, date]
	listHeader2 = ['NAME', 'ENABLED', 'IS FABRIC', 'IS PEER LINK', 'PEER LINK VLAN', 'ETH-PORT PROFILE', 'ETH-PORT TYPE', 'SITE', 'CONNECTOR COLOR', 'LACP ON']
	pad_header1(listHeader1, listHeader2)

	dictSite2Device = {}
	for device_id in dict_device:
		device = dict_device[device_id]
		site = device['site_id']
		if site not in dictSite2Device:
			dictSite2Device[site] = {}
		for port_id in device['ivn_port']:
			port = device['ivn_port'][port_id]
			channelGroup = port['channel_group']
			if channelGroup != None:
				profileID = None if 'port_profile_id' not in port else port['port_profile_id']
				portType = None if 'port_type' not in port else port['port_type']
				dictSite2Device[site][channelGroup] = {
					'port_profile_id': profileID,
					'port_type': portType,
				}
	
	data = []
	for site in dictSite2Device:
		for channelGroup in dictSite2Device[site]:
			# each row is filled with None value by default
			row = [None] * len(listHeader2)
			#   enabled
			#       default 'TRUE'
			indexEnabled = listHeader2.index('ENABLED')
			row[indexEnabled] = 'TRUE'
			#   is fabric
			#       default 'FALSE'
			indexIsFabric = listHeader2.index('IS FABRIC')
			row[indexIsFabric] = 'FALSE'
			#   is peer link
			#       default 'FALSE
			indexIsPEERLINK = listHeader2.index('IS PEER LINK')
			row[indexIsPEERLINK] = 'FALSE'
			#   site
			#       set to name of site
			indexSite = listHeader2.index('SITE')
			row[indexSite] = site
			#   connector color
			#       default 'anakiwa'
			#       for reference, this color is similar to cyan (blue)
			indexConnectorColor = listHeader2.index('CONNECTOR COLOR')
			row[indexConnectorColor] = 'anakiwa'
			#   lacp on
			#       default 'TRUE'
			indexLACP = listHeader2.index('LACP ON')
			row[indexLACP] = 'TRUE'
			#   eth port type
			#       if None, stay None
			#       if 'eth_port', stay 'eth_port'
			#       if 'crosslink', 'layer3', 'service_up', or 'service_down', record 'service_port'
			indexPortType = listHeader2.index('ETH-PORT TYPE')
			portType = dictSite2Device[site][channelGroup]['port_type']
			if portType == None:
				row[indexPortType] = None
			elif portType == 'eth_port':
				row[indexPortType] = 'eth_port'
			else:
				row[indexPortType] = 'service_port'
			#   eth port profile
			#       get name of profile if port profile id is not None
			indexProfileName = listHeader2.index('ETH-PORT PROFILE')
			profileID = dictSite2Device[site][channelGroup]['port_profile_id']
			if profileID == None:
				row[indexProfileName] = None
			else:
				for profile in list_portProfile:
					if profile['port_profile_id'] == profileID:
						row[indexProfileName] = profile['port_profile_name']
					if profile['port_type'] == 'crosslink':
						row[indexIsPEERLINK] = 'TRUE'
						row[indexIsFabric] = 'TRUE'
			#   name
			#       if port type is a crosslink, record as '<site_id> TOR PAIR'
			#       otherwise, record as '<site_id> port-channel<channel_number>'
			indexName = listHeader2.index('NAME')
			if site != None:
				name = site.upper() + ' port-channel' + str(channelGroup)
			else:
				name = 'unknown port-channel' + str(channelGroup)
			if portType == 'crosslink':
				if site != None:
					name = site.upper() + ' TOR Pair'
				else:
					name = 'unknown TOR Pair'
			row[indexName] = name
			data.append(row)
	# output information to csv
	output_csv(listHeader1, listHeader2, data, path_out)
