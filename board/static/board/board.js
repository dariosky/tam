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
                $status.fadeOut('slow');
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
        //if (!message) return false;
        if (socket.socket.connected) {
            socket.emit('message', message);
            $message_input.val('');
            return false;
        }
        // using standard submit
        console.log("Standard submit");
        $submit.prop('disabled', true);
        return true;
        //message = 'messaggio di prova';

    });


    socket.on('message', function (message) {
        addMessage(message, true);
    });

    function processActions(actionList) {
        for (var i = 0; i < actionList.length; i++) {
            var actionDict = actionList[i];
            for (var action in actionDict) {
                console.log(action);
                var arg = actionDict[action];
                if (action == "show") {
                    $(arg).stop().fadeIn().css("display", "inline-block");    // show action
                }
                else if (action == 'hide') {
                    $(arg).fadeOut();    // hide action
                }
                else if (action == 'enableSubmit') {
                    $submit.prop('disabled', false);
                }
                else if (action == 'disableSubmit') {
                    $submit.prop('disabled', true);
                }
                else if (action == 'successMessage') {
                    statusMessage(arg, 'success', 1500);
                }
                else if (action == "errorMessage") {
                    statusMessage(arg, 'error');
                }
                else if (action == "remove") {
                    $(arg).remove();    // delete from DOM
                }
                else {
                    alert("Unknown action " + action);
                }
            }
        }
    }

    socket.on('error', function (message, actionList) {
        if (message) {
            statusMessage(message, 'error');
        }
        else {
            statusMessage('Errore di connessione.', 'error');
        }
        if (actionList) {
            processActions(actionList)
        }
    });

    socket.on('connect', function () {
        //statusMessage('Controllo credenziali...');
    });

    socket.on('protocol', function (actionList) {
        processActions(actionList);
    });

    /* Delete the message */
    $('.del-mark').live('click', function () {
        var message = $(this).parent('.message')[0];
        if (message.id.substr(0, 8) != "message-") throw("Delete a non message?");
        var id = message.id.substr(8);
        console.log("deleting message", id);
        if (socket.socket.connected) {
            socket.emit('deleteMessage', id);
            $(message).fadeOut('slow');
            return false;
        }
        else {
            var tempForm = $('<form/>', {method:'POST', action:''}).css('display', 'none').appendTo($('body'));
            tempForm.append($('<input/>', {name:'deleteMessage', value:id}));
            tempForm.submit();
            return false;
        }
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
}
