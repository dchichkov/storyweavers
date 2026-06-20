#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/crunch_dim_sound_effects_quest_pirate_tale.py
==============================================================================

A small, self-contained story world for a pirate-quest tale with sound effects
and a dim, crunchy mystery word ("crunch-dim"). The premise is simple: a child
pirate crew searches for a treasure clue in a dark cove, follows noisy clues,
mistakes danger for adventure, and finishes by finding a safer, brighter way to
continue the quest.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes
- a forward-chained causal engine
- a reasonableness gate and inline ASP twin
- three QA sets grounded in simulated state, not rendered text
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
DIM_MIN = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Sound:
    id: str
    label: str
    onomatopoeia: str
    effect: str
    clue: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Place:
    id: str
    label: str
    dim: bool
    hidden: str
    floor: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class QuestItem:
    id: str
    label: str
    phrase: str
    useful: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_tension(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["lost"] < THRESHOLD or e.meters["fear"] >= THRESHOLD:
            continue
        sig = ("tension", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["worry"] += 1
        out.append("__tension__")
    return out


def _r_crack(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters["lost"] < THRESHOLD:
            continue
        sig = ("crack", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["damage"] += 1
        out.append("__crack__")
    return out


CAUSAL_RULES = [
    Rule("tension", "social", _r_tension),
    Rule("crack", "physical", _r_crack),
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


def dim_place(place: Place) -> bool:
    return place.dim


def hazard(sound: Sound, place: Place) -> bool:
    return sound.effect == "echo" and place.dim


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for sid, sound in SOUNDS.items():
            for qid, quest in QUESTS.items():
                if hazard(sound, place) and quest.useful == "clue":
                    combos.append((pid, sid, qid))
    return combos


def reasonables() -> list[str]:
    return [r.id for r in sensible_responses()]


def story_outcome(params: "StoryParams") -> str:
    if params.delay <= 0:
        return "safe"
    if RESPONSES[params.response].power >= params.delay + 1:
        return "rescued"
    return "lost"


def _do_sound(world: World, sound: Sound, place: Place) -> None:
    world.get("hero").meters["lost"] += 1
    if place.dim:
        world.get("hero").memes["startled"] += 1
    propagate(world, narrate=False)


def predict(world: World, place: Place, sound: Sound) -> dict:
    sim = world.copy()
    _do_sound(sim, sound, place)
    return {
        "lost": sim.get("hero").meters["lost"] >= THRESHOLD,
        "damage": sim.get("hero").meters["damage"],
    }


def setup(world: World, hero: Entity, mate: Entity, place: Place, quest: QuestItem) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"On a moonlit evening, {hero.id} and {mate.id} turned the little ship into "
        f"a pirate quest. {place.label.capitalize()} was dim enough to hide clues, and "
        f"the map said the treasure was somewhere near {place.hidden}."
    )
    world.say(
        f'"Creak, swish, crunch-dim," {hero.id} whispered, and {mate.id} grinned at the '
        f'sound of the deck beneath {hero.pronoun("possessive")} boots.'
    )


def search(world: World, hero: Entity, mate: Entity, sound: Sound, place: Place, quest: QuestItem) -> None:
    world.say(
        f"They followed a faint trail toward {place.hidden}. Every step went "
        f"{sound.onomatopoeia}, and the noise made the dark feel bigger."
    )
    world.say(
        f"{mate.id} held the lantern higher. \"The clue should be near the {quest.label},\" "
        f"{mate.pronoun()} said, listening for anything that sounded like {sound.clue}."
    )


def warn(world: World, mate: Entity, hero: Entity, sound: Sound, place: Place) -> bool:
    pred = predict(world, place, sound)
    if not pred["lost"]:
        return False
    world.facts["predicted"] = pred
    world.say(
        f'{mate.id} blinked. "{hero.id}, that sound is too loud in a dim place. '
        f'If we rush, we could lose the clue and trip on the deck."'
    )
    mate.memes["caution"] += 1
    return True


def defy(world: World, hero: Entity, sound: Sound) -> None:
    hero.memes["bravado"] += 1
    world.say(
        f'"No fear," {hero.id} said, and charged after the sound with {sound.onomatopoeia}.'
    )


def call_out(world: World, mate: Entity, hero: Entity) -> None:
    mate.memes["trust"] += 1
    world.get("hero").memes["fear"] += 1
    world.say(
        f'But {mate.id} called out fast, and {hero.id} skidded to a stop '
        f'just before the floorboards gave a worrying little crack.'
    )


def rescue(world: World, parent: Entity, response: Response, quest: QuestItem) -> None:
    world.get("hero").meters["lost"] = 0
    body = response.text.replace("{target}", quest.label)
    world.say(
        f"{parent.label_word.capitalize()} came from the cabin and {body}."
    )
    world.say(
        f"The clue was safe again, and the treasure hunt could continue without the danger."
    )


def rescue_fail(world: World, parent: Entity, response: Response, quest: QuestItem) -> None:
    world.get("hero").meters["damage"] += 1
    body = response.fail.replace("{target}", quest.label)
    world.say(f"{parent.label_word.capitalize()} hurried over and {body}.")
    world.say(
        f"The map fluttered away in the dark, and the crew had to back off to the brighter deck."
    )


def finish_safe(world: World, hero: Entity, mate: Entity, place: Place, quest: QuestItem) -> None:
    hero.memes["joy"] += 1
    mate.memes["joy"] += 1
    world.say(
        f"In the end, they used a bright lantern path instead of chasing the crunch-dim sound. "
        f"{hero.id} found the clue near {place.floor}, right beside the {quest.label}, "
        f"and both pirates laughed when the lantern lit the whole deck gold."
    )


def finish_lost(world: World, hero: Entity, mate: Entity, place: Place) -> None:
    hero.memes["fear"] += 1
    mate.memes["fear"] += 1
    world.say(
        f"The dark cove grew quiet. They backed away, counted their steps, and promised to return "
        f"with a safer plan and a better light."
    )


def tell(place: Place, sound: Sound, quest: QuestItem, response: Response,
         hero_name: str = "Mara", hero_gender: str = "girl",
         mate_name: str = "Pip", mate_gender: str = "boy",
         parent_type: str = "mother", delay: int = 0) -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, role="captain"))
    mate = world.add(Entity(id=mate_name, kind="character", type=mate_gender, role="mate"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    world.add(Entity(id="deck", type="place", label="the deck"))
    world.add(Entity(id="map", type="thing", label="the map"))
    world.facts["place"] = place
    world.facts["sound"] = sound
    world.facts["quest"] = quest
    world.facts["response"] = response
    world.facts["delay"] = delay

    setup(world, hero, mate, place, quest)
    world.para()
    search(world, hero, mate, sound, place, quest)
    warn(world, mate, hero, sound, place)
    if delay <= 0:
        world.say(f'"{sound.onomatopoeia}!"' )
        finish_safe(world, hero, mate, place, quest)
        outcome = "safe"
    else:
        defy(world, hero, sound)
        hero.meters["lost"] += 1
        call_out(world, mate, hero)
        severity = delay + 1
        if response.power >= severity:
            rescue(world, parent, response, quest)
            finish_safe(world, hero, mate, place, quest)
            outcome = "rescued"
        else:
            rescue_fail(world, parent, response, quest)
            finish_lost(world, hero, mate, place)
            outcome = "lost"

    world.facts["outcome"] = outcome
    world.facts["hero"] = hero
    world.facts["mate"] = mate
    world.facts["parent"] = parent
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale with the words "crunch-dim" and a hidden clue in a dark cove.',
        f"Tell a pirate-quest story where {f['hero'].id} and {f['mate'].id} follow a noisy clue toward {f['place'].label}, but choose a safer light by the end.",
        f'Write a child-friendly pirate adventure that uses the sound word "{f["sound"].onomatopoeia}" and ends with a treasure hunt clue being found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, mate, place, quest, response = f["hero"], f["mate"], f["place"], f["quest"], f["response"]
    qa = [
        QAItem(
            question="What were the pirates searching for?",
            answer=f"They were searching for a clue to the treasure, and the clue was tied to the {quest.label}. The hunt mattered because the cove was too dim to see well without help.",
        ),
        QAItem(
            question="Why did the mate warn the hero?",
            answer=f"The mate warned the hero because the sound felt risky in a dim place and could make them lose the clue or trip. The warning came from thinking ahead, not from being unkind.",
        ),
    ]
    if f["outcome"] == "rescued":
        qa.append(
            QAItem(
                question="How did the grown-up help?",
                answer=f"The grown-up used {response.qa_text.replace('{target}', quest.label)}. That quick help kept the quest going and made the deck safe again.",
            )
        )
    elif f["outcome"] == "lost":
        qa.append(
            QAItem(
                question="What happened when the rescue was not enough?",
                answer=f"The rescue was too weak, so the danger stayed and the crew had to back away. They left the dim cove and looked for a brighter, safer plan instead.",
            )
        )
    else:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer="It ended safely, with the pirates finding the clue by using a bright lantern path instead of chasing the dark noise. The last image shows them happy, steady, and ready for the next part of the quest.",
            )
        )
    return qa


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question="What does a lantern do on a pirate ship?",
            answer="A lantern gives bright, safe light without making a real flame or adding more danger. Pirates use it to see their way in the dark.",
        ),
        QAItem(
            question="Why is a dim place important in a quest story?",
            answer="A dim place hides clues and makes the search feel tricky. It also means the crew must choose careful steps and use good light.",
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect makes the story feel alive and helps show what the pirates hear. It can also warn that something strange or exciting is nearby.",
        ),
    ]


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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


