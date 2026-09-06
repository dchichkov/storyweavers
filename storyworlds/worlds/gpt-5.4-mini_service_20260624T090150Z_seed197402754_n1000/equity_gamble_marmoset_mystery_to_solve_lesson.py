#!/usr/bin/env python3
"""
A mythic storyworld about a marmoset, a risky gamble, and a mystery solved by
fairness.

The world is small on purpose: one temple-town, one missing thing, one imperfect
choice, and one lesson learned. The tone leans mythic, but the stories stay
child-facing and concrete.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
    hero: object | None = None
    marmoset: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king", "priest"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    place: str
    epithet: str
    affords: set[str] = field(default_factory=set)
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
class Gamble:
    id: str
    verb: str
    risk: str
    twist: str
    outcome_good: str
    outcome_bad: str
    clue: str
    lesson: str
    humor_tag: str
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
    id: str
    label: str
    phrase: str
    region: str
    genders: set[str]
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "sunlit_square": Setting(
        place="the sunlit square",
        epithet="where old stones hummed at noon",
        affords={"shell_toss"},
    )
}

GAMBLES = {
    "shell_toss": Gamble(
        id="shell_toss",
        verb="test one uncertain idea before checking every clue",
        risk="choosing too soon could waste time or make the puzzle harder",
        twist="the apparent shortcut concealed the most useful evidence",
        outcome_good="the risk was checked against evidence",
        outcome_bad="a hurried guess delayed the answer",
        clue="a tiny leaf-shaped mark",
        lesson="equity means giving each person the support needed for a fair chance",
        humor_tag="the marmoset treated every discarded clue like treasure",
    )
}

PRIZES = {
    "crown_seed": Prize(
        id="crown_seed",
        label="seed-crown",
        phrase="a little seed-crown woven from gold thread and leaves",
        region="head",
        genders={"girl", "boy"},
    )
}

NAMES = {
    "girl": ["Ari", "Mina", "Lina", "Suri"],
    "boy": ["Ari", "Taro", "Pavo", "Nico"],
}
TRAITS = ["curious", "brave", "gentle", "quick-thinking", "cheerful"]

MYSTERIES = [
    {
        "id": "silent_bells",
        "premise": "the six festival bells rang, but the smallest bell stayed silent",
        "inequity": "the bell rope was too high for the youngest musicians to reach",
        "bad_idea": "pull the largest rope and hope its echo covered the missing note",
        "clue": "pale fibers caught on a low cedar peg",
        "marmoset_action": "tapped the low peg, then pointed from it to the silent bell",
        "cause": "a caretaker had moved the small bell's rope to the low peg for shorter players, but no sign explained the change",
        "solution": "hung ropes at several heights and added matching leaf signs",
        "proof": "every musician rang one clear note in the next song",
        "ending": "six bell notes crossed the square while the marmoset conducted with a cedar twig",
    },
    {
        "id": "vanishing_water",
        "premise": "water vanished from the public jug before the afternoon games",
        "inequity": "children at the end of the path received empty cups while taller visitors reached a hidden reserve",
        "bad_idea": "race to the fountain and claim the first refill",
        "clue": "a trail of round wet pawprints beneath the serving table",
        "marmoset_action": "rolled out a stoppered cup that had wedged the jug's tap open",
        "cause": "the loose cup pressed the tap, and the water had drained into a covered garden basin",
        "solution": "fixed the tap and placed equal pitchers at two reachable tables",
        "proof": "the line moved steadily and every waiting cup was filled",
        "ending": "sunlight flashed in a hundred cups as the marmoset sipped from a thimble-sized bowl",
    },
    {
        "id": "mixed_seed_tokens",
        "premise": "the seed tokens for the spring garden appeared to have been counted wrongly",
        "inequity": "one neighborhood had rich soil but few tokens, while another needed extra seeds after a flood",
        "bad_idea": "toss a shell to decide which neighborhood received the last packet",
        "clue": "purple pollen dust on only one stack of tokens",
        "marmoset_action": "sneezed beside the purple stack and uncovered a folded flood report",
        "cause": "the stacks were equal by number, but the flood report showing different needs had slipped underneath",
        "solution": "shared seeds according to usable soil and flood loss, then wrote the reasons on a public board",
        "proof": "both gardens had enough rows to plant and everyone could inspect the count",
        "ending": "two gardens raised green shoots beneath signs painted with the same open hand",
    },
    {
        "id": "shadow_map",
        "premise": "a map to the evening story circle showed a path that ended at a blank wall",
        "inequity": "the usual stair route excluded a visitor whose chair needed the smooth ramp",
        "bad_idea": "take the dark stairway because it looked shorter",
        "clue": "a crescent of chalk glowing near the ramp gate",
        "marmoset_action": "held a shiny spoon so moonlight bounced onto the faded ramp arrows",
        "cause": "rain had washed away the accessible route marks while leaving the stair marks untouched",
        "solution": "repainted both routes with raised markers and posted the same story schedule at each entrance",
        "proof": "the whole group arrived together without anyone being carried or left behind",
        "ending": "raised silver arrows gleamed under the moon as cushions formed one unbroken circle",
    },
    {
        "id": "missing_drumbeat",
        "premise": "the parade drummer kept missing a signal that everyone else claimed was obvious",
        "inequity": "the signal was only a whistle, which the drummer could not hear clearly",
        "bad_idea": "guess when to begin from the crowd's movement",
        "clue": "the trembling in the marmoset's paws whenever the great drum sounded",
        "marmoset_action": "pressed both paws to the drumhead and copied its vibration",
        "cause": "the organizers had provided one sound cue but no visible or vibrating cue",
        "solution": "paired the whistle with a bright flag and a gentle tap through the drum stand",
        "proof": "the drummer began exactly with the flag on three practice turns",
        "ending": "a red flag rose, the drum answered boom, and the marmoset bounced in perfect time",
    },
    {
        "id": "crooked_scale",
        "premise": "the grain scale declared identical baskets strangely unequal",
        "inequity": "families were being given different portions because nobody had checked the measuring tool",
        "bad_idea": "accept the next reading and hope the scale corrected itself",
        "clue": "one brass foot left no dust mark on the counter",
        "marmoset_action": "slid a flat seed hull from beneath the raised brass foot",
        "cause": "the hull tilted the scale and changed every reading on that side",
        "solution": "leveled and tested the scale with standard stones before remeasuring every basket",
        "proof": "equal test stones balanced and the corrected portions matched the posted plan",
        "ending": "the scale stood level beside neat baskets while a seed hull rode on the marmoset's head",
    },
    {
        "id": "locked_storybox",
        "premise": "the town story box opened for some carved tokens but rejected others",
        "inequity": "worn tokens used by the oldest reading group no longer fit the narrow slot",
        "bad_idea": "force one worn token into the lock and hope nothing cracked",
        "clue": "soft gold dust gathered along the slot's upper edge",
        "marmoset_action": "held a worn token sideways beside a new one so their different thicknesses showed",
        "cause": "new paint had narrowed the slot, not made the older tokens invalid",
        "solution": "widened the guide safely and tested old and new tokens in public",
        "proof": "every reading group opened the box with its own token",
        "ending": "the story box stood open as pages rustled and the marmoset listened upside down",
    },
    {
        "id": "lantern_queue",
        "premise": "only the first lanterns in the decorating line kept their flames",
        "inequity": "slow crafters reached the oil table after all the filled cups were gone",
        "bad_idea": "stretch one cup of oil among all the remaining lanterns",
        "clue": "empty cups nested beneath a cloth at the front table",
        "marmoset_action": "lifted the cloth and stacked the hidden cups into a wobbling tower",
        "cause": "helpers had filled every cup at once, so early groups accidentally collected extras",
        "solution": "issued one marked cup per lantern and reserved supplies for later groups",
        "proof": "the last lantern burned as steadily as the first",
        "ending": "an even chain of lantern light curved around the square, with no dark gap at its tail",
    },
    {
        "id": "echoing_names",
        "premise": "the announcement wall repeated some helpers' names and erased others",
        "inequity": "quiet work done behind the stage received no credit while public jobs appeared twice",
        "bad_idea": "draw a shell to choose one name for the final empty space",
        "clue": "two lists bore matching berry-juice thumbprints",
        "marmoset_action": "matched the sticky lists and chirped whenever the same line appeared twice",
        "cause": "the public-job list had been copied twice while the backstage list remained folded",
        "solution": "combined both signed lists, checked each contribution, and invited corrections",
        "proof": "every helper found one accurate name and task on the wall",
        "ending": "the complete list fluttered above the feast while the marmoset guarded the inkpot",
    },
    {
        "id": "puzzle_tiles",
        "premise": "a floor puzzle offered no path to the prize no matter how the tiles turned",
        "inequity": "color alone marked matching edges, leaving one solver without usable clues",
        "bad_idea": "place a random final tile before sunset",
        "clue": "tiny scratches formed circles, lines, and stars beneath the colored paint",
        "marmoset_action": "rubbed dust across the scratches until the shapes became visible",
        "cause": "the shape key had been covered by a decorative border",
        "solution": "restored the shape key so color and texture both guided the solvers",
        "proof": "two teams using different clues built the same safe path",
        "ending": "stars, circles, and bright colors made one path, and the seed-crown waited at its center",
    },
    {
        "id": "fruit_vote",
        "premise": "the feast vote showed fifty mango marks although only thirty people had voted",
        "inequity": "children who could not read the written fruit names depended on unclear pictures",
        "bad_idea": "trust the surprising total because mango was popular",
        "clue": "two stamps, mango and melon, shared the same round outline",
        "marmoset_action": "placed a real mango and melon beside their stamps and frowned at the mismatch",
        "cause": "the nearly identical stamps sent both choices into the mango jar",
        "solution": "made distinct raised stamps, explained each option aloud, and held a fresh vote",
        "proof": "the new totals matched the number of voters and every choice could be checked",
        "ending": "three clearly labeled fruit bowls circled the seed-crown while everyone tasted the winner",
    },
    {
        "id": "borrowed_shade",
        "premise": "the shared shade cloth vanished just before the hottest lesson",
        "inequity": "the sunny learning table became unusable for children who needed a cooler place",
        "bad_idea": "wait and hope clouds arrived before the lesson began",
        "clue": "a line of blue knots led from the empty hooks toward the seedling beds",
        "marmoset_action": "followed the knots and tugged one loose corner from behind the watering screen",
        "cause": "gardeners had borrowed the cloth to protect seedlings and left no note",
        "solution": "returned the cloth, moved spare shade to the seedlings, and started a signed borrowing board",
        "proof": "both the learning table and seedlings stayed cool through noon",
        "ending": "two patches of shade rested side by side while the marmoset napped between them",
    },
]

OPENINGS = [
    "Long ago, the sunlit square kept its promises in public.",
    "At noon, old stones warmed the feet of everyone entering the sunlit square.",
    "The sunlit square was famous for puzzles, festivals, and rules anyone could inspect.",
    "On a bright market morning, a question traveled quickly across the sunlit square.",
    "In the sunlit square, even small clues were supposed to receive a hearing.",
    "Before the noon bell, the sunlit square looked orderly, but one detail did not fit.",
    "People came to the sunlit square to share work as well as celebration.",
    "A seed-crown glittered above the sunlit square on the day fairness was tested.",
]

REFLECTIONS = [
    "A fair result needs more than identical treatment; it needs barriers noticed and removed.",
    "Equity is not giving everyone the same tool when different people need different tools to participate.",
    "No loud guess deserves more weight than evidence everyone can examine.",
    "A risk becomes wiser when its cost is small, visible, and reversible.",
    "Fair rules explain both the choice and the reason behind it.",
    "Making room for every person's way of participating strengthens the whole group.",
]

# ---------------------------------------------------------------------------
# Contract-required params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    gamble: str
    prize: str
    hero_name: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
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


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    gamble = _safe_lookup(GAMBLES, params.gamble)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(setting=setting)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    elder = world.add(Entity(id="elder", kind="character", type="priest", label="the elder"))
    marmoset = world.add(Entity(id="marmoset", kind="character", type="marmoset", label="the marmoset"))
    relic = world.add(Entity(
        id="relic",
        type=prize.id,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
    ))

    rng = random.Random(params.seed)
    case = MYSTERIES[rng.randrange(len(MYSTERIES))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    reflection = REFLECTIONS[rng.randrange(len(REFLECTIONS))]
    wager_object = rng.choice(["a painted shell", "a smooth acorn", "a blue ribbon", "a carved seed"])
    investigation = rng.choice([
        "made a list of what everyone had observed before touching anything",
        "asked each group to describe the last moment when the system worked",
        "marked the known facts in chalk and left the guesses unmarked",
        "tested the safest explanation first and recorded what changed",
        "invited the person most affected by the barrier to inspect the clues first",
        "compared the ordinary arrangement with the puzzling one piece by piece",
    ])
    dialogue = rng.choice([
        f'"The same chance is not always a fair chance," {hero.id} said. "Let us find the barrier."',
        f'"We can risk one small test, not somebody else\'s safety," {hero.id} told the elder.',
        f'"First evidence, then guesses," {hero.id} said as the marmoset chirped agreement.',
        f'"Who cannot use the arrangement as it is?" {hero.id} asked. "That answer matters."',
        f'"A mystery is not solved when one person wins," {hero.id} said. "It is solved when the facts fit."',
    ])
    response = rng.choice([
        "The elder paused the crowd and gave every witness an equal turn to speak.",
        "The crowd stepped back, leaving a clear workspace and enough time for careful checking.",
        "Two helpers repeated the test while everyone watched for the same result.",
        "A younger child drew the clue while an older helper read the written notes aloud.",
        "The town posted each observation so quiet voices could be considered with loud ones.",
    ])

    world.facts.update(
        hero=hero,
        elder=elder,
        marmoset=marmoset,
        relic=relic,
        gamble=gamble,
        prize=prize,
        case=case,
        mystery=case["premise"],
        inequity=case["inequity"],
        clue=case["clue"],
        cause=case["cause"],
        solution=case["solution"],
        proof=case["proof"],
        reflection=reflection,
        investigation=investigation,
        response=response,
        wager_object=wager_object,
    )

    world.say(opening)
    world.say(
        f"There lived {hero.id}, a {params.trait} {hero.type} trusted to carry the {prize.label}, "
        f"{prize.phrase}. A bright-eyed marmoset followed close behind."
    )
    world.say(
        f"That day brought a mystery to solve: {case['premise']}. Worse, {case['inequity']}."
    )

    world.para()
    world.say(
        f"Someone proposed a gamble: place {wager_object} beneath one of three cups and let chance decide whether to "
        f"{case['bad_idea']}. No money or prize was at stake, but a wrong risk could still cost time or fairness."
    )
    world.say(dialogue)
    world.say(
        f"Instead of letting chance settle the matter, {hero.id} {investigation}."
    )
    world.say(f"The first useful clue was {case['clue']}.")

    world.para()
    world.say(f"The marmoset {case['marmoset_action']}.")
    world.say(response)
    world.say(
        f"Piece by piece, the evidence revealed the cause: {case['cause']}. The mystery had an answer, but the old "
        f"arrangement still did not offer equity."
    )
    world.say(
        f"So {hero.id} and the town {case['solution']}. They checked their work: {case['proof']}."
    )

    world.para()
    world.say(
        f"The elder returned the {prize.label} to {hero.id}, not as winnings from a gamble, but as thanks for solving "
        f"the mystery without making another person's needs the price of a guess."
    )
    world.say(f"The lesson learned was this: {reflection}")
    world.say(f"By evening, {case['ending']}.")

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for gamble_id in setting.affords:
            for prize_id, prize in PRIZES.items():
                combos.append((place, gamble_id, prize_id))
    return combos


def explain_rejection() -> str:
    return "(No story: the selected square, non-monetary risk choice, and seed-crown are not compatible.)"


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "marmoset": [
        (
            "What is a marmoset?",
            "A marmoset is a very small monkey with quick hands and a lively face.",
        )
    ],
    "equity": [
        (
            "What does equity mean?",
            "Equity means making things fair so people get a proper chance and the rules do not favor only one side.",
        )
    ],
    "gamble": [
        (
            "What is a gamble?",
            "A gamble is a risky choice where the result is not certain.",
        )
    ],
    "mystery": [
        (
            "What is a mystery?",
            "A mystery is a puzzle or question that people need clues to solve.",
        )
    ],
    "lesson": [
        (
            "What is a lesson learned?",
            "A lesson learned is a helpful truth someone understands after an experience.",
        )
    ],
    "humor": [
        (
            "What is humor?",
            "Humor is something funny that makes people smile or laugh.",
        )
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    case = f["case"]
    return [
        f"Write a child-facing mystery about equity, a non-monetary gamble, and a marmoset, beginning when {case['premise']}.",
        f"Tell a gentle legend where {hero.id} investigates {case['clue']} and learns why fairness may require different support.",
        f"Write a mystery to solve in which a marmoset helps reveal that {case['cause']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    case = f["case"]
    qa = [
        QAItem(
            question="What mystery did the town need to solve?",
            answer=f"The town needed to discover why {case['premise']}. The problem mattered because {case['inequity']}.",
        ),
        QAItem(
            question=f"Why did {hero.id} reject the proposed gamble?",
            answer=(
                f"{hero.id} would not let chance decide whether to {case['bad_idea']}. "
                "Even without money, a careless gamble could waste time or deny someone a fair chance."
            ),
        ),
        QAItem(
            question="Which clue helped the investigation turn toward the truth?",
            answer=(
                f"The turning clue was {case['clue']}. Before using it, {hero.id} {f['investigation']}."
            ),
        ),
        QAItem(
            question="What actually caused the mystery?",
            answer=f"The evidence showed that {case['cause']}. That explanation fit the clue better than the crowd's guesses.",
        ),
        QAItem(
            question="How did the town create a more equitable solution?",
            answer=(
                f"{f['response']} Then the town {case['solution']}. "
                f"The result was equitable because {case['proof']}."
            ),
        ),
        QAItem(
            question="What lesson did the hero learn?",
            answer=(
                f"{hero.id} learned that {f['reflection'][0].lower() + f['reflection'][1:]} "
                "The town solved the puzzle by considering evidence and people's different needs."
            ),
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"marmoset", "equity", "gamble", "mystery", "lesson", "humor"}
    out: list[QAItem] = []
    for tag in ["marmoset", "equity", "gamble", "mystery", "lesson", "humor"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
#show valid/3.

valid(P, G, R) :- place(P), gamble(G), prize(R), affords(P, G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for g in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, g))
    for gid in GAMBLES:
        lines.append(asp.fact("gamble", gid))
    for rid, prize in PRIZES.items():
        lines.append(asp.fact("prize", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def tell(params: StoryParams) -> World:
    return build_world(params)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.label:
            bits.append(f"label={e.label}")
        if e.phrase:
            bits.append(f"phrase={e.phrase}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: equity, gamble, marmoset, mystery, lesson, humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--gamble", choices=GAMBLES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "gamble", None):
        combos = [c for c in combos if c[1] == getattr(args, "gamble", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, gamble, prize = rng.choice(list(combos))
    prize_obj = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize_obj.genders))
    if gender not in prize_obj.genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(NAMES[gender])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, gamble=gamble, prize=prize, hero_name=name, hero_type=gender, trait=trait)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(
        place="sunlit_square",
        gamble="shell_toss",
        prize="crown_seed",
        hero_name="Ari",
        hero_type="boy",
        trait="curious",
        seed=197402754,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible stories:\n")
        for p, g, r in asp_valid_combos():
            print(f"  {p:14} {g:12} {r}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
