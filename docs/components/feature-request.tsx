import { Callout } from 'nextra/components'

export function FeatureRequest() {
  return (
    <Callout type="info">
      Didn't find the feature you were looking for? Feel free to submit an{' '}
      <a
        className="underline"
        href="https://github.com/npi-ai/npi/issues/new"
        target="_blank"
      >
        issue
      </a>{' '}
      or{' '}
      <a
        className="underline"
        href="https://github.com/npi-ai/npi/pulls"
        target="_blank"
      >
        PR
      </a>
      !
    </Callout>
  )
}
