define([
    'knockout',
    'viewmodels/widget',
    'map/mapbox-street-style',
    'map/mapbox-satellite-style',
    'map/mapzen-style',
    'bindings/mapbox-gl'
], function (ko, WidgetViewModel, mapStreetStyle, mapSatelliteStyle, mapzenStyle) {
    /**
    * registers a map-widget component for use in forms
    * @function external:"ko.components".map-widget
    * @param {object} params
    */
    return ko.components.register('map-widget', {
        viewModel: function(params) {
            WidgetViewModel.apply(this, [params]);

            this.mapOptions = {
                style: mapzenStyle
            };

            var self = this
            this.setStyle = function(style) {
                self.map.setStyle(style)
            };

            this.mapStreetStyle = mapStreetStyle;
            this.mapSatelliteStyle = mapSatelliteStyle;
            this.mapzenStyle = mapzenStyle;


        },
        template: { require: 'text!widget-templates/map' }
    });
});
