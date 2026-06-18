# Soldering Assistant API

The Soldering Assistant API helps the user when soldering a project by providing information about the next component to be soldered. It helps the user to solder all the components perfectly at their desired location without missing any and carry out the soldering efficiently and error free.

## How It Works
1. Upload the following data about the soldering project:
- Project Name
- Value, Designator and Description of Each Individual Component
2. Get the list of currently active projects
3. Get the details of the next component to be soldered
4. Get components with similar values at once, so they can be soldered in one go.
5. Mark the soldered component
6. Unmark the unsoldered component
7. Delete a specific project

## Features
- Helps user carry out the soldring efficiently and error-free.
- Keeps track of status of multiple soldering projects.
- Helps multiple people working on same project by letting them know which components have been soldered, which are remaining and which is the next component to be soldered.
- Reduces the hassle to look every time at the BOM.
- Let's you handle the soldering iron, while taking care of the component details.

## Tech Stack
**Language:** Python
**Framework:** FastAPI
**Database:** SQLite & SQLAlchemy
**Server:** Uvicorn
**Rate Limiting:** SlowAPI

## Installation & Usage
Clone the repository: https://github.com/Riddhi1407/Soldering_Assistant_API
Install the dependencies: pip install fastapi uvicorn sqlalchemy slowapi pydantic
Start the development server: uvicorn main:app --reload

## API Key
This API requires for all the reqests. The API key is hardcoded in the main.py file by default.
To authorize requests you must include the following header in your requests: X-API-Key: Pass@123

