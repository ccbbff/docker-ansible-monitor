document.addEventListener('DOMContentLoaded', function() {
    // 新增：检查URL中的forceRefresh参数
    const urlParams = new URLSearchParams(window.location.search);
    const forceRefreshParam = urlParams.get('forceRefresh');
    
    // 如果有强制刷新参数
    if (forceRefreshParam) {
        // 清除URL中的参数
        const cleanUrl = window.location.pathname;
        window.history.replaceState(null, null, cleanUrl);
        
        // 显示加载状态
        const statusOutput = document.getElementById('statusOutput');
        statusOutput.innerHTML = '<div class="loading"><i class="fas fa-sync fa-spin"></i> 刷新主机状态中...</div>';
        
        // 立即强制刷新
        fetchHostStatus(true);
        resetTimer();
    }

    const manualBtn = document.getElementById('manualBtn');
    const autoToggle = document.getElementById('autoToggle');
    const autoLabel = document.getElementById('autoLabel');
    const searchInput = document.getElementById('searchInput');
    const statusOutput = document.getElementById('statusOutput');
    const lastUpdate = document.getElementById('lastUpdate');
    const hostCount = document.getElementById('hostCount');
    const onlineCount = document.getElementById('onlineCount');
    const offlineCount = document.getElementById('offlineCount');
    const refreshTimer = document.getElementById('refreshTimer');

    let autoRefresh = true;
    let refreshInterval;
    let timer = 10;

    // 初始化
    fetchHostStatus();
    startAutoRefresh();

    // 手动刷新按钮
    manualBtn.addEventListener('click', function() {
        fetchHostStatus();
        resetTimer();
    });

    // 自动刷新开关
    autoToggle.addEventListener('change', function() {
        autoRefresh = this.checked;
        autoLabel.textContent = `自动刷新: ${autoRefresh ? '开启' : '关闭'}`;
        
        if (autoRefresh) {
            startAutoRefresh();
        } else {
            clearInterval(refreshInterval);
        }
    });

    // 搜索功能
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        const cards = document.querySelectorAll('.status-card');
        
        cards.forEach(card => {
            const hostName = card.querySelector('.host-name').textContent.toLowerCase();
            const hostIp = card.querySelector('.host-ip').textContent.toLowerCase();
            
            if (hostName.includes(searchTerm) || hostIp.includes(searchTerm)) {
                card.style.display = 'flex';
            } else {
                card.style.display = 'none';
            }
        });
    });

    function fetchHostStatus(force = false) {
        // 显示加载状态
        if (!force) {
            statusOutput.innerHTML = '<div class="loading"><i class="fas fa-spinner fa-spin"></i> 正在检查主机状态...</div>';
        }
        
        // 添加随机参数避免缓存
        const url = force ? `/api/status?t=${new Date().getTime()}` : '/api/status';
        
        fetch(url, {
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('获取主机状态失败');
            }
            return response.json();
        })
        .then(data => {
            updateDashboard(data);
            updateHostsList(data.hosts);
        })
        .catch(error => {
            console.error('获取主机状态错误:', error);
            statusOutput.innerHTML = `<div class="loading error">
                <i class="fas fa-exclamation-circle"></i> 加载数据出错: ${error.message}
            </div>`;
        });
    }

    function updateDashboard(data) {
        lastUpdate.textContent = data.last_update || '从未';
        hostCount.textContent = data.host_count || 0;
        onlineCount.textContent = data.online_count || 0;
        offlineCount.textContent = data.offline_count || 0;
    }

    function updateHostsList(hosts) {
        if (!hosts || hosts.length === 0) {
            statusOutput.innerHTML = '<div class="loading"><i class="fas fa-server"></i> 未配置主机</div>';
            return;
        }

        let html = '';
        hosts.forEach(host => {
            const statusClass = getStatusClass(host.status);
            const statusIcon = getStatusIcon(host.status);
            const hostName = host.name || host.ip;
            const firstLetter = hostName.charAt(0).toUpperCase();
            
            // 状态映射为中文
            const statusText = {
                'online': '在线',
                'offline': '离线',
                'unknown': '未知'
            }[host.status] || host.status;
            
            html += `
            <div class="status-card">
                <div class="host-info">
                    <div class="host-icon ${statusClass}">${firstLetter}</div>
                    <div class="status-info">
                        <div class="host-name">${hostName}</div>
                        <div class="host-ip">${host.ip}</div>
                    </div>
                </div>
                <div class="status-indicator ${statusClass}">
                    <i class="${statusIcon}"></i> ${statusText}
                </div>
            </div>`;
        });
        
        statusOutput.innerHTML = html;
    }

    function getStatusClass(status) {
        switch(status.toLowerCase()) {
            case 'success': return 'online';
            case 'online': return 'online';
            case 'unreachable': return 'offline';
            case 'offline': return 'offline';
            default: return 'unknown';
        }
    }

    function getStatusIcon(status) {
        switch(status.toLowerCase()) {
            case 'success': return 'fas fa-check-circle';
            case 'online': return 'fas fa-check-circle';
            case 'unreachable': return 'fas fa-times-circle';
            case 'offline': return 'fas fa-times-circle';
            default: return 'fas fa-question-circle';
        }
    }

    function startAutoRefresh() {
        clearInterval(refreshInterval);
        resetTimer();
        
        refreshInterval = setInterval(() => {
            timer--;
            refreshTimer.textContent = timer;
            
            if (timer <= 0) {
                fetchHostStatus();
                resetTimer();
            }
        }, 1000);
    }

    function resetTimer() {
        timer = 10;
        refreshTimer.textContent = timer;
    }
});