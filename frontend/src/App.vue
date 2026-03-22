<template>
  <div class="app">
    <header class="app-header">
      <div class="header-content">
        <h1>🛒 商品购买咨询助手</h1>
        <p>我可以帮您挑选床垫、智能马桶、花洒、智能门锁、灯具等家居产品</p>
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
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #f0f2f5;
  color: #333;
}

.app {
  height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px;
  text-align: center;
  flex-shrink: 0;
}

.header-content h1 {
  font-size: 24px;
  margin-bottom: 6px;
}

.header-content p {
  font-size: 14px;
  opacity: 0.85;
}
</style>
