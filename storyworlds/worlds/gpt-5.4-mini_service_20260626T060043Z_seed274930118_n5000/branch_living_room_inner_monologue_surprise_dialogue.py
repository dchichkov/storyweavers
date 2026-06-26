#!/usr/bin/env python3
"""
storyworlds/worlds/branch_living_room_inner_monologue_surprise_dialogue.py
===========================================================================

A small mythic living-room story world built from the seed word "branch".

Premise:
- A child brings a branch into the living room and treats it like a relic or staff.
- The branch threatens a cherished object in the room.
- The child has an inner monologue about whether to keep it.
- A surprise reveals the branch is not just a stick, and dialogue turns worry into wonder.
- The ending proves the change in the room and in the child's feeling.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager import of shared results containers
- lazy import of storyworlds.asp inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
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
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class LivingRoom:
    place: str = "the living room"
    affords: set[str] = field(default_factory=lambda: {"wave", "whittle", "admire"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    danger: str
    surprise: str
    keyword: str = "branch"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str


@dataclass
class Remedy:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: LivingRoom) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.turn: str = ""

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.turn = self.turn
        clone.paragraphs = [[]]
        return clone


def _r_danger(world: World) -> list[str]:
    out: list[str] = []
    hero = next((e for e in world.characters() if e.kind == "character"), None)
    branch = world.entities.get("branch")
    prize = world.entities.get("prize")
    if not hero or not branch or not prize:
        return out
    if hero.meters.get("swing", 0.0) < THRESHOLD:
        return out
    sig = ("danger",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if prize.region == "table":
        prize.meters["risk"] = 1.0
        out.append(f"The branch swept close to the table, and {prize.label} trembled.")
    elif prize.region == "floor":
        prize.meters["risk"] = 1.0
        out.append(f"The branch dipped low, and {prize.label} nearly took a knock.")
    return out


def _r_surprise(world: World) -> list[str]:
    hero = next((e for e in world.characters() if e.kind == "character"), None)
    branch = world.entities.get("branch")
    if not hero or not branch:
        return []
    if hero.memes.get("wonder", 0.0) < THRESHOLD:
        return []
    sig = ("surprise",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    branch.meters["bud"] = 1.0
    return [f"Inside the crook of the branch, a tiny green bud was waking up."]


def _r_remedy(world: World) -> list[str]:
    hero = next((e for e in world.characters() if e.kind == "character"), None)
    prize = world.entities.get("prize")
    if not hero or not prize:
        return []
    if hero.memes.get("calm", 0.0) < THRESHOLD:
        return []
    sig = ("remedy",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["peace"] = 1.0
    prize.meters["risk"] = 0.0
    return ["__remedy__"]


CAUSAL_RULES = [_r_danger, _r_surprise, _r_remedy]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(s for s in out if s != "__remedy__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def visible_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in {"table", "floor"} and activity.id == "wave"


def select_remedy(activity: Activity, prize: Prize) -> Optional[Remedy]:
    if prize.region == "table":
        return REMEDIES["basket"]
    if prize.region == "floor":
        return REMEDIES["vase"]
    return None


SETTINGS = {"living_room": LivingRoom()}

ACTIVITIES = {
    "wave": Activity(
        id="wave",
        verb="wave the branch like a staff",
        gerund="waving the branch like a staff",
        rush="lift the branch high and sweep it around",
        danger="knock over a treasured object",
        surprise="a bud begins to open",
        tags={"branch", "wood", "wonder"},
    ),
    "whittle": Activity(
        id="whittle",
        verb="whittle the branch into a pointer",
        gerund="whittling the branch into a pointer",
        rush="scrape at the bark too hard",
        danger="scatter bark on the rug",
        surprise="a pale ribbon of bark curls free",
        tags={"branch", "wood"},
    ),
    "admire": Activity(
        id="admire",
        verb="admire the branch like a relic",
        gerund="admiring the branch like a relic",
        rush="carry it carefully to the window",
        danger="none",
        surprise="it smells of rain and leaf-sap",
        tags={"branch", "wonder"},
    ),
}

PRIZES = {
    "lamp": Prize(label="lamp", phrase="a brass lamp", type="lamp", region="table"),
    "vase": Prize(label="vase", phrase="a blue vase", type="vase", region="table"),
    "book": Prize(label="book", phrase="a storybook with gold corners", type="book", region="floor"),
    "carpet": Prize(label="carpet", phrase="a bright woven carpet", type="carpet", region="floor"),
}

REMEDIES = {
    "basket": Remedy(
        id="basket",
        label="a woven basket",
        prep="place the branch in a woven basket near the hearth",
        tail="set it in a woven basket beside the warm lamp",
        protects={"table"},
    ),
    "vase": Remedy(
        id="vase",
        label="a tall vase",
        prep="set the branch in a tall vase by the window",
        tail="rest it in a tall vase so it could stand like a spear of the woods",
        protects={"floor"},
    ),
}

GIRL_NAMES = ["Mira", "Luna", "Nia", "Iris", "Sera"]
BOY_NAMES = ["Arin", "Eli", "Pax", "Oren", "Tomas"]
TRAITS = ["curious", "bold", "gentle", "thoughtful", "spirited"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_story(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    branch = world.add(Entity(id="branch", type="branch", label="branch", phrase="a branch from an old tree"))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].type, label=PRIZES[params.prize].label,
                             phrase=PRIZES[params.prize].phrase, region=PRIZES[params.prize].region,
                             caretaker=parent.id, owner=parent.id))

    act = ACTIVITIES[params.activity]

    world.say(f"{hero.id} was a little {params.trait} {params.gender} who had brought home a branch like a forest token.")
    world.say(f"To {hero.id}, the branch was not rubbish at all; it was a staff for an old, bright quest.")
    world.say(f"Near the window in {world.setting.place}, {hero.id} loved to {act.gerund}, and {branch.label} felt almost alive.")

    world.para()
    world.say(f"That morning, {hero.id} wanted to {act.verb}.")
    hero.meters["swing"] = 1.0
    hero.memes["desire"] = 1.0
    world.say(f"But the living room held {prize.phrase}, and {params.parent} worried the branch could {act.danger}.")
    if visible_risk(act, PRIZES[params.prize]):
        world.say(f'"Please be careful," {parent.id} said. "That {prize.label} must stay safe."')

    world.para()
    world.say(f"{hero.id} looked down at the branch and thought, " + '"' +
              f"If I put it away, my quest will end before it begins." + '"')
    hero.memes["wonder"] = 1.0
    world.say(f"Then {hero.id} heard a soft crackle from the crook of the wood.")
    propagate(world, narrate=True)

    world.say(f'"Look!" {hero.id} whispered. "It has a bud."')
    world.say(f'"A bud?" {params.parent} said, coming closer. "Then this is not only a branch. It still remembers the tree."')

    world.para()
    hero.memes["calm"] = 1.0
    remedy = select_remedy(act, PRIZES[params.prize])
    if remedy:
        world.say(f"{hero.id} nodded, and the two of them made a gentler plan.")
        world.say(f'{params.parent.capitalize()} said, "How about we {remedy.prep}?"')
        world.say(f'{hero.id} answered, "Yes. Then it can sleep in the room without hurting anything."')
        world.say(f"They {remedy.tail}.")
        world.say(f"After that, {hero.id} could still {act.gerund}, but now the branch stood quietly as a small green promise.")
    else:
        world.say(f"Together they chose to carry the branch to a safe corner, where it could wait without causing trouble.")
        world.say(f"At the end, the room was calm, and the branch rested like a quiet relic by the window.")

    hero.memes["peace"] = 1.0
    world.facts.update(hero=hero, parent=parent, branch=branch, prize=prize, activity=act, remedy=remedy, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    prize = f["prize"]
    return [
        f'Write a short mythic story for a child about a branch in the living room and include the word "branch".',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but must protect {prize.phrase}.",
        f"Write a story with inner monologue, surprise, and dialogue that ends with a branch becoming a small wonder.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    prize = f["prize"]
    act = f["activity"]
    remedy = f["remedy"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the branch in the living room?",
            answer=f"{hero.id} wanted to {act.verb}. To {hero.id}, the branch felt like a staff from a myth.",
        ),
        QAItem(
            question=f"Why was {parent.id} worried about the branch?",
            answer=f"{parent.id} worried because the branch could {act.danger}, and the {prize.label} needed to stay safe.",
        ),
        QAItem(
            question=f"What surprise changed how {hero.id} felt about the branch?",
            answer="A tiny green bud woke up in the crook of the branch, so it seemed like the tree was still speaking through it.",
        ),
        QAItem(
            question=f"What did they do so the branch would not cause trouble?",
            answer=f"They used {remedy.label} to give the branch a safe place, and then the room stayed calm.",
        ),
    ]


KNOWLEDGE = {
    "branch": [("What is a branch?", "A branch is a woody part that grows out of a tree and carries leaves, buds, or fruit.")],
    "bud": [("What is a bud?", "A bud is a small part on a plant that can grow into a leaf, flower, or new shoot.")],
    "vase": [("What is a vase for?", "A vase holds flowers or tall stems so they can stand safely indoors.")],
    "basket": [("What is a basket for?", "A basket is used to carry or hold things in one place.")],
    "wood": [("What is wood?", "Wood is the hard material that makes up trees and many sticks, branches, and boards.")],
    "wonder": [("What does it mean to wonder?", "To wonder means to feel curious about something and think about it with surprise.")],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("branch")
    if world.facts.get("remedy"):
        tags.add(world.facts["remedy"].id)
    out: list[QAItem] = []
    for tag in ["branch", "bud", "wood", "basket", "vase", "wonder"]:
        if tag in tags or tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==", ""]
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
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="living_room", activity="wave", prize="lamp", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="living_room", activity="wave", prize="vase", name="Arin", gender="boy", parent="father", trait="bold"),
    StoryParams(place="living_room", activity="whittle", prize="book", name="Luna", gender="girl", parent="mother", trait="thoughtful"),
    StoryParams(place="living_room", activity="admire", prize="carpet", name="Oren", gender="boy", parent="father", trait="gentle"),
]


ASP_RULES = r"""
visible_risk(A,P) :- activity(A), prize(P), risk_region(P,R), danger_region(A,R).
needs_remedy(A,P) :- visible_risk(A,P), has_remedy(P).
valid_story(Place,A,P) :- setting(Place), activity(A), prize(P), visible_risk(A,P), needs_remedy(A,P).

