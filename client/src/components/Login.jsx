import React, { useState } from 'react';
import axios from 'axios';

const Login = ({ onLoginSuccess }) => {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            const response = await axios.post('/api/login', { email, password });
            localStorage.setItem('token', response.data.token);
            localStorage.setItem('user', JSON.stringify(response.data.user));
            onLoginSuccess(response.data.user);
        } catch (err) {
            setError(err.response?.data?.error || 'Login failed. Check your credentials.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-page">
            <div className="auth-container animate-fade">
                <div className="glass-card" style={{ width: '100%', maxWidth: '420px', padding: '3rem' }}>
                    <div className="brand">
                        <span style={{
                            background: 'var(--accent-gradient)',
                            WebkitBackgroundClip: 'padding-box',
                            backgroundClip: 'padding-box',
                            width: '32px',
                            height: '32px',
                            borderRadius: '8px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            fontSize: '1rem'
                        }}>⚡</span>
                        <span>AttendanceML</span>
                    </div>

                    <h2 style={{ textAlign: 'center', marginBottom: '2.5rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
                        Welcome Back
                    </h2>

                    {error && (
                        <div style={{ marginBottom: '2rem' }}>
                            <div style={{
                                padding: '1rem',
                                background: 'rgba(244, 63, 94, 0.1)',
                                border: '1px solid rgba(244, 63, 94, 0.2)',
                                borderRadius: '12px',
                                color: 'var(--error-color)',
                                fontSize: '0.9rem',
                                textAlign: 'center',
                                fontWeight: 500
                            }}>
                                {error}
                            </div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit}>
                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '8px',
                                fontWeight: 600,
                                fontSize: '0.85rem',
                                color: 'var(--text-secondary)',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em'
                            }}>
                                Email Address
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="form-input"
                                style={{ width: '100%' }}
                                required
                                placeholder="name@university.edu"
                            />
                        </div>

                        <div style={{ marginBottom: '2rem' }}>
                            <label style={{
                                display: 'block',
                                marginBottom: '8px',
                                fontWeight: 600,
                                fontSize: '0.85rem',
                                color: 'var(--text-secondary)',
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em'
                            }}>
                                Password
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="form-input"
                                style={{ width: '100%' }}
                                required
                                placeholder="••••••••"
                            />
                        </div>

                        <button
                            type="submit"
                            className="btn btn-primary"
                            style={{ width: '100%', justifyContent: 'center', padding: '1rem', fontSize: '1rem' }}
                            disabled={isLoading}
                        >
                            {isLoading ? 'Signing In...' : 'Sign In to Dashboard'}
                        </button>
                    </form>

                    <div style={{ marginTop: '2rem', textAlign: 'center', fontSize: '0.95rem', color: 'var(--text-secondary)' }}>
                        Don't have an account? <span style={{ color: 'var(--accent-primary)', cursor: 'not-allowed', fontWeight: 700 }}>Sign up</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Login;
