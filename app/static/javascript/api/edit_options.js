function add_tor(pending_set) {
	helper_device('select_add_tor', 'pending_add_tor', pending_set)
}

function del_tor(pending_set) {
	helper_device('select_del_tor', 'pending_del_tor', pending_set)
}

function add_unmanaged(pending_set) {
	helper_device('select_add_unmanaged', 'pending_add_unmanaged', pending_set)
}

function del_unmanaged(pending_set) {
	helper_device('select_del_unmanaged', 'pending_del_unmanaged', pending_set)
}

function helper_device(elementID_select, elementID_pending, pending_set) {
	var site_id = document.getElementById('show_editSite').innerHTML
	var device_id = document.getElementById(elementID_select).value
	if(site_id != '' && device_id != '') {
		pending_set[site_id].add(device_id)
	} else if (site_id != '' && device_id == '') {
		pending_set[site_id].clear()
	}
	var list = []
	for(var site_id in pending_set) {
		list = list.concat(Array.from(pending_set[site_id]))
	}
	list.sort()
	document.getElementById(elementID_pending).innerHTML = list.join('<br />')
}

function del_gatewaySite(pending_set) {
	helper_site('select_del_gatewaySite', 'pending_del_gatewaySite', pending_set)
}

function add_gatewaySite(pending_set) {
	helper_site('select_add_gatewaySite', 'pending_add_gatewaySite', pending_set)
}

function helper_site(elementID_select, elementID_pending, pending_set) {
	var site_id = document.getElementById(elementID_select).value
	if(site_id == '') {
		pending_set.clear()
	} else {
		pending_set.add(site_id)
	}
	var list = Array.from(pending_set)
	list.sort()
	document.getElementById(elementID_pending).innerHTML = list.join('<br />')
}

function set_serviceUp(set_currentSite, pending_serviceUp) {
	var flag = false
	var device_id = document.getElementById('select_detail_hostname').value
	var interface_id = document.getElementById('select_detail_interface').value
	set_currentSite.forEach(site_id => {
		if(device_id in dict_devices[site_id]) {
			if(dict_devices[site_id][device_id]['is_tor'] == true) {
				if(device_id in pending_serviceUp == false) {
					pending_serviceUp[device_id] = new Set()
				}
				if(pending_serviceUp[device_id].has(interface_id) == false) {
					dict_edgeOther[device_id]['layer3'].push([
						'undefined_serviceUplink',
						interface_id
					])
					pending_serviceUp[device_id].add(interface_id)
					flag = true
				}
			}
		}
	})
	if(flag == true) {
		load_graph(pending_device, pending_site, set_currentSite, graph)
	}
	console.log(pending_serviceUp)
}
