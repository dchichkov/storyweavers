#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/reckon_sound_effects_surprise_repetition_fable.py
==============================================================================

A standalone story world for a small fable about a hidden sound, a hasty guess,
and a surprise reveal.

The domain is built around one compact lesson: a creature hears a repeated noise,
reckons too much from too little, and then learns to look before leaping. The
simulation tracks both physical state (noise, hiddenness, spilled cargo) and
emotional state (alarm, calm, embarrassment, wisdom), so the prose changes with
what actually happens in the world.

Features from the seed:
- includes the word "reckon"
- sound effects drive the middle of the story
- repetition appears in the sound and in the frightened guess
- surprise comes from the harmless reveal
- style stays close to a simple fable

Run it
------
    python storyworlds/worlds/gpt-5.4/reckon_sound_effects_surprise_repetition_fable.py
    python storyworlds/worlds/gpt-5.4/reckon_sound_effects_surprise_repetition_fable.py --source frog --guess river_ogre
    python storyworlds/worlds/gpt-5.4/reckon_sound_effects_surprise_repetition_fable.py --source acorn --guess river_ogre
    python storyworlds/worlds/gpt-5.4/reckon_sound_effects_surprise_repetition_fable.py --all
    python storyworlds/worlds/gpt-5.4/reckon_sound_effects_surprise_repetition_fable.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/reckon_sound_effects_surprise_repetition_fable.py --trace
    python storyworlds/worlds/gpt-5.4/reckon_sound_effects_surprise_repetition_fable.py --verify
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
# from the repo root or from inside this nested world directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"         # "character" | "thing" | "place"
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
        female = {"hen", "vixen", "doe"}
        male = {"hare", "fox", "mouse", "mole", "frog", "owl", "turtle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Source:
    id: str
    label: str
    sound: str
    rhythm: str
    hiding_place: str
    reveal: str
    mover: str
    category: str
    plausible_guesses: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Guess:
    id: str
    label: str
    cry: str
    category: str
    fear: float = 1.0
    tags: set[str] = field(default_factory=set)


@dataclass
class Cargo:
    id: str
    label: str
    phrase: str
    spill_noun: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    type: str
    method: str
    calm_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    source: str
    guess: str
    cargo: str
    helper: str
    response: str
    hare_name: str
    parenthetical_trait: str
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


def _r_noise_alarm(world: World) -> list[str]:
    source = world.entities.get("source")
    hare = world.entities.get("hare")
    lane = world.entities.get("lane")
    if source is None or hare is None or lane is None:
        return []
    if source.meters["noise"] < THRESHOLD:
        return []
    sig = ("noise_alarm", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hare.memes["alarm"] += world.facts.get("guess_cfg").fear
    lane.meters["tension"] += 1
    return []


def _r_spill_embarrass(world: World) -> list[str]:
    basket = world.entities.get("basket")
    hare = world.entities.get("hare")
    if basket is None or hare is None:
        return []
    if basket.meters["spilled"] < THRESHOLD:
        return []
    sig = ("spill_embarrass", basket.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hare.memes["embarrassment"] += 1
    hare.memes["alarm"] = 0.0
    return []


def _r_reveal_relief(world: World) -> list[str]:
    source = world.entities.get("source")
    hare = world.entities.get("hare")
    helper = world.entities.get("helper")
    if source is None or hare is None or helper is None:
        return []
    if source.meters["seen"] < THRESHOLD:
        return []
    sig = ("reveal_relief", source.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hare.memes["relief"] += 1
    hare.memes["wisdom"] += 1
    helper.memes["calm"] += 1
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="noise_alarm", tag="emotional", apply=_r_noise_alarm),
    Rule(name="spill_embarrass", tag="emotional", apply=_r_spill_embarrass),
    Rule(name="reveal_relief", tag="emotional", apply=_r_reveal_relief),
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
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


SOURCES = {
    "acorn": Source(
        id="acorn",
        label="an acorn in a stump",
        sound="tok-tok",
        rhythm="tok-tok! tok-tok! tok-tok!",
        hiding_place="inside an old stump by the lane",
        reveal="a round acorn dropping through a woodpecker hole and bouncing on the hollow wood",
        mover="the morning wind",
        category="knock",
        plausible_guesses={"giant", "woodcutter"},
        tags={"acorn", "tree", "sound"},
    ),
    "frog": Source(
        id="frog",
        label="a frog in the reeds",
        sound="plip-plop",
        rhythm="plip-plop! plip-plop! plip-plop!",
        hiding_place="under the reeds beside a puddle",
        reveal="a fat green frog kicking in the shallow water",
        mover="its own broad feet",
        category="splash",
        plausible_guesses={"river_ogre", "rain_drum"},
        tags={"frog", "puddle", "sound"},
    ),
    "mouse": Source(
        id="mouse",
        label="a mouse in a grain sack",
        sound="scritch-scratch",
        rhythm="scritch-scratch! scritch-scratch! scritch-scratch!",
        hiding_place="behind a leaning grain sack",
        reveal="a little gray mouse tugging oats through a tear in the cloth",
        mover="its small busy paws",
        category="scratch",
        plausible_guesses={"robber", "woodcutter"},
        tags={"mouse", "grain", "sound"},
    ),
    "beetle": Source(
        id="beetle",
        label="a beetle in a jar",
        sound="tap-tap",
        rhythm="tap-tap! tap-tap! tap-tap!",
        hiding_place="inside a clay jar left by the hedge",
        reveal="a shiny beetle bumping a dry bean against the jar wall",
        mover="its hard little shell",
        category="knock",
        plausible_guesses={"giant", "robber"},
        tags={"beetle", "jar", "sound"},
    ),
}

GUESSES = {
    "giant": Guess(
        id="giant",
        label="a giant",
        cry="A giant is knocking in the lane",
        category="knock",
        fear=1.5,
        tags={"giant", "worry"},
    ),
    "woodcutter": Guess(
        id="woodcutter",
        label="a woodcutter",
        cry="A woodcutter is chopping near the lane",
        category="knock",
        fear=1.0,
        tags={"wood", "worry"},
    ),
    "river_ogre": Guess(
        id="river_ogre",
        label="a river ogre",
        cry="A river ogre is slapping the puddle with its tail",
        category="splash",
        fear=1.6,
        tags={"river", "worry"},
    ),
    "rain_drum": Guess(
        id="rain_drum",
        label="a rain drum",
        cry="A rain drum is waking under the reeds",
        category="splash",
        fear=0.8,
        tags={"rain", "sound"},
    ),
    "robber": Guess(
        id="robber",
        label="a robber",
        cry="A robber is rustling for stolen grain",
        category="scratch",
        fear=1.3,
        tags={"robber", "worry"},
    ),
}

CARGO = {
    "plums": Cargo(
        id="plums",
        label="plums",
        phrase="a basket of blue plums",
        spill_noun="plums",
        tags={"fruit", "basket"},
    ),
    "beans": Cargo(
        id="beans",
        label="beans",
        phrase="a basket of pale beans",
        spill_noun="beans",
        tags={"beans", "basket"},
    ),
    "apples": Cargo(
        id="apples",
        label="apples",
        phrase="a basket of red apples",
        spill_noun="apples",
        tags={"apple", "basket"},
    ),
}

HELPERS = {
    "turtle": Helper(
        id="turtle",
        label="Turtle",
        type="turtle",
        method="stretched out his neck and peered slowly into the hiding place",
        calm_line="Slow feet often bring clear eyes.",
        tags={"turtle", "patience"},
    ),
    "owl": Helper(
        id="owl",
        label="Owl",
        type="owl",
        method="tilted his head, blinked once, and looked straight into the hiding place",
        calm_line="Sharp eyes are better than quick guesses.",
        tags={"owl", "patience"},
    ),
    "mole": Helper(
        id="mole",
        label="Mole",
        type="mole",
        method="pressed his nose to the ground and sniffed his way to the hiding place",
        calm_line="A quiet nose can find what a noisy mind cannot.",
        tags={"mole", "patience"},
    ),
}

RESPONSES = {
    "peek": {
        "label": "peek first",
        "tags": {"careful"},
    },
    "bolt": {
        "label": "bolt away",
        "tags": {"panic"},
    },
}

HARE_NAMES = ["Hare", "Bramble", "Thistle", "Swift-Ears", "Pip"]
TRAITS = ["hasty", "jumpy", "proud", "quick-footed", "eager"]


def guess_plausible(source: Source, guess: Guess) -> bool:
    return guess.id in source.plausible_guesses


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for source_id, source in SOURCES.items():
        for guess_id, guess in GUESSES.items():
            if guess_plausible(source, guess):
                combos.append((source_id, guess_id))
    return sorted(combos)


def outcome_of(params: StoryParams) -> str:
    return "careful" if params.response == "peek" else "spill"


def explain_rejection(source: Source, guess: Guess) -> str:
    return (
        f"(No story: {source.sound} from {source.hiding_place} would not reasonably "
        f"make someone reckon {guess.label}. Pick a guess that fits the kind of sound.)"
    )


def predict_reveal(world: World) -> dict:
    sim = world.copy()
    sim.get("source").meters["noise"] += 1
    propagate(sim, narrate=False)
    sim.get("source").meters["seen"] += 1
    propagate(sim, narrate=False)
    return {
        "alarm": sim.get("hare").memes["alarm"],
        "relief": sim.get("hare").memes["relief"],
    }


def introduce(world: World, hare: Entity, helper: Entity, cargo: Cargo) -> None:
    world.say(
        f"One bright morning, {hare.id}, a {world.facts['trait']} hare, went down the lane "
        f"with {cargo.phrase} balanced in a willow basket."
    )
    world.say(
        f"Beside him walked {helper.label}, who never hurried a thought before it had legs."
    )


def hear_sound(world: World, source: Source) -> None:
    source_ent = world.get("source")
    source_ent.meters["noise"] += 1
    propagate(world, narrate=False)
    world.say(
        f"From {source.hiding_place} came a sound: {source.rhythm}"
    )
    world.say(
        f"It came again, and again, and each time it seemed louder in the hush of the lane."
    )


def reckon_guess(world: World, hare: Entity, guess: Guess) -> None:
    hare.memes["certainty"] += 1
    repeated = guess.cry + "! " + guess.cry + "!"
    world.say(
        f'"I reckon it is {guess.label}," said {hare.id}. Then he cried, "{repeated}"'
    )


def helper_warning(world: World, helper_cfg: Helper) -> None:
    pred = predict_reveal(world)
    world.facts["predicted_alarm"] = pred["alarm"]
    world.say(
        f'"{helper_cfg.calm_line}" said {helper_cfg.label}. "Let us look before we leap."'
    )


def bolt(world: World, hare: Entity, cargo: Cargo) -> None:
    basket = world.get("basket")
    basket.meters["spilled"] += 1
    basket.meters["open"] += 1
    propagate(world, narrate=False)
    world.say(
        f"But {hare.id} gave one great bound, then another -- thump! thump! thump! -- and the basket flew from his paws."
    )
    world.say(
        f"Out rolled the {cargo.spill_noun}, over the dust, under the hedge, and into the grass."
    )


def peek(world: World, helper_cfg: Helper) -> None:
    helper = world.get("helper")
    source_ent = world.get("source")
    helper.memes["care"] += 1
    source_ent.meters["seen"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{helper.label} {helper_cfg.method}."
    )


def reveal(world: World, source: Source) -> None:
    source_ent = world.get("source")
    if source_ent.meters["seen"] < THRESHOLD:
        source_ent.meters["seen"] += 1
        propagate(world, narrate=False)
    world.say(
        f"And what came out at last? Not a monster. Not a robber. It was only {source.reveal}."
    )


def aftermath(world: World, hare: Entity, helper: Entity, cargo: Cargo, outcome: str) -> None:
    hare.memes["wisdom"] += 1
    if outcome == "spill":
        helper.memes["kindness"] += 1
        world.say(
            f"{hare.id} stood still, ears low with embarrassment, while {helper.label} helped him gather the {cargo.spill_noun} one by one."
        )
        world.say(
            f'"I reckoned a great thing from a little sound," said {hare.id}, and he spoke much more softly than before.'
        )
        world.say(
            f'Together they filled the basket again, and {hare.id} went on more slowly, listening with better sense than fear.'
        )
    else:
        hare.memes["joy"] += 1
        world.say(
            f"{hare.id} blinked, then laughed to see how small the secret of the noise had been."
        )
        world.say(
            f'"I reckoned too quickly," he admitted. "A sound may be loud, yet the truth may be little."'
        )
        world.say(
            f"The two travelers went on down the lane, and the basket rode steady between them."
        )


def moral(world: World, outcome: str) -> None:
    if outcome == "spill":
        world.say("So the lane taught this: whoever reckons before looking may lose more than his fear.")
    else:
        world.say("So the lane taught this: whoever looks before he reckons will seldom be fooled by echoes.")


def tell(
    source_cfg: Source,
    guess_cfg: Guess,
    cargo_cfg: Cargo,
    helper_cfg: Helper,
    response: str,
    hare_name: str,
    trait: str,
) -> World:
    world = World()
    hare = world.add(Entity(
        id=hare_name,
        kind="character",
        type="hare",
        label=hare_name,
        role="hero",
        traits=[trait],
        tags={"hare"},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_cfg.type,
        label=helper_cfg.label,
        role="helper",
        tags=set(helper_cfg.tags),
    ))
    lane = world.add(Entity(
        id="lane",
        kind="place",
        type="lane",
        label="lane",
    ))
    basket = world.add(Entity(
        id="basket",
        kind="thing",
        type="basket",
        label="basket",
        phrase=cargo_cfg.phrase,
        tags=set(cargo_cfg.tags),
    ))
    source = world.add(Entity(
        id="source",
        kind="thing",
        type="source",
        label=source_cfg.label,
        tags=set(source_cfg.tags),
    ))

    world.facts.update(
        hare=hare,
        helper=helper,
        lane=lane,
        basket=basket,
        source=source,
        source_cfg=source_cfg,
        guess_cfg=guess_cfg,
        cargo_cfg=cargo_cfg,
        helper_cfg=helper_cfg,
        response=response,
        trait=trait,
    )

    introduce(world, hare, helper, cargo_cfg)

    world.para()
    hear_sound(world, source_cfg)
    reckon_guess(world, hare, guess_cfg)
    helper_warning(world, helper_cfg)

    world.para()
    if response == "bolt":
        bolt(world, hare, cargo_cfg)
        reveal(world, source_cfg)
    else:
        peek(world, helper_cfg)
        reveal(world, source_cfg)

    world.para()
    outcome = outcome_of(StoryParams(
        source=source_cfg.id,
        guess=guess_cfg.id,
        cargo=cargo_cfg.id,
        helper=helper_cfg.id,
        response=response,
        hare_name=hare_name,
        parenthetical_trait=trait,
        seed=None,
    ))
    aftermath(world, hare, helper, cargo_cfg, outcome)
    moral(world, outcome)

    world.facts.update(
        outcome=outcome,
        spilled=basket.meters["spilled"] >= THRESHOLD,
        revealed=source.meters["seen"] >= THRESHOLD,
    )
    return world


KNOWLEDGE = {
    "sound": [
        (
            "Why can a small thing make a big sound?",
            "A hollow place can echo and make a little tap or splash seem louder than it really is. That is why ears alone do not always tell the whole truth."
        )
    ],
    "acorn": [
        (
            "What is an acorn?",
            "An acorn is the nut of an oak tree. It is small and hard, so it can make a sharp knocking sound when it hits wood."
        )
    ],
    "frog": [
        (
            "Why does a frog make splashing sounds?",
            "A frog can kick water with its feet and make little splashes. In a quiet place, those small splashes can sound bigger than they are."
        )
    ],
    "mouse": [
        (
            "Why do mice make scratching sounds?",
            "Mice have tiny feet and teeth, and they rustle through grain or cloth with quick scratchy noises. You may hear them before you see them."
        )
    ],
    "beetle": [
        (
            "How can a beetle make a tapping sound?",
            "A hard beetle bumping against something dry can make a neat little tap. Small shells and hard jars can turn tiny bumps into clear sounds."
        )
    ],
    "patience": [
        (
            "Why is patience useful when you hear a strange sound?",
            "Patience gives you time to look, listen, and understand what is really there. It helps stop fear from turning a little thing into a giant one."
        )
    ],
    "basket": [
        (
            "Why should you slow down when carrying a basket?",
            "If you run too fast, the basket can tip and spill what is inside. Slow steps keep the load steady."
        )
    ],
    "worry": [
        (
            "What can happen if you guess before you know?",
            "A quick guess can make you afraid of the wrong thing. Then you may choose badly because your fear is larger than the truth."
        )
    ],
}
KNOWLEDGE_ORDER = ["sound", "acorn", "frog", "mouse", "beetle", "patience", "basket", "worry"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    source = f["source_cfg"]
    guess = f["guess_cfg"]
    helper = f["helper_cfg"]
    cargo = f["cargo_cfg"]
    outcome = f["outcome"]
    if outcome == "spill":
        return [
            'Write a short fable for a 3-to-5-year-old that includes the word "reckon", uses repeated sound effects, and ends with a lesson about hasty fear.',
            f"Tell a fable where a hare hears {source.sound} from {source.hiding_place}, reckons it is {guess.label}, runs in panic, and spills {cargo.label} before the harmless surprise is revealed.",
            f"Write a simple animal story with repetition and surprise in which {helper.label} stays calm while a hare makes too much of a little noise.",
        ]
    return [
        'Write a short fable for a 3-to-5-year-old that includes the word "reckon", uses repeated sound effects, and ends with a gentle moral.',
        f"Tell a fable where a hare hears {source.sound} from {source.hiding_place}, reckons it is {guess.label}, but a calm {helper.label.lower()} looks first and finds a harmless surprise.",
        f"Write a simple animal story with repetition and surprise in which careful looking proves wiser than a quick guess.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hare = f["hare"]
    helper = f["helper_cfg"]
    source = f["source_cfg"]
    guess = f["guess_cfg"]
    cargo = f["cargo_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hare.id} the hare and {helper.label}, who walked beside him. The story follows what happened when they heard a hidden sound on the lane."
        ),
        (
            "What sound did they hear?",
            f"They heard {source.rhythm} from {source.hiding_place}. The sound came again and again, which made it feel bigger and stranger."
        ),
        (
            f'What did {hare.id} reckon the sound was?',
            f"{hare.id} reckoned it was {guess.label}. He guessed too fast because the repeated sound frightened him before he had seen the truth."
        ),
    ]
    if outcome == "spill":
        qa.append((
            f"Why did {hare.id} spill the {cargo.label}?",
            f"He bolted away in fear before anyone looked into the hiding place. Because he jumped too fast, the basket flew from his paws and the {cargo.spill_noun} rolled everywhere."
        ))
        qa.append((
            "What was the surprise at the end?",
            f"The surprise was that there was no {guess.label} at all. It was only {source.reveal}, which was much smaller and safer than {hare.id} had feared."
        ))
        qa.append((
            "What did the hare learn?",
            f"He learned that a little sound can trick a hasty mind. He also learned that reckoning before looking can cost you something real, like the tidy basket he dropped."
        ))
    else:
        qa.append((
            f"How did {helper.label} help?",
            f"{helper.label} stayed calm and looked first instead of running. That careful choice let the truth come out before fear could cause trouble."
        ))
        qa.append((
            "What was the surprise at the end?",
            f"The surprise was that there was no {guess.label} hiding there. It was only {source.reveal}, so the great mystery turned out to be a very small thing."
        ))
        qa.append((
            "What did the hare learn?",
            f"He learned that a loud sound is not always a big danger. Looking first helped him trade fear for understanding."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"sound", "patience", "worry"}
    tags |= set(f["source_cfg"].tags)
    tags |= set(f["cargo_cfg"].tags)
    if f["outcome"] == "spill":
        tags.add("basket")
    tags |= set(f["helper_cfg"].tags)
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
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        source="acorn",
        guess="giant",
        cargo="plums",
        helper="turtle",
        response="bolt",
        hare_name="Hare",
        parenthetical_trait="hasty",
        seed=None,
    ),
    StoryParams(
        source="frog",
        guess="river_ogre",
        cargo="apples",
        helper="owl",
        response="peek",
        hare_name="Thistle",
        parenthetical_trait="jumpy",
        seed=None,
    ),
    StoryParams(
        source="mouse",
        guess="robber",
        cargo="beans",
        helper="mole",
        response="peek",
        hare_name="Bramble",
        parenthetical_trait="proud",
        seed=None,
    ),
    StoryParams(
        source="beetle",
        guess="giant",
        cargo="plums",
        helper="owl",
        response="bolt",
        hare_name="Swift-Ears",
        parenthetical_trait="quick-footed",
        seed=None,
    ),
]


ASP_RULES = r"""
plausible(S, G) :- source(S), guess(G), source_allows(S, G).
valid(S, G) :- plausible(S, G).

outcome(careful) :- chosen_response(peek).
outcome(spill) :- chosen_response(bolt).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        for guess_id in sorted(source.plausible_guesses):
            lines.append(asp.fact("source_allows", source_id, guess_id))
    for guess_id in GUESSES:
        lines.append(asp.fact("guess", guess_id))
    for response_id in RESPONSES:
        lines.append(asp.fact("response", response_id))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = asp.fact("chosen_response", params.response)
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
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
    for response in RESPONSES:
        cases.append(StoryParams(
            source="acorn",
            guess="giant",
            cargo="plums",
            helper="turtle",
            response=response,
            hare_name="Hare",
            parenthetical_trait="hasty",
            seed=None,
        ))
    bad = sum(1 for p in cases if asp_outcome(p) != outcome_of(p))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or not sample.prompts or not sample.story_qa:
            raise StoryError("Smoke test produced an incomplete sample.")
        print("OK: smoke test generate() succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a hidden sound, a hasty guess, and a fable-like lesson."
    )
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--guess", choices=sorted(GUESSES))
    ap.add_argument("--cargo", choices=sorted(CARGO))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid source/guess pairs derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.source and args.guess:
        source = SOURCES[args.source]
        guess = GUESSES[args.guess]
        if not guess_plausible(source, guess):
            raise StoryError(explain_rejection(source, guess))

    combos = [
        combo for combo in valid_combos()
        if (args.source is None or combo[0] == args.source)
        and (args.guess is None or combo[1] == args.guess)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    source_id, guess_id = rng.choice(combos)
    cargo_id = args.cargo or rng.choice(sorted(CARGO))
    helper_id = args.helper or rng.choice(sorted(HELPERS))
    response = args.response or rng.choice(sorted(RESPONSES))
    hare_name = args.name or rng.choice(HARE_NAMES)
    trait = args.trait or rng.choice(TRAITS)

    return StoryParams(
        source=source_id,
        guess=guess_id,
        cargo=cargo_id,
        helper=helper_id,
        response=response,
        hare_name=hare_name,
        parenthetical_trait=trait,
        seed=None,
    )


def generate(params: StoryParams) -> StorySample:
    if params.source not in SOURCES:
        raise StoryError(f"(Unknown source: {params.source})")
    if params.guess not in GUESSES:
        raise StoryError(f"(Unknown guess: {params.guess})")
    if params.cargo not in CARGO:
        raise StoryError(f"(Unknown cargo: {params.cargo})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Unknown helper: {params.helper})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")

    source = SOURCES[params.source]
    guess = GUESSES[params.guess]
    if not guess_plausible(source, guess):
        raise StoryError(explain_rejection(source, guess))

    world = tell(
        source_cfg=source,
        guess_cfg=guess,
        cargo_cfg=CARGO[params.cargo],
        helper_cfg=HELPERS[params.helper],
        response=params.response,
        hare_name=params.hare_name,
        trait=params.parenthetical_trait,
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
        print(f"{len(combos)} compatible (source, guess) pairs:\n")
        for source_id, guess_id in combos:
            print(f"  {source_id:8} {guess_id}")
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
            header = f"### {p.hare_name}: {p.source} -> {p.guess} ({p.response})"
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
