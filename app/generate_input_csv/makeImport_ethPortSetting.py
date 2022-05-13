# user defined python files
#       processInput
#           pad_header1      append header1 with blank spaces
#           output_csv       write to csv file
#           is_none          check if value is '' or None
from .processInput import pad_header1
from .processInput import output_csv
from .processInput import is_none


# makeImport_ethPortSetting
#        input:
#           list_portSetting     list[dict]          list of dictionaries containing setting info
#           dict_service     dict{int:string}    dictionary containing service/vlan information
#           maxPortCount    int                 largest number of interfaces on one single device
#           version         string              version of vnc
#           link            string              link to vnc
#           date            string              current timestamp
#           fileOut         string              output location of csv file
#       output:
#           None
#       function:
#           create headers for output file
#               row 1 is for vnc versioning and indexing of row 2 columns
#               row 2 is for general device information followed by info per interface
#       fill in data columns
#       output results to csv file and place in given output location
def makeImport_ethPortSetting(dict_service, list_portSetting, path_out, version, date, link=None):
	#print(list_portSetting)
	if version == 'v':
		version = 'v0.2'
	# filling out header information
	# set vnc information
	listHeader1 = [
		'Eth-Port Settings Import',
		'Version Number',
		version,
		link,
		date
	]
	# set headers for port setting information
	listHeader2 = [
		'NAME',
		'ENABLED',
		'MAX BITRATE',
		'DUPLEX MODE',
		'CLI COMMANDS',
		'LOOP DETECT ENABLED',
		'STP ENABLED',
		'FAST LEARNING',
		'BPDU GUARD',
		'BPDU FILTER',
		'GUARD LOOP',
		'POE ENABLED',
		'POE PRIORITY',
		'POE ALLOCATED POWER',
		'LLDP ENABLED'
	]
	# pad listHeader1 until it's the same length as listHeader2
	pad_header1(listHeader1, listHeader2)
	# add vnc information
	listHeader1 = listHeader1 + [
		'LLDP MED 1'
	]
	# add headers for port setting information
	listHeader2 = listHeader2 + [
		'LLDP MODE',
		'ALL LLDP MED ENABLED',
		'MAC SECURITY MODE',
		'MAC LIMIT',
		'MAC VIOLATION ACTION',
		'MAC AGING TYPE',
		'MAC AGING TIME',
		'LLDP MED ENABLED',
		'LLDP MED ADVERTISED APPLICATION',
		'LLDP MED SERVICE NAME',
		'LLDP MED DSCP MARK',
		'LLDP MED PRIORITY'
	]
	# pad listHeader1 until it's the same length as listHeader2
	pad_header1(listHeader1, listHeader2)

	# empty list of data
	data = []

	for setting in list_portSetting:
		# each row is filled with None value by default
		row = [None] * (len(listHeader2))
		#   name
		#       set to name of setting
		indexName = listHeader2.index('NAME')
		row[indexName] = setting['port_setting_name']
		#   enabled
		#       default 'TRUE'
		indexEnabled = listHeader2.index('ENABLED')
		row[indexEnabled] = 'TRUE'
		#   max bitrate
		#       default -1
		#       set to speed of setting if found
		indexSpeed = listHeader2.index('MAX BITRATE')
		speed = setting['speed']
		row[indexSpeed] = '-1' if is_none(speed) else str(speed)
		#   duplex mode
		#       default 'auto'
		#       set to duplex of setting if found
		indexDuplex = listHeader2.index('DUPLEX MODE')
		duplex = setting['duplex']
		row[indexDuplex] = 'Auto' if is_none(duplex) else str(duplex).capitalize()
		#   loop detect enabled
		#       default 'FALSE'
		indexLoopDetect = listHeader2.index('LOOP DETECT ENABLED')
		row[indexLoopDetect] = 'FALSE'
		#   stp enabled
		#       default 'TRUE'
		indexSTP = listHeader2.index('STP ENABLED')
		row[indexSTP] = 'TRUE'
		#   fast learning
		#       default 'FALSE
		#       set to value of portfast if found
		indexPortfast = listHeader2.index('FAST LEARNING')
		stp_portfast = setting['stp_portfast']
		row[indexPortfast] = 'FALSE' if is_none(stp_portfast) else str(stp_portfast).upper()
		#   bpdu guard
		#       default 'FALSE'
		#       set to value of bpdu guard if found
		indexGuardBPDU = listHeader2.index('BPDU GUARD')
		stp_bpduguard = setting['stp_bpduguard']
		row[indexGuardBPDU] = 'FALSE' if is_none(stp_bpduguard) else str(stp_bpduguard).upper()
		#   bpdu filter
		#       default 'FALSE'
		#       set to value of bpdu filter if found
		indexFilterBPDU = listHeader2.index('BPDU FILTER')
		stp_bpdufilter = setting['stp_bpdufilter']
		row[indexFilterBPDU] = 'FALSE' if is_none(stp_bpdufilter) else str(stp_bpdufilter).upper()
		#   guard loop
		#       default 'FALSE'
		#       set to value of guard loop if found
		indexGuardLoop = listHeader2.index('GUARD LOOP')
		stp_guardloop = setting['stp_guardloop']
		row[indexGuardLoop] = 'FALSE' if is_none(stp_guardloop) else str(stp_guardloop).upper()
		#   poe enabled
		#       default to 'FALSE'
		#       set to value of poe enabled if found
		indexPOE = listHeader2.index('POE ENABLED')
		poe_enabled = setting['poe_enabled']
		row[indexPOE] = 'FALSE' if is_none(poe_enabled) else str(poe_enabled).upper()
		#   poe priority
		#       default 'Low'
		indexPriorityPOE = listHeader2.index('POE PRIORITY')
		row[indexPriorityPOE] = 'Low'
		#   poe allocated power
		#       default '0.0'
		indexPowerPOE = listHeader2.index('POE ALLOCATED POWER')
		row[indexPowerPOE] = '0.0'
		#   lldp enabled
		#       default 'true'
		indexLLDP = listHeader2.index('LLDP ENABLED')
		row[indexLLDP] = 'TRUE'
		#   lldp mode
		#       default 'RxAndTx'
		indexModeLLDP = listHeader2.index('LLDP MODE')
		row[indexModeLLDP] = 'RxAndTx'
		#   all lldp med enabled
		#       default 'FALSE'
		#       set to 'TRUE' if voice vlan exists
		indexMedLLDP_all = listHeader2.index('ALL LLDP MED ENABLED')
		voice_vlan = setting['voice_vlan']
		row[indexMedLLDP_all] = 'FALSE' if is_none(voice_vlan) else 'TRUE'
		#   mac security mode
		#       default 'disabled'
		#       set to other port security if found
		indexSecurityMAC = listHeader2.index('MAC SECURITY MODE')
		port_security_mode = setting['port_security_mode']
		row[indexSecurityMAC] = 'disabled' if is_none(port_security_mode) else port_security_mode.lower()
		#   mac limit
		#       default '1'
		#       set to other mac limit if found
		indexLimitMAC = listHeader2.index('MAC LIMIT')
		port_security_maximum = setting['port_security_maximum']
		row[indexLimitMAC] = '1' if is_none(port_security_maximum) else port_security_maximum
		#   mac violation action
		#       default 'shutdown'
		#       set other action (ie 'protect') if found
		indexViolationMAC = listHeader2.index('MAC VIOLATION ACTION')
		violation_mode = setting['violation_mode']
		row[indexViolationMAC] = 'shutdown' if is_none(violation_mode) else violation_mode.lower()
		#   mac aging time
		#       default '0'
		#       set other aging time if found
		indexAgingTimeMAC = listHeader2.index('MAC AGING TIME')
		aging_time = setting['aging_time']
		row[indexAgingTimeMAC] = '0' if is_none(aging_time) else aging_time
		#   mac aging type
		#       default 'absolute'
		#       set other aging type if found
		indexAgingTypeMAC = listHeader2.index('MAC AGING TYPE')
		aging_type = setting['aging_type']
		row[indexAgingTypeMAC] = 'absolute' if is_none(aging_type) else aging_type
		#   lldp med enabled
		#       default 'FALSE'
		#       if voice vlan exists, set 'TRUE'
		indexMedLLDP = listHeader2.index('LLDP MED ENABLED')
		voice_vlan = setting['voice_vlan']
		row[indexMedLLDP] = 'FALSE' if is_none(voice_vlan) else 'TRUE'
		#   lldp med advertised application
		#       set to 'Voice' if voice vlan found
		indexMedAdvertised = listHeader2.index('LLDP MED ADVERTISED APPLICATION')
		voice_vlan = setting['voice_vlan']
		row[indexMedAdvertised] = None if is_none(voice_vlan) else 'Voice'
		#   lldp med service name
		#       set to name of voice vlan if voice vlan found
		indexMedServiceName = listHeader2.index('LLDP MED SERVICE NAME')
		voice_pair = setting['voice_vlan']
		if is_none(voice_vlan):
			row[indexMedServiceName] = None
		else:
			site_id = voice_pair[0]
			vlan_id = str(voice_pair[1])
			# check that vlan exists
			is_site = site_id in dict_service and vlan_id in dict_service[site_id]
			is_global = 'global' in dict_service and vlan_id in dict_service['global']
			# only set vlan info if vlan exists
			if site_id in dict_service or 'global' in dict_service:
				if is_site or is_global:
					if is_site:
						voice_vlan = list(dict_service[site_id][vlan_id].keys())[0]
					else:
						voice_vlan = list(dict_service['global'][vlan_id].keys())[0]
				else:
					print('\tWarning: %s vlan %s not in service import' % (site_id, vlan_id))
			#if site_id in dict_service:
			#	voice_vlan = dict_service[site_id][vlan_id]
			else:
				voice_vlan = str(vlan_id) + ' - no site'
			row[indexMedServiceName] = voice_vlan
		#   lldp med dscp mark
		#       set to '46' if voice vlan found
		indexMedDSCP = listHeader2.index('LLDP MED DSCP MARK')
		voice_vlan = setting['voice_vlan']
		row[indexMedDSCP] = None if is_none(voice_vlan) else '46'
		#   lldp med priority
		#       set to '3' if voice vlan found
		indexMedPriority = listHeader2.index('LLDP MED PRIORITY')
		voice_vlan = setting['voice_vlan']
		row[indexMedPriority] = None if is_none(voice_vlan) else '3'
		# remove duplicate settings
		if row not in data:
			data.append(row)
	# output information to csv
	output_csv(listHeader1, listHeader2, data, path_out)
