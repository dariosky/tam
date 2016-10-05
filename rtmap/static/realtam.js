// Note that the path doesn't matter for routing; any WebSocket
// connection gets bumped over to WebSocket consumers

var wsUrl = "ws://" + document.location.host;
socket = new WebSocket(wsUrl);
socket.onmessage = function (e) {
	console.log("Received", e.data);
};

$(function () {
	function initGeolocation() {
		if (navigator && navigator.geolocation) {
			navigator.geolocation.getCurrentPosition(successPositionCallback, errorPositionCallback);
		} else {
			console.error('Geolocation is not supported');
		}
	}

	function errorPositionCallback() {
		logger.error("Error getting current position")
	}

	function successPositionCallback(position) {
		// console.log(position);
		// var mapUrl = "http://maps.google.com/maps/api/staticmap?center=";
		// mapUrl = mapUrl + position.coords.latitude + ',' + position.coords.longitude;
		// mapUrl = mapUrl + '&zoom=15&size=512x512&maptype=roadmap&sensor=false';
		// var imgElement = document.getElementById("static-map");
		// imgElement.src = mapUrl;

		var latlong = [position.coords.latitude, position.coords.longitude],
			marker = L.marker(latlong).addTo(mymap);

		var group = new L.featureGroup([marker]);

		mymap.fitBounds(group.getBounds().pad(5));

		console.log(position);
		socket.send(position);
	}

	socket.onopen = function () {
		console.log("Sending message");
		socket.send("hello world");
		initGeolocation();
	};

});


var
	attribution = "© <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> © <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> <strong><a href='https://www.mapbox.com/map-feedback/' target='_blank'>Improve this map</a></strong>",
	token = RTMAP_SETTINGS.MAPBOX_ACCESS_TOKEN,
	center = RTMAP_SETTINGS.CENTER,
	mymap = L.map('mapid').setView(center, 12);
L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/streets-v10/tiles/256/{z}/{x}/{y}?access_token={accessToken}', {
	attribution: attribution,
	maxZoom: 17,
	accessToken: token
}).addTo(mymap);
function onMapClick(e) {
	L.popup()
		.setLatLng(e.latlng)
		.setContent("You clicked the map at " + e.latlng.toString())
		.openOn(mymap);
}

mymap.on('click', onMapClick);

