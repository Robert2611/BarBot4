function show_page_listrecipes(data){
	//MAIN
	//loop through recipes
	var e_list = clone_from_template("t_list");
	data.recipes.forEach(function(recipe){
		var e_cocktail = clone_from_template("t_cocktail");
		e_cocktail.find('.header>span').html(recipe.name);
		if(recipe.available){
			$(e_cocktail.find('.order')).click(function(){
				get_bar_bot_data({"action" : "order", "id" : recipe.id});
			});
		}else{
			e_cocktail.find('.order').remove()
		}
		$(e_cocktail.find('.edit')).click(function(){
			load_page("edit", {'action':'getrecipe', 'id':recipe.id});
		});
		//loop through items
		recipe.items.forEach(function(item){
			var e_cocktail_ingredient = clone_from_template("t_cocktail_ingredient");
			e_cocktail_ingredient.find(".amount").html(item.amount);
			e_cocktail_ingredient.find(".ingredient").html(item.name);
			if(!item.available)
				e_cocktail_ingredient.addClass("not_available");
			e_cocktail.find('.ingredients').append(e_cocktail_ingredient);
		});
		e_list.find('.cocktails').append(e_cocktail);
	});
	$('#content').append(e_list);
}
