let cachedStars = null
let cachedAt = 0
const CACHE_TTL_MS = 15 * 60 * 1000
const CACHE_CONTROL = 'public, s-maxage=900, stale-while-revalidate=1800'

export default async function handler(req, res) {
  const now = Date.now()

  if (cachedStars !== null && now - cachedAt < CACHE_TTL_MS) {
    res.setHeader('Cache-Control', CACHE_CONTROL)
    return res.status(200).json({ stars: cachedStars })
  }

  try {
    const response = await fetch('https://api.github.com/repos/sparckles/robyn', {
      headers: { 'Accept': 'application/vnd.github.v3+json' },
    })

    if (!response.ok) {
      if (cachedStars !== null) {
        res.setHeader('Cache-Control', CACHE_CONTROL)
        return res.status(200).json({ stars: cachedStars })
      }
      return res.status(502).json({ error: 'Failed to fetch from GitHub' })
    }

    const data = await response.json()
    cachedStars = data.stargazers_count
    cachedAt = now

    res.setHeader('Cache-Control', CACHE_CONTROL)
    return res.status(200).json({ stars: cachedStars })
  } catch {
    if (cachedStars !== null) {
      res.setHeader('Cache-Control', CACHE_CONTROL)
      return res.status(200).json({ stars: cachedStars })
    }
    return res.status(502).json({ error: 'Failed to fetch from GitHub' })
  }
}
