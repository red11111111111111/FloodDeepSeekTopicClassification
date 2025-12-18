<template>
  <div class="model-comparison">
    <div class="comparison-container">
      <div class="upload-section">
        <FileUpload @file-uploaded="onFileUploaded" :selectedFile="file" />
      </div>
      <div class="params-container">
        <div class="params-section">
          <ParamsForm
            @params-submitted="onModel1ParamsSubmitted"
            :loading="loading"
            ref="model1ParamsForm"
          />
        </div>
        <div class="params-section">
          <ParamsForm
            @params-submitted="onModel2ParamsSubmitted"
            :loading="loading"
            ref="model2ParamsForm"
          />
        </div>
      </div>
      <div class="button-group">
        <el-button
          type="primary"
          :loading="loading"
          :disabled="isCompareDisabled"
          @click="submitComparison"
          size="large"
          class="compare-button"
        >
          <i class="el-icon-data-analysis"></i>
          {{ $t("modelComparison.startCompare") }}
        </el-button>
        <el-button
          type="danger"
          :disabled="loading"
          @click="resetForm"
          size="large"
        >
          <i class="el-icon-refresh"></i>
          {{ $t("modelComparison.resetForm") }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script>
import FileUpload from "./FileUpload.vue";
import ParamsForm from "./ParamsForm.vue";

export default {
  name: "ModelComparison",
  props: {
    loading: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      file: null,
      model1Params: null,
      model2Params: null,
    };
  },
  computed: {
    isCompareDisabled() {
      const disabled =
        this.loading || !this.file || !this.model1Params || !this.model2Params;
      console.log("Compare disabled check:", {
        loading: this.loading,
        file: !!this.file,
        model1Params: !!this.model1Params,
        model2Params: !!this.model2Params,
        disabled,
      });
      return disabled;
    },
  },
  methods: {
    onFileUploaded(file) {
      this.file = file;
      console.log("Compare tab - File uploaded:", file);
    },
    onModel1ParamsSubmitted(params) {
      this.model1Params = params;
      console.log("Compare tab - Model 1 params:", params);
    },
    onModel2ParamsSubmitted(params) {
      this.model2Params = params;
      console.log("Compare tab - Model 2 params:", params);
    },
    submitComparison() {
      if (this.isCompareDisabled) {
        console.log("Compare aborted: disabled");
        this.$message.warning(this.$t("modelComparison.uploadFirst"));
        return;
      }
      console.log("Submitting comparison:", {
        file: this.file,
        model1Params: this.model1Params,
        model2Params: this.model2Params,
      });
      this.$emit("compare-submitted", {
        model1Params: this.model1Params,
        model2Params: this.model2Params,
        file: this.file,
      });
    },
    resetForm() {
      this.file = null;
      this.model1Params = null;
      this.model2Params = null;
      this.$refs.model1ParamsForm.resetForm();
      this.$refs.model2ParamsForm.resetForm();
      this.$emit("compare-submitted", null);
      console.log("Compare tab - Form reset");
    },
  },
  components: {
    FileUpload,
    ParamsForm,
  },
};
</script>

<style scoped>
.model-comparison {
  display: flex;
  flex-direction: column;
  gap: 25px;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
}

.title {
  font-size: 20px;
  color: #2c3e50;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
  padding-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
}

.title i {
  color: #4caf50;
  font-size: 24px;
}

.upload-section {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border: 1px dashed #e0e0e0;
}

.params-container {
margin-top: 7%;
  display: flex;
  gap: 30px;
}

.params-section {
  flex: 1;
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.params-section h3 {
  font-size: 16px;
  color: #2c3e50;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.params-section h3 i {
  color: #4caf50;
}

.button-group {
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 10px;
}

.compare-button {
  min-width: 150px;
}

.button-group :deep(.el-button) {
  padding: 12px 25px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.button-group :deep(.el-button i) {
  font-size: 18px;
}

@media (max-width: 1200px) {
  .params-container {
    flex-direction: column;
  }
}
</style>
