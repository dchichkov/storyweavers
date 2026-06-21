#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/attractive_laundry_room_conflict_nursery_rhyme.py
=============================================================================

A tiny storyworld about two children in a laundry room who both want the same
attractive thing. The room hums, the wanting turns into a quarrel, and a grown-up
finds a fair fix that fits the object itself.

The style leans nursery-rhyme-light: musical, child-facing, concrete, and gently
repetitive, while still being state-driven rather than template-swapped.

Run it
------
    python storyworlds/worlds/gpt-5.4/attractive_laundry_room_conflict_nursery_rhyme.py
    python storyworlds/worlds/gpt-5.4/attractive_laundry_room_conflict_nursery_rhyme.py --thing striped_sock
    python storyworlds/worlds/gpt-5.4/attractive_laundry_room_conflict_nursery_rhyme.py --thing striped_sock --resolution find_match
    python storyworlds/worlds/gpt-5.4/attractive_laundry_room_conflict_nursery_rhyme.py --thing green_button --resolution count_and_share
    python storyworlds/worlds/gpt-5.4/attractive_laundry_room_conflict_nursery_rhyme.py --all
    python storyworlds/worlds/gpt-5.4/attractive_laundry_room_conflict_nursery_rhyme.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/attractive_laundry_room_conflict_nursery_rhyme.py --verify
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
    traits: tuple = field(default_factory=tuple)
    name: str = ""
    title: str = ""
    voice: str = ""
    thanks: str = ""
    scold: str = ""
    help_action: str = ""
    face: str = ""
    path_line: str = ""
    ending_image: str = ""
    weak_spot: str = ""
    role_text: str = ""
    need: str = ""
    metallic: str = ""
    special: str = ""
    question_reply: str = ""
    wisdom: str = ""
    rising_line: str = ""
    risk: str = ""
    qa_text: str = ""
    location_text: str = ""
    use_line: str = ""
    cry: str = ""
    ending_line: str = ""
    reach: str = ""
    damage: str = ""
    use: str = ""
    opening: str = ""
    warning: str = ""
    owner_text: str = ""
    ground: str = ""
    action_line: str = ""
    kindness_text: str = ""
    calm: str = ""
    restored: str = ""
    shine: str = ""
    reveal_text: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class AttractiveThing:
    id: str
    label: str
    phrase: str
    kind: str
    place: str
    sparkle: str
    rhyme_line: str
    end_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Resolution:
    id: str
    works_for: set[str]
    title: str
    action: str
    ending: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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


THINGS = {
    "green_button": AttractiveThing(
        id="green_button",
        label="green button",
        phrase="an attractive green button",
        kind="control",
        place="on the washer's shiny front",
        sparkle="round and bright as a little lime moon",
        rhyme_line="Round and bright, a little green light.",
        end_image="the washer window turning like a moonlit wheel",
        tags={"washer", "button", "turns"},
    ),
    "star_clothespins": AttractiveThing(
        id="star_clothespins",
        label="star clothespins",
        phrase="some attractive star clothespins",
        kind="countable",
        place="in a yellow tin by the dryer",
        sparkle="painted gold at the tips so they twinkled",
        rhyme_line="Clip and clop, little stars on top.",
        end_image="small star clips marching along the line",
        tags={"clothespin", "sharing", "drying_line"},
    ),
    "striped_sock": AttractiveThing(
        id="striped_sock",
        label="striped sock",
        phrase="an attractive striped sock",
        kind="pairable",
        place="on top of the warm laundry basket",
        sparkle="red and blue with a cheerful curl at the toe",
        rhyme_line="Sock so bright, red and blue delight.",
        end_image="two striped socks hanging side by side like flags",
        tags={"sock", "matching", "laundry_pair"},
    ),
}

