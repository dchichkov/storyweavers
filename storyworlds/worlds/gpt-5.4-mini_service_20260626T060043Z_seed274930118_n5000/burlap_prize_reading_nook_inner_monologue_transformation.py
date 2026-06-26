#!/usr/bin/env python3
"""
A standalone story world: a mythic reading nook where a small prize in burlap
changes hands, hearts, and shape through inner monologue, transformation, and
friendship.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the reading nook"
    still: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    kind: str
    owner_role: str = "child"


@dataclass
class Charm:
    id: str
    label: str
    prep: str
    reveal: str
    transforms_to: str


@dataclass
class StoryParams:
    activity: str
    prize: str
    name: str
    gender: str
    companion: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.used: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ACTIONS = {
    "read": {
        "verb": "read the old tale",
        "desire": "reading the old tale",
        "risk": "the prize might be forgotten and left lonely",
        "inner": "the letters were like a quiet river",
    },
    "guard": {
        "verb": "guard the prize",
        "desire": "keeping the prize safe",
        "risk": "the prize might never be shared",
        "inner": "a prize kept only in the hand grows small",
    },
    "share": {
        "verb": "share the prize",
        "desire": "sharing the prize",
        "risk": "the prize might be torn or prized too tightly",
        "inner": "a thing given in friendship becomes brighter",
    },
}

PRIZES = {
    "burlap_charm": Prize(
        id="burlap_charm",
        label="burlap prize",
        phrase="a tiny prize wrapped in rough burlap",
        type="prize",
        kind="burlap",
    ),
    "burlap_scroll": Prize(
        id="burlap_scroll",
        label="burlap scroll",
        phrase="a narrow scroll tied in burlap",
        type="scroll",
        kind="burlap",
    ),
}

CHARMS = {
    "read": Charm(
        id="lantern", label="a small lantern", prep="lift the lantern", reveal="the light found the hidden line", transforms_to="a bright page",
    ),
    "guard": Charm(
        id="string", label="a red cord", prep="wind the cord around it", reveal="the knot softened like a thought", transforms_to="a ribbon of trust",
    ),
    "share": Charm(
        id="cup", label="a shared cup of tea", prep="set out the cup", reveal="the steam rose between them", transforms_to="a warm vow",
    ),
}

NAMES = ["Ari", "Mina", "Soren", "Lila", "Tavi", "Nia", "Eli", "Rhea"]
COMPANIONS = ["grandmother", "grandfather", "friend", "teacher"]


def valid_combo(activity: str, prize: Prize) -> bool:
    return activity in ACTIONS and prize.kind == "burlap"


def reason_invalid(activity: str, prize: Prize) -> str:
    return f"(No story: the mythic reading nook only fits burlap prizes, and {activity} cannot be bound to this prize.)"


def build_world(params: StoryParams) -> World:
    setting = Setting()
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["small", "curious"],
        memes={"wonder": 1.0, "loneliness": 0.0, "friendship": 0.0, "hope": 1.0},
    ))
    companion = world.add(Entity(
        id="Companion",
        kind="character",
        type=params.companion,
        label=f"the {params.companion}",
        memes={"kindness": 1.0, "friendship": 1.0},
    ))
    prize = world.add(Entity(
        id="Prize",
        type="prize",
        label=PRIZES[params.prize].label,
        phrase=PRIZES[params.prize].phrase,
        owner=hero.id,
        caretaker=companion.id,
        meters={"burlap": 1.0},
        memes={"value": 1.0, "mystery": 1.0},
    ))
    charm = CHARMS[params.activity]

    world.facts.update(hero=hero, companion=companion, prize=prize, activity=params.activity, charm=charm)
    world.say(f"In the reading nook, {hero.id} sat beneath a quiet lamp with {hero.pronoun('possessive')} {prize.label}.")
    world.say(f"{hero.id} felt a deep wish for {ACTIONS[params.activity]['desire']}; {ACTIONS[params.activity]['inner']}.")
    world.say(f"The {params.companion} watched kindly, knowing the prize in burlap had come like a small gift from old stories.")
    world.para()
    world.say(f"{hero.id} listened to an inner monologue: “If I choose only myself, {ACTIONS[params.activity]['risk']}.”")
    world.say(f"So {hero.id} touched the {prize.kind} wrapping and chose to seek friendship instead of haste.")
    world.say(f"{hero.id} asked the {params.companion} to {ACTIONS[params.activity]['verb']}.")
    world.para()
    world.say(f"{params.companion.capitalize()} answered with a gentle smile and said, “Then let us {charm.prep}.”")
    world.say(f"When they did, {charm.reveal}, and the burlap prize began its transformation.")
    prize.meters["burlap"] = 0.0
    prize.meters["changed"] = 1.0
    prize.memes["value"] = 2.0
    hero.memes["friendship"] = 2.0
    companion.memes["friendship"] = 2.0
    world.say(f"The rough cloth did not vanish; it became {charm.transforms_to}, as if the nook itself had blessed the choice.")
    world.say(f"{hero.id} smiled, because the prize was still there, but now it lived inside a shared memory.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    activity = f["activity"]
    prize = f["prize"]
    return [
        "Write a mythic story set in a reading nook about a child, a burlap prize, and a kind transformation.",
        f"Tell a short legend where {hero.id} must decide whether to {activity} with a {prize.label}.",
        "Write a gentle story that includes inner monologue, friendship, and a prize wrapped in burlap.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    prize = f["prize"]
    activity = f["activity"]
    charm = f["charm"]
    return [
        QAItem(
            question=f"Where did {hero.id} find the {prize.label}?",
            answer=f"{hero.id} found the {prize.label} in the reading nook, under a quiet lamp.",
        ),
        QAItem(
            question=f"What did {hero.id} think about before choosing what to do?",
            answer=f"{hero.id} thought about the inner monologue that warned {hero.pronoun('possessive')} wish could become selfish.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the {prize.label}?",
            answer=f"The {companion.type} helped {hero.id}, and their friendship made the choice gentle.",
        ),
        QAItem(
            question=f"What changed when they used the {charm.label}?",
            answer=f"The rough burlap prize changed into {charm.transforms_to}, and the story became a shared triumph.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reading nook?",
            answer="A reading nook is a small, quiet place made for books, cushions, and calm thoughts.",
        ),
        QAItem(
            question="What is burlap?",
            answer="Burlap is a rough cloth made from plant fibers. It often feels scratchy and looks earthy.",
        ),
        QAItem(
            question="What does transformation mean in a story?",
            answer="Transformation means something changes into a new form or becomes new in meaning.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care for each other, help each other, and share kindly.",
        ),
    ]


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


ASP_RULES = r"""
hero(H).
prize(P).
activity(A).
companion(C).

