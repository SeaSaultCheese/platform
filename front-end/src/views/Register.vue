<template>
    <div class="register-container">
      <el-card class="register-card">
        <div slot="header" class="clearfix">
          <span>User Register</span>
        </div>
        <el-form :model="registerForm" :rules="rules" ref="registerForm" label-width="160px">
          <el-form-item label="Usename" prop="username">
            <el-input v-model="registerForm.username" placeholder="Please enter username"></el-input>
          </el-form-item>
          <el-form-item label="Password" prop="password">
            <el-input type="password" v-model="registerForm.password" placeholder="Please enter password"></el-input>
          </el-form-item>
          <el-form-item label="Confirm Password" prop="confirmPassword">
            <el-input type="password" v-model="registerForm.confirmPassword" placeholder="Please confirm password"></el-input>
          </el-form-item>
          <el-form-item label="email" prop="email">
            <el-input v-model="registerForm.email" placeholder="Please enter email"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" @click="handleRegister" :loading="loading">Register</el-button>
            <el-button @click="$router.push('/login')">Back to login</el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </div>
  </template>
  
  <script>
  import axios from 'axios'
  
  export default {
    name: 'Register',
    data() {
      // 自定义验证规则
      const validatePass2 = (rule, value, callback) => {
        if (value !== this.registerForm.password) {
          callback(new Error('Inconsistent passwords entered twice!'))
        } else {
          callback()
        }
      }
      return {
        registerForm: {
          username: '',
          password: '',
          confirmPassword: '',
          email: ''
        },
        loading: false,
        rules: {
          username: [
            { required: true, message: 'Please enter username', trigger: 'blur' },
            { min: 3, max: 20, message: '3 to 20 characters in length', trigger: 'blur' }
          ],
          password: [
            { required: true, message: 'Please enter password', trigger: 'blur' },
            { min: 6, message: 'Password length cannot be less than 6 digits', trigger: 'blur' }
          ],
          confirmPassword: [
            { required: true, message: 'Please enter your password again', trigger: 'blur' },
            { validator: validatePass2, trigger: 'blur' }
          ],
          email: [
            { required: true, message: 'Please enter your e-mail address', trigger: 'blur' },
            { type: 'email', message: 'Please enter the correct e-mail address', trigger: 'blur' }
          ]
        }
      }
    },
    methods: {
      handleRegister() {
        this.$refs.registerForm.validate(async (valid) => {
          if (valid) {
            this.loading = true
            try {
              const { confirmPassword, ...registerData } = this.registerForm
              const response = await axios.post('http://127.0.0.1:5003/api/register', registerData)
              if (response.data.status === 1) {
                this.$message.success('Successful registration')
                this.$router.push('/login')
              } else {
                this.$message.error(response.data.message)
              }
            } catch (error) {
              this.$message.error('Registration failed, please try again')
              console.error('Register error:', error)
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
  .register-container {
    height: 100vh;
    display: flex;
    justify-content: center;
    align-items: center;
    background-color: #f5f7fa;
  }
  
  .register-card {
    width: 600px;
  }
  
  .el-button {
    margin-right: 15px;
  }
  </style>