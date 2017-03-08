define([
    'knockout',
    'underscore',
    'views/base-manager',
    'viewmodels/alert',
    'project-manager-data',
    'arches',
    'bindings/mapbox-gl',
    'bindings/codemirror',
    'codemirror/mode/javascript/javascript',
    'datatype-config-components'
], function(ko, _, BaseManagerView, AlertViewModel, data, arches) {
    var vm = {
        map: null,
        geomNodes: [],
        loading: ko.observable(false),
        zoom: ko.observable(arches.mapDefaultZoom),
        minZoom: ko.observable(arches.mapDefaultMinZoom),
        maxZoom: ko.observable(arches.mapDefaultMaxZoom),
        centerX: ko.observable(arches.mapDefaultX),
        centerY: ko.observable(arches.mapDefaultY),
        pitch: ko.observable(0),
        bearing: ko.observable(0),
        selectedList: ko.observable(),
        projects: ko.observableArray(data.projects),
        graphs: data.graphs,
        iconFilter: ko.observable('')
    };

    var mapLayers = ko.observableArray($.extend(true, [], arches.mapLayers));

    _.each(mapLayers(), function(layer) {
        layer.addtomap = ko.observable(layer.addtomap);
        layer.name = ko.observable(layer.name);
        layer.icon = ko.observable(layer.icon);
    });


    _.each(vm.projects(), function(project) {
        project._project = ko.observable(JSON.stringify(project));
        project.projectJSON = ko.observable(JSON.stringify(project.config, null, '\t'))
        layer.activated = ko.observable(false);
        project.name = ko.observable(project.name);
        layer.toJSON = ko.computed(function () {
            var project;
            try {
                project = JSON.parse(project.projectJSON());
            }
            catch (e) {
                project = [];
            }
            return JSON.stringify({
                "config": project.config(),
                "name": project.name()
            })
        });

        project.dirty = ko.computed(function() {
            return project.toJSON() !== project._project();
        })
        project.save = function () {
            vm.loading(true);
            $.ajax({
                type: "POST",
                url: window.location.pathname + '/' + layer.maplayerid,
                data: project.toJSON(),
                success: function(response) {
                    project._project(project.toJSON());
                    pageView.viewModel.loading(false);
                },
                error: function(response) {
                    pageView.viewModel.loading(false);
                }
            });
        };
        layer.reset = function () {
            var _layer = JSON.parse(project._project());
        };
        layer.delete = function () {
            pageView.viewModel.alert(new AlertViewModel('ep-alert-red', arches.confirmMaplayerDelete.title, arches.confirmMaplayerDelete.text, function() {
                return;
            }, function(){
                vm.loading(true);
                $.ajax({
                    type: "DELETE",
                    url: window.location.pathname + '/' + project.projectid,
                    success: function(response) {
                        console.log(response)
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
        basemap.select = function () {
            vm.selectedBasemapName(basemap.name());
        }
    });
    var defaultBasemap = _.find(vm.basemaps(), function (basemap) {
        return basemap.addtomap();
    });
    if (!defaultBasemap) {
        defaultBasemap = vm.basemaps()[0];
    }
    vm.selectedBasemapName(defaultBasemap.name());
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


    vm.selection = ko.observable({
        dirty:ko.observable(false),
        projectid:ko.observable(undefined),
        projectJSON:ko.observable({})
    });

    vm.selectedprojectJSON = ko.computed({
        read: function () {
            if (!vm.selection().projectid) {
                return '[]';
            }
            return vm.selection().projectJSON();
        },
        write: function (value) {
            if (vm.selection().projectid) {
                vm.selection().projectJSON(value);
            }
        }
    });
    var displayLayers = [];
    var basemapLayers = getBasemapLayers();
    vm.mapStyle = {
        "version": 8,
        "name": "Basic",
        "metadata": {
            "mapbox:autocomposite": true,
            "mapbox:type": "template"
        },
        "layers": basemapLayers.concat(displayLayers),
        "sources": sources,
        "sprite": arches.mapboxSprites,
        "glyphs": arches.mapboxGlyphs
    };

    vm.setupMap = function(map) {
        vm.map = map;
    }

    // var updateMapStyle = function () {
    //     var displayLayers;
    //     try {
    //         displayLayers = JSON.parse(vm.selectedLayerJSON());
    //     }
    //     catch (e) {
    //         displayLayers = [];
    //     }
    //     var basemapLayers = getBasemapLayers();
    //     if (vm.selection().isoverlay) {
    //         vm.mapStyle.project = basemapLayers.concat(displayLayers);
    //     } else {
    //         vm.mapStyle.project = displayLayers;
    //     }
    //     if (vm.map) {
    //         vm.map.setStyle(vm.mapStyle);
    //     }
    // };

    vm.selection.subscribe();
    vm.listFilter = ko.observable('');
    vm.listItems = ko.computed(function () {
        var listFilter = vm.listFilter().toLowerCase();
        var layerList = ko.unwrap(vm.selectedList());
        return []
        // return _.filter(layerList, function(item) {
        //     var name = item.nodeid ?
        //         (item.config.layerName() ? item.config.layerName() : item.layer.name) :
        //         item.name();
        //     name = name.toLowerCase()
        //     return name.indexOf(listFilter) > -1;
        // })
    });

    var pageView = new BaseManagerView({
        viewModel: vm
    });

    return pageView;
});
