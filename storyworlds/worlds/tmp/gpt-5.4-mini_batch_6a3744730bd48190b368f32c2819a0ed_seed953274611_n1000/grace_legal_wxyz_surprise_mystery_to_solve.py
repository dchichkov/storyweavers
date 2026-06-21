#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/grace_legal_wxyz_surprise_mystery_to_solve.py
==============================================================================

A small heartwarming storyworld about a child, a lost legal envelope, a surprise,
and a gentle mystery to solve.

Premise
-------
Grace helps at a tiny community office where children and grown-ups keep papers
safe. One day, an important legal envelope disappears. The mystery turns into a
kind search, and the surprise is that the missing paper was not lost at all: it
was protecting someone else. The ending should feel warm, safe, and earned.

Seed words to include in the story:
- grace
- legal
- wxyz

Features:
- Surprise
- Mystery to Solve

Style:
- Heartwarming
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
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    indoor: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Paper:
    id: str
    label: str
    phrase: str
    legal: bool = True
    sealed: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Surprise:
    id: str
    label: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    sense: int
    solve_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    envelope = world.entities.get("envelope")
    child = world.entities.get("grace")
    if not envelope or not child:
        return out
    if envelope.meters["missing"] >= THRESHOLD and ("worry", "grace") not in world.fired:
        world.fired.add(("worry", "grace"))
        child.memes["worry"] += 1
        out.append("Grace felt a little worried.")
    return out


def _r_lookcloser(world: World) -> list[str]:
    out: list[str] = []
    envelope = world.entities.get("envelope")
    helper = world.entities.get("sam")
    if not envelope or not helper:
        return out
    if envelope.meters["hidden"] >= THRESHOLD and ("look", "sam") not in world.fired:
        world.fired.add(("look", "sam"))
        helper.memes["curiosity"] += 1
        out.append("Sam noticed a tiny corner peeking out.")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("lookcloser", _r_lookcloser)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for paper_id, paper in PAPERS.items():
            for surprise_id, surprise in SURPRISES.items():
                if place.indoor and paper.legal and surprise_id in {"gift_card", "thank_you_note"}:
                    combos.append((place_id, paper_id, surprise_id))
    return combos


@dataclass
class StoryParams:
    place: str
    paper: str
    surprise: str
    child_name: str
    helper_name: str
    seed: Optional[int] = None


PLACES = {
    "office": Place(id="office", label="the community office", indoor=True, tags={"legal"}),
    "hall": Place(id="hall", label="the town hall", indoor=True, tags={"legal"}),
    "library": Place(id="library", label="the library desk", indoor=True, tags={"legal"}),
}

PAPERS = {
    "envelope": Paper(id="envelope", label="legal envelope", phrase="a sealed legal envelope", legal=True, sealed=True, tags={"legal"}),
    "form": Paper(id="form", label="legal form", phrase="a legal form in a yellow folder", legal=True, sealed=False, tags={"legal"}),
}

SURPRISES = {
    "gift_card": Surprise(id="gift_card", label="a gift card", reveal="it was a thank-you from the neighbors", tags={"surprise"}),
    "thank_you_note": Surprise(id="thank_you_note", label="a thank-you note", reveal="it was a thank-you note tucked behind the papers", tags={"surprise"}),
    "cookies": Surprise(id="cookies", label="cookies", reveal="it was a tray of warm cookies for everyone", tags={"surprise"}),
}

MYSTERIES = {
    "missing": Mystery(id="missing", sense=3, solve_text="found the paper hiding in the binder pockets", fail_text="could not make sense of the empty shelf", tags={"mystery"}),
}

GIRL_NAMES = ["Grace", "Mina", "Ivy", "Nora", "Ava"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Sam", "Max"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming legal mystery storyworld with surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--paper", choices=PAPERS)
    ap.add_argument("--surprise", choices=SURPRISES)
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
              if (args.place is None or c[0] == args.place)
              and (args.paper is None or c[1] == args.paper)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, paper, surprise = rng.choice(sorted(combos))
    child_name = args.name or "Grace"
    helper_name = args.helper or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != child_name])
    return StoryParams(place=place, paper=paper, surprise=surprise, child_name=child_name, helper_name=helper_name)


