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
            <template #default="{ row }">
              <div class="username-cell">
                <i class="el-icon-user"></i>
                <span>{{ row.screen_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            prop="location"
            :label="$t('messagesPage.columns.location')"
            width="200"
            sortable="custom"
          >
            <template #default="{ row }">
              <div class="text-cell">
                <span class="text-content">{{ row.location || "-" }}</span>
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
            <template #default="{ row }">
              <div class="text-cell">
                <span class="text-content">{{ row.cleaned_text }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            prop="category"
            :label="$t('messagesPage.columns.category')"
            width="120"
            sortable="custom"
          >
            <template #default="{ row }">
              <el-tag :type="getCategoryType(row.category)" size="medium">
                {{ row.category }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="created_at"
            :label="$t('messagesPage.columns.createdAt')"
            width="180"
            sortable="custom"
          >
            <template #default="{ row }">
              <div class="time-cell">
                <i class="el-icon-time"></i>
                <span>{{ formatDate(row.created_at) }}</span>
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
        <!-- 移除了标记为已读的按钮 -->
      </div>
    </div>
  </div>
</template>

<script>
import socket from "@/utils/socket";

export default {
  name: "Messages",
  data() {
    return {
      tableData: [],
      total: 0,
      currentPage: 1,
      pageSize: 25,
      tableHeight: 400,
      sortProp: "",
      sortOrder: "",
      // 移除了 lastViewedTime 和 newMessagesCount
    };
  },
  mounted() {
    this.calculateTableHeight();
    window.addEventListener("resize", this.calculateTableHeight);

    // 连接 WebSocket
    socket.emit("get_all_help_messages", {
      page: this.currentPage,
      size: this.pageSize,
    });

    socket.on("all_help_messages", (res) => {
      this.tableData = res.data || [];
      this.total = res.total || 0;
      // 移除了 calculateNewMessages() 调用
    });

    socket.on("new_help_message", (msg) => {
      this.tableData.unshift(msg);
      this.total++;
      // 移除了 calculateNewMessages() 调用
    });
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.calculateTableHeight);
    socket.off("all_help_messages");
    socket.off("new_help_message");
  },
  methods: {
    calculateTableHeight() {
      const footerHeight =
        document.querySelector(".footer-box")?.offsetHeight || 50;
      const padding = 20;
      const extraBuffer = 20;
      const windowHeight = window.innerHeight;
      this.tableHeight = windowHeight - footerHeight - padding - extraBuffer;
      if (this.tableHeight < 300) this.tableHeight = 300;

      this.$nextTick(() => {
        const tableBody = this.$refs.tableRef?.$el.querySelector(
          ".el-table__body-wrapper"
        );
        if (tableBody) {
          const rowHeight = tableBody.querySelector("tr")?.offsetHeight || 48;
          const visibleRows = Math.floor(this.tableHeight / rowHeight);
          this.tableHeight = visibleRows * rowHeight + extraBuffer;
        }
      });
    },
    handlePageChange(page) {
      this.currentPage = page;
      socket.emit("get_all_help_messages", {
        page: this.currentPage,
        size: this.pageSize,
        sort_prop: this.sortProp,
        sort_order: this.sortOrder,
      });
      // 移除了 markAsRead() 调用
    },
    handleSortChange({ prop, order }) {
      this.sortProp = prop;
      this.sortOrder =
        order === "ascending" ? "asc" : order === "descending" ? "desc" : "";
      this.currentPage = 1;
      socket.emit("get_all_help_messages", {
        page: this.currentPage,
        size: this.pageSize,
        sort_prop: this.sortProp,
        sort_order: this.sortOrder,
      });
    },
    // 移除了 markAsRead() 方法
    // 移除了 calculateNewMessages() 方法
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
      } catch {
        return dateString;
      }
    },
    getCategoryType(category) {
      const categoryMap = {
        求助: "success",
        未知: "info",
      };
      return categoryMap[category] || "info";
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

/* 移除了 .custom-button 样式 */
</style>



