#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/permissive_extension_quilt_teamwork_sound_effects_nursery.py
========================================================================================

A small nursery-rhyme story world about two children making a quilt nook in a
nursery. They want light or music inside the cozy space, and one child is
tempted to drag an extension cord across a walking path. The world model knows
when that is a real trip hazard, lets a careful helper foresee the wobble, and
then resolves the story through teamwork and a safer plan.

The seed words "permissive", "extension", and "quilt" are part of the domain
itself rather than being pasted into a frozen template. Sound effects are woven
through the prose, and the ending image always shows what changed in the room.
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

# Make the shared result containers importable when this script is run directly
# from its nested directory under storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BOLDNESS_INIT = 5.0
CAUTIOUS_TRAITS = {"careful", "cautious", "steady", "thoughtful"}


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
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    setup: str
    goal: str
    closing: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    wish: str
    device: str
    sound: str
    cozy_line: str
    plug_needed: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Path:
    id: str
    label: str
    traveler: str
    traveler_sound: str
    reason: str
    risky: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class SafeFix:
    id: str
    label: str
    sense: int
    supports: set[str]
    action: str
    ending: str
    qa_text: str
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

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "helper"}]

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_trip(world: World) -> list[str]:
    out: list[str] = []
    cord = world.entities.get("cord")
    traveler = world.entities.get("traveler")
    device = world.entities.get("device")
    if cord is None or traveler is None or device is None:
        return out
    if cord.meters["across_path"] < THRESHOLD:
        return out
    if traveler.meters["moving"] < THRESHOLD:
        return out
    sig = ("trip", traveler.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    device.meters["wobble"] += 1
    world.get("room").meters["danger"] += 1
    traveler.memes["startled"] += 1
    for kid in world.kids():
        kid.memes["fear"] += 1
    out.append("__wobble__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="trip", tag="physical", apply=_r_trip),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def compatible_fixes(need_id: str) -> list[SafeFix]:
    return [fix for fix in FIXES.values() if need_id in fix.supports and fix.sense >= SENSE_MIN]


def hazard_at_risk(need: Need, path: Path) -> bool:
    return need.plug_needed and path.risky


def would_avert(relation: str, instigator_age: int, helper_age: int, trait: str) -> bool:
    cautious = 5.0 if trait in CAUTIOUS_TRAITS else 3.0
    authority = cautious + 1.0
    if relation == "siblings" and helper_age > instigator_age:
        authority += 3.0
    return authority > BOLDNESS_INIT


def outcome_of(params: "StoryParams") -> str:
    if would_avert(
        relation=params.relation,
        instigator_age=params.instigator_age,
        helper_age=params.helper_age,
        trait=params.helper_trait,
    ):
        return "averted"
    return "wobble"


def _do_extension(world: World, narrate: bool = True) -> None:
    cord = world.get("cord")
    traveler = world.get("traveler")
    cord.meters["across_path"] += 1
    traveler.meters["moving"] += 1
    propagate(world, narrate=narrate)


def predict_wobble(world: World) -> dict:
    sim = world.copy()
    _do_extension(sim, narrate=False)
    device = sim.get("device")
    return {
        "wobble": device.meters["wobble"] >= THRESHOLD,
        "danger": sim.get("room").meters["danger"],
    }


def introduce(world: World, a: Entity, b: Entity, scene: Scene) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In the nursery, {a.id} and {b.id} made {scene.place}. "
        f"{scene.setup}"
    )
    world.say(
        f'Swish-swish went the quilt, and pat-pat went their feet as they worked in teamwork for {scene.goal}.'
    )


def need_line(world: World, a: Entity, b: Entity, need: Need) -> None:
    world.say(
        f'"Hush and listen," said {b.id}. "{need.sound} would make our little nest feel just right."'
    )
    world.say(
        f"{a.id} nodded. They wanted {need.wish}, because {need.cozy_line}."
    )


def tempt(world: World, a: Entity, need: Need, path: Path) -> None:
    a.memes["boldness"] += 1
    world.say(
        f'Then {a.id} spied an extension cord by the wall. "We can pull the {need.device} over," '
        f'{a.pronoun()} said. "Zip-zip across {path.label}, and we will be ready."'
    )


def warn(world: World, b: Entity, caregiver: Entity, path: Path) -> None:
    pred = predict_wobble(world)
    world.facts["predicted_danger"] = pred["danger"]
    b.memes["caution"] += 1
    extra = " and the thought made the helper's heart go thump-thump" if pred["wobble"] else ""
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{caregiver.label_word.capitalize()} is not permissive about '
        f'an extension cord across {path.label}," {b.pronoun()} said. '
        f'"{path.traveler} goes there {path.reason}, and {path.traveler_sound} could bring a stumble."{extra}'
    )


