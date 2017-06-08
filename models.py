from db import Base, Scraper_Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.types import Text


class Scraper(Scraper_Base):
    __tablename__ = 'scraper'

    id = Column(Integer, primary_key=True)
    url = Column(String(200))
    scraped_at = Column(DateTime)


class Domain(Base):
    __tablename__ = 'domain'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))


class Organization(Base):
    __tablename__ = 'organization'

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    description = Column(Text)
    domain_id = Column(Integer, ForeignKey('domain.id'))
    headquarters_address = Column(String(200))
    size = Column(String(100))
    founded_at = Column(DateTime)
    type = Column(String(100))
    industry = Column(String(100))
    revenue = Column(String(100))
    competitors = Column(String(500))
    logo_url = Column(String(200))

    domain = relationship(Domain)


class Location(Base):
    __tablename__ = 'location'

    id = Column(Integer, primary_key=True)
    country = Column(String(50))
    state = Column(String(50))
    city = Column(String(50))


class Job(Base):
    __tablename__ = 'job'

    id = Column(Integer, primary_key=True)
    source = Column(String(100))
    title = Column(String(100))
    created_at = Column(DateTime)
    description = Column(Text)
    organization_id = Column(Integer, ForeignKey('organization.id'))
    location_id = Column(Integer, ForeignKey('location.id'))
    last_date = Column(DateTime)

    organization = relationship(Organization)
    location = relationship(Location)


class Qualification(Base):
    __tablename__ = 'qualification'

    id = Column(Integer, primary_key=True)
    name = Column(String(20))


class JobQualification(Base):
    __tablename__ = 'job_qualification'

    id = Column(Integer, primary_key=True)
    job_id = Column(Integer, ForeignKey('job.id'))
    qualification_id = Column(Integer, ForeignKey('qualification.id'))

    job = relationship(Job)
    qualification = relationship(Qualification)


class AuthorJob(Base):
    __tablename__ = 'author_job'

    id = Column(Integer, primary_key=True)
    job = Column(String(50))


class AuthorLocation(Base):
    __tablename__ = 'author_location'

    id = Column(Integer, primary_key=True)
    location = Column(String(80))


class Review(Base):
    __tablename__ = 'review'

    id = Column(Integer, primary_key=True)
    review_at = Column(DateTime)
    summary = Column(String(100))
    organization_id = Column(Integer, ForeignKey('organization.id'))
    author_job_id = Column(Integer, ForeignKey('author_job.id'))
    author_location_id = Column(Integer, ForeignKey('author_location.id'))
    review = Column(Text)

    organization = relationship(Organization)
    author_job = relationship(AuthorJob)
    author_location = relationship(AuthorLocation)
