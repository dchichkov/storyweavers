#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/pearl_recyclable_participant_dining_room_kindness_humor.py
==========================================================================================

A standalone story world for a tiny dining-room tale: a child becomes upset
about a recycled paper crown with a pearl sticker, a kind helper uses humor to
repair the mood, and everyone ends in reconciliation. The prose is written in a
rhyming-story style with a simple, state-driven turn.

Seed words:
- pearl
- recyclable
- participant

Setting:
- dining room

Features:
- Kindness
- Humor
- Reconciliation
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
from typing import Optional

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
class Thing:
    id: str
    label: str
    phrase: str
    material: str
    recyclable: bool = False
    shiny: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
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
class Action:
    id: str
    verb: str
    rhyming_line: str
    mess: str
    turn_word: str
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
class Comfort:
    id: str
    label: str
    phrase: str
    rhyme: str
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
class World:
    room: str
    entities: dict[str, Entity] = field(default_factory=dict)
    things: dict[str, Thing] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_thing(self, t: Thing) -> Thing:
        self.things[t.id] = t
        return t

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.room)
        w.entities = copy.deepcopy(self.entities)
        w.things = copy.deepcopy(self.things)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w

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


ROOM = "the dining room"

CHAR_NAMES = ["Mia", "Noah", "Luna", "Eli", "Ava", "Theo"]
PARENT_NAMES = ["Mom", "Dad"]
TRAITS = ["kind", "cheerful", "funny", "gentle", "silly"]

ACTIONS = {
    "decorate": Action("decorate", "decorate the table", "decorate and create a plate parade", "messy", "twinkle"),
    "sort": Action("sort the recyclables", "sort and spin like a parade", "paper", "sparkle"),
    "stack": Action("stack cups and napkins", "stack and tap in a happy clap", "wobbly", "giggle"),
}

THINGS = {
    "pearl": Thing("pearl", "pearl", "a pearl sticker", "paper", recyclable=True, shiny=True, tags={"pearl"}),
    "recyclable": Thing("recyclable", "recyclable bin", "a recyclable bin", "plastic", recyclable=True, tags={"recyclable"}),
    "participant": Thing("participant", "participant badge", "a participant badge", "cardboard", recyclable=True, tags={"participant"}),
    "plate": Thing("plate", "plate", "a dinner plate", "ceramic", tags={"plate"}),
}

COMFORTS = {
    "joke_book": Comfort("joke_book", "joke book", "a joke book", "book of bright jokes", tags={"humor"}),
    "rhyme_card": Comfort("rhyme_card", "rhyme card", "a rhyme card", "card of kindly rhymes", tags={"humor"}),
}

SENSE_MIN = 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for a in ACTIONS:
        for t in THINGS:
            if THINGS[t].recyclable and a in {"sort", "decorate", "stack"}:
                combos.append((ROOM, a, t))
    return combos