def back_down(world: World, a: Entity, b: Entity) -> None:
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at the cord, then at {b.id}, and gave a small nod. "No drag-drag on the floor," '
        f'{a.pronoun()} said. The idea stopped right there.'
    )


def stretch(world: World, a: Entity, need: Need, path: Path) -> None:
    _do_extension(world, narrate=False)
    world.say(
        f"Still, the wish for {need.device} felt strong. {a.id} drew the extension cord out over {path.label}."
    )
    world.say(
        f"Scrrrape went the plug. Tight-tight went the cord."
    )


def wobble(world: World, path: Path, need: Need) -> None:
    world.say(
        f"Then {path.traveler_sound} came by, and the cord gave a little tug. Wobble-wobble went the {need.device}."
    )


def teamwork_catch(world: World, a: Entity, b: Entity, caregiver: Entity, need: Need) -> None:
    device = world.get("device")
    device.meters["safe"] += 1
    device.meters["wobble"] = 0.0
    world.get("room").meters["danger"] = 0.0
    for kid in (a, b):
        kid.memes["teamwork"] += 1
        kid.memes["fear"] = 0.0
        kid.memes["relief"] += 1
    caregiver.memes["care"] += 1
    world.say(
        f'{a.id} grabbed one side, {b.id} grabbed the other, and together they steadied the {need.device}. '
        f'Tip-tap, catch-snap, safe again!'
    )
    world.say(
        f'{caregiver.label_word.capitalize()} hurried over, unplugged the extension cord, and said, '
        f'"Thank you for working together so quickly."'
    )


def safe_solution(world: World, a: Entity, b: Entity, caregiver: Entity, scene: Scene,
                  need: Need, fix: SafeFix) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["safety"] += 1
        kid.memes["teamwork"] += 1
    world.say(
        f'{caregiver.label_word.capitalize()} smiled and helped them {fix.action}.'
    )
    world.say(
        f'Soon the nursery was cozy again. {fix.ending}'
    )
    world.say(
        f'Swish-swish went the quilt once more, and the two helpers sat snug in {scene.place}, {scene.closing}.'
    )


def tell(scene: Scene, need: Need, path: Path, fix: SafeFix,
         instigator_name: str = "Mina", instigator_gender: str = "girl",
         helper_name: str = "Jo", helper_gender: str = "boy",
         helper_trait: str = "careful", caregiver_type: str = "mother",
         instigator_age: int = 4, helper_age: int = 6,
         relation: str = "siblings") -> World:
    world = World()
    a = world.add(Entity(
        id=instigator_name,
        kind="character",
        type=instigator_gender,
        role="instigator",
        age=instigator_age,
        traits=["bold"],
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_gender,
        role="helper",
        age=helper_age,
        traits=[helper_trait],
        attrs={"relation": relation},
    ))
    caregiver = world.add(Entity(
        id="Caregiver",
        kind="character",
        type=caregiver_type,
        role="caregiver",
        label="the caregiver",
    ))
    world.add(Entity(id="room", type="room", label="nursery"))
    world.add(Entity(id="quilt", type="quilt", label="quilt"))
    world.add(Entity(id="cord", type="extension_cord", label="extension cord"))
    world.add(Entity(id="device", type="device", label=need.device))
    world.add(Entity(id="traveler", type="traveler", label=path.traveler))

    a.memes["boldness"] = BOLDNESS_INIT
    b.memes["caution"] = 5.0 if helper_trait in CAUTIOUS_TRAITS else 3.0

    introduce(world, a, b, scene)
    need_line(world, a, b, need)

    world.para()
    tempt(world, a, need, path)
    warn(world, b, caregiver, path)

    if would_avert(relation=relation, instigator_age=instigator_age, helper_age=helper_age, trait=helper_trait):
        back_down(world, a, b)
        world.para()
        safe_solution(world, a, b, caregiver, scene, need, fix)
        outcome = "averted"
        wobble_happened = False
    else:
        world.say(f'{a.id} bit {a.pronoun("possessive")} lip. "Just one little pull," {a.pronoun()} whispered.')
        world.para()
        stretch(world, a, need, path)
        wobble(world, path, need)
        teamwork_catch(world, a, b, caregiver, need)
        world.para()
        safe_solution(world, a, b, caregiver, scene, need, fix)
        outcome = "wobble"
        wobble_happened = True

    world.facts.update(
        scene=scene,
        need=need,
        path_cfg=path,
        fix=fix,
        instigator=a,
        helper=b,
        caregiver=caregiver,
        outcome=outcome,
        wobble=wobble_happened,
        relation=relation,
    )
    return world