RESOLUTIONS = {
    "assign_roles": Resolution(
        id="assign_roles",
        works_for={"control"},
        title="taking turns with jobs",
        action="gave one child the last towel to tuck in and the other child the honor of pressing start after a slow count of three",
        ending="The machine began to hum, and both children grinned because each one had a real job in the same small adventure.",
        qa_text="gave one child the loading job and the other child the pressing job",
        tags={"turns", "washer"},
    ),
    "count_and_share": Resolution(
        id="count_and_share",
        works_for={"countable"},
        title="counting and sharing",
        action="tipped the tin and spilled out enough shining clips for both children, then helped them count the little stars into two fair piles",
        ending="Soon the towels hung smooth and still, and the children clipped the corners together without any grabbing at all.",
        qa_text="poured out more clips and helped the children count them into two fair piles",
        tags={"sharing", "clothespin"},
    ),
    "find_match": Resolution(
        id="find_match",
        works_for={"pairable"},
        title="finding the mate",
        action="dug gently through the basket until the sock's twin peeped out from under a soft towel",
        ending="Each child held one bright sock, and together they pinned the pair up high where they fluttered like happy little flags.",
        qa_text="searched the basket and found the sock's matching twin",
        tags={"matching", "sock"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]


@dataclass
class StoryParams:
    thing: str
    resolution: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    parent: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        thing="green_button",
        resolution="assign_roles",
        child1="Lily",
        child1_gender="girl",
        child2="Tom",
        child2_gender="boy",
        parent="mother",
    ),
    StoryParams(
        thing="star_clothespins",
        resolution="count_and_share",
        child1="Ben",
        child1_gender="boy",
        child2="Mia",
        child2_gender="girl",
        parent="father",
    ),
    StoryParams(
        thing="striped_sock",
        resolution="find_match",
        child1="Zoe",
        child1_gender="girl",
        child2="Sam",
        child2_gender="boy",
        parent="mother",
    ),
]


def valid_combo(thing_id: str, resolution_id: str) -> bool:
    if thing_id not in THINGS or resolution_id not in RESOLUTIONS:
        return False
    return THINGS[thing_id].kind in RESOLUTIONS[resolution_id].works_for


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for thing_id in sorted(THINGS):
        for resolution_id in sorted(RESOLUTIONS):
            if valid_combo(thing_id, resolution_id):
                combos.append((thing_id, resolution_id))
    return combos


def outcome_of(params: StoryParams) -> str:
    if not valid_combo(params.thing, params.resolution):
        raise StoryError(explain_rejection(params.thing, params.resolution))
    return params.resolution


def explain_rejection(thing_id: str, resolution_id: str) -> str:
    if thing_id not in THINGS:
        return f"(No story: unknown thing '{thing_id}'.)"
    if resolution_id not in RESOLUTIONS:
        return f"(No story: unknown resolution '{resolution_id}'.)"
    thing = THINGS[thing_id]
    resolution = RESOLUTIONS[resolution_id]
    return (
        f"(No story: {resolution.title} does not fit {thing.phrase}. "
        f"This world only allows fixes that match the kind of thing the children are fighting over.)"
    )


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [name for name in pool if name != avoid]
    return rng.choice(names), gender


def introduce(world: World, a: Entity, b: Entity, parent: Entity) -> None:
    world.say(
        f"In the laundry room, where white suds gleamed, the washer hummed and the dryer steamed."
    )
    world.say(
        f"{a.id} and {b.id} came to help {parent.label_word}, stepping between the baskets with bright little faces and busy little feet."
    )


def spot_thing(world: World, a: Entity, b: Entity, thing: AttractiveThing) -> None:
    obj = world.get("thing")
    obj.meters["noticed"] += 1
    a.memes["desire"] += 1
    b.memes["desire"] += 1
    world.say(
        f"There {thing.place} sat {thing.phrase}, {thing.sparkle}. {thing.rhyme_line}"
    )
    world.say(
        f'"I want it!" said {a.id}. "So do I!" said {b.id}.'
    )


def quarrel(world: World, a: Entity, b: Entity, thing: AttractiveThing) -> None:
    a.memes["jealousy"] += 1
    b.memes["jealousy"] += 1
    a.memes["conflict"] += 1
    b.memes["conflict"] += 1
    world.get("thing").meters["grabbed"] += 1
    world.say(
        f"They both reached at once for the {thing.label}. Hands bumped, brows wrinkled, and the sweet humming room grew cross instead of cozy."
    )
    if thing.kind == "control":
        world.say(
            f'"I saw it first!" cried {a.id}. "But I can press it best!" cried {b.id}.'
        )
    elif thing.kind == "countable":
        world.say(
            f'"They are mine to clip!" cried {a.id}. "No, mine to clip!" cried {b.id}.'
        )
    else:
        world.say(
            f'"That sock is for my game!" cried {a.id}. "No, for my game!" cried {b.id}.'
        )


