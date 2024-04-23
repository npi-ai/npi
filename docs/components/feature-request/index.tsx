import { Callout } from 'nextra/components';
import cn from './style.module.css';

export function FeatureRequest() {
  return (
    <Callout type='info'>
      Didn't find the feature you were looking for? Feel free to submit an{' '}
      <a
        className={cn.link}
        href='https://github.com/npi-ai/npi/issues/new'
        target='_blank'
      >
        issue
      </a>{' '}
      or{' '}
      <a
        className={cn.link}
        href='https://github.com/npi-ai/npi/pulls'
        target='_blank'
      >
        PR
      </a>
      !
    </Callout>
  );
}