SCENES = {
    "chair_tent": Scene(
        id="chair_tent",
        place="a chair-to-chair little house",
        setup="Two chairs stood like sleepy bears, and a patchwork quilt made the roof.",
        goal="a hush-hush hiding place",
        closing="with knees tucked under and eyes bright as buttons",
        tags={"quilt", "nursery"},
    ),
    "crib_cave": Scene(
        id="crib_cave",
        place="a moonlit crib-side cave",
        setup="A soft quilt hung from the rocking chair to the crib rail, making a blue-shadow cave.",
        goal="a whispering reading nook",
        closing="with story pages glowing in their laps",
        tags={"quilt", "reading"},
    ),
    "window_nest": Scene(
        id="window_nest",
        place="a window-side nest",
        setup="They pinned a quilt by the low window seat and tucked cushions underneath like eggs in straw.",
        goal="a snug song corner",
        closing="while evening stars blinked beyond the pane",
        tags={"quilt", "window"},
    ),
}

NEEDS = {
    "lamp": Need(
        id="lamp",
        wish="a warm little light",
        device="lamp",
        sound="click-click",
        cozy_line="soft light makes a small house feel golden",
        tags={"lamp", "light"},
    ),
    "music_box": Need(
        id="music_box",
        wish="a twirling little tune",
        device="music box",
        sound="plink-plink",
        cozy_line="a tune makes quiet work feel merry",
        tags={"music", "sound"},
    ),
    "star_lamp": Need(
        id="star_lamp",
        wish="a ceiling full of tiny stars",
        device="star lamp",
        sound="blink-blink",
        cozy_line="tiny stars make whispers feel like bedtime magic",
        tags={"lamp", "stars"},
    ),
}

PATHS = {
    "doorway": Path(
        id="doorway",
        label="the doorway",
        traveler="someone coming in with careful hands",
        traveler_sound="step-step",
        reason="whenever the door opens",
        risky=True,
        tags={"trip", "doorway"},
    ),
    "book_path": Path(
        id="book_path",
        label="the path to the book basket",
        traveler="small feet fetching more books",
        traveler_sound="tap-tap",
        reason="every time another story is chosen",
        risky=True,
        tags={"trip", "books"},
    ),
    "crib_path": Path(
        id="crib_path",
        label="the crib path",
        traveler="a toddling little brother",
        traveler_sound="pad-pad",
        reason="when he waddles over to peek",
        risky=True,
        tags={"trip", "toddler"},
    ),
    "wall_edge": Path(
        id="wall_edge",
        label="the wall edge",
        traveler="almost nobody at all",
        traveler_sound="hush",
        reason="because the floor there stays empty",
        risky=False,
        tags={"wall"},
    ),
}

FIXES = {
    "battery_lantern": SafeFix(
        id="battery_lantern",
        label="battery lantern",
        sense=3,
        supports={"lamp", "star_lamp"},
        action="set a battery lantern inside the quilt nook instead",
        ending="Click went the safe light, glow-glow went the nest, and no cord crossed anyone's toes.",
        qa_text="used a battery lantern so the cozy nook had light without a cord on the floor",
        tags={"lantern", "light"},
    ),
    "move_near_socket": SafeFix(
        id="move_near_socket",
        label="move the nook near the socket",
        sense=3,
        supports={"lamp", "music_box", "star_lamp"},
        action="shuffle the quilt house closer to the wall socket so the plug could reach without an extension",
        ending="Scoot-scoot went the chairs, smooth went the quilt, and the little device could stay nearby with no line across the path.",
        qa_text="moved the quilt nook close enough to the socket that no extension cord had to cross the path",
        tags={"socket", "teamwork"},
    ),
    "sing_together": SafeFix(
        id="sing_together",
        label="sing together",
        sense=3,
        supports={"music_box"},
        action="clap the beat and sing the tune themselves",
        ending="Clap-clap went their hands, la-la went their voices, and the nursery sounded fuller than any box could make it.",
        qa_text="made the music themselves by singing and clapping instead of dragging a cord across the floor",
        tags={"music", "teamwork"},
    ),
    "long_floor_cord": SafeFix(
        id="long_floor_cord",
        label="long floor cord",
        sense=1,
        supports={"lamp", "music_box", "star_lamp"},
        action="leave the extension cord stretched across the middle of the floor",
        ending="The room stayed risky.",
        qa_text="left the cord on the floor",
        tags={"cord"},
    ),
}

