#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ouch_dim_peek_friendship_comedy.py
===================================================================

A tiny comedy storyworld about two friends, a mysterious peek, and an
"ouch-dim" moment that turns into a laugh.

Premise
-------
Two friends are playing a peek-and-sneak game in a cozy place. One of them
peeks into a silly hiding spot, bumps into an awkward object, says "ouch-dim",
and the other friend helps make it funny and safe again.

This world keeps the tone light and child-facing:
- friendship is central
- the danger is small and comic, not scary
- the turn is state-driven: peeking changes what is hidden / revealed, and the
  ouch-dim bump changes physical and emotional state
- the ending proves the friendship changed from startled to amused and helpful
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
    scene: str
    hiding_spot: str
    surface: str
    note: str

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
class PeekableThing:
    id: str
    label: str
    hidden: str
    reveal: str
    bumpable: bool = True
    tags: set[str] = field(default_factory=set)

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
@dataclass
class StoryParams:
    setting: str
    thing: str
    response: str
    peeker: str
    peeker_gender: str
    friend: str
    friend_gender: str
    parent: str
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


def _r_startled(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["bumped"] < THRESHOLD:
            continue
        sig = ("startled", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["surprise"] += 1
        e.memes["laugh"] += 1
        out.append("__startled__")
    return out


def _r_friend_help(world: World) -> list[str]:
    out: list[str] = []
    p = world.get("peeker")
    f = world.get("friend")
    if p.memes["surprise"] >= THRESHOLD and f.memes["kindness"] >= THRESHOLD:
        sig = ("help",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        p.memes["calm"] += 1
        f.memes["pride"] += 1
        out.append("__help__")
    return out


CAUSAL_RULES = [Rule("startled", "social", _r_startled), Rule("friend_help", "social", _r_friend_help)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, thing in THINGS.items():
            if thing.bumpable:
                combos.append((sid, tid, "kind_laugh"))
    return combos


def reasonableness_check(setting: Setting, thing: PeekableThing) -> bool:
    return thing.bumpable and "peek" in thing.tags


def outcome_of(params: StoryParams) -> str:
    return "comedy"


def _do_peek(world: World, thing: PeekableThing, narrate: bool = True) -> None:
    item = world.get("thing")
    item.meters["peeked"] += 1
    item.meters["revealed"] += 1
    if thing.bumpable:
        item.meters["bumped"] += 1
    propagate(world, narrate=narrate)


def peek_scene(world: World, peeker: Entity, friend: Entity, thing: PeekableThing, setting: Setting) -> None:
    peeker.memes["curiosity"] += 1
    friend.memes["play"] += 1
    world.say(
        f"On a bright afternoon, {peeker.id} and {friend.id} turned {setting.scene} "
        f"into a peek-and-sneak game. {setting.note}"
    )
    world.say(
        f'They dared each other to peek into {setting.hiding_spot}. '
        f'"First peek!" {peeker.id} whispered.'
    )
    world.say(
        f'When {peeker.id} peered inside, {thing.hidden} was there, and the whole hiding spot felt extra mysterious.'
    )


def ouch_dim(world: World, peeker: Entity, friend: Entity, thing: PeekableThing) -> None:
    peeker.meters["bumped"] += 1
    peeker.memes["oops"] += 1
    propagate(world, narrate=False)
    world.say(
        f'"{thing.reveal}!" {peeker.id} yelped. "Ouch-dim!"'
    )
    world.say(
        f'{friend.id} snorted so hard {friend.pronoun()} had to hold {friend.pronoun("possessive")} belly.'
    )


def calm_and_laugh(world: World, peeker: Entity, friend: Entity, parent: Entity, thing: PeekableThing) -> None:
    peeker.memes["calm"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"{friend.id} peeked too, saw the silly spot, and grinned. "
        f'"That was a funny ouch-dim," {friend.id} said. "{parent.label_word.capitalize()}! We found the secret trouble spot!"'
    )
    world.say(
        f"{parent.label_word.capitalize()} came over, checked that nobody was hurt, and moved {thing.label} aside with a smile."
    )


def ending(world: World, peeker: Entity, friend: Entity, setting: Setting) -> None:
    peeker.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Then {peeker.id} and {friend.id} made a new game: they peeked around {setting.surface} instead, "
        f"laughing every time they found something ordinary looking very important."
    )
    world.say(
        f"This time the secret was only a giggle, and their friendship felt as bouncy as a rubber ball."
    )


def tell(setting: Setting, thing: PeekableThing, response: Response,
         peeker_name: str = "Milo", peeker_gender: str = "boy",
         friend_name: str = "Nia", friend_gender: str = "girl",
         parent_type: str = "mother") -> World:
    world = World()
    peeker = world.add(Entity("peeker", kind="character", type=peeker_gender, label=peeker_name, role="peeker"))
    friend = world.add(Entity("friend", kind="character", type=friend_gender, label=friend_name, role="friend"))
    parent = world.add(Entity("parent", kind="character", type=parent_type, label="the parent", role="parent"))
    obj = world.add(Entity("thing", type="thing", label=thing.label))
    peeker.memes["curiosity"] = 1.0
    friend.memes["kindness"] = 1.0

    peek_scene(world, peeker, friend, thing, setting)
    world.para()
    ouch_dim(world, peeker, friend, thing)
    world.para()
    calm_and_laugh(world, peeker, friend, parent, thing)
    world.para()
    ending(world, peeker, friend, setting)

    world.facts.update(
        setting=setting, thing=thing, response=response,
        peeker=peeker, friend=friend, parent=parent,
        outcome="comedy", bumped=True, soothed=True, object=obj,
    )
    return world


SETTINGS = {
    "closet": Setting("closet", "a cozy closet", "the curtain", "the shelf", "The shoes were lined up like tiny guards."),
    "playroom": Setting("playroom", "a colorful playroom", "the toy tower", "the rug", "A stuffed lion watched the room like a sleepy king."),
    "porch": Setting("porch", "the front porch", "the watering can", "the bench", "A wind chime sang little notes whenever anyone giggled."),
}

THINGS = {
    "sock_pile": PeekableThing("sock_pile", "sock pile", "a mountain of socks", "a sock avalanche", tags={"peek", "sock"}),
    "basket": PeekableThing("basket", "laundry basket", "a basket full of towels", "a towel tangle", tags={"peek", "laundry"}),
    "hat_box": PeekableThing("hat_box", "hat box", "a box full of floppy hats", "a hat parade", tags={"peek", "hat"}),
}

RESPONSES = {
    "kind_laugh": Response("kind_laugh", 3, 3,
        "laughed it off, picked up the silly thing, and turned the moment into a joke",
        "laughed, but the funny mess stayed in the way",
        "laughed it off and picked up the silly thing",
        tags={"laugh", "friendship"}),
    "gentle_fix": Response("gentle_fix", 2, 2,
        "moved the obstacle aside and made the peek spot safe again",
        "tried to move it, but it was too wobbly to fix",
        "moved the obstacle aside and made the spot safe again",
        tags={"fix", "friendship"}),
}

GIRL_NAMES = ["Nia", "Mina", "Zoe", "Luna", "Ada", "Bea"]
BOY_NAMES = ["Milo", "Owen", "Finn", "Theo", "Eli", "Noah"]


@dataclass
class StoryParams:
    setting: str
    thing: str
    response: str
    peeker: str
    peeker_gender: str
    friend: str
    friend_gender: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short comedy story for a young child that includes the words "peek" and "ouch-dim".',
        f"Tell a friendship story where {f['peeker'].label} and {f['friend'].label} peek into {f['thing'].label} and something silly happens.",
        f"Write a funny, gentle story about a peek gone wrong, then fixed with kindness and laughter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    peeker, friend, parent, thing, setting = f["peeker"], f["friend"], f["parent"], f["thing"], f["setting"]
    return [
        QAItem(
            question="What were the two friends doing?",
            answer=f"They were playing a peek-and-sneak game in {setting.scene}. The game made them curious and set up the silly surprise."
        ),
        QAItem(
            question=f"What happened when {peeker.label} peeked?",
            answer=f"{peeker.label} bumped into {thing.reveal} and shouted ouch-dim. The bump made the moment funny instead of scary."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{friend.label} laughed kindly, {parent.label_word} helped move the trouble spot aside, and the friends started a safer game. Their friendship ended happier than it began."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does peek mean?",
            answer="Peek means to look quickly or secretly. People peek when they want to see something without staring for long."
        ),
        QAItem(
            question="Why do friends laugh together in a comedy story?",
            answer="Friends laugh together because the problem is small and surprising, not mean or scary. The laughter shows they still care about each other."
        ),
    ]


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(setting: Setting, thing: PeekableThing) -> str:
    return f"(No story: the thing does not make a good peek-comedy beat in {setting.scene}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny friendship comedy storyworld about peek and ouch-dim.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    thing = args.thing or rng.choice(list(THINGS))
    if args.setting and args.thing and not reasonableness_check(SETTINGS[args.setting], THINGS[args.thing]):
        raise StoryError(explain_rejection(SETTINGS[args.setting], THINGS[args.thing]))
    response = args.response or rng.choice(list(RESPONSES))
    peeker_gender = rng.choice(["boy", "girl"])
    friend_gender = "girl" if peeker_gender == "boy" else "boy"
    peeker = args.name or rng.choice(GIRL_NAMES if peeker_gender == "girl" else BOY_NAMES)
    friend = args.friend or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, thing, response, peeker, peeker_gender, friend, friend_gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], THINGS[params.thing], RESPONSES[params.response],
                 params.peeker, params.peeker_gender, params.friend, params.friend_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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


ASP_RULES = r"""
valid(S, T) :- setting(S), thing(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in THINGS:
        lines.append(asp.fact("thing", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, thing=None, response=None, name=None, friend=None, parent=None), random.Random(777)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams("playroom", "sock_pile", "kind_laugh", "Milo", "boy", "Nia", "girl", "mother"),
    StoryParams("closet", "hat_box", "gentle_fix", "Luna", "girl", "Theo", "boy", "father"),
    StoryParams("porch", "basket", "kind_laugh", "Eli", "boy", "Ada", "girl", "mother"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for tid, thing in THINGS.items():
            if reasonableness_check(setting, thing):
                combos.append((sid, tid))
    return combos


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, t in asp_valid_combos():
            print(f"  {s:10} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.peeker} & {p.friend}: peek comedy in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
