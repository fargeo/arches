define([
    'knockout',
    'viewmodels/widget',
    'map/mapbox-street-style',
    'map/mapbox-satellite-style',
    'bindings/mapboxgl'
], function (ko, WidgetViewModel, mapStreetStyle, mapSatelliteStyle) {
    /**
    * registers a map-widget component for use in forms
    * @function external:"ko.components".map-widget
    * @param {object} params
    */
    return ko.components.register('map-widget', {
        viewModel: function(params) {
            WidgetViewModel.apply(this, [params]);

            this.mapOptions = {
                style: mapSatelliteStyle
            };

            var self = this
            this.setStyle = function(style) {
                self.map.setStyle(style)
            };

            this.mapStreetStyle = mapStreetStyle;
            this.mapSatelliteStyle = mapSatelliteStyle;

            
        },
        template: { require: 'text!widget-templates/map' }
    });
});
