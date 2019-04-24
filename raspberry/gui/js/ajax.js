var current_page = "";

function get_bar_bot_data(input) {
	return $.getJSON({
		url: "http://localhost:5555",
		headers: { 'X-Requested-With': 'XMLHttpRequest' },
		type: "post",
		data: input
	}).fail(function () {
		show_start_server();
	});
}

function system_do(input) {
	return $.getJSON({
		url: "http://localhost:1234",
		headers: { 'X-Requested-With': 'XMLHttpRequest' },
		type: "post",
		data: input
	}).fail(function () {
		console.log("FEHLER");
		alert("Fehler beim Ausführen");
	});
}

function clone_from_template(template_name) {
	var t_list = document.querySelector('#' + template_name);
	return $(document.importNode(t_list.content, true));
}

function load_page(name, additional_data = {}) {
	//show wait
	keyboard_hide();
	$("#content").empty();
	$("#content").append($("<div/>", { 'class': 'spinner', 'text': 'Lade...' }));
	var action = name;
	if (action.includes("admin_"))
		action = "admin";
	var data = $.extend({ 'action': action }, additional_data);
	get_bar_bot_data(data)
		.done(function (data) {
			current_page = name;
			$("#content").empty();
			var show_function = "show_page_" + name;
			window[show_function](data);
		});
}

function bar_bot_form(action) {
	var e_form = $("<form/>")
		.submit(function (e) {
			e.preventDefault();
			var form_data = $(e.currentTarget).serialize();
			get_bar_bot_data(form_data).done(function (data) {
				$("#content").empty();
				console.log(data);
				window["show_page_" + current_page](data);
			});
		});
	e_form.append($("<input/>", { "name": "action", 'type': 'hidden', 'value': action }));
	return e_form;
}

function show_start_server() {
	if (current_page != "server_error") {
		current_page = "server_error";
		show_overlayer_from_template("t_server_error");
	}
}

function update_system_buttons(container) {
	container.find(".start_server").click(function () {
		system_do({ 'action': 'start' });
	});
	container.find(".restart_raspberry").click(function () {
		system_do({ 'action': 'reboot' });
	});
	container.find(".shutdown_raspberry").click(function () {
		system_do({ 'action': 'shutdown' });
	});
	container.find(".restart_gui").click(function(){
		location.reload();
	});
}
var period = 1000;

function updater() {
	get_bar_bot_data({ 'action': 'status' })
		.done(function (data) {
			console.log(data);
			if (current_page == "server_error") {
				//try loading the page again
				load_page("listrecipes");
			}
			if (data.status == "connecting") {
				show_overlayer_from_template("t_status_connecting");
			} else if (data.status == "startup") {
				show_overlayer_from_template("t_status_startup");
			} else if (data.status == "cleaning") {
				show_overlayer_from_template("t_status_cleaning");
			} else if (data.status == "mixing") {				
				if (data.message == "place_glas") {
					show_overlayer_from_template("t_message_place_glas");
				} else if(data.message == "mixing_done_remove_glas"){
					var e_message_done = clone_from_template("t_message_mixing_done_remove_glas");			
					if(data.instruction == undefined){
						e_message_done.find(".instruction_wrapper").hide();
					}else{
						e_message_done.find(".instruction").html(data.instruction);
					}
					show_overlayer(e_message_done);
				} else {
					var e_status_mixing = clone_from_template("t_status_mixing");
					var percent = Math.round(data.progress * 100);
					e_status_mixing.find(".mixprogress_bar").width(percent + "%");					
					e_status_mixing.find(".percentage").html(percent);
					show_overlayer(e_status_mixing);
				}
			} else if (data.status == "cleaning_cycle") {
				if (data.message == "place_glas") {
					show_overlayer_from_template("t_message_place_glas");
				} else {
					show_overlayer_from_template("t_status_cleaning");
				}
			} else if (data.status == "single_ingredient") {
				if (data.message == "place_glas") {
					show_overlayer_from_template("t_message_place_glas");
				} else {
					show_overlayer_from_template("t_status_single_ingredient");
				}
			} else {
				hide_overlayer();
			}
		})
		.always(function () {
			//reload after 1 second
			setTimeout(updater, period);
		});
}

function show_overlayer_from_template(template_name){
	var e_content = clone_from_template(template_name);
	update_system_buttons(e_content);
	show_overlayer(e_content);
} 
function show_overlayer(content) {
	$("#overlayer_content").html(content);
	$("#overlayer").show();
}

function hide_overlayer() {
	$("#overlayer").hide();
}