@dataclass
@dataclass
class StoryParams:
    place: str
    sound: str
    quest: str
    response: str
    hero: str
    hero_gender: str
    mate: str
    mate_gender: str
    parent: str
    delay: int = 0
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


PLACES = {
    "cove": Place("cove", "the cove", True, "the hidden rocks", "the deck", {"dim", "quest"}),
    "bay": Place("bay", "the bay", True, "the tidepool path", "the floorboards", {"dim", "quest"}),
    "island": Place("island", "the island inlet", True, "the cave mouth", "the sandy path", {"dim", "quest"}),
}

SOUNDS = {
    "crunch_dim": Sound("crunch_dim", "crunch-dim", "crunch-dim", "echo", "clink of a clue", True, {"sound", "pirate"}),
    "creak": Sound("creak", "creak", "creak", "echo", "wood shifting", True, {"sound", "pirate"}),
    "swish": Sound("swish", "swish", "swish", "echo", "lantern rope", True, {"sound", "pirate"}),
}

QUESTS = {
    "map_key": QuestItem("map_key", "map key", "a map key", "clue", {"quest"}),
    "shell_compass": QuestItem("shell_compass", "shell compass", "a shell compass", "clue", {"quest"}),
    "coin_box": QuestItem("coin_box", "coin box", "a coin box", "clue", {"quest"}),
}

