define([
    'jquery',
    'underscore',
    'knockout',
    'mapboxgl',
    'arches'
], function ($, _, ko, mapboxgl, arches) {
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

            viewModel.map = map
        }
    }

    return ko.bindingHandlers.mapboxgl;
});
