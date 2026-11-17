import { assert, createGame, run } from './e2e_helpers.mjs'

await run('i18n', async ({ context, page }) => {
  const result = {}
  await createGame(context, 'E2E i18n', '404')

  await page.goto('/app/game/options')
  await page.getByRole('heading', { name: /La interfaz/ }).waitFor()
  await page.getByRole('radio', { name: /English/ }).check()
  await page.getByRole('heading', { name: 'The interface, your way.' }).waitFor()
  result.options = await page.getByText('Text size', { exact: true }).isVisible()

  await page.goto('/app/game/squad')
  await page.getByRole('heading', { name: 'Squad', exact: true }).waitFor()
  await page.getByText('Filter by line', { exact: true }).waitFor()
  result.squad = await page.getByText('Wage bill', { exact: true }).isVisible()

  await page.goto('/app/game/market')
  await page.getByRole('heading', { name: 'Transfer market', exact: true }).waitFor()
  await page.getByRole('tab', { name: /Players/ }).click()
  await page.getByText('Apply filters', { exact: true }).waitFor()
  result.market = await page.getByText('Transfer budget', { exact: true }).isVisible()

  await page.goto('/app/game/tactics')
  await page.getByRole('heading', { name: 'Tactics and lineup', exact: true }).waitFor()
  await page.getByText('SET PIECES', { exact: true }).waitFor()
  result.tactics = await page.getByText('Setup', { exact: true }).isVisible()

  await page.goto('/app/game/match')
  await page.getByRole('heading', { name: 'Match preview', exact: true }).waitFor()
  await page.getByText('Match keys', { exact: true }).waitFor()
  result.match = await page.getByText('Quick sim', { exact: true }).isVisible()

  const quick = await context.request.post('/api/match/quick', { data: { travel: 'equilibrado' } })
  assert(quick.ok(), `quick HTTP ${quick.status()}: ${await quick.text()}`)
  await page.goto('/app/game/report')
  await page.getByRole('heading', { name: /^(Win|Loss|Draw)$/ }).waitFor()
  await page.getByText('Refereeing decisions', { exact: true }).waitFor()
  result.report = await page.getByText('Statistics', { exact: true }).isVisible()

  const state = (await (await context.request.get('/api/state')).json()).data
  const playerId = state.team.players[0].id
  const teamId = state.team.id

  await page.goto(`/app/game/player/${playerId}`)
  await page.getByText('Performance', { exact: true }).waitFor()
  await page.getByText('Attributes', { exact: true }).waitFor()
  result.player = await page.getByText('Status and market', { exact: true }).isVisible()

  await page.goto(`/app/game/team/${teamId}`)
  await page.getByText(/record/i).first().waitFor()
  await page.getByText('Coaching staff', { exact: true }).waitFor()
  result.team = await page.getByText(/academy/i).first().isVisible()

  await page.goto('/app/game/training')
  await page.getByRole('heading', { name: 'Weekly training', exact: true }).waitFor()
  await page.getByText('Automatic plan', { exact: true }).waitFor()
  result.training = await page.getByText('Quick reference', { exact: true }).isVisible()

  await page.goto('/app/game/finance')
  await page.getByRole('heading', { name: 'Finance centre', exact: true }).waitFor()
  await page.getByText(/available cash/i).first().waitFor()
  result.finance = await page.getByText(/profit and loss/i).first().isVisible()

  await page.goto('/app/game/board')
  await page.getByRole('heading', { name: 'Board and club vision', exact: true }).waitFor()
  await page.getByText(/board confidence/i).first().waitFor()
  result.board = await page.getByText(/board requests/i).first().isVisible()

  await page.goto('/app/game/news')
  await page.getByRole('heading', { name: 'News', exact: true }).waitFor()
  result.news = await page.getByText('Back to club', { exact: true }).isVisible()

  await page.goto('/app/game/press')
  await page.getByRole('heading', { name: 'Press conference', exact: true }).waitFor()
  await page.getByText(/accredited outlet/i).first().waitFor()
  result.press = await page.getByText(/media relations/i).first().isVisible()

  await page.goto('/app/game/jobs')
  await page.getByRole('heading', { name: 'Job security', exact: true }).waitFor()
  await page.getByText(/board confidence/i).first().waitFor()
  result.jobs = await page.getByText('Find offers', { exact: true }).isVisible()

  await page.goto('/app/game/options')
  await page.getByRole('radio', { name: /Español/ }).check()
  await page.getByRole('heading', { name: /La interfaz/ }).waitFor()
  result.spanishRestored = await page.getByText('Tamaño del texto', { exact: true }).isVisible()

  return result
})
