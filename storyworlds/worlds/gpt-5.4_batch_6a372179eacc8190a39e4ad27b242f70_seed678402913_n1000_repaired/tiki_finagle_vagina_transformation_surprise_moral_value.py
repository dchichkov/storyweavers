#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/tiki_finagle_vagina_transformation_surprise_moral_value.py
=====================================================================================

A standalone storyworld for a gentle ghost-story domain: a child hears a spooky
sign in a dark house, reaches for a small tiki keepsake, and learns that brave,
respectful words calm fear better than silly teasing. The turning point is a
transformation: what seemed like a frightening ghost becomes a shy house spirit
once the child stops trying to finagle courage with a foolish rhyme and instead
uses real words kindly.

The seed words "tiki", "finagle", and "vagina" appear in-story. The body-word
moment is handled respectfully: the child is corrected that "vagina" is a real
body word, not a joke or a magic ghost word.

Run it
------
    python storyworlds/worlds/gpt-5.4/tiki_finagle_vagina_transformation_surprise_moral_value.py
    python storyworlds/worlds/gpt-5.4/tiki_finagle_vagina_transformation_surprise_moral_value.py --place bathroom --omen mirror_message --tiki soap_tiki
    python storyworlds/worlds/gpt-5.4/tiki_finagle_vagina_transformation_surprise_moral_value.py --response mocking_spell
    python storyworlds/worlds/gpt-5.4/tiki_finagle_vagina_transformation_surprise_moral_value.py --all
    python storyworlds/worlds/gpt-5.4/tiki_finagle_vagina_transformation_surprise_moral_value.py --verify
