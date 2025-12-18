<template>
  <div class="messages-container">
    <div class="content-box">
      <div class="show-box">
        <el-table
          ref="tableRef"
          :data="tableData"
          stripe
          style="width: 100%"
          border
          :empty-text="$t('messagesPage.noData')"
          highlight-current-row
          :height="tableHeight"
          class="custom-table"
          @sort-change="handleSortChange"
        >
          <el-table-column
            prop="screen_name"
            :label="$t('messagesPage.columns.screenName')"
            width="150"
            sortable="custom"
          >
            <template slot-scope="scope">
              <div class="username-cell">
                <i class="el-icon-user"></i>
                <span>{{ scope.row.screen_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            prop="location"
            :label="$t('messagesPage.columns.location')"
            width="200"
            sortable="custom"
          >
            <template slot-scope="scope">
              <div class="text-cell">
                <span class="text-content">{{ scope.row.location || '-' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            prop="cleaned_text"
            :label="$t('messagesPage.columns.cleanedText')"
            min-width="300"
            show-overflow-tooltip
            sortable="custom"
          >
            <template slot-scope="scope">
              <div class="text-cell">
                <span class="text-content">{{ scope.row.cleaned_text }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            prop="category"
            :label="$t('messagesPage.columns.category')"
            width="120"
            sortable="custom"
          >
            <template slot-scope="scope">
              <el-tag :type="getCategoryType(scope.row.category)" size="medium">
                {{ scope.row.category }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="created_at"
            :label="$t('messagesPage.columns.createdAt')"
            width="180"
            sortable="custom"
          >
            <template slot-scope="scope">
              <div class="time-cell">
                <i class="el-icon-time"></i>
                <span>{{ formatDate(scope.row.created_at) }}</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="footer-box" v-if="total > pageSize">
        <el-pagination
          background
          layout="total, prev, pager, next, jumper"
          :page-size="pageSize"
          :total="total"
          :current-page.sync="currentPage"
          @current-change="handlePageChange"
          class="custom-pagination"
        />
        <el-button
          v-if="newMessagesCount > 0"
          style="margin-left: 10px"
          type="text"
          class="custom-button"
          @click="markAsRead"
        >
          {{ $t('messagesPage.markAsRead') }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'Messages',
  data() {
    return {
      tableData: [],
      loading: false,
      total: 0,
      currentPage: 1,
      pageSize: 25,
      tableHeight: 400,
      newMessagesCount: 0,
      sortProp: '',
      sortOrder: '',
      lastTotalCount: parseInt(localStorage.getItem('lastTotalCount') || '0', 10), // 从本地存储加载上次总条数
    };
  },
  created() {
    this.fetchData();
  },
  mounted() {
    this.calculateTableHeight();
    window.addEventListener('resize', this.calculateTableHeight);
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.calculateTableHeight);
  },
  methods: {
    calculateTableHeight() {
      const footerHeight = document.querySelector('.footer-box')?.offsetHeight || 50;
      const padding = 20;
      const extraBuffer = 20;

      const windowHeight = window.innerHeight;
      this.tableHeight = windowHeight - footerHeight - padding - extraBuffer;

      if (this.tableHeight < 300) {
        this.tableHeight = 300;
      }

      this.$nextTick(() => {
        const tableBody = this.$refs.tableRef?.$el.querySelector('.el-table__body-wrapper');
        if (tableBody) {
          const rowHeight = tableBody.querySelector('tr')?.offsetHeight || 48;
          const visibleRows = Math.floor(this.tableHeight / rowHeight);
          this.tableHeight = visibleRows * rowHeight + extraBuffer;
        }
      });
    },
    async fetchData() {
      this.loading = true;
      try {
        const params = {
          page: this.currentPage,
          size: this.pageSize,
        };
        if (this.sortProp && this.sortOrder) {
          params.sort_prop = this.sortProp;
          params.sort_order = this.sortOrder;
        }

        const response = await axios.get('http://localhost:5004/api/get_all_help_messages', { params });
        this.tableData = response.data.data || [];
        this.total = response.data.total || 0;
        this.loading = false;

        // 计算新消息数量：比较当前总条数与上次总条数
        console.log('Current Total:', this.total, 'Last Total:', this.lastTotalCount);
        if (this.total > this.lastTotalCount) {
          this.newMessagesCount = this.total - this.lastTotalCount;
          console.log('New Messages Count:', this.newMessagesCount);
          this.$message.warning(`有新的求助信息！（+${this.newMessagesCount} 条）`);
        } else {
          this.newMessagesCount = 0;
        }
      } catch (error) {
        this.loading = false;
        this.$message.error('获取数据失败');
        console.error(error);
      }
    },
    handlePageChange(page) {
      this.currentPage = page;
      this.markAsRead(); // 翻页时标记为已读
      this.fetchData();
    },
    handleSortChange({ prop, order }) {
      this.sortProp = prop;
      this.sortOrder = order === 'ascending' ? 'asc' : order === 'descending' ? 'desc' : '';
      this.currentPage = 1;
      this.fetchData();
    },
    markAsRead() {
      this.lastTotalCount = this.total; // 更新为当前总条数
      localStorage.setItem('lastTotalCount', this.lastTotalCount.toString()); // 保存到本地存储
      this.newMessagesCount = 0; // 清除提示
      console.log('Updated Last Total Count:', this.lastTotalCount); // 调试日志
      this.$message.success('已标记为已读');
    },
    formatDate(dateString) {
      if (!dateString) return '-';
      try {
        const date = new Date(dateString);
        return date.toLocaleString('zh-CN', {
          year: 'numeric',
          month: '2-digit',
          day: '2-digit',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        });
      } catch (error) {
        return dateString;
      }
    },
    getCategoryType(category) {
      const categoryMap = {
        '求助': 'success',
        '未知': 'info',
      };
      return categoryMap[category] || 'info';
    },
  },
};
</script>

<style scoped>
.messages-container {
  padding: 20px;
  height: calc(100vh - 40px);
  box-sizing: border-box;
  background: linear-gradient(135deg, #2c3e50, #34495e);
  border-radius: 10px;
  display: flex;
  flex-direction: column;
}

.content-box {
  border: thin solid rgba(255, 255, 255, 0.1);
  padding: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(5px);
}

.show-box {
  flex: 1;
  min-height: 300px;
  overflow: auto;
  position: relative;
}

.footer-box {
  padding: 15px 0;
  text-align: right;
  background: rgba(255, 255, 255, 0.05);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

:deep(.el-table) {
  font-size: 14px;
  color: #ecf0f1;
  border-radius: 8px 8px 0 0;
  overflow: hidden;
  width: 100%;
}

:deep(.el-table__body-wrapper) {
  overflow-y: auto;
  padding-bottom: 20px;
}

:deep(.el-table th) {
  background: #34495e;
  color: #080707;
  font-weight: 600;
  font-size: 14px;
  padding: 12px 8px;
}

:deep(.el-table td) {
  padding: 8px 0;
  color: #030e11;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: rgba(255, 255, 255, 0.1);
}

:deep(.el-table__body tr:hover > td) {
  background-color: rgba(255, 255, 255, 0.15) !important;
}

.username-cell,
.time-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #000;
}

.username-cell i {
  color: #00eaff;
  font-size: 16px;
}

.time-cell i {
  color: #01080c;
  font-size: 16px;
}

.text-cell {
  line-height: 1.5;
  color: #222881;
  position: relative;
  padding: 4px 0;
}

.text-content {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
  max-width: 100%;
  font-size: 14px;
}

:deep(.el-table .cell) {
  padding: 8px;
  line-height: 1.5;
  word-break: break-all;
}

:deep(.el-tag) {
  border-radius: 4px;
  padding: 0 8px;
  height: 24px;
  line-height: 24px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #ffffff;
  font-size: 19px;
}

:deep(.el-pagination) {
  font-weight: normal;
  padding-right: 15px;
}

:deep(.el-pagination.is-background .el-pager li:not(.disabled).active) {
  background-color: #3498db;
}

:deep(.el-pagination.is-background .el-pager li:not(.disabled):hover) {
  color: #00eaff;
}

:deep(.el-tooltip__popper) {
  max-width: 50%;
  line-height: 1.6;
  background: #34495e;
  color: #ecf0f1;
  border: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 14px;
}

.custom-button {
  color: #ecf0f1;
  font-size: 14px;
  padding: 5px 15px;
  border-radius: 20px;
  transition: all 0.3s;
}

.custom-button:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #00eaff;
}
</style>