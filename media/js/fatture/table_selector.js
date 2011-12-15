function table_selector(global_check, table) {
	/*
	 * Onchange dei singoli checkbox della lista.
	 * Controllo tutti i checkbox nella tabella tranne quello "master"
	 * se sono tutti selezionati spunto il master, se nessuno è selezionato
	 * de-spunto il master, altrimenti rendo il master grigietto
	 */ 
	$('input[type=checkbox]', table).not(global_check).change(function() {
		// changed a single table check
		var checkboxes = $("input[type=checkbox]", table).not(global_check);
		if(this.checked == true) {
			var areAllSelected = (checkboxes.not(":checked").length == 0);
			if(areAllSelected) {
				//console.log("all");
				$(global_check).attr("checked", true);
				return;
			}
		} else {
			var areNoneSelected = (checkboxes.filter(":checked").length == 0);
			if(areNoneSelected) {
				//console.log("none");
				$(global_check).attr("checked", false);
				return;
			}
		}
		$(this).css("background")
		//console.log("partial");
	});
	
	$(global_check).change(function(){
		var checkboxes = $("input[type=checkbox]", table).not(global_check);
		checkboxes.attr("checked", this.checked);
	});
	
}

function selectCheckboxToNext(from) {
	/* TODO: popolo con tutte le checkbox da-a
	 * se sono tutte selezionate le deseleziono altrimenti le seleziono
	 */
	var questaRiga = $(from).closest("tr")[0];
	var nextRows = $(questaRiga).nextAll().andSelf(); // tutte le prossime righe
	
	//console.log("Processo le prossime ", nextRows.length, " righe.")
	nextRows.each(function(){
		//console.log("passo la linea", this);
		if (this!=questaRiga && $(this).has(".clientSelect").length){
			//console.log("Esco", this, "ha clienti");
			return false;	// stop the loop
		}
		else {
			//console.log("Seleziono la riga", this);
			$(this).find("input[type=checkbox]").attr("checked", true);
		}
	});
}

function scrollableGoto(scroller) {
	var scrollParent = scroller.parent();
	//var deltaH = scroller.offset().top - scrollParent.scrollTop();
	//console.log("deltaH:"+deltaH);
	deltaH = 0;
	//console.log("Scroll da "+scroller_min+" a "+scroller_max);
	$(window).scroll(function(){
		if (!scroller.is(":visible")) return;
		var scroller_min = scrollParent.offset().top;
		var scroller_max = scrollParent.offset().top+scrollParent.height();
		//$(window).height()/2
		var newTop = $(window).scrollTop()+deltaH;
		if (newTop>scroller_max) newTop=scroller_max;
		if (newTop<scroller_min) newTop=scroller_min;
		//console.log("set to "+newTop+" ["+scroller_min+","+scroller_max+"]");
		scroller.stop().animate({"top": newTop+"px"}, "fast");
	});
}