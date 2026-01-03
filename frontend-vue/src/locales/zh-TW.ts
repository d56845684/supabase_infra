export default {
  nav: {
    system: '系統管理',
    backendAccounts: '後台帳號管理',
    roles: '角色權限管理',
    payroll: '薪資計算',
    teacherLeave: '老師請假列表',
    courses: '課程管理',
    teacherProfiles: '老師管理',
    teacherAccounts: '老師帳號管理',
    bookingOverview: '老師預約總覽',
    students: '學生管理',
    studentBookings: '預約管理'
  },
  theme: { light: '淺色', dark: '深色' },
  auth: {
    logout: '登出',
    loginTitle: '歡迎回來',
    loginSubtitle: '請使用學校帳號登入後繼續使用系統。',
    email: '電子郵件',
    password: '密碼',
    confirmPassword: '確認密碼',
    phone: '聯絡電話（選填）',
    signIn: '登入',
    register: '建立帳號',
    registerTitle: '建立學生或老師帳號',
    registerSubtitle: '選擇註冊身分並設定密碼，目前不強制信箱驗證。',
    registerSuccess: '註冊成功！即將為您導向系統。',
    registerCheckEmail: '註冊成功，請至信箱確認驗證信完成啟用。',
    registerError: '註冊失敗，請稍後再試。',
    roleHint: '支援的角色',
    roles: {
      admin: '管理者',
      teacher: '老師',
      student: '學生'
    },
    passwordMismatch: '兩次密碼輸入不一致',
    noAccount: '還沒有帳號嗎？',
    createAccount: '立即註冊',
    haveAccount: '已經有帳號了嗎？',
    backToLogin: '返回登入',
    fullName: '姓名',
    emailVerificationHint: '已啟用信箱驗證，提交後請至信箱收取驗證信。',
    emailVerificationDisabled: '目前未啟用信箱驗證，提交後即可直接使用帳號。'
  },
  tables: {
    teacher: '老師',
    role: '角色',
    status: '狀態',
    email: '電子郵件',
    operations: '操作',
    period: '計薪區間',
    lessons: '堂數',
    amount: '金額',
    reason: '原因',
    date: '日期',
    schedule: '排程',
    student: '學生'
  },
  actions: {
    approve: '核准',
    updateStatus: '更新狀態',
    filter: '篩選',
    addBooking: '新增預約'
  },
  bookingForm: {
    title: '建立預約',
    student: '學生',
    teacher: '老師',
    start: '開始時間',
    end: '結束時間',
    status: '狀態',
    studentPlaceholder: '選擇學生',
    teacherPlaceholder: '選擇老師',
    startPlaceholder: '選擇開始時間',
    endPlaceholder: '選擇結束時間',
    submit: '建立',
    cancel: '取消',
    success: '已建立新預約',
    failure: '建立預約時發生錯誤',
    statusLabels: {
      scheduled: '已排程',
      completed: '已完成',
      cancelled: '已取消',
      no_show: '未出席'
    },
    validation: {
      student: '請選擇學生',
      teacher: '請選擇老師',
      start: '請選擇開始時間',
      end: '請選擇結束時間',
      endAfterStart: '結束時間需晚於開始時間',
      noProfiles: '請先建立至少一位學生與老師'
    }
  }
};
