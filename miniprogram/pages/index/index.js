// pages/index/index.js
const app = getApp();

Page({
  data: {
    currentTab: 0,  // 当前标签：0服务 1门店 2团队
    stores: [],
    loading: true,
    userLocation: null,
    swiperHeight: 600  // 默认高度
  },

  onLoad() {
    this.calculateSwiperHeight();
    this.getUserLocation();
  },

  // 计算swiper高度
  calculateSwiperHeight() {
    const systemInfo = wx.getSystemInfoSync();
    // 头部约120rpx = 60px，tab约56rpx = 28px，底部tabBar约100px，留些余量
    const headerHeight = 60;
    const tabHeight = 28;
    const tabBarHeight = 50;
    const swiperHeight = systemInfo.windowHeight - headerHeight - tabHeight - tabBarHeight;
    this.setData({ swiperHeight: Math.max(swiperHeight, 400) });
  },

  onShow() {
    // 检查登录状态
    if (!app.globalData.token) {
      wx.redirectTo({
        url: '/pages/login/login'
      });
      return;
    }
    this.loadStores();
  },

  // 获取用户位置
  getUserLocation() {
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        this.setData({
          userLocation: {
            latitude: res.latitude,
            longitude: res.longitude
          }
        });
        this.loadStores();
      },
      fail: () => {
        // 用户拒绝授权，不传位置参数
        this.loadStores();
      }
    });
  },

  // 加载门店列表
  async loadStores() {
    this.setData({ loading: true });
    
    try {
      let url = '/stores';
      if (this.data.userLocation) {
        url += `?latitude=${this.data.userLocation.latitude}&longitude=${this.data.userLocation.longitude}`;
      }
      
      const stores = await app.request({ url });
      
      // 格式化距离显示，标记最近门店
      stores.forEach((store, index) => {
        // 第一个就是最近的（后端已按距离排序）
        store.isNearest = index === 0 && store.distance;
        
        if (store.distance) {
          if (store.distance < 1000) {
            store.distanceText = Math.round(store.distance) + 'm';
          } else {
            store.distanceText = (store.distance / 1000).toFixed(1) + 'km';
          }
          
          // 估算开车时间（假设平均车速30km/h，城市道路）
          const drivingMinutes = Math.ceil(store.distance / 1000 / 30 * 60);
          if (drivingMinutes < 1) {
            store.drivingTime = '约1分钟';
          } else if (drivingMinutes < 60) {
            store.drivingTime = `约${drivingMinutes}分钟`;
          } else {
            const hours = Math.floor(drivingMinutes / 60);
            const mins = drivingMinutes % 60;
            store.drivingTime = `约${hours}小时${mins}分钟`;
          }
        }
      });
      
      this.setData({ stores, loading: false });
    } catch (err) {
      console.error('加载门店失败:', err);
      this.setData({ loading: false });
      wx.showToast({
        title: '加载失败',
        icon: 'none'
      });
    }
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.loadStores().then(() => {
      wx.stopPullDownRefresh();
    });
  },

  // 点击预约按钮
  goToAppointment(e) {
    const store = e.currentTarget.dataset.store;
    // 保存选中的门店到全局
    app.globalData.selectedStore = store;
    // 跳转到预约页（tabBar页面要用switchTab）
    wx.switchTab({
      url: '/pages/appointment/appointment'
    });
  },

  // 导航到门店
  navigateToStore(e) {
    const store = e.currentTarget.dataset.store;
    wx.openLocation({
      latitude: store.latitude,
      longitude: store.longitude,
      name: store.name,
      address: store.address,
      scale: 18
    });
  },

  // 拨打电话
  callStore(e) {
    const phone = e.currentTarget.dataset.phone;
    if (phone) {
      wx.makePhoneCall({
        phoneNumber: phone
      });
    } else {
      wx.showToast({
        title: '暂无联系电话',
        icon: 'none'
      });
    }
  },

  // 切换标签
  switchTab(e) {
    const index = e.currentTarget.dataset.index;
    this.setData({ currentTab: index });
  },

  // 滑动切换
  onSwiperChange(e) {
    this.setData({ currentTab: e.detail.current });
  }
});
