require([
    'knockout',
    'viewmodels/concept-widget',
    'plugins/knockout-select2'
], function(ko, ConceptWidgetViewModel) {
    /**
     * registers a select-widget component for use in forms
     * @function external:"ko.components".select-widget
     * @param {object} params
     * @param {boolean} params.value - the value being managed
     * @param {object} params.config -
     * @param {string} params.config.label - label to use alongside the select input
     * @param {string} params.config.placeholder - default text to show in the select input
     * @param {string} params.config.options -
     */
    return ko.components.register('concept-checkbox-widget', {
        viewModel: function(params) {
            ConceptWidgetViewModel.apply(this, [params]);

            this.multiple = true;
        },
        template: {
            element: 'checkbox-widget-template'
        }
    });
});
