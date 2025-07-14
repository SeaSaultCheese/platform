<template>
  <div class="home-container">
    <el-container>
      <el-header>
        <div class="header-content">
          <h2>Detection Home</h2>
          <div class="header-right">
            <el-button type="text" @click="goToProfile">Profile</el-button>
            <el-button type="text" @click="logout">Log out</el-button>
          </div>
        </div>
      </el-header>

      <el-aside width="200px">
        <el-menu :default-active="$route.path" @select="handleMenu">
          <el-menu-item index="/home">Defect Detection</el-menu-item>
          <el-menu-item index="/history">Detection Record</el-menu-item>
        </el-menu>
      </el-aside>
      
      <el-main>
        <el-dialog
          title="Detecting"
          :visible.sync="dialogTableVisible"
          :show-close="false"
          :close-on-press-escape="false"
          :append-to-body="true"
          :close-on-click-modal="false"
          :center="true"
        >
          <el-progress :percentage="percentage"></el-progress>
          <span slot="footer" class="dialog-footer">Please wait</span>
        </el-dialog>
        <div class="model-select-wrapper">
          <label class="model-select-label">Model Selection:</label>
          <el-select v-model="selectedModel" placeholder="Select Model">
<<<<<<< HEAD
            <el-option label="FASTSAM" value="FASTSAM"></el-option>
=======
            <el-option label="YOLOv8" value="YOLOv8"></el-option>
