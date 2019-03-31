function show_page_edit(data){
	ingredients = data.ingredients;
	recipe = data.recipe;
	message = data.message;

	var e_form = bar_bot_form('saverecipe');
	var e_edit = CloneFromTemplate("t_edit");

	//initialize if new recipe is to be created
	if(recipe == undefined){
		recipe = {"name":"", "id":-1, "items":[] };
		e_edit.find("h2").html("Neues Rezept");
	}
	
	//message
	e_message = e_edit.find('.message');
	if( message == "created" ){
		e_message.html("Neues Rezept wurde angelegt.");
	}else if( message == "updated" ){
		e_message.html("Rezept wurde gespeichert.");
	}else if( message == "nothing_changed" ){
		e_message.html("Rezept wurde nicht verändert.");
	}else{
		e_message.remove();
	}

	e_edit.find('[name=rid]').val(recipe.id);
	e_edit.find('[name=name]')
		.val(recipe.name)
		.focus(function(){
			show_keyboard(e_name);
		});
	e_list = e_edit.find('ul');
	var e_add_ingredient = e_list.find('li.add_ingredient');
	if(recipe.items.length > 0){
		recipe.items.forEach(function(recipe_item){
			edit_create_recipe_item(recipe_item, ingredients).insertBefore(e_add_ingredient);
		});
	}else{
		e_list.append(edit_create_empty_recipe_item(ingredients));
	}
	e_add_ingredient.click(function(){
		edit_create_empty_recipe_item(ingredients).insertBefore(e_add_ingredient);
	});
	e_form.append(e_edit);
	$('#content').append(e_form);
}

function edit_create_empty_recipe_item(ingredients){
	return edit_create_recipe_item({"id":-1, "iid":-1, "amount":-1},ingredients);
}

function edit_create_recipe_item(recipe_item, ingredients){
	var e_list_item = CloneFromTemplate("t_edit_ingredient");
	e_list_item.find('[name="id[]"]').val(recipe_item.id);
	//select ingredient
	e_select_ingredient = e_list_item.find('[name="ingredient[]"]');
	e_select_ingredient.append($("<option/>", {'value':-1, 'text':'-'}));
	$.each(ingredients, function(id, ing_data){
		e_option = $("<option/>", {'value':id, 'text':ing_data.name});
		if(recipe_item.iid == id)
			e_option.prop("selected", "selected");
		e_select_ingredient.append(e_option);
	});

	//select amount
	e_select_amount = e_list_item.find('[name="amount[]"]');
	e_select_amount.append($("<option/>", {'value':-1, 'text':'-'}));
	for (let i = 1; i <= 16; i++) {
		e_option = $("<option/>", {'value':i, 'text':i});
		if(recipe_item.amount == i)
			e_option.prop("selected", "selected");
		e_select_amount.append(e_option);
	}
	return e_list_item;
}
