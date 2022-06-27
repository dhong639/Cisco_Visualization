class Graph {
	constructor(dict_devices, dict_edgeFabric, dict_edgeOther, dict_details) {
		this.site2device = {}
		for(var site_id in dict_devices) {
			this.site2device[site_id] = {}
			for(var device_id in dict_devices[site_id]) {
				this.site2device[site_id][device_id] = {
					is_tor: dict_devices[site_id][device_id]['is_tor'],
					is_router: dict_devices[site_id][device_id]['is_router']
				}
			}
		}
		this.edges = {}
		for(var source in dict_edgeFabric) {
			var site_source = this.get_deviceSite(source)
			if(source in this.edges == false) {
				this.edges[source] = {}
			}
			for(var target in dict_edgeFabric[source]) {
				var site_target = this.get_deviceSite(target)
				if(target in this.edges == false) {
					this.edges[target] = {}
				}
				var is_sourceLayer3 = this.site2device[site_source][source].is_router
				var is_targetLayer3 = this.site2device[site_target][target].is_router
				var is_router = is_sourceLayer3 || is_targetLayer3 ? true : false
				if(this.site2device)
				this.edges[source][target] = {
					'is_intra': false,
					'is_router': is_router
				}
				this.edges[target][source] = {
					'is_intra': false,
					'is_router': is_router
				}
			}
		}
		for(var site_id in this.site2device) {
			this.breadth_first(site_id)
		}
	}
	get_deviceSite(device_id) {
		var output = null
		for(var site_id in this.site2device) {
			if(device_id in this.site2device[site_id]) {
				output = site_id
				break
			}
		}
		return output
	}
	breadth_first(site_id) {
		var visited = new Set()
		var nodes_curr = new Set()
		var nodes_next = new Set()
		for(var device_id in this.site2device[site_id]) {
			if(this.site2device[site_id][device_id].is_tor == true) {
				nodes_curr.add(device_id)
			}
		}
		console.log(site_id)
		console.log(nodes_curr)
		while(nodes_curr.size > 0) {
			nodes_curr.forEach(node => {
				visited.add(node)
			})
			console.log('\t' + Array.from(nodes_curr).join(', '))
			nodes_curr.forEach(west => {
				nodes_curr.forEach(east => {
					var is_west = west in this.edges && east in this.edges[west]
					var is_east = east in this.edges && west in this.edges[east]
					if(is_west && is_east) {
						console.log('\t\tintra-site\t' + west + '\t' + east)
						this.edges[west][east]['is_intra'] = true
						this.edges[east][west]['is_intra'] = true
					}
				})
			})
			nodes_curr.forEach(parent => {
				for(var child in this.edges[parent]) {
					if(child in this.site2device[site_id]) {
						if(visited.has(child) == false) {
							visited.add(child)
							nodes_next.add(child)
						}
					}
					else {
						console.log('\t\tinter-site\t' + parent + '\t' + child)
						this.edges[parent][child]['is_intra'] = true
						this.edges[child][parent]['is_intra'] = true
					}
				}
			})
			nodes_curr.clear()
			nodes_next.forEach(node => {
				nodes_curr.add(node)
			})
			nodes_next.clear()
		}
	}
}

exports.Graph = Graph