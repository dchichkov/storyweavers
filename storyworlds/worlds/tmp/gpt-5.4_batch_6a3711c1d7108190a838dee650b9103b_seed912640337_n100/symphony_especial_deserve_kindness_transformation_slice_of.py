#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/symphony_especial_deserve_kindness_transformation_slice_of.py
========================================================================================

A small storyworld about a child in a school music room who worries that they do
not deserve an especial part in the class symphony. A kind classmate and teacher
help the child transform that feeling into steady belonging.

The world model tracks simple physical state (sheet music, instruments, sound)
and emotional state (worry, shame, kindness, pride). The rendered story follows
those state changes rather than swapping words into one fixed paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/symphony_especial_deserve_kindness_transformation_slice_of.py
    python storyworlds/worlds/gpt-5.4/symphony_especial_deserve_kindness_transformation_slice_of.py --venue library --job chimes --helper tape
    python storyworlds/worlds/gpt-5.4/symphony_especial_deserve_kindness_transformation_slice_of.py --job violin --problem torn_music
    python storyworlds/worlds/gpt-5.4/symphony_especial_deserve_kindness_transformation_slice_of.py --job drum --problem sticky_sticks
    python storyworlds/worlds/gpt-5.4/symphony_especial_deserve_kindness_transformation_slice_of.py --all
    python storyworlds/worlds/gpt-5.4/symphony_especial_deserve_kindness_transformation_slice_of.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/symphony_especial_deserve_kindness_transformation_slice_of.py --verify
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    portable: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "teacher_f"}
        male = {"boy", "father", "man", "teacher_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "teacher_f": "teacher",
            "teacher_m": "teacher",
        }.get(self.type, self.type)


@dataclass
class Venue:
    id: str
    label: str
    room_phrase: str
    after_phrase: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Job:
    id: str
    label: str
    phrase: str
    sound: str
    need: str
    delicate: bool
    spotlight: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Problem:
    id: str
    label: str
    need: str
    severity: int
    open_line: str
    private_line: str
    solved_line: str
    qa_cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    need: str
    action: str
    finish: str
    qa_method: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

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


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_blocked_part(world: World) -> list[str]:
    hero = world.get("hero")
    sheet = world.get("sheet")
    out: list[str] = []
    if sheet.meters["damaged"] >= THRESHOLD and hero.meters["needs_help"] >= THRESHOLD:
        sig = ("blocked", "part")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["blocked"] += 1
            hero.memes["worry"] += 1
            hero.memes["shame"] += 1
            out.append("__blocked__")
    return out


def _r_sticky_job(world: World) -> list[str]:
    hero = world.get("hero")
    tool = world.get("tool")
    out: list[str] = []
    if tool.meters["sticky"] >= THRESHOLD and hero.meters["needs_help"] >= THRESHOLD:
        sig = ("blocked", "tool")
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["blocked"] += 1
            hero.memes["worry"] += 1
            hero.memes["shame"] += 1
            out.append("__blocked__")
    return out


def _r_kindness_lifts(world: World) -> list[str]:
    hero = world.get("hero")
    helper = world.get("friend")
    out: list[str] = []
    if hero.meters["ready"] >= THRESHOLD and helper.memes["kindness"] >= THRESHOLD:
        sig = ("lift", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] = 0.0
            hero.memes["shame"] = 0.0
            hero.memes["belonging"] += 1
            hero.memes["pride"] += 1
            out.append("__lifted__")
    return out


def _r_music_forms(world: World) -> list[str]:
    hero = world.get("hero")
    ensemble = world.get("ensemble")
    out: list[str] = []
    if hero.meters["playing"] >= THRESHOLD and hero.meters["ready"] >= THRESHOLD:
        sig = ("music", ensemble.id)
        if sig not in world.fired:
            world.fired.add(sig)
            ensemble.meters["sound"] += 1
            out.append("__music__")
    return out


