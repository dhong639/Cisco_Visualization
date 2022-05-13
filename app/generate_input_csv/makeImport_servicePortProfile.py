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
import json

# makeImport_servicePortProfile
#       input:
#           listProfile     list[dict]          list of dictionaries containing profile info
#           dictService     dict{int:string}    dictionary containing service/vlan information
#           maxPortCount    int                 largest number of interfaces on one single device
#           version         string              version of vnc
#           link            string              link to vnc
#           date            string              current timestamp
#           fileOut         string              output location of csv file
#     output:
#                           None
#     function:
#           create headers for output file
#               row 1 is for vnc versioning and indexing of row 2 columns
#               row 2 is for general device information followed by info per interface
#           fill in data columns
#           output results to csv file and place in given output location
#def makeImport_servicePortProfile(listProfile, dictService, version, link, date, fileOut):
def makeImport_servicePortProfile(dict_service, list_portProfile, path_out, version, date, default='', link=None):
	if version == 'v':
		version = 'v0.2'
	# set vnc information
	listHeader1 = [
		'Service Ports Import',
		'Version Number:',
		version,
		link,
		date
	]
	listHeader2 = [
		'NAME',
		'ENABLED',
		'PORT IMPORTANCE',
		'SERVICE DIRECTION',
		'IS TLS',
		'TLS SERVICE',
		'TLS SERVICE IN'
	]
	pad_header1(listHeader1, listHeader2)
	# get maximum number of vlans per profile
	#import json
	#print(json.dumps(listProfile, indent=4))
	maxServiceCount_service_up = get_count_maxService(list_portProfile, 'service_up')
	maxServiceCount_service_down = get_count_maxService(list_portProfile, 'service_down')
	maxServiceCount_service = max(maxServiceCount_service_up, maxServiceCount_service_down)
	maxServiceCount_crosslink = get_count_maxService(list_portProfile, 'crosslink')
	maxServiceCount = max(maxServiceCount_service, maxServiceCount_crosslink)
	# add service information
	#print('max service count is ' + str(maxServiceCount))
	fill_header1(listHeader1, 'SERVICE ', 4, maxServiceCount)
	#print(listHeader1)
	listService = [
		'SERVICE ENABLED',
		'SERVICE NAME',
		'SERVICE VLAN',
		'SERVICE LIMIT IN',
		'SERVICE LIMIT OUT'
	]
	fill_header2(listHeader2, listService, maxServiceCount)

	data = []

	for profile in list_portProfile:
		portType = profile['port_type']
		if 'service' in portType or portType == 'crosslink' or portType == 'layer3':
			# each row is filled with None value by default
			row = [None] * len(listHeader2)
			# get number of vlans in each profile
			listVLAN = get_list_vlan(profile)

			# begin setting vlan independent information
			#   name
			#       set as profile name
			indexName = listHeader2.index('NAME')
			row[indexName] = profile['port_profile_name']
			"""if portType != None:
				row[indexName] = row[indexName] + ' - ' + portType"""
			#   enabled
			#       'FALSE' if no ports use profile
			#       'TRUE' if at least one port uses profile
			indexPortCount = listHeader2.index('ENABLED')
			if 'port_count' in profile.keys():
				portCount = profile['port_count']
				row[indexPortCount] = 'FALSE' if is_none(portCount) else 'TRUE'
			#   port importance
			#       default 'critical'
			indexPortImportance = listHeader2.index('PORT IMPORTANCE')
			row[indexPortImportance] = 'critical'
			#   service direction
			#       'up' if service port
			#       'cross' if crosslink
			indexServiceDirection = listHeader2.index('SERVICE DIRECTION')
			if portType == 'crosslink':
				row[indexServiceDirection] = 'cross'
			elif portType == 'service_up':
				row[indexServiceDirection] = 'up'
			elif portType == 'service_down': 
				row[indexServiceDirection] = 'down'
			elif portType == 'layer3':
				row[indexServiceDirection] = 'no_switchport'
			#   is tls
			#       default 'FALSE'
			indexIsTLS = listHeader2.index('IS TLS')
			row[indexIsTLS] = 'FALSE'

			# begin setting vlan dependent information
			site_id = profile['site_id']
			for j in range(len(listVLAN)):
				# index row 2 by row 1 value
				label = 'SERVICE ' + str(j + 1)
				vlanID = str(listVLAN[j])
				# check that vlan exists
				is_site = site_id in dict_service and vlanID in dict_service[site_id]
				is_global = 'global' in dict_service and vlanID in dict_service['global']
				if site_id in dict_service or 'global' in dict_service:
					if is_site or is_global:
						if is_site:
							name = list(dict_service[site_id][vlanID].keys())[0]
						else:
							name = list(dict_service['global'][vlanID].keys())[0]
						index = listHeader1.index(label)
						#   service enabled
						#       default True
						row[index] = True
						#   service name
						#       set to name of vlan
						row[index + 1] = name
						#   service vlan
						#       set to 'u' if vlan is native
						#       default None
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
					#       default True
					row[index] = True
					#   service name
					#       set to name of vlan
					row[index + 1] = name
					#   service vlan
					#       set to 'u' if vlan is native
					#       default None
					#if str(profile['native_vlan']) == str(vlanID):
					#    row[index + 2] = 'u'
					#       default always set first vlan to untagged
					row[index + 2] = 'u' if j == 0 else None
			data.append(row)
	# output information to csv
	output_csv(listHeader1, listHeader2, data, path_out)
