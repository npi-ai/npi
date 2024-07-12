import YouTube from 'react-youtube'

export function YouTubeComponent({ videoId }: { videoId: string }) {
  const opts = {
    height: 'auto',
    width: '640',
    playerVars: {
      // https://developers.google.com/youtube/player_parameters
      autoplay: 0,
    },
  }

  return (
    <YouTube
      className="w-full [&_iframe]:aspect-video [&_iframe]:max-w-full"
      videoId={videoId}
      opts={opts}
    />
  )
}
