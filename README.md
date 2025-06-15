# Ansible 主机监控系统

![Ansible Dashboard](https://img.shields.io/badge/Ansible-v2.8+-blue.svg)
![Flask API](https://img.shields.io/badge/Flask-API-green.svg)
![Docker](https://img.shields.io/badge/Docker-Containerized-blue.svg)

一个基于Ansible的现代化主机监控与管理平台，提供实时的主机状态监控和便捷的管理界面。

#### 该镜像已上传至阿里云：
```bash
docker pull crpi-tc924g48hyfbhnok.cn-hongkong.personal.cr.aliyuncs.com/ccbbf/ansible-dashboard:latest
```

## 功能亮点

- ✅ **实时主机监控**：可视化展示所有主机的在线/离线状态
- 🚀 **一键式操作**：立即执行Ping测试或设置自动刷新
- 🔧 **主机管理**：通过Web界面添加、编辑或删除主机
- 📊 **状态统计**：直观显示主机总数、在线/离线数量
- 🔍 **智能搜索**：快速查找特定主机
- ⚡ **自动刷新**：可配置的自动刷新功能
- 🐳 **容器化部署**：使用Docker快速部署

## 技术栈

| 组件         | 技术                 |
|--------------|----------------------|
| 前端         | HTML5, CSS3, JavaScript |
| 后端         | Python Flask         |
| 基础设施     | Ansible              |
| 容器化       | Docker               |
| Web服务器    | Nginx                |

## 系统截图

### 监控仪表板
![监控仪表板截图](https://via.placeholder.com/800x500/3498db/ffffff?text=Ansible+监控仪表板)

### 主机管理界面
![主机管理界面截图](https://via.placeholder.com/800x500/2ecc71/ffffff?text=主机管理界面)

## 快速开始

### 部署步骤
1.使用预构建镜像
```bash
# 从阿里云拉取镜像
docker pull crpi-tc924g48hyfbhnok.cn-hongkong.personal.cr.aliyuncs.com/ccbbf/ansible-dashboard:latest

# 运行容器
docker run -d   --name ansible-monitor   --network host(-p 8080:80) -v /etc/localtime:/etc/localtime:ro \
crpi-tc924g48hyfbhnok.cn-hongkong.personal.cr.aliyuncs.com/ccbbf/ansible-dashboard
```
2.从源代码构建
```bash
# 1. 克隆仓库
git clone https://github.com/ccbbf/ansible-monitor.git
cd ansible-monitor

# 2. 构建Docker镜像
docker build -t ansible-monitor .

# 3. 运行容器
docker run -d   --name ansible-monitor   --network host(-p 8080:80) -v /etc/localtime:/etc/localtime:ro \
ansible-monitor
```

## 目前问题
容器采用8080端口启动时，管理主机操作后需要手动刷新才能使Ansible主机监控界面才能正常显示。如果采用host网络模式则无此问题。
