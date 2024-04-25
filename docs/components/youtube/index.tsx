import YouTube from 'react-youtube';

export function YouTubeComponent({videoId}: { videoId: string }) {
    const opts = {
        height: '360',
        width: '640',
        playerVars: {
            // https://developers.google.com/youtube/player_parameters
            autoplay: 0,
        },
    };
    return (
        <YouTube videoId={videoId} opts={opts} />
    );
}

