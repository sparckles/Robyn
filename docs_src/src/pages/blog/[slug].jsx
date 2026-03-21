import { MDXProvider } from '@mdx-js/react'
import { serialize } from 'next-mdx-remote/serialize'
import { MDXRemote } from 'next-mdx-remote'
import { SEO, BreadcrumbJsonLd } from '@/components/SEO'
import { Container } from '@/components/Container'
import { getAllBlogPosts, getBlogPostBySlug } from '@/lib/getAllBlogPosts'
import Link from 'next/link'

function formatDate(dateString) {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

const blogMdxComponents = {
  h1: (props) => <h1 className="text-3xl font-bold text-white mt-8 mb-4" {...props} />,
  h2: (props) => <h2 className="text-2xl font-bold text-white mt-8 mb-3" {...props} />,
  h3: (props) => <h3 className="text-xl font-semibold text-white mt-6 mb-2" {...props} />,
  p: (props) => <p className="text-gray-300 leading-7 mb-4" {...props} />,
  ul: (props) => <ul className="list-disc list-inside text-gray-300 mb-4 space-y-1" {...props} />,
  ol: (props) => <ol className="list-decimal list-inside text-gray-300 mb-4 space-y-1" {...props} />,
  li: (props) => <li className="text-gray-300" {...props} />,
  a: (props) => <a className="text-yellow-400 hover:text-yellow-300 underline" {...props} />,
  code: (props) => <code className="bg-gray-800 rounded px-1.5 py-0.5 text-sm text-yellow-300" {...props} />,
  pre: (props) => <pre className="bg-gray-900 rounded-lg p-4 overflow-x-auto mb-4 border border-white/10" {...props} />,
  blockquote: (props) => <blockquote className="border-l-4 border-yellow-500 pl-4 italic text-gray-400 mb-4" {...props} />,
}

export default function BlogPost({ post }) {
  const breadcrumbs = BreadcrumbJsonLd([
    { name: 'Home', href: '/' },
    { name: 'Blog', href: '/blog' },
    { name: post.title },
  ])

  const articleJsonLd = {
    '@context': 'https://schema.org',
    '@type': 'TechArticle',
    headline: post.title,
    description: post.description,
    datePublished: post.date,
    author: {
      '@type': 'Organization',
      name: 'Sparckles',
      url: 'https://github.com/sparckles',
    },
    publisher: {
      '@type': 'Organization',
      name: 'Robyn Framework',
      url: 'https://robyn.tech',
    },
  }

  return (
    <>
      <SEO
        title={post.title}
        description={post.description}
        ogType="article"
        jsonLd={[breadcrumbs, articleJsonLd]}
      />
      <Container className="mt-16 sm:mt-32">
        <div className="mx-auto max-w-2xl">
          <nav className="mb-8" aria-label="Breadcrumb">
            <ol className="flex items-center space-x-2 text-sm text-gray-500">
              <li><Link href="/" className="hover:text-gray-300">Home</Link></li>
              <li aria-hidden="true">/</li>
              <li><Link href="/blog" className="hover:text-gray-300">Blog</Link></li>
              <li aria-hidden="true">/</li>
              <li className="text-gray-300">{post.title}</li>
            </ol>
          </nav>

          <article>
            <header className="flex flex-col">
              <time
                dateTime={post.date}
                className="order-first flex items-center text-base text-gray-500"
              >
                <span className="h-4 w-0.5 rounded-full bg-yellow-500" />
                <span className="ml-3">{formatDate(post.date)}</span>
              </time>
              <h1 className="mt-6 text-4xl font-bold tracking-tight text-white sm:text-5xl">
                {post.title}
              </h1>
            </header>

            <div className="mt-8">
              <MDXProvider components={blogMdxComponents}>
                <MDXRemote {...post.content} components={blogMdxComponents} />
              </MDXProvider>
            </div>
          </article>

          <div className="mt-16 border-t border-white/10 pt-8">
            <Link href="/blog" className="text-sm font-medium text-yellow-400 hover:text-yellow-300">
              ← Back to blog
            </Link>
          </div>
        </div>
      </Container>
    </>
  )
}

export async function getStaticPaths() {
  const posts = getAllBlogPosts()
  return {
    paths: posts.map((post) => ({ params: { slug: post.slug } })),
    fallback: false,
  }
}

export async function getStaticProps({ params }) {
  const post = getBlogPostBySlug(params.slug)
  const content = await serialize(post.content)

  return {
    props: {
      post: {
        ...post,
        content,
      },
    },
  }
}
