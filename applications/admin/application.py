from flask import Flask, request, jsonify, make_response
from flask_jwt_extended import JWTManager
from sqlalchemy import and_, func

from admin_decorator import role_check
from configuration import Configuration
from models import database, Participant, ElectionParticipant, Election, Vote
from datetime import datetime
from dateutil import parser

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


def validate_participant(name, individual):
    # all
    if len(name) == 0:
        return "Field name is missing."
    if len(str(individual)) == 0:
        return "Field individual is missing."

    # individual
    # if str(individual) != "True" and str(individual) != "False":
    #     return "Invalid individual."

    return "Validation successful!"


def times_overlapping(start1, end1, start2, end2):
    if start1 < start2 and end1 < start2:
        return False

    if start2 < start1 and end2 < start1:
        return False

    return True


def validate_election(start_time, end_time, individual, participants):
    # all
    if len(str(start_time)) == 0:
        return "Field start is missing."
    if len(str(end_time)) == 0:
        return "Field end is missing."
    if len(str(individual)) == 0:
        return "Field individual is missing."
    if len(str(participants)) == 0:
        return "Field participants is missing."

    # times
    try:
        start = parser.parse(str(start_time))
        end = parser.parse(str(end_time))
    except ValueError:
        return "Invalid date and time."

    if end < start:
        return "Invalid date and time."

    elections = Election.query.all()
    for election in elections:
        if times_overlapping(start, end, parser.parse(str(election.start_time)), parser.parse(str(election.end_time))):
            return "Invalid date and time."

    # participants
    if not participants or len(participants) < 2:
        return "Invalid participants."

    for participant in participants:
        if not Participant.query.get(participant) or Participant.query.get(participant).individual != individual:
            return "Invalid participants."

    return "Validation successful!"


def get_invalid_votes(election):
    invalid_votes = []
    votes = Vote.query.filter(
        and_(
            Vote.election_id == election.id,
            Vote.reason != ""
        )
    ).all()
    for vote in votes:
        data = {
            "electionOfficialJmbg": vote.user_jmbg,
            "ballotGuid": vote.guid,
            "pollNumber": vote.participant_id,
            "reason": vote.reason
        }
        invalid_votes.append(data)

    return invalid_votes


def get_nonindividual_valid_votes(votes, number_of_votes, election_id):
    seats = 250
    all_votes = []
    votes_count = []
    winners_count = []

    for vote in votes:
        if int(vote[1]) > (number_of_votes * 0.05):
            votes_count.append(int(vote[1]))
            all_votes.append(int(vote[1]))
            winners_count.append(0)
        else:
            votes_count.append(int(vote[1]))
            all_votes.append(int(vote[1]))
            winners_count.append(-1)

    print(winners_count)
    print(votes_count)
    for i in range(seats):
        curr_max = -1
        winner = 0
        for j in range(len(votes_count)):
            if winners_count[j] != -1 and votes_count[j] > curr_max:
                curr_max = votes_count[j]
                winner = j

        winners_count[winner] += 1
        votes_count[winner] = all_votes[winner] / (winners_count[winner] + 1)

        print(winner)
        print(winners_count)
        print(votes_count)
        print(all_votes)

    for i in range(len(winners_count)):
        if winners_count[i] == -1:
            winners_count[i] = 0

    valid_votes = []
    index = 0
    for vote in votes:
        obj = ElectionParticipant.query.filter(
            and_(
                ElectionParticipant.election_id == election_id,
                ElectionParticipant.election_participant == vote.participant_id
            )
        ).with_entities(ElectionParticipant.participant_id).first()
        data = {
            "pollNumber": vote.participant_id,
            "name": Participant.query.get(obj).name,
            "result": winners_count[index]
        }
        valid_votes.append(data)
        index += 1

    return valid_votes


