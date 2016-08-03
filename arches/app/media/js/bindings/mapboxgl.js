define([
    'jquery',
    'underscore',
    'knockout',
    'mapboxgl'
], function ($, _, ko, mapboxgl) {
    ko.bindingHandlers.mapboxgl = {
        init: function(element, valueAccessor, allBindings, viewModel, bindingContext){
            var options = ko.unwrap(valueAccessor());

            mapboxgl.accessToken = 'pk.eyJ1Ijoicmdhc3RvbiIsImEiOiJJYTdoRWNJIn0.MN6DrT07IEKXadCU8xpUMg';
            var map = new mapboxgl.Map({
                container: element,
                style: 'mapbox://styles/mapbox/streets-v9'
            });
        }
    }

    return ko.bindingHandlers.mapboxgl;
});
