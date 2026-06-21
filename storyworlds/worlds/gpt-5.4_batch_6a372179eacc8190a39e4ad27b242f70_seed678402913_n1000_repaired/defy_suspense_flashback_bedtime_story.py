#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/defy_suspense_flashback_bedtime_story.py
===================================================================

A standalone storyworld for a bedtime-suspense tale with a flashback:
a child hears a worrying night sound, remembers an earlier lesson, and either
stays tucked in to call for help or briefly defies the bedtime rule and creeps
toward the noise before a calm grown-up resolves it.

The world model treats physical state ("dark", "open", "ringing") and emotional
state ("fear", "calm", "bravery", "trust") as live simulation variables.
Rendered prose comes from that state and from the chosen cause of the sound.

Run it
------
    python storyworlds/worlds/gpt-5.4/defy_suspense_flashback_bedtime_story.py
    python storyworlds/worlds/gpt-5.4/defy_suspense_flashback_bedtime_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/defy_suspense_flashback_bedtime_story.py --all --qa
    python storyworlds/worlds/gpt-5.4/defy_suspense_flashback_bedtime_story.py --trace
    python storyworlds/worlds/gpt-5.4/defy_suspense_flashback_bedtime_story.py --verify
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

# Make the shared result containers importable when this script is run directly.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    openable: bool = False
    glowing: bool = False
    soft: bool = False
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
class Noise:
    id: str
    label: str
    phrase: str
    sound: str
    place: str
    cause_text: str
    reveal_text: str
    risk: int
    settled_by: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Comfort:
    id: str
    label: str
    phrase: str
    action: str
    warmth: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    calm_power: int
    requires_bed: bool
    action_text: str
    reveal_text: str
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


