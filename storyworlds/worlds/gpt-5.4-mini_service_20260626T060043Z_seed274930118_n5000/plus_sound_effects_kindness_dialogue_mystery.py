#!/usr/bin/env python3
"""
A small mystery storyworld with sound effects, kindness, and dialogue.

Seed idea:
A child hears strange sounds, asks careful questions, and follows clues
to solve a gentle mystery. The turn comes from noticing a missing object,
listening for the source of the sounds, and choosing kindness over suspicion.

The domain keeps the mystery style close to TinyStories:
- concrete clues
- short, child-facing dialogue
- a clear beginning, middle turn, and ending image
- sound effects woven into the prose
- kindness as the social resolution
- "plus" is used in both the title sense and the story prompts
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

MYSTERY_THRESHOLD = 1.0


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
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    feels: str
    hides: set[str] = field(default_factory=set)
    echoes: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    source_sound: str
    location: str
    reveals: str
    kind: str = "object"


@dataclass
class Mystery:
    id: str
    missing_label: str
    missing_phrase: str
    owner_label: str
    sound_trail: list[str]
    culprit: str
    helper: str
    resolution: str
    secret_place: str
    plus_item: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.clues: dict[str, Clue] = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sound_track: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def add_clue(self, clue: Clue) -> Clue:
        self.clues[clue.id] = clue
        return clue

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.clues = copy.deepcopy(self.clues)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        clone.sound_track = list(self.sound_track)
        return clone


def sound(text: str) -> str:
    return text


def ask_sound(question: str) -> str:
    return question


def kindness_line(helper: Entity, other: Entity) -> str:
    return f"{helper.id} spoke kindly to {other.id}."


def make_noise(world: World, noise: str) -> None:
    world.sound_track.append(noise)
    world.say(noise)


def reveal_clue(world: World, clue: Clue) -> None:
    sig = ("reveal", clue.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.say(clue.reveals)


def pursue_mystery(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curious"] = hero.memes.get("curious", 0.0) + 1
    world.say(
        f"{hero.id} heard {mystery.sound_trail[0]} and frowned. "
        f'"What was that?" {hero.pronoun()} asked.'
    )
    make_noise(world, mystery.sound_trail[0])
    world.say(
        f"{hero.id} looked around the {world.place.label.lower()}, where everything felt {world.place.feels}."
    )


def ask_and_listen(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    world.say(f'"Did you hear that too?" {hero.id} asked.')
    world.say(f'"I did," said {helper.id}. "Let’s listen carefully."')
    hero.memes["trust"] = hero.memes.get("trust", 0.0) + 1
    helper.memes["kind"] = helper.memes.get("kind", 0.0) + 1


def follow_clues(world: World, mystery: Mystery) -> None:
    for clue_text in mystery.sound_trail[1:]:
        make_noise(world, clue_text)
    world.para()


def solve(world: World, hero: Entity, helper: Entity, mystery: Mystery, clue: Clue) -> None:
    world.say(
        f"At last, {hero.id} and {helper.id} found the clue: {clue.label}."
    )
    world.say(
        f"It had been hiding {clue.location}, and that explained the strange sounds."
    )
    world.say(
        f'"Aha!" said {hero.id}. "So the mystery was just {mystery.resolution}!"'
    )
    world.say(
        f'{helper.id} smiled. "Plus, we found {mystery.plus_item} along the way."'
    )


def gentle_finish(world: World, hero: Entity, helper: Entity, owner: Entity, mystery: Mystery) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    owner.memes["relief"] = owner.memes.get("relief", 0.0) + 1
    world.say(
        f"{owner.id} laughed with relief and thanked them both."
    )
    world.say(
        f"{hero.id} felt proud, because {mystery.missing_label} was back where it belonged, and everyone was being kind."
    )


def trace_world(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:10} ({ent.type:8}) {' '.join(bits)}")
    if world.sound_track:
        lines.append(f"  sounds: {world.sound_track}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
    owner_name: str
    missing_item: str
    clue_item: str
    mystery_id: str
    seed: Optional[int] = None


PLACES = {
    "hall": Place(id="hall", label="the hall", feels="quiet", hides={"under the bench", "behind the curtain"}, echoes={"tap-tap", "tick-tick"}),
    "garden": Place(id="garden", label="the garden", feels="soft and leafy", hides={"under the bush", "by the flower pot"}, echoes={"rustle-rustle", "drip-drip"}),
    "kitchen": Place(id="kitchen", label="the kitchen", feels="bright and busy", hides={"inside the cupboard", "behind the chair"}, echoes={"clink-clink", "plink-plink"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        missing_label="the little bell",
        missing_phrase="a tiny silver bell",
        owner_label="the shopkeeper",
        sound_trail=["ding-ding", "tap-tap", "plink"],
        culprit="a curious kitten",
        helper="a gentle friend",
        resolution="a kitten had rolled the bell under the bench",
        secret_place="under the bench",
        plus_item="a ribbon",
    ),
    "book": Mystery(
        id="book",
        missing_label="the picture book",
        missing_phrase="a bright picture book",
        owner_label="the teacher",
        sound_trail=["flip-flip", "shff", "tap-tap"],
        culprit="a helpful mouse",
        helper="a patient friend",
        resolution="a mouse had tucked the book behind the curtain",
        secret_place="behind the curtain",
        plus_item="a bookmark",
    ),
    "key": Mystery(
        id="key",
        missing_label="the brass key",
        missing_phrase="a small brass key",
        owner_label="the neighbor",
        sound_trail=["clink-clink", "plink-plink", "tap"],
        culprit="a playful puppy",
        helper="a kind neighbor",
        resolution="a puppy had nudged the key by the chair",
        secret_place="behind the chair",
        plus_item="a shiny coin",
    ),
}

HERO_NAMES = ["Mia", "Leo", "Nora", "Ava", "Ben", "Theo"]
HELPER_NAMES = ["June", "Sam", "Ivy", "Max", "Rose", "Finn"]


def valid_combos() -> list[tuple[str, str]]:
    return [(place_id, mystery_id) for place_id in PLACES for mystery_id in MYSTERIES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld with sound effects, kindness, and dialogue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--owner-name")
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
    place = args.place or rng.choice(list(PLACES))
    mystery_id = args.mystery or rng.choice(list(MYSTERIES))
    if (place, mystery_id) not in valid_combos():
        raise StoryError("No valid mystery matches those options.")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    helper_name = args.helper_name or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    owner_name = args.owner_name or rng.choice(["Mrs. Bell", "Mr. Pine", "Ms. Wren"])
    hero_type = "girl" if hero_name in {"Mia", "Nora", "Ava", "Rose", "June", "Ivy"} else "boy"
    helper_type = "girl" if helper_name in {"Mia", "Nora", "Ava", "Rose", "June", "Ivy"} else "boy"
    return StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
        owner_name=owner_name,
        missing_item=MYSTERIES[mystery_id].missing_label,
        clue_item=MYSTERIES[mystery_id].plus_item,
        mystery_id=mystery_id,
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    mystery = MYSTERIES[params.mystery_id]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    owner = world.add(Entity(id=params.owner_name, kind="character", type="person"))

    clue = world.add_clue(Clue(
        id="clue",
        label=f"the {params.clue_item}",
        source_sound=mystery.sound_trail[-1],
        location=mystery.secret_place,
        reveals=f"The {params.clue_item} gave a tiny clue.",
    ))

    world.facts.update(hero=hero, helper=helper, owner=owner, clue=clue, mystery=mystery, place=place)

    world.say(f"{hero.id} was in {place.label}, where the air felt {place.feels}.")
    world.say(f"{hero.id} liked mysteries, because every clue could lead somewhere new.")
    world.para()

    pursue_mystery(world, hero, mystery)
    ask_and_listen(world, hero, helper, mystery)
    follow_clues(world, mystery)
    world.say(f"{helper.id} pointed. " + sound("Tap, tap!"))
    reveal_clue(world, clue)
    solve(world, hero, helper, owner, mystery, clue)
    world.para()
    world.say(f"Then everyone smiled, because kindness had helped solve the mystery.")
    gentle_finish(world, hero, helper, owner, mystery)

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
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    return [
        f'Write a short mystery story for a young child that uses the sound "{mystery.sound_trail[0]}" and includes the word "plus".',
        f"Tell a gentle mystery about {hero.id} and {helper.id} listening for clues in {world.place.label}.",
        f"Write a child-friendly story where kindness, dialogue, and sound effects help solve a missing-object mystery.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery: Mystery = f["mystery"]
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    owner: Entity = f["owner"]
    clue: Clue = f["clue"]
    return [
        QAItem(
            question=f"What was missing in the mystery?",
            answer=f"{owner.id} was looking for {mystery.missing_label}, which was {mystery.missing_phrase}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} listen for clues?",
            answer=f"{helper.id} helped {hero.id} listen carefully and follow the sounds.",
        ),
        QAItem(
            question=f"What clue did they find?",
            answer=f"They found {clue.label}, and it gave them one more clue to solve the mystery.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the missing item found, the answer explained, and everyone feeling kind and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps you figure out what happened.",
        ),
        QAItem(
            question="Why do people listen carefully in a mystery?",
            answer="People listen carefully so they can notice small sounds and use them to solve the puzzle.",
        ),
        QAItem(
            question="Why is kindness helpful?",
            answer="Kindness helps people stay calm, work together, and solve problems without being mean.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    return trace_world(world)


ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- case(M).
valid(P,M) :- place(P), mystery(M).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("case", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def explain_rejection() -> str:
    return "No valid combination matches the given options."


CURATED = [
    StoryParams(
        place="hall",
        hero_name="Mia",
        hero_type="girl",
        helper_name="Sam",
        helper_type="boy",
        owner_name="Mrs. Bell",
        missing_item="the little bell",
        clue_item="ribbon",
        mystery_id="bell",
    ),
    StoryParams(
        place="garden",
        hero_name="Leo",
        hero_type="boy",
        helper_name="Ivy",
        helper_type="girl",
        owner_name="Mr. Pine",
        missing_item="the picture book",
        clue_item="bookmark",
        mystery_id="book",
    ),
    StoryParams(
        place="kitchen",
        hero_name="Nora",
        hero_type="girl",
        helper_name="Finn",
        helper_type="boy",
        owner_name="Ms. Wren",
        missing_item="the brass key",
        clue_item="shiny coin",
        mystery_id="key",
    ),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible place/mystery combos:")
        for place, mystery in triples:
            print(f"  {place:8} {mystery}")
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
            header = f"### {p.hero_name}: {p.mystery_id} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
