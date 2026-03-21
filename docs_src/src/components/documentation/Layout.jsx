import { motion } from 'framer-motion'
import { useRouter } from 'next/router'

import { Footer } from '@/components/Footer'
import { SEO, BreadcrumbJsonLd } from '@/components/SEO'
import { BottomNavbar } from '@/components/documentation/BottomNavbar'
import { Navigation } from '@/components/documentation/Navigation'
import { Prose } from '@/components/documentation/Prose'
import { SectionProvider } from '@/components/documentation/SectionProvider'

function buildBreadcrumbs(path) {
  const cleanPath = path.split(/[?#]/)[0]
  const segments = cleanPath.split('/').filter(Boolean)
  const items = [{ name: 'Home', href: '/' }]

  let currentPath = ''
  for (const segment of segments) {
    currentPath += `/${segment}`
    const name = segment
      .replace(/_/g, ' ')
      .replace(/-/g, ' ')
      .replace(/\b\w/g, (c) => c.toUpperCase())
    items.push({ name, href: currentPath })
  }

  return items
}

export function Layout({ children, title, description, sections = [] }) {
  const router = useRouter()
  const breadcrumbs = buildBreadcrumbs(router.asPath)

  const pageTitle = title || breadcrumbs[breadcrumbs.length - 1]?.name || 'Documentation'
  const pageDescription =
    description ||
    `Robyn documentation — ${pageTitle}. Learn how to build fast Python web applications with Robyn's Rust-powered runtime.`

  return (
    <SectionProvider sections={sections}>
      <SEO
        title={pageTitle}
        description={pageDescription}
        jsonLd={BreadcrumbJsonLd(breadcrumbs)}
      />
      <div className="lg:ml-72 xl:ml-80">
        <motion.header
          layoutScroll
          className="contents lg:pointer-events-none lg:fixed lg:inset-0 lg:z-40 lg:flex"
        >
          <div className="contents lg:pointer-events-auto lg:block lg:w-72 lg:overflow-y-auto lg:border-white/10 lg:px-6 lg:pb-8 xl:w-80">
            <BottomNavbar />

            <Navigation className="hidden lg:mt-32 lg:block" />
          </div>
        </motion.header>
        <div className="relative px-4 sm:px-6 lg:px-8">
          <main className="py-16">
            <Prose>{children}</Prose>
          </main>
          <Footer />
        </div>
      </div>
    </SectionProvider>
  )
}
