#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/proficiency_happy_ending_animal_story.py
===================================================================

A small standalone storyworld for gentle animal stories about learning enough
*proficiency* to help a friend. The world simulates a child animal who wants to
solve a concrete forest problem, cannot do it well at first, practices with a
mentor, and then succeeds.

The reasonableness gate is simple and strict:

- each animal species has one natural family skill
- each challenge requires exactly one skill
- each practice lesson trains exactly one skill
- only matching triples are valid

That keeps the stories coherent: the practice beat honestly explains the later
success instead of swapping nouns into one frozen paragraph.

Run it
------
python storyworlds/worlds/gpt-5.4/proficiency_happy_ending_animal_story.py
python storyworlds/worlds/gpt-5.4/proficiency_happy_ending_animal_story.py -n 5 --seed 7
python storyworlds/worlds/gpt-5.4/proficiency_happy_ending_animal_story.py --all
python storyworlds/worlds/gpt-5.4/proficiency_happy_ending_animal_story.py --species squirrel --challenge kite_tree
python storyworlds/worlds/gpt-5.4/proficiency_happy_ending_animal_story.py --challenge pond_raft --species mole
python storyworlds/worlds/gpt-5.4/proficiency_happy_ending_animal_story.py --qa --json
python storyworlds/worlds/gpt-5.4/proficiency_happy_ending_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Species:
    id: str
    label: str
    child_word: str
    home: str
    move: str
    body_part: str
    skill: str
    mentor_title: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    label: str
    need: str
    place: str
    problem: str
    first_fail: str
    try_text: str
    success: str
    ending_image: str
    friend_kind: str
    friend_item: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Lesson:
    id: str
    label: str
    teaches: str
    place: str
    method: str
    sound: str
    progress_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def species_can_do(species: Species, challenge: Challenge) -> bool:
    return species.skill == challenge.need


def lesson_fits(challenge: Challenge, lesson: Lesson) -> bool:
    return challenge.need == lesson.teaches


def valid_story(species: Species, challenge: Challenge, lesson: Lesson) -> bool:
    return species_can_do(species, challenge) and lesson_fits(challenge, lesson)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, species in SPECIES.items():
        for cid, challenge in CHALLENGES.items():
            for lid, lesson in LESSONS.items():
                if valid_story(species, challenge, lesson):
                    combos.append((sid, cid, lid))
    return combos


def explain_rejection(species: Species, challenge: Challenge, lesson: Lesson) -> str:
    if not species_can_do(species, challenge):
        return (
            f"(No story: a {species.child_word}'s family skill is {species.skill}, "
            f"but the challenge '{challenge.label}' needs {challenge.need}. "
            f"Pick a species whose natural skill matches the problem.)"
        )
    if not lesson_fits(challenge, lesson):
        return (
            f"(No story: the lesson '{lesson.label}' teaches {lesson.teaches}, "
            f"but the challenge '{challenge.label}' needs {challenge.need}. "
            f"The practice beat must train the same skill used in the rescue.)"
        )
    return "(No story: this combination is not reasonable.)"


def introduce(world: World, hero: Entity, species: Species, friend: Entity, challenge: Challenge) -> None:
    hero.memes["care"] += 1
    world.say(
        f"In {species.home}, a young {species.child_word} named {hero.id} liked to "
        f"{species.move} wherever something interesting was happening."
    )
    world.say(
        f"One bright morning, {hero.id} heard {friend.id}, a little {challenge.friend_kind}, "
        f"calling from {challenge.place}."
    )
    world.say(challenge.problem)


def first_try(world: World, hero: Entity, species: Species, challenge: Challenge) -> None:
    hero.memes["eagerness"] += 1
    hero.meters["attempts"] += 1
    world.say(
        f"{hero.id} hurried over and tried at once. {challenge.try_text}"
    )
    world.say(
        f"But {challenge.first_fail}."
    )
    hero.memes["worry"] += 1
    hero.meters["proficiency"] = 0.0


def mentor_arrives(world: World, hero: Entity, mentor: Entity, species: Species, lesson: Lesson) -> None:
    mentor.memes["calm"] += 1
    world.say(
        f"Just then, {mentor.id}, the {species.mentor_title}, came along the path "
        f"from {lesson.place}."
    )
    world.say(
        f'"Slow paws make strong work," {mentor.id} said. '
        f'"You care very much, but you need a little more proficiency first."'
    )


