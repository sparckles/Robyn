/** @type {import('next-sitemap').IConfig} */
module.exports = {
  siteUrl: process.env.NEXT_PUBLIC_SITE_URL || 'https://robyn.tech',
  generateRobotsTxt: false,
  generateIndexSitemap: false,
  outDir: 'public',
  exclude: ['/api/*'],
  alternateRefs: [
    {
      href: 'https://robyn.tech',
      hreflang: 'en',
    },
    {
      href: 'https://robyn.tech/zh',
      hreflang: 'zh',
    },
  ],
}
