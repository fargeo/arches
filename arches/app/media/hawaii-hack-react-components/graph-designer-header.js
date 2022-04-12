import React, { useState } from 'react';
import { createRoot } from 'react-dom/client';

function Welcome(props) {
    const updatedLoveMessage = '( ' + props.loveMessage + ' )';

    const [isTitleButtonClicked, setTitleButtonClickedState] = useState(false);

    const titleStyle = {
        backgroundColor: isTitleButtonClicked ? 'green' : 'pink',
        fontSize: '28px',
        fontWeight: 'bold',
        marginRight: '10px',
    };

    return (
        <div style={{display: 'flex', alignItems: 'center', width: '100%'}}>
            <div style={titleStyle}>Hello, I'm a React header {updatedLoveMessage}</div>
            <button onClick={() => setTitleButtonClickedState(!isTitleButtonClicked)}>CLICK ME</button>
        </div>
    );
}

const root = createRoot(
    document.getElementById('hawaii-hackathon-header-root')
);
root.render(<Welcome loveMessage='and I love you' />)