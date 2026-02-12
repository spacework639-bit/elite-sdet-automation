from enum import Enum


class FailureType(str, Enum):
    VALIDATION = "ValidationError"
    BUSINESS = "BusinessRuleViolation"
    DATA = "DataIntegrityError"
    SYSTEM = "SystemError"
    FLAKY = "Flaky"


class Severity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"
