from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import User
from app.schemas.pagination import PaginationParams, PaginationResponse
from app.schemas.user import UserCreate, UserResource, UserUpdate


def paginate(
    session: Session,
    pagination: PaginationParams
) -> PaginationResponse[UserResource]:
    """
    Paginates through User records obtained from the database based on the provided
    pagination parameters.

    Args:
        session: The database session used to execute queries.
        pagination: The pagination parameters for managing page size and offset.

    Returns:
        PaginationResponse[User]: A paginated response containing metadata and a
        list of User records.
    """
    query = select(User)
    # TODO: Extract pagination logic from resource specific services (repository pattern?)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0

    query = query.offset(pagination.get_skip).limit(pagination.per_page)
    result = session.execute(query).scalars().all()

    return PaginationResponse(**pagination.get_pagination_metadata(total), data=result)



def get_all(session: Session) -> Sequence[User]:
    """
    Fetches all ``User`` entities from the database.

    Args:
        session (Session): The database session used for query execution.

    Returns:
        Sequence[User]: A sequence containing all User entities from the database.
    """
    stmt = select(User)

    return session.execute(stmt).scalars().all()


def find_user_by_id(session: Session, user_id: UUID) -> User | None:
    """
    Finds and returns a user by their unique identifier from the database.

    Args:
        session (Session): The database session used to execute the query.
        user_id (UUID): The unique identifier of the user to find.

    Returns:
        User | None: The User object if a matching user is found; otherwise, None.
    """
    stmt = select(User).where(User.id == user_id)

    return session.execute(stmt).scalar_one_or_none()


def create_user(session: Session, user_in: UserCreate) -> User:
    """
    Creates a new user in the database by hashing the password and saving the user's details.

    Args:
        session (Session): Database session used to interact with the database.
        user_in (UserCreate): Data input for creating a new user.

    Returns:
        User: The newly created `User` instance saved in the database.
    """
    data = user_in.model_dump(exclude_unset=True, exclude_defaults=True)
    data["password"] = hash_password(user_in.password.get_secret_value())

    db_user = User(**data)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return db_user


def update_user(session: Session, user_id: UUID, payload: UserUpdate) -> User | None:
    """
    Updates the user information in the database.

    Args:
        session (Session): The database session used to retrieve and update the user.
        user_id (UUID): The identifier of the user whose information is to be updated.
        payload (UserUpdate): The data containing the updated information for the user.

    Returns:
        User | None: The updated user instance if the user exists, otherwise `None`.
    """
    user = find_user_by_id(session, user_id)
    if not user:
        return None

    user.update(payload)
    session.commit()
    session.refresh(user)

    return user


def delete_user(session: Session, user_id: UUID) -> None:
    """
    Deletes a user from the database by their unique identifier. If the user does not exist,
    the operation is a no-op.

    Args:
        session (Session): The database session to use for querying and committing changes.
        user_id (UUID): The unique identifier of the user to be deleted.

    Returns:
        None
    """
    user = find_user_by_id(session, user_id)
    if not user:
        return

    session.delete(user)
    session.commit()
