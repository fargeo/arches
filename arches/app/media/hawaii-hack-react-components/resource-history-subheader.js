import React from 'react';

export default function ResourceHistorySubheader(props) {
    return(
        <div style={{backgroundColor: 'white'}}>
            <div>{props.displayName}</div>
            <div>{props.currentDate}</div>

            <span>REACT input</span>
            <input
                onChange={(e) => {props.textInputValue(e.target.value)}}
                value={props.textInputValue()}
            ></input>
        </div>
    )
}