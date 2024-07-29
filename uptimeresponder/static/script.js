let serverStartTime;
let lastUpdateTime;
let uptimeInterval;

const formatUptime = (milliseconds) => {
    const seconds = Math.floor(milliseconds / 1000);
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;
    return `${days.toString().padStart(2, '0')}:${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
};

const updateUptime = () => {
    const now = Date.now();
    const uptime = now - serverStartTime;
    document.getElementById('uptime').textContent = formatUptime(uptime);
};

const handleStatusResponse = (data) => {
    const serverUptime = parseUptimeString(data.uptime);
    const now = Date.now();

    if (!serverStartTime) {
        serverStartTime = now - serverUptime;
        uptimeInterval = setInterval(updateUptime, 1000);
    } else {
        const expectedUptime = now - serverStartTime;
        if (Math.abs(serverUptime - expectedUptime) > 2000) {
            serverStartTime = now - serverUptime;
        }
    }

    document.getElementById('uptime').textContent = formatUptime(serverUptime);
    document.getElementById('latency').textContent = `${data.latency} ms`;
    lastUpdateTime = now;
};

const fetchStatus = () => {
    fetch('/status')
        .then(response => response.ok ? response.json() : Promise.reject('Network response was not ok'))
        .then(handleStatusResponse)
        .catch(error => {
            console.error('Error fetching status:', error);
            document.getElementById('latency').textContent = 'Time out';
            if (Date.now() - lastUpdateTime > 30000) {
                document.getElementById('uptime').textContent = 'Time out';
                clearInterval(uptimeInterval);
                uptimeInterval = null;
                serverStartTime = null;
            }
        });
};

const parseUptimeString = (uptimeString) => {
    const [days, hours, minutes, seconds] = uptimeString.split(':').map(Number);
    return (days * 86400 + hours * 3600 + minutes * 60 + seconds) * 1000;
};

document.addEventListener('DOMContentLoaded', () => {
    fetchStatus();
    setInterval(fetchStatus, 10000);
});
