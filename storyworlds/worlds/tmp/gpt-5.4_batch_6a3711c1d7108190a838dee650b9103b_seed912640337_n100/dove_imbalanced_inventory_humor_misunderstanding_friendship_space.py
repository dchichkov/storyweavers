#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/dove_imbalanced_inventory_humor_misunderstanding_friendship_space.py
================================================================================================

A standalone storyworld about two young space friends, a funny misunderstanding,
and a little scout pod whose cargo inventory becomes imbalanced.

The seed asks for the words "dove", "imbalanced", and "inventory", with Humor,
Misunderstanding, Friendship, in a Space Adventure style. This world models a
small cargo-packing problem on a cheerful child-facing space station:

- a mission needs a scout pod
- the pod's left and right lockers must be balanced
- a misunderstanding causes a dove mascot to be packed on the wrong side
  together with a heavy mission item
- the inventory screen warns that the pod is imbalanced
- the friends solve it together, with either a smooth launch or a dockside
  adventure, depending on whether their fix is strong enough

Run it
------
    python storyworlds/worlds/gpt-5.4/dove_imbalanced_inventory_humor_misunderstanding_friendship_space.py
    python storyworlds/worlds/gpt-5.4/dove_imbalanced_inventory_humor_misunderstanding_friendship_space.py --mission comet_watch --heavy battery_barrel --dove plush_dove --fix swap_sides
    python storyworlds/worlds/gpt-5.4/dove_imbalanced_inventory_humor_misunderstanding_friendship_space.py --heavy foam_meteor
    python storyworlds/worlds/gpt-5.4/dove_imbalanced_inventory_humor_misunderstanding_friendship_space.py --all
    python storyworlds/worlds/gpt-5.4/dove_imbalanced_inventory_humor_misunderstanding_friendship_space.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
IMBALANCE_MIN = 3
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    side: str = ""
    weight: int = 0
    required: bool = False
    # physical and emotional state
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Mission:
    id: str
    title: str
    destination: str
    view: str
    reason: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class HeavyItem:
    id: str
    label: str
    phrase: str
    weight: int
    purpose: str
    funny_roll: str
    tags: set[str] = field(default_factory=set)


@dataclass
class DoveItem:
    id: str
    label: str
    phrase: str
    weight: int
    flutter: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    line: str
    mistake: str
    reveal: str
    extra_smile: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    sense: int
    power: int
    text: str
    success: str
    fail: str
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


MISSIONS = {
    "comet_watch": Mission(
        "comet_watch",
        "the little scout mission",
        "the blue-glass comet lane",
        "where a silver comet would brush the dark like a paint stroke",
        "to carry the viewing tube and warm juice packs",
        "they skimmed out beneath the comet's tail, grinning at the bright ice fire",
        tags={"comet", "space", "friendship"},
    ),
    "ring_mail": Mission(
        "ring_mail",
        "the ring-post mission",
        "the mail buoy above the ring arch",
        "where tiny delivery lights blinked like fireflies in space",
        "to drop a bundle of letters into the bright ring-post tube",
        "they floated beside the ring arch and watched the letters zip away in shining loops",
        tags={"mail", "space", "friendship"},
    ),
    "moon_garden": Mission(
        "moon_garden",
        "the moon-garden mission",
        "the greenhouse dome on Pebble Moon",
        "where tomato vines curled under purple lamps",
        "to bring fresh supplies to the moon seedlings",
        "they glided to the greenhouse dome and saw the leaves wave in the lamp glow",
        tags={"garden", "space", "friendship"},
    ),
}

HEAVY_ITEMS = {
    "battery_barrel": HeavyItem(
        "battery_barrel",
        "battery barrel",
        "a round battery barrel",
        3,
        "to power the scout lamp all the way to the mission stop",
        "It rolled one tiny inch and made the whole pod sigh to one side",
        tags={"battery", "heavy"},
    ),
    "seed_crate": HeavyItem(
        "seed_crate",
        "seed crate",
        "a square seed crate",
        2,
        "to feed the moon garden with fresh little sprouts",
        "It bumped the wall with a soft thunk, like a polite giant knocking",
        tags={"seeds", "heavy"},
    ),
    "magnet_boots": HeavyItem(
        "magnet_boots",
        "magnet boots",
        "a pair of extra magnet boots",
        2,
        "to help visitors stand steady on the outside rail",
        "The boots clonked together like two grumpy metal ducks",
        tags={"boots", "heavy"},
    ),
    "foam_meteor": HeavyItem(
        "foam_meteor",
        "foam meteor prop",
        "a giant foam meteor from the play cupboard",
        1,
        "for decoration only",
        "It bounced instead of thumping, which was funny but not dangerous",
        tags={"foam", "light"},
    ),
}

