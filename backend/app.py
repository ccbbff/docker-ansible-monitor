import subprocess
import json
import time
import os
import logging
import re
from flask import Flask, jsonify, request

app = Flask(__name__)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HOSTS_PATH = '/etc/ansible/hosts'

class HostsFileParser:
    """自定义 hosts 文件解析器，完全兼容 Ansible 格式要求"""
    def __init__(self, file_path):
        self.file_path = file_path
        self.groups = {}
        self.vars_sections = {}
        self.host_lines = []
        
    def parse(self):
        """解析 hosts 文件"""
        self.groups = {}
        self.vars_sections = {}
        self.host_lines = []
        
        if not os.path.exists(self.file_path):
            return
            
        current_section = None
        
        with open(self.file_path, 'r') as f:
            for line in f:
                line = line.rstrip()  # 保留行尾空格
                clean_line = line.strip()
                
                # 保留原始行（包括空行和注释）
                self.host_lines.append(line)
                
                # 跳过空行和注释的处理
                if not clean_line or clean_line.startswith('#'):
                    continue
                
                # 检测分组
                if clean_line.startswith('[') and clean_line.endswith(']'):
                    section_name = clean_line[1:-1].strip()
                    current_section = section_name
                    
                    # 检测变量段
                    if ':' in section_name:
                        group_name, section_type = section_name.split(':', 1)
                        if section_type.strip() == 'vars':
                            self.vars_sections[group_name.strip()] = []
                            current_section = f"{group_name.strip()}:vars"
                    
                    # 添加新分组
                    if current_section not in self.groups:
                        self.groups[current_section] = []
                    
                    continue
                
                # 处理主机行
                if current_section:
                    if current_section.endswith(':vars'):
                        # 处理变量定义
                        if '=' in clean_line:
                            key, value = clean_line.split('=', 1)
                            if current_section.split(':')[0] not in self.vars_sections:
                                self.vars_sections[current_section.split(':')[0]] = []
                            self.vars_sections[current_section.split(':')[0]].append({key.strip(): value.strip()})
                    else:
                        # 处理主机定义
                        self.groups[current_section].append(clean_line)
    
    def add_host(self, group, host, variables=None):
        """添加主机到指定分组"""
        host_line = host
        if variables:
            for key, value in variables.items():
                host_line += f" {key}={value}"
                
        # 如果分组不存在，创建新分组
        if group not in self.groups:
            self.groups[group] = []
            # 在文件末尾添加新分组
            self.host_lines.append(f"[{group}]")
            self.host_lines.append(host_line)
        else:
            # 找到分组位置并插入主机
            section_found = False
            for i, line in enumerate(self.host_lines):
                clean_line = line.strip()
                if clean_line == f"[{group}]":
                    section_found = True
                    # 在分组标题后插入新主机
                    self.host_lines.insert(i + 1, host_line)
                    break
            
            # 如果找不到分组，在文件末尾添加
            if not section_found:
                self.host_lines.append(f"[{group}]")
                self.host_lines.append(host_line)
        
        # 添加到内存结构
        self.groups[group].append(host_line)
    
    def update_host(self, old_ip, new_ip, group, variables=None):
        """更新主机信息"""
        # 先删除旧主机
        self.delete_host(old_ip)
        # 再添加新主机
        self.add_host(group, new_ip, variables)
    
    def delete_host(self, ip):
        """删除指定IP的主机"""
        # 从内存结构中删除
        for group in list(self.groups.keys()):
            if group.endswith(':vars'):
                continue
                
            new_hosts = []
            for host_line in self.groups[group]:
                host_parts = host_line.split()
                if host_parts[0] == ip:
                    # 从文件行中删除
                    for i in range(len(self.host_lines)-1, -1, -1):
                        if self.host_lines[i].strip() == host_line:
                            del self.host_lines[i]
                            break
                else:
                    new_hosts.append(host_line)
            
            self.groups[group] = new_hosts
            
            # 如果分组为空，删除分组标题
            if not new_hosts:
                for i in range(len(self.host_lines)-1, -1, -1):
                    if self.host_lines[i].strip() == f"[{group}]":
                        del self.host_lines[i]
                        break
                if group in self.groups:
                    del self.groups[group]
    
    def get_hosts(self):
        """获取所有主机"""
        hosts = []
        for group, host_lines in self.groups.items():
            if group.endswith(':vars'):
                continue
                
            for line in host_lines:
                parts = line.split()
                host = parts[0]
                variables = {}
                
                for part in parts[1:]:
                    if '=' in part:
                        key, value = part.split('=', 1)
                        variables[key] = value
                
                hosts.append({
                    'ip': host,
                    'group': group,
                    'vars': variables
                })
        
        return hosts
    
    def save(self):
        """保存 hosts 文件"""
        # 确保目录存在
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        with open(self.file_path, 'w') as f:
            for line in self.host_lines:
                f.write(line + '\n')
                
        # 设置正确权限
        os.chmod(self.file_path, 0o664)
        logger.info(f"Hosts文件已保存: {self.file_path}")

