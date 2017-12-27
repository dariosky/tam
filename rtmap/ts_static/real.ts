/// <reference path="./jquery.d.ts"/>
/// <reference path="./leaflet.d.ts"/>

// import map = L.map;

interface Settings {
    MAPBOX_ACCESS_TOKEN: string
    CENTER: [number, number]
    WEBSOCKET_PORT: number
}

declare var RTMAP_SETTINGS: Settings
declare var currentUID: string

const RANDOMIZE_POSITION = false

class Realtime {
    socket: WebSocket

    /* socket.readyState
     CONNECTING	0	The connection is not yet open.
     OPEN       1	The connection is open and ready to communicate.
     CLOSING	2	The connection is in the process of closing.
     CLOSED     3	The connection is closed or couldn't be opened.
     */

    reconnectDelay: number
    private reconnectTimer: number
    private static MAX_RECONNECT_DELAY = 30000 // retry every 30sec max
    messageQueue = []
    private events: { [event: string]: any } = {}

    constructor(public url: string) {
        this.resetReconnection()
        this.connect()
    }

    connect = () => {
        console.debug("ws connection")
        this.socket = new WebSocket(wsUrl)
        this.socket.onclose = this.disconnected
        this.socket.onopen = this.connected
        this.socket.onmessage = this.receive
    }

    resetReconnection = () => {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer)
        }
        this.reconnectTimer = 0
        // 1-2 sec befor first reconnection
        this.reconnectDelay = 1000
        this.reconnectDelay += Math.floor(Math.random() * 1000)
    }

    connected = () => {
        console.log("Connected")
        this.resetReconnection()
        if (this.messageQueue.length) {
            let len = this.messageQueue.length
            console.log(`Sending ${len} messages`)
            for (let message of this.messageQueue) {
                this.send(message)
            }
        }
    }

    disconnected = () => {
        console.log("Disconnected. Reconnecting in", this.reconnectDelay)

        this.reconnectTimer = setTimeout(this.reconnect, this.reconnectDelay)
    }

    reconnect = () => {
        if (!this.socket || this.socket.readyState == this.socket.CLOSED) {
            console.debug("Attempt reconnection")

            this.reconnectDelay *= 2
            // this.reconnectDelay += Math.floor(Math.random() * 1000);
            this.reconnectDelay = Math.min(this.reconnectDelay, Realtime.MAX_RECONNECT_DELAY)
            this.connect()
        }
    }

    send = (message) => {
        if (this.socket.readyState == this.socket.OPEN) {  // when connection is open
            console.debug("Sending", message)
            this.socket.send(message)
        }
        else {
            console.info("Cannot send message, enqueuing waiting for connection")
            this.messageQueue.push(message)
        }
    }

    receive = (data) => {
        const message = JSON.parse(data.data)
        switch (message.type) {
            case 'realtimePositions':
                console.log("Positions:", message.positions)
                this.fire('positions', message.positions)
                break
            default:
                console.warn("Unknown message type:", message.type)
        }
    }

    on = (eventName, callback) => {
        if (!this.events[eventName]) this.events[eventName] = []
        this.events[eventName].push(callback)
    }

    fire = (eventName, payload) => {
        for (let callback of (this.events[eventName] || [])) {
            callback(payload)
        }
    }
}

class Map {
    attribution: string = "© <a href='https://www.mapbox.com/about/maps/'>Mapbox</a> © <a href='http://www.openstreetmap.org/copyright'>OpenStreetMap</a> <strong><a href='https://www.mapbox.com/map-feedback/' target='_blank'>Improve this map</a></strong>"
    token = RTMAP_SETTINGS.MAPBOX_ACCESS_TOKEN
    center = RTMAP_SETTINGS.CENTER
    tileUrl = 'https://api.mapbox.com/styles/v1/mapbox/streets-v10/tiles/256/{z}/{x}/{y}?access_token='
    leafmap: L.Map
    markers: { [username: string]: any } = {}
    positioned: boolean = false // was it rescaled?

    constructor(public selector) {
        this.leafmap = L.map(selector).setView(this.center, 12)
        L.tileLayer(this.tileUrl + this.token, {
            attribution: this.attribution,
            maxZoom: 17,
        }).addTo(this.leafmap)
    }

    setPositions = (positions) => {
        console.log("Setting map positions to ", positions)
        const leafmap = this.leafmap

        positions.map(position => {
            const latlong: [number, number] = [position.lat, position.lon]
            let user = position.user
            if (this.markers[user]) {
                console.debug("Removing previous marker")
                this.markers[user].remove()
            }
            let myIcon = L.divIcon({
                className: (user === currentUID ? 'current ' : '') +
                'tam-marker',
                iconSize: L.point(49, 49),

            })
            this.markers[user] = L.marker(latlong, {
                icon: myIcon
            })
                .addTo(leafmap)
                .bindPopup(user).openPopup()
        })

        if (!this.positioned) {
            const markers = Object.keys(this.markers).map(key => this.markers[key])
            let group = L.featureGroup(markers)
            leafmap.fitBounds(group.getBounds(), {padding: [5, 5]})
        }
    }

}

let websocketSchema = window.location.protocol === 'https:' ? 'wss' : 'ws',
    wsUrl = `${websocketSchema}://${document.location.host}`,
    rt = new Realtime(wsUrl)

$(function () {
    console.log("Ready!")
    let m = new Map('mapid')
    new GeoLocator(rt, m)
})


class GeoLocator {
    constructor(public realtime?: Realtime, public map?: Map) {
        realtime.on('positions', this.setPositions)

        if (navigator && navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                this.successPositionCallback,
                GeoLocator.errorPositionCallback
            )
        } else {
            console.error('Geolocation is not supported')
        }
    }

    static errorPositionCallback() {
        console.error("Error getting current position")
    }

    successPositionCallback = (position) => {
        const adjustPos = pos => RANDOMIZE_POSITION ? pos * (1 + .0002 * Math.random()) : pos
        let latlong: [number, number] = [
            adjustPos(position.coords.latitude),
            adjustPos(position.coords.longitude)]

        console.debug("Got my geolocation", latlong)

        if (this.map) {
            // we don't set the map directly, we wait for the server to answer it back
        }
        if (this.realtime) {
            this.realtime.send(
                JSON.stringify({position: latlong})
            )
        }
    }

    setPositions = (positions) => {
        this.map.setPositions(positions)
    }

}