def practice(world: World, hero: Entity, mentor: Entity, species: Species, lesson: Lesson) -> None:
    world.say(
        f"So {mentor.id} took {hero.id} to {lesson.place}. {lesson.method}"
    )
    hero.meters["practice_rounds"] += 1
    hero.meters["proficiency"] += 1
    hero.memes["focus"] += 1
    world.say(
        f"Soon the air was full of {lesson.sound}. {lesson.progress_text}"
    )
    world.say(
        f"By the time they finished, {hero.id}'s {species.body_part} knew just what to do."
    )


def return_and_help(world: World, hero: Entity, friend: Entity, challenge: Challenge) -> None:
    hero.meters["attempts"] += 1
    world.say(
        f"They hurried back to {challenge.place}, where {friend.id} was still waiting."
    )
    world.say(challenge.success)
    hero.meters["helped"] += 1
    friend.memes["relief"] += 1
    hero.memes["confidence"] += 1
    hero.memes["worry"] = 0.0


def ending(world: World, hero: Entity, friend: Entity, mentor: Entity, challenge: Challenge) -> None:
    hero.memes["joy"] += 1
    world.say(
        f'{friend.id} beamed and hugged {hero.id}. "You did it!" {friend.pronoun()} said.'
    )
    world.say(
        f"{mentor.id} smiled. \"That is what practice is for. Kind hearts shine brightest when skill can follow them.\""
    )
    world.say(challenge.ending_image)
    world.say(
        f"From then on, whenever {hero.id} practiced, {hero.pronoun()} remembered that "
        f"proficiency grows one careful try at a time."
    )


def tell(species: Species, challenge: Challenge, lesson: Lesson,
         hero_name: str, mentor_name: str, friend_name: str) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=species.id, role="hero", label=hero_name))
    mentor = world.add(Entity(id=mentor_name, kind="character", type=species.id, role="mentor", label=mentor_name))
    friend = world.add(
        Entity(
            id=friend_name,
            kind="character",
            type=challenge.friend_kind,
            role="friend",
            label=friend_name,
            attrs={"item": challenge.friend_item},
        )
    )

    introduce(world, hero, species, friend, challenge)
    world.para()
    first_try(world, hero, species, challenge)
    mentor_arrives(world, hero, mentor, species, lesson)
    world.para()
    practice(world, hero, mentor, species, lesson)
    world.para()
    return_and_help(world, hero, friend, challenge)
    ending(world, hero, friend, mentor, challenge)

    world.facts.update(
        hero=hero,
        mentor=mentor,
        friend=friend,
        species=species,
        challenge=challenge,
        lesson=lesson,
        succeeded=hero.meters["helped"] >= THRESHOLD,
        practiced=hero.meters["practice_rounds"] >= THRESHOLD,
        proficiency=hero.meters["proficiency"],
    )
    return world


SPECIES = {
    "squirrel": Species(
        id="squirrel",
        label="squirrel",
        child_word="squirrel",
        home="the piney edge of the forest",
        move="dart from stump to stump",
        body_part="quick paws and tail",
        skill="climb",
        mentor_title="old tree-guide",
        tags={"squirrel", "climb"},
    ),
    "duck": Species(
        id="duck",
        label="duck",
        child_word="duck",
        home="the silver pond",
        move="waddle and splash",
        body_part="feet and steady wings",
        skill="swim",
        mentor_title="old pond-guide",
        tags={"duck", "swim"},
    ),
    "mole": Species(
        id="mole",
        label="mole",
        child_word="mole",
        home="the soft hill under the meadow",
        move="shuffle through the grass",
        body_part="strong little paws",
        skill="dig",
        mentor_title="old tunnel-guide",
        tags={"mole", "dig"},
    ),
    "beaver": Species(
        id="beaver",
        label="beaver",
        child_word="beaver",
        home="the willow stream",
        move="patter along the bank",
        body_part="broad tail and busy teeth",
        skill="build",
        mentor_title="old bank-guide",
        tags={"beaver", "build"},
    ),
}