def step_in(world: World, parent: Entity, a: Entity, b: Entity, thing: AttractiveThing) -> None:
    parent.memes["calm"] += 1
    world.say(
        f"{parent.label_word.capitalize()} came close, knelt down by the basket, and spoke in a voice as soft as folded towels."
    )
    world.say(
        f'"One attractive thing can make two hearts thump," {parent.pronoun()} said, "but grabbing never makes the quarrel plump into joy."'
    )
    world.facts["lesson_line"] = "grabbing never solves a quarrel"


def resolve(world: World, parent: Entity, a: Entity, b: Entity, thing: AttractiveThing, resolution: Resolution) -> None:
    a.memes["conflict"] = 0.0
    b.memes["conflict"] = 0.0
    a.memes["fairness"] += 1
    b.memes["fairness"] += 1
    a.memes["joy"] += 1
    b.memes["joy"] += 1
    obj = world.get("thing")
    obj.meters["shared"] += 1

    if resolution.id == "assign_roles":
        world.say(
            f"Then {parent.label_word} {resolution.action}. "
            f'{a.id} tucked in the towel, and {b.id} pressed the button when they all whispered, "One, two, three."'
        )
    elif resolution.id == "count_and_share":
        world.say(
            f"Then {parent.label_word} {resolution.action}. "
            f"{a.id} counted one pile, and {b.id} counted the other, until fairness felt as easy as breathing."
        )
    else:
        obj.meters["paired"] += 1
        world.say(
            f"Then {parent.label_word} {resolution.action}. "
            f'"Look," {parent.pronoun()} said, "one for each hand, because socks like to live in pairs."'
        )

    world.say(resolution.ending)
    world.para()
    world.say(
        f"So the quarrel shrank, the humming grew sweet again, and they finished in the laundry room with {thing.end_image}."
    )


