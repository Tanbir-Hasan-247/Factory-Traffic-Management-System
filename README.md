# Smart Traffic Management System

A robust, real-time traffic light management system simulation built with **Django REST Framework** (Backend) and **React + Vite** (Frontend). This system manages complex intersection states, prioritizes emergency vehicles, avoids starvation, and guarantees safety invariants (e.g., conflicting directions cannot be GREEN simultaneously).

## Architecture Overview

1. **Traffic Engine (`run_engine`):** A daemon management command running in the background. It continuously evaluates the traffic queue, calculates priorities based on wait times, and requests state transitions (STABLE -> YELLOW -> ALL_RED -> STABLE).
2. **Backend API:** Provides REST endpoints for junction state, adding vehicles to queues, processing hardware controller ACKs, and fetching audit logs.
3. **Frontend Simulation:** A React dashboard that visualizes the intersection, complete with queueing cars (`🚘`) and accurate traffic light corner placements. It simulates the physical hardware controller by automatically acknowledging (Auto-ACK) state requests from the backend.

## Key Features

* **State Machine Integrity:** Strictly follows a safe transition cycle. Direct changes from GREEN to a conflicting GREEN are blocked. It transitions through YELLOW and ALL_RED states first.
* **Queue-based Priority:** In `AUTOMATIC` mode, the system assigns a dynamic score to each waiting phase based on vehicle count, type (Emergency, Truck, Normal), and wait time.
* **Starvation Protection:** Implements `GREEN_MIN` and `GREEN_MAX` limits. If a phase has been green for the maximum allowed time, the system will force a transition to service other waiting queues.
* **Operating Modes:**
  * `AUTOMATIC`: Driven by queue scores.
  * `MANUAL`: Controlled by explicit user overrides.
  * `EMERGENCY`: Highest priority mode triggered when emergency vehicles are detected.
  * `DEGRADED`: Fallback mode triggered when physical controllers fail to ACK within the timeout threshold, or when an unsafe state is detected.
* **Controller Timeout Recovery:** If the frontend simulation (hardware) takes too long to acknowledge a signal command, the backend engine flags the junction as `DEGRADED` and awaits system recovery.

## Getting Started

### Prerequisites
* Python 3.9+
* Node.js 18+

### 1. Start the Backend Server

```bash
cd traffic-management
python -m venv venv
venv\Scripts\activate   # (On Windows)
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### 2. Start the Traffic Engine (Critical)
The engine calculates all the automatic signal changes. Open a new terminal:
```bash
cd traffic-management
venv\Scripts\activate
python manage.py run_engine
```

### 3. Start the Frontend
Open a new terminal:
```bash
cd traffic-management-client
npm install
npm run dev
```

The application will be available at `http://localhost:5173/`.

## System Invariants & Safety

* **Conflicting Greens:** The engine mathematically verifies that conflicting directions (e.g., NORTH and EAST) cannot be grouped in a single phase.
* **Controller Syncing:** The backend engine won't execute queue calculations unless the physical controller's state is fully synchronized and `ONLINE`.

## Technologies Used
* **Backend:** Django, Django REST Framework, SQLite (default)
* **Frontend:** React, Vite, Tailwind CSS (or standard CSS modules)
* **Code Quality:** Formatted using `black` (Python) and `prettier` (JavaScript).
