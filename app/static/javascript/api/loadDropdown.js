/*
	################################################################
	SECTION: IMMUTABLE DROPDOWN LISTS
		after the page loads, these dropdown lists will never change
	################################################################
*/

/*
	fillSelect_site()
	function:
		fills out the dropdown lists for 'select_siteView' and 'select_siteEdit'
*/
function fillSelect_site() {
	helper_fillSelect('select_siteView', get_listSites())
	helper_fillSelect('select_siteEdit', get_listSites())
}

function update_nodeLabel() {
	var index = document.getElementById('select_nodeLabel').selectedIndex
	var node_label = document.getElementById('select_nodeLabel')[index].text
	//var node_label = document.getElementById('select_nodeLabel').value
	document.getElementById('current_nodeLabel').innerHTML = node_label
}

/*
	#########################################################################################
	SECTION: DISPLAY OPTIONS and SHOW NODE DETAILS
		these dropdown lists are found under DISPLAY OPTIONS and SHOW NODE DETAILS
			DISPLAY OPTIONS:
				select_siteView				determines dropdown lists under SHOW NODE DETAILS
			SHOW NODE DETAILS
				select_detail_hostname		determines values for 'select_detail_interface'
				select_detail_interface		fetches interface details from dict_interface
	#########################################################################################
*/

/*
	fillSelect_deviceID
	input:
		set_currentSite	set		list of sites to be displayed
	function:
		trigger when 'select_siteView' changes value
		empty 'select_detail_hostname' of all but first value
		fill 'select_detail_hostname' with devices from given site
		empty 'select_detail_interface' of all but first value
*/
function fillSelect_deviceID(set_currentSite) {
	// clear device information
	emptySelect("select_detail_hostname", 1)
	document.getElementById('show_detail_hostname').innerHTML = ''

	// clear interface information
	emptySelect("select_detail_interface", 1)
	document.getElementById('show_detail_interface').innerHTML = ''
	document.getElementById('show_detail_channelID').innerHTML = ''
	document.getElementById('show_detail_access').innerHTML = ''
	document.getElementById('show_detail_trunk').innerHTML = ''
	document.getElementById('show_detail_voice').innerHTML = ''
	document.getElementById('show_detail_foundMAC').innerHTML = ''

	var site_id = document.getElementById("select_siteView").value
	// if site_id is set to (None), delete everything in the set
	if(site_id == '') {
		set_currentSite.clear()
	}
	else if(site_id == 'everything') {
		set_currentSite.clear()
		set_currentSite.add('everything')
	}
	// otherwise, add something to the set
	else {
		/*
			if the current set consists only of the value 'everything'
				empty the set and add the new value
		*/
		if(set_currentSite.size == 1 && set_currentSite.has('everything')) {
			set_currentSite.clear()
			set_currentSite.add(site_id)
		}
		// otherwise, add value normally
		else {
			set_currentSite.add(site_id)
		}
	}
	var list_currentSite = Array.from(set_currentSite)
	//display information in preview cell
	list_currentSite.sort()
	document.getElementById('current_site').innerHTML = list_currentSite.join('<br />')
	//update information in "select_detail_hostname" dropdown
	list_currentSite.forEach(site_id => {
		var list = get_list_deviceID(site_id)
		helper_fillSelect("select_detail_hostname", list)
	});
}
/*
	fillSelect_intf
	function:
		trigger when 'select_detail_hostname' or 'select_siteView' changes value
		empty 'select_detail_interface' of all but first value
		fill 'select_detail_interface' with interface names from devices
*/
function fillSelect_intf() {
	// clear displayed interface information
	emptySelect("select_detail_interface", 1)
	document.getElementById('show_detail_interface').innerHTML = ''
	document.getElementById('show_detail_channelID').innerHTML = ''
	document.getElementById('show_detail_access').innerHTML = ''
	document.getElementById('show_detail_trunk').innerHTML = ''
	document.getElementById('show_detail_voice').innerHTML = ''
	document.getElementById('show_detail_foundMAC').innerHTML = ''

	// set displayed hostname
	var device_id = document.getElementById("select_detail_hostname").value
	document.getElementById('show_detail_hostname').innerHTML = device_id

	// fill out interface information
	var list = []
	if(device_id in dict_interfaces) {
		list = Object.keys(dict_interfaces[device_id])
		list.sort()
	}
	helper_fillSelect("select_detail_interface", list)
}

function update_details() {
	var device_id = document.getElementById("select_detail_hostname").value
	var interface_id = document.getElementById('select_detail_interface').value
	if(interface != '') {
		var interface = dict_interfaces[device_id][interface_id]
		document.getElementById('show_detail_interface').innerHTML = interface_id
		document.getElementById('show_detail_channelID').innerHTML = interface['channel_group']
		document.getElementById('show_detail_access').innerHTML = interface['access_vlan']
		var trunk_list = interface['trunk_list'].join('<br />')
		document.getElementById('show_detail_trunk').innerHTML = trunk_list
		document.getElementById('show_detail_voice').innerHTML = interface['voice_vlan']
		var list_foundMAC = interface['list_foundMAC'].join('<br />')
		document.getElementById('show_detail_foundMAC').innerHTML = list_foundMAC
	}
}

/*
	#####################################################################
	SECTION: EDIT OPTIONS
		these dropdown lists are found under EDIT OPTIONS
			select_siteEdit		determines dropdown lists in this section
			select_add_tor		determines TORs to add to graph
			select_del_tor		determines TORS to remove from graph
			select_add_router	determines routers to add to graph
			select_del_router	determines routers to remove from graph
	#####################################################################
*/