GIRL_NAMES = ["Mina", "Lulu", "Poppy", "Nell", "Daisy", "Tess", "Ruby", "Ivy"]
BOY_NAMES = ["Jo", "Toby", "Finn", "Milo", "Ned", "Owen", "Kit", "Ben"]
TRAITS = ["careful", "cautious", "steady", "thoughtful", "curious", "cheerful"]


@dataclass
class StoryParams:
    scene: str
    need: str
    path: str
    fix: str
    instigator: str
    instigator_gender: str
    helper: str
    helper_gender: str
    helper_trait: str
    caregiver: str
    instigator_age: int = 4
    helper_age: int = 6
    relation: str = "siblings"
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id in SCENES:
        for need_id, need in NEEDS.items():
            for path_id, path in PATHS.items():
                if hazard_at_risk(need, path) and compatible_fixes(need_id):
                    combos.append((scene_id, need_id, path_id))
    return combos


CURATED = [
    StoryParams(
        scene="chair_tent",
        need="lamp",
        path="book_path",
        fix="battery_lantern",
        instigator="Mina",
        instigator_gender="girl",
        helper="Jo",
        helper_gender="boy",
        helper_trait="careful",
        caregiver="mother",
        instigator_age=4,
        helper_age=6,
        relation="siblings",
    ),
    StoryParams(
        scene="crib_cave",
        need="music_box",
        path="crib_path",
        fix="sing_together",
        instigator="Milo",
        instigator_gender="boy",
        helper="Nell",
        helper_gender="girl",
        helper_trait="thoughtful",
        caregiver="father",
        instigator_age=5,
        helper_age=5,
        relation="friends",
    ),
    StoryParams(
        scene="window_nest",
        need="star_lamp",
        path="doorway",
        fix="move_near_socket",
        instigator="Poppy",
        instigator_gender="girl",
        helper="Toby",
        helper_gender="boy",
        helper_trait="steady",
        caregiver="mother",
        instigator_age=4,
        helper_age=7,
        relation="siblings",
    ),
]


KNOWLEDGE = {
    "extension": [
        (
            "What is an extension cord?",
            "An extension cord is a long electric cord that carries power farther from a wall socket. It must be used carefully, because a cord stretched across the floor can make someone trip.",
        )
    ],
    "quilt": [
        (
            "What is a quilt?",
            "A quilt is a soft blanket made from layers of cloth, often sewn in patches. It can keep you warm and can also make a cozy little tent when a grown-up says it is okay.",
        )
    ],
    "trip": [
        (
            "Why can a cord on the floor be dangerous?",
            "A cord on the floor can catch on someone's foot and make them stumble. That is why people try to keep walking paths clear.",
        )
    ],
    "lantern": [
        (
            "Why is a battery lantern safer in a little play nook?",
            "A battery lantern gives light without a long cord crossing the floor. It helps children see while keeping the walkway clear.",
        )
    ],
    "socket": [
        (
            "Why is moving closer to the wall socket safer than stretching a cord across the room?",
            "Moving closer means the plug can reach without a line lying where people walk. That keeps the path open and lowers the chance of a trip.",
        )
    ],
    "music": [
        (
            "Can children make music without a machine?",
            "Yes. They can clap, hum, sing, or pat a rhythm together. Their own voices and hands can make happy music safely.",
        )
    ],
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork means people help one another to do a job or solve a problem together. Working as a team can make everyone safer and calmer.",
        )
    ],
}
KNOWLEDGE_ORDER = ["extension", "quilt", "trip", "lantern", "socket", "music", "teamwork"]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        return "a brother and a sister"
    return "two friends"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    scene = f["scene"]
    need = f["need"]
    path = f["path_cfg"]
    outcome = f["outcome"]
    base = (
        f'Write a nursery-rhyme-style story for a 3-to-5-year-old that includes the words "permissive", '
        f'"extension", and "quilt", and uses teamwork and sound effects.'
    )
    if outcome == "averted":
        return [
            base,
            f"Tell a gentle story where {a.id} and {b.id} build {scene.place}, want {need.wish}, and a careful helper stops an extension-cord mistake before it happens.",
            f"Write a cozy nursery story where children work together to make a quilt nook safe after remembering that their caregiver is not permissive about cords across {path.label}.",
        ]
    return [
        base,
        f"Tell a nursery story where {a.id} and {b.id} stretch an extension cord toward a quilt nook, {path.traveler_sound} comes by, and the children use teamwork to steady things and choose a safer plan.",
        f"Write a rhyming-feeling story with swish, click, and wobble sounds, where a small danger in the nursery leads to a cooperative fix and a snug ending image.",
    ]


