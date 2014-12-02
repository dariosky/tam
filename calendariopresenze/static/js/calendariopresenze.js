$(function () {
	var $calendar_man = $('#calendar_man'),
		csrf_token= $('input[type=hidden][name=csrfmiddlewaretoken]').get(0).value;



// hide the "go to day" submit button and react on change
	$('#day').change(function (e) {
		e.target.form.submit();
	});

	$('#changeday_submit').hide();

	$('.calendar_new').on('click', 'button', function (e) {
		// handle the add calendar event
		e.preventDefault();
		var button = e.target,
			$form = $(button.form),
			conducente_id = $("#conducente").val(),
			row = $(button).closest('tr, div, form'),// get the container, we'll check it's children for additional content
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
			data.push({name: "action", value: 'new'});
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

	$calendar_man.on("click", '.del a', function (e) {
		// deleting a calendar, getting id from it's data-id
		e.preventDefault();
		var $this = $(this),
			calendar_id = $this.attr('data-id');
		if (confirm('Sicuro di voler eliminare questo evento?')) {
			$.post('', {action: 'delete', calendar_id: calendar_id, csrfmiddlewaretoken: csrf_token})
				.fail(function (data) {
					alert("Errore nella cancellazione del calendario.\n" + data.responseText)
				})
				.done(function () {
					var deleted_row = $this.closest('tr');
					$(deleted_row).fadeOut();
				});
		}
	});

	$calendar_man.on("click", '.toggle a', function (e) {
		e.preventDefault();
		var $this = $(this),
			calendar_id = $this.attr('data-id');
		$.post('', {action: 'toggle', calendar_id: calendar_id, csrfmiddlewaretoken: csrf_token})
			.fail(function (data) {
				alert("Errore nella commutazione del valore del calendario.\n" + data.responseText)
			})
			.done(function (data) {
				var changed_row = $this.closest('tr');
				console.log(data);
				$(changed_row).replaceWith(data);
			});
	});

});

