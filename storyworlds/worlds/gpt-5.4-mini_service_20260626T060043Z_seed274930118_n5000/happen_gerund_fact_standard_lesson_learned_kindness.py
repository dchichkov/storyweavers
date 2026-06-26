#!/usr/bin/env python3
"""
Standalone Storyweavers world: a small mystery about a missing thing, a kind
surprise, and a lesson learned.

Style goals:
- child-facing mystery tone
- state-driven beginning/middle/end
- lesson learned + kindness
- includes the seed words: happen-gerund, fact, standard
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    hidden: bool = False
    found: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "lady"}
        male = {"boy", "father", "dad", "man", "gentleman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoors: bool = False


@dataclass
class Mystery:
    id: str
    verb: str
    gerund: str
    clue: str
    reveal: str
    lesson: str
    kindness_move: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MissingThing:
    label: str
    phrase: str
    type: str
    clue: str
    owner_role: str = "mother"
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        return w


GIRL_NAMES = ["Mia", "Nora", "Lina", "Ivy", "Tia", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Owen", "Eli", "Finn", "Max", "Noah", "Sam"]
TRAITS = ["curious", "careful", "brave", "quiet", "gentle", "smart"]

SETTINGS = {
    "house": Setting("the house", indoors=True),
    "garden": Setting("the garden", indoors=False),
    "library": Setting("the library", indoors=True),
}

MYSTERIES = {
    "scarf": Mystery(
        id="scarf",
        verb="solve the missing scarf mystery",
        gerund="solving the missing scarf mystery",
        clue="a tiny blue thread on the chair",
        reveal="the scarf had been used to keep a shivering kitten warm",
        lesson="kindness can look like a mystery before you know the reason",
        kindness_move="wrap the scarf around the kitten first",
        tags={"fact", "standard", "happen-gerund"},
    ),
    "book": Mystery(
        id="book",
        verb="solve the missing book mystery",
        gerund="solving the missing book mystery",
        clue="a bookmark near the window",
        reveal="the book had been borrowed to read a story to a sick neighbor",
        lesson="it is kinder to ask before you accuse",
        kindness_move="leave a little note and wait for an answer",
        tags={"fact", "standard", "happen-gerund"},
    ),
    "lantern": Mystery(
        id="lantern",
        verb="solve the missing lantern mystery",
        gerund="solving the missing lantern mystery",
        clue="a warm footprint by the back door",
        reveal="the lantern had been carried to help an older neighbor find her keys",
        lesson="helping someone can be the best clue of all",
        kindness_move="offer a hand and look together",
        tags={"fact", "standard", "happen-gerund"},
    ),
}

THRESHOLD = 1.0


def prize_at_risk(m: Mystery, t: MissingThing) -> bool:
    return True


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for mid in MYSTERIES:
            for tid in THINGS:
                combos.append((place, mid, tid))
    return combos


@dataclass
class StoryParams:
    place: str
    mystery: str
    thing: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


THINGS = {
    "scarf": MissingThing(
        label="scarf",
        phrase="a red scarf with little stars",
        type="scarf",
        clue="a tiny blue thread",
        owner_role="mother",
        tags={"fact", "standard"},
    ),
    "book": MissingThing(
        label="book",
        phrase="a library book with a yellow cover",
        type="book",
        clue="a bookmark",
        owner_role="father",
        tags={"fact", "standard"},
    ),
    "lantern": MissingThing(
        label="lantern",
        phrase="a small brass lantern",
        type="lantern",
        clue="a warm footprint",
        owner_role="grandmother",
        tags={"fact", "standard"},
    ),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother"])
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
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.mystery is None or c[1] == args.mystery)
        and (args.thing is None or c[2] == args.thing)
    ]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, mystery, thing = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father", "grandmother"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, thing=thing, name=name, gender=gender, parent=parent, trait=trait)


def _intro(world: World, child: Entity, parent: Entity, thing: Entity, myst: Mystery) -> None:
    world.say(
        f"{child.id} was a little {next(t for t in [child.type, ''] if t)} who noticed every small thing. "
        f"{child.pronoun().capitalize()} loved quiet days and careful looking."
    )
    world.say(
        f"One day, {child.id}'s {parent.type if parent.type != 'grandmother' else 'grandmother'} showed {child.pronoun('object')} "
        f"{thing.phrase}. {child.id} thought it was special."
    )
    child.memes["curiosity"] = 1
    thing.owner = child.id
    thing.caretaker = parent.id
    thing.hidden = True


def _mystery_turn(world: World, child: Entity, parent: Entity, thing: Entity, myst: Mystery) -> None:
    world.para()
    world.say(
        f"Then, when {child.id} went back for {thing.label}, it was gone."
    )
    world.say(
        f"Only {myst.clue} was left behind. That made the room feel like a puzzle."
    )
    child.memes["worry"] = 1
    child.memes["suspicion"] = 1
    world.say(
        f"{child.id} looked at the clue and wondered what had happened."
    )
    world.say(
        f"{child.id} almost blamed the first person nearby, but {child.pronoun('possessive')} {parent.type if parent.type != 'grandmother' else 'grandmother'} said, "
        f"\"Let's find the fact before we make a guess.\""
    )
    child.memes["lesson_seed"] = 1


def _resolve(world: World, child: Entity, parent: Entity, thing: Entity, myst: Mystery) -> None:
    world.para()
    child.memes["kindness"] = 1
    world.say(
        f"So {child.id} followed the clue quietly and chose {myst.kindness_move}."
    )
    world.say(
        f"At the end of the trail, {myst.reveal}."
    )
    thing.hidden = False
    thing.found = True
    child.memes["relief"] = 1
    child.memes["joy"] = 1
    world.say(
        f"{child.id} felt warm inside, because the missing thing had not been taken for meanness at all."
    )
    world.say(
        f"{child.id}'s {parent.type if parent.type != 'grandmother' else 'grandmother'} smiled and said the lesson out loud: {myst.lesson}."
    )
    world.say(
        f"In the last light, {thing.label} was back where it belonged, and {child.id} knew kindness was the standard way to answer a mystery."
    )


def tell(world: World, child: Entity, parent: Entity, thing: Entity, myst: Mystery) -> None:
    _intro(world, child, parent, thing, myst)
    _mystery_turn(world, child, parent, thing, myst)
    _resolve(world, child, parent, thing, myst)
    world.facts.update(child=child, parent=parent, thing=thing, mystery=myst)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a young child where "{f["thing"].label}" goes missing, but the ending is kind.',
        f"Tell a gentle story about {f['child'].id} in {world.setting.place} that includes the words happen-gerund, fact, and standard.",
        f"Write a child-friendly mystery with a clue, a surprise reveal, and a lesson learned about kindness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, thing, myst = f["child"], f["parent"], f["thing"], f["mystery"]
    return [
        QAItem(
            question=f"What mystery did {child.id} try to solve?",
            answer=f"{child.id} tried to solve the missing {thing.label} mystery.",
        ),
        QAItem(
            question=f"What clue was left behind?",
            answer=f"The clue was {myst.clue}.",
        ),
        QAItem(
            question=f"What was the lesson learned at the end?",
            answer=f"The lesson learned was that {myst.lesson}.",
        ),
        QAItem(
            question=f"How did kindness show up in the story?",
            answer=f"{child.id} chose to be gentle, look for the real reason, and help instead of scolding anyone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fact?",
            answer="A fact is something that is true and can be checked.",
        ),
        QAItem(
            question="What does standard mean?",
            answer="Standard means the usual or expected way something is done.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring toward others.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        parts = []
        if e.hidden:
            parts.append("hidden=True")
        if e.found:
            parts.append("found=True")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(Place,Mystery,Thing) :- place(Place), mystery(Mystery), thing(Thing).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for t in THINGS:
        lines.append(asp.fact("thing", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="house", mystery="scarf", thing="scarf", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="library", mystery="book", thing="book", name="Ben", gender="boy", parent="father", trait="careful"),
    StoryParams(place="garden", mystery="lantern", thing="lantern", name="Lily", gender="girl", parent="grandmother", trait="gentle"),
]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.place]
    myst = MYSTERIES[params.mystery]
    thing_cfg = THINGS[params.thing]
    world = World(setting)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent))
    thing = world.add(Entity(id=params.thing, type=thing_cfg.type, label=thing_cfg.label, phrase=thing_cfg.phrase))
    tell(world, child, parent, thing, myst)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations")
        for c in combos:
            print(c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
