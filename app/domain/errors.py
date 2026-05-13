from enum import Enum


class ParseErrorCode(str, Enum):
    INVALID_FORMAT = "invalid_format"
    INVALID_AMOUNT = "invalid_amount"
    NO_TITLE = "no_title"
    UNKNOWN_PEOPLE = "unknown_people"


class ParseError(Exception):
    def __init__(self, code: ParseErrorCode):
        self.code = code
        super().__init__(code.value)


class SessionErrorCode(str, Enum):
    PAYER_NOT_IN_SESSION = "payer_not_in_session"
    PARTICIPANT_NOT_IN_SESSION = "participant_not_in_session"
    SENDER_NOT_IN_SESSION = "sender_not_in_session"
    RECIPIENT_NOT_IN_SESSION = "recipient_not_in_session"
    TRANSFER_TO_SELF = "transfer_to_self"
    AMOUNT_MUST_BE_POSITIVE = "amount_must_be_positive"


class SessionError(Exception):
    def __init__(self, code: SessionErrorCode):
        self.code = code
        super().__init__(code.value)
