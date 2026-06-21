#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/bureau_twist_rhyming_story.py
=======================================================

A standalone story world for a tiny rhyming tale about a child named Twist,
a mysterious sound in a bedroom bureau, and a gentle twist ending where the
"monster" turns out to be a hidden surprise.

The world model tracks:
- physical meters: dark, rattling, open, found
- emotional memes: fear, caution, courage, relief, delight, trust

The prose is state-driven and rhyming in style. The model prefers only
reasonable combinations:
- the hidden object must be plausible in a bureau drawer
- the bedroom scene must support the object's trigger
- the creature Twist imagines must fit the kind of sound that was heard
- the light used to investigate must be a safe one

Run it
------
    python storyworlds/worlds/gpt-5.4/bureau_twist_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/bureau_twist_rhyming_story.py --scene breezy_night --source paper_kite
    python storyworlds/worlds/gpt-5.4/bureau_twist_rhyming_story.py --source paper_kite --scene moonlit_room
    python storyworlds/worlds/gpt-5.4/bureau_twist_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/bureau_twist_rhyming_story.py -n 5 --seed 7 --qa
    python storyworlds/worlds/gpt-5.4/bureau_twist_rhyming_story.py --verify
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

# Make the shared result containers importable when this script is run directly
# from the repo root or from this nested directory.
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
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {
            "mother": "mom",
            "father": "dad",
            "grandmother": "grandma",
            "grandfather": "grandpa",
            "brother": "brother",
        }.get(self.type, self.type)


@dataclass
class Scene:
    id: str
    lead: str
    room_line: str
    breeze: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Source:
    id: str
    label: str
    phrase: str
    sound: str
    sound_tag: str
    trigger_line: str
    reveal_line: str
    ending_image: str
    needs_breeze: bool = False
    bureau_ok: bool = True
    surprise_kind: str = "gift"
    tags: set[str] = field(default_factory=set)


@dataclass
class Guess:
    id: str
    creature: str
    phrase: str
    hears: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Light:
    id: str
    label: str
    phrase: str
    glow: str
    safe: bool = True
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
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SCENES = {
    "moonlit_room": Scene(
        id="moonlit_room",
        lead="The moon made silver ladders on the floor.",
        room_line="By the tall old bureau stood Twist, snug in striped pajamas, thinking bedtime was a bore.",
        breeze=False,
        tags={"night", "bedroom"},
    ),
    "breezy_night": Scene(
        id="breezy_night",
        lead="A small night breeze brushed the curtain with a swoop.",
        room_line="By the painted bureau stood Twist, hugging a blanket while moonlight made a quiet loop.",
        breeze=True,
        tags={"night", "bedroom", "breeze"},
    ),
    "rainy_window": Scene(
        id="rainy_window",
        lead="Rain tapped the window with a drippy, drowsy tune.",
        room_line="Near the bedroom bureau stood Twist, wide awake and hoping sleep would visit soon.",
        breeze=True,
        tags={"night", "bedroom", "rain"},
    ),
}

SOURCES = {
    "music_box": Source(
        id="music_box",
        label="music box",
        phrase="a little music box tied with ribbon",
        sound="ting-ting",
        sound_tag="tinkly",
        trigger_line="Inside the drawer, an old spring gave one sleepy ping and set the tiny tune to ring.",
        reveal_line="The drawer held a little music box tied with ribbon, meant for morning with a kiss.",
        ending_image="The bureau no longer looked spooky and deep; it held a soft song ready for sleep.",
        needs_breeze=False,
        bureau_ok=True,
        surprise_kind="birthday gift",
        tags={"music_box", "gift", "bureau"},
    ),
    "paper_kite": Source(
        id="paper_kite",
        label="paper kite",
        phrase="a folded paper kite with a silver tail",
        sound="fuff-fuff",
        sound_tag="fluttery",
        trigger_line="A curl of air slipped through the room and made the silver tail go whisk in the gloom.",
        reveal_line="The drawer held a folded paper kite with a silver tail, tucked away for a bright windy day.",
        ending_image="The bureau became a treasure site, promising morning, wind, and kite.",
        needs_breeze=True,
        bureau_ok=True,
        surprise_kind="play surprise",
        tags={"kite", "gift", "wind", "bureau"},
    ),
    "tin_robot": Source(
        id="tin_robot",
        label="tin robot",
        phrase="a shiny tin robot in a gift box",
        sound="clink-clack",
        sound_tag="clacky",
        trigger_line="The drawer had shifted just enough for a tiny tin arm to knock and chuff.",
        reveal_line="The drawer held a shiny tin robot in a gift box, waiting there with a starry grin.",
        ending_image="The bureau seemed funny instead of grim; its secret had a clockwork hymn.",
        needs_breeze=False,
        bureau_ok=True,
        surprise_kind="birthday gift",
        tags={"robot", "gift", "toy", "bureau"},
    ),
}

