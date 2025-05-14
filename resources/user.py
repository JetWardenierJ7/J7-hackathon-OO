"""This module facilitates all user interactions"""

from datetime import datetime, timedelta
from flask import request
from flask.views import MethodView
from flask_smorest import Blueprint, abort, error_handler
from passlib.hash import pbkdf2_sha256
from flask_jwt_extended import (
    create_access_token,
    get_jwt,
    jwt_required,
)
from db import db
from blocklist import BLOCKLIST
from models import UserModel
from schemas import (
    DefaultResponseSchema,
    LoginReponseSchema,
    UserSchema,
    UserUpdateSchema,
    UserPasswordSchema,
    UserCreatedSchema,
)
from .resource_classes import (
    LoginRequirements,
    LastLogin,
    is_global_admin,
    global_administrator_required,
)


blp = Blueprint("Users", "users", description="Operations on users")


@blp.route("/register")
class UserRegister(MethodView):
    """Registers new users to the API"""

    # @jwt_required()
    # @global_administrator_required()
    @blp.arguments(UserSchema)
    @blp.response(200, UserCreatedSchema)
    @blp.alt_response(
        403,
        schema=error_handler.ErrorSchema,
        description="Requesting user does not have sufficient permissions to create a user",
    )
    @blp.alt_response(
        404,
        schema=error_handler.ErrorSchema,
        description="The company of the user was not found",
    )
    @blp.alt_response(
        409, schema=error_handler.ErrorSchema, description="Username already exists"
    )
    @blp.alt_response(
        422, schema=error_handler.ErrorSchema, description="Password validation failed"
    )
    def post(self, user_data):
        """Processes the creation of a user

        :param user_data:
            A dictionary containing the data to create the user with

        :returns: A string, explaining if the creation of the user was successfull
        :rtype: ``Str``

        :raises 403 Forbidden:
            Requesting user does not have sufficient permissions to create a user

        :raises 404 Not found:
            The company of the user was not found

        :raises 409 Already Exists:
            Username already exists

        :raises 422 Validation Failed:
            Password validation failed

        """

        # user = UserModel.query.get_or_404(get_jwt()["sub"])
        # if UserModel.query.filter(UserModel.username == user_data["username"]).first():
        #     abort(409, message="A user with that username already exists.")

        password_requirements = LoginRequirements(
            password=user_data["password"]
        ).check_password()

        if password_requirements:
            return {
                "message": "Password validation failed.",
                "failed_checks": password_requirements,
            }, 422
        else:
            user = UserModel(
                username=user_data["username"],
                password=pbkdf2_sha256.hash(user_data["password"]),
                name=user_data["name"],
                surname=user_data.get("surname"),
                status=True,
                mailings=True,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                role=user_data["role"],
                display_name=user_data["name"] + " " + user_data.get("surname"),
            )
            db.session.add(user)
            db.session.commit()

            return {"user_id": user.id}


@blp.route("/login")
class UserLogin(MethodView):
    """Login functionallity for Users of the API"""

    @blp.arguments(UserSchema)
    @blp.response(200, LoginReponseSchema)
    @blp.alt_response(
        403, schema=error_handler.ErrorSchema, description="Trial period has expired"
    )
    def post(self, user_data):
        """Processes the login request by a user

        :param user_data:
            A dictionary containing the data to perform a login request

        :returns: A string in the form of an Access token
        :rtype: ``Access token``

        :raises 403 Forbidden:
            Trial period has expired

        The login request will fail if;
        - The user cannot be found or the password is incorrect

        When a login is successfull, the following will be executed;
        - Add a claim to the Access token with admin information
        - Log the new login in the user_logins table with IP and timezone info
        - Update existing notifications unread notifications to read
        - If the login of a user was > 7 days ago, create a notification

        """
        user = UserModel.query.filter(
            UserModel.username == user_data["username"]
        ).first()

        if user and pbkdf2_sha256.verify(user_data["password"], user.password):
            access_token = create_access_token(
                identity=user.id,
                expires_delta=timedelta(days=1),
                additional_claims={"is_global_admin": is_global_admin(user)},
            )

            return {"access_token": access_token}, 200

        abort(401, message="Invalid credentials.")


@blp.route("/logout")
class UserLogout(MethodView):
    """Logout functionallity for Users of the API 2"""

    @jwt_required()
    @blp.response(200, DefaultResponseSchema)
    def post(self):
        """Places the access_token of the logged_in user into the blocklist"""
        jti = get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message": "Successfully logged out."}, 200


