/**
 * UI verification for the Phase 8 new-user flow (run: node verify-onboarding.mjs
 * from frontend/, with backend + vite dev server running).
 *
 * Registers a brand-new user, verifies the onboarding gate appears, completes
 * onboarding, verifies the honest dashboard empty state, then starts the
 * diagnostic. Also re-checks the demo learner dashboard still renders.
 */
import { chromium } from 'playwright'
import { mkdirSync } from 'fs'

const BASE = 'http://localhost:5173'
const OUT = 'screenshots'
mkdirSync(OUT, { recursive: true })

const consoleErrors = []
const failedRequests = []

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1500, height: 900 } })
page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()) })
page.on('pageerror', (err) => consoleErrors.push(`PAGEERROR: ${err.message}`))
page.on('requestfailed', (req) => failedRequests.push(`${req.url()} :: ${req.failure()?.errorText}`))

const unique = Date.now()
const EMAIL = `ui_check_${unique}@statlearn.local`

// ── 1. Register a brand-new user through the UI ──
await page.goto(BASE, { waitUntil: 'networkidle' })
await page.click('text=Create Account')
await page.fill('input[placeholder="Full name"]', 'UI Check Officer')
await page.fill('input[placeholder="Email address"]', EMAIL)
await page.fill('input[placeholder="Password"]', 'UiCheck@123')
await page.click('.card-submit-btn')
await page.waitForTimeout(2500)
await page.screenshot({ path: `${OUT}/p8-01-onboarding-shown.png`, fullPage: true })

const onboardingVisible = await page.evaluate(() => !!document.querySelector('.onboarding-glass-card'))
console.log('ONBOARDING gate shown after signup:', onboardingVisible)

// ── 2. Complete onboarding (position + profile) ──
await page.click('.onboarding-role-card:has-text("Statistical Officer")')
await page.fill('#ob-designation', 'Statistical Officer (Grade II)')
await page.fill('#ob-department', 'Directorate of Economics & Statistics')
await page.fill('#ob-assignment', 'District survey compilation')
await page.fill('#ob-education', 'M.Sc. Statistics')
await page.fill('#ob-experience', '3 years')
await page.click('.card-submit-btn')
await page.waitForTimeout(2500)
await page.screenshot({ path: `${OUT}/p8-02-dashboard-empty-state.png`, fullPage: true })

const dashChecks = await page.evaluate(() => {
  const hero = document.querySelector('.hero-name')?.textContent || ''
  const newUserCard = !!document.querySelector('.dashboard-new-user-card')
  const startBtn = [...document.querySelectorAll('button')].some((b) => /start assessment/i.test(b.textContent || ''))
  const metricBoxes = document.querySelectorAll('.metric-box').length
  const donut = !!document.querySelector('.donut-meter-container')
  return { hero, newUserCard, startBtn, metricBoxes, donut }
})
console.log('NEW-USER DASHBOARD:', JSON.stringify(dashChecks))
console.log('  -> empty-state card:', dashChecks.newUserCard, '| Start Assessment button:', dashChecks.startBtn)
console.log('  -> fake metrics hidden (expect 0 boxes):', dashChecks.metricBoxes === 0, '| fake donut hidden:', dashChecks.donut === false)

// ── 3. Start the diagnostic from the empty state CTA ──
await page.click('text=Start Assessment')
await page.waitForTimeout(1200)
await page.screenshot({ path: `${OUT}/p8-03-diagnostic-start.png` })
const diagVisible = await page.evaluate(() =>
  [...document.querySelectorAll('button')].some((b) => /start diagnostic assessment/i.test(b.textContent || '')))
console.log('DIAGNOSTIC intro visible:', diagVisible)

// ── 4. Fresh tab: re-login as the same new user -> onboarding must NOT re-show ──
const page2 = await browser.newPage({ viewport: { width: 1500, height: 900 } })
await page2.goto(BASE, { waitUntil: 'networkidle' })
await page2.fill('input[placeholder="Email address"]', EMAIL)
await page2.fill('input[placeholder="Password"]', 'UiCheck@123')
await page2.click('.card-submit-btn')
await page2.waitForTimeout(2500)
const relogin = await page2.evaluate(() => ({
  onboarding: !!document.querySelector('.onboarding-glass-card'),
  emptyCard: !!document.querySelector('.dashboard-new-user-card'),
}))
console.log('RE-LOGIN same new user -> onboarding shown again (expect false):', relogin.onboarding, '| empty-state dashboard:', relogin.emptyCard)

// ── 5. Demo learner dashboard still renders with real data ──
await page2.click('button[class*="sidebar-logout"]')
await page2.waitForTimeout(1000)
await page2.fill('input[placeholder="Email address"]', 'demo@statlearn.local')
await page2.fill('input[placeholder="Password"]', 'Demo@12345')
await page2.click('.card-submit-btn')
await page2.waitForTimeout(2500)
await page2.screenshot({ path: `${OUT}/p8-04-demo-dashboard.png`, fullPage: true })
const demoDash = await page2.evaluate(() => ({
  onboarding: !!document.querySelector('.onboarding-glass-card'),
  emptyCard: !!document.querySelector('.dashboard-new-user-card'),
  metricBoxes: document.querySelectorAll('.metric-box').length,
  donut: !!document.querySelector('.donut-meter-container'),
}))
console.log('DEMO LEARNER dashboard:', JSON.stringify(demoDash))

console.log('\nCONSOLE ERRORS:', consoleErrors.length ? consoleErrors : 'none')
console.log('FAILED REQUESTS:', failedRequests.length ? failedRequests : 'none')

await browser.close()
