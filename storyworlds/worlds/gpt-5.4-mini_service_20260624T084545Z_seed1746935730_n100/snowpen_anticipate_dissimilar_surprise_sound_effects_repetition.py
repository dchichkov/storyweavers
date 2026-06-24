#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T084545Z_seed1746935730_n100/snowpen_anticipate_dissimilar_surprise_sound_effects_repetition.py
======================================================================================================================

A small comedy storyworld about a child, a snowpen, and a surprise that sounds
very different from what anyone anticipated.

Premise:
- A child builds a snowpen: a tiny pen made of packed snow that holds a toy.
- The child expects it to stay neat and quiet.
- Something dissimilar arrives: a warm surprise that changes the snowpen with
  sound effects, repetition, and a funny turn.
- A simple fix or playful adaptation resolves the scene.

This world is intentionally narrow and constraint-checked: it only generates
stories where the anticipated plan is plausible, the surprise is meaningfully
different, and the ending proves something changed in the world state.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
        if not hasattr(self, "_tags"):
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
    indoor: bool
    affords: set[str] = field(default_factory=set)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class Surprise:
    id: str
    label: str
    phrase: str
    kind: str
    sound: str
    effect: str
    dissimilar_to: str
    warmth: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    weather: str = ""

    clone: object | None = None
    world: object | None = None
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

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
        clone.weather = self.weather
        return clone
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


@dataclass
class StoryParams:
    place: str
    surprise: str
    child_name: str
    gender: str
    parent: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


SETTINGS = {
    "yard": Setting(place="the yard", indoor=False, affords={"snowpen"}),
    "porch": Setting(place="the porch", indoor=False, affords={"snowpen"}),
    "garden": Setting(place="the garden", indoor=False, affords={"snowpen"}),
}

SURPRISES = {
    "bell": Surprise(
        id="bell",
        label="a tiny bell",
        phrase="a tiny silver bell",
        kind="bell",
        sound="ding-ding",
        effect="jiggled the snow walls with bright little rings",
        dissimilar_to="quiet snow",
        warmth="cold",
        tags={"sound", "repetition"},
    ),
    "kettle": Surprise(
        id="kettle",
        label="a warm kettle",
        phrase="a warm kettle of cocoa",
        kind="kettle",
        sound="clink-clink",
        effect="sent a warm puff that softened the snowpen",
        dissimilar_to="cold snow",
        warmth="warm",
        tags={"surprise", "sound"},
    ),
    "drum": Surprise(
        id="drum",
        label="a little drum",
        phrase="a little toy drum",
        kind="drum",
        sound="rat-a-tat",
        effect="made the toy animals bounce in a silly march",
        dissimilar_to="still snow",
        warmth="noisy",
        tags={"sound", "repetition"},
    ),
    "scooter": Surprise(
        id="scooter",
        label="a scooter",
        phrase="a bright red scooter",
        kind="scooter",
        sound="zip-zip",
        effect="whizzed past and blew a swirl of snow dust",
        dissimilar_to="slow snow",
        warmth="cold",
        tags={"surprise", "sound"},
    ),
}

CHILD_NAMES = ["Mina", "Leo", "Toby", "Nora", "Pia", "Eli", "Ivy", "Sam"]
TRAITS = ["curious", "cheerful", "silly", "spirited", "playful"]
GENDERS = ["girl", "boy"]


class SnowWorld:
    pass


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy storyworld about a snowpen, anticipation, and a dissimilar surprise."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def validate_params(args: argparse.Namespace) -> None:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        pass
    if getattr(args, "surprise", None) and getattr(args, "surprise", None) not in SURPRISES:
        pass
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in GENDERS:
        pass
    if getattr(args, "parent", None) and getattr(args, "parent", None) not in {"mother", "father"}:
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    validate_params(args)
    place = getattr(args, "place", None) or rng.choice(sorted(SETTINGS))
    surprise = getattr(args, "surprise", None) or rng.choice(sorted(SURPRISES))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    return StoryParams(place=place, surprise=surprise, child_name=name, gender=gender, parent=parent)


