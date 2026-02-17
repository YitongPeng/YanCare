// pages/staff/appointments.js
const app = getApp();

Page({
  data: {
    appointments: [],
    selectedDate: '',
    dates: [],
    loading: false
  },

  onLoad() {
    this.generateDates();
    const today = new Date().toISOString().split('T')[0];
    this.setData({ selectedDate: today });
    this.loadAppointments();
  },

  // 生成日期选项
  generateDates() {
    const dates = [];
    const today = new Date();
    
    for (let i = -3; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      
      const dateStr = date.toISOString().split('T')[0];
      const month = date.getMonth() + 1;
      const day = date.getDate();
      const label = i === 0 ? '今天' : (i === 1 ? '明天' : `${month}/${day}`);
      
      dates.push({
        date: dateStr,
        label: label
      });
    }
    
    this.setData({ dates });
  },

  // 选择日期
  selectDate(e) {
    const date = e.currentTarget.dataset.date;
    this.setData({ selectedDate: date });
    this.loadAppointments();
  },

  // 加载预约列表
  async loadAppointments() {
    const { selectedDate } = this.data;
    this.setData({ loading: true });
    
    try {
      const appointments = await app.request({
        url: `/appointments/staff-appointments?appointment_date=${selectedDate}`
      });
      
      const serviceMap = {
        'wash': '洗头',
        'soak': '泡头',
        'care': '养发',
        'combo': '综合'
      };
      
      const statusMap = {
        'pending': '待确认',
        'confirmed': '待服务',
        'completed': '已完成',
        'cancelled': '已取消'
      };
      
      appointments.forEach(apt => {
        apt.serviceText = serviceMap[apt.service_type] || apt.service_type;
        apt.statusText = statusMap[apt.status] || apt.status;
      });
      
      this.setData({ appointments, loading: false });
    } catch (err) {
      console.error('加载预约失败:', err);
      this.setData({ loading: false });
    }
  },

  // 核销预约
  async completeAppointment(e) {
    const apt = e.currentTarget.dataset.apt;
    
    // 先获取客户的卡
    wx.showLoading({ title: '加载中...' });
    
    try {
      const cards = await app.request({
        url: `/cards/user/${apt.customer_id}`
      });
      
      wx.hideLoading();
      
      if (cards.length === 0) {
        wx.showToast({
          title: '客户没有可用的卡',
          icon: 'none'
        });
        return;
      }
      
      // 筛选可用的卡
      const availableCards = cards.filter(c => !c.is_expired && c.is_active);
      
      if (availableCards.length === 0) {
        wx.showToast({
          title: '客户没有可用的卡',
          icon: 'none'
        });
        return;
      }
      
      // 选择卡
      const cardNames = availableCards.map(c => `${c.card_name} (剩余${c.remaining_times || '无限'}次)`);
      
      const res = await wx.showActionSheet({
        itemList: cardNames
      });
      
      const selectedCard = availableCards[res.tapIndex];
      
      // 确认核销
      const confirm = await wx.showModal({
        title: '确认核销',
        content: `确定使用「${selectedCard.card_name}」核销此服务吗？`
      });
      
      if (!confirm.confirm) return;
      
      // 执行核销
      await app.request({
        url: `/appointments/${apt.id}/complete`,
        method: 'POST',
        data: {
          user_card_id: selectedCard.id
        }
      });
      
      wx.showToast({
        title: '核销成功',
        icon: 'success'
      });
      
      this.loadAppointments();
    } catch (err) {
      wx.hideLoading();
      // 用户取消选择不算错误
      if (err.errMsg && err.errMsg.includes('cancel')) {
        return;
      }
      console.error('核销失败:', err);
      wx.showToast({
        title: err.detail || '核销失败',
        icon: 'none'
      });
    }
  }
});
