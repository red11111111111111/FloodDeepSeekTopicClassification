<template>
  <div class="center_bottom">
    <div v-if="imageUrl && !isComparisonResult" class="result-section">
      <div class="tab-header">
        <div
          class="tab-item"
          :class="{ active: activeTab === 'chart' }"
          @click="activeTab = 'chart'"
        >
          <i class="el-icon-data-line"></i>
          {{ $t("modelTraining.trainingCurve") }}
        </div>
        <div
          class="tab-item"
          :class="{ active: activeTab === 'metrics' }"
          @click="activeTab = 'metrics'"
        >
          <i class="el-icon-odometer"></i>
          {{ $t("modelTraining.evaluationMetrics") }}
        </div>
      </div>

      <transition name="fade" mode="out-in">
        <div v-if="activeTab === 'chart'" class="tab-content" key="chart">
          <div class="result-box">
            <img
              :src="`http://localhost:5004/${imageUrl}`"
              alt="Training Curve"
              @click="toggleImageZoom"
              @mousemove="updateTooltipPosition"
              @mouseenter="showTooltip = true"
              @mouseleave="showTooltip = false"
              class="chart-image"
            />
            <div
              v-show="showTooltip"
              :class="['zoom-tooltip', tooltipPlacement]"
              :style="{
                left: tooltipPosition.x + 'px',
                top: tooltipPosition.y + 'px',
              }"
            >
              <i class="el-icon-zoom-in"></i>
              {{ $t("modelTraining.clickToZoom") }}
            </div>
          </div>
        </div>

        <div v-else class="tab-content" key="metrics">
          <div class="metrics">
            <table class="metrics-table">
              <thead>
                <tr>
                  <th>{{ $t("modelTraining.metrics.accuracy") }}</th>
                  <th>{{ $t("common.value") }}</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>{{ $t("modelTraining.metrics.accuracy") }}</td>
                  <td>{{ metrics.accuracy || $t("modelTraining.noData") }}</td>
                </tr>
                <tr>
                  <td>{{ $t("modelTraining.metrics.precision") }}</td>
                  <td>{{ metrics.precision || $t("modelTraining.noData") }}</td>
                </tr>
                <tr>
                  <td>{{ $t("modelTraining.metrics.recall") }}</td>
                  <td>{{ metrics.recall || $t("modelTraining.noData") }}</td>
                </tr>
                <tr>
                  <td>{{ $t("modelTraining.metrics.f1Score") }}</td>
                  <td>{{ metrics.f1_score || $t("modelTraining.noData") }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </transition>
    </div>
    <div v-else class="loading-container">
      <div class="loading-animation">
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
        <div class="dot"></div>
      </div>
      <p class="loading-text">{{ $t("modelTraining.waitingForTraining") }}</p>
    </div>

    <!-- 图片放大遮罩层 -->
    <transition name="zoom">
      <div v-if="isZoomed" class="zoom-overlay" @click="toggleImageZoom">
        <div class="zoomed-image-container">
          <img
            :src="`http://localhost:5004/${imageUrl}`"
            alt="Training Curve"
          />
          <div class="zoom-out-hint">
            <i class="el-icon-zoom-out"></i>
            {{ $t("modelTraining.clickToClose") }}
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import { mapGetters } from "vuex";

export default {
  data() {
    return {
      activeTab: "chart",
      isZoomed: false,
      showTooltip: false,
      tooltipPosition: {
        x: 0,
        y: 0,
      },
      tooltipPlacement: "bottom",
    };
  },
  computed: {
    ...mapGetters(["trainingImage"]),
    imageUrl() {
      return this.trainingImage ? this.trainingImage.imageUrl : "";
    },
    metrics() {
      return this.trainingImage ? this.trainingImage.metrics : {};
    },
    isComparisonResult() {
      return this.trainingImage ? this.trainingImage.isComparison : false;
    },
  },
  methods: {
    toggleImageZoom() {
      this.isZoomed = !this.isZoomed;
      if (this.isZoomed) {
        document.addEventListener("keydown", this.handleEscKey);
      } else {
        document.removeEventListener("keydown", this.handleEscKey);
      }
    },
    handleEscKey(e) {
      if (e.key === "Escape" && this.isZoomed) {
        this.isZoomed = false;
        document.removeEventListener("keydown", this.handleEscKey);
      }
    },
    updateTooltipPosition(e) {
      const imgRect = e.target.getBoundingClientRect();
      const relativeY = e.clientY - imgRect.top;
      const imageMiddleY = imgRect.height / 2;
      this.tooltipPlacement = relativeY > imageMiddleY ? "top" : "bottom";
      const x = e.clientX - imgRect.left;
      let y;
      if (this.tooltipPlacement === "top") {
        y = relativeY - 40;
      } else {
        y = relativeY + 25;
      }
      const maxX = imgRect.width - 100;
      this.tooltipPosition = {
        x: Math.min(Math.max(x, 10), maxX),
        y: Math.max(y, 5),
      };
    },
  },
  beforeDestroy() {
    document.removeEventListener("keydown", this.handleEscKey);
  },
};
</script>

<style scoped>
.center_bottom {
  width: 100%;
  height: 100%;
  padding: 0;
  overflow: hidden;
  position: relative;
  display: flex;
  flex-direction: column;
}

.result-section {
  text-align: center;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.tab-header {
  display: flex;
  justify-content: space-around;
  margin-bottom: 10px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
  padding: 5px;
}

.tab-item {
  padding: 8px 15px;
  cursor: pointer;
  color: #95a5a6;
  border-radius: 4px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
}

.tab-item i {
  margin-right: 5px;
  font-size: 16px;
}

.tab-item:hover {
  color: #ecf0f1;
  background: rgba(52, 152, 219, 0.2);
}

.tab-item.active {
  color: #3498db;
  background: rgba(52, 152, 219, 0.1);
  font-weight: bold;
}

.tab-content {
  flex: 1;
  overflow: auto;
  padding: 10px;
}

.result-box {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  position: relative;
}

.chart-image {
  max-width: 95%;
  max-height: 95%;
  object-fit: contain;
  border-radius: 8px;
  cursor: zoom-in;
}

.zoom-tooltip {
  position: absolute;
  background: rgba(0, 0, 0, 0.8);
  color: #ecf0f1;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
  pointer-events: none;
  z-index: 100;
  white-space: nowrap;
}

.zoom-tooltip.bottom::before {
  content: "";
  position: absolute;
  top: -4px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 8px;
  height: 8px;
  background: rgba(0, 0, 0, 0.8);
}

.zoom-tooltip.top::after {
  content: "";
  position: absolute;
  bottom: -4px;
  left: 50%;
  transform: translateX(-50%) rotate(45deg);
  width: 8px;
  height: 8px;
  background: rgba(0, 0, 0, 0.8);
}

.metrics {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.metrics-table {
  width: 90%;
  border-collapse: collapse;
  text-align: center;
  margin: 0 auto;
}

.metrics-table th,
.metrics-table td {
  padding: 10px;
  border: 1px solid #ddd;
  color: #ecf0f1;
}

.metrics-table th {
  background-color: rgba(52, 152, 219, 0.3);
  font-weight: bold;
  color: #3498db;
}

.metrics-table tr:nth-child(even) {
  background-color: rgba(255, 255, 255, 0.05);
}

.metrics-table tr:hover {
  background-color: rgba(52, 152, 219, 0.1);
}

.loading-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-text {
  color: #ecf0f1;
  font-size: 16px;
  margin-top: 20px;
}

.loading-animation {
  display: flex;
  align-items: center;
}

.dot {
  width: 8px;
  height: 8px;
  margin: 0 4px;
  border-radius: 50%;
  background-color: #3498db;
  animation: dot-flashing 1s infinite linear alternate;
}

.dot:nth-child(2) {
  animation-delay: 0.2s;
}

.dot:nth-child(3) {
  animation-delay: 0.4s;
}

.dot:nth-child(4) {
  animation-delay: 0.6s;
}

.zoom-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background-color: rgba(0, 0, 0, 0.9);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: zoom-out;
}

.zoomed-image-container {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 90vw;
  max-height: 90vh;
}

.zoomed-image-container img {
  max-width: 90%;
  max-height: 90vh;
  object-fit: contain;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
  border-radius: 4px;
}

.zoom-out-hint {
  position: absolute;
  bottom: -40px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(255, 255, 255, 0.2);
  color: #ecf0f1;
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}

.zoom-enter-active,
.zoom-leave-active {
  transition: opacity 0.3s;
}
.zoom-enter,
.zoom-leave-to {
  opacity: 0;
}

@keyframes dot-flashing {
  0% {
    opacity: 0.2;
    transform: scale(0.8);
  }
  100% {
    opacity: 1;
    transform: scale(1.2);
  }
}
</style>
