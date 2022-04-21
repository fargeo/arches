import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';
import ManageModal from './manage-modal';
import { createUseStyles } from 'react-jss';

const container = document.getElementById('hawaii-hackathon-header-root');

function Header(props) {
    const useStyles = createUseStyles({
        header: {
            display: 'flex', 
            alignItems: 'center', 
            width: '100%',
            height: '100%'
        }
    });
    const classes = useStyles()

    if(props.showMenu == "True") {
        return (
            <div className={classes.header}>
                <ManageModal path={props.path} graphId={props.graphId} />
            </div>
        );
    } else {
        return (
            <div className={classes.header}>
            </div>
        );
    }
}

const root = createRoot(container);
root.render(<Header graphId={container.getAttribute('graphId')} showMenu={container.getAttribute('showMenu')} path={container.getAttribute('path')} message={container.getAttribute('customMessage')} />)