CHALLENGES = {
    "kite_tree": Challenge(
        id="kite_tree",
        label="a kite stuck in an oak tree",
        need="climb",
        place="the old oak",
        problem="A gust had lifted a red leaf-kite into the branches, and Pip could not reach it.",
        first_fail="the bark felt high and slippery, and the little squirrel slid back down with a shower of bits of moss",
        try_text="Up the trunk went one paw, then another",
        success="This time, the young squirrel went up the bark in neat little bursts, reached the branch, and brought the red leaf-kite down without tearing it.",
        ending_image="The kite sailed above the fern tops again, and even the oak leaves seemed to clap.",
        friend_kind="mouse",
        friend_item="red leaf-kite",
        tags={"tree", "climb"},
    ),
    "pond_raft": Challenge(
        id="pond_raft",
        label="a toy raft drifting from shore",
        need="swim",
        place="the sunny edge of the pond",
        problem="A little frog named Pip had nudged a toy raft too far from shore, and the tiny raft was turning in circles on the water.",
        first_fail="the little duck splashed fast but bumped the water the wrong way and only pushed the raft farther out",
        try_text="Splash-splash, the young duck paddled after it",
        success="This time, the young duck paddled in a smooth curve, slipped behind the raft, and guided it gently back to shore.",
        ending_image="The toy raft rocked safely in the reeds while pond rings sparkled around it.",
        friend_kind="frog",
        friend_item="toy raft",
        tags={"pond", "swim"},
    ),
    "carrot_burrow": Challenge(
        id="carrot_burrow",
        label="a carrot basket stuck near a burrow wall",
        need="dig",
        place="the sandy burrow mouth",
        problem="A little rabbit named Pip had dropped a carrot basket into a narrow side hole, and it was wedged behind packed sand.",
        first_fail="the little mole scratched at the wrong spot and sent only a dry trickle of sand over the basket",
        try_text="The young mole began to dig right away",
        success="This time, the young mole opened a neat side tunnel, loosened the packed sand, and pushed the carrot basket free.",
        ending_image="Orange carrots shone in the burrow doorway like a row of tiny lanterns.",
        friend_kind="rabbit",
        friend_item="carrot basket",
        tags={"burrow", "dig"},
    ),
    "reed_bridge": Challenge(
        id="reed_bridge",
        label="a broken reed bridge over a puddle",
        need="build",
        place="the muddy path by the reeds",
        problem="A little hedgehog named Pip stood beside a puddle where the tiny reed bridge had bent apart, and the berry basket on the other side looked very far away.",
        first_fail="the loose reeds rolled and slipped, and the little beaver made only a wobbly pile",
        try_text="The young beaver pushed a few reeds together",
        success="This time, the young beaver set the thick reeds first, tucked the thin ones across, and made a snug little bridge that held firm.",
        ending_image="Soon small feet were pattering across the bridge while the berry basket bobbed home beside them.",
        friend_kind="hedgehog",
        friend_item="berry basket",
        tags={"bridge", "build"},
    ),
}

LESSONS = {
    "bark_steps": Lesson(
        id="bark_steps",
        label="bark-step practice",
        teaches="climb",
        place="a leaning practice log",
        method="Together they practiced placing each paw on the rough bark, then resting, then reaching again.",
        sound="soft scritch-scritch sounds",
        progress_text="At first the steps were uneven, but soon each climb grew tidier and calmer.",
        tags={"practice", "climb"},
    ),
    "pond_arcs": Lesson(
        id="pond_arcs",
        label="pond-arc practice",
        teaches="swim",
        place="a quiet cove of the pond",
        method="Together they practiced making wide, calm turns and pushing water with even strokes instead of wild splashes.",
        sound="round little swish-swish sounds",
        progress_text="At first the turns were crooked, but soon each circle grew smooth and sure.",
        tags={"practice", "swim"},
    ),
    "side_tunnel": Lesson(
        id="side_tunnel",
        label="side-tunnel practice",
        teaches="dig",
        place="a patch of soft earth under clover",
        method="Together they practiced opening a small tunnel beside a stone instead of scratching straight at it.",
        sound="tiny pat-pat sounds in the earth",
        progress_text="At first the dirt fell back in, but soon each tunnel held its shape.",
        tags={"practice", "dig"},
    ),
    "reed_lacing": Lesson(
        id="reed_lacing",
        label="reed-lacing practice",
        teaches="build",
        place="a calm bank under the willows",
        method="Together they practiced laying thick reeds first and lacing thin reeds across them until they held snugly together.",
        sound="little tap-tap and rustle-rustle sounds",
        progress_text="At first the reeds slid apart, but soon each small frame stayed where it was set.",
        tags={"practice", "build"},
    ),
}


