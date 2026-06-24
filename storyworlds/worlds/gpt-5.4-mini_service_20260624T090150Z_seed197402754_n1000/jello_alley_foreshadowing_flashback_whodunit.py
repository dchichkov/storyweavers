#!/usr/bin/env python3
"""
A small whodunit storyworld about a jello mess in an alley, with foreshadowing
and a flashback that help solve the mystery.

The simulated domain:
- a child-friendly mystery in a narrow alley
- a bowl of jello, a spilled clue, and a careful little detective
- foreshadowing and flashback as explicit narrative instruments
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the alley"
    details: str = "a narrow alley with brick walls and a metal gate"


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    motive: str
    clue: str
    innocence_clue: str


@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_type: str
    witness_name: str
    witness_type: str
    suspect: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
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

SETTINGS = {
    "alley": Setting(place="the alley", details="a narrow alley with brick walls, a flickering lamp, and a rusty gate"),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the alley cat",
        type="cat",
        motive="wanted the fish smell from the lunch cart",
        clue="cat paw prints in the dust",
        innocence_clue="jello on its whiskers but no stolen spoon",
    ),
    "neighbor": Suspect(
        id="neighbor",
        label="the neighbor",
        type="adult",
        motive="was carrying a tray and stumbled when the door banged",
        clue="a cracked tray near the gate",
        innocence_clue="an apology note on the doormat",
    ),
    "kid": Suspect(
        id="kid",
        label="the small kid",
        type="child",
        motive="wanted to help but dropped the bowl by accident",
        clue="tiny shoe prints beside the spill",
        innocence_clue="sticky hands from eating jello earlier",
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Ruby", "Nora", "Ivy"]
BOY_NAMES = ["Leo", "Noah", "Milo", "Eli", "Ben"]
WITNESS_NAMES = ["Tom", "June", "Sam", "Pia", "Ari"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def valid_combo(place: str, suspect: str) -> bool:
    return place in SETTINGS and suspect in SUSPECTS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "alley"
    suspect = args.suspect or rng.choice(list(SUSPECTS))
    if not valid_combo(place, suspect):
        raise StoryError("That alley mystery cannot be built from the requested choices.")

    detective_type = args.detective_type or rng.choice(["girl", "boy"])
    detective_name = args.detective_name or rng.choice(GIRL_NAMES if detective_type == "girl" else BOY_NAMES)
    witness_type = args.witness_type or rng.choice(["girl", "boy"])
    witness_name = args.witness_name or rng.choice(WITNESS_NAMES)
    return StoryParams(
        place=place,
        detective_name=detective_name,
        detective_type=detective_type,
        witness_name=witness_name,
        witness_type=witness_type,
        suspect=suspect,
    )


def build_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label=f"young detective {params.detective_name}",
    ))
    witness = world.add(Entity(
        id=params.witness_name,
        kind="character",
        type=params.witness_type,
        label=f"neighbor {params.witness_name}",
    ))
    suspect = SUSPECTS[params.suspect]
    bowl = world.add(Entity(
        id="bowl",
        kind="thing",
        type="bowl",
        label="a glass bowl",
        phrase="a glass bowl full of red jello",
        location=params.place,
    ))
    spill = world.add(Entity(
        id="spill",
        kind="thing",
        type="jello",
        label="jello spill",
        phrase="a wobbly red jello spill",
        location=params.place,
    ))
    spoon = world.add(Entity(
        id="spoon",
        kind="thing",
        type="spoon",
        label="a spoon",
        phrase="a silver spoon",
        location=params.place,
    ))
    world.facts.update(
        detective=detective,
        witness=witness,
        suspect=suspect,
        bowl=bowl,
        spill=spill,
        spoon=spoon,
    )
    return world


def tell_story(world: World, params: StoryParams) -> str:
    d: Entity = world.facts["detective"]  # type: ignore[assignment]
    w: Entity = world.facts["witness"]  # type: ignore[assignment]
    suspect: Suspect = world.facts["suspect"]  # type: ignore[assignment]

    d.memes["curiosity"] = 1
    d.memes["doubt"] = 1

    world.say(
        f"On a quiet afternoon in {world.setting.place}, {d.label} noticed something odd: "
        f"there was a red jello spill shining under the lamp."
    )
    world.say(
        f"That was the sort of little clue that made {d.pronoun('subject')} pause, because in a whodunit, "
        f"the first thing you see is not always the thing that matters most."
    )

    world.para()
    world.say(
        f"{w.label} pointed at the alley gate and said, \"I heard a tiny thump, then a sticky splash.\""
    )
    world.say(
        f"Near the wall, {d} found {suspect.clue}, and that made {d.pronoun('object')} think someone had been here just before the mess."
    )

    # Foreshadowing
    world.para()
    world.say(
        f"There was another clue too: a silver spoon lay beside the bowl, as if it had slipped from a careful hand."
    )
    world.say(
        f"{d.label} remembered that a neat bowl sitting too close to the edge often meant trouble was coming, and that was the first hint of how the mystery would turn."
    )

    # Flashback
    world.para()
    world.say(
        f"Then {d.pronoun('subject')} had a flashback to the morning, when {w.label} had seen {suspect.label} near the cart."
    )
    if params.suspect == "cat":
        world.say(
            f"In that memory, the cat had only circled the fish smell and sniffed at the shadows, not the bowl."
        )
    elif params.suspect == "neighbor":
        world.say(
            f"In that memory, the neighbor had been carrying groceries and balancing a tray, looking more hurried than guilty."
        )
    else:
        world.say(
            f"In that memory, the small kid had been stretching up to help, sticky fingers and all."
        )
    world.say(
        f"The flashback made the clue fit better: the spill was an accident, not a sneaky theft."
    )

    # Resolution
    world.para()
    world.say(
        f"{d.label} followed the trail, checked the spoon, and looked at the jello on the floor."
    )
    world.say(
        f"At last, {d.pronoun('subject')} told {w.label}, \"{suspect.label.title()} did not steal the jello. "
        f"{suspect.innocence_clue.capitalize()}\""
    )
    world.say(
        f"The real answer was simple: {suspect.motive}, so the bowl tipped, the jello wobbled free, and the alley became red and sticky."
    )
    world.say(
        f"{d.label} smiled, because the mystery was solved, the wrong guess was cleared away, and the only thing left to do was mop the floor."
    )

    world.facts.update(
        solved=True,
        foreshadowing=True,
        flashback=True,
        motive=suspect.motive,
        clue=suspect.clue,
    )
    return world.render()


# ---------------------------------------------------------------------------
# Q&A generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d: Entity = f["detective"]  # type: ignore[assignment]
    suspect: Suspect = f["suspect"]  # type: ignore[assignment]
    return [
        "Write a child-friendly whodunit about a jello spill in an alley, with a clue that looks suspicious at first.",
        f"Tell a short mystery where {d.label} uses foreshadowing and a flashback to solve who made the jello mess.",
        f"Write a gentle detective story set in {world.setting.place} that ends with the real cause of the spill being explained.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d: Entity = f["detective"]  # type: ignore[assignment]
    w: Entity = f["witness"]  # type: ignore[assignment]
    suspect: Suspect = f["suspect"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Where did {d.label} find the jello clue?",
            answer=f"{d.label} found the jello clue in {world.setting.place}, under the alley lamp.",
        ),
        QAItem(
            question="What clue first made the mystery seem suspicious?",
            answer=f"The first suspicious clue was {suspect.clue}.",
        ),
        QAItem(
            question=f"What did {d.label} remember in the flashback?",
            answer=f"{d.label} remembered seeing {suspect.label} near the cart earlier in the day.",
        ),
        QAItem(
            question="How did the story show foreshadowing?",
            answer="It foreshadowed the solution by showing the spoon and by hinting that a bowl too close to the edge could cause trouble.",
        ),
        QAItem(
            question="How was the mystery solved at the end?",
            answer=f"{d.label} noticed the clues fit an accident, explained {suspect.motive}, and showed that the spill was not a theft.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a little hint about something that will matter later.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is when a story briefly shows something that happened earlier.",
        ),
        QAItem(
            question="What is jello like?",
            answer="Jello is a soft, wobbly dessert that can jiggle and make a sticky mess if it spills.",
        ),
        QAItem(
            question="What is an alley?",
            answer="An alley is a narrow path or space between buildings.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A suspect is plausible if the setting is the alley and the clue matches the story domain.
plausible_suspect(S) :- suspect(S).

% The mystery is solvable if there is exactly one suspect and the alley contains jello.
mystery_ok :- place(alley), has_jello, suspect_count(1).

% Foreshadowing and flashback are required for this world.
story_style_ok :- foreshadowing, flashback, whodunit.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    lines.append(asp.fact("has_jello"))
    lines.append(asp.fact("foreshadowing"))
    lines.append(asp.fact("flashback"))
    lines.append(asp.fact("whodunit"))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    lines.append(asp.fact("suspect_count", len(SUSPECTS)))
    return "\n".join(lines)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show mystery_ok/0.\n#show story_style_ok/0."))
    atoms = {a.name for a in model}
    expected = {"mystery_ok", "story_style_ok"}
    if atoms == expected:
        print("OK: ASP rules accept the jello alley whodunit.")
        return 0
    print("MISMATCH: ASP rules did not accept the expected storyworld.")
    print("atoms:", sorted(atoms))
    return 1


# ---------------------------------------------------------------------------
# Generation / output
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = tell_story(world, params)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        bits = []
        if ent.location:
            bits.append(f"location={ent.location}")
        if ent.held_by:
            bits.append(f"held_by={ent.held_by}")
        if ent.memes:
            bits.append(f"memes={dict(ent.memes)}")
        lines.append(f"  {ent.id}: {ent.type} {' '.join(bits)}")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small jello-alley whodunit storyworld.")
    ap.add_argument("--place", choices=list(SETTINGS))
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-type", choices=["girl", "boy"])
    ap.add_argument("--witness-name")
    ap.add_argument("--witness-type", choices=["girl", "boy"])
    ap.add_argument("--suspect", choices=list(SUSPECTS))
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
    return StoryParams(
        place=args.place or "alley",
        detective_name=args.detective_name or rng.choice(GIRL_NAMES + BOY_NAMES),
        detective_type=args.detective_type or rng.choice(["girl", "boy"]),
        witness_name=args.witness_name or rng.choice(WITNESS_NAMES),
        witness_type=args.witness_type or rng.choice(["girl", "boy"]),
        suspect=args.suspect or rng.choice(list(SUSPECTS)),
    )


def curated_params() -> list[StoryParams]:
    return [
        StoryParams("alley", "Maya", "girl", "Tom", "boy", "cat"),
        StoryParams("alley", "Leo", "boy", "June", "girl", "neighbor"),
        StoryParams("alley", "Ivy", "girl", "Ari", "boy", "kid"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mystery_ok/0.\n#show story_style_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show mystery_ok/0.\n#show story_style_ok/0."))
        print("ASP model atoms:")
        for atom in model:
            print(atom)
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in curated_params():
            p.seed = seed
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(seed + i))
            params.seed = seed + i
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
