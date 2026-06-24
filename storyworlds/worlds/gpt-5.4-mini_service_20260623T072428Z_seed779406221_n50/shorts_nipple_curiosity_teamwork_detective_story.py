#!/usr/bin/env python3
"""
storyworlds/worlds/shorts_nipple_curiosity_teamwork_detective_story.py
======================================================================

A tiny detective-story world about curiosity and teamwork.

Seed tale:
---
On a bright afternoon, June and Max were playing detective in the playroom.
June wore blue shorts with a little pocket, and Max carried a toy magnifier.
They wanted to solve the mystery of the missing bottle nipple.

They searched under the couch, behind the curtain, and inside a toy box.
June noticed that the baby bottle was tipped over near the sink.
Max found tiny droplet marks leading to the dog bed.
The puppy had dragged the bottle nipple there and nudged it under a blanket.

June and Max laughed, cleaned up the spill together, and returned the nipple to
the baby bottle. Their curiosity helped them notice the clues, and teamwork
helped them finish the case.

This world keeps that premise small and causal:
curiosity -> clue finding
teamwork -> shared search and cleanup
"""
from __future__ import annotations

import argparse
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
    phrase: str = ""
    role: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the playroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    found_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    question: str
    culprit: str
    trail: list[str] = field(default_factory=list)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def clue_at_risk(mystery: Mystery, clue: Clue) -> bool:
    return mystery.culprit == clue.id or clue.id in mystery.trail


def teamwork_fits(teamwork: bool) -> bool:
    return teamwork


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for m in MYSTERIES:
        for c in CLUES:
            if clue_at_risk(MYSTERIES[m], CLUES[c]):
                out.append((m, c))
    return out


