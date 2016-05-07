// Note that the path doesn't matter for routing; any WebSocket
// connection gets bumped over to WebSocket consumers

socket = new WebSocket("ws://127.0.0.1:8111/sparagnaus/");
socket.onmessage = function (e) {
	console.log("Received", e.data);
};
socket.onopen = function () {
	console.log("Sending message");
	socket.send("hello world");
};
