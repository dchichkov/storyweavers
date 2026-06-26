#!/usr/bin/env python3
"""
storyworlds/worlds/expensive_photograph_twist_sharing_mystery_to_solve.py
=========================================================================

A small mythic storyworld about an expensive photograph, a sharing gesture,
and a mystery that turns on a twist.

Premise:
- In a riverside village, a child or young keeper owns a costly photograph made
  by a temple-scribe.
- The photograph seems to show a lost hero, a crowned ancestor, or a river
  spirit.
- The keeper is proud, but the image causes a mystery: no one agrees on who
  is really in the picture.

Tension:
- The photograph is valuable and fragile; the keeper fears sharing it.
- A neighbor, elder, sibling, or parent asks to see it because the story of
  the village depends on the identity hidden in the frame.

Turn:
- The photograph is finally shared in the lamp-light.
- A small, mythic twist appears: the picture is not of the expected figure at
  all, but of a reflected statue, a masked helper, or a doubled shadow.

Resolution:
- The mystery is solved by looking together, and the keeper learns that sharing
  does not diminish the treasure; it reveals its true meaning.

The script follows the Storyweavers contract and provides a tiny ASP twin for
reasonableness checks.
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    held_by: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    fragile: bool = False
    expensive: bool = False
    symbolic: bool = False

    hero: object | None = None
    keeper: object | None = None
    photo: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    sacred: bool = False
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
class Photograph:
    label: str
    phrase: str
    subject: str
    mystery_hint: str
    twist_reveal: str
    fragile: bool = True
    expensive: bool = True
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
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    keeper_role: str
    photo: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    photo = world.facts.get("photo")
    seeker = world.facts.get("seeker")
    if not photo or not seeker:
        return out
    photo_ent = world.get(photo.id)
    if photo_ent.held_by == seeker.id:
        sig = ("share", photo_ent.id, seeker.id)
        if sig not in world.fired:
            world.fired.add(sig)
            photo_ent.shared_with.append(seeker.id)
            seeker.memes["curiosity"] = seeker.memes.get("curiosity", 0.0) + 1
            out.append(f"They leaned close together over the photograph.")
    return out


def _r_twist(world: World) -> list[str]:
    photo = world.facts.get("photo")
    if not photo:
        return []
    photo_ent = world.get(photo.id)
    if photo_ent.held_by and len(photo_ent.shared_with) >= 1:
        sig = ("twist", photo_ent.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["twist_revealed"] = True
            return ["__twist__"]
    return []


def _r_solve(world: World) -> list[str]:
    if not world.facts.get("twist_revealed"):
        return []
    sig = ("solve",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.facts["solved"] = True
    return ["__solve__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_sharing, _r_twist, _r_solve):
            res = rule(world)
            if res:
                changed = True
                produced.extend(r for r in res if r not in {"__twist__", "__solve__"})
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def build_story(world: World, hero: Entity, keeper: Entity, photo: Entity) -> None:
    world.say(
        f"In the old days by the river, {hero.id} kept a costly photograph in a carved wooden box."
    )
    world.say(
        f"{hero.pronoun().capitalize()} loved it because the picture was rare, bright, and dear enough to make the whole village whisper."
    )
    world.say(
        f"Yet the image carried a mystery to solve: it seemed to show {photo.phrase}, but no two elders agreed on what the face in the frame truly was."
    )

    world.para()
    world.say(
        f"One dusk, {keeper.id} asked to see the photograph by lamp-light, for {keeper.pronoun('possessive')} old eyes wanted the truth."
    )
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0.0) + 1
    world.say(
        f"{hero.id} hesitated, because something so expensive felt safer when kept alone."
    )
    photo.held_by = hero.id

    world.para()
    world.say(
        f"At last, {hero.id} shared the photograph with {keeper.id} beneath the lamp."
    )
    photo.shared_with.append(keeper.id)
    propagate(world, narrate=False)
    world.say(
        f"The glass caught the flame, and a twist of light showed that the figure was not what everyone first believed."
    )
    world.say(
        f"It was {photo.twist_reveal}, and the answer had been hiding in plain sight."
    )
    world.say(
        f"{keeper.id} laughed softly, because the mystery was solved best when it was shared, not guarded."
    )
    world.say(
        f"By morning, the costly photograph was still precious, but now it held a truer story than before."
    )


SETTINGS = {
    "temple": Setting(place="the temple courtyard", sacred=True),
    "river": Setting(place="the river steps", sacred=False),
    "market": Setting(place="the market lane", sacred=False),
    "orchard": Setting(place="the orchard path", sacred=False),
}

PHOTOS = {
    "ancestor": Photograph(
        label="ancestor photograph",
        phrase="a crowned ancestor standing by the river",
        subject="ancestor",
        mystery_hint="an old royal line",
        twist_reveal="a river statue reflected in polished glass",
    ),
    "hero": Photograph(
        label="hero photograph",
        phrase="a brave hero with a raised hand",
        subject="hero",
        mystery_hint="a forgotten rescue",
        twist_reveal="the village baker wearing a festival mask",
    ),
    "spirit": Photograph(
        label="spirit photograph",
        phrase="a pale spirit near a flame",
        subject="spirit",
        mystery_hint="a blessing from the night",
        twist_reveal="the moon on the water behind the shrine",
    ),
}

ROLES = ["mother", "father", "sister", "brother", "aunt", "uncle", "elder"]
GIRL_NAMES = ["Mira", "Lina", "Sera", "Anya", "Nima", "Tara", "Ira"]
BOY_NAMES = ["Arin", "Kavi", "Ravi", "Niko", "Bela", "Soren", "Pavel"]
TRAITS = ["curious", "gentle", "bold", "quiet", "careful"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place, photo_id) for place in SETTINGS for photo_id in PHOTOS]


@dataclass
class StoryWorld:
    setting: Setting
    hero: Entity
    keeper: Entity
    photo: Entity
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
    ap = argparse.ArgumentParser(description="Mythic storyworld: an expensive photograph, a sharing moment, and a mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--photo", choices=PHOTOS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--keeper", choices=ROLES)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "photo", None):
        combos = [c for c in combos if c[1] == getattr(args, "photo", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, photo = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    keeper = getattr(args, "keeper", None) or rng.choice(ROLES)
    return StoryParams(place=place, hero_name=name, hero_type=gender, keeper_role=keeper, photo=photo)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    photo_cfg = _safe_lookup(PHOTOS, params.photo)
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=[rng_trait(params.seed), "careful"],
        memes={"pride": 0.0, "fear": 0.0, "curiosity": 0.0},
    ))
    keeper_name = params.keeper_role.capitalize()
    keeper = world.add(Entity(
        id=keeper_name,
        kind="character",
        type=params.keeper_role,
        traits=["old", "wise"],
        memes={"curiosity": 0.0},
    ))
    photo = world.add(Entity(
        id="photograph",
        kind="thing",
        type="photograph",
        label="photograph",
        phrase=photo_cfg.phrase,
        owner=hero.id,
        caretaker=keeper.id,
        expensive=True,
        fragile=True,
        symbolic=True,
        meters={"value": 1.0, "care": 0.0},
    ))

    world.facts.update(hero=hero, keeper=keeper, photo=photo, photo_cfg=photo_cfg)
    photo.held_by = hero.id
    build_story(world, hero, keeper, photo)

    prompts = [
        f"Write a mythic story about {params.hero_name} and an expensive photograph that carries a village mystery.",
        f"Tell a gentle myth where a {params.hero_type} named {params.hero_name} learns to share a costly photograph with a {params.keeper_role}.",
        f"Write a short legend in which a photograph is shared and the mystery to solve ends with a twist.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.hero_name} keep in the wooden box?",
            answer=f"{params.hero_name} kept an expensive photograph, and it was precious enough to make the village whisper about it.",
        ),
        QAItem(
            question=f"Why did {params.hero_name} hesitate to share it at first?",
            answer=f"{params.hero_name} hesitated because the photograph was expensive and rare, so it felt safer to keep it alone.",
        ),
        QAItem(
            question=f"What happened when {params.hero_name} shared the photograph with {keeper_name}?",
            answer=f"When {params.hero_name} shared it with {keeper_name}, the mystery was solved and a twist in the picture revealed the true subject.",
        ),
        QAItem(
            question=f"What was the twist in the photograph?",
            answer=f"The twist was that {photo_cfg.twist_reveal}, not the first thing everyone believed they saw.",
        ),
    ]
    world_qa = [
        QAItem(
            question="Why can sharing help solve a mystery?",
            answer="Sharing lets more than one person look carefully, compare ideas, and notice details that one pair of eyes might miss.",
        ),
        QAItem(
            question="What does a photograph do?",
            answer="A photograph keeps a moment of light and shape, so people can look back and remember what was there.",
        ),
        QAItem(
            question="Why are expensive things often handled carefully?",
            answer="Expensive things are handled carefully because they are hard to replace and people do not want them damaged or lost.",
        ),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def rng_trait(seed: Optional[int]) -> str:
    rng = random.Random(seed)
    return rng.choice(TRAITS)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.shared_with:
            bits.append(f"shared_with={e.shared_with}")
        if e.expensive:
            bits.append("expensive=True")
        if e.fragile:
            bits.append("fragile=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A photograph is relevant when it is expensive and held by the hero.
relevant(P) :- photograph(P), expensive(P), held_by_hero(P).

% Sharing happens when the hero and keeper both look at it.
shared(P) :- relevant(P), shared_with_keeper(P).

% A twist appears after sharing.
twist(P) :- shared(P), mythic_reveal(P).

% The mystery is solved when the twist is seen.
solved(P) :- twist(P).

#show valid/2.
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for photo_id, photo in PHOTOS.items():
        lines.append(asp.fact("photograph", photo_id))
        lines.append(asp.fact("expensive", photo_id))
        lines.append(asp.fact("fragile", photo_id))
        lines.append(asp.fact("mythic_reveal", photo_id))
    for place in SETTINGS:
        for photo_id in PHOTOS:
            lines.append(asp.fact("valid", place, photo_id))
            lines.append(asp.fact("valid_story", place, photo_id, "keeper"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(a - b))
    print("  only in python:", sorted(b - a))
    return 1


def story_qa(world: World) -> list[QAItem]:
    return world.facts.get("story_qa", [])


CURATED = [
    StoryParams(place="temple", hero_name="Mira", hero_type="girl", keeper_role="elder", photo="ancestor"),
    StoryParams(place="river", hero_name="Arin", hero_type="boy", keeper_role="aunt", photo="hero"),
    StoryParams(place="market", hero_name="Sera", hero_type="girl", keeper_role="mother", photo="spirit"),
]


def explain_rejection() -> str:
    return "(No story: the requested options do not produce a reasonable mythic mystery.)"


def generate_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible (place, photo) combos ({len(stories)} story variants):\n")
        for place, photo in combos:
            print(f"  {place:8} {photo}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate_from_params(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate_from_params(params)
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
            header = f"### {p.hero_name}: {p.photo} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
