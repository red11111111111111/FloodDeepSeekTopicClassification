<template>
  <div class="params-form">
    <h2 class="title">
      <i class="el-icon-setting"></i>
      {{ $t("modelParams.title") }}
    </h2>
    <form @submit.prevent="submitForm" class="form">
      <!-- 模型选择 -->
      <div class="param-group">
        <label for="model" class="param-label"
          >{{ $t("modelParams.modelSelect") }}:</label
        >
        <el-select
          id="model"
          v-model="selectedModel"
          class="model-select"
          required
          :disabled="loading"
        >
          <el-option
            v-for="model in modelOptions"
            :key="model.value"
            :label="model.label"
            :value="model.value"
          >
            <span class="model-option">
              <i class="el-icon-cpu"></i>
              {{ model.label }}
            </span>
          </el-option>
        </el-select>
      </div>

      <!-- 动态参数设置 -->
      <div class="params-grid">
        <div
          v-for="(value, key) in filteredParams"
          :key="key"
          class="param-item"
        >
          <label :for="key" class="param-label"
            >{{ formatParamLabel(key) }}:</label
          >
          <div class="input-wrapper">
            <el-input
              type="number"
              :id="key"
              v-model.number="params[key]"
              :step="getStepValue(key)"
              :min="isDecimalParam(key) ? '0' : '1'"
              :placeholder="getPlaceholder(key)"
              :disabled="loading"
              class="param-input"
              required
            >
              <template v-if="getAddonAfter(key)" slot="append">{{
                getAddonAfter(key)
              }}</template>
            </el-input>
            <div class="param-hint" v-if="getHint(key)">
              <i class="el-icon-info"></i>
              {{ getHint(key) }}
            </div>
          </div>
        </div>
      </div>

      <div class="actions">
        <el-button
          type="primary"
          native-type="submit"
          :loading="loading"
          :disabled="loading"
          icon="el-icon-check"
        >
          {{ $t("modelParams.submitButton") }}
        </el-button>
        <el-button
          @click="resetForm"
          type="info"
          plain
          :disabled="loading"
          icon="el-icon-refresh-left"
        >
          {{ $t("common.reset") }}
        </el-button>
      </div>
    </form>
  </div>
</template>

