import os
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy import create_engine, String, Integer, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship, Session
from pydantic import BaseModel
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = "os.environ["DATABASE_URL"]"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI()

class UpdateUsers(BaseModel):
     username : str | None = None
     email: str | None = None

class CreateUsers(BaseModel):
    username : str
    email: str
    password : str

class CreateJournalEntry(BaseModel):
    title : str
    content : str


class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(125),
        nullable=False
    )

    hashed_password : Mapped[str] = mapped_column(
         String, 
         nullable=False
         )

    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        back_populates="user"
    )


class JournalEntry(Base):
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    title: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    content: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )
    
    user: Mapped["User"] = relationship(
        back_populates="journal_entries"
    )
    

Base.metadata.create_all(engine)



@app.get("/")
def root():
    return {"message ": "Welcome to my Personal Journal API"}


@app.post("/users")
def add_users(user: CreateUsers, db: Session = Depends(get_db)):

    hashed_password = pwd_context.hash(user.password)

    new_user = User(
        username= user.username,
        email= user.email,
        hashed_password= hashed_password
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@app.get("/users")
def get_users(db: Session = Depends(get_db)):

    users = db.query(User).all()

    if not users:
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail="Users don't exist"
             )   
    return users


@app.get("/users/{user_id}")
def get_user_by_id( user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail="User doesn't exist"
             )   
    return user


@app.post("/users/{user_id}/journal-entries")
def add_journal_entries(
    entry: CreateJournalEntry,
    user_id: int,
    db: Session = Depends(get_db)
):
    
    
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User doesn't exist"
        )

    new_entry = JournalEntry(
        title=entry.title,
        content=entry.content,
        user_id=user_id
    )

    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    return new_entry



@app.get("/journal-entries")
def get_entries(db: Session = Depends(get_db)):
     entries = db.query(JournalEntry).all()
     
     if not entries:
         raise HTTPException(
                      status_code=status.HTTP_404_NOT_FOUND,
                      detail="Journal entries don't exist") 
       
     return entries


@app.get("/journal-entries/{journal_entry}")
def get_entry(journal_entry: int , db: Session = Depends(get_db)):
     entry = db.query(JournalEntry).filter(JournalEntry.id == journal_entry).first()
     
     if not entry:
         raise HTTPException(
                      status_code=status.HTTP_404_NOT_FOUND,
                      detail="Journal entry doesn't exist") 
       
     return entry


@app.patch("/users/{user_id}")
def update_id(user_id: int, updateuser: UpdateUsers  ,db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
             raise HTTPException(
                 status_code=status.HTTP_404_NOT_FOUND,
                 detail="User doesn't exist"
             ) 

    if updateuser.username is not None:
        user.username = updateuser.username

    if updateuser.email is not None:
        user.email = updateuser.email

    db.commit()
    db.refresh(user)

    return user


@app.delete("/users/{user_id}")
def delete_id(user_id: int, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User doesn't exist"
        )

    for entry in user.journal_entries:
        db.delete(entry)

    db.delete(user)

    db.commit()

    return {"message": "the user was deleted successfully!"}