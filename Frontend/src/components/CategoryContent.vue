<template>
  <div class="bg">
    <div class="search-box">
      <el-select
        v-model="activeSource"
        :placeholder="$t('categoryContent.selectDataSource')"
        @change="fetchData"
      >
        <el-option :label="$t('categoryContent.originalWeibo')" value="weibo" />
        <el-option :label="$t('categoryContent.cleanedWeibo')" value="cleaned" />
        <el-option :label="$t('categoryContent.classifiedWeibo')" value="classified" />
      </el-select>
      <el-select
        v-if="activeSource === 'classified'"
        v-model="selectedCategory"
        :placeholder="$t('categoryContent.selectCategory')"
        clearable
        @change="fetchData"
      >
        <el-option
          v-for="cat in categoryOptions"
          :key="cat"
          :label="cat"
          :value="cat"
        />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="datetimerange"
        range-separator="至"
        :start-placeholder="$t('categoryContent.startTime')"
        :end-placeholder="$t('categoryContent.endTime')"
        value-format="yyyy-MM-dd HH:mm:ss"
        :default-time="['00:00:00', '23:59:59']"
        @change="fetchData"
      />
    </div>

    <div class="content-box">
      <div class="show-box">
        <el-table
          ref="tableRef"
          :data="paginatedData"
          stripe
          style="width: 100%"
          border
          :empty-text="$t('categoryContent.noData')"
          highlight-current-row
          :height="tableHeight"
        >
          <el-table-column prop="screen_name" :label="$t('categoryContent.username')" width="150">
            <template slot-scope="scope">
              <div class="username-cell">
                <i class="el-icon-user"></i>
                <span>{{ scope.row.screen_name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" :label="$t('categoryContent.publishTime')" width="180">
            <template slot-scope="scope">
              <div class="time-cell">
                <i class="el-icon-time"></i>
                <span>{{ formatDate(scope.row.created_at) }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column
            v-if="activeSource === 'weibo'"
            prop="text"
            :label="$t('categoryContent.content')"
            min-width="300"
            show-overflow-tooltip
          />
          <el-table-column
            v-if="activeSource !== 'weibo'"
            prop="cleaned_text"
            :label="$t('categoryContent.cleanedContent')"
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
            v-if="activeSource === 'classified'"
            prop="category"
            :label="$t('categoryContent.category')"
            width="120"
          >
            <template slot-scope="scope">
              <el-tag :type="getCategoryType(scope.row.category)" size="medium">
                {{ scope.row.category }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="insert_time" :label="$t('categoryContent.insertTime')" width="180">
            <template slot-scope="scope">
              <div class="time-cell">
                <i class="el-icon-date"></i>
                <span>{{ formatDate(scope.row.insert_time) }}</span>
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
        />
      </div>
    </div>
  </div>
</template>

<script>
import socket from "@/utils/socket";
import { mapGetters } from 'vuex';

export default {
  name: "CategoryContent",
  data() {
    return {
      activeSource: "weibo",
      selectedCategory: "",
      categoryOptions: [],
      fullData: [],
      paginatedData: [],
      currentPage: 1,
      pageSize: 25,
      total: 0,
      tableHeight: 400,
      dateRange: null,
    };
  },
  computed: {
    ...mapGetters(['language']),
  },
  watch: {
    language() {
      this.$nextTick(() => {
        this.calculateTableHeight();
      });
    }
  },
  mounted() {
    this.getCategories();
    this.fetchData();
    this.calculateTableHeight();
    window.addEventListener("resize", this.calculateTableHeight);

    // 监听WebSocket事件
    socket.on("categories", (res) => {
      this.categoryOptions = res.data || [];
    });

    socket.on("weibo_data", (res) => {
      if (this.activeSource === "weibo") {
        this.fullData = res.data || [];
        this.total = this.fullData.length;
        this.currentPage = 1;
        this.updatePaginatedData();
        this.$nextTick(() => {
          this.calculateTableHeight();
        });
      }
    });

    socket.on("cleaned_data", (res) => {
      if (this.activeSource === "cleaned") {
        this.fullData = res.data || [];
        this.total = this.fullData.length;
        this.currentPage = 1;
        this.updatePaginatedData();
        this.$nextTick(() => {
          this.calculateTableHeight();
        });
      }
    });

    socket.on("classified_data", (res) => {
      if (this.activeSource === "classified") {
        this.fullData = res.data || [];
        this.total = this.fullData.length;
        this.currentPage = 1;
        this.updatePaginatedData();
        this.$nextTick(() => {
          this.calculateTableHeight();
        });
      }
    });
  },
  beforeUnmount() {
    window.removeEventListener("resize", this.calculateTableHeight);
    socket.off("categories");
    socket.off("weibo_data");
    socket.off("cleaned_data");
    socket.off("classified_data");
  },
  methods: {
    calculateTableHeight() {
      const headerHeight = document.querySelector(".search-box")?.offsetHeight || 60;
      const footerHeight = document.querySelector(".footer-box")?.offsetHeight || 50;
      const padding = 40;
      const extraBuffer = 20;

      const windowHeight = window.innerHeight;
      this.tableHeight = windowHeight - headerHeight - footerHeight - padding - extraBuffer;

      if (this.tableHeight < 300) {
        this.tableHeight = 300;
      }

      this.$nextTick(() => {
        const tableBody = this.$refs.tableRef?.$el.querySelector(".el-table__body-wrapper");
        if (tableBody) {
          const rowHeight = tableBody.querySelector("tr")?.offsetHeight || 48;
          const visibleRows = Math.floor(this.tableHeight / rowHeight);
          this.tableHeight = visibleRows * rowHeight + extraBuffer;
        }
      });
    },
    getCategories() {
      socket.emit("get_categories", {});
    },
    fetchData() {
      this.fullData = [];
      this.paginatedData = [];
      let eventName = "";
      let params = {};

      if (this.activeSource === "weibo") {
        eventName = "get_weibo_data";
      } else if (this.activeSource === "cleaned") {
        eventName = "get_cleaned_data";
      } else if (this.activeSource === "classified") {
        eventName = "get_classified_data";
        if (this.selectedCategory) {
          params.category = this.selectedCategory;
        }
      }

      if (this.dateRange && this.dateRange.length === 2) {
        params.start_date = this.dateRange[0];
        params.end_date = this.dateRange[1];
      }

      try {
        socket.emit(eventName, params);
      } catch (err) {
        this.$message.error(this.$t('messages.getDataFailed'));
      }
    },
    updatePaginatedData() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      this.paginatedData = this.fullData.slice(start, end);
      this.$nextTick(() => {
        this.calculateTableHeight();
      });
    },
    handlePageChange(page) {
      this.currentPage = page;
      this.updatePaginatedData();
    },
    formatDate(dateString) {
      if (!dateString) return "-";
      try {
        const date = new Date(dateString);
        return date.toLocaleString(this.language === 'en' ? 'en-US' : 'zh-CN', {
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
      const categoryMap = {};
      return categoryMap[category] || "info";
    },
  },
};
</script>

<style scoped>
.bg {
  padding: 20px;
  display: flex;
  flex-direction: column;
  height: calc(100vh - 40px);
  box-sizing: border-box;
}

.search-box {
  margin-bottom: 20px;
  display: flex;
  gap: 20px;
  align-items: center;
  flex-shrink: 0;
}

.content-box {
  border: thin solid #e6e6e6;
  padding: 10px;
  background: #fff;
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
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
  background: #fff;
  border-top: 1px solid #f0f0f0;
  flex-shrink: 0;
}

:deep(.el-table) {
  font-size: 14px;
  color: #606266;
  border-radius: 8px 8px 0 0;
  overflow: hidden;
  width: 100%;
}

:deep(.el-table__body-wrapper) {
  overflow-y: auto;
  padding-bottom: 20px;
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
  -webkit-line-clamp: 2;
  overflow: hidden;
  text-overflow: ellipsis;
  word-break: break-all;
  max-width: 100%;
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
}

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

:deep(.el-tooltip__popper) {
  max-width: 50%;
  line-height: 1.6;
}
</style>