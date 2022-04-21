import React, { useState } from 'react';
import Editor from './menus/editor';
import FunctionManager from './menus/function-manager';
import GraphDesigner from './menus/graph-designer';
import { createUseStyles } from 'react-jss';

export default function ManageModal(props) {
    //
    let menu = undefined;
    const [isMenuVisible, setMenuState] = useState(false);
    if(props.path == "views/resource/editor"){
        menu = (<Editor />);
    } else if (props.path == "views/graph/function-manager") {
        menu = (<FunctionManager />);
    } else {
        menu = (<GraphDesigner graphId={props.graphId}/>);
    }

    const useStyles = createUseStyles({
        manageModal: {
            height: '100%',
            '& .menu': {
                zIndex: '18', 
                position: 'absolute', 
                padding: '10px', 
                backgroundColor: '#fff'
            },
            '& button': {
                backgroundColor: '#9490EE',
                border: 'none',
                color: '#eee',
                fontSize: '1.08em',
                height: '100%',
                padding: '0 15px',
                '& span': {
                    padding: '0 5px'
                }
            }
        },
        overlay: {
            position: 'absolute', 
            width: '100%', 
            top: '0', 
            left: '0', 
            height: '100%', 
            zIndex: '17', 
            backgroundColor: 'transparent'
        }
    });
    const classes = useStyles();

    return (
        <div className={classes.manageModal}>
            <button onClick={() => setMenuState(!isMenuVisible)}>
                <div className='fa fa-bars'></div>
                <span>Manage</span>
            </button>
            <div style={{display: !isMenuVisible ? "none" : "block"}}>
                <div className={classes.overlay} onClick={() => setMenuState(!isMenuVisible)} />
                <div className='menu'>
                    {menu}
                </div>
            </div>
        </div>
    );
};