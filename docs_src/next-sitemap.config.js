/** @type {import('next-sitemap').IConfig} */
const siteUrl = process.env.NEXT_PUBLIC_SITE_URL || 'https://robyn.tech'

module.exports = {
  siteUrl,
  generateRobotsTxt: false,
  generateIndexSitemap: false,
  outDir: 'public',
  exclude: ['/api/*'],
  alternateRefs: [
    {
      href: siteUrl,
      hreflang: 'en',
    },
    {
      href: `${siteUrl}/zh`,
      hreflang: 'zh',
    },
  ],
}