<script>
export default {
  props: {
    loading: {
      type: Boolean,
      default: false,
    },
  },
  data() {
    return {
      params: {
        dropout: 0.1, 
        num_epochs: 3, // 预训练模型需要较少epoch
        batch_size: 16, // 适应8GB显存
        learning_rate: 0.00002, // 适合预训练模型微调
      },
      selectedModel: "TextCNN",
      modelOptions: [
        { value: "TextCNN", label: "TextCNN" },
        { value: "TextRNN", label: "TextRNN" },
        { value: "TextRCNN", label: "TextRCNN" },
        { value: "TextRNN_Att", label: "TextRNN_Att" },
        { value: "Transformer", label: "Transformer" },
        { value: "DPCNN", label: "DPCNN" },
        { value: "bert", label: "Bert" },
        { value: "bert_cnn", label: "Bert-CNN" },
      ],
    };
  },
  computed: {
    filteredParams() {
      const { model, ...rest } = this.params;
      return rest;
    },
  },
  methods: {
    submitForm() {
      // 表单验证
      const invalidFields = [];
      if (!this.selectedModel) {
        invalidFields.push("模型类型");
      }
      for (const [key, value] of Object.entries(this.params)) {
        if (value == null || value === "") {
          invalidFields.push(this.formatParamLabel(key));
        } else if (this.isDecimalParam(key) && (value < 0 || value > 1)) {
          invalidFields.push(`${this.formatParamLabel(key)} (需在0-1之间)`);
        } else if (key === "num_epochs" && value < 1) {
          invalidFields.push(`${this.formatParamLabel(key)} (需大于0)`);
        } else if (key === "batch_size" && value < 1) {
          invalidFields.push(`${this.formatParamLabel(key)} (需大于0)`);
        }
      }

      if (invalidFields.length > 0) {
        this.$message.error(`请检查以下字段：${invalidFields.join(", ")}`);
        console.log("ParamsForm - Validation failed:", invalidFields);
        return;
      }

      const payload = {
        ...this.params,
        model: this.selectedModel,
      };
      console.log("ParamsForm - Submitting:", payload);
      this.$emit("params-submitted", payload);
      this.$message.success(this.$t("modelParams.submitSuccess"));
    },
    resetForm() {
      this.params = {
        dropout: this.selectedModel === "Qwen" ? 0.1 : 0.4,
        num_epochs: this.selectedModel === "Qwen" ? 3 : 5,
        batch_size: this.selectedModel === "Qwen" ? 16 : 128,
        learning_rate: this.selectedModel === "Qwen" ? 0.00002 : 0.00004,
      };
      this.selectedModel = "TextCNN";
      console.log("ParamsForm - Reset");
      this.$emit("params-submitted", null);
    },
    formatParamLabel(key) {
      const labelMap = {
        dropout: this.$t("modelParams.fields.dropout"),
        num_epochs: this.$t("modelParams.fields.numEpochs"),
        batch_size: this.$t("modelParams.fields.batchSize"),
        learning_rate: this.$t("modelParams.fields.learningRate"),
      };
      return labelMap[key] || this.capitalize(key.replace(/_/g, " "));
    },
    capitalize(value) {
      if (!value) return "";
      value = value.toString();
      return value.charAt(0).toUpperCase() + value.slice(1);
    },
    isDecimalParam(key) {
      return ["dropout", "learning_rate"].includes(key);
    },
    getStepValue(key) {
      if (key === "dropout") return "0.1";
      if (key === "learning_rate") return "0.00001";
      return "1";
    },
    getPlaceholder(key) {
      const placeholderMap = {
        dropout: this.selectedModel === "Qwen" ? "0.1-0.3" : "0.1-0.9",
        num_epochs: this.selectedModel === "Qwen" ? "1-5" : "1-100",
        batch_size: this.selectedModel === "Qwen" ? "8-32" : "8-512",
        learning_rate: this.selectedModel === "Qwen" ? "0.00001-0.0001" : "0.00001-0.1",
      };
      return placeholderMap[key] || "";
    },
    getHint(key) {
      if (key === "dropout") return this.$t("modelParams.examples.dropout");
      if (key === "num_epochs")
        return this.$t("modelParams.examples.numEpochs");
      if (key === "batch_size")
        return this.$t("modelParams.examples.batchSize");
      if (key === "learning_rate")
        return this.$t("modelParams.examples.learningRate");
      return "";
    },
    getAddonAfter(key) {
      if (key === "num_epochs") return "轮";
      if (key === "batch_size") return "批";
      return "";
    },
  },
};
</script>

<style scoped>
.params-form {
  width: 100%;
  background: transparent;
  border-radius: 8px;
}

.title {
  font-size: 18px;
  color: #2c3e50;
  margin-bottom: 20px;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 8px;
}

.title i {
  color: #4caf50;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

.model-select {
  width: 100%;
  max-width: 300px;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-label {
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.param-input {
  width: 100%;
}

.input-wrapper {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.param-hint {
  font-size: 12px;
  color: #909399;
  display: flex;
  align-items: center;
  gap: 5px;
  margin-top: 4px;
}

.param-hint i {
  color: #4caf50;
}

.actions {
  display: flex;
  gap: 15px;
  margin-top: 5px;
}

.model-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

:deep(.el-input__inner) {
  height: 36px;
  line-height: 36px;
}

:deep(.el-input-group__append) {
  background-color: #f5f7fa;
  color: #909399;
  font-size: 12px;
}

:deep(.el-button--primary) {
  background-color: #4caf50;
  border-color: #4caf50;
}

:deep(.el-button--primary:hover) {
  background-color: #66bb6a;
  border-color: #66bb6a;
}

:deep(.el-button--info.is-plain) {
  color: #909399;
  background: #f4f4f5;
  border-color: #d3d4d6;
}

:deep(.el-button--info.is-plain:hover) {
  background: #909399;
  border-color: #909399;
  color: #fff;
}
</style>
