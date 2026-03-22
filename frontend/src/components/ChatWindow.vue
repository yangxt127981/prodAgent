<template>
  <div class="chat-container">
    <!-- 快捷品类选择 -->
    <div v-if="messages.length === 0" class="quick-start">
      <p class="quick-title">您想了解哪类产品？点击快速开始 👇</p>
      <div class="category-chips">
        <button
          v-for="cat in categories"
          :key="cat"
          class="chip"
          @click="sendQuickMessage('我想买' + cat)"
        >
          {{ cat }}
        </button>
      </div>
    </div>

    <!-- 消息列表 -->
    <div class="messages" ref="messagesRef">
      <div
        v-for="(msg, index) in messages"
        :key="index"
        :class="['message', msg.role]"
      >
        <div class="avatar">{{ msg.role === 'user' ? '🧑' : '🤖' }}</div>
        <div class="bubble" v-html="renderMarkdown(msg.content)"></div>
      </div>
      <div v-if="loading" class="message assistant">
        <div class="avatar">🤖</div>
        <div class="bubble typing">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <button class="reset-btn" @click="resetChat" title="重新开始">🔄</button>
      <input
        v-model="inputText"
        @keyup.enter="sendMessage"
        placeholder="请输入您的问题，例如：我想买一个床垫"
        :disabled="loading"
      />
      <button class="send-btn" @click="sendMessage" :disabled="loading || !inputText.trim()">
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'

const API_BASE = 'http://localhost:8000'

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const sessionId = ref(null)
const messagesRef = ref(null)
const categories = ref([])

onMounted(async () => {
  try {
    const res = await fetch(`${API_BASE}/api/categories`)
    const data = await res.json()
    categories.value = data.categories
  } catch {
    categories.value = ['床垫', '智能马桶', '花洒套装', '智能门锁', '吸顶灯', '台灯', '落地护眼灯']
  }
})

function renderMarkdown(text) {
  return marked.parse(text, { breaks: true })
}

async function scrollToBottom() {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

function sendQuickMessage(text) {
  inputText.value = text
  sendMessage()
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId.value,
        message: text,
      }),
    })

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}`)
    }

    const data = await res.json()
    sessionId.value = data.session_id
    messages.value.push({ role: 'assistant', content: data.reply })
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: `抱歉，出现了一些问题：${err.message}。请检查后端服务是否已启动。`,
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

async function resetChat() {
  if (sessionId.value) {
    try {
      await fetch(`${API_BASE}/api/reset`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId.value }),
      })
    } catch { /* ignore */ }
  }
  messages.value = []
  sessionId.value = null
}
</script>

<style scoped>
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 800px;
  margin: 0 auto;
  width: 100%;
  overflow: hidden;
}

.quick-start {
  padding: 40px 20px 20px;
  text-align: center;
}

.quick-title {
  font-size: 16px;
  color: #666;
  margin-bottom: 16px;
}

.category-chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.chip {
  padding: 10px 20px;
  border: 2px solid #667eea;
  border-radius: 20px;
  background: white;
  color: #667eea;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.2s;
}

.chip:hover {
  background: #667eea;
  color: white;
}

.messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.message {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
  align-items: flex-start;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  background: #e8eaf6;
}

.bubble {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 16px;
  line-height: 1.6;
  font-size: 15px;
  word-break: break-word;
}

.message.user .bubble {
  background: #667eea;
  color: white;
  border-bottom-right-radius: 4px;
}

.message.assistant .bubble {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
}

.bubble :deep(p) {
  margin: 0 0 8px;
}

.bubble :deep(p:last-child) {
  margin-bottom: 0;
}

.bubble :deep(strong) {
  color: #4a5aba;
}

.message.user .bubble :deep(strong) {
  color: #fff;
}

.bubble :deep(ul), .bubble :deep(ol) {
  margin: 4px 0;
  padding-left: 20px;
}

.bubble :deep(li) {
  margin-bottom: 4px;
}

/* 打字动画 */
.typing {
  display: flex;
  gap: 4px;
  padding: 16px 20px;
}

.typing span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #667eea;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing span:nth-child(1) { animation-delay: -0.32s; }
.typing span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 输入区域 */
.input-area {
  padding: 16px 20px;
  display: flex;
  gap: 10px;
  background: white;
  border-top: 1px solid #e8e8e8;
  flex-shrink: 0;
}

.input-area input {
  flex: 1;
  padding: 12px 16px;
  border: 2px solid #e0e0e0;
  border-radius: 24px;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
}

.input-area input:focus {
  border-color: #667eea;
}

.send-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 24px;
  font-size: 15px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.send-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.reset-btn {
  width: 44px;
  height: 44px;
  border: 2px solid #e0e0e0;
  border-radius: 50%;
  background: white;
  font-size: 18px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.reset-btn:hover {
  border-color: #667eea;
  background: #f0f2ff;
}
</style>
