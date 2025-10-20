// Maritime Defense Monitoring Dashboard - JavaScript
// Handles interactive features, animations, and real-time updates

class MaritimeDashboard {
    constructor() {
        this.vessels = new Map();
        this.selectedVessel = null;
        this.trackHistory = [];
        this.updateInterval = null;
        this.init();
    }

    init() {
        console.log('🚢 Maritime Dashboard Initialized');
        this.setupEventListeners();
        this.setupAnimations();
        this.loadSessionState();
    }

    setupEventListeners() {
        // Vessel selection
        document.addEventListener('vessel-selected', (e) => {
            this.selectVessel(e.detail);
        });

        // Track update
        document.addEventListener('track-updated', (e) => {
            this.updateTrack(e.detail);
        });

        // Real-time updates
        document.addEventListener('realtime-update', (e) => {
            this.handleRealtimeUpdate(e.detail);
        });
    }

    setupAnimations() {
        // Add glow effect to active elements
        const activeElements = document.querySelectorAll('[data-active="true"]');
        activeElements.forEach(el => {
            el.classList.add('glow-effect');
        });

        // Add pulse effect to status indicators
        const statusElements = document.querySelectorAll('[data-status]');
        statusElements.forEach(el => {
            if (el.dataset.status === 'active') {
                el.classList.add('pulse-effect');
            }
        });
    }

    selectVessel(vesselData) {
        this.selectedVessel = vesselData;
        console.log('📍 Vessel Selected:', vesselData.name);
        
        // Update UI
        this.updateVesselDisplay(vesselData);
        
        // Store in session
        this.saveSessionState();
    }

    updateVessel Display(vesselData) {
        const vesselCard = document.querySelector('[data-vessel-card]');
        if (vesselCard) {
            vesselCard.innerHTML = `
                <div class="vessel-card">
                    <h3>${vesselData.name}</h3>
                    <p><strong>MMSI:</strong> ${vesselData.mmsi || 'N/A'}</p>
                    <p><strong>Position:</strong> ${vesselData.lat?.toFixed(4)}, ${vesselData.lon?.toFixed(4)}</p>
                    <p><strong>Speed:</strong> ${vesselData.sog || 'N/A'} knots</p>
                    <p><strong>Course:</strong> ${vesselData.cog || 'N/A'}°</p>
                    <p class="status-active">● Active</p>
                </div>
            `;
        }
    }

    updateTrack(trackData) {
        this.trackHistory = trackData;
        console.log('📊 Track Updated:', trackData.length, 'positions');
        this.renderTrackVisualization();
    }

    renderTrackVisualization() {
        // This will be called from Streamlit
        const event = new CustomEvent('render-track', {
            detail: this.trackHistory
        });
        document.dispatchEvent(event);
    }

    handleRealtimeUpdate(data) {
        console.log('🔄 Real-time Update:', data);
        
        // Update vessel position
        if (this.selectedVessel && data.mmsi === this.selectedVessel.mmsi) {
            this.selectedVessel = { ...this.selectedVessel, ...data };
            this.updateVesselDisplay(this.selectedVessel);
        }
    }

    saveSessionState() {
        const state = {
            selectedVessel: this.selectedVessel,
            trackHistory: this.trackHistory,
            timestamp: new Date().toISOString()
        };
        sessionStorage.setItem('maritime_dashboard_state', JSON.stringify(state));
    }

    loadSessionState() {
        const stored = sessionStorage.getItem('maritime_dashboard_state');
        if (stored) {
            try {
                const state = JSON.parse(stored);
                this.selectedVessel = state.selectedVessel;
                this.trackHistory = state.trackHistory;
                console.log('✅ Session State Loaded');
            } catch (e) {
                console.error('Error loading session state:', e);
            }
        }
    }

    // Arrow drawing for movement pattern
    drawMovementArrow(ctx, fromLat, fromLon, toLat, toLon, color = '#00D9FF') {
        const headlen = 15;
        const angle = Math.atan2(toLat - fromLat, toLon - fromLon);

        // Draw line
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(fromLon, fromLat);
        ctx.lineTo(toLon, toLat);
        ctx.stroke();

        // Draw arrowhead
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.moveTo(toLon, toLat);
        ctx.lineTo(toLon - headlen * Math.cos(angle - Math.PI / 6), toLat - headlen * Math.sin(angle - Math.PI / 6));
        ctx.lineTo(toLon - headlen * Math.cos(angle + Math.PI / 6), toLat - headlen * Math.sin(angle + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
    }

    // Get ship icon based on vessel type
    getShipIcon(vesselType) {
        const icons = {
            'cargo': '🚢',
            'tanker': '⛴️',
            'container': '📦',
            'fishing': '🎣',
            'military': '⚓',
            'passenger': '🛳️',
            'default': '🚢'
        };
        return icons[vesselType?.toLowerCase()] || icons.default;
    }

    // Format time series data
    formatTimeSeriesData(trackData) {
        return trackData.map((point, idx) => ({
            index: idx,
            timestamp: point.BaseDateTime,
            lat: parseFloat(point.LAT),
            lon: parseFloat(point.LON),
            sog: parseFloat(point.SOG) || 0,
            cog: parseFloat(point.COG) || 0,
            heading: parseFloat(point.Heading) || 0
        }));
    }

    // Calculate statistics
    calculateStats(trackData) {
        const formatted = this.formatTimeSeriesData(trackData);
        
        return {
            totalPositions: formatted.length,
            avgSpeed: (formatted.reduce((sum, p) => sum + p.sog, 0) / formatted.length).toFixed(2),
            maxSpeed: Math.max(...formatted.map(p => p.sog)).toFixed(2),
            minSpeed: Math.min(...formatted.map(p => p.sog)).toFixed(2),
            avgCourse: (formatted.reduce((sum, p) => sum + p.cog, 0) / formatted.length).toFixed(0),
            timeSpan: formatted.length > 1 ? 
                new Date(formatted[formatted.length - 1].timestamp) - new Date(formatted[0].timestamp) : 0
        };
    }

    // Export data
    exportData(format = 'json') {
        const data = {
            vessel: this.selectedVessel,
            track: this.trackHistory,
            stats: this.calculateStats(this.trackHistory),
            exportedAt: new Date().toISOString()
        };

        if (format === 'json') {
            return JSON.stringify(data, null, 2);
        } else if (format === 'csv') {
            return this.convertToCSV(this.trackHistory);
        }
    }

    convertToCSV(data) {
        const headers = ['Timestamp', 'Latitude', 'Longitude', 'Speed', 'Course', 'Heading'];
        const rows = data.map(p => [
            p.BaseDateTime,
            p.LAT,
            p.LON,
            p.SOG,
            p.COG,
            p.Heading
        ]);

        const csv = [headers, ...rows]
            .map(row => row.join(','))
            .join('\n');

        return csv;
    }

    // Real-time connection (WebSocket placeholder)
    connectRealtime(url) {
        console.log('🔌 Connecting to real-time updates:', url);
        // WebSocket implementation would go here
    }

    // Cleanup
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        console.log('🛑 Maritime Dashboard Destroyed');
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.maritimeDashboard = new MaritimeDashboard();
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.maritimeDashboard) {
        window.maritimeDashboard.destroy();
    }
});

