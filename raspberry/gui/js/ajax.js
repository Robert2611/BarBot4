var current_page = "";

function get_bar_bot_data(input){
	return $.getJSON({
		url: "http://localhost:5555",
		headers: {'X-Requested-With': 'XMLHttpRequest'},
		type: "post",
		data: input
	}).fail(function(){
		console.log("FEHLER");
		show_start_server();
	});
}

function system_do(input){
	return $.getJSON({
		url: "http://localhost:1234",
		headers: {'X-Requested-With': 'XMLHttpRequest'},
		type: "post",
		data: input
	}).fail(function(){
		console.log("FEHLER");
		alert("Fehler beim Ausführen");
	});
}

function clone_from_template(template_name){
	var t_list = document.querySelector('#' + template_name);
	return $(document.importNode(t_list.content,true));
}

function load_page(name, additional_data = {}){
	//show wait
	keyboard_hide();
	$("#content").empty();
	$("#content").append($("<div/>", {'class':'spinner', 'text':'Lade...'}));
	var action = name;
	if( action.includes("admin_") )
		action = "admin";
	var data = $.extend({'action':action}, additional_data);
	get_bar_bot_data(data)
		.done(function(data){
			current_page = name;
			$("#content").empty();
			var show_function = "show_page_" + name;
			window[show_function](data);
		});
}

function bar_bot_form(action){
	var e_form = $("<form/>")
		.submit(function(e){
			e.preventDefault();
			var form_data = $(e.currentTarget).serialize();
			get_bar_bot_data(form_data).done(function(data){
				$("#content").empty();
				console.log(data);
				window["show_page_" + current_page](data);
			});
		});
	e_form.append($("<input/>", {"name":"action", 'type':'hidden', 'value':action}));
	return e_form;
}

function show_start_server(){
	hide_overlayer();
	if(current_page != "server_error"){
		current_page = "server_error";
		$("#content").empty();
		var e_server_error = clone_from_template("t_server_error");
		e_server_error.find(".start_server").click(function(){
			system_do({'action':'start'});
		});
		e_server_error.find(".restart_raspberry").click(function(){
			system_do({'action':'reboot'});
		});
		e_server_error.find(".shutdown_raspberry").click(function(){
			system_do({'action':'shutdown'});
		});
		$("#content").append(e_server_error);
	}
}

var period = 1000;

function updater() {
	get_bar_bot_data({'action':'status'})
		.done(function(data){
			//console.log(data);
			if(!demo){
				console.log(data);
				if(current_page == "server_error")
					load_page("listrecipes");
				if(data.status == "connecting"){
					show_overlayer("Verbinde...<br/><br/>");
					$("#overlayer_content").append($("<div/>",{'class':'button onwhite', 'html':'Neu starten'}).click(function(){
						system_do({'action':'reboot'});
					}));
				}else if(data.status == "startup"){
					show_overlayer("Starte Hardware...<br/><br/>");
					$("#overlayer_content").append($("<div/>",{'class':'button onwhite', 'html':'Neu starten'}).click(function(){
						system_do({'action':'reboot'});
					}));
				}else if(data.status == "cleaning"){
					show_overlayer("Reinige...");
				}else if(data.status == "mixing"){
					if(data.message == "place_glas"){
						show_overlayer("Bitte ein Glas auf die Plattform stellen.");
					}else if(data.message == "remove_glas"){
						show_overlayer("Der Cocktail ist ferig, bitte entnehmen.");
					}else{
						$("#overlayer_content").empty();
						var percent = Math.round(data.progress*100);
						e_wrapper = $("<div/>", {'id':'mixprogress_container'});
						e_wrapper.append($("<div/>", {'id':'mixprogress_bar', 'style':'width:'+percent+'%'}));
						$("#overlayer_content").append(e_wrapper);
						$("#overlayer_content").append($("<p/>", {'html': "Cocktail wird gemischt: "+percent +'%'}));
						$("#overlayer").show();
					}
				}else if (data.status == "cleaning_cycle"){
					if(data.message == "place_glas"){
						show_overlayer("Bitte ein Glas auf die Plattform stellen.");
					}else{
						show_overlayer("Reinige...");
					}
				}else if(data.status == "single_ingredient"){
					if(data.message == "place_glas"){
						show_overlayer("Bitte ein Glas auf die Plattform stellen.");
					}else{
						show_overlayer("Füge einzelne Zutat hinzu..");
					}
				}else{
					hide_overlayer();
				}
			}
		})
		.always(function() {
			//reload after 1 second
			setTimeout(updater, period);
		});
}

function show_overlayer(content){
	$("#overlayer_content").html(content);
	$("#overlayer").show();
}

function hide_overlayer(){
	$("#overlayer").hide();
}
