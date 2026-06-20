#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/stereo_puppet_kitchen_flashback_mystery.py
=====================================================================

A standalone storyworld for a small child-facing kitchen mystery built around a
missing puppet, a humming stereo, and a flashback that helps solve the case.

Premise
-------
A child is in the kitchen, ready for a tiny puppet show, when one favorite
puppet cannot be found. The kitchen stereo is still playing a song from earlier,
and some present-day clue in the room stirs a flashback. That remembered moment
points to a reasonable hiding place in the kitchen, where the puppet is found.
The ending image proves what changed: the show can begin after the mystery is
solved.

Reasonableness constraint
-------------------------
Not every clue can honestly lead to every hiding place. This world only tells a
story when the chosen clue is the kind that could plausibly connect to the
puppet's hiding place:

* flour dust -> baking bowl / mixing bowl
* crinkly bag sound -> grocery bag
* apron string memory -> apron pocket
* chair scrape -> under the kitchen chair

The flashback must also fit the place: the child remembers what happened earlier
while the stereo was playing. Unreasonable explicit combinations are rejected
with a clear StoryError.

Run it
------
    python storyworlds/worlds/gpt-5.4/stereo_puppet_kitchen_flashback_mystery.py
    python storyworlds/worlds/gpt-5.4/stereo_puppet_kitchen_flashback_mystery.py --clue flour_dust --hiding bowl
    python storyworlds/worlds/gpt-5.4/stereo_puppet_kitchen_flashback_mystery.py --clue flour_dust --hiding bag
    python storyworlds/worlds/gpt-5.4/stereo_puppet_kitchen_flashback_mystery.py --all
    python storyworlds/worlds/gpt-5.4/stereo_puppet_kitchen_flashback_mystery.py --qa --json
    python storyworlds/worlds/gpt-5.4/stereo_puppet_kitchen_flashback_mystery.py --verify
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
            "grandmother": "grandma",
            "grandfather": "grandpa",
        }.get(self.type, self.type)


@dataclass
class PuppetKind:
    id: str
    label: str
    phrase: str
    voice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    notice: str
    flashback: str
    question_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HidingPlace:
    id: str
    label: str
    phrase: str
    where: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mood:
    id: str
    stereo_line: str
    opening: str
    ending: str


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


def matches(clue: Clue, hiding: HidingPlace) -> bool:
    return hiding.id in CLUE_TO_HIDING[clue.id]


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for puppet_id in PUPPETS:
        for clue_id, clue in CLUES.items():
            for hiding_id, hiding in HIDING_PLACES.items():
                if matches(clue, hiding):
                    out.append((puppet_id, clue_id, hiding_id))
    return out


def explain_rejection(clue: Clue, hiding: HidingPlace) -> str:
    options = ", ".join(sorted(CLUE_TO_HIDING[clue.id]))
    return (
        f"(No story: the clue '{clue.label}' does not honestly point to {hiding.phrase}. "
        f"In this world, that clue fits only these hiding places: {options}.)"
    )


def introduce(world: World, child: Entity, grownup: Entity, puppet: PuppetKind, mood: Mood) -> None:
    child.memes["anticipation"] += 1
    child.memes["love"] += 1
    world.say(
        f"{mood.opening} {child.id} stood in the kitchen with {puppet.phrase} ready for a tiny puppet show."
    )
    world.say(
        f"On the counter, the stereo {mood.stereo_line}, and the cozy room felt full of secrets."
    )
    world.say(
        f'{grownup.label_word.capitalize()} was nearby, slicing fruit and smiling. "{puppet.voice}" was the special voice {child.id} always used for that puppet.'
    )


def loss(world: World, child: Entity, puppet: PuppetKind) -> None:
    child.memes["worry"] += 1
    world.get("puppet").meters["missing"] += 1
    world.say(
        f"But when {child.pronoun()} reached for {puppet.label}, the puppet was gone."
    )
    world.say(
        f"{child.id} looked on the chair, under the table, and beside the sink. Now the kitchen felt less cozy and more mysterious."
    )


def investigate(world: World, child: Entity, grownup: Entity, clue: Clue) -> None:
    world.say(
        f"Then {child.id} noticed {clue.notice}. {child.pronoun().capitalize()} went still, as if the kitchen itself were whispering a clue."
    )
    world.say(
        f'"What is it?" asked {grownup.label_word}. "{clue.question_word}," {child.id} whispered.'
    )


