$( function() {
	function wrapPicker(e, options){
		e.wrap("<div></div>");
		var startDiv=e.parent()
		$(startDiv).css("width","200px");
		if (options==undefined) {
			$(startDiv).datepicker(
				{	onSelect: function(dateText){
								e.val(dateText);
							}
				}
			);
		}
		else {
			$(startDiv).datepicker(options);
		}
	}

	function keyupUpdatePicker(input){
		var text=$(input).val();
		try{
			var dat=$.datepicker.parseDate('dd/mm/yy', text);
			var startPicker=$(input).parent();
			startPicker.datepicker('setDate', dat);
		}
		catch(err){/*console.log(err);*/}
	}

	function checkConsistency(){
		//console.log("Check");
		var startPicker=$("#datastart").parent();
		var endPicker=$("#dataend").parent();
		var dataStart=startPicker.datepicker('getDate');
		var dataEnd=endPicker.datepicker('getDate');

		endPicker.datepicker('option', 'minDate', dataStart);	// questo mi cambia la data
		if (dataEnd<dataStart) {
			dataEnd=dataStart;
		}
		endPicker.datepicker('setDate', dataEnd);
		var formattedDate=$.datepicker.formatDate('dd/mm/yy', dataEnd);
		$("#dataend").val(formattedDate);
	}

	wrapPicker($("#datastart"), {	onSelect: function(dateText){
												$("#datastart").val(dateText);
												checkConsistency();
												$("#dataend").focus();
											},
									minDate: 1
								});
	wrapPicker($("#dataend"), {	onSelect: function(dateText){
												$("#dataend").val(dateText);
												$("#copyBtn").focus();
												/*var endPicker=$("#dataend").parent();
												var dataEnd=endPicker.datepicker('getDate');
												console.log(dataEnd);*/
											},
								minDate: 1
								});

	$("#datastart").bind('keyup', function(){
		keyupUpdatePicker(this);
		checkConsistency();
	});
	$("#dataend").bind('keyup', function(){
		keyupUpdatePicker(this);
	});

	keyupUpdatePicker($("#datastart"));
	keyupUpdatePicker($("#dataend"));
	checkConsistency();


});