import YouTube from 'react-youtube';
import cn from "./style.module.css";

export function YouTubeComponent({videoId}: { videoId: string }) {
    const opts = {
        height: 'auto',
        width: '640',
        playerVars: {
            // https://developers.google.com/youtube/player_parameters
            autoplay: 0,
        },
    };
    return (
        <YouTube className={cn.video} videoId={videoId} opts={opts} />
    );
}

