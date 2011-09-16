/* funzioni JS comuni ovunque in tam */
if( typeof $ != "undefined") {
	$(document).ready(function() {
		$('.messagebox').css('cursor', 'pointer').click(function() {
			$(this).hide('slow');
			return false;
		})

		$(document).bind('keydown', 'esc', function() {
			var overlay = $("<div style='position:fixed; left:50%; top:50%; width:300px; height:200px; margin-top:-200px; margin-left:-150px; font-size:2em; font-family:Times; text-align:center; z-index:1000;'>" + "Disconnessione in corso" + "</div>");
			$('.content').animate({
				opacity : 0.25
			});
			$('body').append(overlay);
			location.href = '/logout/';
			return false;
		});

		if (typeof moveToNext != "undefined") {
			$(document).bind('keydown', 'n', function() {
				moveToNext();
				return false;
			});
		}
	})
}