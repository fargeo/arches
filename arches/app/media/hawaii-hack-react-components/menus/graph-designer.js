import React, { useState, useRef, useCallback } from 'react';
import { createUseStyles } from 'react-jss';
import MenuItem from './menu-item';
import Cookies from 'js-cookie'
import regeneratorRuntime from "regenerator-runtime";


export default function(props) {
    const useStyles = createUseStyles({
        'graphDesigner': {
            '& input': {
                display: 'none'
            }
        }
    });

    const inputRef = useRef();

    const csrfTokenCallback = useCallback(() => {}, [])

    const navigateToNewGraph = async (url, isResource) => {
        const csrftoken = Cookies.get('csrftoken');

        const graphRequestBody = (isResource === undefined ? {} : {isresource: isResource})

        const newGraph = await fetch(url, {
            method: 'POST',
            body: JSON.stringify(graphRequestBody),
            headers: { 
                'X-CSRFToken': csrftoken 
            }
        });
        const json = await newGraph.json();
        window.open(window.arches.urls.graph_designer(json.graphid), "_blank");
    };

    const deleteRequest = async (instances=false) => {
        const url = instances ? arches.urls.delete_instances(props.graphId) : arches.urls.delete_graph(props.graphId) 
        const result = await fetch(url, {
            method: "DELETE",
            cache: false,
            contentType: false,
            headers: { 
                'X-CSRFToken': csrftoken 
            }
        });
    }

    const handleFileInput = async(e) => {
        const formData = new FormData();
        formData.append("importedGraph", e.target.files[0]);

        const graphImport = await fetch('/graph/import/', {
            method: "POST",
            body: formData,
            processData: false,
            cache: false,
            contentType: false
        });

        const json = await graphImport.json();
    };

    const menuItems = [{
        title: "New Model",
        subtitle: "Create new Model",
        icon: "fa-sitemap",
        onClick: () => { 
            navigateToNewGraph('/graph/new', true);
        }
    }, {
        title: "New Branch",
        subtitle: "Create new Branch",
        icon: "fa-code-fork",
        onClick: () => { 
            navigateToNewGraph('/graph/new', false);
        }
    }, {
        title: "Import Model",
        subtitle: "Import Model by uploading a json file",
        icon: "fa-upload",
        onClick: () => { 
            inputRef.current.click();
        }
    }, {
        title: "Clone Model",
        subtitle: "Clone the existing Resource Model",
        icon: "fa-clone",
        onClick: () => { 
            navigateToNewGraph(arches.urls.clone_graph(props.graphId))
        }
    }, {
        title: "Export Model",
        subtitle: "Export the existing Resource Model",
        icon: "fa-download",
        onClick: () => { 
            window.open(window.arches.urls.export_graph(props.graphId), '_blank');
        }
    }, {
        title: "Functions",
        subtitle: "Configure functions attached to this Resource Model",
        icon: "fa-code",
        onClick: () => { 
            
            window.open(arches.urls.function_manager(props.graphId), '_blank');
        }
    }, {
        title: "Export Mapping File",
        subtitle: "Create new Branch",
        icon: "fa-download",
        onClick: () => { 
            window.open(arches.urls.export_mapping_file(props.graphId), '_blank');
        }
    }, {
        title: "Delete Associated Instances",
        subtitle: "Delete All Associated Instances with this Model",
        icon: "fa-trash",
        onClick: () => { 
            deleteRequest(true);
        }
    }, {
        title: "Delete Model",
        subtitle: "Delete the existing Resource Model",
        icon: "fa-trash",
        onClick: () => { 
            deleteRequest();
        }
    }, {
        title: "Return to Arches Designer",
        subtitle: "Create Arches Resource Models and Branches",
        icon: "fa-tag",
        onClick: () => { 
            window.location.href='/graph';
        }
    }].map((item, index) => {
        return (<MenuItem key={index} title={item.title} subtitle={item.subtitle} icon={item.icon} onClick={item.onClick} />)
    });
 
    const classes = useStyles();

    return (
        <div className={classes.graphDesigner}>
            {menuItems}
            <input ref={inputRef} type="file" onChange={() => { handleFileInput() }}></input>
        </div>
    );
}