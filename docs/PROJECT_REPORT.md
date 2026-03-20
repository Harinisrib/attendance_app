# AttendSmart: ML-Based Attendance Pattern Mining System
## Final Project Report
**Phase 3: Web Development Final Submission**

### 1. Executive Summary
AttendSmart is an intelligent Attendance Management System designed to bridge the gap between traditional manual roll-calls and modern, data-driven educational analytics. The application provides faculties with intuitive tools to manage classrooms and uses historical attendance data to identify at-risk students, analyze attendance streaks, and prevent dropouts using basic statistical machine learning heuristics.

### 2. Architecture & Tech Stack
The project was developed with a modern, lightweight tech stack to ensure quick prototyping and performance:
- **Backend Framework**: Python / Flask (micro-framework allowing rapid API and template development).
- **Database**: SQLite integrated with Flask-SQLAlchemy for ORM mappings. Designed to be easily migrated to PostgreSQL.
- **Frontend**: HTML5, Vanilla CSS, and Jinja2 Templating Engine. Enhanced with custom DOM-manipulation JavaScript for UI/UX refinements like Toast Notifications and dynamic Loaders.
- **Machine Learning Engine**: Pandas and Scikit-learn for processing attendance matrices and calculating consistency scores.
- **Deployment**: Configured for Render.com via gunicorn (`render.yaml`).

### 3. Features Implemented in Phase 3
Phase 3 of the development cycle focused strictly on the **Web Development** criteria:
1. **UI/UX Refinements**: Introduced responsive UI interactions, including a global CSS-based loading spinner during network requests and a non-blocking "Toast" notification system to replace native alert boxes.
2. **Advanced Logic**: Implemented Server-Side Pagination for rendering attendance history and class rosters. This prevents front-end congestion when dealing with large datasets of student records.
3. **Performance & Testing**: 
   - Refactored `models.py` to include SQLAlchemy database indexes (`idx_attendance_student_date`) for O(1) query lookups on high-throughput routes.
   - Introduced basic automated testing pipelines using `pytest` to validate core Authentication and Navigation logic.
4. **Production Deployment**: Prepared declarative infrastructure-as-code files (`render.yaml`) to seamlessly host the Flask instance on Render with persistent disk volumes.

### 4. Database Schema
- **User**: Core entity for Faculty.
- **Classroom**: Entity mapped to Faculty. Has one-to-many relationship with Students.
- **Student**: Tied to Classroom. Has risk-level metadata updated by the ML engine.
- **Attendance**: High-volume table mapping students to individual dates and sessions.

### 5. Future Scope
- Transition to PostgreSQL for concurrent transactional integrity scaling.
- Integrate the provided placeholder React/Vite App (`client/` folder) with Flask via REST APIs instead of Jinja2.
- Integrate Deep Learning (CNNs) for facial recognition-based smart check-ins.
