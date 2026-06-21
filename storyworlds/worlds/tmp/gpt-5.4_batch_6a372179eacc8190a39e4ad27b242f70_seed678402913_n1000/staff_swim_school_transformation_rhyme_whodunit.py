#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/staff_swim_school_transformation_rhyme_whodunit.py
==============================================================================

A standalone story world for a gentle swim-school whodunit with rhyme and
transformation. A silly mural at swim school can temporarily transform a nearby
staff object when a child splashes it and chants a rhyme. One object changes,
the staff notice watery clues, and a calm coach solves the mystery.

The world model keeps a small typed simulation:
- characters and things share one Entity dataclass
- physical meters track wetness, transformation, clue strength, and safety
- emotional memes track worry, curiosity, honesty, relief, and trust
- the story is rendered from simulated state, not from one frozen template

Reasonableness gate:
- only tools that are actually used in a zone may be chosen there
- a tool must splash strongly enough to trigger the chosen target's magic
- the ASP twin mirrors that compatibility gate

Run it
------
    python storyworlds/worlds/gpt-5.4/staff_swim_school_transformation_rhyme_whodunit.py
    python storyworlds/worlds/gpt-5.4/staff_swim_school_transformation_rhyme_whodunit.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/staff_swim_school_transformation_rhyme_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/staff_swim_school_transformation_rhyme_whodunit.py --qa
    python storyworlds/worlds/gpt-5.4/staff_swim_school_transformation_rhyme_whodunit.py --trace
    python storyworlds/worlds/gpt-5.4/staff_swim_school_transformation_rhyme_whodunit.py --json
    python storyworlds/worlds/gpt-5.4/staff_swim_school_transformation_rhyme_whodunit.py --asp
    python storyworlds/worlds/gpt-5.4/staff_swim_school_transformation_rhyme_whodunit.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "coach_f", "clerk_f"}
        male = {"boy", "man", "father", "coach_m", "clerk_m"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Zone:
    id: str
    label: str
    detail: str
    mural_line: str
    form: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    splash: int
    clue: str
    action: str
    carry_text: str
    rhyme_start: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    label: str
    phrase: str
    owner_role: str
    trigger: int
    changed_name: str
    reverse_rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    zone: str
    tool: str
    target: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    culprit_name: str
    culprit_type: str
    suspect_two_name: str
    suspect_two_type: str
    suspect_three_name: str
    suspect_three_type: str
    seed: Optional[int] = None


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


ZONES = {
    "splash_pool": Zone(
        id="splash_pool",
        label="the splash pool",
        detail="where the water was shallow and bright and the little flags trembled in the warm air",
        mural_line='On the wall beside the lane, a painted mermaid smiled under the words, "Swish and rhyme, but only at game time."',
        form="goldfish",
        affords={"kickboard", "scoop_cup"},
        tags={"pool", "splash"},
    ),
    "kick_lane": Zone(
        id="kick_lane",
        label="the kick lane",
        detail="where children held the wall and practiced fast little kicks",
        mural_line='Beside the lane, blue tiles curled around a rhyme: "Kick with care and sing with cheer; magic answers when drops come near."',
        form="seal",
        affords={"kickboard", "noodle"},
        tags={"pool", "kicking"},
    ),
    "bubble_steps": Zone(
        id="bubble_steps",
        label="the bubble steps",
        detail="where tiny jets made silver bubbles dance around small ankles",
        mural_line='A shining tile fish pointed at a line that read, "Bubble, trouble, giggle, rhyme; ask the staff before splash time."',
        form="turtle",
        affords={"scoop_cup", "noodle"},
        tags={"pool", "bubbles"},
    ),
}

TOOLS = {
    "kickboard": Tool(
        id="kickboard",
        label="kickboard",
        splash=2,
        clue="a fan of straight drops",
        action="slapped the water with a kickboard",
        carry_text="held a bright orange kickboard",
        rhyme_start="Swish, splash, little dash",
        tags={"kickboard", "splash"},
    ),
    "noodle": Tool(
        id="noodle",
        label="pool noodle",
        splash=1,
        clue="a wiggly stripe of water",
        action="flicked a pool noodle through the water",
        carry_text="dragged a bendy purple noodle",
        rhyme_start="Wiggle, giggle, noodle noodle",
        tags={"noodle", "splash"},
    ),
    "scoop_cup": Tool(
        id="scoop_cup",
        label="scoop cup",
        splash=1,
        clue="three neat round drops",
        action="lifted and tipped a scoop cup",
        carry_text="carried a little blue scoop cup",
        rhyme_start="Dip and drip, tiny ship",
        tags={"cup", "splash"},
    ),
}

TARGETS = {
    "whistle": Target(
        id="whistle",
        label="whistle",
        phrase="Coach Mina's silver whistle",
        owner_role="detective",
        trigger=1,
        changed_name="a blinking little fish-whistle with a tail",
        reverse_rhyme='“Silver whistle, stop your play. Be a whistle right away.”',
        tags={"whistle", "staff"},
    ),
    "badge": Target(
        id="badge",
        label="staff badge",
        phrase="the front-desk staff badge",
        owner_role="helper",
        trigger=1,
        changed_name="a tiny shell-shaped badge that winked pearly light",
        reverse_rhyme='“Badge so bright, badge so true, turn back to the shape we knew.”',
        tags={"badge", "staff"},
    ),
    "clipboard": Target(
        id="clipboard",
        label="clipboard",
        phrase="the lesson clipboard",
        owner_role="helper",
        trigger=2,
        changed_name="a stiff green turtle-board with the lesson list tucked under one flipper",
        reverse_rhyme='“Board and clip, be neat once more. Flat and ready, as before.”',
        tags={"clipboard", "staff"},
    ),
}

GIRL_NAMES = ["Lina", "Ruby", "Nia", "Tess", "Molly", "Poppy", "June", "Ivy"]
BOY_NAMES = ["Eli", "Milo", "Owen", "Ben", "Theo", "Finn", "Kai", "Jude"]
DETECTIVE_NAMES = ["Mina", "Tara", "Nora", "Leah", "Omar", "Rafi", "Ben", "Joel"]
HELPER_NAMES = ["June", "Paula", "Rosa", "Iris", "Sam", "Noel", "Arun", "Lee"]


def tool_can_transform(zone: Zone, tool: Tool, target: Target) -> bool:
    return tool.id in zone.affords and tool.splash >= target.trigger


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for zid, zone in ZONES.items():
        for tid, tool in TOOLS.items():
            for gid, target in TARGETS.items():
                if tool_can_transform(zone, tool, target):
                    out.append((zid, tid, gid))
    return out


def explain_rejection(zone: Zone, tool: Tool, target: Target) -> str:
    if tool.id not in zone.affords:
        return (
            f"(No story: {tool.label} is not used in {zone.label}, so it would be a weak clue there. "
            f"Choose a tool that belongs in that part of the swim school.)"
        )
    return (
        f"(No story: {tool.label} only makes splash power {tool.splash}, but {target.phrase} "
        f"needs at least {target.trigger} to trigger the temporary transformation.)"
    )


def pick_name(rng: random.Random, gender: str, avoid: set[str]) -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name not in avoid]
    if not choices:
        raise StoryError("(No story: ran out of distinct names for the chosen cast.)")
    return rng.choice(choices)


