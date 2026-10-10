/**
 * UI verification for UPSKILL AI (run: node verify-ui.mjs from frontend/)
 * Captures screenshots + console errors + emblem asset check.
 */
import { chromium } from 'playwright'
import { mkdirSync } from 'fs'

const BASE = 'http://localhost:5173'
const OUT = 'screenshots'
mkdirSync(OUT, { recursive: true })

const consoleErrors = []
const failedRequests = []

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1500, height: 845 } })

page.on('console', (msg) => {
  if (msg.type() === 'error') consoleErrors.push(msg.text())
})
page.on('requestfailed', (req) => failedRequests.push(`${req.url()} :: ${req.failure()?.errorText}`))
page.on('pageerror', (err) => consoleErrors.push(`PAGEERROR: ${err.message}`))

// ── 1. Login page ──────────────────────────────────────────────
await page.goto(BASE, { waitUntil: 'networkidle' })
await page.waitForTimeout(1200)
await page.screenshot({ path: `${OUT}/01-login-light.png` })

// Emblem asset actually rendered?
const emblemOk = await page.evaluate(() => {
  const img = document.querySelector('img.emblem-svg')
  if (!img) return 'NO-IMG'
  return img.complete && img.naturalWidth > 0 ? `OK ${img.naturalWidth}x${img.naturalHeight}` : 'BROKEN'
})
console.log('LOGIN emblem img:', emblemOk)

// Card position sanity: card should be horizontally centered in viewport
const cardBox = await page.evaluate(() => {
  const card = document.querySelector('.login-glass-card')
  if (!card) return null
  const r = card.getBoundingClientRect()
  return { left: Math.round(r.left), right: Math.round(r.right), vw: window.innerWidth, center: Math.round(r.left + r.width / 2) }
})
console.log('LOGIN card box:', JSON.stringify(cardBox), cardBox ? `-> offset from center: ${cardBox.center - cardBox.vw / 2}px` : '')

// ── 2. Login with demo credentials ─────────────────────────────
await page.fill('input[type="email"]', 'demo@statlearn.local')
await page.fill('input[type="password"]', 'Demo@12345')
await page.click('.card-submit-btn')
await page.waitForTimeout(2500)

const url = page.url()
console.log('After login URL:', url)
await page.screenshot({ path: `${OUT}/02-dashboard-light.png`, fullPage: false })

// Dashboard emblem + map present?
const dashChecks = await page.evaluate(() => {
  const emb = document.querySelector('.top-gov-emblem img.emblem-svg')
  const map = document.querySelector('.hero-map-graphic svg')
  return {
    emblem: emb ? (emb.complete && emb.naturalWidth > 0 ? 'OK' : 'BROKEN') : 'MISSING',
    map: map ? 'PRESENT' : 'MISSING',
  }
})
console.log('DASHBOARD:', JSON.stringify(dashChecks))

// ── 3. Dark mode ───────────────────────────────────────────────
const themeBtn = await page.$('button[class*="theme"], [class*="theme-toggle"]')
if (themeBtn) {
  await themeBtn.click()
  await page.waitForTimeout(800)
  await page.screenshot({ path: `${OUT}/03-dashboard-dark.png` })
  console.log('Dark mode toggled via button')
} else {
  // Fall back to settings page toggle
  const clicked = await page.evaluate(() => {
    const btns = [...document.querySelectorAll('button')]
    const b = btns.find((x) => /dark/i.test(x.textContent || ''))
    if (b) { b.click(); return b.textContent.trim() }
    return null
  })
  await page.waitForTimeout(800)
  await page.screenshot({ path: `${OUT}/03-dashboard-dark.png` })
  console.log('Dark mode toggled via:', clicked)
}

const isDark = await page.evaluate(() => document.documentElement.dataset.theme || document.body.className)
console.log('Theme state:', isDark)

// ── 4. Mobile login ────────────────────────────────────────────
const mob = await browser.newPage({ viewport: { width: 420, height: 900 } })
await mob.goto(BASE, { waitUntil: 'networkidle' })
await mob.waitForTimeout(800)
await mob.screenshot({ path: `${OUT}/04-login-mobile.png`, fullPage: true })

console.log('\nCONSOLE ERRORS:', consoleErrors.length ? consoleErrors : 'none')
console.log('FAILED REQUESTS:', failedRequests.length ? failedRequests : 'none')

await browser.close()
