FROM ubuntu:20.04

# 设置环境变量避免交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 安装基础工具
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    iputils-ping \
    net-tools \
    gnupg \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 添加Ansible PPA
RUN apt-add-repository -y ppa:ansible/ansible

# 安装依赖
RUN apt-get update && apt-get install -y \
    ansible \
    python3-pip \
    nginx \
    sshpass \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip3 install flask

# 创建目录结构
RUN mkdir -p /app/frontend /app/backend /etc/ansible /app/backend/logs

# 设置权限
RUN chown -R www-data:www-data /etc/ansible /app/backend/logs
RUN chmod -R 775 /etc/ansible /app/backend/logs

# 复制文件
COPY frontend /usr/share/nginx/html
COPY backend/app.py /app/backend/
COPY ansible/ansible.cfg /etc/ansible/
COPY ansible/hosts /etc/ansible/
COPY nginx.conf /etc/nginx/sites-available/default


# 设置前端文件权限
RUN chmod -R 755 /usr/share/nginx/html

# 确保hosts文件存在
RUN touch /etc/ansible/hosts && \
    chown www-data:www-data /etc/ansible/hosts && \
    chmod 664 /etc/ansible/hosts

# 暴露端口
EXPOSE 80

# 启动脚本
CMD service nginx start && \
    cd /app/backend && \
    python3 app.py