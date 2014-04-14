// hide the "go to day" submit button and react on change
$('#day').change(function (e) {
	e.target.form.submit();
});

$('#changeday_submit').hide();

// handle the add calendar event

$('#calendar_man').on("click", '.del a', function (e) {
	e.preventDefault();
	var $this = $(this),
		calendar_id = $this.attr('data-id');
	if (confirm('Sicuro di voler eliminare questo evento?')) {
		$.post('', {action: 'delete', calendar_id: calendar_id})
			.fail(function (data) {
				alert("Errore nella cancellazione del calendario.\n" + data.responseText)
			})
			.done(function () {
				var deleted_row = $this.closest('tr');
				$(deleted_row).fadeOut();
			});
	}

});

$('.calendar_new').on('click', 'button', function (e) {
	e.preventDefault();
	var button = e.target,
		$form = $(button.form),
		conducente_id = $("#conducente").val(),
		row = $(button).closest('tr'),
		text_fields = $(row).find("input[type=text]"),
		valid = true;
	$.each(text_fields, function () {
		var $field = $(this);
		if (!$field.val()) {
			$field.addClass('error').one('keydown', function () {
				$(this).removeClass('error')
			});
			valid = false;
		}
	});
	if (valid) {
		var data = $form.serializeArray();
		data.push({name: "conducente", value: conducente_id});
		/* add text fields to data */
		$.each(text_fields, function () {
			data.push({name: this.name, value: this.value});
		});
		var caltype = $form.find("input[name=type]").val();	// remember the caltype
		$.post('', data)
			.done(function (data) {
				//console.log("ADDED", data)
				var body = $('#caltype_' + caltype).find('tbody');
				body.append(data);
			})
			.fail(function (data) {
				alert("Errore nell'inserimento del calendario.\n" + data.responseText)
			});
	}
});
