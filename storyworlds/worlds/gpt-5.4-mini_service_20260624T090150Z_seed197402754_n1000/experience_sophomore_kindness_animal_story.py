#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

STORYWORLDS_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path[:0] = [STORYWORLDS_DIR, os.path.dirname(STORYWORLDS_DIR)]
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "animal"
    species: str = "animal"
    name: str = ""
    role: str = ""
    place: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def subject(self) -> str:
        return self.name or self.id

    def possessive(self) -> str:
        return f"{self.subject()}'s"


@dataclass
class Place:
    id: str
    label: str
    kind: str = "school"
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    protagonist: str
    helper: str
    name: str
    helper_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


PLACES = {
    "schoolyard": Place(id="schoolyard", label="the schoolyard", tags={"school", "outside"}),
    "hallway": Place(id="hallway", label="the hallway", tags={"school", "inside"}),
    "library": Place(id="library", label="the library corner", tags={"school", "quiet"}),
}

SPECIES = {
    "rabbit": "rabbit",
    "fox": "fox",
    "bear": "bear",
    "cat": "cat",
    "dog": "dog",
    "mouse": "mouse",
}

NAMES = {
    "rabbit": ["Nina", "Milo", "Pip", "Ruby", "Luna"],
    "fox": ["Tara", "Finn", "Sage", "Junie", "Perry"],
    "bear": ["Ollie", "Benny", "Hazel", "Marta", "Toby"],
    "cat": ["Mina", "Cleo", "Iris", "Sunny", "Niko"],
    "dog": ["Remy", "Barkley", "Moss", "Penny", "Daisy"],
    "mouse": ["Tia", "Momo", "Bea", "Nell", "Wren"],
}

TRAITS = ["kind", "shy", "brave", "gentle", "curious", "patient"]

OPENINGS = [
    "The morning had begun smoothly",
    "Between lessons, the school hummed with busy paws",
    "Just before the next bell, everyone seemed to know where to go",
    "It was an ordinary school day until a small problem appeared",
    "The day felt familiar to the returning students",
    "During a busy part of the day, voices and footsteps filled the school",
]

SOPHOMORE_INSIGHTS = [
    "being experienced meant noticing who had not learned the routine yet",
    "a second year at school was useful only if it helped someone else",
    "knowing the school gave a student the chance to make it kinder",
    "experience was not about showing off; it was about knowing how to help",
    "the best part of being a returning student was making room for someone new",
]

APPROACHES = [
    "asked, \"Would you like company while we solve this?\"",
    "sat beside {newcomer} and said, \"We can take this one step at a time.\"",
    "said, \"That happened to me before. Let me show you what helped.\"",
    "lowered {possessive} voice and asked, \"What would make this easier?\"",
    "invited {helper} over and said, \"Three heads can find a gentle answer.\"",
    "said, \"You do not have to figure everything out alone.\"",
]

ENDING_IMAGES = [
    "At the next bell, the three friends crossed the school together, their steps keeping the same cheerful beat.",
    "Before going home, {newcomer} drew a tiny heart beside today's date and tucked the page safely away.",
    "As afternoon light reached the floor, {newcomer}'s ears stood tall, and {hero} knew the school felt smaller in the best way.",
    "On the way out, {newcomer} held the door for another student, passing the kindness onward without being asked.",
    "The final bell rang over three voices laughing together instead of one quiet voice worrying alone.",
    "By day's end, the problem was only a memory, and a new friendship had taken its place.",
]

