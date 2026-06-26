#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260626T060043Z_seed274930118_n5000/efficiency_whip_hoof_daycare_room_cautionary_ghost.py
=============================================================================================================

A small cautionary ghost-story world set in a daycare room.

Seed-tale inspiration:
A child in a daycare room wants to play a spooky game with a toy whip and a
hoof-clopping ghost horse. A careful grown-up warns that the whip could hit
friends, knock over blocks, or make a big, silly mess. The child feels spooked
and disappointed, then finds a gentler, cleverer game that keeps the ghostly
fun but avoids the danger.

The simulation tracks:
- physical meters: noise, mess, wobble, spooky, soot
- emotional memes: fear, caution, delight, embarrassment, relief, efficiency
- cautionary turn: a warning about a risky object and an unsafe action
- resolution: a safer substitute that preserves the pretend ghost mood

The world aims for a classical TinyStories shape with a beginning, a tension,
and a clean ending image that proves something changed.
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
# World constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0



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
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    caretaker: object | None = None
    hero: object | None = None
    prop_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "teacher", "grown-up"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
class StoryParams:
    hero: str
    gender: str
    caretaker: str
    seed: Optional[int] = None
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
class StoryPiece:
    title: str
    text: str
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


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    mess: str
    spooky: str
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
class Prop:
    id: str
    label: str
    phrase: str
    safe_alt: str
    activity_id: str
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


SETTING = "the daycare room"

ACTIVITIES = {
    "whip": Activity(
        id="whip",
        verb="swing the whip",
        gerund="swinging the whip",
        rush="grab the whip and spin it",
        risk="could snap past a face or tap a friend too hard",
        mess="wobble",
        spooky="made a sharp snap that sounded extra ghostly",
    ),
    "hoof": Activity(
        id="hoof",
        verb="make hoof sounds",
        gerund="making hoof sounds",
        rush="run on tiptoe like a spooky horse",
        risk="could bump the block tower and start a tumble",
        mess="noise",
        spooky="clopped so loudly that the room felt haunted",
    ),
    "efficiency": Activity(
        id="efficiency",
        verb="make a super-efficient cleanup game",
        gerund="planning an efficient cleanup",
        rush="dash around tidying too fast",
        risk="could scatter toys while trying to go quicker and quicker",
        mess="mess",
        spooky="made the room feel busy like a tiny ghost factory",
    ),
}

PROPS = {
    "toy_whip": Prop(
        id="toy_whip",
        label="toy whip",
        phrase="a soft toy whip with a red handle",
        safe_alt="a ribbon streamer",
        activity_id="whip",
    ),
    "hoof_stamps": Prop(
        id="hoof_stamps",
        label="hoof stamps",
        phrase="cardboard hoof stamps",
        safe_alt="paper hoof prints",
        activity_id="hoof",
    ),
    "speed_chart": Prop(
        id="speed_chart",
        label="speed chart",
        phrase="a little efficiency chart",
        safe_alt="a slow-and-steady picture card",
        activity_id="efficiency",
    ),
}

