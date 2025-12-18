<template>
  <div class="crawl-page">
    <div class="content-container">
      <div class="left-panel">
        <el-tabs type="border-card" class="custom-tabs">
          <el-tab-pane :label="$t('onlineClassify.tabs.crawler')">
            <div class="panel-content">
              <crawl-form
                @submit="handleSubmit"
                @stop="stopPolling"
                :loading="loading"
              />
            </div>
          </el-tab-pane>
          <el-tab-pane :label="$t('onlineClassify.tabs.model')">
            <div class="panel-content model-panel">
              <FileUpload
                @file-uploaded="onFileUploaded"
                :selectedFile="file"
              />
              <ParamsForm
                @params-submitted="onParamsSubmitted"
                :loading="isModelLoading"
                ref="paramsForm"
              />
            </div>
          </el-tab-pane>
          <el-tab-pane :label="$t('onlineClassify.tabs.comparison')">
            <div class="panel-content">
              <ModelComparison
                @compare-submitted="onCompareSubmitted"
                :loading="isCompareLoading"
              />
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
      <div class="right-panel">
        <div class="table-header">
          <h3 class="section-title">{{ $t("onlineClassify.table.title") }}</h3>
          <div class="actions">
            <el-button
              type="primary"
              size="small"
              icon="el-icon-refresh"
              @click="refreshData"
              :loading="loading"
              circle
            ></el-button>
          </div>
        </div>
        <div class="filter-container">
          <el-form inline>
            <el-form-item :label="$t('onlineClassify.filters.category')">
              <el-select
                v-model="filters.category"
                clearable
                :placeholder="$t('onlineClassify.filters.categoryPlaceholder')"
                @change="applyFilters"
                :disabled="!categories.length"
              >
                <el-option
                  v-for="cat in categories"
                  :key="cat"
                  :label="cat"
                  :value="cat"
                />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('onlineClassify.filters.createdAt')">
              <el-date-picker
                v-model="filters.dateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="yyyy-MM-dd"
                value-format="yyyy-MM-dd"
                @change="applyFilters"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="danger" size="small" @click="resetFilters">
                {{ $t("onlineClassify.filters.reset") }}
              </el-button>
            </el-form-item>
          </el-form>
        </div>
        <transition name="fade">
          <div v-if="!filteredData.length && !loading" class="empty-tip">
            <i class="el-icon-data-analysis"></i>
            <span>{{ $t("onlineClassify.table.emptyTip") }}</span>
            <el-button
              type="text"
              size="small"
              @click="refreshData"
              style="margin-top: 10px"
            >
              {{ $t("onlineClassify.table.retry") }}
            </el-button>
          </div>
          <div
            v-else-if="loading && !filteredData.length"
            class="loading-container"
          >
            <div class="loading-spinner">
              <i class="el-icon-loading"></i>
            </div>
            <span>{{ $t("onlineClassify.loading") }}</span>
          </div>
          <div v-else class="table-container">
            <classified-table
              :data="paginatedData"
              :loading="loading && filteredData.length > 0"
              :pagination="pagination"
              @current-change="handleCurrentChange"
            />
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import socket from "@/utils/socket";
import CrawlForm from "@/components/OnlineClassify/CrawlForm.vue";
import ClassifiedTable from "@/components/OnlineClassify/ClassifiedTable.vue";
import FileUpload from "@/components/model/FileUpload.vue";
import ParamsForm from "@/components/model/ParamsForm.vue";
import ModelComparison from "@/components/model/ModelComparison.vue";
import { mapGetters, mapActions } from "vuex";
import axios from "axios";

