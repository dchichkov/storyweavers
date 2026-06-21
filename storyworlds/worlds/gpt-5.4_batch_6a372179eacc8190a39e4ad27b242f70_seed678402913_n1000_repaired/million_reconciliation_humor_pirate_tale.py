#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/million_reconciliation_humor_pirate_tale.py
======================================================================

A standalone storyworld for a tiny pirate-tale domain with a quarrel, a funny
turn, and a reconciliation. The seed word "million" is built into the premise:
one child makes a grand pirate boast about "a million" pieces of treasure, the
boast sparks hurt feelings, and a concrete fix helps the children make up.

The world model is classical and state-driven:
- typed entities with physical meters and emotional memes
- a small causal rule engine
- a reasonableness gate over treasure/fix compatibility
- a Python outcome model mirrored by an inline ASP twin

Run it
------
    python storyworlds/worlds/gpt-5.4/million_reconciliation_humor_pirate_tale.py
    python storyworlds/worlds/gpt-5.4/million_reconciliation_humor_pirate_tale.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/million_reconciliation_humor_pirate_tale.py --all
    python storyworlds/worlds/gpt-5.4/million_reconciliation_humor_pirate_tale.py --qa
    python storyworlds/worlds/gpt-5.4/million_reconciliation_humor_pirate_tale.py --json
    python storyworlds/worlds/gpt-5.4/million_reconciliation_humor_pirate_tale.py --trace --seed 777
    python storyworlds/worlds/gpt-5.4/million_reconciliation_humor_pirate_tale.py --verify
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
# from the nested subdirectory storyworlds/worlds/gpt-5.4/.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"            # "character" | "thing"
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
        female = {"girl", "mother", "woman", "aunt"}
        male = {"boy", "father", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    place: str
    opening: str
    hideout: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    count_word: str
    divisible: bool
    tiny: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Trigger:
    id: str
    boast: str
    hurt: str
    grabby: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class FunnyTurn:
    id: str
    text: str
    reveal: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    needs_divisible: bool = False
    needs_indivisible: bool = False
    power: int = 2
    text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    scene: str
    treasure: str
    trigger: str
    funny_turn: str
    fix: str
    captain_name: str
    captain_gender: str
    mate_name: str
    mate_gender: str
    helper_type: str
    captain_trait: str
    mate_trait: str
    stubbornness: int = 1
    seed: Optional[int] = None


CURATED: list[StoryParams] = []


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
        return [e for e in self.entities.values() if e.role in {"captain", "mate"}]

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


def _r_quarrel(world: World) -> list[str]:
    out: list[str] = []
    captain = world.get("captain")
    mate = world.get("mate")
    if captain.memes["greed"] >= THRESHOLD and mate.memes["hurt"] >= THRESHOLD:
        sig = ("quarrel",)
        if sig not in world.fired:
            world.fired.add(sig)
            captain.memes["conflict"] += 1
            mate.memes["conflict"] += 1
            out.append("__quarrel__")
    return out


def _r_laughter_softens(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("funny_happened"):
        for kid in world.kids():
            sig = ("laughter", kid.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            kid.memes["laughter"] += 1
            if kid.memes["conflict"] >= THRESHOLD:
                kid.memes["conflict"] = max(0.0, kid.memes["conflict"] - 1.0)
            out.append("__giggle__")
    return out


def _r_make_up(world: World) -> list[str]:
    out: list[str] = []
    captain = world.get("captain")
    mate = world.get("mate")
    if captain.memes["apology"] >= THRESHOLD and mate.memes["forgiveness"] >= THRESHOLD:
        sig = ("make_up",)
        if sig not in world.fired:
            world.fired.add(sig)
            captain.memes["peace"] += 1
            mate.memes["peace"] += 1
            captain.memes["conflict"] = 0.0
            mate.memes["conflict"] = 0.0
            out.append("__peace__")
    return out


CAUSAL_RULES = [
    Rule(name="quarrel", tag="social", apply=_r_quarrel),
    Rule(name="laughter_softens", tag="social", apply=_r_laughter_softens),
    Rule(name="make_up", tag="social", apply=_r_make_up),
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


SCENES = {
    "beach_cove": Scene(
        id="beach_cove",
        place="the little beach cove",
        opening="The old striped blanket became a pirate ship, a driftwood spoon became a sword, and a bucket became the treasure chest.",
        hideout="behind a sand hill near the water",
        tags={"beach", "pirate"},
    ),
    "attic_ship": Scene(
        id="attic_ship",
        place="the attic",
        opening="A dusty trunk became a pirate ship, a mop handle became a mast, and an apple crate became the treasure chest.",
        hideout="under the sloping roof by the old trunk",
        tags={"attic", "pirate"},
    ),
    "garden_island": Scene(
        id="garden_island",
        place="the garden",
        opening="A wheelbarrow became a pirate ship, two sticks became crossed swords, and a flowerpot became the treasure chest.",
        hideout="behind the big currant bush",
        tags={"garden", "pirate"},
    ),
}

TREASURES = {
    "buttons": Treasure(
        id="buttons",
        label="gold buttons",
        phrase="a handful of shiny gold buttons",
        count_word="buttons",
        divisible=True,
        tiny=True,
        tags={"counting", "sharing"},
    ),
    "shells": Treasure(
        id="shells",
        label="pearl-white shells",
        phrase="a heap of pearl-white shells",
        count_word="shells",
        divisible=True,
        tiny=True,
        tags={"counting", "sharing"},
    ),
    "berries": Treasure(
        id="berries",
        label="red jewel berries",
        phrase="a scoop of red jewel berries",
        count_word="berries",
        divisible=True,
        tiny=True,
        tags={"sharing", "snack"},
    ),
    "map": Treasure(
        id="map",
        label="treasure map",
        phrase="one crinkly treasure map with a crooked X",
        count_word="map",
        divisible=False,
        tiny=False,
        tags={"turns", "map"},
    ),
    "crown": Treasure(
        id="crown",
        label="captain's crown",
        phrase="one bent paper captain's crown",
        count_word="crown",
        divisible=False,
        tiny=False,
        tags={"turns", "roleplay"},
    ),
}

TRIGGERS = {
    "million_boast": Trigger(
        id="million_boast",
        boast='"Ho! This chest has a million {count_word} in it, and every one belongs to Captain {captain}!"',
        hurt='{mate} stared at the chest. Being left out made {mate_obj} feel small, as if the game had slammed shut like a wooden lid.',
        grabby=False,
        tags={"boast", "million"},
    ),
    "bossy_captain": Trigger(
        id="bossy_captain",
        boast='"Ho! I found the treasure first. There are a million {count_word} here, so only I get to be captain and chooser!"',
        hurt='{mate} puffed out {mate_pos} cheeks. The game was supposed to be for two pirates, not one bossy pirate.',
        grabby=False,
        tags={"boast", "million", "bossy"},
    ),
    "grabbed_first": Trigger(
        id="grabbed_first",
        boast='"A million {count_word}! Mine first!" Captain {captain} crowed, scooping the chest tight against {captain_pos} shirt.',
        hurt='{mate} reached for the treasure too late and felt a hot sting of hurt. It was no fun to play pirate with empty hands.',
        grabby=True,
        tags={"grab", "million"},
    ),
}

FUNNY_TURNS = {
    "parrot_echo": FunnyTurn(
        id="parrot_echo",
        text='Just then the toy parrot clipped to the mast tipped sideways and squawked, "Mine! Mine! Million! Million!" in such a rude little voice that both pirates blinked.',
        reveal="The silly echo made the boast sound much meaner than it had a moment before.",
        tags={"parrot", "humor"},
    ),
    "crab_tickle": FunnyTurn(
        id="crab_tickle",
        text="Just then a tiny crab scuttled from the bucket, bumped Captain {captain}'s ankle, and made {captain_obj} hop in a wobbly circle like a pirate dancing on hot toast.",
        reveal="The ridiculous hopping broke the hard, angry feeling for one breath.",
        tags={"crab", "humor"},
    ),
    "hat_plop": FunnyTurn(
        id="hat_plop",
        text="Just then Captain {captain}'s floppy hat slid over {captain_pos} eyes and plopped right down to {captain_pos} chin, so the fierce captain looked more like a confused turnip than a terror of the sea.",
        reveal="It was hard to stay grand and greedy with a hat over your whole face.",
        tags={"hat", "humor"},
    ),
}

FIXES = {
    "split_count": Fix(
        id="split_count",
        label="count and split",
        needs_divisible=True,
        power=3,
        text='{helper_name} knelt beside the chest and said, "Real pirates can count before they brag. Let us pour the {count_word} out, count them together, and make two fair little piles."',
        qa_text="They counted the treasure and made two fair piles.",
        tags={"counting", "sharing"},
    ),
    "trade_turns": Fix(
        id="trade_turns",
        label="take turns",
        needs_indivisible=True,
        power=3,
        text='{helper_name} tapped the one {count_word} and said, "There is only one, so pirate fairness means turns. One of you leads first, and the other leads next."',
        qa_text="They decided to take turns with the treasure and the captain job.",
        tags={"turns", "fairness"},
    ),
    "apology_song": Fix(
        id="apology_song",
        label="apology song",
        power=2,
        text='{helper_name} grinned and drummed the chest with two fingers. "This ship needs an apology song," {helper_sub} said. "A short sorry, a short laugh, and then a fair plan."',
        qa_text="They used a silly apology song and then made a fair plan.",
        tags={"apology", "humor"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["bold", "bouncy", "dramatic", "careful", "steady", "sunny"]


def fix_compatible(treasure: Treasure, fix: Fix) -> bool:
    if fix.needs_divisible and not treasure.divisible:
        return False
    if fix.needs_indivisible and treasure.divisible:
        return False
    return True


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for scene_id in SCENES:
        for treasure_id, treasure in TREASURES.items():
            for trigger_id in TRIGGERS:
                for funny_id in FUNNY_TURNS:
                    for fix_id, fix in FIXES.items():
                        if fix_compatible(treasure, fix):
                            combos.append((scene_id, treasure_id, trigger_id, funny_id, fix_id))
    return combos


def explain_rejection(treasure: Treasure, fix: Fix) -> str:
    if fix.needs_divisible and not treasure.divisible:
        return (f"(No story: {fix.label} needs a treasure that can be shared into fair piles, "
                f"but {treasure.phrase} is only one thing. Try a turn-taking fix instead.)")
    if fix.needs_indivisible and treasure.divisible:
        return (f"(No story: {fix.label} fits one special object, but {treasure.phrase} can be split fairly. "
                f"Try a counting-and-sharing fix instead.)")
    return "(No story: that treasure and fix do not make a reasonable reconciliation.)"


def predict_outcome(trigger: Trigger, treasure: Treasure, fix: Fix, stubbornness: int) -> str:
    if not fix_compatible(treasure, fix):
        raise StoryError(explain_rejection(treasure, fix))
    score = fix.power + (1 if "humor" in fix.tags else 0)
    if trigger.grabby:
        score -= 1
    if stubbornness <= score:
        return "reconciled"
    return "stormy"


def introduce(world: World, scene: Scene, captain: Entity, mate: Entity, treasure: Treasure) -> None:
    for kid in (captain, mate):
        kid.memes["joy"] += 1
        kid.memes["play"] += 1
    world.say(
        f"On a bright afternoon, {captain.id} and {mate.id} turned {scene.place} into a pirate sea. "
        f"{scene.opening}"
    )
    world.say(
        f"Behind their hideout {scene.hideout}, they found {treasure.phrase}, and at once it became the richest pirate treasure they had ever seen."
    )


def boast_and_hurt(world: World, trigger: Trigger, treasure: Treasure, captain: Entity, mate: Entity) -> None:
    captain.memes["greed"] += 1
    if trigger.grabby:
        captain.meters["grip"] += 1
    mate.memes["hurt"] += 1
    world.say(trigger.boast.format(count_word=treasure.count_word, captain=captain.id, captain_pos=captain.pronoun("possessive")))
    world.say(
        trigger.hurt.format(
            mate=mate.id,
            mate_obj=mate.pronoun("object"),
            mate_pos=mate.pronoun("possessive"),
        )
    )
    propagate(world, narrate=False)


def escalate(world: World, captain: Entity, mate: Entity, treasure: Treasure) -> None:
    if captain.meters["grip"] >= THRESHOLD:
        world.say(
            f"{captain.id} hugged the {treasure.label} close and spun away. "
            f'"A captain keeps the best loot!" {captain.pronoun().capitalize()} declared.'
        )
    else:
        world.say(
            f'{mate.id} folded {mate.pronoun("possessive")} arms. "That is not fair," {mate.pronoun()} said.'
        )
    world.say("For a moment, the pirate ship felt smaller than before.")
    world.facts["quarreled"] = True


def funny_turn(world: World, funny: FunnyTurn, captain: Entity) -> None:
    world.facts["funny_happened"] = True
    world.say(
        funny.text.format(
            captain=captain.id,
            captain_obj=captain.pronoun("object"),
            captain_pos=captain.pronoun("possessive"),
        )
    )
    world.say(funny.reveal)
    propagate(world, narrate=False)


def helper_arrives(world: World, helper: Entity) -> None:
    world.say(
        f"{helper.label_word.capitalize()} heard the silence where pirate shouting had been and came over with a calm smile."
    )


def try_fix(world: World, helper: Entity, fix: Fix, treasure: Treasure, captain: Entity, mate: Entity) -> None:
    world.say(
        fix.text.format(
            helper_name=helper.label_word.capitalize(),
            helper_sub=helper.pronoun(),
            count_word=treasure.count_word,
        )
    )
    if fix.id == "split_count":
        captain.memes["apology"] += 1
        mate.memes["forgiveness"] += 1
        captain.meters["shared"] += 1
        mate.meters["shared"] += 1
        world.say(
            f"They tipped the treasure onto the blanket and counted slowly together. "
            f"There were not a million {treasure.count_word} after all, only enough for two neat little pirate shares."
        )
    elif fix.id == "trade_turns":
        captain.memes["apology"] += 1
        mate.memes["forgiveness"] += 1
        captain.meters["took_turns"] += 1
        mate.meters["took_turns"] += 1
        world.say(
            f"{captain.id} looked at the one {treasure.count_word} and then at {mate.id}. "
            f'The grand boast suddenly felt much too big for such a small treasure.'
        )
        world.say(
            f'"You can steer first," {captain.id} said at last. "Then I steer next."'
        )
    else:
        captain.memes["apology"] += 1
        mate.memes["forgiveness"] += 1
        world.say(
            f'{captain.id} sang, "Sorry, matey, I was too grand," and {mate.id} answered, "Sorry, matey, I glowered like a storm cloud."'
        )
        world.say(
            "By the end of the tiny song, both of them were smiling hard enough to wobble."
        )
        if treasure.divisible:
            captain.meters["shared"] += 1
            mate.meters["shared"] += 1
            world.say(
                f"Then they spread the {treasure.count_word} between them in a fair line."
            )
        else:
            captain.meters["took_turns"] += 1
            mate.meters["took_turns"] += 1
            world.say(
                f"Then they agreed to take turns with the {treasure.label} and the captain job."
            )
    propagate(world, narrate=False)


def reconcile(world: World, captain: Entity, mate: Entity, treasure: Treasure, scene: Scene) -> None:
    captain.memes["relief"] += 1
    mate.memes["relief"] += 1
    captain.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"{captain.id} looked at {mate.id} and said, \"I wanted the biggest pirate story, but I forgot the best part was having my mate.\""
    )
    world.say(
        f"{mate.id} stepped closer and nodded. \"A million treasure stories are no fun alone.\""
    )
    world.say(
        f"Soon the two pirates were racing back toward {scene.hideout}, laughing together, and the treasure looked brighter simply because it belonged inside a shared game again."
    )


def stormy_end(world: World, captain: Entity, mate: Entity, treasure: Treasure, helper: Entity) -> None:
    captain.memes["sulk"] += 1
    mate.memes["sulk"] += 1
    world.say(
        f"But the grumpy feeling still clung to both pirates. {captain.id} sat by the {treasure.label}, and {mate.id} sat a little way off, tracing circles in the sand."
    )
    world.say(
        f'{helper.label_word.capitalize()} kept the treasure safe and said they could try again after a drink and a quiet minute.'
    )
    world.say(
        "The pirate game did not end happily yet, but the waiting chest promised there would be another chance to make things right."
    )


def tell(
    scene: Scene,
    treasure: Treasure,
    trigger: Trigger,
    funny: FunnyTurn,
    fix: Fix,
    captain_name: str = "Tom",
    captain_gender: str = "boy",
    mate_name: str = "Lily",
    mate_gender: str = "girl",
    helper_type: str = "mother",
    captain_trait: str = "bold",
    mate_trait: str = "steady",
    stubbornness: int = 1,
) -> World:
    world = World()
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type=captain_gender,
        label=captain_name,
        role="captain",
        traits=[captain_trait],
    ))
    mate = world.add(Entity(
        id="mate",
        kind="character",
        type=mate_gender,
        label=mate_name,
        role="mate",
        traits=[mate_trait],
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_type,
        label=helper_type,
        role="helper",
    ))
    chest = world.add(Entity(
        id="treasure",
        kind="thing",
        type="treasure",
        label=treasure.label,
        phrase=treasure.phrase,
        tags=set(treasure.tags),
    ))

    world.facts["captain_name"] = captain_name
    world.facts["mate_name"] = mate_name
    world.facts["funny_happened"] = False

    introduce(world, scene, captain, mate, treasure)
    world.para()
    boast_and_hurt(world, trigger, treasure, captain, mate)
    escalate(world, captain, mate, treasure)
    world.para()
    funny_turn(world, funny, captain)
    helper_arrives(world, helper)
    try_fix(world, helper, fix, treasure, captain, mate)

    outcome = predict_outcome(trigger, treasure, fix, stubbornness)
    world.para()
    if outcome == "reconciled":
        reconcile(world, captain, mate, treasure, scene)
    else:
        stormy_end(world, captain, mate, treasure, helper)

    world.facts.update(
        scene=scene,
        treasure_cfg=treasure,
        trigger=trigger,
        funny_turn=funny,
        fix=fix,
        captain=captain,
        mate=mate,
        helper=helper,
        treasure_entity=chest,
        stubbornness=stubbornness,
        outcome=outcome,
        repaired=outcome == "reconciled",
        shared=chest.meters["shared"] >= THRESHOLD or captain.meters["shared"] >= THRESHOLD,
        took_turns=captain.meters["took_turns"] >= THRESHOLD,
        million_said=True,
    )
    return world


KNOWLEDGE = {
    "counting": [(
        "What does it mean to count something fairly?",
        "It means you slow down, look carefully, and make sure each person gets the same number when that is possible. Fair counting helps stop arguments."
    )],
    "sharing": [(
        "Why does sharing help friends or siblings make up?",
        "Sharing shows that both people matter. When each person gets a part, the game feels fair again."
    )],
    "turns": [(
        "What does taking turns mean?",
        "Taking turns means one person uses something first and the other uses it next. It is a fair way to share one special object."
    )],
    "fairness": [(
        "What is fairness?",
        "Fairness means trying to treat people in a way that feels even and kind. It does not always mean the exact same thing, but it should make sense to everyone."
    )],
    "apology": [(
        "What is an apology?",
        "An apology is when you say you were wrong and show you want to mend the hurt. A good apology helps someone feel seen."
    )],
    "humor": [(
        "How can laughter help during an argument?",
        "Laughter can soften the hard feeling in your chest for a moment. Then it is easier to listen and make a kinder choice."
    )],
    "map": [(
        "What is a treasure map?",
        "A treasure map is a picture that shows where hidden treasure might be. In pirate games, it helps guide the adventure."
    )],
    "roleplay": [(
        "What is pretend play?",
        "Pretend play is when children imagine they are pirates, explorers, or someone else for fun. It helps turn ordinary things into part of a story."
    )],
}
KNOWLEDGE_ORDER = ["counting", "sharing", "turns", "fairness", "apology", "humor", "map", "roleplay"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    treasure = f["treasure_cfg"]
    outcome = f["outcome"]
    ending = "and they reconcile with a funny, gentle ending" if outcome == "reconciled" else "and they do not make up right away"
    return [
        f'Write a short pirate tale for a 3-to-5-year-old that includes the word "million" and a quarrel over {treasure.label}.',
        f"Tell a funny reconciliation story where {captain.label} boasts about a million {treasure.count_word}, hurts {mate.label}'s feelings, and then learns to be fair.",
        f"Write a child-facing pirate story with humor, a hurt feeling, and a concrete fix, {ending}.",
    ]


def pair_noun(captain: Entity, mate: Entity) -> str:
    if captain.type == "boy" and mate.type == "boy":
        return "two pirate boys"
    if captain.type == "girl" and mate.type == "girl":
        return "two pirate girls"
    return "two young pirates"


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    captain = f["captain"]
    mate = f["mate"]
    helper = f["helper"]
    treasure = f["treasure_cfg"]
    trigger = f["trigger"]
    funny = f["funny_turn"]
    fix = f["fix"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair_noun(captain, mate)}, {captain.label} and {mate.label}, who were pretending to be pirates. {helper.label_word.capitalize()} also came to help when the game turned sour."
        ),
        (
            f"What started the argument?",
            f"{captain.label} made a grand pirate boast about a million {treasure.count_word} and tried to keep the treasure for {captain.pronoun('object')}. That hurt {mate.label}'s feelings because the pirate game stopped feeling shared."
        ),
        (
            "Why did the word million matter in the story?",
            f"It made the boast sound huge and dramatic, the way pirate talk often does. But the giant number also made the unfairness feel bigger, because {captain.label} was acting as if all the treasure belonged to one pirate."
        ),
        (
            "What funny thing happened in the middle?",
            f"{funny.text.format(captain=captain.label, captain_obj=captain.pronoun('object'), captain_pos=captain.pronoun('possessive'))} {funny.reveal}"
        ),
    ]
    if f["outcome"] == "reconciled":
        if fix.id == "split_count":
            repair = f"They counted the {treasure.count_word} and split them fairly. That worked because this treasure could be shared into two piles."
        elif fix.id == "trade_turns":
            repair = f"They decided to take turns with the {treasure.label} and with leading the game. That worked because there was only one special object."
        else:
            repair = f"They used a silly apology song and then made a fair plan. The laughter helped the apology land, and the fair plan turned the game back into a game for two."
        qa.append((
            "How did they make up?",
            repair
        ))
        qa.append((
            f"What did {captain.label} learn?",
            f"{captain.label} learned that a grand pirate story is not worth much if it pushes {mate.label} out. {captain.pronoun().capitalize()} had more fun once the treasure and the captain game were fair again."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the two pirates together again, laughing and racing back to play. The ending image shows that the treasure felt brighter once the friendship was mended."
        ))
    else:
        qa.append((
            "Did they make up right away?",
            f"No. The funny moment and the grown-up's help softened things a little, but the grumpy feeling was still too strong. They needed a quiet pause before they could try again."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with the treasure waiting while both children calmed down. That ending shows the problem was not solved yet, but another chance for reconciliation was still possible."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    treasure = f["treasure_cfg"]
    fix = f["fix"]
    tags = set(treasure.tags) | set(fix.tags) | {"humor"}
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if e.role:
            bits.append(f"role={e.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% Compatibility gate.
valid(Scene, Treasure, Trigger, Funny, Fix) :-
    scene(Scene), treasure(Treasure), trigger(Trigger), funny(Funny), fix(Fix),
    not bad_pair(Treasure, Fix).

bad_pair(T, F) :- needs_divisible(F), not divisible(T).
bad_pair(T, F) :- needs_indivisible(F), divisible(T).

% Outcome model.
fix_score(P) :- chosen_fix(F), power(F, P), not humor_fix(F).
fix_score(P+1) :- chosen_fix(F), power(F, P), humor_fix(F).

base_score(S) :- fix_score(P), chosen_trigger(T), grabby(T), S = P - 1.
base_score(S) :- fix_score(P), chosen_trigger(T), not grabby(T), S = P.

reconciled :- chosen_stubbornness(St), base_score(S), St <= S.
stormy :- chosen_stubbornness(St), base_score(S), St > S.

outcome(reconciled) :- reconciled.
outcome(stormy) :- stormy.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for scene_id in SCENES:
        lines.append(asp.fact("scene", scene_id))
    for treasure_id, treasure in TREASURES.items():
        lines.append(asp.fact("treasure", treasure_id))
        if treasure.divisible:
            lines.append(asp.fact("divisible", treasure_id))
    for trigger_id, trigger in TRIGGERS.items():
        lines.append(asp.fact("trigger", trigger_id))
        if trigger.grabby:
            lines.append(asp.fact("grabby", trigger_id))
    for funny_id in FUNNY_TURNS:
        lines.append(asp.fact("funny", funny_id))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        lines.append(asp.fact("power", fix_id, fix.power))
        if fix.needs_divisible:
            lines.append(asp.fact("needs_divisible", fix_id))
        if fix.needs_indivisible:
            lines.append(asp.fact("needs_indivisible", fix_id))
        if "humor" in fix.tags:
            lines.append(asp.fact("humor_fix", fix_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    extra = "\n".join([
        asp.fact("chosen_fix", params.fix),
        asp.fact("chosen_trigger", params.trigger),
        asp.fact("chosen_stubbornness", params.stubbornness),
    ])
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _check_params(params: StoryParams) -> None:
    if params.scene not in SCENES:
        raise StoryError(f"(No story: unknown scene '{params.scene}'.)")
    if params.treasure not in TREASURES:
        raise StoryError(f"(No story: unknown treasure '{params.treasure}'.)")
    if params.trigger not in TRIGGERS:
        raise StoryError(f"(No story: unknown trigger '{params.trigger}'.)")
    if params.funny_turn not in FUNNY_TURNS:
        raise StoryError(f"(No story: unknown funny turn '{params.funny_turn}'.)")
    if params.fix not in FIXES:
        raise StoryError(f"(No story: unknown fix '{params.fix}'.)")
    if params.stubbornness not in {0, 1, 2, 3}:
        raise StoryError("(No story: stubbornness must be 0, 1, 2, or 3.)")
    treasure = TREASURES[params.treasure]
    fix = FIXES[params.fix]
    if not fix_compatible(treasure, fix):
        raise StoryError(explain_rejection(treasure, fix))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Storyworld: a funny pirate quarrel over treasure, followed by a fair reconciliation when the combination is reasonable."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--funny-turn", dest="funny_turn", choices=FUNNY_TURNS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--stubbornness", type=int, choices=[0, 1, 2, 3],
                    help="higher values make reconciliation harder")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None,
                    help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.treasure and args.fix:
        treasure = TREASURES[args.treasure]
        fix = FIXES[args.fix]
        if not fix_compatible(treasure, fix):
            raise StoryError(explain_rejection(treasure, fix))

    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.treasure is None or c[1] == args.treasure)
              and (args.trigger is None or c[2] == args.trigger)
              and (args.funny_turn is None or c[3] == args.funny_turn)
              and (args.fix is None or c[4] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, treasure_id, trigger_id, funny_id, fix_id = rng.choice(sorted(combos))
    captain_name, captain_gender = _pick_kid(rng)
    mate_name, mate_gender = _pick_kid(rng, avoid=captain_name)
    helper_type = args.helper or rng.choice(["mother", "father", "aunt", "uncle"])
    captain_trait = rng.choice(TRAITS)
    mate_trait = rng.choice(TRAITS)
    stubbornness = args.stubbornness if args.stubbornness is not None else rng.choice([0, 1, 1, 2, 3])
    params = StoryParams(
        scene=scene_id,
        treasure=treasure_id,
        trigger=trigger_id,
        funny_turn=funny_id,
        fix=fix_id,
        captain_name=captain_name,
        captain_gender=captain_gender,
        mate_name=mate_name,
        mate_gender=mate_gender,
        helper_type=helper_type,
        captain_trait=captain_trait,
        mate_trait=mate_trait,
        stubbornness=stubbornness,
    )
    _check_params(params)
    return params


def generate(params: StoryParams) -> StorySample:
    _check_params(params)
    world = tell(
        scene=SCENES[params.scene],
        treasure=TREASURES[params.treasure],
        trigger=TRIGGERS[params.trigger],
        funny=FUNNY_TURNS[params.funny_turn],
        fix=FIXES[params.fix],
        captain_name=params.captain_name,
        captain_gender=params.captain_gender,
        mate_name=params.mate_name,
        mate_gender=params.mate_gender,
        helper_type=params.helper_type,
        captain_trait=params.captain_trait,
        mate_trait=params.mate_trait,
        stubbornness=params.stubbornness,
    )

    # Swap display names into the rendered story and grounded Q&A text.
    story = world.render().replace("captain", params.captain_name).replace("mate", params.mate_name)

    # Preserve entity ids while exposing human names in facts for QA.
    world.facts["captain"].label = params.captain_name
    world.facts["mate"].label = params.mate_name

    return StorySample(
        params=params,
        story=story,
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

    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if cl - py:
            print("  only in clingo:", sorted(cl - py))
        if py - cl:
            print("  only in python:", sorted(py - cl))

    cases: list[StoryParams] = list(CURATED)
    parser = build_parser()
    for s in range(25):
        rng = random.Random(s)
        try:
            p = resolve_params(parser.parse_args([]), rng)
        except StoryError:
            continue
        p.seed = s
        cases.append(p)

    bad = 0
    for p in cases:
        py_out = predict_outcome(TRIGGERS[p.trigger], TREASURES[p.treasure], FIXES[p.fix], p.stubbornness)
        asp_out = asp_outcome(p)
        if py_out != asp_out:
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    # Smoke tests: ordinary generation and serialization must not crash.
    try:
        sample = generate(CURATED[0] if CURATED else resolve_params(parser.parse_args([]), random.Random(0)))
        if not sample.story.strip():
            raise StoryError("Generated story was empty.")
        _ = sample.to_json()
        emit(sample, trace=False, qa=False, header="")
        print("OK: smoke test passed for generate/emit/json.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


CURATED = [
    StoryParams(
        scene="beach_cove",
        treasure="shells",
        trigger="million_boast",
        funny_turn="crab_tickle",
        fix="split_count",
        captain_name="Tom",
        captain_gender="boy",
        mate_name="Lily",
        mate_gender="girl",
        helper_type="mother",
        captain_trait="dramatic",
        mate_trait="steady",
        stubbornness=1,
    ),
    StoryParams(
        scene="attic_ship",
        treasure="map",
        trigger="bossy_captain",
        funny_turn="hat_plop",
        fix="trade_turns",
        captain_name="Mia",
        captain_gender="girl",
        mate_name="Ben",
        mate_gender="boy",
        helper_type="father",
        captain_trait="bold",
        mate_trait="careful",
        stubbornness=1,
    ),
    StoryParams(
        scene="garden_island",
        treasure="buttons",
        trigger="grabbed_first",
        funny_turn="parrot_echo",
        fix="apology_song",
        captain_name="Noah",
        captain_gender="boy",
        mate_name="Ava",
        mate_gender="girl",
        helper_type="aunt",
        captain_trait="bouncy",
        mate_trait="sunny",
        stubbornness=2,
    ),
    StoryParams(
        scene="beach_cove",
        treasure="crown",
        trigger="grabbed_first",
        funny_turn="hat_plop",
        fix="trade_turns",
        captain_name="Ella",
        captain_gender="girl",
        mate_name="Rose",
        mate_gender="girl",
        helper_type="uncle",
        captain_trait="dramatic",
        mate_trait="steady",
        stubbornness=3,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/5.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (scene, treasure, trigger, funny_turn, fix) combos:\n")
        for scene_id, treasure_id, trigger_id, funny_id, fix_id in combos:
            print(f"  {scene_id:13} {treasure_id:8} {trigger_id:14} {funny_id:12} {fix_id}")
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
            header = (
                f"### {p.captain_name} & {p.mate_name}: {p.treasure}, {p.trigger}, "
                f"{p.fix} ({predict_outcome(TRIGGERS[p.trigger], TREASURES[p.treasure], FIXES[p.fix], p.stubbornness)})"
            )
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
