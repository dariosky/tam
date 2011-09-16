function table_selector(global_check, table) {

	$('input[type=checkbox]', table).not(global_check).change(function() {
		// changed a single table check
		var checkboxes = $("input[type=checkbox]", table).not(global_check);
		if(this.checked == true) {
			console.log("check");
			var areAllSelected = (checkboxes.not(":checked").length == 0);
			if(areAllSelected) {
				$(global_check).attr("checked", true);
			}
		} else {
			console.log("uncheck");
			var areNoneSelected = (checkboxes.filter(":checked").length == 0);
			if(areNoneSelected) {
				$(global_check).attr("checked", false);
			}
		}
	});
	
}