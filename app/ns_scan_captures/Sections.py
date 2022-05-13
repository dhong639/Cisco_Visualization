import re

class Sections:
	def __init__(self, file, privileged):
		self.sections = {}
		self.sections['site_id'] = None
		self.sections['ip_address'] = None
		self.sections['location'] = None
		self.deviceID = None
		is_commandShow = re.compile(r'[^#]+#show ([^#]*)')
		if privileged != None and privileged != '' and privileged != '#':
			is_commandShow = re.compile(r'.+' + privileged + r'show (.+)')
		currentSection = None
		for line in file:
			line = line.decode('utf-8')
			line = line.rstrip()
			match_commandShow = re.match(is_commandShow, line)
			if match_commandShow:
				currentSection = match_commandShow.group(1)
			if currentSection != None:
				if currentSection not in self.sections:
					self.sections[currentSection] = []
				if not match_commandShow and '#' not in line:
					self.sections[currentSection].append(line)
					if 'hostname' in line:
						self.deviceID = line.split('hostname')[1].strip()
						self.sections['device_id'] = self.deviceID
		self.sections['interface config'] = self.make_interfaceRun(self.sections['running-config'])
		if 'cdp neig' in self.sections or 'cdp neighbors' in self.sections:
			section_cdp = {}
			if 'cdp neig' in self.sections:
				section_cdp = self.sections['cdp neig']
			elif 'cdp neighbors' in self.sections:
				section_cdp = self.sections['cdp neighbors']
			self.sections['cdp neig'] = self.make_cdpNeig(section_cdp)
		if 'lldp nei de' in self.sections:
			self.sections['lldp nei de'] = self.make_lldpNeiDe(self.sections['lldp nei de'])
		if 'lldp neighbors' in self.sections:
			key = 'lldp neighbors'
			self.sections['lldp neighbors'] = self.make_lldpNeighbors(self.sections[key])
		if 'interface | inc Ethernet|Vlan' in self.sections:
			key = 'interface | inc Ethernet|Vlan'
			self.sections[key] = self.make_interfaceStatus(self.sections[key])
		if 'mac address-table' in self.sections:
			section_tableMAC = self.sections['mac address-table']
			self.sections['unique vlans found'] = self.make_foundVLAN_unique(section_tableMAC)
			self.sections['total vlans found'] = self.make_foundVLAN_total(section_tableMAC)
	
	def add_hardware(self, row):
		self.sections['site_id'] = row['site_id']
		self.sections['ip_address'] = row['ip_address']
		self.sections['location'] = row['location']

	def get_siteID(self):
		if 'site_id' in self.sections:
			return self.sections['site_id']

	def get_dict_all(self):
		return self.sections

	def get_dict_device(self):
		list_ = [
			'running-config',
			'lacp sys-id',
			'interface config',
			'interface | inc Ethernet|Vlan',
			'unique vlans found',
			'total vlans found'
		]
		dict_ = {}
		for section in self.sections:
			if section in list_:
				dict_[section] = self.sections[section]
		return dict_

	def get_dict_neighbor(self):
		list_ = ['cdp neig', 'lldp nei de', 'lldp neighbors']
		dict_ = {}
		for section in self.sections:
			if section in list_:
				dict_[section] = self.sections[section]
		return dict_

	def get_deviceID(self):
		return self.deviceID

	def get_nameIntf(self, string):
		is_intf = re.compile(r'^([a-z]+-?[a-z]+)\s*(\d+(?:\/\d+)*)$')
		match_intf = re.match(is_intf, string)
		prefix = None
		if match_intf:
			prefix = match_intf.group(1)
			if prefix != 'vlan':
				prefix = prefix[0:2]
		return None if not match_intf else prefix + match_intf.group(2)

	def make_foundVLAN_total(self, section_tableMAC):
		sections = {}
		for line in section_tableMAC:
			line = line.strip().lower()
			items = line.split()
			if len(items) > 0:
				for intf in items[-1].split(','):
					name = self.get_nameIntf(intf)
					if name != None:
						if name not in sections:
							sections[name] = 0
						vlan = items[0]
						#if self.is_int(vlan):
						if vlan.isdigit():
							sections[name] += 1
		return sections

	def make_foundVLAN_unique(self, section_tableMAC):
		sections = {}
		for line in section_tableMAC:
			line = line.strip().lower()
			items = line.split()
			if len(items) > 0:
				for intf in items[-1].split(','):
					name = self.get_nameIntf(intf)
					if name != None:
						if name not in sections:
							sections[name] = set()
						vlan = items[0]
						#if self.is_int(vlan):
						if vlan.isdigit():
							sections[name].add(int(vlan))
		for key in sections:
			list_ = sorted(list(sections[key]))
			sections[key] = list_
		return sections

	def make_interfaceStatus(self, section_interfaceStatus):
		sections = {}
		current_key = None
		for line in section_interfaceStatus:
			line = line.strip().lower()
			if not line.startswith('hardware'):
				current_key = line.split()[0]
				if self.get_nameIntf(current_key) != None:
					current_key = self.get_nameIntf(current_key)
				sections[current_key] = []
				sections[current_key].append(line)
			else:
				sections[current_key].append(line)
		return sections

	def make_interfaceRun(self, section_run):
		section = {
			'ethernet': [],
			'vlan': [],
			'port-channel': []
		}
		current_name = None
		current_type = None
		current_value = []
		dict_length2ethernet = {}
		count_ethernet = 0
		for line in section_run:
			if line.startswith('interface'):
				name = line.split('interface')[1].strip().lower()
				if 'ethernet' in name or 'vlan' in name or 'port-channel' in name:
					current_name = name
					if 'ethernet' in name:
						length = len(name)
						if length not in dict_length2ethernet:
							dict_length2ethernet[length] = []
						dict_length2ethernet[length].append(count_ethernet)
						count_ethernet += 1
						current_type = 'ethernet'
					elif 'vlan' in name:
						current_type = 'vlan'
					elif 'port-channel' in name:
						current_type = 'port-channel'
			if line.strip() == '!' and current_name != None and current_type != None:
				section[current_type].append(current_value)
				current_name = None
				current_type = None
				current_value = []
			if current_name != None and current_type != None:
				current_value.append(line)
		length_min = min(dict_length2ethernet.keys())
		if len(dict_length2ethernet[length_min]) == 1:
			index = dict_length2ethernet[length_min][0]
			section['ethernet'][index] = None
		section['ethernet'] = [item for item in section['ethernet'] if item != None]
		return section

	def make_lldpNeiDe(self, section_lldpNeiDe):
		is_localIntf = re.compile(r'local intf: (.+)')
		is_chassisID = re.compile(r'chassis id: (.+)')
		is_portID = re.compile(r'port id: (.+)')
		is_portDescription = re.compile(r'port description: (.+)')
		is_systemName = re.compile(r'system name: (.+)')
		is_systemCapabilities = re.compile(r'system capabilities: (.+)')
		is_enabledCapabilities = re.compile(r'enabled capabilities: (.+)')
		isBreak = re.compile(r'-+')
		list_neighbor = []
		current_neighbor = []
		for line in section_lldpNeiDe:
			matchBreak = re.match(isBreak, line)
			if matchBreak or 'total entries displayed' in line.lower().strip():
				if current_neighbor != []:
					dict_ = {
						'local intf': None,
						'chassis id': None,
						'port id': None,
						'port description': None,
						'system name': None,
						'system capabilities': None,
						'enabled capabilities': None
					}
					for line in current_neighbor:
						match_localIntf = re.match(is_localIntf, line.lower())
						if match_localIntf:
							dict_['local intf'] = match_localIntf.group(1)
						match_chassisID = re.match(is_chassisID, line.lower())
						if match_chassisID:
							dict_['chassis id'] = match_chassisID.group(1)
						match_portID = re.match(is_portID, line.lower())
						if match_portID:
							dict_['port id'] = match_portID.group(1)
						match_portDescription = re.match(is_portDescription, line.lower())
						if match_portDescription:
							dict_['port description'] = match_portDescription.group(1)
						match_systemName = re.match(is_systemName, line.lower())
						if match_systemName:
							index = line.lower().index(match_systemName.group(1))
							dict_['system name'] = line[index:]
						match_systemCapabilities = re.match(is_systemCapabilities, line.lower())
						if match_systemCapabilities:
							dict_['system capabilities'] = match_systemCapabilities.group(1)
						match_enabledCapabilities = re.match(is_enabledCapabilities, line.lower())
						if match_enabledCapabilities:
							dict_['enabled capabilities'] = match_enabledCapabilities.group(1)
					list_neighbor.append(dict_)
				current_neighbor = []
			else:
				current_neighbor.append(line)
		return list_neighbor

	def make_lldpNeighbors(self, section_lldpNeighbors):
		list_neighbor = []
		foundHeader = False
		isTop = re.compile(r'device id\s*local intf\s*hold-time\s*capability\s*port id')
		indx_deviceID = None
		indx_localIntf = None
		indx_holdTime = None
		indx_capability = None
		indx_portID = None
		for line in section_lldpNeighbors:
			if foundHeader == False:
				line = line.strip().lower()
				matchHeader = re.match(isTop, line)
				if matchHeader:
					indx_deviceID = line.index('device id')
					indx_localIntf = line.index('local intf')
					indx_holdTime = line.index('hold-time')
					indx_capability = line.index('capability')
					indx_portID = line.index('port id')
					foundHeader = True
			else:
				if line.strip() != '' and 'total entries displayed' not in line.lower():
					dict_ = {
						'device id': None,
						'local intf': None,
						'hold-time': None,
						'capability': None,
						'port id': None
					}
					dict_['device id'] = line[indx_deviceID: indx_localIntf].strip()
					dict_['local intf'] = line[indx_localIntf: indx_holdTime].strip().lower()
					dict_['hold-time'] = line[indx_holdTime: indx_capability].strip().lower()
					dict_['capability'] = line[indx_capability: indx_portID].strip().lower()
					dict_['port id'] = line[indx_portID:].strip().lower()
					list_neighbor.append(dict_)
		return list_neighbor
	
	def make_cdpNeig(self, section_cdpNeig):
		list_neighbor = []
		foundHeader = False
		isTop = re.compile(r'device id\s*local intrfce\s*holdtme\s*capability\s*platform\s*port id')
		indx_deviceID = None
		indx_localIntrfce = None
		indx_holdtme = None
		indx_capability = None
		indx_platform = None
		indx_portID = None
		device_id = None
		for line in section_cdpNeig:
			if foundHeader == False:
				line = line.strip().lower()
				matchHeader = re.match(isTop, line)
				if matchHeader:
					indx_deviceID = line.index('device id')
					indx_localIntrfce = line.index('local intrfce')
					indx_holdtme = line.index('holdtme')
					indx_capability = line.index('capability')
					indx_platform = line.index('platform')
					indx_portID = line.index('port id')
					foundHeader = True
			else:
				if len(line.split()) == 1:
					device_id = line.strip()
				elif line.strip() != '' and 'total cdp entries' not in line.lower():
					dict_ = {
						'device id': None,
						'local intrfce': None,
						'holdtme': None,
						'capability': None,
						'platform': None,
						'port id': None
					}
					if device_id != None:
						dict_['device id'] = device_id
						device_id = None
					else:
						dict_['device id'] = line[indx_deviceID: indx_localIntrfce].strip()
					dict_['local intrfce'] = line[indx_localIntrfce: indx_holdtme].strip().lower()
					dict_['holdtme'] = line[indx_holdtme: indx_capability].strip().lower()
					dict_['capability'] = line[indx_capability: indx_platform].strip().lower()
					dict_['platform'] = line[indx_platform: indx_portID].strip().lower()
					dict_['port id'] = line[indx_portID:].strip().lower()
					list_neighbor.append(dict_)
		return list_neighbor


	def get_vlanMissing(self, dict_services):
		#print(dict_services.keys())
		list_missing = []
		if 'site_id' in self.sections:
			if 'interface config' in self.sections:
				if 'ethernet' in self.sections['interface config']:
					for item in self.sections['interface config']['ethernet']:
						self.helper_get_vlanMissing(item, list_missing, dict_services)
				if 'port-channel' in self.sections['interface config']:
					for item in self.sections['interface config']['port-channel']:
						self.helper_get_vlanMissing(item, list_missing, dict_services)
		#return sorted(list_missing, key = lambda i: (i['vlan'], i['site'], i['type']))
		return list_missing
	def helper_get_vlanMissing(self, item, list_missing, dict_services):
		site_id = self.sections['site_id']
		if set(dict_services.keys()) == set(['GLOBAL']):
			site_id = 'GLOBAL'
		#print(site_id)
		for line in item:
			line = line.strip().lower()
			
			list_trunk_vlan = self.get_listTrunkVLAN(line)
			if list_trunk_vlan:
				for trunk_vlan in list_trunk_vlan:
					if trunk_vlan not in dict_services[site_id]:
						trunk_vlan = int(trunk_vlan)
						name = '{}_trunk_{}'.format(trunk_vlan, site_id)
						list_missing.append({
							'name': name,
							'vlan': trunk_vlan,
							'type': 'trunk',
							'site': site_id,
							'base': False
						})
						"""dict_services[site_id][trunk_vlan] = {
							"name": name,
							"vlan": trunk_vlan
						}"""
			
			access_vlan = self.get_accessVLAN(line)
			native_vlan = self.get_trunkNativeVLAN(line)
			voice_vlan = self.get_voiceVLAN(line)
			list_vlan = [
				('access', access_vlan), 
				('trunkNative', native_vlan), 
				('voice', voice_vlan)
			]
			for item in list_vlan:
				type_, vlan = item
				if set(dict_services.keys()) != set(['GLOBAL']) and site_id not in dict_services:
					dict_services[site_id] = {}
				if vlan and vlan not in dict_services[site_id]:
					vlan = int(vlan)
					name = '{}_{}_{}'.format(vlan, type_, site_id)
					list_missing.append({
							'name': name,
							'vlan': vlan,
							'type': type_,
							'site': site_id,
							'base': False
						})
					"""dict_services[site_id][vlan] = {
						"name": name,
						"vlan": vlan,
						'base': False
					}"""
	def get_accessVLAN(self, line):
		is_access = re.compile(r'switchport access vlan (\d+)')
		match_access = re.match(is_access, line)
		if match_access:
			return int(match_access.group(1))
	def get_trunkNativeVLAN(self, line):
		is_trunkNative = re.compile(r'switchport trunk native vlan (\d+)')
		match_trunkNative = re.match(is_trunkNative, line)
		if match_trunkNative:
			return int(match_trunkNative.group(1))
	def get_listTrunkVLAN(self, line):
		output = []
		is_listTrunk = re.compile(r'switchport trunk allowed vlan (?:add )?(.+)')
		match_listTrunk = re.match(is_listTrunk, line)
		if match_listTrunk:
			list_trunk = match_listTrunk.group(1).split(',')
			for vlan in list_trunk:
				list_vlan = vlan.split('-')
				list_vlan = [int(item) for item in list_vlan]
				if len(list_vlan) == 2:
					start = list_vlan[0] + 1
					end = list_vlan[1]
					for item in range(start, end):
						list_vlan.append(item)
				for item in list_vlan:
					output.append(item)
		return output
	def get_voiceVLAN(self, line):
		is_voice = re.compile(r'switchport voice vlan (\d+)')
		match_voice = re.match(is_voice, line)
		if match_voice:
			return int(match_voice.group(1))
