/**
 * Web Audio API integration for live preview.
 * Extracts RMS and 5-band frequency data from the mix audio.
 */

export class AudioAnalyzer {
  private ctx: AudioContext | null = null;
  private analyser: AnalyserNode | null = null;
  private source: MediaElementAudioSourceNode | null = null;
  private audioElement: HTMLAudioElement | null = null;
  private fftData: Uint8Array<ArrayBuffer> = new Uint8Array(0);
  private timeDomainData: Uint8Array<ArrayBuffer> = new Uint8Array(0);

  // Band frequency bin boundaries (for 44100 Hz, fftSize=2048 → 1024 bins, ~21.5 Hz per bin)
  // low: 0-200Hz → bins 0-9
  // low_mid: 200-800Hz → bins 9-37
  // mid: 800-2500Hz → bins 37-116
  // high_mid: 2500-6000Hz → bins 116-279
  // high: 6000-20000Hz → bins 279-930
  private bandRanges = [
    { name: "low", lo: 0, hi: 9 },
    { name: "low_mid", lo: 9, hi: 37 },
    { name: "mid", lo: 37, hi: 116 },
    { name: "high_mid", lo: 116, hi: 279 },
    { name: "high", lo: 279, hi: 930 },
  ];

  async init(audioUrl: string): Promise<HTMLAudioElement> {
    this.ctx = new AudioContext();
    this.analyser = this.ctx.createAnalyser();
    this.analyser.fftSize = 2048;
    this.analyser.smoothingTimeConstant = 0.8;

    this.audioElement = new Audio();
    this.audioElement.crossOrigin = "anonymous";
    this.audioElement.src = audioUrl;
    this.audioElement.preload = "auto";

    this.source = this.ctx.createMediaElementSource(this.audioElement);
    this.source.connect(this.analyser);
    this.analyser.connect(this.ctx.destination);

    this.fftData = new Uint8Array(this.analyser.frequencyBinCount) as Uint8Array<ArrayBuffer>;
    this.timeDomainData = new Uint8Array(this.analyser.fftSize) as Uint8Array<ArrayBuffer>;

    return this.audioElement;
  }

  getRMS(): number {
    if (!this.analyser) return 0;
    this.analyser.getByteTimeDomainData(this.timeDomainData);

    let sum = 0;
    for (let i = 0; i < this.timeDomainData.length; i++) {
      const normalized = (this.timeDomainData[i] - 128) / 128;
      sum += normalized * normalized;
    }
    return Math.sqrt(sum / this.timeDomainData.length);
  }

  getBands(): { low: number; low_mid: number; mid: number; high_mid: number; high: number } {
    if (!this.analyser) {
      return { low: 0, low_mid: 0, mid: 0, high_mid: 0, high: 0 };
    }

    this.analyser.getByteFrequencyData(this.fftData);

    const bands: Record<string, number> = {} as any;
    for (const { name, lo, hi } of this.bandRanges) {
      let sum = 0;
      const count = Math.min(hi, this.fftData.length) - lo;
      for (let i = lo; i < Math.min(hi, this.fftData.length); i++) {
        sum += this.fftData[i];
      }
      bands[name] = count > 0 ? sum / count / 255 : 0;
    }

    return bands as { low: number; low_mid: number; mid: number; high_mid: number; high: number };
  }

  async play(): Promise<void> {
    if (this.ctx?.state === "suspended") {
      await this.ctx.resume();
    }
    await this.audioElement?.play();
  }

  pause(): void {
    this.audioElement?.pause();
  }

  get isPlaying(): boolean {
    return !!this.audioElement && !this.audioElement.paused;
  }

  get currentTime(): number {
    return this.audioElement?.currentTime || 0;
  }

  get duration(): number {
    return this.audioElement?.duration || 0;
  }

  destroy(): void {
    this.audioElement?.pause();
    this.source?.disconnect();
    this.analyser?.disconnect();
    this.ctx?.close();
    this.ctx = null;
    this.analyser = null;
    this.source = null;
    this.audioElement = null;
  }
}
