<template>
    <div class="login-container">
      <el-card class="login-card">
        <div slot="header" class="clearfix">
          <span>User login</span>
        </div>
        <el-form :model="loginForm" :rules="rules" ref="loginForm" label-width="80px">
          <el-form-item label="Username" prop="username">
            <el-input v-model="loginForm.username" placeholder="Enter username"></el-input>
          </el-form-item>
          <el-form-item label="Password" prop="password">
            <el-input type="password" v-model="loginForm.password" placeholder="Enter password"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleLogin" :loading="loading">Login</el-button>
            <el-button @click="$router.push('/register')">Register</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  export default {
    name: 'Login',
    data() {
      return {
        loginForm: {
          username: '',
          password: ''
        },
        loading: false,
        rules: {
          username: [
            { required: true, message: 'Please enter username', trigger: 'blur' }
          ],
          password: [
            { required: true, message: 'Please enter password', trigger: 'blur' }
          ]
        }
      }
    },
    methods: {
      handleLogin() {
        this.$refs.loginForm.validate(async (valid) => {
          if (valid) {
            this.loading = true
            try {
              const response = await axios.post('http://127.0.0.1:5003/api/login', this.loginForm)
              if (response.data.status === 1) {
                // 保存token和用户信息
                localStorage.setItem('token', response.data.token)
                localStorage.setItem('user', JSON.stringify(response.data.user))
                this.$message.success('Success')
                
                // 获取重定向地址或默认跳转到主页
                const redirectPath = this.$route.query.redirect || '/home'
                this.$router.replace(redirectPath)
              } else {
                this.$message.error(response.data.message)
              }
            } catch (error) {
              this.$message.error('Login failed, please try again')
              console.error('Login error:', error)
            } finally {
              this.loading = false
            }
          }
        })
      }
    }
  }
  </script>
  
  <style scoped>
  .login-container {
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #f5f7fa;
  }
  
  .login-card {
    width: 400px;
  }
  
  .el-button {
    margin-right: 15px;
  }
  </style>