import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';

const StudentAnalysis = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchStudentData = async () => {
            try {
                const res = await axios.get(`/api/students/${id}/analysis`);
                setData(res.data);
            } catch (err) {
                setError('Failed to load student analysis');
            } finally {
                setLoading(false);
            }
        };
        fetchStudentData();
    }, [id]);

    if (loading) return <div style={{padding: '2rem'}}>Loading Student Profile...</div>;
    if (error) return <div className="error-text" style={{padding: '2rem'}}>{error}</div>;
    if (!data) return <div style={{padding: '2rem'}}>Student not found</div>;

    return (
        <div className="dashboard-content animate-fade">
            <div className="dashboard-header">
                <h1>
                    <button onClick={() => navigate(-1)} style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.5rem', color: 'var(--text-secondary)', marginRight: '1rem' }}>←</button>
                    {data.name} Analysis
                </h1>
                <p>{data.roll_number} • {data.class_name}</p>
            </div>

            <div className="stats-grid" style={{ marginTop: '2rem' }}>
                <div className="stat-card">
                    <div className="stat-value">{data.attendance_pct}%</div>
                    <div className="stat-label">Overall Attendance</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">
                         <span className={`badge badge-${data.risk_level.toLowerCase()}`}>
                            {data.risk_level}
                        </span>
                    </div>
                    <div className="stat-label">ML Risk Assessment</div>
                </div>
            </div>

            <div className="glass-card" style={{ marginTop: '2rem' }}>
                <h3 style={{ marginBottom: '1.5rem' }}>Recent Attendance Logs</h3>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Session</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {data.history.length === 0 ? (
                            <tr><td colSpan="3" style={{textAlign: 'center', padding: '2rem'}}>No logs available</td></tr>
                        ) : (
                            data.history.map((log, idx) => (
                                <tr key={idx}>
                                    <td>{log.date}</td>
                                    <td>{log.session}</td>
                                    <td>
                                        <span style={{ color: log.is_present ? 'var(--success-color)' : 'var(--error-color)', fontWeight: 700 }}>
                                            {log.is_present ? 'PRESENT' : 'ABSENT'}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default StudentAnalysis;
