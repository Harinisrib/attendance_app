import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import ClassList from './components/ClassList';
import ClassDetails from './components/ClassDetails';
import DailyAttendance from './components/DailyAttendance';
import AnalysisDashboard from './components/AnalysisDashboard';
import ClassAnalysis from './components/ClassAnalysis';
import StudentAnalysis from './components/StudentAnalysis';
import StudentDashboard from './components/StudentDashboard';
import StudentAttendance from './components/StudentAttendance';
import Layout from './components/Layout';
import axios from 'axios';

const App = () => {
    const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || 'null'));

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
    }, [user]);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        delete axios.defaults.headers.common['Authorization'];
        setUser(null);
    };


    return (
        <Router>
            <Layout user={user} onLogout={handleLogout}>
                <Routes>
                    <Route
                        path="/login"
                        element={!user ? <Login onLoginSuccess={setUser} /> : <Navigate to="/" />}
                    />
                    <Route
                        path="/"
                        element={user ? (user.type === 'faculty' ? <ClassList /> : <StudentDashboard />) : <Navigate to="/login" />}
                    />
                    <Route
                        path="/attendance"
                        element={user ? (user.type === 'student' ? <StudentAttendance /> : <Navigate to="/" />) : <Navigate to="/login" />}
                    />
                    <Route 
                        path="/class/:id" 
                        element={user ? <ClassDetails /> : <Navigate to="/login" />}
                    />
                    <Route 
                        path="/class/:id/attendance" 
                        element={user ? <DailyAttendance /> : <Navigate to="/login" />}
                    />
                    <Route 
                        path="/analysis" 
                        element={user ? <AnalysisDashboard /> : <Navigate to="/login" />}
                    />
                    <Route 
                        path="/class/:id/analysis" 
                        element={user ? <ClassAnalysis /> : <Navigate to="/login" />}
                    />
                    <Route 
                        path="/student/:id/analysis" 
                        element={user ? <StudentAnalysis /> : <Navigate to="/login" />}
                    />
                    <Route 
                        path="/system" 
                        element={user ? <Dashboard /> : <Navigate to="/login" />} 
                    />
                </Routes>
            </Layout>
        </Router>
    );
};

export default App;
