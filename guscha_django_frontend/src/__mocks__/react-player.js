import React from 'react';

const ReactPlayer = ({ url, ...props }) => {
  return React.createElement('div', {
    'data-testid': 'react-player',
    'data-url': url,
    ...props
  }, 'Video Player');
};

export default ReactPlayer;