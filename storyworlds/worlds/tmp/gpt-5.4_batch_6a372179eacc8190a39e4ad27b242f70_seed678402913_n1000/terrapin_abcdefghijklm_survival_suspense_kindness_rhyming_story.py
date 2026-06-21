#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/terrapin_abcdefghijklm_survival_suspense_kindness_rhyming_story.py
================================================================================================

A standalone story world about a child who finds a terrapin in danger and,
through calm kindness, helps it reach safety. The prose aims for a gentle,
rhyming TinyStories feel while still being driven by a small simulated world.

Seed requirements woven into the domain:
- required words: "terrapin", "abcdefghijklm", "survival"
- features: suspense, kindness
- style: rhyming story

Run it
------
    python storyworlds/worlds/gpt-5.4/terrapin_abcdefghijklm_survival_suspense_kindness_rhyming_story.py
    python storyworlds/worlds/gpt-5.4/terrapin_abcdefghijklm_survival_suspense_kindness_rhyming_story.py --setting garden --threat loose_dog
    python storyworlds/worlds/gpt-5.4/terrapin_abcdefghijklm_survival_suspense_kindness_rhyming_story.py --all
    python storyworlds/worlds/gpt-5.4/terrapin_abcdefghijklm_survival_suspense_kindness_rhyming_story.py --qa --json
    python storyworlds/worlds/gpt-5.4/terrapin_abcdefghijklm_survival_suspense_kindness_rhyming_story.py --verify
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

# Make storyworlds/results.py importable when run directly from this nested path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"           # "character" | "animal" | "thing"
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
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    path: str
    haven: str
    haven_phrase: str
    afford_threats: set[str] = field(default_factory=set)
    line: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    label: str
    hint: str
    beat: str
    danger_line: str
    severity: int
    tags: set[str] = field(default_factory=set)


@dataclass
class Aid:
    id: str
    label: str
    phrase: str
    prep: str
    use_line: str
    ranger_line: str
    sense: int
    power: int
    hold: int
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    threat: str
    aid: str
    child_name: str
    child_gender: str
    parent: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.active_threat: str = ""

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.active_threat = self.active_threat
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_hot_sun(world: World) -> list[str]:
    if world.active_threat != "hot_sun":
        return []
    terrapin = world.get("terrapin")
    sig = ("threat", "hot_sun")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    terrapin.meters["danger"] += 1
    terrapin.meters["thirst"] += 1
    terrapin.memes["strain"] += 1
    return ["__heat__"]


def _r_loose_dog(world: World) -> list[str]:
    if world.active_threat != "loose_dog":
        return []
    terrapin = world.get("terrapin")
    child = world.get("child")
    sig = ("threat", "loose_dog")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    terrapin.meters["danger"] += 1
    terrapin.meters["fear"] += 1
    child.memes["fear"] += 1
    return ["__dog__"]


def _r_storm_drain(world: World) -> list[str]:
    if world.active_threat != "storm_drain":
        return []
    terrapin = world.get("terrapin")
    sig = ("threat", "storm_drain")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    terrapin.meters["danger"] += 1
    terrapin.meters["slip"] += 1
    terrapin.memes["strain"] += 1
    return ["__drain__"]


