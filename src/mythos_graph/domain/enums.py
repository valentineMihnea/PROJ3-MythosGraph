"""Core domain enumerations for entities, relationships, and mythological cycles."""

from enum import StrEnum


class EntityCategory(StrEnum):
    """Canonical classification of mythological figures."""

    PRIMORDIAL = "PRIMORDIAL"
    TITAN = "TITAN"
    OLYMPIAN = "OLYMPIAN"
    DEMIGOD = "DEMIGOD"
    MORTAL = "MORTAL"
    CREATURE = "CREATURE"


class RelationType(StrEnum):
    """Directed semantic relationship types between mythological entities."""

    PARENT_OF = "PARENT_OF"
    CHILD_OF = "CHILD_OF"
    SPOUSE_OF = "SPOUSE_OF"
    CONSORT_OF = "CONSORT_OF"
    SIBLING_OF = "SIBLING_OF"
    SLAYER_OF = "SLAYER_OF"
    PATRON_OF = "PATRON_OF"
    ALLIED_WITH = "ALLIED_WITH"


class MythologicalCycle(StrEnum):
    """Major classical epochs and narrative cycles."""

    TITANOMACHY = "TITANOMACHY"
    ARGONAUTIC_EXPEDITION = "ARGONAUTIC_EXPEDITION"
    TROJAN_WAR = "TROJAN_WAR"
    SEVEN_AGAINST_THEBES = "SEVEN_AGAINST_THEBES"
    GENERAL = "GENERAL"
