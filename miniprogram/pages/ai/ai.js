// pages/ai/ai.js
const app = getApp();

Page({
  data: {
    messages: [],
    inputText: '',
    loading: false,
    suggestions: [],
    canSend: false  // 是否可以发送
  },

  onLoad() {
    this.loadSuggestions();
    
    // 添加欢迎消息
    this.setData({
      messages: [{
        role: 'assistant',
        content: '您好！我是燕儿，燕斛堂的智能养发顾问，很高兴为您服务。您可以问我关于养发、护发的任何问题。'
      }]
    });
  },

  // 加载推荐问题
  async loadSuggestions() {
    try {
      const res = await app.request({ url: '/ai/suggestions' });
      this.setData({ suggestions: res.suggestions });
    } catch (err) {
      console.error('加载推荐问题失败:', err);
    }
  },

  // 输入文字
  onInput(e) {
    const value = e.detail.value;
    this.setData({
      inputText: value,
      canSend: value.trim().length > 0 && !this.data.loading
    });
  },

  // 点击推荐问题
  selectSuggestion(e) {
    const text = e.currentTarget.dataset.text;
    this.setData({ inputText: text, canSend: true });
    this.sendMessage();
  },

  // 发送消息
  async sendMessage() {
    const { inputText, messages } = this.data;
    
    if (!inputText.trim()) return;
    
    // 添加用户消息
    const newMessages = [...messages, {
      role: 'user',
      content: inputText
    }];
    
    this.setData({
      messages: newMessages,
      inputText: '',
      loading: true,
      canSend: false
    });
    
    // 滚动到底部
    this.scrollToBottom();
    
    try {
      // 构建历史消息
      const history = messages.slice(-10).map(m => ({
        role: m.role,
        content: m.content
      }));
      
      const res = await app.request({
        url: '/ai/chat',
        method: 'POST',
        data: {
          message: inputText,
          history: history
        }
      });
      
      // 解析AI回复，检查是否包含操作标记
      const { content, action } = this.parseAIReply(res.reply);
      
      // 添加AI回复
      this.setData({
        messages: [...newMessages, {
          role: 'assistant',
          content: content,
          action: action  // 如果有操作标记，这里会有值
        }],
        loading: false,
        canSend: this.data.inputText.trim().length > 0
      });
      
      this.scrollToBottom();
    } catch (err) {
      console.error('发送消息失败:', err);
      this.setData({
        messages: [...newMessages, {
          role: 'assistant',
          content: '抱歉，服务暂时不可用，请稍后再试。'
        }],
        loading: false,
        canSend: this.data.inputText.trim().length > 0
      });
    }
  },

  // 滚动到底部
  scrollToBottom() {
    setTimeout(() => {
      wx.pageScrollTo({
        scrollTop: 99999,
        duration: 300
      });
    }, 100);
  },

  // 解析AI回复，提取操作标记
  parseAIReply(reply) {
    // 检查是否包含 [ACTION:xxx] 标记
    const actionPattern = /\[ACTION:(\w+)\]/g;
    const match = actionPattern.exec(reply);
    
    if (match) {
      const action = match[1];  // 提取操作类型，如 GOTO_BOOKING
      const content = reply.replace(actionPattern, '').trim();  // 移除标记
      return { content, action };
    }
    
    return { content: reply, action: null };
  },

  // 处理操作按钮点击
  handleAction(e) {
    const action = e.currentTarget.dataset.action;
    
    if (action === 'GOTO_BOOKING') {
      // 预约是tabBar页面，必须用switchTab
      wx.switchTab({
        url: '/pages/appointment/appointment'
      });
    }
  }
});
