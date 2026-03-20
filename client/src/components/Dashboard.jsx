import React, { useState, useEffect } from 'react';
import axios from 'axios';

const Dashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const res = await axios.get('/api/stats');
                setStats(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchStats();
    }, []);

    if (loading) return <div>Loading...</div>;

    return (
        <div className="dashboard-header animate-fade">
            <h1>Welcome, {stats?.user?.name}</h1>
            <p>Phase 2: Decoupled Architecture is active.</p>

            <div className="stats-grid" style={{ marginTop: '2rem' }}>
                <div className="stat-card">
                    <div className="stat-value">REST</div>
                    <div className="stat-label">API Architecture</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">JWT</div>
                    <div className="stat-label">Authentication</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">React</div>
                    <div className="stat-label">UI Framework</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">Zustand</div>
                    <div className="stat-label">State Management</div>
                </div>
            </div>

            <div className="glass-card" style={{ marginTop: '2.5rem' }}>
                <h3>System Status</h3>
                <p style={{ color: 'var(--success-color)', fontWeight: 600, marginTop: '1rem' }}>
                    ✓ Full-Stack CRUD Ready
                </p>
                <p style={{ color: 'var(--success-color)', fontWeight: 600, marginTop: '0.5rem' }}>
                    ✓ Token-Based Security Active
                </p>
            </div>
        </div>
    );
};

export default Dashboard;
