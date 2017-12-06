$(document).ready(function () {
	var auto_refresh_interval = 90
	var count = auto_refresh_interval   // update every TOT seconds
	//var countdown;
	var counter_object = $("#counter"),
		csrf_token = $('input[type=hidden][name=csrfmiddlewaretoken]').get(0).value

	var doRequestCoda = function (data) {
		if (typeof(data) === 'undefined') {
			data = {}
		}
		data.csrfmiddlewaretoken = csrf_token
		$.post('', data)
			.fail(function (data) {
				alert("C'è stato un errore.")
				window.location.reload()
			})
			.done(function (coda) {
				//console.log("Success. Elementi:", coda.length);
				ricreaCoda(coda)
			})
	}

	$("#codacomandi").find("div").click(function () {
		var data
		if (this.id === "dequeue") {
			data = {dequeue: true}
		}
		else if (this.id === "refresh") {
			data = {refresh: true}
			if (count >= auto_refresh_interval - 5) {
				// no a refresh troppo frequenti
				console.log("Refresh troppo frequente")
				return false
			}
		}
		else {
			data = {place: $(this).html()}
		}
		count = auto_refresh_interval  // will wait
		counter_object.hide()
		var user_obj = $('#conducente').find('option:selected')
		if (user_obj) {
			data.user = user_obj.html()
		}

		doRequestCoda(data)
		return false
	})

	/* autorefresh */

	//countdown =
	setInterval(function () {
		if (count <= 10) {
			counter_object.show()
			counter_object.html("Aggiornamento tra " + count + " secondi")
			if (count === 0) {
				//window.location.reload();
				counter_object.hide()
				doRequestCoda()
				count = auto_refresh_interval
				//clearInterval(countdown);
			}
		}
		count--
	}, 1000)

})

function ricreaCoda(coda) {
	/* riceve una lista di oggetti e popola il DOM con la coda */
	var coda_container_obj = $('#coda')
	coda_container_obj.empty()
	var oggiString = (new Date()).toDateString()

	var timeFormat = function (data) {
		var result = ""
		result += ("00" + data.getHours()).slice(-2) + ":"
		result += ("00" + data.getMinutes()).slice(-2)
		return result
	}

	for (var i = coda.length - 1; i >= 0; i--) {
		var e = coda[i]
		//console.log(e);
		var e_obj = $("<div />")
		var e_username = e.utente
		var numerico = e_username.match(/\d+/)
		if (numerico && numerico.length) e_username = numerico[0]
		e_obj.append($("<div />").html(e_username).addClass('name'))

		var data = new Date(e.data)
		var testo = ""
		if (oggiString === data.toDateString()) {
			testo += "\ndalle " + timeFormat(data)
		}
		else {
			testo += "\ndal " + data.toLocaleString()
		}
		//testo += "\n" + e['luogo'];
		e_obj.append($('<div />').html(testo))
		e_obj.append($("<span />", {class: "place"}).html(e.luogo))
		if (e.utente === username) {    // global variable
			e_obj.addClass('current')
		}
		coda_container_obj.prepend(e_obj)
	}
	coda_container_obj.append($("<br />").css("clear", "both"))
}
