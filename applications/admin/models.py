from flask_sqlalchemy import SQLAlchemy

database = SQLAlchemy()


class ElectionParticipant(database.Model):
    __tablename__ = "elections_participants"

    id = database.Column(database.Integer, primary_key=True)
    participant_id = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable=False)
    election_id = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False)
    election_participant = database.Column(database.Integer, nullable=False)


class Participant(database.Model):
    __tablename__ = "participants"

    id = database.Column(database.Integer, primary_key=True)
    name = database.Column(database.String(256), nullable=False)
    individual = database.Column(database.Boolean, nullable=False)

    elections = database.relationship("Election", secondary=ElectionParticipant.__table__, back_populates="participants")
    votes = database.relationship("Vote", back_populates="participant")

    def __repr__(self):
        return "name: {}, individual: {}".format(self.name, self.individual)


class Election(database.Model):
    __tablename__ = "elections"

    id = database.Column(database.Integer, primary_key=True)
    start_time = database.Column(database.DateTime, nullable=False)
    end_time = database.Column(database.DateTime, nullable=False)
    individual = database.Column(database.Boolean, nullable=False)

    participants = database.relationship("Participant", secondary=ElectionParticipant.__table__, back_populates="elections")
    votes = database.relationship("Vote", back_populates="election")

    def __repr__(self):
        return "start: {}, end: {}, individual: {}".format(self.start_time, self.end_time, self.individual)


class Vote(database.Model):
    __tablename__ = "votes"

    id = database.Column(database.Integer, primary_key=True)
    guid = database.Column(database.String(256), nullable=False)
    reason = database.Column(database.String(256), nullable=False)
    user_jmbg = database.Column(database.String(256), nullable=False)

    participant_id = database.Column(database.Integer, database.ForeignKey("participants.id"), nullable=False)
    participant = database.relationship("Participant", back_populates="votes")

    election_id = database.Column(database.Integer, database.ForeignKey("elections.id"), nullable=False)
    election = database.relationship("Election", back_populates="votes")
