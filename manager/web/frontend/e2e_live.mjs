import { assert, createGame, run } from './e2e_helpers.mjs'

await run('live', async ({ context, page }) => {
  const result = {}
  await createGame(context, 'E2E Live', '202')

  const live = await context.request.post('/api/match/live/start', { data: { travel: 'equilibrado' } })
  assert(live.ok(), `live HTTP ${live.status()}: ${await live.text()}`)
  result.liveStart = true

  await page.goto('/app/game/live')
  await page.getByRole('heading', { name: 'Partido en directo' }).waitFor()
  const viewer = page.locator('[data-testid="match-viewer-3d"] canvas')
  await viewer.waitFor()
  const box = await viewer.boundingBox()
  assert(box && box.width >= 200 && box.height >= 150, `viewer size ${JSON.stringify(box)}`)
  await page.waitForTimeout(1800)
  await page.evaluate(() => window.__matchViewer3D.forceBallBodyContact())
  await page.waitForTimeout(250)
  const viewerState = await page.evaluate(() => window.__matchViewer3D)
  assert(viewerState && viewerState.players === 22, `viewer players ${JSON.stringify(viewerState)}`)
  assert(viewerState.frames >= 10, `viewer frames ${viewerState.frames}`)
  assert(viewerState.ballSpeed > 0, `viewer ball ${viewerState.ballSpeed}`)
  assert(viewerState.bodyCollisions > 0, `viewer body collisions ${viewerState.bodyCollisions}`)
  assert(viewerState.stickCollisions > 0, `viewer stick collisions ${viewerState.stickCollisions}`)
  assert(viewerState.sticks === 22, `viewer sticks ${viewerState.sticks}`)
  assert(viewerState.bones >= 22 * 17, `viewer bones ${viewerState.bones}`)
  assert(viewerState.ikSolutions > 100, `viewer ik ${viewerState.ikSolutions}`)
  assert(viewerState.biomechSolutions > 0, `viewer biomechanics ${viewerState.biomechSolutions}`)
  assert(viewerState.clothUpdates > 0, `viewer cloth ${viewerState.clothUpdates}`)
  assert(viewerState.mocapSource === 'CMU-09-01', `viewer mocap source ${viewerState.mocapSource}`)
  assert(viewerState.mocapFrames > 10, `viewer mocap frames ${viewerState.mocapFrames}`)
  assert(viewerState.mocapApplied > 0, `viewer mocap applied ${viewerState.mocapApplied}`)
  await page.evaluate(() => window.__matchViewer3D.forceContact())
  await page.waitForTimeout(400)
  const materialState = await page.evaluate(() => window.__matchViewer3D)
  assert(materialState.stickBodyCollisions > 0, `viewer stick-body ${JSON.stringify(materialState)}`)
  assert(materialState.materialBounces > 0, `viewer material bounces ${materialState.materialBounces}`)
  assert(materialState.stickFlexes > 0, `viewer stick flexes ${materialState.stickFlexes}`)
  result.viewer = {
    players: viewerState.players,
    frames: viewerState.frames,
    bones: viewerState.bones,
    sticks: viewerState.sticks,
    ikSolutions: viewerState.ikSolutions,
    biomechSolutions: viewerState.biomechSolutions,
    mocapFrames: viewerState.mocapFrames,
  }
  result.viewer3d = true

  await page.getByTestId('live-protest-respectful').click()
  await page.locator('.protest-used').waitFor()
  result.liveProtest = true

  let liveData = (await (await context.request.get('/api/match/live')).json()).data
  for (let attempt = 0; attempt < 64; attempt += 1) {
    if (liveData.snapshot?.finished) break
    const advanced = await context.request.post('/api/match/live/advance', { data: { mode: 'moment' } })
    assert(advanced.ok(), `live advance HTTP ${advanced.status()}: ${await advanced.text()}`)
    liveData = (await advanced.json()).data
  }
  result.momentsAdvanced = true
  result.finished = Boolean(liveData.snapshot?.finished)

  await page.reload()
  await page.getByRole('heading', { name: 'Partido en directo' }).waitFor()
  await page.screenshot({ path: '/tmp/opencode/e2e_live_smoke.png', fullPage: true })

  return result
})