export default {
  name: "OnlineClassifyContent",
  components: {
    CrawlForm,
    ClassifiedTable,
    FileUpload,
    ParamsForm,
    ModelComparison,
  },
  data() {
    return {
      paginatedData: [],
      loading: false,
      pagination: {
        currentPage: 1,
        pageSize: 20,
        total: 0,
      },
      file: null,
      params: null,
      isModelLoading: false,
      isCompareLoading: false,
      filters: {
        category: "",
        dateRange: [],
      },
      maxRetries: 3,
      retryDelay: 1000,
      classifiedData: [], // 本地存储classifiedData
      categories: [], // 本地存储categories
    };
  },
  computed: {
    ...mapGetters(["isCrawling"]),
    filteredData() {
      let data = [...this.classifiedData];
      const { category, dateRange } = this.filters;
      if (category) {
        data = data.filter((item) => item.category === category);
      }
      if (dateRange && dateRange.length === 2) {
        const [startDate, endDate] = dateRange;
        data = data.filter((item) => {
          if (!item.created_at) return false;
          const createdAt = new Date(item.created_at);
          const start = new Date(startDate);
          const end = new Date(endDate);
          end.setHours(23, 59, 59, 999);
          return createdAt >= start && createdAt <= end;
        });
      }
      return data;
    },
  },
  watch: {
    filteredData(newData) {
      this.pagination.total = newData.length;
      this.pagination.currentPage = 1;
      this.updatePaginatedData();
    },
  },
  mounted() {
    this.fetchDataWithRetry();
    this.fetchCategoriesWithRetry();
    if (this.isCrawling) {
      this.startPolling();
    }

    // 监听WebSocket事件
    socket.on("classified_data", (res) => {
      this.classifiedData = res.data || [];
      this.loading = false;
    });

    socket.on("categories", (res) => {
      this.categories = res.data || [];
    });
  },
  beforeUnmount() {
    socket.off("classified_data");
    socket.off("categories");
  },
  methods: {
    ...mapActions(["startPolling", "stopPolling", "updateTrainingImage"]),
    async fetchDataWithRetry(retries = 0) {
      try {
        this.loading = true;
        socket.emit("get_classified_data", {
          category: this.filters.category,
          start_date: this.filters.dateRange[0],
          end_date: this.filters.dateRange[1],
        });
      } catch (error) {
        const errorMessage = error.message || "未知错误";
        if (retries < this.maxRetries) {
          console.warn(
            `获取数据失败，重试 ${retries + 1}/${
              this.maxRetries
            }：${errorMessage}`
          );
          setTimeout(() => {
            this.fetchDataWithRetry(retries + 1);
          }, this.retryDelay);
        } else {
          this.$message.error(
            `获取数据失败，已重试 ${this.maxRetries} 次：${errorMessage}`
          );
        }
      } finally {
        this.loading = false;
      }
    },
    async fetchCategoriesWithRetry(retries = 0) {
      try {
        socket.emit("get_categories", {});
      } catch (error) {
        const errorMessage = error.message || "未知错误";
        if (retries < this.maxRetries) {
          console.warn(
            `获取类别失败，重试 ${retries + 1}/${
              this.maxRetries
            }：${errorMessage}`
          );
          setTimeout(() => {
            this.fetchCategoriesWithRetry(retries + 1);
          }, this.retryDelay);
        } else {
          this.$message.error(
            `获取类别失败，已重试 ${this.maxRetries} 次：${errorMessage}`
          );
        }
      }
    },
    async handleSubmit(formData) {
      try {
        this.loading = true;
        const response = await this.$axios.post(
          "http://localhost:5004/api/start_crawl",
          formData
        );
        const message =
          response.data && response.data.message
            ? response.data.message
            : "爬虫已启动成功";
        this.$message({
          message,
          type: "success",
          duration: 3000,
        });
        this.startPolling();
      } catch (error) {
        const errorMessage =
          error.response && error.response.data && error.response.data.error
            ? error.response.data.error
            : error.message || "未知错误";
        this.$message({
          message: "提交失败：" + errorMessage,
          type: "error",
          duration: 5000,
        });
      } finally {
        this.loading = false;
      }
    },
    updatePaginatedData() {
      const { currentPage, pageSize } = this.pagination;
      const start = (currentPage - 1) * pageSize;
      const end = start + pageSize;
      this.paginatedData = this.filteredData.slice(start, end);
    },
    handleCurrentChange(page) {
      this.pagination.currentPage = page;
      this.updatePaginatedData();
    },
    onFileUploaded(file) {
      this.file = file;
      console.log("Model tab - File uploaded:", file);
    },
    onParamsSubmitted(params) {
      this.params = params;
      console.log("Model tab - Params submitted:", params);
      if (params) {
        this.uploadFile();
      } else {
        console.log("Model tab - Params cleared");
      }
    },
    async onCompareSubmitted({ model1Params, model2Params, file }) {
      console.log("Compare submitted:", { model1Params, model2Params, file });

      if (!file || !model1Params || !model2Params) {
        this.$message({
          message: "请上传文件并设置两个模型的参数",
          type: "warning",
          duration: 3000,
        });
        return;
      }

      this.isCompareLoading = true;
      const formData = new FormData();
      formData.append("file", file);
      formData.append("model1_params", JSON.stringify(model1Params));
      formData.append("model2_params", JSON.stringify(model2Params));

      try {
        const token = localStorage.getItem("token");
        const response = await axios.post(
          "http://localhost:5004/api/compare_models",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
              Authorization: `Bearer ${token}`,
            },
          }
        );

        console.log("Compare response:", response.data);

        // 调整 metrics 格式以匹配 updateChart 期望
        const adjustedMetrics = {
          metrics: response.data.metrics.metrics || [
            "Accuracy",
            "Precision",
            "Recall",
            "F1-Score",
          ],
          model1_data: response.data.model1_data,
          model2_data: response.data.model2_data,
          model1_name: response.data.model1_name,
          model2_name: response.data.model2_name,
        };

        // 替换默认提示为带按钮的提示框
        this.$alert("对比已结束，查看结果", "提示", {
          confirmButtonText: "查看",
          callback: (action) => {
            if (action === "confirm") {
              this.$router.push("/dashboard/big");
            }
          },
        });

        // 使用调整后的 metrics 存储到 Vuex
        this.updateTrainingImage({
          imageUrl: response.data.bar_chart,
          metrics: adjustedMetrics,
          isComparison: true,
        });
      } catch (error) {
        const errorMessage =
          error.response && error.response.data
            ? error.response.data.message || "对比失败"
            : "未知错误";
        console.error("Compare error:", errorMessage);
        this.$message.error(errorMessage);
        if (
          error.response &&
          error.response.status === 401 &&
          errorMessage === "Token has expired"
        ) {
          localStorage.removeItem("token");
          this.$router.push("/login");
        }
      } finally {
        this.isCompareLoading = false;
      }
    },
    async uploadFile() {
      console.log("Uploading file with params:", {
        file: this.file,
        params: this.params,
      });
      if (!this.file || !this.params) {
        this.$message({
          message: "请上传文件并设置参数",
          type: "warning",
          duration: 3000,
        });
        console.log("Upload aborted: missing file or params");
        return;
      }
      this.isModelLoading = true;
      const formData = new FormData();
      formData.append("file", this.file);
      formData.append("dropout", this.params.dropout);
      formData.append("num_epochs", this.params.num_epochs);
      formData.append("batch_size", this.params.batch_size);
      formData.append("learning_rate", this.params.learning_rate);
      formData.append("model", this.params.model);
      try {
        const token = localStorage.getItem("token");
        const response = await axios.post(
          "http://localhost:5004/upload",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
              Authorization: `Bearer ${token}`,
            },
          }
        );
        console.log("Upload response:", response.data);
        if (response.data && response.data.image_url) {
          this.updateTrainingImage({
            imageUrl: response.data.image_url,
            metrics: {
              accuracy: response.data.accuracy || "未收到",
              precision: response.data.precision || "未收到",
              recall: response.data.recall || "未收到",
              f1_score: response.data.f1_score || "未收到",
            },
            isComparison: false,
          });
          // 替换默认提示为带按钮的提示框
          this.$alert("训练已结束，查看结果", "提示", {
            confirmButtonText: "查看",
            callback: (action) => {
              if (action === "confirm") {
                this.$router.push("/dashboard/big");
              }
            },
          });
        }
      } catch (error) {
        const errorMessage =
          error.response && error.response.data
            ? error.response.data.message || "训练失败"
            : "未知错误";
        console.error("Upload error:", errorMessage);
        this.$message.error(errorMessage);
        if (
          error.response &&
          error.response.status === 401 &&
          errorMessage === "Token has expired"
        ) {
          localStorage.removeItem("token");
          this.$router.push("/login");
        }
      } finally {
        this.isModelLoading = false;
      }
    },
    refreshData() {
      this.fetchDataWithRetry();
    },
    applyFilters() {
      this.pagination.currentPage = 1;
      this.updatePaginatedData();
      this.fetchDataWithRetry(); // 重新查询过滤后的数据
    },
    resetFilters() {
      this.filters.category = "";
      this.filters.dateRange = [];
      this.applyFilters();
    },
  },
};
</script>

