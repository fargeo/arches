define([
    'knockout',
    'underscore',
    'viewmodels/widget',
    'arches',
    'map/mapbox-style',
    'geoms',
    'bindings/mapbox-gl'
], function (ko, _, WidgetViewModel, arches, mapStyle, geoms) {
    /**
    * registers a map-widget component for use in forms
    * @function external:"ko.components".map-widget
    * @param {object} params
    */
    return ko.components.register('map-widget', {
        viewModel: function(params) {
            var self = this;
            WidgetViewModel.apply(this, [params]);

            this.selectedBasemap = ko.observable('streets');

            var layers = [];
            arches.basemapLayers.forEach(function (layer) {
                if (layer.name === self.selectedBasemap()) {
                    layers.push(layer.layer);
                }
            });

            mapStyle.sources.archesgeojson = {
                "type": "geojson",
                "data": geoms
            };

            layers.push({
                "id": "archesgeojson_layer",
                "type": "fill",
                "paint": {"fill-color": "#000000"},
                "interactive": true,
                "source": "archesgeojson"
            });

            mapStyle.layers = layers;
            this.mapOptions = {
                style: mapStyle
            };

            this.basemaps = ko.observableArray(_.uniq(_.map(arches.basemapLayers, function(layer) { return layer.name })));

            this.selectedBasemap.subscribe(function(val) {
                self.setBasemap(val);
            });
        },
        template: { require: 'text!widget-templates/map' }
    });
});
