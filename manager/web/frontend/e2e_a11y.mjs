import axe from 'axe-core'
import { assert, createGame, run } from './e2e_helpers.mjs'

const pages = [
  ['dashboard', '/app/game'],
  ['calendar', '/app/game/calendar'],
  ['squad', '/app/game/squad'],
  ['tactics', '/app/game/tactics'],
  ['market', '/app/game/market'],
  ['training', '/app/game/training'],
  ['match', '/app/game/match'],
  ['report', '/app/game/report'],
  ['board', '/app/game/board'],
  ['finance', '/app/game/finance'],
  ['shortlist', '/app/game/shortlist'],
]

await run('a11y', async ({ context, page }) => {
  const result = { pages: {}, violations: [], keyboard: {} }
  await createGame(context, 'E2E A11y', '303')
  const quick = await context.request.post('/api/match/quick', { data: { travel: 'equilibrado' } })
  assert(quick.ok(), `quick HTTP ${quick.status()}`)

  // Skip link: primer Tab debe enfocarlo.
  await page.goto('/app/game')
  await page.getByText('Tu primera semana').waitFor()
  await page.keyboard.press('Tab')
  const firstFocus = await page.evaluate(() => ({
    text: document.activeElement?.textContent?.trim() || '',
    href: document.activeElement?.getAttribute('href') || '',
  }))
  assert(firstFocus.text.includes('Saltar al contenido'), `primer foco: ${JSON.stringify(firstFocus)}`)
  result.keyboard.skipLink = firstFocus.href === '#main'
  await page.keyboard.press('Enter')
  await page.waitForTimeout(100)
  result.keyboard.skipTarget = await page.evaluate(() => document.activeElement?.id || document.activeElement?.tagName)

  // Navegación principal: enlaces con nombre accesible.
  const navNames = await page.locator('nav a').evaluateAll((links) =>
    links.map((link) => (link.textContent || '').trim()).filter(Boolean),
  )
  result.keyboard.navLinks = navNames.length
  assert(navNames.length > 0, 'la navegación no tiene enlaces')

  async function audit(name, path) {
    await page.goto(path)
    await page.waitForTimeout(350)
    await page.addScriptTag({ content: axe.source })
    const report = await page.evaluate(async () => {
      const output = await window.axe.run(document, {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'] },
      })
      return {
        violations: output.violations.map((violation) => ({
          id: violation.id,
          impact: violation.impact,
          help: violation.help,
          nodes: violation.nodes.length,
          targets: violation.nodes.slice(0, 3).map((node) => node.target.join(' ')),
        })),
        passes: output.passes.length,
      }
    })
    result.pages[name] = { violations: report.violations.length, passes: report.passes }
    for (const violation of report.violations) {
      result.violations.push({ page: name, ...violation })
    }
  }

  for (const [name, path] of pages) {
    await audit(name, path)
  }

  // Auditoría móvil: mismas pantallas clave a 390x844.
  await page.setViewportSize({ width: 390, height: 844 })
  for (const [name, path] of pages.slice(0, 4)) {
    await audit(`mobile-${name}`, path)
  }

  result.serious = result.violations.filter((item) => item.impact === 'serious' || item.impact === 'critical').length
  result.totalViolations = result.violations.length
  return result
})
