#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/opposite_ire_jungle_foreshadowing_superhero_story.py
================================================================================

A standalone story world for a tiny superhero tale in a jungle city-park domain.

Premise
-------
A young superhero goes into the jungle paths of Green Lantern Park to return a
glowing seed to an old stone jaguar shrine. Early signs foreshadow that the
shrine's guardian is waking in a bad mood: warm wind, shaking leaves, bright
eyes in the stone. A proud sidekick wants to answer danger with more force, but
the world model knows some powers only make the guardian's ire grow.

This world prefers *fewer, stronger* stories:
- a real jungle setting
- explicit foreshadowing in the opening
- a superhero-style problem and fix
- a clear turn driven by state, not template swaps
- a closing image that proves what changed

Reasonableness rule
-------------------
Not every power is a believable solution. Some threats in this world can only be
solved by the *opposite* move:
- anger / ire is best met by calm
- vines are best handled by cutting or shielding, not by more yelling

The Python gate and the ASP twin both enforce which (threat, power, response)
combinations make sense, and what ending they produce.

Run it
------
    python storyworlds/worlds/gpt-5.4/opposite_ire_jungle_foreshadowing_superhero_story.py
    python storyworlds/worlds/gpt-5.4/opposite_ire_jungle_foreshadowing_superhero_story.py --all
    python storyworlds/worlds/gpt-5.4/opposite_ire_jungle_foreshadowing_superhero_story.py -n 5 --seed 7
    python storyworlds/worlds/gpt-5.4/opposite_ire_jungle_foreshadowing_superhero_story.py --qa
    python storyworlds/worlds/gpt-5.4/opposite_ire_jungle_foreshadowing_superhero_story.py --trace --seed 11
    python storyworlds/worlds/gpt-5.4/opposite_ire_jungle_foreshadowing_superhero_story.py --verify
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
SENSE_MIN = 2


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
    owner: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Threat:
    id: str
    label: str
    phrase: str
    foreshadow: str
    reveal: str
    risk: str
    dominant_meter: str
    weakness: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Power:
    id: str
    label: str
    phrase: str
    effect: str
    beats: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    label: str
    sense: int
    helps: set[str] = field(default_factory=set)
    harms: set[str] = field(default_factory=set)
    hero_text: str = ""
    success_text: str = ""
    fail_text: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Setting:
    id: str
    place: str
    skyline: str
    path: str
    shrine: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        clone = World(self.setting)
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


