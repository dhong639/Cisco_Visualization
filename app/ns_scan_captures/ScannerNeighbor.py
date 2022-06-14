import re

class ScannerNeighbor:
	def __init__(self, dict_site2device, dict_neighbor):
		# store unmanaged devices, classify by layer3 and all others
		self.dict_unmanaged = {
			'router': set(),
			'other': set()
		}
		self.dict_tor = {}
		self.set_fabric = set()
		self.dict_edgeFabric = {}
		self.dict_edgeOther = {}

		# classify nodes, routers, and tors for pathing purposes
		#	routers
		#		routers are not fabric, so they should never be a source
		#		direct links to routers are service_up links, so routers can be targets
		#	tors and nodes
		#		all nodes point to a tor
		#		nodes are sources, tors are destinations
		#		not added yet, need to determine if tors are directly connected first
		for site_id in dict_site2device:
			# tors and nodes are categorized by site IDs
			self.dict_tor[site_id] = set()
			# routers are not considered layer 2 and therefore aren't fabric
			#for router in dict_site2device[site_id]['list_router']:
			for router in dict_site2device[site_id]['list_unmanaged']['router']:
				self.dict_unmanaged['router'].add(router)
				self.set_fabric.add(router)
			# all other devices that are not managed
			# unmanaged is same as not in fabric
			for other in dict_site2device[site_id]['list_unmanaged']['other']:
				self.dict_unmanaged['other'].add(other)
				self.set_fabric.add(other)
			# ToRs are considered fabric
			for tor in dict_site2device[site_id]['list_tor']:
				self.dict_tor[site_id].add(tor)
				self.set_fabric.add(tor)
			# nodes are considered fabric
			for node in dict_site2device[site_id]['list_node']:
				self.set_fabric.add(node)

		# add in information for "cdp neig", "lldp nei de", and "lldp neighbors"
		for device_id in dict_neighbor:
			if 'cdp neig' in dict_neighbor[device_id]:
				self.add_cdp(device_id, dict_neighbor[device_id]['cdp neig'])
			if 'lldp nei de' in dict_neighbor[device_id]:
				self.add_lldpNeiDe(device_id, dict_neighbor[device_id]['lldp nei de'])
			if 'lldp neighbors' in dict_neighbor[device_id]:
				self.add_lldpNeighbors(device_id, dict_neighbor[device_id]['lldp neighbors'])

	def get_edgesFabric(self, flag=True):
		if flag:
			return self.dict_edgeFabric

	def get_edgesOther(self):
		#dict_ = {}
		#for device_id in self.dict_edgeOther:
		#	list_layer3 = sorted(self.dict_edgeOther[device_id]['layer3'])
		#	list_other = sorted(self.dict_edgeOther[device_id]['eth_port'])
		#	dict_[device_id] = {
		#		'layer3': list_layer3, 
		#		'eth_port': list_other
		#	}
		return self.dict_edgeOther

	def clean_edges(self):
		for sourceID in self.dict_edgeFabric:
			for targetID in self.dict_edgeFabric[sourceID]:
				set_intfSource = set()
				set_intfTarget = set()
				list_pair = []
				list_intfSource = []
				list_intfTarget = []
				for pair in self.dict_edgeFabric[sourceID][targetID]['pairs']:
					# determine if link has source and target interface
					if pair[0] != None and pair[1] != None:
						set_intfSource.add(pair[0])
						set_intfTarget.add(pair[1])
						list_pair.append([pair[0], pair[1]])
					# link has source interface but no target interface
					elif pair[0] != None and pair[1] == None:
						list_intfSource.append(pair[0])
					# link has target interface but no source interface
					elif pair[1] != None and pair[0] == None:
						list_intfTarget.append(pair[1])
				# remove intf from list_intfSource if it's already part of a complete pair
				for i in range(len(list_intfSource)):
					if list_intfSource[i] in set_intfSource:
						list_intfSource[i] = None
				list_intfSource = [item for item in list_intfSource if item != None]
				# remove intf from list_intfTarget if it's already part of a complete pair
				for i in range(len(list_intfTarget)):
					if list_intfTarget[i] in set_intfTarget:
						list_intfTarget[i] = None
				list_intfTarget = [item for item in list_intfTarget if item != None]
				# count number of source interfaces with missing target interfaces
				# count number of target interfaces with missing source interfaces
				# if the two numbers are equal, merge the two lists into a single list of pairs
				if len(list_intfSource) == len(list_intfTarget):
					for i in range(len(list_intfSource)):
						list_pair.append([list_intfSource[i], list_intfTarget[i]])
				# if the list of pairs has at least one element, set as new value for 'pairs'
				if len(list_pair) != 0:
					self.dict_edgeFabric[sourceID][targetID]['pairs'] = list_pair
				if len(self.dict_edgeFabric[sourceID][targetID]['pairs']) == 1:
					if pair[0] != None and pair[1] == None:
						intf = self.dict_edgeFabric[targetID][sourceID]['pairs'][0][0]
						self.dict_edgeFabric[sourceID][targetID]['pairs'][0][1] = intf
					if pair[1] != None and pair[0] == None:
						intf = self.dict_edgeFabric[targetID][sourceID]['pairs'][0][1]
						self.dict_edgeFabric[sourceID][targetID]['pairs'][0][0] = intf

	def add_cdp(self, sourceID, section_cdp):
		for row in section_cdp:
			sourceIntf = self.get_nameIntf(row['local intrfce'])
			targetIntf = self.get_nameIntf(row['port id'])
			capability = row['capability']
			targetID = row['device id']
			platform = row['platform']
			if targetID != None:
				targetID = None if targetID.strip() == '' else targetID.split('.')[0]
			# if both sourceID and targetID are fabric, record bidirectional links
			if sourceID in self.set_fabric and targetID in self.set_fabric:
				self.helper_addFabric(sourceID, sourceIntf, targetID, targetIntf, capability)
				self.helper_addFabric(targetID, targetIntf, sourceID, sourceIntf, capability)
			# connected to some edge device
			# note that unmanaged devices are still considered fabric when creating the graph
			elif sourceID in self.set_fabric and targetID not in self.set_fabric:
				self.helper_addOther(sourceID, sourceIntf, capability, platform)
	
	def add_lldpNeighbors(self, sourceID, section_lldpNeighbors):
		for row in section_lldpNeighbors:
			sourceIntf = self.get_nameIntf(row['local intf'])
			targetIntf = self.get_nameIntf(row['port id'])
			capability = row['capability']
			targetID = row['device id']
			# cisco naming convention combines hostname with domain name
			if targetID != None:
				targetID = None if targetID.strip() == '' else targetID.split('.')[0]
			# if both sourceID and targetID are fabric, record bidirectional links
			if sourceID in self.set_fabric and targetID in self.set_fabric:
				self.helper_addFabric(sourceID, sourceIntf, targetID, targetIntf, capability)
				self.helper_addFabric(targetID, targetIntf, sourceID, sourceIntf, capability)
			# connected to some edge device
			# note that unmanaged devices are still considered fabric when creating the graph
			elif sourceID in self.set_fabric and targetID not in self.set_fabric:
				self.helper_addOther(sourceID, sourceIntf, capability, targetID)

	def add_lldpNeiDe(self, sourceID, section_lldp):
		for row in section_lldp:
			local_intf = row['local intf']
			system_name = row['system name']
			port_description = row['port description']
			chassis_id = row['chassis id']
			port_id = row['port id']
			capability = row['enabled capabilities']

			# ignore row if there's no identifiable target id
			if not chassis_id and not system_name and not port_description and not port_id:
				continue
			
			targetID = chassis_id if system_name == None else system_name.split('.')[0]
			sourceIntf = self.get_nameIntf(local_intf)
			targetIntf = self.get_nameIntf(port_id)
			if targetIntf == None:
				targetIntf =  self.get_nameIntf(port_description)

			# cisco naming convention combines hostname with domain name
			if targetID != None:
				targetID = None if targetID.strip() == '' else targetID.split('.')[0]
			# if both sourceID and targetID are fabric, record bidirectional links
			if sourceID in self.set_fabric and targetID in self.set_fabric:
				self.helper_addFabric(sourceID, sourceIntf, targetID, targetIntf, capability)
				self.helper_addFabric(targetID, targetIntf, sourceID, sourceIntf, capability)
			# connected to some edge device
			# note that unmanaged devices are still considered fabric when creating the graph
			elif sourceID in self.set_fabric and targetID not in self.set_fabric:
				self.helper_addOther(sourceID, sourceIntf, capability, port_id)

	def get_nameIntf(self, string):
		if string == None:
			return None
		is_intf = re.compile(r'^([a-z]+-?[a-z]+)\s*(\d+(?:\/\d+)*)$')
		match_intf = re.match(is_intf, string)
		prefix = None
		if match_intf:
			prefix = match_intf.group(1)
			if prefix != 'vlan':
				prefix = prefix[0:2]
		return None if not match_intf else prefix + match_intf.group(2)

	def helper_hasSourceIntf(self, listPair, sourceIntf):
		if sourceIntf == None:
			return False
		has_sourceIntf = False
		for pair in listPair:
			if sourceIntf == pair[0]:
				has_sourceIntf = True
		return has_sourceIntf
	
	def helper_hasTargetIntf(self, listPair, targetIntf):
		if targetIntf == None:
			return False
		has_targetIntf = False
		for pair in listPair:
			if targetIntf == pair[1]:
				has_targetIntf = True
		return has_targetIntf

	def helper_addFabric(self, sourceID, sourceIntf, targetID, targetIntf, capability):
		if sourceID in self.dict_edgeOther:
			if sourceIntf in self.dict_edgeOther[sourceID]['layer3']:
				del self.dict_edgeOther[sourceID]['layer3'][sourceIntf]
			if sourceIntf in self.dict_edgeOther[sourceID]['eth_port']:
				del self.dict_edgeOther[sourceID]['eth_port'][sourceIntf]
		if sourceID not in self.dict_edgeFabric:
			self.dict_edgeFabric[sourceID] = {}
		if targetID not in self.dict_edgeFabric[sourceID]:
			self.dict_edgeFabric[sourceID][targetID] = {
				'capability': capability,
				'pairs': [],
			}
		pair = [sourceIntf, targetIntf]
		if pair not in self.dict_edgeFabric[sourceID][targetID]['pairs'] and pair != [None, None]:
			self.dict_edgeFabric[sourceID][targetID]['pairs'].append(pair)

	def helper_addOther(self, sourceID, sourceIntf, capability, platform):
		if sourceID not in self.dict_edgeOther:
			self.dict_edgeOther[sourceID] = {
				'layer3': {},
				'eth_port': {}
			}
		if sourceIntf != None and sourceID in self.set_fabric and platform not in self.set_fabric:
			if capability != None and 'r' in capability and 't' not in capability:
				self.dict_edgeOther[sourceID]['layer3'][sourceIntf] = platform
			else:
				self.dict_edgeOther[sourceID]['eth_port'][sourceIntf] = platform
				#print(self.dict_edgeOther[sourceID]['eth_port'])
