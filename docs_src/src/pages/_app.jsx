import { useEffect, useRef } from 'react'

import { Footer, GithubButton } from '@/components/Footer'
import { Header } from '@/components/Header'

import '@/styles/tailwind.css'
import '@/styles/documentation.css'
import 'focus-visible'
import { Router, useRouter } from 'next/router'

import { MDXProvider } from '@mdx-js/react'
import Link from 'next/link'

import { Layout } from '@/components/documentation/Layout'
import { Container } from '@/components/Container'
import { Layout as ReleaseLayout } from '@/components/releases/Layout'
import * as mdxComponents from '@/components/documentation/mdx'
import * as releaseMdxComponents from '@/components/releases/mdx'
import { useMobileNavigationStore } from '@/components/documentation/MobileNavigation'

import { Analytics } from '@vercel/analytics/react'

function usePrevious(value) {
  let ref = useRef()

  useEffect(() => {
    ref.current = value
  }, [value])

  return ref.current
}

function onRouteChange() {
  useMobileNavigationStore.getState().close()
}

Router.events.on('routeChangeStart', onRouteChange)
Router.events.on('hashChangeStart', onRouteChange)
export default function App({ Component, pageProps, router }) {
  let previousPathname = usePrevious(router.pathname)
  let router_ = useRouter()

  if (router_.pathname.includes('documentation')) {
    return (
      <>
        <Header />
        <MDXProvider components={mdxComponents}>
          <Layout {...pageProps}>
            <Component {...pageProps} />
          </Layout>
        </MDXProvider>
        <Analytics />
      </>
    )
  } else if (router_.pathname.includes('release')) {
    return (
      <>
        <Header />
        <ReleaseLayout>
          <Component {...pageProps} />
        </ReleaseLayout>
        <Footer />
        <Analytics />
      </>
    )
  }

  return (
    <>
      <div className="fixed inset-0 flex justify-center sm:px-8">
        <div className="flex w-full">
          <div className="w-full bg-black" />
        </div>
      </div>
      <div className="relative">
        <Header />
        <main>
          <Component previousPathname={previousPathname} {...pageProps} />
        </main>
        <Footer />
      </div>
      <Analytics />
    </>
  )
}
