// pages/appointment/appointment.js
const app = getApp();

Page({
  data: {
    stores: [],
    selectedStore: null,
    isMember: null,  // true: 有卡, false: 没卡
    userCards: [],   // 用户拥有的卡
    selectedCard: null,  // 选中的卡
    selectedServices: [], // 选中的服务（多选）
    selectedDate: '',
    availableStaff: [],
    selectedStaff: null,
    selectedTime: '',
    dates: [],
    // 非会员可选的服务
    guestServices: [
      { type: 'wash', name: '洗头', duration: 30, icon: '💆' },
      { type: 'soak', name: '泡头', duration: 50, icon: '🧖' },
      { type: 'care', name: '养发', duration: 50, icon: '✨' }
    ],
    loading: false,
    step: 1  // 1:选门店 2:是否会员 3:选服务 4:选时间
  },

  onLoad(options) {
    this.loadStores();
    this.generateDates();
  },

  onShow() {
    // 检查是否从首页传来了选中的门店
    const selectedStore = app.globalData.selectedStore;
    if (selectedStore) {
      this.setData({
        selectedStore: selectedStore,
        step: 2
      });
      app.globalData.selectedStore = null;
    }
  },

  // 加载门店列表
  async loadStores() {
    try {
      const stores = await app.request({ url: '/stores' });
      this.setData({ stores });
      
      if (this.data.selectedStore) {
        const store = stores.find(s => s.id === this.data.selectedStore.id);
        if (store) {
          this.setData({ selectedStore: store });
        }
      }
    } catch (err) {
      console.error('加载门店失败:', err);
    }
  },

  // 加载用户的卡
  async loadUserCards() {
    this.setData({ loading: true });
    try {
      const cards = await app.request({ url: '/cards/my-cards' });
      // 处理每张卡的状态和可用服务
      const now = new Date();
      cards.forEach(card => {
        // 检查是否过期
        if (card.expire_date) {
          const expireDate = new Date(card.expire_date);
          card.isExpired = expireDate < now;
          card.expireDateDisplay = card.expire_date.split('T')[0];
        } else {
          card.isExpired = false;
          card.expireDateDisplay = '永久有效';
        }
        
        // 根据卡类型设置可选服务
        card.availableServices = this.getCardServices(card.service_type);
      });
      
      this.setData({ userCards: cards, loading: false });
    } catch (err) {
      console.error('加载用户卡失败:', err);
      this.setData({ userCards: [], loading: false });
    }
  },

  // 根据服务类型获取可选服务
  getCardServices(serviceType) {
    if (!serviceType) return [];
    
    // 综合卡可以选择洗泡或养
    if (serviceType === 'combo') {
      return [
        { type: 'wash_soak', name: '洗泡', duration: 50, icon: '💆🧖' },
        { type: 'care', name: '养发', duration: 50, icon: '✨' }
      ];
    }
    
    // 其他卡类型固定服务
    const serviceMap = {
      'wash': [{ type: 'wash', name: '洗头', duration: 30, icon: '💆' }],
      'soak': [{ type: 'soak', name: '泡头', duration: 50, icon: '🧖' }],
      'care': [{ type: 'care', name: '养发', duration: 50, icon: '✨' }],
      'wash_soak': [{ type: 'wash_soak', name: '洗泡', duration: 50, icon: '💆🧖' }]
    };
    
    return serviceMap[serviceType] || [];
  },

  // 生成可选日期（未来7天）
  generateDates() {
    const dates = [];
    const today = new Date();
    const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六'];
    
    for (let i = 0; i < 7; i++) {
      const date = new Date(today);
      date.setDate(today.getDate() + i);
      
      const dateStr = date.toISOString().split('T')[0];
      const month = date.getMonth() + 1;
      const day = date.getDate();
      const weekDay = i === 0 ? '今天' : (i === 1 ? '明天' : weekDays[date.getDay()]);
      
      dates.push({
        date: dateStr,
        display: `${month}月${day}日`,
        weekDay: weekDay
      });
    }
    
    this.setData({ dates });
  },

  // 选择门店
  selectStore(e) {
    const store = e.currentTarget.dataset.store;
    this.setData({
      selectedStore: store,
      step: 2,
      isMember: null,
      userCards: [],
      selectedCard: null,
      selectedServices: [],
      availableStaff: [],
      selectedStaff: null,
      selectedTime: '',
      selectedDate: ''
    });
  },

  // 选择是否会员
  selectMemberStatus(e) {
    const isMember = e.currentTarget.dataset.ismember;
    
    // 重置散客服务的选中状态
    const guestServices = this.data.guestServices.map(s => ({
      ...s,
      isSelected: false
    }));
    
    this.setData({
      isMember: isMember,
      step: 3,
      selectedCard: null,
      selectedServices: [],
      guestServices: guestServices
    });
    
    if (isMember) {
      this.loadUserCards();
    }
  },

  // 选择卡
  selectCard(e) {
    const card = e.currentTarget.dataset.card;
    // 如果卡已过期或次数用完，不能选
    if (card.isExpired || card.remaining_times <= 0) {
      wx.showToast({
        title: card.isExpired ? '此卡已过期' : '此卡次数已用完',
        icon: 'none'
      });
      return;
    }
    
    // 初始化服务的选中状态
    card.availableServices = card.availableServices.map(s => ({
      ...s,
      isSelected: false
    }));
    
    this.setData({
      selectedCard: card,
      selectedServices: []  // 重置服务选择
    });
  },

  // 切换服务选择（多选）
  toggleService(e) {
    const service = e.currentTarget.dataset.service;
    let selectedServices = [...this.data.selectedServices];
    
    const index = selectedServices.findIndex(s => s.type === service.type);
    if (index > -1) {
      // 已选中，取消
      selectedServices.splice(index, 1);
    } else {
      // 未选中，添加
      selectedServices.push(service);
    }
    
    // 更新服务列表的选中状态
    this.updateServiceSelection(selectedServices);
    
    this.setData({ selectedServices });
  },

  // 更新服务列表的选中状态
  updateServiceSelection(selectedServices) {
    const { isMember, selectedCard } = this.data;
    
    if (isMember && selectedCard) {
      // 会员：更新卡的可用服务选中状态
      const availableServices = selectedCard.availableServices.map(s => ({
        ...s,
        isSelected: selectedServices.some(sel => sel.type === s.type)
      }));
      this.setData({
        'selectedCard.availableServices': availableServices
      });
    } else {
      // 非会员：更新散客服务选中状态
      const guestServices = this.data.guestServices.map(s => ({
        ...s,
        isSelected: selectedServices.some(sel => sel.type === s.type)
      }));
      this.setData({ guestServices });
    }
  },

  // 进入下一步（选时间）
  goToSelectTime() {
    if (this.data.selectedServices.length === 0) {
      wx.showToast({
        title: '请选择服务',
        icon: 'none'
      });
      return;
    }
    this.setData({ step: 4 });
  },

  // 选择日期
  selectDate(e) {
    const date = e.currentTarget.dataset.date;
    this.setData({
      selectedDate: date,
      availableStaff: [],
      selectedStaff: null,
      selectedTime: ''
    });
    
    this.loadAvailableStaff();
  },

  // 加载可用员工
  async loadAvailableStaff() {
    const { selectedStore, selectedDate, selectedServices } = this.data;
    
    if (!selectedStore || !selectedDate || selectedServices.length === 0) return;
    
    // 计算总服务时长
    const totalDuration = selectedServices.reduce((sum, s) => sum + s.duration, 0);
    
    this.setData({ loading: true });
    
    try {
      const staff = await app.request({
        url: `/schedules/available-staff?store_id=${selectedStore.id}&work_date=${selectedDate}&service_duration=${totalDuration}`
      });
      
      this.setData({ availableStaff: staff, loading: false });
    } catch (err) {
      console.error('加载员工失败:', err);
      this.setData({ loading: false, availableStaff: [] });
    }
  },

  // 选择员工
  selectStaff(e) {
    const staff = e.currentTarget.dataset.staff;
    this.setData({
      selectedStaff: staff,
      selectedTime: ''
    });
  },

  // 选择时间
  selectTime(e) {
    const time = e.currentTarget.dataset.time;
    this.setData({ selectedTime: time });
  },

  // 提交预约
  async submitAppointment() {
    const { selectedStore, selectedDate, selectedServices, selectedStaff, selectedTime, isMember, selectedCard } = this.data;
    
    if (!selectedStore || !selectedDate || selectedServices.length === 0 || !selectedStaff || !selectedTime) {
      wx.showToast({
        title: '请完成所有选择',
        icon: 'none'
      });
      return;
    }
    
    this.setData({ loading: true });
    
    try {
      // 获取服务类型（映射到后端枚举）
      // wash_soak 映射到 soak（泡头必洗头）
      const serviceTypeMap = {
        'wash': 'wash',
        'soak': 'soak',
        'care': 'care',
        'wash_soak': 'soak',  // 洗泡 -> soak
        'combo': 'combo'
      };
      
      // 取第一个服务类型
      const firstService = selectedServices[0];
      const serviceType = serviceTypeMap[firstService.type] || firstService.type;
      
      // 综合卡选了多少个服务，核销时就扣多少次
      const serviceCount = selectedServices.length;
      
      await app.request({
        url: '/appointments',
        method: 'POST',
        data: {
          store_id: selectedStore.id,
          staff_id: selectedStaff.staff.id,
          service_type: serviceType,
          appointment_date: selectedDate,
          start_time: selectedTime,
          user_card_id: isMember && selectedCard ? selectedCard.id : null,
          service_count: serviceCount  // 服务数量，用于综合卡扣次
        }
      });
      
      wx.showToast({
        title: '预约成功',
        icon: 'success'
      });
      
      setTimeout(() => {
        wx.switchTab({
          url: '/pages/my/my'
        });
      }, 1500);
    } catch (err) {
      console.error('预约失败:', err);
      wx.showToast({
        title: err.detail || '预约失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  },

  // 返回上一步
  goBack() {
    const { step } = this.data;
    if (step > 1) {
      if (step === 4) {
        // 从选时间返回选服务
        this.setData({ 
          step: 3,
          selectedDate: '',
          availableStaff: [],
          selectedStaff: null,
          selectedTime: ''
        });
      } else if (step === 3) {
        // 从选服务返回是否会员
        this.setData({ 
          step: 2,
          selectedCard: null,
          selectedServices: []
        });
      } else {
        this.setData({ step: step - 1 });
      }
    }
  }
});