@blp.route("/user/<int:user_id>")
class User(MethodView):
    """Interactions with the User object"""

    @jwt_required()
    @global_administrator_required()
    @blp.response(200, UserSchema)
    @blp.alt_response(
        403,
        schema=error_handler.ErrorSchema,
        description="The requesting user does not have sufficient permissions",
    )
    @blp.alt_response(
        404, schema=error_handler.ErrorSchema, description="The user (id) was not found"
    )
    def get(self, user_id):
        """Retrieves a ``User`` object by it's identifier

        :param user_id:
            An integer representing the identifier of the user

        :returns: The ``User`` object
        :rtype: UserModel

        :raises 403 Forbidden:
            The requesting user does not have sufficient permissions

        :raises 404 Not found:
            The user (id) was not found

        """
        user = UserModel.query.get_or_404(user_id)

        return user

    @jwt_required()
    @global_administrator_required()
    @blp.response(200, DefaultResponseSchema)
    @blp.alt_response(
        403,
        schema=error_handler.ErrorSchema,
        description="The requesting ``User`` does not have sufficient permissions",
    )
    @blp.alt_response(
        404, schema=error_handler.ErrorSchema, description="The user (id) was not found"
    )
    def delete(self, user_id):
        """Deletes a ``User`` object by it's identifier

        :param user_id: An integer representing the identifier of the user
        :returns: A message telling the user if the action succeeded
        :rtype: Str
        :raises 403 Forbidden: The requesting user does not have sufficient permissions
        :raises 404 Not found: The user (id) was not found

        """
        targeted_user = UserModel.query.get_or_404(user_id)

        db.session.delete(targeted_user)
        db.session.commit()

        return {"message": "User deleted."}, 200

    @jwt_required()
    @global_administrator_required()
    @blp.arguments(UserUpdateSchema)
    @blp.response(200, UserSchema)
    @blp.alt_response(
        403,
        schema=error_handler.ErrorSchema,
        description="The requesting user does not have sufficient permissions",
    )
    @blp.alt_response(
        404, schema=error_handler.ErrorSchema, description="The user (id) was not found"
    )
    def put(self, user_data, user_id):
        """Updates a ``User`` object by it's id with the provided data

        :param user_id: An integer representing the identifier of the ``User`` object
        :returns: The updated ``User`` object
        :rtype: UserModel
        :raises 403 Forbidden: The requesting user does not have sufficient permissions
        :raises 404 Not found: The user (id) was not found

        """
        user = UserModel.query.get_or_404(user_id)

        user.name = user_data.get("name")
        user.surname = user_data.get("surname")
        user.mailings = user_data.get("mailings")
        user.display_name = user_data.get("name") + " " + user_data.get("surname")
        user.updated_at = datetime.now()

        db.session.add(user)
        db.session.commit()

        return user


@blp.route("/user/<int:user_id>/change_password")
class UserChangePassword(MethodView):
    """This class is responsible for changing the user's password"""

    @jwt_required()
    @blp.arguments(UserPasswordSchema)
    @blp.response(200, DefaultResponseSchema)
    @blp.alt_response(
        403,
        schema=error_handler.ErrorSchema,
        description="The user is not allowed to change the password",
    )
    @blp.alt_response(
        406,
        schema=error_handler.ErrorSchema,
        description="The passwords do not match",
    )
    @blp.alt_response(
        422,
        schema=error_handler.ErrorSchema,
        description="Password validation failed",
    )
    def put(self, password_data, user_id):
        """Changes the password for the current ``User`` object

        :param user_id:
            An integer representing the identifier of the ``User`` object

        :param password_data:
            The new and confirming passwords

        :returns: A message explaining if the changing process succeeded.
        :rtype: Str

        :raises 403 Forbidden:
            The user is not allowed to change the password

        :raises 406 No match:
            The passwords do not match

        :raises 422 Validation failed:
            Password validation failed

        The ``User`` will be logged out after changing the password.

        """
        user = UserModel.query.get_or_404(user_id)

        # Check requesting user permissions
        if user_id != get_jwt()["sub"]:
            return {"message": "This user is not allowed to change this password."}, 403

        if password_data["new_password"] != password_data["new_password_confirmation"]:
            return {"message": "The passwords do not match"}, 406

        password_requirements = LoginRequirements(
            password=password_data["new_password"]
        ).check_password()

        if password_requirements:
            return {
                "message": "Password validation failed.",
                "failed_checks": password_requirements,
            }, 422

        user.password = pbkdf2_sha256.hash(password_data["new_password"])

        db.session.add(user)
        db.session.commit()

        if user_id == get_jwt()["sub"]:
            jti = get_jwt()["jti"]
            BLOCKLIST.add(jti)

        return {"message": "Pasword changed."}, 200


@blp.route("/user/me")
class CurrentUser(MethodView):
    """Retrieves informatie from the logged in user"""

    @jwt_required()
    @blp.response(200, UserSchema)
    @blp.alt_response(
        404,
        schema=error_handler.ErrorSchema,
        description="The user was not found",
    )
    def get(self):
        """Returns a User object by the access_token

        :param user_id:
            An integer representing the identifier of the ``User`` object

        :returns:
            The ``User`` object.
        :rtype: UserModel

        :raises 404 Not found:
            The ``User`` object could not be found by it's identifier

        """
        user = UserModel.query.get_or_404(get_jwt()["sub"])
        return user