def _r_dark_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    room = world.get("room")
    if child.meters["awake"] >= THRESHOLD and room.meters["dark"] >= THRESHOLD:
        sig = ("dark_fear", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += 1
            out.append("__fear__")
    return out


def _r_noise_fear(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    noise = world.get("noise")
    if noise.meters["rattling"] >= THRESHOLD:
        sig = ("noise_fear", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["fear"] += max(1.0, noise.attrs.get("risk", 1))
            out.append("__fear__")
    return out


def _r_comfort_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    comfort = world.get("comfort")
    if comfort.meters["hugged"] >= THRESHOLD:
        sig = ("comfort", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["calm"] += comfort.attrs.get("warmth", 1)
            out.append("__calm__")
    return out


def _r_light_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    lamp = world.get("lamp")
    room = world.get("room")
    if lamp.meters["on"] >= THRESHOLD and room.meters["dark"] >= THRESHOLD:
        sig = ("lamp", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["dark"] = 0.0
            child.memes["calm"] += 1
            out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule(name="dark_fear", tag="emotional", apply=_r_dark_fear),
    Rule(name="noise_fear", tag="emotional", apply=_r_noise_fear),
    Rule(name="comfort", tag="emotional", apply=_r_comfort_calm),
    Rule(name="lamp", tag="physical", apply=_r_light_calm),
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


NOISES = {
    "shutter": Noise(
        id="shutter",
        label="loose shutter",
        phrase="a loose shutter by the window",
        sound="tap... tap-tap...",
        place="by the window",
        cause_text="the wind nudging the loose shutter",
        reveal_text="Outside, the wind was only tapping the loose shutter against the wall.",
        risk=1,
        settled_by="window_check",
        tags={"wind", "window", "night_sound"},
    ),
    "kitten": Noise(
        id="kitten",
        label="kitten",
        phrase="a tiny kitten on the porch",
        sound="mew... mew...",
        place="near the front step",
        cause_text="a tiny kitten crying on the porch",
        reveal_text="At the door sat a tiny kitten, making the small mewing sound all by itself.",
        risk=2,
        settled_by="door_peek",
        tags={"kitten", "night_sound"},
    ),
    "wagon": Noise(
        id="wagon",
        label="toy wagon",
        phrase="a toy wagon under the hall table",
        sound="rrrrk... clack...",
        place="in the hall",
        cause_text="a toy wagon rolling until one wheel bumped the table leg",
        reveal_text="In the hall, the toy wagon had rolled a little and knocked softly against the table leg.",
        risk=1,
        settled_by="hall_peek",
        tags={"toy", "hall", "night_sound"},
    ),
    "branch": Noise(
        id="branch",
        label="tree branch",
        phrase="a tree branch brushing the roof",
        sound="scritch... scritch...",
        place="above the room",
        cause_text="a tree branch brushing the roof",
        reveal_text="Above the room, a tree branch was only brushing the roof in the breeze.",
        risk=2,
        settled_by="window_check",
        tags={"tree", "roof", "night_sound"},
    ),
}

COMFORTS = {
    "blanket": Comfort(
        id="blanket",
        label="blanket",
        phrase="a moon-soft blanket",
        action="pulled the blanket up to the chin",
        warmth=1,
        tags={"blanket", "comfort"},
    ),
    "bear": Comfort(
        id="bear",
        label="teddy bear",
        phrase="a sleepy teddy bear",
        action="hugged the teddy bear close",
        warmth=2,
        tags={"bear", "comfort"},
    ),
    "pillow": Comfort(
        id="pillow",
        label="pillow",
        phrase="a cool pillow",
        action="rested one cheek on the pillow and listened",
        warmth=1,
        tags={"pillow", "comfort"},
    ),
}

RESPONSES = {
    "call_parent": Response(
        id="call_parent",
        label="call for a parent",
        sense=3,
        calm_power=3,
        requires_bed=True,
        action_text='called softly for {parent_word} instead of getting up',
        reveal_text="A sleepy grown-up voice answered at once, and warm footsteps came down the hall.",
        qa_text="called for a parent from bed",
        tags={"call_help", "bedtime"},
    ),
    "bell": Response(
        id="bell",
        label="ring the bedside bell",
        sense=3,
        calm_power=3,
        requires_bed=True,
        action_text='rang the little bedside bell that {parent_word} had left for nighttime worries',
        reveal_text="The bell gave one bright silver note, and a grown-up came right away.",
        qa_text="rang the bedside bell from bed",
        tags={"bell", "call_help", "bedtime"},
    ),
    "nightlight": Response(
        id="nightlight",
        label="switch on the night-light",
        sense=2,
        calm_power=2,
        requires_bed=False,
        action_text="switched on the night-light and watched the corners turn gentle again",
        reveal_text="With the room no longer so dark, the sound already seemed smaller.",
        qa_text="turned on the night-light before getting help",
        tags={"nightlight", "light", "bedtime"},
    ),
    "hall_peek": Response(
        id="hall_peek",
        label="peek into the hall",
        sense=1,
        calm_power=1,
        requires_bed=False,
        action_text="tiptoed to the doorway to peek into the hall alone",
        reveal_text="The long hall looked much longer at night, and every board seemed ready to creak.",
        qa_text="peeked into the hall alone",
        tags={"peek", "hall", "bedtime"},
    ),
}


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combo(noise_id: str, response_id: str) -> bool:
    noise = NOISES[noise_id]
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        return False
    if noise.risk >= 2 and response.id == "nightlight":
        return False
    return True


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for noise_id in NOISES:
        for response_id in RESPONSES:
            if valid_combo(noise_id, response_id):
                out.append((noise_id, response_id))
    return sorted(out)


def would_defy(trait: str, trust: int, flashback_strength: int, response_id: str) -> bool:
    if response_id == "hall_peek":
        return True
    if response_id in {"call_parent", "bell"}:
        return False
    urge = (3 if trait == "bold" else 2 if trait == "curious" else 1)
    return urge + trust > flashback_strength + 3


def resolved_quickly(noise: Noise, response: Response, defied: bool) -> bool:
    power = response.calm_power + (0 if defied else 1)
    return power >= noise.risk + 1


def predict_outcome(noise_id: str, response_id: str, trait: str, trust: int,
                    flashback_strength: int) -> str:
    noise = NOISES[noise_id]
    response = RESPONSES[response_id]
    defied = would_defy(trait, trust, flashback_strength, response_id)
    return "settled" if resolved_quickly(noise, response, defied) else "spooked"


def predict_safest(world: World) -> dict:
    child = world.get("child")
    best = None
    for response in sensible_responses():
        defied = would_defy(
            trait=child.attrs["trait"],
            trust=child.attrs["trust"],
            flashback_strength=child.attrs["flashback_strength"],
            response_id=response.id,
        )
        solved = resolved_quickly(world.facts["noise_cfg"], response, defied)
        score = (1 if solved else 0, response.sense, response.calm_power)
        if best is None or score > best["score"]:
            best = {
                "response": response.id,
                "defied": defied,
                "solved": solved,
                "score": score,
            }
    return best or {"response": "call_parent", "defied": False, "solved": True, "score": (0, 0, 0)}


def introduce(world: World, child: Entity, parent: Entity, comfort: Comfort) -> None:
    world.say(
        f"In a small quiet room, {child.id} snuggled under {comfort.phrase} while "
        f"{child.pronoun('possessive')} {parent.label_word} tucked the blanket smooth."
    )
    world.say(
        f'"Time to rest," {parent.label_word} whispered. "If the dark ever feels too big, '
        f'stay in bed and call for me."'
    )


def bedtime_detail(world: World, child: Entity) -> None:
    room = world.get("room")
    room.meters["dark"] = 1
    child.meters["awake"] = 1
    propagate(world, narrate=False)
    world.say(
        "Soon the house settled into hushes. The clock made a tiny tick, and the shadows "
        "in the corners looked deep and still."
    )


def start_noise(world: World, noise: Noise) -> None:
    noise_ent = world.get("noise")
    noise_ent.meters["rattling"] = 1
    propagate(world, narrate=False)
    world.say(
        f"Then, from {noise.place}, came a sound: {noise.sound} It was small, "
        f"but in the dark it seemed to hold its breath between each little noise."
    )


def comfort_beat(world: World, child: Entity, comfort: Comfort) -> None:
    comfort_ent = world.get("comfort")
    comfort_ent.meters["hugged"] = 1
    propagate(world, narrate=False)
    world.say(f"{child.id} {comfort.action}.")
    if child.memes["fear"] > child.memes["calm"]:
        world.say("The cozy feeling helped, but not enough to answer the question in the dark.")


def flashback(world: World, child: Entity, parent: Entity, response: Response) -> None:
    world.say(
        "Then a memory floated back, soft as a lantern in mist."
    )
    if response.id == "bell":
        world.say(
            f"Earlier that week, when thunder had muttered outside, {parent.label_word} had set a small bell "
            f"on the bedside table and said, \"You do not have to be brave all alone. Ring once, and I will come.\""
        )
    else:
        world.say(
            f"One evening before, when a closet door had creaked, {parent.label_word} had sat on the edge of the bed "
            f"and said, \"Night sounds can feel bigger than they are. You never have to chase them by yourself.\""
        )
    child.memes["memory"] += 1


def choose_response(world: World, child: Entity, parent: Entity, response: Response, defied: bool) -> None:
    lamp = world.get("lamp")
    if response.id == "nightlight":
        lamp.meters["on"] = 1
        propagate(world, narrate=False)
    if defied:
        child.memes["defiance"] += 1
        child.meters["out_of_bed"] = 1
        world.say(
            f"But the wondering feeling tugged harder than the memory. For one brave, shaky moment, "
            f"{child.id} decided to defy the rule and {response.action_text}."
        )
    else:
        child.memes["trust"] += 1
        world.say(
            f"{child.id} remembered the kind voice from before and {response.action_text}."
        )
    if response.id in {"call_parent", "bell"}:
        world.say(response.reveal_text.replace("{parent_word}", parent.label_word))
    elif response.id == "nightlight":
        world.say(response.reveal_text)
        world.say(f'After that, {child.id} called, "{parent.label_word.capitalize()}?"')
    else:
        world.say(response.reveal_text)


def reveal(world: World, parent: Entity, noise: Noise, response: Response, defied: bool, settled: bool) -> None:
    child = world.get("child")
    if response.id == "hall_peek":
        world.say(
            f"Before {child.id} could take another step, {parent.label_word} opened the bedroom door and knelt beside "
            f"{child.pronoun('object')} in the dim hall."
        )
    else:
        world.say(
            f"In a moment, {parent.label_word} came close, listened once, and smiled the small calm smile "
            f"grown-ups use when they already know the night is gentler than it sounds."
        )
    world.say(noise.reveal_text)
    if settled:
        child.memes["fear"] = 0.0
        child.memes["calm"] += 2
        world.say(
            f'"There it is," {parent.label_word} said. "Only {noise.cause_text}." '
            f'The sound did not seem like a monster now. It seemed like part of the house telling the truth.'
        )
    else:
        child.memes["fear"] = 1.0
        child.memes["calm"] += 1
        world.say(
            f'"There it is," {parent.label_word} said. "Only {noise.cause_text}." '
            f'Even so, the night still felt a little prickly, so {parent.pronoun()} stayed until every shadow softened.'
        )


def ending(world: World, child: Entity, parent: Entity, comfort: Comfort, defied: bool, settled: bool) -> None:
    world.say(
        f"{parent.label_word.capitalize()} walked {child.pronoun('object')} back to bed and tucked {comfort.phrase} around "
        f"{child.pronoun('object')} again."
    )
    if defied:
        world.say(
            f'"Next time," {parent.label_word} whispered, "let me come to the mystery. You do not need to go to it." '
            f"{child.id} nodded and tucked both feet safely under the covers."
        )
    else:
        world.say(
            f'"You did just the right thing," {parent.label_word} whispered. "{parent.pronoun().capitalize()} will always come."'
        )
    if settled:
        world.say(
            f"Soon the same house that had sounded so strange felt sleepy again, and {child.id} drifted off while "
            f"the little night noises turned into ordinary, harmless music."
        )
    else:
        world.say(
            f"After a long cuddle, the room finally grew gentle enough for sleep, and {child.id}'s breathing slowed "
            f"until the dark was only dark and nothing more."
        )


def tell(noise: Noise, comfort: Comfort, response: Response, child_name: str,
         child_gender: str, parent_type: str, trait: str, trust: int,
         flashback_strength: int) -> World:
    world = World()
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_gender,
        label=child_name,
        phrase=child_name,
        role="child",
        attrs={"display": child_name, "trait": trait, "trust": trust, "flashback_strength": flashback_strength},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        phrase="the parent",
        role="parent",
    ))
    world.add(Entity(id="room", type="room", label="room"))
    world.add(Entity(
        id="noise",
        type="noise",
        label=noise.label,
        phrase=noise.phrase,
        attrs={"risk": noise.risk},
        tags=set(noise.tags),
    ))
    world.add(Entity(
        id="comfort",
        type="comfort",
        label=comfort.label,
        phrase=comfort.phrase,
        attrs={"warmth": comfort.warmth},
        tags=set(comfort.tags),
        soft=True,
    ))
    world.add(Entity(id="lamp", type="lamp", label="night-light", glowing=True))

    world.facts.update(
        child=child,
        parent=parent,
        noise_cfg=noise,
        comfort_cfg=comfort,
        response_cfg=response,
    )

    introduce(world, child, parent, comfort)
    bedtime_detail(world, child)

    world.para()
    start_noise(world, noise)
    comfort_beat(world, child, comfort)

    world.para()
    flashback(world, child, parent, response)
    safest = predict_safest(world)
    world.facts["predicted_response"] = safest["response"]

    defied = would_defy(trait=trait, trust=trust, flashback_strength=flashback_strength, response_id=response.id)
    choose_response(world, child, parent, response, defied)

    world.para()
    settled = resolved_quickly(noise, response, defied)
    reveal(world, parent, noise, response, defied, settled)

    world.para()
    ending(world, child, parent, comfort, defied, settled)

    world.facts.update(
        child_name=child_name,
        defied=defied,
        settled=settled,
        trust=trust,
        flashback_strength=flashback_strength,
        outcome="settled" if settled else "spooked",
    )
    return world


@dataclass
class StoryParams:
    noise: str
    comfort: str
    response: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    trust: int
    flashback_strength: int
    seed: Optional[int] = None


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Nora", "Maya"]
BOY_NAMES = ["Ben", "Max", "Sam", "Leo", "Finn", "Noah", "Theo", "Eli"]
TRAITS = ["gentle", "curious", "bold", "careful"]

CURATED = [
    StoryParams(
        noise="shutter",
        comfort="bear",
        response="bell",
        child_name="Lily",
        child_gender="girl",
        parent="mother",
        trait="careful",
        trust=3,
        flashback_strength=4,
        seed=None,
    ),
    StoryParams(
        noise="kitten",
        comfort="blanket",
        response="call_parent",
        child_name="Ben",
        child_gender="boy",
        parent="father",
        trait="gentle",
        trust=2,
        flashback_strength=4,
        seed=None,
    ),
    StoryParams(
        noise="wagon",
        comfort="pillow",
        response="nightlight",
        child_name="Mia",
        child_gender="girl",
        parent="mother",
        trait="curious",
        trust=3,
        flashback_strength=2,
        seed=None,
    ),
    StoryParams(
        noise="branch",
        comfort="bear",
        response="hall_peek",
        child_name="Max",
        child_gender="boy",
        parent="father",
        trait="bold",
        trust=3,
        flashback_strength=1,
        seed=None,
    ),
]


KNOWLEDGE = {
    "night_sound": [
        (
            "Why do sounds seem bigger at night?",
            "At night the house is quieter, so small sounds stand out more. When you cannot see the cause right away, your imagination can make the sound feel bigger.",
        )
    ],
    "call_help": [
        (
            "What should a child do if a night sound feels scary?",
            "Stay where it is safe and call for a grown-up. A calm grown-up can help find the cause without the child wandering alone in the dark.",
        )
    ],
    "bell": [
        (
            "Why might a bedside bell help at night?",
            "A bedside bell gives a child an easy way to call for help without leaving bed. That can make the dark feel less lonely and more manageable.",
        )
    ],
    "nightlight": [
        (
            "What does a night-light do?",
            "A night-light makes a soft glow that helps a room feel less dark. It can make ordinary shapes and corners easier to understand.",
        )
    ],
    "kitten": [
        (
            "Why might a kitten cry at night?",
            "A kitten might cry because it is alone, hungry, or looking for warmth. Its small mew can sound mysterious if you do not know what made it.",
        )
    ],
    "window": [
        (
            "Why can a window or shutter make tapping sounds?",
            "Wind can nudge a loose shutter or window part so it taps again and again. The sound is harmless, but it can surprise you in a quiet room.",
        )
    ],
    "tree": [
        (
            "Why does a tree branch scratch a roof or wall?",
            "When the wind moves a branch, it can brush against a roof or wall and make a scratching sound. The noise is just the branch moving back and forth.",
        )
    ],
    "toy": [
        (
            "How can a toy make a noise by itself?",
            "A toy can roll or tip if the floor is uneven or if someone bumped it earlier. Then it may knock softly against furniture and sound spooky in the dark.",
        )
    ],
    "comfort": [
        (
            "Why does hugging a soft toy or blanket help when you feel afraid?",
            "A familiar soft thing can make your body feel safer and steadier. That cozy feeling can help your breathing slow down while you wait for help.",
        )
    ],
}
KNOWLEDGE_ORDER = ["night_sound", "call_help", "bell", "nightlight", "kitten", "window", "tree", "toy", "comfort"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    noise = f["noise_cfg"]
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the word "defy" and a mysterious sound in the night.',
        f"Tell a gentle suspense story where a {child.type} named {f['child_name']} hears {noise.sound} at bedtime, remembers an earlier lesson in a flashback, and learns the safe way to handle fear.",
        f"Write a soft, suspenseful bedtime tale with a flashback, a night noise, and a calm ending that explains what really made the sound.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    noise = f["noise_cfg"]
    comfort = f["comfort_cfg"]
    response = f["response_cfg"]
    child_name = f["child_name"]
    pw = parent.label_word
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child_name}, a child getting ready for sleep, and {child.pronoun('possessive')} {pw}. The story follows what happens when a strange sound breaks the quiet bedtime room.",
        ),
        (
            "What made the story feel suspenseful?",
            f"The room was dark and quiet, and then {noise.sound} came from {noise.place}. Because {child_name} could not see the cause at first, the small sound felt much bigger and more mysterious.",
        ),
        (
            "What was the flashback about?",
            f"The flashback was about an earlier time when {pw} taught {child_name} what to do with scary night sounds. That memory mattered because it gave {child.pronoun('object')} a safer choice than chasing the mystery alone.",
        ),
    ]
    if f["defied"]:
        qa.append(
            (
                f"How did {child_name} defy the bedtime rule?",
                f"{child_name} briefly defied the rule by {response.qa_text}. The child was pulled by worry and curiosity, even after remembering the earlier bedtime lesson.",
            )
        )
    else:
        qa.append(
            (
                f"How did {child_name} handle the sound safely?",
                f"{child_name} stayed where it was safe and {response.qa_text}. That choice let a grown-up come to the mystery instead of sending the child out into the dark alone.",
            )
        )
    qa.append(
        (
            "What really made the noise?",
            f"It turned out to be {noise.cause_text}. The scary feeling changed once the hidden cause had a simple, ordinary explanation.",
        )
    )
    if f["settled"]:
        qa.append(
            (
                "How did the story end?",
                f"It ended peacefully, with {pw} tucking {child_name} back into bed. Once the sound was explained, the room felt ordinary again and sleep could come back.",
            )
        )
    else:
        qa.append(
            (
                "How did the story end?",
                f"It ended with a long cuddle and a calmer room, even though the night still felt a little prickly at first. {pw.capitalize()} stayed close until the fear softened enough for sleep.",
            )
        )
    qa.append(
        (
            f"Why did hugging the {comfort.label} help?",
            f"Hugging the {comfort.label} gave {child_name} a little warmth and steadiness while the child listened. It did not solve the mystery by itself, but it helped {child.pronoun('object')} wait for comfort and help.",
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["noise_cfg"].tags) | set(world.facts["comfort_cfg"].tags) | set(world.facts["response_cfg"].tags)
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
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_response(response_id: str) -> str:
    response = RESPONSES[response_id]
    better = ", ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(No story: '{response_id}' is known to the world but refused because it is not a sensible bedtime response "
        f"(sense={response.sense} < {SENSE_MIN}). Try one of: {better}.)"
    )


def explain_combo(noise_id: str, response_id: str) -> str:
    noise = NOISES[noise_id]
    response = RESPONSES[response_id]
    if response.sense < SENSE_MIN:
        return explain_response(response_id)
    if noise.risk >= 2 and response.id == "nightlight":
        return (
            f"(No story: for {noise.label}, turning on the night-light alone is too weak. "
            f"The child still needs a grown-up or a bedside help signal.)"
        )
    return "(No story: that combination is not reasonable in this world.)"


ASP_RULES = r"""
response_sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
too_weak(N, nightlight) :- noise(N), risk(N, R), R >= 2.
valid(N, R) :- noise(N), response(R), response_sensible(R), not too_weak(N, R).

urge(3) :- trait(bold).
urge(2) :- trait(curious).
urge(1) :- trait(gentle).
urge(1) :- trait(careful).

defied :- chosen_response(hall_peek).
defied :- chosen_response(nightlight), urge(U), trust(T), flashback(F), U + T > F + 3.
defied :- chosen_response(call_parent), 1 = 0.
defied :- chosen_response(bell), 1 = 0.

effective_power(P) :- chosen_response(R), calm_power(R, C), defied, P = C.
effective_power(P) :- chosen_response(R), calm_power(R, C), not defied, P = C + 1.

settled :- chosen_noise(N), effective_power(P), risk(N, R), P >= R + 1.
outcome(settled) :- settled.
outcome(spooked) :- not settled.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for noise_id, noise in NOISES.items():
        lines.append(asp.fact("noise", noise_id))
        lines.append(asp.fact("risk", noise_id, noise.risk))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("calm_power", response_id, response.calm_power))
    for trait in TRAITS:
        lines.append(asp.fact("trait_name", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_noise", params.noise),
            asp.fact("chosen_response", params.response),
            asp.fact("trait", params.trait),
            asp.fact("trust", params.trust),
            asp.fact("flashback", params.flashback_strength),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0

    c_set = set(asp_valid_combos())
    p_set = set(valid_combos())
    if c_set == p_set:
        print(f"OK: gate matches valid_combos() ({len(c_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if c_set - p_set:
            print("  only in clingo:", sorted(c_set - p_set))
        if p_set - c_set:
            print("  only in python:", sorted(p_set - c_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            args = build_parser().parse_args([])
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            cases.append(params)
        except StoryError:
            rc = 1
            print(f"Unexpected StoryError during verify sampling at seed {seed}.")
            break

    mismatch = 0
    for params in cases:
        py = predict_outcome(
            noise_id=params.noise,
            response_id=params.response,
            trait=params.trait,
            trust=params.trust,
            flashback_strength=params.flashback_strength,
        )
        asp_val = asp_outcome(params)
        if py != asp_val:
            mismatch += 1
    if mismatch == 0:
        print(f"OK: outcome model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatch}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story or "{" in sample.story or "}" in sample.story:
            raise StoryError("Generated story was empty or contained unresolved template braces.")
        print("OK: smoke-test generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Storyworld: bedtime suspense with a flashback and a small act of defiance."
    )
    ap.add_argument("--noise", choices=sorted(NOISES))
    ap.add_argument("--comfort", choices=sorted(COMFORTS))
    ap.add_argument("--response", choices=sorted(RESPONSES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--trust", type=int, choices=list(range(0, 5)))
    ap.add_argument("--flashback-strength", type=int, choices=list(range(1, 6)))
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list valid (noise, response) combos from clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the inline ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response is not None and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    if args.noise is not None and args.response is not None and not valid_combo(args.noise, args.response):
        raise StoryError(explain_combo(args.noise, args.response))

    combos = [
        combo for combo in valid_combos()
        if (args.noise is None or combo[0] == args.noise)
        and (args.response is None or combo[1] == args.response)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    noise_id, response_id = rng.choice(combos)
    comfort_id = args.comfort or rng.choice(sorted(COMFORTS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name_pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    child_name = args.name or rng.choice(name_pool)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    trust = args.trust if args.trust is not None else rng.randint(0, 4)
    flashback_strength = args.flashback_strength if args.flashback_strength is not None else rng.randint(1, 5)
    return StoryParams(
        noise=noise_id,
        comfort=comfort_id,
        response=response_id,
        child_name=child_name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        trust=trust,
        flashback_strength=flashback_strength,
        seed=None,
    )


def validate_params(params: StoryParams) -> None:
    if params.noise not in NOISES:
        raise StoryError(f"(Unknown noise: {params.noise})")
    if params.comfort not in COMFORTS:
        raise StoryError(f"(Unknown comfort item: {params.comfort})")
    if params.response not in RESPONSES:
        raise StoryError(f"(Unknown response: {params.response})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.parent not in {"mother", "father"}:
        raise StoryError(f"(Unknown parent type: {params.parent})")
    if params.trait not in TRAITS:
        raise StoryError(f"(Unknown trait: {params.trait})")
    if not valid_combo(params.noise, params.response):
        raise StoryError(explain_combo(params.noise, params.response))


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(
        noise=NOISES[params.noise],
        comfort=COMFORTS[params.comfort],
        response=RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
        trait=params.trait,
        trust=params.trust,
        flashback_strength=params.flashback_strength,
    )
    story_text = world.render().replace("child", params.child_name)
    story_text = story_text.replace("parent", world.facts["parent"].label_word)
    story_text = story_text.replace("the parent", world.facts["parent"].label_word)
    story_text = story_text.replace("Child", params.child_name)

    child_name = params.child_name
    story_text = story_text.replace("child", child_name)
    story_text = story_text.replace("  ", " ")

    story_text = story_text.replace("In a small quiet room, child", f"In a small quiet room, {child_name}")
    story_text = story_text.replace("Soon the same house", "Soon the same house")
    story_text = story_text.replace("child's", f"{child_name}'s")

    return StorySample(
        params=params,
        story=story_text,
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
        print(f"{len(combos)} compatible (noise, response) combos:\n")
        for noise_id, response_id in combos:
            print(f"  {noise_id:8} {response_id}")
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
            header = f"### {p.child_name}: {p.noise} with {p.response} ({predict_outcome(p.noise, p.response, p.trait, p.trust, p.flashback_strength)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
