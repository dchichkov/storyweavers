#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/inspector_missy_teamwork_surprise_ghost_story.py
============================================================================

A standalone storyworld for a gentle, child-facing ghost-story domain built from
the seed words "inspector" and "missy", with the required features of
**Teamwork** and **Surprise**.

Premise
-------
Missy and a child inspector hear something spooky in an old place at night.
They investigate together with a safe light and one useful helper tool. The
mystery looks ghostly at first, but the surprise is always friendly and real:
a sheet, a latch, or a jar of fireflies. The world model tracks fear, courage,
curiosity, and teamwork, and the prose is rendered from those simulated state
changes.

Reasonableness constraint
-------------------------
Not every spooky clue fits every place, and not every helper can solve every
mystery. This world only generates combinations where:

* the chosen place plausibly supports the chosen reveal,
* the reveal plausibly explains the chosen clue, and
* the chosen helper covers the action the reveal requires.

A Python gate enforces those constraints, and an inline ASP twin mirrors them.
`--verify` checks parity and also runs smoke tests on normal story generation.

Run it
------
    python storyworlds/worlds/gpt-5.4/inspector_missy_teamwork_surprise_ghost_story.py
    python storyworlds/worlds/gpt-5.4/inspector_missy_teamwork_surprise_ghost_story.py --place attic --reveal sheet_kitten
    python storyworlds/worlds/gpt-5.4/inspector_missy_teamwork_surprise_ghost_story.py --light candle
    python storyworlds/worlds/gpt-5.4/inspector_missy_teamwork_surprise_ghost_story.py --all
    python storyworlds/worlds/gpt-5.4/inspector_missy_teamwork_surprise_ghost_story.py --qa --json
