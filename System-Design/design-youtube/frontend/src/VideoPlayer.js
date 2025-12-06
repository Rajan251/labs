import React, { useRef, useEffect } from 'react';
import videojs from 'video.js';
import 'video.js/dist/video-js.css';

export const VideoPlayer = (props) => {
    const videoNode = useRef(null);
    const player = useRef(null);

    useEffect(() => {
        if (videoNode.current) {
            player.current = videojs(videoNode.current, {
                autoplay: false,
                controls: true,
                sources: [{
                    src: props.src,
                    type: 'application/x-mpegURL'
                }]
            });
        }

        return () => {
            if (player.current) {
                player.current.dispose();
            }
        };
    }, [props.src]);

    return (
        <div data-vjs-player>
            <video ref={videoNode} className="video-js" />
        </div>
    );
}

export default VideoPlayer;
