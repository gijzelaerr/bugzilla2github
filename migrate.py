import mysql.connector
import github3
import logging
from settings import *

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not owner:
    owner = github.user()

if not assignee:
    assignee = owner.username

q = """
select
    bugs.bug_id as bug_id,
    bugs.short_desc as short,
    bugs.bug_status as status,
    bugs.bug_severity as severity,
    bugs.resolution as resolution,
    bugs.product_id as product
from
    bugs
order by
    bug_id
"""

q2 = """
select
    thetext
from
    longdescs
where
    bug_id=%s
order by
    bug_when
"""

repositories = {
    1: "meqtrees",
    2: "purr",
    3: "tigger",
    4: "owlcat",
}

github = github3.login(username=github_username, password=github_password)
con = mysql.connector.connect(user='root', database='bugzilla')
cur = con.cursor()
cur.execute(q)
rows = cur.fetchall()

for row in rows:
    id, short, status, severity, resolution, product = row
    repository = repositories[product]
    labels = []
    if resolution:
        labels.append(resolution.lower())
    logger.info("making new issue for bug " + str(id))
    issue = github.create_issue(owner=owner, repository=repository,
                                title=short, body=short, labels=labels,
                                assignee=assignee)
    if not issue:
        raise Exception("something went wrong")
    logger.info(issue)
    if status in ["CLOSED", "RESOLVED"] or resolution in "fixed":
        logger.info("closing issue")
        issue.close()
    cur.execute(q2 % id)
    rows = cur.fetchall()
    for row in rows:
        logger.info("adding comment")
        thetext = row[0]
        issue.create_comment(thetext)
