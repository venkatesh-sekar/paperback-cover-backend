import hashlib
import uuid


def hash_user_id(user_uuid: uuid.UUID) -> str:
    """Do not use it for identifying user. This is originally created to hash images so the path doesnt contain the user id

    Args:
        user_uuid (uuid.UUID): _description_

    Returns:
        str: _description_
    """
    return hashlib.sha256(user_uuid.bytes).hexdigest()[:12]
