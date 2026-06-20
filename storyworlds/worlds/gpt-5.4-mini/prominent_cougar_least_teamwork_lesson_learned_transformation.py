#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/prominent_cougar_least_teamwork_lesson_learned_transformation.py
=================================================================================================

A standalone fairy-tale story world about a proud, prominent cougar, the least
likely helpers, a teamwork fix, and a transformation that teaches a lesson.

The seed words are woven into the simulated premise:
- prominent
- cougar
- least

The world models a small magical domain where a troublemaker or lonely leader
faces a problem that cannot be solved alone, learns from help, and changes by
the end.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "witch"}
        male = {"boy", "father", "dad", "man", "king", "cougar"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    scenic: str
    obstacle: str
    magic: str
    danger: str
    transforms: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Helper:
    id: str
    label: str
    size: str
    gift: str
    teamwork: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["worry"] < THRESHOLD:
            continue
        sig = ("worry", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("glade").meters["tension"] += 1
        out.append("")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    cougar = world.get("cougar")
    if cougar.meters["softened"] >= THRESHOLD and cougar.memes["humility"] >= THRESHOLD:
        sig = ("transform", cougar.id)
        if sig not in world.fired:
            world.fired.add(sig)
            cougar.attrs["transformed"] = True
            cougar.memes["warmth"] += 1
            world.get("glade").meters["glow"] += 1
            out.append("")
    return out


CAUSAL_RULES = [Rule("worry", "social", _r_worry), Rule("transform", "magic", _r_transformation)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def needs_teamwork(place: Place, helper: Helper) -> bool:
    return place.transforms and helper.size == "small"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def outcome_of(params: "StoryParams") -> str:
    return "transformed" if params.response in {"bridge", "song"} else "softened"


def tell(place: Place, helper: Helper, response: Response, cougar_name: str, companion_name: str) -> World:
    world = World()
    cougar = world.add(Entity("cougar", kind="character", type="cougar", role="protagonist"))
    companion = world.add(Entity("companion", kind="character", type="mouse", role="helper"))
    glade = world.add(Entity("glade", type="place", label=place.label))
    cougar.attrs["name"] = cougar_name
    companion.attrs["name"] = companion_name
    cougar.memes["pride"] = 2.0
    cougar.memes["least"] = 1.0
    companion.memes["help"] = 1.0

    world.say(
        f"In a fairy-tale glade, a prominent cougar lived beside {place.label}. "
        f"{cougar_name} liked to sit on the tallest stone and watch the wind move over the leaves."
    )
    world.say(
        f"But the path to the far side of the glade was blocked by {place.obstacle}, "
        f"and the magic there was the least bit steady."
    )

    world.para()
    world.say(
        f"A tiny {helper.label} named {companion_name} came along and offered {helper.gift}. "
        f"Together, they could make a way across."
    )

    world.para()
    cougar.memes["worry"] += 1
    world.say(
        f'"I can do it alone," {cougar_name} said at first, but {companion_name} showed '
        f"how {helper.teamwork}."
    )
    world.say(
        f"They worked side by side: one held the rope, one tied the knots, and one steady paw "
        f"kept the board from slipping."
    )

    world.para()
    cougar.meters["softened"] += 1
    cougar.memes["humility"] += 1
    world.say(
        f"At last, the bridge held. The cougar crossed, then bowed to the little helper and said "
        f"that the least helper can make the biggest difference."
    )
    world.say(
        f"The glade answered with a soft shimmer, and {cougar_name} changed too: "
        f"less proud, more kind, as if the night had turned to gold."
    )

    propagate(world, narrate=False)
    world.facts.update(place=place, helper=helper, response=response,
                       cougar_name=cougar_name, companion_name=companion_name,
                       transformed=True)
    return world


PLACES = {
    "bridge": Place("bridge", "a narrow wooden bridge", "moonlit boards", "a rushing stream", "a little crossing spell", "the water below", True),
    "hill": Place("hill", "a steep hill path", "silver grass", "a wall of thorny brambles", "a patient climbing spell", "the rocks below", True),
    "gate": Place("gate", "a garden gate", "roses and ivy", "a heavy fallen branch", "a shared lifting spell", "the path beyond", True),
}

HELPERS = {
    "mouse": Helper("mouse", "mouse", "small", "a strip of ribbon", "wove a little bridge from reeds", {"small", "least"}),
    "sparrow": Helper("sparrow", "sparrow", "small", "a bright feather", "tied the knot from above", {"small", "least"}),
    "rabbit": Helper("rabbit", "rabbit", "small", "a basket of twine", "held the boards while the rope was tied", {"small", "least"}),
}

RESPONSES = {
    "bridge": Response("bridge", 3, 3, "built a little bridge with reed ropes", "tried to cross, but the way was too broken", "built a little bridge"),
    "song": Response("song", 3, 2, "called for a teamwork song that steadied their paws", "called for a song, but the tune was too weak", "called for a teamwork song"),
    "lift": Response("lift", 2, 2, "lifted the branch together, one push at a time", "lifted the branch, but it slipped back down", "lifted the branch together"),
}

COUGAR_NAMES = ["Cora", "Milo", "Clara", "Bram", "Nella", "Rowan"]
COMPANION_NAMES = ["Pip", "Mira", "Tess", "Finn", "Lulu", "Bess"]


@dataclass
@dataclass
class StoryParams:
    place: str
    helper: str
    response: str
    cougar_name: str
    companion_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for h in HELPERS:
            for r in RESPONSES:
                if needs_teamwork(PLACES[p], HELPERS[h]):
                    combos.append((p, h, r))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale story world with teamwork and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.helper is None or c[1] == args.helper)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, helper, response = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        helper=helper,
        response=response,
        cougar_name=args.name or rng.choice(COUGAR_NAMES),
        companion_name=args.companion or rng.choice(COMPANION_NAMES),
    )


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a fairy-tale story about a prominent cougar who learns the least likely helper can still save the day.",
        "Tell a story where teamwork helps a cougar overcome a blocked path and learn a lesson.",
        "Write a gentle transformation tale with a prominent cougar, a tiny helper, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem("Who is the story about?", f"It is about {f['cougar_name']}, a prominent cougar, and {f['companion_name']}, the tiny helper who came along. The story follows how they worked together and changed the glade."),
        QAItem("What problem did they face?", f"They had to get past {f['place'].obstacle}. It could not be solved alone, so teamwork was needed."),
        QAItem("What did the cougar learn?", f"The cougar learned that the least helper can still matter a lot. After working together, {f['cougar_name']} became kinder and less proud."),
        QAItem("How did the story end?", f"The path was cleared, the glade glowed softly, and the cougar was transformed by the lesson learned. The ending proves that teamwork changed both the journey and the cougar's heart."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is teamwork?", "Teamwork means people help each other and do a job together. When they share the work, hard things can become easier."),
        QAItem("What is a lesson learned?", "A lesson learned is something new a character understands after a choice or an event. Fairy tales often end with a lesson like that."),
        QAItem("What is a transformation?", "A transformation is a big change. In a fairy tale, a character may become braver, kinder, or wiser."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], HELPERS[params.helper], RESPONSES[params.response], params.cougar_name, params.companion_name)
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
        print("--- world model state ---")
        for e in sample.list(world.entities.values()):
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: meters={meters} memes={memes} attrs={e.attrs}")
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(P,H,R) :- place(P), helper(H), response(R), teamwork_needed(P,H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    for p, place in PLACES.items():
        if place.transforms:
            lines.append(asp.fact("teamwork_needed_place", p))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid combos.")
    try:
        generate(resolve_params(argparse.Namespace(place=None, helper=None, response=None, name=None, companion=None), random.Random(7)))
        print("OK: generate smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


CURATED = [
    StoryParams("bridge", "mouse", "bridge", "Cora", "Pip"),
    StoryParams("hill", "sparrow", "song", "Milo", "Mira"),
    StoryParams("gate", "rabbit", "lift", "Clara", "Tess"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
