from sqlalchemy import String
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine

from settings import get_settings

cfg = get_settings()

EncryptedStr = StringEncryptedType(String, cfg.encryption_key, FernetEngine)
