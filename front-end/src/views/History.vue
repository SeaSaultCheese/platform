<template>
    <el-card>
      <div class="home-container">
        <el-container>
          <el-header>
            <div class="header-content">
              <h2>Defection Record</h2>
              <div class="header-right">
                <el-button type="primary" @click="goToHome">Back to detection</el-button>
              </div>
            </div>
          </el-header>
      </el-container>
      </div>
      <el-table :data="records" style="width: 100%">
        <el-table-column label="Time" prop="created_at" width="180"/>
        <el-table-column label="Original Image">
          <template slot-scope="scope">
            <el-image :src="scope.row.original_image_url" style="height: 100px"/>
          </template>
        </el-table-column>
        <el-table-column label="Annotated Image">
          <template slot-scope="scope">
            <el-image :src="scope.row.detected_image_url" style="height: 100px"/>
          </template>
        </el-table-column>
        <el-table-column label="Model" prop="model_version" width="100"/>
        <el-table-column label="Defect info">
          <template slot-scope="scope">
            <el-button size="mini" @click="viewDetails(scope.row)">View Details</el-button>
          </template>
        </el-table-column>
        <el-table-column label="Action" width="120">
          <template slot-scope="scope">
          <el-button size="mini" type="danger" @click="deleteRecord(scope.row.id)">Delete</el-button>
        </template>
        </el-table-column>

      </el-table>
      <el-pagination
        background
        layout="prev, pager, next"
        :total="total"
        :page-size="10"
        :current-page.sync="page"
        @current-change="fetchRecords"
      />
  
      <el-dialog title="Detection info" :visible.sync="dialogVisible" width="600px">
        <el-table-column label="No. of defects" prop="total_defects" width="100"/>
        <el-table-column label="Type">
          <template slot-scope="scope">
            <el-tag
              v-for="(type, index) in scope.row.defect_types"
              :key="index"
              type="info"
              size="small"
              style="margin-right: 4px"
            >{{ type }}</el-tag>
          </template>
        </el-table-column>
        <el-table :data="selectedData">
          <el-table-column label="Type" prop="class"/>
          <el-table-column label="Confidence Level" prop="confidence"/>
          <el-table-column label="Size" :formatter="sizeFormatter"/>
        </el-table>
      </el-dialog>
    </el-card>
  </template>
  
  <script>
  import axios from 'axios'
  
  export default {
    data() {
      return {
        records: [],
        dialogVisible: false,
        selectedData: [],
        page: 1,
        perPage: 10,
        total: 0
      }
    },
    mounted() {
    this.fetchRecords()
    },
    methods: {
      viewDetails(row) {
        this.selectedData = row.detection_data
        this.dialogVisible = true
      },
      sizeFormatter(row) {
        return `${row.size.width} x ${row.size.height}`
      },
      goToHome() {
        this.$router.push('/home')
      },
      fetchRecords(page = 1) {
        this.page = page
        axios.get('http://127.0.0.1:5003/api/history', {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          },
          params: {
            page: this.page,
            per_page: this.perPage
          }
        }).then(res => {
          if (res.data.status === 1) {
            this.records = res.data.records
            this.total = res.data.pagination.total
          } else {
            this.$message.error('Failed to get history')
          }
        }).catch(err => {
          console.error('Request failed:', err)
          this.$message.error('Request failed')
        })
      },
      deleteRecord(record_id) {
        this.$confirm('Are you sure to delete this record?', 'Warning', {
          confirmButtonText: 'Yes',
          cancelButtonText: 'Cancel',
          type: 'warning'
        }).then(() => {
          axios.post('http://127.0.0.1:5003/api/history/delete', {
            record_id
          }, {
            headers: {
              Authorization: `Bearer ${localStorage.getItem('token')}`
            }
          }).then(res => {
            if (res.data.status === 1) {
              this.$message.success('Deleted successfully')
              this.fetchRecords(this.page)
            } else {
              this.$message.error('Failed to delete')
            }
          })
        }).catch(() => {})
      }
    }



  }
  
  </script>
  
<style scoped>
.home-container {
  min-height: 18vh;
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
</style>