def story_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["helper"]
    caregiver = f["caregiver"]
    scene = f["scene"]
    need = f["need"]
    path = f["path_cfg"]
    fix = f["fix"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, making a cozy nursery nook together. {caregiver.label_word.capitalize()} also helps them choose the safer plan.",
        ),
        (
            "What were the children building?",
            f"They were building {scene.place} with a quilt so they could have {scene.goal}. The quilt changed the plain nursery into a snug little world of its own.",
        ),
        (
            f"Why did {a.id} want the extension cord?",
            f"{a.id} wanted to pull the {need.device} over to the quilt nook so it could have {need.wish}. The cord seemed like a quick way to bring the cozy thing closer.",
        ),
        (
            f"Why did {b.id} say the caregiver was not permissive about that idea?",
            f"{b.id} knew a cord across {path.label} could make trouble because {path.traveler} goes there {path.reason}. The warning came from thinking about who would cross that path and what might happen to the device.",
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"What happened after the warning?",
                f"{a.id} stopped before dragging the extension cord across the floor. Then the children and {caregiver.label_word} worked together and {fix.qa_text}.",
            )
        )
    else:
        qa.append(
            (
                "What was the middle problem in the story?",
                f"When the extension cord was stretched across {path.label}, {path.traveler_sound} came by and the {need.device} began to wobble. The danger came from putting a cord where someone could catch or tug it.",
            )
        )
        qa.append(
            (
                "How did the children solve the problem?",
                f"They used teamwork to steady the {need.device} together, and then {caregiver.label_word} removed the risky cord. After that, they {fix.qa_text}.",
            )
        )
    qa.append(
        (
            "How did the story end?",
            f"It ended with the nursery feeling cozy and safe again. The final image proves the change, because the quilt nook stayed snug without an extension cord lying across the path.",
        )
    )
    return qa


