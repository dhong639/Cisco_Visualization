from .processInput import pad_header1
from .processInput import output_csv

def makeImport_deviceSetting(path_out, version, date, link=None):
	if version == 'v':
		version = 'v0.2'
	# set vnc information
	listHeader1 = [
		'Device Settings Import',
		'Version Number:',
		version,
		link,
		date
	]
	listHeader2 = [
		'NAME',
		'ENABLED',
		'LED TIMER',
		'POE BATTERY AVAILABLE',
		'POE EXTERNAL BATTERY AVAILABLE',
		'POE MODE',
		'POE USAGE THRESHOLD',
		'CLOCKING PACKET ACCELERATION',
		'MAC AGING TIMER',
		'SPANNING TREE PRIORITY'
	]
	pad_header1(listHeader1, listHeader2)

	data = []

	row = [None] * len(listHeader2)
	index_name = listHeader2.index('NAME')
	row[index_name] = 'PoE Device Default'

	index_enabled = listHeader2.index('ENABLED')
	row[index_enabled] = 'true'

	index_timerLED = listHeader2.index('LED TIMER')
	row[index_timerLED] = 0

	index_batteryAvailable_POE = listHeader2.index('POE BATTERY AVAILABLE')
	row[index_batteryAvailable_POE] = 40

	index_batteryAvailable_externalPOE = listHeader2.index('POE EXTERNAL BATTERY AVAILABLE')
	row[index_batteryAvailable_externalPOE] = 75

	index_modePOE = listHeader2.index('POE MODE')
	row[index_modePOE] = 'Automatic'

	index_usageThresholdPOE = listHeader2.index('POE USAGE THRESHOLD')
	row[index_usageThresholdPOE] = 0.99

	index_clockingPacketAcceleration= listHeader2.index('CLOCKING PACKET ACCELERATION')
	row[index_clockingPacketAcceleration] = 'false'

	index_agingTimer_mac = listHeader2.index('MAC AGING TIMER')
	row[index_agingTimer_mac] = None

	index_spanningTreePriority = listHeader2.index('SPANNING TREE PRIORITY')
	row[index_spanningTreePriority] = 'byLevel'

	data.append(row)

	output_csv(listHeader1, listHeader2, data, path_out)