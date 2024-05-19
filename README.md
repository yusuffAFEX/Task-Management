# Task-Management

## SET UP

1. Clone the project repository:
    ```sh
    git clone <repository-url>
    ```
2. Install the required packages:
    ```sh
    pip install -r requirements.txt
    ```
3. Create a PostgreSQL database.
4. Create a `.env` file.
5. Generate a secret key (make it a long string with different characters to ensure security).
6. Set up the secret key and database credentials in the `.env` file, replicating the structure in the `.env.sample` file.
7. Start the server by running:
    ```sh
    python manage.py runserver
    ```
    (for running the application without data streaming)
8. You can start calling the endpoints.
9. Check the documentation at `localhost:<port>/api/v1/docs`.

## Running WebSocket for Data Streaming

1. Start the server with:
    ```sh
    daphne -b 0.0.0.0 -p <port> niyo_group_task_management.asgi:application
    ```
2. Change `<port>` to the port you want to run the server on.
3. The data streaming URL is `localhost:<port>/ws/tasks/`. This can be used on the frontend to listen to the backend server when calling endpoints for create or update operations.
