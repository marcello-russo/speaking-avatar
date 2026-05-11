<script lang="ts">
  export let model: 'default' | 'alternative' = 'default';
</script>

<div class="classroom-bg"></div>

<style>
  .classroom-bg {
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, #e8ebf3 0%, #d5d9e8 100%);
    z-index: 0;
  }
</style>