def flashback(world: World, child: Entity, clue: Clue, hiding: HidingPlace) -> None:
    child.memes["memory"] += 1
    world.facts["flashback_triggered"] = True
    world.para()
    world.say("A memory fluttered back.")
    world.say(
        f"Earlier, while the stereo was playing, {clue.flashback} {hiding.where}."
    )
    world.say(
        f"In the memory, it had happened so fast that {child.id} had not understood it then. Now the old moment clicked into place."
    )


def solve(world: World, child: Entity, grownup: Entity, puppet: PuppetKind, hiding: HidingPlace) -> None:
    puppet_ent = world.get("puppet")
    puppet_ent.meters["missing"] = 0.0
    puppet_ent.meters["found"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    grownup.memes["pride"] += 1
    world.para()
    world.say(
        f"{child.id} hurried to {hiding.phrase}. {hiding.reveal}"
    )
    world.say(
        f'"There you are!" {child.pronoun()} cried, hugging {puppet.label} close. {grownup.label_word.capitalize()} laughed softly and said that good detectives notice small things.'
    )


def ending(world: World, child: Entity, puppet: PuppetKind, mood: Mood) -> None:
    world.say(
        f"Soon {child.id} lifted the puppet again, and the little kitchen show could finally begin."
    )
    world.say(
        f"{mood.ending} The stereo kept playing, but now it sounded less spooky and more like applause."
    )


def tell(
    puppet: PuppetKind,
    clue: Clue,
    hiding: HidingPlace,
    mood: Mood,
    child_name: str = "Mira",
    child_type: str = "girl",
    grownup_type: str = "grandmother",
) -> World:
    if not matches(clue, hiding):
        raise StoryError(explain_rejection(clue, hiding))

    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="child"))
    grownup = world.add(
        Entity(id="Grownup", kind="character", type=grownup_type, role="grownup", label="the grown-up")
    )
    puppet_ent = world.add(
        Entity(id="puppet", type="puppet", label=puppet.label, attrs={"kind": puppet.id})
    )
    stereo = world.add(Entity(id="stereo", type="stereo", label="stereo"))
    kitchen = world.add(Entity(id="kitchen", type="room", label="kitchen"))

    stereo.meters["playing"] += 1
    kitchen.memes["mystery"] += 1

    introduce(world, child, grownup, puppet, mood)
    loss(world, child, puppet)
    world.para()
    investigate(world, child, grownup, clue)
    flashback(world, child, clue, hiding)
    solve(world, child, grownup, puppet, hiding)
    ending(world, child, puppet, mood)

    world.facts.update(
        child=child,
        grownup=grownup,
        puppet_cfg=puppet,
        clue=clue,
        hiding=hiding,
        mood=mood,
        found=puppet_ent.meters["found"] >= THRESHOLD,
        missing=puppet_ent.meters["missing"] >= THRESHOLD,
        flashback=world.facts.get("flashback_triggered", False),
    )
    return world


PUPPETS = {
    "rabbit": PuppetKind("rabbit", "the rabbit puppet", "a soft rabbit puppet", "Carrot crumbs for everyone!", {"puppet"}),
    "dragon": PuppetKind("dragon", "the dragon puppet", "a bright green dragon puppet", "Beware my tiny roar!", {"puppet"}),
    "duck": PuppetKind("duck", "the duck puppet", "a yellow duck puppet", "Quack-quack, detective on duty!", {"puppet"}),
}

CLUES = {
    "flour_dust": Clue(
        "flour_dust",
        "a faint dusting of flour on the counter",
        "a faint dusting of flour leading toward the big mixing bowl",
        "the puppet had slid across the counter in a puff of flour",
        "Flour",
        {"flour", "kitchen"},
    ),
    "bag_crinkle": Clue(
        "bag_crinkle",
        "a soft crinkle from the grocery bag by the door",
        "a soft crinkle from the grocery bag by the door",
        "the puppet had toppled in when the grocery bag rustled open",
        "That bag",
        {"bag", "kitchen"},
    ),
    "apron_string": Clue(
        "apron_string",
        "one apron string swaying from a hook",
        "one apron string swaying from a hook",
        "the puppet had been tucked away when the apron was lifted in a hurry",
        "The apron",
        {"apron", "kitchen"},
    ),
    "chair_scrape": Clue(
        "chair_scrape",
        "a tiny scrape mark beside the kitchen chair",
        "a tiny scrape mark beside the kitchen chair",
        "the chair had bumped back and the puppet had slipped to the floor",
        "The chair",
        {"chair", "kitchen"},
    ),
}

