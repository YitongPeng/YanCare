// pages/staff/addcard.js
const app = getApp();

Page({
  data: {
    searchName: '',
    searchResult: [],
    selectedUser: null,
    cardTypes: [],
    selectedCard: null,
    loading: false
  },

  onLoad() {
    this.loadCardTypes();
  },

  // 加载卡类型
  async loadCardTypes() {
    try {
      const cardTypes = await app.request({ url: '/cards/types' });
      
      const serviceMap = {
        'wash': '洗头',
        'soak': '泡头',
        'care': '养发',
        'combo': '综合'
      };
      
      cardTypes.forEach(card => {
        card.serviceText = serviceMap[card.service_type] || card.service_type;
        card.timesText = card.total_times || '无限';
        card.validityText = card.validity_days ? `${Math.round(card.validity_days / 30)}个月` : '永久';
      });
      
      this.setData({ cardTypes });
    } catch (err) {
      console.error('加载卡类型失败:', err);
    }
  },

  // 输入姓名
  onPhoneInput(e) {
    this.setData({ searchName: e.detail.value });
  },

  // 搜索用户
  async searchUser() {
    const { searchName } = this.data;
    
    if (!searchName) {
      wx.showToast({ title: '请输入姓名', icon: 'none' });
      return;
    }
    
    this.setData({ loading: true });
    
    try {
      const users = await app.request({
        url: `/users/search?nickname=${encodeURIComponent(searchName)}`
      });
      
      this.setData({
        searchResult: users,
        loading: false,
        selectedUser: null
      });
      
      if (users.length === 0) {
        wx.showToast({ title: '未找到用户', icon: 'none' });
      }
    } catch (err) {
      console.error('搜索失败:', err);
      this.setData({ loading: false });
    }
  },

  // 选择用户
  selectUser(e) {
    const user = e.currentTarget.dataset.user;
    this.setData({ selectedUser: user });
  },

  // 选择卡类型
  selectCard(e) {
    const card = e.currentTarget.dataset.card;
    this.setData({ selectedCard: card });
  },

  // 确认开卡
  async confirmAddCard() {
    const { selectedUser, selectedCard } = this.data;
    
    if (!selectedUser) {
      wx.showToast({ title: '请选择用户', icon: 'none' });
      return;
    }
    
    if (!selectedCard) {
      wx.showToast({ title: '请选择卡类型', icon: 'none' });
      return;
    }
    
    const res = await wx.showModal({
      title: '确认开卡',
      content: `确定为「${selectedUser.nickname || selectedUser.phone || '用户'}」开通「${selectedCard.name}」吗？`
    });
    
    if (!res.confirm) return;
    
    this.setData({ loading: true });
    
    try {
      await app.request({
        url: '/cards/add-card',
        method: 'POST',
        data: {
          user_id: selectedUser.id,
          card_type_id: selectedCard.id
        }
      });
      
      wx.showToast({
        title: '开卡成功',
        icon: 'success'
      });
      
      // 清空选择
      this.setData({
        selectedUser: null,
        selectedCard: null,
        searchName: '',
        searchResult: []
      });
    } catch (err) {
      console.error('开卡失败:', err);
      wx.showToast({
        title: err.detail || '开卡失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  }
});