burlap_prize(P) :- prize(P), burlap_kind(P).
valid_story(A,P) :- activity(A), burlap_prize(P), has_friendship(A).
transforms(P) :- valid_story(A,P), change_chosen(A).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for aid in ACTIONS:
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("has_friendship", aid))
        lines.append(asp.fact("change_chosen", aid))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("burlap_kind", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(a, p.id) for a in ACTIONS for p in PRIZES.values() if valid_combo(a, p)}
    asp_set = set(asp_valid())
    if python_set == asp_set:
        print(f"OK: clingo gate matches valid_combo() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("python-only:", sorted(python_set - asp_set))
    print("asp-only:", sorted(asp_set - python_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic reading nook storyworld.")
    ap.add_argument("--activity", choices=sorted(ACTIONS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
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
    activity = args.activity or rng.choice(list(ACTIONS))
    prize = args.prize or rng.choice(list(PRIZES))
    if not valid_combo(activity, PRIZES[prize]):
        raise StoryError(reason_invalid(activity, PRIZES[prize]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    companion = args.companion or rng.choice(COMPANIONS)
    return StoryParams(activity=activity, prize=prize, name=name, gender=gender, companion=companion)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
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


CURATED = [
    StoryParams(activity="read", prize="burlap_charm", name="Ari", gender="boy", companion="grandmother"),
    StoryParams(activity="share", prize="burlap_scroll", name="Mina", gender="girl", companion="friend"),
    StoryParams(activity="guard", prize="burlap_charm", name="Rhea", gender="girl", companion="teacher"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
