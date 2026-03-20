import React from 'react';

import { Link, useLocation } from 'react-router-dom';

const Layout = ({ children, user, onLogout }) => {
    const location = useLocation();
    
    if (!user) return <main className="main-content">{children}</main>;

    return (
        <div className="app-container">
            <aside className="sidebar">
                <div className="brand">
                    <div style={{
                        background: 'var(--accent-gradient)',
                        WebkitBackgroundClip: 'padding-box',
                        backgroundClip: 'padding-box',
                        width: '32px',
                        height: '32px',
                        borderRadius: '8px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white'
                    }}>
                        ⚡
                    </div>
                    <span>AttendanceML</span>
                </div>

                <ul className="nav-links">
                    {user.type === 'faculty' ? (
                        <>
                            <li className="nav-item">
                                <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
                                    <i>🏠</i> <span>Dashboard</span>
                                </Link>
                            </li>
                            <li className="nav-item">
                                <Link to="/analysis" className={location.pathname === '/analysis' ? 'active' : ''}>
                                    <i>📈</i> <span>Overall Analysis</span>
                                </Link>
                            </li>
                            <li className="nav-item">
                                <Link to="/system" className={location.pathname === '/system' ? 'active' : ''}>
                                    <i>⚙️</i> <span>System Status</span>
                                </Link>
                            </li>
                        </>
                    ) : (
                        <>
                            <li className="nav-item">
                                <Link to="/" className={location.pathname === '/' ? 'active' : ''}>
                                    <i>📊</i> <span>My Stats</span>
                                </Link>
                            </li>
                            <li className="nav-item">
                                <Link to="/attendance" className={location.pathname === '/attendance' ? 'active' : ''}>
                                    <i>📅</i> <span>My Attendance</span>
                                </Link>
                            </li>
                        </>
                    )}
                </ul>

                <div className="user-profile">
                    <div className="user-avatar">
                        {user.name ? user.name[0].toUpperCase() : '?'}
                    </div>
                    <div style={{ flex: 1, overflow: 'hidden' }}>
                        <p style={{
                            fontWeight: 700,
                            fontSize: '0.9rem',
                            color: 'var(--text-primary)',
                            whiteSpace: 'nowrap',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            marginBottom: '2px'
                        }}>
                            {user.name}
                        </p>
                        <button
                            onClick={onLogout}
                            style={{
                                background: 'none',
                                border: 'none',
                                padding: 0,
                                cursor: 'pointer',
                                color: 'var(--error-color)',
                                textDecoration: 'none',
                                fontSize: '0.75rem',
                                fontWeight: 600,
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                opacity: 0.8
                            }}
                        >
                            Sign Out
                        </button>
                    </div>
                </div>
            </aside>

            <main className="main-content">
                {children}
            </main>
        </div>
    );
};

export default Layout;
