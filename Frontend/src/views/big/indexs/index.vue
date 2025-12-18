<template>
  <div class="contents">
    <div class="contetn_left">
      <div class="pagetab"></div>

      <ItemWrap class="contetn_left-top contetn_lr-item" :title="$t('visualization.dataOverview')">
        <LeftTop :dataId="dataId" />
      </ItemWrap>

      <ItemWrap class="contetn_left-center contetn_lr-item" :title="$t('visualization.textLength')">
        <LeftCenter :dataId="dataId" />
      </ItemWrap>

      <ItemWrap class="contetn_left-bottom contetn_lr-item" :title="$t('visualization.wordCloud')" style="padding: 0 10px 16px 10px">
        <LeftBottom :dataId="dataId" />
      </ItemWrap>
    </div>

    <div class="contetn_center">
      <CenterMap :data="mapData" :dataId="dataId" @update:dataId="updateDataId" class="contetn_center_top" />

      <ItemWrap class="contetn_center-bottom" :title="$t('visualization.themeEvolution')">
        <CenterBottom :data-id="dataId" />
      </ItemWrap>
    </div>

    <div class="contetn_right">
      <ItemWrap class="contetn_left-bottom contetn_lr-item" :title="$t('visualization.training')">
        <RightTop :dataId="dataId" />
      </ItemWrap>

      <ItemWrap class="contetn_left-bottom contetn_lr-item" :title="$t('visualization.comparison')" style="padding: 0 10px 16px 10px">
        <RightCenter :dataId="dataId" />
      </ItemWrap>

      <ItemWrap class="contetn_left-bottom contetn_lr-item" :title="$t('visualization.userType')">
        <RightBottom :dataId="dataId" />
      </ItemWrap>
    </div>
  </div>
</template>

<script>
import LeftTop from "./left-top.vue";
import LeftCenter from "./left-center.vue";
import LeftBottom from "./left-bottom.vue";
import CenterMap from "./center-map.vue";
import CenterBottom from "./center-bottom.vue";
import RightTop from "./right-top.vue";
import RightCenter from "./right-center.vue";
import RightBottom from "./right-bottom.vue";
import data from "./data/data.json";

export default {
  components: {
    LeftTop,
    LeftCenter,
    LeftBottom,
    CenterMap,
    RightTop,
    RightCenter,
    RightBottom,
    CenterBottom,
  },
  data() {
    return {
      dataId: 1,
      mapData: null,
    };
  },
  created() {
    this.updateMapData();
  },
  methods: {
    updateMapData() {
      const categoryData = data.find((item) => item.categoryName === "热度分布");
      const maxIndex = categoryData.list.length - 1;
      const scaledIndex = Math.round((this.dataId / 100) * maxIndex);
      this.mapData = categoryData?.list?.[scaledIndex] || null;
    },
    updateDataId(newDataId) {
      this.dataId = newDataId;
    },
  },
  watch: {
    dataId: {
      handler() {
        this.updateMapData();
      },
      immediate: true,
    },
  },
};
</script>

<style lang="scss" scoped>
.contents {
  .contetn_left,
  .contetn_right {
    width: 540px;
    box-sizing: border-box;
  }
  .contetn_center {
    width: 720px;
  }
  .contetn_lr-item {
    height: 310px;
    padding: 0;
    box-sizing: border-box;
  }
  .contetn_center_top {
    width: 100%;
  }
  .contetn_center {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
  }
  .contetn_center-bottom {
    height: 315px;
  }
  .contetn_left,
  .contetn_right {
    display: flex;
    flex-direction: column;
    justify-content: space-around;
    position: relative;
  }
}
</style>
