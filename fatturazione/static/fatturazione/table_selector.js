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
	var nextRows = $(questaRiga).nextAll().addBack(); // tutte le prossime righe
	
	var seleziono = !$(questaRiga).find("input[type=checkbox]").prop("checked");
	//console.log(seleziono?"Seleziono":"Deseleziono" + " le prossime ", nextRows.length, " righe.");
	var righe=0;
	nextRows.each(function(){
		if (this!=questaRiga && $(this).has(".clientSelect").length){
			return false;	// stop the loop
		}
		else {
			righe += 1;
			$(this).find("input[type=checkbox]").prop("checked", seleziono);
		}

	});
	//console.log(righe + ' righe.')
}