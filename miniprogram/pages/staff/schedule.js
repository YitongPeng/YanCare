// pages/staff/schedule.js
const app = getApp();

Page({
  data: {
    stores: [],
    selectedStore: null,
    selectedDate: '',
    startTime: '08:15',
    endTime: '20:30',
    dates: [],
    mySchedules: [],
    loading: false,
    step: 1  // 1:选门店 2:选日期 3:填时间
  },

  onLoad() {
    this.loadStores();
    this.generateDates();
    this.loadMySchedules();
  },

  // 加载门店列表
  async loadStores() {
    try {
      const stores = await app.request({ url: '/stores' });
      this.setData({ stores });
    } catch (err) {
      console.error('加载门店失败:', err);
    }
  },

  // 生成可选日期（未来14天）
  generateDates() {
    const dates = [];
    const today = new Date();
    const weekDays = ['日', '一', '二', '三', '四', '五', '六'];
    
    for (let i = 0; i < 14; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      
      const dateStr = date.toISOString().split('T')[0];
      const month = date.getMonth() + 1;
      const day = date.getDate();
      
      dates.push({
        date: dateStr,
        display: `${month}/${day}`,
        weekDay: weekDays[date.getDay()]
      });
    }
    
    this.setData({ dates });
  },

  // 加载我的排班
  async loadMySchedules() {
    try {
      const schedules = await app.request({ url: '/schedules/my-schedules' });
      this.setData({ mySchedules: schedules });
    } catch (err) {
      console.error('加载排班失败:', err);
    }
  },

  // 步骤1: 选择门店
  selectStore(e) {
    const store = e.currentTarget.dataset.store;
    this.setData({ 
      selectedStore: store,
      step: 2
    });
  },

  // 步骤2: 选择日期（单选）
  selectDate(e) {
    const date = e.currentTarget.dataset.date;
    this.setData({ 
      selectedDate: date,
      step: 3
    });
  },

  // 选择开始时间
  onStartTimeChange(e) {
    this.setData({ startTime: e.detail.value });
  },

  // 选择结束时间
  onEndTimeChange(e) {
    this.setData({ endTime: e.detail.value });
  },

  // 返回上一步
  goBack() {
    const { step } = this.data;
    if (step === 2) {
      this.setData({ step: 1, selectedStore: null });
    } else if (step === 3) {
      this.setData({ step: 2, selectedDate: '' });
    }
  },

  // 重新开始（换店）
  resetFlow() {
    this.setData({
      step: 1,
      selectedStore: null,
      selectedDate: '',
      startTime: '08:15',
      endTime: '20:30'
    });
  },

  // 提交排班
  async submitSchedule() {
    const { selectedStore, selectedDate, startTime, endTime } = this.data;
    
    if (!selectedStore) {
      wx.showToast({ title: '请选择门店', icon: 'none' });
      return;
    }
    
    if (!selectedDate) {
      wx.showToast({ title: '请选择日期', icon: 'none' });
      return;
    }
    
    this.setData({ loading: true });
    
    try {
      await app.request({
        url: '/schedules/batch',
        method: 'POST',
        data: {
          store_id: selectedStore.id,
          work_dates: [selectedDate],
          start_time: startTime,
          end_time: endTime
        }
      });
      
      wx.showToast({
        title: '排班设置成功',
        icon: 'success'
      });
      
      // 重置流程并刷新排班列表
      this.setData({
        step: 1,
        selectedStore: null,
        selectedDate: '',
        startTime: '08:15',
        endTime: '20:30'
      });
      this.loadMySchedules();
    } catch (err) {
      console.error('设置排班失败:', err);
      wx.showToast({
        title: err.detail || '设置失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 删除排班
  async deleteSchedule(e) {
    const id = e.currentTarget.dataset.id;
    
    const res = await wx.showModal({
      title: '确认删除',
      content: '确定要删除这个排班吗？'
    });
    
    if (!res.confirm) return;
    
    try {
      await app.request({
        url: `/schedules/${id}`,
        method: 'DELETE'
      });
      
      wx.showToast({ title: '已删除', icon: 'success' });
      this.loadMySchedules();
    } catch (err) {
      wx.showToast({ title: '删除失败', icon: 'none' });
    }
  }
});
