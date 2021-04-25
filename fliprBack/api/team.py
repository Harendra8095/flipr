from fliprBack.models.userModel import Userteam
from flask import Blueprint, request
from flask.globals import session
from fliprBack.constants import *
from fliprBack.models import *
from fliprBack.response import *
from fliprBack.auth import *

teamBP = Blueprint('teamApi', __name__)


@teamBP.route('/matches', methods=['GET'])
def matches():
    auth_token = request.headers.get('auth-token')
    if not auth_token:
        return make_response("No 'auth-token' in header", HTTPStatus.NoToken)
    valid_token, usr_ = validate_token(auth_token)
    if not valid_token:
        if usr_ == Constants.InvalidToken:
            return make_response("Invalid token", HTTPStatus.InvalidToken)
        elif usr_ == Constants.TokenExpired:
            return make_response("Token expired.", HTTPStatus.InvalidToken)
        else:
            return make_response("User not verified", HTTPStatus.UnAuthorised)
    else:
        from server import SQLSession
        session = SQLSession()
        connection = session.connection()
        q = session.query(Match).all()
        payload = []
        for i in q:
            payload.append(
                {
                    "match_id": i.id,
                    "start_date": i.start_date,
                    "team1": i.team1,
                    "team2": i.team2,
                    "match_status": i.match_status
                }
            )
        session.close()
        connection.close()
        return make_response("success", HTTPStatus.Success, payload)


@teamBP.route('/playerlist', methods=['POST'])
def playerlist():
    auth_token = request.headers.get('auth-token')
    if not auth_token:
        return make_response("No 'auth-token' in header", HTTPStatus.NoToken)
    valid_token, usr_ = validate_token(auth_token)
    data = request.json
    required_parameters = ['match_id']
    if (set(required_parameters)-data.keys()):
        return make_response("Missing Input.", HTTPStatus.BadRequest)
    if not valid_token:
        if usr_ == Constants.InvalidToken:
            return make_response("Invalid token", HTTPStatus.InvalidToken)
        elif usr_ == Constants.TokenExpired:
            return make_response("Token expired.", HTTPStatus.InvalidToken)
        else:
            return make_response("User not verified", HTTPStatus.UnAuthorised)
    else:
        match_id = data['match_id']
        from server import SQLSession
        session = SQLSession()
        connection = session.connection()
        p_l = session.query(Playermatch).filter_by(match_id=match_id).all()
        payload = []
        for i in p_l:
            payload.append(
                {
                    "player_id": i.player.id,
                    "playername": i.player.playername,
                    "credit_value": i.player.credit_value
                }
            )
        session.close()
        connection.close()
        return make_response("success", HTTPStatus.Success, payload)


@teamBP.route('/addtoteam', methods=['POST'])
def addtoteam():
    auth_token = request.headers.get('auth-token')
    if not auth_token:
        return make_response("No 'auth-token' in header", HTTPStatus.NoToken)
    valid_token, usr_ = validate_token(auth_token)
    data = request.json
    required_parameters = ['match_id', 'player_id']
    if (set(required_parameters)-data.keys()):
        return make_response("Missing Input.", HTTPStatus.BadRequest)
    if not valid_token:
        if usr_ == Constants.InvalidToken:
            return make_response("Invalid token", HTTPStatus.InvalidToken)
        elif usr_ == Constants.TokenExpired:
            return make_response("Token expired.", HTTPStatus.InvalidToken)
        else:
            return make_response("User not verified", HTTPStatus.UnAuthorised)
    else:
        match_id = data['match_id']
        player_id = data['player_id']
        from server import SQLSession
        session = SQLSession()
        connection = session.connection()
        my_team = session.query(Userteam).join(Userteam.playermatch).filter(
            Userteam.user_id == usr_.id).filter(Playermatch.match_id == match_id).all()
        credit_spent = 0
        team_size = 0
        for i in my_team:
            credit_spent += i.playermatch.player.credit_value
            team_size += 1
        if team_size >= 11:
            session.close()
            connection.close()
            return make_response("Team size full.", HTTPStatus.BadRequest)
        p_m_id = session.query(Playermatch).filter_by(
            match_id=match_id).filter_by(player_id=player_id).first()
        if p_m_id == None:
            session.close()
            connection.close()
            return make_response("No such player for this match.", HTTPStatus.BadRequest)
        userteam = Userteam(
            user_id=usr_.id,
            playermatch_id=p_m_id.id,
            credit_bal=p_m_id.player.credit_value
        )
        payload = {
            "credit_spent": credit_spent+p_m_id.player.credit_value,
            "team_size": team_size+1,
        }
        session.add(userteam)
        session.commit()
        session.close()
        connection.close()
        return make_response("success", HTTPStatus.Success, payload)


@teamBP.route('/removefromteam', methods=['POST'])
def removefromteam():
    auth_token = request.headers.get('auth-token')
    if not auth_token:
        return make_response("No 'auth-token' in header", HTTPStatus.NoToken)
    valid_token, usr_ = validate_token(auth_token)
    data = request.json
    required_parameters = ['match_id', 'player_id']
    if (set(required_parameters)-data.keys()):
        return make_response("Missing Input.", HTTPStatus.BadRequest)
    if not valid_token:
        if usr_ == Constants.InvalidToken:
            return make_response("Invalid token", HTTPStatus.InvalidToken)
        elif usr_ == Constants.TokenExpired:
            return make_response("Token expired.", HTTPStatus.InvalidToken)
        else:
            return make_response("User not verified", HTTPStatus.UnAuthorised)
    else:
        match_id = data['match_id']
        player_id = data['player_id']
        from server import SQLSession
        session = SQLSession()
        connection = session.connection()
        p_m_id = session.query(Playermatch).filter_by(
            match_id=match_id).filter_by(player_id=player_id).first()
        if p_m_id == None:
            session.close()
            connection.close()
            return make_response("No such player for this match.", HTTPStatus.BadRequest)
        del_player = session.query(Userteam).filter_by(
            user_id=usr_.id).filter_by(playermatch_id=p_m_id.id)
        del_player.delete()
        session.commit()
        my_team = session.query(Userteam).join(Userteam.playermatch).filter(
            Userteam.user_id == usr_.id).filter(Playermatch.match_id == match_id).all()
        credit_spent = 0
        team_size = 0
        for i in my_team:
            credit_spent += i.playermatch.player.credit_value
            team_size += 1
        payload = {
            "credit_spent": credit_spent,
            "team_size": team_size,
        }
        session.close()
        connection.close()
        return make_response("success", HTTPStatus.Success, payload)
