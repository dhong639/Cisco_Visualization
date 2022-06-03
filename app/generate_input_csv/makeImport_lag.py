# user defined python files
#	 processInput
# 			pad_header1			append header1 with blank spaces
# 			output_csv			write to csv file
from .processInput import pad_header1
from .processInput import output_csv
from .processInput import get_nameLAG


# makeImport_lag
# 		input:
# 			dict_device			list[dict]	list of dictionaries containing device information
# 			list_portProfile	list[dict]	list of dictionaries containing profile info
# 			version 			string		version of vnc
# 			link 			 	string		link to vnc
# 			date 			 	string		current timestamp
# 			fileOut 			string		output location of csv file
# 		output:
# 		 		 				None
# 		function:
# 			create headers for output file
# 		 		 row 1 is for vnc versioning and indexing of row 2 columns
# 		 		 row 2 is for general device information followed by info per interface
# 			fill in data columns
# 		 		 output results to csv file and place in given output location
def makeImport_lag(dict_device, list_portProfile, dict_edgesFabric, path_out, version, date, link=None):
	if version == 'v':
		version = 'v0.2'
	# define headers
	listHeader1 = ['LAGs Import', 'Version Number:', version, link, date]
	listHeader2 = ['NAME', 'ENABLED', 'IS FABRIC', 'IS PEER LINK', 'PEER LINK VLAN', 'ETH-PORT PROFILE', 'ETH-PORT TYPE', 'SITE', 'CONNECTOR COLOR', 'LACP ON']
	pad_header1(listHeader1, listHeader2)

	dict_torPair = {}
	for device_id in dict_device:
		source = dict_device[device_id]
		if source['is_tor'] == True:
			for target_id in dict_edgesFabric[device_id]:
				if target_id in dict_device:
					target = dict_device[target_id]
					if target['is_tor'] == True and source['site_id'] == target['site_id']:
						list_intfPair = dict_edgesFabric[device_id][target_id]['pairs']
						for pair in list_intfPair:
							source_intf = source['ivn_port'][pair[0]]
							target_intf = target['ivn_port'][pair[1]]
							if source_intf['channel_group'] == target_intf['channel_group']:
								channel_group = source_intf['channel_group']
								if channel_group not in dict_torPair:
									dict_torPair[channel_group] = {}
								site_id = source['site_id']
								if site_id not in dict_torPair[channel_group]:
									dict_torPair[channel_group][site_id] = set()
								dict_torPair[channel_group][site_id].add(device_id)
								dict_torPair[channel_group][site_id].add(target_id)

	data = []
	set_nameLAG = set()
	for device_id in dict_device:
		site_id = dict_device[device_id]['site_id']
		for port_id in dict_device[device_id]['ivn_port']:
			port = dict_device[device_id]['ivn_port'][port_id]
			channel_group = port['channel_group']
			if channel_group:
				# determine name of channel group
				# lags between tor pairs are considered "TOR Pairs"
				# all other lags are named according to originating device
				# there are no duplicates
				name_lag = get_nameLAG(site_id, device_id, channel_group, False)
				is_peerLink = False
				is_fabric = False
				if channel_group in dict_torPair and site_id in dict_torPair[channel_group]:
					if device_id in dict_torPair[channel_group][site_id]:
						name_lag = get_nameLAG(site_id, device_id, channel_group, True)
						is_peerLink = True
						is_fabric = True
				port_type = None
				port_profile_name = None
				if 'port_type' in port:
					port_type = port['port_type']
					if port_type != 'crosslink':
						if 'port_profile_id' in port:
							for profile in list_portProfile:
								if profile['port_profile_id'] == port['port_profile_id']:
									port_profile_name = profile['port_profile_name']
				if name_lag not in set_nameLAG:
					# each row is filled with None value by default
					row = [None] * len(listHeader2)
					# 	enabled
					# 		default 'TRUE'
					indexEnabled = listHeader2.index('ENABLED')
					row[indexEnabled] = 'TRUE'
					# 	is fabric
					# 		default 'FALSE'
					# 		set to True for if lag is for a tor pair
					indexIsFabric = listHeader2.index('IS FABRIC')
					row[indexIsFabric] = is_fabric
					# 	is peer link
					# 		default 'FALSE
					# 		set to True for if lag is for a tor pair
					indexIsPEERLINK = listHeader2.index('IS PEER LINK')
					row[indexIsPEERLINK] = is_peerLink
					# 	site
					# 		set to name of site
					indexSite = listHeader2.index('SITE')
					row[indexSite] = site_id
					# 	connector color
					# 		default 'anakiwa'
					# 		for reference, this color is similar to cyan (blue)
					indexConnectorColor = listHeader2.index('CONNECTOR COLOR')
					row[indexConnectorColor] = 'anakiwa'
					# 	lacp on
					# 		default 'TRUE'
					indexLACP = listHeader2.index('LACP ON')
					row[indexLACP] = 'TRUE'
					# 	eth port type
					# 		if None, stay None
					# 		if 'eth_port', stay 'eth_port'
					# 		if 'crosslink', 'layer3', 'service_up', or 'service_down', 
					# 			record 'service_port'
					indexPortType = listHeader2.index('ETH-PORT TYPE')
					if port_type == None:
						row[indexPortType] = None
					elif port_type == 'eth_port':
						row[indexPortType] = 'eth_port'
					else:
						row[indexPortType] = 'service_port'
					# 	eth port profile
					# 		get name of profile if port profile id is not None
					# 		ignore if lag is for tor pairs
					indexProfileName = listHeader2.index('ETH-PORT PROFILE')
					if port_profile_name != None and port_type != 'crosslink':
						row[indexProfileName] = port_profile_name
					# 	name
					# 		if port type is a crosslink, record as '<site_id> TOR PAIR'
					# 		otherwise, record as '<site_id> port-channel<channel_number>'
					indexName = listHeader2.index('NAME')
					row[indexName] = name_lag
					# finalize
					data.append(row)
					set_nameLAG.add(name_lag)

	# output information to csv
	output_csv(listHeader1, listHeader2, data, path_out)