/*
	resetSelect_edits
	function:
		clear all select dropdowns
		fill dropdowns with applicable items based on site_id
		remove all pending 
*/
function resetSelect_edits(/*dict*/) {
	emptySelect("select_add_tor", 1)
	fillSelect_addTOR()
	emptySelect("select_del_tor", 1)
	fillSelect_delTOR()
	emptySelect('select_add_unmanaged', 1)
	fillSelect_addUnmanaged()
	emptySelect('select_del_unmanaged', 1)
	fillSelect_delUnmanaged()
	var site_id = document.getElementById('select_siteEdit').value
	document.getElementById('show_editSite').innerHTML = site_id
}
/*
	fillSelect_addTOR
	function:
		remove all but first option from 'select_add_tor'
		get list of all non-TORs within given site
		add non-TOR device IDs to dropdown
*/
function fillSelect_addTOR() {
	emptySelect("select_add_tor", 1)
	var site_id = document.getElementById('select_siteEdit').value
	var list = get_listTOR(site_id, false)
	helper_fillSelect("select_add_tor", list)
}
/*
	fillSelect_delTOR
	function:
		remove all but first option from 'select_del_tor'
		get list of all TORs within given site
		add TOR device IDs to dropdown
*/
function fillSelect_delTOR() {
	emptySelect("select_del_tor", 1)
	var site_id = document.getElementById('select_siteEdit').value
	var list = get_listTOR(site_id, true)
	helper_fillSelect("select_del_tor", list)
}
/*
	get_listTOR
	input:
		site_id		name of current site
		flag		true	only get TORs
					false	only get non-TORs
	output:
		list		list of device IDs
	function:
		get list of all (non-)TOR devices from given site
*/
function get_listTOR(site_id, flag) {
	var list = []
	if (site_id in dict_devices){
		helper_get_list_deviceID(site_id, list, 'is_tor', flag)
	}
	list.sort()
	return list
}
function fillSelect_addUnmanaged() {
	emptySelect("select_add_unmanaged", 1)
	var site_id = document.getElementById('select_siteEdit').value
	var list = get_listManaged(site_id, true)
	helper_fillSelect("select_add_unmanaged", list)
}
function fillSelect_delUnmanaged() {
	emptySelect("select_del_unmanaged", 1)
	var site_id = document.getElementById('select_siteEdit').value
	var list = get_listManaged(site_id, false)
	for(var device_id in dict_devices[site_id]) {
		if(dict_devices[site_id][device_id]['is_managed'] == false) {
			//console.log(device_id)
		}
	}
	helper_fillSelect("select_del_unmanaged", list)
}
/*
	get_listManaged
	input:
		site_id		string	name of current site
		flag		true	get managed devices only
					false	get unmanaged devices only
	output:
		list		list	list of devices that either either un/managed
	function: 
		get list of all un/managed devices
		note that routers are ignored
*/
function get_listManaged(site_id, flag) {
	var list = []
	if (site_id in dict_devices){
		helper_get_list_deviceID(site_id, list, 'is_managed', flag)
	}
	list.sort()
	return list
}

/*
	fillSelect_delGatewaySite
	input:
		graph		Graph	object describing topology
	function:
		get all sites that have routers uplinks and aren't ignored
		fill options for "select_del_gatewaySite"
*/
function fillSelect_delGatewaySite(graph) {
	emptySelect("select_del_gatewaySite", 1)
	var list = graph.get_list_site_gateway()
	helper_fillSelect("select_del_gatewaySite", list)
}
/*
	fillSelect_addGatewaySite
	input:
		graph		Graph	object describing topology
	function:
		get all sites that have routers uplinks and are ignored
		fill options for "select_add_gatewaySite"
*/
function fillSelect_addGatewaySite(graph) {
	emptySelect("select_add_gatewaySite", 1)
	//var list = graph.get_site_ignored()
	var list = graph.get_list_site_ignored()
	helper_fillSelect("select_add_gatewaySite", list)
}

/*
	##########################################################################
	SECTION: HELPER FUNCTIONS
		functions below are used to aid in running functions in above sections
	##########################################################################
*/

function helper_fillSelect(elementID, list) {
	list.sort()
	var select = document.getElementById(elementID)
	list.forEach(element => {
		var option = document.createElement('option')
		option.text = element
		option.value = element
		select.add(option)
	});
}

function emptySelect(elementID, count_remaining) {
	var select = document.getElementById(elementID)
	var count_current = select.length
	while(count_current != count_remaining) {
		select.remove(count_current - 1)
		count_current = select.length
	}
}

function get_listSites() {
	var list = []
	for(site_id in dict_devices) {
		list.push(site_id)
	}
	list.sort()
	return list
}

function get_list_deviceID(site_id) {
	var list = []
	if (site_id == 'everything') {
		for(var item in dict_devices) {
			helper_get_list_deviceID(item, list)
		}
	} else if(site_id in dict_devices) {
		helper_get_list_deviceID(site_id, list)
	}
	list.sort()
	return list
}

function helper_get_list_deviceID(site_id, list, condition=null, flag=null) {
	for(device_id in dict_devices[site_id]) {
		if(condition == null && flag == null) {
			list.push(device_id)
		} else if(dict_devices[site_id][device_id][condition] == flag) {
			list.push(device_id)
		}
	}
}