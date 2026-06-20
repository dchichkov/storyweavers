#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/koala_twist_bedtime_story.py
=============================================================

A small bedtime storyworld about a child, a sleepy koala, and a twist in the
bedtime routine that turns into a calm, cozy resolution.

Premise:
- A child and a koala are getting ready for bed.
- A twist in the story is that a blanket or ribbon gets tangled, making sleep
  feel impossible for a moment.
- A gentle grown-up helps untwist the trouble.
- The ending proves what changed by returning the room to quiet, soft, safe
  bedtime comfort.

The world is intentionally tiny and classical: a few typed entities, physical
meters, emotional memes, forward-chained causal rules, a reasonableness gate,
and a state-driven renderer.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/koala_twist_bedtime_story.py
    python storyworlds/worlds/gpt-5.4-mini/koala_twist_bedtime_story.py --all
    python storyworlds/worlds/gpt-5.4-mini/koala_twist_bedtime_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4-mini/koala_twist_bedtime_story.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/koala_twist_bedtime_story.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Room:
    id: str
    name: str
    quiet: bool = False
    dim: bool = False
    cozy: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class StoryThing:
    id: str
    label: str
    phrase: str
    kind: str
    soft: bool = False
    tangled: bool = False
    helps_sleep: bool = False
    makes_twist: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        self.room = Room("room", "the bedroom")

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.room = copy.deepcopy(self.room)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_twist(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["twisted"] < THRESHOLD:
            continue
        sig = ("twist", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.room.meters["tension"] += 1
        for e in list(world.entities.values()):
            if e.kind == "character":
                e.memes["worry"] += 1
        out.append("__twist__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.room.meters["tension"] < THRESHOLD:
        return out
    sig = ("calm", world.room.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("twist", "social", _r_twist), Rule("calm", "social", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_ok(kid: Entity, koala: Entity, blanket: StoryThing, twisty: StoryThing) -> bool:
    return kid.kind == "character" and koala.type == "koala" and blanket.soft and twisty.makes_twist


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def choose_response() -> Response:
    return max(sensible_responses(), key=lambda r: r.sense)


def predict_tangle(world: World, blanket_id: str) -> bool:
    sim = world.copy()
    sim.get(blanket_id).meters["twisted"] += 1
    propagate(sim, narrate=False)
    return sim.room.meters["tension"] >= THRESHOLD


def setup(world: World, child: Entity, koala: Entity, setting: Room) -> None:
    child.memes["sleepy"] += 1
    koala.memes["sleepy"] += 1
    world.say(
        f"At bedtime, {child.id} and {koala.id} were in {setting.name}, where the lamp glowed softly and the pillow waited like a cloud."
    )
    world.say(
        f"{koala.id} was a sleepy koala who liked quiet corners, and {child.id} loved having a cuddly friend nearby."
    )


def twist(world: World, child: Entity, blanket: StoryThing, ribbon: StoryThing) -> None:
    child.memes["curiosity"] += 1
    blanket.meters["twisted"] += 1
    ribbon.meters["twisted"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{child.id} tugged the {blanket.label} to make a little nest, but the {ribbon.label} snagged and turned the blanket into a twisty knot."
    )


def worry(world: World, child: Entity, koala: Entity, blanket: StoryThing) -> None:
    if predict_tangle(world, blanket.id):
        child.memes["worry"] += 1
        koala.memes["worry"] += 1
        world.say(
            f"{child.id} frowned. The knot made the bed feel busy instead of cozy, and even {koala.id} stopped wiggling."
        )
        world.say(
            f'"This is too twisty," {child.id} whispered, hugging {koala.id}. "It will not feel sleepy like this."'
        )


def untwist(world: World, parent: Entity, blanket: StoryThing, ribbon: StoryThing) -> None:
    blanket.meters["twisted"] = 0.0
    ribbon.meters["twisted"] = 0.0
    world.room.meters["tension"] = 0.0
    for e in list(world.entities.values()):
        e.memes["worry"] = 0.0
    world.say(
        f"{parent.label_word.capitalize()} came in with a calm smile, loosened the knot, and helped the {blanket.label} fall smooth again."
    )


def settle(world: World, child: Entity, koala: Entity, blanket: StoryThing, nightlight: StoryThing, parent: Entity) -> None:
    child.memes["joy"] += 1
    koala.memes["joy"] += 1
    child.memes["sleepy"] += 1
    koala.memes["sleepy"] += 1
    world.say(
        f"Then {parent.label_word} tucked them in, switched on the soft {nightlight.label}, and placed the {blanket.label} just right."
    )
    world.say(
        f"{koala.id} curled into a round, fuzzy ball, {child.id} yawned a long yawn, and the room grew quiet as a dream."
    )
    world.say(
        f"With the twist gone, the bedtime story ended the way sleepy nights should: warm, still, and safe."
    )


def tell(params: "StoryParams") -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    koala = world.add(Entity(id="koala", kind="character", type="koala", role="friend"))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_gender, label="the parent", role="parent"))
    blanket = world.add(Entity(id="blanket", type="thing", label="blanket"))
    ribbon = world.add(Entity(id="ribbon", type="thing", label="ribbon"))
    nightlight = world.add(Entity(id="nightlight", type="thing", label="night-light"))

    child.memes["sleepy"] = 1.0
    koala.memes["sleepy"] = 1.0
    world.facts["blanket"] = blanket
    world.facts["ribbon"] = ribbon
    world.facts["nightlight"] = nightlight

    setup(world, child, koala, world.room)
    world.para()
    twist(world, child, blanket, ribbon)
    worry(world, child, koala, blanket)
    world.para()
    untwist(world, parent, blanket, ribbon)
    settle(world, child, koala, blanket, nightlight, parent)

    world.facts.update(
        child=child,
        koala=koala,
        parent=parent,
        outcome="calm",
        twisted_before=True,
        twisted_after=False,
    )
    return world


@dataclass
@dataclass
class StoryParams:
    child: str
    child_gender: str
    parent_gender: str
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


CHILDREN = [("Mia", "girl"), ("Leo", "boy"), ("Nina", "girl"), ("Theo", "boy")]
PARENTS = ["mother", "father"]


RESPONSES = {
    "untwist": Response(
        "untwist",
        3,
        3,
        "untwisted the blanket and smoothed it flat",
        "tried to untwist the blanket, but the knot stayed too tight",
        "helped untwist the blanket",
        tags={"calm", "bedtime"},
    ),
    "nightlight": Response(
        "nightlight",
        2,
        2,
        "switched on the night-light and made the room glow softly",
        "turned on the night-light, but the tangled blanket still felt wrong",
        "turned on the night-light",
        tags={"calm", "bedtime"},
    ),
}


def valid_combos() -> list[tuple[str, str]]:
    return [("bedroom", "koala")]


KNOWLEDGE = {
    "koala": [
        ("What is a koala?", "A koala is a furry tree-dwelling animal that rests a lot and likes quiet, sleepy moments."),
        ("What do koalas like to do?", "Koalas spend lots of time resting and clinging to branches, so they are often very calm and sleepy."),
    ],
    "nightlight": [
        ("What is a night-light?", "A night-light is a small lamp that gives a gentle glow in the dark without being bright or scary."),
    ],
    "blanket": [
        ("What is a blanket for?", "A blanket helps keep someone warm and cozy when it is time to rest."),
    ],
    "bedtime": [
        ("Why is bedtime important?", "Bedtime helps bodies rest so they can wake up with more energy in the morning."),
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime storyworld with a koala and a twist.")
    ap.add_argument("--child", choices=[n for n, _ in CHILDREN])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
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
    if args.gender is not None and args.child is None:
        pass
    child, gender = rng.choice(CHILDREN)
    if args.child:
        for n, g in CHILDREN:
            if n == args.child:
                child, gender = n, g
                break
    if args.gender and args.gender != gender:
        raise StoryError("That child name does not match the requested gender.")
    parent = args.parent or rng.choice(PARENTS)
    return StoryParams(child=child, child_gender=gender, parent_gender=parent)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a bedtime story for a small child about a koala, a twist, and a calm grown-up fix.",
        f"Tell a cozy story where {f['child'].id} and a koala face a twisty blanket at bedtime, then settle down safely.",
        "Write a gentle bedtime story that includes the word koala and ends with a warm, sleepy room.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, koala, parent = f["child"], f["koala"], f["parent"]
    return [
        ("Who is the story about?", f"It is about {child.id}, a sleepy koala, and {parent.label_word} helping at bedtime."),
        ("What went wrong at bedtime?", f"The blanket got twisty and tangled, so the bed stopped feeling calm and cozy."),
        ("How was the problem fixed?", f"{parent.label_word.capitalize()} loosened the knot, smoothed the blanket, and helped everyone settle down again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"koala", "nightlight", "blanket", "bedtime"}
    out: list[tuple[str, str]] = []
    for tag, qa in KNOWLEDGE.items():
        if tag in tags:
            out.extend(qa)
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  room: tension={world.room.meters.get('tension', 0.0)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("Mia", "girl", "mother"),
    StoryParams("Leo", "boy", "father"),
    StoryParams("Nina", "girl", "mother"),
]


def explain_rejection() -> str:
    return "(No story: this bedtime world needs a koala, a child, and a twisty blanket. The requested choices do not make a plausible bedtime turn.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("entity_kind", "koala"))
    lines.append(asp.fact("entity_kind", "blanket"))
    lines.append(asp.fact("entity_kind", "nightlight"))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(calm) :- sensible(untwist).
outcome(calm) :- sensible(nightlight).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1.\n#show outcome/1."))
    sens = sorted(r for (r,) in asp.atoms(model, "sensible"))
    if set(sens) != {r.id for r in sensible_responses()}:
        print("MISMATCH: ASP sensible responses differ from Python.")
        return 1
    print("OK: ASP twin matches Python gate.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        print("MISMATCH: story generation produced empty output.")
        return 1
    print("OK: story generation smoke test passed.")
    return 0


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    if args.show_asp:
        print(asp_program("", "#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(asp_sensible()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} and the koala ({p.parent_gender})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
