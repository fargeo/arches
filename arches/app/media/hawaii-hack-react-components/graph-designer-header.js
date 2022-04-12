import React from 'react';
import { createRoot } from 'react-dom/client';

const root = createRoot(
    document.getElementById('hawaii-hackathon-header-root')
);

root.render(<h1>Hello, I'm a React header ( and I love you )</h1>)