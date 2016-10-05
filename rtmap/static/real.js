/// <reference path="./jquery.d.ts"/>
/// <reference path="./leaflet.d.ts"/>
var map = L.map;
var Realtime = (function () {
    function Realtime(url) {
        this.url = url;
        this.connect();
    }
    Realtime.prototype.connect = function () {
        console.debug("ws connection");
        this.socket = new WebSocket(wsUrl);
    };
    Realtime.prototype.send = function (message) {
        console.debug("Sending", message);
        this.socket.send(message);
    };
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
