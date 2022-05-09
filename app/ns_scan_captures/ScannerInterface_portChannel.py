from .ScannerInterface import ScannerInterface

class ScannerInterface_portChannel(ScannerInterface):
	def __init__(self, section):
		try:
			ScannerInterface.__init__(self, section)
		except:
			super().__init__(section)
		self.count_vlanTotal = 0
		self.channel_id = int(self.if_name.strip().split('port-channel')[1])
		self.if_name = 'po' + str(self.channel_id)
		self.list_foundMAC = []
		for line in section:
			line = line.lower().strip()
			self.set_accessVLAN(line)
			self.set_trunkNativeVLAN(line)
			self.set_voiceVLAN(line)
			self.set_listTrunkVLAN(line)
		self.set_nativeVLAN()

	def get_dict(self):
		try:
			dict_ = ScannerInterface.get_dict(self)
		except:
			dict_ = super().get_dict()
		dict_['list_foundMAC'] = self.list_foundMAC
		#dict_['count_vlanTotal'] = self.count_vlanTotal
		dict_['channel_id'] = self.channel_id
		dict_['native_id'] = self.native_vlan
		dict_['trunk_count'] = self.trunk_count
		dict_['trunk_native_vlan'] = self.trunk_native_vlan
		dict_['trunk_list'] = self.trunk_list
		dict_['voice_vlan'] = self.voice_vlan
		dict_['access_vlan'] = self.access_vlan
		return dict_
	
	def set_count_vlanTotal(self, count_vlanTotal):
		self.count_vlanTotal = count_vlanTotal
