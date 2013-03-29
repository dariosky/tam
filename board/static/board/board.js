$(function () {
    function statusMessage(message, class_name, hideAfter) {
        // Set the status message with classtype and hide it after a timeout
        var oldTimeout = $status.data('timer');
        if (oldTimeout) {
            clearTimeout(oldTimeout);
            $status.removeData('timer');
        }
        //console.log(message);
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
    var $submit = $("#submit_btn");

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
        addMessage(message, true);
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


    $('.del-mark').live('click', function () {
        var message = $(this).parent('.message')[0];
        console.log(this);
        console.log(message);
        console.log(message.id);
        if (message.id.substr(0, 8) != "message-") throw("Delete a non message?");
        var id = message.id.substr(8);
        console.log("deleting message", id);
        socket.emit('deleteMessage', id);
        // TODO: Nascondo il messaggio (lo cancellerò quando arriva la conferma)
        return false;
    });

});

function addMessage(message, hilight) {
    var newHilightDuration = 5000;
    var messageDiv = $('<div/>', {class: 'message', id: 'message-' + message.id});
    var headDiv = $('<div/>', {class: 'head'}).appendTo(messageDiv);
    headDiv.append($('<div/>', {class: 'date'}).html(message.d));
    headDiv.append($('<div/>', {class: 'author'}).html(message.a));
    var attachment = message.f;
    if (attachment) {
        headDiv.append($("<div/>", {class: 'attachment-mark'}));
    }
    console.log("message:", message.m, 'from:', message.a);
    $('<div/>', {class: 'm'}).text(message.m).appendTo(messageDiv);
    if (attachment) {
        var attachDiv = $('<div/>', {class: 'attachment'});
        attachDiv.append($('<a/>', {href: attachment.url}).html(attachment.name));
        messageDiv.append(attachDiv);
    }
    messageDiv.append($('<div/>', {class: 'del-mark'}));
    if (hilight) {
        messageDiv.addClass('new').hide();
    }
    $('#board').prepend(messageDiv);
    if (hilight) {
        messageDiv.fadeIn('slow').css("display", "inline-block").delay(newHilightDuration).queue(function (next) {
            $(this).removeClass("new");
            next();
        });
    }
};
