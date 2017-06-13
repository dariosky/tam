$(function () {
	var csrf_token = $('input[type=hidden][name=csrfmiddlewaretoken]').get(0).value;

	function myParse(string) {
		string = string.replace(",", ".");
		return parseFloat(string)
	}

	function rowProcess(row) {
		var id = row.find('input:hidden').val();
		var price = myParse(row.find('#riga-prezzo-' + id).text() || "0");
		var iva = myParse(row.find('#riga-iva-' + id).text() || "0");
		var qta = myParse(row.find('#riga-qta-' + id).html() || "0");
		//console.log("Valori letti", qta, price, iva);
		var val_imponibile = Math.round(price * qta * 100) / 100;
		var val_iva = Math.round(price * qta * iva) / 100;
		var val_totale = val_imponibile + val_iva;
		//console.log("Valori:", val_imponibile, val_iva, val_totale);
		return {
			id: id,
			price: price,
			iva: iva,
			qta: qta,
			val_imponibile: val_imponibile,
			val_iva: val_iva,
			val_totale: val_totale
		}
	}

	function ricalcolaTotali() {
		var imponibile = 0;
		var iva = 0;
		var totale = 0;
		var righe = $('#righe').find('.priceRow').each(function () {
			var rowData = rowProcess($(this));
			iva = iva + rowData.val_iva;
			imponibile += rowData.val_imponibile;
			totale += rowData.val_totale;
		});
		$('#tot_imponibile').text(imponibile.formatMoney(2, ',', '.'));
		$('#tot_iva').text(iva.formatMoney(2, ',', '.'));
		$('#tot_totale').text(totale.formatMoney(2, ',', '.'));

	}

	function editableSubmit(content) {
		var pre = $.trim(content.previous), post = $.trim(content.current);
		if (post !== pre) {
			var $this = $(this);
			var id = $this.attr('id');
			$.post("", {
				action: "set",
				id: id,
				value: post,
				csrfmiddlewaretoken: csrf_token
			})
				.complete(function (xhr, data) {
					if (xhr.status === 200) {
						//console.log("set successful")
						var row = $this.closest('#righe .priceRow');
						if (row.length === 1) {
							var rowData = rowProcess(row);
							//console.log("Modifica ad una riga. Ricomputo.");
							var $totaleRiga = row.find('.totale').text(rowData.val_totale.formatMoney(2, ',', '.'));
							ricalcolaTotali();
						}
					}
					else {
						messageBox(xhr.responseText || "Si è verificato un errore", "error");
						$this.html(pre);
					}
				});
		}
	}

	Number.prototype.formatMoney = function (c, d, t) {
		var n = this, c = isNaN(c = Math.abs(c)) ? 2 : c, d = d == undefined ? "," : d,
			t = t == undefined ? "." : t, s = n < 0 ? "-" : "",
			i = parseInt(n = Math.abs(+n || 0).toFixed(c)) + "", j = (j = i.length) > 3 ? j % 3 : 0;
		return s + (j ? i.substr(0, j) + t : "") + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + t) + (c ? d + Math.abs(n - i).toFixed(c).slice(2) : "");
	};


// creo le azioni in Ajax per la cancellazione
	$('.delrow').on("click",
		function () {
			if (!confirm('Sicuro di voler cancellare la riga?')) return;
			var row = $(this).closest('tr');
			$.post("",
				{
					action: 'delete-row', row: row.find('input:hidden').val(),
					csrfmiddlewaretoken: csrf_token
				}
			)
				.complete(function (xhr, data) {
					if (xhr.status === 200) {
						row.hide('fast', function () {
							row.remove();
							ricalcolaTotali();
						});

					}
					else {
						messageBox(xhr.responseText || "Si è verificato un errore", "error");
					}
				})
		}
	);

	$('.delfat').on("click",
		function () {
			if (!confirm('Sicuro di voler cancellare l\'intera fattura?')) return false;
			$.post("",
				{action: 'delete-fat', csrfmiddlewaretoken: csrf_token}
			)
				.complete(function (xhr, data) {
					if (xhr.status === 200) {
						document.location = xhr.responseText;
					}
					else {
						messageBox(xhr.responseText || "Si è verificato un errore", "error");
					}
				})
		}
	);

// creazione di una nuova riga
	$('#newRow').click(
		function () {
			var lastRow = $(this).closest('tr');
			$.post("", {action: 'append-row', csrfmiddlewaretoken: csrf_token})
				.complete(function (xhr, data) {
					if (xhr.status === 200) {
						var newRow = $(xhr.responseText); // return the row to insert
						$(newRow).find('.editable').editable({onSubmit: editableSubmit}); // keep things editable
						lastRow.before(newRow);
					}
					else {
						messageBox(xhr.responseText || "Si è verificato un errore", "error");
					}
				})
		}
	);

	$('div.editable').editable({type: 'textarea', onSubmit: editableSubmit});
	$('span.editable').editable({onSubmit: editableSubmit});
	$('td.editable').editable({onSubmit: editableSubmit});

// TODO: Editable Data fattura
});
