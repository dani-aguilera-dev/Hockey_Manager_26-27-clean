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
  await page.getByText('Strokes', { exact: true }).waitFor()
  await page.getByText('Decisiones arbitrales').waitFor()
  await page.getByText('Ventajas').waitFor()
  await page.getByText('Tiempo añadido').waitFor()
  result.refereeAndSetPieces = true
  result.refereeDiscretion = true
  result.refereeDiscipline = true

  await page.goto('/app/game/analysis')
  await page.getByRole('heading', { name: 'Análisis de partido' }).waitFor()
  await page.getByText('COMPARATIVA', { exact: true }).waitFor()
  await page.locator('.analysis-timeline').waitFor()
  result.analysis = true
  await page.screenshot({ path: '/tmp/opencode/e2e_analysis.png', fullPage: true })

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
  await page.waitForTimeout(1800)
  await page.evaluate(() => window.__matchViewer3D.forceBallBodyContact())
  await page.waitForTimeout(250)
  const viewerState = await page.evaluate(() => window.__matchViewer3D)
  if (!viewerState || viewerState.players !== 22) throw new Error(`viewer players ${JSON.stringify(viewerState)}`)
  if (viewerState.frames < 10) throw new Error(`viewer frames ${viewerState.frames}`)
  if (!(viewerState.ballSpeed > 0)) throw new Error(`viewer ball ${viewerState.ballSpeed}`)
  if (!(viewerState.bodyCollisions > 0)) throw new Error(`viewer body collisions ${viewerState.bodyCollisions}`)
  if (!(viewerState.stickCollisions > 0)) throw new Error(`viewer stick collisions ${viewerState.stickCollisions}`)
  if (viewerState.sticks !== 22) throw new Error(`viewer sticks ${viewerState.sticks}`)
  if (viewerState.bones < 22 * 17) throw new Error(`viewer bones ${viewerState.bones}`)
  if (!(viewerState.ikSolutions > 100)) throw new Error(`viewer ik ${viewerState.ikSolutions}`)
  if (!(viewerState.biomechSolutions > 0)) throw new Error(`viewer biomechanics ${viewerState.biomechSolutions}`)
  if (!(viewerState.clothUpdates > 0)) throw new Error(`viewer cloth ${viewerState.clothUpdates}`)
  result.viewerBiomechanics = {
    biomechSolutions: viewerState.biomechSolutions,
    clothUpdates: viewerState.clothUpdates,
  }
  await page.evaluate(() => window.__matchViewer3D.forceContact())
  await page.waitForTimeout(400)
  const materialState = await page.evaluate(() => window.__matchViewer3D)
  if (!(materialState.stickBodyCollisions > 0)) throw new Error(`viewer stick-body ${JSON.stringify(materialState)}`)
  if (!(materialState.materialBounces > 0)) throw new Error(`viewer material bounces ${materialState.materialBounces}`)
  if (!(materialState.stickFlexes > 0)) throw new Error(`viewer stick flexes ${materialState.stickFlexes}`)
  await page.getByTestId('live-protest-respectful').click()
  await page.locator('.protest-used').waitFor()
  result.liveProtest = true
  await page.getByRole('button', { name: 'Cámara táctica' }).click()
  result.viewer3d = true
  result.viewerMaterials = {
    stickBodyCollisions: materialState.stickBodyCollisions,
    materialBounces: materialState.materialBounces,
    stickFlexes: materialState.stickFlexes,
  }
  result.viewerSkeleton = { bones: viewerState.bones, sticks: viewerState.sticks, ikSolutions: viewerState.ikSolutions }
  result.viewerPhysics = {
    frames: viewerState.frames,
    playerCollisions: viewerState.playerCollisions,
    bodyCollisions: viewerState.bodyCollisions,
    stickCollisions: viewerState.stickCollisions,
    ballSpeed: viewerState.ballSpeed,
  }
  await page.screenshot({ path: '/tmp/opencode/e2e_3d.png' })

  let liveData = (await (await context.request.get('/api/match/live')).json()).data
  for (let attempt = 0; attempt < 4; attempt += 1) {
    const decision = liveData.last_decision
    if (decision && !decision.reviewed && decision.side !== liveData.user_side) break
    const advanced = await context.request.post('/api/match/live/advance', { data: { mode: 'quarter' } })
    if (!advanced.ok()) throw new Error(`live advance HTTP ${advanced.status()}: ${await advanced.text()}`)
    liveData = (await advanced.json()).data
  }
  const reviewDecision = liveData.last_decision
  if (!reviewDecision || reviewDecision.side === liveData.user_side) {
    throw new Error(`no reviewable decision ${JSON.stringify(reviewDecision)}`)
  }
  await page.reload()
  await page.getByRole('heading', { name: 'Partido en directo' }).waitFor()
  const reviewButton = page.getByRole('button', { name: 'Solicitar revisión' })
  await reviewButton.waitFor()
  await reviewButton.click()
  await page.locator('.review-row').first().waitFor()
  result.videoReview = true
  result.videoReviewType = reviewDecision.type
  await page.screenshot({ path: '/tmp/opencode/e2e_review.png', fullPage: true })

  await page.goto('/app/game/board')
  await page.getByRole('heading', { name: 'Junta y visión de club' }).waitFor()
  await page.getByText('VISIÓN DE CLUB', { exact: true }).waitFor()
  const boardRequest = page.locator('[data-testid="board-request-training"]')
  await boardRequest.waitFor()
  await boardRequest.click()
  await page.locator('.board-history-row').first().waitFor()
  result.boardRequest = true
  await page.screenshot({ path: '/tmp/opencode/e2e_board.png', fullPage: true })

  await page.goto('/app/game/loans')
  await page.getByRole('heading', { name: 'Cesiones y préstamos' }).waitFor()
  await page.getByText('CESIONES ENTRANTES', { exact: true }).waitFor()
  const loanButton = page.locator('[data-testid^="loan-in-"]').first()
  await loanButton.waitFor()
  await loanButton.click()
  await page.locator('.loan-history-row').first().waitFor()
  result.loans = true
  await page.screenshot({ path: '/tmp/opencode/e2e_loans.png', fullPage: true })

  await page.goto('/app/game/datahub')
  await page.getByRole('heading', { name: 'Data hub e instrucciones' }).waitFor()
  await page.getByText('JUGADORES CLAVE E INSTRUCCIONES', { exact: true }).waitFor()
  const instruction = page.locator('[data-testid^="instruction-"]').first()
  await instruction.selectOption('tight_marking')
  await page.getByTestId('datahub-save').click()
  await page.locator('.datahub-saved').waitFor()
  result.datahub = true
  await page.screenshot({ path: '/tmp/opencode/e2e_datahub.png', fullPage: true })

  await page.goto('/app/game/affiliates')
  await page.getByRole('heading', { name: 'Afiliados y mentoring' }).waitFor()
  await page.getByText('CANDIDATOS A AFILIACIÓN', { exact: true }).waitFor()
  const affiliateButton = page.locator('[data-testid^="affiliate-"]').first()
  await affiliateButton.waitFor()
  await affiliateButton.click()
  await page.locator('.affiliate-history-row').first().waitFor()
  result.affiliates = true
  await page.getByTestId('mentoring-assign').click()
  await page.locator('.mentoring-row').first().waitFor()
  result.mentoring = true
  await page.screenshot({ path: '/tmp/opencode/e2e_affiliates.png', fullPage: true })

  await page.goto('/app/game/history')
  await page.getByRole('heading', { name: 'Historial completo' }).waitFor()
  await page.getByRole('button', { name: 'Partidos' }).click()
  await page.locator('.data-table tbody tr').first().waitFor()
  await page.getByRole('button', { name: 'Jugadores' }).click()
  await page.locator('.data-table tbody tr').first().waitFor()
  await page.getByRole('button', { name: 'Récords' }).click()
  await page.getByText('MÁXIMO GOLEADOR', { exact: true }).waitFor()
  result.history = true
  await page.screenshot({ path: '/tmp/opencode/e2e_history.png', fullPage: true })

  await page.goto('/app/game/scouting')
  await page.getByRole('heading', { name: 'Ojeo y asignaciones' }).waitFor()
  await page.getByTestId('scout-assignment-create').click()
  await page.locator('.scout-assignment-row').first().waitFor()
  result.scouting = true
  await page.screenshot({ path: '/tmp/opencode/e2e_scouting.png', fullPage: true })

  await page.goto('/app/game/team-meeting')
  await page.getByRole('heading', { name: 'Reunión de equipo' }).waitFor()
  await page.getByTestId('team-meeting-submit').click()
  await page.locator('.team-meeting-result').waitFor()
  result.teamMeeting = true
  await page.screenshot({ path: '/tmp/opencode/e2e_team_meeting.png', fullPage: true })

  await page.goto('/app/game/finance')
  await page.getByRole('heading', { name: 'Centro financiero' }).waitFor()
  await page.getByTestId('finance-ticket-input').fill('22')
  await page.getByTestId('finance-ticket-save').click()
  await page.locator('.finance-saved').waitFor()
  result.finance = true
  await page.screenshot({ path: '/tmp/opencode/e2e_finance.png', fullPage: true })

  await page.goto('/app/game/responsibilities')
  await page.getByRole('heading', { name: 'Responsabilidades del staff' }).waitFor()
  await page.getByTestId('responsibility-select-attack').selectOption({ index: 1 })
  await page.getByTestId('responsibility-save-attack').click()
  await page.locator('.responsibility-saved').waitFor()
  result.responsibilities = true
  await page.screenshot({ path: '/tmp/opencode/e2e_responsibilities.png', fullPage: true })

  await page.goto('/app/game/development')
  await page.getByRole('heading', { name: 'Desarrollo de jugadores' }).waitFor()
  await page.locator('[data-testid^="development-save-"]').first().click()
  await page.locator('.development-saved').waitFor()
  result.development = true
  await page.screenshot({ path: '/tmp/opencode/e2e_development.png', fullPage: true })

  await page.goto('/app/game/awards')
  await page.getByRole('heading', { name: 'Premios y galardones' }).waitFor()
  await page.locator('.awards-grid').waitFor()
  await page.locator('.award-xi-row').first().waitFor()
  result.awards = true
  await page.screenshot({ path: '/tmp/opencode/e2e_awards.png', fullPage: true })

  await page.goto('/app/game/contracts')
  await page.getByRole('heading', { name: 'Centro de contratos' }).waitFor()
  await page.locator('.data-table tbody tr').first().waitFor()
  result.contracts = true
  await page.screenshot({ path: '/tmp/opencode/e2e_contracts.png', fullPage: true })

  await page.goto('/app/game/facilities')
  await page.getByRole('heading', { name: 'Instalaciones del club' }).waitFor()
  await page.locator('[data-testid^="facility-upgrade-"]:not([disabled])').first().click()
  await page.locator('.facility-saved').waitFor()
  result.facilities = true
  await page.screenshot({ path: '/tmp/opencode/e2e_facilities.png', fullPage: true })

  await page.goto('/app/game/clauses')
  await page.getByRole('heading', { name: 'Cláusulas y primas' }).waitFor()
  await page.locator('[data-testid^="clause-save-"]').first().click()
  await page.locator('.clause-saved').waitFor()
  result.clauses = true
  await page.screenshot({ path: '/tmp/opencode/e2e_clauses.png', fullPage: true })

  await page.goto('/app/game/shortlist')
  await page.getByRole('heading', { name: 'Lista de seguimiento' }).waitFor()
  const shortlistAdd = page.locator('[data-testid^="shortlist-add-"]').first()
  await shortlistAdd.waitFor()
  await shortlistAdd.click()
  const shortlistRow = page.locator('.shortlist-row').first()
  await shortlistRow.waitFor()
  await shortlistRow.locator('[data-testid^="shortlist-priority-"]').selectOption('alta')
  await shortlistRow.locator('[data-testid^="shortlist-save-"]').click()
  await shortlistRow.locator('.badge-ok').filter({ hasText: 'Prioridad alta' }).waitFor()
  result.shortlist = true
  await page.screenshot({ path: '/tmp/opencode/e2e_shortlist.png', fullPage: true })

  await page.goto('/app/game/match-plans')
  await page.getByRole('heading', { name: 'Planes de partido' }).waitFor()
  await page.getByTestId('match-plan-name').fill('Cerrar el partido')
  await page.getByTestId('match-plan-create').click()
  const matchPlanCard = page.locator('.match-plan-card').first()
  await matchPlanCard.waitFor()
  await matchPlanCard.locator('[data-testid^="match-plan-toggle-"]').click()
  await page.locator('.match-plan-status').filter({ hasText: 'Desactivado' }).waitFor()
  result.matchPlans = true
  await page.screenshot({ path: '/tmp/opencode/e2e_match_plans.png', fullPage: true })

  await page.goto('/app/game/manager')
  await page.getByRole('heading', { name: 'Perfil del mánager' }).waitFor()
  await page.locator('.manager-record').waitFor()
  await page.locator('.manager-milestones').waitFor()
  result.managerProfile = true
  await page.screenshot({ path: '/tmp/opencode/e2e_manager_profile.png', fullPage: true })

  await page.goto('/app/game/commercial')
  await page.getByText('CONTRATOS INDIVIDUALES DE IMAGEN').waitFor()
  result.playerBrands = true

  await page.screenshot({ path: '/tmp/opencode/e2e_beta.png', fullPage: true })
  console.log(JSON.stringify(result))
} finally {
  await browser.close()
}