def sprinkle_clue(world: World, culprit: Entity, zone: Zone, tool: Tool, target_ent: Entity) -> None:
    target_ent.meters["wet"] += float(tool.splash)
    target_ent.meters["transformed"] += 1
    target_ent.meters["clue"] += 1
    culprit.meters["wet_feet"] += 1
    culprit.memes["worry"] += 1
    culprit.memes["honesty_pull"] += 1
    world.facts["clue_shape"] = tool.clue
    world.facts["splash_power"] = tool.splash
    world.facts["form"] = zone.form


def introduce(world: World, detective: Entity, helper: Entity, zone: Zone) -> None:
    world.say(
        f"At swim school, the morning lesson had just begun in {zone.label}, {zone.detail}."
    )
    world.say(
        f"{detective.id}, one of the staff coaches, clipped a whistle to {detective.pronoun('possessive')} shirt, "
        f"while {helper.id} from the front desk checked names and smiled at the waiting children."
    )
    world.say(zone.mural_line)


def cast_kids(world: World, culprit: Entity, suspect_two: Entity, suspect_three: Entity,
              tool: Tool, zone: Zone) -> None:
    world.say(
        f"{culprit.id} {tool.carry_text}, while {suspect_two.id} and {suspect_three.id} practiced nearby and tried not to splash too high."
    )
    world.say(
        f"The swim school staff liked the rhyme mural, but everybody knew the rule: children could only use it when a coach said it was time."
    )


