import nextMDX from '@next/mdx'
import { remarkPlugins } from './mdx/remark.mjs'
import { rehypePlugins } from './mdx/rehype.mjs'
import { recmaPlugins } from './mdx/recma.mjs'

const withMDX = nextMDX({
  options: {
    remarkPlugins,
    rehypePlugins,
    recmaPlugins,
    providerImportSource: '@mdx-js/react',
  },
})

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  pageExtensions: ['js', 'jsx', 'ts', 'tsx', 'mdx'],
  experimental: {
    scrollRestoration: true,
  },
  i18n: {
    locales: ['en', 'zh'],
    defaultLocale: 'en',
    localeDetection: false,
  },
  async redirects() {
    return [
      {
        source: '/documentation',
        destination: '/documentation/en',
        permanent: false,
      },
    ]
  },
}

export default withMDX(nextConfig)
