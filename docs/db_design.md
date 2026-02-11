# DB Schema & Entity Design

## ER Diagram

```mermaid
erDiagram
    USER ||--o{ CLASSROOM : "manages"
    CLASSROOM ||--o{ STUDENT : "enrolled"
    STUDENT ||--o{ ATTENDANCE : "marked"

    USER {
        int id PK
        string email
        string password
        string name
    }
    CLASSROOM {
        int id PK
        string name
        int faculty_id FK
    }
    STUDENT {
        int id PK
        string name
        string roll_number
        int classroom_id FK
        string risk_level "Low/Medium/High"
    }
    ATTENDANCE {
        int id PK
        date date
        string session "Morning/Afternoon"
        boolean is_present
        int student_id FK
    }
```

## Table Structures & Data Types

### User Table
| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| id | Integer | Unique identifier | Primary Key, Auto-increment |
| email | String(100) | Faculty email | Unique, Not Null |
| password | String(255) | Hashed password | Not Null |
| name | String(1000) | Faculty name | Not Null |

### Classroom Table
| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| id | Integer | Unique identifier | Primary Key, Auto-increment |
| name | String(100) | Name of the class | Not Null |
| faculty_id | Integer | Reference to User | Foreign Key, Not Null |

### Student Table
| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| id | Integer | Unique identifier | Primary Key, Auto-increment |
| name | String(100) | Student's full name | Not Null |
| roll_number | String(50) | Student's roll number | Not Null |
| classroom_id | Integer | Reference to Classroom | Foreign Key, Not Null |
| risk_level | String(20) | Machine learning risk level | Default 'Low' |

### Attendance Table
| Field | Type | Description | Constraints |
| :--- | :--- | :--- | :--- |
| id | Integer | Unique identifier | Primary Key, Auto-increment |
| date | Date | Date of the session | Not Null |
| session | String(10) | Time of day session | Not Null ('Morning'/'Afternoon') |
| is_present | Boolean | Attendance status | Default False |
| student_id | Integer | Reference to Student | Foreign Key, Not Null |
