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

function add_uplinkSingle(pending_uplinkSingle) {
	var device_id = document.getElementById('select_uplinkTOR').value
	var interface_id = document.getElementById('select_add_uplinkSingle').value
	/**
	 * given interface can only be a service_up in the following situations: 
	 * 		not a fabric port
	 * if conditions are satisfied, add to pending_serviceUp
	 * if interface is an eth, the interface is overriden
	 */
	var flag = false
	for(var target_id in dict_edgeFabric[device_id]) {
		dict_edgeFabric[device_id][target_id]['pairs'].forEach(pair => {
			if(pair[0] != null && interface_id == pair[0]) {
				flag= true
			}
		})
	}
	if(flag == false) {
		if(device_id in pending_uplinkSingle == false) {
			pending_uplinkSingle[device_id] = new Set()
		}
		pending_uplinkSingle[device_id].add(interface_id)
		var string = ''
		for(var key in pending_uplinkSingle) {
			string += key + '<br />'
			pending_uplinkSingle[key].forEach(value => {
				string += ' - ' + value + '<br />' 
			})
		}
		document.getElementById('pending_uplinkSingle').innerHTML = string
	}
}

function add_uplinkMultiple(pending_uplinkMultiple, set_currentSite) {
	//	acquire search string and clear value from input
	var string = document.getElementById('string_add_uplinkMultiple').value.toLowerCase()
	document.getElementById('string_add_uplinkMultiple').value = ''

	//	search string may be deleted later
	var select_del_uplinkMultiple = document.getElementById('select_del_uplinkMultiple')
	var set_options = new Set()
	for(var i = 0; i<select_del_uplinkMultiple.length; i++) {
		set_options.add(select_del_uplinkMultiple.options[i].text)
	}
	if(set_options.has(string) == false) {
		var option = document.createElement('option')
		option.text = string
		option.value = string
		select_del_uplinkMultiple.add(option)
	}
	
	/**
	 * 	for each currently loaded site, set the search string
	 * 	doesn't do anything now, only displayed
	 * 	will eventually search for string in port descriptions
	 */
	set_currentSite.forEach(site_id => {
		if(site_id in pending_uplinkMultiple == false) {
			pending_uplinkMultiple[site_id] = new Set()
		}
		pending_uplinkMultiple[site_id].add(string)
	})
	var string = ''
	for(var key in pending_uplinkMultiple) {
		string += key + '<br />'
		pending_uplinkMultiple[key].forEach(value => {
			string += ' - ' + value + '<br />'
		})
	}
	document.getElementById('pending_uplinkMultiple').innerHTML = string
}

function del_uplinkMultiple(pending_uplinkMultiple) {
	//	get value of string to be deleted and remove it from select element
	var select_del_uplinkMultiple = document.getElementById('select_del_uplinkMultiple')
	if(select_del_uplinkMultiple.selectedIndex != 0) {
		var removed_string = select_del_uplinkMultiple.value
		select_del_uplinkMultiple.remove(select_del_uplinkMultiple.selectedIndex)
		pending_removedString.add(removed_string)
		/**
		 * 	remove string from all sites to be searched
		 * 	at same time, update pending text
		 * 	these items can be done concurrently
		 */
		var string = ''
		for(var site_id in pending_uplinkMultiple) {
			//	Set definition return false when removing non-existent elements
			pending_uplinkMultiple[site_id].delete(removed_string)
			string += site_id + '<br />'
			pending_uplinkMultiple[site_id].forEach(value => {
				string += ' - ' + value + '<br />'
			})
		}
		document.getElementById('pending_uplinkMultiple').innerHTML = string
		var string = ''
		pending_removedString.forEach(item => {
			string += ' - ' + item + '<br />'
		})
		document.getElementById('pending_removedString').innerHTML = string
	}
}
