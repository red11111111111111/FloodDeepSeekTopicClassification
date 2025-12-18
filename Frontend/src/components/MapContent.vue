<template>
  <div class="map-content">
    <!-- 地图容器 -->
    <div id="map-container" class="map-container"></div>
    <!-- 新求助信息提示窗口 -->
    <div v-if="newHelpPoints.length > 0" class="new-help-notification">
      <div v-for="(point, index) in newHelpPoints" :key="index" class="notification-item" :class="{ unread: !point.isViewed }">
        <p><strong>{{ $t('helpMessage.newRequest') }}</strong></p>
    <p><strong>{{ $t('helpMessage.location') }}</strong>{{ point.location }}</p>
    <p><strong>{{ $t('helpMessage.content') }}</strong>{{ point.cleaned_text }}</p>
    <button @click="viewNewPoint(point, index)">{{ $t('helpMessage.view') }}</button>
      </div>
    </div>
  </div>
</template>

<script>
import { AMapLoader } from "@/utils/amap";
import socket from "@/utils/socket";

export default {
  data() {
    return {
      map: null,
      infoWindow: null,
      markers: [],
      timer: null,
      previousPoints: new Set(),
      newHelpPoints: [],
      currentNewPointIndex: 0,
      viewedPoints: new Set(),
      retryCount: 0,  // 新增：重试计数器，防止无限延迟
      maxRetries: 3,  // 新增：最大重试次数
    };
  },
  mounted() {
    this.$nextTick(() => {
      const savedViewed = localStorage.getItem('viewedHelpPoints');
      if (savedViewed) {
        this.viewedPoints = new Set(JSON.parse(savedViewed));
        console.log('Loaded viewedPoints from LocalStorage:', Array.from(this.viewedPoints));
      } else {
        console.log('No viewedPoints in LocalStorage');
      }
      this.initMap();
      this.startPolling();

      // 监听 WebSocket 事件
      socket.on("help_locations", this.handleHelpData);
    });
  },
  beforeUnmount() {
    if (this.map) {
      this.map.destroy();
      this.map = null;
    }
    this.markers.forEach(marker => marker && marker.getExtData && marker.getExtData()?.infoWindow?.close());
    this.markers = [];
    if (this.timer) {
      clearInterval(this.timer);
    }
    socket.off("help_locations", this.handleHelpData);
  },
  methods: {
    initMap() {
      console.log('Initializing AMap...');
      const amapOptions = {
        key: "6f5894aff371b20019c78c2789dd5323",
        version: "1.4.5",
        plugins: [],
        AMapUI: {
          version: "1.0",
          plugins: ["control/BasicControl"],
        },
        Loca: {
          version: "1.3.2",
        },
      };

      AMapLoader(amapOptions)
        .then((AMap) => {
          console.log('AMap loaded successfully');
          const map = new AMap.Map("map-container", {
            zoom: 14,
            center: [113.625351, 34.746303],
            pitch: 60,
            cityName: "郑州",
            mapStyle: "amap://styles/c4676056f9bf08adcc707d7a7801a66d",
            viewMode: "3D",
          });

          map.addControl(new AMapUI.BasicControl.Zoom({ position: "rb", showZoomNum: true }));
          map.addControl(new AMapUI.BasicControl.LayerSwitcher({ position: "rt" }));

          this.map = map;

          this.infoWindow = new AMap.InfoWindow({
            offset: new AMap.Pixel(0, -30),
          });

          map.on('click', (e) => {
            const center = this.map.getCenter();
            const clickLngLat = e.lnglat;
            if (Math.abs(clickLngLat.lng - center.lng) < 0.01 && Math.abs(clickLngLat.lat - center.lat) < 0.01) {
              this.switchToNextNewPoint();
            }
          });

          console.log('Map initialized successfully');
          // 新增：AMap 加载完成后，手动触发一次数据获取，确保同步
          this.fetchHelpData();
        })
        .catch((err) => {
          console.error("高德地图加载失败：", err);
          this.$message.error("地图加载失败，请刷新页面重试");
        });
    },

    startPolling() {
      console.log('Starting polling for help data');
      // 新增：初始调用改为在 AMap 加载后触发，避免过早 emit
      // this.fetchHelpData();  // 移除这里，移到 initMap().then 中
      this.timer = setInterval(() => {
        this.fetchHelpData();
      }, 30000);
    },

    fetchHelpData() {
      try {
        console.log('Fetching help data via WebSocket');
        socket.emit("get_help_locations", {});
      } catch (err) {
        console.error("WebSocket 请求失败：", err);
        this.$message.error("获取求助数据失败，请检查网络");
      }
    },

    // 处理 WebSocket 响应（优化：检查 map 是否加载）
    handleHelpData(res) {
      // 新增：如果 map 未加载，延迟重试
      if (!this.map) {
        if (this.retryCount < this.maxRetries) {
          console.warn(`AMap 未加载，重试 ${this.retryCount + 1}/${this.maxRetries}`);
          this.retryCount++;
          setTimeout(() => this.handleHelpData(res), 500 * this.retryCount);  // 渐进延迟：500ms, 1000ms, 1500ms
          return;
        } else {
          console.error('AMap 加载超时，丢弃数据');
          this.$message.error("地图加载超时，请刷新页面");
          return;
        }
      }
      this.retryCount = 0;  // 重置计数器

      try {
        console.log('Response from WebSocket:', res);
        const data = res.data || [];
        if (data.length === 0) {
          console.warn('No valid geocoded data received');
          return;
        }

        const newPoints = [];
        data.forEach(item => {
          const pointId = `${item.location}_${item.created_at}`;
          if (!this.previousPoints.has(pointId) && item.lng && item.lat) {
            newPoints.push({ ...item, isViewed: this.viewedPoints.has(pointId) });
            this.previousPoints.add(pointId);
          }
        });

        this.newHelpPoints = [...this.newHelpPoints, ...newPoints];
        if (newPoints.length > 0) {
          console.log(`Found ${newPoints.length} new help points`);
          if (this.map && newPoints[0].lng && newPoints[0].lat) {
            this.map.setCenter([newPoints[0].lng, newPoints[0].lat]);
          }
          this.currentNewPointIndex = this.newHelpPoints.length - newPoints.length;
        }

        this.clearMarkers();
        data.forEach((item) => {
          // 新增：额外检查 map 存在
          if (!this.map) {
            console.warn('Map 未就绪，跳过标记添加');
            return;
          }
          if (!item.lng || !item.lat) {
            console.warn(`Skipping invalid coordinates for location: ${item.location}`);
            return;
          }
          console.log(`Adding marker for ${item.location} at [${item.lng}, ${item.lat}]`);
          const marker = new AMap.Marker({
            position: [item.lng, item.lat],
            map: this.map,
            animation: 'AMAP_ANIMATION_BOUNCE',
            extData: { id: `${item.location}_${item.created_at}` },
          });
          const content = `
            <div class="description">
              ${item.screen_name ? `<strong>Bloger：</strong>${item.screen_name}<br>` : ''}
              ${item.created_at ? `<strong>PublishDate：</strong>${item.created_at}<br>` : ''}
              ${item.location ? `<strong>Location：</strong>${item.location}<br><br>` : ''}
              ${item.cleaned_text ? `<strong>Content：</strong>${item.cleaned_text}<br>` : ''}
              <strong>Coordinates：</strong>${item.lng}, ${item.lat}
            </div>
          `;
          marker.content = content;
          marker.on("mouseover", () => {
            this.infoWindow.setContent(marker.content);
            this.infoWindow.open(this.map, marker.getPosition());
          });
          marker.on("mouseout", () => {
            this.infoWindow.close();
          });
          this.markers.push(marker);
        });
        console.log(`Added ${data.length} markers to map`);
      } catch (err) {
        console.error("处理求助数据失败：", err);
        this.$message.error("数据处理失败，请刷新页面");
      }
    },

    clearMarkers() {
      this.markers.forEach(marker => {
        if (this.map) {
          this.map.remove(marker);
        }
      });
      this.markers = [];
      console.log('Cleared all markers');
    },

    viewNewPoint(point, index) {
      if (point.lng && point.lat && this.map) {
        this.map.setCenter([point.lng, point.lat]);
        this.infoWindow.setContent(`
          <div class="description">
            ${point.screen_name ? `<strong>博主：</strong>${point.screen_name}<br>` : ''}
            ${point.created_at ? `<strong>发布时间：</strong>${point.created_at}<br>` : ''}
            ${point.location ? `<strong>位置：</strong>${point.location}<br><br>` : ''}
            ${point.cleaned_text ? `<strong>内容：</strong>${point.cleaned_text}<br>` : ''}
            <strong>坐标：</strong>${point.lng}, ${point.lat}
          </div>
        `);
        this.infoWindow.open(this.map, [point.lng, point.lat]);
        this.$set(this.newHelpPoints, index, { ...this.newHelpPoints[index], isViewed: true });
        const pointId = `${point.location}_${point.created_at}`;
        this.viewedPoints.add(pointId);
        localStorage.setItem('viewedHelpPoints', JSON.stringify(Array.from(this.viewedPoints)));
        console.log('Updated viewedPoints in LocalStorage:', Array.from(this.viewedPoints));
      }
    },

    switchToNextNewPoint() {
      if (this.newHelpPoints.length === 0) return;
      this.currentNewPointIndex = (this.currentNewPointIndex + 1) % this.newHelpPoints.length;
      const nextPoint = this.newHelpPoints[this.currentNewPointIndex];
      this.viewNewPoint(nextPoint, this.currentNewPointIndex);
      console.log(`Switched to new point: ${nextPoint.location}`);
    },
  },
};
</script>

