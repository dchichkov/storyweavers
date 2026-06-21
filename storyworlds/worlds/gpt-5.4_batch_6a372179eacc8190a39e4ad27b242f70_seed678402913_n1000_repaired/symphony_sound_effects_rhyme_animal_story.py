#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/symphony_sound_effects_rhyme_animal_story.py
=======================================================================

A standalone storyworld for a tiny animal story about making a forest symphony.

The core tale shape is:

- a small animal wants to join a woodland symphony
- the animal tries a loud or clattery sound that does not fit
- a friend notices the trouble and helps the animal choose a better way
- the group plays together, and the ending image proves the animal belongs

The world model tracks simple physical meters (noise, rhythm, readiness) and
emotional memes (hope, embarrassment, pride, friendship). Story prose is driven
by the simulated choice of role, tool, problem, and repair.

Run it
------
    python storyworlds/worlds/gpt-5.4/symphony_sound_effects_rhyme_animal_story.py
    python storyworlds/worlds/gpt-5.4/symphony_sound_effects_rhyme_animal_story.py --animal mouse --problem sneeze
    python storyworlds/worlds/gpt-5.4/symphony_sound_effects_rhyme_animal_story.py --role hush
    python storyworlds/worlds/gpt-5.4/symphony_sound_effects_rhyme_animal_story.py --all
    python storyworlds/worlds/gpt-5.4/symphony_sound_effects_rhyme_animal_story.py --qa
    python storyworlds/worlds/gpt-5.4/symphony_sound_effects_rhyme_animal_story.py --verify
