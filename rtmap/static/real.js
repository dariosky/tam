/// <reference path="./jquery.d.ts"/>
/// <reference path="./leaflet.d.ts"/>
var map = L.map;
var Realtime = (function () {
    function Realtime(url) {
        var _this = this;
        this.url = url;
        this.messageQueue = [];
        this.connect = function () {
            console.debug("ws connection");
            _this.socket = new WebSocket(wsUrl);
            _this.socket.onclose = _this.disconnected;
            _this.socket.onopen = _this.connected;
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
        this.resetReconnection();
        this.connect();
    }
    Realtime.MAX_RECONNECT_DELAY = 30000; // retry every 30sec max
    return Realtime;
}());
var Map = (function () {
    function Map(selector) {
        this.selector = selector;
        this.attribution = "© <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> © <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> <strong><a href='https://www.mapbox.com/map-feedback/' target='_blank'>Improve this map</a></strong>";
        this.token = RTMAP_SETTINGS.MAPBOX_ACCESS_TOKEN;
        this.center = RTMAP_SETTINGS.CENTER;
        this.tileUrl = 'https://api.mapbox.com/styles/v1/mapbox/streets-v10/tiles/256/{z}/{x}/{y}?access_token=';
        this.leafmap = L.map(selector).setView(this.center, 12);
        L.tileLayer(this.tileUrl + this.token, {
            attribution: this.attribution,
            maxZoom: 17,
        }).addTo(this.leafmap);
    }
    return Map;
}());
var wsUrl = "ws://" + document.location.host, rt = new Realtime(wsUrl);
$(function () {
    console.log("Ready!;");
    var m = new Map('mapid'), locator = new GeoLocator(rt);
});
var GeoLocator = (function () {
    function GeoLocator(realtime, map) {
        this.realtime = realtime;
        this.map = map;
        console.debug("Init locator", "rt:", realtime);
        if (navigator && navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(this.successPositionCallback.bind(this), GeoLocator.errorPositionCallback);
        }
        else {
            console.error('Geolocation is not supported');
        }
    }
    GeoLocator.errorPositionCallback = function () {
        console.error("Error getting current position");
    };
    GeoLocator.prototype.successPositionCallback = function (position) {
        var latlong = [position.coords.latitude, position.coords.longitude];
        console.debug("Got position", latlong);
        /*
         if (this.map) {
         let leafmap = this.map.leafmap,
         marker = L.marker(latlong).addTo(leafmap),
         group = L.featureGroup([marker]);
         leafmap.fitBounds(group.getBounds().pad(5));
         }
         */
        if (this.realtime) {
            this.realtime.send(JSON.stringify(latlong));
        }
    };
    return GeoLocator;
}());
