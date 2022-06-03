class Graph:
	def __init__(self, count, set_siteGateway, dict_site2device, dict_edgeFabric, dict_edgeOther):
		# device information, group key devices by site
		self.count = count
		self.dict_device2site = {}
		self.dict_site2device = dict_site2device
		self.set_unmanaged_all = set()
		self.set_unmanaged_layer3 = set()
		self.set_unmanaged_other = set()
		# represents all unmanaged devices
		# assumes site-independent hostnames
		for site_id in dict_site2device:
			set_router = dict_site2device[site_id]['list_unmanaged']['router']
			set_other = dict_site2device[site_id]['list_unmanaged']['other']
			self.set_unmanaged_all = self.set_unmanaged_all.union(set_router)
			self.set_unmanaged_all = self.set_unmanaged_all.union(set_other)
			self.set_unmanaged_layer3 = self.set_unmanaged_layer3.union(set_router)
			self.set_unmanaged_other = self.set_unmanaged_other.union(set_other)


		# site information, determine source and target sites
		self.set_siteGateway = set_siteGateway
		self.set_siteNoRoute = set()
		for site_id in dict_site2device:
			if site_id not in set_siteGateway:
				self.set_siteNoRoute.add(site_id)

		# connections between devices, already determined in ScannerNeighbor
		self.dict_edgeFabric = dict_edgeFabric
		self.dict_edgeOther = dict_edgeOther

		# set weights dependent on how many links are between each source/target pair
		self.dict_weights = {source_id: {} for source_id in dict_edgeFabric}
		for source_id in dict_edgeFabric:
			for target_id in dict_edgeFabric[source_id]:
				len_pairs = len(dict_edgeFabric[source_id][target_id]['pairs'])
				self.dict_weights[source_id][target_id] = 1 / len_pairs

	def get_targetsTOR(self, tor_id):
		dict_targetsTOR = {}
		for device_id in self.dict_edgeFabric[tor_id]:
			if device_id not in dict_targetsTOR:
				dict_targetsTOR[device_id] = []
			for pair in self.dict_edgeFabric[tor_id][device_id]['pairs']:
				dict_targetsTOR[device_id].append(pair)
		return dict_targetsTOR

	def get_pairs_fabric(self, source_id, target_id):
		if source_id in self.set_unmanaged_all or target_id in self.set_unmanaged_all:
			return None
		if source_id not in self.dict_edgeFabric:
			return None
		if target_id not in self.dict_edgeFabric[source_id]:
			return None
		return self.dict_edgeFabric[source_id][target_id]['pairs']

	def get_intf_eth(self, device_id):
		if device_id in self.set_unmanaged_all:
			return None
		if device_id not in self.dict_edgeOther:
			return None
		list_eth = [port[1] for port in self.dict_edgeOther[device_id]['eth_port']]
		print(device_id)
		print(list_eth)
		if device_id in self.dict_edgeFabric:
			for target_id in self.dict_edgeFabric[device_id]:
				if target_id in self.set_unmanaged_other:
					list_eth.append(target_id)
		return list_eth

	def get_intf_layer3(self, device_id):
		if device_id in self.set_unmanaged_all:
			return None
		if device_id not in self.dict_edgeOther:
			return None
		list_layer3 = [port[1] for port in self.dict_edgeOther[device_id]['layer3']]
		if device_id in self.dict_edgeFabric:
			for target_id in self.dict_edgeFabric[device_id]:
				if target_id in self.set_unmanaged_other:
					list_layer3.append(target_id)
		return list_layer3

	def path_toTOR(self, site_id, device_id):
		shortest_path = []
		min_length = float('inf')
		if device_id in self.dict_site2device[site_id]['list_tor']:
			return None
		for tor_id in self.dict_site2device[site_id]['list_tor']:
			path = self.helper_dijkstra(device_id, tor_id)
			if path != None and len(path) < min_length:
				min_length = len(path)
				shortest_path = path
		return shortest_path

	def path_toGateway(self, site_id):
		shortest_path = []
		min_length = float('inf')
		if site_id in self.set_siteGateway:
			return None
		list_source_tor = self.dict_site2device[site_id]['list_tor']
		for source_id in list_source_tor:
			for gateway in self.set_siteGateway:
				list_target_tor = self.dict_site2device[gateway]['list_tor']
				for target_id in list_target_tor:
					path = self.helper_dijkstra(source_id, target_id)
					if path != None and len(path) < min_length:
						min_length = len(path)
						shortest_path = path
		return shortest_path

	def helper_dijkstra(self, initial, end):
		if initial not in self.dict_edgeFabric:
			return None
		shortest_paths = {}
		shortest_paths[initial] = [None, 0]
		current_node = initial
		visited = set()

		while current_node != end:

			visited.add(current_node)
			destinations = self.dict_edgeFabric[current_node].keys()
			weight_to_current_node = shortest_paths[current_node][1]

			for next_node in destinations:
				weight = self.dict_weights[current_node][next_node] + weight_to_current_node
				if current_node in self.set_unmanaged_all or next_node in self.set_unmanaged_all:
					# maximum number of edges in a graph
					weight = self.count * (self.count - 1) / 2
				if next_node not in shortest_paths:
					shortest_paths[next_node] = [current_node, weight]
				else:
					current_shortestWeight = shortest_paths[next_node][1]
					if current_shortestWeight > weight:
						shortest_paths[next_node] = [current_node, weight]

			next_destinations = {}
			for node in shortest_paths:
				if node not in visited:
					next_destinations[node] = shortest_paths[node]

			if len(next_destinations.keys()) == 0:
				return None

			lowestWeight = float('inf')
			for key in next_destinations:
				node = next_destinations[key]
				weight = node[1]
				if weight < lowestWeight:
					lowestWeight = weight
					current_node = key

		path = []
		while current_node != None:
			next_node = shortest_paths[current_node][0]
			path.insert(0, current_node)
			current_node = next_node
		return path
