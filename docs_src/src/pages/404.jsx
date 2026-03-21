import Link from 'next/link'
import { SEO } from '@/components/SEO'
import { Container } from '@/components/Container'

export default function NotFound() {
  return (
    <>
      <SEO title="Page Not Found" description="The page you're looking for doesn't exist." noindex />
      <Container className="mt-16 sm:mt-32">
        <div className="flex flex-col items-center text-center">
          <p className="text-base font-semibold text-yellow-400">404</p>
          <h1 className="mt-4 text-4xl font-bold tracking-tight text-white sm:text-5xl">
            Page not found
          </h1>
          <p className="mt-4 text-base text-gray-400">
            Sorry, we couldn&apos;t find the page you&apos;re looking for.
          </p>
          <div className="mt-10 flex items-center gap-x-6">
            <Link
              href="/"
              className="rounded-md bg-yellow-500 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-yellow-600"
            >
              Go back home
            </Link>
            <Link
              href="/documentation/en"
              className="text-sm font-semibold text-white"
            >
              Documentation <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>
      </Container>
    </>
  )
}
