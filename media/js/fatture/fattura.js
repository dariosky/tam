function rowProcess(row){
	var id = row.find('input:hidden').val();
	var price=parseFloat(row.find('#riga-prezzo-'+id).text());
	var iva=parseFloat(row.find('#riga-iva-'+id).text());
	var qta=parseFloat(row.find('#riga-qta-'+id).html());
	return {
			id:id,
			price:price,
			iva:iva,
			qta:qta,
			imponibile:qta*price,
			tot_iva:Math.round(price*qta*iva)/100,
			tot_riga:Math.round(price*qta*(100+iva))/100
		}
}

function ricalcolaTotali(){
	console.log("Ritotalo")
	var imponibile=0;
	var iva=0;
	var totale=0;
	 
	var righe=$('#righe .priceRow').each(function(){
		var rowData=rowProcess( $(this) );
		iva= iva + rowData.tot_iva;
		imponibile += rowData.imponibile;
		totale += rowData.tot_riga;
	})
	$('#tot_imponibile').text(imponibile.formatMoney(2, ',', '.' ));
	$('#tot_iva').text(iva.formatMoney(2, ',', '.' ));
	$('#tot_totale').text(totale.formatMoney(2, ',', '.' ));
	
}

function editableSubmit(content) {
	var pre = $.trim(content.previous), post=$.trim(content.current)
	if (post!=pre || true) {
		var $this = $(this);
		var id = $this.attr('id');
		$.post("", {action:"set",
					id:id,
					value:post
					})
		.complete(function(xhr, data){
			if (xhr.status==200) {
				//console.log("set successful")
				var row = $this.closest('#righe .priceRow');
				if (row.length==1) {
					rowData=rowProcess(row);
					console.log("Modifica ad una riga. Ricomputo.");
					var $totaleRiga=row.find('.totale').text(rowData.tot_riga.formatMoney(2, ',', '.' ));
					//TODO: Dovrei formattare le celle appena inserite, se sono della classe price
					ricalcolaTotali();
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
// TODO: Editable Data fattura