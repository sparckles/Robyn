import Head from 'next/head'
import { useRouter } from 'next/router'

const SITE_URL = (process.env.NEXT_PUBLIC_SITE_URL || 'https://robyn.tech').replace(/\/+$/, '')
const DEFAULT_OG_IMAGE = `${SITE_URL}/robynog.png`
const TWITTER_HANDLE = '@robaborobyn'
const SITE_NAME = 'Robyn Framework'

function escapeJsonLd(obj) {
  return JSON.stringify(obj).replace(/</g, '\\u003c').replace(/>/g, '\\u003e')
}

export function SEO({
  title,
  description,
  ogImage = DEFAULT_OG_IMAGE,
  ogType = 'website',
  noindex = false,
  jsonLd,
}) {
  const router = useRouter()
  const cleanPath = router.asPath.split(/[?#]/)[0]
  const canonicalUrl = `${SITE_URL}${cleanPath}`

  const fullTitle = title
    ? `${title} | ${SITE_NAME}`
    : 'Robyn - A Fast, Innovator Friendly, and Community Driven Python Web Framework'

  const defaultDescription =
    'Robyn is a high-performance async Python web framework powered by a Rust runtime. Build fast, scalable web applications with Python simplicity and Rust speed.'

  const metaDescription = description || defaultDescription

  const locales = router.locales || ['en', 'zh']
  const defaultLocale = router.defaultLocale || 'en'

  const localePrefix = new RegExp(`^/(${locales.join('|')})(/|$)`)
  const normalizedPath = cleanPath.replace(localePrefix, '/$2').replace(/^\/\//, '/')

  return (
    <Head>
      <title>{fullTitle}</title>
      <meta name="description" content={metaDescription} />
      {noindex && <meta name="robots" content="noindex,nofollow" />}

      <link rel="canonical" href={canonicalUrl} />

      {locales.map((locale) => {
        const href =
          locale === defaultLocale
            ? `${SITE_URL}${normalizedPath}`
            : `${SITE_URL}/${locale}${normalizedPath}`
        return (
          <link
            key={locale}
            rel="alternate"
            hrefLang={locale}
            href={href}
          />
        )
      })}
      <link rel="alternate" hrefLang="x-default" href={`${SITE_URL}${normalizedPath}`} />

      {/* Open Graph */}
      <meta property="og:title" content={fullTitle} />
      <meta property="og:description" content={metaDescription} />
      <meta property="og:image" content={ogImage} />
      <meta property="og:url" content={canonicalUrl} />
      <meta property="og:type" content={ogType} />
      <meta property="og:site_name" content={SITE_NAME} />
      <meta property="og:locale" content={router.locale === 'zh' ? 'zh_CN' : 'en_US'} />

      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:site" content={TWITTER_HANDLE} />
      <meta name="twitter:title" content={fullTitle} />
      <meta name="twitter:description" content={metaDescription} />
      <meta name="twitter:image" content={ogImage} />

      {/* JSON-LD Structured Data */}
      {jsonLd && (
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: escapeJsonLd(jsonLd) }}
        />
      )}
    </Head>
  )
}

export function WebsiteJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: SITE_NAME,
    url: SITE_URL,
    description:
      'Robyn is a high-performance async Python web framework powered by a Rust runtime.',
    potentialAction: {
      '@type': 'SearchAction',
      target: {
        '@type': 'EntryPoint',
        urlTemplate: `${SITE_URL}/documentation/en?q={search_term_string}`,
      },
      'query-input': 'required name=search_term_string',
    },
  }
}

export function SoftwareApplicationJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'SoftwareSourceCode',
    name: 'Robyn',
    description:
      'A high-performance, community-driven async Python web framework with a Rust runtime.',
    url: SITE_URL,
    codeRepository: 'https://github.com/sparckles/robyn',
    programmingLanguage: ['Python', 'Rust'],
    license: 'https://opensource.org/licenses/BSD-2-Clause',
    operatingSystem: 'Cross-platform',
    runtimePlatform: 'Python 3.10+',
    author: OrganizationJsonLd(),
    offers: {
      '@type': 'Offer',
      price: '0',
      priceCurrency: 'USD',
    },
  }
}

export function OrganizationJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Sparckles',
    url: 'https://github.com/sparckles',
    logo: `${SITE_URL}/robynog.png`,
    sameAs: [
      'https://github.com/sparckles/robyn',
      'https://discord.gg/rkERZ5eNU8',
    ],
  }
}

export function BreadcrumbJsonLd(items) {
  return {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: items.map((item, index) => ({
      '@type': 'ListItem',
      position: index + 1,
      name: item.name,
      item: item.href ? `${SITE_URL}${item.href}` : undefined,
    })),
  }
}
