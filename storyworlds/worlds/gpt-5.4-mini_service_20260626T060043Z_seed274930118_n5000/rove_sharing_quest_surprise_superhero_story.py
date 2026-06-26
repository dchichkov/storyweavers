#!/usr/bin/env python3
"""
A standalone story world for a small superhero tale about a roving hero,
a sharing choice, a quest, and a surprise.
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

@dataclass
class MeteredEntity:
    id: str
    kind: str
    label: str
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryPlace:
    name: str
    clue: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    route: str
    risk: str
    surprise: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Shareable:
    id: str
    label: str
    phrase: str
    kind: str = "item"
    plural: bool = False
    cherished_by: set[str] = field(default_factory=set)
    solves: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: StoryPlace) -> None:
        self.place = place
        self.entities: dict[str, MeteredEntity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, ent: MeteredEntity) -> MeteredEntity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> MeteredEntity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "skyline": StoryPlace(name="the skyline", clue="tall roofs and bright windows", affords={"rove", "quest"}),
    "harbor": StoryPlace(name="the harbor", clue="windy docks and bobbing boats", affords={"rove", "quest"}),
    "museum": StoryPlace(name="the museum", clue="quiet halls and shining displays", affords={"quest"}),
    "park": StoryPlace(name="the park", clue="wide paths and shady trees", affords={"rove", "quest"}),
}

QUESTS = {
    "lostkite": Quest(
        id="lostkite",
        goal="find the lost kite",
        route="follow the ribbon trail",
        risk="the wind might toss the clue away",
        surprise="a trapped kitten was tugging the string instead",
        clue="a red ribbon that flapped like a tiny flag",
        tags={"sky", "wind", "surprise"},
    ),
    "silverkey": Quest(
        id="silverkey",
        goal="bring back the silver key",
        route="cross the bridge of glass",
        risk="the bridge was slippery",
        surprise="the key was inside a puzzle box",
        clue="a silver glint under a bench",
        tags={"shiny", "key", "surprise"},
    ),
    "starlight": Quest(
        id="starlight",
        goal="deliver the starlight badge",
        route="rove through the lantern lane",
        risk="the lane was crowded",
        surprise="the badge belonged to a shy helper",
        clue="a star-shaped pin on a blue cloth",
        tags={"badge", "light", "surprise"},
    ),
}

SHARES = {
    "cape": Shareable(
        id="cape",
        label="cape",
        phrase="a soft blue cape",
        cherished_by={"hero"},
        solves={"cold", "glow"},
    ),
    "snack": Shareable(
        id="snack",
        label="snack pack",
        phrase="a pouch of berry snacks",
        plural=False,
        cherished_by={"friend"},
        solves={"hunger", "sharing"},
    ),
    "mask": Shareable(
        id="mask",
        label="mask",
        phrase="a shiny mask",
        cherished_by={"hero"},
        solves={"disguise"},
    ),
    "gloves": Shareable(
        id="gloves",
        label="gloves",
        phrase="a pair of warm gloves",
        plural=True,
        cherished_by={"friend", "hero"},
        solves={"cold"},
    ),
}

HERO_NAMES = ["Nova", "Riley", "Milo", "Zuri", "Bea", "Jett", "Nia", "Tate"]
FRIEND_NAMES = ["Pip", "June", "Ollie", "Sky", "Mina", "Finn", "Luna"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["brave", "kind", "curious", "quick", "gentle", "bold"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    quest: str
    share: str
    hero_name: str
    hero_type: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- site(P).
quest(Q) :- mission(Q).
share(S) :- gift(S).

can_story(P,Q,S) :- site(P), mission(Q), gift(S), afford(P,rove), afford(P,quest), share_solves(S,sharing), quest_has(Q,surprise).
can_story(P,Q,S) :- site(P), mission(Q), gift(S), afford(P,rove), afford(P,quest), share_solves(S,cold), quest_has(Q,surprise).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("site", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("afford", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("mission", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("quest_has", qid, t))
    for sid, s in SHARES.items():
        lines.append(asp.fact("gift", sid))
        for s2 in sorted(s.solves):
            lines.append(asp.fact("share_solves", sid, s2))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show can_story/3."))
    return sorted(set(asp.atoms(model, "can_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        if "rove" not in place.affords:
            continue
        for qid in QUESTS:
            for sid, share in SHARES.items():
                if "surprise" in QUESTS[qid].tags and share.solves & {"sharing", "cold"}:
                    combos.append((pid, qid, sid))
    return combos


def explain_rejection(place: str, quest: str, share: str) -> str:
    p = PLACES[place]
    q = QUESTS[quest]
    s = SHARES[share]
    return (
        f"(No story: {p.name} does not support the roving quest in a way that fits "
        f"this sharing surprise. Try a place with room to rove, a quest with a surprise, "
        f"and a shareable item that actually helps.)"
    )


# ---------------------------------------------------------------------------
# Narrative engine
# ---------------------------------------------------------------------------

def _hero_phrase(hero: MeteredEntity) -> str:
    return f"{hero.label}"


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(MeteredEntity(id="hero", kind="character", label=params.hero_name, type=params.hero_type))
    friend = world.add(MeteredEntity(id="friend", kind="character", label=params.friend_name, type="boy"))
    share = world.add(MeteredEntity(id="share", kind="thing", label=SHARES[params.share].label))
    quest = world.add(MeteredEntity(id="quest", kind="thing", label=QUESTS[params.quest].goal))

    world.facts.update(hero=hero, friend=friend, share=share, quest=quest, params=params)
    hero.memes["hope"] = 1
    friend.memes["trust"] = 1
    share.meters["value"] = 1
    quest.meters["importance"] = 1
    return world


def narrate(world: World) -> None:
    f = world.facts
    hero: MeteredEntity = f["hero"]
    friend: MeteredEntity = f["friend"]
    share: MeteredEntity = f["share"]
    q: MeteredEntity = f["quest"]
    params: StoryParams = f["params"]
    quest_def = QUESTS[params.quest]
    share_def = SHARES[params.share]

    world.say(
        f"{hero.label} was a {params.trait} young superhero who loved to rove "
        f"across {world.place.name} looking for people to help."
    )
    world.say(
        f"One bright day, {hero.label} and {friend.label} heard about a quest to {quest_def.goal}."
    )
    world.say(
        f"They packed {share_def.phrase}, because even heroes need to share when a long day starts."
    )
    world.para()
    hero.memes["quest"] = 1
    world.say(
        f"At {world.place.name}, they began to rove past {world.place.clue} and followed {quest_def.clue}."
    )
    world.say(
        f"The path was tricky, and {quest_def.risk}, but {hero.label} kept going anyway."
    )
    if params.quest == "lostkite":
        world.say("Then came a surprise: the ribbon led to a kitten hiding under a bench.")
    elif params.quest == "silverkey":
        world.say("Then came a surprise: the shining key was tucked inside a puzzle box.")
    else:
        world.say("Then came a surprise: the badge belonged to a shy helper who needed a friend.")
    hero.memes["surprise"] = 1
    world.para()
    share.meters["shared"] = 1
    hero.memes["kindness"] = 1
    friend.memes["joy"] = 1
    world.say(
        f"{hero.label} shared {share_def.label} with {friend.label}, and that made the quest easier."
    )
    world.say(
        f"Together they finished the quest, and {hero.label} carried home the lesson that a true hero can rove, share, and still be ready for a surprise."
    )
    world.say(
        f"By the end, {friend.label} smiled beside {hero.label}, and the city felt a little safer."
    )
    world.facts["resolved"] = True


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    return [
        f"Write a superhero story about {p.hero_name} who loves to rove, share, and handle a surprise quest.",
        f"Tell a short child-friendly tale where a hero named {p.hero_name} goes on the {QUESTS[p.quest].goal} quest.",
        f"Write a story that includes roving across {PLACES[p.place].name}, sharing {SHARES[p.share].phrase}, and a surprise ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    q = QUESTS[p.quest]
    s = SHARES[p.share]
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {p.hero_name}, a {p.trait} {p.hero_type} who likes to rove and help.",
        ),
        QAItem(
            question=f"What quest did {p.hero_name} go on?",
            answer=f"{p.hero_name} went on a quest to {q.goal}.",
        ),
        QAItem(
            question=f"What did {p.hero_name} share during the quest?",
            answer=f"{p.hero_name} shared {s.phrase} with a friend.",
        ),
        QAItem(
            question=f"What was the surprise in the story?",
            answer=f"The surprise was that {q.surprise}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to rove?",
            answer="To rove means to move around from place to place, looking, exploring, or searching.",
        ),
        QAItem(
            question="Why do superheroes share?",
            answer="Superheroes share because helping friends and using things together can make hard jobs easier.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special goal or adventure that someone tries to finish.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens when you did not know it was coming.",
        ),
    ]


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
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world with roving, sharing, questing, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--share", choices=SHARES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=HERO_TYPES)
    ap.add_argument("--friend")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.quest or args.share:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.quest is None or c[1] == args.quest)
            and (args.share is None or c[2] == args.share)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, quest, share = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        quest=quest,
        share=share,
        hero_name=args.name or rng.choice(HERO_NAMES),
        hero_type=args.gender or rng.choice(HERO_TYPES),
        friend_name=args.friend or rng.choice(FRIEND_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:7} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="skyline", quest="lostkite", share="snack", hero_name="Nova", hero_type="girl", friend_name="Pip", trait="brave"),
    StoryParams(place="harbor", quest="silverkey", share="gloves", hero_name="Riley", hero_type="boy", friend_name="June", trait="kind"),
    StoryParams(place="park", quest="starlight", share="cape", hero_name="Zuri", hero_type="girl", friend_name="Sky", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show can_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
