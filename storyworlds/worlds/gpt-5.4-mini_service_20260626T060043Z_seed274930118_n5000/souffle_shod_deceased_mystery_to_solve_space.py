#!/usr/bin/env python3
"""
storyworlds/worlds/souffle_shod_deceased_mystery_to_solve_space.py
===================================================================

A small space-adventure mystery world: a crew, a strange soufflé, special shod
boots, and a case about a deceased captain's last clue.

Premise:
- The crew is aboard a little starship with a kitchen, a map room, and a dock.
- A fluffy soufflé has gone missing from the galley.
- A deceased captain left behind a trail of clues.
- The crew must solve the mystery by checking places, gear, and records.

World model:
- Characters have meters for physical conditions and memes for emotional state.
- Objects can be worn, carried, or left in rooms.
- The story follows a concrete investigation: discovery, doubt, clue-finding,
  and a final reveal.

Style:
- Space Adventure, but child-facing and gentle.
- Every story ends with a clear solution image proving what changed.
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

PLACES = ["galley", "airlock", "map room", "cargo bay", "observation deck"]
CHARACTER_TYPES = ["captain", "pilot", "mechanic", "navigator", "cook"]
GENDERS = ["girl", "boy"]
TRAITS = ["brave", "curious", "careful", "cheerful", "steady", "sharp"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    room: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"dusty": 0.0, "lost": 0.0, "tired": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "hope": 0.0, "grief": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot", "mechanic", "navigator", "cook"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    name: str
    kind: str
    clues: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    place: str
    points_to: str
    discovered_by: Optional[str] = None


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_gender: str
    hero_type: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.places: dict[str, Place] = {k: Place(name=k, kind=k) for k in PLACES}
        self.clues: dict[str, Clue] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        self.places[clue.place].clues.add(clue.id)
        return clue

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def get(self, eid: str) -> Entity:
        return self.entities[eid]


def _subject_name(entity: Entity) -> str:
    return entity.id


def _char_desc(entity: Entity) -> str:
    trait = next((t for t in entity.traits if t != "little"), "")
    return f"little {trait} {entity.type}".strip()


def build_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=["little", params.trait],
    ))
    friend = w.add(Entity(
        id="Quill",
        kind="character",
        type="navigator",
        traits=["tiny", "quick"],
    ))
    deceased_captain = w.add(Entity(
        id="CaptainSol",
        kind="character",
        type="captain",
        traits=["wise"],
    ))
    deceased_captain.memes["grief"] = 1.0

    w.add(Entity(
        id="souffle",
        type="souffle",
        label="soufflé",
        phrase="a warm cheese soufflé",
        owner="CaptainSol",
        carried_by="Quill",
        room="galley",
    ))
    w.add(Entity(
        id="boots",
        type="boots",
        label="shod boots",
        phrase="shiny shod boots",
        owner=params.hero_name,
        worn_by=params.hero_name,
        room=params.place,
        plural=True,
    ))

    w.add_clue(Clue(
        id="crumbs",
        label="crumb trail",
        phrase="tiny crumbs that floated like stars",
        place="airlock",
        points_to="galley",
    ))
    w.add_clue(Clue(
        id="note",
        label="note",
        phrase="a note with the captain's last words",
        place="map room",
        points_to="airlock",
    ))
    w.add_clue(Clue(
        id="spoon",
        label="silver spoon",
        phrase="a silver spoon tucked behind a panel",
        place="cargo bay",
        points_to="map room",
    ))

    w.facts.update(
        hero=hero,
        friend=friend,
        captain=deceased_captain,
        souffle=w.get("souffle"),
        boots=w.get("boots"),
        starting_place=params.place,
    )
    return w


def reason_gate(params: StoryParams) -> None:
    if params.place not in PLACES:
        raise StoryError("The ship has no such place.")
    if params.hero_gender not in GENDERS:
        raise StoryError("The hero must be a girl or a boy.")
    if params.hero_type not in CHARACTER_TYPES:
        raise StoryError("That character type does not fit this space story.")
    if params.trait not in TRAITS:
        raise StoryError("Unknown hero trait.")


def tell_story(w: World, params: StoryParams) -> None:
    hero = w.facts["hero"]
    friend = w.facts["friend"]
    captain = w.facts["captain"]
    souffle = w.facts["souffle"]
    boots = w.facts["boots"]

    w.say(
        f"{hero.id} was a {_char_desc(hero)} aboard the starship Bright Comet, "
        f"and {hero.pronoun('subject')} loved puzzles more than naps."
    )
    w.say(
        f"One day, {hero.id} found {boots.label} on {hero.pronoun('possessive')} feet "
        f"and followed {friend.id} toward the galley, where a {souffle.phrase} was gone."
    )

    w.para()
    w.say(
        f'"The captain made that before {captain.id} died," {friend.id} said softly. '
        f'"Now the kitchen looks wrong, and the clue trail feels shod and strange."'
    )
    w.say(
        f"{hero.id} blinked at the word shod, then noticed the little crumbs on the floor. "
        f"{hero.pronoun('subject').capitalize()} knew the first mystery was not about a thief with big pockets; "
        f"it was about where the crumbs had drifted."
    )

    w.para()
    w.say(
        f"{hero.id} and {friend.id} moved from the galley to the airlock. "
        f"There, tiny crumbs floated near the seal like pale moons."
    )
    w.say(
        f"That meant the souffle had been moved after the captain's last flight walk, "
        f"and the next clue had to be deeper inside the ship."
    )

    w.para()
    w.say(
        f"They hurried to the map room. Behind the table, {hero.id} found a note with "
        f"{captain.pronoun('possessive')} careful handwriting: "
        f'"Check the cargo bay. The answer is not lost. It is waiting."'
    )
    w.say(
        f"{hero.id} smiled, because a deceased captain could still leave a kind trail for a brave crew."
    )

    w.para()
    w.say(
        f"In the cargo bay, {hero.id} found a silver spoon tucked behind a panel, "
        f"and beside it sat the missing soufflé in a warm travel tin."
    )
    w.say(
        f"It had not been stolen at all. {captain.id} had hidden it there as a surprise feast for the crew "
        f"before {captain.pronoun('subject')} died, and the note had guided them to it."
    )

    w.para()
    w.say(
        f"{hero.id} carried the tin back to the galley, still shod in the shiny boots, "
        f"while {friend.id} laughed with relief. "
        f"Together they served the souffle to the whole ship and placed the captain's note beside the table, "
        f"so the mystery ended in warm light instead of worry."
    )

    w.facts.update(
        resolved=True,
        clue_order=["crumbs", "note", "spoon"],
        ending_place="galley",
        souffle_found=True,
        deceased=True,
    )


def generation_prompts(w: World) -> list[str]:
    hero = w.facts["hero"]
    return [
        "Write a short space-adventure mystery for a child about a missing soufflé and a gentle crew.",
        f"Tell a story where {hero.id} follows clues through a starship and solves what happened to the deceased captain's treat.",
        "Create a simple mystery with shod boots, floating crumbs, and a happy reveal in a spaceship kitchen.",
    ]


def story_qa(w: World) -> list[QAItem]:
    hero = w.facts["hero"]
    friend = w.facts["friend"]
    captain = w.facts["captain"]
    return [
        QAItem(
            question=f"Who solved the mystery in the starship?",
            answer=f"{hero.id} solved it with help from {friend.id}. {hero.id} followed the clues and found the answer.",
        ),
        QAItem(
            question="What was missing from the galley at the start?",
            answer="A warm cheese soufflé was missing from the galley.",
        ),
        QAItem(
            question="What did the note from the deceased captain say to do?",
            answer="It said to check the cargo bay because the answer was waiting there.",
        ),
        QAItem(
            question=f"Why was the story about {captain.id} sad at first?",
            answer=f"It was sad because {captain.id} had died, but the captain still left kind clues for the crew.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The crew found the soufflé, served it in the galley, and turned the mystery into a happy meal.",
        ),
    ]


def world_knowledge_qa(w: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a soufflé?",
            answer="A soufflé is a light, fluffy baked dish that can puff up in the oven.",
        ),
        QAItem(
            question="What does shod mean?",
            answer="Shod means wearing shoes or boots.",
        ),
        QAItem(
            question="What does deceased mean?",
            answer="Deceased means someone has died.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
        bits = []
        if e.room:
            bits.append(f"room={e.room}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {', '.join(bits)}")
    lines.append(f"clues: {sorted(world.clues)}")
    return "\n".join(lines)


def explain_params() -> StoryParams:
    return StoryParams(place="galley", hero_name="Nova", hero_gender="girl", hero_type="pilot", trait="curious")


def generate(params: StoryParams) -> StorySample:
    reason_gate(params)
    world = build_world(params)
    tell_story(world, params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure mystery world with a soufflé clue trail.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--hero-type", choices=CHARACTER_TYPES)
    ap.add_argument("--trait", choices=TRAITS)
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
    return StoryParams(
        place=args.place or rng.choice(PLACES),
        hero_name=args.name or rng.choice(["Nova", "Iris", "Pip", "Milo", "Luna", "Jett"]),
        hero_gender=args.gender or rng.choice(GENDERS),
        hero_type=args.hero_type or rng.choice(CHARACTER_TYPES),
        trait=args.trait or rng.choice(TRAITS),
    )


ASP_RULES = r"""
place(galley). place(airlock). place("map room"). place("cargo bay"). place("observation deck").

