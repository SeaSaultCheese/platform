<template>
  <div class="profile-container">
    <el-card class="profile-card">
      <div slot="header" class="clearfix">
        <span>Personal profile</span>
        <el-button style="float: right; padding: 3px 0" type="text" @click="goToHome">Back to detect</el-button>
      </div>
      <div class="profile-content">
        <el-avatar :size="100" :src="userAvatar"></el-avatar>
        <h2>{{ userInfo.username }}</h2>
        <p>Email：{{ userInfo.email }}</p>
        <p>Registration Time：{{ formatDate(userInfo.created_at) }}</p>
        <el-button type="primary" @click="goToHome">Back to detect</el-button>
        <el-button type="danger" @click="logout">Log out</el-button>
      </div>
    </el-card>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Profile',
  data() {
    return {
      server_url: 'http://127.0.0.1:5003',
      userInfo: {
        username: '',
        email: '',
        create_time: ''
      },
      userAvatar: 'https://cube.elemecdn.com/3/7c/3ea6beec64369c2642b92c6726f1epng.png'
    }
  },
  created() {
    this.getUserInfo()
  },
  methods: {
    goToHome() {
      this.$router.push('/home')
    },
    logout() {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      this.$router.push('/login')
    },
    async getUserInfo() {
      try {
        const response = await axios.get(`${this.server_url}/api/user/info`, {
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`
          }
        })
        if (response.data.status === 1) {
          this.userInfo = response.data.user
        } else {
          this.$message.error(response.data.message || 'Failed to get user information')
        }
      } catch (error) {
        console.error('Get user info error:', error)
        this.$message.error('Failed to get user information')
      }
    },
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.profile-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f5f7fa;
}

.profile-card {
  width: 400px;
}

.profile-content {
  text-align: center;
  padding: 20px 0;
}

.profile-content h2 {
  margin: 20px 0;
}

.profile-content p {
  color: #666;
  margin-bottom: 20px;
}

.el-button {
  margin: 10px;
}
</style> 