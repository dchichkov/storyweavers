#!/usr/bin/env python3
"""
storyworlds/worlds/javelin_suspense_sharing_whodunit.py
=======================================================

A standalone storyworld for a tiny whodunit: a missing javelin, a little
suspense, and a sharing-based reveal.

Premise:
- A child plans a careful javelin throw in a small field.
- A prized javelin goes missing, and everyone suspects the wrong person.
- The truth is found through close observation of shared objects and clues.
- The ending proves what changed: the javelin is recovered, and the group
  agrees to share the practice time fairly.

This world models:
- physical meters: distance, hiddenness, dampness, sharpness risk, track marks
- emotional memes: worry, suspicion, calm, trust, generosity, relief

It follows the storyworld contract:
- self-contained stdlib script
- eager import of storyworlds/results.py for QAItem, StoryError, StorySample
- lazy import of storyworlds/asp.py inside ASP helpers
- build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carries: Optional[str] = None
    hidden: bool = False
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    setting_line: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    region: str
    risky_for: set[str] = field(default_factory=set)
    plural: bool = False


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    reveals: str
    sharing_hint: str


@dataclass
class StoryParams:
    place: str
    javelin: str
    clue: str
    hero: str
    hero_gender: str
    witness: str
    witness_gender: str
    adult: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _py_story(name: str, *args):
    return locals()


def _spread_suspense(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters.get("hidden", 0) >= THRESHOLD and ("mystery", e.id) not in world.fired:
            world.fired.add(("mystery", e.id))
            e.memes["worry"] = e.memes.get("worry", 0) + 1
            for other in world.entities.values():
                if other.kind == "character" and other.id != e.id:
                    other.memes["suspicion"] = other.memes.get("suspicion", 0) + 1
            out.append("__suspense__")
    return out


def _resolve_clue(world: World) -> list[str]:
    out = []
    if world.facts.get("clue_found") and ("sharing", "reveal") not in world.fired:
        world.fired.add(("sharing", "reveal"))
        for e in world.entities.values():
            if e.kind == "character":
                e.memes["relief"] = e.memes.get("relief", 0) + 1
                e.memes["trust"] = e.memes.get("trust", 0) + 1
        out.append("__reveal__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_spread_suspense, _resolve_clue):
            xs = rule(world)
            if xs:
                changed = True
                produced.extend(xs)
    if narrate:
        for s in produced:
            if s.startswith("__"):
                continue
            world.say(s)
    return produced


def valid_combo(place: Place, javelin: Thing, clue: Clue) -> bool:
    return "javelin" in place.affords and "clue" in clue.reveals and javelin.region == "field"


def select_unwound_clue(javelin: Thing, clue: Clue) -> bool:
    return javelin.id == "practice_javelin" and clue.id in {"rope_loop", "chalk_mark", "mud_print"}


def tell(place: Place, javelin: Thing, clue: Clue, hero_name: str, hero_gender: str,
         witness_name: str, witness_gender: str, adult: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name))
    witness = world.add(Entity(id=witness_name, kind="character", type=witness_gender, label=witness_name))
    adult_ent = world.add(Entity(id="adult", kind="character", type=adult, label=f"the {adult}"))
    obj = world.add(Entity(id=javelin.id, type="thing", label=javelin.label, plural=javelin.plural,
                           location=place.label, hidden=True))
    clue_ent = world.add(Entity(id=clue.id, type="thing", label=clue.label, location=place.label))
    hero.memes["calm"] = 1
    witness.memes["calm"] = 1

    world.say(f"{hero.id} and {witness.id} came to {place.label}. {place.setting_line}")
    world.say(f"{hero.id} loved the long practice javelin because {hero.pronoun('subject')} was careful and proud of {javelin.phrase}.")
    world.say(f"That morning, the javelin was missing from its hook, and the field felt strangely quiet.")

    world.para()
    world.say(f"{witness.id} noticed {clue.phrase} near the practice lane, but nobody touched it at first.")
    hero.memes["worry"] = 1
    witness.memes["suspicion"] = 1
    propagate(world, narrate=False)
    world.say(f"{hero.id} frowned. “Who took the javelin?” {hero.pronoun('subject').capitalize()} asked.")
    world.say(f"{witness.id} whispered that the clue looked like it belonged to someone who had been sharing space near the lane.")

    world.para()
    if select_unwound_clue(javelin, clue):
        world.say(f"Then {witness.id} remembered the shared bundle of cords and the muddy track beside the shed.")
        world.say(f"The clue was not a theft at all. It pointed to the wind-blown practice cover that had slipped off the hook.")
        clue_ent.meters["revealed"] = 1
        world.facts["clue_found"] = True
        obj.hidden = False
        obj.owner = hero.id
        obj.location = "the shed shelf"
        propagate(world, narrate=False)
        world.say(f"{adult_ent.id} lifted the cover, and there was the javelin, safe on the shelf, exactly where a shared tidy-up had left it.")
        world.say(f"{hero.id} let out a shaky laugh, and {witness.id} laughed too, because the mystery had an ordinary answer.")
        world.para()
        world.say(f"At the end, they agreed to share the practice gear list, the cleaning jobs, and the first turn with the javelin.")
        world.say(f"{hero.id} held the javelin again, but this time the whole group felt calmer, as if the field itself had stopped holding its breath.")
    else:
        world.say(f"The clue stayed confusing, so the mystery did not clear up yet.")
        world.say(f"{adult_ent.id} told them to keep searching together and not to touch the javelin until everyone had looked carefully.")
    world.facts.update(hero=hero, witness=witness, adult=adult_ent, javelin=obj, clue=clue_ent, trait=trait, place=place)
    return world


PLACES = {
    "field": Place(
        id="field",
        label="the small field",
        setting_line="A narrow lane cut through the grass, and a practice hook waited beside the shed.",
        affords={"javelin"},
    ),
    "schoolyard": Place(
        id="schoolyard",
        label="the schoolyard",
        setting_line="A chalk line marked the throwing area, and the fence cast long shadows.",
        affords={"javelin"},
    ),
}

JAVELINS = {
    "practice_javelin": Thing(
        id="practice_javelin",
        label="practice javelin",
        phrase="the bright practice javelin on the hook",
        region="field",
        risky_for={"scratch"},
    ),
    "red_javelin": Thing(
        id="red_javelin",
        label="red javelin",
        phrase="the red javelin with the smooth grip",
        region="field",
        risky_for={"scratch"},
    ),
}

CLUES = {
    "rope_loop": Clue(
        id="rope_loop",
        label="a loop of rope",
        phrase="a loop of rope near the lane",
        reveals="sharing clue rope",
        sharing_hint="It matched the bundle everyone had used together.",
    ),
    "chalk_mark": Clue(
        id="chalk_mark",
        label="a chalk mark",
        phrase="a chalk mark by the hook",
        reveals="sharing clue chalk",
        sharing_hint="It showed where the javelin had last been shared and set down.",
    ),
    "mud_print": Clue(
        id="mud_print",
        label="a muddy print",
        phrase="a muddy print by the shed",
        reveals="sharing clue mud",
        sharing_hint="It led from the shared cover to the shelf.",
    ),
}

HEROES = ["Mina", "Leo", "Nora", "Eli", "Ava", "Tess", "Finn", "Maya"]
WITNESSES = ["Iris", "Owen", "Zoe", "Kai", "June", "Arlo", "Luca", "Pia"]


@dataclass
class QAGuide:
    topic: str
    answer: str


KNOWLEDGE = {
    "javelin": [
        ("What is a javelin?", "A javelin is a long, light spear used in sports practice. It should be handled carefully and only where it is safe to throw."),
    ],
    "sharing": [
        ("What does sharing mean?", "Sharing means letting other people use something too, or taking turns so everyone gets a fair chance."),
    ],
    "mystery": [
        ("What is a mystery?", "A mystery is a problem where you do not know the answer yet, so you look for clues."),
    ],
    "clue": [
        ("What is a clue?", "A clue is a little piece of information that helps solve a mystery."),
    ],
    "suspense": [
        ("What is suspense?", "Suspense is the tense feeling you get when you are waiting to find out what will happen next."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit for a child where a javelin goes missing in {f["place"].label} and the answer is found by sharing clues.',
        f"Tell a suspenseful but gentle mystery about {f['hero'].id} and {f['witness'].id} searching for a missing javelin.",
        f'Write a simple story with the word "javelin" that ends with the children sharing the practice gear fairly.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    witness = f["witness"]
    adult = f["adult"]
    javelin = f["javelin"]
    clue = f["clue"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the story about in {place.label}?",
            answer=f"It was about {hero.id} and {witness.id}, who found a mystery around the missing javelin in {place.label}.",
        ),
        QAItem(
            question=f"What was missing from the hook?",
            answer=f"The practice javelin was missing, and that made everyone feel a little worried until they followed the clue.",
        ),
        QAItem(
            question=f"What clue helped solve the mystery?",
            answer=f"{clue.label.capitalize()} helped. It pointed toward where the javelin had been left after a shared tidy-up.",
        ),
        QAItem(
            question=f"Who helped when the mystery got solved?",
            answer=f"{adult.id} helped by lifting the cover and showing that the javelin had simply been tucked away safely.",
        ),
        QAItem(
            question=f"What did the children do at the end?",
            answer=f"They agreed to share the practice gear list, the cleaning jobs, and the first turn with the javelin.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ("mystery", "clue", "suspense", "javelin", "sharing"):
        for q, a in KNOWLEDGE[key]:
            out.append(QAItem(question=q, answer=a))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.hidden:
            bits.append("hidden=True")
        if e.location:
            bits.append(f"location={e.location}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:16} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,J,C) :- place(P), javelin(J), clue(C), affords(P,javelin), clue_reveals(C,sharing), javelin_region(J,field).
solved(P,J,C) :- valid(P,J,C).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for a in sorted(PLACES[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for jid, j in JAVELINS.items():
        lines.append(asp.fact("javelin", jid))
        lines.append(asp.fact("javelin_region", jid, j.region))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_reveals", cid, "sharing"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set((p, j, c) for p in PLACES for j in JAVELINS for c in CLUES if valid_combo(PLACES[p], JAVELINS[j], CLUES[c]))
    if asp_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("MISMATCH")
    print("only in asp:", sorted(asp_set - py_set))
    print("only in python:", sorted(py_set - asp_set))
    return 1


def valid_combo(place: Place, javelin: Thing, clue: Clue) -> bool:
    return "javelin" in place.affords and javelin.region == "field" and "sharing" in clue.reveals


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    javelin = args.javelin or rng.choice(list(JAVELINS))
    clue = args.clue or rng.choice(list(CLUES))
    if not valid_combo(PLACES[place], JAVELINS[javelin], CLUES[clue]):
        raise StoryError("That combination does not make a plausible javelin mystery.")
    hero = args.hero or rng.choice(HEROES)
    witness = args.witness or rng.choice([n for n in WITNESSES if n != hero])
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    witness_gender = args.witness_gender or rng.choice(["girl", "boy"])
    adult = args.adult or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(["careful", "curious", "patient", "thoughtful"])
    return StoryParams(place, javelin, clue, hero, hero_gender, witness, witness_gender, adult, trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], JAVELINS[params.javelin], CLUES[params.clue],
                 params.hero, params.hero_gender, params.witness, params.witness_gender,
                 params.adult, params.trait)
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
    ap = argparse.ArgumentParser(description="A tiny whodunit about a missing javelin, suspense, and sharing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--javelin", choices=JAVELINS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--witness")
    ap.add_argument("--witness-gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["mother", "father"])
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams("field", "practice_javelin", "rope_loop", "Mina", "girl", "Leo", "boy", "mother", "careful"),
    StoryParams("schoolyard", "red_javelin", "chalk_mark", "Nora", "girl", "Eli", "boy", "father", "curious"),
    StoryParams("field", "red_javelin", "mud_print", "Ava", "girl", "Kai", "boy", "mother", "thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                p = resolve_params(args, random.Random((args.seed or 0) + i))
            except StoryError as e:
                print(e)
                return
            p.seed = (args.seed or 0) + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} and {p.witness} | {p.place} | {p.javelin} | {p.clue}"
        elif len(samples) > 1:
            header = f"### variant {idx+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
