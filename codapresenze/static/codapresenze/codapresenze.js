$(document).ready(function () {
    var auto_refresh_interval = 60;
    var count = auto_refresh_interval;   // update every TOT seconds
    var countdown;
    var counter_object = $("#counter");

    var doRequestCoda = function (data) {
        $.post('', data)
            .fail(function (data) {
                console.log("I've got an error.");
                console.log(data);
            })
            .done(function (coda) {
                console.log("Success", coda);
                ricreaCoda(coda);
            });
    }

    $("#codacomandi div").click(function () {
        count = auto_refresh_interval;  // will wait
        var data = {place: $(this).html()};
        if (this.id == 'dequeue') {
            data = {dequeue: true};
        }
        doRequestCoda(data);
        return false;
    });

    /* autorefresh */

    countdown = setInterval(function () {
        if (count <= 10) {
            counter_object.html("Aggiornamento tra " + count + " secondi");
            if (count == 0) {
                //window.location.reload();
                doRequestCoda();
                count = auto_refresh_interval;
                //clearInterval(countdown);
            }
        }
        count--;
    }, 1000);

});

function ricreaCoda(coda) {
    /* riceve una lista di oggetti e popola il DOM con la coda */
    var coda_container_obj = $('#coda');
    coda_container_obj.empty();
    var oggiString = (new Date()).toDateString();
    for (var i = coda.length - 1; i >= 0; i--) {
        var e = coda[i];
        var e_obj = $("<div />");
        console.log(e);
        var data = new Date(e['data'])
        var testo = e['utente'];
        if (oggiString == data.toDateString()) {
            testo += "\ndalle " + data.getHours() + ":" + data.getMinutes();
        }
        else {
            testo += "\ndal " + data.toLocaleString();
        }
        //testo += "\n" + e['luogo'];
        e_obj.html(testo);
        e_obj.append($("<span />", {class: "place"}).html(e['luogo']));
        if (e['utente'] == username) {    // global variable
            e_obj.addClass('current')
        }
        coda_container_obj.prepend(e_obj);
    }
    coda_container_obj.append($("<br />").css("clear", "both"));
}