"""

from __future__ import annotations

import argparse
import copy
import io
import json
import os
import random
import sys
from collections import defaultdict
from contextlib import redirect_stdout
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
RESPECT_MIN = 2


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
        male = {"boy", "father", "grandfather", "man"}
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
        }.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    phrase: str
    surfaces: set[str] = field(default_factory=set)
    mood: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Omen:
    id: str
    label: str
    requires: str
    text: str
    reveal: str
    scare: int
    tags: set[str] = field(default_factory=set)


@dataclass
class TikiItem:
    id: str
    label: str
    phrase: str
    rooms: set[str] = field(default_factory=set)
    glow: int = 0
    surprise: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    respect: int
    calm: int
    action: str
    reveal_line: str
    fail_line: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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
        clone = World(self.place)
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


def _r_chill(world: World) -> list[str]:
    omen = world.entities.get("omen")
    room = world.entities.get("room")
    hero = world.entities.get("hero")
    if omen is None or room is None or hero is None:
        return []
    if omen.meters["active"] < THRESHOLD:
        return []
    sig = ("chill",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    room.meters["chill"] += 1
    hero.memes["fear"] += 1
    return []


def _r_transform(world: World) -> list[str]:
    omen = world.entities.get("omen")
    hero = world.entities.get("hero")
    room = world.entities.get("room")
    if omen is None or hero is None or room is None:
        return []
    if omen.meters["softened"] < THRESHOLD:
        return []
    sig = ("transform",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    omen.meters["transformed"] += 1
    room.meters["chill"] = 0.0
    hero.memes["fear"] = 0.0
    hero.memes["wonder"] += 1
    return []


CAUSAL_RULES = [
    Rule(name="chill", tag="physical", apply=_r_chill),
    Rule(name="transform", tag="emotional", apply=_r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                produced.extend(lines)
                changed = True
            elif any(sig[0] == rule.name for sig in world.fired):
                pass
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def place_supports_omen(place: Place, omen: Omen) -> bool:
    return omen.requires in place.surfaces


def tiki_fits_place(tiki: TikiItem, place: Place) -> bool:
    return place.id in tiki.rooms


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for omen_id, omen in OMENS.items():
            if not place_supports_omen(place, omen):
                continue
            for tiki_id, tiki in TIKIS.items():
                if tiki_fits_place(tiki, place):
                    combos.append((place_id, omen_id, tiki_id))
    return combos


def sensible_responses() -> list[Response]:
    return [resp for resp in RESPONSES.values() if resp.respect >= RESPECT_MIN]


def response_strength(response: Response, tiki: TikiItem) -> int:
    return response.calm + tiki.glow


def omen_pressure(omen: Omen, delay: int) -> int:
    return omen.scare + delay


def transformed(response: Response, tiki: TikiItem, omen: Omen, delay: int) -> bool:
    return response_strength(response, tiki) >= omen_pressure(omen, delay)


@dataclass
class StoryParams:
    place: str
    omen: str
    tiki: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_type: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def introduce(world: World, hero: Entity, helper: Entity, tiki: TikiItem) -> None:
    place = world.place
    hero.memes["curious"] += 1
    world.say(
        f"On a windy night, {hero.id} stayed awake in {place.phrase}. "
        f"{place.mood}"
    )
    world.say(
        f"Near the bed sat {tiki.phrase}, a little tiki keepsake that {helper.id} "
        f"said had watched over the house for years."
    )


def hush_before_omen(world: World, hero: Entity) -> None:
    world.say(
        f"The boards gave a long creak, and even brave {hero.id} pulled the blanket "
        f"closer under {hero.pronoun('possessive')} chin."
    )


def omen_appears(world: World, hero: Entity, omen_cfg: Omen) -> None:
    omen = world.get("omen")
    omen.meters["active"] += 1
    propagate(world, narrate=False)
    world.say(omen_cfg.text)
    if hero.memes["fear"] >= THRESHOLD:
        world.say(
            f"A cold shiver ran through {hero.id}. For a moment, the room felt full "
            f"of watching silence."
        )


def temptation(world: World, hero: Entity) -> None:
    hero.memes["tempted"] += 1
    world.say(
        f"{hero.id} almost tried to finagle {hero.pronoun('possessive')} fear away "
        f"with a foolish rhyme an older cousin had once used for teasing."
    )
    world.say(
        f'"Maybe if I whisper a silly magic word," {hero.pronoun()} murmured, '
        f'"even the word vagina, the ghost will run."'
    )


def correction(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["embarrassment"] += 1
    helper.memes["care"] += 1
    world.say(
        f'But {helper.id} touched the blanket gently and shook {helper.pronoun("possessive")} head. '
        f'"No, {hero.id}," {helper.pronoun()} said softly. '
        f'"Vagina is a real body word. It is not a joke word and not a ghost word. '
        f'In this house, we use real words with respect."'
    )


def choose_response(world: World, hero: Entity, helper: Entity, response: Response, tiki: TikiItem) -> None:
    hero.memes["respect"] += float(response.respect)
    hero.memes["bravery"] += float(response.calm)
    world.say(response.action.format(hero=hero.id, helper=helper.id, tiki=tiki.label))
    if tiki.glow > 0:
        world.say(
            f"As {hero.id} held the {tiki.label}, a small honey-colored light "
            f"spread over the walls."
        )


def reveal(world: World, hero: Entity, helper: Entity, omen_cfg: Omen, tiki: TikiItem, response: Response) -> None:
    omen = world.get("omen")
    omen.meters["softened"] += 1
    propagate(world, narrate=False)
    world.say(response.reveal_line.format(hero=hero.id, helper=helper.id))
    world.say(omen_cfg.reveal)
    world.say(tiki.surprise)
    world.say(
        f"{hero.id} gave a shaky laugh. The scary shape had not wanted to hurt anyone. "
        f"It had wanted someone to be brave enough to be kind."
    )


def unresolved_ending(world: World, hero: Entity, helper: Entity, response: Response) -> None:
    hero.memes["fear"] += 1
    world.say(response.fail_line.format(hero=hero.id, helper=helper.id))
    world.say(
        f"So {helper.id} stayed beside {hero.id} until morning, and the room slowly "
        f"stopped feeling so sharp and strange."
    )
    world.say(
        f"{hero.id} learned that a silly trick could not fix every fear. Quiet truth "
        f"and patient company were stronger."
    )


def bright_moral(world: World, hero: Entity, helper: Entity, tiki: TikiItem) -> None:
    hero.memes["relief"] += 1
    hero.memes["love"] += 1
    world.say(
        f'Before sleeping, {hero.id} whispered, "I will not use words to tease." '
        f'{helper.id} smiled and tucked the blanket snugly around {hero.pronoun("object")}.'
    )
    world.say(
        f"By the window, the little {tiki.label} no longer looked grim at all. "
        f"It looked as if it were guarding the room with a secret smile."
    )


def tell(
    place: Place,
    omen_cfg: Omen,
    tiki_cfg: TikiItem,
    response_cfg: Response,
    child_name: str = "Mira",
    child_gender: str = "girl",
    helper_name: str = "Grandma",
    helper_type: str = "grandmother",
    trait: str = "curious",
    delay: int = 0,
) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_gender,
        role="hero",
        label=child_name,
        attrs={"trait": trait},
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=helper_type,
        role="helper",
        label=helper_name,
    ))
    room = world.add(Entity(
        id="room",
        type="room",
        label=place.label,
    ))
    omen = world.add(Entity(
        id="omen",
        type="spirit",
        label=omen_cfg.label,
    ))
    tiki = world.add(Entity(
        id="tiki",
        type="talisman",
        label=tiki_cfg.label,
    ))
    hero.memes["caution"] = 2.0 if trait in {"careful", "gentle", "thoughtful"} else 1.0

    introduce(world, hero, helper, tiki_cfg)
    hush_before_omen(world, hero)

    world.para()
    omen_appears(world, hero, omen_cfg)
    temptation(world, hero)
    correction(world, hero, helper)

    for _ in range(delay):
        hero.memes["fear"] += 1
        room.meters["chill"] += 1

    world.para()
    choose_response(world, hero, helper, response_cfg, tiki_cfg)

    good = transformed(response_cfg, tiki_cfg, omen_cfg, delay)
    if good:
        reveal(world, hero, helper, omen_cfg, tiki_cfg, response_cfg)
        world.para()
        bright_moral(world, hero, helper, tiki_cfg)
        outcome = "transformed"
    else:
        unresolved_ending(world, hero, helper, response_cfg)
        world.para()
        bright_moral(world, hero, helper, tiki_cfg)
        outcome = "comforted"

    world.facts.update(
        hero=hero,
        helper=helper,
        place=place,
        omen_cfg=omen_cfg,
        tiki_cfg=tiki_cfg,
        response=response_cfg,
        delay=delay,
        outcome=outcome,
        transformed=(outcome == "transformed"),
    )
    return world


PLACES = {
    "bathroom": Place(
        id="bathroom",
        label="bathroom",
        phrase="the old upstairs bathroom",
        surfaces={"mirror", "sink", "tile"},
        mood="Rain tapped the small window, and the mirror held a pale moon-shaped glow.",
        tags={"bathroom", "mirror"},
    ),
    "bedroom": Place(
        id="bedroom",
        label="bedroom",
        phrase="the guest bedroom at the end of the hall",
        surfaces={"window", "curtain", "bed"},
        mood="The curtains breathed in and out with the storm, and the shadows looked taller than daytime shadows.",
        tags={"bedroom", "window"},
    ),
    "hallway": Place(
        id="hallway",
        label="hallway",
        phrase="the narrow hallway beside the stairs",
        surfaces={"mirror", "window", "floor"},
        mood="The hall lamp was off, and the long runner rug drank up every small sound.",
        tags={"hallway", "mirror", "window"},
    ),
}

OMENS = {
    "mirror_message": Omen(
        id="mirror_message",
        label="misty writing",
        requires="mirror",
        text="A line of misty writing bloomed on the mirror as if an invisible finger had traced it there.",
        reveal="Then the white marks curled into the shape of a tiny bowed spirit, no bigger than a teacup, who seemed more shy than frightening.",
        scare=2,
        tags={"mirror", "ghost"},
    ),
    "window_face": Omen(
        id="window_face",
        label="window face",
        requires="window",
        text="A pale face seemed to float in the dark window, and the glass gave one soft, unhappy tap.",
        reveal="The face melted into a silver puff like breath on winter air, and inside it blinked two kind eyes full of relief.",
        scare=3,
        tags={"window", "ghost"},
    ),
    "curtain_shadow": Omen(
        id="curtain_shadow",
        label="curtain shadow",
        requires="curtain",
        text="A tall shadow rose in the curtain folds as if someone had stood up inside the cloth itself.",
        reveal="But when the cloth settled, the tall shape folded into a round little guardian with a paper-thin grin, almost silly in its smallness.",
        scare=2,
        tags={"curtain", "ghost"},
    ),
}

TIKIS = {
    "soap_tiki": TikiItem(
        id="soap_tiki",
        label="tiki soap dish",
        phrase="a small green tiki soap dish",
        rooms={"bathroom"},
        glow=1,
        surprise="A drop of water slid down the soap dish and caught the light, making the tiny carved face seem to wink.",
        tags={"tiki", "bathroom"},
    ),
    "night_tiki": TikiItem(
        id="night_tiki",
        label="tiki night-light",
        phrase="a wooden tiki night-light with a tiny amber bulb",
        rooms={"bedroom", "hallway"},
        glow=2,
        surprise="The tiki night-light clicked on by itself and painted a warm gold circle on the floor, as if the house had answered with its own yes.",
        tags={"tiki", "light"},
    ),
    "shell_tiki": TikiItem(
        id="shell_tiki",
        label="tiki shell charm",
        phrase="a little tiki shell charm hanging from blue string",
        rooms={"hallway", "bedroom"},
        glow=1,
        surprise="The shell charm gave one bright clink, and the sound was so cheerful that the last of the dread broke apart.",
        tags={"tiki", "shell"},
    ),
}

RESPONSES = {
    "name_kindly": Response(
        id="name_kindly",
        label="name kindly",
        respect=3,
        calm=1,
        action='"I am scared," {hero} said, "but I will speak kindly in this room." Then {helper} helped {hero} hold the {tiki} steady and breathe slowly.',
        reveal_line='At once, the hard feeling in the air loosened, as if the room had been waiting for exactly those honest words.',
        fail_line='The air did soften a little, but the dark corners still trembled. Honest words helped, though the room stayed uneasy for a while.',
        tags={"honesty", "respect"},
    ),
    "wipe_and_lamp": Response(
        id="wipe_and_lamp",
        label="wipe and lamp",
        respect=3,
        calm=2,
        action='{helper} handed {hero} a soft cloth. Together they wiped away the scary mark, set the {tiki} where its light could shine, and said that this house was for truth, not teasing.',
        reveal_line='As the last damp streak vanished, the room gave a small sigh, and the shadowed shape seemed to bow in thanks.',
        fail_line='They cleaned and lit the room, which made it safer, but the spirit did not fully change before bedtime.',
        tags={"cleaning", "respect", "light"},
    ),
    "mocking_spell": Response(
        id="mocking_spell",
        label="mocking spell",
        respect=0,
        calm=1,
        action='{hero} tried a sing-song spell instead, squeezing the {tiki} too hard and hoping a trick would do the work of courage.',
        reveal_line='',
        fail_line='The rhyme only made the room feel meaner, not kinder. Tricks and teasing fed the fear instead of shrinking it.',
        tags={"teasing"},
    ),
}

GIRL_NAMES = ["Mira", "Lena", "Nora", "Ivy", "June", "Tessa", "Molly", "Etta"]
BOY_NAMES = ["Owen", "Miles", "Theo", "Eli", "Jude", "Simon", "Nico", "Felix"]
TRAITS = ["curious", "careful", "gentle", "bold", "thoughtful", "quiet"]


CURATED = [
    StoryParams(
        place="bathroom",
        omen="mirror_message",
        tiki="soap_tiki",
        response="wipe_and_lamp",
        child_name="Mira",
        child_gender="girl",
        helper_name="Grandma",
        helper_type="grandmother",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        place="bedroom",
        omen="window_face",
        tiki="night_tiki",
        response="wipe_and_lamp",
        child_name="Theo",
        child_gender="boy",
        helper_name="Grandpa",
        helper_type="grandfather",
        trait="thoughtful",
        delay=0,
    ),
    StoryParams(
        place="hallway",
        omen="window_face",
        tiki="shell_tiki",
        response="name_kindly",
        child_name="Nora",
        child_gender="girl",
        helper_name="Grandma",
        helper_type="grandmother",
        trait="careful",
        delay=1,
    ),
    StoryParams(
        place="bedroom",
        omen="curtain_shadow",
        tiki="shell_tiki",
        response="name_kindly",
        child_name="Miles",
        child_gender="boy",
        helper_name="Grandma",
        helper_type="grandmother",
        trait="quiet",
        delay=1,
    ),
]


KNOWLEDGE = {
    "ghost": [
        (
            "What is a ghost story?",
            "A ghost story is a spooky kind of story about strange sounds, shadows, or spirits. In a gentle ghost story, the scary part often leads to a kind or surprising ending.",
        )
    ],
    "tiki": [
        (
            "What is a tiki?",
            "A tiki is a carved figure or face used as decoration in some art styles. In this story, the tiki object is a small keepsake that helps the room feel less dark.",
        )
    ],
    "mirror": [
        (
            "Why can a mirror look spooky at night?",
            "A mirror can reflect shadows, raindrops, and dim light in odd ways. That can make ordinary things look strange when a room is dark.",
        )
    ],
    "window": [
        (
            "Why can a window look scary in a storm?",
            "Rain and darkness can blur a window, and your own reflection can mix with what is outside. That can make a shape look like a face for a moment.",
        )
    ],
    "honesty": [
        (
            "Why is it brave to say you are scared?",
            "Saying you are scared is honest, and honesty lets other people help you. Naming a feeling calmly can make it smaller and easier to face.",
        )
    ],
    "respect": [
        (
            "Why should words be used respectfully?",
            "Words can comfort people or hurt them. Using real words respectfully shows kindness and helps a home feel safe.",
        )
    ],
    "body_words": [
        (
            "Is vagina a silly magic word?",
            "No. Vagina is a real body word. Real body words should be said respectfully, not used for teasing or jokes.",
        )
    ],
    "light": [
        (
            "Why does a small light help at night?",
            "A small light helps your eyes see what is really there. When shadows become clearer, they often feel less frightening.",
        )
    ],
}
KNOWLEDGE_ORDER = ["ghost", "tiki", "mirror", "window", "honesty", "respect", "body_words", "light"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    omen = f["omen_cfg"]
    tiki = f["tiki_cfg"]
    return [
        'Write a gentle ghost story for a 3-to-5-year-old that includes the words "tiki", "finagle", and "vagina", and ends with a kind moral.',
        f"Tell a spooky-but-soft story where {hero.id} sees {omen.label} in {place.phrase}, reaches for {tiki.phrase}, and learns that respectful words are stronger than teasing.",
        f"Write a short transformation story in a ghost-story style where {helper.id} helps {hero.id} face fear honestly, and the surprise is that the ghost was not mean at all.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    omen = f["omen_cfg"]
    tiki = f["tiki_cfg"]
    response = f["response"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {hero.id}, who felt frightened by a strange sign in {place.phrase}, and {helper.id}, who stayed close and helped. The little {tiki.label} also mattered because it brought a warm point of light into the scene.",
        ),
        (
            "What spooky thing happened first?",
            f"The first spooky thing was {omen.text[0].lower() + omen.text[1:] if omen.text else omen.label}. That strange sign made the room feel colder and raised {hero.id}'s fear.",
        ),
        (
            f"Why did {helper.id} stop {hero.id} from using the word vagina as a ghost trick?",
            f"{helper.id} explained that vagina is a real body word, not a joke word and not a magic spell. The lesson was about respect, because real words about bodies should be used kindly instead of for teasing.",
        ),
        (
            f"What did {hero.id} do instead of trying to finagle away the fear?",
            f"{hero.id} followed a calmer plan: {response.action.format(hero=hero.id, helper=helper.id, tiki=tiki.label)} That action worked better because it used honesty, care, and light instead of a silly trick.",
        ),
    ]
    if outcome == "transformed":
        qa.append(
            (
                "How did the ghost change?",
                f"The scary sign softened and turned into a shy little spirit. That transformation happened after the room was treated with respect instead of teasing.",
            )
        )
        qa.append(
            (
                "What was the surprise?",
                f"The surprise was that the ghost was not trying to be cruel. It seemed to be waiting for someone to bring kindness and truthful words into the room.",
            )
        )
    else:
        qa.append(
            (
                "Did everything stop feeling scary right away?",
                f"No. The fear eased, but it took time for the room to feel normal again. That showed {hero.id} that patient comfort can matter even when a problem does not vanish all at once.",
            )
        )
    qa.append(
        (
            "What is the moral of the story?",
            f"The moral is that fear should be met with honest, respectful words instead of teasing or mean jokes. Kindness changed the room more deeply than any pretend spell could.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags: set[str] = {"ghost", "tiki", "honesty", "respect", "body_words"}
    place = f["place"]
    omen = f["omen_cfg"]
    response = f["response"]
    if "mirror" in place.tags or "mirror" in omen.tags:
        tags.add("mirror")
    if "window" in place.tags or "window" in omen.tags:
        tags.add("window")
    if "light" in response.tags or f["tiki_cfg"].glow > 0:
        tags.add("light")
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(sig[0] for sig in world.fired))}")
    return "\n".join(lines)


def explain_rejection(place: Place, omen: Omen, tiki: Optional[TikiItem] = None) -> str:
    if not place_supports_omen(place, omen):
        return (
            f"(No story: {place.label} has {sorted(place.surfaces)}, but {omen.label} needs a "
            f"{omen.requires}. Pick a place where that spooky sign could really happen.)"
        )
    if tiki is not None and not tiki_fits_place(tiki, place):
        return (
            f"(No story: the {tiki.label} does not belong in the {place.label}. "
            f"Choose a tiki object that fits that room.)"
        )
    return "(No story: that combination does not make a grounded ghost scene.)"


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{response_id}': it is not respectful enough "
        f"(respect={response.respect} < {RESPECT_MIN}). This world only tells "
        f"stories where the child-facing solution models kindness. Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    response = RESPONSES[params.response]
    tiki = TIKIS[params.tiki]
    omen = OMENS[params.omen]
    return "transformed" if transformed(response, tiki, omen, params.delay) else "comforted"


ASP_RULES = r"""
valid(P, O, T) :- place(P), omen(O), tiki(T), needs(O, S), has_surface(P, S), fits(T, P).
sensible(R) :- response(R), respect(R, V), respect_min(M), V >= M.

