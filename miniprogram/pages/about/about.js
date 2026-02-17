// pages/about/about.js
Page({
  data: {
    type: '', // '', 'user', 'privacy'
    pageTitle: '关于我们'
  },

  onLoad(options) {
    const type = options.type || '';
    let pageTitle = '关于我们';
    
    if (type === 'user') {
      pageTitle = '用户协议';
    } else if (type === 'privacy') {
      pageTitle = '隐私政策';
    }
    
    this.setData({ type, pageTitle });
    
    wx.setNavigationBarTitle({
      title: pageTitle
    });
  }
});
