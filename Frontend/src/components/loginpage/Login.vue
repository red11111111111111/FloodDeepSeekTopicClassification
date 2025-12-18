<template>
  <div class="login-container">
    <div class="login-background"></div>
    <!-- Remove LanguageSwitch component -->
    <el-card class="login-card animated fadeIn">
      <h2 class="login-title">{{ $t("loginPage.title") }}</h2>
      <el-form
        :model="loginForm"
        :rules="loginRules"
        ref="loginForm"
        label-width="80px"
        @submit.native.prevent="handleLogin"
      >
        <el-form-item :label="$t('loginPage.username')" prop="username">
          <el-input
            v-model="loginForm.username"
            :placeholder="$t('loginPage.usernamePlaceholder')"
            prefix-icon="el-icon-user"
          ></el-input>
        </el-form-item>
        <el-form-item :label="$t('loginPage.password')" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            :placeholder="$t('loginPage.passwordPlaceholder')"
            prefix-icon="el-icon-lock"
          ></el-input>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            @click="handleLogin"
            :loading="loading"
            class="login-button"
          >
            {{ $t("loginPage.loginButton") }}
          </el-button>
          <el-button
            @click="$router.push('/register')"
            class="register-link-button"
          >
            {{ $t("loginPage.goToRegister") }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script>
import axios from "axios";
// Remove LanguageSwitch import
export default {
  name: "Login",
  components: {
    // Remove LanguageSwitch from components
  },
  data() {
    return {
      loginForm: {
        username: "",
        password: "",
      },
      loginRules: {
        username: [
          {
            required: true,
            message: this.$t("loginPage.usernamePlaceholder"),
            trigger: "blur",
          },
        ],
        password: [
          {
            required: true,
            message: this.$t("loginPage.passwordPlaceholder"),
            trigger: "blur",
          },
          {
            min: 6,
            message: this.$t("loginPage.passwordNotMatch"),
            trigger: "blur",
          },
        ],
      },
      loading: false,
    };
  },
  methods: {
    handleLogin() {
      this.$refs.loginForm.validate(async (valid) => {
        if (valid) {
          this.loading = true;
          console.log("Sending  login request:", {
            username: this.loginForm.username,
            password: this.loginForm.password,
          });
          try {
            const response = await axios.post(
              "http://localhost:5004/api/login",
              {
                username: this.loginForm.username,
                password: this.loginForm.password,
              }
            );
            console.log("Login  response:", response);
            if (response.status === 200 && response.data.token) {
              localStorage.setItem("token", response.data.token);
              localStorage.setItem("username", response.data.username);
              this.$message.success(this.$t("loginPage.loginSuccess"));
              this.$router.push("/menu");
            } else {
              this.$message.error(this.$t("loginPage.loginFailed"));
            }
          } catch (error) {
            console.error("Login  error:", error.response);
            const errorMessage =
              error.response &&
              error.response.data &&
              error.response.data.message
                ? error.response.data.message
                : this.$t("loginPage.loginFailed");
            this.$message.error(errorMessage);
          } finally {
            this.loading = false;
          }
        }
      });
    },
  },
};
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  position: relative;
}

.login-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: url("../../assets/img/洪涝.png") no-repeat center center;
  background-size: cover;
  z-index: 0; /* 确保背景在最底层 */
}

.login-card {
  width: 400px;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  background-color: rgba(255, 255, 255, 0.9); /* 半透明白色背景 */
  backdrop-filter: blur(10px); /* 毛玻璃效果，模糊半径可调整 */
  -webkit-backdrop-filter: blur(10px); /* 兼容 Safari */
  z-index: 1; /* 确保卡片在背景之上 */
}

/* 其余样式保持不变 */
.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #2c3e50;
  font-size: 28px;
  font-weight: 600;
}

.login-button {
  width: 45%;
  margin-right: 10px;
  background-color: #3498db;
  border-color: #3498db;
  transition: background-color 0.3s ease;
}

.login-button:hover {
  background-color: #2980b9;
  border-color: #2980b9;
}

.register-link-button {
  width: 45%;
  color: #3498db;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animated {
  animation-duration: 0.6s;
  animation-fill-mode: both;
}

.fadeIn {
  animation-name: fadeIn;
}

/* Remove language-switch styles as they are no longer needed here */
</style>