def accident(world: World, culprit: Entity, detective: Entity, helper: Entity,
             zone: Zone, tool: Tool, target_cfg: Target, target_ent: Entity) -> None:
    owner = detective if target_cfg.owner_role == "detective" else helper
    culprit.memes["curiosity"] += 1
    world.say(
        f"When {owner.id} turned away for one moment to help another swimmer, {culprit.id} whispered, "
        f'{tool.rhyme_start}, what can water do?"'
    )
    world.say(
        f"Then {culprit.pronoun()} {tool.action}. A bright splash kissed the mural tiles and bounced onto {target_cfg.phrase}."
    )
    sprinkle_clue(world, culprit, zone, tool, target_ent)
    world.say(
        f"There was a twinkle, a plip, and suddenly {target_cfg.phrase} was gone. In its place sat {target_cfg.changed_name}."
    )


def start_mystery(world: World, detective: Entity, helper: Entity, target_cfg: Target, zone: Zone) -> None:
    detective.memes["curiosity"] += 1
    helper.memes["worry"] += 1
    world.say(
        f'"Oh!" said {helper.id}. "One of the staff things changed shape."'
    )
    world.say(
        f"{detective.id} bent down beside the puddle and looked carefully. This felt less like a scolding moment and more like a little poolside whodunit."
    )
    world.say(
        f'"Who turned {target_cfg.label} into a {zone.form}?" {detective.id} asked in a calm detective voice.'
    )


def inspect_clue(world: World, detective: Entity, culprit: Entity, suspect_two: Entity,
                 suspect_three: Entity, tool: Tool, zone: Zone) -> None:
    detective.memes["confidence"] += 1
    suspect_two.memes["worry"] += 0.5
    suspect_three.memes["worry"] += 0.5
    world.say(
        f"Near the transformed object, {detective.id} found {tool.clue} and a tiny wet trail leading back toward {zone.label}."
    )
    world.say(
        f'"That clue matters," {detective.pronoun()} murmured. "Water leaves a shape before it leaves a name."'
    )


def question_others(world: World, detective: Entity, suspect_two: Entity, suspect_three: Entity) -> None:
    world.say(
        f"{detective.id} asked {suspect_two.id} and {suspect_three.id} where they had been. One had been counting bubbles on the steps, and the other had been practicing quiet kicks against the wall."
    )
    world.say(
        f"Both children were damp, of course, because this was swim school, but neither one had the special clue-shape near {detective.pronoun('possessive')} hands."
    )


def reveal(world: World, detective: Entity, culprit: Entity, tool: Tool, zone: Zone) -> None:
    culprit.memes["honesty"] += 1
    culprit.memes["worry"] += 1
    world.say(
        f"{detective.id} looked at {culprit.id}'s {tool.label}, then at the water marks, then back at the mural."
    )
    world.say(
        f'"I think I know," {detective.pronoun()} said softly. "The clue was {tool.clue}. That matches a {tool.label}, and only someone splashing in {zone.label} could have reached the mural from there."'
    )
    world.say(
        f"{culprit.id}'s cheeks grew pink. "
        f'"It was me," {culprit.pronoun()} admitted. "I only wanted to see if the rhyme was real."'
    )


def comfort_and_fix(world: World, detective: Entity, helper: Entity, culprit: Entity,
                    target_cfg: Target, target_ent: Entity) -> None:
    culprit.memes["relief"] += 1
    culprit.memes["trust"] += 1
    detective.memes["care"] += 1
    helper.memes["relief"] += 1
    target_ent.meters["transformed"] = 0.0
    world.say(
        f'{detective.id} knelt beside {culprit.id}. "Thank you for telling the truth," {detective.pronoun()} said. "At this swim school, the staff want honest words faster than perfect behavior."'
    )
    world.say(
        f"Then {detective.id} and {helper.id} touched the changed object together and sang {target_cfg.reverse_rhyme}"
    )
    world.say(
        f"With one warm blink, the magic slipped away, and {target_cfg.phrase} was itself again."
    )


