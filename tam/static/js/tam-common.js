/* Common JS functions for TAM */
if (typeof $ !== "undefined") {
    $(document).ready(function () {
        $('body').on("click", '.messages', function (e) {
            var $message = $(e.target);
            $message.fadeOut('slow', function () {
                $message.remove();
            });
            return false;
        });

        $(document).bind('keydown', 'esc', function () {
            if (!confirm("Sicuro di volerti disconnettere?")) {
                return false;
            }
            var overlay = $("<div id='overlay'>" + "Disconnessione in corso" + "</div>");
            $('.content').animate({
                opacity: 0.25
            });
            $('body').append(overlay);
            location.href = '/logout/';
            return false;
        });

        if (typeof moveToNext !== "undefined") {
            $(document).bind('keydown', 'n', function () {
                moveToNext();
                return false;
            });
        }

        var $clock = $('.clock');
        if ($clock.length) {
            var current_time;

            var zeroPadded = function (value) {
                return ("0" + value).slice(-2);
            };

            var updateClock = function () {
                var now = new Date(),
                    timeString = zeroPadded(now.getHours()) + ":" + zeroPadded(now.getMinutes());
                if (timeString !== current_time) {
                    $clock.text(timeString);
                    current_time = timeString;
                }
            };

            setInterval(updateClock, 1000);
            updateClock();
        }

    });
}

function messageBox(msg, classes) {
    var msgBox = $('.messages');
    var message = $('<div class="alert"/>').html(msg);
    if (classes) {
        message.addClass(classes);
    }
    if (msgBox.length === 0) {
        msgBox = $('<div />', {
            "id": 'msg-box',
            "class": 'messages'
        }).hide().prependTo('body');
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
    var deltaH = 0;
    //console.log("Scroll da "+scroller_min+" a "+scroller_max);
    $(window).scroll(function () {
        if (!scroller.is(":visible")) {
            return;
        }
        var scroller_min = scrollParent.offset().top;
        var scroller_max = scrollParent.offset().top + scrollParent.height();
        //$(window).height()/2
        var newTop = $(window).scrollTop() + deltaH;
        if (newTop > scroller_max) {
            newTop = scroller_max;
        }
        if (newTop < scroller_min) {
            newTop = scroller_min;
        }
        //console.log("set to "+newTop+" ["+scroller_min+","+scroller_max+"]");
        scroller.stop().animate({"top": newTop + "px"}, "fast");
    });
};

if ($.datepicker) {
    $(".datepicker").datepicker();
}
