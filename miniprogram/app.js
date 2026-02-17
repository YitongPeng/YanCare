// app.js
App({
  globalData: {
    userInfo: null,
    token: null,
    isStaff: false,
    baseUrl: 'https://api.yanhutang.cn/api'  // 线上域名
    // baseUrl: 'http://localhost:8000/api'  // 本地测试
  },

  onLaunch() {
    // 检查登录状态
    const token = wx.getStorageSync('token');
    const userInfo = wx.getStorageSync('userInfo');
    
    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
      this.globalData.isStaff = userInfo.role === 'staff' || userInfo.role === 'admin';
    }
  },

  // 封装请求方法
  request(options) {
    const { url, method = 'GET', data, needAuth = true } = options;
    
    return new Promise((resolve, reject) => {
      const header = {
        'Content-Type': 'application/json'
      };
      
      if (needAuth && this.globalData.token) {
        header['Authorization'] = `Bearer ${this.globalData.token}`;
      }
      
      wx.request({
        url: this.globalData.baseUrl + url,
        method,
        data,
        header,
        success: (res) => {
          if (res.statusCode === 200) {
            resolve(res.data);
          } else if (res.statusCode === 401) {
            // token失效，跳转登录
            this.logout();
            reject(res.data || { detail: '登录已过期' });
          } else {
            reject(res.data || { detail: '请求失败' });
          }
        },
        fail: (err) => {
          // 网络错误统一格式，确保有detail字段
          reject({ detail: '网络连接失败，请检查网络', errMsg: err.errMsg });
        }
      });
    });
  },

  // 登录方法（名字登录，无需微信授权）
  async login(role = 'customer', staffPassword = '', nickname = '') {
    try {
      const data = await this.request({
        url: '/auth/name-login',
        method: 'POST',
        data: {
          name: nickname,
          role: role,
          staff_password: staffPassword || undefined
        },
        needAuth: false
      });
      
      // 保存登录信息
      this.globalData.token = data.access_token;
      this.globalData.userInfo = data.user;
      this.globalData.isStaff = data.user.role === 'staff' || data.user.role === 'admin';
      
      wx.setStorageSync('token', data.access_token);
      wx.setStorageSync('userInfo', data.user);
      
      return data;
    } catch (err) {
      throw err;
    }
  },

  // 退出登录
  logout() {
    this.globalData.token = null;
    this.globalData.userInfo = null;
    this.globalData.isStaff = false;
    
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
    
    wx.reLaunch({
      url: '/pages/login/login'
    });
  },

  // 检查是否登录
  checkLogin() {
    if (!this.globalData.token) {
      wx.redirectTo({
        url: '/pages/login/login'
      });
      return false;
    }
    return true;
  }
});