RESPONSES = {
    "lantern": Response("lantern", 3, 3, "lit a lantern and swept the beam across the rocks", "lit a lantern, but it was too dim and wobbly to help", "used a lantern to light the way", {"light"}),
    "flares": Response("flares", 2, 2, "fired a flare and made enough light to find the clue", "used a flare, but the light sputtered out before they could see anything", "fired a flare to make light", {"light"}),
    "torch": Response("torch", 1, 1, "grabbed a torch and rushed ahead", "tried a torch, but it was not enough to beat the dark cove", "used a torch", {"light"}),
}

GIRL_NAMES = ["Mara", "Nia", "Ruby", "Luna", "Tess", "Ivy"]
BOY_NAMES = ["Pip", "Finn", "Jude", "Otis", "Beck", "Rowan"]
TRAITS = ["brave", "curious", "cheerful", "bold", "quick", "careful"]

CURATED = [
    StoryParams("cove", "crunch_dim", "map_key", "lantern", "Mara", "girl", "Pip", "boy", "mother", 1),
    StoryParams("bay", "creak", "shell_compass", "flares", "Finn", "boy", "Nia", "girl", "father", 2),
    StoryParams("island", "swish", "coin_box", "lantern", "Ruby", "girl", "Otis", "boy", "mother", 0),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate quest storyworld with sound effects and a crunch-dim clue.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--mate")
    ap.add_argument("--mate-gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def explain_rejection(place: Place, sound: Sound, quest: QuestItem) -> str:
    if not place.dim:
        return "(No story: this cove is not dim enough for a crunchy pirate quest.)"
    if sound.effect != "echo":
        return "(No story: the sound does not behave like a clue-hunting echo.)"
    return "(No story: the combination does not make a believable quest.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place and args.sound and args.quest:
        if (args.place, args.sound, args.quest) not in combos:
            raise StoryError(explain_rejection(PLACES[args.place], SOUNDS[args.sound], QUESTS[args.quest]))
    choices = [c for c in combos if (args.place is None or c[0] == args.place) and (args.sound is None or c[1] == args.sound) and (args.quest is None or c[2] == args.quest)]
    if not choices:
        raise StoryError("(No valid combination matches the given options.)")
    place, sound, quest = rng.choice(sorted(choices))
    response = args.response or rng.choice(sorted(RESPONSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    mate_gender = args.mate_gender or ("boy" if hero_gender == "girl" else "girl")
    hero = args.hero or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    mate = args.mate or rng.choice([n for n in (GIRL_NAMES if mate_gender == "girl" else BOY_NAMES) if n != hero])
    parent = args.parent or rng.choice(["mother", "father"])
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    return StoryParams(place, sound, quest, response, hero, hero_gender, mate, mate_gender, parent, delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], SOUNDS[params.sound], QUESTS[params.quest], RESPONSES[params.response], params.hero, params.hero_gender, params.mate, params.mate_gender, params.parent, params.delay)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.dim:
            lines.append(asp.fact("dim", pid))
    for sid, s in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("effect", sid, s.effect))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,Q) :- place(P), sound(S), quest(Q), dim(P), effect(S,echo).
sensible(R) :- response(R), sense(R,N), sense_min(M), N >= M.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos differ.")
        rc = 1
    if set(asp_sensible()) != set(RESPONSES):
        print("MISMATCH: ASP and Python sensible responses differ.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
    except Exception as exc:
        print(f"MISMATCH: generation smoke test failed: {exc}")
        rc = 1
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for p, s, q in asp_valid_combos():
            print(f"{p:8} {s:12} {q}")
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
            header = f"### {p.hero} & {p.mate}: {p.sound} at {p.place} ({story_outcome(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
