<script lang="ts">
  export let mode: string = 'widget';
  export let minimized: boolean = false;

  let container: HTMLDivElement;
  let dragStartX = 0, dragStartY = 0, dragOrigX = 0, dragOrigY = 0;
  let posX = 16, posY = 16;
  let w = 280, h = 360;
  let dragging = false, resizing = false;

  function onDragStart(e: MouseEvent) {
    if (minimized) return;
    dragging = true;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    dragOrigX = posX;
    dragOrigY = posY;
    e.preventDefault();
  }

  function onResizeStart(e: MouseEvent) {
    if (minimized) return;
    resizing = true;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    dragOrigX = w;
    dragOrigY = h;
    e.preventDefault();
    e.stopPropagation();
  }

  function onMouseMove(e: MouseEvent) {
    if (dragging) {
      posX = Math.max(0, dragOrigX + (e.clientX - dragStartX));
      posY = Math.max(0, dragOrigY + (e.clientY - dragStartY));
    }
    if (resizing) {
      w = Math.max(160, dragOrigX + (e.clientX - dragStartX));
      h = Math.max(200, dragOrigY + (e.clientY - dragStartY));
    }
  }

  function onMouseUp() {
    dragging = false;
    resizing = false;
  }

  function toggleMinimize() {
    minimized = !minimized;
  }

  function expandFromBubble(e: MouseEvent) {
    if (minimized) {
      minimized = false;
      e.stopPropagation();
    }
  }
</script>

<svelte:window on:mousemove={onMouseMove} on:mouseup={onMouseUp} />

<div
  class="aw-root"
  class:aw-minimized={minimized}
  bind:this={container}
  on:click={expandFromBubble}
  style="left: {posX}px; top: {posY}px; width: {minimized ? 56 : w}px; height: {minimized ? 56 : h}px;"
>
  <div
    class="aw-titlebar"
    on:mousedown={onDragStart}
    class:aw-dragging={dragging}
  >
    <span class="aw-title">Tutor</span>
    <button class="aw-btn" on:click={toggleMinimize} on:mousedown={(e) => e.stopPropagation()}>
      {minimized ? '+' : '−'}
    </button>
  </div>

  {#if !minimized}
    <div class="aw-content">
      <slot />
    </div>
    <div class="aw-resize-handle" on:mousedown={onResizeStart} />
  {/if}
</div>

<style>
  .aw-root {
    position: fixed;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    background: transparent;
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
    transition: width 0.15s, height 0.15s;
    user-select: none;
  }
  .aw-root.aw-minimized {
    border-radius: 50%;
    box-shadow: 0 2px 12px rgba(0,0,0,0.2);
    cursor: pointer;
  }
  .aw-titlebar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 10px;
    background: #2a2a3e;
    color: #fff;
    font-size: 13px;
    cursor: grab;
    flex-shrink: 0;
    border-radius: 12px 12px 0 0;
    z-index: 1;
  }
  .aw-titlebar.aw-dragging {
    cursor: grabbing;
  }
  .aw-title {
    opacity: 0.8;
  }
  .aw-btn {
    background: none;
    border: none;
    color: #fff;
    font-size: 18px;
    cursor: pointer;
    padding: 0 4px;
    line-height: 1;
    opacity: 0.7;
  }
  .aw-btn:hover {
    opacity: 1;
  }
  .aw-content {
    flex: 1;
    position: relative;
    overflow: hidden;
  }
  .aw-resize-handle {
    position: absolute;
    right: 0;
    bottom: 0;
    width: 16px;
    height: 16px;
    cursor: nwse-resize;
    z-index: 2;
  }
  .aw-resize-handle::after {
    content: '';
    position: absolute;
    right: 3px;
    bottom: 3px;
    width: 10px;
    height: 10px;
    border-right: 2px solid rgba(255,255,255,0.4);
    border-bottom: 2px solid rgba(255,255,255,0.4);
  }
</style>
