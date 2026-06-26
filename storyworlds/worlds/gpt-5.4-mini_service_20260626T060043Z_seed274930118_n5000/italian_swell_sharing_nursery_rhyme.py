#!/usr/bin/env python3
"""
storyworlds/worlds/italian_swell_sharing_nursery_rhyme.py
==========================================================

A tiny storyworld about sharing an Italian treat in a nursery-rhyme style.

Seed idea:
- A little child has a swell Italian snack.
- Friends want to share.
- One greedy moment causes worry.
- A fair sharing plan turns the day sweet again.

The simulation models:
- physical meters: slice count, crumbs, fullness, sticky mess
- emotional memes: joy, worry, greed, kindness, calm

The generated stories stay small, concrete, child-facing, and state-driven.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    friend: object | None = None
    platter: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

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
class Treat:
    id: str
    label: str
    phrase: str
    pieces: int
    messy: bool
    soil: str
    keyword: str
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
class SharingGist:
    id: str
    phrase: str
    helps: str
    GIST: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    for eater in list(world.entities.values()):
        if eater.meter("sticky") < THRESHOLD:
            continue
        sig = ("sticky", eater.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        eater.memes["worry"] = eater.memes.get("worry", 0.0) + 1
        out.append(f"{eater.id} got sticky fingers and began to worry.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    platter = world.entities.get("treat")
    if not platter:
        return out
    if platter.meter("pieces") >= 2 and platter.memes.get("shared", 0.0) < THRESHOLD:
        sig = ("share",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        platter.memes["shared"] = 1.0
        out.append("The sweet thing could still be shared.")
    return out


CAUSAL_RULES = [
    _r_sticky,
    _r_share,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTING = Setting(place="the little kitchen", affords={"share"})
TREATS = {
    "pizza": Treat(
        id="pizza",
        label="pizza",
        phrase="a swell Italian pizza",
        pieces=4,
        messy=True,
        soil="greasy",
        keyword="italian",
    ),
    "bread": Treat(
        id="bread",
        label="bread",
        phrase="warm Italian bread",
        pieces=6,
        messy=False,
        soil="crumbly",
        keyword="italian",
    ),
    "gelato": Treat(
        id="gelato",
        label="gelato",
        phrase="swell Italian gelato",
        pieces=3,
        messy=True,
        soil="melty",
        keyword="swell",
    ),
}

GIST = SharingGist(
    id="sharing",
    phrase="sharing makes the table feel fair",
    helps="there is enough for each friend",
)

NAMES = ["Mia", "Luca", "Nina", "Marco", "Rosa", "Leo", "Gina", "Tino"]
FRIEND_NAMES = ["Pip", "Mina", "Noah", "Lia"]
TRAITS = ["gentle", "cheery", "tiny", "bright", "peppy"]


@dataclass
class StoryParams:
    place: str
    treat: str
    child: str
    friend: str
    trait: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Italian sharing nursery-rhyme storyworld.")
    ap.add_argument("--place", choices=[SETTING.place], default=None)
    ap.add_argument("--treat", choices=sorted(TREATS), default=None)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--trait")
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


def valid_combos() -> list[tuple[str, str]]:
    return [(SETTING.place, tid) for tid, t in TREATS.items() if t.pieces >= 3]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "treat", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "treat", None) is None or c[1] == getattr(args, "treat", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, treat = rng.choice(list(combos))
    return StoryParams(
        place=place,
        treat=treat,
        child=getattr(args, "name", None) or rng.choice(NAMES),
        friend=getattr(args, "friend", None) or rng.choice(FRIEND_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def choose_treat(params: StoryParams) -> Treat:
    return _safe_lookup(TREATS, params.treat)


def tell(params: StoryParams) -> World:
    setting = SETTING
    treat = choose_treat(params)
    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type="girl" if params.child in {"Mia", "Nina", "Rosa", "Gina"} else "boy"))
    friend = world.add(Entity(id=params.friend, kind="character", type="girl" if params.friend in {"Lia", "Mina"} else "boy"))
    platter = world.add(Entity(
        id="treat",
        type=treat.id,
        label=treat.label,
        phrase=treat.phrase,
        plural=False,
        meters={"pieces": float(treat.pieces), "crumbs": 0.0, "sticky": 0.0},
        memes={"shared": 0.0},
    ))
    child.memes["joy"] = 1.0
    friend.memes["want"] = 1.0

    world.say(f"{child.id} had a {treat.phrase} in {setting.place}.")
    world.say(f"It looked so {params.trait} and neat, with a golden smell and a warm little beat.")
    world.say(f"{friend.id} came by and smiled in sight, for {GIST.phrase} felt very right.")
    world.para()

    world.say(f"{friend.id} said, \"May I have some too?\" and {child.id} said, \"Yes, I can share with you.\"")
    platter.meters["pieces"] -= 1
    child.memes["kindness"] = child.memes.get("kindness", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    if treat.messy:
        child.meters["sticky"] += 1
        platter.meters["crumbs"] += 1
    propagate(world)

    world.para()
    if treat.messy:
        world.say(f"One bite was a bit too fast, and {child.id} got {treat.soil} fingers by chance.")
        world.say(f"{child.id} frowned a little, then heard a soft little tune: sharing could be done with care.")
    else:
        world.say(f"The bites were tidy and mild, and {child.id} and {friend.id} laughed like a nursery child.")

    world.say(f"So they split the rest in twos and threes, like counting stones beneath the trees.")
    platter.meters["pieces"] = 0.0
    child.memes["calm"] = child.memes.get("calm", 0.0) + 1
    friend.memes["calm"] = friend.memes.get("calm", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(f"In the end, each tummy felt full and bright, and the table felt fair as a song at night.")

    world.facts.update(child=child, friend=friend, treat=platter, params=params, treat_cfg=treat, shared=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme story about "{f["treat_cfg"].keyword}" and sharing in a little kitchen.',
        f"Tell a gentle story where {f['child'].id} shares a {f['treat_cfg'].phrase} with {f['friend'].id}.",
        f'Write a child-friendly rhyme about an Italian treat, a little worry, and a kind share.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, friend, treat = f["child"], f["friend"], f["treat_cfg"]
    return [
        QAItem(
            question=f"What did {child.id} have in the little kitchen?",
            answer=f"{child.id} had {treat.phrase} in the little kitchen.",
        ),
        QAItem(
            question=f"Who asked {child.id} to share?",
            answer=f"{friend.id} asked {child.id} to share, and {child.id} said yes.",
        ),
        QAItem(
            question=f"Why did the story feel sweet at the end?",
            answer=f"It felt sweet because they shared the Italian treat fairly and everyone felt full and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people have some of what you have so everyone can enjoy it.",
        ),
        QAItem(
            question="What is Italian food?",
            answer="Italian food is food that comes from Italy, like pizza, bread, pasta, and gelato.",
        ),
        QAItem(
            question="Why can sticky fingers happen after eating?",
            answer="Sticky fingers can happen when food is soft, sweet, or melty, so a little of it stays on your hands.",
        ),
    ]
    return out


ASP_RULES = r"""
#show valid/2.
valid(P,T) :- place(P), treat(T), shares(T).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", SETTING.place)]
    for tid, t in TREATS.items():
        lines.append(asp.fact("treat", tid))
        if t.pieces >= 3:
            lines.append(asp.fact("shares", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
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
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/2."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in [StoryParams(place=SETTING.place, treat=t, child="Mia", friend="Pip", trait="gentle") for t in sorted(TREATS)]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.child}: {p.treat} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