HIDING_PLACES = {
    "bowl": HidingPlace(
        "bowl",
        "the big mixing bowl",
        "the big mixing bowl on the counter",
        "into the big mixing bowl",
        "Inside the bowl lay the puppet, dusted with a silly little cloud of flour.",
        {"bowl", "kitchen"},
    ),
    "bag": HidingPlace(
        "bag",
        "the grocery bag",
        "the crinkly grocery bag near the door",
        "into the grocery bag",
        "Inside the bag sat the puppet between a loaf of bread and a bunch of parsley.",
        {"bag", "kitchen"},
    ),
    "apron": HidingPlace(
        "apron",
        "the apron pocket",
        "the apron hanging by the pantry door",
        "into the apron pocket",
        "There, deep in the pocket, waited the puppet with one ear peeking out.",
        {"apron", "kitchen"},
    ),
    "chair": HidingPlace(
        "chair",
        "under the kitchen chair",
        "the wooden chair by the little table",
        "under the kitchen chair",
        "Curled in the shadow under the chair was the puppet, looking as if it had been hiding on purpose.",
        {"chair", "kitchen"},
    ),
}

CLUE_TO_HIDING = {
    "flour_dust": {"bowl"},
    "bag_crinkle": {"bag"},
    "apron_string": {"apron"},
    "chair_scrape": {"chair"},
}

MOODS = {
    "soft": Mood(
        "soft",
        "played a soft song with a tiny hiss between notes",
        "One late afternoon",
        "Sunlight warmed the yellow tiles",
    ),
    "rainy": Mood(
        "rainy",
        "murmured under the patter of rain on the window",
        "On a rainy afternoon",
        "Rain still tapped the glass",
    ),
    "dusky": Mood(
        "dusky",
        "played a twinkly tune as the light outside turned blue",
        "At dusky suppertime",
        "The window had gone deep blue",
    ),
}

GIRL_NAMES = ["Mira", "Lina", "Tess", "Nora", "Ivy", "Ruby", "Ella", "June"]
BOY_NAMES = ["Owen", "Milo", "Finn", "Theo", "Ben", "Eli", "Jude", "Noah"]


