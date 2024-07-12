import Logo from '@components/logo'
import Image from 'next/image'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { DocsThemeConfig, useConfig } from 'nextra-theme-docs'
import React from 'react'

const defaultMeta = {
  title: 'NPi AI',
  description: 'NPi, Function calling as a Service',
  image: 'https://npi.ai/images/logo-full.svg',
}

const config: DocsThemeConfig = {
  logo: <Logo width={100} />,
  project: {
    link: 'https://github.com/npi-ai/npi',
  },
  chat: {
    link: 'https://discord.gg/VvSnx7z26c',
  },
  docsRepositoryBase: 'https://github.com/npi-ai/npi',
  sidebar: {
    toggleButton: true,
  },
  editLink: {
    text: 'Edit this page on GitHub →',
  },
  toc: {
    backToTop: true,
  },
  useNextSeoProps() {
    return {
      titleTemplate: '%s – NPi AI',
    }
  },
  navbar: {
    extraContent: () => {
      return (
        <Link href="https://x.com/npi_ai" className="p-2">
          <svg
            viewBox="0 0 1200 1227"
            xmlns="http://www.w3.org/2000/svg"
            className="size-5"
          >
            <path
              d="M714.163 519.284L1160.89 0H1055.03L667.137 450.887L357.328 0H0L468.492 681.821L0 1226.37H105.866L515.491 750.218L842.672 1226.37H1200L714.137 519.284H714.163ZM569.165 687.828L521.697 619.934L144.011 79.6944H306.615L611.412 515.685L658.88 583.579L1055.08 1150.3H892.476L569.165 687.854V687.828Z"
              fill="currentColor"
            ></path>
          </svg>
        </Link>
      )
    },
  },
  head: () => {
    const { frontMatter } = useConfig()
    const pathname = usePathname()

    const title = frontMatter.title || defaultMeta.title
    const description = frontMatter.description || defaultMeta.description
    const image = frontMatter.coverImage || defaultMeta.image
    const url = `https://www.npi.ai${pathname}`

    return (
      <>
        <link
          rel="icon"
          href="/favicon.ico"
          type="image/x-icon"
          sizes="32x32"
        />

        <meta name="robots" content="follow, index" />
        <meta name="description" content={description} />
        <meta property="og:url" content={url} />
        <meta property="og:type" content="website" />
        <meta property="og:title" content={title} />
        <meta property="og:description" content={description} />
        <meta property="og:image" content={image} />

        {/*twitter*/}
        <meta name="twitter:card" content="summary_large_image" />
        <meta property="twitter:domain" content="npi.ai" />
        <meta name="twitter:url" content={url} />
        <meta name="twitter:title" content={title} />
        <meta name="twitter:description" content={description} />
        <meta name="twitter:image" content={image} />
      </>
    )
  },
  footer: {
    text: () => {
      return (
        <Link
          href="/"
          className="inline-flex items-center gap-2 hover:underline"
        >
          <Image
            src="/images/logo.svg"
            alt="NPi AI"
            width={16}
            height={16}
            className="dark:invert"
          />
          NPi AI &copy; {new Date().getFullYear()}
        </Link>
      )
    },
  },
  main: ({ children }: { children: React.ReactNode }) => {
    const { frontMatter } = useConfig()
    const pathname = usePathname()

    if (!/blog\/(?!tags\/).*/.test(pathname)) {
      return children
    }

    const tags = frontMatter.tag?.split(',').map((tag: string) => tag.trim())

    return (
      <>
        <h1
          className="my-4 text-4xl font-bold leading-tight tracking-tight
            text-slate-900 dark:text-slate-100"
        >
          {frontMatter.title}
        </h1>
        {/* author and date */}
        <p className="my-4 text-sm text-slate-500 dark:text-slate-400">
          {frontMatter.author || 'NPi Authors'}
          {frontMatter.date ? ` • ${frontMatter.date}` : ''}
        </p>

        {/* tags */}
        {tags ? (
          <nav className="mb-10 mt-6 flex flex-wrap gap-2">
            {tags.map((tag: string) => (
              <Link
                key={tag}
                href="/blog/tags/[tag]"
                as={`/blog/tags/${tag}`}
                className="text-nowrap rounded-md bg-blue-500 px-2 py-1 text-sm
                  text-white transition-all hover:opacity-75 dark:bg-blue-900
                  dark:text-slate-100"
              >
                {tag}
              </Link>
            ))}
          </nav>
        ) : null}
        {children}
      </>
    )
  },
}

export default config
