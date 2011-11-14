/* funzioni JS comuni ovunque in tam */
if( typeof $ != "undefined") {
	$(document).ready(function() {
		$('.messagebox').live("click", function() {
			$(this).fadeOut('slow', function(){$(this).remove()});
			return false;
		})

		$(document).bind('keydown', 'esc', function() {
			if (!confirm("Sicuro di volerti disconnettere?")) return;
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

function messageBox(msg, classes) {
  var msgBox = $('.messagebox');
  var message = $('<li />').html(msg);
  if (msgBox.length === 0) {
      msgBox = $('<div />', { "id":'msg-box', "class":'messagebox '+classes}).hide().prependTo('body');
      msgBox.append(message).fadeIn('slow');
  }
  else {
  	msgBox.append(message);
  }
}