<style scoped>
/* 原样式保持不变 */
.crawl-page {
  min-height: 100%;
  box-sizing: border-box;
  padding: 10px;
  overflow: hidden;
}
.content-container {
  display: flex;
  gap: 20px;
  width: 100%;
  margin: 0 auto;
  height: calc(100vh - 80px);
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}
.left-panel,
.right-panel {
  border-radius: 8px;
  padding: 0;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
.left-panel {
  flex: 0 0 35%;
  min-width: 400px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: white;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
}
.custom-tabs {
  height: 100%;
  border: none !important;
  background: transparent;
}
.panel-content {
  padding: 15px;
  height: 100%;
  overflow-y: auto;
}
.model-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 15px;
  border-bottom: 1px solid #f0f0f0;
}
.section-title {
  color: #2c3e50;
  font-size: 18px;
  margin: 0;
  position: relative;
  padding-left: 15px;
  font-weight: 600;
}
.section-title::before {
  content: "";
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 4px;
  height: 18px;
  background: linear-gradient(to bottom, #4caf50, #388e3c);
  border-radius: 2px;
}
.empty-tip {
  margin: 30px auto;
  padding: 25px;
  background: #f9fbfd;
  border-radius: 8px;
  text-align: center;
  color: #909399;
  font-size: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 15px;
  max-width: 350px;
  border: 1px dashed #e0e0e0;
}
.empty-tip i {
  font-size: 40px;
  color: #dcdfe6;
}
.loading-container {
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 15px;
  color: #909399;
}
.loading-spinner {
  font-size: 36px;
  color: #409eff;
}
.table-container {
  flex: 1;
  overflow: hidden;
  padding: 10px;
}
.filter-container {
  padding: 10px 15px;
  border-bottom: 1px solid #f0f0f0;
  background: #fff;
}
.filter-container :deep(.el-form-item) {
  margin-bottom: 10px;
}
.filter-container :deep(.el-select) {
  width: 150px;
}
.filter-container :deep(.el-date-editor) {
  width: 300px;
}
:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #f0f0f0;
}
:deep(.el-tabs__item) {
  height: 45px;
  line-height: 45px;
  font-size: 15px;
  transition: all 0.3s;
}
:deep(.el-tabs__item.is-active) {
  color: #4caf50;
  font-weight: 600;
}
:deep(.el-tabs__active-bar) {
  background-color: #4caf50;
  height: 3px;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
@media (max-width: 1400px) {
  .left-panel {
    flex: 0 0 40%;
    min-width: 380px;
  }
}
@media (max-width: 1200px) {
  .content-container {
    flex-direction: column;
    height: auto;
    min-height: calc(100vh - 80px);
  }
  .left-panel {
    flex: 0 0 auto;
    width: 100%;
    min-width: 0;
    min-height: 500px;
  }
  .right-panel {
    flex: 1;
    min-height: 500px;
  }
}
@media (max-width: 768px) {
  .crawl-page {
    padding: 5px;
  }
  .content-container {
    padding: 10px;
  }
  .section-title {
    font-size: 16px;
  }
  .empty-tip {
    font-size: 14px;
    padding: 15px;
  }
}
</style>
