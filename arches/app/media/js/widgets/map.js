define(['knockout', 'viewmodels/widget', 'bindings/mapboxgl'], function (ko, WidgetViewModel) {
    /**
    * registers a map-widget component for use in forms
    * @function external:"ko.components".map-widget
    * @param {object} params
    */
    return ko.components.register('map-widget', {
        viewModel: function(params) {
            WidgetViewModel.apply(this, [params]);
        },
        template: { require: 'text!widget-templates/map' }
    });
});