HERO_NAMES = ["Mina", "Toby", "Lena", "Nico", "Pia", "Jasper"]
CARETAKERS = {
    "teacher": "the teacher",
    "grown-up": "the grown-up",
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary daycare-room ghost story world.")
    ap.add_argument("--hero", choices=HERO_NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker", choices=list(CARETAKERS))
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    caretaker = getattr(args, "caretaker", None) or rng.choice(list(CARETAKERS))
    return StoryParams(hero=hero, gender=gender, caretaker=caretaker)


def choose_activity(rng: random.Random) -> Activity:
    return rng.choice([ACTIVITIES["whip"], ACTIVITIES["hoof"], ACTIVITIES["efficiency"]])


def choose_prop(activity: Activity) -> Prop:
    for prop in PROPS.values():
        if prop.activity_id == activity.id:
            return prop
    pass


def _meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def setup_world(params: StoryParams, activity: Activity, prop: Prop) -> World:
    w = World()
    hero_type = params.gender
    hero = w.add(Entity(id=params.hero, kind="character", type=hero_type))
    caretaker = w.add(Entity(id="caretaker", kind="character", type=params.caretaker, label=_safe_lookup(CARETAKERS, params.caretaker)))
    prop_ent = w.add(Entity(id=prop.id, type="thing", label=prop.label, phrase=prop.phrase, owner=hero.id))
    w.facts.update(hero=hero, caretaker=caretaker, prop=prop_ent, activity=activity, setting=SETTING)
    return w


def narrate_intro(w: World) -> None:
    hero: Entity = w.facts["hero"]
    activity: Activity = w.facts["activity"]
    prop: Entity = w.facts["prop"]
    caretaker: Entity = w.facts["caretaker"]
    w.say(
        f"{hero.id} was a little {hero.type} in {SETTING} who loved ghost stories."
    )
    w.say(
        f"{hero.id} found {prop.phrase} and imagined {activity.spooky}."
    )
    w.say(
        f"{hero.id} wanted to {activity.verb}, because spooky games felt fun and brave."
    )
    _meme(hero, "delight", 1)
    _meme(hero, "efficiency", 1)


def warn_and_turn(w: World) -> None:
    hero: Entity = w.facts["hero"]
    caretaker: Entity = w.facts["caretaker"]
    activity: Activity = w.facts["activity"]
    prop: Entity = w.facts["prop"]

    _meme(hero, "caution", 1)
    _meme(hero, "fear", 1)
    if activity.id == "whip":
        _meter(hero, "spooky", 1)
        w.say(
            f'"Careful," {caretaker.label_word} said. "That {prop.label} could {activity.risk}."'
        )
    elif activity.id == "hoof":
        _meter(hero, "noise", 1)
        w.say(
            f'"Careful," {caretaker.label_word} said. "Those hoof sounds could {activity.risk}."'
        )
    else:
        _meter(hero, "mess", 1)
        w.say(
            f'"Careful," {caretaker.label_word} said. "Trying to go too fast could {activity.risk}."'
        )
    w.say(
        f"{hero.id} stopped short and felt a small shiver, like a friendly ghost had tapped {hero.pronoun('possessive')} shoulder."
    )


def resolve(w: World) -> None:
    hero: Entity = w.facts["hero"]
    caretaker: Entity = w.facts["caretaker"]
    activity: Activity = w.facts["activity"]
    prop: Entity = w.facts["prop"]

    _meme(hero, "relief", 1)
    _meme(hero, "caution", 1)
    w.para()
    if activity.id == "whip":
        w.say(
            f'{caretaker.label_word} smiled and said, "How about a {prop.safe_alt} instead?"'
        )
        w.say(
            f"{hero.id} tried the {prop.safe_alt}, which swished softly and did not snap at anybody."
        )
    elif activity.id == "hoof":
        w.say(
            f'{caretaker.label_word} pointed to some paper shapes. "How about paper hoof prints instead?"'
        )
        w.say(
            f"{hero.id} stamped the paper hoof prints beside a little ghost horse picture."
        )
    else:
        w.say(
            f'{caretaker.label_word} held up a picture card. "Let’s make a slow-and-steady cleanup game."'
        )
        w.say(
            f"{hero.id} helped put blocks in bins one by one, and the room became neat without rushing."
        )
    _meme(hero, "efficiency", 1)
    _meme(hero, "delight", 1)


def generate_story(params: StoryParams, rng: random.Random) -> StorySample:
    activity = choose_activity(rng)
    prop = choose_prop(activity)
    w = setup_world(params, activity, prop)
    narrate_intro(w)
    w.para()
    warn_and_turn(w)
    resolve(w)
    hero: Entity = w.facts["hero"]
    caretaker: Entity = w.facts["caretaker"]
    w.say(
        f"In the end, {SETTING} stayed calm, and {hero.id} learned that a little caution could keep the ghost game fun."
    )
    w.say(
        f"{caretaker.label_word} laughed, {hero.id} smiled, and the room felt tidy and safe."
    )
    w.facts["resolved"] = True
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_qa(w),
        world=w,
    )


def generation_prompts(w: World) -> list[str]:
    hero: Entity = w.facts["hero"]
    activity: Activity = w.facts["activity"]
    prop: Entity = w.facts["prop"]
    return [
        f'Write a short cautionary ghost story set in a daycare room that includes "{prop.label}" and "{activity.id}".',
        f"Tell a child-facing story where {hero.id} wants to {activity.verb} but a grown-up warns them gently.",
        f"Make a daycare-room story with a spooky feeling, a safety warning, and a safer replacement for {prop.label}.",
    ]


def story_qa(w: World) -> list[QAItem]:
    hero: Entity = w.facts["hero"]
    caretaker: Entity = w.facts["caretaker"]
    activity: Activity = w.facts["activity"]
    prop: Entity = w.facts["prop"]
    return [
        QAItem(
            question=f"Who was the story about in {SETTING}?",
            answer=f"It was about {hero.id}, a little {hero.type} who loved ghost stories and daycare-room play.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {prop.label}?",
            answer=f"{hero.id} wanted to {activity.verb}, because it seemed spooky and exciting.",
        ),
        QAItem(
            question=f"Why did {caretaker.label_word} warn {hero.id}?",
            answer=f"{caretaker.label_word} warned {hero.id} because {activity.risk}.",
        ),
        QAItem(
            question=f"What safer idea did they choose instead of the risky plan?",
            answer=_safer_answer(activity, prop),
        ),
    ]


def _safer_answer(activity: Activity, prop: Prop) -> str:
    if activity.id == "whip":
        return "They chose a ribbon streamer, which swished softly without hitting anyone."
    if activity.id == "hoof":
        return "They used paper hoof prints, which made the game spooky without bumping the blocks."
    return "They used a slow-and-steady cleanup game, which kept the room neat without rushing."
    

def world_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a daycare room?",
            answer="A daycare room is a safe room where young children play, learn, and rest together.",
        ),
        QAItem(
            question="What does caution mean?",
            answer="Caution means paying attention to danger so nobody gets hurt.",
        ),
        QAItem(
            question="What does efficiency mean in a simple way?",
            answer="Efficiency means doing a job well without wasting extra time or effort.",
        ),
        QAItem(
            question="Why should a whip be used carefully?",
            answer="A whip should be used carefully because it can snap hard and hurt someone if it is swung carelessly.",
        ),
        QAItem(
            question="What does hoof mean when people talk about animals?",
            answer="A hoof is the hard foot of an animal like a horse.",
        ),
    ]


