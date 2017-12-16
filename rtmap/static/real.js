/// <reference path="./jquery.d.ts"/>
/// <reference path="./leaflet.d.ts"/>
var RANDOMIZE_POSITION = false;
var Realtime = /** @class */ (function () {
    function Realtime(url) {
        var _this = this;
        this.url = url;
        this.messageQueue = [];
        this.events = {};
        this.connect = function () {
            console.debug("ws connection");
            _this.socket = new WebSocket(wsUrl);
            _this.socket.onclose = _this.disconnected;
            _this.socket.onopen = _this.connected;
            _this.socket.onmessage = _this.receive;
        };
        this.resetReconnection = function () {
            if (_this.reconnectTimer) {
                clearTimeout(_this.reconnectTimer);
            }
            _this.reconnectTimer = 0;
            // 1-2 sec befor first reconnection
            _this.reconnectDelay = 1000;
            _this.reconnectDelay += Math.floor(Math.random() * 1000);
        };
        this.connected = function () {
            console.log("Connected");
            _this.resetReconnection();
            if (_this.messageQueue.length) {
                var len = _this.messageQueue.length;
                console.log("Sending " + len + " messages");
                for (var _i = 0, _a = _this.messageQueue; _i < _a.length; _i++) {
                    var message = _a[_i];
                    _this.send(message);
                }
            }
        };
        this.disconnected = function () {
            console.log("Disconnected. Reconnecting in", _this.reconnectDelay);
            _this.reconnectTimer = setTimeout(_this.reconnect, _this.reconnectDelay);
        };
        this.reconnect = function () {
            if (!_this.socket || _this.socket.readyState == _this.socket.CLOSED) {
                console.debug("Attempt reconnection");
                _this.reconnectDelay *= 2;
                // this.reconnectDelay += Math.floor(Math.random() * 1000);
                _this.reconnectDelay = Math.min(_this.reconnectDelay, Realtime.MAX_RECONNECT_DELAY);
                _this.connect();
            }
        };
        this.send = function (message) {
            if (_this.socket.readyState == _this.socket.OPEN) {
                console.debug("Sending", message);
                _this.socket.send(message);
            }
            else {
                console.info("Cannot send message, enqueuing waiting for connection");
                _this.messageQueue.push(message);
            }
        };
        this.receive = function (data) {
            var message = JSON.parse(data.data);
            switch (message.type) {
                case 'realtimePositions':
                    console.log("Positions:", message.positions);
                    _this.fire('positions', message.positions);
                    break;
                default:
                    console.warn("Unknown message type:", message.type);
            }
        };
        this.on = function (eventName, callback) {
            if (!_this.events[eventName])
                _this.events[eventName] = [];
            _this.events[eventName].push(callback);
        };
        this.fire = function (eventName, payload) {
            for (var _i = 0, _a = (_this.events[eventName] || []); _i < _a.length; _i++) {
                var callback = _a[_i];
                callback(payload);
            }
        };
        this.resetReconnection();
        this.connect();
    }
    Realtime.MAX_RECONNECT_DELAY = 30000; // retry every 30sec max
    return Realtime;
}());
var Map = /** @class */ (function () {
    function Map(selector) {
        var _this = this;
        this.selector = selector;
        this.attribution = "© <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> © <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> <strong><a href='https://www.mapbox.com/map-feedback/' target='_blank'>Improve this map</a></strong>";
        this.token = RTMAP_SETTINGS.MAPBOX_ACCESS_TOKEN;
        this.center = RTMAP_SETTINGS.CENTER;
        this.tileUrl = 'https://api.mapbox.com/styles/v1/mapbox/streets-v10/tiles/256/{z}/{x}/{y}?access_token=';
        this.markers = {};
        this.positioned = false; // was it rescaled?
        this.setPositions = function (positions) {
            console.log("Setting map positions to ", positions);
            var leafmap = _this.leafmap;
            positions.map(function (position) {
                var latlong = [position.lat, position.lon];
                var user = position.user;
                if (_this.markers[user]) {
                    console.debug("Removing previous marker");
                    _this.markers[user].remove();
                }
                var myIcon = L.divIcon({
                    className: (user === currentUID ? 'highlighted ' : '') +
                        'tam-marker',
                    iconSize: L.point(49, 49),
                });
                _this.markers[user] = L.marker(latlong, {
                    icon: myIcon
                })
                    .addTo(leafmap)
                    .bindPopup(user).openPopup();
            });
            if (!_this.positioned) {
                var markers = Object.keys(_this.markers).map(function (key) { return _this.markers[key]; });
                var group = L.featureGroup(markers);
                leafmap.fitBounds(group.getBounds(), { padding: [5, 5] });
            }
        };
        this.leafmap = L.map(selector).setView(this.center, 12);
        L.tileLayer(this.tileUrl + this.token, {
            attribution: this.attribution,
            maxZoom: 17,
        }).addTo(this.leafmap);
    }
    return Map;
}());
var websocketSchema = window.location.protocol === 'https:' ? 'wss' : 'ws', wsUrl = websocketSchema + "://" + document.location.host, rt = new Realtime(wsUrl);
$(function () {
    console.log("Ready!");
    var m = new Map('mapid');
    new GeoLocator(rt, m);
});
var GeoLocator = /** @class */ (function () {
    function GeoLocator(realtime, map) {
        var _this = this;
        this.realtime = realtime;
        this.map = map;
        this.successPositionCallback = function (position) {
            var adjustPos = function (pos) { return RANDOMIZE_POSITION ? pos * (1 + .0002 * Math.random()) : pos; };
            var latlong = [
                adjustPos(position.coords.latitude),
                adjustPos(position.coords.longitude)
            ];
            console.debug("Got my geolocation", latlong);
            if (_this.map) {
                // we don't set the map directly, we wait for the server to answer it back
            }
            if (_this.realtime) {
                _this.realtime.send(JSON.stringify({ position: latlong }));
            }
        };
        this.setPositions = function (positions) {
            _this.map.setPositions(positions);
        };
        realtime.on('positions', this.setPositions);
        if (navigator && navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(this.successPositionCallback, GeoLocator.errorPositionCallback);
        }
        else {
            console.error('Geolocation is not supported');
        }
    }
    GeoLocator.errorPositionCallback = function () {
        console.error("Error getting current position");
    };
    return GeoLocator;
}());
