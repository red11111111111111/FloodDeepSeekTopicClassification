import MapLoader from '@amap/amap-jsapi-loader'

// 官方实例： https://lbs.amap.com/demo/amap-ui/demos/amapui-amaploader/amapui-amaploader1/

// "key": "",              // 申请好的Web端开发者Key，首次调用 load 时必填
// "version": "2.0",   // 指定要加载的 JSAPI 的版本，缺省时默认为 1.4.15
// "plugins": []           // 需要使用的的插件列表，如比例尺'AMap.Scale'等
// "AMapUI": {             // 是否加载 AMapUI，缺省不加载
//     "version": '1.1',   // AMapUI 缺省 1.1
//     "plugins":[],       // 需要加载的 AMapUI ui插件
// },
// "Loca":{                // 是否加载 Loca， 缺省不加载
//     "version": '1.3.2'  // Loca 版本，缺省 1.3.2
// }

export function AMapLoader(opts = {}) {
  const options = {
    key: '93b256aadeceda9c75bfd8f056d41cd0',
    version: '2.0',
    // 'AMap.Autocomplete', 'AMap.Geolocation', 'AMap.GeometryUtil', 'AMap.DistrictSearch'
    plugins: [],
    Loca: {
      version: '2.0.0'
    },
    ...opts
  }
  return new Promise((resolve, reject) => {
    MapLoader.load(options).then((AMap) => {
      resolve(AMap)
    }).catch(error => {
      reject(error)
    })
  })
}

var infoWin
var tableDom
/**
 * 封装便捷的撞题
 * @param {AMap.Map} map
 * @param {Array} event
 * @param {Object} content
 */
export function openInfoWin(map, event, content) {
  if (!infoWin) {
    infoWin = new AMap.InfoWindow({
      autoMove: false,
      isCustom: true, //使用自定义窗体
      offset: new AMap.Pixel(130, 100)
    })
  }

  var x = event.offsetX
  var y = event.offsetY
  var lngLat = map.containerToLngLat(new AMap.Pixel(x, y))

  if (!tableDom) {
    const infoDom = document.createElement('div')
    infoDom.className = 'info-window'
    tableDom = document.createElement('table')
    infoDom.appendChild(tableDom)
    infoWin.setContent(infoDom)
  }

  var trStr = ''
  for (var name in content) {
    var val = content[name]
    trStr += `<tr>
      <td class="label">${name}</td>
      <td>&nbsp;</td>
      <td class="content">${val}</td>
    </tr>`
  }

  tableDom.innerHTML = trStr
  infoWin.open(map, lngLat)
}

export function closeInfoWin() {
  if (infoWin) {
    infoWin.close()
  }
}

/**
 * 获取多边形的中心点 [lng, lat]
 * @param {array} data  [[113.769953613282, 34.866593967014],[113.78726264106, 34.86249186198]]
 * @returns {object} {lng:'经度',lat:'纬度'}
 */
export function getCenterPoint(data) {
  var lng = 0.0, lat = 0.0
  for (var i = 0; i < data.length; i++) {
    // AMap.Util.isEmpty 判断一个对象是都为空
    if (AMap.Util.isEmpty(data[i])) { continue }
    lng = lng + parseFloat(data[i][0])
    lat = lat + parseFloat(data[i][1])
  }
  lng = lng / data.length
  lat = lat / data.length
  return [lng, lat]
}