def dump_trace(w: World) -> str:
    lines = ["--- trace ---"]
    for e in w.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
activity(whip).
activity(hoof).
activity(efficiency).

risk(whip,snap).
risk(hoof,bump).
risk(efficiency,scatter).

safe_alt(whip,ribbon_streamer).
safe_alt(hoof,paper_hoof_prints).
safe_alt(efficiency,slow_and_steady_game).

valid(A) :- activity(A).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("setting", "daycare_room")]
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for p in PROPS:
        lines.append(asp.fact("prop", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/1."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = {(a,) for a in ACTIVITIES}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python ({len(py_set)} activities).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP only:", sorted(asp_set - py_set))
    print("Python only:", sorted(py_set - asp_set))
    return 1


def build_sample(args: argparse.Namespace, seed: int) -> StorySample:
    rng = random.Random(seed)
    params = resolve_params(args, rng)
    params.seed = seed
    return generate(params)


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    return generate_story(params, rng)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"[prompt {i}] {p}")
        print()
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid/1."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print("valid activities:", ", ".join(v[0] for v in vals))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        params_list = [
            StoryParams(hero="Mina", gender="girl", caretaker="teacher", seed=base_seed),
            StoryParams(hero="Toby", gender="boy", caretaker="grown-up", seed=base_seed + 1),
            StoryParams(hero="Lena", gender="girl", caretaker="teacher", seed=base_seed + 2),
        ]
        samples = [generate(p) for p in params_list]
    else:
        samples = []
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            sample = build_sample(args, base_seed + i)
            i += 1
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
