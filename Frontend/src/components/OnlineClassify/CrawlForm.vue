<template>
  <div class="form-container">
    <h2 class="component-title">
      <i class="el-icon-connection"></i>
      {{ $t("onlineClassify.title") }}
    </h2>

    <el-form
      ref="form"
      :model="formData"
      :rules="rules"
      label-width="110px"
      @submit.native.prevent
      class="crawler-form"
      :disabled="loading"
    >
      <el-form-item :label="$t('onlineClassify.cookie.label')" prop="cookie">
        <el-input
          v-model="formData.cookie"
          type="textarea"
          :rows="3"
          :placeholder="$t('onlineClassify.cookie.placeholder')"
          clearable
          :disabled="loading"
        ></el-input>
        <div class="form-tip">
          <i class="el-icon-info"></i>
          {{ $t("onlineClassify.cookie.tip") }}
          <a
            href="https://weibo.com/"
            target="_blank"
            rel="noopener noreferrer"
            class="link-text"
            >{{ $t("onlineClassify.cookie.platform") }}</a
          >
          {{ $t("onlineClassify.cookie.getTip") }}
          <el-tooltip
            :content="$t('onlineClassify.cookie.tooltip')"
            placement="top"
          >
            <i class="el-icon-question"></i>
          </el-tooltip>
        </div>
      </el-form-item>

      <el-form-item
        :label="$t('onlineClassify.keywords.label')"
        prop="keyword_list"
        class="keyword-item"
      >
        <el-input
          v-model="formData.keyword_list"
          :placeholder="$t('onlineClassify.keywords.placeholder')"
          clearable
          @input="formatKeywords"
          :disabled="loading"
        >
          <template slot="prepend">
            <i class="el-icon-collection-tag"></i>
          </template>
        </el-input>
        <div class="tags-preview" v-if="keywordTags.length > 0">
          <el-tag
            v-for="tag in keywordTags"
            :key="tag"
            size="small"
            closable
            @close="removeKeyword(tag)"
            :disabled="loading"
          >
            {{ tag }}
          </el-tag>
        </div>
      </el-form-item>

      <el-form-item :label="$t('onlineClassify.region.label')" prop="region">
        <el-input
          v-model="formData.region"
          :placeholder="$t('onlineClassify.region.placeholder')"
          clearable
          :disabled="loading"
        >
          <template slot="prepend">
            <i class="el-icon-map-location"></i>
          </template>
        </el-input>
        <div class="tags-preview" v-if="regionTags.length > 0">
          <el-tag
            v-for="tag in regionTags"
            :key="tag"
            size="small"
            type="info"
            closable
            @close="removeRegion(tag)"
            :disabled="loading"
          >
            {{ tag }}
          </el-tag>
        </div>
      </el-form-item>

      <el-form-item :label="$t('onlineClassify.dateRange.label')">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="至"
          :start-placeholder="$t('onlineClassify.dateRange.startPlaceholder')"
          :end-placeholder="$t('onlineClassify.dateRange.endPlaceholder')"
          format="yyyy-MM-dd"
          value-format="yyyy-MM-dd"
          :picker-options="pickerOptions"
          :disabled="loading"
          style="width: 100%"
        ></el-date-picker>
      </el-form-item>

      <div class="form-actions">
        <el-button
          type="primary"
          @click="submitForm"
          :loading="loading"
          :disabled="loading || isCrawling"
          icon="el-icon-upload"
          class="submit-btn"
        >
          {{
            loading
              ? $t("onlineClassify.buttons.submitting")
              : $t("onlineClassify.buttons.submit")
          }}
        </el-button>
        <el-button
          type="danger"
          @click="stopCrawl"
          :disabled="!isCrawling || loading"
          icon="el-icon-circle-close"
        >
          {{ $t("onlineClassify.buttons.stop") }}
        </el-button>
        <el-button
          @click="resetForm"
          :disabled="loading"
          icon="el-icon-refresh-left"
        >
          {{ $t("onlineClassify.buttons.reset") }}
        </el-button>
      </div>

      <div class="crawl-status" v-if="isCrawling || statusMessage">
        <div class="status-indicator">
          <div class="pulse-dot"></div>
          <span>{{ statusMessage }}</span>
        </div>
      </div>
    </el-form>
  </div>
