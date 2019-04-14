function show_page_statistics(data){
    var e_statistics = clone_from_template("t_statistics");
    var e_select_partydate = e_statistics.find("select[name=partydate]");
    e_select_partydate.change(function(){
        load_page("statistics", {'date':$(this).val()});
    });
    $.each(data.parties, function(id,party){
        e_option = $("<option/>", {'value':party.partydate, 'text':party.partydate})
        if(party.partydate == data.date)
            e_option.prop("selected", "selected");
        e_select_partydate.append(e_option);
    });
    e_statistics.find(".total_count").html(data.total_count);
    e_statistics.find(".total_amount").html(Math.round(data.total_amount*10)/10);
    createCocktailCountGraph(e_statistics.find(".graph_cocktail_count"), data);
    createIngredientsAmountGraph(e_statistics.find(".graph_ingredients_amount"), data);
    createCocktailsByTimeGraph(e_statistics.find(".graph_cocktails_by_time"), data);
	$("#content").append(e_statistics);
}

function createCocktailCountGraph(container, data){
    var max = 1.0;
    $.each(data.cocktail_count, function(id, cocktail){
        if(cocktail.count > max)
            max = cocktail.count;
    });
    $.each(data.cocktail_count, function(id, cocktail){
        var e_row = clone_from_template("t_bar_chart_row");
        e_row.find(".bar_chart_label").html(cocktail.name);
        e_row.find(".bar_chart_value").html(cocktail.count);
        e_row.find(".bar_chart_bar_fill").width( ( cocktail.count/max*100 ) + "%");        
        container.append(e_row);
    });
}

function createIngredientsAmountGraph(container, data){  
    var max = 1.0;
    $.each(data.ingredients_amount, function(id, ingredient){
        if(ingredient.liters > max)
            max = ingredient.liters;
    });
    $.each(data.ingredients_amount, function(id, ingredient){
        var e_row = clone_from_template("t_bar_chart_row");
        e_row.find(".bar_chart_label").html(ingredient.ingredient);
        e_row.find(".bar_chart_value").html(ingredient.liters);
        e_row.find(".bar_chart_bar_fill").width( ( ingredient.liters/max*100 ) + "%");        
        container.append(e_row);
    });
}

function createCocktailsByTimeGraph(container, data){
    var max = 1.0;
    $.each(data.cocktails_by_time, function(id, hour){
        if(hour.count > max)
            max = hour.count;
    });
    $.each(data.cocktails_by_time, function(id, hour){
        var e_row = clone_from_template("t_bar_chart_row");
        e_row.find(".bar_chart_label").html(hour.hour);
        e_row.find(".bar_chart_value").html(hour.count);
        e_row.find(".bar_chart_bar_fill").width( ( hour.count/max*100 ) + "%");        
        container.append(e_row);
    });
}
