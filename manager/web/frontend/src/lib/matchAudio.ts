/**
 * Ambiente y efectos del partido generados con Web Audio.
 *
 * No usa samples externos: todo es ruido filtrado y osciladores, así que no
 * hay licencias de audio que revisar. El audio empieza apagado y solo se
 * activa con un gesto del usuario.
 */

export class MatchAudio {
  private ctx: AudioContext | null = null
  private master: GainNode | null = null
  private ambientSource: AudioBufferSourceNode | null = null
  private ambientGain: GainNode | null = null
  enabled = false

  async enable(): Promise<void> {
    if (!this.ctx) {
      const Ctor =
        window.AudioContext ||
        (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
      if (!Ctor) return
      this.ctx = new Ctor()
      this.master = this.ctx.createGain()
      this.master.gain.value = 0.5
      this.master.connect(this.ctx.destination)
    }
    await this.ctx.resume()
    this.enabled = true
    this.startAmbient()
  }

  disable(): void {
    this.enabled = false
    this.stopAmbient()
  }

  dispose(): void {
    this.disable()
    if (this.ctx) {
      void this.ctx.close()
      this.ctx = null
      this.master = null
    }
  }

  play(type: string): void {
    if (!this.enabled || !this.ctx || !this.master) return
    if (type === 'goal') {
      this.cheer()
      this.whistle()
      return
    }
    if (['card', 'foul', 'pc_decision', 'dangerous_play', 'protest', 'unsportsmanlike'].includes(type)) {
      this.whistle()
      return
    }
    if (['shot', 'pc', 'stroke', 'save', 'chance', 'circle_entry', 'free_hit'].includes(type)) {
      this.hit()
    }
  }

  private startAmbient(): void {
    if (!this.ctx || !this.master || this.ambientSource) return
    const seconds = 2
    const buffer = this.ctx.createBuffer(1, this.ctx.sampleRate * seconds, this.ctx.sampleRate)
    const data = buffer.getChannelData(0)
    let last = 0
    for (let index = 0; index < data.length; index += 1) {
      const white = Math.random() * 2 - 1
      last = (last + 0.02 * white) / 1.02
      data[index] = last * 3.2
    }
    const source = this.ctx.createBufferSource()
    source.buffer = buffer
    source.loop = true
    const filter = this.ctx.createBiquadFilter()
    filter.type = 'lowpass'
    filter.frequency.value = 850
    const gain = this.ctx.createGain()
    gain.gain.value = 0.03
    source.connect(filter)
    filter.connect(gain)
    gain.connect(this.master)
    source.start()
    this.ambientSource = source
    this.ambientGain = gain
  }

  private stopAmbient(): void {
    if (this.ambientSource) {
      try {
        this.ambientSource.stop()
      } catch {
        // El nodo ya podía estar parado.
      }
      this.ambientSource.disconnect()
      this.ambientSource = null
    }
    if (this.ambientGain) {
      this.ambientGain.disconnect()
      this.ambientGain = null
    }
  }

  private whistle(): void {
    if (!this.ctx || !this.master) return
    const ctx = this.ctx
    const now = ctx.currentTime
    for (const [start, duration] of [
      [0, 0.16],
      [0.22, 0.24],
    ]) {
      const oscillator = ctx.createOscillator()
      const gain = ctx.createGain()
      oscillator.type = 'sine'
      oscillator.frequency.setValueAtTime(1900, now + start)
      oscillator.frequency.linearRampToValueAtTime(2300, now + start + duration)
      gain.gain.setValueAtTime(0.0001, now + start)
      gain.gain.exponentialRampToValueAtTime(0.16, now + start + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + start + duration)
      oscillator.connect(gain)
      gain.connect(this.master)
      oscillator.start(now + start)
      oscillator.stop(now + start + duration + 0.02)
    }
  }

  private hit(): void {
    if (!this.ctx || !this.master) return
    const ctx = this.ctx
    const now = ctx.currentTime
    const buffer = ctx.createBuffer(1, Math.floor(ctx.sampleRate * 0.06), ctx.sampleRate)
    const data = buffer.getChannelData(0)
    for (let index = 0; index < data.length; index += 1) {
      data[index] = (Math.random() * 2 - 1) * (1 - index / data.length) ** 3
    }
    const source = ctx.createBufferSource()
    source.buffer = buffer
    const filter = ctx.createBiquadFilter()
    filter.type = 'bandpass'
    filter.frequency.value = 1300
    filter.Q.value = 0.9
    const gain = ctx.createGain()
    gain.gain.value = 0.14
    source.connect(filter)
    filter.connect(gain)
    gain.connect(this.master)
    source.start(now)
  }

  private cheer(): void {
    if (!this.ctx || !this.master) return
    const ctx = this.ctx
    const now = ctx.currentTime
    const duration = 1.2
    const buffer = ctx.createBuffer(1, Math.floor(ctx.sampleRate * duration), ctx.sampleRate)
    const data = buffer.getChannelData(0)
    for (let index = 0; index < data.length; index += 1) {
      const envelope = Math.sin((Math.PI * index) / data.length) ** 1.5
      data[index] = (Math.random() * 2 - 1) * envelope
    }
    const source = ctx.createBufferSource()
    source.buffer = buffer
    const filter = ctx.createBiquadFilter()
    filter.type = 'bandpass'
    filter.frequency.value = 750
    filter.Q.value = 0.7
    const gain = ctx.createGain()
    gain.gain.setValueAtTime(0.0001, now)
    gain.gain.exponentialRampToValueAtTime(0.18, now + 0.12)
    gain.gain.exponentialRampToValueAtTime(0.0001, now + duration)
    source.connect(filter)
    filter.connect(gain)
    gain.connect(this.master)
    source.start(now)
  }
}
