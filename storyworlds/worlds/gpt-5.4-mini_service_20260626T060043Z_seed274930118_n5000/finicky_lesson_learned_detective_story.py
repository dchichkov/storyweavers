#!/usr/bin/env python3
"""
A small detective-story world about a finicky clue hunt and a lesson learned.

Seed tale premise:
A careful little detective keeps missing one tiny detail because the case is finicky.
After a false start, the detective learns to slow down, check neatly, and the clue
finally points to the truth.
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

CASE_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    vibe: str
    allows: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    finicky: bool
    reveals: str
    location: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    alibi: str
    tells: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
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


@dataclass
class StoryParams:
    place: str
    clue: str
    suspect: str
    name: str
    role: str
    helper: str
    seed: Optional[int] = None


SETTINGS = {
    "library": Setting(place="the library", vibe="quiet", allows={"ink", "stamps"}),
    "bakery": Setting(place="the bakery", vibe="warm", allows={"crumbs", "sprinkles"}),
    "garden": Setting(place="the garden shed", vibe="dusty", allows={"dust", "soil"}),
}

CLUES = {
    "ink": Clue(
        id="ink",
        label="ink blot",
        phrase="a tiny ink blot",
        finicky=True,
        reveals="the note was written with a left-handed swirl",
        location="under the table",
        tags={"ink", "paper"},
    ),
    "crumbs": Clue(
        id="crumbs",
        label="crumb trail",
        phrase="a line of crumbs",
        finicky=True,
        reveals="someone had nibbled the cookie before the door closed",
        location="by the chair",
        tags={"crumbs", "food"},
    ),
    "soil": Clue(
        id="soil",
        label="mud print",
        phrase="a soft mud print",
        finicky=True,
        reveals="the shoes matched the garden path",
        location="near the mat",
        tags={"mud", "garden"},
    ),
}

SUSPECTS = {
    "librarian": Suspect(
        id="librarian",
        label="the librarian",
        type="adult",
        alibi="was shelving books all morning",
        tells="kept brushing paper dust from her sleeve",
        tags={"paper", "ink"},
    ),
    "baker": Suspect(
        id="baker",
        label="the baker",
        type="adult",
        alibi="was kneading dough at dawn",
        tells="laughed with flour on his nose",
        tags={"food", "crumbs"},
    ),
    "gardener": Suspect(
        id="gardener",
        label="the gardener",
        type="adult",
        alibi="was trimming vines by the gate",
        tells="left muddy marks on the steps",
        tags={"garden", "mud"},
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Theo", "June", "Max"]
ROLES = ["detective", "sleuth", "investigator"]
HELPERS = ["mouse helper", "paper map", "magnifying glass", "notebook"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for clue_id in setting.allows:
            for suspect_id, suspect in SUSPECTS.items():
                if clue_id in suspect.tags:
                    out.append((place, clue_id, suspect_id))
    return out


def _reasonableness_gate(clue: Clue, suspect: Suspect, setting: Setting) -> bool:
    return clue.id in setting.allows and clue.id in suspect.tags


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    clue = CLUES[params.clue]
    suspect = SUSPECTS[params.suspect]
    if not _reasonableness_gate(clue, suspect, setting):
        raise StoryError("That clue and suspect do not fit the same case.")
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="girl" if params.role == "detective" else "boy"))
    helper = world.add(Entity(id="helper", kind="thing", type="thing", label=params.helper, plural=False))
    clue_ent = world.add(Entity(id="clue", kind="thing", type="thing", label=clue.label, phrase=clue.phrase))
    suspect_ent = world.add(Entity(id="suspect", kind="character", type=suspect.type, label=suspect.label))
    world.facts.update(hero=hero, helper=helper, clue=clue_ent, suspect=suspect_ent, clue_cfg=clue, suspect_cfg=suspect)
    return world


def open_case(world: World) -> None:
    h = world.facts["hero"]
    c = world.facts["clue_cfg"]
    s = world.facts["suspect_cfg"]
    world.say(f"{h.id} was a little detective with a careful eye and a finicky case to solve.")
    world.say(f"One morning at {world.setting.place}, {h.id} found {c.phrase}, but the mark was so tiny it almost vanished.")
    world.say(f"The clue seemed to point at {s.label}, yet the answer would not come easily.")


def search(world: World) -> None:
    h = world.facts["hero"]
    c = world.facts["clue_cfg"]
    s = world.facts["suspect_cfg"]
    h.memes["curiosity"] = h.memes.get("curiosity", 0) + 1
    h.memes["frustration"] = h.memes.get("frustration", 0) + 1
    world.para()
    world.say(f"{h.id} rushed to {c.location}, but the finicky clue kept slipping out of sight.")
    world.say(f"{h.id} checked too fast and got the wrong idea, because {s.label} {s.alibi}.")


def lesson(world: World) -> None:
    h = world.facts["hero"]
    c = world.facts["clue_cfg"]
    s = world.facts["suspect_cfg"]
    helper = world.facts["helper"]
    h.memes["patience"] = h.memes.get("patience", 0) + 1
    h.memes["frustration"] = 0.0
    world.para()
    world.say(f"Then {h.id} took a slow breath and used {helper.label} to look again.")
    world.say(f"This time, {h.id} noticed {c.reveals}, and the little clue finally made sense.")
    world.say(f"It was not a mean trick after all; it was just finicky, and careful looking solved it.")


def solve_case(world: World) -> None:
    h = world.facts["hero"]
    c = world.facts["clue_cfg"]
    s = world.facts["suspect_cfg"]
    h.memes["pride"] = h.memes.get("pride", 0) + 1
    world.para()
    world.say(f"{h.id} smiled and explained that {c.phrase} matched {s.label}, not by luck, but by patient work.")
    world.say(f"{s.label} was never the culprit, and the real mystery was simply a finicky clue hiding in plain sight.")
    world.say(f"By the end, {h.id} had learned that going slowly can be the best way to catch the truth.")


CURATED = [
    StoryParams(place="library", clue="ink", suspect="librarian", name="Mia", role="detective", helper="magnifying glass"),
    StoryParams(place="bakery", clue="crumbs", suspect="baker", name="Leo", role="sleuth", helper="notebook"),
    StoryParams(place="garden", clue="soil", suspect="gardener", name="Nora", role="investigator", helper="paper map"),
]


def tell(params: StoryParams) -> World:
    world = build_world(params)
    open_case(world)
    search(world)
    lesson(world)
    solve_case(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short detective story for a young child about a finicky clue and a lesson learned.",
        f"Tell a story where {f['hero'].id} solves a mystery at {world.setting.place} by slowing down and looking carefully.",
        f"Write a simple mystery with {f['clue_cfg'].phrase} that leads to a kind lesson about patience.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, clue, suspect = f["hero"], f["clue_cfg"], f["suspect_cfg"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little detective who had a finicky case to solve.",
        ),
        QAItem(
            question=f"What clue did {hero.id} find at {world.setting.place}?",
            answer=f"{hero.id} found {clue.phrase}, and it was so finicky that it was easy to miss at first.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that slowing down and checking carefully can solve a mystery better than rushing.",
        ),
        QAItem(
            question=f"Who looked like the answer at first?",
            answer=f"{suspect.label} looked like the answer at first, but the clue turned out to be pointing somewhere else.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a detective do?",
            answer="A detective looks for clues, asks careful questions, and tries to figure out what happened.",
        ),
        QAItem(
            question="What does it mean if something is finicky?",
            answer="If something is finicky, it is fussy or hard to handle because tiny details matter a lot.",
        ),
        QAItem(
            question="Why is a magnifying glass useful?",
            answer="A magnifying glass helps you look closely at small things and see details more clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(X) :- name(X).
finicky_clue(C) :- clue(C).
good_match(C,S) :- clue_for(C,T), suspect_tag(S,T).
valid_case(P,C,S) :- place(P), allows(P,C), clue_for(C,T), suspect_tag(S,T).
#show valid_case/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("place", place))
        for clue in sorted(setting.allows):
            lines.append(asp.fact("allows", place, clue))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_for", cid, clue.id))
        if clue.finicky:
            lines.append(asp.fact("finicky", cid))
    for sid, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for tag in sorted(suspect.tags):
            lines.append(asp.fact("suspect_tag", sid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_case/3."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_cases())
    if py == cl:
        print(f"OK: clingo matches python gate ({len(py)} cases).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A finicky detective story world with a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--clue", choices=CLUES.keys())
    ap.add_argument("--suspect", choices=SUSPECTS.keys())
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
        and (args.suspect is None or c[2] == args.suspect)
    ]
    if not filtered:
        raise StoryError("No valid detective case matches those choices.")
    place, clue, suspect = rng.choice(sorted(filtered))
    return StoryParams(
        place=place,
        clue=clue,
        suspect=suspect,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
        helper=args.helper or rng.choice(HELPERS),
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_case/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid_case/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
