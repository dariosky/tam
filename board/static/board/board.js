$(function () {
    function statusMessage(message, class_name, hideAfter) {
        // Set the status message with classtype and hide it after a timeout
        var oldTimeout = $status.data('timer');
        if (oldTimeout) {
            clearTimeout(oldTimeout);
            $status.removeData('timer');
            $.removeData($status, 'timer');
        }
        console.log(message);
        $status.removeClass().text(message).show();
        if (class_name) $status.addClass(class_name);
        if (hideAfter) {
            var timer = setTimeout(function () {
                $status.hide('slow');
            }, hideAfter);
            $status.data('timer', timer);
        }
    }

    var $form = $('#boardForm');
    var $message_input = $form.find('#m');
    var $status = $("#status");
    var $submit = $("#newMessageBoard input[type=submit]");

    socket = io.connect("http://localhost:8080/board"
        //{ resource: 'backeca/socket.io' }
    );

    $form.bind('submit', function () {
        var message = $message_input.val();
        //message = 'messaggio di prova';
        if (!message) return false;
        socket.emit('message', message);
        $message_input.val('');
        return false;
    });


    socket.on('message', function (message) {
        addMessage(message);
    });

    socket.on('error', function (data) {
        if (data) {
            statusMessage(data, 'error');
        }
        else {
            statusMessage('Errore di connessione.', 'error');
        }
        $submit.prop('disabled', true);
    });

    socket.on('connect', function () {
        //statusMessage('Controllo credenziali...');
    });

    socket.on('connectStatus', function (result) {
        if (result) {
            statusMessage('Connesso come ' + result + '.', 'success', 1500);
        }
        else {
            statusMessage('Credenziali non valide.', 'error');
        }
        $submit.prop('disabled', !result);
    });

});

addMessage = function(message) {
    var messageDiv = $('<div/>', {class:'message', id:'message-'+message.id});
    var headDiv = $('<div/>', {class:'head'}).appendTo(messageDiv);
    headDiv.append($('<div/>', {class:'date'}).html(message.d));
    headDiv.append($('<div/>', {class:'author'}).html(message.a))
    console.log("message:", message.m, 'from:', message.a);
    $('<div/>', {class:'m'}).text(message.m).appendTo(messageDiv);
    $('#board').append(messageDiv);
}
