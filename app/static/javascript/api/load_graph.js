function invertColor(hexTripletColor) {
	var color = hexTripletColor;
	color = color.substring(1);				// remove #
	color = parseInt(color, 16);			// convert to integer
	color = 0xFFFFFF ^ color;				// invert three bytes
	color = color.toString(16);				// convert to hex
	color = ("000000" + color).slice(-6);	// pad with leading zeros
	color = "#" + color;					// prepend #
	return color;
}

function set_label(site_id, device_id) {
	var selected = document.getElementById('select_nodeLabel').value
	var label = site_id
	if(selected != 'site_id') {
		label = dict_devices[site_id][device_id][selected]
	} 
	var hostname = dict_devices[site_id][device_id]['hostname']
	var string = hostname + '\n'
	for(var i = 0; i<hostname.length; i++) {
		string += '-'
	}
	string = string + '\n' + label
	return string
}

function set_other(type, set_validNodes, cy) {
	var set_node = new Set()
	var set_edge = new Set()
	for(var device_id in dict_edgeOther) {
		if(set_validNodes.has(device_id)) {
			// get list of source interfaces that are fabric
			var set_portFabric = new Set()
			for(var target_id in dict_edgeFabric[device_id]) {
				dict_edgeFabric[device_id][target_id]['pairs'].forEach(pair => {
					set_portFabric.add(pair[0])
				})
			}
			for(var source_intf in dict_edgeOther[device_id][type]) {
				var platform = dict_edgeOther[device_id][type][source_intf]
				if(set_portFabric.has(source_intf) == false) {
					var color = '#FFA500'
					var node_label
					var shape
					if(type == 'eth_port') {
						node_label = 'eth'
						shape = 'ellipse'
					} else if(type == 'layer3') {
						node_label = 'router'
						shape = 'square'
					}
					var edge_id = device_id + '.' + source_intf
					var target_label
					var line_style
					var access_vlan = null
					if(type == 'eth_port') {
						access_vlan = dict_interfaces[device_id][source_intf]['access_vlan']
						edge_id += ' - vlan' + access_vlan
						target_label = 'vlan ' + access_vlan
						line_style = 'solid'
					} else if(type == 'layer3') {
						edge_id += ' - uplink'
						target_label = 'uplink'
						line_style = 'dashed'
					}
					if(type == 'layer3' || (type == 'eth_port' && access_vlan != null)) {
						var node_id = device_id + '.' + source_intf
						if(!set_node.has(node_id)) {
							cy.add({
								data: {
									id: node_id,
									label: platform + '\n' + node_label,
									color_main: color,
									color_invert: invertColor(color),
									shape: shape,
									size: 25
								}
							})
							set_node.add(node_id)
						}
						if(!set_edge.has(edge_id)) {
							cy.add({
								data: {
									id: edge_id,
									source_label: source_intf,
									source: device_id,
									target: node_id,
									target_label: target_label,
									color_main: color,
									color_invert: invertColor(color),
									line_style: line_style
								}
							})
							set_edge.add(edge_id)
						}
					}
				}
			}
		}
	}
}