GUESSES = {
    "mouse": Guess(
        id="mouse",
        creature="mouse",
        phrase="a whiskery mouse with tip-tap toes",
        hears={"clacky"},
        tags={"mouse"},
    ),
    "ghost": Guess(
        id="ghost",
        creature="ghost",
        phrase="a fluttery ghost in floating clothes",
        hears={"fluttery", "tinkly"},
        tags={"ghost"},
    ),
    "fairy": Guess(
        id="fairy",
        creature="fairy",
        phrase="a moonlit fairy with bell-bright wings",
        hears={"tinkly", "fluttery"},
        tags={"fairy"},
    ),
    "dragon": Guess(
        id="dragon",
        creature="dragon",
        phrase="a pocket dragon with armor rings",
        hears={"clacky"},
        tags={"dragon"},
    ),
}

LIGHTS = {
    "flashlight": Light(
        id="flashlight",
        label="flashlight",
        phrase="a small flashlight",
        glow="clicked on a neat white beam",
        safe=True,
        tags={"flashlight", "light"},
    ),
    "nightlight": Light(
        id="nightlight",
        label="night-light",
        phrase="a starry night-light",
        glow="glowed with a soft gold gleam",
        safe=True,
        tags={"nightlight", "light"},
    ),
    "lantern": Light(
        id="lantern",
        label="camping lantern",
        phrase="a little camping lantern",
        glow="made a warm round pool of light",
        safe=True,
        tags={"lantern", "light"},
    ),
}

HELPERS = {
    "mother": "mother",
    "father": "father",
    "grandmother": "grandmother",
    "brother": "brother",
}


def source_fits_scene(scene: Scene, source: Source) -> bool:
    if not source.bureau_ok:
        return False
    if source.needs_breeze and not scene.breeze:
        return False
    return True


def guess_fits_source(guess: Guess, source: Source) -> bool:
    return source.sound_tag in guess.hears


def light_is_reasonable(light: Light) -> bool:
    return light.safe


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for scene_id, scene in SCENES.items():
        for source_id, source in SOURCES.items():
            if not source_fits_scene(scene, source):
                continue
            for guess_id, guess in GUESSES.items():
                if not guess_fits_source(guess, source):
                    continue
                for light_id, light in LIGHTS.items():
                    if light_is_reasonable(light):
                        combos.append((scene_id, source_id, guess_id, light_id))
    return sorted(combos)


@dataclass
class StoryParams:
    scene: str
    source: str
    guess: str
    light: str
    helper: str
    seed: Optional[int] = None


def introduce(world: World, child: Entity, bureau: Entity, scene: Scene) -> None:
    child.memes["calm"] += 1
    bureau.meters["dark"] += 1
    world.say(
        f"{scene.lead} {scene.room_line}"
    )
    world.say(
        f'"That bureau is so tall and wide," whispered {child.id}, '
        f'"it looks like it could hide a ride."'
    )


def stir_sound(world: World, child: Entity, bureau: Entity, source: Source) -> None:
    bureau.meters["rattle"] += 1
    child.memes["fear"] += 2
    world.say(
        f"Then from the bureau came {source.sound} so small, then {source.sound} once more from behind the drawer and wall."
    )
    world.say(
        f"{child.id}'s knees felt wobbly, chin tucked tight; the room grew bigger in the night."
    )


def imagine(world: World, child: Entity, guess: Guess) -> None:
    child.memes["guessing"] += 1
    world.say(
        f'"Oh dear," said {child.id}, "what could that be? Perhaps {guess.phrase} is peeking back at me."'
    )


def helper_arrives(world: World, child: Entity, helper: Entity, light: Light) -> None:
    helper.memes["care"] += 1
    child.memes["trust"] += 1
    world.say(
        f"{helper.label_word.capitalize()} came in slow and heard the fright, then brought {light.phrase} that {light.glow} in the night."
    )
    world.say(
        f'"We do not run from every sound," said {helper.label_word}, '
        f'"first we look gently all around."'
    )


