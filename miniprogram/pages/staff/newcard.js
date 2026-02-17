// pages/staff/newcard.js
const app = getApp();

Page({
  data: {
    step: 1,  // 1:输入姓名和手机号 2:选服务 3:选卡类型
    customerName: '',
    customerPhone: '',
    selectedServices: [],  // 选中的服务类型
    services: [
      { type: 'wash', name: '洗头', icon: '💆', selected: false },
      { type: 'soak', name: '泡头', icon: '🧖', selected: false },
      { type: 'care', name: '养发', icon: '✨', selected: false }
    ],
    availableCards: [],  // 根据服务类型匹配的卡
    selectedCard: null,
    loading: false,
    allCardTypes: []  // 所有卡类型
  },

  onLoad() {
    this.loadCardTypes();
  },

  // 加载所有卡类型
  async loadCardTypes() {
    try {
      const cardTypes = await app.request({ url: '/cards/types' });
      this.setData({ allCardTypes: cardTypes });
    } catch (err) {
      console.error('加载卡类型失败:', err);
    }
  },

  // 输入姓名
  onNameInput(e) {
    this.setData({ customerName: e.detail.value.trim() });
  },

  // 输入手机号
  onPhoneInput(e) {
    this.setData({ customerPhone: e.detail.value.trim() });
  },

  // 确认信息，进入下一步
  confirmName() {
    const { customerName, customerPhone } = this.data;
    
    if (!customerName) {
      wx.showToast({ title: '请输入姓名', icon: 'none' });
      return;
    }
    
    if (!customerPhone || customerPhone.length !== 11) {
      wx.showToast({ title: '请输入正确的手机号', icon: 'none' });
      return;
    }
    
    this.setData({ step: 2 });
  },

  // 切换服务选择
  toggleService(e) {
    const type = e.currentTarget.dataset.type;
    const services = this.data.services.map(s => {
      if (s.type === type) {
        s.selected = !s.selected;
      }
      return s;
    });
    
    const selectedServices = services.filter(s => s.selected).map(s => s.type);
    this.setData({ services, selectedServices });
  },

  // 确认服务选择，进入下一步
  confirmServices() {
    const { selectedServices } = this.data;
    
    if (selectedServices.length === 0) {
      wx.showToast({ title: '请选择服务类型', icon: 'none' });
      return;
    }
    
    // 根据选择的服务匹配卡类型
    const availableCards = this.matchCardTypes(selectedServices);
    this.setData({ 
      step: 3,
      availableCards,
      selectedCard: null
    });
  },

  // 根据服务类型匹配卡类型
  matchCardTypes(selectedServices) {
    const { allCardTypes } = this.data;
    const hasWash = selectedServices.includes('wash');
    const hasSoak = selectedServices.includes('soak');
    const hasCare = selectedServices.includes('care');
    
    let result = [];
    
    // 1. 全选洗+泡+养 -> 只显示综合卡
    if (hasWash && hasSoak && hasCare) {
      return allCardTypes.filter(c => 
        c.service_type === 'combo' || c.service_type === 'comprehensive' || c.name.includes('综合')
      );
    }
    
    // 2. 单选洗头 -> 洗头卡
    if (hasWash && !hasSoak && !hasCare) {
      return allCardTypes.filter(c => 
        c.service_type === 'wash' || c.name.includes('洗头')
      );
    }
    
    // 3. 单选泡头 或 洗+泡 -> 泡头卡
    if ((hasSoak && !hasCare) || (hasWash && hasSoak && !hasCare)) {
      return allCardTypes.filter(c => 
        c.service_type === 'soak' || c.service_type === 'wash_soak' || 
        c.name.includes('泡头') || c.name.includes('洗泡')
      );
    }
    
    // 4. 单选养发 -> 4张保养卡
    if (hasCare && !hasWash && !hasSoak) {
      return allCardTypes.filter(c => 
        c.service_type === 'care' || c.name.includes('养') || c.name.includes('保养')
      );
    }
    
    // 5. 泡+养 -> 泡头卡 + 4种保养卡 + 综合卡
    if (hasSoak && hasCare && !hasWash) {
      // 泡头卡
      result = result.concat(allCardTypes.filter(c => 
        c.service_type === 'soak' || c.service_type === 'wash_soak' || 
        c.name.includes('泡头') || c.name.includes('洗泡')
      ));
      // 保养卡
      result = result.concat(allCardTypes.filter(c => 
        c.service_type === 'care' || c.name.includes('养') || c.name.includes('保养')
      ));
      // 综合卡
      result = result.concat(allCardTypes.filter(c => 
        c.service_type === 'combo' || c.service_type === 'comprehensive' || c.name.includes('综合')
      ));
      return result;
    }
    
    // 6. 洗+养 -> 洗头卡 + 4种保养卡
    if (hasWash && hasCare && !hasSoak) {
      // 洗头卡
      result = result.concat(allCardTypes.filter(c => 
        c.service_type === 'wash' || c.name.includes('洗头')
      ));
      // 保养卡
      result = result.concat(allCardTypes.filter(c => 
        c.service_type === 'care' || c.name.includes('养') || c.name.includes('保养')
      ));
      return result;
    }
    
    // 默认返回所有卡
    return allCardTypes;
  },

  // 选择卡类型
  selectCard(e) {
    const card = e.currentTarget.dataset.card;
    this.setData({ selectedCard: card });
  },

  // 返回上一步
  goBack() {
    const { step } = this.data;
    if (step > 1) {
      this.setData({ step: step - 1 });
    }
  },

  // 确认开卡
  async confirmNewCard() {
    const { customerName, customerPhone, selectedCard, selectedServices } = this.data;
    
    if (!selectedCard) {
      wx.showToast({ title: '请选择卡类型', icon: 'none' });
      return;
    }
    
    const res = await wx.showModal({
      title: '确认开卡',
      content: `确定为「${customerName}」(${customerPhone}) 开通「${selectedCard.name}」吗？`
    });
    
    if (!res.confirm) return;
    
    this.setData({ loading: true });
    
    try {
      // 先创建新用户，再开卡
      await app.request({
        url: '/cards/new-customer-card',
        method: 'POST',
        data: {
          customer_name: customerName,
          customer_phone: customerPhone,
          card_type_id: selectedCard.id,
          services: selectedServices
        }
      });
      
      wx.showToast({
        title: '开卡成功',
        icon: 'success'
      });
      
      // 重置表单
      setTimeout(() => {
        this.setData({
          step: 1,
          customerName: '',
          customerPhone: '',
          selectedServices: [],
          services: this.data.services.map(s => ({ ...s, selected: false })),
          availableCards: [],
          selectedCard: null
        });
      }, 1500);
      
    } catch (err) {
      console.error('开卡失败:', err);
      wx.showToast({
        title: err.detail || '开卡失败',
        icon: 'none'
      });
    } finally {
      this.setData({ loading: false });
    }
  }
});
