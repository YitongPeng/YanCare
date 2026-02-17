// pages/my/my.js
const app = getApp();

Page({
  data: {
    userInfo: null,
    myCards: [],
    myAppointments: [],
    activeTab: 'cards',  // cards 或 appointments
    loading: false,
    showPhoneModal: false,
    bindPhone: ''
  },

  onLoad() {
    
  },

  onShow() {
    if (!app.checkLogin()) return;
    
    this.setData({
      userInfo: app.globalData.userInfo
    });
    
    this.loadMyCards();
    this.loadMyAppointments();
  },

  // 加载我的卡
  async loadMyCards() {
    try {
      const cards = await app.request({ url: '/cards/my-cards' });
      this.setData({ myCards: cards });
    } catch (err) {
      console.error('加载卡列表失败:', err);
    }
  },

  // 加载我的预约
  async loadMyAppointments() {
    try {
      const appointments = await app.request({ url: '/appointments/my-appointments' });
      
      // 格式化状态显示
      const statusMap = {
        'pending': '待确认',
        'confirmed': '已确认',
        'completed': '已完成',
        'cancelled': '已取消'
      };
      
      const serviceMap = {
        'wash': '洗头',
        'soak': '泡头',
        'care': '养发',
        'combo': '综合'
      };
      
      appointments.forEach(apt => {
        apt.statusText = statusMap[apt.status] || apt.status;
        apt.serviceText = serviceMap[apt.service_type] || apt.service_type;
      });
      
      this.setData({ myAppointments: appointments });
    } catch (err) {
      console.error('加载预约列表失败:', err);
    }
  },

  // 切换Tab
  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    this.setData({ activeTab: tab });
  },

  // 取消预约
  async cancelAppointment(e) {
    const id = e.currentTarget.dataset.id;
    
    const res = await wx.showModal({
      title: '确认取消',
      content: '确定要取消这个预约吗？'
    });
    
    if (!res.confirm) return;
    
    try {
      await app.request({
        url: `/appointments/${id}/cancel`,
        method: 'POST'
      });
      
      wx.showToast({
        title: '已取消',
        icon: 'success'
      });
      
      this.loadMyAppointments();
    } catch (err) {
      wx.showToast({
        title: '取消失败',
        icon: 'none'
      });
    }
  },

  // 进入员工端
  goToStaff() {
    if (app.globalData.isStaff) {
      wx.navigateTo({
        url: '/pages/staff/index'
      });
    } else {
      wx.showToast({
        title: '您不是员工',
        icon: 'none'
      });
    }
  },

  // 退出登录
  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.logout();
        }
      }
    });
  },

  // 显示绑定手机号弹窗
  showBindPhone() {
    this.setData({ showPhoneModal: true, bindPhone: '' });
  },

  // 隐藏绑定手机号弹窗
  hideBindPhone() {
    this.setData({ showPhoneModal: false, bindPhone: '' });
  },

  // 输入手机号
  onBindPhoneInput(e) {
    this.setData({ bindPhone: e.detail.value });
  },

  // 确认绑定手机号
  async confirmBindPhone() {
    const { bindPhone } = this.data;
    
    if (!bindPhone || bindPhone.length !== 11) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' });
      return;
    }
    
    try {
      const result = await app.request({
        url: '/users/bind-phone',
        method: 'POST',
        data: { phone: bindPhone }
      });
      
      // 更新本地用户信息
      app.globalData.userInfo = result.user;
      this.setData({
        userInfo: result.user,
        showPhoneModal: false
      });
      
      wx.showToast({
        title: '绑定成功',
        icon: 'success'
      });
      
      // 刷新卡列表
      this.loadMyCards();
    } catch (err) {
      wx.showToast({
        title: err.detail || '绑定失败',
        icon: 'none'
      });
    }
  }
});
