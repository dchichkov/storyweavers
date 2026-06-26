#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/elect_hen_reconciliation_rhyme_superhero_story.py
=============================================================================================================================

A small superhero story world about an election, a proud hen, reconciliation,
and a rhyme that helps everyone choose a leader together.

Premise:
- A tiny superhero squad is choosing a new captain.
- A brave hen wants to be elected too.
- The team nearly splits into two camps.
- A rhyme helps them reconcile and elect a leader who keeps everyone included.

This world is intentionally small and constraint-checked:
- If the candidate cannot reasonably be elected, StoryError is raised.
- The story is driven by state changes in meters and memes.
- An inline ASP twin mirrors the Python reasonableness gate.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# Entity model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    leader: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "hen"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def maybe_plural(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Chamber:
    name: str = "the hall"
    place: str = "the bright hall"
    crowd_size: int = 0
    banners: bool = True


@dataclass
class Contestant:
    id: str
    label: str
    phrase: str
    type: str
    kind: str = "character"
    can_lead: bool = True
    can_rhyme: bool = False
    can_reconcile: bool = False
    bright: bool = True
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    candidate: str
    challenger: str
    setting: str
    seed: Optional[int] = None


class World:
    def __init__(self, chamber: Chamber):
        self.chamber = chamber
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy
        w = World(self.chamber)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
CHAMBERS = {
    "hall": Chamber(name="hall", place="the bright hall", crowd_size=8, banners=True),
    "rooftop": Chamber(name="rooftop", place="the windy rooftop", crowd_size=5, banners=True),
    "courtyard": Chamber(name="courtyard", place="the sunny courtyard", crowd_size=10, banners=False),
}

CANDIDATES = {
    "star": Contestant(
        id="Starling",
        label="Starling",
        phrase="a starry superhero with a red cape",
        type="girl",
        can_lead=True,
        can_rhyme=True,
        can_reconcile=True,
    ),
    "shield": Contestant(
        id="Shield",
        label="Shield",
        phrase="a careful superhero with a round shield",
        type="boy",
        can_lead=True,
        can_rhyme=False,
        can_reconcile=True,
    ),
    "hen": Contestant(
        id="Henrietta",
        label="Henrietta the hen",
        phrase="a brave hen with a feathered mask",
        type="hen",
        can_lead=True,
        can_rhyme=True,
        can_reconcile=True,
    ),
}

# Purposeful seeded words: elect, hen.
TOPICS = {"elect", "hen", "reconciliation", "rhyme", "superhero"}

# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
candidate(C) :- can_lead(C).
electable(C) :- candidate(C), has_rhyme(C).
reconcile(C) :- candidate(C), can_reconcile(C).
valid_story(Cand, Chall, Place) :- candidate(Cand), candidate(Chall), Cand != Chall, setting(Place),
                                   electable(Cand), reconcile(Cand), has_hen(Cand), has_hen(Chall).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, c in CANDIDATES.items():
        lines.append(asp.fact("candidate", cid))
        if c.can_lead:
            lines.append(asp.fact("can_lead", cid))
        if c.can_rhyme:
            lines.append(asp.fact("has_rhyme", cid))
        if c.can_reconcile:
            lines.append(asp.fact("can_reconcile", cid))
        if "hen" in c.phrase.lower() or cid.lower().startswith("hen"):
            lines.append(asp.fact("has_hen", cid))
    for sid in CHAMBERS:
        lines.append(asp.fact("setting", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Rules / simulation
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


def _is_hen(entity: Entity) -> bool:
    return entity.type == "hen"


def can_elect(candidate: Contestant) -> bool:
    return candidate.can_lead and candidate.can_rhyme and candidate.can_reconcile


def valid_pair(candidate: Contestant, challenger: Contestant) -> bool:
    return candidate.id != challenger.id and candidate.can_lead and challenger.can_lead


def resolve_reconciliation(world: World, leader: Entity, challenger: Entity) -> None:
    leader.memes["hope"] = leader.memes.get("hope", 0.0) + 1
    challenger.memes["hope"] = challenger.memes.get("hope", 0.0) + 1
    leader.memes["conflict"] = 0.0
    challenger.memes["conflict"] = 0.0


def rhyme_line(leader: Entity, challenger: Entity) -> str:
    if _is_hen(leader):
        return "Hen and hero, side by side, can share the job and still take pride."
    return "Cape and feather, bright and true, a team can choose a path for two."


def tell(params: StoryParams) -> World:
    chamber = CHAMBERS[params.setting]
    world = World(chamber)
    cand_cfg = CANDIDATES[params.candidate]
    chall_cfg = CANDIDATES[params.challenger]

    if not valid_pair(cand_cfg, chall_cfg):
        raise StoryError("The chosen candidates cannot meaningfully face each other in this election.")
    if not can_elect(cand_cfg):
        raise StoryError(f"{cand_cfg.label} is not a reasonable elected hero for this story.")
    if not _is_hen(cand_cfg) and not _is_hen(chall_cfg):
        raise StoryError("This world needs a hen somewhere in the election to match the seed.")

    candidate = world.add(Entity(
        id=cand_cfg.id,
        kind="character",
        type=cand_cfg.type,
        label=cand_cfg.label,
        phrase=cand_cfg.phrase,
        leader=False,
    ))
    challenger = world.add(Entity(
        id=chall_cfg.id,
        kind="character",
        type=chall_cfg.type,
        label=chall_cfg.label,
        phrase=chall_cfg.phrase,
        leader=False,
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="group",
        type="crowd",
        label="the little crowd",
        plural=True,
    ))

    # Setup
    world.say(f"In {chamber.place}, the little superhero crowd gathered to elect a new captain.")
    world.say(f"{candidate.id} arrived wearing {candidate.phrase}, and {challenger.id} stepped in with {challenger.phrase}.")
    world.say(f"Everyone liked the idea of a strong leader, but everyone liked a different one.")

    # Conflict
    world.para()
    candidate.memes["pride"] = candidate.memes.get("pride", 0.0) + 1
    challenger.memes["pride"] = challenger.memes.get("pride", 0.0) + 1
    candidate.memes["conflict"] = 1.0
    challenger.memes["conflict"] = 1.0
    world.say(f"The room buzzed as the vote split in two.")
    if _is_hen(candidate):
        world.say(f"Henrietta puffed up her feathers and clucked, 'I can lead the flock of heroes!'")
    else:
        world.say(f"{candidate.id} pointed to the banners and said a captain must be calm, fast, and fair.")
    world.say(f"{challenger.id} frowned, because they thought their own plan was better.")

    # Turn
    world.para()
    leader = candidate
    if candidate.can_rhyme:
        world.say(f"Then {candidate.id} tapped the floor and sang a tiny rhyme: '{rhyme_line(candidate, challenger)}'")
    else:
        world.say(f"Then {challenger.id} whispered a rhyme, and the words softened the room.")
        leader = challenger

    resolve_reconciliation(world, candidate, challenger)
    world.say("The angry voices quieted. The heroes looked at one another and remembered they were on the same side.")

    # Resolution
    world.para()
    candidate.leader = True
    challenger.leader = False
    crowd.meters["happy"] = crowd.meters.get("happy", 0.0) + 1
    world.say(f"They reconciled the two plans into one: a captain who would listen first and act fast.")
    world.say(f"The crowd elected {candidate.id}, and even {challenger.id} nodded along.")
    if _is_hen(candidate):
        world.say("Henrietta stood taller than ever, her feathers neat and her cape bright, as the heroes cheered.")
    else:
        world.say(f"{candidate.id} raised a hand, and the hall rang with one last rhyme and a happy cheer.")

    world.facts = {
        "candidate": candidate,
        "challenger": challenger,
        "leader": candidate,
        "chamber": chamber,
        "rhyme": True,
        "reconciliation": True,
        "hen": _is_hen(candidate) or _is_hen(challenger),
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cand: Entity = f["candidate"]
    chall: Entity = f["challenger"]
    return [
        "Write a short superhero story about an election, a hen, and a rhyme that helps everyone get along.",
        f"Tell a child-friendly superhero tale where {cand.id} and {chall.id} both want to be elected, but reconciliation changes the ending.",
        f"Write a story that includes the words elect, hen, reconciliation, and rhyme, and ends with a happy vote.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cand: Entity = f["candidate"]
    chall: Entity = f["challenger"]
    chamber: Chamber = f["chamber"]
    qa = [
        QAItem(
            question=f"Where did the heroes elect a new captain?",
            answer=f"They held the election in {chamber.place}, where the superhero crowd could see both candidates clearly.",
        ),
        QAItem(
            question=f"Who was elected captain in the end?",
            answer=f"{cand.id} was elected captain after the group found a calmer way to choose.",
        ),
        QAItem(
            question=f"What helped the heroes reconcile their disagreement?",
            answer=f"A small rhyme helped the room settle down, so the heroes could reconcile and make one shared decision.",
        ),
    ]
    if _is_hen(cand) or _is_hen(chall):
        hen_name = cand.id if _is_hen(cand) else chall.id
        qa.append(QAItem(
            question=f"Why did the hen matter in the election?",
            answer=f"The hen, {hen_name}, gave the story its brave and funny superhero feeling, and the others listened to her too.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does elect mean?",
            answer="To elect someone means to choose that person for a job by voting.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace after an argument so people can work together again.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pair of words or lines that sound alike at the end, like 'light' and 'night'.",
        ),
        QAItem(
            question="What is a hen?",
            answer="A hen is a grown female chicken.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP verification
# ---------------------------------------------------------------------------
def asp_verify() -> int:
    import asp
    py = {
        (p.candidate, p.challenger, p.setting)
        for p in (
            StoryParams(candidate=c, challenger=d, setting=s)
            for c in CANDIDATES
            for d in CANDIDATES
            for s in CHAMBERS
        )
        if can_elect(CANDIDATES[p.candidate]) if False else True
    }
    # Above dummy comprehension avoided; compute explicitly below.
    py = set()
    for cand in CANDIDATES.values():
        for chall in CANDIDATES.values():
            for setting in CHAMBERS:
                if valid_pair(cand, chall) and can_elect(cand) and (_is_hen(cand) or _is_hen(chall)):
                    py.add((cand.id, chall.id, setting))
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in Python:", sorted(py - cl))
    print(" only in ASP:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Storyworld interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero election story world with a hen, reconciliation, and rhyme.")
    ap.add_argument("--candidate", choices=CANDIDATES)
    ap.add_argument("--challenger", choices=CANDIDATES)
    ap.add_argument("--setting", choices=CHAMBERS)
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
    candidate = args.candidate or rng.choice(list(CANDIDATES))
    challenger = args.challenger or rng.choice([k for k in CANDIDATES if k != candidate])
    setting = args.setting or rng.choice(list(CHAMBERS))
    cand = CANDIDATES[candidate]
    chall = CANDIDATES[challenger]
    if not valid_pair(cand, chall):
        raise StoryError("The chosen candidates are not a valid pair for this election story.")
    if not can_elect(cand):
        raise StoryError(f"{cand.label} cannot be elected in this story because the candidate lacks the right qualities.")
    if not (_is_hen(cand) or _is_hen(chall)):
        raise StoryError("This story needs a hen to satisfy the seed and theme.")
    return StoryParams(candidate=candidate, challenger=challenger, setting=setting)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def curated() -> list[StoryParams]:
    return [
        StoryParams(candidate="hen", challenger="star", setting="hall"),
        StoryParams(candidate="star", challenger="hen", setting="rooftop"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible stories:")
        for item in stories:
            print("  ", item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
