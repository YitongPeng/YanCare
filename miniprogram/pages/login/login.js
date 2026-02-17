// pages/login/login.js
const app = getApp();

Page({
  data: {
    role: 'customer',  // customer 或 staff
    staffPassword: '',
    nickname: '',
    loading: false,
    agreed: false  // 是否同意隐私协议（默认不勾选）
  },

  // 选择顾客
  selectCustomer() {
    this.setData({
      role: 'customer',
      staffPassword: '',
      nickname: ''
    });
  },

  // 选择员工
  selectStaff() {
    this.setData({
      role: 'staff',
      staffPassword: '',
      nickname: ''
    });
  },

  // 输入员工密码
  onPasswordInput(e) {
    this.setData({
      staffPassword: e.detail.value
    });
  },

  // 输入名字
  onNicknameInput(e) {
    this.setData({
      nickname: e.detail.value
    });
  },

  // 切换协议勾选
  toggleAgreement() {
    this.setData({
      agreed: !this.data.agreed
    });
  },

  // 打开用户协议
  openUserAgreement() {
    wx.navigateTo({
      url: '/pages/about/about?type=user'
    });
  },

  // 打开隐私政策
  openPrivacyPolicy() {
    wx.navigateTo({
      url: '/pages/about/about?type=privacy'
    });
  },

  // 统一登录方法（顾客和员工都用名字登录）
  async handleLogin() {
    const { role, staffPassword, nickname, agreed } = this.data;

    // 校验是否同意协议
    if (!agreed) {
      wx.showToast({
        title: '请先阅读并同意用户协议和隐私政策',
        icon: 'none'
      });
      return;
    }

    // 校验名字
    if (!nickname || !nickname.trim()) {
      wx.showToast({
        title: '请输入您的名字',
        icon: 'none'
      });
      return;
    }

    // 员工需要输入密码
    if (role === 'staff' && !staffPassword) {
      wx.showToast({
        title: '请输入员工密码',
        icon: 'none'
      });
      return;
    }

    // 防止重复点击
    if (this.data.loading) {
      return;
    }

    this.setData({ loading: true });

    try {
      await app.login(role, staffPassword, nickname.trim());
      
      wx.showToast({
        title: '登录成功',
        icon: 'success'
      });

      // 根据角色跳转到不同页面
      setTimeout(() => {
        if (role === 'staff') {
          wx.reLaunch({
            url: '/pages/staff/index'
          });
        } else {
          wx.switchTab({
            url: '/pages/index/index'
          });
        }
      }, 1000);
    } catch (err) {
      console.error('登录失败:', err);
      wx.showToast({
        title: err.detail || '登录失败，请重试',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  }
});
