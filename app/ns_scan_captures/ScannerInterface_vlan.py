from .ScannerInterface import ScannerInterface

class ScannerInterface_vlan(ScannerInterface):
	def __init__(self, section):
		try:
			ScannerInterface.__init__(self, section)
		except:
			super().__init__(section)
		self.vlan_id = int(self.if_name.lower().split('vlan')[1])
		self.ip_address = None
		for line in section:
			line = line.strip().lower()
			self.set_addressIP(line)

	def get_vlanID(self):
		return self.vlan_id

	def get_dict(self):
		try:
			dict_ = ScannerInterface.get_dict(self)
		except:
			dict_ = super().get_dict()
		dict_['vlan_id'] = self.vlan_id
		dict_['ip_address'] = self.ip_address
		return dict_
