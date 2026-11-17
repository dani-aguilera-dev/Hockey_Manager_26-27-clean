import { chromium } from 'playwright-core'

export const base = process.env.BASE_URL || 'http://127.0.0.1:5000'
export const executablePath =
  process.env.CHROME_PATH || `${process.env.HOME}/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome`

export async function openApp() {
  const browser = await chromium.launch({ headless: true, executablePath })
  const context = await browser.newContext({ baseURL: base })
  const page = await context.newPage()
  page.on('dialog', async (dialog) => {
    await dialog.accept()
  })
  return { browser, context, page }
}

export async function createGame(context, manager, seed) {
  const response = await context.request.post('/api/new-game', {
    data: { club_id: 'cd-terrassa', manager, seed },
  })
  if (!response.ok()) throw new Error(`new-game HTTP ${response.status()}: ${await response.text()}`)
  const payload = await response.json()
  if (!payload.ok) throw new Error(`new-game rejected: ${JSON.stringify(payload)}`)
  return payload.data
}

export function assert(condition, message) {
  if (!condition) throw new Error(message)
}

export async function run(name, body) {
  const started = Date.now()
  let browser
  try {
    const app = await openApp()
    browser = app.browser
    const result = await body(app)
    result.ok = true
    result.suite = name
    result.ms = Date.now() - started
    console.log(JSON.stringify(result))
    process.exitCode = 0
  } catch (error) {
    console.error(JSON.stringify({ ok: false, suite: name, error: String(error), ms: Date.now() - started }))
    process.exitCode = 1
  } finally {
    if (browser) await browser.close()
  }
}
