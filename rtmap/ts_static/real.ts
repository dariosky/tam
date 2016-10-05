/// <reference path="./jquery.d.ts"/>
/// <reference path="./leaflet.d.ts"/>

import map = L.map;
interface Settings {
    MAPBOX_ACCESS_TOKEN: string;
    CENTER: [number,number];
}

declare var RTMAP_SETTINGS: Settings;

class Realtime {
    socket: WebSocket;

    constructor(public url: string) {
        this.connect()
    }

    connect() {
        console.debug("ws connection");
        this.socket = new WebSocket(wsUrl);
    }

    send(message) {
        console.debug("Sending", message);
        this.socket.send(message);
    }
}

class Map {
    attribution: string = "© <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> © <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> <strong><a href='https://www.mapbox.com/map-feedback/' target='_blank'>Improve this map</a></strong>";
    token = RTMAP_SETTINGS.MAPBOX_ACCESS_TOKEN;
    center = RTMAP_SETTINGS.CENTER;
    tileUrl = 'https://api.mapbox.com/styles/v1/mapbox/streets-v10/tiles/256/{z}/{x}/{y}?access_token=';
    leafmap: L.Map;

    constructor(public selector) {
        this.leafmap = L.map(selector).setView(this.center, 12);
        L.tileLayer(this.tileUrl + this.token, {
            attribution: this.attribution,
            maxZoom: 17,
        }).addTo(this.leafmap);
    }

}

let wsUrl = "ws://" + document.location.host,
    rt = new Realtime(wsUrl);

$(function () {
    console.log("Ready!;");
    let m = new Map('mapid'),
        locator = new GeoLocator(rt);
});


class GeoLocator {
    constructor(public realtime?: Realtime, public map?: Map) {
        console.debug("Init locator", "rt:", realtime);
        if (navigator && navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                this.successPositionCallback.bind(this),
                GeoLocator.errorPositionCallback
            );
        } else {
            console.error('Geolocation is not supported');
        }
    }

    static errorPositionCallback() {
        console.error("Error getting current position")
    }

    successPositionCallback(position) {
        let latlong: [number,number] = [position.coords.latitude, position.coords.longitude];
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
    }

}
