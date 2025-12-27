UiPin - Social Platform for Developers & Designers
Video Demo: [[<URL HERE>](https://youtu.be/0jODA0ll4po)](https://youtu.be/0jODA0ll4po)
Description:
UiPin is a full-stack web application designed to serve as a specialized visual discovery engine for software engineers, UI/UX designers, and frontend developers. While traditional platforms allow for image curation, UiPin distinguishes itself by bridging the gap between visual inspiration and technical implementation. It allows users not only to pin images but also to attach code snippets (HTML, CSS, JS, Python) directly to those pins, creating a "living" repository of design components.

The project solves a common problem: developers often find a design they like but lose time recreating it from scratch. With UiPin, a user can view a card design, click on it, and immediately see the underlying code snippet associated with that visual component. The platform supports user authentication, real-time messaging, board management, and a robust admin panel for content moderation.

Project Structure and File Descriptions
The project is structured using the MVC (Model-View-Controller) architectural pattern, adapted for FastAPI with Jinja2 templates. Here is a detailed breakdown of the files and directories created for this project:

1. Backend Core (/ root directory)
main.py: This is the entry point of the application. It initializes the FastAPI app instance, mounts static files, and includes all the routers. It also handles the startup and shutdown events for database connections.

database.py: Handles the asynchronous connection to the PostgreSQL database using SQLAlchemy. It defines the get_db dependency used throughout the API to manage database sessions securely.

models.py: Contains the SQLAlchemy ORM class definitions. It defines the schema for User, Pin, Board, Comment, and Message tables. Relationships between tables (e.g., One-to-Many between Users and Pins) are established here.

schemas.py: Holds Pydantic models used for data validation and serialization. This ensures that data entering the API (like registration forms) and leaving the API (like JSON responses) conforms to strict type rules.

requirements.txt: Lists all the Python dependencies required to run the project, including FastAPI, SQLAlchemy, Uvicorn, and Redis.

2. Routers (/routers directory)
This directory acts as the "Controller" layer, separating logic by functionality:

users.py: Manages user-related logic such as registration, secure login (using OAuth2 with Password flow), and profile management. It handles password hashing using bcrypt.

pins.py: The core logic for content. It handles image uploading, saving file paths to the database, creating pins, and the search functionality. It also manages the association of code snippets with pins.

messages.py: Handles the real-time messaging system. It implements WebSocket endpoints to allow users to chat instantly. Recently, I integrated Redis logic here to manage "Online/Offline" presence status efficiently without hitting the main database repeatedly.

admin.py: Restricted endpoints for administrators. It allows for the moderation of content, including the ability to delete users. I implemented a "clean-up" logic here to ensure that when a user is deleted, all their associated pins, likes, and comments are also removed (cascade delete) to maintain database integrity.

3. Frontend Templates (/templates directory)
I chose Jinja2 for server-side rendering to keep the application lightweight and SEO-friendly.

base.html: The skeleton of the application. It contains the <head>, the navigation bar, and the footer. All other pages extend this file to avoid code duplication.

index.html: The homepage. It serves as the container for the Masonry layout grid where pins are displayed.

profile.html: Displays user-specific data, separating their uploaded pins and their created boards using dynamic tabs.

board_detail.html: A specific view for looking inside a user's curated board.

4. Static Assets (/static directory)

js/layout.js: (Crucial File) This file contains the custom algorithm I wrote for the Masonry Layout. Unlike a standard CSS grid which leaves gaps between items of different heights, this JavaScript calculates the height of each card and dynamically positions it in the shortest available column, creating a seamless "waterfall" effect.

js/actions.js: Handles asynchronous frontend logic using the Fetch API. It manages liking a pin without refreshing the page, submitting comments, and handling form data for image uploads.

5. Testing & Performance (/tests & root)
tests/conftest.py & tests/test_main.py: Integration tests written with Pytest. These ensure that critical paths (Login, Register, Home Load) work as expected before deployment.

locustfile.py: A performance testing script for Locust. It simulates 50+ concurrent users to test the load capacity of the application, randomly selecting images from a test directory to simulate realistic traffic.

Design Choices and Trade-offs
During the development of UiPin, I had to make several architectural decisions, weighing complexity against performance.

1. FastAPI vs. Django/Flask: I chose FastAPI over Django or Flask primarily for its asynchronous capabilities. Since UiPin involves heavy I/O operations (image uploading, database queries, and WebSocket connections), the async/await syntax allows the server to handle multiple requests concurrently without blocking. Additionally, FastAPI’s automatic documentation (Swagger UI) significantly sped up the testing of API endpoints.

2. PostgreSQL & SQLAlchemy (Async): For the database, I opted for PostgreSQL instead of SQLite. While SQLite is easier to set up, PostgreSQL is a production-grade database that handles concurrency much better. I used SQLAlchemy with an asynchronous driver (asyncpg) to ensure that database queries did not become a bottleneck for the FastAPI event loop.

3. Vanilla JavaScript vs. React/Vue: This was a major debate. While a framework like React manages state efficiently, I decided to use Vanilla JavaScript and Jinja2 templates. My goal was to understand the underlying mechanics of the DOM. Writing the Masonry Layout algorithm manually in JavaScript gave me a deep understanding of element positioning and window resize events that I would have missed if I had simply imported a React library.

4. Implementing Redis for Presence: Initially, I planned to store user "Online" status in the PostgreSQL database. However, during testing, I realized that writing to the hard disk (DB) every time a user connects or disconnects via WebSocket is inefficient and unscalable. I decided to introduce Redis as an in-memory key-value store. Now, when a user connects via WebSocket, their ID is cached in Redis with a Time-To-Live (TTL). This makes checking "Who is online" incredibly fast and reduces load on the primary database.

5. Soft Deletion & Data Integrity: In the Admin panel, I faced a choice between "Soft Delete" (marking a user as inactive) and "Hard Delete". I implemented a rigorous Hard Delete process that cleans up all related data (likes, comments, boards). This was chosen to comply with privacy standards (Right to be Forgotten) and to ensure the application doesn't serve broken links or "orphan" data.

UiPin represents a comprehensive effort to build a scalable, modern web application that solves a real need for the developer community while adhering to strong software engineering principles.
Here is a preview of the application:
<img width="1422" height="686" alt="Ekran görüntüsü 2025-12-27 195230" src="https://github.com/user-attachments/assets/c0505ae9-36fc-4a25-a329-838b262204c4" />
<img width="1400" height="687" alt="Ekran görüntüsü 2025-12-27 195248" src="https://github.com/user-attachments/assets/330072df-a912-43b2-adfa-fc8513c8d501" />
<img width="1385" height="686" alt="Ekran görüntüsü 2025-12-27 195301" src="https://github.com/user-attachments/assets/3f19c528-31d5-4d34-9fdd-399d13c7844f" />
<img width="1478" height="683" alt="Ekran görüntüsü 2025-12-27 195314" src="https://github.com/user-attachments/assets/ae2c8305-8c0b-4b2e-95f6-768fdcb4cd01" />
<img width="1421" height="696" alt="Ekran görüntüsü 2025-12-27 195351" src="https://github.com/user-attachments/assets/0e158c86-8286-4274-b42b-98599433b285" />
<img width="1454" height="707" alt="Ekran görüntüsü 2025-12-27 195404" src="https://github.com/user-attachments/assets/5724bda7-bd6a-4f50-accc-3c25882ba2cf" />
<img width="1453" height="699" alt="Ekran görüntüsü 2025-12-27 195413" src="https://github.com/user-attachments/assets/db575081-dfaf-4f8c-aefc-fac60973192f" />
<img width="1457" height="695" alt="Ekran görüntüsü 2025-12-27 195429" src="https://github.com/user-attachments/assets/d6cf8d5d-fe44-476d-951e-8462cd45245a" />
<img width="1464" height="693" alt="Ekran görüntüsü 2025-12-27 195438" src="https://github.com/user-attachments/assets/0648a5a4-4b23-4af6-a667-2d46e41315c9" />
<img width="1436" height="689" alt="Ekran görüntüsü 2025-12-27 195449" src="https://github.com/user-attachments/assets/734ae0ab-eb2e-4ce9-9bbf-49667fd18165" />




