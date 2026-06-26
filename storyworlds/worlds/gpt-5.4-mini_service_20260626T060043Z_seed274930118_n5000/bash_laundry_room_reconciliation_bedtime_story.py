#!/usr/bin/env python3
"""
A small bedtime-story world in a laundry room: a bash goes wrong, then two
characters reconcile and calm the room back down.

The world premise:
- A child loves to bash a soft laundry basket like a drum.
- A parent worries because the noise scatters folded clothes and wakes a tired
  little sibling nearby.
- A gentle apology and a helpful repair routine lead to reconciliation.

This file is self-contained and follows the storyworld contract:
- typed entities with meters and memes
- causal world state drives prose
- explicit invalid choices raise StoryError
- inline ASP twin and Python reasonableness gate
- generation + QA + emit + CLI
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
# World data
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("noise", "mess", "tidy", "tired", "workload"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "shame", "love", "hurt", "reconcile"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the laundry room"
    indoor: bool = True


@dataclass
class Act:
    id: str
    verb: str
    gerund: str
    rush: str
    keyword: str = "bash"
    mess: str = "noise"


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    sibling: str
    act: str = "bash"
    seed: Optional[int] = None


NAMES = {
    "girl": ["Mia", "Lina", "Nora", "Ivy", "June"],
    "boy": ["Leo", "Owen", "Milo", "Theo", "Finn"],
}
SIBLINGS = {
    "girl": ["baby sister", "little sister"],
    "boy": ["baby brother", "little brother"],
}
PARENT_TYPES = ["mother", "father"]


SETTING = Setting(place="the laundry room", indoor=True)
ACT = Act(
    id="bash",
    verb="bash the basket",
    gerund="bashing the basket",
    rush="rush to bash the basket again",
    keyword="bash",
    mess="noise",
)


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_story(params: StoryParams) -> bool:
    return params.act == "bash" and params.parent in PARENT_TYPES and params.gender in {"girl", "boy"}


def explain_rejection(params: StoryParams) -> str:
    return "This world only tells a bedtime-style reconciliation story about a bash in the laundry room."


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"noise": 0.0, "mess": 0.0, "tidy": 0.0, "tired": 0.0, "workload": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "shame": 0.0, "love": 0.0, "hurt": 0.0, "reconcile": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the parent",
        meters={"noise": 0.0, "mess": 0.0, "tidy": 0.0, "tired": 0.0, "workload": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "shame": 0.0, "love": 0.0, "hurt": 0.0, "reconcile": 0.0},
    ))
    sibling = world.add(Entity(
        id="Sibling",
        kind="character",
        type="sister" if params.gender == "boy" else "brother",
        label=params.sibling,
        meters={"noise": 0.0, "mess": 0.0, "tidy": 0.0, "tired": 1.0, "workload": 0.0},
        memes={"joy": 0.0, "worry": 0.0, "shame": 0.0, "love": 0.0, "hurt": 0.0, "reconcile": 0.0},
    ))
    basket = world.add(Entity(
        id="Basket",
        kind="thing",
        type="basket",
        label="laundry basket",
        phrase="a wicker laundry basket",
        owner=params.name,
    ))
    blanket = world.add(Entity(
        id="Blanket",
        kind="thing",
        type="blanket",
        label="blanket",
        phrase="a folded blanket",
        caretaker=parent.id,
    ))

    # Setup
    world.say(f"{child.id} was a sleepy little {params.gender} who loved quiet nights in {world.setting.place}.")
    world.say(f"At bedtime, {child.id} liked {ACT.gerund} because the basket made a soft thump that felt like a drum.")
    world.say(f"{parent.pronoun('possessive').capitalize()} {parent.label} had folded the clothes carefully, and {sibling.label} was nearly asleep.")

    # Conflict
    world.para()
    child.meters["noise"] += 1
    child.meters["mess"] += 1
    child.memes["joy"] += 1
    sibling.memes["hurt"] += 1
    sibling.meters["tired"] += 1
    parent.memes["worry"] += 1
    blanket.meters["tidy"] += 1
    world.say(f"Then {child.id} gave the basket one loud bash, and the room shook with a happy boom.")
    world.say(f"The sound made {sibling.label} blink awake, and one folded blanket slipped off the stack.")
    world.say(f"{parent.pronoun().capitalize()} looked over with a soft but worried face. \"That was too loud for bedtime,\" {parent.pronoun('subject')} said.")

    # Turn toward reconciliation
    world.para()
    child.memes["shame"] += 1
    child.memes["worry"] += 1
    child.say = None  # harmless placeholder; no effect
    world.say(f"{child.id} stopped right away. The room felt small and sorry all at once.")
    world.say(f"{child.id} whispered, \"I'm sorry. I can fix it.\"")
    parent.memes["love"] += 1
    world.say(f"{parent.pronoun().capitalize()} sat down beside {child.id}. \"Thank you for stopping,\" {parent.pronoun('subject')} said. \"Let's make it calm again.\"")

    # Reconciliation and repair
    child.meters["tidy"] += 1
    parent.meters["workload"] += 1
    sibling.memes["hurt"] = 0.0
    child.memes["shame"] = 0.0
    child.memes["reconcile"] += 1
    parent.memes["reconcile"] += 1
    child.memes["love"] += 1
    child.meters["noise"] = 0.0
    world.say(f"Together they picked up the blanket, stacked the clothes again, and tucked the basket back in its corner.")
    world.say(f"{child.id} gave the basket just one tiny tap this time, as gentle as a mouse's paw.")
    world.say(f"{sibling.label} smiled sleepily and rolled back under the covers, and the laundry room grew quiet and warm.")

    world.facts.update(
        child=child,
        parent=parent,
        sibling=sibling,
        basket=basket,
        blanket=blanket,
        act=ACT,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        'Write a bedtime story about a child who wants to bash a laundry basket in the laundry room, then learns to apologize.',
        f"Tell a gentle reconciliation story where {child.id} makes a loud bash, {parent.label} worries about bedtime, and they fix the mess together.",
        f'Write a child-facing story that includes the word "{ACT.keyword}" and ends with a peaceful bedtime feeling.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    sibling = f["sibling"]
    return [
        QAItem(
            question=f"Why did {child.id}'s bash upset {parent.label}?",
            answer=f"It was too loud for bedtime, and it woke {sibling.label} and knocked the calm clothes stack out of place.",
        ),
        QAItem(
            question=f"What did {child.id} say after noticing the trouble in {world.setting.place}?",
            answer=f"{child.id} stopped, felt sorry, and said, \"I'm sorry. I can fix it.\"",
        ),
        QAItem(
            question=f"How did {child.id} and {parent.label} make things better?",
            answer="They picked up the blanket, stacked the clothes again, and made the room quiet and cozy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a laundry room for?",
            answer="A laundry room is a room where people wash, dry, fold, and sort clothes.",
        ),
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset, say sorry if needed, and come back to being kind with each other.",
        ),
        QAItem(
            question="Why should bedtime be quiet?",
            answer="Bedtime should be quiet so sleepy children can rest and their bodies can get ready for sleep.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
child_likes_bash.
problem(noise) :- child_likes_bash.
reconciliation :- apology, repair, calm_return.

valid_story(act_bash, setting_laundry_room, bedtime_style).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    return "\n".join([
        asp.fact("setting", "laundry_room"),
        asp.fact("style", "bedtime"),
        asp.fact("act", "bash"),
        asp.fact("feature", "reconciliation"),
        asp.fact("keyword", "bash"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("act_bash", "setting_laundry_room", "bedtime_style")}
    cl = set(asp_valid())
    if py == cl:
        print("OK: ASP parity matches the Python gate.")
        return 0
    print("MISMATCH:")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Laundry-room bedtime reconciliation story world.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENT_TYPES)
    ap.add_argument("--sibling", choices=["baby sister", "little sister", "baby brother", "little brother"])
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.sibling:
        sibling = args.sibling
    else:
        sibling = rng.choice(SIBLINGS[gender])
    name = args.name or rng.choice(NAMES[gender])
    parent = args.parent or rng.choice(PARENT_TYPES)
    params = StoryParams(name=name, gender=gender, parent=parent, sibling=sibling, act="bash")
    if not valid_story(params):
        raise StoryError(explain_rejection(params))
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.kind == "character":
            bits.append(f"type={e.type}")
        lines.append(f"{e.id}: " + ", ".join(bits))
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_story/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(name="Mia", gender="girl", parent="mother", sibling="little sister", act="bash"),
            StoryParams(name="Leo", gender="boy", parent="father", sibling="baby brother", act="bash"),
            StoryParams(name="Nora", gender="girl", parent="father", sibling="baby sister", act="bash"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