CAUSAL_RULES: list[Rule] = [
    Rule(name="hot_sun", tag="physical", apply=_r_hot_sun),
    Rule(name="loose_dog", tag="social", apply=_r_loose_dog),
    Rule(name="storm_drain", tag="physical", apply=_r_storm_drain),
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
                produced.extend(sents)
    if narrate:
        for sent in produced:
            if sent.startswith("__"):
                continue
            world.say(sent)
    return produced


SETTINGS = {
    "garden": Setting(
        id="garden",
        place="the garden path",
        path="between bean poles and mint",
        haven="lily pond",
        haven_phrase="the cool lily pond under the leaves",
        afford_threats={"hot_sun", "loose_dog"},
        line="Mint smelled sweet, and bees made a tiny tuning din.",
        tags={"garden", "pond"},
    ),
    "park": Setting(
        id="park",
        place="the park path",
        path="beside tall reeds and a wooden rail",
        haven="duck pond",
        haven_phrase="the shady duck pond by the reeds",
        afford_threats={"hot_sun", "loose_dog"},
        line="A breeze bent the grass, then stopped as still as a pin.",
        tags={"park", "pond"},
    ),
    "sidewalk": Setting(
        id="sidewalk",
        place="the wet sidewalk",
        path="beside a curb and a storm grate",
        haven="marsh ditch",
        haven_phrase="the soft marsh ditch with long green grass",
        afford_threats={"storm_drain", "hot_sun"},
        line="Rain had passed, yet silver drops still clung in a row.",
        tags={"street", "marsh"},
    ),
}

THREATS = {
    "hot_sun": Threat(
        id="hot_sun",
        label="hot sun",
        hint="the stones felt warm enough to toast a crumb",
        beat="The terrapin blinked on the dry path while the noon light pressed down.",
        danger_line="For terrapin survival, shade and water mattered more than speed.",
        severity=2,
        tags={"sun", "survival"},
    ),
    "loose_dog": Threat(
        id="loose_dog",
        label="loose dog",
        hint="a collar jingled somewhere close, then closer still",
        beat="A loose dog snuffled nearby, and every little jingle made the air feel thin.",
        danger_line="One rough pounce could crack the quiet and flip the little shell.",
        severity=3,
        tags={"dog", "animal_safety"},
    ),
    "storm_drain": Threat(
        id="storm_drain",
        label="storm drain",
        hint="rainwater whispered toward the grate with a hungry, sucking sound",
        beat="The terrapin tottered near a storm drain where the street made a dark mouth.",
        danger_line="A slip into the grate would turn a short walk into a hard, hidden route.",
        severity=3,
        tags={"drain", "street_safety"},
    ),
}

AIDS = {
    "wash_tub": Aid(
        id="wash_tub",
        label="wash tub",
        phrase="a shallow wash tub",
        prep="brought a shallow wash tub and kept it low to the ground",
        use_line="Together they slid the terrapin into the tub and carried it in slow, careful rhyme-time.",
        ranger_line="They used the tub as a calm waiting nest until a ranger came to help.",
        sense=3,
        power=4,
        hold=4,
        helps={"hot_sun", "loose_dog", "storm_drain"},
        tags={"tub", "gentle_help"},
    ),
    "laundry_basket": Aid(
        id="laundry_basket",
        label="laundry basket",
        phrase="a holey laundry basket",
        prep="turned a holey laundry basket into a little wall of space",
        use_line="The basket blocked the barking bustle while they guided the terrapin toward the pond.",
        ranger_line="The basket made a safe little shelter while they waited for the ranger van.",
        sense=3,
        power=3,
        hold=4,
        helps={"loose_dog", "hot_sun"},
        tags={"basket", "gentle_help"},
    ),
    "cardboard_box": Aid(
        id="cardboard_box",
        label="cardboard box",
        phrase="a cardboard box with air holes",
        prep="found a cardboard box with air holes and lined it with a damp towel",
        use_line="The dark, cool box soothed the terrapin while they moved it away from danger.",
        ranger_line="The box kept the terrapin shaded while they called the ranger station.",
        sense=2,
        power=2,
        hold=3,
        helps={"hot_sun", "storm_drain"},
        tags={"box", "shade"},
    ),
    "soft_broom": Aid(
        id="soft_broom",
        label="soft broom",
        phrase="a soft broom",
        prep="used a soft broom like a quiet fence, never poking, only steering",
        use_line="The broom made a gentle lane, and the terrapin plodded away from the grate toward the grass.",
        ranger_line="The broom kept the terrapin from the grate until help could arrive.",
        sense=2,
        power=2,
        hold=4,
        helps={"storm_drain"},
        tags={"broom", "street_safety"},
    ),
}

GIRL_NAMES = ["Lila", "Mina", "Nora", "Eva", "Ivy", "Cora", "June", "Ava"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Eli", "Noah", "Finn", "Jude", "Ben"]
TRAITS = ["gentle", "careful", "curious", "steady", "kind", "thoughtful"]


def aid_works(aid: Aid, threat: Threat) -> bool:
    return threat.id in aid.helps


def threat_fits(setting: Setting, threat: Threat) -> bool:
    return threat.id in setting.afford_threats


def sensible_aids() -> list[Aid]:
    return [aid for aid in AIDS.values() if aid.sense >= SENSE_MIN]


def severity_of(threat: Threat, delay: int) -> int:
    return threat.severity + delay


def outcome_of_params(params: StoryParams) -> str:
    threat = THREATS[params.threat]
    aid = AIDS[params.aid]
    sev = severity_of(threat, params.delay)
    if aid.power >= sev:
        return "guided_home"
    if aid.hold >= sev:
        return "waited_for_ranger"
    return "hopeless"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, setting in SETTINGS.items():
        for tid, threat in THREATS.items():
            if not threat_fits(setting, threat):
                continue
            for aid_id, aid in AIDS.items():
                if aid.sense >= SENSE_MIN and aid_works(aid, threat):
                    combos.append((sid, tid, aid_id))
    return combos


def explain_rejection(setting: Setting, threat: Threat, aid: Aid) -> str:
    if not threat_fits(setting, threat):
        return (
            f"(No story: {threat.label} does not fit {setting.place}. "
            f"Pick a setting that can honestly contain that danger.)"
        )
    if not aid_works(aid, threat):
        return (
            f"(No story: {aid.label} is not a believable way to handle {threat.label}. "
            f"Choose help that matches the danger.)"
        )
    if aid.sense < SENSE_MIN:
        return (
            f"(No story: {aid.label} scores too low on common sense here. "
            f"The world prefers calmer, kinder help.)"
        )
    return "(No story: this combination is not reasonable.)"


def explain_delay(params: StoryParams) -> str:
    threat = THREATS[params.threat]
    aid = AIDS[params.aid]
    sev = severity_of(threat, params.delay)
    return (
        f"(No story: with delay={params.delay}, {threat.label} reaches severity {sev}, "
        f"and {aid.label} is too weak even to hold the terrapin safely while help comes.)"
    )


def predict_danger(world: World, threat: Threat) -> dict:
    sim = world.copy()
    sim.active_threat = threat.id
    propagate(sim, narrate=False)
    terrapin = sim.get("terrapin")
    return {
        "danger": terrapin.meters["danger"],
        "thirst": terrapin.meters["thirst"],
        "fear": terrapin.meters["fear"],
        "slip": terrapin.meters["slip"],
    }


def opening(world: World, child: Entity, parent: Entity, terrapin: Entity, trait: str) -> None:
    world.say(
        f"{child.id} was a {trait} little {child.type} who noticed small things in big places, "
        f"and {child.pronoun('possessive')} {parent.label_word} liked that bright-eyed grace."
    )
    world.say(
        f"They walked along {world.setting.place}, {world.setting.path}. "
        f"{world.setting.line}"
    )
    world.say(
        f"Then {child.id} saw a terrapin no bigger than a lunch-box lid, "
        f"with a shell that shone like polished rain where tiny brown lines slid."
    )
    child.memes["wonder"] += 1
    terrapin.memes["calm"] += 1


def notice_threat(world: World, child: Entity, terrapin: Entity, threat: Threat) -> None:
    world.active_threat = threat.id
    propagate(world, narrate=False)
    world.say(threat.beat)
    world.say(
        f"{threat.hint}, and {child.id}'s heart gave one quick leap within."
    )
    child.memes["fear"] += 1
    terrapin.meters["exposed"] += 1


def alphabet_calm(world: World, child: Entity) -> None:
    child.memes["care"] += 1
    world.say(
        f'So {child.id} whispered, "abcdefghijklm," soft and slow, '
        f"one quiet letter at a time, to help {child.pronoun('object')} move low and go slow."
    )


def parent_warning(world: World, child: Entity, parent: Entity, threat: Threat) -> None:
    pred = predict_danger(world, threat)
    world.facts["predicted_danger"] = pred["danger"]
    world.facts["predicted_thirst"] = pred["thirst"]
    world.facts["predicted_fear"] = pred["fear"]
    world.facts["predicted_slip"] = pred["slip"]
    extra = ""
    if pred["thirst"] >= THRESHOLD:
        extra = " It needed cool shade and water soon."
    elif pred["slip"] >= THRESHOLD:
        extra = " One wrong step could send it where small feet could not follow."
    elif pred["fear"] >= THRESHOLD:
        extra = " Loud rushing would only make the danger feel bigger."
    world.say(
        f'"Stay gentle," {parent.label_word} said. "{threat.danger_line}{extra}"'
    )


def fetch_aid(world: World, child: Entity, parent: Entity, aid: Aid) -> None:
    child.memes["hope"] += 1
    world.say(
        f"So {child.id}'s {parent.label_word} {aid.prep}, "
        f"and {child.id} kept watch with kind, still eyes."
    )


def resolve_guided_home(
    world: World,
    child: Entity,
    parent: Entity,
    terrapin: Entity,
    aid: Aid,
) -> None:
    terrapin.meters["danger"] = 0.0
    terrapin.meters["safe"] += 1
    child.memes["relief"] += 1
    child.memes["care"] += 1
    terrapin.memes["calm"] += 1
    world.say(aid.use_line)
    world.say(
        f"Soon the terrapin reached {world.setting.haven_phrase}, "
        f"where water winked and reeds bent low."
    )
    world.say(
        f"{child.id} smiled to see its little legs go plod-plod-plod, then slip from sight below."
    )
    world.say(
        f'"That was kindness," {parent.label_word} said. "For survival, wild things need the right home, '
        f'and gentle hands help them get there without making fear their own."'
    )


def resolve_waited(
    world: World,
    child: Entity,
    parent: Entity,
    terrapin: Entity,
    aid: Aid,
) -> None:
    terrapin.meters["danger"] = 0.0
    terrapin.meters["safe"] += 1
    terrapin.meters["waited"] += 1
    child.memes["relief"] += 1
    child.memes["patience"] += 1
    terrapin.memes["calm"] += 1
    world.say(
        f"The danger was too close for a quick trip, so nobody hurried and nobody shoved."
    )
    world.say(aid.ranger_line)
    world.say(
        f"A ranger came at dusk, checked the terrapin, and carried it to {world.setting.haven_phrase}."
    )
    world.say(
        f"{child.id} watched the little shell bob away and learned that sometimes the kindest help is to wait."
    )
    world.say(
        f"The night grew calm, the reeds grew dim, and the worried drum in {child.pronoun('possessive')} chest grew late and faint."
    )


def tell(
    setting: Setting,
    threat: Threat,
    aid: Aid,
    child_name: str,
    child_gender: str,
    parent_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World(setting)
    child = world.add(
        Entity(
            id=child_name,
            kind="character",
            type=child_gender,
            label=child_name,
            role="child",
            traits=[trait],
        )
    )
    parent = world.add(
        Entity(
            id="Parent",
            kind="character",
            type=parent_type,
            label="the parent",
            role="parent",
        )
    )
    terrapin = world.add(
        Entity(
            id="terrapin",
            kind="animal",
            type="terrapin",
            label="terrapin",
            phrase="a little terrapin",
            role="animal",
            tags={"terrapin", "wildlife"},
        )
    )
    helper = world.add(
        Entity(
            id="aid",
            kind="thing",
            type="aid",
            label=aid.label,
            phrase=aid.phrase,
            role="aid",
            tags=set(aid.tags),
        )
    )
    world.facts["delay"] = delay

    opening(world, child, parent, terrapin, trait)

    world.para()
    notice_threat(world, child, terrapin, threat)
    for _ in range(delay):
        terrapin.meters["danger"] += 1
        if threat.id == "hot_sun":
            terrapin.meters["thirst"] += 1
        elif threat.id == "loose_dog":
            terrapin.meters["fear"] += 1
        elif threat.id == "storm_drain":
            terrapin.meters["slip"] += 1
    alphabet_calm(world, child)
    parent_warning(world, child, parent, threat)

    world.para()
    fetch_aid(world, child, parent, aid)
    outcome = outcome_of_params(
        StoryParams(
            setting=setting.id,
            threat=threat.id,
            aid=aid.id,
            child_name=child_name,
            child_gender=child_gender,
            parent=parent_type,
            trait=trait,
            delay=delay,
        )
    )
    if outcome == "guided_home":
        resolve_guided_home(world, child, parent, terrapin, aid)
    elif outcome == "waited_for_ranger":
        resolve_waited(world, child, parent, terrapin, aid)
    else:
        raise StoryError(explain_delay(
            StoryParams(
                setting=setting.id,
                threat=threat.id,
                aid=aid.id,
                child_name=child_name,
                child_gender=child_gender,
                parent=parent_type,
                trait=trait,
                delay=delay,
            )
        ))

    world.facts.update(
        child=child,
        parent=parent,
        terrapin=terrapin,
        helper=helper,
        setting_cfg=setting,
        threat_cfg=threat,
        aid_cfg=aid,
        outcome=outcome,
        survival_line=threat.danger_line,
    )
    return world


KNOWLEDGE = {
    "terrapin": [
        (
            "What is a terrapin?",
            "A terrapin is a small turtle that lives in or near water. It needs a safe place to rest, hide, and stay cool."
        )
    ],
    "survival": [
        (
            "What does survival mean?",
            "Survival means staying alive and safe. Animals survive when they have the right home, water, food, and protection from danger."
        )
    ],
    "sun": [
        (
            "Why can a hot path be dangerous for a terrapin?",
            "A hot path can dry a terrapin out and make it too warm. A terrapin needs shade and water so its body does not get stressed."
        )
    ],
    "dog": [
        (
            "Why should a dog stay away from a wild terrapin?",
            "A dog might paw, bark at, or bite the terrapin by mistake. Wild animals feel safer when people and pets give them space."
        )
    ],
    "drain": [
        (
            "Why is a storm drain dangerous for a small animal?",
            "A storm drain is dark, steep, and hard to climb out of. A little animal can slip in and get trapped far from home."
        )
    ],
    "gentle_help": [
        (
            "Why should you move slowly around a wild animal?",
            "Slow, quiet movement keeps the animal from getting more scared. Calm help is often the kindest help."
        )
    ],
    "street_safety": [
        (
            "Who should help with a wild animal near a street or drain?",
            "A grown-up should help right away, and sometimes a ranger or animal helper should be called. Streets and drains can be too risky for children alone."
        )
    ],
    "shade": [
        (
            "Why do air holes and shade matter in a rescue box?",
            "Air holes let the animal breathe, and shade keeps it cooler. A dark, cool box can help an animal stay calmer for a short time."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "terrapin",
    "survival",
    "sun",
    "dog",
    "drain",
    "gentle_help",
    "street_safety",
    "shade",
]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    threat = f["threat_cfg"]
    setting = f["setting_cfg"]
    outcome = f["outcome"]
    if outcome == "guided_home":
        ending = f"ends with the terrapin reaching {setting.haven_phrase}"
    else:
        ending = "ends with a ranger helping after a calm wait"
    return [
        (
            'Write a short rhyming story for a 3-to-5-year-old that includes the words '
            '"terrapin", "abcdefghijklm", and "survival". Make it suspenseful but kind.'
        ),
        (
            f"Tell a gentle suspense story where a child named {child.id} finds a terrapin in danger from {threat.label} "
            f"and stays calm enough to help. The story should feel musical and end kindly."
        ),
        (
            f"Write a rhyming rescue story set on {setting.place} where a child whispers abcdefghijklm to stay steady, "
            f"and the tale {ending}."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    terrapin = f["terrapin"]
    threat = f["threat_cfg"]
    aid = f["aid_cfg"]
    setting = f["setting_cfg"]
    outcome = f["outcome"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {child.id}, {child.pronoun('possessive')} {parent.label_word}, and a little terrapin on {setting.place}. "
            f"The story follows how they noticed the animal and chose a gentle way to help."
        ),
        (
            "Why did the story feel suspenseful?",
            f"It felt suspenseful because the terrapin was close to {threat.label}, so something bad might happen if nobody acted. "
            f"Each small sound and careful step mattered while {child.id} tried to help."
        ),
        (
            f"Why did {child.id} whisper abcdefghijklm?",
            f"{child.id} whispered abcdefghijklm to stay calm and move slowly. "
            f"That helped {child.pronoun('object')} choose kindness instead of rushing and scaring the terrapin."
        ),
        (
            "What did the grown-up explain about survival?",
            f"{f['survival_line']} "
            f"The warning came from the danger in front of them, not from guessing."
        ),
    ]
    if outcome == "guided_home":
        qa.append(
            (
                "How did they help the terrapin?",
                f"They used {aid.phrase} and moved with great care until the terrapin reached {setting.haven_phrase}. "
                f"The method worked because it matched the danger and gave the animal a calm path to safety."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the terrapin safe in the right watery place, and {child.id} feeling relieved and proud. "
                f"The ending image of the little shell slipping into shade shows that the danger had truly changed."
            )
        )
    else:
        qa.append(
            (
                "Why did they wait for a ranger?",
                f"They could protect the terrapin with {aid.phrase}, but the danger was still too close for a quick trip home. "
                f"Waiting was kinder because it kept the terrapin safe until stronger help arrived."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended quietly, with a ranger taking the terrapin to {setting.haven_phrase} while {child.id} watched. "
                f"The calm ending proves the danger had passed, even though the child did not do every part alone."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags: set[str] = {"terrapin", "survival", "gentle_help"}
    tags |= set(world.facts["threat_cfg"].tags)
    tags |= set(world.facts["aid_cfg"].tags)
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
    for ent in world.entities.values():
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
        if ent.attrs:
            bits.append(f"attrs={ent.attrs}")
        lines.append(f"  {ent.id:10} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        setting="garden",
        threat="hot_sun",
        aid="wash_tub",
        child_name="Lila",
        child_gender="girl",
        parent="mother",
        trait="gentle",
        delay=0,
    ),
    StoryParams(
        setting="park",
        threat="loose_dog",
        aid="laundry_basket",
        child_name="Milo",
        child_gender="boy",
        parent="father",
        trait="steady",
        delay=0,
    ),
    StoryParams(
        setting="sidewalk",
        threat="storm_drain",
        aid="soft_broom",
        child_name="Nora",
        child_gender="girl",
        parent="mother",
        trait="careful",
        delay=1,
    ),
    StoryParams(
        setting="sidewalk",
        threat="hot_sun",
        aid="cardboard_box",
        child_name="Theo",
        child_gender="boy",
        parent="father",
        trait="thoughtful",
        delay=1,
    ),
    StoryParams(
        setting="park",
        threat="hot_sun",
        aid="cardboard_box",
        child_name="Eva",
        child_gender="girl",
        parent="mother",
        trait="kind",
        delay=0,
    ),
]


ASP_RULES = r"""
% reasonable triples
valid(S, T, A) :- setting(S), threat(T), aid(A), affords(S, T), helps(A, T), sense(A, N), sense_min(M), N >= M.

% outcome for one chosen scenario
severity(V) :- chosen_threat(T), base_severity(T, B), delay(D), V = B + D.
guided_home :- chosen_aid(A), severity(V), power(A, P), P >= V.
waited_for_ranger :- chosen_aid(A), severity(V), hold(A, H), H >= V, not guided_home.
hopeless :- chosen_aid(A), severity(V), hold(A, H), H < V.

outcome(guided_home) :- guided_home.
outcome(waited_for_ranger) :- waited_for_ranger.
outcome(hopeless) :- hopeless.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for tid in sorted(setting.afford_threats):
            lines.append(asp.fact("affords", sid, tid))
    for tid, threat in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("base_severity", tid, threat.severity))
    for aid_id, aid in AIDS.items():
        lines.append(asp.fact("aid", aid_id))
        lines.append(asp.fact("sense", aid_id, aid.sense))
        lines.append(asp.fact("power", aid_id, aid.power))
        lines.append(asp.fact("hold", aid_id, aid.hold))
        for tid in sorted(aid.helps):
            lines.append(asp.fact("helps", aid_id, tid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp

    extra = "\n".join(
        [
            asp.fact("chosen_setting", params.setting),
            asp.fact("chosen_threat", params.threat),
            asp.fact("chosen_aid", params.aid),
            asp.fact("delay", params.delay),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _smoke_generate() -> None:
    sample = generate(CURATED[0])
    if not sample.story.strip():
        raise StoryError("Smoke test failed: generated story was empty.")
    if "terrapin" not in sample.story:
        raise StoryError("Smoke test failed: generated story missed required seed word.")


def asp_verify() -> int:
    rc = 0

    py_valid = set(valid_combos())
    asp_valid = set(asp_valid_combos())
    if py_valid == asp_valid:
        print(f"OK: gate matches valid_combos() ({len(py_valid)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid triples:")
        if asp_valid - py_valid:
            print("  only in clingo:", sorted(asp_valid - py_valid))
        if py_valid - asp_valid:
            print("  only in python:", sorted(py_valid - asp_valid))

    scenarios: list[StoryParams] = list(CURATED)
    for seed in range(100):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        scenarios.append(params)

    mismatches = 0
    for params in scenarios:
        if asp_outcome(params) != outcome_of_params(params):
            mismatches += 1
    if mismatches == 0:
        print(f"OK: outcome model matches on {len(scenarios)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {mismatches}/{len(scenarios)} outcomes differ.")

    try:
        _smoke_generate()
        print("OK: smoke test generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a terrapin, a danger, and calm kindness."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--delay", type=int, choices=[0, 1, 2])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible triples derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check ASP/Python parity and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.threat and args.aid:
        setting = SETTINGS[args.setting]
        threat = THREATS[args.threat]
        aid = AIDS[args.aid]
        if not (threat_fits(setting, threat) and aid_works(aid, threat) and aid.sense >= SENSE_MIN):
            raise StoryError(explain_rejection(setting, threat, aid))

    combos = [
        combo for combo in valid_combos()
        if (args.setting is None or combo[0] == args.setting)
        and (args.threat is None or combo[1] == args.threat)
        and (args.aid is None or combo[2] == args.aid)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    setting_id, threat_id, aid_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)

    if args.delay is not None:
        params = StoryParams(
            setting=setting_id,
            threat=threat_id,
            aid=aid_id,
            child_name=name,
            child_gender=gender,
            parent=parent,
            trait=trait,
            delay=args.delay,
        )
        if outcome_of_params(params) == "hopeless":
            raise StoryError(explain_delay(params))
        return params

    good_delays = []
    for delay in [0, 1, 2]:
        trial = StoryParams(
            setting=setting_id,
            threat=threat_id,
            aid=aid_id,
            child_name=name,
            child_gender=gender,
            parent=parent,
            trait=trait,
            delay=delay,
        )
        if outcome_of_params(trial) != "hopeless":
            good_delays.append(delay)
    if not good_delays:
        raise StoryError("(No believable delay works for the chosen danger and aid.)")

    return StoryParams(
        setting=setting_id,
        threat=threat_id,
        aid=aid_id,
        child_name=name,
        child_gender=gender,
        parent=parent,
        trait=trait,
        delay=rng.choice(good_delays),
    )


def generate(params: StoryParams) -> StorySample:
    try:
        setting = SETTINGS[params.setting]
        threat = THREATS[params.threat]
        aid = AIDS[params.aid]
    except KeyError as err:
        raise StoryError(f"(Invalid parameter key: {err.args[0]})") from err

    if not (threat_fits(setting, threat) and aid_works(aid, threat) and aid.sense >= SENSE_MIN):
        raise StoryError(explain_rejection(setting, threat, aid))
    if outcome_of_params(params) == "hopeless":
        raise StoryError(explain_delay(params))

    world = tell(
        setting=setting,
        threat=threat,
        aid=aid,
        child_name=params.child_name,
        child_gender=params.child_gender,
        parent_type=params.parent,
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, threat, aid) triples:\n")
        for setting, threat, aid in combos:
            print(f"  {setting:9} {threat:12} {aid}")
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
            header = (
                f"### {p.child_name}: {p.threat} at {p.setting} with {p.aid} "
                f"({outcome_of_params(p)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
