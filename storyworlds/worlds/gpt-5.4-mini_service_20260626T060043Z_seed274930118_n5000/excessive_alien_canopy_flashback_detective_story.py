#!/usr/bin/env python3
"""
Standalone storyworld: an excessive alien canopy detective tale with flashback.

The world is small and classical:
- A detective follows a strange clue.
- A flashback reveals an earlier detail.
- The clue turns out to be an alien canopy hiding something real.
- The ending proves the mystery changed from confusing to understood.

The script supports the shared Storyweavers interface:
- build_parser()
- resolve_params()
- generate()
- emit()
- main()

It also includes a reasonableness gate and an inline ASP twin.
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

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    suspicious: bool = False
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "detective"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False
    shadowy: bool = False


@dataclass
class Case:
    id: str
    mystery: str
    clue: str
    reveal: str
    location: str
    flashback_line: str
    cover_phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    case: str
    detective_name: str
    assistant_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.flashback_used = False

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.flashback_used = self.flashback_used
        return w


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden": Setting(place="the garden", outdoors := True, shadowy=False),
    "museum": Setting(place="the museum", outdoors := False, shadowy=True),
    "rooftop": Setting(place="the rooftop", outdoors := True, shadowy=True),
    "alley": Setting(place="the alley", outdoors := True, shadowy=True),
}

CASES = {
    "canopy": Case(
        id="canopy",
        mystery="an excessive alien canopy was draped over the courtyard",
        clue="the canopy's ribs were too neat to be vines",
        reveal="the canopy was a folded alien awning that hid a stolen lantern",
        location="courtyard",
        flashback_line="Earlier, the detective had seen the same silver thread on a broken latch.",
        cover_phrase="the alien canopy",
        tags={"alien", "canopy", "flashback", "detective"},
    ),
    "greenlight": Case(
        id="greenlight",
        mystery="a green glow kept slipping under a porch roof",
        clue="the light pulsed in a pattern like footsteps",
        reveal="the glow came from a toy beacon tucked above the rafters",
        location="porch",
        flashback_line="The detective remembered a child saying the toy blinked only when hidden.",
        cover_phrase="the porch roof",
        tags={"flashback", "detective"},
    ),
    "market": Case(
        id="market",
        mystery="the market stall looked too tidy after the theft",
        clue="a ribbon of dust led behind the crates",
        reveal="the missing coins were in a jar under the canvas",
        location="stall",
        flashback_line="A minute earlier, the detective had noticed the jar's lid on the ground.",
        cover_phrase="the canvas",
        tags={"detective", "flashback"},
    ),
}

DETECTIVE_NAMES = ["Mara", "Ivy", "Noah", "June", "Eli", "Nina"]
ASSISTANT_NAMES = ["Pip", "Toby", "Lena", "Milo", "Sage", "Otis"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def case_reasonable(place: str, case: Case) -> bool:
    if case.id == "canopy":
        return place in {"garden", "rooftop", "alley"}
    if case.id == "greenlight":
        return place in {"museum", "alley"}
    if case.id == "market":
        return place in {"garden", "market", "alley"}
    return False


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for cid, case in CASES.items():
            if case_reasonable(place, case):
                out.append((place, cid))
    return out


def explain_rejection(place: str, case: Case) -> str:
    return (
        f"(No story: the mystery '{case.mystery}' does not fit at {SETTINGS[place].place}. "
        f"Try a different setting where the clue could plausibly hide there.)"
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
reasonable(P, C) :- place(P), case(C), allowed(P, C).
valid(P, C) :- reasonable(P, C).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        for t in sorted(case.tags):
            lines.append(asp.fact("tag", cid, t))
    for place, cid in valid_combos():
        lines.append(asp.fact("allowed", place, cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gate:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def flashback_line(case: Case) -> str:
    return case.flashback_line


def detect(world: World, detective: Entity, assistant: Entity, case: Case) -> None:
    detective.memes["curiosity"] += 1
    world.say(
        f"{detective.id}, a careful detective, walked into {world.setting.place} with {assistant.id} beside {detective.pronoun('object')}."
    )
    world.say(
        f"They were looking for {case.mystery}."
    )


def clue_seen(world: World, detective: Entity, case: Case) -> None:
    detective.meters["evidence"] += 1
    detective.memes["unease"] += 1
    world.say(
        f"At the center of the scene, {case.cover_phrase} hung in an {('excessive ' if case.id == 'canopy' else '')}odd way."
    )
    world.say(f"{case.clue.capitalize()}.")


def do_flashback(world: World, detective: Entity, case: Case) -> None:
    world.flashback_used = True
    detective.memes["memory"] += 1
    world.para()
    world.say("Flashback:")
    world.say(f"{flashback_line(case)}")
    world.say(
        f"That memory made the clue feel less random and more like a trail."
    )


def reveal(world: World, detective: Entity, assistant: Entity, case: Case) -> None:
    detective.meters["evidence"] += 1
    detective.memes["relief"] += 1
    world.say(
        f"Following the trail, {detective.id} reached behind {case.location} and found the truth."
    )
    world.say(
        f"{case.reveal.capitalize()}."
    )
    world.say(
        f"{assistant.id} let out a small gasp, and {detective.id} smiled because the strange cover was only pretending to be a monster."
    )


def resolve(world: World, detective: Entity, assistant: Entity, case: Case) -> None:
    detective.memes["confidence"] += 1
    assistant.memes["calm"] += 1
    world.say(
        f"By the end, {detective.id} had the answer, and {case.cover_phrase} was no longer a mystery."
    )
    world.say(
        f"The whole place looked ordinary again, except now everyone knew what had been hiding there."
    )


def tell(setting: Setting, case: Case, detective_name: str, assistant_name: str) -> World:
    w = World(setting)
    detective = w.add(Entity(id=detective_name, kind="character", type="detective"))
    assistant = w.add(Entity(id=assistant_name, kind="character", type="assistant"))
    clue = w.add(Entity(id="clue", label=case.cover_phrase, suspicious=True, hidden=False))
    w.facts.update(detective=detective, assistant=assistant, case=case, clue=clue)
    detect(w, detective, assistant, case)
    w.para()
    clue_seen(w, detective, case)
    do_flashback(w, detective, case)
    w.para()
    reveal(w, detective, assistant, case)
    resolve(w, detective, assistant, case)
    return w


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    case: Case = f["case"]
    return [
        'Write a short detective story for children that includes the words "excessive", "alien", and "canopy".',
        f"Tell a mystery story with a flashback where a detective discovers that {case.mystery}.",
        f"Write a simple detective tale about a strange cover at {world.setting.place} that turns out to be {case.reveal}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    case: Case = f["case"]
    det: Entity = f["detective"]
    assistant: Entity = f["assistant"]
    return [
        QAItem(
            question=f"What kind of story is this about {det.id} and {assistant.id}?",
            answer=f"It is a detective story about {det.id} solving a strange mystery with help from {assistant.id}.",
        ),
        QAItem(
            question=f"What was strange about the thing they found at {world.setting.place}?",
            answer=f"They found {case.mystery}, which looked weird until the detective followed the clues.",
        ),
        QAItem(
            question="What did the flashback add to the mystery?",
            answer=f"The flashback reminded the detective of {case.flashback_line.lower()}",  # child-facing and grounded
        ),
        QAItem(
            question="What was the truth in the end?",
            answer=f"The truth was that {case.reveal}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks carefully for clues and tries to figure out what really happened.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that shows something that happened earlier.",
        ),
        QAItem(
            question="What is a canopy?",
            answer="A canopy is a cover that stretches over something, like a roof, cloth, or leafy top.",
        ),
        QAItem(
            question="What does excessive mean?",
            answer="Excessive means too much or more than is needed.",
        ),
        QAItem(
            question="What does alien mean?",
            answer="Alien means from somewhere not familiar, or from another world in a space story.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.suspicious:
            bits.append("suspicious=True")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  flashback_used={world.flashback_used}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Parameters / generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    case: str
    detective_name: str
    assistant_name: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Child-friendly detective storyworld with a flashback.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--case", choices=CASES.keys())
    ap.add_argument("--name")
    ap.add_argument("--assistant")
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
    if args.place and args.case:
        if not case_reasonable(args.place, CASES[args.case]):
            raise StoryError(explain_rejection(args.place, CASES[args.case]))
    filtered = [
        (p, c) for p, c in combos
        if (args.place is None or p == args.place)
        and (args.case is None or c == args.case)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, case = rng.choice(sorted(filtered))
    detective_name = args.name or rng.choice(DETECTIVE_NAMES)
    assistant_name = args.assistant or rng.choice(ASSISTANT_NAMES)
    return StoryParams(place=place, case=case, detective_name=detective_name, assistant_name=assistant_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], CASES[params.case], params.detective_name, params.assistant_name)
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="garden", case="canopy", detective_name="Mara", assistant_name="Pip"),
    StoryParams(place="museum", case="greenlight", detective_name="Ivy", assistant_name="Lena"),
    StoryParams(place="alley", case="market", detective_name="Noah", assistant_name="Otis"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, case) combos:\n")
        for place, case in triples:
            print(f"  {place:10} {case}")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.detective_name}: {p.case} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