</template>

<script>
import { mapGetters } from "vuex";
import axios from "axios";

export default {
  name: "CrawlForm",
  props: {
    loading: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      formData: {
        cookie: "",
        keyword_list: "",
        region: "",
        start_date: "",
        end_date: "",
      },
      dateRange: [],
      rules: {
        cookie: [
          {
            required: true,
            message: this.$t("onlineClassify.cookie.placeholder"),
            trigger: "blur",
          },
        ],
        keyword_list: [
          {
            required: true,
            message: this.$t("onlineClassify.keywords.placeholder"),
            trigger: "blur",
          },
        ],
        region: [
          {
            required: true,
            message: this.$t("onlineClassify.region.placeholder"),
            trigger: "blur",
          },
        ],
      },
      pickerOptions: {
        disabledDate(time) {
          return time.getTime() > Date.now();
        },
        shortcuts: [
          {
            text: "最近一周",
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setTime(start.getTime() - 3600 * 1000 * 24 * 7);
              picker.$emit("pick", [start, end]);
            },
          },
          {
            text: "最近一个月",
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setMonth(start.getMonth() - 1);
              picker.$emit("pick", [start, end]);
            },
          },
          {
            text: "最近三个月",
            onClick(picker) {
              const end = new Date();
              const start = new Date();
              start.setMonth(start.getMonth() - 3);
              picker.$emit("pick", [start, end]);
            },
          },
        ],
      },
      statusMessage: "",
    };
  },
  computed: {
    ...mapGetters(["isCrawling"]),
    keywordTags() {
      return this.formData.keyword_list
        ? this.formData.keyword_list.split(",").filter((k) => k.trim())
        : [];
    },
    regionTags() {
      return this.formData.region
        ? this.formData.region.split(",").filter((r) => r.trim())
        : [];
    },
  },
  watch: {
    dateRange(newVal) {
      if (newVal && newVal.length === 2) {
        this.formData.start_date = newVal[0];
        this.formData.end_date = newVal[1];
      } else {
        this.formData.start_date = "";
        this.formData.end_date = "";
      }
    },
    isCrawling(newVal) {
      if (newVal) {
        this.statusMessage = this.$t("onlineClassify.status.crawling");
      } else {
        this.statusMessage = "";
      }
    },
  },
  methods: {
    formatKeywords(value) {
      if (value) {
        this.formData.keyword_list = value.replace(/\s*,\s*/g, ",").trim();
      }
    },
    removeKeyword(tag) {
      const keywords = this.formData.keyword_list.split(",");
      const index = keywords.indexOf(tag);
      if (index !== -1) {
        keywords.splice(index, 1);
        this.formData.keyword_list = keywords.join(",");
      }
    },
    removeRegion(tag) {
      const regions = this.formData.region.split(",");
      const index = regions.indexOf(tag);
      if (index !== -1) {
        regions.splice(index, 1);
        this.formData.region = regions.join(",");
      }
    },
    async submitForm() {
      try {
        await this.$refs.form.validate();
        this.$emit("update:loading", true);
        const token = localStorage.getItem("token");
        const response = await axios.post(
          "http://localhost:5004/api/start_crawl",
          this.formData,
          {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          }
        );
        this.$message({
          message: response.data.message || "爬虫和数据处理器已启动",
          type: "success",
          duration: 3000,
        });
        this.$store.commit("SET_CRAWLING", true);
      } catch (error) {
        const errorMessage =
          error.response && error.response.data
            ? error.response.data.error || "启动爬虫失败"
            : "未知错误";
        this.$message({
          message: errorMessage,
          type: "error",
          duration: 5000,
        });
        if (
          error.response &&
          error.response.status === 401 &&
          errorMessage.includes("Token")
        ) {
          localStorage.removeItem("token");
          this.$router.push("/login");
        }
      } finally {
        this.$emit("update:loading", false);
      }
    },
    async stopCrawl() {
      try {
        this.$emit("update:loading", true);
        const token = localStorage.getItem("token");
        const response = await axios.post(
          "http://localhost:5004/api/stop_crawl",
          {},
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );
        const { message, new_help_count } = response.data;
        this.$message({
          message: message || "爬虫已停止，数据处理完成",
          type: "success",
          duration: 3000,
        });
        this.$store.commit("SET_CRAWLING", false);
        this.statusMessage = "";

        // 新增：显示新增求助信息弹窗
        if (new_help_count > 0) {
          this.$confirm(
            `新增 ${new_help_count} 条求助信息，是否立即查看？`,
            '数据处理完成',
            {
              confirmButtonText: '查看',
              cancelButtonText: '稍后',
              type: 'success',
            }
          ).then(() => {
            this.$router.push('/dashboard/messages');
          }).catch(() => {
            this.$message.info('您可以稍后在“消息”页面查看');
          });
        }
      } catch (error) {
        const errorMessage =
          error.response && error.response.data
            ? error.response.data.error || "停止爬虫失败"
            : "未知错误";
        this.$message({
          message: errorMessage,
          type: "error",
          duration: 5000,
        });
        if (
          error.response &&
          error.response.status === 401 &&
          errorMessage.includes("Token")
        ) {
          localStorage.removeItem("token");
          this.$router.push("/login");
        }
      } finally {
        this.$emit("update:loading", false);
      }
    },
    resetForm() {
      this.$refs.form.resetFields();
      this.dateRange = [];
      this.statusMessage = "";
    },
  },
};
</script>

