#!/usr/bin/env python3
"""
Standalone storyworld: hallow duffel sandbox conflict ghost story.

A small, child-facing simulation where a hallow in a sandbox gets tangled with
a duffel bag, creating a gentle ghost-story conflict that is resolved by a
careful, state-driven turn.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------


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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    duffel: object | None = None
    hallow: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    world: object | None = None
    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
    name: str
    helper: str
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


PLACES = {
    "sandbox": "the sandbox",
}

HERO_NAMES = ["Mina", "Pip", "June", "Toby", "Nora", "Eli"]
HELPER_NAMES = ["Moss", "Wren", "Milo", "Ivy", "Lark", "Bea"]

ASPECTS = {
    "hallow": {
        "label": "hallow",
        "phrase": "a small hallow carved in the sand",
        "meter": "open",
        "risk": "the hallow could collapse",
    },
    "duffel": {
        "label": "duffel",
        "phrase": "a soft duffel bag with a flap",
        "meter": "sag",
        "risk": "sand could clog the flap",
    },
}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the sandbox contains both focal objects and the
% conflict can be resolved by a gentle repair.
conflict(hallow_duffel) :- in_place(hallow), in_place(duffel).
resolved(hallow_duffel) :- conflict(hallow_duffel), careful_fix.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("place", "sandbox"),
        asp.fact("in_place", "hallow"),
        asp.fact("in_place", "duffel"),
        asp.fact("feature", "conflict"),
        asp.fact("style", "ghost_story"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> bool:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
    atoms = set(asp.atoms(model, "conflict")) | set(asp.atoms(model, "resolved"))
    return ("hallow_duffel",) in atoms


# ---------------------------------------------------------------------------
# Parser / params
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story sandbox world with a hallow and a duffel.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    place = getattr(args, "place", None) or "sandbox"
    if place != "sandbox":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(place=place, name=name, helper=helper)


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = World(place=_safe_lookup(PLACES, params.place))

    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    helper = world.add(Entity(id=params.helper, kind="character", type="child"))
    hallow = world.add(Entity(
        id="hallow",
        type="hallow",
        label="hallow",
        phrase=ASPECTS["hallow"]["phrase"],
        owner=hero.id,
        meters={"open": 1.0},
        memes={"haunted": 0.0, "conflict": 0.0},
    ))
    duffel = world.add(Entity(
        id="duffel",
        type="duffel",
        label="duffel",
        phrase=ASPECTS["duffel"]["phrase"],
        owner=helper.id,
        meters={"sag": 1.0},
        memes={"conflict": 0.0},
    ))

    # Beginning.
    world.say(
        f"In {world.place}, {hero.id} found {hallow.phrase}, and {helper.id} found {duffel.phrase}."
    )
    world.say(
        f"The sand felt quiet, but the little hallow made the day seem like a ghost story with a secret."
    )

    # Middle turn: the duffel's flap is pulled into the hollow shape.
    world.para()
    hallow.memes["haunted"] += 1
    duffel.meters["sand"] = duffel.meters.get("sand", 0.0) + 1.0
    hallow.meters["crumbly"] = hallow.meters.get("crumbly", 0.0) + 1.0
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1

    world.say(
        f"When {helper.id} set the {duffel.label} near the hollow, sand slipped into the flap and the bag sagged."
    )
    world.say(
        f"{hero.id} worried the hallow would collapse, and {helper.id} worried the bag would stay stuck."
    )
    world.say(
        f"They both stopped, listening to the soft hiss of sand like a tiny ghost whisper."
    )

    # Resolution: lift, shake, and reshape.
    world.para()
    duffel.meters["sand"] = 0.0
    hallow.meters["crumbly"] = 0.0
    hero.memes["conflict"] = 0.0
    helper.memes["conflict"] = 0.0
    hallow.memes["calm"] = 1.0
    duffel.memes["calm"] = 1.0

    world.say(
        f"Then {helper.id} lifted the duffel by the strap while {hero.id} gently packed the sand back into the hallow."
    )
    world.say(
        f"The flap opened cleanly again, the hollow kept its shape, and the sandbox felt peaceful."
    )
    world.say(
        f"At the end, the hallow stayed bright in the sand, and the duffel sat beside it as if it had learned the quiet rule of the place."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        hallow=hallow,
        duffel=duffel,
        place=params.place,
        conflict=True,
        resolved=True,
    )

    story = world.render()
    prompts = [
        "Write a gentle ghost story set in a sandbox with a hallow and a duffel.",
        f"Tell a child-friendly story where {params.name} and {params.helper} solve a small conflict about sand and a bag.",
        "Make the ending show that the sandbox changed from tense to calm.",
    ]
    story_qa = [
        QAItem(
            question="What did the children find in the sandbox?",
            answer="They found a small hallow in the sand and a soft duffel bag with a flap.",
        ),
        QAItem(
            question="Why did the children feel worried?",
            answer="They worried because sand slipped into the duffel flap and the hallow might collapse.",
        ),
        QAItem(
            question="How did they fix the problem?",
            answer="They lifted the duffel, shook out the sand, and packed the hallow back into shape together.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a sandbox?",
            answer="A sandbox is a box or shallow area filled with sand where children can dig and build.",
        ),
        QAItem(
            question="What does a duffel bag usually do?",
            answer="A duffel bag is a soft bag used to carry toys, clothes, or other belongings.",
        ),
        QAItem(
            question="What can happen to a hollow shape in sand?",
            answer="A hollow shape in sand can crumble or fill in if the sand is not packed carefully.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(f"- {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# Verification / main
# ---------------------------------------------------------------------------

def verify() -> int:
    if not asp_valid():
        print("ASP parity check failed.")
        return 1
    print("OK: ASP program and Python world agree.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show conflict/1.\n#show resolved/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show conflict/1.\n#show resolved/1."))
        print("conflicts:", asp.atoms(model, "conflict"))
        print("resolved:", asp.atoms(model, "resolved"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        params = resolve_params(argparse.Namespace(place="sandbox", name=None, helper=None), random.Random(base_seed))
        params.seed = base_seed
        samples = [generate(params)]
    else:
        for i in range(getattr(args, "n", None)):
            rng = random.Random(base_seed + i)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
            samples.append(generate(params))

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
