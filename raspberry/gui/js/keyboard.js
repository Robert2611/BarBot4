var keyboard_target = undefined;
var shift = false;
var capslock = false;


function show_keyboard(target){
	keyboard_target = target;
	//close keyboard on click anywhere in the body
	$("body").click(function(e){
		keyboard_hide();
	});
	//if click was on the target, cancel the event
	target.click(function(ev){
		ev.stopPropagation();
	});
	if($("#keyboard").length == 0)
		keyboard_add();
	else
		$("#keyboard").show();
}
function keyboard_hide(){
	if($("#keyboard").length != 0)
		$("#keyboard").hide();
}

function keyboard_add(){
	e_footer = $("<div/>", {'id':'footer'});
	e_keyboard = $("<div/>", {'id':'keyboard'});
	//first row
	ul_row = $("<ul/>", {'class':'row first'});
	[["1","!"],["2","\""],["3","§"],["4","$"],["5","%"],["6","&"],["7","/"],["8","("],["9",")"],["0","ß"]].forEach(function(name){
		e_li = $("<li/>", {'class':'key symbol', 'click':key_click});
		e_li.append($("<span/>", {'class':'on', 'text':name[1]}));
		e_li.append($("<span/>", {'class':'off', 'text':name[0]}));
		ul_row.append(e_li);
	});
	e_keyboard.append(ul_row);
	//second row
	ul_row = $("<ul/>", {'class':'row second'});
	["q","w","e","r","t","z","u","i","o","p"].forEach(function(name){
		ul_row.append($("<li/>", {'class':'key letter', 'text':name, 'click':key_click}));
	});
	e_keyboard.append(ul_row);
	//third row
	ul_row = $("<ul/>", {'class':'row third'});
	["a","s","d","f","g","h","j","k","l","ö"].forEach(function(name){
		ul_row.append($("<li/>", {'class':'key letter', 'text':name, 'click':key_click}));
	});
	e_keyboard.append(ul_row);
	//fifth row
	ul_row = $("<ul/>", {'class':'row fifth'});
	["y","x","c","v","b","n","m","ä","ü"].forEach(function(name){
		ul_row.append($("<li/>", {'class':'key letter', 'text':name, 'click':key_click}));
	});
	e_keyboard.append(ul_row);
	//last row

	ul_row = $("<ul/>", {'class':'row last'});
	ul_row.append($("<li/>", {'class':'key caps', 'text':'▲', 'click':key_click}));
	//space
	ul_row.append($("<li/>", {'class':'key space', 'text':'\xa0', 'click':key_click}));
	//delete
	ul_row.append($("<li/>", {'class':'key delete', 'text':'←', 'click':key_click}));
	e_keyboard.append(ul_row);

	e_footer.append(e_keyboard);
	$("#wrapper").append(e_footer);
}

function update_shift(){
	if (shift){
		$('.symbol .on').show();
		$('.symbol .off').hide();
		$('.letter').addClass('uppercase');
	}else{
		$('.symbol .off').show();
		$('.symbol .on').hide();
		$('.letter').removeClass('uppercase');
	}
	if(capslock){
		$('.caps').addClass('locked');
	}else{
		$('.caps').removeClass('locked');
	}
}

function key_click(ev){
	//keyboard closes on click of any child of body
	//stop the propagation here to keep it open on key click
	ev.stopPropagation();

	if(keyboard_target == undefined)
		return;
	var e_key = $(this);
	// If it's a lowercase letter, nothing happens to this variable
	var character = e_key.html(); 

	// Shift keys
	if (e_key.hasClass('caps')) {
		//nothing set yet
		if (!shift){
			shift = true;
			capslock = false;
		}else{
			if (capslock){
				shift = false;
				capslock = false;
			}else{
				capslock = true;
			}
		}
		update_shift();
		return false;
	}

	// Delete
	if (e_key.hasClass('delete')) {
		if(keyboard_target.is("input")){
			var content = keyboard_target.val();
			keyboard_target.val(content.substr(0, content.length - 1));
		}else{
			var content = keyboard_target.html();
			keyboard_target.html(content.substr(0, content.length - 1));
		}
		return false;
	}

	// Special characters
	if (e_key.hasClass('symbol')) character = $('span:visible', e_key).html();
	if (e_key.hasClass('space')) character = ' ';
	if (e_key.hasClass('tab')) character = "\t";
	if (e_key.hasClass('return')) character = "\n";

	// Uppercase letter
	if (e_key.hasClass('uppercase')) character = character.toUpperCase();

	// Remove shift once a key is clicked.
	if (!capslock)
		shift = false;
	update_shift();
	// Add the character
	if(keyboard_target.is("input")){
		keyboard_target.val(keyboard_target.val() + character);
	}else{
		keyboard_target.html(keyboard_target.html() + character);
	}
}
