<!DOCTYPE html>
<html>
	<head>
		<title>Topology Preview</title>
		<!--
			<title>{{customer}} Topology Preview</title>
		-->
		<meta charset="utf-8">
		<meta name="viewport" content="width=device-width, initial-scale=1">

		<!--
			set stylesheets
		-->
		<link rel="stylesheet" href="{{url_for('static', filename='css/bootstrap/bootstrap.min.css')}}">
		<!--
			<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.3.1/dist/css/bootstrap.min.css" integrity="sha384-ggOyR0iXCbMQv3Xipma34MD+dH/1fQ784/j6cY/iJTQUOhcWr7x9JvoRxT2MZw1T" crossorigin="anonymous">
		-->
		<link rel="stylesheet" href="{{url_for('static', filename='css/stylesheet.css')}}">
		<!--
			<link rel="stylesheet" href="static/css/bootstrap/bootstrap.min.css">
			<link rel="stylesheet" href="static/css/stylesheet.css">
		-->

		<!--
			load cytoscape graph functions
		-->
		<script type="text/javascript" src="{{url_for('static', filename='javascript/api/cytoscape/cytoscape.min.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/api/cytoscape/layout-base.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/api/cytoscape/cose-base.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/api/cytoscape/cytoscape-fcose.js')}}"></script>
		<!--
			<script type="text/javascript" src="static/javascript/api/cytoscape/cytoscape.min.js"></script>
			<script type="text/javascript" src="static/javascript/api/cytoscape/layout-base.js"></script>
			<script type="text/javascript" src="static/javascript/api/cytoscape/cose-base.js"></script>
			<script type="text/javascript" src="static/javascript/api/cytoscape/cytoscape-fcose.js"></script>
		-->
		<!--
			<script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>
			<script src="https://unpkg.com/layout-base/layout-base.js"></script>
			<script src="https://unpkg.com/cose-base/cose-base.js"></script>
			<script src="https://unpkg.com/cytoscape-fcose/cytoscape-fcose.js"></script>
		-->

		<!--
			load resources to generate graph
		-->
		<script type="text/javascript" src="{{url_for('static', filename='javascript/current_preview/details.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/current_preview/device.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/current_preview/interface.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/current_preview/graph_fabric.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/current_preview/graph_other.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/current_preview/details.js')}}"></script>
		
		<!--
			<script type="text/javascript" src="static/javascript/current_preview/device.js"></script>
			<script type="text/javascript" src="static/javascript/current_preview/interface.js"></script>
			<script type="text/javascript" src="static/javascript/current_preview/graph_fabric.js"></script>
			<script type="text/javascript" src="static/javascript/current_preview/graph_other.js"></script>
			<script type="text/javascript" src="static/javascript/current_preview/details.js"></script>
		-->

		<!--
			load all other javascript functions
		-->
		<script type="text/javascript" src="{{url_for('static', filename='javascript/api/loadDropdown.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/api/edit_options.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/api/load_graph.js')}}"></script>
		<script type="text/javascript" src="{{url_for('static', filename='javascript/api/Graph.js')}}"></script>
		<!--
			<script type="text/javascript" src="static/javascript/api/loadDropdown.js"></script>
			<script type="text/javascript" src="static/javascript/api/edit_options.js"></script>
			<script type="text/javascript" src="static/javascript/api/load_graph.js"></script>
			<script type="text/javascript" src="static/javascript/api/Graph.js"></script>
		-->

		<!--
			load favicon image to look official
		-->
		<!--
			<link rel="icon" type="image/x-icon" href="static/favicon.ico">
		-->
		<link rel="icon" type="image/x-icon" href="{{url_for('static', filename='favicon.ico')}}">

		<style>
			form {
				width: 100%;
				height: 100%
			}
			h2, h4 {
				text-align: center;
			}
		</style>
	</head>
	<body>
		<!--
			by default, the container is 100% of the page
		-->
		<div class="container-fluid h-100">
			<!--
				this is the header
					occupies 5% of the page
					contains the following
						toggle for showing left sidebar
						title of page
						link to next page
			-->
			<div class="row header" style="height: 5%; top: 0px; left: 0px;">
				<!--
					toggle for showing left sidebar
					press to hide and show left sidebar
					by default, it is shown
				-->
				<div class="col-md-3 d-flex justify-content-center">
					<button onclick="toggleNav()" class="openbtn">
						<h3>☰ Generation Options</h3>
					</button>
				</div>
				<!--
					this serves as the page title
				-->
				<div class="col-md-6">
					<h2>Preview Topology before Next Step</h2>
				</div>
				<!--
					link to next page
					will trigger a post response that calculates export files
					post response will redirect to the conclusion page
				-->
				<div class="col-md-3 d-flex justify-content-center">
					<form method="post" id="form_nextStep" action="/{{ customer }}/{{ timestamp }}/save-edits/0">
						<input type="hidden" id="list_tor" name="list_tor" value="">
						<input type="hidden" id="list_unmanaged" name="list_unmanaged" value="">
						<!--<input type="hidden" id="list_gatewaySite" name="list_gatewaySite" value="">
						<input type="hidden" id="list_gatewaySite_all" name="list_gatewaySite_all" value="">
						<input type="hidden" id="list_gatewaySite_del" name="list_gatewaySite_del" value="">-->
						<input type="hidden" id="list_site_gateway" name="list_site_gateway" value="">
						<input type="hidden" id="list_site_ignored" name="list_site_ignored" value="">
						<input type="hidden" id="pending_serviceUp" name="pending_serviceUp" value="">
						<button type="submit" class="openbtn" onclick="next_step(graph)">
							<h3>go to next step ➞</h3>
						</button>
					</form>
					<!--<button onclick="toggleNav()" class="openbtn">
						<h3>Next ➞</h3>
					</button>-->
				</div>
			</div>
			<!--
				this is the main content
					this occupies the lower 95% of the screen
					if the left toggle is off, roughly a quarter of the page will be a sidebar
					otherwise, the entire page will consist of a cytoscape graph
			-->
			<div class="row" style="height: 94.9%; top: 5%; left: 5%;">
				<!--
					this is the sidebar
						the sidebar consists of several accordion-style headers
						pressing the header will show the options underneath
						the further options are hidden by default
				-->
				<div id="sidebar" class="col-md-3 sidebar" style=" overflow-y: scroll;">
					<!--
						this is the display control
							hide/show eth ports
							hide/show edge service links
							change node sublabels
							change amount of sites displayed
					-->
					<button class="accordion">Display Options</button>
					<div class="panel">
						<!--
							change amount of sites displayed
								add sites to display
								each added site will be displayed
								can only add, not delete, sites
								use (none) to remove all sites 
								sites to be shown will be displayed beforehand
						-->
						<div class="row">
							<div class="col-sm-12">
								<h5>Set Sites to View</h5>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-9">
								<!--
									updated via template and javascript
								-->
								<select id="select_siteView">
									<option value="everything">(all sites)</option>
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button onclick="fillSelect_deviceID(set_currentSite)">add</button>
							</div>
						</div>
						<!--
							sites to be shown will be displayed beforehand
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>Will view site(s):</p>
							</div>
							<div class="col-sm-6">
								<p id="current_site"></p>
							</div>
						</div>
						<!--
							hide/show options
						-->
						<div class="row">
							<div class="col-sm-12">
								<h5>Toggle Edge Nodes</h5>
							</div>
						</div>
						<!--
							hide/show eth ports
								hide by default
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>show eth ports</p>
							</div>
							<div class="col-sm-3">
								<label for="showEth">true</label>
								<input type="radio" id="showEth" name="eth" value="showEth">
							</div>
							<div class="col-sm-3">
								<label for="hideEth">false</label>
								<input type="radio" id="hideEth" name="eth" value="hideEth" checked>
							</div>
						</div>
						<!--
							hide/show edge routers
								hide by default
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>show edge router</p>
							</div>
							<div class="col-sm-3">
								<label for="showRouter_edge">true</label>
								<input type="radio" id="showRouter_edge" name="router_edge" value="showRouter_edge">
							</div>
							<div class="col-sm-3">
								<label for="hideRouter_edge">false</label>
								<input type="radio" id="hideRouter_edge" name="router_edge" value="hideRouter_edge" checked>
							</div>
						</div>
						<!--
							change node sublabels
								device hostnames are the main label
						-->
						<div class="row">
							<div class="col-sm-12">
								<h5>Change Sub-Labels</h5>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6">
								<label for="select_nodeLabel">display node sub-label</label>
							</div>
							<div class="col-sm-6">
								<select id="select_nodeLabel" onchange="update_nodeLabel()">
									<option value="site_id">Site</option>
									<option value="location">Location</option>
									<option value="domain_name">Domain</option>
									<option value="ip_address">IP Address</option>
									<option value="chassis_id">MAC Address(es)</option>
									<option value="community_string">Community String</option>
									<option value="listModelHW">Hardware Model(s)</option>
								</select>
							</div>
						</div>
						<!--
							record current sublabel
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>Will view label:</p>
							</div>
							<div class="col-sm-6">
								<p id="current_nodeLabel">Site</p>
							</div>
						</div>
						<!--
							finalize every change made in display options
						-->
						<button type="button" onclick="load_graph(pending_device, pending_site, set_currentSite, graph)">update topology</button>
					</div>
					<!--
						this is the detail control
							for a given device ID
								for a given interface ID
									display channel group
									display known VLANs
					-->
					<button class="accordion">Show Node Details</button>
					<div class="panel">
						<div class="row">
							<div class="col-sm-12">
								<h4>Select Device and Interface</h4>
								<p>(Note: uses site_id from "Display Options")</p>
							</div>
						</div>
						<div style="overflow-y: scroll;">
						</div>
						<div class="row">
							<!--
								draws from a list of all device IDs
							-->
							<div class="col-sm-3">
								<label for="select_detail_hostname">hostname</label>
							</div>
							<div class="col-sm-9">
								<select id="select_detail_hostname" onchange="fillSelect_intf('select_detail_hostname')">
									<option value="">(none)</option>
								</select>
							</div>
						</div>
						<!--
							draws from a list of all interface IDs for given device ID
						-->
						<div class="row">
							<div class="col-sm-3">
								<label for="select_detail_interface">interface</label>
							</div>
							<div class="col-sm-9">
								<select id="select_detail_interface" onchange="update_details()">
									<option value="">(none)</option>
								</select>
							</div>
						</div>
						<!--
							show non-VLAN information
						-->
						<div class="row">
							<div class="col-sm-12">
								<h5>Other Information</h5>
							</div>
						</div>
						<!--
							show device ID
						-->
						<div class="row">
							<div class="col-sm-3">
								<p>hostname: </p>
							</div>
							<div class="col-sm-9">
								<p id="show_detail_hostname"></p>
							</div>
						</div>
						<!--
							show interface ID
						-->
						<div class="row">
							<div class="col-sm-3">
								<p>interface:</p>
							</div>
							<div class="col-sm-9">
								<p id="show_detail_interface"></p>
							</div>
						</div>
						<!--
							show description
						-->
						<div class="row">
							<div class="col-sm-3">
								<p>description:</p>
							</div>
							<div class="col-sm-9">
								<p id="show_description_interface"></p>
							</div>
						</div>
						<!--
							show channel group ID ID
						-->
						<div class="row">
							<div class="col-sm-3">
								<p>channel:</p>
							</div>
							<div class="col-sm-9">
								<p id="show_detail_channelID"></p>
							</div>
						</div>
						<!--
							show VLAN information
						-->
						<div class="row">
							<div class="col-sm-12">
								<h5>VLAN specific information</h5>
							</div>
						</div>
						<!--
							show access vlan
						-->
						<div class="row">
							<div class="col-sm-3">
								<p>access: </p>
							</div>
							<div class="col-sm-9">
								<p id="show_detail_access"></p>
							</div>
						</div>
						<!--
							show list of trunk vlans
						-->
						<div class="row">
							<div class="col-sm-3">
								<p>trunk: </p>
							</div>
							<div class="col-sm-9">
								<p id="show_detail_trunk"></p>
							</div>
						</div>
						<!--
							show voice vlan
						-->
						<div class="row">
							<div class="col-sm-3">
								<p>voice:</p>
							</div>
							<div class="col-sm-9">
								<p id="show_detail_voice"></p>
							</div>
						</div>
						<!--
							show any vlan found in the mac-address table for this interface
						-->
						<div class="row">
							<div class="col-sm-3">
								<p>recorded:</p>
							</div>
							<div class="col-sm-9">
								<p id="show_detail_foundMAC"></p>
							</div>
						</div>
					</div>

					<!--
						this is the edit uplinks section
							add and remove uplinks
							add can be done one-by-one or all at once
							delete is one-by-one
					-->
					<button class="accordion">Edit Service Uplinks</button>
					<div class="panel">
						<div class="row">
							<div class="col-sm-12">
								<select id="select_uplinkTOR" onchange="fillSelect_intf('select_uplinkTOR')">
									<option value="">(none)</option>
								</select>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-12">
								<h4>Add Uplinks</h4>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-9">
								<select id="select_add_uplinkSingle">
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="add_uplinkSingle(pending_uplinkSingle)">add</button>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6">
								<p>Adding single uplinks:</p>
							</div>
							<div class="col-sm-6">
								<p id="pending_uplinkSingle"></p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-9">
								<input id="string_add_uplinkMultiple" style="width: 100%">
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="add_uplinkMultiple(pending_uplinkMultiple, set_currentSite)">add</button>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6">
								<p>Search sites for string:</p>
							</div>
							<div class="col-sm-6">
								<p id="pending_uplinkMultiple"></p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-9">
								<select id="select_del_uplinkMultiple" style="width: 100%">
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="del_uplinkMultiple(pending_uplinkMultiple)">remove</button>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-6">
								<p>Remove uplinks with:</p>
							</div>
							<div class="col-sm-6">
								<p id="pending_removedString"></p>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-12">
								<button onclick="load_graph(pending_device, pending_site, set_currentSite, graph)">set interfaces as uplink (TOR only)</button>
							</div>
						</div>
					</div>

					<!--
						this is the edit device panel
							for a given site
								add and remove TORs
								add and remove routers
					-->
					<button class="accordion">Edit Devices</button>
					<div class="panel">
						<!--
							choose site to edit
								will list all devices in site when editing TORs and routers
						-->
						<div class="row">
							<div class="col-sm-9">
								<select id="select_siteEdit">
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="resetSelect_edits()">set site</button>
							</div>
						</div>
						<!--
							display site being edited
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>Editing for site:</p>
							</div>
							<div class="col-sm-6">
								<p id="show_editSite"></p>
							</div>
						</div>
						<!--
							add and remove TORs
						-->
						<div class="row">
							<div class="col-sm-12">
								<h4>Edit TORs in Topology</h4>
							</div>
						</div>
						<!--
							add TORs
								draws from a list of all non-TOR device IDs
								if applied, will turn the listed devices into stars
						-->
						<div class="row">
							<div class="col-sm-9">
								<select id="select_add_tor">
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="add_tor(pending_device.add.tor)">add</button>
							</div>
						</div>
						<!--
							list proposed TORs to be added
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>Will add TORs:</p>
							</div>
							<div class="col-sm-6">
								<p id="pending_add_tor"></p>
							</div>
						</div>
						<!--
							delete TORs
								draws from a list of all TOR device IDs
								if applied, will turn the listed TORs into circles
						-->
						<div class="row">
							<div class="col-sm-9">
								<select id="select_del_tor">
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="del_tor(pending_device.del.tor)">remove</button>
							</div>
						</div>
						<!--
							list proposed TORs to be deleted
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>Will delete TORs:</p>
							</div>
							<div class="col-sm-6">
								<p id="pending_del_tor"></p>
							</div>
						</div>
						<!--
							add and remove managed devices
						-->
						<div class="row">
							<div class="col-sm-12">
								<h4>Edit Device Management</h4>
							</div>
						</div>
						<!--
							add routers
								draws from a list of all managed device IDs
								if applied, will turn the listed devices orange
						-->
						<div class="row">
							<div class="col-sm-9">
								<select id="select_add_unmanaged">
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="add_unmanaged(pending_device.add.unmanaged)">add</button>
							</div>
						</div>
						<!--
							list devices to be unmanaged
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>To be unmanaged:</p>
							</div>
							<div class="col-sm-6">
								<p id="pending_add_unmanaged"></p>
							</div>
						</div>
						<!--
							add routers
								draws from a list of all unmanaged devices
								ignores devices without any vlan traffic (routers)
								if applied, will turn the listed devices blue or green
						-->
						<div class="row">
							<div class="col-sm-9">
								<select id="select_del_unmanaged">
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="del_unmanaged(pending_device.del.unmanaged)">remove</button>
							</div>
						</div>
						<!--
							list proposed devices to be managed
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>To be managed:</p>
							</div>
							<div class="col-sm-6">
								<p id="pending_del_unmanaged"></p>
							</div>
						</div>

						<!--
							finalize every change made in display options
						-->
						<button type="button" onclick="load_graph(pending_device, pending_site, set_currentSite, graph)">update topology</button>
					</div>

					<!--
						this is the edit sites control
							add and remove central sites
					-->
					<button class="accordion">Edit Sites</button>
					<div class="panel">
						<!--
							add and remove central sites
						-->
						<div class="row">
							<div class="col-sm-12">
								<h4>Edit Paths to Routers in Topology</h4>
							</div>
						</div>
						<!--
							add ignored gateway sites 
								draws from a list of ignored gateway site IDs
								if applied, recalculate service uplinks and downlinks
						-->
						<div class="row">
							<div class="col-sm-9">
								<select id="select_add_gatewaySite">
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="add_gatewaySite(pending_site.add.gateway)">add</button>
							</div>
						</div>
						<!--
							display ignored gateway sites to be added
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>Will add gateway sites:</p>
							</div>
							<div class="col-sm-6">
								<p id="pending_add_gatewaySite"></p>
							</div>
						</div>
						<!--
							ignore gateway sites
								draws from a list of gateway site IDs
								if applied, recalculate service uplinks and downlinks
						-->
						<div class="row">
							<div class="col-sm-9">
								<select id="select_del_gatewaySite">
									<option value="">(none)</option>
								</select>
							</div>
							<div class="col-sm-3">
								<button type="button" onclick="del_gatewaySite(pending_site.del.gateway)">remove</button>
							</div>
						</div>
						<!--
							display gateway sites to be ignored
						-->
						<div class="row">
							<div class="col-sm-6">
								<p>Ignoring gateway Sites:</p>
							</div>
							<div class="col-sm-6">
								<p id="pending_del_gatewaySite"></p>
							</div>
						</div>
						<!--
							finalize every change made in display options
						-->
						<button type="button" onclick="load_graph(pending_device, pending_site, set_currentSite, graph)">update topology</button>
					</div>
					<!--
						save behavior
						determines what clicking "go to next step" does
					-->
					<button class="accordion">Save Options</button>
					<div class="panel">
						<div class="row">
							<div class="col-sm-12">
								<h4>Determine next step behavior</h4>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-9">
								<label for="action_0">save and continue to csv generation</label>
							</div>
							<div class="col-sm-3">
								<input type="radio" id="action_0" name="next_action" value="0" onclick="change_save(0)" checked>
							</div>
						</div>
						<div class="row">
							<div class="col-sm-9">
								<label for="action_1">save and exit to login screen</label>
							</div>
							<div class="col-sm-3">
								<input type="radio" id="action_1" name="next_action" value="1" onclick="change_save(1)">
							</div>
						</div>
						<div class="row">
							<div class="col-sm-9">
								<label for="action_2">don't save, delete configuration</label>
							</div>
							<div class="col-sm-3">
								<input type="radio" id="action_2" name="next_action" value="2" onclick="change_save(2)">
							</div>
						</div>
					</div>
				</div>
				<!--
					this is where the cytoscape topology will be displayed
				-->
				<div id="main" class="col-md-9" style="background-color: FloralWhite;">
					<div id="cy"></div>
				</div>
			</div>
		</div>
	</body>
	<script>
		// prevent overflow from sidebar
		var height = window.innerHeight * 0.949 + 'px'
		console.log(height)
		document.getElementById('sidebar').style.maxHeight = height

		// get list of sites in customer network
		// sites are immutable
		fillSelect_site()
		
		// load previously set service uplinks
		// service uplinks only added to dict_edgeOther for real after preview is confirmed
		var pending_serviceUp = {}
		var pending_uplinkSingle = {}
		var pending_uplinkMultiple = {}
		var pending_removedString = new Set()
		for(var device_id in dict_details['dict_serviceUp']) {
			if(device_id in pending_serviceUp == false) {
				pending_serviceUp[device_id] = new Set()
			}
			dict_details['dict_serviceUp'][device_id].forEach(interface_id => {
				pending_serviceUp[device_id].add(interface_id)
				if(device_id in pending_serviceUp == false) {
					pending_serviceUp[device_id] = {
						'layer3': {},
						'eth_port': {}
					}
				}
				var other_id = null
				if(device_id in dict_edgeOther) {
					if(interface_id in dict_edgeOther[device_id]['eth_port']) {
						other_id = dict_edgeOther[device_id]['eth_port'][interface_id]
					}
				}
				dict_edgeOther[device_id]['layer3'][interface_id] = other_id
			})
		}

		// based on known sites, create dictionary to store pending edits
		var pending_device = {
			add: {
				tor: {},
				router: {},
				unmanaged: {}
			},
			del: {
				tor: {},
				router: {},
				unmanaged: {}
			}
		}
		var pending_site = {
			add: {
				gateway: new Set()
			},
			del: {
				gateway: new Set()
			}
		}
		for(var site_id in dict_devices) {
			pending_device.add.tor[site_id] = new Set()
			pending_device.add.router[site_id] = new Set()
			pending_device.add.unmanaged[site_id] = new Set()
			pending_device.del.tor[site_id] = new Set()
			pending_device.del.router[site_id] = new Set()
			pending_device.del.unmanaged[site_id] = new Set()
		}

		// graph used to calculate service up/downlinks
		graph = new Graph(dict_devices, dict_edgeFabric, dict_edgeOther, dict_details)

		// by default, show everything
		var set_currentSite = new Set(['everything'])
		// control left bar hide/show
		var flagNav = false;
		// control collapsible left bar sections
		var accordion = document.getElementsByClassName('accordion')

		/*
			each time an accordion panel is activated
				show content underneath if previously hidden
				hide content underneath if previously shown
			all panels are hidden by default
		*/
		for(var i = 0; i<accordion.length; i++) {
			accordion[i].addEventListener("click", function() {
				this.classList.toggle("active")
				var panel = this.nextElementSibling
				if(panel.style.display == "block") {
					panel.style.display = "none"
				} else {
					panel.style.display = "block"
				}
			})
		}
		/*
			each time left sidebar control is toggled
				hide if previously visible
				show if previuosly hidden
			is shown by default
		*/
		function toggleNav() {
			if(flagNav == true) {
				document.getElementById("sidebar").className = "col-md-3 sidebar";
				document.getElementById("main").className = "col-md-9";
				flagNav = false;
			} else {
				document.getElementById("sidebar").className = "hidden";
				document.getElementById("main").className = "col-md-12";
				flagNav = true;
			}
		}

		function change_save(num) {
			var string = document.getElementById('form_nextStep').action
			string = string.substring(0, string.length - 1)
			console.log(string)
			document.getElementById('form_nextStep').action = string + num
		}

		/*
			the item "go to next step" is a form
			when pressed, user is sent to next step in import process
				acquire all devices that are considered valid tors
				acquire all devices that are considered valid routers
			the above lists are sent to ns_scan_capture to generate network configuration

			depending on the value in "select_nextAction", the action of the form will change
		*/
		function next_step(graph) {
			var list_tor = []
			var list_unmanaged = []
			for(var site_id in dict_devices) {
				for(var device_id in dict_devices[site_id]) {
					if(dict_devices[site_id][device_id]['is_tor'] == true) {
						list_tor.push(device_id)
					}
					if(dict_devices[site_id][device_id]['is_managed'] == false) {
						list_unmanaged.push(device_id)
					}
				}
			}
			var list_site_gateway = graph.get_list_site_gateway()
			var list_site_ignored = graph.get_list_site_ignored()
			document.getElementById('list_tor').value = JSON.stringify(list_tor)
			document.getElementById('list_unmanaged').value = JSON.stringify(list_unmanaged)
			document.getElementById('list_site_gateway').value = JSON.stringify(list_site_gateway)
			document.getElementById('list_site_ignored').value = JSON.stringify(list_site_ignored)
			for(var device_id in pending_serviceUp) {
				pending_serviceUp[device_id] = Array.from(pending_serviceUp[device_id]).sort()
			}
			document.getElementById('pending_serviceUp').value = JSON.stringify(pending_serviceUp)
		}

		// load initial view of graph
		load_graph(pending_device, pending_site, set_currentSite, graph)
	</script>
</html>
