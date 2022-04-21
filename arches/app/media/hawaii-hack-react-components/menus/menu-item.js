import React, { useState } from 'react';
import { createUseStyles } from 'react-jss';

export default function(props) {
    const useStyles = createUseStyles({
        menuItem: {
            display: 'flex',
            alignItems: 'center',
            cursor: 'pointer',
            padding: '10px 5px',
            '& .text': {
                padding: '0 10px',
                color: '#777',
                '& .title': {
                    fontSize: '1.05em'
                },
                '& .subtitle': {
                    fontSize: '0.85em'
                }
            } 
        }
    });
    const classes = useStyles();

    const iconClasses = ['icon', 'fa', props.icon];

    return (
        <div className={classes.menuItem} onClick={props.onClick}>
            <div className={iconClasses.join(' ')}></div>
            <div className='text'>
                <div className='title'>{props.title}</div>
                <div className='subtitle'>{props.subtitle}</div>
            </div>
        </div>
    );
}