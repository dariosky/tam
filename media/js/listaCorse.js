function moveToNext() {
	// scroll to the first next run of the day
	//console.log("moveToNEXT");
	var next;
	var corseDiOggi = $('.bighour');
	var now = new Date();
	var ora = now.getHours() + ":";
	if(ora.length < 3) {
		ora = "0" + ora;
	}
	var minute = now.getMinutes();
	if(minute < 10)
		minute = "0" + minute;

	var testoAdesso = ora + minute;
	//console.log(testoAdesso);
	corseDiOggi.each(function() {
		var oraCorsa = $(this).text();
		next = this;
		if(oraCorsa >= testoAdesso) {
			return false;
		}
	})
	if(next) {
		//console.log("Mi sposto alla prossima corsa. "+ $(next).text() );
		$.scrollTo(next, 800, {
			offset : {
				top : -100
			}
		});
	}
}

$(function() {
	$(".advFilters input").datepicker();
	//$('.conducenteOkBtn').hide();	// lo usavo quando lasciavo il pulsante to degrade gracefully
	// hide ok button on confirm conducente...
	$('.cbConducente').click(function() {// and submit them on cb
		$(this).hide();
		this.form.submit();
	});

	$(".viaggioId").click(function() {// ma lo mostro se seleziono qualche corsa
		if(this.checked || $(".viaggioId:checked").size() > 0)
			$('#selActions').show();
		else
			$('#selActions').hide();
	});

	$('#linkUrl').click(function() {
		$('#assoType').attr('value', 'link');
	})
	$('#unlinkUrl').click(function() {
		$('#assoType').attr('value', 'unlink');
	})
	$('#selActions a').click(function() {
		$('#viaggioActions').get(0).submit();
		return false;
	})
	//ora, e ogni 10 minuti mi muovo al successivo
	moveToNext();
	setInterval(moveToNext, 10 * 60 * 1000);

	$('#whenSelect').change(function() {
		var selected = $("#whenSelect option:selected").get(0).value;
		if(selected == "advanced") {
			showAdvancedFilter();
		} else {
			$('.advFilters').hide();
		}
	});
	function populateSelect(select, address) {
		$(select).bind('click keydown', function() {
			var is_populated = $(this).data('done');
			if(!is_populated) {
				//console.log("populate " + this);
				$(this).data('done', true);
				// mark the select as populated
				var options = $(this);
				$.getJSON(address, function(result) {
					$.each(result, function() {
						// this è un array: (id, nome, attivo)
						options.append($('<option />').val(this[0]).text(this[1]));
					});
				});
			}
		});
	}

	populateSelect('#select_clienti', '/api/get/cliente/json/');
	populateSelect('#select_conducenti', '/api/get/conducente/json/');

});
function showAdvancedFilter() {
	$('.advFilters').show();
};