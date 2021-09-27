import sys

from flask import Flask
from redis import Redis
from applications.admin.models import database, Vote, Election, ElectionParticipant
from configuration import Configuration
from datetime import datetime

application = Flask(__name__)
application.config.from_object(Configuration)


def active_election():
    elections = Election.query.all()

    for election in elections:
        if datetime.isoformat(election.start_time) <= datetime.isoformat(datetime.now())\
                <= datetime.isoformat(election.end_time):
            return election

    return None


def check_vote(guid, participant_id, election):
    votes = Vote.query.all()
    for vote in votes:
        if vote.guid == guid:
            return "Duplicate ballot."

    polls = ElectionParticipant.query.filter(ElectionParticipant.election_id == election.id).all()
    poll_numbers = []

    for poll in polls:
        poll_numbers.append(poll.election_participant)

    if not participant_id in poll_numbers:
        return "Invalid poll number."

    return ""


def check_votes():
    with Redis(host=Configuration.REDIS_HOST) as redis:
        current_user = "0000000000000"
        while True:
            votes = redis.lrange(Configuration.REDIS_VOTES_LIST, 0, -1)
            if len(votes) != 0:
                votes_text = redis.lpop(Configuration.REDIS_VOTES_LIST)
                votes_text = votes_text.decode("utf-8")

                votes = votes_text.split(",")
                if votes[0] == "jmbg":
                    current_user = votes[1]
                else:
                    guid = votes[0]
                    participant_id = int(votes[1])
                    election = active_election()
                    # print(str(election), file=sys.stderr)
                    if election is not None:
                        reason = check_vote(guid, participant_id, election)

                        vote = Vote(guid=guid, user_jmbg=current_user, reason=reason, election_id=election.id, participant_id=participant_id)
                        database.session.add(vote)
                        database.session.commit()


with application.app_context() as context:
    database.init_app(application)
    check_votes()

