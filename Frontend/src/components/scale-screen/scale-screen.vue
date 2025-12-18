<!--
 * @Author: wei
 * @description: 大屏自适应容器组件
 * @LastEditTime: 2022-09-09 16:42:40
-->
<template>
  <!-- <section class="screen-box" :style="boxStyle"> -->
  <div class="screen-wrapper" ref="screenWrapper" :style="wrapperStyle">
    <slot></slot>
  </div>
  <!-- </section> -->
</template>
<script>
function debounce(fn, delay) {
  let timer = null;
  return function (...args) {
    timer = setTimeout(
      () => {
        typeof fn === "function" && fn.apply(null, args);
        clearTimeout(timer);
      },
      delay > 0 ? delay : 100
    );
  };
}

export default {
  name: "VScaleScreen",
  props: {
    width: {
      type: [String, Number],
      default: 1920,
    },
    height: {
      type: [String, Number],
      default: 1080,
    },
    fullScreen: {
      type: Boolean,
      default: false,
    },
    autoScale: {
      type: [Object, Boolean],
      default: true,
    },
    selfAdaption: {
      type: Boolean,
      default: true,
    },
    delay: {
      type: Number,
      default: 500,
    },
    boxStyle: {
      type: Object,
      default: () => ({}),
    },
    wrapperStyle: {
      type: Object,
      default: () => ({}),
    },
  },
  data() {
    return {
      currentWidth: 0,
      currentHeight: 0,
      originalWidth: 0,
      originalHeight: 0,
      onResize: null,
      observer: null,
    };
  },
  watch: {
    selfAdaption(val) {
      if (val) {
        this.resize();
        this.addListener();
      } else {
        this.clearListener();
        this.clearStyle();
      }
    },
  },
  computed: {
    screenWrapper() {
      return this.$refs["screenWrapper"];
    },
  },
  methods: {
    initSize() {
      return new Promise((resolve, reject) => {
        this.screenWrapper.parentNode.style.overflow = "hidden";
        this.screenWrapper.parentNode.scrollLeft = 0;
        this.screenWrapper.parentNode.scrollTop = 0;

        this.$nextTick(() => {
          if (this.width && this.height) {
            this.currentWidth = this.width;
            this.currentHeight = this.height;
          } else {
            this.currentWidth = this.screenWrapper.clientWidth;
            this.currentHeight = this.screenWrapper.clientHeight;
          }

          if (!this.originalHeight || !this.originalWidth) {
            this.originalWidth = window.screen.width;
            this.originalHeight = window.screen.height;
          }
          resolve();
        });
      });
    },
    updateSize() {
      if (this.currentWidth && this.currentHeight) {
        this.screenWrapper.style.width = `${this.currentWidth}px`;
        this.screenWrapper.style.height = `${this.currentHeight}px`;
      } else {
        this.screenWrapper.style.width = `${this.originalWidth}px`;
        this.screenWrapper.style.height = `${this.originalHeight}px`;
      }
    },
    handleAutoScale(scale) {
      if (!this.autoScale) return;
      const screenWrapper = this.screenWrapper;
      screenWrapper.style.transform = `scale(${scale}, ${scale})`;
      // 移除 margin 居中逻辑，让内容贴合父容器
      screenWrapper.style.margin = "0";
    },
    updateScale() {
      const screenWrapper = this.screenWrapper;
      const currentWidth = document.documentElement.clientWidth;
      const currentHeight = document.documentElement.clientHeight;
      const realWidth = this.currentWidth || this.originalWidth;
      const realHeight = this.currentHeight || this.originalHeight;

      const widthScale = currentWidth / realWidth;
      const heightScale = currentHeight / realHeight;

      if (this.fullScreen) {
        screenWrapper.style.transform = `scale(${widthScale}, ${heightScale})`;
        screenWrapper.style.transformOrigin = "top left";
        return;
      }

      const scale = Math.min(widthScale, heightScale);
      this.handleAutoScale(scale);

      // 动态调整父容器的高度以适应缩放后的内容
      const scaledHeight = realHeight * scale;
      screenWrapper.parentNode.style.height = `${scaledHeight}px`;
      screenWrapper.parentNode.style.overflowY = "auto"; // 确保父容器可以滚动
    },
    initMutationObserver() {
      const screenWrapper = this.screenWrapper;
      const observer = (this.observer = new MutationObserver(() => {
        this.onResize();
      }));

      observer.observe(screenWrapper, {
        attributes: true,
        attributeFilter: ["style"],
        attributeOldValue: true,
      });
    },
    clearListener() {
      window.removeEventListener("resize", this.onResize);
    },
    addListener() {
      window.addEventListener("resize", this.onResize);
    },
    clearStyle() {
      const screenWrapper = this.screenWrapper;
      screenWrapper.parentNode.style.overflow = "auto";
      screenWrapper.style = "";
    },
    async resize() {
      if (!this.selfAdaption) {
        return;
      }
      await this.initSize();
      this.updateSize();
      this.updateScale();
    },
  },
  mounted() {
    this.onResize = debounce(() => {
      this.resize();
    }, this.delay);
    this.$nextTick(() => {
      if (this.selfAdaption) {
        this.resize();
        this.addListener();
      }
    });
  },
  beforeDestroy() {
    this.clearListener();
  },
};
</script>

<style scoped>
.screen-wrapper {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
  transition-duration: 500ms;
  position: relative;
  overflow: visible; /* 改为 visible，避免内容被截断 */
  z-index: 100;
  transform-origin: left top;
}
</style>