pressure(S + D) :- chosen_omen(O), scare(O, S), delay(D).
strength(C + G) :- chosen_response(R), calm(R, C), chosen_tiki(T), glow(T, G).

outcome(transformed) :- sensible_response, strength(X), pressure(Y), X >= Y.
outcome(comforted) :- sensible_response, strength(X), pressure(Y), X < Y.

sensible_response :- chosen_response(R), sensible(R).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place in PLACES.items():
        lines.append(asp.fact("place", place_id))
        for surface in sorted(place.surfaces):
            lines.append(asp.fact("has_surface", place_id, surface))
    for omen_id, omen in OMENS.items():
        lines.append(asp.fact("omen", omen_id))
        lines.append(asp.fact("needs", omen_id, omen.requires))
        lines.append(asp.fact("scare", omen_id, omen.scare))
    for tiki_id, tiki in TIKIS.items():
        lines.append(asp.fact("tiki", tiki_id))
        lines.append(asp.fact("glow", tiki_id, tiki.glow))
        for room in sorted(tiki.rooms):
            lines.append(asp.fact("fits", tiki_id, room))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("respect", response_id, response.respect))
        lines.append(asp.fact("calm", response_id, response.calm))
    lines.append(asp.fact("respect_min", RESPECT_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp

    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp

    scenario = "\n".join([
        asp.fact("chosen_omen", params.omen),
        asp.fact("chosen_tiki", params.tiki),
        asp.fact("chosen_response", params.response),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


def asp_verify() -> int:
    rc = 0

    c_valid = set(asp_valid_combos())
    p_valid = set(valid_combos())
    if c_valid == p_valid:
        print(f"OK: gate matches valid_combos() ({len(c_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_valid - p_valid:
            print("  only in clingo:", sorted(c_valid - p_valid))
        if p_valid - c_valid:
            print("  only in python:", sorted(p_valid - c_valid))

    c_sens = set(asp_sensible())
    p_sens = {resp.id for resp in sensible_responses()}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    parser = build_parser()
    for seed in range(100):
        try:
            params = resolve_params(parser.parse_args([]), random.Random(seed))
        except StoryError:
            continue
        cases.append(params)
    bad = 0
    for params in cases:
        if asp_outcome(params) != outcome_of(params):
            bad += 1
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with redirect_stdout(buf):
            emit(sample, trace=True, qa=True, header="### smoke test")
        if not sample.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke test generated and emitted a normal story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Gentle ghost-story world: a tiki keepsake, a spooky sign, and a lesson about respectful words."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--tiki", choices=TIKIS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the spooky feeling lingers before the child acts")
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["grandmother", "grandfather", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible combinations derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_child(rng: random.Random) -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return name, gender


def _pick_helper(rng: random.Random) -> tuple[str, str]:
    helper_type = rng.choice(["grandmother", "grandfather", "mother", "father"])
    default_name = {
        "grandmother": "Grandma",
        "grandfather": "Grandpa",
        "mother": "Mom",
        "father": "Dad",
    }[helper_type]
    return default_name, helper_type


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.omen:
        if not place_supports_omen(PLACES[args.place], OMENS[args.omen]):
            raise StoryError(explain_rejection(PLACES[args.place], OMENS[args.omen]))
    if args.place and args.tiki:
        if not tiki_fits_place(TIKIS[args.tiki], PLACES[args.place]):
            omen = OMENS[args.omen] if args.omen else next(iter(OMENS.values()))
            raise StoryError(explain_rejection(PLACES[args.place], omen, TIKIS[args.tiki]))
    if args.response and RESPONSES[args.response].respect < RESPECT_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.omen is None or combo[1] == args.omen)
        and (args.tiki is None or combo[2] == args.tiki)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place_id, omen_id, tiki_id = rng.choice(sorted(combos))
    response_id = args.response or rng.choice(sorted(resp.id for resp in sensible_responses()))
    child_name, child_gender = _pick_child(rng)
    helper_name, helper_type = _pick_helper(rng)
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 1)

    if args.child_name:
        child_name = args.child_name
    if args.child_gender:
        child_gender = args.child_gender
    if args.helper_name:
        helper_name = args.helper_name
    if args.helper_type:
        helper_type = args.helper_type

    return StoryParams(
        place=place_id,
        omen=omen_id,
        tiki=tiki_id,
        response=response_id,
        child_name=child_name,
        child_gender=child_gender,
        helper_name=helper_name,
        helper_type=helper_type,
        trait=trait,
        delay=delay,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        place = PLACES[params.place]
        omen = OMENS[params.omen]
        tiki = TIKIS[params.tiki]
        response = RESPONSES[params.response]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter: {exc.args[0]}.)") from None

    if not place_supports_omen(place, omen):
        raise StoryError(explain_rejection(place, omen))
    if not tiki_fits_place(tiki, place):
        raise StoryError(explain_rejection(place, omen, tiki))
    if response.respect < RESPECT_MIN:
        raise StoryError(explain_response(params.response))

    world = tell(
        place=place,
        omen_cfg=omen,
        tiki_cfg=tiki,
        response_cfg=response,
        child_name=params.child_name,
        child_gender=params.child_gender,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
        trait=params.trait,
        delay=params.delay,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, omen, tiki) combos:\n")
        for place_id, omen_id, tiki_id in combos:
            print(f"  {place_id:9} {omen_id:15} {tiki_id}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
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
            header = f"### {p.child_name}: {p.omen} in {p.place} ({p.tiki}, {outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
