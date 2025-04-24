以下是一个适合您项目的 `README.md` 文件内容。它清晰地介绍了项目的功能、使用方法、依赖项以及如何贡献代码。您可以根据需要进一步修改或扩展。

---

# 短信AI审核系统

一个基于大语言模型和向量缓存的智能短信审核系统，能够高效地审核短信内容是否合规，并通过向量缓存机制显著提高处理效率和降低API调用成本。

## 系统特点

- **智能审核**：利用DeepSeek大语言模型进行内容审核，具备强大的理解能力
- **向量缓存**：基于语义相似度的缓存机制，可高效处理相似短信
- **批量处理**：支持批量处理大量短信，并提供实时进度和统计
- **性能优化**：通过缓存减少API调用，显著提高处理速度并降低成本

## 工作原理

### 核心流程

1. **初始化**：加载向量模型和初始化缓存
2. **短信审核**：
   - 首先检查缓存中是否有相似短信
   - 如有相似短信，直接返回缓存结果
   - 否则调用API进行审核，并将结果缓存
3. **批量处理**：处理多条短信，并提供统计分析

### 向量缓存机制

系统使用语义向量模型(`paraphrase-multilingual-MiniLM-L12-v2`)将短信文本转换为384维向量，通过计算欧氏距离来判断短信相似度：

- 每条短信及其审核结果都被缓存
- 新短信会与缓存中的短信计算相似度
- 当相似度距离小于阈值(默认0.85)时，直接复用缓存结果
- 相似度阈值可调整：值越大容忍度越高，值越小要求越严格

## 系统流程图

```
┌─────────────┐       ┌───────────────┐       ┌──────────────┐
│  输入短信   │──────▶│  缓存查找     │──Yes─▶│ 返回缓存结果 │
└─────────────┘       └───────┬───────┘       └──────────────┘
                              │ No
                              ▼
                      ┌───────────────┐       ┌──────────────┐
                      │  API审核调用  │──────▶│ 处理审核结果 │
                      └───────────────┘       └──────┬───────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │ 缓存审核结果 │
                                              └──────────────┘
```

## 性能与效率

缓存机制显著提高了系统效率：

- **API调用减少**：相似短信只需一次API调用
- **处理速度**：缓存命中时处理速度提升100倍以上(毫秒vs秒级)
- **成本降低**：减少API调用次数，直接降低成本

在处理大量短信时，随着缓存积累，命中率逐渐提高，系统效率会越来越高。

## 安装与依赖

```bash
pip install sentence-transformers faiss-cpu
pip install requests
```

## 使用方法

### 单条短信审核

```python
from ai_check import AIAuditor

auditor = AIAuditor()
passed, details = auditor.audit_sms_with_cache(
    signature="公司名称", 
    content="短信内容", 
    business_type="行业类型"
)

print(f"审核结果: {'通过' if passed else '失败'}")
print(f"详情: {details}")
```

### 批量短信审核

```python
from ai_check import AIAuditor

# 准备短信列表
sms_list = [
    {"signature": "签名1", "content": "内容1", "business_type": "类型1"},
    {"signature": "签名2", "content": "内容2", "business_type": "类型2"},
    # ...更多短信
]

# 批量审核
auditor = AIAuditor()
results = auditor.batch_audit(sms_list)

# 统计结果
pass_count = sum(1 for r in results if r['passed'])
print(f"通过: {pass_count}/{len(results)}")
```

## 调优建议

1. **相似度阈值调整**：
   - 默认值为0.85，较为严格
   - 增大阈值(如1.0)可提高缓存命中率，但可能降低精确度
   - 减小阈值(如0.5)可提高精确度，但会降低缓存命中率

2. **性能优化**：
   - 对于大规模处理，可考虑将缓存持久化到磁盘
   - 处理相似短信时，先运行测试批次建立缓存，再处理主批次

## 日志与监控

系统会输出详细日志，包括：
- 缓存命中率统计
- API调用耗时
- Token使用情况
- 批量处理进度

## 注意事项

- 首次运行时缓存为空，命中率低
- 随着处理短信数量增加，缓存积累，命中率会提高
- 相似度计算是基于语义的，不仅仅是文本匹配

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
