# About the project - ArtSimplified:
A prototype web application designed to help aspiring artists grow by learning the fundametals of art, sharing artwork, joining discussions, asking problems, and exploring course materials for free, also users could create their own schedule that suits best with their time, or follow a pre-made one. Developed as an internship project.
## Author:
- Intern Developer: Nguyễn Xuân Hồng Vũ - 22BI13479
- Project Supervisor: Huỳnh Vinh Nam

## Features:

### Authentication
- User registration and login
- Profile system with default and custom profile pictures
- Admin role with elevated privileges

###  User Posts
- Users can create posts with titles, content, image uploads, and tags
- Tags are parsed and stored in a separate table for flexible filtering
- Posts require admin approval before becoming public
- Admin can approve or delete pending posts

### Upvote System (not implemented yet)
- Users can upvote posts to promote high-quality content
- Posts are sorted based on both upvotes and timestamp 

###  Tagging System
- Tags are stored in a many-to-many relationship with posts
- Tags are parsed from user input (e.g., `#portrait #fun`)
- Users can search/filter posts based on tags (to be implemented)

### Courses
- Courses are added only by admin
- Admin dashboard for managing course content and images

### Comments (Coming Soon)
- Each post will support a comment section with threaded replies

## Techs used
- **Backend**: Python, Flask, Flask-Login, Flask-Migrate, SQLAlchemy
- **Frontend**: HTML, CSS (Bootstrap), Jinja2 templates
- **Database**: SQLite (for development), DBeaver 
- **Deployment**: Docker/OnRender (i dont really know how to use Docker lol)
## Further development comin soon!

## Notes:
- This is a prototype app — there are no real users in the database
- Admin must manually approve new user posts
- Courses and content are added/edited or removed via the admin dashboard
- Profile images default to a placeholder unless changed