def approach(world: World, child: Entity, helper: Entity, bureau: Entity, light: Light) -> None:
    child.memes["courage"] += 1
    helper.memes["calm"] += 1
    bureau.meters["seen"] += 1
    world.say(
        f"Together they padded across the rug so white, with {light.label} making the corners bright."
    )
    world.say(
        f"{child.id} held {helper.label_word}'s hand quite tight, yet took one step, then one more brave little bite."
    )


def reveal(world: World, child: Entity, helper: Entity, bureau: Entity, source: Source) -> None:
    bureau.meters["open"] += 1
    child.memes["fear"] = 0.0
    child.memes["relief"] += 1
    child.memes["delight"] += 2
    world.get("surprise").meters["found"] += 1
    world.say(
        f"{helper.label_word.capitalize()} eased the bureau drawer open wide, and there was the twist tucked safe inside."
    )
    world.say(source.trigger_line)
    world.say(source.reveal_line)


def turn_and_end(world: World, child: Entity, helper: Entity, bureau: Entity, source: Source, guess: Guess) -> None:
    child.memes["laugh"] += 1
    bureau.meters["friendly"] += 1
    world.say(
        f"{child.id} blinked once, then laughed outright. "
        f'"So it was not a {guess.creature} at all tonight!"'
    )
    world.say(
        f"{helper.label_word.capitalize()} kissed {child.pronoun('possessive')} hair and said, "
        f'"Sometimes a bump means a gift is there."'
    )
    world.say(source.ending_image)


