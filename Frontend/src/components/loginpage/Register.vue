<template>
  <div class="register-container">
    <div class="register-background"></div>
    <!-- Remove LanguageSwitch component -->
    <el-card class="register-card animated fadeIn">
      <h2 class="register-title">{{ $t("registerPage.title") }}</h2>
      <el-form
        :model="registerForm"
        :rules="registerRules"
        ref="registerForm"
        label-width="80px"
        @submit.native.prevent="handleRegister"
      >
        <el-form-item :label="$t('registerPage.username')" prop="username">
          <el-input
            v-model="registerForm.username"
            :placeholder="$t('registerPage.usernamePlaceholder')"
            prefix-icon="el-icon-user"
          ></el-input>
        </el-form-item>
        <el-form-item :label="$t('registerPage.password')" prop="password">
          <el-input
            v-model="registerForm.password"
            type="password"
            :placeholder="$t('registerPage.passwordPlaceholder')"
            prefix-icon="el-icon-lock"
          ></el-input>
        </el-form-item>
        <el-form-item
          :label="$t('registerPage.confirmPassword')"
          prop="confirmPassword"
        >
          <el-input
            v-model="registerForm.confirmPassword"
            type="password"
            :placeholder="$t('registerPage.confirmPasswordPlaceholder')"
            prefix-icon="el-icon-lock"
          ></el-input>
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            @click="handleRegister"
            :loading="loading"
            class="register-button"
          >
            {{ $t("registerPage.registerButton") }}
          </el-button>
          <el-button @click="$router.push('/login')" class="login-link-button">
            {{ $t("registerPage.goToLogin") }}
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
  name: "Register",
  components: {
    // Remove LanguageSwitch from components
  },
  data() {
    const validateConfirmPassword = (rule, value, callback) => {
      if (value !== this.registerForm.password) {
        callback(new Error(this.$t("registerPage.passwordNotMatch")));
      } else {
        callback();
      }
    };
    return {
      registerForm: {
        username: "",
        password: "",
        confirmPassword: "",
      },
      registerRules: {
        username: [
          {
            required: true,
            message: this.$t("registerPage.usernamePlaceholder"),
            trigger: "blur",
          },
        ],
        password: [
          {
            required: true,
            message: this.$t("registerPage.passwordPlaceholder"),
            trigger: "blur",
          },
          {
            min: 6,
            message: this.$t("registerPage.passwordNotMatch"),
            trigger: "blur",
          },
        ],
        confirmPassword: [
          {
            required: true,
            message: this.$t("registerPage.confirmPasswordPlaceholder"),
            trigger: "blur",
          },
          { validator: validateConfirmPassword, trigger: "blur" },
        ],
      },
      loading: false,
    };
  },
  methods: {
    handleRegister() {
      this.$refs.registerForm.validate(async (valid) => {
        if (valid) {
          this.loading = true;
          console.log("Sending  register request:", {
            username: this.registerForm.username,
            password: this.registerForm.password,
          });
          try {
            const response = await axios.post(
              "http://localhost:5004/api/register",
              {
                username: this.registerForm.username,
                password: this.registerForm.password,
              }
            );
            console.log("Register  response:", response);
            if (response && response.data && response.data.message) {
              this.$message.success(this.$t("registerPage.registerSuccess"));
              this.$router.push("/login");
            } else {
              this.$message.error(this.$t("registerPage.registerFailed"));
            }
          } catch (error) {
            console.error("Register  error:", error.response);
            const errorMessage =
              error.response &&
              error.response.data &&
              error.response.data.message
                ? error.response.data.message
                : this.$t("registerPage.registerFailed");
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
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  position: relative;
}

.register-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: url("../../assets/img/洪涝.png") no-repeat center center;
  background-size: cover;
  z-index: 0; /* 确保背景在最底层 */
}

.register-card {
  width: 400px;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  background-color: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: 1;
}

/* 其余样式保持不变 */
.register-title {
  text-align: center;
  margin-bottom: 30px;
  color: #2c3e50;
  font-size: 28px;
  font-weight: 600;
}

.register-button {
  background-color: #27ae60;
  border-color: #27ae60;
  transition: background-color 0.3s ease;
}

.register-button:hover {
  background-color: #2ecc71;
  border-color: #2ecc71;
}

.login-link-button {
  color: #27ae60;
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
</style>