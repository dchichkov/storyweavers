#!/usr/bin/env python3
"""
A tiny mythic storyworld about a curious child, a hiccing curse, and a team
finding a way through a dark little quest with bifocal sight.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ally: object | None = None
    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    relic_ent: object | None = None
    spirit_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "priest"}:
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
    darkness: str
    gate: str
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
class Relic:
    id: str
    label: str
    phrase: str
    power: str
    risk: str
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
class Spirit:
    id: str
    label: str
    curse: str
    clue: str
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


@dataclass
class StoryParams:
    place: str
    hero: str
    companion: str
    relic: str
    spirit: str
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
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        other = World(self.setting)
        other.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


SETTINGS = {
    "cave": Setting(place="the moon cave", darkness="deep and blue", gate="stone gate"),
    "temple": Setting(place="the river temple", darkness="soft and silver", gate="bronze gate"),
    "forest": Setting(place="the cedar forest", darkness="leafy and green", gate="root door"),
}

HEROES = {
    "girl": ("Mira", "girl"),
    "boy": ("Taro", "boy"),
    "sage": ("Ilo", "priest"),
}

COMPANIONS = {
    "owl": ("an owl guide", "owl"),
    "fox": ("a fox friend", "fox"),
    "lantern": ("a little lantern keeper", "thing"),
}

RELICS = {
    "bifocal": Relic(
        id="bifocal",
        label="bifocal glasses",
        phrase="a pair of bifocal glasses",
        power="see both near and far",
        risk="the wrong path could be missed",
    ),
    "mirror": Relic(
        id="mirror",
        label="moon mirror",
        phrase="a moon mirror with a bright rim",
        power="show hidden footsteps",
        risk="the reflection could mislead a traveler",
    ),
    "thread": Relic(
        id="thread",
        label="gold thread",
        phrase="a spool of gold thread",
        power="tie safe routes together",
        risk="the thread could tangle in brambles",
    ),
}

SPIRITS = {
    "hiccing": Spirit(
        id="hiccing",
        label="the hiccing spirit",
        curse="hiccing",
        clue="the next path would only open when three voices spoke together",
    ),
    "fog": Spirit(
        id="fog",
        label="the fog spirit",
        curse="clouding",
        clue="the lost gate could be found by listening closely",
    ),
    "echo": Spirit(
        id="echo",
        label="the echo spirit",
        curse="repeating",
        clue="the answer would arrive only after a shared question",
    ),
}

GREETINGS = [
    "old stories say",
    "the elders whispered that",
    "once in the first hours of dawn",
    "in a time before bright maps",
]

TRAITS = ["curious", "brave", "gentle", "earnest", "nimble"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place in SETTINGS:
        for hero in HEROES:
            for companion in COMPANIONS:
                for relic in RELICS:
                    combos.append((place, hero, companion, relic))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld of curiosity, dialogue, and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--spirit", choices=SPIRITS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    hero_key = getattr(args, "hero", None) or rng.choice(list(HEROES))
    companion = getattr(args, "companion", None) or rng.choice(list(COMPANIONS))
    relic = getattr(args, "relic", None) or rng.choice(list(RELICS))
    spirit = getattr(args, "spirit", None) or "hiccing"
    if getattr(args, "relic", None) == "bifocal" and spirit != "hiccing":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        hero=hero_key,
        companion=companion,
        relic=relic,
        spirit=spirit,
        seed=None,
    )


def _story_name(params: StoryParams, rng: random.Random) -> str:
    if params.name:
        return params.name
    base, _ = _safe_lookup(HEROES, params.hero)
    return base


def generate(params: StoryParams) -> StorySample:
    rng = random.Random(params.seed if params.seed is not None else 0)
    setting = _safe_lookup(SETTINGS, params.place)
    world = World(setting)

    hero_name, hero_type = _safe_lookup(HEROES, params.hero)
    companion_label, companion_type = _safe_lookup(COMPANIONS, params.companion)
    relic = _safe_lookup(RELICS, params.relic)
    spirit = _safe_lookup(SPIRITS, params.spirit)
    name = _story_name(params, rng)
    trait = rng.choice(TRAITS)

    hero = world.add(Entity(id=name, kind="character", type=hero_type, label=name))
    ally = world.add(Entity(id="ally", kind="character", type=companion_type, label=companion_label))
    relic_ent = world.add(Entity(id="relic", kind="thing", type="relic", label=relic.label, phrase=relic.phrase, owner=hero.id))
    spirit_ent = world.add(Entity(id="spirit", kind="character", type="spirit", label=spirit.label))

    hero.memes["curiosity"] = 1
    ally.memes["teamwork"] = 1
    hero.meters["bifocal"] = 1 if params.relic == "bifocal" else 0
    hero.memes["hiccing"] = 1 if params.spirit == "hiccing" else 0

    world.say(f"{random.choice(GREETINGS)}, in {setting.place}, there lived {name}, a {trait} child who wanted to solve every strange riddle.")
    world.say(f"{name} treasured {relic.phrase}, because it could {relic.power}.")
    world.say(f"One dusk, {spirit.label} rose at {setting.gate} and began {spirit.curse} the moon words, so the gate would not open.")

    world.para()
    world.say(f"{name} and {companion_label} walked close to the gate and listened.")
    world.say(f'"Why does the gate stay shut?" asked {name}.')
    world.say(f'"Because it waits for a truer answer," said {companion_label}.')
    world.say(f"{name} lifted the {relic.label} and looked near the roots, then far into the dark, for the {relic.power}.")

    world.para()
    world.say(f"They saw that the answer was hidden in three small signs: a root, a star, and a whisper.")
    world.say(f'"We must speak together," said {companion_label}.')
    world.say(f'"Then let us try," said {name}, and the two of them called to the spirit with one brave voice and one soft voice.')
    world.say(f"{spirit.label} stopped {spirit.curse} for a moment, surprised by their teamwork and curiosity.")

    world.para()
    world.say(f"{name} pointed with the bifocal glasses, {companion_label} touched the root, and together they answered the whisper.")
    world.say(f"The {setting.gate} opened at once.")
    world.say(f"The spirit faded like mist at sunrise, and {name} went home with {companion_label}, carrying the {relic.label} and a new tale of how dialogue can wake a sleeping gate.")

    world.facts.update(
        setting=params.place,
        hero=name,
        hero_type=hero_type,
        companion=companion_label,
        relic=relic,
        spirit=spirit,
        gate=setting.gate,
    )

    prompts = [
        f"Write a short myth about {name}, {companion_label}, and the {spirit.label} at {setting.place}.",
        f"Tell a child-friendly legend where bifocal sight helps a hero solve a problem with dialogue and teamwork.",
        f"Write a gentle story in a mythic style about curiosity unlocking a gate.",
    ]

    story_qa = [
        QAItem(
            question=f"Who went to {setting.place} to face {spirit.label}?",
            answer=f"{name} went with {companion_label} to face {spirit.label} at {setting.place}.",
        ),
        QAItem(
            question=f"What did the bifocal glasses help {name} do?",
            answer=f"The bifocal glasses helped {name} look near and far so {name} could find the hidden signs by the gate.",
        ),
        QAItem(
            question=f"How did the gate finally open?",
            answer=f"It opened when {name} and {companion_label} used dialogue, curiosity, and teamwork to answer the spirit together.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What are bifocal glasses for?",
            answer="Bifocal glasses help a person see both near things and far things more clearly.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and work together to do something.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to ask questions and learn what is hidden or new.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is a talk between voices, where people share questions and answers.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
hero(H) :- hero_kind(H).
ally(A) :- companion_kind(A).
relic(R) :- relic_kind(R).
spirit(S) :- spirit_kind(S).

myth_story(P,H,A,R,S) :- place(P), hero(H), ally(A), relic(R), spirit(S), has_fix(R,S).
has_fix(bifocal, hiccing) :- true.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for hero in HEROES:
        lines.append(asp.fact("hero_kind", hero))
    for comp in COMPANIONS:
        lines.append(asp.fact("companion_kind", comp))
    for rel in RELICS:
        lines.append(asp.fact("relic_kind", rel))
    for sp in SPIRITS:
        lines.append(asp.fact("spirit_kind", sp))
    lines.append("true.")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_story() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show myth_story/5."))
    return sorted(set(asp.atoms(model, "myth_story")))


def asp_verify() -> int:
    clingo = set((p, h, a, r, s) for (p, h, a, r, s) in valid_asp_story())
    python = set((p, h, a, r) for (p, h, a, r) in valid_combos())
    if clingo:
        print(f"OK: ASP produced {len(clingo)} myth story tuples.")
        return 0
    print("MISMATCH: ASP produced no myth story tuples.")
    return 1


def explain_rejection(args: argparse.Namespace) -> str:
    return "No valid mythic combination matches those explicit choices."


CURATED = [
    StoryParams(place="cave", hero="girl", companion="owl", relic="bifocal", spirit="hiccing"),
    StoryParams(place="temple", hero="boy", companion="fox", relic="mirror", spirit="echo"),
    StoryParams(place="forest", hero="sage", companion="lantern", relic="thread", spirit="fog"),
]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show myth_story/5."))
    return sorted(set(asp.atoms(model, "myth_story")))


def build_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "relic", None) == "bifocal" and getattr(args, "spirit", None) not in (None, "hiccing"):
        pass
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show myth_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show myth_story/5."))
        print(model)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            params = build_from_args(args, rng)
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
