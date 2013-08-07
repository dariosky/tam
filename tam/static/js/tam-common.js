/* funzioni JS comuni ovunque in tam */
if (typeof $ != "undefined") {
	$(document).ready(function () {
		$('.messages').on("click", function () {
			$(this).fadeOut('slow', function () {
				$(this).remove()
			});
			return false;
		});

		$(document).bind('keydown', 'esc', function () {
			if (!confirm("Sicuro di volerti disconnettere?")) return false;
			var overlay = $("<div style='position:fixed; left:50%; top:50%; width:300px; height:200px; margin-top:-200px; margin-left:-150px; font-size:2em; font-family:Times; text-align:center; z-index:1000;'>" + "Disconnessione in corso" + "</div>");
			$('.content').animate({
				opacity: 0.25
			});
			$('body').append(overlay);
			location.href = '/logout/';
			return false;
		});

		if (typeof moveToNext != "undefined") {
			$(document).bind('keydown', 'n', function () {
				moveToNext();
				return false;
			});
		}
	})
}

function messageBox(msg, classes) {
	var msgBox = $('.messages');
	var message = $('<div class="alert"/>').html(msg);
	if (msgBox.length === 0) {
		msgBox = $('<div />', { "id": 'msg-box', "class": 'messages ' + classes}).hide().prependTo('body');
		msgBox.append(message).fadeIn('slow');
	}
	else {
		msgBox.append(message);
	}
}

window.scrollableGoto = function scrollableGoto(scroller) {
	var scrollParent = scroller.parent();
	//var deltaH = scroller.offset().top - scrollParent.scrollTop();
	//console.log("deltaH:"+deltaH);
	deltaH = 0;
	//console.log("Scroll da "+scroller_min+" a "+scroller_max);
	$(window).scroll(function () {
		if (!scroller.is(":visible")) return;
		var scroller_min = scrollParent.offset().top;
		var scroller_max = scrollParent.offset().top + scrollParent.height();
		//$(window).height()/2
		var newTop = $(window).scrollTop() + deltaH;
		if (newTop > scroller_max) newTop = scroller_max;
		if (newTop < scroller_min) newTop = scroller_min;
		//console.log("set to "+newTop+" ["+scroller_min+","+scroller_max+"]");
		scroller.stop().animate({"top": newTop + "px"}, "fast");
	});
}