def world_knowledge_qa_items(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"extension", "quilt", "teamwork", "trip"} | set(f["fix"].tags)
    if f["need"].id == "music_box":
        tags.add("music")
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
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.age:
            bits.append(f"age={e.age}")
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:10} ({e.type:14}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(path: Path) -> str:
    return (
        f"(No story: {path.label} is not a real walking lane here, so an extension cord there would not create a believable nursery problem. "
        f"Choose a path like doorway, book_path, or crib_path where someone really passes.)"
    )


def explain_fix(fix_id: str, need_id: str) -> str:
    fix = FIXES[fix_id]
    if fix.sense < SENSE_MIN:
        return (
            f"(Refusing fix '{fix_id}': it leaves the extension cord on the floor and scores below the common-sense minimum.)"
        )
    return (
        f"(No story: fix '{fix_id}' does not actually solve the need '{need_id}' in this world.)"
    )


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
hazard(N, P) :- need(N), path(P), plug_needed(N), risky(P).
sensible_fix(F) :- fix(F), sense(F, S), sense_min(M), S >= M.
supports_need(F, N) :- fix_supports(F, N).
valid(Scene, N, P) :- scene(Scene), hazard(N, P), path(P), need(N).

% --- outcome model ---------------------------------------------------------
cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
older_helper :- relation(siblings), helper_age(HA), instigator_age(IA), HA > IA.
bonus(3) :- older_helper.
bonus(0) :- not older_helper.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- authority(A), boldness_init(B), A > B.

outcome(averted) :- averted.
outcome(wobble) :- not averted.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for scene_id in SCENES:
        lines.append(asp.fact("scene", scene_id))
    for need_id, need in NEEDS.items():
        lines.append(asp.fact("need", need_id))
        if need.plug_needed:
            lines.append(asp.fact("plug_needed", need_id))
    for path_id, path in PATHS.items():
        lines.append(asp.fact("path", path_id))
        if path.risky:
            lines.append(asp.fact("risky", path_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("sense", fix_id, fix.sense))
        for need_id in sorted(fix.supports):
            lines.append(asp.fact("fix_supports", fix_id, need_id))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("boldness_init", int(BOLDNESS_INIT)))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_fixes() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible_fix/1."))
    return sorted(f for (f,) in asp.atoms(model, "sensible_fix"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join(
        [
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("helper_age", params.helper_age),
            asp.fact("trait", params.helper_trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_fixes = {fix.id for fix in compatible_fixes("lamp")} | {fix.id for fix in compatible_fixes("music_box")} | {
        fix.id for fix in compatible_fixes("star_lamp")
    }
    asp_fixes = set(asp_sensible_fixes())
    if py_fixes == asp_fixes:
        print(f"OK: sensible fixes match ({sorted(py_fixes)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible fixes: clingo={sorted(asp_fixes)} python={sorted(py_fixes)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(50):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story from smoke test")
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Nursery-rhyme story world: a quilt nook, an extension-cord temptation, and a teamwork fix."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--caregiver", choices=["mother", "father"])
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


def _pick_child(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.path and not PATHS[args.path].risky:
        raise StoryError(explain_rejection(PATHS[args.path]))
    if args.fix:
        if FIXES[args.fix].sense < SENSE_MIN:
            need_id = args.need or "lamp"
            raise StoryError(explain_fix(args.fix, need_id))
        if args.need and args.need not in FIXES[args.fix].supports:
            raise StoryError(explain_fix(args.fix, args.need))

    combos = [
        combo
        for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.need is None or combo[1] == args.need)
        and (args.path is None or combo[2] == args.path)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, need_id, path_id = rng.choice(sorted(combos))
    fix_id = args.fix or rng.choice(sorted(fix.id for fix in compatible_fixes(need_id)))
    instigator, instigator_gender = _pick_child(rng)
    helper, helper_gender = _pick_child(rng, avoid=instigator)
    helper_trait = rng.choice(TRAITS)
    caregiver = args.caregiver or rng.choice(["mother", "father"])
    relation = rng.choice(["siblings", "friends"])
    instigator_age, helper_age = rng.sample([3, 4, 5, 6, 7], 2)
    return StoryParams(
        scene=scene_id,
        need=need_id,
        path=path_id,
        fix=fix_id,
        instigator=instigator,
        instigator_gender=instigator_gender,
        helper=helper,
        helper_gender=helper_gender,
        helper_trait=helper_trait,
        caregiver=caregiver,
        instigator_age=instigator_age,
        helper_age=helper_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        scene = SCENES[params.scene]
        need = NEEDS[params.need]
        path = PATHS[params.path]
        fix = FIXES[params.fix]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter: {err.args[0]})") from None

    if not hazard_at_risk(need, path):
        raise StoryError(explain_rejection(path))
    if fix.sense < SENSE_MIN or need.id not in fix.supports:
        raise StoryError(explain_fix(params.fix, params.need))

    world = tell(
        scene=scene,
        need=need,
        path=path,
        fix=fix,
        instigator_name=params.instigator,
        instigator_gender=params.instigator_gender,
        helper_name=params.helper,
        helper_gender=params.helper_gender,
        helper_trait=params.helper_trait,
        caregiver_type=params.caregiver,
        instigator_age=params.instigator_age,
        helper_age=params.helper_age,
        relation=params.relation,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_items(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa_items(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible_fix/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible fixes: {', '.join(asp_sensible_fixes())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, need, path) combos:\n")
        for scene_id, need_id, path_id in combos:
            print(f"  {scene_id:12} {need_id:10} {path_id}")
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
            header = f"### {p.instigator} & {p.helper}: {p.need} in {p.scene} ({outcome_of(p)})"
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
