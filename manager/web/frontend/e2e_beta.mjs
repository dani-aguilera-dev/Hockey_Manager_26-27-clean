import { chromium } from 'playwright-core'

const base = process.env.BASE_URL || 'http://127.0.0.1:5000'
const executablePath = process.env.CHROME_PATH || `${process.env.HOME}/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`

const browser = await chromium.launch({ headless: true, executablePath })
const context = await browser.newContext({ baseURL: base })
const page = await context.newPage()

const result = {}
try {
  const created = await context.request.post('/api/new-game', {
    data: { club_id: 'cd-terrassa', manager: 'E2E Beta', seed: '20261029' },
  })
  if (!created.ok()) throw new Error(`new-game HTTP ${created.status()}: ${await created.text()}`)
  result.newGame = (await created.json()).ok

  await page.goto('/app/game/calendar')
  await page.getByRole('heading', { name: 'Calendario y amistosos' }).waitFor()
  await page.getByText('VISTA MENSUAL').waitFor()
  result.calendar = true
  await page.getByRole('button', { name: 'Mes siguiente' }).click()
  result.monthNavigation = true

  const quick = await context.request.post('/api/match/quick', { data: { travel: 'equilibrado' } })
  if (!quick.ok()) throw new Error(`quick HTTP ${quick.status()}: ${await quick.text()}`)
  result.quickMatch = true

  await page.goto('/app/game/report')
  await page.getByText('Árbitro:').waitFor()
  await page.getByText('Strokes').waitFor()
  result.refereeAndSetPieces = true

  await page.goto('/app/game/press/post')
  await page.getByRole('heading', { name: 'La voz del vestuario' }).waitFor()
  const questionCount = await page.locator('.press-question').count()
  for (let index = 0; index < questionCount; index += 1) {
    await page.locator('.press-question').nth(index).locator('input[type="radio"]').first().check()
  }
  await page.getByRole('button', { name: 'Enviar respuestas' }).click()
  await page.getByText('Rueda completada').waitFor()
  result.postPress = true

  const live = await context.request.post('/api/match/live/start', { data: { travel: 'equilibrado' } })
  if (!live.ok()) throw new Error(`live HTTP ${live.status()}: ${await live.text()}`)
  await page.goto('/app/game/live')
  const viewer = page.locator('[data-testid="match-viewer-3d"] canvas')
  await viewer.waitFor()
  const box = await viewer.boundingBox()
  if (!box || box.width < 200 || box.height < 150) throw new Error(`viewer size ${JSON.stringify(box)}`)
  result.viewer3d = true
  await page.screenshot({ path: '/tmp/opencode/e2e_3d.png' })

  await page.goto('/app/game/commercial')
  await page.getByText('CONTRATOS INDIVIDUALES DE IMAGEN').waitFor()
  result.playerBrands = true

  await page.screenshot({ path: '/tmp/opencode/e2e_beta.png', fullPage: true })
  console.log(JSON.stringify(result))
} finally {
  await browser.close()
}
