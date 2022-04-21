import React, { useState } from 'react';

export default function(props) {
    return (
        <div>
            <div style={{display: 'flex'}} className='menu-item'>
                <div className='icon fa fa-sitemap'></div>
                <div className='text'>
                    <div className='title'>New Model</div>
                    <div className='subtitle'>Create new Branch</div>
                </div>
            </div>
        </div>
    );
}