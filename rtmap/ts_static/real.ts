/// <reference path="./jquery.d.ts"/>
/// <reference path="./leaflet.d.ts"/>

import map = L.map;
interface Settings {
    MAPBOX_ACCESS_TOKEN: string;
    CENTER: [number, number];
}

declare var RTMAP_SETTINGS: Settings;

class Realtime {
    socket: WebSocket;

    /* socket.readyState
     CONNECTING	0	The connection is not yet open.
     OPEN       1	The connection is open and ready to communicate.
     CLOSING	2	The connection is in the process of closing.
     CLOSED     3	The connection is closed or couldn't be opened.
     */

    reconnectDelay: number;
    private reconnectTimer: number;
    private static MAX_RECONNECT_DELAY = 30000; // retry every 30sec max
    messageQueue = [];

    constructor(public url: string) {
        this.resetReconnection();
        this.connect()
    }

    connect = () => {
        console.debug("ws connection");
        this.socket = new WebSocket(wsUrl);
        this.socket.onclose = this.disconnected;
        this.socket.onopen = this.connected;
    };

    resetReconnection = () => {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        this.reconnectTimer = 0;
        // 1-2 sec befor first reconnection
        this.reconnectDelay = 1000;
        this.reconnectDelay += Math.floor(Math.random() * 1000)
    };

    connected = () => {
        console.log("Connected");
        this.resetReconnection();
        if (this.messageQueue.length) {
            let len = this.messageQueue.length;
            console.log(`Sending ${len} messages`);
            for (let message of this.messageQueue) {
                this.send(message);
            }
        }
    };

    disconnected = () => {
        console.log("Disconnected. Reconnecting in", this.reconnectDelay);

        this.reconnectTimer = setTimeout(this.reconnect, this.reconnectDelay)
    };

    reconnect = () => {
        if (!this.socket || this.socket.readyState == this.socket.CLOSED) {
            console.debug("Attempt reconnection");

            this.reconnectDelay *= 2;
            // this.reconnectDelay += Math.floor(Math.random() * 1000);
            this.reconnectDelay = Math.min(this.reconnectDelay, Realtime.MAX_RECONNECT_DELAY);
            this.connect();
        }
    };

    send = (message) => {
        if (this.socket.readyState == this.socket.OPEN) {  // when connection is open
            console.debug("Sending", message);
            this.socket.send(message);
        }
        else {
            console.info("Cannot send message, enqueuing waiting for connection");
            this.messageQueue.push(message)
        }
    };
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

let websocketSchema = window.location.protocol === 'https:' ? 'wss' : 'ws',
    wsUrl = websocketSchema + "://" + document.location.host,
    rt = new Realtime(wsUrl);

$(function () {
    console.log("Ready!");
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
        let latlong: [number, number] = [position.coords.latitude, position.coords.longitude];
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
