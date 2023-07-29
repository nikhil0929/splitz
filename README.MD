# Development Log

### July 20th, 2023

I developed a user authentication backend component using Twilio for SMS verification.

There is no Web API component built out yet, it is just running locally from my `main.py` file.

### July 21, 2023

I am now developing the web API component that uses the Twilio SMS verification code that i developed yesterday so that it takes in HTTP requests.

I am going to the be using FastAPI as well as SQLAlchemy as my ORM.

I am also going to be using a locally hosted instance of PostgreSQL.

Database files and models are defined in `db` directory.

Run the development server using the command:

```bash
uvicorn main:app --reload
```
