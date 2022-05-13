# user defined python files
#       processInput
#           get_count_maxService  maximum services in provisioning list
#           get_list_vlan         get vlans in provisioning
#           fill_header1         append header1 with repeating values
#           fill_header2         append header2 with repeating values
#           pad_header1          append header1 with blank spaces
#           output_csv           write to csv file
#           is_none              check if value is '' or None
from .processInput import get_count_maxService
from .processInput import get_list_vlan
from .processInput import fill_header1
from .processInput import fill_header2
from .processInput import pad_header1
from .processInput import output_csv
from .processInput import is_none


# makeImport_ethPortProfile
#       input:
#           list_portProfile     list[dict]          list of dictionaries containing profile info
#           dict_service     dict{int:string}    dictionary containing service/vlan information
#           maxPortCount    int                 largest number of interfaces on one single device
#           version         string              version of vnc
#           link            string              link to vnc
#           date            string              current timestamp
#           fileOut         string              output location of csv file
#     output:
#           None
#     function:
#           create headers for output file
#               row 1 is for vnc versioning and indexing of row 2 columns
#               row 2 is for general device information followed by info per interface
#           fill in data columns
#               output results to csv file and place in given output location
def makeImport_ethPortProfile(dict_service, list_portProfile, path_out, version, date, link=None):
	if version == 'v':
		version = 'v0.2'
	# set vnc information
	listHeader1 = [
		'Eth-Port Profiles Import',
		'Version Number:',
		version,
		link,
		date
	]
	# set headers for port profile information
	listHeader2 = [
		'NAME',
		'ENABLED',
		'IS TLS',
		'TLS SERVICE',
		'SORT BY NAME',
		'PORT IMPORTANCE'
	]
	# pad listHeader1 to same length as listHeader2
	pad_header1(listHeader1, listHeader2)

	# get maximum number of vlans in a profile
	maxServiceCount = get_count_maxService(list_portProfile, 'eth_port')

	# add five columns for each vlan in maxServiceCount
	fill_header1(listHeader1, 'SERVICE ', 4, maxServiceCount)
	# listService
	#       'SERVICE ENABLED'           whether or not vlan is used
	#       'SERVICE NAME'              name of vlan
	#       'SERVICE VLAN'              set to 'u' for first vlan in list
	#       'SERVICE ALC'               unused
	#       'SERVICE SPECIAL HANDLING'  unused
	listService = [
		'SERVICE ENABLED',
		'SERVICE NAME',
		'SERVICE VLAN',
		'SERVICE ALC',
		'SERVICE SPECIAL HANDLING'
	]
	fill_header2(listHeader2, listService, maxServiceCount)

	# empty list of data
	data = []

	for profile in list_portProfile:
		# get profile dependent information
		#       get list of vlans in the profile
		#       ignore everything that's not an eth port
		if profile['port_type'] == 'eth_port':
			# each row is filled with None value by default
			row = [None] * len(listHeader2)
			# get list of valid vlans
			listVLAN = get_list_vlan(profile)
			#   name
			#       set to name of profile
			indexName = listHeader2.index('NAME')
			row[indexName] = profile['port_profile_name']
			#   enabled
			#       'FALSE' if no ports use profile
			#       'TRUE' if at least one port uses profile
			indexEnabled = listHeader2.index('ENABLED')
			if 'port_count' in profile.keys():
				portCount = profile['port_count']
				row[indexEnabled] = 'FALSE' if is_none(portCount) or portCount == 0 else 'TRUE'
			else:
				print('\tWarning: port counts are missing from profiles')
			#   sort by name
			#       default 'FALSE'
			indexSort = listHeader2.index('SORT BY NAME')
			row[indexSort] = 'FALSE'

			# begin setting vlan information
			site_id = profile['site_id']
			for j in range(len(listVLAN)):
				# label is used for indexing header2
				# vlanID from services-import.csv is a string
				label = 'SERVICE ' + str(j + 1)
				vlanID = str(listVLAN[j])
				# check that vlan exists
				is_site = site_id in dict_service and vlanID in dict_service[site_id]
				is_global = 'global' in dict_service and vlanID in dict_service['global']
				# only set vlan info if vlan exists
				if site_id in dict_service or 'global' in dict_service:
					if is_site or is_global:
						if is_site:
							name = list(dict_service[site_id][vlanID].keys())[0]
						else:
							name = list(dict_service['global'][vlanID].keys())[0]
						index = listHeader1.index(label)
						#   service enabled
						#       True as long as vlan is provided
						row[index] = True
						#   service name
						#       get name of vlan
						row[index + 1] = name
						#   service vlan
						#       if native vlan, set untagged traffic
						#if str(profile['native_vlan']) == str(vlanID):
						#    row[index + 2] = 'u'
						#       default always set first vlan to untagged
						row[index + 2] = 'u' if j == 0 else None
					else:
						print('\tWarning: %s vlan %s not in service import' % (site_id, vlanID))
				else:
					print('\tWarning: vlan %s has no site' % str(vlanID))
					name = str(vlanID) + ' - no site'
					index = listHeader1.index(label)
					#   service enabled
					#       True as long as vlan is provided
					row[index] = True
					#   service name
					#       get name of vlan
					row[index + 1] = name
					#   service vlan
					#       if native vlan, set untagged traffic
					#if str(profile['native_vlan']) == str(vlanID):
					#    row[index + 2] = 'u'
					#       default always set first vlan to untagged
					row[index + 2] = 'u' if j == 0 else None
			data.append(row)
	# output information to csv
	output_csv(listHeader1, listHeader2, data, path_out)
