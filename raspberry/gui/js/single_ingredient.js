function show_page_single_ingredient(data){
	var e_single_ingredient = clone_from_template("t_single_ingredient");
	var e_form = bar_bot_form("single_ingredient");
	var e_select_ingredient = e_single_ingredient.find("select[name=ingredient]");
	var e_select_amount = e_single_ingredient.find("select[name=amount]");
	$.each(data.ingredients, function(id, ing_data){
		//only show available ingredients
		if( ing_data.port != null ){
			e_select_ingredient.append($("<option/>", {'value':ing_data.id, 'text':ing_data.name}));
		}
	});
	for (let i = 1; i <= 16; i++) {
		e_select_amount.append($("<option/>", {'value':i, 'text':i}));
	}
	e_form.append(e_single_ingredient);
	$("#content").append(e_form);
}