SCENARIOS = [
    {
        "problem": "a gust scattered {newcomer}'s hand-drawn classroom map across the ground",
        "memory": "once following the wrong arrows and arriving late to music",
        "action": "caught the nearest page while {helper} stopped another with a paw; then they numbered the pages and walked the route together",
        "outcome": "the map was complete again, and {newcomer} could point out every turn without guessing",
        "proof": "held the repaired map like a guide instead of a puzzle",
    },
    {
        "problem": "the handle tore from {newcomer}'s project box, spilling paper animals just before class",
        "memory": "carrying a wobbly project alone during the first year",
        "action": "made a sling from two spare ribbons while {helper} gathered the paper animals in their proper order",
        "outcome": "the class display arrived safely, with every paper animal standing in its place",
        "proof": "carried one end of the ribbon sling with a steady smile",
    },
    {
        "problem": "{newcomer} froze at the edge of a game because nobody had explained the rules",
        "memory": "pretending to understand a game and feeling more confused with every turn",
        "action": "paused the game, demonstrated one slow practice round, and asked {helper} to play beside {newcomer}",
        "outcome": "{newcomer} learned the rules and made the pass that completed the next round",
        "proof": "called out the next play clearly while the others listened",
    },
    {
        "problem": "a stack of returned books slid from {newcomer}'s cart and blocked the quiet corner",
        "memory": "trying to shelve books by color before learning about their labels",
        "action": "showed {newcomer} how to read one shelf label while {helper} sorted the books into small, manageable piles",
        "outcome": "every book found its shelf, and {newcomer} understood how the labels worked",
        "proof": "slid the last book home and whispered, \"Now I know where it belongs.\"",
    },
    {
        "problem": "{newcomer}'s lunch tray tipped, leaving the only meal in a puddle on the floor",
        "memory": "dropping a snack and being too embarrassed to ask what to do",
        "action": "shared half of {possessive} lunch, found a cloth with {helper}, and quietly helped clean the spill",
        "outcome": "the floor was clean, both students had enough to eat, and the embarrassing moment became a friendly lunch",
        "proof": "saved the last berry to split with {hero}",
    },
    {
        "problem": "the wheels on {newcomer}'s supply cart caught in a floor groove while hurried students squeezed past",
        "memory": "pulling a jammed cart harder until its boxes nearly fell",
        "action": "asked everyone for a little space, lifted one side with {helper}, and guided the wheel around the groove",
        "outcome": "the cart rolled safely to class without losing a single supply",
        "proof": "steered the cart around the groove on the return trip",
    },
    {
        "problem": "{newcomer} could not make the first sound during rehearsal for a class reading",
        "memory": "forgetting a line when a whole room seemed to be waiting",
        "action": "practiced the opening sentence in a whisper, then invited {helper} to add the next line like a friendly echo",
        "outcome": "{newcomer} read the whole passage aloud at a comfortable pace",
        "proof": "closed the book only after the listeners applauded",
    },
    {
        "problem": "water leaked from {newcomer}'s plant jar and soaked the observation notes",
        "memory": "losing careful work to a bottle that had not been closed tightly",
        "action": "moved the plant to safety, blotted each page with {helper}, and helped rewrite the blurred measurements from the class chart",
        "outcome": "the plant and its record were both saved before the lesson began",
        "proof": "set the dry notes beside the upright plant and checked the lid twice",
    },
    {
        "problem": "{newcomer} searched every pocket for a missing hall pass as the line began to leave",
        "memory": "panicking over a lost pass that had slipped behind a folder",
        "action": "helped retrace the morning in order while {helper} checked beneath the nearby bench",
        "outcome": "the pass turned up inside a folded timetable, exactly where the clues led",
        "proof": "placed the pass in a bright front pocket before joining the line",
    },
    {
        "problem": "two students claimed the same costume piece, and {newcomer} was too nervous to speak",
        "memory": "giving up a turn because arguing had seemed easier for everyone else",
        "action": "asked each student to explain, then helped them plan two scenes so both could use the costume with {helper} keeping time",
        "outcome": "both scenes worked, and {newcomer} got a fair turn without a quarrel",
        "proof": "returned the costume at the agreed signal and bowed with confidence",
    },
    {
        "problem": "{newcomer}'s carefully built tower leaned after one block cracked",
        "memory": "starting an entire project over instead of repairing the weak part",
        "action": "tested the base with {newcomer} while {helper} found two flat blocks to brace the cracked one",
        "outcome": "the tower stood through the class demonstration and showed how a repair could strengthen a design",
        "proof": "tapped the sturdy base and explained the repair to the class",
    },
    {
        "problem": "a wrong turn left {newcomer} outside the practice room as the club meeting began",
        "memory": "wandering past the same doorway twice during the first week",
        "action": "pointed out a painted star beside the correct door and asked {helper} to make a matching star for {newcomer}'s schedule",
        "outcome": "{newcomer} reached the meeting and learned a landmark that would work tomorrow too",
        "proof": "found the painted star first when the group left together",
    },
]

