/* funzioni JS comuni ovunque in tam */
if (typeof $ != "undefined") {
	$(document).ready(function(){
		$('.messagebox').css('cursor','pointer').click(
				function(){
					$(this).hide('slow');
					return false;
				})
	})
}