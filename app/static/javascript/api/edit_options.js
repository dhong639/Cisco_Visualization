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
