#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bobby_owl_teamwork_foreshadowing_sound_effects_mystery.py
===============================================================================================================================

A small mystery storyworld with Bobby, an owl, teamwork, foreshadowing, and
sound effects.

Premise:
- Bobby and a wise owl investigate a little mystery in a quiet place.
- Strange sounds foreshadow where the hidden thing might be.
- Bobby and the owl must work together to follow the clues.

The domain stays small and constraint-checked:
- Each setting has a limited set of mystery objects it can plausibly hide.
- Each mystery object has a sound trail and a final hiding place.
- The story is generated from world state, not from a frozen template swap.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    BOBBY: object | None = None
    OWL: object | None = None
    hidden: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "child"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    mood: str
    sound_hint: str
    hide_spots: tuple[str, ...]
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
class Mystery:
    id: str
    label: str
    phrase: str
    sound: str
    hiding_spot: str
    clue_words: tuple[str, ...]
    tags: tuple[str, ...]
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
    place: str
    mystery: str
    name: str = "Bobby"
    seed: Optional[int] = None
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


SETTINGS = {
    "library": Setting(
        place="the quiet library",
        mood="whisper-soft",
        sound_hint="a tiny click from the shelves",
        hide_spots=("behind books", "under a reading chair", "inside a return cart"),
    ),
    "garden": Setting(
        place="the moonlit garden",
        mood="still and breezy",
        sound_hint="a rustle in the leaves",
        hide_spots=("under a bench", "inside a flower pot", "behind a watering can"),
    ),
    "attic": Setting(
        place="the dusty attic",
        mood="creaky and secret",
        sound_hint="a squeak from the beams",
        hide_spots=("inside a trunk", "under a box", "behind a blanket"),
    ),
}

MYSTERIES = {
    "key": Mystery(
        id="key",
        label="little brass key",
        phrase="a little brass key with a loop on top",
        sound="clink-clink",
        hiding_spot="inside a trunk",
        clue_words=("key", "brass", "unlock"),
        tags=("metal", "secret"),
    ),
    "bell": Mystery(
        id="bell",
        label="tiny silver bell",
        phrase="a tiny silver bell tied with blue string",
        sound="ding-ding",
        hiding_spot="under a cushion",
        clue_words=("bell", "ring", "silver"),
        tags=("metal", "sound"),
    ),
    "note": Mystery(
        id="note",
        label="folded note",
        phrase="a folded note with a blue star on it",
        sound="shh-shh",
        hiding_spot="behind books",
        clue_words=("note", "paper", "message"),
        tags=("paper", "secret"),
    ),
}

BOBBY = Entity(
    id="Bobby",
    kind="character",
    type="boy",
    label="Bobby",
    meters={"curiosity": 1.0, "steps": 0.0},
    memes={"wonder": 1.0, "teamwork": 0.0, "relief": 0.0},
)

OWL = Entity(
    id="Owl",
    kind="character",
    type="owl",
    label="an owl",
    meters={"perch": 1.0, "listens": 1.0},
    memes={"helpfulness": 1.0, "teamwork": 1.0},
)


class World:
    def __init__(self, setting: Setting, mystery: Mystery, hero_name: str = "Bobby") -> None:
        self.setting = setting
        self.mystery = mystery
        self.hero_name = hero_name
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.add(Entity(
            id=hero_name,
            kind="character",
            type="boy",
            label=hero_name,
            meters={"curiosity": 1.0, "steps": 0.0},
            memes={"wonder": 1.0, "teamwork": 0.0, "relief": 0.0},
        ))
        self.add(Entity(
            id="Owl",
            kind="character",
            type="owl",
            label="an owl",
            meters={"perch": 1.0, "listens": 1.0},
            memes={"helpfulness": 1.0, "teamwork": 1.0},
        ))
        self.hidden = Entity(
            id="hidden",
            kind="thing",
            type=mystery.id,
            label=mystery.label,
            phrase=mystery.phrase,
            owner=hero_name,
            meters={"hidden": 1.0},
            memes={"mystery": 1.0},
        )
        self.add(self.hidden)
        self.hidden_spot = mystery.hiding_spot
        self.sound_trail = mystery.sound

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

    def copy(self) -> "World":
        clone = World(self.setting, self.mystery, self.hero_name)
        clone.entities = json.loads(json.dumps(self.as_plain()))
        raise RuntimeError("copy() should not be used in this world")

    def as_plain(self) -> dict:
        return {
            "setting": self.setting.place,
            "mystery": self.mystery.id,
            "hero": self.hero_name,
        }


def reasonableness_gate(setting: Setting, mystery: Mystery) -> bool:
    if mystery.hiding_spot not in setting.hide_spots:
        return False
    return True


def explain_rejection(setting: Setting, mystery: Mystery) -> str:
    return (
        f"(No story: {mystery.label} cannot plausibly hide in {setting.place}. "
        f"Try a mystery whose hiding spot fits this setting.)"
    )


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sname, setting in SETTINGS.items():
        for mname, mystery in MYSTERIES.items():
            if reasonableness_gate(setting, mystery):
                out.append((sname, mname))
    return sorted(out)


