#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/news_whisker_detergent_reconciliation_ghost_story.py
==============================================================================

A standalone story world about a gentle misunderstanding in an old house:
a child hears unsettling news, meets a cat ghost beside spilled detergent,
blames the wrong culprit, then discovers the ghost was trying to save a keepsake.
The story resolves through apology, repair, and reconciliation.

Words carried by the world:
- news
- whisker
- detergent

Run it
------
    python storyworlds/worlds/gpt-5.4/news_whisker_detergent_reconciliation_ghost_story.py
    python storyworlds/worlds/gpt-5.4/news_whisker_detergent_reconciliation_ghost_story.py --room laundry --keepsake clipping --repair press_flat
    python storyworlds/worlds/gpt-5.4/news_whisker_detergent_reconciliation_ghost_story.py --room back_hall --keepsake scarf --repair rinse_gently
    python storyworlds/worlds/gpt-5.4/news_whisker_detergent_reconciliation_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/news_whisker_detergent_reconciliation_ghost_story.py --verify
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        catlike = {"cat_ghost", "cat"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in catlike:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Room:
    id: str
    label: str
    phrase: str
    mood: str
    detergent_spot: str
    clue: str
    supports: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Keepsake:
    id: str
    label: str
    phrase: str
    material: str
    memory: str
    ghost_goal: str
    damage_text: str
    fixed_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    needs: set[str] = field(default_factory=set)
    materials: set[str] = field(default_factory=set)
    action: str = ""
    result: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    room: str
    keepsake: str
    repair: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    storm_level: str
    seed: Optional[int] = None


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_detergent_soaks(world: World) -> list[str]:
    out: list[str] = []
    detergent = world.entities.get("detergent")
    keepsake = world.entities.get("keepsake")
    if not detergent or not keepsake:
        return out
    if detergent.meters["spilled"] < THRESHOLD:
        return out
    if keepsake.meters["sudsy"] >= THRESHOLD:
        return out
    sig = ("detergent_soaks", keepsake.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    keepsake.meters["sudsy"] += 1
    keepsake.meters["threatened"] += 1
    out.append("__suds__")
    return out


def _r_wrong_accusation(world: World) -> list[str]:
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    if not child or not ghost:
        return []
    if child.memes["accused"] < THRESHOLD:
        return []
    sig = ("wrong_accusation",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["guilt_seed"] += 1
    ghost.memes["hurt"] += 1
    ghost.memes["distance"] += 1
    return ["__hurt__"]


def _r_reconciliation(world: World) -> list[str]:
    child = world.entities.get("child")
    ghost = world.entities.get("ghost")
    keepsake = world.entities.get("keepsake")
    if not child or not ghost or not keepsake:
        return []
    if child.memes["apology"] < THRESHOLD or child.memes["repair_done"] < THRESHOLD:
        return []
    sig = ("reconciliation",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["relief"] += 1
    child.memes["trust"] += 1
    ghost.memes["trust"] += 1
    ghost.memes["hurt"] = 0.0
    ghost.memes["distance"] = 0.0
    ghost.memes["peace"] += 1
    keepsake.meters["saved"] += 1
    return ["__peace__"]


CAUSAL_RULES = [
    Rule(name="detergent_soaks", tag="physical", apply=_r_detergent_soaks),
    Rule(name="wrong_accusation", tag="social", apply=_r_wrong_accusation),
    Rule(name="reconciliation", tag="social", apply=_r_reconciliation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            items = rule.apply(world)
            if items:
                changed = True
                produced.extend(items)
    if narrate:
        for item in produced:
            if item == "__suds__":
                world.say("A pale streak of detergent crept closer, leaving cold little bubbles around the keepsake.")
            elif item == "__hurt__":
                world.say("The cat ghost shrank back, as if the sharp words had passed through it like wind through lace.")
            elif item == "__peace__":
                world.say("The room felt warmer at once, and the small haunting no longer seemed lonely.")
    return produced


ROOMS = {
    "laundry": Room(
        id="laundry",
        label="laundry room",
        phrase="the old laundry room behind the kitchen",
        mood="The rafters held a soft gray gloom, and the wash tub shone like a moon in the dark.",
        detergent_spot="on the shelf above the wash tub",
        clue="a crooked shelf had left a bright blue trail down the wall",
        supports={"press_flat", "rinse_gently", "polish_softly"},
        tags={"laundry", "detergent"},
    ),
    "back_hall": Room(
        id="back_hall",
        label="back hall",
        phrase="the back hall beside the coat hooks",
        mood="The boards gave small sighs, and the single window showed a slice of silver rain.",
        detergent_spot="in a wooden crate by the mop bucket",
        clue="the crate had tipped and leaked a foamy ribbon across the floorboards",
        supports={"press_flat", "polish_softly"},
        tags={"hall", "detergent"},
    ),
    "wash_cellar": Room(
        id="wash_cellar",
        label="wash cellar",
        phrase="the stone wash cellar under the stairs",
        mood="The stone walls breathed out cool air, and every drip sounded farther away than it should have.",
        detergent_spot="beside the deep stone sink",
        clue="a cracked tin had dripped bubbles toward the drain",
        supports={"press_flat", "rinse_gently", "polish_softly"},
        tags={"cellar", "detergent"},
    ),
}

KEEPSAKES = {
    "clipping": Keepsake(
        id="clipping",
        label="news clipping",
        phrase="a yellowed news clipping",
        material="paper",
        memory="an old newspaper piece about the day the house won the village garden ribbon",
        ghost_goal="keep the paper from melting into blue soap",
        damage_text="the paper edges were curling from damp suds",
        fixed_text="the paper lay smooth again beneath a heavy book",
        tags={"news", "paper"},
    ),
    "scarf": Keepsake(
        id="scarf",
        label="ribbon scarf",
        phrase="a little ribbon scarf",
        material="fabric",
        memory="the tiny scarf the cat had once worn when it slept on Grandma's lap",
        ghost_goal="keep the scarf from smelling sharp with detergent",
        damage_text="the ribbon scarf was streaked with soap and going stiff",
        fixed_text="the scarf hung clean and soft over a chair back",
        tags={"fabric", "cat"},
    ),
    "bell": Keepsake(
        id="bell",
        label="bell collar",
        phrase="a small bell collar",
        material="metal",
        memory="the old bell collar that used to tinkle whenever the cat ran for supper",
        ghost_goal="keep the brass from turning crusty with spilled soap",
        damage_text="white soap crust was gathering in the little bell",
        fixed_text="the brass bell collar gave one shy, bright chime",
        tags={"metal", "cat"},
    ),
}

REPAIRS = {
    "press_flat": Repair(
        id="press_flat",
        label="press it flat",
        needs={"press_flat"},
        materials={"paper"},
        action="slid clean towels under the damp paper, blotted it gently, and laid it beneath the thick family dictionary",
        result="The pages stopped curling, and the old print could breathe again.",
        qa_text="blotted the damp paper and pressed it flat under a heavy book",
        tags={"paper"},
    ),
    "rinse_gently": Repair(
        id="rinse_gently",
        label="rinse it gently",
        needs={"rinse_gently"},
        materials={"fabric"},
        action="carried the scarf to the sink, rinsed the soap away with cool water, and patted it dry in a towel",
        result="The cloth lost its sharp smell and turned soft again.",
        qa_text="rinsed the scarf gently in cool water and dried it with a towel",
        tags={"fabric", "sink"},
    ),
    "polish_softly": Repair(
        id="polish_softly",
        label="polish it softly",
        needs={"polish_softly"},
        materials={"metal"},
        action="wiped the bell with a soft cloth until the soap crust lifted away from the tiny clapper",
        result="A small gold shine came back to the metal.",
        qa_text="wiped the soap away and polished the bell with a soft cloth",
        tags={"metal"},
    ),
}

GIRL_NAMES = ["Mina", "Lucy", "Nora", "Ella", "Ruby", "Ava"]
BOY_NAMES = ["Theo", "Leo", "Ben", "Max", "Sam", "Finn"]
TRAITS = ["careful", "brave", "quiet", "curious", "gentle", "thoughtful"]
STORM_LEVELS = {
    "still": "Outside, the night was very still.",
    "rain": "Outside, rain tapped at the windows.",
    "wind": "Outside, the wind worried the branches against the eaves.",
}


def repair_fits(room: Room, keepsake: Keepsake, repair: Repair) -> bool:
    return keepsake.material in repair.materials and repair.needs.issubset(room.supports)


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for room_id, room in ROOMS.items():
        for keepsake_id, keepsake in KEEPSAKES.items():
            for repair_id, repair in REPAIRS.items():
                if repair_fits(room, keepsake, repair):
                    combos.append((room_id, keepsake_id, repair_id))
    return combos


def predict_damage(world: World) -> dict:
    sim = world.copy()
    sim.get("detergent").meters["spilled"] += 1
    propagate(sim, narrate=False)
    keepsake = sim.get("keepsake")
    return {
        "sudsy": keepsake.meters["sudsy"] >= THRESHOLD,
        "threatened": keepsake.meters["threatened"] >= THRESHOLD,
    }


def introduce(world: World, child: Entity, parent: Entity, room: Room, storm_text: str) -> None:
    world.say(
        f"That evening, {child.id} received unsettling news: {child.pronoun('possessive')} {parent.label_word} said that strangers would come tomorrow to look through the old house."
    )
    world.say(
        f"{child.id} did not want anything precious to be thrown away by mistake. {storm_text}"
    )
    world.say(
        f"When a soft rustle drifted from {room.phrase}, {child.id} took a candle-shaped flashlight and went to listen."
    )
    world.say(room.mood)


def encounter(world: World, child: Entity, ghost: Entity, keepsake: Entity, room: Room) -> None:
    child.memes["fear"] += 1
    ghost.memes["protective"] += 1
    world.say(
        f"Near the detergent {room.detergent_spot}, {child.id} saw {keepsake.phrase or keepsake.label} on the floor and a thin silver whisker floating where no living cat stood."
    )
    world.say(
        f"Then the rest of the cat ghost appeared: pale paws, bright eyes, and a tail like smoke."
    )


def spill_and_accuse(world: World, child: Entity, ghost: Entity, keepsake: Entity) -> None:
    world.get("detergent").meters["spilled"] += 1
    propagate(world, narrate=True)
    child.memes["accused"] += 1
    world.say(
        f'"Oh no," {child.id} whispered. "{keepsake.label.capitalize()}! Did you do this?"'
    )
    propagate(world, narrate=True)
    ghost.memes["sad"] += 1


def inspect_clue(world: World, child: Entity, room: Room, keepsake_cfg: Keepsake) -> None:
    child.memes["curiosity"] += 1
    child.memes["fear"] = 0.0
    world.say(
        f"But when {child.id} knelt down, {child.pronoun()} noticed something else: {room.clue}."
    )
    world.say(
        f"The ghost cat had not dragged the detergent toward the keepsake at all. It had tugged {keepsake_cfg.label} away from the worst of the spill, trying to {keepsake_cfg.ghost_goal}."
    )
    world.facts["realized_truth"] = True


def apologize_and_repair(world: World, child: Entity, ghost: Entity, repair: Repair, keepsake_cfg: Keepsake) -> None:
    child.memes["apology"] += 1
    world.say(
        f'{child.id} put a hand over {child.pronoun("possessive")} heart. "I was wrong," {child.pronoun()} said softly. "You were helping. I am sorry."'
    )
    world.say(
        f"Very carefully, {child.pronoun()} {repair.action} {repair.result}"
    )
    world.get("keepsake").meters["repaired"] += 1
    child.memes["repair_done"] += 1
    propagate(world, narrate=True)
    world.say(
        f"Beside {child.id}, the cat ghost lowered its head until one cool whisker brushed the back of {child.pronoun('possessive')} hand."
    )
    world.facts["repair_text"] = repair.qa_text
    world.facts["keepsake_fixed_text"] = keepsake_cfg.fixed_text


def ending(world: World, child: Entity, parent: Entity, keepsake_cfg: Keepsake) -> None:
    world.say(
        f"When {child.id}'s {parent.label_word} came looking, {child.id} showed {parent.pronoun('object')} the saved keepsake and told the true story."
    )
    world.say(
        f"{parent.pronoun().capitalize()} did not laugh at the ghost. {parent.pronoun().capitalize()} only said that old love can linger in a house just as long as old dust can."
    )
    world.say(
        f"By bedtime, {keepsake_cfg.fixed_text}, and the cat ghost was curled nearby, no longer guarding it alone."
    )


def tell(
    room: Room,
    keepsake_cfg: Keepsake,
    repair: Repair,
    child_name: str,
    child_gender: str,
    parent_type: str,
    trait: str,
    storm_level: str,
) -> World:
    world = World()
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        label=child_name,
        role="child",
        attrs={"trait": trait},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))
    ghost = world.add(Entity(
        id="ghost",
        kind="character",
        type="cat_ghost",
        label="the cat ghost",
        phrase="the cat ghost",
        role="ghost",
    ))
    keepsake = world.add(Entity(
        id="keepsake",
        kind="thing",
        type=keepsake_cfg.material,
        label=keepsake_cfg.label,
        phrase=keepsake_cfg.phrase,
        attrs={"memory": keepsake_cfg.memory},
        tags=set(keepsake_cfg.tags),
    ))
    detergent = world.add(Entity(
        id="detergent",
        kind="thing",
        type="detergent",
        label="detergent",
        phrase="the detergent box",
        tags={"detergent"},
    ))

    introduce(world, child, parent, room, STORM_LEVELS[storm_level])
    world.para()
    encounter(world, child, ghost, keepsake, room)
    world.say(f"{keepsake_cfg.damage_text.capitalize()}.")
    spill_and_accuse(world, child, ghost, keepsake)
    world.para()
    inspect_clue(world, child, room, keepsake_cfg)
    apologize_and_repair(world, child, ghost, repair, keepsake_cfg)
    world.para()
    ending(world, child, parent, keepsake_cfg)

    world.facts.update(
        room=room,
        keepsake_cfg=keepsake_cfg,
        repair=repair,
        child=child,
        parent=parent,
        ghost=ghost,
        keepsake=keepsake,
        detergent=detergent,
        storm_level=storm_level,
        reconciled=ghost.memes["peace"] >= THRESHOLD,
        misjudged=child.memes["accused"] >= THRESHOLD,
        saved=keepsake.meters["saved"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "news": [
        (
            "What is news?",
            "News is information about something that has happened or is going to happen. People share news to help others know what is changing."
        )
    ],
    "whisker": [
        (
            "What is a whisker?",
            "A whisker is a stiff hair that grows on an animal's face, especially on a cat. Cats use whiskers to help feel where things are around them."
        )
    ],
    "detergent": [
        (
            "What is detergent?",
            "Detergent is soap used for washing clothes or cleaning things. It helps lift dirt away, but it can still make a mess if it spills."
        )
    ],
    "paper": [
        (
            "Why should wet paper be dried carefully?",
            "Wet paper tears easily and can wrinkle when it dries. Blotting it gently and pressing it flat helps save it."
        )
    ],
    "fabric": [
        (
            "Why do you rinse soap out of cloth?",
            "Soap left in cloth can make it stiff and sticky. Rinsing with clean water helps the cloth feel soft again."
        )
    ],
    "metal": [
        (
            "Why should metal be wiped dry after soap gets on it?",
            "Soap can leave a crusty film on metal. Wiping it clean and dry helps the surface stay bright."
        )
    ],
    "ghost": [
        (
            "What makes a ghost story gentle instead of scary?",
            "A gentle ghost story has mystery and shivers, but it does not end in harm. The ghost usually wants something kind, sad, or loving."
        )
    ],
    "apology": [
        (
            "Why is an apology important after a misunderstanding?",
            "An apology shows that you know you hurt someone and want to make things better. It can open the door for trust to return."
        )
    ],
}
KNOWLEDGE_ORDER = ["news", "whisker", "detergent", "paper", "fabric", "metal", "ghost", "apology"]


def generation_prompts(world: World) -> list[str]:
    child = world.facts["child"]
    room = world.facts["room"]
    keepsake = world.facts["keepsake_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "news," "whisker," and "detergent."',
        f"Tell a ghost story where {child.id} hears troubling news, follows a mysterious whisker into {room.label}, and discovers that a cat ghost is trying to protect {keepsake.phrase}.",
        "Write a reconciliation story with a haunted misunderstanding: a child blames a ghost for a mess, learns the truth, apologizes, and ends in peace.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    room = f["room"]
    keepsake = f["keepsake_cfg"]
    repair = f["repair"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, a child in an old house, and a cat ghost keeping watch in the {room.label}. The story is also about the keepsake they both learn to care for."
        ),
        (
            "What unsettling news did the child hear at the beginning?",
            f"{child.id} heard that strangers would come the next day to look through the old house. That news made {child.pronoun('object')} worry that something precious might be lost."
        ),
        (
            f"What did {child.id} see near the detergent?",
            f"{child.id} saw {keepsake.phrase} on the floor, a silver whisker in the air, and then the shape of a cat ghost. The sight felt spooky because the detergent had spilled close to the keepsake."
        ),
        (
            f"Why did {child.id} think the ghost had done something wrong?",
            f"{child.id} first saw the mess before seeing the clue. Because the keepsake was wet with detergent, {child.pronoun()} wrongly guessed the ghost had caused the trouble."
        ),
    ]
    if f.get("realized_truth"):
        qa.append(
            (
                f"What truth did {child.id} discover?",
                f"{child.id} discovered that the detergent had leaked on its own from the broken shelf or tipped crate, depending on the room. The cat ghost had actually pulled the keepsake away to save it."
            )
        )
    if f.get("saved"):
        qa.append(
            (
                f"How did {child.id} make peace with the cat ghost?",
                f"{child.id} apologized for the unfair accusation and then {repair.qa_text}. That careful repair proved the apology was real, so the ghost stopped hiding and trusted {child.pronoun('object')} again."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully: the keepsake was safe, the misunderstanding was over, and the cat ghost no longer had to guard it alone. The ending image shows a haunted room becoming warm instead of lonely."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"news", "whisker", "detergent", "ghost", "apology"}
    material = world.facts["keepsake_cfg"].material
    tags.add(material)
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
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        room="laundry",
        keepsake="clipping",
        repair="press_flat",
        child_name="Mina",
        child_gender="girl",
        parent="mother",
        trait="careful",
        storm_level="rain",
    ),
    StoryParams(
        room="wash_cellar",
        keepsake="scarf",
        repair="rinse_gently",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="gentle",
        storm_level="wind",
    ),
    StoryParams(
        room="back_hall",
        keepsake="bell",
        repair="polish_softly",
        child_name="Lucy",
        child_gender="girl",
        parent="mother",
        trait="quiet",
        storm_level="still",
    ),
]


def explain_rejection(room: Room, keepsake: Keepsake, repair: Repair) -> str:
    if keepsake.material not in repair.materials:
        return (
            f"(No story: '{repair.id}' is not the right kind of repair for {keepsake.phrase}. "
            f"A {keepsake.material} keepsake needs a repair that fits its material.)"
        )
    return (
        f"(No story: the {room.label} does not support '{repair.id}'. "
        f"The fix must be available in the room where the haunting happens.)"
    )


ASP_RULES = r"""
fits_material(K, Rp) :- keepsake(K), repair(Rp), material_of(K, M), repair_for(Rp, M).
fits_room(Rm, Rp) :- room(Rm), repair(Rp), room_supports(Rm, Rp).
valid(Rm, K, Rp) :- room(Rm), keepsake(K), repair(Rp), fits_material(K, Rp), fits_room(Rm, Rp).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for room_id, room in ROOMS.items():
        lines.append(asp.fact("room", room_id))
        for support in sorted(room.supports):
            lines.append(asp.fact("room_supports", room_id, support))
    for keepsake_id, keepsake in KEEPSAKES.items():
        lines.append(asp.fact("keepsake", keepsake_id))
        lines.append(asp.fact("material_of", keepsake_id, keepsake.material))
    for repair_id, repair in REPAIRS.items():
        lines.append(asp.fact("repair", repair_id))
        for material in sorted(repair.materials):
            lines.append(asp.fact("repair_for", repair_id, material))
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
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("smoke test generated an empty story")
        print("OK: smoke test story generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    for seed in range(10):
        rng = random.Random(seed)
        try:
            params = resolve_params(build_parser().parse_args([]), rng)
            params.seed = seed
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("random smoke test generated an empty story")
        except Exception as err:
            rc = 1
            print(f"RANDOM GENERATION FAILED at seed {seed}: {err}")
            break

    if rc == 0:
        print("OK: random generation smoke tests passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a child, a ghost cat, spilled detergent, and reconciliation."
    )
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--keepsake", choices=KEEPSAKES)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--storm-level", choices=sorted(STORM_LEVELS))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (room, keepsake, repair) combos from ASP")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.keepsake and args.repair:
        room = ROOMS[args.room]
        keepsake = KEEPSAKES[args.keepsake]
        repair = REPAIRS[args.repair]
        if not repair_fits(room, keepsake, repair):
            raise StoryError(explain_rejection(room, keepsake, repair))

    combos = [
        combo for combo in valid_combos()
        if (args.room is None or combo[0] == args.room)
        and (args.keepsake is None or combo[1] == args.keepsake)
        and (args.repair is None or combo[2] == args.repair)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    room_id, keepsake_id, repair_id = rng.choice(sorted(combos))
    child_name, child_gender = pick_child(rng)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    storm_level = args.storm_level or rng.choice(sorted(STORM_LEVELS))
    return StoryParams(
        room=room_id,
        keepsake=keepsake_id,
        repair=repair_id,
        child_name=child_name,
        child_gender=child_gender,
        parent=parent,
        trait=trait,
        storm_level=storm_level,
    )


def generate(params: StoryParams) -> StorySample:
    if params.room not in ROOMS:
        raise StoryError(f"(Unknown room: {params.room})")
    if params.keepsake not in KEEPSAKES:
        raise StoryError(f"(Unknown keepsake: {params.keepsake})")
    if params.repair not in REPAIRS:
        raise StoryError(f"(Unknown repair: {params.repair})")
    room = ROOMS[params.room]
    keepsake = KEEPSAKES[params.keepsake]
    repair = REPAIRS[params.repair]
    if not repair_fits(room, keepsake, repair):
        raise StoryError(explain_rejection(room, keepsake, repair))

    world = tell(
        room=room,
        keepsake_cfg=keepsake,
        repair=repair,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        storm_level=params.storm_level,
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
        print(f"{len(combos)} valid (room, keepsake, repair) combos:\n")
        for room_id, keepsake_id, repair_id in combos:
            print(f"  {room_id:12} {keepsake_id:10} {repair_id}")
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
            p = sample.params
            header = f"### {p.child_name}: {p.keepsake} in {p.room} ({p.repair})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