hero_type(captain). hero_type(pilot). hero_type(mechanic). hero_type(navigator). hero_type(cook).

clue(crumbs). clue(note). clue(spoon).

points_to(crumbs, galley).
points_to(note, "airlock").
points_to(spoon, "map room").

solves(H, M) :- hero(H), mystery(M), clue(C), points_to(C, P), target(M, P).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for t in CHARACTER_TYPES:
        lines.append(asp.fact("hero_type", t))
    for c in ["crumbs", "note", "spoon"]:
        lines.append(asp.fact("clue", c))
    lines.append(asp.fact("target", "mystery1", "cargo bay"))
    lines.append(asp.fact("hero", "Nova"))
    lines.append(asp.fact("mystery", "mystery1"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show solves/2."))
    atoms = set(asp.atoms(model, "solves"))
    expected = {("Nova", "mystery1")}
    if atoms == expected:
        print("OK: ASP parity matches Python reasoner.")
        return 0
    print("MISMATCH:", atoms, expected)
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show solves/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams(place="galley", hero_name="Nova", hero_gender="girl", hero_type="pilot", trait="curious"),
            StoryParams(place="cargo bay", hero_name="Milo", hero_gender="boy", hero_type="mechanic", trait="careful"),
            StoryParams(place="map room", hero_name="Luna", hero_gender="girl", hero_type="navigator", trait="sharp"),
        ]
        samples = [generate(p) for p in presets]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