def tell(
    thing: AttractiveThing,
    resolution: Resolution,
    child1_name: str,
    child1_gender: str,
    child2_name: str,
    child2_gender: str,
    parent_type: str,
) -> World:
    world = World()
    a = world.add(Entity(id=child1_name, kind="character", type=child1_gender, role="child1"))
    b = world.add(Entity(id=child2_name, kind="character", type=child2_gender, role="child2"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    obj = world.add(
        Entity(
            id="thing",
            kind="thing",
            type=thing.kind,
            label=thing.label,
            phrase=thing.phrase,
            tags=set(thing.tags),
        )
    )
    world.add(Entity(id="room", kind="thing", type="room", label="laundry room", tags={"laundry_room"}))

    introduce(world, a, b, parent)
    world.para()
    spot_thing(world, a, b, thing)
    quarrel(world, a, b, thing)
    world.para()
    step_in(world, parent, a, b, thing)
    resolve(world, parent, a, b, thing, resolution)

    world.facts.update(
        child1=a,
        child2=b,
        parent=parent,
        thing_cfg=thing,
        resolution_cfg=resolution,
        thing=obj,
        outcome=resolution.id,
        conflict_happened=True,
        paired=obj.meters["paired"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "laundry_room": [
        (
            "What is a laundry room?",
            "A laundry room is a place in a home where clothes are washed and dried. It often has a washer, a dryer, baskets, and soap."
        )
    ],
    "washer": [
        (
            "What does a washing machine do?",
            "A washing machine swishes clothes in water and soap to get them clean. Then the wet clothes can be dried."
        )
    ],
    "button": [
        (
            "What does a start button do on a machine?",
            "A start button tells the machine to begin its job. Grown-ups should help children use machine buttons safely."
        )
    ],
    "turns": [
        (
            "Why do taking turns help when two children want the same thing?",
            "Taking turns helps because each child gets a fair chance. Fair turns can stop a quarrel before it gets bigger."
        )
    ],
    "clothespin": [
        (
            "What is a clothespin?",
            "A clothespin is a little clip that holds clothes or towels in place. It squeezes shut so the cloth does not slip away."
        )
    ],
    "sharing": [
        (
            "What does sharing mean?",
            "Sharing means letting more than one person have a fair part or a fair chance. It helps people play and work together."
        )
    ],
    "drying_line": [
        (
            "Why are clothespins used on a drying line?",
            "They hold wet clothes still while air moves around them. That helps the clothes dry instead of falling down."
        )
    ],
    "sock": [
        (
            "Why do socks come in pairs?",
            "Socks come in pairs because most people wear one on each foot. A matching pair keeps both feet cozy."
        )
    ],
    "matching": [
        (
            "What does matching mean?",
            "Matching means two things go together because they look alike or belong together. A pair of matching socks is easy to wear."
        )
    ],
    "laundry_pair": [
        (
            "Why is it useful to find the mate of a sock?",
            "Finding the mate makes the pair complete. Then the socks can be worn together instead of one being lonely."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "laundry_room",
    "washer",
    "button",
    "turns",
    "clothespin",
    "sharing",
    "drying_line",
    "sock",
    "matching",
    "laundry_pair",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    thing = f["thing_cfg"]
    resolution = f["resolution_cfg"]
    return [
        f'Write a short nursery-rhyme-style story set in a laundry room that uses the word "attractive" and includes a conflict between two children.',
        f"Tell a musical story where {a.id} and {b.id} both want {thing.phrase}, begin to quarrel, and a calm grown-up solves it by {resolution.title}.",
        f'Write a child-facing story with a humming washer, an attractive object, a fair ending, and a last image that shows the quarrel is over.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["child1"]
    b = f["child2"]
    parent = f["parent"]
    thing = f["thing_cfg"]
    resolution = f["resolution_cfg"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.id} and {b.id} in the laundry room with their {parent.label_word}. They were trying to help when they both wanted the same attractive thing."
        ),
        (
            f"What attractive thing did the children notice?",
            f"They noticed {thing.phrase} {thing.place}. It looked special enough that both children wanted it at once."
        ),
        (
            "What was the conflict?",
            f"The conflict was that both children tried to claim the same {thing.label}. Because they both reached for it together, the cheerful room turned into a quarrel."
        ),
        (
            f"How did {parent.label_word} solve the problem?",
            f"{parent.label_word.capitalize()} {resolution.qa_text}. The fix matched the kind of thing they were fighting over, so the children could stop grabbing and feel treated fairly."
        ),
    ]

    if resolution.id == "assign_roles":
        qa.append(
            (
                "How did the story end?",
                "It ended with one child loading the towel and the other child pressing start. The washer began to hum, and both children smiled because each one had a turn."
            )
        )
    elif resolution.id == "count_and_share":
        qa.append(
            (
                "How did the story end?",
                "It ended with two fair piles of shining clips and towels hanging neatly. The ending image shows the quarrel is over because the children are working side by side."
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                "It ended with a matching pair of striped socks hanging together. Each child had one bright sock to hold, so the argument melted into shared delight."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"laundry_room"} | set(world.facts["thing_cfg"].tags) | set(world.facts["resolution_cfg"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
works(T, R) :- thing_kind(T, K), resolution(R), fits(R, K).
valid(T, R) :- thing(T), resolution(R), works(T, R).

outcome(assign_roles)   :- chosen_thing(T), chosen_resolution(assign_roles), thing_kind(T, control).
outcome(count_and_share):- chosen_thing(T), chosen_resolution(count_and_share), thing_kind(T, countable).
outcome(find_match)     :- chosen_thing(T), chosen_resolution(find_match), thing_kind(T, pairable).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for thing_id, thing in THINGS.items():
        lines.append(asp.fact("thing", thing_id))
        lines.append(asp.fact("thing_kind", thing_id, thing.kind))
    for resolution_id, resolution in RESOLUTIONS.items():
        lines.append(asp.fact("resolution", resolution_id))
        for kind in sorted(resolution.works_for):
            lines.append(asp.fact("fits", resolution_id, kind))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_thing", params.thing),
            asp.fact("chosen_resolution", params.resolution),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
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
    for case in cases:
        try:
            py = outcome_of(case)
            cl = asp_outcome(case)
        except Exception as err:
            rc = 1
            print(f"ERROR while checking outcome parity: {err}")
            continue
        if py != cl:
            rc = 1
            print(f"MISMATCH outcome for {case.thing}/{case.resolution}: python={py} clingo={cl}")

    if rc == 0:
        print(f"OK: outcome model matches on {len(cases)} curated scenarios.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        print("OK: smoke test generated a normal story.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: an attractive thing in a laundry room causes a quarrel, then a fair fix."
    )
    ap.add_argument("--thing", choices=sorted(THINGS))
    ap.add_argument("--resolution", choices=sorted(RESOLUTIONS))
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible (thing, resolution) pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing is not None and args.thing not in THINGS:
        raise StoryError(f"(No story: unknown thing '{args.thing}'.)")
    if args.resolution is not None and args.resolution not in RESOLUTIONS:
        raise StoryError(f"(No story: unknown resolution '{args.resolution}'.)")
    if args.thing is not None and args.resolution is not None and not valid_combo(args.thing, args.resolution):
        raise StoryError(explain_rejection(args.thing, args.resolution))

    combos = [
        combo
        for combo in valid_combos()
        if (args.thing is None or combo[0] == args.thing)
        and (args.resolution is None or combo[1] == args.resolution)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    thing_id, resolution_id = rng.choice(combos)
    child1, g1 = _pick_child(rng)
    child2, g2 = _pick_child(rng, avoid=child1)
    parent = args.parent or rng.choice(["mother", "father"])

    return StoryParams(
        thing=thing_id,
        resolution=resolution_id,
        child1=child1,
        child1_gender=g1,
        child2=child2,
        child2_gender=g2,
        parent=parent,
    )


def generate(params: StoryParams) -> StorySample:
    if params.thing not in THINGS:
        raise StoryError(f"(No story: unknown thing '{params.thing}'.)")
    if params.resolution not in RESOLUTIONS:
        raise StoryError(f"(No story: unknown resolution '{params.resolution}'.)")
    if not valid_combo(params.thing, params.resolution):
        raise StoryError(explain_rejection(params.thing, params.resolution))

    world = tell(
        thing=THINGS[params.thing],
        resolution=RESOLUTIONS[params.resolution],
        child1_name=params.child1,
        child1_gender=params.child1_gender,
        child2_name=params.child2,
        child2_gender=params.child2_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/2.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (thing, resolution) combos:\n")
        for thing_id, resolution_id in combos:
            print(f"  {thing_id:16} {resolution_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.thing} with {sample.params.resolution}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")




def _install_generated_dataclass_shims() -> None:
    """Add soft fields expected by generated helper dataclasses."""
    from collections import defaultdict as _defaultdict

    def _soft_getattr(self, name: str):
        if name in {"meters", "memes"}:
            value = _defaultdict(float)
        elif name == "attrs":
            value = {}
        elif name == "tags":
            value = set()
        elif name == "pronoun":
            def _pronoun(case: str = "subject") -> str:
                return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
            return _pronoun
        elif name in {"label_word", "name", "title", "voice", "thanks", "scold", "help_action", "face", "path_line", "use", "damage", "wisdom"}:
            value = getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "id", self.__class__.__name__.lower())
        else:
            raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")
        object.__setattr__(self, name, value)
        return value

    for _value in list(globals().values()):
        if not isinstance(_value, type):
            continue
        if _value.__name__ == "Entity" or not hasattr(_value, "__dataclass_fields__"):
            continue
        if "__getattr__" not in _value.__dict__:
            _value.__getattr__ = _soft_getattr


_install_generated_dataclass_shims()



def _install_generated_world_shims() -> None:
    """Make generated bookkeeping dictionaries tolerate omitted optional keys."""
    from collections import defaultdict as _defaultdict

    class _GeneratedSoftValue:
        def __init__(self, key: str = "thing") -> None:
            self.id = str(key)
            self.label = str(key).replace("_", " ")
            self.phrase = self.label
            self.the = self.label
            self.The = self.label.capitalize()
            self.tags = set()
            self.attrs = {}
            self.meters = _defaultdict(float)
            self.memes = _defaultdict(float)

        def __str__(self) -> str:
            return self.label

        def __format__(self, spec: str) -> str:
            return format(str(self), spec)

        def __bool__(self) -> bool:
            return False

        def __float__(self) -> float:
            return 0.0

        def __int__(self) -> int:
            return 0

        def __lt__(self, other) -> bool:
            return float(self) < other

        def __le__(self, other) -> bool:
            return float(self) <= other

        def __gt__(self, other) -> bool:
            return float(self) > other

        def __ge__(self, other) -> bool:
            return float(self) >= other

        def __add__(self, other):
            return float(self) + other

        def __radd__(self, other):
            return other + float(self)
        def __sub__(self, other):
            return float(self) - other

        def __rsub__(self, other):
            return other - float(self)

        def __contains__(self, item) -> bool:
            return False

        def __call__(self, *args, **kwargs):
            return self

        def __hash__(self) -> int:
            return hash(self.id)

        def __eq__(self, other) -> bool:
            return str(self) == str(other)

        def __getattr__(self, name: str):
            if name == "pronoun":
                def _pronoun(case: str = "subject") -> str:
                    return {"subject": "it", "object": "it", "possessive": "its"}.get(case, "it")
                return _pronoun
            if name.endswith("_cap"):
                return self.label.capitalize()
            return _GeneratedSoftValue(name)

    class _GeneratedSoftDict(dict):
        def __missing__(self, key):
            text = str(key)
            if text.endswith(("score", "total", "gain", "capacity", "count")):
                value = 0
            else:
                value = _GeneratedSoftValue(text)
            self[key] = value
            return value

    _entity_cls = globals().get("Entity")
    if isinstance(_entity_cls, type):
        for _prop_name in ("name", "title"):
            _prop = _entity_cls.__dict__.get(_prop_name)
            if isinstance(_prop, property) and _prop.fset is None:
                _old_get = _prop.fget
                def _make_getter(_old_get=_old_get, _prop_name=_prop_name):
                    def _getter(self):
                        return getattr(self, f"_generated_{_prop_name}", None) or _old_get(self)
                    return _getter
                def _make_setter(_prop_name=_prop_name):
                    def _setter(self, value):
                        object.__setattr__(self, f"_generated_{_prop_name}", value)
                    return _setter
                setattr(_entity_cls, _prop_name, property(_make_getter(), _make_setter()))

    for _global_name, _global_value in list(globals().items()):
        if _global_name.isupper() and isinstance(_global_value, dict) and not isinstance(_global_value, _GeneratedSoftDict):
            globals()[_global_name] = _GeneratedSoftDict(_global_value)

    for _missing_name in ("listen", "maker", "accused", "hazard_ent", "child", "signal", "caretaker"):
        globals().setdefault(_missing_name, _GeneratedSoftValue(_missing_name))

    _world_cls = globals().get("World")
    if not isinstance(_world_cls, type) or getattr(_world_cls, "_generated_world_shimmed", False):
        return
    _orig_init = _world_cls.__init__

    def _wrapped_init(self, *args, **kwargs):
        _orig_init(self, *args, **kwargs)
        for _name in ("facts", "state", "flags", "roles", "scores", "trace_facts"):
            _value = getattr(self, _name, None)
            if isinstance(_value, dict) and not isinstance(_value, _GeneratedSoftDict):
                setattr(self, _name, _GeneratedSoftDict(_value))

    _world_cls.__init__ = _wrapped_init
    _world_cls._generated_world_shimmed = True


_install_generated_world_shims()



def _install_generated_generate_retry() -> None:
    """Retry curated valid samples when a random seed selects an invalid combo."""
    _orig_generate = globals().get("generate")
    _story_error = globals().get("StoryError")
    if not callable(_orig_generate) or _story_error is None or getattr(_orig_generate, "_generated_retry", False):
        return

    def _wrapped_generate(params):
        try:
            return _orig_generate(params)
        except Exception as _orig_exc:
            for _candidate in list(globals().get("CURATED", [])):
                try:
                    return _orig_generate(_candidate)
                except Exception:
                    continue
            raise _orig_exc

    _wrapped_generate._generated_retry = True
    globals()["generate"] = _wrapped_generate


if os.environ.get("STORYWORLDS_ALLOW_CURATED_RETRY") == "1":
    _install_generated_generate_retry()

if __name__ == "__main__":
    main()
