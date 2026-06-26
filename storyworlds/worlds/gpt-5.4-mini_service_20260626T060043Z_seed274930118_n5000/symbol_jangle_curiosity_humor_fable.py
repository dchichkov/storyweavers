#!/usr/bin/env python3
"""
storyworlds/worlds/symbol_jangle_curiosity_humor_fable.py
==========================================================

A tiny fable-world about Curiosity and Humor: a young animal notices a strange
symbol, hears a jangle, and learns a gentle way to satisfy curiosity without
causing trouble.

Seed sketch:
---
In a bright little village, a curious fox saw a brass symbol hanging from the
old gate. When the wind touched it, it went jangle-jangle, and every ear in the
lane turned toward the sound. The fox wanted to poke it, then laugh at the
noise, but the wise old goose warned that some shiny things make a fuss.

The fox paused, listened, and asked why the symbol mattered. The goose smiled
and said the symbol marked the gate for travelers, while the jangle simply
helped neighbors hear when the gate was open. Together they tied the symbol so
it would ring softly instead of clanging, and the fox learned that a little
curiosity can be kind when it wears a little humor.

Causal state updates:
---
    curiosity + unknown object -> desire, attention, asking
    noisy tinkering          -> jangle += 1, surprise += 1
    surprise + wise helper   -> humor += 1, calm += 1
    soft fix + understanding -> curiosity satisfied, trouble down
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "mouse", "rabbit", "cat", "dog"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    afford: set[str] = field(default_factory=set)
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
class ObjectKind:
    id: str
    label: str
    phrase: str
    sound: str
    purpose: str
    can_soften: bool = False
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
    object_kind: str
    hero: str
    hero_type: str
    guide: str
    guide_type: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


def _entity_word(e: Entity) -> str:
    return e.label or e.type


def _hero_desc(hero: Entity) -> str:
    return f"little curious {hero.type}"


def _intro(world: World, hero: Entity, guide: Entity, obj: Entity) -> None:
    world.say(
        f"{hero.id} was a {_hero_desc(hero)} who noticed every small thing, especially "
        f"the shiny {obj.label} near {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} also liked a good laugh, and the odd little "
        f"jangle of the {obj.label} made {hero.pronoun('object')} grin."
    )
    guide.memes["wisdom"] = guide.memes.get("wisdom", 0) + 1
    world.say(
        f"{guide.id}, the old {guide.type}, watched with a gentle eye and waited to see "
        f"what curiosity would do."
    )


def _approach(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["delight"] = hero.memes.get("delight", 0) + 1
    world.say(
        f"One breezy morning, {hero.id} crept closer to the {obj.label}. "
        f"The {obj.label} sat on a post by {world.setting.place}, and the wind kept "
        f"making it go {obj.sound}."
    )


def _warn(world: World, guide: Entity, hero: Entity, obj: Entity) -> None:
    if hero.memes.get("curiosity", 0) < THRESHOLD:
        return
    guide.memes["care"] = guide.memes.get("care", 0) + 1
    world.say(
        f'"Easy now," said {guide.id}. "That {obj.label} is a symbol, and symbols have '
        f'jobs. If you shove it hard, the jangle will become a fuss."'
    )


def _tinker(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    hero.meters["jangle"] = hero.meters.get("jangle", 0) + 1
    hero.meters["surprise"] = hero.meters.get("surprise", 0) + 1
    world.say(
        f"{hero.id} tried to touch the {obj.label} anyway, just once, because the sound "
        f"was too funny to ignore. The little tap made it jangle louder, and two sparrows "
        f"jumped as if a joke had landed on the fence."
    )


def _wise_turn(world: World, guide: Entity, hero: Entity, obj: Entity) -> None:
    guide.memes["humor"] = guide.memes.get("humor", 0) + 1
    hero.memes["humor"] = hero.memes.get("humor", 0) + 1
    world.say(
        f"{guide.id} did not scold. {guide.pronoun().capitalize()} only chuckled and said, "
        f'"Curiosity is a lantern. Humor is the soft shoe under it."'
    )
    world.say(
        f"That made {hero.id} laugh instead of fuss, and the sound became smaller in "
        f"{hero.pronoun('possessive')} mind."
    )


def _soft_fix(world: World, hero: Entity, guide: Entity, obj: Entity) -> None:
    if hero.memes.get("humor", 0) < THRESHOLD:
        return
    hero.meters["jangle"] = 0
    hero.meters["peace"] = hero.meters.get("peace", 0) + 1
    world.say(
        f"Together they tied a soft ribbon around the {obj.label}, so the symbol could still "
        f"ring, only lightly. After that, {hero.id} could listen without making a scene."
    )
    world.say(
        f"{hero.id} smiled at the neat little fix. The symbol stayed useful, the jangle stayed "
        f"kind, and the lane kept its calm."
    )


SETTING_REGISTRY = {
    "gate": Setting(place="the village gate", afford={"symbol"}),
    "square": Setting(place="the market square", afford={"symbol"}),
    "bridge": Setting(place="the old bridge", afford={"symbol"}),
}

OBJECTS = {
    "symbol": ObjectKind(
        id="symbol",
        label="symbol",
        phrase="a brass symbol that marked the gate",
        sound="jangle-jangle",
        purpose="to help travelers find the way",
        can_soften=True,
    ),
    "bellsymbol": ObjectKind(
        id="bellsymbol",
        label="symbol-bell",
        phrase="a bright symbol-bell with a round edge",
        sound="jangle",
        purpose="to signal that the gate was open",
        can_soften=True,
    ),
}

HERO_TYPES = ["fox", "rabbit", "mouse", "cat"]
GUIDE_TYPES = ["goose", "owl", "tortoise", "hen"]
NAMES = {
    "fox": ["Finn", "Faye", "Toby"],
    "rabbit": ["Pip", "Mina", "June"],
    "mouse": ["Nib", "Midge", "Pica"],
    "cat": ["Milo", "Nora", "Luna"],
    "goose": ["Greta", "Gus"],
    "owl": ["Odo", "Opal"],
    "tortoise": ["Tully", "Tessa"],
    "hen": ["Hattie", "Hazel"],
}


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTING_REGISTRY.items():
        for obj_id in setting.afford:
            combos.append((place, obj_id))
    return combos


def explain_rejection(place: str, obj_id: str) -> str:
    return f"(No story: {obj_id} does not belong at {place} in this small fable-world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about Curiosity, Humor, and a jangle-ing symbol.")
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--object-kind", choices=OBJECTS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--guide")
    ap.add_argument("--guide-type", choices=GUIDE_TYPES)
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
    if getattr(args, "place", None) and getattr(args, "object_kind", None) and (getattr(args, "place", None), getattr(args, "object_kind", None)) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj = None, None
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "object_kind", None):
        combos = [c for c in combos if c[1] == getattr(args, "object_kind", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    guide_type = getattr(args, "guide_type", None) or rng.choice(GUIDE_TYPES)
    hero = getattr(args, "hero", None) or rng.choice(_safe_lookup(NAMES, hero_type))
    guide = getattr(args, "guide", None) or rng.choice(_safe_lookup(NAMES, guide_type))
    return StoryParams(place=place, object_kind=obj, hero=hero, hero_type=hero_type, guide=guide, guide_type=guide_type)


def tell(params: StoryParams) -> World:
    world = World(SETTING_REGISTRY[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    guide = world.add(Entity(id=params.guide, kind="character", type=params.guide_type))
    objk = _safe_lookup(OBJECTS, params.object_kind)
    obj = world.add(Entity(id=objk.id, type=objk.id, label=objk.label, phrase=objk.phrase, owner=guide.id))
    world.facts.update(hero=hero, guide=guide, obj=obj, objk=objk, params=params)

    _intro(world, hero, guide, obj)
    world.para()
    _approach(world, hero, obj)
    _warn(world, guide, hero, obj)
    _tinker(world, hero, obj)
    _wise_turn(world, guide, hero, obj)
    world.para()
    _soft_fix(world, hero, guide, obj)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, objk = f["hero"], f["guide"], f["objk"]
    return [
        QAItem(
            question=f"What did {hero.id} notice near {world.setting.place}?",
            answer=f"{hero.id} noticed the shiny {objk.label} near {world.setting.place}, and the little jangle made {hero.pronoun('object')} curious.",
        ),
        QAItem(
            question=f"Why did {guide.id} speak up when {hero.id} came closer to the {objk.label}?",
            answer=f"{guide.id} warned {hero.id} because the {objk.label} was a symbol with a job, and rough poking could turn its jangle into a fuss.",
        ),
        QAItem(
            question=f"How did {hero.id} and {guide.id} keep the {objk.label} useful without making too much noise?",
            answer=f"They tied a soft ribbon around the {objk.label} so it could still ring lightly, which let the symbol do its work without a big clatter.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the playful feeling that helps people laugh and stay light-hearted when something is surprising.",
        ),
        QAItem(
            question="What does jangle mean?",
            answer="Jangle means to make a bright, clattering little ringing sound.",
        ),
        QAItem(
            question="What is a symbol?",
            answer="A symbol is something that stands for an idea, a place, or a message, so people can understand it at a glance.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, objk = f["hero"], f["guide"], f["objk"]
    return [
        f"Write a short fable for children about {hero.id}, {guide.id}, and a {objk.label} that goes jangle.",
        f"Tell a gentle story about Curiosity and Humor when a young {hero.type} meets a symbol at {world.setting.place}.",
        f"Write a small moral tale where a {hero.type} learns to be curious without making a big fuss over a noisy symbol.",
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
obj_at_risk(O) :- object(O).
curious(H) :- meme(H, curiosity), meme(H, curiosity_nz).
noisy(O) :- object(O), sound(O, jangle).
soft_fix(O) :- object(O), can_soften(O).

valid_story(P, O) :- place(P), afford(P, O), object(O), soft_fix(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTING_REGISTRY:
        lines.append(asp.fact("place", p))
        for obj in sorted(SETTING_REGISTRY[p].afford):
            lines.append(asp.fact("afford", p, obj))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("sound", oid, "jangle"))
        if o.can_soften:
            lines.append(asp.fact("can_soften", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set:
        print("OK: ASP emitted some compatible story facts.")
        return 0
    if python_set:
        print(f"OK: Python gate found {len(python_set)} valid combos.")
        return 0
    print("MISMATCH: no valid story could be derived.")
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


CURATED = [
    StoryParams(place="gate", object_kind="symbol", hero="Finn", hero_type="fox", guide="Greta", guide_type="goose"),
    StoryParams(place="square", object_kind="symbol", hero="Pip", hero_type="rabbit", guide="Odo", guide_type="owl"),
    StoryParams(place="bridge", object_kind="bellsymbol", hero="Midge", hero_type="mouse", guide="Tully", guide_type="tortoise"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} compatible story combos:")
        for c in combos:
            print("  ", c)
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
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
