#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/garage_stomach_humor_whodunit.py
===========================================================

A standalone storyworld for a tiny humorous whodunit: two children hear a
mysterious growl in the garage and start a detective case. They inspect the
most plausible suspect in the room, gather clues, and discover that the "culprit"
is not a monster or machine at all, but a hungry child's rumbling stomach.

The world is deliberately small and constraint-checked:

* The setting is always a garage, but different kinds of garage play change
  which suspect is plausible and what clues are available.
* A suspect must actually fit the garage setup, or the story is refused.
* A snack must be substantial enough to settle a hungry stomach, or the world
  rejects it as a weak fix.
* The story renders from simulated state and trace facts rather than swapping
  nouns into one frozen paragraph.

Run it
------
    python storyworlds/worlds/gpt-5.4/garage_stomach_humor_whodunit.py
    python storyworlds/worlds/gpt-5.4/garage_stomach_humor_whodunit.py --setup rainy_day --suspect toolbox
    python storyworlds/worlds/gpt-5.4/garage_stomach_humor_whodunit.py --suspect snowman
    python storyworlds/worlds/gpt-5.4/garage_stomach_humor_whodunit.py --snack lollipop
    python storyworlds/worlds/gpt-5.4/garage_stomach_humor_whodunit.py --all
    python storyworlds/worlds/gpt-5.4/garage_stomach_humor_whodunit.py --qa --json
    python storyworlds/worlds/gpt-5.4/garage_stomach_humor_whodunit.py --verify
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
FILLING_MIN = 2


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
class Setup:
    id: str
    opening: str
    props: str
    mission: str
    weather_line: str
    clue_style: str
    suspects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    place: str
    clue: str
    innocent_reason: str
    plausible_in: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    smell: str
    filling: int = 2
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