DOVES = {
    "plush_dove": DoveItem(
        "plush_dove",
        "plush dove",
        "a puffy plush dove with a gold felt beak",
        1,
        "Its wings bobbed every time somebody laughed",
        tags={"dove", "toy"},
    ),
    "paper_dove": DoveItem(
        "paper_dove",
        "paper dove glider",
        "a folded paper dove glider",
        1,
        "Its white paper tail wiggled in the air fan",
        tags={"dove", "paper"},
    ),
    "tin_dove": DoveItem(
        "tin_dove",
        "tin dove mascot",
        "a shiny tin dove mascot",
        2,
        "Its little metal wings flashed like moonlight",
        tags={"dove", "metal"},
    ),
}

MISUNDERSTANDINGS = {
    "dove_verb": Misunderstanding(
        "dove_verb",
        '"I already dove into the locker and found the straps,"',
        "the helper robot heard the word dove and decided a dove must belong on the mission inventory",
        "When the replay chirped back the sentence, everybody could hear how the robot had mixed up a verb with a bird",
        "Even the robot gave an embarrassed beep that sounded almost like a giggle",
        tags={"misunderstanding", "robot", "dove"},
    ),
    "lucky_charm": Misunderstanding(
        "lucky_charm",
        '"Bring the dove if you want luck,"',
        "one friend thought that meant the dove mascot was required space gear instead of a joke",
        "Once they compared the real checklist with what had been said out loud, the mix-up was easy to spot",
        "The lucky-dove idea was silly enough to make both friends snort with laughter",
        tags={"misunderstanding", "luck", "dove"},
    ),
    "doodle": Misunderstanding(
        "doodle",
        '"Who drew a dove in the corner of the inventory sheet?"',
        "the robot treated the doodled dove as an official cargo stamp and packed it with the mission load",
        "The drawing was only a doodle, but the scanner had read it like serious space business",
        "It was hard to stay worried when the mighty inventory scanner had been fooled by a crayon bird",
        tags={"misunderstanding", "drawing", "dove"},
    ),
}

FIXES = {
    "swap_sides": Fix(
        "swap_sides",
        3,
        4,
        "They slid the heavy item across to the quiet locker and let the dove ride on the light side",
        "The pod settled level at once",
        "but the heavy item still pulled too hard, and the pod stayed tilted",
        "moved the heavy cargo to the other locker and put the dove on the light side",
        tags={"balance", "move"},
    ),
    "split_inventory": Fix(
        "split_inventory",
        2,
        3,
        "They opened the cargo chart and spread the inventory more evenly between left and right",
        "The pod straightened enough for a smooth little launch",
        "but one side was still too heavy for a proper launch",
        "spread the inventory between both lockers until the weight was nearly even",
        tags={"balance", "inventory"},
    ),
    "leave_dove": Fix(
        "leave_dove",
        2,
        2,
        "They set the dove back on the dock bench and kept only the truly needed gear on board",
        "The warning light clicked off with a tiny happy ping",
        "but the mission cargo was still too lopsided without moving the big item too",
        "took the dove off the pod and kept only the needed mission gear",
        tags={"balance", "dove"},
    ),
    "wiggle_pod": Fix(
        "wiggle_pod",
        1,
        1,
        "They bounced in their seats and hoped the pod would feel better by itself",
        "For one silly second the pod looked straighter",
        "and of course a wiggle could not fix real cargo balance at all",
        "just wiggled in their seats instead of fixing the cargo",
        tags={"silly"},
    ),
}

GIRL_NAMES = ["Lina", "Mara", "Nova", "Zuri", "Ivy", "Tessa", "Rumi", "Pia"]
BOY_NAMES = ["Jax", "Milo", "Orin", "Tao", "Nico", "Remy", "Finn", "Sol"]
ROBOT_NAMES = ["Pip", "Orbit", "Bloop", "Tink"]


@dataclass
class StoryParams:
    mission: str
    heavy: str
    dove: str
    misunderstanding: str
    fix: str
    friend_a: str
    friend_a_gender: str
    friend_b: str
    friend_b_gender: str
    robot: str
    parent: str
    seed: Optional[int] = None


def imbalance_severity(heavy: HeavyItem, dove: DoveItem) -> int:
    return heavy.weight + dove.weight


