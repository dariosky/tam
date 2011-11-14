function editableSubmit(content) {
	if (content.current!=content.previous || true) {
		var $this = $(this);
		var id = $this.attr('id');
		var pre = $.trim(content.previous), post=$.trim(content.current)
		$.post("", {action:"set",
					id:id,
					value:post
					})
		.complete(function(xhr, data){
			if (xhr.status==200) {
				//console.log("set successful")
				var row = $this.closest('#righe tr');
				if (row.length==1) {
					console.log("Modifica ad una riga. Ricomputo.");
					var id = row.find('input:hidden').val();
					var prezzo=parseFloat(row.find('#riga-prezzo-'+id).html());
					var qta=parseFloat(row.find('#riga-qta-'+id).html());
					var iva=parseFloat(row.find('#riga-iva-'+id).html());
					var prezzoRiga = Math.round(prezzo*qta*(100+iva))/100;
					console.log("prezzo:" +prezzo, "qta:"+qta, "iva:"+iva);
					console.log("tot:"+prezzoRiga);
					console.log(row);
					var $totaleRiga=row.find('.totale').html(prezzoRiga.formatMoney(2, ',', '.' ));
					
					$this.find()
				}
			}
			else {
				messageBox(xhr.responseText);
				$this.html(pre);
			}
		})
	}
}

Number.prototype.formatMoney = function(c, d, t){
	var n = this, c = isNaN(c = Math.abs(c)) ? 2 : c, d = d == undefined ? "," : d, t = t == undefined ? "." : t, s = n < 0 ? "-" : "", i = parseInt(n = Math.abs(+n || 0).toFixed(c)) + "", j = (j = i.length) > 3 ? j % 3 : 0;
	return s + (j ? i.substr(0, j) + t : "") + i.substr(j).replace(/(\d{3})(?=\d)/g, "$1" + t) + (c ? d + Math.abs(n - i).toFixed(c).slice(2) : "");
 };


// creo le azioni in Ajax per la cancellazione
$('.delrow').live("click",
	function(){
		if (!confirm('Sicuro di voler cancellare la riga?')) return;
		var row = $(this).closest('tr');
		$.post("",
				{action:'delete-row', row:row.find('input:hidden').val()}
		)
		.complete(function(xhr, data){
			if (xhr.status==200) {
				row.hide('fast', function(){row.remove()})
			}
			else {
				messageBox(xhr.responseText);
			}
		})
	}
);

// creazione di una nuova riga
$('#newRow').click(
	function(){
		var lastRow = $(this).closest('tr');
		$.post("", {action:'append-row'} )
		.complete(function(xhr, data){
			if (xhr.status==200) {
				var newRow = $(xhr.responseText); // return the row to insert
				$(newRow).find('.editable').editable({onSubmit:editableSubmit}); // keep things editable
				lastRow.before(newRow);
			}
			else {
				messageBox(xhr.responseText);
			}
		})
	}
)

$('div.editable').editable({type:'textarea', onSubmit:editableSubmit});
$('span.editable').editable({onSubmit:editableSubmit});
$('td.editable').editable({onSubmit:editableSubmit});
/* TODO: Editable Data fattura */