@dataclass
@dataclass
class StoryParams:
    room: str
    action: str
    thing: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    parent: str
    trait: str
    comfort: str
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
    ap = argparse.ArgumentParser(description="Rhyming dining-room kindness storyworld.")
    ap.add_argument("--room", choices=[ROOM])
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["Mom", "Dad"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--comfort", choices=COMFORTS)
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = [n for n in CHAR_NAMES if n != avoid]
    return rng.choice(pool)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and not THINGS[args.thing].recyclable:
        raise StoryError("This dining-room tale wants a recyclable, shiny little prop.")
    combos = [c for c in valid_combos()
              if (args.room is None or c[0] == args.room)
              and (args.action is None or c[1] == args.action)
              and (args.thing is None or c[2] == args.thing)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, action, thing = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender, avoid=hero)
    parent = args.parent or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    comfort = args.comfort or rng.choice(list(COMFORTS))
    return StoryParams(room, action, thing, hero, hero_gender, friend, friend_gender, parent, trait, comfort)


def _tell(params: StoryParams) -> World:
    w = World(params.room)
    hero = w.add_entity(Entity(params.hero, "character", params.hero_gender, role="hero", traits=[params.trait]))
    friend = w.add_entity(Entity(params.friend, "character", params.friend_gender, role="friend", traits=["kind"]))
    parent = w.add_entity(Entity(params.parent, "character", "mother" if params.parent == "Mom" else "father", role="parent"))
    thing = w.add_thing(copy.deepcopy(THINGS[params.thing]))
    comfort = w.add_thing(copy.deepcopy(COMFORTS[params.comfort]))
    w.facts.update(hero=hero, friend=friend, parent=parent, thing=thing, comfort=comfort, action=ACTIONS[params.action])

    hero.memes["pride"] += 1
    friend.memes["warmth"] += 1
    w.say(
        f"In the dining room bright, where the silverware gleamed, "
        f"{hero.id} and {friend.id} made a small game of dreams."
    )
    w.say(
        f"They saw {thing.phrase}, all tidy and neat, and wanted a rhyme that could tap with their feet."
    )
    w.para()
    hero.memes["want"] += 1
    friend.memes["caution"] += 1
    w.say(
        f'{hero.id} said, "Let\'s {ACTIONS[params.action].verb}!" with a grin like a star, '
        f'but {friend.id} said, "Be gentle; let kindness go far."'
    )
    if params.action == "sort":
        thing.meters["scattered"] += 1
        w.say(
            f"They laughed at the bins and the labels with care, then stacked little pieces all neat in the air."
        )
    else:
        thing.memes["attention"] += 1
        w.say(
            f'The idea felt lively, with giggles and glow, but {hero.id} bumped a chair just a little too low.'
        )
    w.para()
    hero.memes["sad"] += 1
    friend.memes["humor"] += 1
    w.say(
        f'{friend.id} showed {hero.id} a {comfort.label} and winked with a grin, '
        f'"A joke and a deep breath can help us begin."'
    )
    parent.memes["kindness"] += 1
    w.say(
        f"{parent.id} came beside them, so calm and so wise, and made a small rhyme with the brightest of eyes."
    )
    w.say(
        f'"A giggle, a helping hand, and a new plan," {parent.id} said, '
        f'"can mend a small frown and bring peace back again."'
    )
    hero.memes["reconciled"] += 1
    friend.memes["reconciled"] += 1
    thing.meters["used"] += 1
    w.para()
    w.say(
        f"So {hero.id} and {friend.id} set the {thing.label} in place, "
        f"and shared a small smile that lit up the space."
    )
    w.say(
        f"In the dining room warm, with a kind little cheer, they ended as friends, "
        f"with no fuss and no fear."
    )
    w.facts["outcome"] = "reconciled"
    return w


def generate(params: StoryParams) -> StorySample:
    world = _tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming kindness story in the dining room that includes the words "pearl", "recyclable", and "participant".',
        f"Tell a short rhyming tale where {f['hero'].id} and {f['friend'].id} disagree, then use humor and kindness to reconcile.",
        f"Write a child-friendly story about a recyclable dining-room participant badge and a pearl sticker that ends with everyone making peace.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, parent, thing, comfort, action = f["hero"], f["friend"], f["parent"], f["thing"], f["comfort"], f["action"]
    return [
        ("Who is the story about?",
         f"It is about {hero.id}, {friend.id}, and {parent.id} in the dining room. They are the participants who keep the little problem from turning sour."),
        ("What problem did they have?",
         f"{hero.id} and {friend.id} wanted to use the {thing.label} in a playful way, and that caused a small mix-up. The mix-up made kindness and humor important."),
        ("How did they fix it?",
         f"{friend.id} brought out {comfort.phrase}, and {parent.id} added a gentle rhyme. That humor helped {hero.id} calm down so they could make peace again."),
        ("How did the story end?",
         "It ended with reconciliation. Everyone smiled, the dining room felt warm again, and the small mistake turned into a kind memory."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is recyclable stuff?",
         "Recyclable things are items that can be collected and made into something new instead of being thrown away."),
        ("What is a participant?",
         "A participant is a person who takes part in an activity or game."),
        ("What does kindness mean?",
         "Kindness means choosing gentle words and helpful actions so other people feel cared for."),
        ("What is humor?",
         "Humor is what makes people laugh or smile. A funny idea can help calm a tense moment."),
        ("What is reconciliation?",
         "Reconciliation means making peace again after a disagreement or hurt feelings."),
        ("What is a pearl?",
         "A pearl is a shiny little gem that often looks smooth and bright."),
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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    for t in world.things.values():
        meters = {k: v for k, v in t.meters.items() if v}
        memes = {k: v for k, v in t.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if t.tags:
            bits.append(f"tags={sorted(t.tags)}")
        lines.append(f"  {t.id:10} (thing  ) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
recyclable(X) :- thing(X), recyclable_fact(X).
valid(Room, Action, Thing) :- room(Room), action(Action), thing(Thing), recyclable(Thing).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("room", ROOM)]
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if t.recyclable:
            lines.append(asp.fact("recyclable_fact", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in ASP valid combo parity.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(
            room=None, action=None, thing=None, hero=None, hero_gender=None,
            friend=None, friend_gender=None, parent=None, trait=None, comfort=None,
            n=1, seed=None, all=False, trace=False, qa=False, json=False,
            asp=False, verify=False, show_asp=False
        ), random.Random(7)))
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample, trace=True, qa=True)
        if not buf.getvalue().strip():
            raise RuntimeError("empty emit output")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


CURATED = [
    StoryParams(ROOM, "sort", "recyclable", "Mia", "girl", "Noah", "boy", "Mom", "kind", "joke_book"),
    StoryParams(ROOM, "decorate", "pearl", "Eli", "boy", "Ava", "girl", "Dad", "funny", "rhyme_card"),
    StoryParams(ROOM, "stack", "participant", "Luna", "girl", "Theo", "boy", "Mom", "gentle", "joke_book"),
]


def resolve_params_for_test(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
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
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.friend}: {p.action} with {p.thing}"
        if header:
            print(header)
        print(sample.story)
        if args.trace and sample.world is not None:
            print(dump_trace(sample.world))
        if args.qa:
            print()
            print(format_qa(sample))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
