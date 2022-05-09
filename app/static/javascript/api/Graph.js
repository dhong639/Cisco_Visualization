class Graph {
	/*
		constructor
		input:
			dict_devices		dict	general information regarding devices
			dict_edgeFabric		dict	neighbors of a given device
		function
			map all tor device ids to a site id
			map fabric dictionary into dictionary of weighted edges
	*/
	constructor(dict_devices, dict_edgeFabric, dict_edgeOther, dict_details) {
		/*
			all edges in graphs
			each value is a source_id with a set containing target_id
		*/
		this.edges = {}
		/*
			weights of all edges
			each value is a source_id with a number of dictionaries with target_id and weight
		*/
		this.weights = {}
		/*
			sites with router uplinks that can't be used
				added and removed on user discretion
		*/
		this.set_site_ignore = new Set()
		/*
			each site contains a number of tors
			string to set of strings mapping
			each tor is a potential starting/ending point for a site-to-site path
		*/
		this.site2tor = {}
		/*
			each site can contain a number of unmanaged devices
			there are two kinds of unmanaged devices:
				other	any layer 2 unmanaged device
				router	if no longer managed, all layer 3 switche are treated as routers
						used to determine gateway sites
			if a device on a path is within the total set of unmanaged devices,
			where total set is the union of 'other' and 'router',
			when calculating paths, that path weight is increased to Infinity

		*/
		this.site2unmanaged = {}

		/*
			counts number of layer3 uplinks in a site
			a gateway is a site with at least one layer3 uplink
				if a layer3 switch is unmanaged, it may create a new gateway site
				if a layer3 switch is managed, it may remove a gateway site
		*/
		this.site2countLayer3 = {}

		/*
			count_nodes is number of devices on the network provided by customer
			used to increase weight of links to routers for path calculation purposes
		*/
		this.count_nodes = 0

		for(var site_id in dict_devices) {
			if(site_id in this.site2tor == false) {
				this.site2tor[site_id] = new Set()
			} 
			if(site_id in this.site2unmanaged == false) {
				this.site2unmanaged[site_id] = {
					'router': new Set(),
					'other': new Set()
				}
			}
			if(site_id in this.site2countLayer3 == false) {
				this.site2countLayer3[site_id] = 0
			}
			for(var device_id in dict_devices[site_id]) {
				// increment number of nodes in graph
				this.count_nodes += 1
				// add to tors in site if device is a tor
				if(dict_devices[site_id][device_id]['is_tor']) {
					this.site2tor[site_id].add(device_id)
				}
				// increment count of unmanaged devices
				//		if "is_router" is true, add device as router
				//		otherwise, add device as other
				if(dict_devices[site_id][device_id]['is_managed'] == false) {
					if(dict_devices[site_id][device_id]['is_router'] == true) {
						this.site2unmanaged[site_id]['router'].add(device_id)
						this.site2countLayer3[site_id] += 1
					}
					else {
						this.site2unmanaged[site_id]['other'].add(device_id)
					}
				}
				// add routers links in non-fabric edge links to set of routers in site
				if(device_id in dict_edgeOther) {
					dict_edgeOther[device_id]['layer3'].forEach(port_id => {
						this.site2countLayer3[site_id] += 1
					})
				}
				/*
					get edges in fabric topology
						routers will never be a source_id
						routers may be a target_id
					edges are added bidirectionally regardless
					adding edges here instead of separate loop allows keying routers by sites
				*/
				if(device_id in dict_edgeFabric) {
					
					/*if(this.site2router[site_id].has(device_id)) {
						weight = this.count_nodes
					}*/
					for(var target_id in dict_edgeFabric[device_id]) {
						var weight = 1 / dict_edgeFabric[device_id][target_id]['pairs'].length
						/*if(this.site2router[site_id].has(target_id)) {
							weight = this.count_nodes
						}*/
						this.add_edge(device_id, target_id, weight)
					}
				}
			}
		}
		dict_details['list_site_ignored'].forEach(site => {
			if(site in this.site2countLayer3 && this.site2countLayer3[site] > 0) {
				this.add_site_ignore(site)
			}
		})
	}

	/*
		get_list_site_gateway
			output:
				list_site	list	list of sites that are gateway and not ignored
			function: 
				return all sites with at least one layer3 uplink that are not ignored
	*/
	get_list_site_gateway() {
		var list_site = []
		for(var site_id in this.site2countLayer3) {
			var count = this.site2countLayer3[site_id]
			if(count && this.set_site_ignore.has(site_id) == false) {
				list_site.push(site_id)
			}
		}
		list_site.sort()
		return list_site
	}
	/*
		get_list_site_ignored
			output: 
				list_site	list	list of sites that are gateway and ignored
			function: 
				return all sites with at least one layer3 uplink that are ignored
	*/
	get_list_site_ignored() {
		var list_site = Array.from(this.set_site_ignore)
		//console.log(list_site)
		//console.log(list_site)
		list_site.sort()
		return list_site
	}
	/*
		get_list_site_noRoute
			output:
				list_site	site	list of sites that are not gateways or ignored
			function: 
				return all sites without any layer3 uplinks
	*/
	get_list_site_noRoute() {
		var list_site = []
		for(var site_id in this.site2countLayer3) {
			var count = this.site2countLayer3[site_id]
			if(count == 0 || this.set_site_ignore.has(site_id)) {
				list_site.push(site_id)
			}
		}
		list_site.sort()
		return list_site
	}

	/*
		add_site_ignore
			input: 
				site_id		string	name of site
			function: 
				check if site_id has at least one router uplink
					if yes, site_id is now ignored when calculating service uplink paths
				sites without router uplinks are ignored
	*/
	add_site_ignore(site_id) {
		if(this.site2countLayer3[site_id] > 0) {
			this.set_site_ignore.add(site_id)
		}
	}
	/*
		add_site_ignore
			input: 
				site_id		string	name of site
			function: 
				check if site_id has at least one router uplink
					site can now be used for calculating service paths
				sites without router uplinks are ignored
	*/
	del_site_ignore(site_id) {
		if(this.site2countLayer3[site_id] > 0) {
			this.set_site_ignore.delete(site_id)
		}
	}
	/*
		add_unmanaged
			input:
				site_id		string	name of site
				device_id	string	name of device
			function: 
				Graph will treat device as unmanaged
				edges with input devices are weighted as infinity (unreachable)
				if layer 3, used to determine potential gateway sites
	*/
	add_unmanaged(site_id, device_id) {
		if(dict_devices[site_id][device_id]['is_layer3'] == true) {
			this.site2unmanaged[site_id]['router'].add(device_id)
			this.site2countLayer3[site_id] += 1
		}
		else {
			this.site2unmanaged[site_id]['other'].add(device_id)
		}
	}
	/*
		del_unmanaged
			input:
				site_id		string	name of site
				device_id	string	name of device
			function: 
				Graph will treat device as managed
				edges with devices are treated normally
	*/
	del_unmanaged(site_id, device_id) {
		if(this.site2unmanaged[site_id]['router'].has(device_id)) {
			this.site2unmanaged[site_id]['router'].delete(device_id)
			this.site2countLayer3[site_id] -= 1
		}
		else if (this.site2unmanaged[site_id]['other'].has(device_id)){
			this.site2unmanaged[site_id]['other'].delete(device_id)
		}
	}
	/*
		add_tor
			input:
				site_id		string	name of site
				tor_id		string	name of tor
			function: 
				add tor to given site
				if tor was previously a router
					remove from set of routers
					reduce count of routers for given site
					reduce weight of associated links
	*/
	add_tor(site_id, tor_id) {
		this.site2tor[site_id].add(tor_id)
		for(var target_id in this.weights[tor_id]) {
			this.weights[tor_id][target_id] = 1
		}
		for(var source_id in this.weights) {
			if(tor_id in this.weights[source_id]) {
				this.weights[source_id][tor_id] = 1
			}
		}
	}
	/*
		del_tor
			input:
				site_id		string	name of site
				tor_id		string	name of tor
			function: 
				remove tor stored in given site
	*/
	del_tor(site_id, tor_id) {
		this.site2tor[site_id].delete(tor_id)
	}
	/*
		get_path_site2gateway
			input: 
				source_site		string	name of starting site, site has no routers
			output:
				shortest_path	list	all nodes to get from source to target site
			function: 
				get path from site with no routers to site with at least one router
				get every path from every tor between a source and target site
				return shortest of those paths
	*/
	get_path_site2gateway(source_site) {
		/*
			under these conditions, return null and stop processing
				site contains at least one router uplink
				site has not been deliberately ignored by user
		*/
		// remember shortest path
		var shortest_path = []
		var shortest_length = Number.MAX_SAFE_INTEGER
		// ge list of tor in source site
		var list_sourceTOR = Array.from(this.site2tor[source_site])
		// get list of target sites
		var list_targetSite = []
		for(var target_site in this.site2countLayer3) {
			if(target_site != source_site) {
				var count = this.site2countLayer3[target_site]
				if(count && this.set_site_ignore.has(target_site) == false) {
					list_targetSite.push(target_site)
				}
			}
		}
		//console.log(list_targetSite)
		list_sourceTOR.forEach(source_tor => {
			list_targetSite.forEach(target_site => {
				// get list of tor in current target site
				var list_targetTOR = Array.from(this.site2tor[target_site])
				list_targetTOR.forEach(target_tor => {
					var path = this.helper_dijkstra(source_tor, target_tor)
					if(path != null && path.length < shortest_length) {
						shortest_path = path
						shortest_length = path.length
					}
				})
			})
		})
		//console.log(shortest_path)
		return shortest_path
	}
	/*
		add_edge
			input: 
				source_id	string	starting end of edge
				target_id	string	ending point of edge
				weight		int		likelihood of using link (increase weight for routers)
			function: 
				for each edge in dict_edgeFabric, add edge to this.edges
				all links are considered bidirectional
				must also add links for routers in case removing router breaks graph
					in the case that there is a link to a router, increase the weight of that link
					note that edges are immutable
	*/
	add_edge(source_id, target_id, weight) {
		// set source edges
		if(source_id in this.edges == false) {
			this.edges[source_id] = []
		}
		if(this.edges[source_id].includes(target_id) == false) {
			this.edges[source_id].push(target_id)
		}
		// set target edges
		if(target_id in this.edges == false) {
			this.edges[target_id] = []
		}
		if(this.edges[target_id].includes(source_id) == false) {
			this.edges[target_id].push(source_id)
		}
		// set source to target weight
		if(source_id in this.weights == false) {
			this.weights[source_id] = {}
		}
		this.weights[source_id][target_id] = weight
		//set target to source weight
		if(target_id in this.weights == false) {
			this.weights[target_id] = {}
		}
		this.weights[target_id][source_id] = weight
	}
	/*
		helper_dijkstra
			input:
				initial		string	starting node
				end			string	ending node
			output:
				path		list	nodes between initial and end, inclusive, in order
			function: 
				record shortest path of next-hops to get from initial to end
				meant to only be used to get between TORs
	*/
	helper_dijkstra(initial, end) {
		var set_unmanaged = new Set()
		for(var site_id in this.site2unmanaged) {
			this.site2unmanaged[site_id]['router'].forEach(device_id => {
				set_unmanaged.add(device_id)
			})
			this.site2unmanaged[site_id]['other'].forEach(device_id => {
				set_unmanaged.add(device_id)
			})
		}
		//console.log('unmanaged devices')
		//console.log(set_unmanaged)
		var shortest_paths = {}
		shortest_paths[initial] = [null, 0]
		var current_node = initial
		var visited = new Set()

		while(current_node != end) {
			visited.add(current_node)
			var destinations = []
			if(current_node in this.edges) {
				destinations = this.edges[current_node]
			}
			var weight_to_current_node = shortest_paths[current_node][1]
			
			destinations.forEach(next_node => {
				var weight = this.weights[current_node][next_node] + weight_to_current_node
				if(set_unmanaged.has(current_node) || set_unmanaged.has(next_node)) {
					weight = this.count_nodes
				}
				if(next_node in shortest_paths == false) {
					shortest_paths[next_node] = [current_node, weight]
				} else {
					var current_shortest_weight = shortest_paths[next_node][1]
					if(current_shortest_weight > weight) {
						shortest_paths[next_node] = [current_node, weight]
					}
				}
			})

			var next_destinations = {}
			for(var node in shortest_paths) {
				if(visited.has(node) == false) {
					next_destinations[node] = shortest_paths[node]
				}
			}
			if(Object.keys(next_destinations).length == 0) {
				return null
			}
			var lowest_weight = Number.MAX_SAFE_INTEGER
			for(var key in next_destinations) {
				var node = next_destinations[key]
				var weight = node[1]
				if(weight < lowest_weight) {
					lowest_weight = weight
					current_node = key
				}
			}
		}
		var path = []
		while(current_node != null) {
			var next_node = shortest_paths[current_node][0]
			path.unshift(current_node)
			current_node = next_node
		}
		var flag_noUnmanaged = true
		path.forEach(device_id => {
			if(set_unmanaged.has(device_id)) {
				flag_noUnmanaged = false
			}
		})
		if(flag_noUnmanaged) {
			return path
		}
		else {
			return null
		}
	}
}