CAUSAL_RULES = [
    Rule("blocked_part", "physical", _r_blocked_part),
    Rule("sticky_job", "physical", _r_sticky_job),
    Rule("kindness_lifts", "social", _r_kindness_lifts),
    Rule("music_forms", "physical", _r_music_forms),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    return produced


VENUES = {
    "school": Venue(
        "school",
        "the school music room",
        "the school music room smelled faintly of pencil shavings and polished wood",
        "after class",
        "The last note floated under the bright classroom lights, and the whole room felt warmer than before.",
        tags={"school"},
    ),
    "library": Venue(
        "library",
        "the library meeting room",
        "the library meeting room had stacked chairs along one wall and a paper sign that said COMMUNITY MUSIC",
        "after the library program",
        "The last note softened into the hush of the library hall, and even the whispering pages nearby seemed to listen.",
        tags={"library"},
    ),
    "apartment": Venue(
        "apartment",
        "the apartment building common room",
        "the apartment building common room held folding chairs, a tin of crackers, and coats drying by the door",
        "after supper practice",
        "The last note settled over the little common room, and the evening felt stitched together by sound.",
        tags={"home"},
    ),
}

JOBS = {
    "violin": Job(
        "violin",
        "violin",
        "a small violin part",
        "thin bright notes",
        "clear_music",
        delicate=True,
        spotlight="The violin line rose like a ribbon over the others.",
        tags={"violin", "music"},
    ),
    "chimes": Job(
        "chimes",
        "chime bar",
        "the chime part",
        "soft silver rings",
        "steady_hands",
        delicate=False,
        spotlight="Each chime ring slipped into the song like a tiny star.",
        tags={"chimes", "music"},
    ),
    "drum": Job(
        "drum",
        "drum",
        "the drum beat",
        "a round steady thump",
        "dry_sticks",
        delicate=False,
        spotlight="The drum beat held everyone together like careful footsteps.",
        tags={"drum", "music"},
    ),
}

PROBLEMS = {
    "torn_music": Problem(
        "torn_music",
        "torn sheet music",
        "clear_music",
        2,
        "A corner of the music page had torn away where the next notes should have been.",
        'When the child looked down, the missing corner made the part feel suddenly too hard.',
        "The page lay flat again, and the notes could be read in one calm line.",
        "part of the music page was torn, so the notes were hard to read",
        tags={"music_page", "reading_music"},
    ),
    "shaky_hands": Problem(
        "shaky_hands",
        "shaky hands",
        "steady_hands",
        1,
        "The room buzzed with chairs scraping and cases opening, and the child's hands began to wobble.",
        'The child worried that everyone would see the instrument shake and think, "You do not deserve this especial part."',
        "With a slow breath and a kind shoulder beside them, the hands steadied.",
        "nervous hands made it hard to hold the part steady",
        tags={"feelings", "breathing"},
    ),
    "sticky_sticks": Problem(
        "sticky_sticks",
        "sticky drum sticks",
        "dry_sticks",
        2,
        "One drum stick had picked up juice from the snack table and felt tacky in the child's palm.",
        "The sticky grip made every practice tap feel wrong and clumsy.",
        "The sticks felt clean and dry again, so the beat came back smoothly.",
        "the drum sticks were sticky, so they did not feel right in the child's hands",
        tags={"cleanup", "drum"},
    ),
}

HELPERS = {
    "tape": Helper(
        "tape",
        "a strip of tape",
        "clear_music",
        "smoothed the torn corner and fixed it down with a neat strip of tape",
        "The page no longer fluttered when the child lifted it.",
        "used tape to mend the torn music page",
        tags={"tape", "fixing"},
    ),
    "breathe": Helper(
        "breathe",
        "a slow breathing count",
        "steady_hands",
        'stood close and whispered, "Breathe in for four, and let it out for four with me,"',
        "Soon the child's shoulders loosened instead of bunching up.",
        "counted slow breaths together until the hands were steady",
        tags={"breathing", "kindness"},
    ),
    "cloth": Helper(
        "cloth",
        "a damp cloth",
        "dry_sticks",
        "wiped the sticky drum sticks clean with a damp cloth and dried them on a paper napkin",
        "The wood felt smooth again instead of tacky.",
        "cleaned and dried the sticky drum sticks",
        tags={"cleanup", "helping"},
    ),
}

GIRL_NAMES = ["Lina", "Maya", "Ava", "Nora", "Ella", "Lucy", "Zoe", "Ivy"]
BOY_NAMES = ["Eli", "Noah", "Ben", "Theo", "Sam", "Milo", "Finn", "Jack"]
TRAITS = ["careful", "gentle", "hopeful", "quiet", "earnest", "thoughtful"]


def valid_helper(job: Job, problem: Problem, helper: Helper) -> bool:
    return job.need == problem.need == helper.need


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for venue in VENUES:
        for job_id, job in JOBS.items():
            for prob_id, prob in PROBLEMS.items():
                for helper_id, helper in HELPERS.items():
                    if valid_helper(job, prob, helper):
                        combos.append((venue, job_id, prob_id, helper_id))
    return combos


def explain_rejection(job: Job, problem: Problem, helper: Helper) -> str:
    return (
        f"(No story: the {helper.label} helps with {helper.need.replace('_', ' ')}, "
        f"but the {job.label} facing {problem.label} needs {job.need.replace('_', ' ')}. "
        "Pick a helper that truly fixes the problem.)"
    )


def intro(world: World, venue: Venue, hero: Entity, friend: Entity, teacher: Entity, job: Job) -> None:
    world.say(
        f"On Tuesday afternoon, {hero.id} hurried into {venue.label}. "
        f"{venue.room_phrase.capitalize()}."
    )
    world.say(
        f"Music class was getting ready for a little symphony for families, and "
        f"{teacher.id} had already set the chairs in a half-circle."
    )
    world.say(
        f"{hero.id} had been given {job.phrase}. {friend.id} smiled from the next chair, "
        f"already warming up with small careful sounds."
    )


def assign_special(world: World, hero: Entity, teacher: Entity, job: Job) -> None:
    hero.memes["hope"] += 1
    world.say(
        f'"This part is especial," {teacher.id} said, tapping the top of the page. '
        f'"It may be small, but the whole song leans on it."'
    )
    world.say(
        f"{hero.id} sat a little straighter. Being trusted with {job.phrase} made "
        f"{hero.pronoun('object')} feel proud for one bright second."
    )


def trouble_appears(world: World, hero: Entity, job: Job, problem: Problem) -> None:
    hero.meters["needs_help"] += 1
    if problem.id == "torn_music":
        world.get("sheet").meters["damaged"] += 1
    elif problem.id == "sticky_sticks":
        world.get("tool").meters["sticky"] += 1
    elif problem.id == "shaky_hands":
        hero.meters["tremble"] += 1
    propagate(world, narrate=False)
    world.say(problem.open_line)
    world.say(problem.private_line)


def shrink_back(world: World, hero: Entity, teacher: Entity) -> None:
    hero.memes["withdrawal"] += 1
    world.say(
        f"When {teacher.id} asked everyone to get ready, {hero.id} lowered "
        f"{hero.pronoun('possessive')} eyes and held back instead of playing."
    )


def notice_kindness(world: World, friend: Entity, hero: Entity) -> None:
    friend.memes["kindness"] += 1
    world.say(
        f"{friend.id} noticed at once. Instead of laughing or hurrying ahead, "
        f"{friend.pronoun()} leaned over with a soft, waiting face."
    )


def help_fix(world: World, friend: Entity, hero: Entity, helper: Helper, problem: Problem) -> None:
    if helper.id == "tape":
        world.get("sheet").meters["damaged"] = 0.0
    elif helper.id == "cloth":
        world.get("tool").meters["sticky"] = 0.0
    elif helper.id == "breathe":
        hero.meters["tremble"] = 0.0
    hero.meters["ready"] += 1
    propagate(world, narrate=False)
    world.say(
        f'{friend.id} {helper.action}. "{hero.id}, you deserve to be here with the rest of us," '
        f"{friend.pronoun()} said."
    )
    world.say(helper.finish)
    world.say(problem.solved_line)


def teacher_reframes(world: World, teacher: Entity, hero: Entity, job: Job) -> None:
    teacher.memes["care"] += 1
    world.say(
        f'{teacher.id} came over then and nodded. "An especial part is not the same '
        f'as a big part," {teacher.pronoun()} said. "It means the song would miss you '
        f'if you were gone."'
    )
    world.say(
        f"The words landed gently. {hero.id} no longer felt as if {hero.pronoun()} "
        f"had to prove anything bigger than one honest note."
    )


def play_together(world: World, hero: Entity, friend: Entity, job: Job) -> None:
    hero.meters["playing"] += 1
    propagate(world, narrate=False)
    world.say(
        f"When the teacher counted them in, {hero.id} joined {friend.id}. "
        f"{job.spotlight}"
    )
    world.say(
        f"Soon {job.sound} folded into the room, and the small class sounded like one warm symphony."
    )


def ending(world: World, venue: Venue, hero: Entity, friend: Entity, teacher: Entity) -> None:
    hero.memes["gratitude"] += 1
    world.say(
        f"{venue.ending_image} {hero.id} looked at {friend.id}, then at {teacher.id}, "
        f"and smiled without ducking away."
    )
    world.say(
        f"{hero.pronoun().capitalize()} still had the same seat and the same little part, "
        f"but inside, something had changed. Kindness had turned fear into belonging."
    )


def tell(
    venue: Venue,
    job: Job,
    problem: Problem,
    helper: Helper,
    hero_name: str = "Lina",
    hero_gender: str = "girl",
    friend_name: str = "Ben",
    friend_gender: str = "boy",
    teacher_type: str = "teacher_f",
    trait: str = "quiet",
) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="hero", traits=[trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_gender, role="friend", traits=["kind"]))
    teacher = world.add(Entity(id="Ms. Bell" if teacher_type == "teacher_f" else "Mr. Bell",
                               kind="character", type=teacher_type, role="teacher"))
    world.add(Entity(id="sheet", type="sheet_music", label="music page", portable=True))
    world.add(Entity(id="tool", type="instrument_tool", label=job.label, portable=True))
    world.add(Entity(id="ensemble", type="group", label="class ensemble"))

    intro(world, venue, hero, friend, teacher, job)
    assign_special(world, hero, teacher, job)

    world.para()
    trouble_appears(world, hero, job, problem)
    shrink_back(world, hero, teacher)

    world.para()
    notice_kindness(world, friend, hero)
    help_fix(world, friend, hero, helper, problem)
    teacher_reframes(world, teacher, hero, job)

    world.para()
    play_together(world, hero, friend, job)
    ending(world, venue, hero, friend, teacher)

    world.facts.update(
        venue=venue,
        job=job,
        problem=problem,
        helper=helper,
        hero=hero,
        friend=friend,
        teacher=teacher,
        resolved=hero.meters["ready"] >= THRESHOLD,
        played=hero.meters["playing"] >= THRESHOLD,
        sounded=world.get("ensemble").meters["sound"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    venue: str
    job: str
    problem: str
    helper: str
    hero_name: str
    hero_gender: str
    friend_name: str
    friend_gender: str
    teacher_gender: str
    trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "music": [(
        "What is a symphony?",
        "A symphony is music made from many parts played together. Even quiet parts matter because they help the whole piece sound full."
    )],
    "music_page": [(
        "Why does sheet music need to be easy to read?",
        "A player looks at the notes to know when and how to play. If part of the page is torn, the player can lose the place."
    )],
    "breathing": [(
        "Why can slow breathing help before performing?",
        "Slow breathing tells your body to settle down. That can make shaky hands and a fast heartbeat calm a little."
    )],
    "cleanup": [(
        "Why should instruments and music tools stay clean and dry?",
        "Clean, dry tools are easier to hold and use well. Sticky or messy tools can make playing harder."
    )],
    "kindness": [(
        "What does kindness look like when someone feels left out?",
        "Kindness can look like noticing quietly, helping without teasing, and saying words that help the person feel they belong."
    )],
    "school": [(
        "What happens in a school music room?",
        "Children can practice songs, learn rhythms, and play together there. The room is a place for listening as well as making sound."
    )],
    "library": [(
        "Why might a library have a music program?",
        "Libraries often host community events where people learn and share together. A music program can turn a quiet room into a friendly gathering place."
    )],
    "home": [(
        "What is a common room?",
        "A common room is a space shared by many people in a building. Neighbors can meet there for snacks, games, or small events."
    )],
}

KNOWLEDGE_ORDER = ["music", "music_page", "breathing", "cleanup", "kindness", "school", "library", "home"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, job, venue, problem = f["hero"], f["job"], f["venue"], f["problem"]
    return [
        f'Write a slice-of-life story for ages 3 to 5 that includes the words "symphony", "especial", and "deserve".',
        f"Tell a gentle school-and-community story where {hero.id} worries about {job.phrase} in {venue.label} because of {problem.label}, and kindness changes the feeling of the whole afternoon.",
        'Write a story about transformation through kindness, where a child thinks they do not deserve an especial place in the music, but learns that small parts matter.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero, friend, teacher = f["hero"], f["friend"], f["teacher"]
    job, problem, helper, venue = f["job"], f["problem"], f["helper"], f["venue"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who was getting ready to play {job.phrase}, and about {friend.id} and {teacher.id}, who helped. The story stays close to one ordinary afternoon in {venue.label}."
        ),
        (
            f"Why did {hero.id} pull back before playing?",
            f"{hero.id} pulled back because {problem.qa_cause}. That trouble made {hero.pronoun('object')} worry that {hero.pronoun()} did not deserve the especial part after all."
        ),
        (
            f"How did {friend.id} help {hero.id}?",
            f"{friend.id} {helper.qa_method}. Just as important, {friend.pronoun()} said that {hero.id} deserved to be there with everybody else."
        ),
        (
            f"What did the teacher mean by calling the part especial?",
            f"{teacher.id} meant that the part mattered to the whole song even if it was small. The child did not need to be the loudest one to belong in the symphony."
        ),
    ]
    if f["played"]:
        qa.append((
            f"How did {hero.id} change by the end?",
            f"At first {hero.id} felt ashamed and tried to disappear. By the end, {hero.pronoun()} played with the group and felt proud to belong, which shows the transformation clearly."
        ))
    if f["sounded"]:
        qa.append((
            "What proved that things were better at the end?",
            f"The music came together and sounded like one warm symphony. The ending image shows {hero.id} smiling openly instead of hiding."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"music", "kindness"} | set(world.facts["venue"].tags) | set(world.facts["problem"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        lines.append(f"  {ent.id:10} ({ent.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("school", "violin", "torn_music", "tape", "Lina", "girl", "Ben", "boy", "teacher_f", "quiet"),
    StoryParams("library", "chimes", "shaky_hands", "breathe", "Eli", "boy", "Maya", "girl", "teacher_f", "earnest"),
    StoryParams("apartment", "drum", "sticky_sticks", "cloth", "Nora", "girl", "Sam", "boy", "teacher_m", "careful"),
    StoryParams("school", "chimes", "shaky_hands", "breathe", "Theo", "boy", "Lucy", "girl", "teacher_m", "thoughtful"),
    StoryParams("library", "drum", "sticky_sticks", "cloth", "Ava", "girl", "Milo", "boy", "teacher_f", "gentle"),
]


ASP_RULES = r"""
valid_helper(J, P, H) :- job(J), problem(P), helper(H), need_job(J, N), need_problem(P, N), need_helper(H, N).
valid(V, J, P, H) :- venue(V), valid_helper(J, P, H).

resolved(J, P, H) :- valid_helper(J, P, H).
played(J, P, H) :- resolved(J, P, H).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for venue in VENUES:
        lines.append(asp.fact("venue", venue))
    for jid, job in JOBS.items():
        lines.append(asp.fact("job", jid))
        lines.append(asp.fact("need_job", jid, job.need))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("need_problem", pid, problem.need))
    for hid, helper in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("need_helper", hid, helper.need))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    cset = set(asp_valid_combos())
    pset = set(valid_combos())
    if cset == pset:
        print(f"OK: ASP gate matches valid_combos() ({len(cset)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cset - pset:
            print("  only in clingo:", sorted(cset - pset))
        if pset - cset:
            print("  only in python:", sorted(pset - cset))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path only
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child in music practice learns that kindness can change how a small part feels."
    )
    ap.add_argument("--venue", choices=VENUES)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--teacher-gender", choices=["teacher_f", "teacher_m"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_name(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.job and args.problem and args.helper:
        job = JOBS[args.job]
        problem = PROBLEMS[args.problem]
        helper = HELPERS[args.helper]
        if not valid_helper(job, problem, helper):
            raise StoryError(explain_rejection(job, problem, helper))

    combos = [
        c for c in valid_combos()
        if (args.venue is None or c[0] == args.venue)
        and (args.job is None or c[1] == args.job)
        and (args.problem is None or c[2] == args.problem)
        and (args.helper is None or c[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    venue, job, problem, helper = rng.choice(sorted(combos))
    hero_name, hero_gender = _pick_name(rng)
    friend_name, friend_gender = _pick_name(rng, avoid=hero_name)
    teacher_gender = args.teacher_gender or rng.choice(["teacher_f", "teacher_m"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        venue=venue,
        job=job,
        problem=problem,
        helper=helper,
        hero_name=hero_name,
        hero_gender=hero_gender,
        friend_name=friend_name,
        friend_gender=friend_gender,
        teacher_gender=teacher_gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        VENUES[params.venue],
        JOBS[params.job],
        PROBLEMS[params.problem],
        HELPERS[params.helper],
        params.hero_name,
        params.hero_gender,
        params.friend_name,
        params.friend_gender,
        params.teacher_gender,
        params.trait,
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
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (venue, job, problem, helper) combos:\n")
        for venue, job, problem, helper in combos:
            print(f"  {venue:10} {job:8} {problem:13} {helper}")
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
            header = f"### {p.hero_name}: {p.job} / {p.problem} / {p.helper} at {p.venue}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