def causes_problem(heavy: HeavyItem, dove: DoveItem) -> bool:
    return imbalance_severity(heavy, dove) >= IMBALANCE_MIN


def sensible_fixes() -> list[Fix]:
    return [f for f in FIXES.values() if f.sense >= SENSE_MIN]


def is_contained(fix: Fix, heavy: HeavyItem, dove: DoveItem) -> bool:
    return fix.power >= imbalance_severity(heavy, dove)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for mission in MISSIONS:
        for heavy_id, heavy in HEAVY_ITEMS.items():
            for dove_id, dove in DOVES.items():
                for mis_id in MISUNDERSTANDINGS:
                    if causes_problem(heavy, dove):
                        combos.append((mission, heavy_id, dove_id, mis_id))
    return combos


def explain_rejection(heavy: HeavyItem, dove: DoveItem) -> str:
    sev = imbalance_severity(heavy, dove)
    return (
        f"(No story: {heavy.phrase} plus {dove.phrase} only makes an imbalance score of "
        f"{sev}, below the story threshold of {IMBALANCE_MIN}. The pod would not feel "
        f"truly imbalanced, so there is no strong problem to fix.)"
    )


def explain_fix(fid: str) -> str:
    fix = FIXES[fid]
    better = " / ".join(sorted(f.id for f in sensible_fixes()))
    return (
        f"(Refusing fix '{fid}': it scores too low on common sense "
        f"(sense={fix.sense} < {SENSE_MIN}). Try a real balancing fix such as {better}.)"
    )


def update_balance(world: World) -> None:
    pod = world.get("pod")
    left = sum(e.weight for e in world.entities.values() if e.side == "left")
    right = sum(e.weight for e in world.entities.values() if e.side == "right")
    pod.meters["left_mass"] = float(left)
    pod.meters["right_mass"] = float(right)
    pod.meters["difference"] = float(abs(left - right))
    if abs(left - right) >= THRESHOLD:
        pod.meters["tilt"] = 1.0
    else:
        pod.meters["tilt"] = 0.0
    if abs(left - right) >= IMBALANCE_MIN:
        pod.meters["imbalanced"] = 1.0
    else:
        pod.meters["imbalanced"] = 0.0


def introduce(world: World, a: Entity, b: Entity, robot: Entity, mission: Mission) -> None:
    for kid in (a, b):
        kid.memes["excitement"] += 1
    world.say(
        f"On Starling Station, {a.id} and {b.id} were best friends and junior sky-scouts."
    )
    world.say(
        f"That morning they were allowed to take a tiny pod for {mission.title}, "
        f"out toward {mission.destination}, {mission.view}."
    )
    world.say(
        f'Their helper robot, {robot.id}, rolled beside them on bright blue wheels and said, '
        f'"Please present your inventory in a calm and not-at-all-panicky manner."'
    )


def mission_need(world: World, a: Entity, b: Entity, mission: Mission, heavy: HeavyItem) -> None:
    world.say(
        f"The mission needed {heavy.phrase} {heavy.purpose}. "
        f"{a.id} held the cargo strap, and {b.id} read the inventory board aloud."
    )


def packing(world: World, a: Entity, b: Entity, robot: Entity,
            heavy: HeavyItem, dove: DoveItem, mis: Misunderstanding) -> None:
    for kid in (a, b):
        kid.memes["focus"] += 1
    world.say(
        f"{mis.line} said {a.id if mis.id != 'lucky_charm' else b.id}. "
        f"But {mis.mistake}."
    )
    world.say(
        f"So {robot.id} tucked {heavy.phrase} and {dove.phrase} onto the same side of the pod. "
        f"{dove.flutter}"
    )


def warning(world: World, a: Entity, b: Entity, robot: Entity, heavy: HeavyItem) -> None:
    pod = world.get("pod")
    for kid in (a, b):
        kid.memes["worry"] += 1
    robot.memes["confusion"] += 1
    world.say(
        f"When the dock clamps let go for a practice glide, the pod leaned like a sleepy duck. "
        f"{heavy.funny_roll}"
    )
    world.say(
        f'Then the inventory screen flashed red: "IMBALANCED." '
        f"{b.id} grabbed the rail, and {a.id} blinked at the wobbling stars."
    )
    world.facts["difference"] = int(pod.meters["difference"])