def _r_ire_overflow(world: World) -> list[str]:
    out: list[str] = []
    guardian = world.entities.get("guardian")
    if guardian is None:
        return out
    if guardian.memes["ire"] < 2:
        return out
    sig = ("ire_overflow",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    guardian.meters["roaring"] += 1
    if "jungle" in world.entities:
        world.get("jungle").meters["danger"] += 1
    for ent in list(world.entities.values()):
        if ent.role in {"hero", "sidekick"}:
            ent.memes["fear"] += 1
    out.append("__roar__")
    return out


def _r_vines_grab(world: World) -> list[str]:
    out: list[str] = []
    guardian = world.entities.get("guardian")
    if guardian is None:
        return out
    if guardian.meters["vines"] < THRESHOLD:
        return out
    sig = ("vines_grab",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    if "sidekick" in world.entities:
        world.get("sidekick").meters["stuck"] += 1
    if "jungle" in world.entities:
        world.get("jungle").meters["danger"] += 1
    out.append("__grab__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="ire_overflow", tag="emotional", apply=_r_ire_overflow),
    Rule(name="vines_grab", tag="physical", apply=_r_vines_grab),
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
        for sent in produced:
            world.say(sent)
    return produced


SETTINGS = {
    "emerald_park": Setting(
        id="emerald_park",
        place="Emerald Park",
        skyline="Beyond the trees, the city roofs shone like silver blocks.",
        path="a mossy path under giant leaves",
        shrine="an old jaguar shrine hidden in the deepest green",
        tags={"jungle"},
    ),
    "river_garden": Setting(
        id="river_garden",
        place="River Garden",
        skyline="Far away, bright windows blinked through the leaves.",
        path="a fern-lined trail beside a sleepy river",
        shrine="a vine-wrapped jaguar shrine near the water",
        tags={"jungle"},
    ),
}

THREATS = {
    "ire": Threat(
        id="ire",
        label="guardian's ire",
        phrase="the jaguar guardian's hot ire",
        foreshadow="a low growl rolled from the shrine stones, as if they were dreaming an angry dream",
        reveal="the stone jaguar's eyes flashed gold and its voice boomed through the jungle air",
        risk="If the guardian stayed angry, it would shake the path apart and scare everyone away.",
        dominant_meter="ire",
        weakness="calm",
        tags={"ire", "guardian", "anger"},
    ),
    "vines": Threat(
        id="vines",
        label="snapping jungle vines",
        phrase="a whip of snapping jungle vines",
        foreshadow="the hanging vines kept twitching before any wind touched them",
        reveal="the vines lashed down from the branches and knotted across the path",
        risk="If the vines kept whipping, they would trap anyone trying to reach the shrine.",
        dominant_meter="vines",
        weakness="clear",
        tags={"jungle", "vines"},
    ),
}

POWERS = {
    "calm_light": Power(
        id="calm_light",
        label="calm light",
        phrase="a soft blue calm light",
        effect="calm",
        beats={"ire"},
        tags={"calm", "light"},
    ),
    "vine_cutter": Power(
        id="vine_cutter",
        label="vine-cutter ring",
        phrase="a bright green vine-cutter ring",
        effect="clear",
        beats={"vines"},
        tags={"ring", "vines"},
    ),
    "thunder_fists": Power(
        id="thunder_fists",
        label="thunder fists",
        phrase="a pair of crackling thunder fists",
        effect="smash",
        beats=set(),
        tags={"thunder"},
    ),
}

RESPONSES = {
    "soothe": Response(
        id="soothe",
        label="soothe",
        sense=3,
        helps={"calm"},
        harms=set(),
        hero_text='raised one hand and let a cool blue shine spread in a slow circle',
        success_text='The blue light touched the guardian, and its hard stone face softened. The growling faded until the jungle could hear the river again.',
        fail_text='The blue light glimmered, but it could not untangle the wild vines whipping across the path.',
        qa_text="used calm light to cool the guardian's anger",
        tags={"calm", "opposite"},
    ),
    "slice": Response(
        id="slice",
        label="slice",
        sense=3,
        helps={"clear"},
        harms=set(),
        hero_text='spun the vine-cutter ring, and a neat green arc zipped through the air',
        success_text='The snarled vines split apart and dropped harmlessly to the ground. The path to the shrine opened like a door.',
        fail_text="The ring flashed, but cutting could not quiet the guardian's angry heart.",
        qa_text="used the vine-cutter ring to clear the path",
        tags={"ring", "jungle"},
    ),
    "shout_back": Response(
        id="shout_back",
        label="shout back",
        sense=1,
        helps=set(),
        harms={"ire"},
        hero_text='cupped both hands and shouted right back at the danger',
        success_text="For one tiny second the noise surprised the jungle.",
        fail_text='The answer only fed the trouble, and the guardian\'s ire swelled hotter than before.',
        qa_text="shouted back at the danger",
        tags={"anger"},
    ),
    "punch": Response(
        id="punch",
        label="punch",
        sense=2,
        helps={"clear"},
        harms={"ire"},
        hero_text='leapt forward with thunder fists blazing like two little storms',
        success_text='The hard punch knocked branches and vines away from the path.',
        fail_text='The thunder only made the guardian angrier, and golden cracks ran through the shrine stones.',
        qa_text="used thunder fists to smash the danger",
        tags={"thunder"},
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Ava", "Nora", "Zoe", "Ella", "Ruby", "Kira"]
BOY_NAMES = ["Kai", "Leo", "Max", "Noah", "Finn", "Eli", "Theo", "Sam"]
SIDEKICK_NAMES = ["Pip", "Dot", "Nova", "Jet", "Bee", "Milo"]
TRAITS = ["brave", "gentle", "quick", "steady", "thoughtful", "sparky"]


def hazard_at_risk(threat: Threat, power: Power) -> bool:
    return True if threat.id and power.id else False


def response_sensible(response: Response) -> bool:
    return response.sense >= SENSE_MIN


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id in SETTINGS:
        for threat_id, threat in THREATS.items():
            for power_id, power in POWERS.items():
                if not hazard_at_risk(threat, power):
                    continue
                if threat.weakness == power.effect:
                    combos.append((setting_id, threat_id, power_id))
    return combos


def predict_trouble(world: World, threat: Threat) -> dict:
    sim = world.copy()
    guardian = sim.get("guardian")
    if threat.id == "ire":
        guardian.memes["ire"] += 2
    elif threat.id == "vines":
        guardian.meters["vines"] += 1
    propagate(sim, narrate=False)
    sidekick = sim.get("sidekick")
    jungle = sim.get("jungle")
    return {
        "danger": jungle.meters["danger"],
        "fear": sidekick.memes["fear"],
        "stuck": sidekick.meters["stuck"],
    }


def introduce(world: World, hero: Entity, sidekick: Entity, setting: Setting, power: Power) -> None:
    hero.memes["hope"] += 1
    sidekick.memes["trust"] += 1
    world.say(
        f"In {setting.place}, where the paths felt like a real jungle even though the city stood nearby, "
        f"{hero.id} ran with {sidekick.id} under giant leaves."
    )
    world.say(setting.skyline)
    world.say(
        f"{hero.id} wore a cape with a leaf-green star, and {power.phrase} rested at {hero.pronoun('possessive')} wrist."
    )


def foreshadow(world: World, hero: Entity, sidekick: Entity, setting: Setting, threat: Threat) -> None:
    hero.memes["alert"] += 1
    world.say(
        f"They were carrying a glowing seed back to {setting.shrine} when {threat.foreshadow}."
    )
    world.say(
        f'{sidekick.id} slowed down. "That does not sound friendly," {sidekick.pronoun()} whispered.'
    )
    world.say(
        f"{hero.id} looked at the shaking leaves and listened carefully. {threat.risk}"
    )


def warn(world: World, hero: Entity, sidekick: Entity, threat: Threat, response: Response) -> None:
    pred = predict_trouble(world, threat)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_stuck"] = pred["stuck"]
    if threat.id == "ire":
        line = (
            f'"If anger wakes in there, shouting back will make it bigger," {hero.id} said. '
            f'"The opposite of ire is calm."'
        )
    else:
        line = (
            f'"Those vines are already reaching for the path," {hero.id} said. '
            f'"We need a clean, careful move, not a noisy one."'
        )
    world.say(line)
    if response.id in {"shout_back", "punch"}:
        world.say(
            f'{sidekick.id} frowned. "But {response.label.replace("_", " ")} is faster," {sidekick.pronoun()} said.'
        )


def reveal(world: World, threat: Threat) -> None:
    guardian = world.get("guardian")
    if threat.id == "ire":
        guardian.memes["ire"] += 2
    else:
        guardian.meters["vines"] += 1
    propagate(world, narrate=False)
    world.say(
        f"At the next bend, {threat.reveal}. The glowing seed flickered in {world.get('hero').id}'s hands."
    )


def sidekick_mistake(world: World, sidekick: Entity, response: Response, threat: Threat) -> None:
    sidekick.memes["defiance"] += 1
    world.say(
        f"Before {world.get('hero').id} could answer, {sidekick.id} jumped ahead and {response.hero_text}."
    )
    if threat.id in response.harms:
        if threat.id == "ire":
            world.get("guardian").memes["ire"] += 1
        if threat.id == "vines":
            world.get("guardian").meters["vines"] += 1
        propagate(world, narrate=False)
        world.say(response.fail_text)
    else:
        world.say(
            "It looked bold, but it was the wrong kind of help for what was waking in the jungle."
        )


def hero_acts(world: World, hero: Entity, power: Power, response: Response, threat: Threat, setting: Setting) -> bool:
    hero.memes["courage"] += 1
    hero.memes["care"] += 1
    world.say(
        f"{hero.id} planted {hero.pronoun('possessive')} boots on {setting.path} and {response.hero_text}."
    )
    success = power.effect in response.helps and threat.weakness in response.helps
    if success:
        guardian = world.get("guardian")
        if threat.id == "ire":
            guardian.memes["ire"] = 0.0
            guardian.meters["roaring"] = 0.0
        if threat.id == "vines":
            guardian.meters["vines"] = 0.0
            if "sidekick" in world.entities:
                world.get("sidekick").meters["stuck"] = 0.0
        if "jungle" in world.entities:
            world.get("jungle").meters["danger"] = 0.0
        hero.memes["joy"] += 1
        world.say(response.success_text)
        return True
    if threat.id == "ire":
        world.get("guardian").memes["ire"] += 1
    else:
        world.get("guardian").meters["vines"] += 1
    propagate(world, narrate=False)
    world.say(response.fail_text)
    return False


def resolution(world: World, hero: Entity, sidekick: Entity, threat: Threat, success: bool, setting: Setting) -> None:
    guardian = world.get("guardian")
    if success:
        sidekick.memes["relief"] += 1
        sidekick.memes["lesson"] += 1
        world.say(
            f'The guardian bowed its heavy stone head. "You heard the warning before the trouble," it rumbled.'
        )
        if threat.id == "ire":
            world.say(
                f"{hero.id} set the glowing seed before the shrine, and soft green light ran through the carved jaguar. "
                f"The whole jungle seemed to breathe out."
            )
        else:
            world.say(
                f"{hero.id} tucked the glowing seed safely into the shrine bowl, and the branches above stopped thrashing. "
                f"Sunbeams slipped down to the mossy ground."
            )
        world.say(
            f'{sidekick.id} came close and said, "I thought louder would be stronger. But the right power was better."'
        )
        if threat.id == "ire":
            world.say(
                f"{hero.id} smiled. Calm had been the opposite of ire, and that was what saved the day."
            )
        else:
            world.say(
                f"{hero.id} smiled. In a jungle full of wild motion, the careful move had saved the day."
            )
    else:
        guardian.meters["rampage"] += 1
        sidekick.memes["fear"] += 1
        world.say(
            f"The shrine stones shook so hard that pebbles danced across the path. {hero.id} grabbed {sidekick.id}'s hand and pulled {sidekick.pronoun('object')} back."
        )
        world.say(
            f"They still got away safely, but they could not leave the seed at {setting.shrine} that day."
        )
        if threat.id == "ire":
            world.say(
                "As they hurried out of the jungle shadows, both children knew that anger answered with more anger only grows."
            )
        else:
            world.say(
                "As they hurried out of the jungle shadows, both children knew that wild danger needs the right tool, not the loudest one."
            )


def tell(
    setting: Setting,
    threat: Threat,
    power: Power,
    response: Response,
    hero_name: str = "Maya",
    hero_gender: str = "girl",
    sidekick_name: str = "Pip",
    sidekick_gender: str = "boy",
    parent_type: str = "mother",
    trait: str = "brave",
) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_gender,
        label=hero_name,
        phrase=hero_name,
        role="hero",
        traits=[trait],
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="character",
        type=sidekick_gender,
        label=sidekick_name,
        phrase=sidekick_name,
        role="sidekick",
        traits=["eager"],
    ))
    guardian = world.add(Entity(
        id="guardian",
        kind="character",
        type="guardian",
        label="guardian",
        phrase="the stone jaguar guardian",
        role="guardian",
        tags=set(threat.tags),
    ))
    jungle = world.add(Entity(
        id="jungle",
        kind="thing",
        type="place",
        label="jungle",
        phrase=setting.place,
        role="place",
        tags={"jungle"},
    ))
    world.add(Entity(
        id="seed",
        kind="thing",
        type="seed",
        label="seed",
        phrase="the glowing seed",
        role="goal",
    ))
    world.add(Entity(
        id="parent",
        kind="character",
        type=parent_type,
        label="the parent",
        role="parent",
    ))

    world.facts.update(
        setting=setting,
        threat=threat,
        power=power,
        response=response,
        hero_name=hero_name,
        sidekick_name=sidekick_name,
        hero=hero,
        sidekick=sidekick,
        guardian=guardian,
    )

    introduce(world, hero, sidekick, setting, power)
    foreshadow(world, hero, sidekick, setting, threat)

    world.para()
    warn(world, hero, sidekick, threat, response)
    reveal(world, threat)

    trouble_started = False
    if response.id in {"shout_back", "punch"}:
        trouble_started = True
        sidekick_mistake(world, sidekick, response, threat)

    world.para()
    success = hero_acts(world, hero, power, response, threat, setting)
    resolution(world, hero, sidekick, threat, success, setting)

    outcome = "saved" if success else "retreat"
    world.facts.update(
        outcome=outcome,
        trouble_started=trouble_started,
        seed_returned=success,
        guardian_calm=guardian.memes["ire"] < THRESHOLD,
        path_clear=world.get("jungle").meters["danger"] < THRESHOLD,
    )
    return world


@dataclass
class StoryParams:
    setting: str
    threat: str
    power: str
    response: str
    hero_name: str
    hero_gender: str
    sidekick_name: str
    sidekick_gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        setting="emerald_park",
        threat="ire",
        power="calm_light",
        response="soothe",
        hero_name="Maya",
        hero_gender="girl",
        sidekick_name="Pip",
        sidekick_gender="boy",
        parent="mother",
        trait="steady",
    ),
    StoryParams(
        setting="river_garden",
        threat="vines",
        power="vine_cutter",
        response="slice",
        hero_name="Kai",
        hero_gender="boy",
        sidekick_name="Dot",
        sidekick_gender="girl",
        parent="father",
        trait="quick",
    ),
    StoryParams(
        setting="emerald_park",
        threat="ire",
        power="thunder_fists",
        response="punch",
        hero_name="Ruby",
        hero_gender="girl",
        sidekick_name="Jet",
        sidekick_gender="boy",
        parent="mother",
        trait="brave",
    ),
    StoryParams(
        setting="river_garden",
        threat="ire",
        power="calm_light",
        response="shout_back",
        hero_name="Leo",
        hero_gender="boy",
        sidekick_name="Nova",
        sidekick_gender="girl",
        parent="father",
        trait="thoughtful",
    ),
]


def explain_rejection(threat: Threat, power: Power, response: Optional[Response] = None) -> str:
    if threat.weakness != power.effect:
        return (
            f"(No story: {power.label} does not match this threat. "
            f"The danger is {threat.label}, and this world only accepts a hero power that can answer it in a believable way.)"
        )
    if response is not None and not response_sensible(response):
        return (
            f"(Refusing response '{response.id}': it scores too low on common sense "
            f"(sense={response.sense} < {SENSE_MIN}). Try a calmer or more fitting response.)"
        )
    return "(No valid combination matches the given options.)"


def outcome_of(params: StoryParams) -> str:
    power = POWERS[params.power]
    response = RESPONSES[params.response]
    threat = THREATS[params.threat]
    return "saved" if (power.effect in response.helps and threat.weakness in response.helps) else "retreat"


KNOWLEDGE = {
    "jungle": [(
        "What is a jungle?",
        "A jungle is a thick, warm place with many trees, vines, and plants growing close together."
    )],
    "ire": [(
        "What does ire mean?",
        "Ire is a strong angry feeling. It is a story word for anger that feels hot and hard to control."
    )],
    "opposite": [(
        "What does opposite mean?",
        "Opposite means as different as two things can be in that moment. In this story, calm is the opposite of ire."
    )],
    "foreshadow": [(
        "What is foreshadowing in a story?",
        "Foreshadowing is when a story shows a small clue early on that hints at trouble or change later."
    )],
    "calm": [(
        "Why can calm help when someone is angry?",
        "Calm can help because it does not add more heat to the problem. A soft voice and a steady action can stop anger from growing."
    )],
    "vines": [(
        "What are vines?",
        "Vines are long plant stems that climb and twist around trees or other things."
    )],
    "superhero": [(
        "What makes someone a superhero?",
        "A superhero uses special gifts bravely to help others. The best superheroes also make wise choices, not just flashy ones."
    )],
}
KNOWLEDGE_ORDER = ["superhero", "jungle", "ire", "opposite", "foreshadow", "calm", "vines"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    threat = f["threat"]
    setting = f["setting"]
    power = f["power"]
    outcome = f["outcome"]
    base = (
        f'Write a short superhero story for a 3-to-5-year-old set in a jungle path at {setting.place}. '
        f'Include the words "opposite", "ire", and "jungle", and use foreshadowing.'
    )
    if outcome == "saved":
        return [
            base,
            f"Tell a gentle superhero story where {hero.label} notices a clue early, understands the danger, and uses {power.label} to stop {threat.label}.",
            f"Write a superhero tale where {sidekick.label} first thinks a louder move will work, but the hero proves that the right answer is the opposite of anger.",
        ]
    return [
        base,
        f"Tell a cautionary superhero story where {hero.label} and {sidekick.label} meet {threat.label}, but the wrong move makes the trouble worse and they must retreat safely.",
        f"Write a story with foreshadowing where jungle clues matter because using the wrong power teaches the heroes an important lesson.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    threat = f["threat"]
    power = f["power"]
    response = f["response"]
    setting = f["setting"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about the young superhero {hero.label} and {sidekick.label} in the jungle paths of {setting.place}. They were trying to return a glowing seed to the jaguar shrine."
        ),
        (
            "What early clue warned that trouble was coming?",
            f"The story gave a clue before the big problem: {threat.foreshadow}. That foreshadowing warned the children that the shrine was not quiet after all."
        ),
        (
            "Why did the danger matter?",
            f"{threat.risk} The clue mattered because the hero used it to understand what kind of help the jungle needed."
        ),
    ]
    if outcome == "saved":
        qa.append((
            f"How did {hero.label} stop the trouble?",
            f"{hero.label} {response.qa_text}. That worked because {power.label} matched the real weakness of the danger instead of only looking strong."
        ))
        if threat.id == "ire":
            qa.append((
                "Why does the story use the word opposite?",
                "The story says calm was the opposite of ire. That matters because the hero solved anger by cooling it instead of adding more anger."
            ))
        else:
            qa.append((
                f"What changed at the end of the story?",
                f"At the end, the path was safe again and the glowing seed was placed in the shrine. The final picture shows the jungle growing quiet because the right move changed the whole scene."
            ))
    else:
        qa.append((
            "What went wrong?",
            f"The heroes used a response that did not truly fit the danger. Because of that, the trouble grew instead of shrinking, and they had to leave the shrine without finishing the mission."
        ))
        qa.append((
            "What did the children learn?",
            "They learned that loud power is not always wise power. The foreshadowing clues were trying to teach them what kind of help the danger really needed."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"superhero", "jungle", "foreshadow", "opposite"}
    tags |= set(f["threat"].tags)
    tags |= set(f["power"].tags)
    tags |= set(f["response"].tags)
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
        bits: list[str] = []
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
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
        lines.append(f"  {ent.id:9} ({ent.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
% --- reasonableness gate ---------------------------------------------------
valid(S, T, P) :- setting(S), threat(T), power(P), weakness(T, E), effect(P, E).

sensible(R) :- response(R), sense(R, V), sense_min(M), V >= M.

% --- outcome model ---------------------------------------------------------
success(T, P, R) :- weakness(T, E), effect(P, E), helps(R, E).
outcome(T, P, R, saved)   :- success(T, P, R).
outcome(T, P, R, retreat) :- not success(T, P, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id in SETTINGS:
        lines.append(asp.fact("setting", setting_id))
    for threat_id, threat in THREATS.items():
        lines.append(asp.fact("threat", threat_id))
        lines.append(asp.fact("weakness", threat_id, threat.weakness))
    for power_id, power in POWERS.items():
        lines.append(asp.fact("power", power_id))
        lines.append(asp.fact("effect", power_id, power.effect))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        for tag in sorted(response.helps):
            lines.append(asp.fact("helps", response_id, tag))
    lines.append(asp.fact("sense_min", SENSE_MIN))
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
    extra = "\n".join([
        asp.fact("chosen_threat", params.threat),
        asp.fact("chosen_power", params.power),
        asp.fact("chosen_response", params.response),
        "want_outcome(O) :- chosen_threat(T), chosen_power(P), chosen_response(R), outcome(T, P, R, O).",
    ])
    model = asp.one_model(asp_program(extra, "#show want_outcome/1."))
    atoms = asp.atoms(model, "want_outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))

    c_sens = set(asp_sensible())
    p_sens = {rid for rid, resp in RESPONSES.items() if response_sensible(resp)}
    if c_sens == p_sens:
        print(f"OK: sensible responses match ({sorted(c_sens)}).")
    else:
        rc = 1
        print(f"MISMATCH in sensible responses: clingo={sorted(c_sens)} python={sorted(p_sens)}")

    cases = list(CURATED)
    for seed in range(50):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
            cases.append(params)
        except StoryError:
            continue
    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        smoke = generate(CURATED[0])
        if not smoke.story.strip():
            raise StoryError("Generated empty story during smoke test.")
        print("OK: smoke generation succeeded.")
    except Exception as err:  # pragma: no cover - verify path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(conflict_handler="resolve",
        description="Story world sketch: a superhero in a jungle notices foreshadowed danger and solves it with the right kind of power."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick-gender", choices=["girl", "boy"])
    ap.add_argument("--hero-name")
    ap.add_argument("--sidekick-name")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible (setting, threat, power) combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner against the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    options = [name for name in pool if name != avoid]
    return rng.choice(options)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.threat and args.power:
        threat = THREATS[args.threat]
        power = POWERS[args.power]
        if threat.weakness != power.effect:
            raise StoryError(explain_rejection(threat, power))
    if args.response and not response_sensible(RESPONSES[args.response]):
        threat = THREATS[args.threat] if args.threat else next(iter(THREATS.values()))
        power = POWERS[args.power] if args.power else next(iter(POWERS.values()))
        raise StoryError(explain_rejection(threat, power, RESPONSES[args.response]))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.threat is None or combo[1] == args.threat)
        and (args.power is None or combo[2] == args.power)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, threat_id, power_id = rng.choice(sorted(combos))
    response_id = args.response
    if response_id is None:
        candidates = [rid for rid, resp in RESPONSES.items() if response_sensible(resp)]
        themed = [rid for rid in candidates if THREATS[threat_id].weakness in RESPONSES[rid].helps]
        response_id = rng.choice(sorted(themed or candidates))

    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    sidekick_gender = args.sidekick_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or pick_name(rng, hero_gender)
    if args.sidekick_name:
        sidekick_name = args.sidekick_name
    else:
        sidekick_name = rng.choice([name for name in SIDEKICK_NAMES if name != hero_name])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(
        setting=setting_id,
        threat=threat_id,
        power=power_id,
        response=response_id,
        hero_name=hero_name,
        hero_gender=hero_gender,
        sidekick_name=sidekick_name,
        sidekick_gender=sidekick_gender,
        parent=parent,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        threat = THREATS[params.threat]
        power = POWERS[params.power]
        response = RESPONSES[params.response]
    except KeyError as err:
        raise StoryError(f"(Unknown parameter value: {err})") from err

    if threat.weakness != power.effect:
        raise StoryError(explain_rejection(threat, power))
    if not response_sensible(response):
        raise StoryError(explain_rejection(threat, power, response))

    world = tell(
        setting=setting,
        threat=threat,
        power=power,
        response=response,
        hero_name=params.hero_name,
        hero_gender=params.hero_gender,
        sidekick_name=params.sidekick_name,
        sidekick_gender=params.sidekick_gender,
        parent_type=params.parent,
        trait=params.trait,
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
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (setting, threat, power) combos:\n")
        for setting_id, threat_id, power_id in combos:
            print(f"  {setting_id:13} {threat_id:7} {power_id}")
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
            header = f"### {p.hero_name} in {p.setting}: {p.threat} with {p.power} ({outcome_of(p)})"
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
