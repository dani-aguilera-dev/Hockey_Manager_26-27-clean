import { assert, createGame, run } from './e2e_helpers.mjs'

await run('smoke', async ({ context, page }) => {
  const result = {}

  const health = await context.request.get('/api/health')
  assert(health.ok(), `health HTTP ${health.status()}`)
  result.health = true

  await createGame(context, 'E2E Smoke', '101')
  result.newGame = true

  await page.goto('/app/game')
  await page.getByText('Tu primera semana').waitFor()
  result.onboarding = true
  result.dashboard = await page.locator('.dashboard-kpis').count() > 0

  await page.goto('/app/game/calendar')
  await page.getByRole('heading', { name: 'Calendario y amistosos' }).waitFor()
  await page.getByText('VISTA MENSUAL').waitFor()
  result.calendar = true

  await page.goto('/app/game/squad')
  await page.getByRole('heading', { name: 'Plantilla' }).waitFor()
  result.squad = true

  await page.goto('/app/game/tactics')
  await page.getByRole('heading', { name: 'Táctica y once' }).waitFor()
  result.tactics = true

  await page.goto('/app/game/market')
  await page.getByRole('heading', { name: 'Mercado', exact: true }).waitFor()
  result.market = true

  const quick = await context.request.post('/api/match/quick', { data: { travel: 'equilibrado' } })
  assert(quick.ok(), `quick HTTP ${quick.status()}: ${await quick.text()}`)
  result.quickMatch = true

  await page.goto('/app/game/report')
  await page.getByText('Árbitro:').waitFor()
  await page.getByText('Decisiones arbitrales').waitFor()
  result.report = true

  await page.goto('/app/game/analysis')
  await page.getByRole('heading', { name: 'Análisis de partido' }).waitFor()
  await page.locator('.analysis-timeline').waitFor()
  result.analysis = true

  await page.goto('/app/game/options')
  await page.getByRole('heading', { name: /La interfaz/ }).waitFor()
  await page.getByRole('radio', { name: /English/ }).check()
  await page.locator('.nav-link', { hasText: 'Squad' }).first().waitFor()
  result.i18nEnglish = await page.evaluate(() => document.documentElement.lang === 'en')
  await page.reload()
  await page.locator('.nav-link', { hasText: 'Squad' }).first().waitFor()
  result.i18nPersisted = true
  await page.getByRole('radio', { name: /Español/ }).check()
  await page.locator('.nav-link', { hasText: 'Plantilla' }).first().waitFor()
  result.i18nSpanish = true

  return result
})
