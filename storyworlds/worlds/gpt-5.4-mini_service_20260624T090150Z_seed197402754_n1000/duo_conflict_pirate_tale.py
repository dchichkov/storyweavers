#!/usr/bin/env python3
"""
A small pirate-tale storyworld about a duo whose shared plan runs into a conflict
and ends with a changed course, a repaired bond, and a clear final image.
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


@dataclass
class Person:
    id: str
    role: str
    type: str = "pirate"
    label: str = ""
    kind: str = "character"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    kind: str = "place"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class ObjectItem:
    id: str
    label: str
    type: str = "thing"
    kind: str = "thing"
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    duo_a: str
    duo_b: str
    place: str
    conflict: str
    treasure: str
    seed: Optional[int] = None


DUO_NAMES = [
    ("Ari", "Beck"),
    ("Mira", "Nico"),
    ("Tess", "Pip"),
    ("Jory", "Luna"),
    ("Finn", "Sora"),
]

PLACES = {
    "harbor": Place(id="harbor", label="the harbor"),
    "cove": Place(id="cove", label="a hidden cove"),
    "island": Place(id="island", label="a small island"),
    "reef": Place(id="reef", label="the bright reef"),
}

TREASURES = {
    "golden_compass": "a golden compass",
    "ruby_key": "a ruby key",
    "moon_chest": "a tiny moon chest",
    "silver_ring": "a silver ring",
}

CONFLICTS = {
    "map": "which path to follow on the map",
    "captaincy": "who should steer the boat first",
    "share": "how to share the treasure",
    "signal": "which signal to use in the fog",
}


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, object] = {}
        self.fired: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        clone = World(self.place)
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _conflict_rule(world: World) -> list[str]:
    out: list[str] = []
    duo_a = world.get("duo_a")
    duo_b = world.get("duo_b")
    if duo_a.memes.get("argue", 0) >= 1 and duo_b.memes.get("argue", 0) >= 1:
        if "conflict" not in world.fired:
            world.fired.add("conflict")
            duo_a.memes["hurt"] = duo_a.memes.get("hurt", 0) + 1
            duo_b.memes["hurt"] = duo_b.memes.get("hurt", 0) + 1
            out.append("A sharp conflict rose between the two mates.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    while True:
        next_lines = _conflict_rule(world)
        if not next_lines:
            break
        produced.extend(next_lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    a = world.add(Person(id="duo_a", role="first mate", label=params.duo_a))
    b = world.add(Person(id="duo_b", role="second mate", label=params.duo_b))
    treasure = world.add(ObjectItem(id="treasure", label=TREASURES[params.treasure], owner=a.id))
    route = world.add(ObjectItem(id="route", label=params.conflict))

    a.meters["joy"] = 1
    b.meters["joy"] = 1
    a.memes["bond"] = 1
    b.memes["bond"] = 1

    world.say(
        f"On {world.place.label}, two pirates, {a.label} and {b.label}, sailed as a duo."
    )
    world.say(
        f"They had a map, a small boat, and {treasure.label} waiting for them."
    )
    world.para()
    world.say(
        f"But they fell into a conflict about {CONFLICTS[params.conflict]}."
    )
    a.memes["argue"] = 1
    b.memes["argue"] = 1
    propagate(world)
    world.say(
        f"{a.label} wanted one way, while {b.label} wanted another."
    )
    world.para()
    if params.conflict == "map":
        world.say(
            f"Then {b.label} noticed a tide mark on the map and showed {a.label} the safer path."
        )
    elif params.conflict == "captaincy":
        world.say(
            f"Then {a.label} smiled and let {b.label} hold the wheel first."
        )
    elif params.conflict == "share":
        world.say(
            f"Then they split the treasure fairly, with each mate keeping a bright share."
        )
    else:
        world.say(
            f"Then they agreed on a single fog signal so neither pirate would be left behind."
        )
    a.memes["argue"] = 0
    b.memes["argue"] = 0
    a.memes["bond"] = a.memes.get("bond", 0) + 1
    b.memes["bond"] = b.memes.get("bond", 0) + 1
    world.say(
        f"By sunset, the duo was smiling again, and {treasure.label} sat safe between them."
    )
    world.say(
        f"Their little boat rocked home while the sea glowed gold around their shared prize."
    )
    world.facts.update(a=a, b=b, treasure=treasure, route=route)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a short pirate tale for a young child about a duo who run into a conflict and solve it kindly.',
        f"Tell a gentle story where {world.facts['a'].label} and {world.facts['b'].label} disagree at {world.place.label} but end the day together.",
        f"Write a simple pirate story that includes {world.facts['treasure'].label} and a repaired friendship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    a = world.facts["a"]
    b = world.facts["b"]
    treasure = world.facts["treasure"]
    return [
        QAItem(
            question=f"Who was the pirate duo in the story?",
            answer=f"The pirate duo was {a.label} and {b.label}.",
        ),
        QAItem(
            question=f"What caused the conflict on the ship?",
            answer=f"The conflict was about {CONFLICTS[world.facts['route'].label]}.",
        ),
        QAItem(
            question=f"What treasure did the duo keep safe?",
            answer=f"They kept {treasure.label} safe by the end of the story.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The two pirates worked things out, smiled again, and sailed home together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a duo?",
            answer="A duo is a pair of two people or things working together.",
        ),
        QAItem(
            question="What is a conflict?",
            answer="A conflict is a disagreement or struggle between people who want different things.",
        ),
        QAItem(
            question="What is a treasure map for?",
            answer="A treasure map helps pirates find something hidden by showing where to look.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if getattr(ent, "label", ""):
            bits.append(f"label={ent.label}")
        lines.append(f"  {ent.id:10} ({ent.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(conflict: str) -> str:
    if conflict not in CONFLICTS:
        return "(No story: unknown conflict choice.)"
    return f"(No story: the chosen conflict '{conflict}' is not available.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate-tale storyworld about a duo and a conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name-a")
    ap.add_argument("--name-b")
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
    place = args.place or rng.choice(sorted(PLACES))
    conflict = args.conflict or rng.choice(sorted(CONFLICTS))
    treasure = args.treasure or rng.choice(sorted(TREASURES))
    if args.conflict and args.conflict not in CONFLICTS:
        raise StoryError(explain_rejection(args.conflict))
    duo_a, duo_b = (args.name_a, args.name_b) if args.name_a and args.name_b else rng.choice(DUO_NAMES)
    return StoryParams(duo_a=duo_a, duo_b=duo_b, place=place, conflict=conflict, treasure=treasure)


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


ASP_RULES = r"""
duo(a,b) :- pair(a,b).
conflict(P) :- wants(a,P), wants(b,Q), P != Q.
resolved :- compromise.
#show duo/2.
#show conflict/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a, b in DUO_NAMES:
        lines.append(asp.fact("pair", a, b))
    for key in CONFLICTS:
        lines.append(asp.fact("wants", "a", key))
        lines.append(asp.fact("wants", "b", key))
    lines.append(asp.fact("compromise"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show duo/2.\n#show conflict/1.\n#show resolved/0."))
    return 0 if model is not None else 1


CURATED = [
    StoryParams("Ari", "Beck", "harbor", "map", "golden_compass"),
    StoryParams("Mira", "Nico", "cove", "captaincy", "ruby_key"),
    StoryParams("Tess", "Pip", "island", "share", "moon_chest"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show duo/2.\n#show conflict/1.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
