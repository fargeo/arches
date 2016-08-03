define([], function() {
    return {
        "version": 8,
        "name": "Mapbox Satellite",
        "metadata": {
            "mapbox:autocomposite": true,
            "mapbox:type": "default"
        },
        "sources": {
            "mapbox": {
                "type": "raster",
                "url": "mapbox://mapbox.satellite",
                "tileSize": 256
            }
        },
        "sprite": "mapbox://sprites/mapbox/satellite-v9",
        "glyphs": "mapbox://fonts/mapbox/{fontstack}/{range}.pbf",
        "layers": [
            {
                "id": "background",
                "type": "background",
                "paint": {
                    "background-color": "rgb(4,7,14)"
                }
            },
            {
                "id": "satellite",
                "type": "raster",
                "source": "mapbox",
                "source-layer": "mapbox_satellite_full"
            }
        ]
    };
});