>>>>>>> 56a3681b5e259475872eb42ed8a074c9bff9e2e1
            <el-option label="YOLOv11" value="YOLOv11"></el-option>
          </el-select>
        </div>
        <div class="detection-container">
          <!-- <el-select v-model="selectedModel" placeholder="Select Model" style="width: 200px; margin-bottom: 20px;">
            <el-option label="YOLOv8" value="YOLOv8"></el-option>
            <el-option label="YOLOv11" value="YOLOv11"></el-option>
          </el-select> -->
          <div class="image-section">
            <el-card class="image-card">
              <div class="image-row"> 
              <div class="image-preview">
                <div v-loading="loading" element-loading-text="Uploading" element-loading-spinner="el-icon-loading">
                  <el-image
                    :src="originalImage"
                    class="preview-image"
                    :preview-src-list="originalImageList"
                  >
                    <div slot="error">
                      <div slot="placeholder" class="error">
                        <el-button
                          v-show="showUploadButton"
                          type="primary"
                          icon="el-icon-upload"
                          class="upload-button"
                          @click="triggerUpload"
                        >
                          Upload image
                          <input
                            ref="upload"
                            style="display: none"
                            name="file"
                            type="file"
                            @change="handleUpload"
                          />
                        </el-button>
                      </div>
                    </div>
                  </el-image>
                </div>
                <div class="image-info">
                  <span>Original Image</span>
                </div>
              </div>

              <div class="image-preview">
                <div v-loading="loading" element-loading-text="Processing" element-loading-spinner="el-icon-loading">
                  <el-image
                    :src="detectedImage"
                    class="preview-image"
                    :preview-src-list="detectedImageList"
                  >
                    <div slot="error">
                      <div slot="placeholder" class="error">{{ waitMessage }}</div>
                    </div>
                  </el-image>
                </div>
                <div class="image-info">
                  <span>Dectecion Result</span>
                </div>
              </div>
              </div>
            </el-card>
          </div>

          <div class="result-section">
            <el-card>
              <div slot="header" class="clearfix">
                <span>Defect list</span>
                
                <el-button
                  style="margin-left: 35px"
                  v-show="!showUploadButton"
                  type="primary"
                  icon="el-icon-upload"
                  class="upload-button"
                  @click="triggerUpload"
                >Reupload
                
                  <input
                    ref="upload2"
                    style="display: none"
                    name="file"
                    type="file"
                    @change="handleUpload"
                  />
                </el-button>
                <el-button
                  v-show="!showUploadButton"
                  type="success"
                  @click="calculateStats"
                >
                  Count
                </el-button>
              </div>
              <el-table
                v-if="stats.length > 0"
                :data="stats"
                class="mb-4"
                border
                stripe
                style="margin-bottom: 20px"
              >
                <el-table-column label="Tyoe" prop="class"></el-table-column>
                <el-table-column label="Total count" prop="count"></el-table-column>
                <el-table-column label="Average confidence level" prop="avg_confidence"></el-table-column>
              </el-table>
              <el-table
                :data="feature_list"
                height="390"
                border
                style="width: 750px; text-align: center"
                v-loading="loading"
                element-loading-text="Processing..."
                element-loading-spinner="el-icon-loading"
              >

                <el-table-column label="Type" width="250px">
                  <template slot-scope="scope">
                    <span>{{ scope.row.class }}</span>
                  </template>
                </el-table-column>

                <el-table-column label="Confidence level" width="250px">
                  <template slot-scope="scope">
                    <span>{{ scope.row.confidence.toFixed(3) }}</span>
                  </template>
                </el-table-column>

                <el-table-column label="Size (W x H)" width="250px">
                  <template slot-scope="scope">
                    <span>{{ scope.row.size.width }} x {{ scope.row.size.height }}</span>
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </div>
      </el-main>
    </el-container>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Home',
  data() {
    return {
      server_url: 'http://127.0.0.1:5003',
      originalImage: '',
      detectedImage: '',
      feature_list: [],
      stats: [],
      originalImageList: [],
      detectedImageList: [],
      detectionResults: [],
      loading: false,
      showUploadButton: true,
      waitMessage: 'Wait for uploading',
      percentage: 0,
      dialogTableVisible: false,
      currentView: 'Home',
      selectedModel: 'YOLOv11',  // 默认使用 YOLOv11
      headers: {
        Authorization: `Bearer ${localStorage.getItem('token')}`
      }
    }
  },
  mounted() {
    this.startSSE()
  },
  beforeDestroy() {
    this.stopSSE()
  },
  methods: {
    startSSE() {
      const token = localStorage.getItem('token')
      if (!token) {
        this.$message.error('Not logged in, please log in first')
        this.$router.push('/login')
        return
      }
      this.eventSource = new EventSource(`${this.server_url}/stream?token=${encodeURIComponent(token)}`)

      this.eventSource.onopen = () => {
        this.$message.success('Connected to real-time update service')
      },
      this.eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.status === 1 && data.image_url !== this.lastImagePath) {
          this.lastImagePath = data.image_url
          this.originalImage = data.image_url
          this.originalImageList = [data.image_url]
          this.detectedImage = data.draw_url
          this.detectedImageList = [data.draw_url]
          this.feature_list = data.defect_detection && data.defect_detection.detections || []
          this.loading = false
          this.showUploadButton = false
          this.waitMessage = ''
          this.percentage = 0
          this.dialogTableVisible = false

          this.$notify({
            title: 'New image received',
            message: 'Click the image to view the full size',
            duration: 0,
            type: 'success'
          })
        }
      }

      this.eventSource.onerror = async (error) => {
        try {
          const response = await fetch(sseUrl)
          if (response.status === 404) {
            this.$message.error('SSE endpoint not found (404). Check server configuration.')
          } else if (response.status === 401) {
            this.$message.error('Invalid or expired token. Please log in again.')
            this.$router.push('/login')
          } else {
            this.$message.error(`SSE connection failed: ${response.statusText}`)
          }
        } catch (fetchError) {
          this.$message.error('Cannot connect to the server.')
        }
        this.eventSource.close()
        setTimeout(() => this.startSSE(), 5000)
      }
    },
    stopSSE() {
      if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
      }
    },

    goToProfile() {
      this.$router.push('/profile')
    },
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      this.$router.push('/login')
    },
    triggerUpload() {
      if (this.showUploadButton) {
        this.$refs.upload.click()
      } else {
        this.$refs.upload2.click()
      }
    },
    getObjectURL(file) {
      let url = null
      if (window.createObjectURL !== undefined) {
        url = window.createObjectURL(file)
      } else if (window.URL !== undefined) {
        url = window.URL.createObjectURL(file)
      } else if (window.webkitURL !== undefined) {
        url = window.webkitURL.createObjectURL(file)
      }
      return url
    },
    handleUpload(e) {
      this.percentage = 0
      this.dialogTableVisible = true
      this.detectedImage = ''
      this.detectedImageList = []
      this.detectionResults = []
      this.waitMessage = ''
      this.loading = true
      this.showUploadButton = false

      const file = e.target.files[0]
      // 保存原始图片的预览，即使上传失败也保留
      this.originalImage = this.getObjectURL(file)
      this.originalImageList = [this.originalImage]
      
      const formData = new FormData()
      formData.append('file', file, file.name)
      formData.append('version', this.selectedModel) // 添加模型版本

      const timer = setInterval(() => {
        if (this.percentage + 33 < 99) {
          this.percentage += 33
        } else {
          this.percentage = 99
        }
      }, 30)

      const config = {
        headers: {
          'Content-Type': 'multipart/form-data',
          ...this.headers
        }
      }

      axios.post(`${this.server_url}/upload`, formData, config)
        .then(response => {
          this.percentage = 100
          clearInterval(timer)
          
          // 修改图片URL，使用后端提供的路径
          const originalImagePath = response.data.image_url.split('/').pop()
          const detectedImagePath = response.data.draw_url.split('/').pop()
          
          this.originalImage = `${this.server_url}/tmp/ct/${originalImagePath}`
          this.originalImageList = [this.originalImage]
          this.detectedImage = `${this.server_url}/tmp/draw/${detectedImagePath}`
          this.detectedImageList = [this.detectedImage]
          
          this.feature_list = response.data.defect_detection && response.data.defect_detection.detections || []


          this.loading = false
          this.dialogTableVisible = false
          this.percentage = 0
          
          this.$notify({
            title: 'Success',
            message: 'Click image for a larger view',
            duration: 0,
            type: 'success'
          })
        })
        .catch(error => {
          this.$message.error('Upload failed, please try again')
          this.loading = false
          this.dialogTableVisible = false
          // 上传失败时不清除原始图片预览
          this.waitMessage = 'Upload failed, please try again'
        })
    },
    calculateStats() {
      const grouped = {};

      this.feature_list.forEach(item => {
        const cls = item.class;
        const conf = item.confidence;

        if (!grouped[cls]) {
          grouped[cls] = { count: 0, total_conf: 0 };
        }

        grouped[cls].count += 1;
        grouped[cls].total_conf += conf;
      });

      // 构造统计结果表
      this.stats = Object.entries(grouped).map(([cls, { count, total_conf }]) => ({
        class: cls,
        count,
        avg_confidence: (total_conf / count).toFixed(2)
      }));
    },

  reset() {
    this.feature_list = [];
    this.stats = [];
    // 其他重置逻辑...
  },

  handleMenu(index) {
    this.$router.push(index)
  }
  }
}
</script>