<style scoped>
/* 原样式保持不变 */
.form-container {
  background: #ffffff;
  border-radius: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.component-title {
  font-size: 18px;
  color: #2c3e50;
  margin-bottom: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.component-title i {
  color: #4caf50;
}

.crawler-form {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.el-form-item {
  margin-bottom: 20px;
}

.form-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 4px;
}

.form-tip i {
  font-size: 14px;
  color: #4caf50;
}

.form-tip .el-icon-question {
  color: #909399;
  cursor: pointer;
}

.form-tip .el-icon-question:hover {
  color: #4caf50;
}

.link-text {
  color: #4caf50;
  text-decoration: none;
  font-weight: 500;
}

.link-text:hover {
  text-decoration: underline;
  color: #388e3c;
}

.tags-preview {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.submit-btn {
  flex: 1.5;
}

.crawl-status {
  margin-top: 20px;
  padding: 12px;
  background: #f0f9f0;
  border-radius: 6px;
  display: flex;
  align-items: center;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #4caf50;
  font-weight: 500;
}

.pulse-dot {
  width: 12px;
  height: 12px;
  background-color: #4caf50;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(0.8);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.2);
    opacity: 1;
  }
  100% {
    transform: scale(0.8);
    opacity: 0.8;
  }
}

:deep(.el-textarea__inner) {
  font-family: monospace;
  line-height: 1.5;
}

:deep(.el-input-group__prepend) {
  background-color: #f5f7fa;
  color: #909399;
}

:deep(.el-button--primary) {
  background-color: #4caf50;
  border-color: #4caf50;
}

:deep(.el-button--primary:hover) {
  background-color: #66bb6a;
  border-color: #66bb6a;
}

:deep(.el-button--danger) {
  background-color: #f44336;
  border-color: #f44336;
}

:deep(.el-button--danger:hover) {
  background-color: #e53935;
  border-color: #e53935;
}

:deep(.el-tag) {
  border-radius: 4px;
}

:deep(.el-date-editor .el-range-separator) {
  padding: 0 5px;
}
</style>