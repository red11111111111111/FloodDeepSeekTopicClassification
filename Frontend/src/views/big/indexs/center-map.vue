<template>
  <div class="centermap">
    <div class="maptitle">
      <div class="zuo"></div>
      <span class="titletext">{{ $t("centermap.title") }}</span>
      <div class="you"></div>
    </div>
    <div class="mapwrap">
      <dv-border-box-13>
        <div class="quanguo" @click="getData('china')" v-if="code !== 'china'">
          {{ $t("centermap.china") }}
        </div>
        <div class="switchButton" v-if="code == '410000'" @click="switchView">
          {{ switchButtonLabel }}
        </div>
        <Echart id="CenterMap" :options="options" ref="CenterMap" />
      </dv-border-box-13>
    </div>
    <el-slider
      v-model="localDataId"
      :min="0"
      :max="100"
      @input="updateDataId"
    />
  </div>
</template>

<script>
import xzqCode from "../../../utils/map/xzqCode";
import { GETNOBASE } from "api";
import * as echarts from "echarts";
import { chinaList, henanList } from "./data/type";

export default {
  props: {
    data: { type: Object, default: () => ({}) },
    dataId: { type: Number, default: 1 },
  },
  data() {
    return {
      options: {},
      code: "china",
      echartBindClick: false,
      isHeNan: false,
      henanViewType: "heat",
      localDataId: 0,
    };
  },
  computed: {
    // 热力图可视化映射（等级1-8）
    heatVisualMap() {
      return {
        left: 20,
        bottom: 20,
        pieces: [
          { gte: 8, lte: 8, label: this.$t("centermap.level8") },
          { gte: 7, lte: 7, label: this.$t("centermap.level7") },
          { gte: 6, lte: 6, label: this.$t("centermap.level6") },
          { gte: 5, lte: 5, label: this.$t("centermap.level5") },
          { gte: 4, lte: 4, label: this.$t("centermap.level4") },
          { gte: 3, lte: 3, label: this.$t("centermap.level3") },
          { gte: 2, lte: 2, label: this.$t("centermap.level2") },
          { lte: 1, label: this.$t("centermap.level1") },
        ],
        inRange: {
          color: [
            "#c3d7df",
            "#5cb3cc",
            "#8abcd1",
            "#66a9c9",
            "#2f90b9",
            "#1781b5",
          ],
        },
        textStyle: { color: "#fff" },
      };
    },
    // 降雨可视化映射
    rainfallVisualMap() {
      return {
        left: 20,
        bottom: 20,
        pieces: [
          { gte: 139.9, label: this.$t("centermap.rainLevel7") },
          { gte: 69.9, lte: 139.9, label: this.$t("centermap.rainLevel6") },
          { gte: 29.9, lte: 69.9, label: this.$t("centermap.rainLevel5") },
          { gte: 14.9, lte: 29.9, label: this.$t("centermap.rainLevel4") },
          { gte: 4.9, lte: 14.9, label: this.$t("centermap.rainLevel3") },
          { gte: 0.5, lte: 4.9, label: this.$t("centermap.rainLevel2") },
          { lte: 0.5, label: this.$t("centermap.rainLevel1") },
        ],
        inRange: {
          color: [
            "#8BC34A",
            "#FFEB3B",
            "#FF9800",
            "#FF5722",
            "#F44336",
            "#D32F2F",
            "#9C27B0",
          ],
        },
        textStyle: { color: "#fff" },
      };
    },
    // 当前使用的 visualMap
    currentVisualMap() {
      if (this.code === "china") {
        return this.heatVisualMap;
      } else if (this.code === "410000") {
        return this.henanViewType === "heat"
          ? this.heatVisualMap
          : this.rainfallVisualMap;
      }
      return this.heatVisualMap;
    },
    // 切换按钮文字
    switchButtonLabel() {
      return this.henanViewType === "heat"
        ? this.$t("centermap.switchToRain")
        : this.$t("centermap.switchToHeat");
    },
  },
  mounted() {
    this.getData("china");
    this.$nextTick(() => {
      this.updateDataId(this.localDataId);
    });
  },
  methods: {
    getData(code) {
      let d = [],
        key = "",
        arr = [];
      this.isHeNan = false;
      if (code === "china") {
        key = "level-china";
        arr = chinaList;
      } else if (code === "410000") {
        this.isHeNan = true;
        if (this.henanViewType === "heat") {
          key = "level-HN-redu";
        } else {
          key = "henan-rainfall";
        }
        arr = henanList;
      }

      if (this.data && this.data[key]) {
        d = arr.map((item, index) => ({
          name: item,
          value: this.data[key][index],
        }));
      }
      this.getGeojson(code, d);
      this.$nextTick(() => {
        this.mapclick();
      });
    },
    async getGeojson(name, mydata) {
      this.code = name;
      let geoname = name;
      let mapjson = echarts.getMap(name);
      if (mapjson) {
        mapjson = mapjson.geoJSON;
      } else {
        mapjson = await GETNOBASE(`./map-geojson/${geoname}.json`).then(
          (res) => res
        );
        echarts.registerMap(name, mapjson);
      }

      let cityCenter = {};
      mapjson.features.forEach((item) => {
        cityCenter[item.properties.name] =
          item.properties.centroid || item.properties.center;
      });

      let newData = [];
      mydata.forEach((item) => {
        if (cityCenter[item.name]) {
          newData.push({
            name: item.name,
            value: cityCenter[item.name].concat(item.value),
          });
        }
      });

      this.init(name, mydata, newData);
    },
    init(name, data, data2) {
      const top = 45;
      const zoom = 1.05;

      // 翻译省份名称的辅助函数
      const translateProvince = (name) => {
        return this.$t(`Chinamap.province.${name}`) || name;
      };

      const option = {
        backgroundColor: "rgba(0,0,0,0)",
        tooltip: { show: false },
        legend: { show: false },
        visualMap: this.currentVisualMap,
        geo: {
          map: name,
          roam: false,
          selectedMode: false,
          zoom: zoom,
          top: top,
          show: false,
        },
        series: [
          {
            name: "MAP",
            type: "map",
            map: name,
            data: data,
            selectedMode: false,
            zoom: zoom,
            geoIndex: 1,
            top: top,
            tooltip: {
              show: true,
              formatter: (params) => {
                if (params.data) {
                  const name = translateProvince(params.name);
                  return `${name}：${params.data.value}`;
                }
                return translateProvince(params.name);
              },
              backgroundColor: "rgba(0,0,0,.6)",
              borderColor: "rgba(147, 235, 248, .8)",
              textStyle: { color: "#FFF" },
            },
            label: {
              show: false,
              color: "#000",
              formatter: (val) => {
                if (val.data !== undefined) {
                  return translateProvince(val.name);
                }
                return "";
              },
            },
            emphasis: {
              label: { show: false },
              itemStyle: { areaColor: "#389BB7", borderWidth: 1 },
            },
            itemStyle: {
              borderColor: "rgba(147, 235, 248, .8)",
              borderWidth: 1,
              areaColor: {
                type: "radial",
                x: 0.5,
                y: 0.5,
                r: 0.8,
                colorStops: [
                  { offset: 0, color: "rgba(147, 235, 248, 0)" },
                  { offset: 1, color: "rgba(147, 235, 248, .2)" },
                ],
                globalCoord: false,
              },
              shadowColor: "rgba(128, 217, 248, .3)",
              shadowOffsetX: -2,
              shadowOffsetY: 2,
              shadowBlur: 10,
            },
          },
          {
            data: data2,
            type: "effectScatter",
            coordinateSystem: "geo",
            symbolSize: () => 4,
            showEffectOn: "render",
            rippleEffect: {
              scale: 6,
              color: "rgba(255,255,255, 1)",
              brushType: "fill",
            },
            tooltip: {
              show: true,
              formatter: (params) => {
                if (params.data) {
                  const name = translateProvince(params.name);
                  return `${name}：${params.data.value[2]}`;
                }
                return translateProvince(params.name);
              },
              backgroundColor: "rgba(0,0,0,.6)",
              borderColor: "rgba(147, 235, 248, .8)",
              textStyle: { color: "#FFF" },
            },
            label: {
              formatter: (param) => {
                return translateProvince(param.name);
              },
              fontSize: 11,
              offset: [0, 2],
              position: "bottom",
              textBorderColor: "#fff",
              textShadowColor: "#000",
              textShadowBlur: 10,
              textBorderWidth: 0,
              color: "#FFF",
              show: true,
            },
            itemStyle: {
              color: "rgba(255,255,255,1)",
              borderColor: "rgba(255,255,255,2)",
              borderWidth: 4,
              shadowColor: "#000",
              shadowBlur: 10,
            },
          },
        ],
      };

      this.options = option;
      this.$nextTick(() => this.mapclick());
    },
    switchView() {
      this.henanViewType = this.henanViewType === "heat" ? "rainfall" : "heat";
      this.getData(this.code);
    },
    message(text) {
      this.$Message({ text: text, type: "warning" });
    },
    mapclick() {
      if (this.echartBindClick) return;
      if (!this.$refs.CenterMap || !this.$refs.CenterMap.chart) {
        console.warn("Chart instance not ready");
        return;
      }
      this.$refs.CenterMap.chart.on("click", (params) => {
        // 注意：GeoJSON 中的 name 是中文，所以仍用中文判断
        if (params.name !== "河南省") return;
        let xzqData = xzqCode[params.name];
        if (xzqData) {
          this.getData(xzqData.adcode);
        } else {
          this.message(this.$t("map.noData"));
        }
      });
      this.echartBindClick = true;
    },
    updateDataId(value) {
      const mappedDataId = Math.round((value / 100) * 100) + 1;
      console.log("滑动条值:", value, "映射dataId:", mappedDataId);
      this.$emit("update:dataId", mappedDataId);
    },
  },
  watch: {
  // 👇 新增：监听语言切换，实时更新地图中的文本（省名、等级等）
  '$i18n.locale': {
    handler() {
      this.$nextTick(() => {
        this.getData(this.code); // 重新加载当前地图数据，触发重新渲染
      });
    },
    immediate: false
  },

  // 👇 原有的 data 监听（保持不变）
  data: {
    handler() {
      this.getData(this.isHeNan ? "410000" : "china");
    },
    deep: true
  }
}
};
</script>

