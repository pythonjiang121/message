以下是一个适合您项目的 `README.md` 文件内容。它清晰地介绍了项目的功能、使用方法、依赖项以及如何贡献代码。您可以根据需要进一步修改或扩展。

---

# 短信审核工具

## 项目简介
本项目是一个用于批量审核短信内容的工具，支持对短信签名、内容和业务类型进行自动化验证。适用于需要批量处理短信数据的场景，如营销短信审核、合规检查等。

## 主要功能
1. **签名审核**：验证短信签名是否符合规范（如是否包含有效姓氏）。
2. **内容审核**：检查短信内容是否合规（如是否包含敏感词）。
3. **业务审核**：根据业务类型和账户类型验证短信的合法性。
4. **批量处理**：支持从 Excel 文件中读取短信数据，并批量审核。
5. **结果导出**：将审核结果导出为 Excel 文件，便于进一步分析。

## 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/pythonjiang121/message.git
cd message
```

### 2. 安装依赖
确保已安装 Python 3.7 或更高版本，然后安装依赖库：
```bash
pip install -r requirements.txt
```

### 3. 准备数据
将需要审核的短信数据保存为 Excel 文件，确保包含以下列：
- `短信签名`
- `短信内容`
- `客户业务类型`
- `账户类型`

示例文件格式：
| 短信签名 | 短信内容         | 客户业务类型 | 账户类型 |
|----------|------------------|--------------|----------|
| 【公司A】| 您好，您的订单已发货 | 电商         | 普通账户 |
| 【公司B】| 点击链接领取优惠券 | 营销         | VIP账户  |

### 4. 运行脚本
使用以下命令运行脚本：
```bash
python main.py 输入文件.xlsx 输出文件.xlsx
```
- `输入文件.xlsx`：包含待审核短信数据的 Excel 文件。
- `输出文件.xlsx`（可选）：审核结果保存路径。如果未提供，将自动生成一个带时间戳的文件。

### 5. 查看结果
审核结果将保存到指定的 Excel 文件中，包含以下列：
- `审核结果`：是否通过审核（True/False）。
- `签名审核`：签名审核结果。
- `内容审核`：内容审核结果。
- `业务审核`：业务审核结果。

## 项目结构
```
message/
├── main.py                  # 主程序入口
├── requirements.txt         # 依赖库列表
├── surnames.json            # 姓氏数据文件
├── signature.py             # 签名审核模块
├── content.py               # 内容审核模块
├── business.py              # 业务审核模块
├── README.md                # 项目说明文件
└── tests/                   # 单元测试目录
```

## 依赖项
- Python 3.7+
- pandas
- openpyxl

安装依赖：
```bash
pip install pandas openpyxl
```

## 贡献指南
欢迎贡献代码！以下是参与项目的步骤：
1. Fork 本项目。
2. 创建一个新分支：
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. 提交您的更改：
   ```bash
   git commit -m "描述您的更改"
   ```
4. 推送分支：
   ```bash
   git push origin feature/your-feature-name
   ```
5. 提交 Pull Request。

## 许可证
本项目采用 [MIT 许可证](LICENSE)。

---

## 联系方式
如有问题或建议，请联系：
- 邮箱：zhengdongjiang06@gmail.com
- GitHub: [pythonjiang121](https://github.com/pythonjiang121)

---

## 示例
### 输入文件
| 短信签名 | 短信内容         | 客户业务类型 | 账户类型 |
|----------|------------------|--------------|----------|
| 【公司A】| 您好，您的订单已发货 | 电商         | 普通账户 |
| 【公司B】| 点击链接领取优惠券 | 营销         | VIP账户  |

### 输出文件
| 短信签名 | 短信内容         | 客户业务类型 | 账户类型 | 审核结果 | 签名审核 | 内容审核 | 业务审核 |
|----------|------------------|--------------|----------|----------|----------|----------|----------|
| 【公司A】| 您好，您的订单已发货 | 电商         | 普通账户 | True     | 通过     | 通过     | 通过     |
| 【公司B】| 点击链接领取优惠券 | 营销         | VIP账户  | False    | 通过     | 不通过   | 通过     |

---

希望这个 `README.md` 文件能帮助用户快速了解和使用您的项目！如果有其他需求，请随时告诉我。

## Docker部署

本项目支持使用Docker进行部署，提供更一致的运行环境和简化的部署流程。

### 前置要求

- 安装Docker和Docker Compose
  - Docker: https://docs.docker.com/get-docker/
  - Docker Compose: https://docs.docker.com/compose/install/

### 快速部署

使用提供的部署脚本：

```bash
# 赋予脚本执行权限（仅首次需要）
chmod +x docker-deploy.sh

# 构建并启动服务
./docker-deploy.sh --build

# 查看服务日志
./docker-deploy.sh --logs
```

### 运行模式

系统支持多种运行模式，可以根据需要选择：

1. **标准处理模式** - 处理短信文件
   ```bash
   ./docker-deploy.sh
   ```

2. **API服务模式** - 启动API服务，用于接口调用
   ```bash
   ./docker-deploy.sh --api
   
   # 查看API服务日志
   ./docker-deploy.sh --logs api
   ```

3. **检查模式** - 运行Excel文件检查
   ```bash
   ./docker-deploy.sh --check
   ```

### 常用命令

```bash
# 重启服务
./docker-deploy.sh --restart

# 停止服务
./docker-deploy.sh --stop
```

### 手动操作Docker

如果需要手动管理Docker容器：

```bash
# 构建镜像
docker-compose build

# 启动标准服务
docker-compose up -d

# 启动API服务
docker-compose --profile api up -d

# 运行检查服务
docker-compose --profile check up

# 停止所有服务
docker-compose down

# 查看日志
docker-compose logs -f sms-audit
```

### 文件挂载

Docker配置已设置以下挂载点：

- `./data`: 应用数据目录
- `./logs`: 日志输出目录
- `./sms_data.db`: 数据库文件
- `./无标题.csv`: 输入数据文件

这些文件会从宿主机挂载到容器内，确保数据持久化。