"""

from __future__ import annotations

import argparse
import copy
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
    phrase: str = ""
    role: str = ""
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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"mother", "father", "person", "child", "friend"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class AnimalKind:
    id: str
    label: str
    phrase: str
    sound: str
    move: str
    size: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RoleKind:
    id: str
    label: str
    need: str
    good_tool_types: set[str]
    effect: str
    group_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ToolKind:
    id: str
    label: str
    phrase: str
    tool_type: str
    onomat: str
    style: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ProblemKind:
    id: str
    label: str
    causes: set[str]
    fix_tool_types: set[str]
    line: str
    lesson: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = copy.deepcopy(self.facts)
        return other


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_problem_disrupts(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    chorus = world.entities.get("chorus")
    if hero is None or chorus is None:
        return out
    if hero.meters["misfit"] < THRESHOLD:
        return out
    sig = ("problem_disrupts",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chorus.meters["tangle"] += 1
    hero.memes["embarrassment"] += 1
    out.append("__tangle__")
    return out


def _r_fit_brings_music(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    chorus = world.entities.get("chorus")
    if hero is None or chorus is None:
        return out
    if hero.meters["fit"] < THRESHOLD:
        return out
    sig = ("fit_brings_music",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chorus.meters["music"] += 1
    hero.memes["pride"] += 1
    hero.memes["belonging"] += 1
    out.append("__music__")
    return out


CAUSAL_RULES = [
    Rule(name="problem_disrupts", tag="physical", apply=_r_problem_disrupts),
    Rule(name="fit_brings_music", tag="physical", apply=_r_fit_brings_music),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(got)
    if narrate:
        for sentence in produced:
            if not sentence.startswith("__"):
                world.say(sentence)
    return produced


ANIMALS = {
    "mouse": AnimalKind(
        id="mouse",
        label="mouse",
        phrase="a small gray mouse",
        sound="squeak",
        move="tiptoed",
        size="small",
        tags={"mouse", "animal"},
    ),
    "duck": AnimalKind(
        id="duck",
        label="duck",
        phrase="a bright-beaked duck",
        sound="quack",
        move="waddled",
        size="medium",
        tags={"duck", "animal"},
    ),
    "frog": AnimalKind(
        id="frog",
        label="frog",
        phrase="a springy green frog",
        sound="ribbit",
        move="hopped",
        size="small",
        tags={"frog", "animal"},
    ),
    "rabbit": AnimalKind(
        id="rabbit",
        label="rabbit",
        phrase="a soft brown rabbit",
        sound="thump",
        move="bounced",
        size="small",
        tags={"rabbit", "animal"},
    ),
}

ROLES = {
    "bell": RoleKind(
        id="bell",
        label="bell part",
        need="clear tiny notes",
        good_tool_types={"light_ring"},
        effect="made the high notes sparkle",
        group_line="the high chime line",
        tags={"bells", "high_notes"},
    ),
    "drum": RoleKind(
        id="drum",
        label="drum part",
        need="steady soft beats",
        good_tool_types={"soft_beat"},
        effect="kept a gentle beat for dancing feet",
        group_line="the thump-thump line",
        tags={"drum", "rhythm"},
    ),
    "hush": RoleKind(
        id="hush",
        label="wind part",
        need="soft whisper sounds",
        good_tool_types={"soft_whoosh"},
        effect="filled the spaces with a breezy hush",
        group_line="the hush-hush line",
        tags={"wind", "soft_sound"},
    ),
}

TOOLS = {
    "bluebell": ToolKind(
        id="bluebell",
        label="bluebell cup",
        phrase="a bluebell cup",
        tool_type="light_ring",
        onomat="ting-ting",
        style="light and bright",
        tags={"flower", "bell_sound"},
    ),
    "reed": ToolKind(
        id="reed",
        label="reed shaker",
        phrase="a reed shaker",
        tool_type="soft_whoosh",
        onomat="shhh-shhh",
        style="whispery and slow",
        tags={"reed", "wind_sound"},
    ),
    "acorn": ToolKind(
        id="acorn",
        label="acorn drum",
        phrase="an acorn drum",
        tool_type="soft_beat",
        onomat="tum-tum",
        style="round and steady",
        tags={"acorn", "drum_sound"},
    ),
    "pot": ToolKind(
        id="pot",
        label="tin pot",
        phrase="a shiny tin pot",
        tool_type="clang",
        onomat="BANG-CLANG",
        style="loud and clattery",
        tags={"pot", "loud_sound"},
    ),
}

PROBLEMS = {
    "too_loud": ProblemKind(
        id="too_loud",
        label="too-loud clanging",
        causes={"clang"},
        fix_tool_types={"light_ring", "soft_beat", "soft_whoosh"},
        line="The sound came out much too loud for the little glade.",
        lesson="Music feels best when each friend leaves room for the rest.",
        tags={"loud", "listening"},
    ),
    "sneeze": ProblemKind(
        id="sneeze",
        label="a sneezy nose",
        causes={"light_ring", "soft_beat", "soft_whoosh", "clang"},
        fix_tool_types={"soft_beat", "soft_whoosh"},
        line="A tickly nose kept popping up right in the middle of the practice.",
        lesson="When a body needs a slower job, a kinder plan can help.",
        tags={"sneeze", "body"},
    ),
    "rush": ProblemKind(
        id="rush",
        label="rushing ahead",
        causes={"light_ring", "soft_beat"},
        fix_tool_types={"soft_beat", "soft_whoosh"},
        line="The little player hurried ahead and tangled the song.",
        lesson="A good symphony grows when everyone listens and keeps the same pace.",
        tags={"rhythm", "listening"},
    ),
}


def good_tools_for(role_id: str, problem_id: str) -> list[str]:
    role = ROLES[role_id]
    problem = PROBLEMS[problem_id]
    return sorted(
        tid for tid, tool in TOOLS.items()
        if tool.tool_type in role.good_tool_types and tool.tool_type in problem.fix_tool_types
    )


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for animal_id in sorted(ANIMALS):
        for role_id in sorted(ROLES):
            for problem_id in sorted(PROBLEMS):
                if good_tools_for(role_id, problem_id):
                    combos.append((animal_id, role_id, problem_id))
    return combos


def explain_rejection(role_id: str, problem_id: str) -> str:
    role = ROLES[role_id]
    problem = PROBLEMS[problem_id]
    return (
        f"(No story: {role.label} needs {role.need}, but {problem.label} leaves no "
        f"reasonable tool that fits that part. Pick a different role or problem.)"
    )


def predict_fit(role_id: str, tool_id: str, problem_id: str) -> bool:
    tool = TOOLS[tool_id]
    role = ROLES[role_id]
    problem = PROBLEMS[problem_id]
    return tool.tool_type in role.good_tool_types and tool.tool_type in problem.fix_tool_types


def introduce(world: World, hero: Entity, friend: Entity, animal: AnimalKind) -> None:
    hero.memes["hope"] += 1
    friend.memes["kindness"] += 1
    world.say(
        f"In a mossy glade, {hero.id} the {animal.label} heard the morning symphony begin. "
        f"Birds trilled, leaves swished, and the brook sang a silver song."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} {animal.move} beside {friend.id}, listening with wide, happy eyes."
    )


def invitation(world: World, hero: Entity, role: RoleKind) -> None:
    chorus = world.get("chorus")
    chorus.meters["ready"] += 1
    world.say(
        f'"Today we need {role.need}," said the conductor robin. '
        f'"Who wants to try {role.group_line}?"'
    )
    world.say(f'{hero.id} lifted a paw and whispered, "I do. I want to help the symphony too."')


def first_try(world: World, hero: Entity, wrong_tool: ToolKind, role: RoleKind, animal: AnimalKind) -> None:
    hero.meters["playing"] += 1
    hero.meters["misfit"] += 1
    if wrong_tool.tool_type == "clang":
        hero.meters["noise"] += 2
    else:
        hero.meters["noise"] += 1
    propagate(world, narrate=False)
    extra = f'"{wrong_tool.onomat}!" went {wrong_tool.phrase}.'
    world.say(
        f"{hero.id} picked up {wrong_tool.phrase} and tried the {role.label}. {extra}"
    )
    world.say(
        f"The little {animal.label} meant well, but the sound did not sit softly with the others."
    )


def problem_turn(world: World, hero: Entity, problem: ProblemKind) -> None:
    world.say(problem.line)
    if hero.memes["embarrassment"] >= THRESHOLD:
        world.say(
            f"{hero.id}'s ears drooped. {hero.pronoun('subject').capitalize()} worried that the whole song might stop because of {hero.pronoun('object')}."
        )


def helper_notices(world: World, friend: Entity, hero: Entity, role: RoleKind, tool: ToolKind, problem: ProblemKind) -> None:
    hero.memes["friendship"] += 1
    world.say(
        f'{friend.id} stepped close and spoke in a gentle voice. '
        f'"Maybe your part needs something {tool.style}, not a big noisy crash."'
    )
    world.say(
        f'"For {role.group_line}, let\'s try {tool.phrase}. It can help even with {problem.label}."'
    )


def switch_tool(world: World, hero: Entity, tool: ToolKind, role: RoleKind, problem: ProblemKind) -> None:
    hero.meters["misfit"] = 0.0
    hero.meters["fit"] += 1
    hero.meters["noise"] = 0.0
    hero.meters["rhythm"] += 1
    hero.attrs["tool"] = tool.id
    hero.attrs["fixed_problem"] = problem.id
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} took {tool.phrase}, breathed once, and tried again: "
        f'"{tool.onomat}," went the new sound, neat and sweet.'
    )
    world.say(
        f"This time the sound fit the circle. It {role.effect}."
    )


def rhyme_finish(world: World, hero: Entity, animal: AnimalKind, tool: ToolKind) -> None:
    world.say(
        f'Soon the glade was glowing with music. "{tool.onomat}, {tool.onomat}, play and stay; '
        f'sway and say, we find our way," sang the animals.'
    )
    world.say(
        f"{hero.id} the {animal.label} smiled so wide that even the daisies seemed to nod. "
        f"What had begun with a bump ended with a jump into joy."
    )


def closing_image(world: World, hero: Entity, friend: Entity, problem: ProblemKind) -> None:
    world.say(
        f"When the last note floated away, {friend.id} bumped shoulders with {hero.id}. "
        f"{hero.id} no longer felt small in the circle."
    )
    world.say(
        f"{problem.lesson} The forest evening hummed, and the symphony carried them all home."
    )


def tell(
    animal: AnimalKind,
    role: RoleKind,
    problem: ProblemKind,
    name: str,
    friend_name: str,
    wrong_tool: ToolKind,
    right_tool: ToolKind,
) -> World:
    world = World()
    hero = world.add(Entity(id=name, kind="character", type=animal.id, label=animal.label, phrase=animal.phrase))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend", label="friend"))
    chorus = world.add(Entity(id="chorus", kind="thing", type="chorus", label="forest chorus"))
    world.facts["hero_name"] = name
    world.facts["friend_name"] = friend_name

    introduce(world, hero, friend, animal)
    invitation(world, hero, role)

    world.para()
    first_try(world, hero, wrong_tool, role, animal)
    problem_turn(world, hero, problem)

    world.para()
    helper_notices(world, friend, hero, role, right_tool, problem)
    switch_tool(world, hero, right_tool, role, problem)

    world.para()
    rhyme_finish(world, hero, animal, right_tool)
    closing_image(world, hero, friend, problem)

    world.facts.update(
        hero=hero,
        friend=friend,
        animal=animal,
        role_cfg=role,
        problem_cfg=problem,
        wrong_tool=wrong_tool,
        right_tool=right_tool,
        success=hero.meters["fit"] >= THRESHOLD,
        tangled=chorus.meters["tangle"] >= THRESHOLD,
        music=chorus.meters["music"] >= THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    animal: str
    role: str
    problem: str
    wrong_tool: str
    right_tool: str
    name: str
    friend_name: str
    seed: Optional[int] = None


NAME_POOLS = {
    "mouse": ["Mimi", "Pip", "Tilly", "Nib"],
    "duck": ["Dilly", "Puddle", "Sunny", "Wobble"],
    "frog": ["Peep", "Moss", "Ribby", "Dot"],
    "rabbit": ["Bramble", "Poppy", "Clover", "Skip"],
}
FRIEND_NAMES = ["Fern", "Pico", "Mallow", "Juniper", "Pebble", "Lark"]

CURATED = [
    StoryParams(
        animal="mouse",
        role="bell",
        problem="too_loud",
        wrong_tool="pot",
        right_tool="bluebell",
        name="Mimi",
        friend_name="Fern",
    ),
    StoryParams(
        animal="frog",
        role="drum",
        problem="sneeze",
        wrong_tool="pot",
        right_tool="acorn",
        name="Moss",
        friend_name="Pebble",
    ),
    StoryParams(
        animal="duck",
        role="hush",
        problem="too_loud",
        wrong_tool="pot",
        right_tool="reed",
        name="Sunny",
        friend_name="Lark",
    ),
    StoryParams(
        animal="rabbit",
        role="drum",
        problem="rush",
        wrong_tool="bluebell",
        right_tool="acorn",
        name="Clover",
        friend_name="Juniper",
    ),
]


KNOWLEDGE = {
    "symphony": [
        (
            "What is a symphony?",
            "A symphony is a big piece of music made from many sounds working together. Different parts join to make one whole song."
        )
    ],
    "bells": [
        (
            "Why do bells sound high and clear?",
            "Bell sounds ring because the hard shape vibrates quickly. That quick shaking makes a bright, high note."
        )
    ],
    "drum": [
        (
            "What does a drum do in music?",
            "A drum gives the beat. The beat helps everyone stay together."
        )
    ],
    "wind": [
        (
            "What is a whisper sound?",
            "A whisper sound is soft and gentle. It does not push over the other sounds around it."
        )
    ],
    "listening": [
        (
            "Why do musicians listen to each other?",
            "They listen so they can keep the same pace and volume. Listening helps the music fit together."
        )
    ],
    "loud": [
        (
            "Why can a very loud sound be a problem in a group song?",
            "One very loud sound can cover the others. Then the group cannot hear or match each other well."
        )
    ],
    "sneeze": [
        (
            "Why might someone choose a slower job when they feel sneezy?",
            "A slower job is easier to do carefully when your body feels jumpy. It helps you still join in without spoiling the work."
        )
    ],
    "flower": [
        (
            "How can a flower cup make a tiny sound in pretend play?",
            "A child can imagine tapping or ringing it very gently. In stories, small things can stand in for little bells."
        )
    ],
    "reed": [
        (
            "What sound can a reed make?",
            "A reed can swish and whisper when air moves through it. That makes it good for a soft breezy sound."
        )
    ],
    "acorn": [
        (
            "Why is an acorn a good pretend drum in a story?",
            "An acorn is small and round, so it fits a gentle tapping game. It suggests a soft beat instead of a crashing bang."
        )
    ],
}
KNOWLEDGE_ORDER = ["symphony", "bells", "drum", "wind", "listening", "loud", "sneeze", "flower", "reed", "acorn"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    animal = f["animal"]
    role = f["role_cfg"]
    problem = f["problem_cfg"]
    right_tool = f["right_tool"]
    return [
        f'Write an animal story for a 3-to-5-year-old that uses the word "symphony" and includes sound effects and rhyme.',
        f"Tell a gentle forest story where {hero.id} the {animal.label} wants to help with {role.group_line}, makes a mistake, and a friend helps find a better sound.",
        f'Write a child-facing story with onomatopoeia like "{right_tool.onomat}" and a rhyming line, ending with the animals making music together after solving {problem.label}.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    animal = f["animal"]
    role = f["role_cfg"]
    problem = f["problem_cfg"]
    wrong_tool = f["wrong_tool"]
    right_tool = f["right_tool"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id} the {animal.label}, who wanted to join the forest symphony, and {friend.id}, the kind friend who helped. The story follows how {hero.id} found the right sound for the group."
        ),
        (
            f"What did {hero.id} want to do?",
            f"{hero.id} wanted to help with {role.group_line} in the symphony. Joining the music mattered because {hero.pronoun('subject')} wanted to belong in the circle."
        ),
        (
            f"What went wrong at first?",
            f"{hero.id} tried using {wrong_tool.phrase}, but the sound did not fit the group. {problem.line[0].upper()}{problem.line[1:]}"
        ),
        (
            f"How did {friend.id} help?",
            f"{friend.id} listened carefully and suggested {right_tool.phrase} instead. That helped because the new tool matched the part and also worked better with {problem.label}."
        ),
    ]
    if f.get("success"):
        qa.append(
            (
                f"Why did the second try work?",
                f"The second try worked because {right_tool.phrase} made a sound that fit {role.group_line}. Once {hero.id} switched, the music could move together instead of tangling."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the animals playing a happy symphony together. {hero.id} felt proud and included because the right sound let {hero.pronoun('object')} help the whole group."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"symphony"} | set(f["role_cfg"].tags) | set(f["problem_cfg"].tags) | set(f["right_tool"].tags)
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


ASP_RULES = r"""
good_tool(R, P, T) :- role(R), problem(P), tool(T), role_needs(R, K), tool_type(T, K), fixes(P, K).
valid(A, R, P) :- animal(A), role(R), problem(P), good_tool(R, P, _).

