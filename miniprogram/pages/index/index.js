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
    console.log('[index] onLoad 开始');
    try {
      this.calculateSwiperHeight();
      console.log('[index] swiper高度计算完成');
      this.getUserLocation();
      console.log('[index] 位置请求已发起');
    } catch (err) {
      console.error('[index] onLoad 错误:', err);
      // 即使出错也要设置默认高度
      this.setData({ swiperHeight: 600 });
    }
  },

  // 计算swiper高度
  calculateSwiperHeight() {
    try {
      const systemInfo = wx.getSystemInfoSync();
      console.log('[index] 系统信息:', systemInfo);
      
      // 使用 rpx 转 px 的比例，确保在不同设备上一致
      const pixelRatio = systemInfo.pixelRatio || 2;
      const screenWidth = systemInfo.screenWidth || 375;
      const rpxToPx = screenWidth / 750;  // 小程序规范：750rpx = 屏幕宽度
      
      // 头部约120rpx，tab约56rpx，底部tabBar约100rpx
      const headerHeight = 120 * rpxToPx;
      const tabHeight = 56 * rpxToPx;
      const tabBarHeight = 100 * rpxToPx;
      
      const swiperHeight = systemInfo.windowHeight - headerHeight - tabHeight - tabBarHeight;
      const finalHeight = Math.max(swiperHeight, 400);
      
      console.log('[index] swiper高度计算:', {
        windowHeight: systemInfo.windowHeight,
        rpxToPx: rpxToPx.toFixed(2),
        finalHeight: finalHeight.toFixed(0)
      });
      
      this.setData({ swiperHeight: Math.round(finalHeight) });
    } catch (err) {
      console.error('[index] calculateSwiperHeight 错误:', err);
      this.setData({ swiperHeight: 600 });
    }
  },

  onShow() {
    console.log('[index] onShow 开始');
    console.log('[index] token 状态:', !!app.globalData.token);
    
    // 首页允许游客浏览，不强制登录（符合微信小程序规范）
    // 只在点击需要登录的功能时才提示登录
    
    console.log('[index] 当前门店数量:', this.data.stores.length);
    // 只有在没有门店数据时才重新加载（避免重复请求）
    if (this.data.stores.length === 0) {
      console.log('[index] 门店数据为空，开始加载');
      this.loadStores();
    } else {
      console.log('[index] 门店数据已存在，跳过加载');
    }
  },

  // 获取用户位置
  getUserLocation() {
    console.log('[index] 开始获取位置');
    wx.getLocation({
      type: 'gcj02',
      success: (res) => {
        console.log('[index] 位置获取成功:', res);
        this.setData({
          userLocation: {
            latitude: res.latitude,
            longitude: res.longitude
          }
        });
        this.loadStores();
      },
      fail: (err) => {
        console.log('[index] 位置获取失败:', err);
        // 用户拒绝授权，不传位置参数
        this.loadStores();
      }
    });
  },

  // 加载门店列表
  async loadStores() {
    console.log('[index] loadStores 开始');
    this.setData({ loading: true });
    
    try {
      let url = '/stores';
      if (this.data.userLocation) {
        url += `?latitude=${this.data.userLocation.latitude}&longitude=${this.data.userLocation.longitude}`;
      }
      console.log('[index] 请求URL:', url);
      
      const stores = await app.request({ url });
      console.log('[index] 门店数据返回:', stores);
      
      // 确保返回的是数组
      if (!Array.isArray(stores)) {
        throw new Error('门店数据格式错误');
      }
      
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
      
      console.log('[index] 门店数据处理完成，数量:', stores.length);
      this.setData({ stores, loading: false });
    } catch (err) {
      console.error('[index] 加载门店失败:', err);
      this.setData({ 
        stores: [], // 确保设置为空数组，而不是保持loading状态
        loading: false 
      });
      
      // 显示具体的错误信息
      const errorMsg = err.detail || err.errMsg || err.message || '网络连接失败';
      wx.showModal({
        title: '加载门店失败',
        content: errorMsg + '\n\n请检查网络或稍后重试',
        showCancel: true,
        cancelText: '取消',
        confirmText: '重试',
        success: (res) => {
          if (res.confirm) {
            this.loadStores();
          }
        }
      });
    }
  },

  // 下拉刷新
  onPullDownRefresh() {
    console.log('[index] 下拉刷新');
    this.loadStores().then(() => {
      wx.stopPullDownRefresh();
    }).catch(err => {
      console.error('[index] 下拉刷新失败:', err);
      wx.stopPullDownRefresh();
    });
  },

  // 点击预约按钮
  goToAppointment(e) {
    try {
      const store = e.currentTarget.dataset.store;
      console.log('[index] 跳转预约，门店:', store);
      // 保存选中的门店到全局
      app.globalData.selectedStore = store;
      // 跳转到预约页（tabBar页面要用switchTab）
      wx.switchTab({
        url: '/pages/appointment/appointment'
      });
    } catch (err) {
      console.error('[index] 跳转预约失败:', err);
      wx.showToast({
        title: '跳转失败',
        icon: 'none'
      });
    }
  },

  // 导航到门店
  navigateToStore(e) {
    try {
      const store = e.currentTarget.dataset.store;
      console.log('[index] 导航到门店:', store);
      wx.openLocation({
        latitude: store.latitude,
        longitude: store.longitude,
        name: store.name,
        address: store.address,
        scale: 18
      });
    } catch (err) {
      console.error('[index] 导航失败:', err);
      wx.showToast({
        title: '导航失败',
        icon: 'none'
      });
    }
  },

  // 拨打电话
  callStore(e) {
    try {
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
    } catch (err) {
      console.error('[index] 拨打电话失败:', err);
      wx.showToast({
        title: '拨打失败',
        icon: 'none'
      });
    }
  },

  // 切换标签
  switchTab(e) {
    try {
      const index = e.currentTarget.dataset.index;
      console.log('[index] 切换标签:', index);
      this.setData({ currentTab: index });
    } catch (err) {
      console.error('[index] 切换标签失败:', err);
    }
  },

  // 滑动切换
  onSwiperChange(e) {
    try {
      this.setData({ currentTab: e.detail.current });
    } catch (err) {
      console.error('[index] 滑动切换失败:', err);
    }
  },

  // 页面错误处理
  onError(err) {
    console.error('[index] 页面错误:', err);
    wx.showModal({
      title: '页面错误',
      content: '页面出现异常，请重启小程序',
      showCancel: false
    });
  },

  // 页面卸载
  onUnload() {
    console.log('[index] 页面卸载');
  }
});