def _r_hunger_noise(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.role != "hungry_child":
            continue
        if ent.meters["hunger"] < THRESHOLD:
            continue
        sig = ("stomach_noise", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["stomach_noise"] += 1
        world.facts["real_culprit"] = ent.id
        world.facts["sound_origin"] = "stomach"
        out.append("__growl__")
    return out


def _r_noise_spooks(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("sound_origin") != "stomach":
        return out
    detective = world.entities.get("detective")
    hungry = world.entities.get("hungry")
    if detective is None or hungry is None:
        return out
    sig = ("spooked", detective.id, hungry.id)
    if sig in world.fired:
        return out
    if hungry.meters["stomach_noise"] < THRESHOLD:
        return out
    world.fired.add(sig)
    detective.memes["curiosity"] += 1
    hungry.memes["embarrassment"] += 1
    out.append("__mystery__")
    return out


def _r_snack_solves(world: World) -> list[str]:
    out: list[str] = []
    hungry = world.entities.get("hungry")
    snack = world.entities.get("snack")
    if hungry is None or snack is None:
        return out
    if snack.meters["eaten"] < THRESHOLD:
        return out
    sig = ("settled", hungry.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hungry.meters["hunger"] = 0.0
    hungry.meters["stomach_noise"] = 0.0
    hungry.memes["relief"] += 1
    hungry.memes["joy"] += 1
    detective = world.entities.get("detective")
    if detective is not None:
        detective.memes["joy"] += 1
        detective.memes["curiosity"] = 0.0
    out.append("__settled__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="hunger_noise", tag="physical", apply=_r_hunger_noise),
    Rule(name="noise_spooks", tag="emotional", apply=_r_noise_spooks),
    Rule(name="snack_solves", tag="physical", apply=_r_snack_solves),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if not s.startswith("__"))
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def suspect_fits_setup(setup: Setup, suspect: Suspect) -> bool:
    return suspect.id in setup.suspects and setup.id in suspect.plausible_in


def snack_is_enough(snack: Snack) -> bool:
    return snack.filling >= FILLING_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setup_id, setup in SETUPS.items():
        for suspect_id, suspect in SUSPECTS.items():
            if not suspect_fits_setup(setup, suspect):
                continue
            for snack_id, snack in SNACKS.items():
                if snack_is_enough(snack):
                    combos.append((setup_id, suspect_id, snack_id))
    return combos


def predict_noise(world: World) -> dict:
    sim = world.copy()
    propagate(sim, narrate=False)
    hungry = sim.get("hungry")
    return {
        "growls": hungry.meters["stomach_noise"] >= THRESHOLD,
        "real_culprit": sim.facts.get("real_culprit", ""),
    }


def introduce_case(world: World, detective: Entity, hungry: Entity, setup: Setup) -> None:
    detective.memes["play"] += 1
    hungry.memes["play"] += 1
    world.say(
        f"On a funny afternoon, {detective.id} and {hungry.id} turned the garage into {setup.opening}. "
        f"{setup.props}"
    )
    world.say(
        f'"Detective {detective.id} is on the case," {detective.id} announced. '
        f'"Today we will solve {setup.mission}."'
    )
    world.say(setup.weather_line)


def hide_hunger(world: World, hungry: Entity) -> None:
    hungry.meters["hunger"] += 1
    hungry.memes["embarrassment"] += 1
    world.facts["skipped_snack"] = True
    world.say(
        f"{hungry.id} nodded, but {hungry.pronoun()} had come out to play so fast that {hungry.pronoun()} had forgotten snack time."
    )


def first_growl(world: World, detective: Entity, hungry: Entity) -> None:
    pred = predict_noise(world)
    if not pred["growls"]:
        raise StoryError("(No story: the hungry child is not hungry enough to make the mystery noise.)")
    propagate(world, narrate=False)
    world.facts["predicted_culprit"] = pred["real_culprit"]
    hungry.memes["embarrassment"] += 1
    detective.memes["curiosity"] += 1
    world.say(
        'Then the garage said, "Grrrroooowl."'
    )
    world.say(
        f"{detective.id} froze with one finger in the air. {hungry.id} froze too. "
        f"The sound was low, wiggly, and much too silly to be a proper monster."
    )


def accuse_suspect(world: World, detective: Entity, suspect: Suspect) -> None:
    world.say(
        f'"Aha!" whispered {detective.id}. "The culprit must be {suspect.phrase} {suspect.place}."'
    )
    world.say(
        f"{detective.id} crept over in tiptoe-detective steps. {suspect.clue}"
    )


def inspect_and_clear(world: World, detective: Entity, hungry: Entity, suspect: Suspect) -> None:
    detective.memes["reasoning"] += 1
    world.facts["false_suspect"] = suspect.id
    world.facts["false_clue"] = suspect.clue
    world.say(
        f"But {suspect.innocent_reason} That made {detective.id} squint harder, because the case was still open."
    )
    world.say(
        f'Just then the sound came again -- "blurp-gurrrp!" -- and this time it was much closer to {hungry.id} than to {suspect.label}.'
    )


def reveal_culprit(world: World, detective: Entity, hungry: Entity) -> None:
    hungry.memes["embarrassment"] += 1
    detective.memes["surprise"] += 1
    world.facts["culprit_kind"] = "stomach"
    world.say(
        f"{detective.id}'s eyes traveled from the quiet garage shelf to {hungry.id}'s middle."
    )
    world.say(
        f'"Wait," said {detective.id}. "Was that... your stomach?"'
    )
    world.say(
        f"{hungry.id} pressed both hands over {hungry.pronoun('possessive')} tummy and gave a tiny laugh. "
        f'"Maybe," {hungry.pronoun()} admitted. "It sounds louder in the garage."'
    )


def parent_arrives(world: World, parent: Entity, snack: Snack) -> None:
    parent.memes["care"] += 1
    world.say(
        f"{parent.label_word.capitalize()} poked {parent.pronoun('possessive')} head through the side door and sniffed the air. "
        f"{snack.smell}"
    )


def solve_with_snack(world: World, parent: Entity, hungry: Entity, detective: Entity, snack: Snack) -> None:
    snack_ent = world.get("snack")
    snack_ent.meters["eaten"] += 1
    propagate(world, narrate=False)
    world.facts["snack_used"] = snack.id
    world.say(
        f'"Mystery solved," said {parent.label_word}. "{hungry.id} needs {snack.phrase}."'
    )
    world.say(
        f"{hungry.id} took a bite. The garage stayed quiet for one whole second, and then everyone waited."
    )
    world.say(
        'No growl came back. Only a happy chewing sound.'
    )
    world.say(
        f'{detective.id} put a hand on {hungry.id}\'s shoulder and declared, "Case closed. The sneaky noise was a stomach, not a monster."'
    )


def ending_image(world: World, detective: Entity, hungry: Entity, setup: Setup) -> None:
    detective.memes["joy"] += 1
    hungry.memes["joy"] += 1
    world.say(
        f"Soon the two detectives were laughing so hard they had to lean against the garage wall."
    )
    world.say(
        f"{hungry.id}'s stomach was quiet at last, and {detective.id} wrote the answer to {setup.mission.lower()} on a cardboard clue card: "
        f'"Feed the detective team before the next case."'
    )


def tell(
    setup: Setup,
    suspect: Suspect,
    snack: Snack,
    detective_name: str = "Mia",
    detective_gender: str = "girl",
    hungry_name: str = "Ben",
    hungry_gender: str = "boy",
    parent_type: str = "mother",
    detective_trait: str = "serious",
    hungry_trait: str = "bouncy",
) -> World:
    world = World()
    detective = world.add(Entity(
        id="detective",
        kind="character",
        type=detective_gender,
        label=detective_name,
        phrase=detective_name,
        role="detective",
        traits=[detective_trait],
        attrs={"name": detective_name},
    ))
    hungry = world.add(Entity(
        id="hungry",
        kind="character",
        type=hungry_gender,
        label=hungry_name,
        phrase=hungry_name,
        role="hungry_child",
        traits=[hungry_trait],
        attrs={"name": hungry_name},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    world.add(Entity(
        id="suspect",
        kind="thing",
        type="suspect",
        label=suspect.label,
        phrase=suspect.phrase,
        role="suspect",
        tags=set(suspect.tags),
    ))
    world.add(Entity(
        id="snack",
        kind="thing",
        type="snack",
        label=snack.label,
        phrase=snack.phrase,
        role="snack",
        tags=set(snack.tags),
    ))

    introduce_case(world, detective, hungry, setup)
    hide_hunger(world, hungry)

    world.para()
    first_growl(world, detective, hungry)
    accuse_suspect(world, detective, suspect)
    inspect_and_clear(world, detective, hungry, suspect)

    world.para()
    reveal_culprit(world, detective, hungry)
    parent_arrives(world, parent, snack)
    solve_with_snack(world, parent, hungry, detective, snack)

    world.para()
    ending_image(world, detective, hungry, setup)

    world.facts.update(
        setup=setup,
        suspect_cfg=suspect,
        snack_cfg=snack,
        detective=detective,
        hungry=hungry,
        parent=parent,
        mystery_solved=True,
        culprit="stomach",
        culprit_owner=hungry.label,
        detective_name=detective.label,
        hungry_name=hungry.label,
    )
    return world


SETUPS = {
    "rainy_day": Setup(
        id="rainy_day",
        opening="a rainy-day detective headquarters",
        props="A wobbling card table held a notebook, a magnifying glass, and three bottle-cap badges.",
        mission="The Case of the Garage Growl",
        weather_line="Rain tapped on the garage door like impatient fingers, which made every little sound feel twice as mysterious.",
        clue_style="echoes and drips",
        suspects={"toolbox", "lawnmower", "bike_tire"},
        tags={"garage", "rain", "detective"},
    ),
    "fix_it_day": Setup(
        id="fix_it_day",
        opening="a workshop for junior detectives",
        props="On one side stood a bike with one wheel off, and on the other sat a shelf of screws sorted into jam jars.",
        mission="The Rumble-by-the-Workbench Mystery",
        weather_line="The garage smelled like rubber, wood, and yesterday's sawdust.",
        clue_style="rattles and tiny clangs",
        suspects={"toolbox", "lawnmower", "bike_tire"},
        tags={"garage", "tools", "detective"},
    ),
    "costume_day": Setup(
        id="costume_day",
        opening="a costume-and-clues clubhouse",
        props="A cape hung from a ladder, a toy trumpet rested on a box, and a flashlight sat on an upside-down paint can.",
        mission="Who Hummed in the Garage?",
        weather_line="The garage was so full of odd things that even a sneeze could sound suspicious.",
        clue_style="echoes and funny shadows",
        suspects={"toolbox", "bike_tire", "costume_box"},
        tags={"garage", "pretend", "detective"},
    ),
}

SUSPECTS = {
    "toolbox": Suspect(
        id="toolbox",
        label="toolbox",
        phrase="the red toolbox",
        place="under the workbench",
        clue="The box was shut tight, and when {name} tapped it, it only gave a small clink.".replace("{name}", "the detective"),
        innocent_reason="nothing inside was moving except a loose wrench",
        plausible_in={"rainy_day", "fix_it_day", "costume_day"},
        tags={"tools", "garage"},
    ),
    "lawnmower": Suspect(
        id="lawnmower",
        label="lawnmower",
        phrase="the lawnmower",
        place="beside the wall",
        clue="It looked grumpy enough, but its cord was coiled neatly and its wheels were still.",
        innocent_reason="a machine that is turned off cannot growl by itself",
        plausible_in={"rainy_day", "fix_it_day"},
        tags={"machine", "garage"},
    ),
    "bike_tire": Suspect(
        id="bike_tire",
        label="bike tire",
        phrase="the half-flat bike tire",
        place="next to the pegboard",
        clue="The tire gave a soft hiss when squeezed, but a hiss is not the same as a tummy-growl.",
        innocent_reason="a sleepy tire can sigh, but it cannot say blurp-gurrrp",
        plausible_in={"rainy_day", "fix_it_day", "costume_day"},
        tags={"bike", "garage"},
    ),
    "costume_box": Suspect(
        id="costume_box",
        label="costume box",
        phrase="the costume box",
        place="behind the ladder",
        clue="Feather boas and paper crowns spilled out, but none of them looked hungry.",
        innocent_reason="hats may flop and boas may swish, but dress-up clothes do not have stomachs",
        plausible_in={"costume_day"},
        tags={"costume", "garage"},
    ),
    "snowman": Suspect(
        id="snowman",
        label="snowman",
        phrase="a snowman",
        place="in the corner",
        clue="There was, of course, no snowman there at all.",
        innocent_reason="a snowman does not belong in a normal garage in this little world",
        plausible_in=set(),
        tags={"silly"},
    ),
}

SNACKS = {
    "sandwich": Snack(
        id="sandwich",
        label="sandwich",
        phrase="a peanut butter sandwich cut into triangles",
        smell="A good sandwich smell drifted in from the kitchen.",
        filling=3,
        tags={"sandwich", "food"},
    ),
    "apple_crackers": Snack(
        id="apple_crackers",
        label="apple slices and crackers",
        phrase="a plate of apple slices and cheese crackers",
        smell="A crisp apple smell came in first, followed by the toasty smell of crackers.",
        filling=2,
        tags={"apple", "crackers", "food"},
    ),
    "banana_muffin": Snack(
        id="banana_muffin",
        label="banana muffin",
        phrase="a warm banana muffin",
        smell="The air suddenly smelled like bananas and cinnamon.",
        filling=2,
        tags={"muffin", "banana", "food"},
    ),
    "lollipop": Snack(
        id="lollipop",
        label="lollipop",
        phrase="one tiny lollipop",
        smell="A sweet candy smell floated in, but it was a very small smell for a very loud growl.",
        filling=1,
        tags={"candy"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Zoe", "Ava", "Ella", "Nora", "Ruby", "Anna"]
BOY_NAMES = ["Ben", "Max", "Leo", "Sam", "Eli", "Theo", "Finn", "Jack"]
TRAITS = ["serious", "curious", "careful", "dramatic", "bouncy", "cheerful"]


@dataclass
class StoryParams:
    setup: str
    suspect: str
    snack: str
    detective_name: str
    detective_gender: str
    hungry_name: str
    hungry_gender: str
    parent: str
    detective_trait: str
    hungry_trait: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "garage": [
        (
            "What is a garage?",
            "A garage is a room or small building where people often keep a car, tools, bikes, or boxes. Because it echoes and holds many objects, little noises can sound bigger there.",
        )
    ],
    "stomach": [
        (
            "Why can a stomach make growling sounds?",
            "A stomach can growl when it is empty and getting ready for food. The sound is just the body moving air and juices around, even though it can seem funny or mysterious.",
        )
    ],
    "detective": [
        (
            "What does a detective do?",
            "A detective looks for clues and tries to explain what really happened. Good detectives do not just guess; they notice details and test ideas.",
        )
    ],
    "sandwich": [
        (
            "Why can a sandwich help a hungry tummy?",
            "A sandwich is a real snack with food that helps fill an empty stomach. When the stomach is not empty anymore, its loud growls often settle down.",
        )
    ],
    "apple": [
        (
            "What are apple slices?",
            "Apple slices are pieces of an apple cut into smaller parts so they are easy to eat. They are a common snack because they are crunchy and sweet.",
        )
    ],
    "crackers": [
        (
            "What are crackers?",
            "Crackers are thin, crisp baked snacks. People often eat them with fruit or cheese for a small snack.",
        )
    ],
    "muffin": [
        (
            "What is a muffin?",
            "A muffin is a small soft cake-like bread, often baked in a paper cup. A banana muffin can make a warm and filling snack.",
        )
    ],
    "tools": [
        (
            "What is a toolbox for?",
            "A toolbox holds tools like hammers, screwdrivers, or wrenches. Tools can clink and rattle, which is why a toolbox can seem suspicious in a garage mystery.",
        )
    ],
    "machine": [
        (
            "Can a turned-off machine make a growling sound by itself?",
            "Usually no. A turned-off machine might creak or settle, but it should not suddenly growl like something alive.",
        )
    ],
    "bike": [
        (
            "What happens when a bike tire is low on air?",
            "A low bike tire can feel squishy and sometimes make a little hiss when pressed. That is different from a stomach growl, which comes from a person.",
        )
    ],
    "costume": [
        (
            "What is a costume?",
            "A costume is clothing or dress-up gear worn for pretend play. It can make a person look silly or dramatic, but it does not make tummy noises by itself.",
        )
    ],
}
KNOWLEDGE_ORDER = ["garage", "detective", "stomach", "sandwich", "apple", "crackers", "muffin", "tools", "machine", "bike", "costume"]


CURATED = [
    StoryParams(
        setup="rainy_day",
        suspect="toolbox",
        snack="sandwich",
        detective_name="Mia",
        detective_gender="girl",
        hungry_name="Ben",
        hungry_gender="boy",
        parent="mother",
        detective_trait="serious",
        hungry_trait="bouncy",
    ),
    StoryParams(
        setup="fix_it_day",
        suspect="lawnmower",
        snack="apple_crackers",
        detective_name="Leo",
        detective_gender="boy",
        hungry_name="Ava",
        hungry_gender="girl",
        parent="father",
        detective_trait="careful",
        hungry_trait="cheerful",
    ),
    StoryParams(
        setup="costume_day",
        suspect="costume_box",
        snack="banana_muffin",
        detective_name="Zoe",
        detective_gender="girl",
        hungry_name="Finn",
        hungry_gender="boy",
        parent="mother",
        detective_trait="dramatic",
        hungry_trait="curious",
    ),
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    hungry = f["hungry"]
    setup = f["setup"]
    suspect = f["suspect_cfg"]
    snack = f["snack_cfg"]
    return [
        f'Write a funny whodunit for a 3-to-5-year-old set in a garage. Include the word "stomach" and end with a silly, harmless reveal.',
        f"Tell a gentle mystery where {detective.label} hears a strange growl in the garage, suspects {suspect.phrase}, and discovers the real culprit is {hungry.label}'s hungry stomach.",
        f'Write a short child-facing detective story with clues, a false suspect, and a happy ending with {snack.phrase}. Make the mystery sound big at first and funny by the end.',
    ]


def story_qa_pairs(world: World) -> list[tuple[str, str]]:
    f = world.facts
    detective = f["detective"]
    hungry = f["hungry"]
    parent = f["parent"]
    setup = f["setup"]
    suspect = f["suspect_cfg"]
    snack = f["snack_cfg"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {detective.label} and {hungry.label}, two children playing detective in the garage, and their {parent.label_word} who helps at the end.",
        ),
        (
            "What was the mystery in the garage?",
            f"The children heard a strange growling sound in the garage and did not know what made it. Because the garage echoed and was full of objects, the sound seemed like a real case.",
        ),
        (
            f"Who did {detective.label} suspect first?",
            f"{detective.label} first suspected {suspect.phrase}. That was a sensible guess because it was right there in the garage and looked as if it might make a funny noise.",
        ),
        (
            f"Why was {suspect.label} not the culprit?",
            f"{suspect.innocent_reason.capitalize()}. The clue cleared that suspect and pushed the children to look for a better answer.",
        ),
        (
            "What was the real culprit?",
            f"The real culprit was {hungry.label}'s stomach. It was growling because {hungry.label} had hurried out to play and forgotten snack time.",
        ),
        (
            f"How was the mystery solved?",
            f"{parent.label_word.capitalize()} brought {snack.phrase}, and {hungry.label} ate it. After that, the growling stopped, which proved the noise had come from a hungry tummy and not from anything spooky in the garage.",
        ),
        (
            "How did the story end?",
            f"It ended with everyone laughing in the garage instead of feeling worried. The final clue card showed what changed: the detectives learned to feed the team before opening a new case.",
        ),
    ]
    if setup.id == "costume_day":
        qa.append(
            (
                "Why did the garage feel extra mysterious?",
                "The garage was full of costume things and funny shadows, so every little noise felt suspicious. That playful setting made the harmless stomach sound seem like a bigger mystery at first.",
            )
        )
    return qa


def world_knowledge_pairs(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"garage", "stomach", "detective"}
    tags |= set(world.facts["suspect_cfg"].tags)
    tags |= set(world.facts["snack_cfg"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:10} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def explain_bad_suspect(setup: Setup, suspect: Suspect) -> str:
    return (
        f"(No story: {suspect.phrase} is not a reasonable garage suspect for the {setup.id.replace('_', ' ')} setup. "
        f"Pick one of: {', '.join(sorted(setup.suspects))}.)"
    )


def explain_bad_snack(snack: Snack) -> str:
    return (
        f"(No story: {snack.phrase} is too small to settle the mystery in a believable way "
        f"(filling={snack.filling} < {FILLING_MIN}). Choose a more filling snack.)"
    )


ASP_RULES = r"""
suspect_fits(Su, Se) :- suspect(Su), setup(Se), plausible_in(Su, Se), available_suspect(Se, Su).
snack_enough(Sn) :- snack(Sn), filling(Sn, F), filling_min(M), F >= M.
valid(Se, Su, Sn) :- suspect_fits(Su, Se), snack_enough(Sn).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for setup_id, setup in SETUPS.items():
        lines.append(asp.fact("setup", setup_id))
        for suspect_id in sorted(setup.suspects):
            lines.append(asp.fact("available_suspect", setup_id, suspect_id))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        for setup_id in sorted(suspect.plausible_in):
            lines.append(asp.fact("plausible_in", suspect_id, setup_id))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        lines.append(asp.fact("filling", snack_id, snack.filling))
    lines.append(asp.fact("filling_min", FILLING_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between clingo and valid_combos():")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    smoke_cases = list(CURATED)
    try:
        default_params = resolve_params(build_parser().parse_args([]), random.Random(123))
        smoke_cases.append(default_params)
    except StoryError as err:
        rc = 1
        print(f"SMOKE setup failure: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story or "garage" not in sample.story.lower() or "stomach" not in sample.story.lower():
                rc = 1
                print("SMOKE failure: generated story missing required story content.")
            emit(sample, trace=False, qa=False, header="")
        except Exception as err:  # pragma: no cover - verify path
            rc = 1
            print(f"SMOKE failure while generating story: {err}")
    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} story generations.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a humorous garage whodunit where the culprit is a rumbling stomach."
    )
    ap.add_argument("--setup", choices=SETUPS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [name for name in pool if name != avoid]
    return rng.choice(choices)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setup and args.suspect:
        setup = SETUPS[args.setup]
        suspect = SUSPECTS[args.suspect]
        if not suspect_fits_setup(setup, suspect):
            raise StoryError(explain_bad_suspect(setup, suspect))
    if args.snack:
        snack = SNACKS[args.snack]
        if not snack_is_enough(snack):
            raise StoryError(explain_bad_snack(snack))

    combos = [
        combo for combo in valid_combos()
        if (args.setup is None or combo[0] == args.setup)
        and (args.suspect is None or combo[1] == args.suspect)
        and (args.snack is None or combo[2] == args.snack)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setup_id, suspect_id, snack_id = rng.choice(sorted(combos))
    detective_gender = rng.choice(["girl", "boy"])
    hungry_gender = rng.choice(["girl", "boy"])
    detective_name = pick_name(rng, detective_gender)
    hungry_name = pick_name(rng, hungry_gender, avoid=detective_name)
    parent = args.parent or rng.choice(["mother", "father"])
    detective_trait = rng.choice(["serious", "curious", "careful", "dramatic"])
    hungry_trait = rng.choice(["bouncy", "cheerful", "curious", "wiggly"])
    return StoryParams(
        setup=setup_id,
        suspect=suspect_id,
        snack=snack_id,
        detective_name=detective_name,
        detective_gender=detective_gender,
        hungry_name=hungry_name,
        hungry_gender=hungry_gender,
        parent=parent,
        detective_trait=detective_trait,
        hungry_trait=hungry_trait,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setup not in SETUPS:
        raise StoryError(f"(Unknown setup: {params.setup})")
    if params.suspect not in SUSPECTS:
        raise StoryError(f"(Unknown suspect: {params.suspect})")
    if params.snack not in SNACKS:
        raise StoryError(f"(Unknown snack: {params.snack})")

    setup = SETUPS[params.setup]
    suspect = SUSPECTS[params.suspect]
    snack = SNACKS[params.snack]
    if not suspect_fits_setup(setup, suspect):
        raise StoryError(explain_bad_suspect(setup, suspect))
    if not snack_is_enough(snack):
        raise StoryError(explain_bad_snack(snack))

    world = tell(
        setup=setup,
        suspect=suspect,
        snack=snack,
        detective_name=params.detective_name,
        detective_gender=params.detective_gender,
        hungry_name=params.hungry_name,
        hungry_gender=params.hungry_gender,
        parent_type=params.parent,
        detective_trait=params.detective_trait,
        hungry_trait=params.hungry_trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_pairs(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_pairs(world)],
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
        print(f"{len(combos)} compatible (setup, suspect, snack) combos:\n")
        for setup_id, suspect_id, snack_id in combos:
            print(f"  {setup_id:12} {suspect_id:12} {snack_id}")
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
            header = f"### {p.detective_name} and {p.hungry_name}: {p.setup} / {p.suspect} / {p.snack}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
