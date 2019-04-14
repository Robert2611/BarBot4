function show_page_admin_clean(data){
	var e_admin_clean = CloneFromTemplate("t_admin_clean");
	e_admin_clean.find(".clean_cycle_left")
		.click(function(){
			get_bar_bot_data({"action" : "clean_cycle_left"});
	});
	e_admin_clean.find(".clean_cycle_right")
		.click(function(){
			get_bar_bot_data({"action" : "clean_cycle_right"});
	});
	var e_clean_ports = e_admin_clean.find(".ports");
	for( port=0; port<12; port++){
		var e_clean_port = CloneFromTemplate("t_admin_clean_port").find(".port");
		e_clean_port.html( (port + 1) + " reinigen" );
		//pass data to the click event
		e_clean_port.click({port : port}, function(e){
			get_bar_bot_data({"action" : "clean", "port" : e.data.port});
		});
		e_clean_ports.append(e_clean_port);
	}
	$("#content").append(e_admin_clean);
}

function show_page_admin_edit_ports(data){
	var e_admin_edit_ports = CloneFromTemplate("t_admin_edit_ports");
	var e_form = bar_bot_form("set_ports");
	var e_table = e_admin_edit_ports.find("table.ports");
	//ports
	$.each(data.ports, function(port, iid){
		//don't show special ports
		if( port >= 12 )
			return;
		var e_admin_edit_port = CloneFromTemplate("t_admin_edit_port").find("tr");
		//workaround
		var port_name = parseInt(port) + 1;
		e_admin_edit_port.find(".port_name").text( `Port ${port_name}`);
		var e_port = e_admin_edit_port.find("select.port_content");
		e_port.attr("name","port_" + port);
		e_port.append($("<option/>", {'value':-1, 'text':'-'}));
		$.each(data.ingredients, function(id, ing_data){
			if(ing_data.type == "special")
				return;
			e_option = $("<option/>", {'value':id, 'text':ing_data.name})
			if(iid == id)
				e_option.prop("selected", "selected");
			e_port.append(e_option);
		});
		e_table.append(e_admin_edit_port);
	});
	e_form.append(e_admin_edit_ports);
	if(data.message == "ports_set"){
		$("#content").append($("<p/>", {'class':'message', 'text':"Positionen wurden gesetzt" }));
	}
	$("#content").append(e_form);
}

function show_page_admin_calibrate(data){
	var e_admin_calibrate = CloneFromTemplate("t_admin_calibrate");
	var e_form = bar_bot_form("set_calibration");
	var e_port = e_admin_calibrate.find("select[name=port]");
	e_port.append($("<option/>", {'value':-1, 'text':'-'}));
	$.each(data.ports, function(port, iid){
		if( iid < 0 )
			return;
		e_option = $("<option/>", {'value':port, 'text':port + ": " + data.ingredients[iid].name})
		e_port.append(e_option);
	});
	var pump_started = false;
	var e_start_pump = e_admin_calibrate.find(".start_pump");
	var e_submit = e_admin_calibrate.find("input[type=submit]");
	//disable submit button and gray it out
	e_submit.css({"opacity":0.5});
	//enable touch keyboard
	var e_calibration = e_admin_calibrate.find("input[name=calibration]");
	e_calibration.focus(function(){
		show_keyboard(e_calibration);
	});
	e_start_pump.click(function(e){
		e.preventDefault();
		get_bar_bot_data({"action" : "calibrate", "port" : e_port.val()})
			.done(function(){
				if(!pump_started){
					pump_started = true;
					//remove form send prevention
					e_submit.prop("disabled", false);
					e_submit.css({"opacity":1});
				}
			});
	});

	e_form.append(e_admin_calibrate);
	if(data.message == "calibration_set"){
		$("#content").append($("<p/>", {'class':'message', 'text':"Kalibrierung wurden gesetzt" }));
	}
	$("#content").append(e_form);
}

function show_page_admin_overview(data){
	var e_admin_overview = CloneFromTemplate("t_admin_overview");
	var e_table = e_admin_overview.find(".ports");
	$.each(data.ports, function(port, iid){
		if( iid < 0 )
			return;
		var e_row = CloneFromTemplate("t_admin_overview_port");
		e_row.find(".port").html(port);
		e_row.find(".ingredient").html(data.ingredients[iid].name);
		e_row.find(".calibration").html(data.ingredients[iid].calibration);
		e_table.append(e_row);
	});
	//admin navigation
	e_admin_overview.find("[page]").click(function(e){
		var page = $(this).attr('page');
		load_page(page);
	});
	$("#content").append(e_admin_overview);
}

function show_page_admin_system(data){
	var e_admin_system = CloneFromTemplate("t_admin_system");
	e_admin_system.find(".restart_gui").click(function(){
		location.reload();
	});
	e_admin_system.find(".restart_raspberry").click(function(){
		system_do({'action':'reboot'});
	});
	e_admin_system.find(".shutdown_raspberry").click(function(){
		system_do({'action':'shutdown'});
	});
	$("#content").append(e_admin_system);
}
