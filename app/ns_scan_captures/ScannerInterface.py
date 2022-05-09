import re

class ScannerInterface(object):
	def __init__(self, section):
		self.config = section
		self.description = None
		self.if_name = None
		for line in section:
			line = line.strip()
			self.set_description(line)
			line = line.lower()
			self.set_ifName(line)
		self.ip_address = None
		self.list_foundMAC = []
		self.native_vlan = None
		self.trunk_count = 0
		self.trunk_list = []
		self.voice_vlan = None
		self.access_vlan = None
		self.trunk_native_vlan = None

	def get_name(self):
		return self.if_name

	def get_addressIP(self):
		return self.ip_address

	def get_dict(self):
		dict_ = {}
		dict_['config'] = self.config
		dict_['description'] = self.description
		dict_['if_name'] = self.if_name
		return dict_

	def set_description(self, line):
		is_description = re.compile(r'description (.+)')
		match_description = re.match(is_description, line)
		if match_description:
			self.description = match_description.group(1)

	def set_listFoundMAC(self, list_foundMAC):
		self.list_foundMAC = list_foundMAC

	def set_ifName(self, line):
		is_ifName = re.compile(r'interface (.+)')
		match_ifName = re.match(is_ifName, line.lower())
		if match_ifName:
			self.if_name = match_ifName.group(1)
	
	def set_nativeVLAN(self):
		if self.trunk_native_vlan != None:
			self.native_vlan = self.trunk_native_vlan
		elif self.access_vlan:
			self.native_vlan = self.access_vlan
	
	def set_accessVLAN(self, line):
		is_access = re.compile(r'switchport access vlan (\d+)')
		match_access = re.match(is_access, line)
		if match_access:
			self.access_vlan = int(match_access.group(1))

	def set_trunkNativeVLAN(self, line):
		is_trunkNative = re.compile(r'switchport trunk native vlan (\d+)')
		match_trunkNative = re.match(is_trunkNative, line)
		if match_trunkNative:
			self.trunk_native_vlan = int(match_trunkNative.group(1))
			self.native_vlan = int(match_trunkNative.group(1))

	def set_listTrunkVLAN(self, line):
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
					self.trunk_list.append(item)

	def set_voiceVLAN(self, line):
		is_voice = re.compile(r'switchport voice vlan (\d+)')
		match_voice = re.match(is_voice, line)
		if match_voice:
			self.voice_vlan = int(match_voice.group(1))

	def set_addressIP(self, line):
		is_addressIP = re.compile(r'ip address (\d+(?:\.\d+){3}) (\d+(?:\.\d+){3})')
		match_addressIP = re.match(is_addressIP, line.strip().lower())
		if match_addressIP:
			self.ip_address = match_addressIP.group(1)
