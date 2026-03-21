import Link from 'next/link'
import { SEO } from '@/components/SEO'
import { Container } from '@/components/Container'
import { getAllBlogPosts } from '@/lib/getAllBlogPosts'
import { formatDate } from '@/lib/formatDate'

export default function BlogIndex({ posts }) {
  return (
    <>
      <SEO
        title="Blog"
        description="News, tutorials, and insights from the Robyn Python web framework team. Learn about building fast web applications with Python and Rust."
      />
      <Container className="mt-16 sm:mt-32">
        <div className="mx-auto max-w-2xl">
          <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Blog
          </h1>
          <p className="mt-6 text-base text-gray-400">
            News, tutorials, and insights from the Robyn team.
          </p>

          <div className="mt-16 space-y-20">
            {posts.map((post) => (
              <article key={post.slug} className="group relative flex flex-col items-start">
                <h2 className="text-base font-semibold tracking-tight text-white">
                  <Link href={`/blog/${post.slug}`}>
                    <span className="absolute -inset-x-4 -inset-y-6 z-20 sm:-inset-x-6 sm:rounded-2xl" />
                    <span className="relative z-10">{post.title}</span>
                  </Link>
                </h2>
                <time
                  className="relative z-10 order-first mb-3 flex items-center pl-3.5 text-sm text-gray-500"
                  dateTime={post.date}
                >
                  <span className="absolute inset-y-0 left-0 flex items-center" aria-hidden="true">
                    <span className="h-4 w-0.5 rounded-full bg-yellow-500" />
                  </span>
                  {formatDate(post.date)}
                </time>
                <p className="relative z-10 mt-2 text-sm text-gray-400">
                  {post.description}
                </p>
                <div aria-hidden="true" className="relative z-10 mt-4 flex items-center text-sm font-medium text-yellow-400">
                  Read post
                  <svg viewBox="0 0 16 16" fill="none" aria-hidden="true" className="ml-1 h-4 w-4 stroke-current">
                    <path d="M6.75 5.75 9.25 8l-2.5 2.25" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                  </svg>
                </div>
              </article>
            ))}
          </div>

          {posts.length === 0 && (
            <p className="mt-10 text-gray-500">
              No blog posts yet. Check back soon!
            </p>
          )}
        </div>
      </Container>
    </>
  )
}

export async function getStaticProps() {
  const posts = getAllBlogPosts()
  return {
    props: {
      posts,
    },
  }
}