remedy_ok(P,R) :- prize(P), risk_region(P,R), remedy_for(P,Rem).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
        if aid == "wave":
            lines.append(asp.fact("danger_region", aid, "table"))
            lines.append(asp.fact("danger_region", aid, "floor"))
        elif aid == "whittle":
            lines.append(asp.fact("danger_region", aid, "floor"))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("risk_region", pid, p.region))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy_for", rid, rid))
        lines.append(asp.fact("has_remedy", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    python_set = {( "living_room", a, p) for a in ACTIVITIES for p in PRIZES if visible_risk(ACTIVITIES[a], PRIZES[p]) and select_remedy(ACTIVITIES[a], PRIZES[p])}
    clingo_set = set(asp_valid_stories())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python gate ({len(clingo_set)} valid stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic living-room story world about a branch.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = []
    for a in ACTIVITIES:
        for p in PRIZES:
            if visible_risk(ACTIVITIES[a], PRIZES[p]) and select_remedy(ACTIVITIES[a], PRIZES[p]):
                combos.append(("living_room", a, p))
    if args.activity and args.prize:
        if not visible_risk(ACTIVITIES[args.activity], PRIZES[args.prize]) or not select_remedy(ACTIVITIES[args.activity], PRIZES[args.prize]):
            raise StoryError("No story: that branch action would not create a real problem-and-fix in the living room.")
    combos = [c for c in combos if (args.activity is None or c[1] == args.activity) and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    _, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place="living_room", activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_story(World(SETTINGS[params.place]), params)
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for c in combos:
            print("  ", c)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} with a branch in the living room"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
