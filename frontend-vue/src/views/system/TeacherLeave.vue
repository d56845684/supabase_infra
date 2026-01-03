<template>
  <div class="page">
    <h2>{{ $t('nav.teacherLeave') }}</h2>
    <el-alert
      type="info"
      :closable="false"
      title="教師請假流程尚未啟用"
      description="若需要追蹤教師請假，請先建立後端資料表與權限規則，再於前端串接對應 API。"
      show-icon
    />
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>
