<template>
  <div class="table-container">
    <el-table
      :data="data"
      border
      style="width: 100%"
      v-loading="loading"
      :max-height="maxHeight"
      stripe
      class="data-table"
      :empty-text="$t('onlineClassify.table.emptyData')"
      highlight-current-row
    >
      <el-table-column
        prop="screen_name"
        :label="$t('onlineClassify.table.columns.username')"
        width="150"
      >
        <template slot-scope="scope">
          <div class="username-cell">
            <i class="el-icon-user"></i>
            <span>{{ scope.row.screen_name }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        prop="cleaned_text"
        :label="$t('onlineClassify.table.columns.cleanedText')"
        min-width="300"
        show-overflow-tooltip
      >
        <template slot-scope="scope">
          <div class="text-cell">
            <span class="text-content">{{ scope.row.cleaned_text }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        prop="category"
        :label="$t('onlineClassify.table.columns.category')"
        width="120"
      >
        <template slot-scope="scope">
          <el-tag :type="getCategoryType(scope.row.category)" size="medium">
            {{ scope.row.category }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column
        prop="created_at"
        :label="$t('onlineClassify.table.columns.createdAt')"
        width="180"
      >
        <template slot-scope="scope">
          <div class="time-cell">
            <i class="el-icon-time"></i>
            <span>{{ formatDate(scope.row.created_at) }}</span>
          </div>
        </template>
      </el-table-column>

      <el-table-column
        prop="insert_time"
        :label="$t('onlineClassify.table.columns.insertTime')"
        width="180"
      >
        <template slot-scope="scope">
          <div class="time-cell">
            <i class="el-icon-date"></i>
            <span>{{ formatDate(scope.row.insert_time) }}</span>
          </div>
        </template>
      </el-table-column>
    </el-table>

    <div
      class="pagination-container"
      v-if="pagination.total > pagination.pageSize"
    >
      <el-pagination
        layout="total, prev, pager, next, jumper"
        :total="pagination.total"
        :page-size="pagination.pageSize"
        :current-page.sync="pagination.currentPage"
        @current-change="$emit('current-change', $event)"
        background
      />
    </div>
  </div>
</template>

<script>
export default {
  name: "ClassifiedTable",
  props: {
    data: {
      type: Array,
      default: () => [],
    },
    loading: {
      type: Boolean,
      default: false,
    },
    pagination: {
      type: Object,
      default: () => ({ currentPage: 1, pageSize: 20, total: 0 }),
    },
  },
  computed: {
    maxHeight() {
      return window.innerHeight - 280;
    },
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return "-";

      try {
        const date = new Date(dateString);
        return date.toLocaleString("zh-CN", {
          year: "numeric",
          month: "2-digit",
          day: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
        });
      } catch (error) {
        return dateString;
      }
    },
    getCategoryType(category) {
      const categoryMap = {

      };

      return categoryMap[category] || "info";
    },
  },
};
</script>

<style scoped>
.table-container {
  background: #ffffff;
  border-radius: 8px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.data-table {
  border-radius: 8px 8px 0 0;
  overflow: hidden;
  flex: 1;
}

/* 自定义表格样式 */
:deep(.el-table) {
  font-size: 14px;
  color: #606266;
}

:deep(.el-table th) {
  background: linear-gradient(to right, #f5f7fa, #f9f9f9);
  color: #606266;
  font-weight: 600;
  font-size: 14px;
  padding: 12px 8px;
}

:deep(.el-table td) {
  padding: 8px 0;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #fafafa;
}

:deep(.el-table__body tr:hover > td) {
  background-color: #f0f9f0 !important;
}

.pagination-container {
  padding: 15px 0;
  text-align: right;
  background: #fff;
  border-top: 1px solid #f0f0f0;
}

/* 单元格样式 */
.username-cell,
.time-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.username-cell i {
  color: #4caf50;
  font-size: 16px;
}

.time-cell i {
  color: #909399;
  font-size: 16px;
}

.text-cell {
  line-height: 1.5;
  color: #303133;
  position: relative;
  padding: 4px 0;
}

.text-content {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2; /* 最多显示2行 */
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
  max-width: 100%;
}

/* 确保表格单元格内容不会溢出 */
:deep(.el-table .cell) {
  padding: 8px;
  line-height: 1.5;
  word-break: break-all;
}

/* 标签样式 */
:deep(.el-tag) {
  border-radius: 4px;
  padding: 0 8px;
  height: 24px;
  line-height: 24px;
}

/* 分页样式 */
:deep(.el-pagination) {
  font-weight: normal;
  padding-right: 15px;
}

:deep(.el-pagination.is-background .el-pager li:not(.disabled).active) {
  background-color: #4caf50;
}

:deep(.el-pagination.is-background .el-pager li:not(.disabled):hover) {
  color: #4caf50;
}

/* 优化tooltip样式 */
:deep(.el-tooltip__popper) {
  max-width: 50%;
  line-height: 1.6;
}
</style>