@dataclass
class StoryParams:
    puppet: str
    clue: str
    hiding: str
    mood: str
    child_name: str
    child_type: str
    grownup: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "stereo": [(
        "What is a stereo?",
        "A stereo is a machine that plays music out loud through speakers. It can make a room feel calm, busy, or exciting."
    )],
    "puppet": [(
        "What is a puppet?",
        "A puppet is a toy you move with your hand or strings to make it seem alive. People often use puppets to tell stories or put on shows."
    )],
    "flashback": [(
        "What is a flashback in a story?",
        "A flashback is when the story remembers something that happened earlier. It helps you understand the present by looking back for a moment."
    )],
    "flour": [(
        "What is flour?",
        "Flour is a soft white powder used for baking. It can leave dusty marks when it spills."
    )],
    "bag": [(
        "Why does a paper grocery bag make a crinkly sound?",
        "A paper bag wrinkles and bends when it moves, so it makes a crisp crinkly sound. That sound can help you notice where something is."
    )],
    "apron": [(
        "What is an apron for?",
        "An apron is a cloth covering people wear over clothes while cooking or baking. Some aprons have pockets that can hold small things."
    )],
    "chair": [(
        "Why might something slide under a chair?",
        "A small toy can slip under a chair if it drops and rolls or gets bumped by a foot or a chair leg. Shadows under furniture can make it hard to see."
    )],
    "mystery": [(
        "What makes a mystery feel exciting?",
        "A mystery feels exciting when something is hidden and the characters must notice clues to solve it. Each clue makes the answer feel closer."
    )],
}
KNOWLEDGE_ORDER = ["stereo", "puppet", "flashback", "mystery", "flour", "bag", "apron", "chair"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    puppet = f["puppet_cfg"]
    clue = f["clue"]
    hiding = f["hiding"]
    return [
        'Write a short mystery for a 3-to-5-year-old set in a kitchen that includes the words "stereo" and "puppet" and uses a flashback.',
        f"Tell a gentle kitchen mystery where {child.id} cannot find {puppet.label}, notices {clue.label}, remembers something from earlier, and finds the puppet in {hiding.phrase}.",
        "Write a child-facing story with a small missing-object mystery, a flashback clue, and a happy ending where a puppet show can finally begin.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    grownup = f["grownup"]
    puppet = f["puppet_cfg"]
    clue = f["clue"]
    hiding = f["hiding"]
    mood = f["mood"]
    pw = grownup.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {pw}, and {puppet.phrase}. {child.id} wants to start a little puppet show in the kitchen."
        ),
        (
            "What made the kitchen feel mysterious?",
            f"The puppet was missing just when the show was supposed to begin, and the stereo kept playing in the background. That made the ordinary kitchen feel full of clues."
        ),
        (
            f"What clue did {child.id} notice?",
            f"{child.id} noticed {clue.notice}. That small detail made {child.pronoun()} stop and think instead of searching wildly."
        ),
    ]
    if f.get("flashback"):
        qa.append((
            "How did the flashback help solve the mystery?",
            f"The flashback brought back an earlier moment while the stereo was playing, and that memory showed what had happened to the puppet. Because of that remembered moment, {child.id} knew to look in {hiding.phrase}."
        ))
    if f.get("found"):
        qa.append((
            f"Where was the puppet, and why did it end up there?",
            f"The puppet was in {hiding.phrase}. It ended up there because earlier, during the busy kitchen moment, it slipped or got tucked there without {child.id} noticing."
        ))
        qa.append((
            "How did the story end?",
            f"It ended happily: {child.id} found the puppet, felt relieved, and could finally begin the show. {mood.ending}, and the stereo no longer sounded spooky."
        ))
    qa.append((
        f"What did {pw} say about solving mysteries?",
        f"{pw.capitalize()} said good detectives notice small things. That mattered because the tiny clue was what led {child.id} to the right memory."
    ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"stereo", "puppet", "flashback", "mystery"}
    tags |= set(f["clue"].tags)
    tags |= set(f["hiding"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("rabbit", "flour_dust", "bowl", "soft", "Mira", "girl", "grandmother"),
    StoryParams("dragon", "bag_crinkle", "bag", "rainy", "Owen", "boy", "father"),
    StoryParams("duck", "apron_string", "apron", "dusky", "Lina", "girl", "mother"),
    StoryParams("rabbit", "chair_scrape", "chair", "soft", "Theo", "boy", "grandfather"),
]


ASP_RULES = r"""
match(flour_dust, bowl).
match(bag_crinkle, bag).
match(apron_string, apron).
match(chair_scrape, chair).

valid(P, C, H) :- puppet(P), clue(C), hiding(H), match(C, H).

found_story :- chosen_clue(C), chosen_hiding(H), match(C, H).
outcome(found) :- found_story.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PUPPETS:
        lines.append(asp.fact("puppet", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for hid in HIDING_PLACES:
        lines.append(asp.fact("hiding", hid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_clue", params.clue),
        asp.fact("chosen_hiding", params.hiding),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "found" if matches(CLUES[params.clue], HIDING_PLACES[params.hiding]) else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    cases = list(CURATED)
    for p in cases:
        if asp_outcome(p) != outcome_of(p):
            rc = 1
            print("MISMATCH in outcome:", p)

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("(Verify failed: generated story was empty.)")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Kitchen mystery storyworld with a stereo, a puppet, and a flashback clue."
    )
    ap.add_argument("--puppet", choices=PUPPETS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--hiding", choices=HIDING_PLACES)
    ap.add_argument("--mood", choices=MOODS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.clue and args.hiding:
        clue, hiding = CLUES[args.clue], HIDING_PLACES[args.hiding]
        if not matches(clue, hiding):
            raise StoryError(explain_rejection(clue, hiding))

    combos = [
        c for c in valid_combos()
        if (args.puppet is None or c[0] == args.puppet)
        and (args.clue is None or c[1] == args.clue)
        and (args.hiding is None or c[2] == args.hiding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    puppet_id, clue_id, hiding_id = rng.choice(sorted(combos))
    mood = args.mood or rng.choice(sorted(MOODS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    grownup = args.grownup or rng.choice(["mother", "father", "grandmother", "grandfather"])
    return StoryParams(puppet_id, clue_id, hiding_id, mood, child_name, gender, grownup)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PUPPETS[params.puppet],
        CLUES[params.clue],
        HIDING_PLACES[params.hiding],
        MOODS[params.mood],
        params.child_name,
        params.child_type,
        params.grownup,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (puppet, clue, hiding) combos:\n")
        for puppet, clue, hiding in combos:
            print(f"  {puppet:8} {clue:13} {hiding}")
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
            header = f"### {p.child_name}: {p.puppet} / {p.clue} / {p.hiding}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
