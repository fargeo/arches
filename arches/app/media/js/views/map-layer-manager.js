define([
    'knockout',
    'underscore',
    'views/base-manager',
    'models/node',
    'viewmodels/alert',
    'map-layer-manager-data',
    'arches',
    'bindings/mapbox-gl',
    'bindings/codemirror',
    'codemirror/mode/javascript/javascript',
    'datatype-config-components'
], function(ko, _, BaseManagerView, NodeModel, AlertViewModel, data, arches) {
    var vm = {
        map: null,
        geomNodes: [],
        loading: ko.observable(false),
        zoom: ko.observable(0),
        minZoom: ko.observable(0),
        maxZoom: ko.observable(20),
        centerX: ko.observable(-80),
        centerY: ko.observable(0),
        pitch: ko.observable(0),
        bearing: ko.observable(0),
        iconFilter: ko.observable(''),
    };
    vm.icons = ko.computed(function () {
        return _.filter(data.icons, function (icon) {
            return icon.name.indexOf(vm.iconFilter()) >= 0;
        });
    });
    var mapLayers = ko.observableArray($.extend(true, [], arches.mapLayers));
    _.each(mapLayers(), function(layer) {
        layer._layer = ko.observable(JSON.stringify(layer));
        layer.layerJSON = ko.observable(JSON.stringify(layer.layer_definitions, null, '\t'))
        layer.activated = ko.observable(layer.activated);
        layer.name = ko.observable(layer.name);
        layer.icon = ko.observable(layer.icon);
        layer.toJSON = ko.computed(function () {
            var layers;
            try {
                layers = JSON.parse(layer.layerJSON());
            }
            catch (e) {
                layers = [];
            }
            return JSON.stringify({
                "maplayerid": layer.maplayerid,
                "name": layer.name(),
                "layer_definitions": layers,
                "isoverlay": layer.isoverlay,
                "icon": layer.icon(),
                "activated": layer.activated(),
                "is_resource_layer": false
            })
        });
        layer.dirty = ko.computed(function() {
            return layer.toJSON() !== layer._layer();
        })
        layer.save = function () {
            vm.loading(true);
            $.ajax({
                type: "POST",
                url: window.location.pathname + '/' + layer.maplayerid,
                data: layer.toJSON(),
                success: function(response) {
                    layer._layer(layer.toJSON());
                    pageView.viewModel.loading(false);
                },
                error: function(response) {
                    pageView.viewModel.loading(false);
                }
            });
        };
        layer.reset = function () {
            var _layer = JSON.parse(layer._layer());
            layer.layerJSON(JSON.stringify(_layer.layer_definitions, null, '\t'))
            layer.activated(_layer.activated);
            layer.name(_layer.name);
            layer.icon(_layer.icon);
        };
        layer.delete = function () {
            pageView.viewModel.alert(new AlertViewModel('ep-alert-red', arches.confirmMaplayerDelete.title, arches.confirmMaplayerDelete.text, function() {
                return;
            }, function(){
                vm.loading(true);
                $.ajax({
                    type: "DELETE",
                    url: window.location.pathname + '/' + layer.maplayerid,
                    success: function(response) {
                        mapLayers.remove(layer);
                        var newSelection = mapLayers()[0] || vm.geomNodes[0]
                        vm.selection(mapLayers()[0]);
                        pageView.viewModel.loading(false);
                    },
                    error: function(response) {
                        pageView.viewModel.loading(false);
                    }
                });
            }));
        };
    });

    vm.selectedBasemapName = ko.observable('');
    vm.basemaps = ko.computed(function() {
        return _.filter(mapLayers(), function(layer) {
            return !layer.isoverlay;
        })
    });
    vm.basemaps().forEach(function (basemap) {
        if (vm.selectedBasemapName() === '') {
            vm.selectedBasemapName(basemap.name());
        }
        if (basemap.name() === 'streets') {
            vm.selectedBasemapName('streets');
        }
        basemap.select = function () {
            vm.selectedBasemapName(basemap.name());
        }
    });
    vm.overlays = ko.computed(function() {
        return _.filter(mapLayers(), function(layer) {
            return layer.isoverlay && !layer.is_resource_layer;
        })
    });

    var getBasemapLayers = function () {
        return _.filter(vm.basemaps(), function(layer) {
            return layer.name() === vm.selectedBasemapName();
        }).reduce(function(layers, layer) {
            return layers.concat(layer.layer_definitions);
        }, []);
    };
    var sources = $.extend(true, {}, arches.mapSources);
    _.each(sources, function(sourceConfig, name) {
        if (sourceConfig.tiles) {
            sourceConfig.tiles.forEach(function(url, i) {
                if (url.startsWith('/')) {
                    sourceConfig.tiles[i] = window.location.origin + url;
                }
            });
        }
    });

    var datatypelookup = {};
    _.each(data.datatypes, function(datatype){
        datatypelookup[datatype.datatype] = datatype;
    }, this);

    _.each(data.geom_nodes, function(node) {
        vm.geomNodes.push(
            new NodeModel({
                loading: vm.loading,
                source: node,
                datatypelookup: datatypelookup,
                graph: undefined,
                layer: _.find(data.resource_map_layers, function(layer) {
                    return layer.nodeid === node.nodeid;
                }),
                mapSource: _.find(data.resource_map_sources, function(source) {
                    return source.nodeid === node.nodeid;
                }),
                graph: _.find(data.graphs, function(graph) {
                    return graph.graphid === node.graph_id;
                })
            })
        );
    });

    vm.selection = ko.observable(vm.geomNodes[0] || mapLayers()[0]);
    vm.selectedLayerJSON = ko.computed({
        read: function () {
            if (!vm.selection().maplayerid) {
                return '[]';
            }
            return vm.selection().layerJSON();
        },
        write: function (value) {
            if (vm.selection().maplayerid) {
                vm.selection().layerJSON(value);
            }
        }
    });

    var displayLayers = JSON.parse(vm.selectedLayerJSON());
    var basemapLayers = getBasemapLayers();

    vm.mapStyle = {
        "version": 8,
        "name": "Basic",
        "metadata": {
            "mapbox:autocomposite": true,
            "mapbox:type": "template"
        },
        "sources": sources,
        "sprite": "mapbox://sprites/mapbox/basic-v9",
        "glyphs": "mapbox://fonts/mapbox/{fontstack}/{range}.pbf",
        "layers": basemapLayers.concat(displayLayers)
    };

    vm.setupMap = function(map) {
        vm.map = map;
    }

    var updateMapStyle = function () {
        var displayLayers;
        try {
            displayLayers = JSON.parse(vm.selectedLayerJSON());
        }
        catch (e) {
            displayLayers = [];
        }
        var basemapLayers = getBasemapLayers();
        if (vm.selection().isoverlay) {
            vm.mapStyle.layers = basemapLayers.concat(displayLayers);
        } else {
            vm.mapStyle.layers = displayLayers;
        }
        if (vm.map) {
            vm.map.setStyle(vm.mapStyle);
        }
    };

    vm.selectedBasemapName.subscribe(updateMapStyle);
    vm.selection.subscribe(updateMapStyle);
    vm.selectedLayerJSON.subscribe(updateMapStyle);

    var pageView = new BaseManagerView({
        viewModel: vm
    });

    return pageView;
});