<style lang="scss" scoped>
.map-content {
  width: 100%;
  position: relative;
}

.map-container {
  width: 100%;
  min-height: 1270px;
  position: relative;
}

.description {
  width: 400px;
  max-height: 300px;
  padding: 10px;
  background: rgba(34, 41, 98, 0.7);
  color: #fff;
  font-size: 12px;
  line-height: 1.6;
  overflow: auto;
  border-radius: 4px;
}

.new-help-notification {
  position: absolute;
  top: 20px;
  right: 20px;
  background: linear-gradient(135deg, #e6f7ff, #bae7ff);
  border: 2px solid #1890ff;
  border-radius: 12px;
  padding: 15px;
  max-width: 320px;
  height: 1200px;
  overflow-y: auto;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  z-index: 1000;
}

.notification-item {
  margin-bottom: 15px;
  padding: 12px;
  background: #ffffff;
  border-radius: 8px;
  position: relative;
  transition: all 0.3s ease;
}

.notification-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.notification-item.unread:before {
  content: '';
  position: absolute;
  left: -12px;
  top: 12px;
  width: 10px;
  height: 10px;
  background: red;
  border-radius: 50%;
  border: 2px solid #fff;
}

.notification-item p {
  margin: 6px 0;
  font-size: 14px;
  color: #333;
  font-family: 'Arial', sans-serif;
}

.notification-item strong {
  color: #1890ff;
}

.notification-item button {
  background: #1890ff;
  color: #fff;
  border: none;
  padding: 6px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 12px;
  margin-top: 8px;
  transition: background 0.3s ease;
}

.notification-item button:hover {
  background: #40a9ff;
}
</style>