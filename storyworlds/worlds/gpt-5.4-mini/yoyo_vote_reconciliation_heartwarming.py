#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/yoyo_vote_reconciliation_heartwarming.py
=========================================================================

A small heartwarming story world about friends, a toy yoyo, and a vote that
leads to reconciliation.

The domain is intentionally tiny: two or three children want different things,
they vote, somebody feels left out, and a kind reset turns the moment into a
shared game. The yoyo is the concrete object that anchors the ending image.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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
    feel: str
    activity: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class ObjectItem:
    id: str
    label: str
    sparkle: str
    weight: int = 1

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Choice:
    id: str
    text: str
    effect: str
    fair: bool
    happy: bool

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("resolved"):
        for e in world.characters():
            if e.memes["hurt"] >= THRESHOLD:
                sig = ("reconcile", e.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                e.memes["hurt"] = 0.0
                e.memes["warmth"] += 1
                out.append("__reconcile__")
    return out


CAUSAL_RULES = [Rule("reconcile", "social", _r_reconcile)]


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


def vote_outcome(choice_a: Choice, choice_b: Choice) -> str:
    if choice_a.id == choice_b.id:
        return "shared"
    if choice_a.fair and choice_b.fair:
        return "reconciled"
    return "split"


SETTINGS = {
    "living_room": Setting("living_room", "the living room", "soft and cozy", "a rainy afternoon"),
    "playroom": Setting("playroom", "the playroom", "bright and cheerful", "an after-school hour"),
    "porch": Setting("porch", "the sunny porch", "gentle and warm", "a quiet morning"),
}

OBJECTS = {
    "yoyo": ObjectItem("yoyo", "a red yoyo", "bright little circles"),
    "book": ObjectItem("book", "a picture book", "golden page corners"),
    "blocks": ObjectItem("blocks", "a stack of blocks", "tiny painted edges"),
}

CHOICES = {
    "yoyo": Choice("yoyo", "play with the yoyo", "spin the yoyo together", True, True),
    "book": Choice("book", "read a picture book", "read together quietly", True, True),
    "blocks": Choice("blocks", "build a tower of blocks", "build something together", True, True),
}

NAMES = ["Mia", "Noah", "Lena", "Owen", "Ava", "Eli", "Nora", "Leo"]
GENDERS = ["girl", "boy"]
TRAITS = ["gentle", "kind", "patient", "thoughtful", "careful"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    object: str
    vote1: str
    vote2: str
    host: str
    host_gender: str
    guest: str
    guest_gender: str
    trait: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    ap = argparse.ArgumentParser(description="Heartwarming vote-and-reconciliation story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--vote1", choices=CHOICES)
    ap.add_argument("--vote2", choices=CHOICES)
    ap.add_argument("--host")
    ap.add_argument("--host-gender", choices=GENDERS)
    ap.add_argument("--guest")
    ap.add_argument("--guest-gender", choices=GENDERS)
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for obj in OBJECTS:
            for v1 in CHOICES:
                for v2 in CHOICES:
                    if v1 != v2:
                        out.append((s, obj, f"{v1}:{v2}"))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.object:
        combos = [c for c in combos if c[1] == args.object]
    if args.vote1:
        combos = [c for c in combos if c[2].split(":")[0] == args.vote1]
    if args.vote2:
        combos = [c for c in combos if c[2].split(":")[1] == args.vote2]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, votes = rng.choice(sorted(combos))
    v1, v2 = votes.split(":")
    host_gender = args.host_gender or rng.choice(GENDERS)
    guest_gender = args.guest_gender or ("boy" if host_gender == "girl" else "girl")
    host = args.host or rng.choice(NAMES)
    guest = args.guest or rng.choice([n for n in NAMES if n != host])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, obj, v1, v2, host, host_gender, guest, guest_gender, trait)


def _setup(world: World, params: StoryParams) -> None:
    host = world.add(Entity(params.host, "character", params.host_gender, role="host", traits=[params.trait]))
    guest = world.add(Entity(params.guest, "character", params.guest_gender, role="guest", traits=["gentle"]))
    toy = world.add(Entity("toy", "thing", "toy", label=OBJECTS[params.object].label))
    host.memes["hope"] += 1
    guest.memes["hope"] += 1
    world.facts.update(host=host, guest=guest, toy=toy, setting=SETTINGS[params.setting],
                       object_cfg=OBJECTS[params.object], vote1=CHOICES[params.vote1],
                       vote2=CHOICES[params.vote2])


def tell_story(world: World, params: StoryParams) -> None:
    host = world.get(params.host)
    guest = world.get(params.guest)
    toy = world.get("toy")
    setting = SETTINGS[params.setting]
    c1 = CHOICES[params.vote1]
    c2 = CHOICES[params.vote2]

    world.say(f"On a {setting.feel} {setting.activity}, {host.id} and {guest.id} sat together in {setting.place}.")
    world.say(f"On the rug sat {toy.label}, shining with {OBJECTS[params.object].sparkle}.")
    world.say(f'{host.id} wanted to {c1.text}, but {guest.id} wanted to {c2.text}.')
    host.memes["stubborn"] += 1
    guest.memes["stubborn"] += 1

    world.para()
    world.say(f"They chose to vote. {host.id} raised a hand for {c1.id}, and {guest.id} raised a hand for {c2.id}.")
    outcome = vote_outcome(c1, c2)
    world.facts["vote_outcome"] = outcome

    if outcome == "split":
        host.memes["hurt"] += 1
        guest.memes["hurt"] += 1
        world.say(f"The vote did not help, because they both still wanted different things.")
        world.say(f"For a tiny moment, the room went quiet, and {host.id} looked down at the {toy.label}.")
    else:
        host.memes["joy"] += 1
        guest.memes["joy"] += 1
        world.say(f"The vote gave them a fair start, but one friend still felt left out.")
        hurt = guest if params.vote1 == "yoyo" else host
        hurt.memes["hurt"] += 1
        world.say(f"{hurt.id} crossed {hurt.pronoun('possessive')} arms and went still.")

    world.para()
    if host.memes["hurt"] >= THRESHOLD or guest.memes["hurt"] >= THRESHOLD:
        world.say(f"Then the other friend scooted closer and said, 'I don't want to win if it makes you sad.'")
        world.say(f"They tried again, this time with kind words and one more small vote for what to do next.")
        world.facts["resolved"] = True
        propagate(world, narrate=False)
        host.memes["love"] += 1
        guest.memes["love"] += 1
        world.say(f'They chose to share the {toy.label} and take turns, smiling when the spinning string danced in the air.')
        world.say(f'{host.id} gave {guest.id} the first turn, and then they laughed together when the yoyo hummed back down into a waiting hand.')
        world.say(f"By the end, no one felt left out. The little choice had turned into a friendlier plan.")
    else:
        world.facts["resolved"] = True
        propagate(world, narrate=False)
        world.say(f"They laughed, because the vote had already given them the same idea.")
        world.say(f'Together they picked up the {toy.label} and played side by side until the room felt warm with easy happiness.')

    world.facts["ended_with_yoyo"] = params.object == "yoyo"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    host, guest, toy = f["host"], f["guest"], f["toy"]
    return [
        f'Write a heartwarming story for a young child that includes the words "yoyo" and "vote".',
        f"Tell a gentle story where {host.id} and {guest.id} cannot agree, so they vote and then make up kindly.",
        f'Write a sweet reconciliation story where a small vote helps two children share {toy.label} and feel close again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    host, guest, toy = f["host"], f["guest"], f["toy"]
    setting = f["setting"]
    vote1, vote2 = f["vote1"], f["vote2"]
    items = [
        QAItem(
            question="What were the children trying to decide?",
            answer=f"They were deciding whether to {vote1.text} or {vote2.text}. The vote gave them a fair way to choose without shouting."
        ),
        QAItem(
            question="What did they vote about?",
            answer=f"They voted about what to do with the {toy.label}. One child wanted one thing, and the other wanted something different."
        ),
        QAItem(
            question="How did the story become kind again?",
            answer="They talked softly, noticed the hurt feelings, and chose to share. That helped them make up and feel close again."
        ),
    ]
    if f.get("vote_outcome") == "split":
        items.append(QAItem(
            question=f"Why did {host.id} and {guest.id} feel upset at first?",
            answer=f"They each wanted a different plan, so the vote did not settle everything. Once they saw that, they found a gentler way to play together."
        ))
    else:
        items.append(QAItem(
            question="What made the ending warm and happy?",
            answer=f"They used the {toy.label} together instead of fighting over it. The room stayed calm, and the ending image showed sharing instead of winning."
        ))
    return items


WORLD_KNOWLEDGE = {
    "vote": [
        QAItem(
            question="What is a vote?",
            answer="A vote is when people choose by raising hands or saying what they prefer. It is a fair way to decide together."
        )
    ],
    "yoyo": [
        QAItem(
            question="What is a yoyo?",
            answer="A yoyo is a small toy on a string. You throw it down and bring it back up again."
        )
    ],
    "reconciliation": [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means making up after a disagreement. People listen, forgive, and feel friendly again."
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"vote", "reconciliation", "yoyo"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(WORLD_KNOWLEDGE.get(tag, []))
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("living_room", "yoyo", "yoyo", "book", "Mia", "girl", "Noah", "boy", "gentle"),
    StoryParams("playroom", "yoyo", "blocks", "yoyo", "Ava", "girl", "Leo", "boy", "patient"),
    StoryParams("porch", "yoyo", "book", "blocks", "Nora", "girl", "Owen", "boy", "kind"),
]


def explain_rejection() -> str:
    return "(No story: the choices did not leave enough room for a fair vote and a kind reconciliation.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
    for cid in CHOICES:
        lines.append(asp.fact("choice", cid))
    lines.append(asp.fact("feature", "reconciliation"))
    lines.append(asp.fact("word", "yoyo"))
    lines.append(asp.fact("word", "vote"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,C1,C2) :- setting(S), object(O), choice(C1), choice(C2), C1 != C2.
reconciled(O) :- object(O), feature(reconciliation).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH: ASP and Python valid_combos() differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            setting=None, object=None, vote1=None, vote2=None,
            host=None, host_gender=None, guest=None, guest_gender=None,
            trait=None, seed=None
        ), random.Random(777)))
        _ = sample.story
        print("OK: smoke-tested generate() successfully.")
    except Exception as exc:
        rc = 1
        print(f"MISMATCH: generate() crashed: {exc}")
    return rc


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for o in OBJECTS:
            for c1 in CHOICES:
                for c2 in CHOICES:
                    if c1 != c2:
                        out.append((s, o, f"{c1}:{c2}"))
    return out


def build_story(params: StoryParams) -> StorySample:
    world = World()
    _setup(world, params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generate(params: StoryParams) -> StorySample:
    return build_story(params)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)]
    if not combos:
        raise StoryError(explain_rejection())
    setting, obj, votes = rng.choice(sorted(combos))
    v1, v2 = votes.split(":")
    host_gender = args.host_gender or rng.choice(GENDERS)
    guest_gender = args.guest_gender or ("boy" if host_gender == "girl" else "girl")
    host = args.host or rng.choice(NAMES)
    guest = args.guest or rng.choice([n for n in NAMES if n != host])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, obj, v1, v2, host, host_gender, guest, guest_gender, trait)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