def run_ansible_ping():
    try:
        logger.info("正在执行Ansible ping操作...")
        
        # 使用显式库存路径
        result = subprocess.run(
            ['ansible', 'all', '-i', HOSTS_PATH, '-m', 'ping', '-o'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # 记录详细输出
        logger.info(f"Ansible执行结果: {result.returncode}")
        if result.stdout:
            logger.info(f"Ansible输出: {result.stdout[:500]}{'...' if len(result.stdout) > 500 else ''}")
        if result.stderr:
            logger.error(f"Ansible错误输出: {result.stderr}")
        
        return parse_ansible_output(result.stdout)
    except subprocess.TimeoutExpired:
        logger.error("Ansible执行超时")
        return {'error': 'Ansible执行超时', 'output': ''}
    except Exception as e:
        logger.exception("执行Ansible时发生异常")
        return {'error': str(e), 'output': e.stdout if hasattr(e, 'stdout') else ""}

def parse_ansible_output(output):
    hosts = []
    online_count = 0
    offline_count = 0
    
    if not output:
        return {
            'last_update': time.strftime('%Y-%m-%d %H:%M:%S'),
            'host_count': 0,
            'online_count': 0,
            'offline_count': 0,
            'hosts': []
        }
    
    for line in output.splitlines():
        if '|' in line:
            parts = line.split('|')
            host_info = parts[0].strip()
            status_info = parts[1].strip() if len(parts) > 1 else ""
            
            # 提取主机名/IP
            host = host_info.split(' ')[0] if ' ' in host_info else host_info
            
            # 解析状态
            status = 'unknown'
            if 'SUCCESS' in status_info:
                status = 'online'
                online_count += 1
            elif 'UNREACHABLE' in status_info:
                status = 'offline'
                offline_count += 1
            else:
                status = 'offline'
                offline_count += 1
            
            hosts.append({
                'name': host,
                'ip': host,
                'status': status,
                'message': status_info
            })
    
    return {
        'last_update': time.strftime('%Y-%m-%d %H:%M:%S'),
        'host_count': len(hosts),
        'online_count': online_count,
        'offline_count': offline_count,
        'hosts': hosts
    }

@app.route('/api/status')
def get_status():
    result = run_ansible_ping()
    return jsonify(result)

@app.route('/api/hosts', methods=['GET'])
def get_hosts():
    """获取所有主机配置"""
    try:
        parser = HostsFileParser(HOSTS_PATH)
        parser.parse()
        return jsonify({'hosts': parser.get_hosts()})
    except Exception as e:
        logger.exception("获取主机列表失败")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hosts', methods=['POST'])
def add_host():
    """添加新主机"""
    try:
        data = request.json
        logger.info(f"添加主机: {data}")
        
        ip = data.get('ip')
        group = data.get('group', 'all')
        variables = data.get('vars', {})
        
        if not ip:
            return jsonify({'error': 'IP地址不能为空'}), 400
        
        # 验证IP格式
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            return jsonify({'error': 'IP地址格式无效'}), 400
        
        parser = HostsFileParser(HOSTS_PATH)
        parser.parse()
        parser.add_host(group, ip, variables)
        parser.save()
        
        logger.info(f"主机添加成功: {ip} in {group}")
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.exception("添加主机失败")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hosts/<ip>', methods=['DELETE'])
def delete_host(ip):
    """删除主机"""
    try:
        logger.info(f"删除主机: {ip}")
        
        # 验证IP格式
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip):
            return jsonify({'error': 'IP地址格式无效'}), 400
        
        parser = HostsFileParser(HOSTS_PATH)
        parser.parse()
        parser.delete_host(ip)
        parser.save()
        
        logger.info(f"主机删除成功: {ip}")
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.exception("删除主机失败")
        return jsonify({'error': str(e)}), 500

@app.route('/api/hosts/<ip>', methods=['PUT'])
def update_host(ip):
    """更新主机配置"""
    try:
        data = request.json
        logger.info(f"更新主机 {ip}: {data}")
        
        new_ip = data.get('ip', ip)
        group = data.get('group', 'all')
        variables = data.get('vars', {})
        
        # 验证IP格式
        if not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip) or \
           not re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', new_ip):
            return jsonify({'error': 'IP地址格式无效'}), 400
        
        parser = HostsFileParser(HOSTS_PATH)
        parser.parse()
        parser.update_host(ip, new_ip, group, variables)
        parser.save()
        
        logger.info(f"主机更新成功: {new_ip} in {group}")
        return jsonify({'status': 'success'})
    except Exception as e:
        logger.exception("更新主机失败")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # 确保hosts文件存在
    if not os.path.exists(HOSTS_PATH):
        open(HOSTS_PATH, 'a').close()
        os.chmod(HOSTS_PATH, 0o664)
    
    app.run(host='0.0.0.0', port=5000)