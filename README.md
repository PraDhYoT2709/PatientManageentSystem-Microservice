# 🏥 Patient Management System – Microservices Architecture

This project is a **Patient Management System (PMS)** implemented using **Spring Boot Microservices** with JWT authentication, API Gateway, Service Discovery, and a Chatbot integration.  

---

## 🚀 Microservices Included

- **patient-service** → CRUD operations for Patients (MySQL)
- **doctor-service** → CRUD operations for Doctors (MySQL)
- **appointment-service** → CRUD operations for Appointments (MySQL, Feign calls to patient/doctor services)
- **auth-service** → Authentication & Authorization (Spring Security, JWT, OAuth2)
- **discovery-service** → Eureka Server for service discovery
- **api-gateway** → Spring Cloud Gateway for routing & JWT validation
- **chatbot-service** → NLU-powered chatbot to assist patients/doctors
- **pms-chat-widget** → React frontend widget for chatbot integration
- **pms-docker** → Dockerfiles & docker-compose for running all services

---

## 🛠️ Tech Stack

- **Backend:** Spring Boot, Spring Security, Spring Cloud (Eureka, Gateway, OpenFeign)  
- **Frontend:** React + Tailwind (chat widget)  
- **Database:** MySQL  
- **Authentication:** JWT + OAuth2 (Google login supported)  
- **Containerization:** Docker & Docker Compose  
- **CI/CD:** GitHub Actions (Maven build + JUnit tests)  

---

## ⚙️ Architecture Overview

```
           +-------------------+
           |   React Frontend  |
           |  (Chat Widget)    |
           +---------+---------+
                     |
                     v
              +------+------+
              |  API Gateway |
              +------+------+
                     |
     -----------------------------------------
     |        |         |         |          |
     v        v         v         v          v
+---------+ +---------+ +-----------+ +-------------+ +---------------+
| patient | | doctor  | | appointment | | auth-service | | chatbot-service |
+---------+ +---------+ +-----------+ +-------------+ +---------------+
       \           \         /            /                 /
        \           v       v            v                 /
         +-------------------------------+----------------+
                         |
                +------------------+
                | discovery-service |
                +------------------+
```

---

## ▶️ Running the Project

### 1. Clone all repositories
Each service is in its own GitHub repository. Clone them locally:

```bash
git clone <repo-url>/patient-service
git clone <repo-url>/doctor-service
git clone <repo-url>/appointment-service
git clone <repo-url>/auth-service
git clone <repo-url>/discovery-service
git clone <repo-url>/api-gateway
git clone <repo-url>/chatbot-service
git clone <repo-url>/pms-chat-widget
git clone <repo-url>/pms-docker
```

### 2. Configure Databases
- Create MySQL databases:  
  - `patient_db`  
  - `doctor_db`  
  - `appointment_db`  
  - `auth_db`  

Update `application.yml` of each service with DB credentials.

### 3. Start Services (Local)
- Start **discovery-service** (Eureka)
- Start **auth-service**, then other services
- Start **api-gateway** last
- Optionally run **pms-chat-widget (React)** with:
  ```bash
  cd pms-chat-widget
  npm install
  npm start
  ```

### 4. Run with Docker (Recommended)
```bash
cd pms-docker
docker-compose up --build
```

---

## 🔑 Authentication Flow
1. Register/Login via **auth-service** → get JWT  
2. Include `Authorization: Bearer <token>` in API requests  
3. API Gateway validates JWT and forwards request to target service  

---

## 🧪 Testing
- Each service includes **JUnit + Mockito tests** for controllers & service layer  
- Chatbot-service includes **intent detection tests**  
- GitHub Actions run Maven tests on each push  

---

## 📌 Example API Usage (via Gateway)

### Register User
```bash
POST http://localhost:8080/auth/register
Content-Type: application/json

{
  "username": "john",
  "password": "password123",
  "role": "PATIENT"
}
```

### Get All Patients
```bash
GET http://localhost:8080/patients
Authorization: Bearer <JWT>
```

### Book Appointment
```bash
POST http://localhost:8080/appointments
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "patientId": 1,
  "doctorId": 2,
  "date": "2025-09-01T10:00:00"
}
```

---

## 💬 Chatbot Integration
- Chatbot accessible via `/chat/message` endpoint  
- React widget communicates with chatbot-service through API Gateway  
- Example:
```bash
POST http://localhost:8080/chat/message
Authorization: Bearer <JWT>
Content-Type: application/json

{
  "message": "Book an appointment with Dr. Smith tomorrow"
}
```

---

## 📚 Features Roadmap
- ✅ Core CRUD for Patients, Doctors, Appointments  
- ✅ Authentication & JWT Security  
- ✅ Service Discovery & API Gateway  
- ✅ Chatbot integration (React + Spring Boot)  
- 🚀 Audit trail & logging with Spring Data Envers  
- 🚀 Notifications (Email/SMS)  
- 🚀 Advanced NLU for chatbot  

---

## 👨‍💻 Author
**Pradhyot Prakhaar**  
Patient Management System – Microservice Architecture  
