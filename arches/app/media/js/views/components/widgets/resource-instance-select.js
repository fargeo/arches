define([
    'knockout',
    'viewmodels/widget',
    'arches',
    'bindings/select2-query'
], function(ko, WidgetViewModel, arches) {
    return ko.components.register('resource-instance-select-widget', {
        viewModel: function(params) {
            var self = this;
            params.configKeys = ['placeholder'];
            WidgetViewModel.apply(this, [params]);

            var nameLookup = {};
            this.select2Config = {
                value: this.value,
                clickBubble: true,
                multiple: false,
                placeholder: this.placeholder,
                allowClear: true,
                ajax: {
                    url: arches.urls.search_results,
                    dataType: 'json',
                    quietMillis: 250,
                    data: function (term, page) {
                        var graphid = ko.unwrap(params.node.config.graphid);
                        var data = {
                            no_filters: true,
                            page: page
                        };
                        if (graphid) {
                            data.no_filters = false;
                            data.typeFilter = JSON.stringify([{
                                "graphid": graphid,
                                "inverted": false
                            }]);
                        }
                        if (term) {
                            data.no_filters = false;
                            termFilter = JSON.stringify([{
                                "inverted": false,
                                "type": "string",
                                "context": "",
                                "context_label": "",
                                "id": term,
                                "text": term,
                                "value": term
                            }]);
                        }
                        return data;
                    },
                    results: function (data, page) {
                        return {
                            results: data.results.hits.hits,
                            more: data.paginator.has_next
                        };
                    }
                },
                id: function(item) {
                    return item._id;
                },
                formatResult: function(item) {
                    return item._source.displayname;
                },
                formatSelection: function(item) {
                    return item._source.displayname;
                },
                initSelection: function(el, callback) {
                    var value = self.value();
                    var setSelectionData = function () {
                        callback({
                            _id: value,
                            _source: {
                                displayname: nameLookup[value]
                            }
                        });
                    }
                    if (value) {
                        if (nameLookup[value]) {
                            setSelectionData();
                        } else {
                            $.ajax(arches.urls.resource_descriptors + value, {
                                dataType: "json"
                            }).done(function(data) {
                                nameLookup[value] = data.displayname
                                setSelectionData();
                            });
                        }
                    }
                }
            };
        },
        template: {
            require: 'text!widget-templates/resource-instance-select'
        }
    });
});