#!/usr/bin/env python3
"""
A standalone story world for a small Superhero Story about praise, repetition,
caution, and kindness.

The seed premise:
A young superhero wants to help people right away, but must learn that being
kind also means being careful and repeating a safe plan until everyone feels
ready. Praise helps the hero stay brave.
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

HERO_NAMES = ["Nova", "Pip", "Zuri", "Milo", "Juno", "Iris", "Arlo", "Tessa"]
HELPER_NAMES = ["Captain Bright", "Aunt Beacon", "Coach Star", "Ms. Halo"]
CITY_NAMES = ["Sunrise City", "Rivergate", "Bluebell Town", "Clover City"]
MISHAPS = ["a stuck kite", "a blocked bridge", "a fallen sign", "a lost kitten", "a jammed door"]
TOOLS = ["a rope", "a flashlight", "a ladder", "a map", "a walkie-talkie"]
ACTIONS = ["climb", "carry", "lift", "guide", "reach", "steady"]
TRAITS = ["brave", "eager", "gentle", "careful", "friendly", "cheerful"]

INCIDENTS = {
    "a stuck kite": [
        {
            "id": "bakery_weather_vane",
            "premise": "a silver kite was wound around the bakery's weather vane, and its tail kept knocking loose flour tins toward the sidewalk",
            "impulse": "spring straight to the roof",
            "warning": "A tumbling tin clanged beside an empty bench and showed how rushing could endanger someone below",
            "clue": "the kite string tightened whenever the wind turned east",
            "solution": "closed the sidewalk, waited for a quiet gust, and guided the baker as the string was unhooked from indoors",
            "kindness": "asked the worried kite owner to count the safe steps with them",
            "result": "the kite floated down without another tin falling",
            "ending": "the kite's silver tail rested across the bakery counter beside a warm loaf",
        },
        {
            "id": "tram_wire",
            "premise": "a red kite had snagged near a tram wire while its young owner tugged harder and harder",
            "impulse": "fly up and grab the wet string",
            "warning": "The string snapped blue with a tiny spark, warning everyone to stay far away",
            "clue": "a warning plate on the pole named the transit crew to call",
            "solution": "moved the crowd back and helped the transit crew stop the line before they freed the kite",
            "kindness": "sat with the frightened owner and explained that a kite can be replaced but a person cannot",
            "result": "the crew lowered the kite after the wire was safely switched off",
            "ending": "the red kite rode home folded beneath its owner's arm while the tram bell rang again",
        },
        {
            "id": "park_branch",
            "premise": "a kite was pulling a cracked branch over the tables at the park picnic",
            "impulse": "yank the string with superhero strength",
            "warning": "The branch creaked lower when the string was pulled, scattering cups across one table",
            "clue": "the split in the branch widened each time the kite fluttered",
            "solution": "cleared the tables, steadied the dangling string, and let the park keeper trim the cracked branch first",
            "kindness": "turned the waiting children into a calm counting team instead of blaming the kite flyer",
            "result": "the trimmed branch and the kite both came down gently",
            "ending": "everyone ate beneath a safe green tree while the kite dried on the grass",
        },
    ],
    "a blocked bridge": [
        {
            "id": "hidden_plank",
            "premise": "storm branches covered the footbridge, hiding a plank that had cracked underneath",
            "impulse": "sweep every branch aside in one mighty rush",
            "warning": "One boot touched the hidden plank and it dipped toward the stream",
            "clue": "a thin line of water bubbled up through the split wood",
            "solution": "closed both ends, uncovered the boards one at a time, and helped the bridge crew mark the cracked plank",
            "kindness": "found a level detour for a neighbor pushing a stroller",
            "result": "the branches were cleared only after the weak board had been replaced",
            "ending": "the first safe footsteps crossed beside a fresh yellow repair mark",
        },
        {
            "id": "parade_gridlock",
            "premise": "two parade carts had met nose to nose on the narrow bridge while families crowded behind them",
            "impulse": "push both carts apart at once",
            "warning": "The bridge rail shivered when both crowds leaned forward together",
            "clue": "the smaller cart had a clear lane to reverse into",
            "solution": "asked both sides to step back, reversed the smaller cart, and brought each group across in turn",
            "kindness": "let the youngest musicians cross first so their heavy drums could be set down",
            "result": "the carts passed separately and the bridge stopped shaking",
            "ending": "the parade restarted with one soft drumbeat at each end of the bridge",
        },
        {
            "id": "rising_creek",
            "premise": "the creek had risen over the bridge approach and a delivery rider was waiting with medicine",
            "impulse": "wade through the fast brown water",
            "warning": "A loose bucket spun past faster than anyone could run",
            "clue": "the flood marker showed that the safe riverside path was already underwater",
            "solution": "sealed the approach and sent the medicine around the hill by the dry emergency route",
            "kindness": "carried a message ahead so the waiting family knew the medicine was still coming",
            "result": "the delivery arrived by the high road while the bridge stayed closed",
            "ending": "a porch lamp blinked thank-you across the wet valley at dusk",
        },
    ],
    "a fallen sign": [
        {
            "id": "school_crossing",
            "premise": "the school crossing sign had fallen across the curb just as morning bicycles arrived",
            "impulse": "lift the heavy post alone before the bell rang",
            "warning": "The bent base scraped forward and nearly rolled into the bicycle lane",
            "clue": "two rusted bolts were still sticking through the base",
            "solution": "stopped the bicycles, covered the sharp bolts, and helped the crossing guard set a temporary sign",
            "kindness": "walked beside a nervous new student through the marked crossing",
            "result": "everyone entered school safely while a repair crew secured a new post",
            "ending": "the new sign flashed gold in the afternoon sun above a row of parked bicycles",
        },
        {
            "id": "market_awning",
            "premise": "a market sign had dropped onto an awning, trapping a vendor's cart beneath the sagging cloth",
            "impulse": "crawl under the awning and shoulder the sign up",
            "warning": "A second hook popped loose and the canvas sagged another inch",
            "clue": "the remaining hook was bearing all the weight",
            "solution": "cleared the stall, supported the awning from outside, and guided the market crew to lower the sign together",
            "kindness": "saved the vendor's fruit by passing each crate down a careful line of helpers",
            "result": "the cart rolled free before the awning was repaired",
            "ending": "the vendor arranged a bright apple star where the fallen sign had been",
        },
        {
            "id": "trail_arrow",
            "premise": "a trail sign had fallen and twisted, sending walkers toward a muddy ravine",
            "impulse": "stand the sign up without checking which way it pointed",
            "warning": "A returning walker called that the arrow had already led three people the wrong way",
            "clue": "moss on the post matched the shaded side of its old hole",
            "solution": "blocked the false turn, compared the trail map with the moss mark, and reset the arrow toward the lake",
            "kindness": "waited for the missing walkers and shared water when they returned",
            "result": "the corrected sign guided everyone back to the main trail",
            "ending": "three muddy boot prints curved safely toward the blue lake",
        },
    ],
    "a lost kitten": [
        {
            "id": "storm_drain",
            "premise": "a lost kitten was mewing beneath a storm-drain grate as rain began to spot the pavement",
            "impulse": "pull up the grate with bare hands",
            "warning": "The heavy grate shifted and pinched the edge of a dropped glove",
            "clue": "the mews came from a dry side pipe rather than the rushing channel",
            "solution": "kept the street clear and guided an animal rescuer to open the side hatch",
            "kindness": "spoke softly so the kitten followed the rescuer's warm food instead of hiding deeper",
            "result": "the kitten emerged dry just before the rain became heavy",
            "ending": "two damp paw prints appeared on the rescuer's yellow towel",
        },
        {
            "id": "shop_awning",
            "premise": "a lost kitten crouched on a striped shop awning above a noisy crowd",
            "impulse": "leap onto the awning and scoop it up",
            "warning": "The cloth bowed when the kitten backed away from the sudden movement",
            "clue": "it leaned toward the quiet sound of its owner's bell",
            "solution": "quieted the crowd and helped the shopkeeper open an upstairs window beside the awning",
            "kindness": "gave the worried owner the job of ringing the familiar bell slowly",
            "result": "the kitten stepped through the window by itself",
            "ending": "its tiny bell jingled once from the safety of its owner's coat",
        },
        {
            "id": "delivery_van",
            "premise": "a lost kitten was hiding beneath a delivery van that was due to leave the square",
            "impulse": "slide underneath and reach between the wheels",
            "warning": "The driver started jingling the keys before noticing the small tail",
            "clue": "a trail of crumbs led from the van to a quiet cardboard box",
            "solution": "returned the keys to the driver, guarded the wheels, and placed the box at the end of the crumb trail",
            "kindness": "asked everyone to kneel far back so the kitten had a calm path out",
            "result": "the kitten crept into the box and the van left only after a full wheel check",
            "ending": "the box rode home on its owner's lap with two green eyes peeking over the rim",
        },
    ],
    "a jammed door": [
        {
            "id": "library_pebble",
            "premise": "the library's side door was jammed while a reading club waited inside",
            "impulse": "ram the door open with one powerful shoulder",
            "warning": "A glass pane rattled and everyone inside stepped back",
            "clue": "a tiny pebble was wedged beneath the lower hinge",
            "solution": "kept the main exit clear and helped the librarian lift the door just enough to remove the pebble",
            "kindness": "told the waiting children a quiet riddle so nobody crowded the doorway",
            "result": "the door swung freely without cracking the glass",
            "ending": "the reading club filed out beneath a paper moon hanging perfectly still",
        },
        {
            "id": "rain_swollen",
            "premise": "rain had swollen the community-center door while a soup delivery cooled outside",
            "impulse": "pull the handle until the latch broke",
            "warning": "The handle bent and the hot soup cart began rolling down the ramp",
            "clue": "the top of the wooden door rubbed while the latch itself still moved",
            "solution": "stopped the cart, used the other entrance, and helped the caretaker sand the swollen edge",
            "kindness": "carried bowls first to the people who had been waiting longest",
            "result": "the soup stayed warm and the repaired door closed without sticking",
            "ending": "steam curled from the last bowl as rain tapped the easy-moving door",
        },
        {
            "id": "greenhouse_vine",
            "premise": "the greenhouse door was jammed with the gardening class on the warm side of the glass",
            "impulse": "tear the whole vine away from the latch",
            "warning": "The vine tightened around a shelf of seedling pots when it was tugged",
            "clue": "one soft loop, not the thick stem, was caught behind the latch",
            "solution": "opened the roof vents, supported the pots, and let the gardener unwind the single trapped loop",
            "kindness": "protected both the waiting class and the living vine instead of choosing one over the other",
            "result": "the door opened and the vine remained rooted and green",
            "ending": "a heart-shaped leaf rested beside the freed latch",
        },
    ],
}

TOOL_STEPS = {
    "a rope": "mark a safe waiting line between two cones",
    "a flashlight": "inspect the trouble from the safe side without touching it",
    "a ladder": "keep everyone clear while the trained helper locked a ladder in place for a higher view",
    "a map": "mark the hazard and the safest route around it",
    "a walkie-talkie": "report each step and wait for a clear reply before continuing",
}

OPENINGS = [
    "Morning patrol had barely begun.",
    "The city clocks had just chimed nine.",
    "A neighborhood festival filled the streets.",
    "Clouds hurried over the rooftops.",
    "The community garden was opening for the day.",
    "Shopkeepers were lifting their shutters.",
]

PRAISE_LINES = [
    '"You noticed the danger before anyone was hurt. That is excellent hero work,"',
    '"Good spotting. Real courage begins by paying attention,"',
    '"You cared enough to stop and look. I am proud of that choice,"',
    '"Sharp eyes, kind heart. You found the moment when help was needed,"',
    '"That warning may have protected a neighbor. Well done,"',
    '"You saw who needed help, not just a problem to conquer. Good work,"',
]

CHECKLISTS = [
    ("Look, listen, ask, then act", "looked again, listened for changes, asked who was responsible, and only then acted"),
    ("Clear the way, check the risk, choose the helper", "cleared the way, named the risk, and chose the right helper"),
    ("People back, danger marked, grown-ups ready", "moved people back, marked the danger, and waited until the trained adults were ready"),
    ("Pause, plan, protect", "paused, explained the plan, and protected the people nearest the trouble"),
    ("No rush, no guess, one safe step", "stopped rushing, checked the clue, and took one safe step at a time"),
    ("See it, say it, solve it safely", "studied the trouble, said the plan aloud, and solved it with the team"),
]

CLOSING_PRAISE = [
    "praised the careful decision rather than the superhero strength",
    "said the kindest rescue was the one that kept every helper safe",
    "pointed out that changing a risky plan was a brave thing to do",
    "thanked the hero for listening before acting",
    "cheered the teamwork that made the rescue calm",
    "called the patient plan a power worth practicing",
]



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

@dataclass
class Hero:
    name: str
    title: str
    trait: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    hero: object | None = None
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
class Helper:
    name: str
    role: str
    helper: object | None = None
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
class Problem:
    thing: str
    place: str
    risk: str
    caution_rule: str
    repetition_line: str
    problem: object | None = None
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
class World:
    hero: Hero
    helper: Helper
    problem: Problem
    tool: str
    city: str
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.facts.setdefault("story_lines", []).append(text)

    def render(self) -> str:
        return " ".join(self.facts.get("story_lines", []))
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
class StoryParams:
    hero: str
    helper: str
    city: str
    mishap: str
    tool: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero Story world with praise, repetition, caution, and kindness.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--city", choices=CITY_NAMES)
    ap.add_argument("--mishap", choices=MISHAPS)
    ap.add_argument("--tool", choices=TOOLS)
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


def valid_combo(params: StoryParams) -> bool:
    return params.tool in {"a rope", "a flashlight", "a ladder", "a map", "a walkie-talkie"}


def asp_facts() -> str:
    import asp
    lines = []
    for h in HERO_NAMES:
        lines.append(asp.fact("hero", h))
    for h in HELPER_NAMES:
        lines.append(asp.fact("helper", h))
    for c in CITY_NAMES:
        lines.append(asp.fact("city", c))
    for m in MISHAPS:
        lines.append(asp.fact("mishap", m))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


ASP_RULES = r"""
selected(H,He,C,M,T) :- hero(H), helper(He), city(C), mishap(M), tool(T).
good(T) :- tool(T).
valid(H,He,C,M,T) :- selected(H,He,C,M,T), good(T).
#show valid/5.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set()
    for h in HERO_NAMES:
        for he in HELPER_NAMES:
            for c in CITY_NAMES:
                for m in MISHAPS:
                    for t in TOOLS:
                        if valid_combo(StoryParams(h, he, c, m, t, "brave")):
                            py.add((h, he, c, m, t))
    cl = set(asp_valid())
    if cl == py:
        print(f"OK: clingo gate matches Python ({len(cl)} combos).")
        return 0
    print("MISMATCH:")
    print("only in clingo:", sorted(cl - py))
    print("only in python:", sorted(py - cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    city = getattr(args, "city", None) or rng.choice(CITY_NAMES)
    mishap = getattr(args, "mishap", None) or rng.choice(MISHAPS)
    tool = getattr(args, "tool", None) or rng.choice(TOOLS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    params = StoryParams(hero=hero, helper=helper, city=city, mishap=mishap, tool=tool, trait=trait)
    if not valid_combo(params):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def make_world(params: StoryParams) -> World:
    stable_seed = params.seed
    if stable_seed is None:
        signature = "|".join(
            [params.hero, params.helper, params.city, params.mishap, params.tool, params.trait]
        )
        stable_seed = sum((index + 1) * ord(char) for index, char in enumerate(signature))
    rng = random.Random(stable_seed)
    incident = rng.choice(INCIDENTS[params.mishap])
    checklist, checklist_action = rng.choice(CHECKLISTS)
    hero = Hero(
        name=params.hero,
        title="superhero",
        trait=params.trait,
        meters={"courage": 1.0, "kindness": 1.0},
        memes={"pride": 1.0, "worry": 0.0, "praise": 0.0, "repetition": 0.0, "caution": 0.0},
    )
    helper = Helper(name=params.helper, role="guide")
    problem = Problem(
        thing=params.mishap,
        place=params.city,
        risk="someone could get hurt",
        caution_rule="slow down and check first",
        repetition_line="the plan was repeated until it sounded clear and safe",
    )
    return World(
        hero=hero,
        helper=helper,
        problem=problem,
        tool=params.tool,
        city=params.city,
        facts={
            "incident": incident,
            "opening": rng.choice(OPENINGS),
            "first_praise": rng.choice(PRAISE_LINES),
            "checklist": checklist,
            "checklist_action": checklist_action,
            "tool_step": TOOL_STEPS[params.tool],
            "closing_praise": rng.choice(CLOSING_PRAISE),
        },
    )


def generate_story(world: World) -> None:
    h = world.hero
    he = world.helper
    p = world.problem
    incident = world.facts["incident"]
    checklist = world.facts["checklist"]

    article = "an" if h.trait[:1].lower() in "aeiou" else "a"
    world.say(
        f"{world.facts['opening']} In {world.city}, {h.name}, {article} {h.trait} "
        "young superhero, heard someone call for help."
    )
    world.say(f"The trouble was {p.thing}: {incident['premise']}.")
    world.say(
        f"{h.name}'s first impulse was to {incident['impulse']}. "
        f"Then {incident['warning'].lower()}."
    )
    world.say(f"{world.facts['first_praise']} said {he.name}.")
    h.memes["praise"] += 1
    h.memes["worry"] += 0.5

    world.say(
        f'"But praise is not permission to rush," {he.name} added. '
        f'"Use caution. What clue do you see?" {h.name} noticed that {incident["clue"]}.'
    )
    h.memes["caution"] += 1
    h.memes["repetition"] += 1
    world.say(
        f'Together they made a short plan: "{checklist}." {h.name} repeated it; '
        f'the neighbors repeated it; then everyone followed it. The useful repetition settled the '
        f'order in every mind, and the group {world.facts["checklist_action"]}.'
    )

    world.say(
        f"For the next step, {h.name} used {world.tool} to {world.facts['tool_step']}. "
        f"Then the team {incident['solution']}."
    )
    h.meters["helped"] = 1.0
    h.memes["worry"] = max(0.0, h.memes["worry"] - 0.5)

    world.say(
        f"Kindness shaped one more choice: {h.name} {incident['kindness']}. "
        f"Because nobody rushed, {incident['result']}."
    )
    h.memes["praise"] += 1
    h.memes["kindness"] += 1
    world.say(
        f"Afterward, {he.name} {world.facts['closing_praise']}. {h.name} understood the "
        "cautionary lesson: praise should encourage careful kindness, not careless showing off."
    )
    world.say(f"That evening in {world.city}, {incident['ending']}.")


def story_qa(world: World) -> list[QAItem]:
    h, he, p = world.hero, world.helper, world.problem
    incident = world.facts["incident"]
    article = "an" if h.trait[:1].lower() in "aeiou" else "a"
    return [
        QAItem(
            question="Who was the superhero in the story?",
            answer=f"The superhero was {h.name}, {article} {h.trait} young hero in {world.city}.",
        ),
        QAItem(
            question=f"What did {h.name} nearly do too quickly?",
            answer=f"{h.name} nearly tried to {incident['impulse']}. {incident['warning']}.",
        ),
        QAItem(
            question=f"What clue helped {h.name} understand {p.thing}?",
            answer=f"{h.name} noticed that {incident['clue']}. That clue helped the team choose a safer plan.",
        ),
        QAItem(
            question="What plan did everyone repeat?",
            answer=f'Everyone repeated, "{world.facts["checklist"]}." The repetition helped the group remember the safe order.',
        ),
        QAItem(
            question=f"How did {h.name} use {world.tool}?",
            answer=f"{h.name} used {world.tool} to {world.facts['tool_step']}.",
        ),
        QAItem(
            question="How did kindness affect the rescue?",
            answer=f"{h.name} {incident['kindness']}. This made the rescue considerate as well as safe.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is praise?",
            answer="Praise is kind words that tell someone they did a good job.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful so you can stay safe.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing something again to help remember it.",
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means helping others and being gentle with them.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    incident = world.facts["incident"]
    return [
        "Write a child-friendly superhero story where praise, repetition, caution, and kindness all change what the hero does.",
        f"Tell how {world.hero.name} handles {world.problem.thing} in {world.city} after noticing that {incident['clue']}.",
        f"Write a cautionary rescue in which a hero repeats the plan '{world.facts['checklist']}' and uses {world.tool} safely.",
    ]


def dump_trace(world: World) -> str:
    h = world.hero
    incident = world.facts["incident"]
    lines = ["--- world model state ---"]
    lines.append(f"hero={h.name} meters={h.meters} memes={h.memes}")
    lines.append(f"helper={world.helper.name} role={world.helper.role}")
    lines.append(f"problem={world.problem.thing} place={world.problem.place}")
    lines.append(f"incident={incident['id']} clue={incident['clue']}")
    lines.append(f"result={incident['result']}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== world QA ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams("Nova", "Captain Bright", "Sunrise City", "a blocked bridge", "a rope", "brave"),
    StoryParams("Pip", "Aunt Beacon", "Rivergate", "a lost kitten", "a flashlight", "gentle"),
    StoryParams("Zuri", "Coach Star", "Bluebell Town", "a fallen sign", "a ladder", "careful"),
]


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    generate_story(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show valid/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/5."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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