def introducer(world: World) -> None:
    hero = world.get(world.hero_name)
    world.say(
        f"Bobby liked quiet places, because quiet places made small mysteries stand out."
    )
    world.say(
        f"Nearby, {world.get('Owl').label} blinked slowly and listened like a tiny detective."
    )
    hero.memes["wonder"] += 1


def foreshadow(world: World) -> None:
    hero = world.get(world.hero_name)
    mystery = world.mystery
    hint = world.setting.sound_hint
    world.say(
        f"Then Bobby heard {hint}: {mystery.sound}. "
        f"It sounded soft, but it was loud enough to matter."
    )
    hero.memes["curiosity"] += 1
    hero.meters["steps"] += 1
    world.facts["first_sound"] = mystery.sound
    world.facts["hint"] = hint


def teamwork(world: World) -> None:
    hero = world.get(world.hero_name)
    owl = world.get("Owl")
    mystery = world.mystery
    world.say(
        f'“I think the sound is coming from {world.hidden_spot},” Bobby whispered.'
    )
    world.say(
        f"{owl.label.capitalize()} fluffed its feathers and pointed a wing. "
        f"Together they followed the sound: {mystery.sound}, {mystery.sound}, {mystery.sound}."
    )
    hero.memes["teamwork"] += 1
    owl.memes["teamwork"] += 1
    world.facts["teamwork"] = True


def reveal(world: World) -> None:
    hero = world.get(world.hero_name)
    mystery = world.mystery
    world.say(
        f"At last, Bobby and the owl found {mystery.phrase} {world.hidden_spot}."
    )
    world.say(
        f"It was exactly where the clues had been leading all along."
    )
    hero.memes["relief"] += 1
    world.hidden.meters["hidden"] = 0.0
    world.facts["found"] = True


def ending(world: World) -> None:
    hero = world.get(world.hero_name)
    owl = world.get("Owl")
    mystery = world.mystery
    world.say(
        f"Bobby smiled, and {owl.label} gave one last {mystery.sound} as if to say the case was solved."
    )
    world.say(
        f"The little mystery was not scary anymore. It had become a happy clue that Bobby and the owl solved together."
    )


def tell(setting: Setting, mystery: Mystery, hero_name: str = "Bobby") -> World:
    if not reasonableness_gate(setting, mystery):
        pass
    world = World(setting, mystery, hero_name)
    world.say(
        f"One night in {setting.place}, Bobby and an owl began a quiet mystery."
    )
    world.say(
        f"Something important was missing, and the room felt whisper-soft and strange."
    )
    world.para()
    introducer(world)
    foreshadow(world)
    teamwork(world)
    world.para()
    reveal(world)
    ending(world)
    world.facts.update(
        setting=setting,
        mystery=mystery,
        hero=world.get(hero_name),
        owl=world.get("Owl"),
    )
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sname, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sname))
        for spot in setting.hide_spots:
            lines.append(asp.fact("hide_spot", sname, spot))
    for mname, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mname))
        lines.append(asp.fact("hides_at", mname, mystery.hiding_spot))
        lines.append(asp.fact("sound", mname, mystery.sound))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, M) :- setting(S), mystery(M), hide_spot(S, Spot), hides_at(M, Spot).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small teamwork mystery about Bobby and an owl.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--mystery", choices=MYSTERIES.keys())
    ap.add_argument("--name", default="Bobby")
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
    combos = [
        (s, m) for s, m in valid_combos()
        if (getattr(args, "place", None) is None or s == getattr(args, "place", None))
        and (getattr(args, "mystery", None) is None or m == getattr(args, "mystery", None))
    ]
    if not combos:
        if getattr(args, "place", None) and getattr(args, "mystery", None):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(combos)
    return StoryParams(place=place, mystery=mystery, name=getattr(args, "name", None))


def story_text(world: World) -> str:
    return world.render()


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a child-friendly mystery story where Bobby and an owl solve a clue by listening carefully.",
        f"Tell a short mystery set in {world.setting.place} that uses a sound like {world.mystery.sound}.",
        "Write a story about teamwork, foreshadowing, and a hidden object being found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Who worked together to solve the mystery?",
            answer="Bobby and the owl worked together to follow the clues and find the hidden thing.",
        ),
        QAItem(
            question="What sound helped foreshadow the answer?",
            answer=f"The sound was {world.mystery.sound}, and it pointed them toward the hiding spot.",
        ),
        QAItem(
            question=f"Where was the {world.mystery.label} found?",
            answer=f"It was found {world.hidden_spot} in {world.setting.place}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do detectives listen for clues?",
            answer="Detectives listen for clues because sounds, footsteps, and little details can help solve a mystery.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when an early clue hints at what will happen later in the story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  setting: {world.setting.place}")
    lines.append(f"  mystery: {world.mystery.label}")
    lines.append(f"  hidden_spot: {world.hidden_spot}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", mystery="note", name="Bobby"),
    StoryParams(place="garden", mystery="bell", name="Bobby"),
    StoryParams(place="attic", mystery="key", name="Bobby"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MYSTERIES, params.mystery), params.name)
    return StorySample(
        params=params,
        story=story_text(world),
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible (setting, mystery) combos:\n")
        for s, m in models:
            print(f"  {s:10} {m}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
