// modified from https://github.com/vercel/swr-site/blob/01ab74e8ce302d6c6a108b09d9c3ea01c53db90c/components/blog-index.js
import Link from 'next/link'
import { useRouter } from 'next/router'
import { getPagesUnderRoute } from 'nextra/context'

function PostList({ tag }: { tag?: string }) {
  if (!tag) {
    return null
  }

  const posts = getPagesUnderRoute('/blog')
    .filter((page) => page.kind === 'MdxPage')
    .filter((page) => {
      // @ts-expect-error: frontMatter exists on Page
      const { frontMatter } = page
      return frontMatter.tag
        ?.split(',')
        .map((t) => t.trim())
        .includes(tag)
    })
    .map((page) => {
      // @ts-expect-error: frontMatter exists on Page
      const { frontMatter, meta } = page
      return (
        <div key={page.route} className="mb-10 space-y-4">
          <h1>
            <Link
              href={page.route}
              className="text-2xl font-semibold hover:underline"
            >
              {meta?.title || frontMatter?.title || page.name}
            </Link>
          </h1>
          <p className="leading-7 opacity-80">
            {frontMatter?.description}{' '}
            <span className="inline-block">
              <Link
                href={page.route}
                className="text-[color:hsl(var(--nextra-primary-hue),100%,50%)]
                  underline decoration-from-font underline-offset-2
                  hover:opacity-75"
              >
                <span className="ml-2">Read more →</span>
              </Link>
            </span>
          </p>
          {frontMatter?.date ? (
            <p className="my-4 text-sm opacity-50">
              {frontMatter.author || 'NPi Authors'}
              {frontMatter.date ? ` • ${frontMatter.date}` : ''}
            </p>
          ) : null}
        </div>
      )
    })

  return <>{posts}</>
}

export default function TaggedPosts() {
  const router = useRouter()
  const tag = router.query.tag as string | undefined

  return (
    <>
      <h1 className="my-10 text-center text-4xl font-extrabold md:text-5xl">
        Posts Tagged with “{tag}”
      </h1>

      <PostList tag={tag} />
    </>
  )
}