def resolution(world: World, detective: Entity, helper: Entity, culprit: Entity,
               zone: Zone, target_cfg: Target) -> None:
    culprit.memes["joy"] += 1
    culprit.memes["lesson"] += 1
    world.say(
        f'"Next time," said {helper.id}, "ask one of the staff first, and we can do the rhyme game the safe way together."'
    )
    world.say(
        f'{culprit.id} nodded. "I will."'
    )
    world.say(
        f"Soon the mystery was solved, the lesson list was ready, and the children were kicking and splashing again under watchful eyes. In {zone.label}, the water still shone, but now everyone waited for the coach before trying any magic rhyme."
    )
    world.facts["solved"] = True
    world.facts["confessed"] = True
    world.facts["lesson"] = "ask the staff first"


def tell(params: StoryParams) -> World:
    if params.zone not in ZONES or params.tool not in TOOLS or params.target not in TARGETS:
        raise StoryError("(No story: one or more requested options are not in this world.)")

    zone = ZONES[params.zone]
    tool = TOOLS[params.tool]
    target_cfg = TARGETS[params.target]
    if not tool_can_transform(zone, tool, target_cfg):
        raise StoryError(explain_rejection(zone, tool, target_cfg))

    world = World()
    detective = world.add(Entity(
        id=params.detective_name,
        kind="character",
        type=params.detective_type,
        label="coach",
        role="detective",
        tags={"staff"},
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        label="staff helper",
        role="helper",
        tags={"staff"},
    ))
    culprit = world.add(Entity(
        id=params.culprit_name,
        kind="character",
        type=params.culprit_type,
        label="child",
        role="culprit",
        attrs={"tool": tool.id, "zone": zone.id},
    ))
    suspect_two = world.add(Entity(
        id=params.suspect_two_name,
        kind="character",
        type=params.suspect_two_type,
        label="child",
        role="suspect",
        attrs={"tool": "", "zone": "other_side"},
    ))
    suspect_three = world.add(Entity(
        id=params.suspect_three_name,
        kind="character",
        type=params.suspect_three_type,
        label="child",
        role="suspect",
        attrs={"tool": "", "zone": "wall_side"},
    ))
    target_ent = world.add(Entity(
        id="target",
        kind="thing",
        type="staff_object",
        label=target_cfg.label,
        phrase=target_cfg.phrase,
        role="target",
        tags=set(target_cfg.tags),
    ))

    introduce(world, detective, helper, zone)
    cast_kids(world, culprit, suspect_two, suspect_three, tool, zone)

    world.para()
    accident(world, culprit, detective, helper, zone, tool, target_cfg, target_ent)

    world.para()
    start_mystery(world, detective, helper, target_cfg, zone)
    inspect_clue(world, detective, culprit, suspect_two, suspect_three, tool, zone)
    question_others(world, detective, suspect_two, suspect_three)
    reveal(world, detective, culprit, tool, zone)

    world.para()
    comfort_and_fix(world, detective, helper, culprit, target_cfg, target_ent)
    resolution(world, detective, helper, culprit, zone, target_cfg)

    world.facts.update(
        zone=zone,
        tool=tool,
        target_cfg=target_cfg,
        detective=detective,
        helper=helper,
        culprit=culprit,
        suspect_two=suspect_two,
        suspect_three=suspect_three,
        target=target_ent,
        form=zone.form,
        staff_count=2,
    )
    return world


KNOWLEDGE = {
    "staff": [
        (
            "Who are the staff at a swim school?",
            "The staff are the grown-ups who work there, like coaches and desk helpers. They teach, watch carefully, and help everyone stay safe."
        )
    ],
    "whistle": [
        (
            "Why does a coach use a whistle at swim school?",
            "A whistle makes a clear sharp sound that children can hear over splashing water. It helps a coach stop a game or get attention quickly."
        )
    ],
    "kickboard": [
        (
            "What is a kickboard for?",
            "A kickboard is a float children hold while they practice kicking. It helps them keep part of their body up while they work on their legs."
        )
    ],
    "noodle": [
        (
            "What is a pool noodle?",
            "A pool noodle is a long bendy float made of soft foam. Children can hold it while they play or practice in the water."
        )
    ],
    "cup": [
        (
            "What is a scoop cup used for in a pool lesson?",
            "A scoop cup lets children lift and pour a little water in a controlled way. Teachers use it for simple water games and careful practice."
        )
    ],
    "rhyme": [
        (
            "What is a rhyme?",
            "A rhyme is when words have matching end sounds, like splash and dash. Rhymes are fun to say because the sounds bounce together."
        )
    ],
    "pool": [
        (
            "Why do people walk carefully near a pool?",
            "Pool decks can be slippery when they are wet. Careful feet help people keep their balance and stay safe."
        )
    ],
}

