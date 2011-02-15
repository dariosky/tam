/* funzioni JS comuni ovunque in tam */
if (typeof $ != "undefined") {
	$(document).ready(function(){
		$('.messagebox').append($('<li><a href="#">chiudi messaggio</a></li>').click(function(){
			$(this).parent().hide('slow');
			return false;
		}));
	});
}