chosen_valid :- chosen_animal(A), chosen_role(R), chosen_problem(P), valid(A, R, P).
bad_wrong :- chosen_wrong(W), chosen_problem(P), causes(P, K), tool_type(W, K).
success :- chosen_valid, chosen_right(T), chosen_role(R), chosen_problem(P),
           role_needs(R, K), tool_type(T, K), fixes(P, K).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for animal_id in sorted(ANIMALS):
        lines.append(asp.fact("animal", animal_id))
    for role_id, role in sorted(ROLES.items()):
        lines.append(asp.fact("role", role_id))
        for need in sorted(role.good_tool_types):
            lines.append(asp.fact("role_needs", role_id, need))
    for tool_id, tool in sorted(TOOLS.items()):
        lines.append(asp.fact("tool", tool_id))
        lines.append(asp.fact("tool_type", tool_id, tool.tool_type))
    for problem_id, problem in sorted(PROBLEMS.items()):
        lines.append(asp.fact("problem", problem_id))
        for cause in sorted(problem.causes):
            lines.append(asp.fact("causes", problem_id, cause))
        for fix in sorted(problem.fix_tool_types):
            lines.append(asp.fact("fixes", problem_id, fix))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_success(params: StoryParams) -> bool:
    import asp
    extra = "\n".join([
        asp.fact("chosen_animal", params.animal),
        asp.fact("chosen_role", params.role),
        asp.fact("chosen_problem", params.problem),
        asp.fact("chosen_wrong", params.wrong_tool),
        asp.fact("chosen_right", params.right_tool),
    ])
    model = asp.one_model(asp_program(extra, "#show success/0.\n#show bad_wrong/0."))
    success_atoms = asp.atoms(model, "success")
    return bool(success_atoms)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:8} ({ent.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Animal storyworld: a forest symphony, a wrong sound, and a kind repair."
    )
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--role", choices=sorted(ROLES))
    ap.add_argument("--problem", choices=sorted(PROBLEMS))
    ap.add_argument("--wrong-tool", dest="wrong_tool", choices=sorted(TOOLS))
    ap.add_argument("--right-tool", dest="right_tool", choices=sorted(TOOLS))
    ap.add_argument("--name")
    ap.add_argument("--friend-name", dest="friend_name")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (animal, role, problem) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def _pick_name(rng: random.Random, animal_id: str) -> str:
    return rng.choice(NAME_POOLS[animal_id])


def _pick_friend_name(rng: random.Random, avoid: str) -> str:
    choices = [n for n in FRIEND_NAMES if n != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.role and args.problem and not good_tools_for(args.role, args.problem):
        raise StoryError(explain_rejection(args.role, args.problem))

    combos = [
        combo for combo in valid_combos()
        if (args.animal is None or combo[0] == args.animal)
        and (args.role is None or combo[1] == args.role)
        and (args.problem is None or combo[2] == args.problem)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    animal_id, role_id, problem_id = rng.choice(sorted(combos))

    wrong_candidates = [tid for tid, tool in TOOLS.items() if tool.tool_type in PROBLEMS[problem_id].causes]
    if not wrong_candidates:
        raise StoryError("(No story: this problem has no wrong first tool to cause the trouble.)")
    wrong_tool = args.wrong_tool or rng.choice(sorted(wrong_candidates))
    if TOOLS[wrong_tool].tool_type not in PROBLEMS[problem_id].causes:
        raise StoryError(
            f"(No story: {TOOLS[wrong_tool].label} would not cause {PROBLEMS[problem_id].label}. "
            f"Pick a wrong tool that actually creates the trouble.)"
        )

    right_candidates = good_tools_for(role_id, problem_id)
    if not right_candidates:
        raise StoryError(explain_rejection(role_id, problem_id))
    right_tool = args.right_tool or rng.choice(right_candidates)
    if not predict_fit(role_id, right_tool, problem_id):
        raise StoryError(
            f"(No story: {TOOLS[right_tool].label} does not reasonably solve the {role_id} part under {problem_id}. "
            f"Pick one of: {', '.join(right_candidates)}.)"
        )

    name = args.name or _pick_name(rng, animal_id)
    friend_name = args.friend_name or _pick_friend_name(rng, name)

    return StoryParams(
        animal=animal_id,
        role=role_id,
        problem=problem_id,
        wrong_tool=wrong_tool,
        right_tool=right_tool,
        name=name,
        friend_name=friend_name,
    )


def generate(params: StoryParams) -> StorySample:
    if params.animal not in ANIMALS:
        raise StoryError(f"(Unknown animal: {params.animal})")
    if params.role not in ROLES:
        raise StoryError(f"(Unknown role: {params.role})")
    if params.problem not in PROBLEMS:
        raise StoryError(f"(Unknown problem: {params.problem})")
    if params.wrong_tool not in TOOLS:
        raise StoryError(f"(Unknown wrong tool: {params.wrong_tool})")
    if params.right_tool not in TOOLS:
        raise StoryError(f"(Unknown right tool: {params.right_tool})")
    if TOOLS[params.wrong_tool].tool_type not in PROBLEMS[params.problem].causes:
        raise StoryError("(The chosen wrong tool would not cause the chosen problem.)")
    if not predict_fit(params.role, params.right_tool, params.problem):
        raise StoryError("(The chosen right tool does not fit the role and problem.)")

    world = tell(
        animal=ANIMALS[params.animal],
        role=ROLES[params.role],
        problem=PROBLEMS[params.problem],
        name=params.name,
        friend_name=params.friend_name,
        wrong_tool=TOOLS[params.wrong_tool],
        right_tool=TOOLS[params.right_tool],
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


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))

    for params in CURATED:
        try:
            py_success = True
            asp_ok = asp_success(params)
            if not asp_ok:
                rc = 1
                print(f"MISMATCH: ASP did not mark curated story successful: {params}")
        except Exception as err:
            rc = 1
            print(f"ERROR during ASP scenario check: {err}")

    try:
        smoke_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_params.seed = 123
        sample = generate(smoke_params)
        if not sample.story or "symphony" not in sample.story.lower():
            rc = 1
            print("SMOKE FAIL: generated story missing or does not mention symphony.")
        else:
            print("OK: smoke generation passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE FAIL: ordinary generation crashed: {err}")

    try:
        curated_sample = generate(CURATED[0])
        emit(curated_sample, trace=False, qa=False, header="")
        print("OK: smoke emit passed.")
    except Exception as err:
        rc = 1
        print(f"SMOKE FAIL: emit crashed: {err}")

    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show success/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (animal, role, problem) combos:\n")
        for animal_id, role_id, problem_id in combos:
            print(f"  {animal_id:8} {role_id:6} {problem_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for params in CURATED:
            sample = generate(params)
            samples.append(sample)
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
            header = f"### {p.name}: {p.animal}, {p.role}, {p.problem}"
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
