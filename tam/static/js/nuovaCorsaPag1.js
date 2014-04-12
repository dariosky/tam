$(function () {
	$("#id_data_0").datepicker({onSelect: function () {
		$('#id_data_1').focus().select();
	} });

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
