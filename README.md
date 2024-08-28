# Player DB Microservice

## Overview

The Player DB Microservice is a RESTful service built with `aiohttp` and `asyncio`, designed to serve player data from a CSV file via REST API endpoints.


### Key Points

1. **Setup Instructions**: Provides clear steps to install dependencies, run the service locally, or use Docker.
2. **API Usage**: Detailed instructions for using endpoints with Postman and `curl`, ensuring ease of testing.
3. **Error Handling**: Includes common errors and solutions to guide users through troubleshooting.

This `README.md` should serve as a helpful guide for anyone setting up or using your microservice, ensuring they can quickly test and interact with the service endpoints.

## Setup Instructions

### Prerequisites

- Python 3.9 or higher
- `pip` (Python package installer)
- Docker (optional, if running via Docker)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/hagaihe/player_db_microservice.git
   cd player_db_microservice

2. Create a virtual environment and activate it:
   - For Windows:

   ```bash
   Copy code
   python -m venv venv
   venv\Scripts\activate

   - For macOS:

   ```bash
   Copy code
   python3 -m venv venv
   source venv/bin/activate

3. Install dependencies:
   ```bash
   pip install -r requirements.txt

### Running the Service

1. Run Locally:
   ```bash
   python app/main.py

2. Run with Docker:

   To run the microservice in a Docker container, follow these steps:

   - Build the Docker Image:
   ```bash
   docker build -t player-db-microservice .

   - Run the Docker Container:
   ```bash
   docker run -p 8080:8080 player-db-microservice

   This will build the Docker image from the Dockerfile and run the service on port 8080.

### API Endpoints
The service exposes the following RESTful endpoints:

- GET /api/players: Returns the list of all players
   - this endpoint also support sending pagination params:
   GET /api/players?page=50&limit=100

- GET /api/players/{playerID}: Returns a single player by their ID.





