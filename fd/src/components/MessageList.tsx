import { useEffect, useRef } from 'react'
import { useChatStore } from '../stores/chatStore'
import { useConversationStore } from '../stores/conversationStore'
import { useAuthStore } from '../stores/authStore'
import { getMessages } from '../services/chat'
import { marked } from 'marked'
import DOMPurify from 'dompurify'

export default function MessageList() {
  const { messages, currentAssistantMessage, hasError, setHasError } = useChatStore()
  const { currentConversationId, isNewConversation } = useConversationStore()
  const { isAuthenticated } = useAuthStore()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const previousConversationId = useRef<number | null>(null)

  useEffect(() => {
    // 检测对话是否切换
    const conversationChanged = currentConversationId !== previousConversationId.current

    // 从 null 变为某个 ID 也算作变化
    const fromNullToValue = previousConversationId.current === null && currentConversationId !== null

    // 消息为空说明还没加载过
    const needsLoading = messages.length === 0

    // 在以下情况加载消息：
    // 1. 有选中的对话ID
    // 2. 不是新对话状态
    // 3. 用户已登录
    // 4. 对话ID发生变化，或者消息为空（还没加载过）
    if (currentConversationId && !isNewConversation && isAuthenticated &&
        (conversationChanged || fromNullToValue || needsLoading)) {
      loadMessages()
      previousConversationId.current = currentConversationId
    }
  }, [currentConversationId, isNewConversation, isAuthenticated, messages.length])

  useEffect(() => {
    scrollToBottom()
  }, [messages, currentAssistantMessage])

  const loadMessages = async () => {
    try {
      const data = await getMessages(currentConversationId!)
      useChatStore.getState().setMessages(data)
      // 延迟滚动，确保图片和其他资源已加载
      setTimeout(() => {
        scrollToBottom()
      }, 100)
    } catch (err) {
      console.error('Failed to load messages:', err)
    }
  }

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  const renderContent = (content: string | Record<string, unknown>[]) => {
    if (Array.isArray(content)) {
      return content.map((item, index) => {
        const itemType = item.type as string
        if (itemType === 'text') {
          const text = item.text as string || ''
          const html = marked.parse(text) as string
          return (
            <div
              key={index}
              className="markdown-content"
              dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }}
            />
          )
        } else if (itemType === 'image_url') {
          // image_url 可能是字符串或对象
          const imageUrl = typeof item.image_url === 'string'
            ? item.image_url
            : (item.image_url as { url: string }).url
          return (
            <img
              key={index}
              src={imageUrl}
              alt="Uploaded image"
              className="max-w-full max-h-48 h-auto rounded"
              onError={(e) => {
                // 图片加载失败，显示占位符
                e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="192" height="192"%3E%3Crect width="192" height="192" fill="%23e5e5e5"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23999"%3EImage%3C/text%3E%3C/svg%3E'
              }}
            />
          )
        }
        return null
      })
    } else {
      const html = marked.parse(content || '') as string
      return (
        <div
          className="markdown-content"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }}
        />
      )
    }
  }

  const renderImages = (content: string | Record<string, unknown>[]) => {
    if (!Array.isArray(content)) return null
    return content.map((item, index) => {
      if (item.type === 'image_url') {
        const imageUrl = typeof item.image_url === 'string'
          ? item.image_url
          : (item.image_url as { url: string }).url
        return (
          <img
            key={index}
            src={imageUrl}
            alt="Uploaded image"
            className="max-w-full max-h-48 h-auto rounded mb-2"
            onError={(e) => {
              // 图片加载失败，显示占位符
              e.currentTarget.src = 'data:image/svg+xml,%3Csvg xmlns="http://www.w3.org/2000/svg" width="192" height="192"%3E%3Crect width="192" height="192" fill="%23e5e5e5"/%3E%3Ctext x="50%25" y="50%25" dominant-baseline="middle" text-anchor="middle" fill="%23999"%3EImage%3C/text%3E%3C/svg%3E'
            }}
          />
        )
      }
      return null
    })
  }

  const renderText = (content: string | Record<string, unknown>[]) => {
    if (!Array.isArray(content)) {
      const html = marked.parse(content || '') as string
      return (
        <div
          className="markdown-content"
          dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }}
        />
      )
    }
    return content.map((item, index) => {
      if (item.type === 'text') {
        const text = item.text as string || ''
        const html = marked.parse(text) as string
        return (
          <div
            key={index}
            className="markdown-content"
            dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(html) }}
          />
        )
      }
      return null
    })
  }

  return (
    <div
      ref={messagesContainerRef}
      className="flex-1 overflow-y-auto p-6 space-y-6 relative"
    >
      {!currentConversationId && !isNewConversation && messages.length === 0 && !currentAssistantMessage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2">Chat</h2>
            <p className="opacity-60">Select a conversation or start a new one</p>
          </div>
        </div>
      )}

      {isNewConversation && messages.length === 0 && !currentAssistantMessage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-2">New Chat</h2>
            <p className="opacity-60">Send a message to start</p>
          </div>
        </div>
      )}

      {messages.map((message, index) => {
        const hasImage = Array.isArray(message.content) && message.content.some(item => item.type === 'image_url')
        return (
          <div
            key={index}
            className={`flex flex-col ${message.role === 'user' ? 'items-end' : 'items-start'} mb-4`}
          >
            {hasImage && (
              <div className="mb-2">
                {renderImages(message.content)}
              </div>
            )}
            <div
              className={`max-w-[80%] p-2 m-0 inline-block message-content ${
                message.role === 'user'
                  ? 'bg-mono-800 rounded-lg'
                  : ''
              }`}
              style={{ lineHeight: '1.2', margin: '0', color: message.role === 'user' ? 'var(--color-bg)' : undefined }}
            >
              {renderText(message.content)}
            </div>
          </div>
        )
      })}

      {currentAssistantMessage && (
        <div className="flex flex-col items-start">
          <div
            className="max-w-[80%] p-2 m-0 inline-block message-content whitespace-pre-wrap"
            style={{ lineHeight: '1.2', margin: '0' }}
          >
            {currentAssistantMessage}
          </div>
          {hasError && (
            <div className="flex items-center gap-2 mt-1">
              <button
                onClick={() => {
                  setHasError(false)
                  window.dispatchEvent(new CustomEvent('retryMessage'))
                }}
                className="text-xs py-0.5 px-2 border-0 hover:bg-[var(--color-text)] hover:text-[var(--color-bg)] transition-colors"
              >
                重试
              </button>
            </div>
          )}
        </div>
      )}

      <div ref={messagesEndRef} />
    </div>
  )
}