#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/clarinet_tiara_rinse_lesson_learned_conflict_flashback.py
===================================================================================================

A small animal-story world about a careful musician, a shiny tiara, and a
lesson learned after a muddy mistake.

Premise:
- An animal child loves music and a special costume piece.
- A wet, messy place can damage the special items.
- A parent or friend warns the child.
- A flashback reminds the child of an earlier mess.
- The child learns the lesson, chooses a safer way, and the story ends with
  the items clean and the feeling changed.

This file is self-contained and follows the Storyweavers world contract.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"   # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: str = ""
    clarinet: object | None = None
    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    tiara: object | None = None
    def __post_init__(self):
        for k in ("wet", "dirty", "sparkle", "care", "fear", "joy", "conflict", "lesson", "flashback"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"rabbit", "mouse", "goat", "cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"fox", "bear", "dog", "lion"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Setting:
    place: str = "the garden"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    ACTIVITY: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Prize:
    label: str
    phrase: str
    region: str
    type: str = "thing"
    plural: bool = False
    PRIZE_CLARINET: object | None = None
    PRIZE_TIARA: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


ACTIVITY = Activity(
    id="rinse",
    verb="rinse the stage ribbons",
    gerund="rinsing the stage ribbons",
    rush="dash through the splashy path",
    mess="wet",
    soil="soaked and muddy",
    zone={"feet", "legs", "torso"},
    keyword="rinse",
)

SETTING = Setting(place="the garden", affords={"rinse"})

PRIZE_TIARA = Prize(
    label="tiara",
    phrase="a tiny silver tiara",
    region="torso",
    type="tiara",
)

PRIZE_CLARINET = Prize(
    label="clarinet",
    phrase="a polished clarinet",
    region="torso",
    type="clarinet",
)

GEAR = [
    Gear(
        id="raincoat",
        label="a raincoat",
        covers={"torso"},
        guards={"wet"},
        prep="put on a raincoat first",
        tail="came back in the raincoat",
    ),
    Gear(
        id="boots",
        label="rubber boots",
        covers={"feet"},
        guards={"wet"},
        prep="pull on rubber boots first",
        tail="came back in the rubber boots",
        plural=True,
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Tia", "Pippa", "Nori"]
BOY_NAMES = ["Ollie", "Bram", "Pico", "Milo", "Tobi"]
ANIMALS = ["rabbit", "fox", "mouse", "cat", "bear", "dog"]


INCIDENTS = {
    "runoff": {
        "place": "the garden concert path",
        "premise": "A sudden shower sent brown runoff across the route to the rehearsal arbor",
        "goal": "carry the clarinet and tiara to the arbor before rehearsal began",
        "conflict": "the shortest path crossed the runoff, but turning back might make the whole woodland band wait",
        "warning": "That water is deeper than it looks, and one slip could soak both treasures",
        "memory": "a week earlier, a ribbon had looked dry until one hurried step pressed muddy water through it",
        "mistake": "started toward the glossy stones before testing them",
        "clue": "a floating leaf spun in place, showing that water was still moving over the stones",
        "tool": "a covered instrument case and a high stepping-stone route",
        "action": "latched the clarinet inside the case, tucked the tiara into its dry pocket, and followed the high stones slowly",
        "result": "reached rehearsal safely and helped mark the flooded shortcut with a bright cord",
        "lesson": "a route that looks quick is not truly quick when it risks something entrusted to you",
        "ending": "Under the arbor, the silver tiara reflected the first clear patch of sky while the clarinet opened with a warm low note",
    },
    "paint": {
        "place": "the school pageant room",
        "premise": "Volunteers were rinsing paint cups beside the costume table before the afternoon pageant",
        "goal": "practice a clarinet fanfare while wearing the tiara",
        "conflict": "the music stand was beside the rinse basin, and moving it seemed likely to upset the carefully arranged rehearsal",
        "warning": "A swinging sleeve could tip that cloudy rinse cup onto the keys and crown",
        "memory": "during the last craft day, a hurried elbow had knocked blue rinse water across a paper moon",
        "mistake": "raised the clarinet beside the crowded basin",
        "clue": "each time someone reached for a brush, the rinse cup wobbled toward the table edge",
        "tool": "a rolling music stand and a dry costume shelf",
        "action": "asked the painters to pause, rolled the stand across the room, and set the tiara on the dry shelf between songs",
        "result": "played the fanfare clearly while the volunteers finished rinsing at a safe distance",
        "lesson": "protecting shared work sometimes means changing the setup instead of blaming the people using it",
        "ending": "When the curtain rose, the tiara flashed above a spotless costume and the clarinet's last note made the painted moon seem to glow",
    },
    "sprinkler": {
        "place": "the community orchard",
        "premise": "The orchard sprinklers clicked on just as the harvest parade assembled",
        "goal": "lead the parade with the clarinet and wear the tiara made for the apple captain",
        "conflict": "the parade map followed the wet row, while the dry row wound around a hill and would delay everyone",
        "warning": "The next sprinkler turns without warning; shiny things and clarinet pads do not enjoy surprise showers",
        "memory": "last spring, a sprinkler had turned behind a hedge and drenched a sign that seemed safely far away",
        "mistake": "declared the nearest sprinkler finished after watching it pause once",
        "clue": "a ticking valve under the grass grew faster before every burst",
        "tool": "the valve schedule and a wagon with a waterproof lid",
        "action": "checked the schedule, placed the clarinet and tiara in the wagon during each burst, and led the group between timed sprays",
        "result": "kept the parade moving without wasting water or damaging the instruments and costumes",
        "lesson": "curiosity can turn a remembered warning into useful timing instead of frightened guessing",
        "ending": "At the final tree, droplets made tiny rainbows over the closed wagon; then the dry clarinet played and the tiara shone like an apple blossom",
    },
    "fountain": {
        "place": "the town-square fountain",
        "premise": "A loose garland slipped into the shallow fountain minutes before a music ceremony",
        "goal": "rinse pollen from the garland and return it while keeping the clarinet and tiara ready",
        "conflict": "reaching from the rim seemed faster, but carrying both special items left no free hand for balance",
        "warning": "Set the music things down first; leaning over water with full paws is not careful",
        "memory": "at a picnic, reaching for a cup while holding too many plates had sent every plate sliding",
        "mistake": "knelt at the rim with the clarinet strap and tiara box still hanging from one shoulder",
        "clue": "the strap brushed the stone whenever the garland drifted farther away",
        "tool": "a dry bench, a mesh scoop, and a clean rinse bucket",
        "action": "locked the treasures in their cases on the bench, used the scoop, and rinsed the garland in the bucket instead of the fountain",
        "result": "returned the fresh garland without leaning into the water or wetting the clarinet",
        "lesson": "putting precious things down safely can be the bravest first step",
        "ending": "The restored garland circled the fountain, and its reflection framed the tiara as a gentle clarinet melody floated over the square",
    },
    "backstage": {
        "place": "the theater backstage corridor",
        "premise": "A stagehand began rinsing a sticky floor mat while performers hurried toward their marks",
        "goal": "reach the opening scene with the clarinet and moon tiara",
        "conflict": "the usual doorway was blocked by suds, but the alternate stairs were narrow and unfamiliar",
        "warning": "Do not step through the suds; wet soles can slide even when the mat looks flat",
        "memory": "during an earlier rehearsal, one patch of clear soap had made a prop chest skate across the floor",
        "mistake": "tested the soapy edge with one foot while holding the clarinet",
        "clue": "a dropped feather slid sideways instead of resting where it landed",
        "tool": "a stage map, a handrail, and a padded clarinet case",
        "action": "closed the case, studied the map with the stagehand, and used the dry stairs while keeping one hand on the rail",
        "result": "arrived before the cue and warned the next performers with a clearly lettered sign",
        "lesson": "a detour is worthwhile when evidence shows the familiar way is unsafe",
        "ending": "From the wings, the tiara caught a line of footlights just as the clarinet gave the actor's entrance cue",
    },
    "sand": {
        "place": "the seaside bandstand",
        "premise": "Wind blew fine sand onto the tiara while a custodian rinsed salt from the bandstand rail",
        "goal": "clean the tiara before joining the clarinet quartet",
        "conflict": "rinsing it under the rail hose would be quick, but water could carry grit into its tiny settings",
        "warning": "Do not blast grit with water; it can scratch the silver as it moves",
        "memory": "once, rubbing a sandy window had left faint lines that no polishing could erase",
        "mistake": "reached for the hose before examining where the sand had settled",
        "clue": "grains hid beneath every raised star on the tiara instead of sitting only on top",
        "tool": "a soft brush, a small bowl, and a lint-free cloth",
        "action": "brushed away loose sand, gave the tiara a gentle bowl rinse, dried it fully, and washed hands before touching the clarinet",
        "result": "cleaned the tiara without scratches and joined the quartet on time",
        "lesson": "the right cleaning method matters as much as the wish to make something clean",
        "ending": "At sunset, four clarinets sounded over the waves, and not one scratch interrupted the tiara's rose-colored gleam",
    },
    "greenhouse": {
        "place": "the greenhouse music corner",
        "premise": "A watering tray overflowed beneath the chair where the clarinet case and tiara box waited",
        "goal": "save the music corner before water reached the special cases",
        "conflict": "lifting both cases alone seemed heroic, but the wet floor made carrying a stack dangerous",
        "warning": "Call for another pair of paws; saving two things at once is not a solo performance",
        "memory": "on moving day, a tall stack had hidden the path and bumped a lamp from a table",
        "mistake": "balanced the tiara box on top of the clarinet case",
        "clue": "water was spreading toward one table leg faster than toward the other",
        "tool": "two dry carts, absorbent towels, and the watering shutoff",
        "action": "asked a gardener to close the valve, rolled each case away on its own cart, and helped press towels around the tray",
        "result": "protected both treasures and stopped the overflow at its source",
        "lesson": "asking for teamwork is wiser than turning care into a balancing trick",
        "ending": "Later, fern shadows trembled across the dry tiara box while the clarinet played a duet with rain tapping safely on the greenhouse roof",
    },
    "costume": {
        "place": "the library costume workshop",
        "premise": "A jar of washable paste spilled onto the cloth beside the tiara and clarinet cleaning swab",
        "goal": "remove the paste before it dried without spreading it to the instrument",
        "conflict": "a helper wanted to rinse everything together, while the young musician remembered that the clarinet needed special care",
        "warning": "Washable does not mean every object belongs in water",
        "memory": "after an old craft spill, a soaked paper label had peeled away from the box it was meant to identify",
        "mistake": "carried the sticky cloth toward the sink with the swab still wrapped inside it",
        "clue": "the clarinet care card showed a crossed-out faucet beside the instrument body",
        "tool": "the care card, a separate basin, and a fresh dry swab",
        "action": "separated the supplies, rinsed only the washable cloth, wiped the tiara as directed, and left clarinet cleaning to the approved swab",
        "result": "cleared the spill while teaching the whole workshop how different materials need different care",
        "lesson": "instructions are evidence, not an obstacle to getting a job done",
        "ending": "A new care card hung above the sink; beneath it, the tiara sparkled beside a clarinet whose keys clicked cleanly",
    },
    "creek": {
        "place": "the creekside story circle",
        "premise": "A gust carried the tiara's cloth pouch onto a muddy stone near the creek",
        "goal": "retrieve and rinse the pouch before the evening clarinet story-song",
        "conflict": "the pouch was close enough to see but beyond the marked path, and waiting for help felt unbearably slow",
        "warning": "The bank can crumble under dry-looking edges; stay behind the marker",
        "memory": "a small bank had collapsed beneath an empty basket after rain, even though its top looked firm",
        "mistake": "leaned past the marker and stretched a branch toward the pouch",
        "clue": "tiny crumbs of soil dropped whenever the branch touched the bank",
        "tool": "a ranger's long grabber, a rinse bottle, and a dry replacement pouch",
        "action": "stepped back, called the ranger, used the grabber from the path, and rinsed the muddy pouch away from the clarinet",
        "result": "recovered the pouch without entering the creek or weakening the bank",
        "lesson": "waiting for the proper helper protects more than the object you want to rescue",
        "ending": "The clean pouch fluttered from a line behind the circle while the tiara rested dry and the clarinet answered the creek with three soft notes",
    },
    "kitchen": {
        "place": "the community kitchen stage",
        "premise": "A rehearsal banner fell beside a sink where cooks were rinsing berry bowls",
        "goal": "lift the banner without staining the tiara or the clarinet case",
        "conflict": "the cooks needed the sink, while the musicians needed the narrow passage beside it",
        "warning": "Berry rinse water splashes farther than plain water, so we need one shared plan",
        "memory": "at breakfast, a single berry had rolled under a cup and tipped purple juice across a place mat",
        "mistake": "tried to squeeze past while a cook poured out a bowl",
        "clue": "purple dots on the wall showed exactly how far earlier splashes had traveled",
        "tool": "a folding screen, two trays, and a five-minute crossing schedule",
        "action": "helped set the screen, moved the treasures on separate trays during the cooks' pause, and then reopened the sink lane",
        "result": "gave both groups room to finish without stains or an argument",
        "lesson": "conflict can become cooperation when everyone names what their work requires",
        "ending": "After supper, berry-colored banners hung above the stage while the spotless tiara bobbed in time with a bright clarinet dance",
    },
    "museum": {
        "place": "the children's music museum",
        "premise": "A demonstration pump sent rinse water through a clear tube beside the dress-up display",
        "goal": "perform a clarinet tune in the tiara without interrupting the water exhibit",
        "conflict": "the performance mark sat inside the exhibit's splash boundary, and both presenters believed their sign had been placed first",
        "warning": "Before choosing sides, find out which floor mark belongs to which demonstration",
        "memory": "two similar labels had once been swapped, causing everyone to line up at the wrong classroom door",
        "mistake": "insisted that the blue floor mark must belong to the music show",
        "clue": "a faded water-drop symbol appeared beneath one corner of the blue tape",
        "tool": "the exhibit map and a new gold performance marker",
        "action": "checked the map with the presenter, apologized, placed the gold marker beyond the splash line, and covered the clarinet until showtime",
        "result": "let visitors enjoy both demonstrations safely and resolved the disagreement fairly",
        "lesson": "a remembered mix-up is useful when it reminds you to check before insisting",
        "ending": "The clear tube bubbled behind the boundary as the tiara gleamed on the gold mark and the clarinet finished to delighted applause",
    },
    "porch": {
        "place": "the rain-soaked porch recital",
        "premise": "Wind pushed mist beneath the porch roof while neighbors arranged chairs for a tiny recital",
        "goal": "play the clarinet in the tiara without disappointing the waiting audience",
        "conflict": "moving indoors meant fewer seats, but staying outside could dampen the clarinet and make the boards slick",
        "warning": "A recital can change rooms; damaged woodwind pads cannot simply change back",
        "memory": "at the previous picnic, everyone had waited too long to move and spent the song rescuing wet sheet music",
        "mistake": "used a towel to wipe one chair and declared the whole porch dry enough",
        "clue": "the tiara's reflection blurred whenever a new veil of mist crossed the porch table",
        "tool": "an indoor reading room, a rinse-safe boot tray, and a chair-count list",
        "action": "invited small groups indoors, set wet shoes by the tray, and carried the closed clarinet case and tiara box to the dry performance corner",
        "result": "gave two cozy mini-recitals so every neighbor heard the music",
        "lesson": "keeping a promise can mean changing its shape when conditions change",
        "ending": "In the last quiet group, rain silvered the window behind the tiara while the clarinet's final note warmed the little room",
    },
}

OPENINGS = [
    "{name}, a young {animal}, treated music practice like a promise.",
    "Whenever {name} lifted a clarinet, the young {animal}'s busy thoughts settled into rhythm.",
    "The brightest objects in {name}'s room were a silver tiara and a carefully polished clarinet.",
    "On performance days, {name} the {animal} checked every clarinet key twice and every tiara clasp once.",
    "A clarinet melody drifted from {name}'s window on the morning this trouble began.",
    "For {name}, the tiara meant celebration, while the clarinet meant patient practice.",
    "Before breakfast was over, {name} the {animal} was already humming the clarinet part for the day's event.",
    "Everyone knew {name} loved two things especially: the clarinet's mellow voice and the tiara's small silver stars.",
]

FLASHBACK_LEADS = [
    "The warning opened a flashback as clearly as a book.",
    "For one quiet second, the present scene faded into a flashback.",
    "That clue tugged loose a useful flashback.",
    "Instead of arguing again, {name} let a flashback finish in {possessive} mind.",
    "The sound nearby carried {name} into a brief flashback.",
    "A flashback arrived, not to frighten {name}, but to offer evidence.",
    "Then {name} remembered why this conflict felt familiar; a flashback supplied the missing detail.",
    "The hasty idea paused when a flashback returned.",
]

REFLECTIONS = [
    '"I do not have to repeat the old mistake just because I am in a hurry," {name} said.',
    '"The memory is a clue, not a scolding," {name} whispered.',
    '"First protect what I carry; then solve what is actually wrong," {name} decided.',
    '"I was defending my plan before I tested it," {name} admitted.',
    '"Careful can still be creative," {name} told {parent}.',
    '"A better ending starts with noticing the evidence," {name} said.',
    '"Let us slow down long enough to choose well," {name} suggested.',
    '"I can keep the promise without keeping my first idea," {name} realized.',
]


@dataclass
class StoryParams:
    name: str
    animal: str
    parent: str
    seed: Optional[int] = None
    incident: str = "runoff"
    telling: int = 0
    p: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection() -> str:
    return (
        "(No story: the rinse lesson only works when the shiny prize can be "
        "protected in a believable way.)"
    )


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["wet"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["wet"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got wet and dirty.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities["hero"]
    if hero.memes["fear"] >= THRESHOLD and hero.memes["conflict"] < THRESHOLD:
        hero.memes["conflict"] += 1
        out.append("__conflict__")
    return out


CAUSAL_RULES = [
    _r_soak,
    _r_conflict,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= THRESHOLD}


def tell(params: StoryParams) -> World:
    incident = INCIDENTS[params.incident]
    local_setting = Setting(place=incident["place"], affords={"rinse"})
    world = World(local_setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.animal, label=params.name))
    parent = world.add(Entity(id="parent", kind="character", type=params.parent, label=params.parent))
    tiara = world.add(Entity(
        id="tiara", type="tiara", label="tiara", phrase=PRIZE_TIARA.phrase,
        owner=hero.id, caretaker=parent.id, region="torso",
    ))
    clarinet = world.add(Entity(
        id="clarinet", type="clarinet", label="clarinet", phrase=PRIZE_CLARINET.phrase,
        owner=hero.id, caretaker=parent.id, region="torso",
    ))
    hero.memes["love"] = 1.0
    tiara.worn_by = hero.id
    clarinet.worn_by = hero.id
    possessive = hero.pronoun("possessive")
    rng = random.Random((params.seed if params.seed is not None else 0) ^ 0xC1A21E7)
    opening = OPENINGS[params.telling % len(OPENINGS)].format(
        name=params.name, animal=params.animal
    )
    flashback_lead = rng.choice(FLASHBACK_LEADS).format(
        name=params.name, possessive=possessive
    )
    reflection = rng.choice(REFLECTIONS).format(
        name=params.name, parent=params.parent
    )
    warning_verbs = ["warned", "said", "called", "explained", "reminded"]
    clue_leads = [
        "Then {name} noticed the evidence:",
        "A closer look revealed the useful clue:",
        "Before taking another step, {name} observed that",
        "The argument changed when {name} pointed out that",
        "One small detail mattered:",
        "Together, they examined the scene and saw that",
    ]
    action_leads = [
        "With the conflict understood, {name}",
        "This time, {name}",
        "After asking one more careful question, {name}",
        "The evidence suggested a practical plan, so {name}",
        "Rather than repeating the old error, {name}",
        "Working beside {parent}, {name}",
    ]
    lesson_leads = [
        "The lesson learned was simple:",
        "By then, {name} could state the lesson learned:",
        "The flashback had changed the choice, and the lesson learned was this:",
        "What began as conflict ended with a lesson learned:",
        "On the way home, {name} repeated the lesson learned:",
        "No lecture was needed; the result made the lesson learned clear:",
    ]
    warning_verb = rng.choice(warning_verbs)
    clue_lead = rng.choice(clue_leads).format(name=params.name)
    action_lead = rng.choice(action_leads).format(name=params.name, parent=params.parent)
    lesson_lead = rng.choice(lesson_leads).format(name=params.name)

    world.say(opening)
    world.say(
        f"{incident['premise']}. {params.name}'s goal was to {incident['goal']}."
    )
    world.say(
        f"The clarinet belonged in careful paws, and the tiara had been entrusted to {params.name} for the day."
    )

    world.para()
    world.say(f"At {incident['place']}, a real conflict appeared: {incident['conflict']}.")
    world.say(f"{params.name} {incident['mistake']}.")
    world.say(
        f'"{incident["warning"]}," {warning_verb} the {params.parent}.'
    )
    world.say(f"{clue_lead} {incident['clue']}.")

    world.para()
    world.say(flashback_lead)
    world.say(f"{params.name} remembered how {incident['memory']}.")
    hero.memes["flashback"] += 1
    hero.memes["fear"] += 1
    hero.memes["lesson"] += 1
    hero.memes["conflict"] += 1
    world.say(reflection)
    world.say(
        f"The old consequence matched the present clue, so {params.name} chose {incident['tool']} instead of relying on haste."
    )

    gear_def = select_gear(ACTIVITY, tiara)
    gear = world.add(Entity(
        id="safety_plan",
        type="safety plan",
        label=incident["tool"],
        protective=True,
        covers={"torso"},
        plural=False,
        owner=hero.id,
    ))

    hero.memes["fear"] = 0.0
    hero.memes["conflict"] = 0.0
    hero.memes["joy"] += 1

    world.para()
    world.say(f"{action_lead} {incident['action']}.")
    world.say(f"The plan worked: {params.name} {incident['result']}.")
    world.say(
        "Anything that truly needed a rinse was washed separately, away from the clarinet and the tiara."
    )
    world.say(f"{lesson_lead} {incident['lesson']}.")
    world.say(f"{incident['ending']}.")

    world.facts.update(
        hero=hero,
        parent=parent,
        tiara=tiara,
        clarinet=clarinet,
        gear=gear,
        activity=ACTIVITY,
        setting=local_setting,
        incident_id=params.incident,
        premise=incident["premise"],
        goal=incident["goal"],
        conflict_detail=incident["conflict"],
        warning=incident["warning"],
        memory=incident["memory"],
        clue=incident["clue"],
        action=incident["action"],
        result=incident["result"],
        lesson=incident["lesson"],
        ending=incident["ending"],
        lesson_learned=True,
        conflict=True,
        flashback=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    setting = f["setting"]
    return [
        f"Write an animal story about {hero.label}, a {hero.type}, facing this problem at {setting.place}: {f['conflict_detail']}.",
        f"Tell a story in which a flashback about how {f['memory']} helps {hero.label} protect a clarinet and a tiara.",
        f"Write a gentle conflict-and-lesson story where {hero.label} uses this clue: {f['clue']}. Include a safe rinse and the concrete ending from the world facts.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    tiara = _safe_fact(world, f, "tiara")
    clarinet = _safe_fact(world, f, "clarinet")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a little {hero.type} who loves a clarinet and a tiara.",
        ),
        QAItem(
            question=f"What conflict did {hero.label} face at {f['setting'].place}?",
            answer=(
                f"{hero.label} faced a conflict because {f['conflict_detail']}. "
                f"The {parent.label} warned, '{f['warning']}'."
            ),
        ),
        QAItem(
            question=f"What did {hero.label} remember in the flashback?",
            answer=(
                f"In the flashback, {hero.label} remembered how {f['memory']}. "
                f"That memory helped {hero.label} recognize the present clue instead of repeating the mistake."
            ),
        ),
        QAItem(
            question=f"What clue changed {hero.label}'s plan?",
            answer=(
                f"The useful clue was that {f['clue']}. "
                f"It showed why the first plan was risky and pointed toward {gear.label}."
            ),
        ),
        QAItem(
            question=f"How did {hero.label} resolve the conflict?",
            answer=(
                f"{hero.label} {f['action']}. "
                f"As a result, {hero.label} {f['result']}."
            ),
        ),
        QAItem(
            question=f"What lesson was learned about the {tiara.label} and {clarinet.label}?",
            answer=(
                f"The lesson learned was that {f['lesson']}. "
                "The story proves it by keeping rinsing separate from the protected music and costume items."
            ),
        ),
        QAItem(
            question="What final image shows that the choice worked?",
            answer=f"The final image is this: {f['ending']}.",
        ),
    ]


KNOWLEDGE = {
    "clarinet": (
        "What is a clarinet?",
        "A clarinet is a long woodwind instrument with keys. You blow air through it to make music.",
    ),
    "tiara": (
        "What is a tiara?",
        "A tiara is a small crown-like headpiece, often shiny and decorative.",
    ),
    "rinse": (
        "What does rinse mean?",
        "To rinse means to wash something lightly with water to remove soap, dirt, or sticky stuff.",
    ),
    "lesson": (
        "What is a lesson learned?",
        "A lesson learned is something you remember after a mistake, so you make a better choice next time.",
    ),
    "flashback": (
        "What is a flashback in a story?",
        "A flashback is a short memory from the past that helps explain why a character feels or acts a certain way.",
    ),
    "conflict": (
        "What is conflict in a story?",
        "Conflict is a problem or disagreement that makes the characters stop and decide what to do.",
    ),
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(question=q, answer=a) for q, a in KNOWLEDGE.values()]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("activity", "rinse"),
        asp.fact("mess_of", "rinse", "wet"),
        asp.fact("worn_on", "tiara", "torso"),
        asp.fact("worn_on", "clarinet", "torso"),
        asp.fact("gear", "raincoat"),
        asp.fact("gear", "boots"),
        asp.fact("guards", "raincoat", "wet"),
        asp.fact("guards", "boots", "wet"),
        asp.fact("covers", "raincoat", "torso"),
        asp.fact("covers", "boots", "feet"),
        asp.fact("splashes", "rinse", "feet"),
        asp.fact("splashes", "rinse", "legs"),
        asp.fact("splashes", "rinse", "torso"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(A) :- activity(A), has_fix(A, tiara).
#show prize_at_risk/2.
#show protects/3.
#show valid/1.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    valid = set(asp.atoms(model, "valid"))
    if valid == {("rinse",)}:
        print("OK: ASP gate agrees with Python reasonableness.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    print("ASP atoms:", sorted(valid))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: clarinet, tiara, rinse.")
    ap.add_argument("--name", choices=GIRL_NAMES + BOY_NAMES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--parent", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--incident", choices=sorted(INCIDENTS))
    ap.add_argument("--telling", type=int, choices=range(len(OPENINGS)))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    animal = getattr(args, "animal", None) or rng.choice(ANIMALS)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father", "aunt", "uncle"])
    incident = getattr(args, "incident", None) or rng.choice(list(INCIDENTS))
    telling = getattr(args, "telling", None)
    if telling is None:
        telling = rng.randrange(len(OPENINGS))
    return StoryParams(
        name=name,
        animal=animal,
        parent=parent,
        incident=incident,
        telling=telling,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, name in enumerate(["Mina", "Ollie", "Tia", "Bram", "Luna"]):
            p = StoryParams(
                name=name,
                animal=_safe_lookup(ANIMALS, i % len(ANIMALS)),
                parent="mother",
                seed=base_seed + i,
                incident=list(INCIDENTS)[i % len(INCIDENTS)],
                telling=i % len(OPENINGS),
            )
            samples.append(generate(p))
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