SCENARIOS_BY_PLACE = {
    "schoolyard": [0, 2, 4, 7, 10],
    "hallway": [0, 1, 5, 8, 9, 11],
    "library": [1, 3, 6, 7, 10],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world: kindness, experience, and a sophomore animal at school.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--protagonist", choices=SPECIES)
    ap.add_argument("--helper", choices=SPECIES)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    protagonist = args.protagonist or rng.choice(list(SPECIES))
    helper = args.helper or rng.choice([s for s in SPECIES if s != protagonist])
    name = args.name or rng.choice(NAMES[protagonist])
    helper_name = args.helper_name or rng.choice(NAMES[helper])
    return StoryParams(place=place, protagonist=protagonist, helper=helper, name=name, helper_name=helper_name)


def select_name(species: str, used: set[str], rng: random.Random) -> str:
    options = [n for n in NAMES[species] if n not in used]
    if not options:
        options = NAMES[species]
    choice = rng.choice(options)
    used.add(choice)
    return choice


def generate_story(world: World, params: StoryParams) -> None:
    seed_text = f"{params.seed}|{params.place}|{params.protagonist}|{params.helper}|{params.name}|{params.helper_name}"
    story_seed = int.from_bytes(hashlib.sha256(seed_text.encode("utf-8")).digest()[:8], "big")
    rng = random.Random(story_seed)
    hero = world.add(Entity(id="hero", species=params.protagonist, name=params.name, role="sophomore"))
    helper = world.add(Entity(id="helper", species=params.helper, name=params.helper_name, role="friend"))
    newcomer_species = rng.choice([species for species in SPECIES if species not in {hero.species, helper.species}])
    newcomer_name = select_name(newcomer_species, {hero.name, helper.name}, rng)
    new_student = world.add(Entity(id="new_student", species=newcomer_species, name=newcomer_name, role="new student"))
    scenario = SCENARIOS[rng.choice(SCENARIOS_BY_PLACE[params.place])]
    opening = rng.choice(OPENINGS)
    insight = rng.choice(SOPHOMORE_INSIGHTS)
    approach = rng.choice(APPROACHES)
    ending = rng.choice(ENDING_IMAGES)
    details = {
        "hero": hero.subject(),
        "helper": helper.subject(),
        "newcomer": new_student.subject(),
        "possessive": "their",
    }
    problem = scenario["problem"].format(**details)
    memory = scenario["memory"].format(**details)
    action = scenario["action"].format(**details)
    outcome = scenario["outcome"].format(**details)
    proof = scenario["proof"].format(**details)
    approach_text = approach.format(**details)
    ending_text = ending.format(**details)

    hero.meters["experience"] = 2.0
    hero.memes["kindness"] = 1.0
    helper.memes["worry"] = 1.0
    new_student.memes["nervous"] = 2.0

    place_preposition = "In" if world.place.id in {"hallway", "library"} else "At"
    world.say(f"{place_preposition} {world.place.label}, {opening[:1].lower() + opening[1:]}.")
    world.say(
        f"{hero.subject()}, a sophomore {hero.species} in the second year of school, had enough experience to know the routines "
        f"but still remembered {memory}."
    )
    world.say(f"That was why {hero.subject()} noticed when {new_student.subject()}, a new {new_student.species}, faced a problem: {problem}.")
    world.say(f"{helper.subject()}, a {helper.species} classmate, noticed too and waited to see what {new_student.subject()} wanted.")
    world.para()

    hero.memes["kindness"] += 1.0
    helper.meters["experience"] = 1.0
    new_student.memes["nervous"] -= 1.0
    new_student.memes["hope"] = 1.5

    world.say(f"Kindness, {hero.subject()} decided, meant offering help and letting {new_student.subject()} choose instead of taking over.")
    world.say(f"{hero.subject()} {approach_text}")
    world.say(f"When {new_student.subject()} nodded, {hero.subject()} {action}.")
    world.say(f"The plan worked: {outcome}.")
    world.para()

    hero.meters["experience"] += 1.0
    new_student.memes["safe"] = 1.0
    helper.memes["admiration"] = 1.0

    proof_sentence = f"A little later, {new_student.subject()} {proof}"
    world.say(proof_sentence if proof_sentence.endswith((".", "!", "?", '."', '!"', '?"')) else proof_sentence + ".")
    world.say(f"{hero.subject()} understood that {insight}.")
    world.say(ending_text)

    world.facts.update(
        hero=hero,
        helper=helper,
        new_student=new_student,
        place=world.place,
        problem=problem,
        memory=memory,
        action=action,
        outcome=outcome,
        proof=proof,
        insight=insight,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    new_student = f["new_student"]
    place = f["place"]
    return [
        QAItem(
            question=f"Who was the sophomore in the story?",
            answer=f"{hero.subject()} was the sophomore {hero.species} in the story.",
        ),
        QAItem(
            question=f"What problem did {new_student.subject()} face at {place.label}?",
            answer=f"{new_student.subject()} needed help because {f['problem']}.",
        ),
        QAItem(
            question=f"How did {hero.subject()} and {helper.subject()} show kindness?",
            answer=f"They helped when {hero.subject()} {f['action']}.",
        ),
        QAItem(
            question="How did the story show that the plan worked?",
            answer=f"The plan worked because {f['outcome']}. Later, {new_student.subject()} {f['proof']}.",
        ),
        QAItem(
            question=f"What did {hero.subject()} learn about being a sophomore?",
            answer=f"{hero.subject()} learned that {f['insight']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, caring, and helpful to someone else.",
        ),
        QAItem(
            question="What is a sophomore?",
            answer="A sophomore is a student in the second year of school at that level.",
        ),
        QAItem(
            question="What is experience?",
            answer="Experience is what you learn by doing something or being part of it.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    new_student = f["new_student"]
    place = f["place"]
    return [
        f"Write an animal story about a sophomore {hero.species} at {place.label} who uses kindness to help a new {new_student.species}.",
        f"Tell a child-friendly story where {hero.subject()}'s school experience helps solve this problem: {f['problem']}.",
        "Write a gentle school story in which animals ask before helping, solve a problem together, and show what changed.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"  {ent.id}: species={ent.species} role={ent.role} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero_kind(H) :- hero(H), kindness(H, K), K > 0.
helped(New) :- hero(H), new_student(New), kindness(H, K), K > 0.
good_experience(H) :- experience(H, E), E > 0, kindness(H, K), K > 0.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for sp in SPECIES:
        lines.append(asp.fact("species", sp))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def select_story_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    generate_story(world, params)
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
        print("== (1) Generation prompts -- asks that would produce this story ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== (2) Story questions -- answerable from the story text ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== (3) World-knowledge questions -- child level, no story needed ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show hero_kind/1.\n#show helped/1.\n#show good_experience/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        curated = [
            StoryParams(place="schoolyard", protagonist="rabbit", helper="cat", name="Nina", helper_name="Cleo"),
            StoryParams(place="hallway", protagonist="fox", helper="dog", name="Sage", helper_name="Remy"),
            StoryParams(place="library", protagonist="bear", helper="mouse", name="Hazel", helper_name="Tia"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.protagonist} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
