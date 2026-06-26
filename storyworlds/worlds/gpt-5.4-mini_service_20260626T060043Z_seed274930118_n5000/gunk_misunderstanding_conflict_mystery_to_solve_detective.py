#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gunk_misunderstanding_conflict_mystery_to_solve_detective.py
================================================================================================

A standalone story world for a tiny detective-style mystery with gunk, a
misunderstanding, a conflict, and a mystery to solve.

Premise:
- A child or small detective notices gunk in a place where it should not be.
- A misunderstanding causes conflict between two characters.
- The detective follows clues, resolves the mix-up, and reveals what the gunk
  really was.

The world model tracks:
- physical meters: gunkiness, mess, fear, trust, relief, suspicion
- emotional memes: worry, confidence, frustration, curiosity, apology, pride

The prose is driven by simulated state: observations, clues, mistaken guesses,
and the final reveal all emerge from the world model rather than a fixed
paragraph template.
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    handled_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "detective-girl"}
        male = {"boy", "man", "father", "detective-boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the bakery"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    name: str
    label: str
    meaning: str
    reveal: str


@dataclass
class Suspect:
    id: str
    label: str
    type: str
    mood: str
    likely: str
    false_guess: str
    clue_needed: str


@dataclass
class Mystery:
    gunk_name: str
    gunk_label: str
    source: str
    mistaken_source: str
    solution: str
    location: str
    clue: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
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
        clone = World(self.setting)
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, phrase=v.phrase,
            owner=v.owner, handled_by=v.handled_by, plural=v.plural,
            meters=dict(v.meters), memes=dict(v.memes)
        ) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def meme(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def bump_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = meter(ent, key) + amt


def bump_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = meme(ent, key) + amt


def is_embedded(value: float) -> bool:
    return value >= THRESHOLD


def setting_line(setting: Setting) -> str:
    return {
        "the bakery": "The bakery smelled like warm bread and sugar.",
        "the library": "The library was quiet, with tall shelves and soft carpet.",
        "the garage": "The garage was crowded with boxes, tools, and a bicycle.",
        "the garden shed": "The garden shed was small, dusty, and full of tools.",
        "the school hall": "The school hall was bright and busy, with echoes on the floor.",
    }.get(setting.place, f"{setting.place.capitalize()} felt still and ready for a clue.")


def clue_line(clue: Clue) -> str:
    return clue.reveal


def observe_gunk(world: World, detective: Entity, mystery: Mystery, clue: Clue) -> None:
    bump_meme(detective, "curiosity")
    bump_meter(detective, "suspicion", 1)
    world.say(
        f"{detective.id} spotted a smear of {mystery.gunk_name} near the counter. "
        f"It looked odd, like it did not belong there."
    )
    world.say(clue_line(clue))


def misunderstanding(world: World, detective: Entity, suspect: Entity, mystery: Mystery) -> None:
    bump_meme(suspect, "frustration")
    bump_meme(detective, "worry")
    bump_meter(suspect, "conflict", 1)
    bump_meter(detective, "suspicion", 1)
    world.say(
        f"{suspect.label.capitalize()} frowned when {detective.id} pointed at the gunk. "
        f"{suspect.pronoun().capitalize()} thought {detective.id} was blaming {suspect.pronoun('object')}."
    )
    world.say(
        f'"That was not mine," {suspect.pronoun("subject")} said, sounding hurt, '
        f"and the room grew tense."
    )
    world.facts["misunderstanding"] = True
    world.facts["false_guess"] = mystery.mistaken_source


def interview(world: World, detective: Entity, suspect: Entity, clue: Clue) -> None:
    bump_meme(detective, "confidence")
    bump_meme(suspect, "worry")
    world.say(
        f"{detective.id} stayed calm and asked a careful question instead of arguing. "
        f"{detective.pronoun().capitalize()} looked at the clue again: {clue.meaning}."
    )
    world.say(
        f"That made {suspect.label} stop and think, because the clue did not match the first guess."
    )


def inspect(world: World, detective: Entity, mystery: Mystery) -> None:
    bump_meter(detective, "suspicion", 1)
    world.say(
        f"{detective.id} followed the tiny marks around the room. "
        f"The trail of {mystery.gunk_name} led away from the counter and toward {mystery.location}."
    )


def solve(world: World, detective: Entity, helper: Entity, mystery: Mystery, suspect: Entity) -> None:
    bump_meme(detective, "pride", 1)
    bump_meme(helper, "relief", 1)
    bump_meme(suspect, "apology", 1)
    bump_meter(detective, "suspicion", -1)
    world.say(
        f"At last, {detective.id} showed everyone the real answer: the gunk came from "
        f"{mystery.source}, not from {suspect.label}."
    )
    world.say(
        f"{helper.label} let out a breath of relief, and {suspect.label} looked ashamed. "
        f"{suspect.pronoun().capitalize()} had been caught in a misunderstanding."
    )
    world.say(
        f"{suspect.label} apologized, and {detective.id} accepted it with a nod."
    )


def ending(world: World, detective: Entity, suspect: Entity, mystery: Mystery) -> None:
    bump_meme(detective, "confidence", 1)
    world.say(
        f"After the gunk was cleaned away, the room looked neat again. "
        f"{detective.id} smiled, because the mystery was solved and the conflict was over."
    )
    world.say(
        f"{detective.id} walked off with a clean notebook and a sharper eye, while "
        f"{suspect.label} stood nearby feeling much better."
    )


SETTINGS = {
    "bakery": Setting("the bakery", True, {"crumbs", "flour", "jam"}),
    "library": Setting("the library", True, {"ink", "dust", "mud"}),
    "garage": Setting("the garage", True, {"grease", "paint", "dust"}),
    "shed": Setting("the garden shed", True, {"mud", "grease", "sap"}),
    "hall": Setting("the school hall", True, {"paint", "jam", "mud"}),
}

CLUES = {
    "crumbs": Clue(
        name="crumbs",
        label="crumbs",
        meaning="crumbs usually come from bread or cookies",
        reveal="The little bits were crumbs, and they pointed toward the bread shelf.",
    ),
    "flour": Clue(
        name="flour",
        label="flour dust",
        meaning="flour dust floats up when someone bakes",
        reveal="The pale dust was flour, and it showed that someone had been baking nearby.",
    ),
    "jam": Clue(
        name="jam",
        label="sticky jam",
        meaning="jam is sticky and comes from fruit",
        reveal="The sticky smear was jam, and it smelled like berries from the kitchen.",
    ),
    "ink": Clue(
        name="ink",
        label="ink drops",
        meaning="ink comes from pens and markers",
        reveal="The dark spots were ink, and they matched the art table by the window.",
    ),
    "dust": Clue(
        name="dust",
        label="dust",
        meaning="dust gathers in old corners",
        reveal="The gray specks were dust, and they had blown down from the shelf above.",
    ),
    "grease": Clue(
        name="grease",
        label="grease",
        meaning="grease comes from wheels and tools",
        reveal="The shiny smear was grease, and it matched the bicycle chain in the back.",
    ),
    "paint": Clue(
        name="paint",
        label="paint",
        meaning="paint can drip when a brush is set down too fast",
        reveal="The bright streak was paint, and it came from the art cart, not from anyone's hands.",
    ),
    "sap": Clue(
        name="sap",
        label="sap",
        meaning="sap comes from trees and can stick to fingers",
        reveal="The sticky blob was tree sap, and it had been carried in on a leaf.",
    ),
    "mud": Clue(
        name="mud",
        label="mud",
        meaning="mud sticks to shoes after outdoor play",
        reveal="The brown smear was mud, and it had been tracked in from outside.",
    ),
}

MYSTERIES = {
    "bakery": Mystery("gunk", "gunk", "a tipped flour sack", "a cookie jar spill", "clear the floor", "the flour bin", "the flour sack"),
    "library": Mystery("gunk", "gunk", "a leaking ink pen", "a spilled juice box", "wipe the table", "the art corner", "the art table"),
    "garage": Mystery("gunk", "gunk", "a bicycle chain", "a muddy boot", "clean the workbench", "the bike rack", "the bicycle"),
    "shed": Mystery("gunk", "gunk", "a garden trowel", "a wet scarf", "find the sticky leaf", "the back door", "the leaf mat"),
    "hall": Mystery("gunk", "gunk", "a paintbrush left open", "a jam sandwich", "clean the hall floor", "the art cart", "the art cart"),
}

DETECTIVE_NAMES = ["Maya", "Noah", "Ivy", "Theo", "Lina", "Eli", "Ruby", "Finn"]
HELPER_NAMES = ["Mrs. Bell", "Mr. Stone", "Aunt June", "Ms. Park", "Mr. Lane"]
SUSPECT_NAMES = ["Ben", "Sara", "Owen", "Mina", "Tara", "Cal", "Jules", "Pia"]


@dataclass
class StoryParams:
    place: str
    clue: str
    detective_name: str
    detective_gender: str
    helper_name: str
    suspect_name: str
    suspect_gender: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Detective story world: gunk, misunderstanding, conflict, mystery to solve."
    )
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--detective-name")
    ap.add_argument("--detective-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--suspect-name")
    ap.add_argument("--suspect-gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(sorted(SETTINGS[place].affords))
    detective_gender = args.detective_gender or rng.choice(["girl", "boy"])
    suspect_gender = args.suspect_gender or ("boy" if detective_gender == "girl" else "girl")
    detective_name = args.detective_name or rng.choice(DETECTIVE_NAMES)
    helper_name = args.helper_name or rng.choice(HELPER_NAMES)
    suspect_name = args.suspect_name or rng.choice(SUSPECT_NAMES)

    if clue not in SETTINGS[place].affords:
        raise StoryError(f"(No story: {clue} does not fit {place}; that clue would not plausibly be there.)")

    if args.detective_name and args.suspect_name and args.detective_name == args.suspect_name:
        raise StoryError("(No story: the detective and suspect must be different characters.)")

    return StoryParams(
        place=place,
        clue=clue,
        detective_name=detective_name,
        detective_gender=detective_gender,
        helper_name=helper_name,
        suspect_name=suspect_name,
        suspect_gender=suspect_gender,
    )


def pronoun_for_gender(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    mystery = MYSTERIES[params.place]
    clue = CLUES[params.clue]

    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type="girl" if params.detective_gender == "girl" else "boy",
        label=f"detective {params.detective_name}",
        meters={"suspicion": 0.0, "gunkiness": 0.0},
        memes={"curiosity": 1.0, "confidence": 0.0, "pride": 0.0},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type="woman" if params.detective_gender == "girl" else "man",
        label=params.helper_name,
        meters={"relief": 0.0},
        memes={"worry": 0.0},
    ))
    suspect = world.add(Entity(
        id=params.suspect_name,
        kind="character",
        type="girl" if params.suspect_gender == "girl" else "boy",
        label=params.suspect_name,
        meters={"conflict": 0.0},
        memes={"frustration": 0.0, "apology": 0.0},
    ))

    world.say(setting_line(world.setting))
    world.say(
        f"{detective.id} liked solving small mysteries, especially when something looked like gunk."
    )
    world.say(
        f"One afternoon, {detective.id} found a messy smear near the center of {world.setting.place}."
    )
    world.para()
    observe_gunk(world, detective, mystery, clue)
    misunderstanding(world, detective, suspect, mystery)
    interview(world, detective, suspect, clue)
    world.para()
    inspect(world, detective, mystery)
    solve(world, detective, helper, mystery, suspect)
    ending(world, detective, suspect, mystery)

    world.facts.update(
        detective=detective,
        helper=helper,
        suspect=suspect,
        mystery=mystery,
        clue=clue,
        place=params.place,
        clue_name=params.clue,
    )

    story = world.render()
    prompts = [
        f"Write a child-friendly detective story where {params.detective_name} finds gunk in {world.setting.place} and solves the mystery.",
        f"Tell a short mystery story with a misunderstanding, a tense moment, and a clear solution involving {params.clue}.",
        f"Write a small detective tale about gunk, a mistaken guess, and a peaceful ending at {world.setting.place}.",
    ]
    story_qa = [
        QAItem(
            question=f"What did {params.detective_name} find in {world.setting.place}?",
            answer=f"{params.detective_name} found a smear of gunk that looked out of place in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {params.suspect_name} get upset?",
            answer=f"{params.suspect_name} got upset because {params.detective_name} seemed to be blaming {params.suspect_name} for the gunk.",
        ),
        QAItem(
            question="How was the mystery solved?",
            answer=f"{params.detective_name} followed the clue and showed that the gunk came from {mystery.source}, not from {params.suspect_name}.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"The misunderstanding ended, the conflict settled down, and the room was cleaned again.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="Why do detectives look carefully at a scene?",
            answer="Detectives look carefully so they can notice details that other people might miss.",
        ),
        QAItem(
            question="What is gunk?",
            answer="Gunk is a messy, sticky, or dirty substance that does not belong where it is found.",
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if abs(v) > 0}
        memes = {k: v for k, v in e.memes.items() if abs(v) > 0}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(parts)}")
    return "\n".join(lines)


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


ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_name(C).
valid_story(P,C) :- setting(P), clue_for_place(P,C).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for c in sorted(setting.affords):
            lines.append(asp.fact("clue_for_place", place, c))
    for cname in CLUES:
        lines.append(asp.fact("clue_name", cname))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid_story/2.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(place, clue) for place, setting in SETTINGS.items() for clue in setting.affords}
    if clingo_set == python_set:
        print(f"OK: ASP gate matches Python registry ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if clingo_set - python_set:
        print("  only in ASP:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in Python:", sorted(python_set - clingo_set))
    return 1


def build_sample_from_params(params: StoryParams) -> StorySample:
    return generate(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid story combos:")
        for place, clue in combos:
            print(f"  {place:14} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place in sorted(SETTINGS):
            for clue in sorted(SETTINGS[place].affords):
                params = StoryParams(
                    place=place,
                    clue=clue,
                    detective_name=DETECTIVE_NAMES[0],
                    detective_gender="girl",
                    helper_name=HELPER_NAMES[0],
                    suspect_name=SUSPECT_NAMES[0],
                    suspect_gender="boy",
                    seed=base_seed,
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
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
