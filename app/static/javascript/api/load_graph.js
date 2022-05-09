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

/*function get_countVLAN(device_id, interface_id) {
	var count_vlan = 0
	if(dict_interfaces[device_id][interface_id]['access_vlan'] != null) {
		count_vlan += 1
	}
	if(dict_interfaces[device_id][interface_id]['voice_lan'] != null) {
		count_vlan += 1
	}
	count_vlan += dict_interfaces[device_id][interface_id]['trunk_list'].length
	count_vlan += dict_interfaces[device_id][interface_id]['list_foundMAC'].length
	return count_vlan
}*/

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
	for(var device_id in dict_edgeOther) {
		if(set_validNodes.has(device_id)) {
			// get list of source interfaces that are fabric
			var set_portFabric = new Set()
			for(var target_id in dict_edgeFabric[device_id]) {
				dict_edgeFabric[device_id][target_id]['pairs'].forEach(pair => {
					set_portFabric.add(pair[0])
				})
			}
			dict_edgeOther[device_id][type].forEach(interface_id => {
				// ignore interface_id if already in fabric
				// used to avoid re-listing interface ids for routers
				if(set_portFabric.has(interface_id) == false) {
					//var color = 'Orange
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
					var edge_id
					var target_label
					var line_style
					var access_vlan = null
					if(type == 'eth_port') {
						access_vlan = dict_interfaces[device_id][interface_id]['access_vlan']
						edge_id = device_id + '.' + interface_id + ' - vlan' + access_vlan
						target_label = 'vlan ' + access_vlan
						line_style = 'solid'
					} else if(type == 'layer3') {
						edge_id = device_id + '.' + interface_id + ' - uplink'
						target_label = 'uplink'
						line_style = 'dashed'
					}
					if(type == 'layer3' || (type == 'eth_port' && access_vlan != null)) {
						cy.add({
							data: {
								id: device_id + '.' + interface_id,
								label: node_label,
								color_main: color,
								color_invert: invertColor(color),
								shape: shape,
								size: 25
							}
						})
						cy.add({
							data: {
								id: edge_id,
								source_label: interface_id,
								source: device_id,
								target: device_id + '.' + interface_id,
								target_label: target_label,
								color_main: color,
								color_invert: invertColor(color),
								line_style: line_style
							}
						})
					}
				}
			});
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

	// declare cytoscape object
	var cy = cytoscape({
		container: document.getElementById('cy'),
		wheelSensitivity: 0.1,
		elements: []
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
		site_id = list_validSite[i]
		for(var device_id in dict_devices[site_id]) {
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
					set edge as dashed
				*/
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
						cy.add({
							data: {
								id: edge_id,
								source: source_id,
								target: target_id,
								source_label: pair[0],
								target_label: pair[1],
								color_main: color,
								color_invert: invertColor(color),
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
	cy.style().selector("node").style("label", "data(label)");
	cy.style().selector("node").style("text-wrap", "wrap");
	cy.style().selector("node").style("height", "data(size)");
	cy.style().selector("node").style("width", "data(size)");
	cy.style().selector("node").style("text-valign", "center");
	cy.style().selector("node").style("text-halign", "center");
	cy.style().selector("node").style("shape", "data(shape)")
	cy.style().selector("node").style("background-color", "data(color_main)")
	cy.style().selector("node").style("background-opacity", 0.75)
	cy.style().selector("edge").style("curve-style", "bezier");
	cy.style().selector("edge").style("source-label", "data(source_label)");
	cy.style().selector("edge").style("source-text-offset", 50);
	cy.style().selector("edge").style("source-text-rotation", "autorotate");
	cy.style().selector("edge").style("target-label", "data(target_label)");
	cy.style().selector("edge").style("target-text-offset", 50);
	cy.style().selector("edge").style("target-text-rotation", "autorotate");
	cy.style().selector("edge").style("text-wrap", "wrap");
	cy.style().selector("edge").style("line-color", "data(color_main)");
	cy.style().selector("edge").style("line-opacity", 0.5);
	cy.style().selector("edge").style("line-style", "data(line_style)")
	cy.style().selector(":selected").style("background-color", "data(color_invert)")
	cy.style().selector(":selected").style("line-color", "data(color_invert)")
	if(set_edgeID.size < 15) {
		cy.layout({
			name: 'concentric'
		}).run()
	} else {
		cy.layout({
			name: 'fcose', 
			"edgeElasicity": edge => 0,  
			"nodeRepulsion": node => 999999, 
			"idealEdgeLength": edge => 250
		}).run();
	}
}