"""

from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
LIGHT_SENSE_MIN = 2


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
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    entry: str
    spooky_detail: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    text: str
    approach: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Reveal:
    id: str
    label: str
    surprise_text: str
    explain_text: str
    need: str
    teamwork_text: str
    ending_text: str
    clues: set[str] = field(default_factory=set)
    places: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    sense: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    phrase: str
    covers: set[str] = field(default_factory=set)
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

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_fear_softens(world: World) -> list[str]:
    out: list[str] = []
    missy = world.entities.get("missy")
    inspector = world.entities.get("inspector")
    if not missy or not inspector:
        return out
    if missy.memes["teamwork"] >= THRESHOLD and inspector.memes["teamwork"] >= THRESHOLD:
        for kid in (missy, inspector):
            sig = ("fear_softens", kid.id)
            if sig in world.fired:
                continue
            if kid.memes["fear"] < THRESHOLD:
                continue
            world.fired.add(sig)
            kid.memes["fear"] = max(0.0, kid.memes["fear"] - 1.0)
            kid.memes["bravery"] += 1.0
        out.append("__calmer__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="fear_softens", tag="emotional", apply=_r_fear_softens),
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


PLACES = {
    "attic": Place(
        id="attic",
        label="attic",
        phrase="the attic at the top of the house",
        entry="up the narrow stairs to the attic door",
        spooky_detail="The beams creaked, and moonlight lay across old trunks like pale dust.",
        ending_image="The attic no longer looked haunted. It looked like a sleepy room with one happy purr in it.",
        tags={"attic", "house"},
    ),
    "library": Place(
        id="library",
        label="library",
        phrase="the little library with tall shelves",
        entry="through the hall and into the moonlit library",
        spooky_detail="The long curtains breathed in and out beside the high windows, and every shelf made dark corners.",
        ending_image="The library no longer felt full of ghosts. It felt full of books and the soft click of a safe window latch.",
        tags={"library", "books"},
    ),
    "greenhouse": Place(
        id="greenhouse",
        label="greenhouse",
        phrase="the glass greenhouse behind the yard",
        entry="along the stepping-stones to the greenhouse door",
        spooky_detail="Fog pearled on the glass, and every leaf made a shadow that wobbled when the wind passed.",
        ending_image="The greenhouse no longer glimmered like a ghost cave. It glowed with leaves, glass, and a warm little jar of lights.",
        tags={"greenhouse", "garden"},
    ),
}

CLUES = {
    "white_shape": Clue(
        id="white_shape",
        text="a pale white shape swaying in the dark",
        approach="The shape rose, dipped, and brushed the shadows as if it were trying to wave.",
        tags={"ghost", "sheet"},
    ),
    "rattle": Clue(
        id="rattle",
        text="a clink-clink rattle that sounded like ghost chains",
        approach="Each gust made the small sound start again, then stop all at once.",
        tags={"ghost", "wind"},
    ),
    "blue_glow": Clue(
        id="blue_glow",
        text="a blue glow bobbing near the floor",
        approach="The glow drifted behind pots and boards, then blinked out, then shone again.",
        tags={"ghost", "glow"},
    ),
}

REVEALS = {
    "sheet_kitten": Reveal(
        id="sheet_kitten",
        label="sheet and kitten",
        surprise_text="It was only a laundry sheet caught on a hook, and under it sat a tiny kitten with round shining eyes.",
        explain_text="The sheet was the white ghost-shape, and the kitten had been bumping it whenever it tried to crawl free.",
        need="reach",
        teamwork_text="Inspector held the light steady while Missy climbed the stool just enough to lift the sheet loose. Then Inspector scooped up the kitten before it could tumble into another box.",
        ending_text="The kitten kneaded Missy's sleeve, and both children laughed so hard that the attic sounded friendly again.",
        clues={"white_shape"},
        places={"attic"},
        tags={"kitten", "sheet"},
    ),
    "window_latch": Reveal(
        id="window_latch",
        label="loose window latch",
        surprise_text="There was no ghost at all. A loose window latch was tapping the frame every time the wind slipped in.",
        explain_text="That neat little tap-tap was the chain-like rattle they had heard from the dark.",
        need="steady",
        teamwork_text="Missy pressed the window still with both hands while Inspector used the wedge to hold the latch snug. When the wind blew again, the glass only hummed softly.",
        ending_text="They listened for one more spooky rattle, but the room answered with quiet.",
        clues={"rattle"},
        places={"library", "greenhouse"},
        tags={"window", "wind"},
    ),
    "firefly_jar": Reveal(
        id="firefly_jar",
        label="firefly jar",
        surprise_text="The ghost-light turned out to be a jar of sleepy fireflies tipped behind a watering can.",
        explain_text="Their tiny lantern-bellies made the blue glow, and the glass made the light wobble in a spooky way.",
        need="lift",
        teamwork_text="Inspector carefully raised the watering can with the hook while Missy cupped the jar with both hands so it would not roll away. Together they set it upright, and the fireflies blinked like stars.",
        ending_text="Missy carried the jar to the table, and the soft lights made the greenhouse look magical instead of scary.",
        clues={"blue_glow"},
        places={"greenhouse", "library"},
        tags={"firefly", "light"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a flashlight",
        glow="clicked on a clear white beam",
        sense=3,
        tags={"flashlight", "safe_light"},
    ),
    "lantern": Light(
        id="lantern",
        label="lantern",
        phrase="a little battery lantern",
        glow="glowed warm and round",
        sense=3,
        tags={"lantern", "safe_light"},
    ),
    "moonlamp": Light(
        id="moonlamp",
        label="moon-lamp",
        phrase="a moon-shaped lamp",
        glow="spilled a soft silver circle",
        sense=2,
        tags={"lamp", "safe_light"},
    ),
    "candle": Light(
        id="candle",
        label="candle",
        phrase="a candle",
        glow="flickered with a real flame",
        sense=1,
        tags={"candle", "flame"},
    ),
}

HELPERS = {
    "step_stool": Helper(
        id="step_stool",
        label="step stool",
        phrase="a little step stool",
        covers={"reach"},
        tags={"stool"},
    ),
    "wedge": Helper(
        id="wedge",
        label="rubber wedge",
        phrase="a rubber wedge",
        covers={"steady"},
        tags={"wedge"},
    ),
    "garden_hook": Helper(
        id="garden_hook",
        label="garden hook",
        phrase="a long garden hook",
        covers={"lift"},
        tags={"hook"},
    ),
    "teacup": Helper(
        id="teacup",
        label="teacup",
        phrase="a tiny teacup",
        covers=set(),
        tags={"teacup"},
    ),
}

INSPECTOR_NAMES = ["Inspector Pip", "Inspector June", "Inspector Ben", "Inspector Tilda"]
MISSY_NAMES = ["Missy"]


@dataclass
class StoryParams:
    place: str
    clue: str
    reveal: str
    light: str
    helper: str
    inspector_name: str = "Inspector Pip"
    missy_name: str = "Missy"
    inspector_gender: str = "girl"
    seed: Optional[int] = None


def reveal_fits(place: str, clue: str, reveal: str) -> bool:
    r = REVEALS[reveal]
    return place in r.places and clue in r.clues


def helper_fits(helper: str, reveal: str) -> bool:
    return REVEALS[reveal].need in HELPERS[helper].covers


def sensible_lights() -> list[Light]:
    return [light for light in LIGHTS.values() if light.sense >= LIGHT_SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place in sorted(PLACES):
        for clue in sorted(CLUES):
            for reveal in sorted(REVEALS):
                if not reveal_fits(place, clue, reveal):
                    continue
                for helper in sorted(HELPERS):
                    if helper_fits(helper, reveal):
                        combos.append((place, clue, reveal, helper))
    return combos


def explain_rejection(place: str, clue: str, reveal: str, helper: str) -> str:
    pieces: list[str] = []
    if not reveal_fits(place, clue, reveal):
        pieces.append(
            f"{REVEALS[reveal].label} does not sensibly explain {CLUES[clue].text} in the {PLACES[place].label}"
        )
    if not helper_fits(helper, reveal):
        pieces.append(
            f"{HELPERS[helper].label} cannot do the job needed for {REVEALS[reveal].label}"
        )
    if not pieces:
        pieces.append("that combination is not reasonable in this world")
    return "(No story: " + "; ".join(pieces) + ".)"


def explain_light(light_id: str) -> str:
    light = LIGHTS[light_id]
    better = ", ".join(sorted(l.id for l in sensible_lights()))
    return (
        f"(Refusing light '{light_id}': {light.phrase} uses a real flame "
        f"(sense={light.sense} < {LIGHT_SENSE_MIN}). A gentle ghost mystery should use safe light instead. "
        f"Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if LIGHTS[params.light].sense < LIGHT_SENSE_MIN:
        return "unsafe"
    if not reveal_fits(params.place, params.clue, params.reveal):
        return "invalid"
    if not helper_fits(params.helper, params.reveal):
        return "invalid"
    return "solved"


def setup_story(world: World, place: Place, missy: Entity, inspector: Entity) -> None:
    missy.memes["curiosity"] += 1
    inspector.memes["curiosity"] += 1
    world.say(
        f"One hushy evening, {missy.id} and {inspector.id} padded {place.entry}. "
        f"They were playing ghost inspectors, though Missy stayed close enough to brush the inspector's sleeve."
    )
    world.say(place.spooky_detail)


def hear_clue(world: World, missy: Entity, inspector: Entity, place: Place, clue: Clue) -> None:
    for kid in (missy, inspector):
        kid.memes["fear"] += 1
    world.say(
        f"From inside {place.phrase} came {clue.text}. {clue.approach}"
    )
    world.say(
        f'"Did you hear that?" Missy whispered. "{place.label.capitalize()} ghosts always sound busiest when the house gets quiet."'
    )


def choose_tools(world: World, missy: Entity, inspector: Entity, light: Light, helper: Helper) -> None:
    inspector.memes["bravery"] += 1
    world.say(
        f'{inspector.id} swallowed once, then stood a little taller. "Real inspectors do not run first," '
        f'{inspector.pronoun()} said. {inspector.pronoun().capitalize()} picked up {light.phrase}, which {light.glow}, '
        f"and Missy carried {helper.phrase}."
    )
    world.say(
        "They promised to stay side by side, because spooky places felt smaller when two sets of footsteps went together."
    )


def approach(world: World, missy: Entity, inspector: Entity, clue: Clue) -> None:
    missy.memes["fear"] += 1
    inspector.memes["fear"] += 1
    world.say(
        f"The closer they crept, the more the mystery seemed to breathe around them. {clue.approach}"
    )
    world.say(
        f"Missy reached for the inspector's hand, and {inspector.id} squeezed back instead of pretending not to be nervous."
    )


def teamwork(world: World, missy: Entity, inspector: Entity, reveal: Reveal) -> None:
    for kid in (missy, inspector):
        kid.memes["teamwork"] += 1
    propagate(world, narrate=False)
    world.say(reveal.teamwork_text)


def reveal_scene(world: World, missy: Entity, inspector: Entity, reveal: Reveal) -> None:
    for kid in (missy, inspector):
        kid.memes["fear"] = 0.0
        kid.memes["surprise"] += 1
        kid.memes["joy"] += 1
    world.say(reveal.surprise_text)
    world.say(reveal.explain_text)


def ending(world: World, missy: Entity, inspector: Entity, place: Place, reveal: Reveal) -> None:
    world.say(reveal.ending_text)
    world.say(
        f'Missy grinned at {inspector.id}. "So the ghost was only a puzzle," she said.'
    )
    world.say(
        f'"And puzzles are best solved by two," {inspector.id} replied.'
    )
    world.say(place.ending_image)


def tell(
    place: Place,
    clue: Clue,
    reveal: Reveal,
    light: Light,
    helper: Helper,
    inspector_name: str = "Inspector Pip",
    missy_name: str = "Missy",
    inspector_gender: str = "girl",
) -> World:
    world = World()
    missy = world.add(Entity(id=missy_name, kind="character", type="girl", role="missy", label=missy_name))
    inspector = world.add(
        Entity(
            id=inspector_name,
            kind="character",
            type=inspector_gender,
            role="inspector",
            label="the inspector",
        )
    )
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="light", type="tool", label=light.label))
    world.add(Entity(id="helper", type="tool", label=helper.label))
    world.facts["need"] = reveal.need

    setup_story(world, place, missy, inspector)
    world.para()
    hear_clue(world, missy, inspector, place, clue)
    choose_tools(world, missy, inspector, light, helper)
    world.para()
    approach(world, missy, inspector, clue)
    teamwork(world, missy, inspector, reveal)
    world.para()
    reveal_scene(world, missy, inspector, reveal)
    ending(world, missy, inspector, place, reveal)

    world.facts.update(
        place=place,
        clue=clue,
        reveal=reveal,
        light=light,
        helper=helper,
        missy=missy,
        inspector=inspector,
        solved=True,
        surprise_kind=reveal.label,
        teamwork_used=True,
        calm_after=missy.memes["fear"] < THRESHOLD and inspector.memes["fear"] < THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "ghost": [
        (
            "Do all spooky sounds mean there is a ghost?",
            "No. A spooky sound can come from wind, glass, cloth, or an animal. Things often seem scarier before you know what made them.",
        )
    ],
    "flashlight": [
        (
            "Why is a flashlight good for dark places?",
            "A flashlight gives you light without a flame. That makes it a safe way to look around in the dark.",
        )
    ],
    "lantern": [
        (
            "What does a battery lantern do?",
            "A battery lantern glows so you can see in dark places. It is useful because it gives steady light without making fire.",
        )
    ],
    "lamp": [
        (
            "What is a lamp for at night?",
            "A lamp helps you see when a room is dark. A gentle lamp can make shadows look less scary.",
        )
    ],
    "candle": [
        (
            "Why should children be careful with candles?",
            "Candles have real flames, and real flames can burn skin or start fires. A grown-up should handle them.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten make a spooky noise?",
            "A kitten can rustle cloth, bump boxes, or cry from a hiding place. If you cannot see it yet, those little sounds can seem mysterious.",
        )
    ],
    "window": [
        (
            "Why does a loose window latch rattle?",
            "Wind can shake a loose latch against the window frame. The tapping repeats each time the air moves the glass.",
        )
    ],
    "wind": [
        (
            "How can wind make a place sound spooky?",
            "Wind can push curtains, shake glass, and tap loose things together. Those sounds are ordinary, but in the dark they can feel eerie.",
        )
    ],
    "firefly": [
        (
            "Why do fireflies glow?",
            "Fireflies make their own light inside their bodies. Their glow helps them signal in the dark.",
        )
    ],
    "stool": [
        (
            "What is a step stool for?",
            "A step stool helps you reach something a little higher up. It is useful when a shelf or hook is above your head.",
        )
    ],
    "wedge": [
        (
            "What does a wedge do?",
            "A wedge can hold something in place so it does not slip or swing. That makes a shaky thing steadier.",
        )
    ],
    "hook": [
        (
            "What can a long hook help you do?",
            "A long hook can lift or pull something without making you stretch too far. It helps you reach safely from a short distance.",
        )
    ],
}
KNOWLEDGE_ORDER = [
    "ghost",
    "flashlight",
    "lantern",
    "lamp",
    "candle",
    "kitten",
    "window",
    "wind",
    "firefly",
    "stool",
    "wedge",
    "hook",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place, clue, reveal = f["place"], f["clue"], f["reveal"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "inspector" and "Missy". Use teamwork and a surprise ending in {place.phrase}.',
        f"Tell a spooky-but-safe mystery where Missy and a child inspector hear {clue.text}, investigate together, and discover {reveal.label} instead of a ghost.",
        f"Write a child-facing ghost-story scene with soft suspense, a shared investigation, and a final surprise that explains the scary sound kindly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    missy = f["missy"]
    inspector = f["inspector"]
    place = f["place"]
    clue = f["clue"]
    reveal = f["reveal"]
    light = f["light"]
    helper = f["helper"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Missy and {inspector.id}, a child inspector, exploring {place.phrase}. They start out nervous, but they stay together.",
        ),
        (
            "What scared Missy and the inspector at first?",
            f"They heard {clue.text} in the dark. The mystery felt ghostly because they could hear or see it before they understood what was making it.",
        ),
        (
            "How did they get ready to investigate?",
            f"They took {light.phrase} and {helper.phrase} with them. The light helped them see, and the helper matched the job the mystery would need solved.",
        ),
        (
            "How did teamwork help them?",
            f"They stayed side by side and shared the work instead of one child doing everything alone. {reveal.teamwork_text} That made them calmer as well as more capable.",
        ),
        (
            "What was the surprise at the end?",
            f"{reveal.surprise_text} {reveal.explain_text}",
        ),
        (
            "How did the place feel different at the end?",
            f"It stopped feeling haunted once the mystery was understood. The ending image shows that fear changed into relief and joy because the children learned the true cause.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["clue"].tags) | set(f["reveal"].tags) | set(f["light"].tags) | set(f["helper"].tags)
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
        bits: list[str] = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:14} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="attic",
        clue="white_shape",
        reveal="sheet_kitten",
        light="lantern",
        helper="step_stool",
        inspector_name="Inspector Pip",
        missy_name="Missy",
        inspector_gender="boy",
    ),
    StoryParams(
        place="library",
        clue="rattle",
        reveal="window_latch",
        light="flashlight",
        helper="wedge",
        inspector_name="Inspector June",
        missy_name="Missy",
        inspector_gender="girl",
    ),
    StoryParams(
        place="greenhouse",
        clue="blue_glow",
        reveal="firefly_jar",
        light="moonlamp",
        helper="garden_hook",
        inspector_name="Inspector Ben",
        missy_name="Missy",
        inspector_gender="boy",
    ),
    StoryParams(
        place="greenhouse",
        clue="rattle",
        reveal="window_latch",
        light="lantern",
        helper="wedge",
        inspector_name="Inspector Tilda",
        missy_name="Missy",
        inspector_gender="girl",
    ),
]


ASP_RULES = r"""
% Reasonableness gate.
valid(P, C, R, H) :- place(P), clue(C), reveal(R), helper(H),
                     supports(P, R), hint_of(R, C),
                     reveal_needs(R, N), helper_covers(H, N).