<style lang="scss" scoped>
.centermap {
  margin-bottom: -50px;
  .maptitle {
    height: 60px;
    display: flex;
    justify-content: center;
    padding-top: 10px;
    box-sizing: border-box;
    .titletext {
      font-size: 24px;
      font-weight: 900;
      letter-spacing: 6px;
      background: linear-gradient(
        92deg,
        #0072ff 0%,
        #00eaff 48.8525390625%,
        #01aaff 100%
      );
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin: 0 10px;
    }
    .zuo,
    .you {
      background-size: 100% 100%;
      width: 29px;
      height: 20px;
      margin-top: 8px;
    }
    .zuo {
      background: url("../../../assets/img/xiezuo.png") no-repeat;
    }
    .you {
      background: url("../../../assets/img/xieyou.png") no-repeat;
    }
  }
  .mapwrap {
    height: 548px;
    width: 100%;
    box-sizing: border-box;
    position: relative;
    :deep(.dv-border-box-13) {
      width: 100%;
      height: 100%;
    }
    .quanguo {
      position: absolute;
      right: 20px;
      top: -46px;
      width: 80px;
      height: 28px;
      border: 1px solid #00eded;
      border-radius: 10px;
      color: #00f7f6;
      text-align: center;
      line-height: 26px;
      letter-spacing: 6px;
      cursor: pointer;
      box-shadow: 0 2px 4px rgba(0, 237, 237, 0.5),
        0 0 6px rgba(0, 237, 237, 0.4);
      z-index: 10;
    }
    .switchButton {
      position: absolute;
      left: 20px;
      top: -46px;
      width: 120px;
      height: 28px;
      border: 1px solid #00eded;
      border-radius: 10px;
      color: #00f7f6;
      text-align: center;
      line-height: 26px;
      letter-spacing: 6px;
      cursor: pointer;
      box-shadow: 0 2px 4px rgb(0 237 237 / 50%), 0 0 6px rgb(0 237 237 / 40%);
      z-index: 10;
    }
  }
}
</style>
