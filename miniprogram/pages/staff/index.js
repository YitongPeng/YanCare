// pages/staff/index.js
const app = getApp();

Page({
  data: {
    userInfo: null,
    stores: [],
    todayStatsByStore: [],  // 按门店分组的业绩
    todayAppointments: []
  },

  onLoad() {
    
  },

  onShow() {
    if (!app.globalData.isStaff) {
      wx.showToast({
        title: '无权限访问',
        icon: 'none'
      });
      // 用reLaunch确保能回到登录页，navigateBack可能无上一页会失败
      wx.reLaunch({
        url: '/pages/login/login'
      });
      return;
    }
    
    this.setData({
      userInfo: app.globalData.userInfo
    });
    
    this.loadStores();
    this.loadTodayAppointments();
  },

  // 加载门店列表
  async loadStores() {
    try {
      const stores = await app.request({ url: '/stores' });
      this.setData({ stores });
      this.loadTodayStatsByStore(stores);
    } catch (err) {
      console.error('加载门店失败:', err);
    }
  },

  // 按门店加载今日统计
  async loadTodayStatsByStore(stores) {
    const today = new Date().toISOString().split('T')[0];
    const statsByStore = [];
    
    for (const store of stores) {
      try {
        const stats = await app.request({
          url: `/appointments/staff-stats?start_date=${today}&end_date=${today}&store_id=${store.id}`
        });
        statsByStore.push({
          store: store,
          stats: stats
        });
      } catch (err) {
        // 如果这个门店没有数据，显示0
        statsByStore.push({
          store: store,
          stats: { wash: 0, soak: 0, care: 0, total: 0 }
        });
      }
    }
    
    this.setData({ todayStatsByStore: statsByStore });
  },

  // 加载今日预约
  async loadTodayAppointments() {
    try {
      const today = new Date().toISOString().split('T')[0];
      const appointments = await app.request({
        url: `/appointments/staff-appointments?appointment_date=${today}`
      });
      
      const serviceMap = {
        'wash': '洗头',
        'soak': '泡头',
        'care': '养发',
        'combo': '综合'
      };
      
      appointments.forEach(apt => {
        apt.serviceText = serviceMap[apt.service_type] || apt.service_type;
      });
      
      this.setData({ todayAppointments: appointments });
    } catch (err) {
      console.error('加载预约失败:', err);
    }
  },

  // 去排班设置
  goToSchedule() {
    wx.navigateTo({
      url: '/pages/staff/schedule'
    });
  },

  // 去查看预约
  goToAppointments() {
    wx.navigateTo({
      url: '/pages/staff/appointments'
    });
  },

  // 去续卡（老客户）
  goToAddCard() {
    wx.navigateTo({
      url: '/pages/staff/addcard'
    });
  },

  // 去开卡（新客户）
  goToNewCard() {
    wx.navigateTo({
      url: '/pages/staff/newcard'
    });
  },

  // 返回客户端
  backToCustomer() {
    wx.switchTab({
      url: '/pages/index/index'
    });
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
  }
});
