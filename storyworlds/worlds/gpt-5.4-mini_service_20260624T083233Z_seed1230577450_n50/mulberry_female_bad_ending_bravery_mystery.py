#!/usr/bin/env python3
"""
storyworlds/worlds/mulberry_female_bad_ending_bravery_mystery.py
=================================================================

A small mystery storyworld with a brave female lead, a mulberry-themed clue,
and a deliberately bad ending that still feels complete.

Premise:
- A girl notices something strange in a quiet garden.
- She follows clues about a mulberry bush and a missing keepsake.
- She is brave enough to look, ask, and climb into the uncertain place.

Tension:
- The mystery points toward a hidden answer.
- The brave choice costs her comfort, and the clue trail gets harder to follow.

Turn:
- She learns the truth, but it is disappointing.
- The lost thing is gone, spoiled, or unreachable.

Resolution:
- The ending is sad, but the bravery remains real.
- The final image shows what changed in her mood and what the mystery revealed.
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
# Core world entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def name_or_label(self) -> str:
        return self.id if self.kind == "character" else (self.label or self.id)


@dataclass
class Place:
    name: str
    indoor: bool = False
    clues: set[str] = field(default_factory=set)
    hazards: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    kind: str = "thing"


@dataclass
class StoryParams:
    place: str
    clue: str
    lead: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "garden": Place(name="the garden", clues={"mulberry", "path", "gate"}, hazards={"thorn"}),
    "orchard": Place(name="the orchard", clues={"mulberry", "branch", "wind"}, hazards={"height"}),
    "lane": Place(name="the lane", clues={"mud", "footprints", "mulberry"}, hazards={"dark"}),
    "shedyard": Place(name="the shed yard", clues={"key", "dust", "mulberry"}, hazards={"lock"}),
}

CLUES = {
    "mulberry": Clue(
        id="mulberry",
        label="mulberry stain",
        phrase="a dark purple mulberry stain",
        reveals="someone brushed past the bush",
    ),
    "key": Clue(
        id="key",
        label="little key",
        phrase="a tiny brass key",
        reveals="the box could be opened",
    ),
    "ribbon": Clue(
        id="ribbon",
        label="blue ribbon",
        phrase="a frayed blue ribbon",
        reveals="the missing keepsake had once been tied to something",
    ),
}

LEADS = {
    "Mina": {"type": "girl", "trait": "brave"},
    "Lena": {"type": "girl", "trait": "curious"},
    "Iris": {"type": "girl", "trait": "careful"},
    "Tessa": {"type": "girl", "trait": "bold"},
}


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
class MysteryWorld:
    def __init__(self, world: World) -> None:
        self.world = world

    def setup(self, lead_name: str, clue_id: str) -> None:
        lead_def = LEADS[lead_name]
        hero = self.world.add(Entity(
            id=lead_name,
            kind="character",
            type=lead_def["type"],
            meters={"bravery": 0.0, "worry": 0.0, "hope": 0.0},
            memes={"curiosity": 0.0, "bravery": 0.0, "sadness": 0.0},
        ))
        clue = self.world.add(Entity(
            id=clue_id,
            kind="thing",
            type="clue",
            label=CLUES[clue_id].label,
            phrase=CLUES[clue_id].phrase,
        ))
        box = self.world.add(Entity(
            id="box",
            kind="thing",
            type="box",
            label="small wooden box",
            phrase="a small wooden box with a bent latch",
            location=self.world.place.name,
        ))
        keeper = self.world.add(Entity(
            id="keeper",
            kind="character",
            type="woman",
            label="the garden keeper",
            meters={"tiredness": 0.0},
            memes={"silence": 0.0},
        ))
        self.world.facts.update(hero=hero, clue=clue, box=box, keeper=keeper)

    def intro(self) -> None:
        h: Entity = self.world.facts["hero"]
        p = self.world.place.name
        self.world.say(
            f"{h.id} was a brave girl who noticed when a quiet place felt a little too still."
        )
        self.world.say(
            f"That morning, she stood in {p} and saw a dark {CLUES['mulberry'].label} on the stones."
        )

    def search(self) -> None:
        h: Entity = self.world.facts["hero"]
        clue: Entity = self.world.facts["clue"]
        self.world.para()
        h.meters["bravery"] += 1
        h.memes["curiosity"] += 1
        self.world.say(
            f"{h.id} took a deep breath and followed the clue instead of turning away."
        )
        self.world.say(
            f"The trail led past a mulberry bush, where {clue.phrase} sat like a secret."
        )

    def warning(self) -> None:
        h: Entity = self.world.facts["hero"]
        self.world.para()
        h.meters["worry"] += 1
        self.world.say(
            f"At the edge of the path, the branches scratched the air, and {h.id} felt a shiver of fear."
        )
        self.world.say(
            f"Still, {h.pronoun().capitalize()} kept going, because brave hearts do not stop at the first hush."
        )

    def reveal_bad_end(self) -> None:
        h: Entity = self.world.facts["hero"]
        clue: Entity = self.world.facts["clue"]
        box: Entity = self.world.facts["box"]
        keeper: Entity = self.world.facts["keeper"]
        self.world.para()
        if clue.id == "mulberry":
            self.world.say(
                f"Behind the bush, {h.id} found the little box, but the latch was already broken open."
            )
            self.world.say(
                f"Inside, there was only a smudge of purple and a torn bit of ribbon, not the thing she hoped for."
            )
            h.memes["sadness"] += 1
        else:
            self.world.say(
                f"{h.id} found the box at last, but it was empty except for dust and one lonely clue."
            )
            h.memes["sadness"] += 1

        self.world.say(
            f"The garden keeper came slowly and admitted the truth: the missing keepsake had been lost yesterday in the rain."
        )
        self.world.say(
            f"By then, the best part was gone, and even {h.id}'s brave search could not bring it back."
        )
        box.location = "open"
        keeper.memes["silence"] += 1

    def ending(self) -> None:
        h: Entity = self.world.facts["hero"]
        self.world.para()
        self.world.say(
            f"{h.id} stood beside the mulberry bush with purple spots on {h.pronoun('possessive')} fingers."
        )
        self.world.say(
            f"{h.pronoun().capitalize()} was sad, but {h.pronoun('possessive')} shoulders stayed straight, because bravery still mattered even on a bad day."
        )

    def run(self) -> World:
        self.intro()
        self.search()
        self.warning()
        self.reveal_bad_end()
        self.ending()
        return self.world


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_name, place in PLACES.items():
        for clue_id in CLUES:
            if clue_id in place.clues:
                for lead_name in LEADS:
                    combos.append((place_name, clue_id, lead_name))
    return combos


def explain_rejection(place: str, clue: str, lead: str) -> str:
    reasons = []
    if clue not in PLACES[place].clues:
        reasons.append(f"{place} does not naturally support the {clue} clue")
    if LEADS[lead]["type"] != "girl":
        reasons.append("the lead should be female for this storyworld")
    return "(No story: " + "; ".join(reasons) + ".)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A story is valid when the place supports the clue, and the lead is female.
valid(Place, Clue, Lead) :- place(Place), clue(Clue), lead(Lead),
                            supports(Place, Clue), female(Lead).

#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place_name, place in PLACES.items():
        lines.append(asp.fact("place", place_name))
        for clue in sorted(place.clues):
            lines.append(asp.fact("supports", place_name, clue))
    for clue_id in CLUES:
        lines.append(asp.fact("clue", clue_id))
    for lead_name, lead in LEADS.items():
        lines.append(asp.fact("lead", lead_name))
        if lead["type"] == "girl":
            lines.append(asp.fact("female", lead_name))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Story / QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Entity = f["clue"]
    return [
        f'Write a short mystery story for a child about a brave female lead and a {clue.label}.',
        f"Tell a gentle but sad story where {hero.id} follows a mulberry clue and finds out the truth too late.",
        f"Write a story with a brave girl, a quiet place, and a bad ending that still feels complete.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    clue: Entity = f["clue"]
    place = world.place.name
    return [
        QAItem(
            question=f"Who is the brave girl in the story?",
            answer=f"The brave girl is {hero.id}. She is the one who follows the clue in {place}.",
        ),
        QAItem(
            question=f"What clue did {hero.id} notice first?",
            answer=f"{hero.id} noticed a {clue.label} first, and it led her deeper into the mystery.",
        ),
        QAItem(
            question=f"Did the mystery end happily?",
            answer="No. It ended sadly, because the lost thing was already gone by the time the truth was found.",
        ),
        QAItem(
            question=f"Why was {hero.id} brave?",
            answer=f"{hero.id} was brave because she kept searching even after the path felt scary and uncertain.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mulberry?",
            answer="A mulberry is a small berry that can grow on a tree or bush and make purple stains.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel scared, because you think it is worth trying.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something you do not understand at first, so you look for clues to figure it out.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.clue and args.lead:
        if args.clue not in PLACES[args.place].clues:
            raise StoryError(explain_rejection(args.place, args.clue, args.lead))
        if LEADS[args.lead]["type"] != "girl":
            raise StoryError(explain_rejection(args.place, args.clue, args.lead))
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.clue is None or c[1] == args.clue)
        and (args.lead is None or c[2] == args.lead)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue, lead = rng.choice(sorted(combos))
    return StoryParams(place=place, clue=clue, lead=lead, seed=args.seed)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    mw = MysteryWorld(world)
    mw.setup(params.lead, params.clue)
    mw.run()
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
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld with a brave female lead and a bad ending."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--lead", choices=LEADS)
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


CURATED = [
    StoryParams(place="garden", clue="mulberry", lead="Mina"),
    StoryParams(place="orchard", clue="mulberry", lead="Lena"),
    StoryParams(place="lane", clue="mulberry", lead="Iris"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for t in combos:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.lead}: {p.clue} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
