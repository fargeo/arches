import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';

const container = document.getElementById('hawaii-hackathon-header-root');

function Header(props) {
    const updatedMessage = '( ' + props.message + ' )';

    const [isTitleButtonClicked, setTitleButtonClickedState] = useState(false);

    const titleStyle = {
        fontSize: '28px',
        fontWeight: 'bold',
        marginRight: '10px',
    };

    return (
        <div style={{display: 'flex', alignItems: 'center', width: '100%', backgroundColor: isTitleButtonClicked ? 'green' : 'pink',}}>
            <div style={titleStyle}>Hello, I'm a React header {updatedMessage}</div>
            <button class='btn btn-small btn-info' onClick={() => setTitleButtonClickedState(!isTitleButtonClicked)}>CLICK ME!</button>
        </div>
    );
}

const root = createRoot(container);
root.render(<Header message={container.getAttribute('customMessage')} />)