def tell(scene: Scene, source: Source, guess: Guess, light: Light, helper_type: str) -> World:
    world = World()
    child = world.add(Entity(
        id="Twist",
        kind="character",
        type="girl",
        label="Twist",
        role="child",
        attrs={"age": 5},
        tags={"child"},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label=helper_type,
        role="helper",
        tags={"helper"},
    ))
    bureau = world.add(Entity(
        id="bureau",
        kind="thing",
        type="bureau",
        label="bureau",
        phrase="the tall bedroom bureau",
        role="furniture",
        tags={"bureau"},
    ))
    surprise = world.add(Entity(
        id="surprise",
        kind="thing",
        type=source.label,
        label=source.label,
        phrase=source.phrase,
        role="hidden",
        tags=set(source.tags),
    ))

    introduce(world, child, bureau, scene)
    world.para()
    stir_sound(world, child, bureau, source)
    imagine(world, child, guess)
    helper_arrives(world, child, helper, light)
    world.para()
    approach(world, child, helper, bureau, light)
    reveal(world, child, helper, bureau, source)
    world.para()
    turn_and_end(world, child, helper, bureau, source, guess)

    world.facts.update(
        child=child,
        helper=helper,
        bureau=bureau,
        scene=scene,
        source=source,
        guess=guess,
        light=light,
        surprise=surprise,
        twist_kind=source.surprise_kind,
        feared=guess.creature,
        found=surprise.meters["found"] >= THRESHOLD,
        brave=child.memes["courage"] >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    source = f["source"]
    guess = f["guess"]
    light = f["light"]
    return [
        'Write a short rhyming story for a 3-to-5-year-old that includes the word "bureau" and has a gentle twist ending.',
        f"Tell a rhyming bedtime story where a child named Twist hears a strange sound in a bureau, fears a {guess.creature}, and then discovers {source.phrase}.",
        f"Write a simple rhyming story with a calm helper, {light.phrase}, a mysterious bureau drawer, and an ending that turns fear into delight.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    scene = f["scene"]
    source = f["source"]
    guess = f["guess"]
    light = f["light"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about Twist, who heard a strange sound in a bedroom bureau, and {helper.label_word} who came to help. The story follows Twist from a scared guess to a happy discovery."
        ),
        (
            "Why was Twist scared?",
            f"Twist heard {source.sound} coming from the bureau in the quiet room, so {child.pronoun('subject')} imagined {guess.phrase}. The dark and the mysterious sound made the bureau seem much scarier than it really was."
        ),
        (
            f"What did {helper.label_word} bring?",
            f"{helper.label_word.capitalize()} brought {light.phrase}. The safe light helped them look closely instead of guessing in the dark."
        ),
        (
            "What was the twist at the end?",
            f"The bureau was not hiding a {guess.creature} at all. It was hiding {source.phrase}, and that surprise was what made the sound."
        ),
        (
            "How did Twist feel at the end?",
            f"Twist felt relieved and delighted. Once the drawer was opened, the fear melted into laughter because the strange noise had a kind and harmless cause."
        ),
    ]
    if scene.breeze and source.needs_breeze:
        qa.append(
            (
                f"Why did the {source.label} make a sound?",
                f"It made a sound because the room had a little breeze moving through it. That small breath of air stirred the hidden surprise inside the bureau drawer."
            )
        )
    else:
        qa.append(
            (
                f"Why did the {source.label} make a sound?",
                f"It made a sound because something inside it shifted or woke a little in the drawer. The sound seemed spooky at first, but it came from an ordinary hidden object."
            )
        )
    return qa


KNOWLEDGE = {
    "bureau": [
        (
            "What is a bureau?",
            "A bureau is a tall piece of furniture with drawers for clothes or other things. People use it to keep items tidy and tucked away."
        )
    ],
    "flashlight": [
        (
            "What is a flashlight?",
            "A flashlight is a small light you can carry in your hand. It helps you see in the dark without using a flame."
        )
    ],
    "nightlight": [
        (
            "What is a night-light?",
            "A night-light is a small lamp that glows softly in a room at night. It helps a dark room feel gentler and easier to see."
        )
    ],
    "lantern": [
        (
            "What is a camping lantern?",
            "A camping lantern is a safe lamp that shines in many directions. It can light a whole little area instead of just one spot."
        )
    ],
    "music_box": [
        (
            "What does a music box do?",
            "A music box is a small box that plays a tune. When its little parts move, it can make tiny ringing sounds."
        )
    ],
    "kite": [
        (
            "Why does a kite move in the wind?",
            "A kite is light, so moving air can push and flutter it. That is why a breeze can make its tail rustle and dance."
        )
    ],
    "robot": [
        (
            "Why can a tin toy make clinky sounds?",
            "A tin toy has hard little parts that tap against each other. When it shifts, those parts can make clinks and clacks."
        )
    ],
    "fear": [
        (
            "Why can a sound seem scarier in the dark?",
            "In the dark, it is harder to see what made the noise. When you cannot see clearly, your imagination may guess something much scarier than the truth."
        )
    ],
}

KNOWLEDGE_ORDER = [
    "bureau",
    "fear",
    "flashlight",
    "nightlight",
    "lantern",
    "music_box",
    "kite",
    "robot",
]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    light = f["light"]
    source = f["source"]
    tags = {"bureau", "fear"} | set(light.tags) | set(source.tags)
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
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:9} ({ent.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_scene_source(scene: Scene, source: Source) -> str:
    if source.needs_breeze and not scene.breeze:
        return (
            f"(No story: {source.phrase} only makes sense here when a little breeze can stir it, "
            f"but the scene '{scene.id}' has still air. Pick a breezy or rainy bedroom scene.)"
        )
    return (
        f"(No story: {source.phrase} is not a good match for scene '{scene.id}'.)"
    )


def explain_guess(source: Source, guess: Guess) -> str:
    return (
        f"(No story: a sound like {source.sound} is not a good fit for guessing {guess.phrase}. "
        f"Pick a creature that matches the kind of noise Twist hears.)"
    )


ASP_RULES = r"""
stored_ok(S)    :- source(S), bureau_ok(S).
trigger_ok(C,S) :- scene(C), source(S), not needs_breeze(S).
trigger_ok(C,S) :- scene(C), source(S), needs_breeze(S), breeze(C).

plausible(G,S)  :- guess(G), source(S), sound_tag(S,T), hears(G,T).
safe(L)         :- light(L), safe_light(L).

valid(C,S,G,L)  :- scene(C), source(S), guess(G), light(L),
                   stored_ok(S), trigger_ok(C,S), plausible(G,S), safe(L).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for scene_id, scene in SCENES.items():
        lines.append(asp.fact("scene", scene_id))
        if scene.breeze:
            lines.append(asp.fact("breeze", scene_id))
    for source_id, source in SOURCES.items():
        lines.append(asp.fact("source", source_id))
        lines.append(asp.fact("sound_tag", source_id, source.sound_tag))
        if source.bureau_ok:
            lines.append(asp.fact("bureau_ok", source_id))
        if source.needs_breeze:
            lines.append(asp.fact("needs_breeze", source_id))
    for guess_id, guess in GUESSES.items():
        lines.append(asp.fact("guess", guess_id))
        for tag in sorted(guess.hears):
            lines.append(asp.fact("hears", guess_id, tag))
    for light_id, light in LIGHTS.items():
        lines.append(asp.fact("light", light_id))
        if light.safe:
            lines.append(asp.fact("safe_light", light_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


CURATED = [
    StoryParams(
        scene="moonlit_room",
        source="music_box",
        guess="ghost",
        light="nightlight",
        helper="mother",
    ),
    StoryParams(
        scene="breezy_night",
        source="paper_kite",
        guess="fairy",
        light="lantern",
        helper="father",
    ),
    StoryParams(
        scene="rainy_window",
        source="tin_robot",
        guess="dragon",
        light="flashlight",
        helper="grandmother",
    ),
    StoryParams(
        scene="breezy_night",
        source="tin_robot",
        guess="mouse",
        light="flashlight",
        helper="brother",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming story world: Twist hears a sound in a bureau and discovers a gentle twist ending."
    )
    ap.add_argument("--scene", choices=sorted(SCENES))
    ap.add_argument("--source", choices=sorted(SOURCES))
    ap.add_argument("--guess", choices=sorted(GUESSES))
    ap.add_argument("--light", choices=sorted(LIGHTS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.scene and args.source:
        scene = SCENES[args.scene]
        source = SOURCES[args.source]
        if not source_fits_scene(scene, source):
            raise StoryError(explain_scene_source(scene, source))
    if args.source and args.guess:
        source = SOURCES[args.source]
        guess = GUESSES[args.guess]
        if not guess_fits_source(guess, source):
            raise StoryError(explain_guess(source, guess))
    if args.light and not light_is_reasonable(LIGHTS[args.light]):
        raise StoryError(f"(No story: {args.light} is not treated as a safe investigating light here.)")

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.source is None or combo[1] == args.source)
        and (args.guess is None or combo[2] == args.guess)
        and (args.light is None or combo[3] == args.light)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, source_id, guess_id, light_id = rng.choice(combos)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        scene=scene_id,
        source=source_id,
        guess=guess_id,
        light=light_id,
        helper=helper,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Invalid scene: {params.scene})")
    if params.source not in SOURCES:
        raise StoryError(f"(Invalid source: {params.source})")
    if params.guess not in GUESSES:
        raise StoryError(f"(Invalid guess: {params.guess})")
    if params.light not in LIGHTS:
        raise StoryError(f"(Invalid light: {params.light})")
    if params.helper not in HELPERS:
        raise StoryError(f"(Invalid helper: {params.helper})")

    scene = SCENES[params.scene]
    source = SOURCES[params.source]
    guess = GUESSES[params.guess]
    light = LIGHTS[params.light]

    if not source_fits_scene(scene, source):
        raise StoryError(explain_scene_source(scene, source))
    if not guess_fits_source(guess, source):
        raise StoryError(explain_guess(source, guess))
    if not light_is_reasonable(light):
        raise StoryError(f"(No story: {light.label} is not treated as a safe investigating light here.)")

    world = tell(scene, source, guess, light, params.helper)
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
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: ASP gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    smoke_cases = list(CURATED)
    try:
        default_args = build_parser().parse_args([])
        smoke_cases.append(resolve_params(default_args, random.Random(123)))
    except StoryError as err:
        rc = 1
        print(f"SMOKE FAILURE while resolving default params: {err}")

    for params in smoke_cases:
        try:
            sample = generate(params)
            if not sample.story.strip():
                raise StoryError("Generated empty story.")
        except Exception as err:  # pragma: no cover - verification path
            rc = 1
            print(f"SMOKE FAILURE for params={params}: {err}")

    if rc == 0:
        print(f"OK: smoke-tested {len(smoke_cases)} generated stories.")
    return rc


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (scene, source, guess, light) combos:\n")
        for scene_id, source_id, guess_id, light_id in combos:
            print(f"  {scene_id:14} {source_id:10} {guess_id:8} {light_id}")
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
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### Twist: {p.source} in the bureau ({p.scene}, guessed {p.guess})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