def get_individual_valid_votes(votes, number_of_votes, election_id):
    valid_votes = []

    for vote in votes:
        obj = ElectionParticipant.query.filter(
            and_(
                ElectionParticipant.election_id == election_id,
                ElectionParticipant.election_participant == vote.participant_id
            )
        ).with_entities(ElectionParticipant.participant_id).first()
        data = {
            "pollNumber": vote.participant_id,
            "name": Participant.query.get(obj).name,
            "result": float("{:.2f}".format(int(vote[1]) / number_of_votes))
        }
        valid_votes.append(data)

    return valid_votes


def get_valid_votes(election):
    count = func.count(Vote.participant_id)
    votes = Vote.query.filter(
        and_(
            Vote.election_id == election.id,
            Vote.reason == ""
        )
    ).group_by(Vote.participant_id).with_entities(Vote.participant_id, count).all()

    number_of_votes = 0
    for vote in votes:
        number_of_votes += vote[1]

    if election.individual is True:
        return get_individual_valid_votes(votes, number_of_votes, int(election.id))

    return get_nonindividual_valid_votes(votes, number_of_votes, int(election.id))


@application.route("/createParticipant", methods=["POST"])
@role_check(role="admin")
def create_participant():
    name = request.json.get("name", "")
    individual = request.json.get("individual", "")

    response = validate_participant(name, individual)
    if response != "Validation successful!":
        return make_response(jsonify(message=response), 400)

    participant = Participant(name=name, individual=individual)
    database.session.add(participant)
    database.session.commit()

    return make_response(jsonify(id=participant.id), 200)


@application.route("/getParticipants", methods=["GET"])
@role_check(role="admin")
def get_participants():
    json_participants = []
    participants = Participant.query.all()
    for participant in participants:
        data = {
            "id": participant.id,
            "name": participant.name,
            "individual": participant.individual
        }
        json_participants.append(data)

    return make_response(jsonify(participants=json_participants), 200)


@application.route("/createElection", methods=["POST"])
@role_check(role="admin")
def create_election():
    start_time = request.json.get("start", "")
    end_time = request.json.get("end", "")
    individual = request.json.get("individual", "")
    participants = request.json.get("participants", "")

    response = validate_election(start_time, end_time, individual, participants)
    if response != "Validation successful!":
        return make_response(jsonify(message=response), 400)

    election = Election(start_time=parser.parse(str(start_time)), end_time=parser.parse(str(end_time)), individual=individual)
    database.session.add(election)
    database.session.commit()

    index = 1
    poll_numbers = []
    for participant in participants:
        election_participant = ElectionParticipant(election_id=election.id, participant_id=participant, election_participant=index)
        poll_numbers.append(index)
        index += 1
        database.session.add(election_participant)
        database.session.commit()

    return make_response(jsonify(pollNumbers=poll_numbers), 200)


@application.route("/getElections", methods=["GET"])
@role_check(role="admin")
def get_elections():
    json_elections = []
    elections = Election.query.all()
    for election in elections:
        json_participants = []
        participants = Participant.query.join(ElectionParticipant)\
            .filter(ElectionParticipant.election_id == election.id).all()

        index = 1
        for participant in participants:
            participant_data = {
                "id": participant.id,
                "name": participant.name
            }
            json_participants.append(participant_data)

        election_data = {
            "id": election.id,
            "start": str(election.start_time),
            "end": str(election.end_time),
            "individual": election.individual,
            "participants": json_participants
        }

        json_elections.append(election_data)

    return make_response(jsonify(elections=json_elections), 200)


@application.route("/getResults", methods=["GET"])
@role_check(role="admin")
def get_election_results():
    election_id = request.args.get("id", "")
    if election_id == "":
        return make_response(jsonify(message="Field id is missing."), 400)

    election = Election.query.get(int(election_id))
    if not election:
        return make_response(jsonify(message="Election does not exist."), 400)
    if parser.parse(str(election.start_time)) <= parser.parse(str(datetime.now())) \
            <= parser.parse(str(election.end_time)):
        return make_response(jsonify(message="Election is ongoing."), 400)

    return make_response(jsonify(participants=get_valid_votes(election), invalidVotes=get_invalid_votes(election)), 200)


if __name__ == "__main__":
    database.init_app(application)
    application.run(debug=True, host="0.0.0.0", port=5001)