def inspect(world: World, a: Entity, b: Entity, robot: Entity, mis: Misunderstanding) -> None:
    a.memes["confusion"] += 1
    b.memes["confusion"] += 1
    world.say(
        f"They opened the cargo map together and traced each square with one finger. "
        f"{mis.reveal}."
    )
    world.say(
        f'"Oh!" said {a.id}. "{mis.extra_smile[0].lower() + mis.extra_smile[1:]}" '
        f"said {b.id}, and even {robot.id} dipped its lamp like a shy little bow."
    )


def apply_fix(world: World, fix: Fix, heavy_ent: Entity, dove_ent: Entity) -> None:
    if fix.id == "swap_sides":
        heavy_ent.side = "left"
        dove_ent.side = "right"
    elif fix.id == "split_inventory":
        heavy_ent.side = "left"
        dove_ent.side = "right"
    elif fix.id == "leave_dove":
        dove_ent.side = "dock"
        heavy_ent.side = "right"
    update_balance(world)


def friendship_laugh(world: World, a: Entity, b: Entity, robot: Entity) -> None:
    for kid in (a, b):
        kid.memes["laughter"] += 1
        kid.memes["friendship"] += 1
    robot.memes["relief"] += 1
    world.say(
        f"Soon they were laughing instead of panicking. {a.id} steadied the cargo while "
        f"{b.id} read the list again, and {robot.id} promised to ask one extra question "
        f"before packing any future birds."
    )


def success_ending(world: World, a: Entity, b: Entity, mission: Mission, dove: DoveItem) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"The pod floated level at last, soft and straight as a bedtime dream in space."
    )
    world.say(
        f"Then {a.id} and {b.id} zipped out together. {mission.ending}, while the {dove.label} "
        f"drifted safely in its place and the stars no longer slanted."
    )


def dockside_ending(world: World, a: Entity, b: Entity, mission: Mission, dove: DoveItem) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    world.say(
        "The pod was safer, but not ready for a real glide, so they stayed on the bright dock."
    )
    world.say(
        f"Instead they sat by the wide window with warm juice, watched {mission.destination} shimmer, "
        f"and took turns tossing the {dove.label} gently in the station air. It was not the trip "
        f"they planned, but it still felt like an adventure they shared."
    )


def tell(
    mission: Mission,
    heavy: HeavyItem,
    dove: DoveItem,
    mis: Misunderstanding,
    fix: Fix,
    friend_a: str = "Lina",
    friend_a_gender: str = "girl",
    friend_b: str = "Jax",
    friend_b_gender: str = "boy",
    robot_name: str = "Pip",
    parent_type: str = "mother",
) -> World:
    world = World()
    a = world.add(Entity(friend_a, kind="character", type=friend_a_gender, role="friend_a"))
    b = world.add(Entity(friend_b, kind="character", type=friend_b_gender, role="friend_b"))
    robot = world.add(Entity(robot_name, kind="character", type="robot", role="robot"))
    parent = world.add(Entity("Guide", kind="character", type=parent_type, role="guide", label="the guide"))
    pod = world.add(Entity("pod", type="pod", label="scout pod"))
    heavy_ent = world.add(
        Entity("heavy", type="cargo", label=heavy.label, weight=heavy.weight, side="right", required=True)
    )
    dove_ent = world.add(
        Entity("dove", type="cargo", label=dove.label, weight=dove.weight, side="right", required=False)
    )
    update_balance(world)

    introduce(world, a, b, robot, mission)
    mission_need(world, a, b, mission, heavy)

    world.para()
    packing(world, a, b, robot, heavy, dove, mis)
    update_balance(world)
    warning(world, a, b, robot, heavy)

    world.para()
    inspect(world, a, b, robot, mis)
    friendship_laugh(world, a, b, robot)
    world.say(f"{fix.text}.")
    apply_fix(world, fix, heavy_ent, dove_ent)

    outcome = "smooth" if is_contained(fix, heavy, dove) else "dockside"
    if outcome == "smooth":
        world.say(f"{fix.success}.")
        world.para()
        success_ending(world, a, b, mission, dove)
    else:
        world.say(f"{fix.fail}.")
        world.para()
        dockside_ending(world, a, b, mission, dove)

    world.facts.update(
        mission=mission,
        heavy_cfg=heavy,
        dove_cfg=dove,
        misunderstanding=mis,
        fix=fix,
        friend_a=a,
        friend_b=b,
        robot=robot,
        parent=parent,
        pod=pod,
        heavy=heavy_ent,
        dove=dove_ent,
        severity=imbalance_severity(heavy, dove),
        outcome=outcome,
        imbalanced_before=True,
        left_mass=int(pod.meters["left_mass"]),
        right_mass=int(pod.meters["right_mass"]),
    )
    return world


