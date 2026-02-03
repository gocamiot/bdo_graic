from django.db import models

class InherentImpact(models.TextChoices):
    INSIGNIFICANT = 'INSIGNIFICANT', 'Insignificant'
    MINOR = 'MINOR', 'Minor'
    MODERATE = 'MODERATE', 'Moderate'
    MAJOR = 'MAJOR', 'Major'
    SEVERE = 'SEVERE', 'Severe'


class Likelihood(models.TextChoices):
    FREQUENT = 'FREQUENT', 'A-Frequent'
    PROBABLE = 'PROBABLE', 'B-Probable'
    OCCASIONAL = 'OCCASIONAL', 'C-Occasional'
    REMOTE = 'REMOTE', 'D-Remote'
    IMPROGRABLE = 'IMPROGRABLE', 'E-Improbable'
    ELIMINATED = 'ELIMINATED', 'F-Eliminated'


class ResidualRiskRating(models.TextChoices):
    CATASTROPHIC = 'CATASTROPHIC', '1-Catastrophic'
    CRITICAL = 'CRITICAL', '2-Critical'
    MARGINAL = 'MARGINAL', '3-Marginal'
    NEGLIGIBLE = 'NEGLIGIBLE', '4-Negligible'


class ConfidenceInResults(models.TextChoices):
    HIGH = 'HIGH', 'High (100%)'
    MEDIUM = 'MEDIUM', 'Medium (70%)'
    LOW = 'LOW', 'Low (30%)'


class PrimaryRootCause(models.TextChoices):
    PROCESS_GAP = 'PROCESS_GAP', 'Process gap'
    POLICY_NOT_ENFORCED = 'POLICY_NOT_ENFORCED', 'Policy not enforced'
    SYSTEM_CONFIGURATION = 'SYSTEM_CONFIGURATION', 'System configuration'
    HUMAN_ERROR = 'HUMAN_ERROR', 'Human error'
    TOOL_LIMITATION = 'TOOL_LIMITATION', 'Tool limitation'
    THIRD_PARTY_DEPENDENCY = 'THIRD_PARTY_DEPENDENCY', 'Third-party dependency'


class SecondaryRootCause(models.TextChoices):
    PROCESS_GAP = 'PROCESS_GAP', 'Process gap'
    POLICY_NOT_ENFORCED = 'POLICY_NOT_ENFORCED', 'Policy not enforced'
    SYSTEM_CONFIGURATION = 'SYSTEM_CONFIGURATION', 'System configuration'
    HUMAN_ERROR = 'HUMAN_ERROR', 'Human error'
    TOOL_LIMITATION = 'TOOL_LIMITATION', 'Tool limitation'
    THIRD_PARTY_DEPENDENCY = 'THIRD_PARTY_DEPENDENCY', 'Third-party dependency'


class BusinessImpact(models.TextChoices):
    SECURITY_BREACH = 'SECURITY_BREACH', 'Security breach risk'
    FINANCIAL_LOSS = 'FINANCIAL_LOSS', 'Financial loss'
    REGULATORY_NON_COMPLIANCE = 'REGULATORY_NON_COMPLIANCE', 'Regulatory non-compliance'
    OPERATIONAL_DISRUPTION = 'OPERATIONAL_DISRUPTION', 'Operational disruption'
    REPUTATIONAL_DAMAGE = 'REPUTATIONAL_DAMAGE', 'Reputational damage'


class OwnerRoleChoices(models.TextChoices):
    IT = 'IT', 'IT'
    HR = 'HR', 'HR'
    SECURITY = 'SECURITY', 'Security'
    FINANCE = 'FINANCE', 'Finance'
    OPERATIONS = 'OPERATIONS', 'Operations'
    VENDOR = 'VENDOR', 'Vendor'


RISK_MATRIX = {
    'FREQUENT': {
        'CATASTROPHIC': 'High',
        'CRITICAL': 'High',
        'MARGINAL': 'Serious',
        'NEGLIGIBLE': 'Medium',
    },
    'PROBABLE': {
        'CATASTROPHIC': 'High',
        'CRITICAL': 'High',
        'MARGINAL': 'Serious',
        'NEGLIGIBLE': 'Medium',
    },
    'OCCASIONAL': {
        'CATASTROPHIC': 'High',
        'CRITICAL': 'Serious',
        'MARGINAL': 'Medium',
        'NEGLIGIBLE': 'Low',
    },
    'REMOTE': {
        'CATASTROPHIC': 'Serious',
        'CRITICAL': 'Medium',
        'MARGINAL': 'Medium',
        'NEGLIGIBLE': 'Low',
    },
    'IMPROGRABLE': {
        'CATASTROPHIC': 'Medium',
        'CRITICAL': 'Medium',
        'MARGINAL': 'Medium',
        'NEGLIGIBLE': 'Low',
    },
    'ELIMINATED': {
        'CATASTROPHIC': 'Eliminated',
        'CRITICAL': 'Eliminated',
        'MARGINAL': 'Eliminated',
        'NEGLIGIBLE': 'Eliminated',
    }
}

CONFIDENCE_PERCENTAGE = {
    'HIGH': 100,
    'MEDIUM': 70,
    'LOW': 30,
}
