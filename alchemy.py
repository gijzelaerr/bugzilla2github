"""
doesn't work for me, somehow some tables are missing using SQLALchemy and automap_base
"""
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Table
from sqlalchemy.schema import MetaData
import github3
from settings import *

# TODO: context, uid mapping

#mysql_uri = "mysql+mysqlconnector://root@localhost/bugzilla"
mysql_uri = "mysql+mysqldb://root@localhost/bugzilla"


repositories = {
    "1": "meqtrees",
    "2": "purr",
    "3": "tigger",
    "4": "wwlcat",
}


Base = automap_base()
engine = create_engine(mysql_uri, echo=True)
Base.prepare(engine, reflect=True)
session = Session(engine)
metadata = MetaData(bind=engine)

Decl_Base = declarative_base()


class Longdescs(Base):
    __table__ = Table('longdescs', metadata, autoload=True)



Bugs = Base.classes.bugs
Profiles = Base.classes.profiles

github = github3.login(username=github_username, password=github_password)

for bug, profile in session.query(Bugs, Longdescs, Profiles).\
                            filter(Bugs.reporter == Profiles.userid).\
                            all():
    short_desc = bug.short_desc
    priority = bug.priority
    version = bug.version
    reporter = profile.realname
    status = bug.bug_status
    severity = bug.bug_severity
    resolution = bug.resolution
    repository = repositories[bug.product_id]
    #assigned_to = bug.assigned_to # todo: create profile mapping?

    labels = []
    if resolution:
        labels.append(resolution.lower())

    print "making new issue"
    issue = github.create_issue(owner=github.user(), repository=repository,
                                title=short_desc, body=short_desc, labels=labels)
    print issue

    if status in ["CLOSED", "RESOLVED"] or resolution in "fixed":
        print "closing issue"
        issue.close()

    print issue


