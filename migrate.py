import mysql.connector
import github3
import logging
from settings import *


id_file = open('id_file', 'a')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

github = github3.login(username=github_username, password=github_password)
con = mysql.connector.connect(user='root', database='bugzilla')

if not owner:
    owner = github.user()

if not assignee:
    assignee = owner.login

q = """
select
    bugs.bug_id as bug_id,
    bugs.short_desc as short,
    bugs.bug_status as status,
    bugs.bug_severity as severity,
    bugs.resolution as resolution,
    bugs.product_id as product,
    bugs.creation_ts as ts,
    profiles.realname as reporter
from
    bugs,
    profiles
where
	bugs.reporter = profiles.userid
order by
    bug_id
;
"""
    # limit
    #1, 18446744073709551615;



q2 = """
select
    longdescs.thetext,
    longdescs.bug_when as ts,
    profiles.realname as reporter
from
    longdescs,
    profiles
where
    bug_id=%s
and
     longdescs.who = profiles.userid
order by
    bug_when
;
"""

repositories = {
    1: "meqtrees",
    2: "purr",
    3: "tigger",
    4: "owlcat",
}


cur = con.cursor()
cur.execute(q)
rows = cur.fetchall()

num_bugs = len(rows)
for row in rows:
    id_, short, status, severity, resolution, product, ts, who = row
    repository = repositories[product]
    labels = []
    if resolution:
        logging.info("adding label: %s" % resolution)
        labels.append(resolution.lower())
    logger.info("making new issue for bug (%s/%s)" % (str(id_), str(num_bugs)))
    formatted = "##### at %s %s reported:\n%s" % (ts, who, short)
    issue = github.create_issue(owner=owner, repository=repository,
                                title=short, body=formatted, labels=labels,
                                assignee=assignee)

    logger.info("bugzilla id: %s, github id: %s" % (id_, issue.number))
    id_file.write("%s -> %s\n" % (id_, issue.number))

    if not issue:
        raise Exception("something went wrong")
    logger.info(issue)

    ## fetch the comments
    cur.execute(q2 % id_)
    rows = cur.fetchall()

    if not len(rows):
        continue

    response = "*Original comment thread migrated from bugzilla*\n\n"
    for row in rows:
        logger.info("adding comment")
        thetext, ts, reporter = row
        thetext = thetext.strip()
        ## github doesn't accept empty comments
        if thetext:
            response += "##### at %s %s replied:\n%s\n\n" % (ts, reporter, thetext)
    issue.create_comment(response)

    ## close the issue (if closed or resolved)
    if status in ["CLOSED", "RESOLVED"]:
        logger.info("closing issue, resolution: %s, status: %s" % (resolution, status))
        issue.close()
    else:
        logger.info("NOT closing issue, resolution: %s, status: %s" % (resolution, status))