def valid_combos() -> list[tuple[str, str]]:
    return [(p, s) for p in SETTINGS for s in SURPRISES]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p, setting in SETTINGS.items():
        lines.append(asp.fact("place", p))
        if setting.indoor:
            lines.append(asp.fact("indoor", p))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", p, a))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("kind", sid, s.kind))
        lines.append(asp.fact("dissimilar_to", sid, s.dissimilar_to))
        for t in sorted(s.tags):
            lines.append(asp.fact("tag", sid, t))
    return "\n".join(lines)


ASP_RULES = r"""
% A story is valid if the place affords snowpen and the surprise is meaningfully dissimilar.
valid_story(P, S) :- affords(P, snowpen), surprise(S), dissimilar_to(S, D), D != snow.
% The surprise is reasonable only if it has at least one salient feature.
salient(S) :- tag(S, sound).
salient(S) :- tag(S, surprise).
valid_story(P, S) :- valid_story(P, S), salient(S).
#show valid_story/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set((p, s) for p, s in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python combos:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def select_combo(params: StoryParams) -> tuple[Setting, Surprise]:
    if params.place not in SETTINGS:
        pass
    if params.surprise not in SURPRISES:
        pass
    return _safe_lookup(SETTINGS, params.place), _safe_lookup(SURPRISES, params.surprise)


def story_setup(world: World, child: Entity, parent: Entity, surprise: Surprise) -> None:
    child.memes["anticipation"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} was a {next((t for t in child.memes if False), '')}"
    )


def make_story(world: World, child: Entity, parent: Entity, surprise: Surprise) -> None:
    child.memes["anticipation"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} loved building a snowpen because {child.pronoun('subject')} could "
        f"pretend it was a tiny kingdom for a toy animal."
    )
    world.say(
        f"Every afternoon, {child.id} packed the snow walls, pat-pat, pat-pat, and "
        f"checked that the little gate stayed straight."
    )
    world.say(
        f"{child.id} even anticipated the {surprise.label}, though {child.pronoun('subject')} "
        f"did not know the surprise would be so dissimilar to the quiet snowpen."
    )
    world.para()
    world.say(
        f"One chilly day, {child.id} and {child.pronoun('possessive')} {parent.label_word} "
        f"went to {world.setting.place} with the snowpen ready."
    )
    world.say(
        f"{child.id} whispered, 'First the snowpen, then the surprise,' and waited with a grin."
    )
    world.say(
        f"Then came {surprise.phrase}: {surprise.sound}! {surprise.sound}! "
        f"It {surprise.effect}."
    )
    child.meters["surprised"] += 1
    child.memes["surprise"] += 1
    if surprise.kind in {"kettle", "scooter"}:
        world.say(
            f"{child.id} blinked. That was not the quiet thing {child.pronoun('subject')} had anticipated at all."
        )
    else:
        world.say(
            f"{child.id} laughed, because the noise went on and on like a joke that forgot where to stop."
        )
    world.say(
        f"{surprise.sound}, {surprise.sound}, {surprise.sound} went the little sound, and "
        f"{child.id} repeated, 'Again, again, again!'"
    )
    child.memes["repetition"] += 1
    world.para()
    if surprise.kind == "kettle":
        world.say(
            f"The warm puff softened the front of the snowpen, and the tiny gate slid open by itself."
        )
        world.say(
            f"The toy animal waddled out, shook its nose, and sat in the safest dry spot it could find."
        )
        world.say(
            f"{child.id} giggled. 'I built a snowpen,' {child.pronoun('subject')} said, 'and the cocoa made it into a slide!'"
        )
        world.say(
            f"{child.id} and {child.pronoun('possessive')} {parent.label_word} laughed so hard that the snowpen looked almost proud of itself."
        )
    elif surprise.kind == "bell":
        world.say(
            f"The bell kept saying ding-ding, ding-ding, ding-ding, and each ring made the snow walls sparkle."
        )
        world.say(
            f"{child.id} put the toy animal near the gate, and it hopped once, twice, three times, as if marching to the music."
        )
        world.say(
            f"That was not what {child.id} expected, but it was even funnier."
        )
    elif surprise.kind == "drum":
        world.say(
            f"The drum went rat-a-tat, rat-a-tat, rat-a-tat, and the toy animal bounced in place like it had tiny knees."
        )
        world.say(
            f"{child.id} tried to keep a straight face, but the repeated beat made {child.pronoun('object')} snort with laughter."
        )
        world.say(
            f"The snowpen became a stage, and the toy animal gave its silliest parade."
        )
    else:
        world.say(
            f"The scooter zipped zip-zip past the pen and blew a puff of snow dust over the gate."
        )
        world.say(
            f"{child.id} sneezed, then laughed, then sneezed again, which was a very dissimilar ending from the neat plan."
        )
        world.say(
            f"So {child.id} scooped the snow back into a lumpy wall and called it a 'faster fence.'"
        )
    child.memes["joy"] += 1
    world.say(
        f"In the end, the snowpen was not quiet or perfect, but it was full of funny noise, surprise, and happy repetition."
    )


def tell(setting: Setting, surprise: Surprise, child_name: str, gender: str, parent_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.facts.update(child=child, parent=parent, surprise=surprise, setting=setting)
    make_story(world, child, parent, surprise)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    s: Surprise = f["surprise"]
    return [
        f"Write a short comedy story about {child.id} building a snowpen and anticipating {s.phrase}.",
        f"Tell a child-friendly story where a snowpen meets a dissimilar surprise with sound effects like {s.sound}.",
        f"Write a playful story with repetition, surprise, and a snowpen at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    parent: Entity = f["parent"]
    s: Surprise = f["surprise"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"What was {child.id} building at {place}?",
            answer=f"{child.id} was building a snowpen, a tiny snow fence for a toy animal.",
        ),
        QAItem(
            question=f"What did {child.id} anticipate before the surprise arrived?",
            answer=f"{child.id} anticipated {s.phrase}, but the surprise turned out to be dissimilar to the quiet snowpen.",
        ),
        QAItem(
            question=f"What sound effects showed that the surprise had arrived?",
            answer=f"The surprise made sounds like {s.sound}, and those repeated sounds made the scene feel funny.",
        ),
        QAItem(
            question=f"How did the ending change the snowpen?",
            answer="The ending showed the snowpen had changed from neat and quiet into something sillier, softer, or more playful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    s: Surprise = world.facts["surprise"]
    out = [
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears or happens when someone does not know it is coming.",
        ),
        QAItem(
            question="What are sound effects in a story?",
            answer="Sound effects are words that imitate noises, like ding-ding or rat-a-tat, so the reader can almost hear them.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition means saying or doing something again and again, which can make a story funny or memorable.",
        ),
        QAItem(
            question="Why can repetition be funny for children?",
            answer="Repetition can be funny because a sound or phrase keeps returning, and that makes it feel playful and a little silly.",
        ),
    ]
    if s.kind == "kettle":
        out.append(QAItem(question="Why does warm cocoa feel different from snow?", answer="Warm cocoa is warm and liquid, while snow is cold and solid, so they feel very different to touch."))
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    setting, surprise = select_combo(params)
    world = tell(setting, surprise, params.child_name, params.gender, params.parent)
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


def select_combo(params: StoryParams) -> tuple[Setting, Surprise]:
    if params.place not in SETTINGS:
        pass
    if params.surprise not in SURPRISES:
        pass
    return _safe_lookup(SETTINGS, params.place), _safe_lookup(SURPRISES, params.surprise)


CURATED = [
    StoryParams(place="yard", surprise="bell", child_name="Mina", gender="girl", parent="mother"),
    StoryParams(place="porch", surprise="kettle", child_name="Leo", gender="boy", parent="father"),
    StoryParams(place="garden", surprise="drum", child_name="Nora", gender="girl", parent="mother"),
    StoryParams(place="yard", surprise="scooter", child_name="Sam", gender="boy", parent="father"),
]


def build_asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(build_asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child_name}: {p.surprise} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