KNOWLEDGE_ORDER = ["staff", "whistle", "kickboard", "noodle", "cup", "rhyme", "pool"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    zone = f["zone"]
    tool = f["tool"]
    target_cfg = f["target_cfg"]
    detective = f["detective"]
    culprit = f["culprit"]
    return [
        f'Write a gentle whodunit for a 3-to-5-year-old set at swim school that includes the word "staff" and a playful rhyme.',
        f"Tell a mystery where a staff object changes shape near {zone.label}, and Coach {detective.id} solves the puzzle by noticing water clues from a {tool.label}.",
        f"Write a story where {culprit.id} accidentally transforms {target_cfg.phrase} with a rhyme and a splash, then tells the truth and helps put things right.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    culprit = f["culprit"]
    zone = f["zone"]
    tool = f["tool"]
    target_cfg = f["target_cfg"]
    form = f["form"]

    qa: list[tuple[str, str]] = [
        (
            "Where does the story happen?",
            f"It happens at a swim school, in {zone.label}. The setting matters because splashes, pool tools, and wet clues all belong there."
        ),
        (
            "What was the mystery?",
            f"The mystery was who turned {target_cfg.phrase} into a {form}. The change happened after a rhyme and a splash near the mural."
        ),
        (
            f"How did {detective.id} solve the mystery?",
            f"{detective.id} looked for the shape of the water clue and found {tool.clue}. That clue matched a {tool.label}, and it also pointed back to {zone.label}, so {detective.pronoun()} knew who had been close enough to trigger the magic."
        ),
        (
            f"Why did {culprit.id} admit what happened?",
            f"{culprit.id} felt worried and then heard {detective.id} speak calmly instead of angrily. That made it easier to tell the truth about trying the rhyme just to see if it was real."
        ),
        (
            "How did the story end?",
            f"The staff said the reverse rhyme together, and the changed object turned back the right way. After that, the children kept swimming, but they learned to ask the staff before trying poolside magic."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"staff", "rhyme", "pool"}
    target_cfg = world.facts["target_cfg"]
    tool = world.facts["tool"]
    if "whistle" in target_cfg.tags:
        tags.add("whistle")
    if tool.id == "kickboard":
        tags.add("kickboard")
    elif tool.id == "noodle":
        tags.add("noodle")
    elif tool.id == "scoop_cup":
        tags.add("cup")

    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
    for ent in world.entities.values():
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
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:10} ({ent.type:11}) {' '.join(bits)}")
    lines.append(f"  facts: clue_shape={world.facts.get('clue_shape')!r}, form={world.facts.get('form')!r}")
    return "\n".join(lines)


ASP_RULES = r"""
compatible(Z, T, G) :- zone(Z), tool(T), target(G), affords(Z, T), splash(T, S), trigger(G, Need), S >= Need.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for zid, zone in ZONES.items():
        lines.append(asp.fact("zone", zid))
        for tool_id in sorted(zone.affords):
            lines.append(asp.fact("affords", zid, tool_id))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("splash", tid, tool.splash))
    for gid, target in TARGETS.items():
        lines.append(asp.fact("target", gid))
        lines.append(asp.fact("trigger", gid, target.trigger))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


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
            raise StoryError("(Verify failure: generated story was empty.)")
        _ = sample.to_json()
        _ = dump_trace(sample.world) if sample.world is not None else ""
        print("OK: smoke test generate() and serialization succeeded.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"VERIFY SMOKE TEST FAILED: {err}")
    return rc


CURATED = [
    StoryParams(
        zone="splash_pool",
        tool="kickboard",
        target="whistle",
        detective_name="Mina",
        detective_type="coach_f",
        helper_name="June",
        helper_type="clerk_f",
        culprit_name="Eli",
        culprit_type="boy",
        suspect_two_name="Ruby",
        suspect_two_type="girl",
        suspect_three_name="Finn",
        suspect_three_type="boy",
    ),
    StoryParams(
        zone="bubble_steps",
        tool="scoop_cup",
        target="badge",
        detective_name="Nora",
        detective_type="coach_f",
        helper_name="Sam",
        helper_type="clerk_m",
        culprit_name="Poppy",
        culprit_type="girl",
        suspect_two_name="Ben",
        suspect_two_type="boy",
        suspect_three_name="Ivy",
        suspect_three_type="girl",
    ),
    StoryParams(
        zone="kick_lane",
        tool="kickboard",
        target="clipboard",
        detective_name="Omar",
        detective_type="coach_m",
        helper_name="Rosa",
        helper_type="clerk_f",
        culprit_name="Theo",
        culprit_type="boy",
        suspect_two_name="Nia",
        suspect_two_type="girl",
        suspect_three_name="Jude",
        suspect_three_type="boy",
    ),
    StoryParams(
        zone="bubble_steps",
        tool="noodle",
        target="badge",
        detective_name="Leah",
        detective_type="coach_f",
        helper_name="Lee",
        helper_type="clerk_m",
        culprit_name="Molly",
        culprit_type="girl",
        suspect_two_name="Kai",
        suspect_two_type="boy",
        suspect_three_name="June",
        suspect_three_type="girl",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a swim-school whodunit with rhyme, transformation, and staff."
    )
    ap.add_argument("--zone", choices=sorted(ZONES))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--target", choices=sorted(TARGETS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.zone and args.tool and args.target:
        zone = ZONES[args.zone]
        tool = TOOLS[args.tool]
        target = TARGETS[args.target]
        if not tool_can_transform(zone, tool, target):
            raise StoryError(explain_rejection(zone, tool, target))

    combos = [
        combo for combo in valid_combos()
        if (args.zone is None or combo[0] == args.zone)
        and (args.tool is None or combo[1] == args.tool)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    zone_id, tool_id, target_id = rng.choice(sorted(combos))

    detective_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    culprit_gender = rng.choice(["girl", "boy"])
    suspect_two_gender = rng.choice(["girl", "boy"])
    suspect_three_gender = rng.choice(["girl", "boy"])

    used: set[str] = set()

    detective_name = rng.choice([n for n in DETECTIVE_NAMES if n not in used])
    used.add(detective_name)
    helper_name = rng.choice([n for n in HELPER_NAMES if n not in used])
    used.add(helper_name)

    culprit_name = pick_name(rng, culprit_gender, used)
    used.add(culprit_name)
    suspect_two_name = pick_name(rng, suspect_two_gender, used)
    used.add(suspect_two_name)
    suspect_three_name = pick_name(rng, suspect_three_gender, used)
    used.add(suspect_three_name)

    return StoryParams(
        zone=zone_id,
        tool=tool_id,
        target=target_id,
        detective_name=detective_name,
        detective_type="coach_f" if detective_gender == "girl" else "coach_m",
        helper_name=helper_name,
        helper_type="clerk_f" if helper_gender == "girl" else "clerk_m",
        culprit_name=culprit_name,
        culprit_type="girl" if culprit_gender == "girl" else "boy",
        suspect_two_name=suspect_two_name,
        suspect_two_type="girl" if suspect_two_gender == "girl" else "boy",
        suspect_three_name=suspect_three_name,
        suspect_three_type="girl" if suspect_three_gender == "girl" else "boy",
    )


def generate(params: StoryParams) -> StorySample:
    if params.zone not in ZONES:
        raise StoryError(f"(No story: unknown zone {params.zone!r}.)")
    if params.tool not in TOOLS:
        raise StoryError(f"(No story: unknown tool {params.tool!r}.)")
    if params.target not in TARGETS:
        raise StoryError(f"(No story: unknown target {params.target!r}.)")

    zone = ZONES[params.zone]
    tool = TOOLS[params.tool]
    target = TARGETS[params.target]
    if not tool_can_transform(zone, tool, target):
        raise StoryError(explain_rejection(zone, tool, target))

    world = tell(params)
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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (zone, tool, target) combos:\n")
        for zone_id, tool_id, target_id in combos:
            print(f"  {zone_id:12} {tool_id:10} {target_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
        for i, sample in enumerate(samples):
            sample.params.seed = i
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
            header = f"### {p.zone} / {p.tool} / {p.target}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
