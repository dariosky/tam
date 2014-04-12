// hide the "go to day" submit button and react on change
$('#day').change(function (e) {
	e.target.form.submit();
});

$('#changeday_submit').hide();

// handle the add calendar event

$('.del a').click(function (e) {
	e.preventDefault();
	var $this = $(this),
		calendar_id = $this.attr('data-id');
	if (confirm('Sicuro di voler eliminare questo evento?')) {
		$.post('', {action: 'delete', calendar_id: calendar_id},function (data) {
				var deleted_row = $this.closest('tr');
				console.log(deleted_row);
				$(deleted_row).fadeOut();
			}
		).fail(function () {
				alert("Errore nella cancellazione del calendario.")
			});
	}

});