<style scoped>
.home-container {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.el-header {
  background-color: #fff;
  box-shadow: 0 2px 4px rgba(56, 54, 54, 0.12);
  position: relative;
  z-index: 1;
  font-size: 20px;
}

.header-content h2 {
  color: #2d2c31; 
}

.header-right .el-button {
  font-size: 18px; 
}


.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-right {
  display: flex;
  gap: 20px;
  font-size: 16px;
}

.el-main {
  padding: 20px;
}

.detection-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.image-section {
  margin-bottom: 20px;
}

.image-section,
.result-section {
  max-width: 1100px;
  margin: 0 auto;
}

.image-card {
  padding: 20px;
}

.image-card,
.result-section .el-card {
  padding: 20px;
  box-sizing: border-box;
}

.image-row {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  max-width: 100%;
  overflow: hidden;
  gap: 40px; 
}

.image-preview {
  width: 400px;
  text-align: center;
  display: inline-block;
  margin: 0 20px;
  position: relative;
}

.preview-image {
  width: 400px;
  height: 400px;
  object-fit: contain;
  background: #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  font-size: 20px;
  font-family: "Arial"
}

.image-info {
  height: 30px;
  width: 400px;
  text-align: center;
  background-color: #21b3b9;
  line-height: 30px;
  color: white;
  margin-top: 10px;
  font-size: 20px;
  font-family: "Arial";
  letter-spacing: 4px;
}

.error {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
  text-align: center;
  font-size: 20px;
}

.upload-button {
  margin: 10px 0;
  font-size: 20px;
}

.result-section {
  margin-top: 20px;
}

.el-card {
  width: 100%;
}

.el-table {
  width: 100%;
}

.el-table-column {
  width: 33.33%;
}

.model-select-wrapper {
  margin-left: 300px;
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 40px;
}

.model-select-label {
  font-size: 20px;
  font-weight: bold;
  color: #333;
}
</style> 


<style>
body {
  overflow-x: hidden;
}
</style>