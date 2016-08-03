define([
    'jquery',
    'underscore',
    'knockout',
    'mapbox-gl',
    'arches',
    'plugins/mapbox-gl-draw'
], function ($, _, ko, mapboxgl, arches, Draw) {
    ko.bindingHandlers.mapboxgl = {
        init: function(element, valueAccessor, allBindings, viewModel, bindingContext){
            var defaults = {
                container: element
            };
            var options = ko.unwrap(valueAccessor());

            mapboxgl.accessToken = arches.mapboxApiKey;

            var map = new mapboxgl.Map(
                _.defaults(options, defaults)
            );

            viewModel.map = map;

            var draw = Draw();
            map.addControl(draw);
        }
    }

    return ko.bindingHandlers.mapboxgl;
});