function load_graph(pending_device, pending_site, set_currentSite, graph) {
	// clear all preview cells for devices
	document.getElementById('pending_add_tor').innerHTML = ''
	document.getElementById('pending_del_tor').innerHTML = ''
	document.getElementById('pending_add_unmanaged').innerHTML = ''
	document.getElementById('pending_del_unmanaged').innerHTML = ''
	document.getElementById('show_editSite').innerHTML = ''
	// clear all preview cells for sites
	document.getElementById('pending_add_gatewaySite').innerHTML = ''
	document.getElementById('pending_del_gatewaySite').innerHTML = ''
	//	clear edit service links
	document.getElementById('pending_uplinkSingle').innerHTML = ''
	document.getElementById('pending_uplinkMultiple').innerHTML = ''
	document.getElementById('pending_removedString').innerHTML = ''
	/*
		get list of sites that to display
			'everything' will display all sites
			'' won't display anything
			all other values displayed as normal
		won't reset the corresponding select option or preview cell
	*/
	var list_validSite = []
	if(set_currentSite.size == 1 && set_currentSite.has('everything')) {
		for(var site_id in dict_devices) {
			list_validSite.push(site_id)
		}
	} else {
		list_validSite = Array.from(set_currentSite)
	}

	// reset edit options for devices
	document.getElementById("select_siteEdit").selectedIndex = "0"; 
	// set pending added tors
	for(var site_id in pending_device.add.tor) {
		pending_device.add.tor[site_id].forEach(device_id => {
			// cannot make an unmanaged device a TOR
			// that wouldn't make sense
			if (dict_devices[site_id][device_id]['is_managed'] == true) {
				dict_devices[site_id][device_id]['is_tor'] = true
				// add tor for calculation of gateway sites
				graph.add_tor(site_id, device_id)
			}
		})
		pending_device.add.tor[site_id].clear()
	}
	fillSelect_addTOR()
	// set pending deleted tors
	for(var site_id in pending_device.del.tor) {
		pending_device.del.tor[site_id].forEach(device_id => {
			dict_devices[site_id][device_id]['is_tor'] = false
			// remove tor when considering gateway sites
			graph.del_tor(site_id, device_id)
		})
		pending_device.del.tor[site_id].clear()
	}
	fillSelect_delTOR()
	// set pending added unmanaged devices
	for(var site_id in pending_device.add.unmanaged) {
		pending_device.add.unmanaged[site_id].forEach(device_id => {
			// cannot remove TORs from managed devices
			// that wouldn't make sense
			if (dict_devices[site_id][device_id]['is_tor'] == false) {
				dict_devices[site_id][device_id]['is_managed'] = false
				graph.add_unmanaged(site_id, device_id)
			}
		})
		pending_device.add.unmanaged[site_id].clear()
	}
	fillSelect_addUnmanaged()
	// set pending removed unmanaged devices
	for(var site_id in pending_device.del.unmanaged) {
		pending_device.del.unmanaged[site_id].forEach(device_id => {
			dict_devices[site_id][device_id]['is_managed'] = true
			graph.del_unmanaged(site_id, device_id)
		})
		pending_device.del.unmanaged[site_id].clear()
	}
	fillSelect_delUnmanaged()


	// apply and reset edits for added gateway sites
	pending_site.add.gateway.forEach(site_id => {
		// remove site from list of ignored gateway sites
		graph.del_site_ignore(site_id)
	})
	pending_site.add.gateway.clear()
	// apply and reset edits for ignored gateway sites
	pending_site.del.gateway.forEach(site_id => {
		// add site to list of ignored gateway sites
		graph.add_site_ignore(site_id)
	})
	pending_site.del.gateway.clear()
	// reset index for gateway site select fields
	document.getElementById('pending_add_gatewaySite').index = '0'
	document.getElementById('pending_del_gatewaySite').index = '0'
	// update results based on graph contents
	fillSelect_addGatewaySite(graph)
	fillSelect_delGatewaySite(graph)

	console.log('gateway sites: ' + graph.get_list_site_gateway())
	console.log('ignored sites: ' + graph.get_list_site_ignored())

	/*
		calculate site-to-site paths for gateway sites
		later on, edge information is saved in the following format: 
			source_id + '.' + pair[0] + ' - ' + target_id + '.' + pair[1]
			target_id + '.' + pair[1] + ' - ' + source_id + '.' + pair[0]
		therefore, create a set containing all of these edge IDs
			if an edge ID generated later on is in this set, color it purple
	*/
	//var list_sourceSite = graph.get_site_noUplink()
	var list_sourceSite = graph.get_list_site_noRoute()
	var set_path2gateway = new Set()
	list_sourceSite.forEach(source_site => {
		//console.log(source_site)
		var path = graph.get_path_site2gateway(source_site)
		for(var i = 0; i < path.length - 1; i++) {
			var source_id = path[i]
			var target_id = path[i + 1]
			var list_pairs = dict_edgeFabric[source_id][target_id]['pairs']
			list_pairs.forEach(pair => {
				var edge_id = source_id + '.' + pair[0] + ' - ' + target_id + '.' + pair[1]
				set_path2gateway.add(edge_id)
				var edge_reverse = target_id + '.' + pair[1] + ' - ' + source_id + '.' + pair[0]
				set_path2gateway.add(edge_reverse)
			})
		}
	})

	/*
		links from fabric devices to TOR are called vertical
		some links are redundant, and these links are horizontal
		horizontal links will be crosslinks (in this case, dashed lines)
	*/
	var dict_vertical = graph.get_dict_vertical()
	console.log(dict_vertical)

	// declare cytoscape object
	var cy = cytoscape({
		container: document.getElementById('cy'),
		wheelSensitivity: 0.1,
		elements: [],
		style: [
			{
				selector: 'node',
				style: {
					'label': 'data(label)',
					'text-wrap': 'wrap',
					'height': 'data(size)',
					'width': 'data(size)',
					'text-valign': 'center',
					'text-halign': 'center',
					'shape': 'data(shape)',
					'background-color': 'data(color_main)',
					'background-opacity': 0.75
				}
			}, 
			{
				selector: 'edge',
				style: {
					'curve-style': 'bezier',
					'source-label': 'data(source_label)',
					'source-text-offset': 50,
					'source-text-rotation': 'autorotate',
					'target-label': 'data(target_label)',
					'target-text-offset': 50,
					'target-text-rotation': 'autorotate',
					'text-wrap': 'wrap',
					//'line-color': 'data(color_main)',
					'line-opacity': 0.5,
					'line-style': 'data(line_style)'
				}
			}, 
			{
				selector: 'node:selected',
				style: {
					'background-color': 'data(color_invert)',
					'line-color': 'data(color_invert)'
				}
			}
		]
	})
	
	// set sizes of nodes
	for(var source_id in dict_edgeFabric) {
		var size = Object.keys(dict_edgeFabric[source_id]).length
		for(var site_id in dict_devices) {
			for(var device_id in dict_devices[site_id]) {
				if(device_id == source_id) {
					dict_devices[site_id][source_id]['size'] = size
				}
			}
		}
	}

	// only create edge if source and target IDs are in the given site
	// store those nodes here
	var set_validNodes = new Set()

	for(var i = 0; i<list_validSite.length; i++) {
		var site_id = list_validSite[i]
		for(var device_id in dict_devices[site_id]) {
			/**
			 * if a string is no longer applicable to search for service uplinks,
			 * it is necessary to remove previously identified service uplinks
			 * this applies to all sites and all devices
			 * if the service_uplink points to null, it's probably not an eth port
			 */
			console.log(pending_removedString)
			if(device_id in dict_edgeOther) {
				var set_layer3_removed = new Set()
				for(var intf_id in dict_edgeOther[device_id]['layer3']) {
					var description = dict_interfaces[device_id][intf_id]['description']
					description = description.toLowerCase()
					pending_removedString.forEach(removedString => {
						console.log(description)
						if(description.includes(removedString)) {
							set_layer3_removed.add(intf_id)
							/**
							 * if possible, try to replace an eth_port if it was removed
							 * will not work if eth_port naturally ports to a null other_id
							 */
							var other_id = dict_edgeOther[device_id]['layer3'][intf_id]
							if(other_id != null) {
								dict_edgeOther[device_id]['eth_port'][intf_id] = other_id
							}
						}
					})
				}
				set_layer3_removed.forEach(intf_id => {
					delete dict_edgeOther[device_id]['layer3'][intf_id]
					pending_serviceUp[device_id].delete(intf_id)
				})
			}
			/**
			 * check if current device has new service uplinks to handle
			 * remove if already set as an eth_port
			 */
			if(device_id in pending_uplinkSingle) {
				if(device_id in dict_edgeOther == false) {
					dict_edgeOther[device_id] = {
						'layer3': {},
						'eth_port': {}
					}
				}
				pending_uplinkSingle[device_id].forEach(intf_id => {
					var other_id = null
					if(intf_id in dict_edgeOther[device_id]['eth_port']) {
						other_id = dict_edgeOther[device_id]['eth_port'][intf_id]
						delete dict_edgeOther[device_id]['eth_port'][intf_id]
					}
					dict_edgeOther[device_id]['layer3'][intf_id] = other_id
					if(device_id in pending_serviceUp == false) {
						pending_serviceUp[device_id] = new Set()
					}
					pending_serviceUp[device_id].add(intf_id)
				})
			}
			/**
			 *	check if current site has a string to search through
			 *	check every non-fabric interface description for string
			 *		ignore for ports that are fabric, check dict_edgesOther
			 *		no need to check layer3 ports
			 *		applicable eth ports removed afterwards
			 *	check description in dict_interfaces of port for string, lowercase
			 */
			if(site_id in pending_uplinkMultiple) {
				if(device_id in dict_edgeOther == false) {
					dict_edgeOther[device_id] = {
						'layer3': new Set(),
						'eth_port': new Set()
					}
				}
				var set_intf = new Set()
				pending_uplinkMultiple[site_id].forEach(string => {
					string = string.toLowerCase()
					console.log(string)
					for(var intf_id in dict_interfaces[device_id]) {
						var flag = false
						//	avoid fabric edges
						for(var target_id in dict_edgeFabric[device_id]) {
							dict_edgeFabric[device_id][target_id]['pairs'].forEach(pair => {
								if(pair[0] == intf_id) {
									flag = true
								}
							})
						}
						if(flag == false) {
							//	search description string for occurence of string
							var description = dict_interfaces[device_id][intf_id]['description']
							if(description != null && description.toLowerCase().includes(string)) {
								set_intf.add(intf_id)
							}
						}
					}
				})
				/**
				 * may be necessary to remove service uplinks first
				 * if user decides that a search string is inapplicable,
				 * the change would not be reflected
				 * instead, what's happening is that there is a set of revoked search strings,
				 * and anything in the set cannot be considered a service up
				 */
				set_intf.forEach(intf_id => {
					var other_id = null
					if(intf_id in dict_edgeOther[device_id]['eth_port']) {
						other_id = dict_edgeOther[device_id]['eth_port'][intf_id]
						delete dict_edgeOther[device_id]['eth_port'][intf_id]
					}
					dict_edgeOther[device_id]['layer3'][intf_id] = other_id
					if(device_id in pending_serviceUp == false) {
						pending_serviceUp[device_id] = new Set()
					}
					pending_serviceUp[device_id].add(intf_id)
				})
			}
			
			//	start setting cytoscape content
			set_validNodes.add(device_id)
			var device = dict_devices[site_id][device_id]
			var hostname = device['hostname']
			var is_router = device['is_router']
			var is_tor = device['is_tor']
			var is_managed = device['is_managed']
			var is_layer3 = device['is_layer3']
			var shape = 'ellipse'
			if(is_tor == true) {
				shape = 'star'
			} else if(is_router || (!is_managed && is_layer3)) {
				shape = 'square'
			}
			var is_layer3 = device['is_layer3']
			//var color = 'yellowgreen'
			var color = '#9ACD32'
			if(is_layer3 == true) {
				//color = 'turquoise'
				color = '#40E0D0'
			}
			var size = 0
			if(dict_devices[site_id][device_id]['is_managed'] == false) {
				//color = 'Orange
				color = '#FFA500'
			}
			if('size' in device) {
				size = device['size']
			}
			cy.add({
				data: {
					id: hostname,
					label: set_label(site_id, device_id),
					shape: shape,
					color_main: color,
					color_invert: invertColor(color),
					size: size * 5 + 25
				}
			})
		}
	}
	pending_uplinkSingle = {}
	pending_uplinkMultiple = {}
	pending_removedString = new Set()

	var set_edgeID = new Set()
	for(var source_id in dict_edgeFabric) {
		for(var target_id in dict_edgeFabric[source_id]) {
			for(i = 0; i< dict_edgeFabric[source_id][target_id]['pairs'].length; i++) {
				var pair = dict_edgeFabric[source_id][target_id]['pairs'][i]
				var edge_id = source_id + '.' + pair[0] + ' - ' + target_id + '.' + pair[1]
				var edge_reverse = target_id + '.' + pair[1] + ' - ' + source_id + '.' + pair[0]
				// var color = 'DarkGray'
				var color = '#A9A9A9'
				if(set_path2gateway.has(edge_id) || set_path2gateway.has(edge_reverse)) {
					// color = 'FireBrick'
					color = '#B22222'
				}
				var line_style = 'solid'
				/*
					determine service links
						link is between TORs
						link is to a layer3 uplink
						link is uplink to central site
						link is horizontal (redundant)
					set edge as dashed
				*/
				if(source_id in dict_vertical && !dict_vertical[source_id].has(target_id)) {
					line_style = 'dashed'
				}
				for(var site_id in dict_devices) {
					site = dict_devices[site_id]
					if(source_id in site && target_id in site) {
						source = site[source_id]
						target = site[target_id]
						if(source['is_tor'] == true && target['is_tor'] == true) {
							line_style = 'dashed'
						} else if(source['is_router'] == true || target['is_router'] == true) {
							line_style = 'dashed'
						}
					}
				}
				/*
					add edges to graph
					add both directions of edge to set
						this avoids duplicate edges
				*/
				if(set_validNodes.has(source_id) && set_validNodes.has(target_id)) {
					if(!set_edgeID.has(edge_id) && !set_edgeID.has(edge_reverse)) {
						var source_label = pair[0] + ' - '
						if(pair[0] != null) {
							source_label += dict_interfaces[source_id][pair[0]]['port_number']
						}
						else {
							source_label += 'null'
						}
						var target_label = pair[1] + ' - '
						if(pair[1] != null) {
							target_label += dict_interfaces[target_id][pair[1]]['port_number']
						}
						else {
							target_label += 'null'
						}
						cy.add({
							data: {
								id: edge_id,
								source: source_id,
								target: target_id,
								source_label: source_label,
								target_label: target_label,
								line_style: line_style
							}
						})
						set_edgeID.add(edge_id)
						set_edgeID.add(edge_reverse)
					}
				}
			}
		}
	}

	if(document.getElementById('showRouter_edge').checked == true) {
		set_other('layer3', set_validNodes, cy)
	}
	if(document.getElementById('showEth').checked == true) {
		set_other('eth_port', set_validNodes, cy)
	}
	cy.layout({
		name: 'fcose', 
		"edgeElasicity": edge => 0,  
		"nodeRepulsion": node => 999999, 
		"idealEdgeLength": edge => 250
	}).run();
}
