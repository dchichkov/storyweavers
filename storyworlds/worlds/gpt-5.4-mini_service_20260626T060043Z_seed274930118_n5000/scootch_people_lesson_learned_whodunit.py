#!/usr/bin/env python3
"""
storyworlds/worlds/scootch_people_lesson_learned_whodunit.py
=============================================================

A small whodunit-style storyworld where a few people at a tiny place must
solve a puzzling mishap, discover who caused the clue trail, and learn a
gentle lesson by the end.

The story is driven by a simple simulated world:
- people have physical meters and emotional memes
- clues can be moved, hidden, smudged, or revealed
- suspicion grows from evidence, then settles into a clear solution
- the ending proves what changed in the world and in the people's moods
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    rooms: list[str]
    hidden_spot: str
    clue_spot: str


@dataclass
class Mystery:
    missing: str
    clue: str
    culprit_action: str
    reveal_action: str
    lesson: str


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    witness: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def people(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "library": Setting(place="the little library", rooms=["front desk", "aisle", "reading nook"], hidden_spot="behind the atlas", clue_spot="under the bench"),
    "kitchen": Setting(place="the bright kitchen", rooms=["table", "pantry", "stool"], hidden_spot="behind the sugar jar", clue_spot="under the mat"),
    "garden_room": Setting(place="the glass garden room", rooms=["bench", "potting table", "door"], hidden_spot="behind the watering can", clue_spot="under the leaf basket"),
}

MYSTERIES = {
    "cookie": Mystery(
        missing="cookie",
        clue="crumbs",
        culprit_action="scootched the plate",
        reveal_action="scootched the plate by mistake",
        lesson="look before moving something that belongs to other people",
    ),
    "button": Mystery(
        missing="button",
        clue="thread",
        culprit_action="scootched the basket",
        reveal_action="scootched the basket while searching for a scarf",
        lesson="ask first before touching a tidy pile",
    ),
    "key": Mystery(
        missing="key",
        clue="shiny dust",
        culprit_action="scootched the box",
        reveal_action="scootched the box to reach a note",
        lesson="follow clues calmly instead of guessing too fast",
    ),
}

NAMES = ["Mina", "Toby", "Nora", "Eli", "Lena", "Pip", "Ruby", "Otis"]
HELPERS = ["neighbor", "teacher", "friend"]
WITNESSES = ["cat", "bird", "dog"]


class Reasoner:
    @staticmethod
    def suspicious(world: World) -> Optional[str]:
        for e in world.people():
            if e.memes.get("suspicion", 0.0) >= THRESHOLD:
                return e.id
        return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a small lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--witness", choices=WITNESSES)
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str]]:
    return [(place, mystery) for place in SETTINGS for mystery in MYSTERIES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.mystery:
        if (args.place, args.mystery) not in valid_combos():
            raise StoryError("That place and mystery do not make a reasonable whodunit.")
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    witness = args.witness or rng.choice(WITNESSES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, witness=witness, helper=helper)


def introduce(world: World, hero: Entity, helper: Entity, witness: Entity, mystery: Mystery) -> None:
    world.say(f"{hero.id} was a small {hero.type} who noticed everything in {world.setting.place}.")
    world.say(f"{hero.pronoun().capitalize()} liked quiet places, tidy corners, and little puzzles.")
    world.say(f"One afternoon, {hero.id} found a mystery: the {mystery.missing} was gone.")
    world.say(f"{helper.label.capitalize()} came to help, and even the {witness.label} seemed to watch closely.")


def add_clues(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] = 1.0
    hero.memes["suspicion"] = 0.0
    world.say(f"{hero.id} leaned near the clue spot and found {mystery.clue}.")
    world.say(f"That meant someone had moved something from where it had been resting.")


def question_people(world: World, hero: Entity, helper: Entity, witness: Entity) -> None:
    helper.memes["calm"] = 1.0
    witness.meters["watching"] = 1.0
    world.say(f"{hero.id} asked the other people one by one, trying not to rush.")
    world.say(f"{helper.label.capitalize()} said to follow the small signs and keep thinking.")
    world.say(f"The {witness.label} only blinked, but its stare pointed toward the hidden spot.")


def suspect(world: World, hero: Entity, culprit: Entity) -> None:
    hero.memes["suspicion"] = 1.0
    culprit.memes["nervous"] = 1.0
    world.say(f"{hero.id} noticed a tiny trail leading to the hidden spot.")
    world.say(f"That made {hero.pronoun('object')} suspect {culprit.id}, though {hero.pronoun('subject')} still needed proof.")


def reveal(world: World, hero: Entity, culprit: Entity, mystery: Mystery) -> None:
    culprit.memes["guilty"] = 1.0
    culprit.memes["relief"] = 1.0
    hero.memes["suspicion"] = 0.0
    hero.memes["understanding"] = 1.0
    world.say(f"At last, the clue led to the hidden spot, and the missing {mystery.missing} turned up there.")
    world.say(f"{culprit.id} admitted the truth: {mystery.reveal_action}.")
    world.say(f"It had not been mean; it had only been careless, and now everyone could see what happened.")


def lesson(world: World, hero: Entity, helper: Entity, mystery: Mystery) -> None:
    hero.memes["wisdom"] = 1.0
    helper.memes["pride"] = 1.0
    world.say(f"{hero.id} smiled and learned the lesson: {mystery.lesson}.")
    world.say(f"After that, the people in {world.setting.place} agreed to pause, ask, and look before they scootched anything important.")
    world.say(f"The room felt peaceful again, with the missing thing returned and the people gentler than before.")


def tell(setting: Setting, mystery: Mystery, name: str, gender: str, witness: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name))
    guide = world.add(Entity(id=helper.capitalize(), kind="character", type="person", label=helper))
    watch = world.add(Entity(id=witness.capitalize(), kind="character", type="animal", label=witness))
    culprit = world.add(Entity(id="Casey", kind="character", type="person", label="Casey"))

    culprit.meters["near"] = 1.0
    culprit.memes["careless"] = 1.0

    world.facts.update(hero=hero, helper=guide, witness=watch, culprit=culprit, mystery=mystery)

    introduce(world, hero, guide, watch, mystery)
    world.para()
    add_clues(world, hero, mystery)
    question_people(world, hero, guide, watch)
    suspect(world, hero, culprit)
    world.para()
    reveal(world, hero, culprit, mystery)
    lesson(world, hero, guide, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    return [
        f'Write a short whodunit for a young child about {hero.id}, some people, and a missing {mystery.missing}.',
        f"Tell a small mystery story that includes the word \"scootch\" and ends with a lesson learned.",
        f"Write a gentle detective story in which {hero.id} asks people questions, finds a clue, and solves the case.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    culprit: Entity = f["culprit"]
    mystery: Mystery = f["mystery"]
    helper: Entity = f["helper"]
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was the {mystery.missing}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} think through the mystery?",
            answer=f"{helper.label.capitalize()} helped {hero.id} stay calm and follow the clues.",
        ),
        QAItem(
            question=f"Who admitted moving the thing at the end?",
            answer=f"{culprit.id} admitted the truth and explained that {mystery.reveal_action}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does it mean to investigate a mystery?",
            answer="To investigate a mystery means to look for clues, ask questions, and think carefully about what happened.",
        ),
        QAItem(
            question="Why do people ask questions when something goes missing?",
            answer="People ask questions so they can learn what happened and find the truth instead of guessing.",
        ),
    ]
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", mystery="cookie", name="Mina", gender="girl", witness="cat", helper="teacher"),
    StoryParams(place="kitchen", mystery="button", name="Toby", gender="boy", witness="dog", helper="neighbor"),
    StoryParams(place="garden_room", mystery="key", name="Nora", gender="girl", witness="bird", helper="friend"),
]


ASP_RULES = r"""
person(P) :- hero(P).
person(P) :- helper(P).
person(P) :- culprit(P).

