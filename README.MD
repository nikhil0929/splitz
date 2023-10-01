# Development Log

### July 20th, 2023

I developed a user authentication backend component using Twilio for SMS verification.

There is no Web API component built out yet, it is just running locally from my `main.py` file.

```bash
uvicorn main:app --reload
```

### August 6th, 2023

**Some things that I am considering:**

So far I have developed the backend with user authentication from Twilio using their phone-number. But now i am trying to implement security with FastAPI's built in security API using OAuth2. But FastApi's security API automatically comes pre-built to work with 2 different Schemas:
- Using built in username and password to authenticate (OAuth2PasswordBearer)

## **Application Architecture Design:**

The application follows a modular, object-oriented design that separates concerns into distinct classes, each with their own responsibilities. This design includes a `Database` class for database operations, a `UserService` class for user-related business logic, and a `UserController` class for handling HTTP requests and responses.

#### **Key Benefits:**

1. **Modularity**: Each class has a specific role, making the code easier to understand and maintain.

2. **Reusability**: The classes can be reused across the application, promoting code efficiency and consistency.

3. **Testability**: Each class can be tested independently, facilitating robust and comprehensive testing.

4. **Flexibility**: Changes in one class (e.g., database interactions) do not affect others, making the codebase more adaptable to future modifications.

This design does not inherently add security but provides a structured framework within which secure coding practices can be effectively implemented.

![design drawing](assets/UserService.png)


## Next Steps

Do what i did in Scaleable software architectures class. First, create a way to upload images sent from the clients side. Then the backend takes that image and puts it into an s3 bucket with a UUID as its folder name. This folder on s3 represents the GROUP UUID to which all these uploaded receipt images belong. Anyone that has this UUID in their "groups" field of their database record, can access all the images within subdirectory on s3. Maybe even add a list of all Group UUID's a User is in. 

a `room` is going to represented as a UUID as the primary key. the User and Rooms table will be a  `many-to-many` relationship. For this we will be using an *association table*:

`UserRoom Association Table`:
`   user_id`: Foreign Key referencing Users
`    room_id`: Foreign Key referencing Rooms

`Rooms Table`:
`   room_id:`Primary key (UUID)
`   room_name`: Name of the room
`   room_password`: Password for the room (hashed + salt)


ssh -i "splitz_ec2.pem" ubuntu@ec2-3-14-255-133.us-east-2.compute.amazonaws.com