% Safe-light gate.
sensible_light(L) :- light(L), light_sense(L, S), light_sense_min(M), S >= M.

% Outcome model for one chosen scenario.
outcome(solved) :- chosen_place(P), chosen_clue(C), chosen_reveal(R),
                   chosen_helper(H), chosen_light(L),
                   valid(P, C, R, H), sensible_light(L).
outcome(invalid) :- chosen_place(P), chosen_clue(C), chosen_reveal(R),
                    chosen_helper(H), not valid(P, C, R, H).
outcome(unsafe) :- chosen_light(L), not sensible_light(L).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id in sorted(PLACES):
        lines.append(asp.fact("place", place_id))
    for clue_id in sorted(CLUES):
        lines.append(asp.fact("clue", clue_id))
    for reveal_id, reveal in REVEALS.items():
        lines.append(asp.fact("reveal", reveal_id))
        for place_id in sorted(reveal.places):
            lines.append(asp.fact("supports", place_id, reveal_id))
        for clue_id in sorted(reveal.clues):
            lines.append(asp.fact("hint_of", reveal_id, clue_id))
        lines.append(asp.fact("reveal_needs", reveal_id, reveal.need))
    for helper_id, helper in HELPERS.items():
        lines.append(asp.fact("helper", helper_id))
        for need in sorted(helper.covers):
            lines.append(asp.fact("helper_covers", helper_id, need))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        lines.append(asp.fact("light_sense", light_id, light.sense))
    lines.append(asp.fact("light_sense_min", LIGHT_SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible_lights() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible_light/1."))
    return sorted(light for (light,) in asp.atoms(model, "sensible_light"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join(
        [
            asp.fact("chosen_place", params.place),
            asp.fact("chosen_clue", params.clue),
            asp.fact("chosen_reveal", params.reveal),
            asp.fact("chosen_helper", params.helper),
            asp.fact("chosen_light", params.light),
        ]
    )
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: valid combos match ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    py_lights = {light.id for light in sensible_lights()}
    asp_lights = set(asp_sensible_lights())
    if py_lights == asp_lights:
        print(f"OK: sensible lights match ({sorted(py_lights)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible lights: clingo={sorted(asp_lights)} python={sorted(py_lights)}")

    cases = list(CURATED)
    for seed in range(30):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} scenario outcomes differ.")

    try:
        smoke_params = CURATED[0]
        smoke_sample = generate(smoke_params)
        assert "Missy" in smoke_sample.story
        assert "Inspector" in smoke_sample.story
        assert "{" not in smoke_sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(smoke_sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test passed for generate()/emit().")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world: Missy and a child inspector solve a spooky mystery with teamwork and a surprise."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--reveal", choices=REVEALS)
    ap.add_argument("--light", choices=LIGHTS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--inspector-name")
    ap.add_argument("--inspector-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the valid mystery tuples from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and run smoke tests")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.light and LIGHTS[args.light].sense < LIGHT_SENSE_MIN:
        raise StoryError(explain_light(args.light))

    if args.place and args.clue and args.reveal and args.helper:
        if not (reveal_fits(args.place, args.clue, args.reveal) and helper_fits(args.helper, args.reveal)):
            raise StoryError(explain_rejection(args.place, args.clue, args.reveal, args.helper))

    combos = [
        combo
        for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.clue is None or combo[1] == args.clue)
        and (args.reveal is None or combo[2] == args.reveal)
        and (args.helper is None or combo[3] == args.helper)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, clue, reveal, helper = rng.choice(sorted(combos))
    light = args.light or rng.choice(sorted(light.id for light in sensible_lights()))
    inspector_name = args.inspector_name or rng.choice(INSPECTOR_NAMES)
    inspector_gender = args.inspector_gender or rng.choice(["girl", "boy"])
    return StoryParams(
        place=place,
        clue=clue,
        reveal=reveal,
        light=light,
        helper=helper,
        inspector_name=inspector_name,
        missy_name="Missy",
        inspector_gender=inspector_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"(No story: unknown place '{params.place}'.)")
    if params.clue not in CLUES:
        raise StoryError(f"(No story: unknown clue '{params.clue}'.)")
    if params.reveal not in REVEALS:
        raise StoryError(f"(No story: unknown reveal '{params.reveal}'.)")
    if params.light not in LIGHTS:
        raise StoryError(f"(No story: unknown light '{params.light}'.)")
    if params.helper not in HELPERS:
        raise StoryError(f"(No story: unknown helper '{params.helper}'.)")
    if LIGHTS[params.light].sense < LIGHT_SENSE_MIN:
        raise StoryError(explain_light(params.light))
    if not reveal_fits(params.place, params.clue, params.reveal) or not helper_fits(params.helper, params.reveal):
        raise StoryError(explain_rejection(params.place, params.clue, params.reveal, params.helper))

    world = tell(
        place=PLACES[params.place],
        clue=CLUES[params.clue],
        reveal=REVEALS[params.reveal],
        light=LIGHTS[params.light],
        helper=HELPERS[params.helper],
        inspector_name=params.inspector_name,
        missy_name=params.missy_name,
        inspector_gender=params.inspector_gender,
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
        print(asp_program("", "#show valid/4.\n#show sensible_light/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible lights: {', '.join(asp_sensible_lights())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} valid (place, clue, reveal, helper) combos:\n")
        for place, clue, reveal, helper in combos:
            print(f"  {place:10} {clue:11} {reveal:14} {helper}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
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
            header = f"### {p.missy_name} & {p.inspector_name}: {p.reveal} in {p.place}"
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