@dataclass
class StoryParams:
    species: str
    challenge: str
    lesson: str
    hero_name: str
    mentor_name: str
    friend_name: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        species="squirrel",
        challenge="kite_tree",
        lesson="bark_steps",
        hero_name="Nibbles",
        mentor_name="Moss",
        friend_name="Pip",
    ),
    StoryParams(
        species="duck",
        challenge="pond_raft",
        lesson="pond_arcs",
        hero_name="Dabble",
        mentor_name="Ripple",
        friend_name="Pip",
    ),
    StoryParams(
        species="mole",
        challenge="carrot_burrow",
        lesson="side_tunnel",
        hero_name="Minto",
        mentor_name="Loam",
        friend_name="Pip",
    ),
    StoryParams(
        species="beaver",
        challenge="reed_bridge",
        lesson="reed_lacing",
        hero_name="Tumble",
        mentor_name="Cedar",
        friend_name="Pip",
    ),
]

NAMES = {
    "squirrel": ["Nibbles", "Hazel", "Poppy", "Twig", "Acorn"],
    "duck": ["Dabble", "Pebble", "Sunny", "Ripple", "Merry"],
    "mole": ["Minto", "Truffle", "Dottie", "Loam", "Nib"],
    "beaver": ["Tumble", "Cedar", "Willow", "Bramble", "Plank"],
}
FRIEND_NAMES = ["Pip", "Dot", "Mimi", "Tad", "Bram"]


