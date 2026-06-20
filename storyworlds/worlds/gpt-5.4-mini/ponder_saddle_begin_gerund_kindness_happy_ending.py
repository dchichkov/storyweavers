#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ponder_saddle_begin_gerund_kindness_happy_ending.py
===================================================================================

A small standalone storyworld: a child finds a shy ghost pony in a moonlit barn,
ponders how to help it, saddles it gently, and kindness turns a spooky scene into
a happy ending.

The world keeps a light simulation with physical meters and emotional memes.
The core tension is whether the child can calm the ghost pony enough to begin
moving again; if so, the pony "begin-gerund" beat becomes a safe, joyful ride.

Seed words woven into the domain:
- ponder
- saddle
- begin-gerund

Style note:
- Ghost-story atmosphere, but child-facing and kind.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
class Setting:
    id: str
    place: str
    mood: str
    sound: str
    darkness: str
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
class Saddle:
    id: str
    label: str
    phrase: str
    kind: str
    fit: str
    gentle: str
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
class Pony:
    id: str
    label: str
    phrase: str
    kind: str
    weight: str
    shy: bool = True
    glowing: bool = True
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

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


def _r_kindness(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    pony = world.entities.get("pony")
    if not child or not pony:
        return out
    if child.memes["kindness"] < THRESHOLD:
        return out
    sig = ("kindness",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pony.memes["trust"] += 1
    pony.memes["fear"] = max(0.0, pony.memes["fear"] - 0.5)
    out.append("__kindness__")
    return out


def _r_begingerund(world: World) -> list[str]:
    pony = world.entities.get("pony")
    if not pony:
        return []
    if pony.memes["trust"] < THRESHOLD or pony.meters["saddled"] < THRESHOLD:
        return []
    sig = ("begin",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    pony.meters["moving"] += 1
    pony.memes["brave"] += 1
    return ["__begin__"]


CAUSAL_RULES = [
    Rule("kindness", "social", _r_kindness),
    Rule("begin", "movement", _r_begingerund),
]


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


def is_reasonable(setting: Setting, saddle: Saddle, pony: Pony) -> bool:
    return "barn" in setting.tags and saddle.kind == pony.kind


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for pid, p in PONIES.items():
            for ad, a in SADDLES.items():
                if is_reasonable(s, a, p):
                    combos.append((sid, ad, pid))
    return combos


@dataclass
@dataclass
class StoryParams:
    setting: str
    saddle: str
    pony: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with kindness, a saddle, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--saddle", choices=SADDLES)
    ap.add_argument("--pony", choices=PONIES)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.saddle is None or c[1] == args.saddle)
              and (args.pony is None or c[2] == args.pony)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, saddle, pony = rng.choice(sorted(combos))
    child_gender = rng.choice(["girl", "boy"])
    helper_gender = "girl" if child_gender == "boy" else "boy"
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_name = args.helper or rng.choice(GIRL_NAMES if helper_gender == "girl" else BOY_NAMES)
    return StoryParams(setting, saddle, pony, child_name, child_gender, helper_name, helper_gender)


def tell(setting: Setting, saddle: Saddle, pony: Pony, child_name: str, child_gender: str,
         helper_name: str, helper_gender: str) -> World:
    world = World(setting)
    child = world.add(Entity("child", "character", child_gender, role="child", traits=["kind"]))
    helper = world.add(Entity("helper", "character", helper_gender, role="helper", traits=["gentle"]))
    pony_ent = world.add(Entity("pony", "character", "thing", label=pony.label, role="ghost pony",
                                traits=["shy", "glowing"]))
    world.facts["saddle"] = saddle
    world.facts["pony_cfg"] = pony
    world.facts["setting"] = setting
    child.id = child_name
    helper.id = helper_name
    world.entities = {child.id: child, helper.id: helper, pony_ent.id: pony_ent}

    child.memes["kindness"] = 1.0
    helper.memes["curiosity"] = 1.0
    pony_ent.memes["fear"] = 1.0
    pony_ent.memes["trust"] = 0.0

    world.say(
        f"On a moonlit night, {child_name} and {helper_name} listened to the barn "
        f"{setting.sound}. {setting.mood} {setting.place} looked dark enough to hold a secret."
    )
    world.say(
        f"Inside that hush stood a ghost pony named {pony.label}, bright at the edges and "
        f"still as a held breath."
    )

    world.para()
    child.memes["thoughtful"] += 1
    world.say(
        f"{child_name} did not run. {child_name} began to ponder what a lonely ghost pony might need."
    )
    world.say(
        f'"Maybe it only needs a little kindness," {helper_name} whispered, and the word felt warm in the cold air.'
    )

    world.para()
    pony_ent.memes["fear"] += 0.5
    world.say(
        f"{child_name} carried over {saddle.phrase}, the {saddle.label} {saddle.fit}. "
        f'It looked like a small promise, not a trap.'
    )
    world.say(
        f"With slow hands, {child_name} set the {saddle.label} on {pony.label} and spoke softly: "
        f'"You may stay if you want. We will be gentle."'
    )
    pony_ent.meters["saddled"] += 1
    child.memes["kindness"] += 1
    propagate(world)

    world.para()
    world.say(
        f"The ghost pony flickered once, then steadied. Its bright mane stopped shivering, and its eyes lost their scared glow."
    )
    if pony_ent.meters["moving"] >= THRESHOLD:
        world.say(
            f"Then the pony began-gerund, stepping forward with a soft clop that sounded more like a thank-you than a hoofbeat."
        )
    else:
        world.say(
            f"For one slow moment, nobody moved at all. Then the pony leaned into the {saddle.label} and waited for a kinder sign."
        )

    world.para()
    helper.memes["joy"] += 1
    child.memes["joy"] += 1
    if pony_ent.meters["moving"] >= THRESHOLD:
        world.say(
            f"{child_name} climbed up, and the ghost pony carried {child_name} and {helper_name} through the barn door into silver grass."
        )
        world.say(
            f"The night did not feel spooky anymore. It felt like a secret ride under the stars, and the pony's pale trail glimmered behind them."
        )
    else:
        world.say(
            f"At last the pony took a brave step, and the three of them laughed when the old boards creaked like happy mice."
        )
        world.say(
            f"By the end, the barn was still dark, but it no longer felt lonely."
        )

    world.facts.update(child=child, helper=helper, pony=pony_ent, outcome="happy")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a young child that uses the words "ponder", "saddle", and "begin-gerund", and ends kindly.',
        f"Tell a spooky-but-sweet story where {f['child'].id} helps a ghost pony with kindness and a saddle.",
        f"Write a moonlit barn story with a happy ending, where the child has to ponder what the ghost pony needs before it can begin moving again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child = world.facts["child"]
    pony = world.facts["pony"]
    saddle = world.facts["saddle"]
    return [
        QAItem(
            question="What did the child do before helping the pony?",
            answer=f"{child.id} paused to ponder what the ghost pony might need. That quiet thinking made the help gentle instead of scary."
        ),
        QAItem(
            question="What did the child use on the ghost pony?",
            answer=f"{child.id} used {saddle.phrase}. The {saddle.label} fit the pony well and helped it feel safe."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended happily. The ghost pony trusted them, began moving again, and carried them out into the moonlight without any fear."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to ponder?",
            answer="To ponder means to think carefully for a moment before you act. It is a slow, thoughtful kind of thinking."
        ),
        QAItem(
            question="What is a saddle for?",
            answer="A saddle is a seat or cover that helps someone ride a horse or pony more safely and comfortably."
        ),
        QAItem(
            question="Why can kindness help a scared animal?",
            answer="Kindness makes a scared animal feel safe. When an animal trusts you, it can relax and accept help."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
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


def dump_trace(world: World) -> str:
    lines = ["--- world ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: meters={meters} memes={memes} role={e.role} type={e.type}")
    return "\n".join(lines)


SETTINGS = {
    "barn": Setting("barn", "the barn", "sleepy", "boards sighed", "the shadows"),
    "stable": Setting("stable", "the stable", "quiet", "straw rustled", "the corners"),
}
SADDLES = {
    "gentle": Saddle("gentle", "gentle saddle", "a gentle saddle with a soft blanket", "pony", "fit just right", "softly"),
    "star": Saddle("star", "star saddle", "a small starry saddle", "pony", "rested lightly", "carefully"),
}
PONIES = {
    "moon": Pony("moon", "Moonhoof", "a pale ghost pony", "pony", "light as mist", tags={"ghost", "pony"}),
    "ember": Pony("ember", "Emberstep", "a bright little ghost pony", "pony", "light as mist", tags={"ghost", "pony"}),
}
GIRL_NAMES = ["Lily", "Mia", "Nora", "Rose", "Ella"]
BOY_NAMES = ["Ben", "Theo", "Max", "Finn", "Leo"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(sid, sad, pid) for sid in SETTINGS for sad in SADDLES for pid in PONIES if is_reasonable(SETTINGS[sid], SADDLES[sad], PONIES[pid])]


CURATED = [
    StoryParams("barn", "gentle", "moon", "Lily", "girl", "Ben", "boy"),
    StoryParams("stable", "star", "ember", "Theo", "boy", "Mia", "girl"),
]


ASP_RULES = r"""
valid(S, Sa, P) :- setting(S), saddle(Sa), pony(P), barnlike(S), ponykind(P, K), saddlekind(Sa, K).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "barn" in s.tags:
            lines.append(asp.fact("barnlike", sid))
    for aid, a in SADDLES.items():
        lines.append(asp.fact("saddle", aid))
        lines.append(asp.fact("saddlekind", aid, a.kind))
    for pid, p in PONIES.items():
        lines.append(asp.fact("pony", pid))
        lines.append(asp.fact("ponykind", pid, p.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import random as _r
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), _r.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SADDLES[params.saddle], PONIES[params.pony],
                 params.child_name, params.child_gender, params.helper_name, params.helper_gender)
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
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2 ** 31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random((args.seed or 0) + i if args.seed is not None else rng.randrange(2 ** 31)))
            samples.append(generate(p))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
