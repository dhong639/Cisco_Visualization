import re
from .ScannerInterface_portChannel import ScannerInterface_portChannel
from .ScannerInterface_vlan import ScannerInterface_vlan
from .ScannerInterface_interface import ScannerInterface_interface

class ScannerDevice:
	def __init__(self, sections):
		section_run = sections['running-config']
		section_lacp = sections['lacp sys-id']
		section_intfRun = sections['interface config']
		section_intfStatus = sections['interface | inc Ethernet|Vlan']
		section_foundVLAN_unique = {}
		if 'unique vlans found' in sections:
			section_foundVLAN_unique = sections['unique vlans found']
		section_vlanTotal = {}
		if 'total vlans found' in sections:
			section_vlanTotal = sections['total vlans found']
		self.access_only = False
		self.chassis_id = None
		self.community_string = None
		self.count_vlanTotal = 0
		self.domain_name = None
		self.expected_parent_id = None
		self.expected_parent_intf = None
		self.hostname = None
		self.hw_model = None
		self.ip_address = sections['ip_address']
		self.is_layer3 = False
		self.is_managed = True
		self.is_router = False
		self.is_tor = False
		self.ivn_port = {}
		self.location = sections['location']
		self.lldp_enabled = False
		self.mgmt_vlan = None
		self.mgmt_vlan_native = False
		self.port_channels = {}
		self.port_count = 0
		self.site_id = sections['site_id']
		self.spt_mode = None
		self.vlans = {}
		self.set_byRun(section_run)
		self.set_byLACP(section_lacp)

		for data in section_intfRun['vlan']:
			scanner_vlan = ScannerInterface_vlan(data)
			vlan_id = scanner_vlan.get_vlanID()
			if scanner_vlan.get_addressIP() == self.ip_address:
				self.mgmt_vlan = scanner_vlan.get_vlanID()
			self.vlans[vlan_id] = scanner_vlan.get_dict()
		for data in section_intfRun['port-channel']:
			scanner_portChannel = ScannerInterface_portChannel(data)
			name = scanner_portChannel.get_name()
			if name in section_foundVLAN_unique:
				scanner_portChannel.set_listFoundMAC(section_foundVLAN_unique[name])
			if name in section_vlanTotal:
				scanner_portChannel.set_count_vlanTotal(section_vlanTotal[name])
				self.count_vlanTotal += section_vlanTotal[name]
			self.port_channels[name] = scanner_portChannel.get_dict()
		for i in range(len(section_intfRun['ethernet'])):
			data = section_intfRun['ethernet'][i]
			scanner_interface = ScannerInterface_interface(data, i+1)
			name = scanner_interface.get_name()
			if name in section_intfStatus:
				scanner_interface.set_connected(section_intfStatus[name])
				scanner_interface.set_addressMAC(section_intfStatus[name])
			if name in section_foundVLAN_unique:
				scanner_interface.set_listFoundMAC(section_foundVLAN_unique[name])
			if name in section_vlanTotal:
				scanner_interface.set_count_vlanTotal(section_vlanTotal[name])
				self.count_vlanTotal += section_vlanTotal[name]
			if self.mgmt_vlan != None and self.mgmt_vlan == scanner_interface.get_nativeVLAN():
				self.mgmt_vlan_native = True
			self.ivn_port[name] = scanner_interface.get_dict()
		self.port_count = len(self.ivn_port)
		self.set_isRouter()

	def get_deviceID(self):
		return self.hostname

	def get_siteID(self):
		return self.site_id

	def get_count_vlanTotal(self):
		return self.count_vlanTotal
	
	def get_layer3(self):
		return self.is_layer3

	def get_dictPreview_interface(self):
		dict_ = {}
		for interface_id in self.ivn_port:
			interface = self.ivn_port[interface_id]
			if_name = interface['if_name']
			port_number = interface['port_number']
			trunk_list = interface['trunk_list']
			access_vlan = interface['access_vlan']
			voice_vlan = interface['voice_vlan']
			list_foundMAC = interface['list_foundMAC']
			channel_group = interface['channel_group']
			connected = interface['connected']
			#is_eth = True if access_vlan != None and connected == True else False
			dict_[if_name] = {
				'if_name': if_name,
				'port_number': port_number,
				'trunk_list':  trunk_list,
				'access_vlan':  access_vlan,
				'voice_vlan':  voice_vlan,
				'list_foundMAC':  list_foundMAC,
				'channel_group':  channel_group,
				'connected': connected,
				#'is_eth': is_eth
			}
		return dict_

	def get_dictPreview_device(self):
		dict_ = {
				'hostname': self.hostname,
				'is_router': self.is_router,
				'chassis_id': self.chassis_id,
				'is_tor': self.is_tor,
				'domain_name': self.domain_name,
				'ip_address': self.ip_address,
				'community_string': self.community_string,
				'is_layer3': self.is_layer3,
				'location': self.location,
				'is_managed': self.is_managed,
			}
		return dict_

	def get_dict(self):
		dict_ = {
			'access_only': self.access_only,
			'chassis_id': self.chassis_id,
			'community_string': self.community_string,
			'count_vlanTotal': self.count_vlanTotal,
			'domain_name': self.domain_name,
			'expected_parent_id': self.expected_parent_id,
			'expected_parent_intf': self.expected_parent_intf,
			'hostname': self.hostname,
			'hw_model': self.hw_model,
			'ip_address': self.ip_address,
			'is_layer3': self.is_layer3,
			'is_managed': self.is_managed,
			'is_router': self.is_router,
			'is_tor': self.is_tor,
			'ivn_port': self.ivn_port,
			'lldp_enabled': self.lldp_enabled,
			'mgmt_vlan': self.mgmt_vlan,
			'mgmt_vlan_native': self.mgmt_vlan_native,
			'port_channels': self.port_channels,
			'port_count': self.port_count,
			'site_id': self.site_id,
			'spt_mode': self.spt_mode,
			'vlans': self.vlans
		}
		return dict_

	def set_isTOR(self):
		self.is_tor = True

	def set_byRun(self, section_run):
		is_hostname = re.compile(r'hostname (.+)')
		is_domainName = re.compile(r'ip domain-name (.+)')
		is_sptMode = re.compile(r'spanning-tree mode (.+)')
		is_snmpCommunityRO = re.compile(r'snmp-server community (.+) RO')
		is_snmpCommunityRW = re.compile(r'snmp-server community (.+) RW')
		for line in section_run:
			match_hostname = re.match(is_hostname, line.strip())
			if match_hostname:
				self.hostname = match_hostname.group(1)
				if 'core' in self.hostname.lower():
					self.is_tor = True
			match_domainName = re.match(is_domainName, line.strip())
			if match_domainName:
				self.domain_name = match_domainName.group(1)
			if 'lldp run' in line.strip().lower():
				self.lldp_enabled = True
			match_sptMode = re.match(is_sptMode, line.lower().strip())
			if match_sptMode:
				self.spt_mode = match_sptMode.group(1)
			if line.lower().strip().startswith('ip route'):
				self.is_layer3 = True
			match_snmpCommunityRO = re.match(is_snmpCommunityRO, line.strip())
			if match_snmpCommunityRO:
				self.community_string = match_snmpCommunityRO.group(1)
			match_snmpCommunityRW = re.match(is_snmpCommunityRW, line.strip())
			if match_snmpCommunityRW:
				self.community_string = match_snmpCommunityRW.group(1)

	def set_byLACP(self, section_lacp):
		is_chassisID = re.compile(r'\d+,\s*(.+)')
		for line in section_lacp:
			match_chassisID = re.match(is_chassisID, line.strip())
			if match_chassisID:
				self.chassis_id = match_chassisID.group(1)

	def set_byHardware(self, hardware):
		if hardware != None:
			self.site_id = hardware['site_id']
			self.ip_address = hardware['ip_address']
			self.location = hardware['location']
	
	def set_isRouter(self):
		count_vlan = 0
		for port_id in self.ivn_port:
			count_vlan += len(self.ivn_port[port_id]['list_foundMAC'])
		for channel_id in self.port_channels:
			count_vlan += len(self.port_channels[channel_id]['list_foundMAC'])
		if count_vlan == 0 and self.is_layer3 == True:
			self.is_router = True
			self.is_managed = False
