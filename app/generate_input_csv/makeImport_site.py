#  user defined python files
#       processInput
#           pad_header1  append header1 with blank spaces
#           output_csv   write to csv file
from .processInput import pad_header1
from .processInput import output_csv
from .processInput import format_endpointName

# makeImport_ethPortSetting
#       input:
#           listDevice  list[dict]  list of dictionaries containing device information
#           version     string      version of vnc
#           link        string      link to vnc
#           date        string      current timestamp
#           fileOut     string      output location of csv file
#       output:
#                       None
#       function:
#           create headers for output file
#               row 1 is for vnc versioning and indexing of row 2 columns
#               row 2 is for general device information followed by info per interface
#           fill in data columns
#           output results to csv file and place in given output location
def makeImport_site(dict_device, dict_service, path_out, version, date, link=None):
	# set vnc information
	listHeader1 = [
		'Sites Import',
		'Version Number:',
		version,
		link,
		date
	]
	# set headers for device site information
	listHeader2 = [
		'NAME',
		'ENABLED',
		'SERVICE',
		'DOMAIN',
		'FABRIC SPANNING-TREE',
		'SYSTEM GRAPHS',
		'SPANNING TREE MODE',
	]
	pad_header1(listHeader1, listHeader2)
	# begin looking for TORs
	#		a tor is any device that has routing information in its "show run" output
	#		each time a TOR is found, append it to a list mapped to its respective site
	#		set maxLengthTOR to length of site with most TORs
	maxLengthTOR = 0
	dictSiteDevice = {}
	for device_id in dict_device:
		device = dict_device[device_id]
		if device['is_tor'] == True:
			if 'site_id' in device.keys():
				siteID = device['site_id']
				if siteID not in dictSiteDevice:
					dictSiteDevice[siteID] = []
				dictSiteDevice[siteID].append(device['hostname'])
				lengthTOR = len(dictSiteDevice[siteID])
				maxLengthTOR = lengthTOR if lengthTOR > maxLengthTOR else maxLengthTOR
			else:
				print('\tWarning: site ID not found (%s)' % device['hostname'])
	# add columns for each count in maxLength TOR
	for i in range(maxLengthTOR):
		listHeader1.append(str(i + 1))
		listHeader2.append('TOI ENDPOINT')
	# statically append following columns to headers; they are not used
	#listHeader1 = listHeader1 + ['', '', '', '', '']
	listHeader2 = listHeader2 + ['PAIRS NAME', 'PAIRS ENDPOINT 1', 'PAIRS ENDPOINT 2', 'PAIRS LAG', 'PAIRS IS WHITEBOX PAIR']
	pad_header1(listHeader1, listHeader2)

	# empty list of data
	data = []
	for siteID in dictSiteDevice:
		#print(dictSiteDevice[siteID])
		listTOR = [tor for tor in dictSiteDevice[siteID]]
		# begin getting list of TORs in each site
		lengthTOR = len(dictSiteDevice[siteID])
		# if length of list is smaller than maxLength
		#		for each missing position, add ''
		if lengthTOR < maxLengthTOR:
			for i in range(maxLengthTOR - lengthTOR):
				dictSiteDevice[siteID].append(None)
		# row composition:
		#		1st, assign siteID, followed by 6 default values
		#		2nd, append list of TORs in site (with padding of empty strings)
		#		3rd, append 4 empty strings (represents unused informatino for pairs)
		mgmt_vlan = dict_device[listTOR[0]]['mgmt_vlan']
		if mgmt_vlan != None:
			if siteID in dict_service:
				mgmt_vlan = dict_service[siteID][str(mgmt_vlan)]['name']
			elif 'global' in dict_service:
				mgmt_vlan = dict_service['global'][str(mgmt_vlan)]['name']
		else:
			mgmt_vlan = str(mgmt_vlan) + ' - no site'
		list_endpointName = []
		for device_id in dictSiteDevice[siteID]:
			if device_id in dict_device:
				list_endpointName.append(format_endpointName(dict_device[device_id]))
			else:
				list_endpointName.append(None)
		row = [siteID, 'TRUE', mgmt_vlan, '', 'FALSE', '', ''] + list_endpointName + ['', '', '', '', '']

		if len(listTOR) == 2:
			indexPairsName = listHeader2.index('PAIRS NAME')
			row[indexPairsName] = 'TOR Pair'
			# add pair endpoints
			#		if a site contains exactly 2 tors
			#		if tors are connected by LAG
			#			record name of each item in the pair
			#			set name to site name + 'TOR Pair'
			listTOR.sort()
			indexPairsEndpoint1 = listHeader2.index('PAIRS ENDPOINT 1')
			row[indexPairsEndpoint1] = listTOR[0]
			indexPairsEndpoint2 = listHeader2.index('PAIRS ENDPOINT 2')
			row[indexPairsEndpoint2] = listTOR[1]

			indexPairsLAG = listHeader2.index('PAIRS LAG')
			if siteID != None:
				row[indexPairsLAG] = siteID.upper() + ' TOR Pair'
			else:
				row[indexPairsLAG] = 'unknown TOR Pair'

			indexWhiteboxPairs = listHeader2.index('PAIRS IS WHITEBOX PAIR')
			row[indexWhiteboxPairs] = 'FALSE'
		data.append(row)
	# output information to csv
	output_csv(listHeader1, listHeader2, data, path_out)