clue_found(M) :- mystery(M), clue(C), seen(C).
missing_revealed(M) :- mystery(M), clue_found(M), culprit_admits(M).

lesson_learned :- missing_revealed(_).
scootch_action :- culprit_action(_).

#show lesson_learned/0.
#show scootch_action/0.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        lines.append(asp.fact("clue", m.clue))
        lines.append(asp.fact("culprit_action", mid))
    lines.append("seen(crumbs).")
    lines.append("seen(thread).")
    lines.append("seen(shiny_dust).")
    lines.append("culprit_admits(cookie).")
    lines.append("culprit_admits(button).")
    lines.append("culprit_admits(key).")
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show lesson_learned/0.\n#show scootch_action/0."))
    atoms = set((sym.name, len(sym.arguments)) for sym in model)
    expected = {("lesson_learned", 0), ("scootch_action", 0)}
    if atoms == expected:
        print("OK: ASP twin matches the Python storyworld signals.")
        return 0
    print("MISMATCH between ASP and Python signals.")
    print("  got:", atoms)
    print("  expected:", expected)
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], MYSTERIES[params.mystery], params.name, params.gender, params.witness, params.helper)
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


def resolve_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    mystery = args.mystery or rng.choice(list(MYSTERIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    witness = args.witness or rng.choice(WITNESSES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, witness=witness, helper=helper)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show lesson_learned/0.\n#show scootch_action/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show lesson_learned/0.\n#show scootch_action/0."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
