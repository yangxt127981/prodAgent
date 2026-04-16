<template>
  <div class="app">
    <header class="app-header">
      <div class="header-content">
        <h1>🛒 商品购买咨询助手</h1>
        <p>床垫 · 马桶 · 花洒 · 门锁 · 灯具</p>
      </div>
    </header>
    <ChatWindow />
  </div>
</template>

<script setup>
import ChatWindow from './components/ChatWindow.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  -webkit-tap-highlight-color: transparent;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f0f2f5;
  color: #333;
  overscroll-behavior: none;
}

.app {
  height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 12px 16px;
  padding-top: calc(12px + env(safe-area-inset-top));
  text-align: center;
  flex-shrink: 0;
}

.header-content h1 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 2px;
}

.header-content p {
  font-size: 12px;
  opacity: 0.8;
}

@media (min-width: 600px) {
  .app-header {
    padding: 16px 20px;
  }
  .header-content h1 {
    font-size: 22px;
    margin-bottom: 4px;
  }
  .header-content p {
    font-size: 13px;
  }
}
</style>