KNOWLEDGE = {
    "inventory": [(
        "What is an inventory?",
        "An inventory is a careful list of what you have packed. It helps you notice what is missing, extra, or on the wrong side."
    )],
    "balance": [(
        "Why does a little spacecraft need balanced cargo?",
        "Balanced cargo keeps the craft from leaning too much to one side. If one side is much heavier, steering gets harder and the ride feels wobbly."
    )],
    "dove": [(
        "What is a dove?",
        "A dove is a small bird with a gentle shape. In stories, a toy or picture dove can also stand for peace or luck."
    )],
    "comet": [(
        "What is a comet?",
        "A comet is a ball of ice and dust that travels through space. When sunlight warms it, it can grow a bright tail."
    )],
    "mail": [(
        "How can mail travel in a space station?",
        "A station can send mail through little tubes, pods, or delivery robots. The letters still need to be sorted and packed carefully."
    )],
    "garden": [(
        "How can plants grow in space?",
        "Plants can grow in special space gardens with lights, water, and warm air. People take good care of them because space is not a natural farm."
    )],
    "misunderstanding": [(
        "What is a misunderstanding?",
        "A misunderstanding happens when someone hears or reads something the wrong way. Talking it through can clear the mix-up."
    )],
    "friendship": [(
        "What makes a good friendship during a problem?",
        "Good friends stay kind while they figure things out. They listen, help, and solve the problem together instead of blaming each other."
    )],
}
KNOWLEDGE_ORDER = ["inventory", "balance", "dove", "misunderstanding", "friendship", "comet", "mail", "garden"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission = f["mission"]
    mis = f["misunderstanding"]
    heavy = f["heavy_cfg"]
    dove = f["dove_cfg"]
    outcome = f["outcome"]
    ending = "a smooth launch" if outcome == "smooth" else "a dockside adventure"
    return [
        f'Write a child-friendly space adventure that includes the words "dove", "imbalanced", and "inventory".',
        f"Tell a funny story where two friends preparing {mission.title} pack {heavy.phrase}, a {dove.label}, and discover a misunderstanding.",
        f"Write a gentle friendship story in space where {mis.mistake}, the pod becomes imbalanced, and the ending is {ending}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["friend_a"]
    b = f["friend_b"]
    robot = f["robot"]
    mission = f["mission"]
    heavy = f["heavy_cfg"]
    dove = f["dove_cfg"]
    mis = f["misunderstanding"]
    fix = f["fix"]
    outcome = f["outcome"]

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about two friends, {a.id} and {b.id}, and their helper robot {robot.id}. They were getting ready for {mission.title}."
        ),
        (
            "Why did the pod become imbalanced?",
            f"It became imbalanced because {mis.mistake}. That put {heavy.phrase} and {dove.phrase} on the same side, so one locker was much heavier than the other."
        ),
        (
            "What did the inventory screen say?",
            'It flashed the warning "IMBALANCED." The screen was showing that the pod\'s cargo was leaning too much to one side.'
        ),
        (
            "How did the friends figure out the problem?",
            f"They opened the cargo map and checked the inventory together. By tracing each item and listening to the mix-up again, they discovered the misunderstanding instead of blaming each other."
        ),
        (
            f"How did {a.id} and {b.id} solve it?",
            f"They {fix.qa_text}. Working together mattered because the problem was not meanness; it was a misunderstanding that needed careful checking."
        ),
    ]
    if outcome == "smooth":
        qa.append((
            "How did the story end?",
            f"It ended with a smooth launch. After the cargo was balanced, the pod flew level and the friends could enjoy {mission.destination} together."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"It ended on the station dock instead of in open space. The pod was safer after the fix, but not balanced enough for launch, so the friends made a cheerful window-side adventure together."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"inventory", "balance", "dove", "misunderstanding", "friendship"}
    mission = f["mission"]
    if "comet" in mission.tags:
        tags.add("comet")
    if "mail" in mission.tags:
        tags.add("mail")
    if "garden" in mission.tags:
        tags.add("garden")
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if e.side:
            bits.append(f"side={e.side}")
        if e.weight:
            bits.append(f"weight={e.weight}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("comet_watch", "battery_barrel", "plush_dove", "dove_verb", "swap_sides",
                "Lina", "girl", "Jax", "boy", "Pip", "mother"),
    StoryParams("ring_mail", "seed_crate", "paper_dove", "doodle", "split_inventory",
                "Mara", "girl", "Nico", "boy", "Orbit", "father"),
    StoryParams("moon_garden", "magnet_boots", "tin_dove", "lucky_charm", "leave_dove",
                "Nova", "girl", "Remy", "boy", "Bloop", "mother"),
]


