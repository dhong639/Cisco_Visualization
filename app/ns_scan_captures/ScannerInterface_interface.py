import re
from .ScannerInterface import ScannerInterface

class ScannerInterface_interface(ScannerInterface):
	def __init__(self, section, port_number):
		try:
			ScannerInterface.__init__(self, section)
		except:
			super().__init__(section)
		self.speed = -1
		self.format_name()
		self.aging_time = 0
		self.aging_type = 'absolute'
		self.channel_group = None
		self.connected = False
		self.count_vlanTotal = 0
		self.duplex = 'auto'
		self.enabled = True
		self.list_foundMAC = []
		self.lldp_neighbors = None
		self.mac = None
		self.poe_enabled = True
		self.port_number = port_number
		self.port_security_maximum = 1
		self.port_security_mode = 'disabled'
		self.stp_bpdufilter = False
		self.stp_bpduguard = False
		self.stp_guardloop = False
		self.stp_portfast = False
		self.switchport = True
		self.violation_mode = 'shutdown'
		for line in section:
			line = line.lower().strip()
			self.set_portSecurity_agingTime(line)
			self.set_portSecurity_agingType(line)
			self.set_channelGroup(line)
			self.set_duplex(line)
			self.set_enabled(line)
			self.set_addressIP(line)
			self.set_poe(line)
			self.set_portSecurity_maximum(line)
			self.set_portSecurity_mode(line)
			self.set_speed(line)
			self.set_bpduFilter(line)
			self.set_bpduGuard(line)
			self.set_guardLoop(line)
			self.set_portfast(line)
			self.set_switchport(line)
			self.set_portSecurity_violation(line)
			self.set_accessVLAN(line)
			self.set_trunkNativeVLAN(line)
			self.set_voiceVLAN(line)
			self.set_listTrunkVLAN(line)
		self.set_nativeVLAN()

	def get_nativeVLAN(self):
		return self.native_vlan

	def get_dictPreview(self):
		dict_ = {
			'if_name': self.if_name,
			'port_number': self.port_number,
			'trunk_list': self.trunk_list,
			'access_vlan': self.access_vlan,
			'voice_vlan': self.voice_vlan,
			'list_foundMAC': self.list_foundMAC,
			'channel_group': self.channel_group
		}
		return dict_

	def get_dict(self):
		try:
			dict_ = ScannerInterface.get_dict(self)
		except:
			dict_ = super().get_dict()
		dict_['native_vlan'] = self.native_vlan
		dict_['trunk_count'] = self.trunk_count
		dict_['trunk_native_vlan'] = self.trunk_native_vlan
		dict_['trunk_list'] = self.trunk_list
		dict_['voice_vlan'] = self.voice_vlan
		dict_['access_vlan'] = self.access_vlan
		dict_['list_foundMAC'] = self.list_foundMAC
		dict_['aging_time'] = self.aging_time
		dict_['aging_type'] = self.aging_type
		dict_['channel_group'] = self.channel_group
		dict_['connected'] = self.connected
		#dict_['count_vlanTotal'] = self.count_vlanTotal
		dict_['duplex'] = self.duplex
		dict_['enabled'] = self.enabled
		dict_['ip_address'] = self.ip_address
		dict_['list_foundMAC'] = self.list_foundMAC
		dict_['lldp_neighbors'] = self.lldp_neighbors
		dict_['mac'] = self.mac
		dict_['poe_enabled'] = self.poe_enabled
		dict_['port_number'] = self.port_number
		dict_['port_security_maximum'] = self.port_security_maximum
		dict_['port_security_mode'] = self.port_security_mode
		dict_['speed'] = self.speed
		dict_['stp_bpdufilter'] = self.stp_bpdufilter
		dict_['stp_bpduguard'] = self.stp_bpduguard
		dict_['stp_guardloop'] = self.stp_guardloop
		dict_['stp_portfast'] = self.stp_portfast
		dict_['switchport'] = self.switchport
		dict_['violation_mode'] = self.violation_mode
		return dict_

	def set_addressMAC(self, section_status):
		is_mac = re.compile(r'.+\(bia (.+)\)')
		for line in section_status:
			match_mac = re.match(is_mac, line)
			if match_mac:
				self.mac = match_mac.group(1)

	def set_listFoundMAC(self, listFoundMAC):
		self.list_foundMAC = listFoundMAC

	def set_connected(self, section_status):
		is_connected = re.compile(r'.+\((.*connect.*)\)')
		for line in section_status:
			match_connected = re.match(is_connected, line)
			if match_connected:
				if match_connected.group(1) == 'connected':
					self.connected = True
				elif match_connected.group(1) == 'noconnect':
					self.connected = False

	def set_count_vlanTotal(self, count_vlanTotal):
		self.count_vlanTotal = count_vlanTotal

	def format_name(self):
		if 'tengigabitethernet' in self.if_name:
			self.if_name = self.if_name.replace('tengigabitethernet', 'te')
			#self.speed = 10000
		elif 'gigabitethernet' in self.if_name:
			self.if_name = self.if_name.replace('gigabitethernet', 'gi')
			#self.speed = 1000
		elif 'fastethernet':
			self.if_name = self.if_name.replace('fastethernet', 'fa')
			#self.speed = 100

	def set_portSecurity_agingTime(self, line):
		is_portSecurity_agingTime = re.compile(r'switchport port-security aging time (\d+)')
		match_portSecurity_agingTime = re.match(is_portSecurity_agingTime, line)
		if match_portSecurity_agingTime:
			self.port_security_maximum = int(match_portSecurity_agingTime.group(1))

	def set_portSecurity_agingType(self, line):
		is_portSecurity_agingType = re.compile(r'switchport port-security aging type (.+)')
		match_portSecurity_agingType = re.match(is_portSecurity_agingType, line)
		if match_portSecurity_agingType:
			self.aging_type = match_portSecurity_agingType.group(1)

	def set_channelGroup(self, line):
		is_channelGroup = re.compile(r'channel-group (\d+) mode (?:on|active)')
		match_channelGroup = re.match(is_channelGroup, line)
		if match_channelGroup:
			self.channel_group = int(match_channelGroup.group(1))

	def set_duplex(self, line):
		is_duplex = re.compile(r'duplex (.+)')
		match_duplex = re.match(is_duplex, line)
		if match_duplex:
			self.duplex = match_duplex.group(1)

	def set_enabled(self, line):
		if line == 'shutdown':
			self.enabled = False

	def set_poe(self, line):
		if line == 'power inline never':
			self.poe_enabled = False

	def set_portSecurity_maximum(self, line):
		is_portSecurity_maximum = re.compile(r'switchport port-security maximum (\d+)')
		match_portSecurity_maximum = re.match(is_portSecurity_maximum, line)
		if match_portSecurity_maximum:
			self.port_security_maximum = int(match_portSecurity_maximum.group(1))

	def set_portSecurity_mode(self, line):
		if line == 'switchport port-security':
			self.port_security_mode = 'dynamic'
		elif line == 'switchport port-security mac-address sticky':
			self.port_security_mode = 'sticky'

	def set_speed(self, line):
		is_speed = re.compile(r'speed (.+)')
		match_speed = re.match(is_speed, line)
		if match_speed and 'auto' not in match_speed.group(1):
			self.speed = int(match_speed.group(1))

	def set_bpduFilter(self, line):
		is_bpduFilter = re.compile(r'spanning-tree bpdufilter (.+)')
		match_bpduFilter = re.match(is_bpduFilter, line)
		if match_bpduFilter:
			self.stp_bpdufilter = match_bpduFilter.group(1)

	def set_bpduGuard(self, line):
		is_bpduGuard = re.compile(r'spanning-tree bpduguard (.+)')
		match_bpduGuard = re.match(is_bpduGuard, line)
		if match_bpduGuard:
			self.stp_bpduguard = match_bpduGuard.group(1)

	def set_guardLoop(self, line):
		if line.startswith('spanning-tree guard loop'):
			self.stp_guardloop = True

	def set_portfast(self, line):
		if line.startswith('spanning-tree portfast'):
			self.stp_portfast = True

	def set_switchport(self, line):
		if line == 'no switchport':
			self.switchport = False

	def set_portSecurity_violation(self, line):
		is_portSecurity_violation = re.compile(r'switchport port-security violation (.+)')
		match_portSecurity_violation = re.match(is_portSecurity_violation, line)
		if match_portSecurity_violation:
			self.violation_mode = match_portSecurity_violation.group(1)
