$(function () {
	$("#id_data_0").datepicker({onSelect: function () {
		$('#id_data_1').focus().select();
	} });
	$("#id_data_1").bind('keyup', function () {
			if ((this.value.length > 2) && (this.value.indexOf(":") == -1)) {
				this.value = this.value.slice(0, 2) + ':' + this.value.slice(2);
			}
		}
	);

	$("#id_privato").change(function () {        // mostra /nasconde lo span "passeggero" a seconda il cliente scelto sia 'Privato'
		if ($(this)[0].checked) {
			$("#bloccoPasseggero").show(0);       // nasconde il campo passeggero se non privato
			$("#bloccoCliente").hide(0);
		}
		else {
			$("#bloccoPasseggero").hide(0);
			$("#bloccoCliente").show(0);
		}
	}).change();    // fa scattare il controllo del cliente per nascondere gli altri controlli all'avvio
});
