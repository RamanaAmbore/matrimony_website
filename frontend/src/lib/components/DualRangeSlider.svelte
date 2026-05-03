<script lang="ts">
  let {
    min = 18,
    max = 60,
    valueMin = $bindable(18),
    valueMax = $bindable(60),
  }: {
    min?: number;
    max?: number;
    valueMin?: number;
    valueMax?: number;
  } = $props();

  function clamp(v: number, lo: number, hi: number) {
    return Math.min(hi, Math.max(lo, v));
  }

  function onMinInput(e: Event) {
    const v = Number((e.currentTarget as HTMLInputElement).value);
    valueMin = clamp(v, min, valueMax - 1);
  }

  function onMaxInput(e: Event) {
    const v = Number((e.currentTarget as HTMLInputElement).value);
    valueMax = clamp(v, valueMin + 1, max);
  }

  // Compute track fill percentages
  const pctMin = $derived(((valueMin - min) / (max - min)) * 100);
  const pctMax = $derived(((valueMax - min) / (max - min)) * 100);
</script>

<div class="dual-range-wrapper">
  <!-- Filled track between the two thumbs -->
  <div
    class="dual-range-track"
    style="left: {pctMin}%; right: {100 - pctMax}%;"
  ></div>
  <input
    type="range"
    {min}
    {max}
    step="1"
    value={valueMin}
    oninput={onMinInput}
    class="dual-range-input"
    aria-label="Minimum age"
  />
  <input
    type="range"
    {min}
    {max}
    step="1"
    value={valueMax}
    oninput={onMaxInput}
    class="dual-range-input"
    aria-label="Maximum age"
  />
</div>

<style>
  .dual-range-wrapper {
    position: relative;
    height: 28px;
    display: flex;
    align-items: center;
  }

  /* Grey base track */
  .dual-range-wrapper::before {
    content: '';
    position: absolute;
    left: 0; right: 0;
    top: 50%; transform: translateY(-50%);
    height: 4px;
    background: #e5d5b0;
    border-radius: 2px;
    pointer-events: none;
  }

  /* Gold filled portion between thumbs */
  .dual-range-track {
    position: absolute;
    top: 50%; transform: translateY(-50%);
    height: 4px;
    background: #c9a227;
    border-radius: 2px;
    pointer-events: none;
    z-index: 1;
  }

  .dual-range-input {
    position: absolute;
    width: 100%;
    -webkit-appearance: none;
    appearance: none;
    background: transparent;
    pointer-events: none;
    z-index: 2;
    height: 28px;
  }

  /* Thumb styles — cross-browser */
  .dual-range-input::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px; height: 18px;
    border-radius: 50%;
    background: #6b0f1a;
    border: 2px solid #c9a227;
    cursor: pointer;
    pointer-events: all;
    position: relative; z-index: 3;
    box-shadow: 0 1px 3px rgba(0,0,0,0.25);
  }

  .dual-range-input::-moz-range-thumb {
    width: 18px; height: 18px;
    border-radius: 50%;
    background: #6b0f1a;
    border: 2px solid #c9a227;
    cursor: pointer;
    pointer-events: all;
    box-shadow: 0 1px 3px rgba(0,0,0,0.25);
  }

  .dual-range-input:focus::-webkit-slider-thumb {
    outline: 2px solid #f4a300;
    outline-offset: 2px;
  }
  .dual-range-input:focus::-moz-range-thumb {
    outline: 2px solid #f4a300;
  }
  .dual-range-input:focus-visible {
    outline: none;
  }
</style>
