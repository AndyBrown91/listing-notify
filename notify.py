import sqlalchemy as db
import os

from sqlalchemy import Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

import requests
from bs4 import BeautifulSoup

Base = declarative_base()


class Listing(Base):
    __tablename__ = "listings"

    name = Column('name', String, primary_key=True)
    location = Column('location', String)
    description = Column('description', String)


engine = db.create_engine(os.getenv("DB_URI"))
connection = engine.connect()

Base.metadata.create_all(bind=engine)

Session = sessionmaker(engine)

page = requests.get(os.getenv("URL"))
soup = BeautifulSoup(page.content, "html.parser")

listing_list = soup.find('div', id=lambda x: x and x.startswith('paragraphs-detailed_accordion'))
num_added = 0

for listing in listing_list.findAll("div", class_="accordion-item"):
    db_listing = Listing()
    db_listing.name = str(listing.find("a", href="#na").contents[0]).strip()

    listing_contents = listing.find("div", class_="expandable")
    db_listing.description = listing_contents.find("p").get_text()

    for p in listing_contents.findAll("p"):
        if "Location" in str(p):
            try:
                db_listing.location = p.contents[1].strip()
            except:
                txt = p.get_text()
                txt = txt[len("Location: "):].strip()

                if len(txt) == 0:
                    db_listing.location = None
                else:
                    db_listing.location = txt
                continue

    if db_listing.location:
        Session.configure(bind=engine)
        session = Session()
        session.add(db_listing)

        try:
            session.commit()
            num_added += 1
        except IntegrityError:
            pass  # already in db

exit(num_added)