def tell(place: Place, paper: Paper, surprise: Surprise, child_name: str, helper_name: str) -> World:
    world = World()
    grace = world.add(Entity(id=child_name, kind="character", type="girl", role="child"))
    helper = world.add(Entity(id=helper_name, kind="character", type="boy" if helper_name in BOY_NAMES else "girl", role="helper"))
    room = world.add(Entity(id="room", kind="thing", type="room", label=place.label))
    envelope = world.add(Entity(id="envelope_obj", kind="thing", type="paper", label=paper.label))
    clue = world.add(Entity(id="clue", kind="thing", type="note", label="a clue card"))
    grace.memes["kindness"] += 1
    helper.memes["helpfulness"] += 1
    world.say(f"Grace worked at {place.label}, where papers were kept neat and safe.")
    world.say(f"One afternoon, {grace.id} noticed that the {paper.label} was gone.")
    world.say(f"She took a slow breath and said, \"We can solve this.\"")
    world.para()
    envelope.meters["missing"] += 1
    clue.meters["hidden"] += 1
    propagate(world)
    world.say(f"{helper_name} found a small clue near the desk: wxyz, written on a sticky label.")
    world.say(f"That little trail led them to the binder shelf, where the clue kept pointing up high.")
    world.para()
    envelope.meters["hidden"] += 1
    propagate(world)
    world.say(f"At last, {helper_name} reached behind a row of folders and smiled.")
    world.say(f"The mystery was solved: {surprise.reveal}.")
    world.say(f"Inside was the {surprise.label}, saved for the people who had helped the office all week.")
    world.say("Grace laughed, not because the paper was missing anymore, but because the answer was so kind.")
    world.say("They shared the surprise together, and the office felt warm and happy again.")
    world.facts.update(place=place, paper=paper, surprise=surprise, mystery=MYSTERIES["missing"], child=grace, helper=helper, room=room, envelope=envelope, clue=clue)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming mystery story that includes the words "grace", "legal", and "wxyz".',
        f"Tell a gentle story where {f['child'].id} helps solve a legal mystery at {f['place'].label} and finds a surprise.",
        f"Write a child-friendly story about a missing legal envelope, a clue marked wxyz, and a kind surprise at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    return [
        ("Who is the story about?", f"It is about {f['child'].id} and {f['helper'].id}, who worked together to solve a small mystery."),
        ("What was missing?", f"The {f['paper'].label} was missing, so Grace and the helper searched carefully until they found it."),
        ("What did the clue say?", "The clue said wxyz, and that little note helped them look in the right place."),
        ("What was the surprise?", f"The surprise was that {f['surprise'].reveal}."),
        ("How did the story end?", "It ended warmly, with Grace smiling because the mystery was solved and everyone shared the happy surprise."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What does legal mean?", "Legal means it has to do with rules or the law. Legal papers are the kind grown-ups keep safe and organized."),
        ("What is a mystery?", "A mystery is something you do not understand yet. You solve it by looking for clues and asking careful questions."),
        ("What is a surprise?", "A surprise is something you did not expect. It can make people smile when it is kind and helpful."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:12} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("indoor", pid))
    for paper_id, paper in PAPERS.items():
        lines.append(asp.fact("paper", paper_id))
        if paper.legal:
            lines.append(asp.fact("legal", paper_id))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("surprise_label", sid, s.label))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, Pa, S) :- place(P), paper(Pa), surprise(S), legal(Pa), indoor(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            ok = False
            print("MISMATCH: empty story from generate().")
    except Exception as err:
        ok = False
        print(f"MISMATCH: generate() crashed: {err}")
    if ok:
        print("OK: ASP parity and generate() smoke test passed.")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.paper not in PAPERS or params.surprise not in SURPRISES:
        raise StoryError("(Invalid params.)")
    world = tell(PLACES[params.place], PAPERS[params.paper], SURPRISES[params.surprise], params.child_name, params.helper_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print("== Q&A ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


CURATED = [
    StoryParams(place="office", paper="envelope", surprise="gift_card", child_name="Grace", helper_name="Sam"),
    StoryParams(place="hall", paper="form", surprise="thank_you_note", child_name="Grace", helper_name="Mina"),
    StoryParams(place="library", paper="envelope", surprise="cookies", child_name="Grace", helper_name="Eli"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(str(t) for t in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