@dataclass
class StoryParams:
    mystery: str
    clue: str
    name1: str
    name2: str
    gender1: str
    gender2: str
    setting: str = "playroom"
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny detective story world.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--gender1", choices=["girl", "boy"])
    ap.add_argument("--gender2", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.mystery and args.clue and (args.mystery, args.clue) not in combos:
        raise StoryError("That clue does not fit the mystery.")
    if not combos:
        raise StoryError("No reasonable detective story can be made.")
    valid = [c for c in combos if (args.mystery is None or c[0] == args.mystery)
             and (args.clue is None or c[1] == args.clue)]
    if not valid:
        raise StoryError("(No valid combination matches the given options.)")
    m_id, c_id = rng.choice(sorted(valid))
    g1 = args.gender1 or rng.choice(["girl", "boy"])
    g2 = args.gender2 or ("boy" if g1 == "girl" else "girl")
    n1 = args.name1 or rng.choice(GIRL_NAMES if g1 == "girl" else BOY_NAMES)
    n2 = args.name2 or rng.choice([n for n in (GIRL_NAMES if g2 == "girl" else BOY_NAMES) if n != n1])
    return StoryParams(mystery=m_id, clue=c_id, name1=n1, name2=n2, gender1=g1, gender2=g2, setting=args.setting or "playroom")


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    a = world.add(Entity(id=params.name1, kind="character", type=params.gender1, role="detective"))
    b = world.add(Entity(id=params.name2, kind="character", type=params.gender2, role="detective"))
    bottle = world.add(Entity(id="bottle", type="thing", label="baby bottle", phrase="the baby bottle"))
    shorts = world.add(Entity(id="shorts", type="thing", label="shorts", phrase="blue shorts"))
    nipple = world.add(Entity(id="nipple", type="thing", label="nipple", phrase="the bottle nipple"))
    pup = world.add(Entity(id="puppy", type="thing", label="puppy", phrase="the puppy"))
    mystery = MYSTERIES[params.mystery]
    clue = CLUES[params.clue]

    a.memes["curiosity"] += 1
    b.memes["teamwork"] += 1
    world.say(
        f"{a.id} and {b.id} were playing detective in {world.setting.place}. "
        f"{a.id} wore blue shorts, and {b.id} carried a toy magnifier."
    )
    world.say(
        f"They wanted to solve the mystery of {mystery.question}."
    )
    world.para()
    a.memes["curiosity"] += 1
    b.memes["curiosity"] += 1
    world.say(
        f"Their curiosity made them search under the couch, behind the curtain, "
        f"and inside the toy box."
    )
    world.say(
        f"{a.id} noticed that {bottle.phrase} was tipped over near the sink."
    )
    world.say(
        f"{b.id} found tiny droplet marks leading to the dog bed."
    )
    world.para()
    b.memes["teamwork"] += 1
    a.memes["teamwork"] += 1
    pup.meters["helpful"] += 1
    world.say(
        f"Together they followed the trail and found {clue.found_text}. "
        f"The puppy had nudged it under a blanket."
    )
    world.say(
        f"{a.id} and {b.id} laughed, cleaned the spill together, and put {nipple.it()} back in {bottle.phrase}."
    )
    world.say(
        f"The case was solved because {a.id}'s curiosity spotted the clues and {b.id}'s teamwork tied them together."
    )
    world.facts.update(
        detective_a=a, detective_b=b, bottle=bottle, shorts=shorts, nipple=nipple,
        clue=clue, mystery=mystery, puppy=pup, solved=True
    )
    return world


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a, b = f["detective_a"], f["detective_b"]
    return [
        f'Write a short detective story for a young child about {a.id}, {b.id}, shorts, and a missing nipple.',
        f"Tell a playful mystery where {a.id} and {b.id} use curiosity and teamwork to solve a clue trail.",
        f'Write a gentle detective story that includes the words "shorts" and "nipple" and ends with the case solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["detective_a"], f["detective_b"]
    mystery, clue = f["mystery"], f["clue"]
    return [
        QAItem(question=f"What kind of game were {a.id} and {b.id} playing?",
               answer=f"They were playing detective in {world.setting.place} and looking for clues."),
        QAItem(question=f"What did {a.id} wear in the story?",
               answer=f"{a.id} wore blue shorts while helping solve the mystery."),
        QAItem(question=f"What did curiosity help them notice?",
               answer=f"Curiosity helped them notice the tipped-over baby bottle and the clue trail."),
        QAItem(question=f"How did teamwork help?",
               answer=f"Teamwork helped them follow the clues together, clean up, and solve the case."),
        QAItem(question=f"What happened to the nipple?",
               answer=f"They found the bottle nipple and put it back in the baby bottle."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is curiosity?",
               answer="Curiosity is the feeling that makes you want to look, ask, and learn about something new."),
        QAItem(question="What is teamwork?",
               answer="Teamwork means people help each other and work together to finish a job."),
        QAItem(question="What is a detective?",
               answer="A detective is someone who looks for clues to solve a mystery."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        out.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    return "\n".join(out)


SETTINGS = {
    "playroom": Setting(place="the playroom", affords={"detective"}),
    "kitchen": Setting(place="the kitchen", affords={"detective"}),
    "hall": Setting(place="the hall", affords={"detective"}),
}

MYSTERIES = {
    "missing_nipple": Mystery(
        id="missing_nipple",
        question="the missing bottle nipple",
        culprit="nipple",
        trail=["bottle", "sink", "dogbed", "nipple"],
    ),
    "muddy_shorts": Mystery(
        id="muddy_shorts",
        question="the muddy shorts",
        culprit="shorts",
        trail=["couch", "hall", "shorts"],
    ),
}

CLUES = {
    "nipple": Clue(
        id="nipple",
        label="nipple",
        phrase="the bottle nipple",
        found_text="the bottle nipple tucked under a blanket",
        tags={"nipple"},
    ),
    "shorts": Clue(
        id="shorts",
        label="shorts",
        phrase="the shorts",
        found_text="the shorts hanging on a chair",
        tags={"shorts"},
    ),
}

GIRL_NAMES = ["June", "Mia", "Lena", "Tia", "Ruby"]
BOY_NAMES = ["Max", "Leo", "Sam", "Ned", "Owen"]


ASP_RULES = r"""
% A clue is relevant when it is part of the mystery trail.
relevant(C, M) :- clue(C), mystery(M), trail(M, C).

% A case is valid when the clue fits the mystery.
valid(M, C) :- mystery(M), clue(C), relevant(C, M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("trail", mid, m.culprit))
        for t in m.trail:
            lines.append(asp.fact("trail", mid, t))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    return 1


def valid_combos() -> list[tuple[str, str]]:
    return [(m, c) for m in MYSTERIES for c in CLUES if clue_at_risk(MYSTERIES[m], CLUES[c])]


def explain_rejection() -> str:
    return "(No story: the clue does not fit this mystery.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/2."))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(mystery=m, clue=c, name1="June", name2="Max", gender1="girl", gender2="boy")) for m, c in valid_combos()]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        print(s.story)
        if args.trace and s.world:
            print(dump_trace(s.world))
        if args.qa:
            print()
            print(format_qa(s))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
