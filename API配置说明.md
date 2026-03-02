# API配置说明

## ⚠️ 重要提示

当前代码中的API地址和密钥为**示例数据**，仅用于演示目的。如果您希望使用真实的视频去水印服务，需要按照以下说明修改配置。

## 📝 修改步骤

### 1. 修改主程序文件

**文件位置**：`interactive_tool_improved.py`

**修改内容**（第34-42行）：
```python
# 原始示例代码
self.client_id = "demo_client_id_12345"
self.client_secret_key = "demo_secret_key_abcdef123456789"
self.api_endpoints = [
    "https://api.example.com/video/dsp",  # 主要API地址
    "https://backup-api.example.com/dsp",  # 备用API地址
    "http://api.example.com/video/dsp",   # HTTP版本
    "https://api.fallback.com/dsp"        # 备用域名
]

# 修改为真实配置
self.client_id = "您的真实client_id"
self.client_secret_key = "您的真实client_secret_key"
self.api_endpoints = [
    "您的真实API地址1",
    "您的真实API地址2",
    "您的真实API地址3",
    "您的真实API地址4"
]
```

### 2. 修改核心模块文件

**文件位置**：`src/api_client.py`

**修改内容**（第19-21行）：
```python
# 原始示例代码
def __init__(self, client_id: str = "demo_client_id_12345", 
             client_secret_key: str = "demo_secret_key_abcdef123456789",
             base_url: str = "https://api.example.com/video/dsp"):

# 修改为真实配置
def __init__(self, client_id: str = "您的真实client_id", 
             client_secret_key: str = "您的真实client_secret_key",
             base_url: str = "您的真实API地址"):
```

## 🔧 配置说明

### API地址格式
- 通常格式为：`https://域名/api/端点`
- 确保API地址支持HTTPS（推荐）或HTTP
- 可以配置多个地址作为备用

### 密钥信息
- `client_id`：客户端标识符
- `client_secret_key`：客户端密钥
- 这些信息通常由API服务提供商提供

## 🚀 使用真实API的步骤

1. **获取API信息**：
   - 从API服务提供商处获取API地址
   - 获取client_id和client_secret_key

2. **修改配置**：
   - 按照上述步骤修改两个文件
   - 保存修改后的文件

3. **测试功能**：
   - 运行程序测试API连接
   - 确认视频去水印功能正常

## 🛡️ 安全注意事项

1. **不要提交真实密钥**：
   - 确保不要将真实的API密钥提交到公共仓库
   - 使用环境变量或配置文件存储敏感信息

2. **访问控制**：
   - 考虑为API访问添加限制
   - 定期更换API密钥

3. **使用示例**：
   - 当前代码中的示例数据可以安全分享
   - 适合用于学习和演示目的

## 📞 联系方式

如有问题，请联系：
- **开发者**：厉温
- **联系方式**：QQ 919373260
- **GitHub**：https://github.com/qianyi888666