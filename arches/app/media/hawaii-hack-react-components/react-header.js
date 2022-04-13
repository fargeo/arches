import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';

const container = document.getElementById('hawaii-hackathon-header-root');
const root = createRoot(container);

function Header(props) {
    const updatedMessage = '( ' + props.message + ' )';

    const [isTitleButtonClicked, setTitleButtonClickedState] = useState(false);

    const titleStyle = {
        backgroundColor: isTitleButtonClicked ? 'green' : 'pink',
        fontSize: '28px',
        fontWeight: 'bold',
        marginRight: '10px',
    };

    return (
        <div style={{display: 'flex', alignItems: 'center', width: '100%'}}>
            <div style={titleStyle}>Hello, I'm a React header {updatedMessage}</div>
            <button onClick={() => setTitleButtonClickedState(!isTitleButtonClicked)}>CLICK ME!</button>
        </div>
    );
}

root.render(<Header message={container.getAttribute('customMessage')} />)