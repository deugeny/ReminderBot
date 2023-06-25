from enum import Enum
from typing import List


class ValidationItemType(Enum):
    TEXT = 0
    INFO = 1
    WARNING = 2
    ERROR = 3

class ValidationKey(Enum):
    NONE = 0
    SECURITY = 1
    INVALID_DATA = 2



class ValidationItem:
    def __init__(self,
                 text: str,
                 key: ValidationKey,
                 item_type: ValidationItemType = ValidationItemType.TEXT
                 ) -> None:
        self.__item_type = item_type
        self.__key = key
        self.__text = text

    @property
    def validation_key(self) -> ValidationKey:
        return self.__key
    @property
    def item_type(self) -> ValidationItemType:
        return self.__item_type
    @property
    def text(self) ->str:
        return self.__text

    def get_message(self) -> str:
        return self.text

    def __str__(self) -> str:
        return self.get_message()

    def __repr__(self) -> str:
        return self.get_message()


class TextValidationItem(ValidationItem):
    def __init__(self, text: str, key: ValidationKey = ValidationKey.NONE) -> None:
        super().__init__(text, key, ValidationItemType.TEXT)

class InfoValidationItem(ValidationItem):
    def __init__(self, text: str, key: ValidationKey = ValidationKey.NONE) -> None:
        super().__init__(text, key, ValidationItemType.INFO)

    def get_message(self) -> str:
        return "ℹ " + self.text

class ErrorValidationItem(ValidationItem):
    def __init__(self, text: str, key: ValidationKey) -> None:
        super().__init__(text, key, ValidationItemType.ERROR)

    def get_message(self) -> str:
        return "❗ " + self.text

class WarningValidationItem(ValidationItem):
    def __init__(self, text: str, key: ValidationKey) -> None:
        super().__init__(text, key, ValidationItemType.WARNING)

    def get_message(self) -> str:
        return "⚠ " + self.text


class ValidationResult:
    def __init__(self,
                 items:List[ValidationItem]):
        assert items is not None
        self.__items = list(items)
        self.__has_error = False
        self.__has_warning = False
        self.__has_info = False
        self.__message = ""
        prefix = ""
        for item in self.__items:
            if item.item_type == ValidationItemType.ERROR:
                self.__has_error = True
            if item.item_type == ValidationItemType.WARNING:
                self.__has_warning = True
            if item.item_type == ValidationItemType.INFO:
                self.__has_info = True
            text = item.get_message()
            if text:
                self.__message += ''.join([prefix, text])
                prefix = "\n"


    def has_validation_key(self, validation_key: ValidationKey) -> bool:
        for item in self.__items:
            if item.validation_key == validation_key:
                return True
        return False

    @property
    def has_info(self) -> bool:
        return self.__has_info
    @property
    def has_errors(self) -> bool:
        return self.__has_error

    @property
    def has_warning(self) -> bool:
        return self.__has_warning

    @property
    def is_valid(self) -> bool:
        return not (self.__has_warning or self.__has_error)

    @property
    def message(self) -> str:
        return self.__message

    def __add__(self, other):
        assert other is not None
        assert issubclass(type(other), ValidationResult)
        return ValidationResult(self.__items + other.__items)



class Validation:
    def __init__(self) -> None:
        self.__items : List[ValidationItem] = []

    @staticmethod
    def start():
        return Validation()
    def info(self, text: str, condition: bool = True, key: ValidationKey = ValidationKey.NONE) -> "Validation":
        if condition:
            self.__items.append(InfoValidationItem(key = key, text = text))
        return self
    def error(self, text:str, key: ValidationKey, condition: bool = True) -> "Validation":
        if condition:
            self.__items.append(ErrorValidationItem(key = key, text = text))
        return self

    def warning(self, text: str, key: ValidationKey, condition: bool = True) -> "Validation":
        if condition:
            self.__items.append(WarningValidationItem(key = key, text = text))
        return self

    def text(self, text:str, condition: bool = True, key: ValidationKey = ValidationKey.NONE) -> "Validation":
        if condition:
            self.__items.append(WarningValidationItem(key = key, text = text))
        return self

    def build(self) -> ValidationResult:
        return ValidationResult(self.__items)