ASP_RULES = r"""
problem(Heavy, Dove) :- heavy(Heavy), dove(Dove),
                        heavy_weight(Heavy, HW), dove_weight(Dove, DW),
                        imbalance_min(M), HW + DW >= M.

valid(Mission, Heavy, Dove, Mis) :- mission(Mission), misunderstanding(Mis),
                                    problem(Heavy, Dove).

sensible(Fix) :- fix(Fix), fix_sense(Fix, S), sense_min(M), S >= M.

severity(V) :- chosen_heavy(Heavy), chosen_dove(Dove),
               heavy_weight(Heavy, HW), dove_weight(Dove, DW), V = HW + DW.
contained :- chosen_fix(Fix), severity(V), fix_power(Fix, P), P >= V.
outcome(smooth) :- contained.
outcome(dockside) :- not contained.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for mid in MISSIONS:
        lines.append(asp.fact("mission", mid))
    for hid, heavy in HEAVY_ITEMS.items():
        lines.append(asp.fact("heavy", hid))
        lines.append(asp.fact("heavy_weight", hid, heavy.weight))
    for did, dove in DOVES.items():
        lines.append(asp.fact("dove", did))
        lines.append(asp.fact("dove_weight", did, dove.weight))
    for mis in MISUNDERSTANDINGS:
        lines.append(asp.fact("misunderstanding", mis))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("fix_sense", fid, fix.sense))
        lines.append(asp.fact("fix_power", fid, fix.power))
    lines.append(asp.fact("imbalance_min", IMBALANCE_MIN))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(v for (v,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_heavy", params.heavy),
        asp.fact("chosen_dove", params.dove),
        asp.fact("chosen_fix", params.fix),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def outcome_of(params: StoryParams) -> str:
    return "smooth" if is_contained(FIXES[params.fix], HEAVY_ITEMS[params.heavy], DOVES[params.dove]) else "dockside"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos.")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_sens = {f.id for f in sensible_fixes()}
    asp_sens = set(asp_sensible())
    if py_sens == asp_sens:
        print(f"OK: sensible fixes match ({sorted(py_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_sens)} python={sorted(py_sens)}")

    cases = list(CURATED)
    for seed in range(30):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: an imbalanced pod inventory, a dove misunderstanding, and friendship in space."
    )
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--heavy", choices=HEAVY_ITEMS)
    ap.add_argument("--dove", choices=DOVES)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--parent", choices=["mother", "father"])
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


def _pick_friend(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.heavy and args.dove:
        heavy = HEAVY_ITEMS[args.heavy]
        dove = DOVES[args.dove]
        if not causes_problem(heavy, dove):
            raise StoryError(explain_rejection(heavy, dove))
    if args.fix and FIXES[args.fix].sense < SENSE_MIN:
        raise StoryError(explain_fix(args.fix))

    combos = [
        c for c in valid_combos()
        if (args.mission is None or c[0] == args.mission)
        and (args.heavy is None or c[1] == args.heavy)
        and (args.dove is None or c[2] == args.dove)
        and (args.misunderstanding is None or c[3] == args.misunderstanding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    mission, heavy, dove, misunderstanding = rng.choice(sorted(combos))
    fix = args.fix or rng.choice(sorted(f.id for f in sensible_fixes()))
    a, ag = _pick_friend(rng)
    b, bg = _pick_friend(rng, avoid=a)
    robot = rng.choice(ROBOT_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(mission, heavy, dove, misunderstanding, fix, a, ag, b, bg, robot, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        MISSIONS[params.mission],
        HEAVY_ITEMS[params.heavy],
        DOVES[params.dove],
        MISUNDERSTANDINGS[params.misunderstanding],
        FIXES[params.fix],
        params.friend_a,
        params.friend_a_gender,
        params.friend_b,
        params.friend_b_gender,
        params.robot,
        params.parent,
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
        print(asp_program("", "#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (mission, heavy, dove, misunderstanding) combos:\n")
        for mission, heavy, dove, mis in combos:
            print(f"  {mission:12} {heavy:14} {dove:12} {mis}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
            header = (
                f"### {p.friend_a} & {p.friend_b}: {p.mission} "
                f"({p.heavy}, {p.dove}, {p.fix}, {outcome_of(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
