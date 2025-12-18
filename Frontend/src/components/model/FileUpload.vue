<template>
  <div class="file-upload">
    <h2 class="component-title">
      <i class="el-icon-upload"></i>
      {{ $t("fileUpload.title") }}
    </h2>
    <div class="crawler-option">
      <el-checkbox v-model="useCrawlerData" @change="toggleCrawlerOption">
        {{ $t("fileUpload.useCrawlerData") }}
      </el-checkbox>
      <div v-if="useCrawlerData" class="crawler-input">
        <el-input
          v-model.number="crawlerDataCount"
          type="number"
          :min="1"
          :placeholder="$t('fileUpload.dataCountPlaceholder')"
          style="width: 200px; margin-right: 10px"
        ></el-input>
        <el-button
          type="primary"
          :loading="extracting"
          :disabled="!crawlerDataCount || crawlerDataCount <= 0"
          @click="extractCrawlerData"
        >
          {{ $t("fileUpload.extractData") }}
        </el-button>
      </div>
    </div>
    <div
      class="file-upload-box"
      :class="{ 'has-file': selectedFile }"
      @click="triggerFileInput"
      @dragover.prevent="onDragOver"
      @dragleave.prevent="onDragLeave"
      @drop.prevent="onFileDrop"
    >
      <input
        type="file"
        ref="fileInput"
        @change="onFileChange"
        accept=".txt,.csv"
        :disabled="useCrawlerData"
      />
      <div class="upload-content" v-if="!selectedFile">
        <div class="upload-icon">
          <i class="el-icon-upload2"></i>
        </div>
        <p class="upload-text">{{ $t("fileUpload.dragText") }}</p>
        <p class="upload-hint">{{ $t("fileUpload.supportedFormats") }}</p>
      </div>
      <div class="file-info" v-else>
        <div class="file-icon">
          <i class="el-icon-document"></i>
        </div>
        <div class="file-details">
          <p class="file-name">{{ selectedFile.name }}</p>
          <p class="file-size">{{ formatFileSize(selectedFile.size) }}</p>
        </div>
        <div class="file-actions">
          <el-button
            type="danger"
            size="mini"
            icon="el-icon-delete"
            circle
            @click.stop="removeFile"
          ></el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import request from '@/utils/request';

export default {
  props: {
    selectedFile: {
      type: File,
      default: null,
    },
  },
  data() {
    return {
      isDragging: false,
      file: null,
      useCrawlerData: false,
      crawlerDataCount: null,
      extracting: false,
    };
  },
  methods: {
    triggerFileInput() {
      if (!this.selectedFile && !this.useCrawlerData) {
        this.$refs.fileInput.click();
      }
    },
    onFileChange(e) {
      const file = e.target.files[0];
      if (file) {
        this.file = file;
        console.log("FileUpload - Emitting file-uploaded:", file);
        this.$emit("file-uploaded", file);
      }
    },
    onDragOver(e) {
      if (!this.useCrawlerData) {
        this.isDragging = true;
        e.dataTransfer.dropEffect = "copy";
      }
    },
    onDragLeave() {
      this.isDragging = false;
    },
    onFileDrop(e) {
      if (!this.useCrawlerData) {
        this.isDragging = false;
        const file = e.dataTransfer.files[0];
        if (file) {
          this.file = file;
          console.log("FileUpload - Emitting file-uploaded:", file);
          this.$emit("file-uploaded", file);
        }
      }
    },
    removeFile(e) {
      e.stopPropagation();
      this.file = null;
      this.$refs.fileInput.value = "";
      console.log("FileUpload - Emitting file-uploaded: null");
      this.$emit("file-uploaded", null);
    },
    formatFileSize(bytes) {
      if (bytes === 0) return "0 Bytes";
      const k = 1024;
      const sizes = ["Bytes", "KB", "MB", "GB"];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
    },
    toggleCrawlerOption() {
      if (!this.useCrawlerData) {
        this.removeFile(new Event("click"));
      }
    },
    async extractCrawlerData() {
      if (!this.crawlerDataCount || this.crawlerDataCount <= 0) {
        this.$message.error("请输入有效的提取数据条数！");
        return;
      }
      this.extracting = true;
      try {
        const response = await request.post("/extract_crawler_data", {
          count: this.crawlerDataCount,
        });
        this.$message.success(
          "数据提取成功，test.txt 已保存至服务器 uploaded_files 目录，并已自动加载为上传文件"
        );
        const fileResponse = await request.get("/download/test.txt", {
          responseType: "blob",
        });
        const file = new File([fileResponse.data], "test.txt", {
          type: "text/plain",
        });
        this.file = file;
        console.log("FileUpload - Emitting file-uploaded:", file);
        this.$emit("file-uploaded", file);
      } catch (error) {
        this.$message.error(error.message);
        if (error.response?.status === 401) {
          localStorage.removeItem("token");
          this.$router.push("/login");
        }
      } finally {
        this.extracting = false;
      }
    },
  },
};
</script>

<style scoped>
.file-upload {
  width: 100%;
  background: #ffffff;
  border-radius: 10px;
}
.component-title {
  font-size: 18px;
  color: #2c3e50;
  margin-bottom: 15px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}
.component-title i {
  color: #4caf50;
}
.crawler-option {
  margin-bottom: 15px;
}
.crawler-input {
  margin-top: 10px;
  display: flex;
  align-items: center;
}
.file-upload-box {
  border: 2px dashed #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  background-color: #fafafa;
  transition: all 0.3s ease;
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.file-upload-box:hover {
  border-color: #4caf50;
  background-color: #f0f9f0;
}
.file-upload-box.has-file {
  border-color: #4caf50;
  background-color: #f0f9f0;
}
.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.upload-icon {
  font-size: 40px;
  color: #4caf50;
  margin-bottom: 10px;
}
.upload-text {
  margin: 5px 0;
  color: #606266;
  font-size: 16px;
  font-weight: 500;
}
.upload-hint {
  margin: 5px 0 0;
  color: #909399;
  font-size: 12px;
}
input[type="file"] {
  display: none;
}
.file-info {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 10px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 6px;
}
.file-icon {
  font-size: 24px;
  color: #4caf50;
  margin-right: 15px;
}
.file-details {
  flex: 1;
}
.file-name {
  margin: 0 0 5px;
  font-weight: 500;
  color: #303133;
  font-size: 14px;
  word-break: break-all;
}
.file-size {
  margin: 0;
  color: #909399;
  font-size: 12px;
}
.file-actions {
  margin-left: 15px;
}
</style>