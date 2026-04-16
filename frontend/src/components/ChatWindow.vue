<template>
  <div class="chat-container">
    <!-- 快捷品类选择 -->
    <div v-if="messages.length === 0" class="quick-start">
      <div class="quick-banner">
        <div class="quick-icon">🛋️</div>
        <p class="quick-title">您想咨询哪类产品？</p>
        <p class="quick-sub">点击下方品类快速开始</p>
      </div>
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
      <!-- 流式输出中的消息 -->
      <div v-if="streamingContent !== null" class="message assistant">
        <div class="avatar">🤖</div>
        <div class="bubble" v-html="renderMarkdown(streamingContent || ' ')"></div>
      </div>
      <!-- 等待第一个 token（纯 loading 点） -->
      <div v-else-if="loading" class="message assistant">
        <div class="avatar">🤖</div>
        <div class="bubble typing"><span></span><span></span><span></span></div>
      </div>
      <!-- 查询排期提示 -->
      <div v-if="toolHint" class="tool-hint">{{ toolHint }}</div>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <button class="reset-btn" @click="resetChat" title="重新开始">🔄</button>
      <textarea
        v-model="inputText"
        @keyup.enter.exact="handleEnter"
        placeholder="请输入问题…"
        :disabled="loading"
        rows="1"
        ref="textareaRef"
        @input="autoResize"
      ></textarea>
      <button class="send-btn" @click="sendMessage" :disabled="loading || !inputText.trim()">
        <svg v-if="!loading" width="20" height="20" viewBox="0 0 24 24" fill="none">
          <path d="M22 2L11 13" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <path d="M22 2L15 22L11 13L2 9L22 2Z" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span v-else class="send-loading"></span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue'
import { marked } from 'marked'

const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000`

const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const streamingContent = ref(null)   // null = 不在流式中，string = 流式累积内容
const toolHint = ref('')
const sessionId = ref(null)
const messagesRef = ref(null)
const textareaRef = ref(null)
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

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 100) + 'px'
}

function handleEnter() {
  if (window.innerWidth >= 600) sendMessage()
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
  streamingContent.value = null
  toolHint.value = ''

  await nextTick()
  if (textareaRef.value) textareaRef.value.style.height = 'auto'
  scrollToBottom()

  try {
    const res = await fetch(`${API_BASE}/api/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId.value, message: text }),
    })
    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() // 保留不完整的行

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6).trim()
        if (!raw) continue

        let event
        try { event = JSON.parse(raw) } catch { continue }

        if (event.type === 'session') {
          sessionId.value = event.session_id

        } else if (event.type === 'token') {
          if (streamingContent.value === null) streamingContent.value = ''
          streamingContent.value += event.content
          toolHint.value = ''
          scrollToBottom()

        } else if (event.type === 'tool_start') {
          toolHint.value = '⏳ ' + event.message
          scrollToBottom()

        } else if (event.type === 'done') {
          // 把流式内容转为正式消息
          if (streamingContent.value !== null) {
            messages.value.push({ role: 'assistant', content: streamingContent.value })
          }
          streamingContent.value = null
          toolHint.value = ''

        } else if (event.type === 'error') {
          messages.value.push({ role: 'assistant', content: `抱歉，出现错误：${event.message}` })
          streamingContent.value = null
          toolHint.value = ''
        }
      }
    }
  } catch (err) {
    streamingContent.value = null
    toolHint.value = ''
    messages.value.push({
      role: 'assistant',
      content: `抱歉，出现了一些问题：${err.message}`,
    })
  } finally {
    loading.value = false
    streamingContent.value = null
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
  loading.value = false
  streamingContent.value = null
  toolHint.value = ''
}
</script>

<style scoped>
/* ── 容器 ── */
.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
  background: #f5f5f5;
}

/* ── 快捷开始 ── */
.quick-start {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 20px;
  gap: 24px;
}

.quick-banner {
  text-align: center;
}

.quick-icon {
  font-size: 52px;
  margin-bottom: 12px;
}

.quick-title {
  font-size: 18px;
  font-weight: 600;
  color: #222;
  margin-bottom: 4px;
}

.quick-sub {
  font-size: 13px;
  color: #999;
}

.category-chips {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  width: 100%;
}

.chip {
  padding: 12px 6px;
  border: 1.5px solid #667eea;
  border-radius: 12px;
  background: white;
  color: #667eea;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  min-height: 48px;
  transition: all 0.15s;
  font-family: inherit;
}

.chip:active {
  background: #667eea;
  color: white;
  transform: scale(0.97);
}

/* ── 消息列表 ── */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px 12px 8px;
  -webkit-overflow-scrolling: touch;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.message {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}

.message.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
  background: #e8eaf6;
  margin-bottom: 2px;
}

.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 18px;
  line-height: 1.65;
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
  color: #222;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}

.bubble :deep(p) { margin: 0 0 8px; }
.bubble :deep(p:last-child) { margin-bottom: 0; }
.bubble :deep(strong) { color: #4a5aba; }
.message.user .bubble :deep(strong) { color: #fff; }
.bubble :deep(ul), .bubble :deep(ol) { margin: 6px 0; padding-left: 18px; }
.bubble :deep(li) { margin-bottom: 4px; }
.bubble :deep(hr) { border: none; border-top: 1px solid #f0f0f0; margin: 10px 0; }

/* 打字动画 */
.typing {
  display: flex;
  gap: 5px;
  padding: 14px 18px;
  align-items: center;
}
.typing span {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #667eea;
  animation: bounce 1.4s infinite ease-in-out both;
}
.typing span:nth-child(1) { animation-delay: -0.32s; }
.typing span:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.3); }
  40% { transform: scale(1); }
}

/* ── 输入区域 ── */
.input-area {
  padding: 10px 12px;
  padding-bottom: calc(10px + env(safe-area-inset-bottom));
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: white;
  border-top: 1px solid #ebebeb;
  flex-shrink: 0;
}

.input-area textarea {
  flex: 1;
  padding: 10px 14px;
  border: 1.5px solid #e0e0e0;
  border-radius: 20px;
  font-size: 16px;
  font-family: inherit;
  outline: none;
  resize: none;
  overflow: hidden;
  line-height: 1.5;
  min-height: 44px;
  max-height: 100px;
  background: #f8f8f8;
  transition: border-color 0.2s, background 0.2s;
  color: #222;
}

.input-area textarea:focus {
  border-color: #667eea;
  background: white;
}

.send-btn {
  width: 44px;
  height: 44px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: opacity 0.2s, transform 0.1s;
}

.send-btn:active {
  transform: scale(0.93);
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.send-loading {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.reset-btn {
  width: 44px;
  height: 44px;
  border: 1.5px solid #e0e0e0;
  border-radius: 50%;
  background: white;
  font-size: 18px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;
}

.reset-btn:active {
  background: #f0f2ff;
  border-color: #667eea;
}

/* 工具调用提示 */
.tool-hint {
  text-align: center;
  font-size: 12px;
  color: #999;
  padding: 4px 0 8px;
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to   { opacity: 1; transform: translateY(0); }
}

/* 桌面端 hover */
@media (hover: hover) {
  .chip:hover { background: #667eea; color: white; }
  .reset-btn:hover { background: #f0f2ff; border-color: #667eea; }
}

/* 桌面端宽屏微调 */
@media (min-width: 600px) {
  .chat-container { background: #f0f2f5; }
  .bubble { font-size: 15px; }
  .input-area { padding: 12px 16px; }
}
</style>
