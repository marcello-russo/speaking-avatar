<script lang="ts">
  export let size: string = '1.5rem';
</script>

<div class="spinner" style="width: {size}; height: {size};"></div>

<style>
  .spinner {
    border: 2px solid rgba(99, 102, 241, 0.2);
    border-top-color: #6366f1;
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>