KNOWLEDGE = {
    "climb": [
        (
            "What does proficiency mean?",
            "Proficiency means being able to do something well because you have practiced it. It grows little by little, not all at once.",
        ),
        (
            "Why do squirrels climb well?",
            "Squirrels have sharp little claws and good balance. Those help them hold on to bark and move safely in trees.",
        ),
    ],
    "swim": [
        (
            "Why do ducks paddle so smoothly?",
            "A duck's feet push water backward, and that moves the duck forward. Calm, even strokes help a duck steer well.",
        ),
        (
            "What does proficiency mean?",
            "Proficiency means being able to do something well because you have practiced it. Practice helps your body remember what to do.",
        ),
    ],
    "dig": [
        (
            "Why are moles good at digging?",
            "Moles have strong front paws that scoop dirt aside. Their bodies are shaped for moving through soft earth.",
        ),
        (
            "What does proficiency mean?",
            "Proficiency means being skillful because you practiced carefully. It is what turns trying into doing something well.",
        ),
    ],
    "build": [
        (
            "Why are beavers good builders?",
            "Beavers are good builders because they work with sticks, mud, and water all the time. They learn how to place things so they stay together.",
        ),
        (
            "What does proficiency mean?",
            "Proficiency means knowing how to do a job well after practice. It helps kind ideas turn into helpful actions.",
        ),
    ],
}
KNOWLEDGE_ORDER = ["climb", "swim", "dig", "build"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    species = f["species"]
    challenge = f["challenge"]
    lesson = f["lesson"]
    hero = f["hero"]
    return [
        f'Write a gentle animal story for a 3-to-5-year-old that includes the word "proficiency" and ends happily.',
        f"Tell a forest story where a young {species.child_word} named {hero.id} wants to help a friend with {challenge.label}, cannot do it at first, practices, and then succeeds.",
        f"Write a simple animal story in which {lesson.label} teaches a caring child enough proficiency to solve a real problem.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    friend = f["friend"]
    species = f["species"]
    challenge = f["challenge"]
    lesson = f["lesson"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, a young {species.child_word}, and {friend.id}, the friend who needed help. {mentor.id} also matters because the mentor teaches the practice that changes the ending.",
        ),
        (
            f"What problem did {friend.id} have?",
            f"{friend.id} had trouble with {challenge.label}. The problem was at {challenge.place}, so {hero.id} wanted to help right away.",
        ),
        (
            f"Why could {hero.id} not fix it on the first try?",
            f"{hero.id} cared and hurried in, but caring was not enough by itself. {challenge.first_fail[0].upper()}{challenge.first_fail[1:]}, which showed that {hero.id} needed more proficiency first.",
        ),
        (
            f"What did {mentor.id} teach {hero.id}?",
            f"{mentor.id} taught {lesson.label} at {lesson.place}. The lesson matched the same skill the problem needed, so the practice prepared {hero.id} for the second try.",
        ),
        (
            f"How did practice help {hero.id} succeed?",
            f"Practice gave {hero.id} more proficiency before returning to help. Because {hero.pronoun()} had practiced the right skill, {challenge.success[0].lower() + challenge.success[1:]}",
        ),
        (
            "How did the story end?",
            f"It ended happily: {friend.id} got help, {hero.id} felt proud, and {mentor.id} saw the lesson work. The final picture is warm and calm because the problem is solved and everyone is safe.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    skill = world.facts["species"].skill
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key == skill:
            out.extend(KNOWLEDGE[key])
    return out


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
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
skill_match(S, C) :- species_skill(S, K), challenge_need(C, K).
lesson_match(C, L) :- challenge_need(C, K), lesson_teaches(L, K).
valid(S, C, L) :- species(S), challenge(C), lesson(L), skill_match(S, C), lesson_match(C, L).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, species in SPECIES.items():
        lines.append(asp.fact("species", sid))
        lines.append(asp.fact("species_skill", sid, species.skill))
    for cid, challenge in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("challenge_need", cid, challenge.need))
    for lid, lesson in LESSONS.items():
        lines.append(asp.fact("lesson", lid))
        lines.append(asp.fact("lesson_teaches", lid, lesson.teaches))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Animal storyworld about practice, proficiency, and a happy ending."
    )
    ap.add_argument("--species", choices=SPECIES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--lesson", choices=LESSONS)
    ap.add_argument("--hero-name")
    ap.add_argument("--mentor-name")
    ap.add_argument("--friend-name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate matches Python and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.species and args.challenge and args.lesson:
        species = SPECIES[args.species]
        challenge = CHALLENGES[args.challenge]
        lesson = LESSONS[args.lesson]
        if not valid_story(species, challenge, lesson):
            raise StoryError(explain_rejection(species, challenge, lesson))

    combos = [
        combo
        for combo in valid_combos()
        if (args.species is None or combo[0] == args.species)
        and (args.challenge is None or combo[1] == args.challenge)
        and (args.lesson is None or combo[2] == args.lesson)
    ]
    if not combos:
        if args.species and args.challenge and not args.lesson:
            species = SPECIES[args.species]
            challenge = CHALLENGES[args.challenge]
            dummy_lesson = next(iter(LESSONS.values()))
            if not species_can_do(species, challenge):
                raise StoryError(explain_rejection(species, challenge, dummy_lesson))
        if args.challenge and args.lesson and not args.species:
            dummy_species = next(iter(SPECIES.values()))
            challenge = CHALLENGES[args.challenge]
            lesson = LESSONS[args.lesson]
            if not lesson_fits(challenge, lesson):
                raise StoryError(explain_rejection(dummy_species, challenge, lesson))
        raise StoryError("(No valid combination matches the given options.)")

    species_id, challenge_id, lesson_id = rng.choice(sorted(combos))
    species = SPECIES[species_id]
    hero_name = args.hero_name or rng.choice(NAMES[species_id])
    mentor_choices = [n for n in NAMES[species_id] if n != hero_name]
    mentor_name = args.mentor_name or rng.choice(mentor_choices)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    return StoryParams(
        species=species_id,
        challenge=challenge_id,
        lesson=lesson_id,
        hero_name=hero_name,
        mentor_name=mentor_name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.species not in SPECIES:
        raise StoryError(f"(Unknown species: {params.species})")
    if params.challenge not in CHALLENGES:
        raise StoryError(f"(Unknown challenge: {params.challenge})")
    if params.lesson not in LESSONS:
        raise StoryError(f"(Unknown lesson: {params.lesson})")

    species = SPECIES[params.species]
    challenge = CHALLENGES[params.challenge]
    lesson = LESSONS[params.lesson]
    if not valid_story(species, challenge, lesson):
        raise StoryError(explain_rejection(species, challenge, lesson))

    world = tell(
        species=species,
        challenge=challenge,
        lesson=lesson,
        hero_name=params.hero_name,
        mentor_name=params.mentor_name,
        friend_name=params.friend_name,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (species, challenge, lesson) combos:\n")
        for species, challenge, lesson in combos:
            print(f"  {species:9} {challenge:13} {lesson}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.hero_name}: {p.species} / {p.challenge} / {p.lesson}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
