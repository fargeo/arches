define([
    'knockout',
    'viewmodels/widget',
    'arches',
    'map/mapbox-style',
    'bindings/mapbox-gl'
], function (ko, WidgetViewModel, arches, mapStyle) {
    /**
    * registers a map-widget component for use in forms
    * @function external:"ko.components".map-widget
    * @param {object} params
    */
    return ko.components.register('map-widget', {
        viewModel: function(params) {
            WidgetViewModel.apply(this, [params]);

            this.mapOptions = {
                style: mapStyle
            };
        },
        template: { require: 'text!widget-templates/map' }
    });
});
