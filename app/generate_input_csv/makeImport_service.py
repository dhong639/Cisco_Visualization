import csv
from .processInput import pad_header1

def makeImport_service(dict_service, path_out, version, date):
	# declare headers
	data = []
	listHeader1 = [
		'Service Import CSV',
		'Version Number:',
		version,
		'',
		date
	]
	listHeader2 = [
		'NAME',
		'ENABLED',
		'VLAN',
		'RATE LIMIT IN',
		'RATE LIMIT OUT',
		'PACKET PRIORITY',
		'MULTICAST MODE',
		'IS MULTICAST QUERIER',
		'IS MANAGEMENT',
		'REMARK PACKETS',
		'IS TLS',
		'LOCAL SWITCHING',
		'SUMMARY',
		'BLOCK DHCP SERVER',
		'WARN ON NO EXTERN'
	]
	pad_header1(listHeader1, listHeader2)
	# set rows for data
	for site_id in dict_service:
		for vlan_id in dict_service[site_id]:
			for vlan_name in dict_service[site_id][vlan_id]:
				is_mgmt = dict_service[site_id][vlan_id][vlan_name]['management']
				dict_ = {
					'NAME': vlan_name,
					'ENABLED': 'TRUE',
					'VLAN': vlan_id,
					'RATE LIMIT IN': None,
					'RATE LIMIT OUT': None,
					'PACKET PRIORITY': 7 if is_mgmt == True else 0,
					'MULTICAST MODE': 'flooding',
					'IS MULTICAST QUERIER': 'FALSE',
					'IS MANAGEMENT': 'TRUE' if is_mgmt == True else 'FALSE',
					'REMARK PACKETS': 'TRUE' if is_mgmt == True else 'FALSE',
					'IS TLS': 'FALSE',
					'LOCAL SWITCHING': 'TRUE',
					'SUMMARY': 'TRUE',
					'BLOCK DHCP SERVER': 'TRUE' if is_mgmt == True else 'FALSE',
					'WARN ON NO EXTERN': 'FALSE'
				}
				data.append(dict_)
	# write to output file
	with open(path_out, 'w') as file:
		writer = csv.writer(file)
		writer.writerow(listHeader1)
		writer = csv.DictWriter(file, listHeader2)
		writer.writeheader()
		writer.writerows(data)
