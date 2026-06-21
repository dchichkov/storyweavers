#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/interactive_replica_bad_ending_folk_tale.py
======================================================================

A small storyworld for a folk-tale-shaped bad ending built around a tempting
fake warning tool: a child is trusted with the village alarm, a peddler offers
an "interactive replica" of the true warning instrument, and when danger comes,
the child chooses the clever-sounding copy over the real thing. The copy can
answer back, but it cannot call the village. Help does not come in time, and
something precious is lost.

The world model prefers only a few coherent variants:

* a hill village, wolves, and the goat pen
* a riverside village, floodwater, and the mill
* a pine-edge village, sparks, and the hayrick

Every generated sample keeps the same bad-ending folk-tale shape, but the exact
setting, instrument, child, and degree of loss vary in a grounded way.

Run it
------
    python storyworlds/worlds/gpt-5.4/interactive_replica_bad_ending_folk_tale.py
    python storyworlds/worlds/gpt-5.4/interactive_replica_bad_ending_folk_tale.py --place hill --danger wolves
    python storyworlds/worlds/gpt-5.4/interactive_replica_bad_ending_folk_tale.py --target mill
    python storyworlds/worlds/gpt-5.4/interactive_replica_bad_ending_folk_tale.py --all
    python storyworlds/worlds/gpt-5.4/interactive_replica_bad_ending_folk_tale.py --trace --seed 7
    python storyworlds/worlds/gpt-5.4/interactive_replica_bad_ending_folk_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4/interactive_replica_bad_ending_folk_tale.py --verify
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

# Make the shared result containers importable when this nested script is run
# directly from the repo root.
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
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    village: str
    opening: str
    warning_name: str
    warning_phrase: str
    warning_place: str
    echo_desc: str
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Danger:
    id: str
    sign: str
    arrival: str
    target_kind: str
    rush: int
    whisper: str
    mild_loss: str
    grave_loss: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Target:
    id: str
    kind: str
    label: str
    phrase: str
    keeper_task: str
    fragility: int
    mild_after: str
    grave_after: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.delay: int = 1

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
        out = World()
        out.entities = copy.deepcopy(self.entities)
        out.fired = set(self.fired)
        out.paragraphs = [[]]
        out.delay = self.delay
        return out


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_false_alarm(world: World) -> list[str]:
    child = world.get("child")
    replica = world.get("replica")
    village = world.get("village")
    if replica.meters["used"] < THRESHOLD or village.meters["warned"] >= THRESHOLD:
        return []
    sig = ("false_alarm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    village.meters["fooled"] += 1
    child.memes["false_hope"] += 1
    return ["__false_alarm__"]


def _r_harm(world: World) -> list[str]:
    danger = world.get("danger")
    village = world.get("village")
    target = world.get("target")
    child = world.get("child")
    elder = world.get("elder")
    if danger.meters["active"] < THRESHOLD or village.meters["warned"] >= THRESHOLD:
        return []
    sig = ("harm",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    severity = float(danger.attrs["rush"] + world.delay)
    target.meters["harm"] += severity
    child.memes["fear"] += 1
    elder.memes["grief"] += 1
    return ["__harm__"]


CAUSAL_RULES = [
    Rule(name="false_alarm", tag="social", apply=_r_false_alarm),
    Rule(name="harm", tag="physical", apply=_r_harm),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for item in produced:
            if not item.startswith("__"):
                world.say(item)
    return produced


def valid_combo(place: str, danger: str, target: str) -> bool:
    if place not in SETTINGS or danger not in DANGERS or target not in TARGETS:
        return False
    return danger in SETTINGS[place].affords and TARGETS[target].kind == DANGERS[danger].target_kind


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for danger_id in DANGERS:
            if danger_id not in setting.affords:
                continue
            for target_id, target in TARGETS.items():
                if target.kind == DANGERS[danger_id].target_kind:
                    combos.append((place, danger_id, target_id))
    return combos


def loss_level_of(danger: Danger, target: Target, delay: int) -> str:
    return "grave" if danger.rush + delay > target.fragility else "hard"


def predict_loss(setting: Setting, danger: Danger, target: Target, delay: int) -> dict:
    level = loss_level_of(danger, target, delay)
    return {
        "level": level,
        "warned": False,
        "severity": danger.rush + delay,
        "loss_text": danger.grave_loss if level == "grave" else danger.mild_loss,
    }


def explain_rejection(place: Optional[str], danger: Optional[str], target: Optional[str]) -> str:
    if place and danger and danger not in SETTINGS[place].affords:
        return (
            f"(No story: {SETTINGS[place].village} does not fit the danger '{danger}'. "
            f"Pick one of {', '.join(sorted(SETTINGS[place].affords))} for that village.)"
        )
    if danger and target and TARGETS[target].kind != DANGERS[danger].target_kind:
        want = DANGERS[danger].target_kind
        return (
            f"(No story: {danger} threatens a {want}, but {TARGETS[target].label} is a "
            f"{TARGETS[target].kind}. The warning must fail in a believable way.)"
        )
    return "(No valid combination matches the given options.)"


def introduce(world: World, child: Entity, elder: Entity, setting: Setting, target: Target) -> None:
    world.say(
        f"In {setting.village}, where {setting.opening}, there lived a child named {child.id}."
    )
    world.say(
        f"{child.id} often helped {elder.id}, {child.pronoun('possessive')} {elder.label_word}, "
        f"who kept watch over {target.phrase} and over {setting.warning_phrase} in {setting.warning_place}."
    )
    world.say(
        f"{elder.id} would always say, \"A true {setting.warning_name} is plain and honest. "
        f"When it speaks, every door in the village should hear it.\""
    )


def temptation(world: World, child: Entity, setting: Setting) -> None:
    replica = world.get("replica")
    peddler = world.get("peddler")
    child.memes["curiosity"] += 1
    child.memes["pride"] += 1
    world.say(
        f"One market morning a bent peddler came along the road with a pack full of bright oddments."
    )
    world.say(
        f'From the pack {peddler.id} drew {replica.phrase} and whispered, '
        f'"Here is an interactive replica of the village {setting.warning_name}. '
        f'Ask it a question and it answers. Strike it lightly and it echoes like the true one."'
    )
    world.say(
        f"{child.id} had never seen such a thing. The little copy gleamed, and its clever voice made "
        f"{child.pronoun('object')} feel older and wiser than the other children."
    )


def elder_warning(world: World, child: Entity, elder: Entity, setting: Setting, danger: Danger) -> None:
    pred = predict_loss(setting, danger, TARGETS[world.facts["target_cfg"].id], world.delay)
    world.facts["predicted_level"] = pred["level"]
    world.facts["predicted_severity"] = pred["severity"]
    child.memes["doubt"] += 1
    world.say(
        f"{elder.id} frowned when {child.id} showed the trinket. "
        f'"A copy may chatter, but it cannot carry warning over wind and water," '
        f"{elder.pronoun()} said. \"If {danger.sign} comes, run to the real {setting.warning_name}.\""
    )


def danger_comes(world: World, child: Entity, danger: Danger, setting: Setting) -> None:
    danger_ent = world.get("danger")
    child.memes["urgency"] += 1
    danger_ent.meters["active"] += 1
    world.say(
        f"Not many days later, {danger.sign}. {danger.arrival}"
    )
    world.say(
        f"{child.id} was nearest to {setting.warning_place}, and for one breath the child stood between "
        f"good sense and the glittering toy."
    )


def choose_replica(world: World, child: Entity, setting: Setting) -> None:
    replica = world.get("replica")
    child.memes["choice_pride"] += 1
    replica.meters["used"] += 1
    world.say(
        f"Instead of climbing to the real {setting.warning_name}, {child.id} snatched up the interactive replica."
    )
    world.say(
        f"{child.pronoun().capitalize()} tapped it and cried, \"Call the village!\" "
        f"The little copy answered in a sweet voice, \"I hear you. I hear you.\""
    )
    world.say(
        f"It sang back to the child exactly as the peddler had promised, but its sound stayed close, "
        f"no louder than a bird in a hedge."
    )


def ruin(world: World, child: Entity, elder: Entity, danger: Danger, target: Target) -> None:
    propagate(world, narrate=False)
    target_ent = world.get("target")
    level = loss_level_of(danger, target, world.delay)
    world.facts["loss_level"] = level
    if level == "grave":
        world.say(danger.grave_loss)
        world.say(target.grave_after)
    else:
        world.say(danger.mild_loss)
        world.say(target.mild_after)
    world.say(
        f"By the time {elder.id} heard the true trouble and came running, the wrong choice had already grown heavy."
    )
    child.memes["shame"] += 1
    elder.memes["sorrow"] += 1
    target_ent.attrs["loss_level"] = level


def aftermath(world: World, child: Entity, elder: Entity, setting: Setting, danger: Danger, target: Target) -> None:
    replica = world.get("replica")
    world.say(
        f"{elder.id} took the replica from {child.id}'s hands. It was still ready with its tiny answer, "
        f'but now its cleverness sounded thin and foolish.'
    )
    world.say(
        f'"Remember this," {elder.id} said at last. "{danger.lesson} A thing that only answers you is not the same '
        f'as a thing that can help everyone."'
    )
    world.say(
        f"{child.id} looked toward {target.phrase}, and the village seemed older and sadder than it had at sunrise."
    )
    world.say(
        f"As for the peddler, he was gone by evening, and the interactive replica lay silent on the table, "
        f"only a copy after all."
    )
    replica.memes["discarded"] += 1


def tell(
    setting: Setting,
    danger: Danger,
    target_cfg: Target,
    *,
    child_name: str,
    child_type: str,
    elder_type: str,
    trait: str,
    delay: int,
) -> World:
    world = World()
    world.delay = delay
    child = world.add(Entity(
        id="child",
        kind="character",
        type=child_type,
        label=child_name,
        role="child",
        attrs={"name": child_name, "trait": trait},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=elder_type,
        label="the elder",
        role="elder",
        attrs={"name": "Grandam" if elder_type == "mother" else "Old Bran"},
    ))
    peddler = world.add(Entity(
        id="peddler",
        kind="character",
        type="man",
        label="the peddler",
        role="tempter",
    ))
    village = world.add(Entity(
        id="village",
        type="place",
        label=setting.village,
    ))
    replica = world.add(Entity(
        id="replica",
        type="tool",
        label=f"replica {setting.warning_name}",
        phrase=f"a small interactive replica {setting.warning_name}",
        attrs={"interactive": True, "replica": True, "warning_name": setting.warning_name},
        tags={"interactive", "replica"},
    ))
    danger_ent = world.add(Entity(
        id="danger",
        type="danger",
        label=danger.id,
        attrs={"rush": danger.rush},
        tags=set(danger.tags),
    ))
    target = world.add(Entity(
        id="target",
        type=target_cfg.kind,
        label=target_cfg.label,
        phrase=target_cfg.phrase,
        attrs={"fragility": target_cfg.fragility},
        tags=set(target_cfg.tags),
    ))

    world.facts["child_cfg_name"] = child_name
    world.facts["target_cfg"] = target_cfg
    world.facts["setting_cfg"] = setting
    world.facts["danger_cfg"] = danger

    introduce(world, child, elder, setting, target_cfg)
    world.para()
    temptation(world, child, setting)
    elder_warning(world, child, elder, setting, danger)
    world.para()
    danger_comes(world, child, danger, setting)
    choose_replica(world, child, setting)
    world.para()
    ruin(world, child, elder, danger, target_cfg)
    aftermath(world, child, elder, setting, danger, target_cfg)

    world.facts.update(
        child=child,
        elder=elder,
        peddler=peddler,
        replica=replica,
        village=village,
        target=target,
        danger=danger_ent,
        loss_level=world.facts.get("loss_level", "hard"),
        delay=delay,
    )
    return world


SETTINGS = {
    "hill": Setting(
        id="hill",
        village="the hill village",
        opening="the wind combed the sheep paths and the stones remembered old footsteps",
        warning_name="bell",
        warning_phrase="the bronze bell",
        warning_place="the watch tower",
        echo_desc="a round bronze mouth and a bright little tongue",
        affords={"wolves"},
        tags={"bell", "village"},
    ),
    "riverside": Setting(
        id="riverside",
        village="the riverside village",
        opening="the river bent like a silver arm around the houses",
        warning_name="horn",
        warning_phrase="the long river horn",
        warning_place="the landing stage",
        echo_desc="a curved mouth of polished horn and painted reeds",
        affords={"flood"},
        tags={"horn", "village"},
    ),
    "pine": Setting(
        id="pine",
        village="the pine-edge village",
        opening="the trees stood dark beyond the fields and resin sweetened the air",
        warning_name="drum",
        warning_phrase="the warning drum",
        warning_place="the square by the well",
        echo_desc="a tight skin and bright red cords",
        affords={"sparks"},
        tags={"drum", "village"},
    ),
}

DANGERS = {
    "wolves": Danger(
        id="wolves",
        sign="the dogs began to bark toward the dusk-blue slope",
        arrival="From the high grass came the quick gray shapes of wolves, lean with hunger.",
        target_kind="herd",
        rush=2,
        whisper="They come softly and leave emptiness behind.",
        mild_loss="The wolves snatched two goats before anyone reached the pen.",
        grave_loss="The wolves broke the whole pen, and by dawn nearly the whole goat herd was gone.",
        lesson="Wolves do not wait for pretty noises",
        tags={"wolves"},
    ),
    "flood": Danger(
        id="flood",
        sign="the river rose against its banks and began to carry branches like thrown spears",
        arrival="Brown water came racing at the posts below the mill, faster than shouting feet.",
        target_kind="building",
        rush=1,
        whisper="Water does not stop to hear excuses.",
        mild_loss="The flood tore away the mill wheel and left the lower room full of mud.",
        grave_loss="The flood struck hard, ripped the mill from its posts, and carried the wheel downstream.",
        lesson="Floodwater does not pause because a child has been deceived",
        tags={"flood"},
    ),
    "sparks": Danger(
        id="sparks",
        sign="a hard wind blew from the charcoal pits and carried red sparks over the field",
        arrival="One bright coal landed in the straw and at once a hungry fire began to creep.",
        target_kind="fodder",
        rush=2,
        whisper="Fire grows while people are still deciding.",
        mild_loss="Half the hayrick burned before the first bucket came.",
        grave_loss="The whole hayrick flared up, and the winter fodder folded into black ash.",
        lesson="Fire listens only to haste and to water",
        tags={"fire"},
    ),
}

TARGETS = {
    "goats": Target(
        id="goats",
        kind="herd",
        label="goats",
        phrase="the goat pen",
        keeper_task="keeping the pen gate latched at dusk",
        fragility=3,
        mild_after="All that evening the children counted the gaps in the herd, and every missing bell note sounded sharp.",
        grave_after="For many mornings after, the pen looked wide and wrong, and the poorer families had less milk to share.",
        tags={"goats"},
    ),
    "mill": Target(
        id="mill",
        kind="building",
        label="mill",
        phrase="the old mill",
        keeper_task="watching the grain sacks stay dry",
        fragility=2,
        mild_after="The miller spent the week scraping mud from the stones while the village waited for flour.",
        grave_after="Afterward people ground grain by hand, and bread came slowly and dearly to the tables.",
        tags={"mill"},
    ),
    "hayrick": Target(
        id="hayrick",
        kind="fodder",
        label="hayrick",
        phrase="the winter hayrick",
        keeper_task="stacking the straw high and dry for cold months",
        fragility=2,
        mild_after="Smoke clung to the square, and every spared bundle had to be guarded like treasure.",
        grave_after="When snow later came, everyone remembered the empty place where the fodder should have stood.",
        tags={"hay"},
    ),
}


@dataclass
class StoryParams:
    place: str
    danger: str
    target: str
    child_name: str
    child_gender: str
    elder: str
    trait: str
    delay: int = 1
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        place="hill",
        danger="wolves",
        target="goats",
        child_name="Mira",
        child_gender="girl",
        elder="mother",
        trait="curious",
        delay=1,
    ),
    StoryParams(
        place="riverside",
        danger="flood",
        target="mill",
        child_name="Tarin",
        child_gender="boy",
        elder="father",
        trait="proud",
        delay=2,
    ),
    StoryParams(
        place="pine",
        danger="sparks",
        target="hayrick",
        child_name="Elsa",
        child_gender="girl",
        elder="mother",
        trait="eager",
        delay=1,
    ),
]

GIRL_NAMES = ["Mira", "Anya", "Lina", "Nessa", "Bria", "Tala", "Iris", "Elin"]
BOY_NAMES = ["Tarin", "Milo", "Oren", "Pavel", "Rowan", "Ivo", "Ned", "Sava"]
TRAITS = ["curious", "proud", "eager", "restless", "trusting", "quick-handed"]

KNOWLEDGE = {
    "replica": [
        (
            "What is a replica?",
            "A replica is a copy made to look like something real. A copy can resemble the real thing without doing the real job."
        )
    ],
    "interactive": [
        (
            "What does interactive mean?",
            "Interactive means something responds when you touch it or speak to it. That does not always mean it is useful in an emergency."
        )
    ],
    "bell": [
        (
            "Why did villages use bells?",
            "A village bell could carry a loud warning over a long distance. People listened for it when danger came."
        )
    ],
    "horn": [
        (
            "What is a warning horn?",
            "A warning horn is blown to make a strong sound that many people can hear. It helps call people quickly."
        )
    ],
    "drum": [
        (
            "Why would people beat a warning drum?",
            "A warning drum makes a sharp carrying rhythm. In a village, that rhythm could tell everyone to hurry."
        )
    ],
    "wolves": [
        (
            "Why are wolves dangerous to farm animals?",
            "Wolves hunt quickly and can carry off small animals or break into a pen. Farmers protect their herds by warning one another fast."
        )
    ],
    "flood": [
        (
            "Why is floodwater dangerous?",
            "Floodwater moves with great force and can knock down wood, stone, and wheels. It can ruin buildings before people have much time to react."
        )
    ],
    "fire": [
        (
            "Why must people answer a fire quickly?",
            "A small flame can grow larger every moment. Quick warning gives more people time to bring water and help."
        )
    ],
    "goats": [
        (
            "Why were goats important in old villages?",
            "Goats gave milk and sometimes cheese, and they were valuable to a family. Losing them could make a village poorer."
        )
    ],
    "mill": [
        (
            "Why was a mill important?",
            "A mill turned grain into flour for bread. If a mill stopped working, feeding the village became harder."
        )
    ],
    "hay": [
        (
            "Why is hay important in winter?",
            "Hay is dried grass stored for animals to eat when fields are cold or bare. If hay burns, animals may have too little food later."
        )
    ],
}
KNOWLEDGE_ORDER = ["interactive", "replica", "bell", "horn", "drum", "wolves", "flood", "fire", "goats", "mill", "hay"]


def child_name(world: World) -> str:
    return world.facts["child_cfg_name"]


def generation_prompts(world: World) -> list[str]:
    setting = world.facts["setting_cfg"]
    danger = world.facts["danger_cfg"]
    target = world.facts["target_cfg"]
    cname = child_name(world)
    return [
        (
            f'Write a short folk tale for a young child that includes the words "interactive" '
            f'and "replica" and ends badly. A child trusts a false warning {setting.warning_name}, '
            f'and {target.phrase} is lost when {danger.id} come.'
        ),
        (
            f"Tell a folk-tale-style story about {cname}, a village child who is tempted by an "
            f"interactive replica {setting.warning_name} and uses it at the wrong time."
        ),
        (
            f"Write a cautionary village tale with a sad ending, where a talking copy seems clever "
            f"but fails to do the work of the real thing."
        ),
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    setting = world.facts["setting_cfg"]
    danger = world.facts["danger_cfg"]
    target = world.facts["target_cfg"]
    cname = child_name(world)
    elder = world.get("elder")
    level = world.facts["loss_level"]
    answer_loss = danger.grave_loss if level == "grave" else danger.mild_loss
    result = [
        (
            "Who is the story about?",
            f"It is about {cname}, a village child, and {elder.attrs['name']}, the elder who cared for {target.phrase}. "
            f"The tale also turns on a peddler's fake warning tool."
        ),
        (
            f"What was the interactive replica?",
            f"It was a small copy of the village {setting.warning_name} that could answer back when {cname} spoke to it. "
            f"It sounded clever, but it could not send a real warning through the village."
        ),
        (
            f"Why did the elder distrust the replica?",
            f"{elder.attrs['name']} knew a true warning tool had to reach many ears at once. "
            f"A toy that only answered the child could not bring the neighbors running."
        ),
        (
            f"What happened when {danger.id} came?",
            f"{cname} chose the interactive replica instead of the real {setting.warning_name}. "
            f"Because the warning did not carry, help came too late."
        ),
        (
            f"What was lost in the end?",
            f"{answer_loss} The ending is sad because the wrong tool delayed the whole village."
        ),
        (
            "What is the lesson of the story?",
            f"The story teaches that a pretty copy is not the same as the real thing. "
            f"In danger, what matters is not whether a tool sounds clever, but whether it truly helps."
        ),
    ]
    return result


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    setting = world.facts["setting_cfg"]
    danger = world.facts["danger_cfg"]
    target = world.facts["target_cfg"]
    tags = {"interactive", "replica"} | set(setting.tags) | set(danger.tags) | set(target.tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
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
        if ent.role:
            bits.append(f"role={ent.role}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v or v == 0}
            if shown:
                bits.append(f"attrs={shown}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.tags:
            bits.append(f"tags={sorted(ent.tags)}")
        lines.append(f"  {ent.id:8} ({ent.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    lines.append(f"  delay: {world.delay}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, D, T) :- setting(P), danger(D), target(T), affords(P, D), target_kind(T, K), threatens(D, K).

severity(V) :- chosen_danger(D), delay(Delay), rush(D, R), V = R + Delay.
grave :- chosen_target(T), severity(V), fragility(T, F), V > F.
loss(grave) :- grave.
loss(hard) :- not grave.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place_id))
        for danger_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place_id, danger_id))
    for danger_id, danger in DANGERS.items():
        lines.append(asp.fact("danger", danger_id))
        lines.append(asp.fact("threatens", danger_id, danger.target_kind))
        lines.append(asp.fact("rush", danger_id, danger.rush))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        lines.append(asp.fact("target_kind", target_id, target.kind))
        lines.append(asp.fact("fragility", target_id, target.fragility))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_loss(params: StoryParams) -> str:
    import asp

    extra = "\n".join([
        asp.fact("chosen_danger", params.danger),
        asp.fact("chosen_target", params.target),
        asp.fact("delay", params.delay),
    ])
    model = asp.one_model(asp_program(extra, "#show loss/1."))
    losses = sorted(atom[0] for atom in asp.atoms(model, "loss"))
    return "grave" if "grave" in losses else "hard"


def asp_verify() -> int:
    rc = 0

    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: gate matches valid_combos() ({len(python_set)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid combos:")
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))

    cases = list(CURATED)
    for seed in range(40):
        try:
            params = resolve_params(build_parser().parse_args([]), random.Random(seed))
        except StoryError:
            continue
        params.seed = seed
        cases.append(params)

    mismatches = []
    for params in cases:
        py = loss_level_of(DANGERS[params.danger], TARGETS[params.target], params.delay)
        cl = asp_loss(params)
        if py != cl:
            mismatches.append((params, py, cl))
    if not mismatches:
        print(f"OK: loss model matches on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {len(mismatches)}/{len(cases)} loss outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("empty story")
        if "interactive replica" not in sample.story:
            raise StoryError("story lost seed words")
        print("OK: smoke test generated a normal story.")
    except Exception as err:  # pragma: no cover - verification path
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a folk-tale child trusts an interactive replica warning tool, and the ending goes badly."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--danger", choices=DANGERS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--child-name")
    ap.add_argument("--elder", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[1, 2], help="how long the child lingers with the fake tool")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list compatible combos derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP twin and run a smoke test")
    ap.add_argument("--show-asp", action="store_true", help="print the ASP program")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.danger and args.target and not valid_combo(args.place, args.danger, args.target):
        raise StoryError(explain_rejection(args.place, args.danger, args.target))
    if args.place and args.danger and args.danger not in SETTINGS[args.place].affords:
        raise StoryError(explain_rejection(args.place, args.danger, args.target))
    if args.danger and args.target and TARGETS[args.target].kind != DANGERS[args.danger].target_kind:
        raise StoryError(explain_rejection(args.place, args.danger, args.target))

    combos = [
        combo for combo in valid_combos()
        if (args.place is None or combo[0] == args.place)
        and (args.danger is None or combo[1] == args.danger)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError(explain_rejection(args.place, args.danger, args.target))

    place, danger, target = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    elder = args.elder or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.choice([1, 2])
    return StoryParams(
        place=place,
        danger=danger,
        target=target,
        child_name=child_name,
        child_gender=child_gender,
        elder=elder,
        trait=trait,
        delay=delay,
    )


def _validate_params(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        raise StoryError(f"(Unknown place: {params.place})")
    if params.danger not in DANGERS:
        raise StoryError(f"(Unknown danger: {params.danger})")
    if params.target not in TARGETS:
        raise StoryError(f"(Unknown target: {params.target})")
    if params.child_gender not in {"girl", "boy"}:
        raise StoryError(f"(Unknown child gender: {params.child_gender})")
    if params.elder not in {"mother", "father"}:
        raise StoryError(f"(Unknown elder: {params.elder})")
    if params.delay not in {1, 2}:
        raise StoryError("(Delay must be 1 or 2.)")
    if not valid_combo(params.place, params.danger, params.target):
        raise StoryError(explain_rejection(params.place, params.danger, params.target))


def generate(params: StoryParams) -> StorySample:
    _validate_params(params)
    world = tell(
        SETTINGS[params.place],
        DANGERS[params.danger],
        TARGETS[params.target],
        child_name=params.child_name,
        child_type=params.child_gender,
        elder_type=params.elder,
        trait=params.trait,
        delay=params.delay,
    )
    story = world.render().replace("child named child", f"child named {params.child_name}")
    story = story.replace("child's", f"{params.child_name}'s")
    story = story.replace("child ", f"{params.child_name} ", 1) if story.startswith("child ") else story
    story = story.replace(" child ", f" {params.child_name} ")
    story = story.replace("elder", world.get("elder").attrs["name"])
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("", "#show valid/3.\n#show loss/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, danger, target) combos:\n")
        for place, danger, target in combos:
            print(f"  {place:10} {danger:8} {target}")
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
            header = f"### {p.child_name}: {p.danger} in {p.place} (target: {p.target}, delay: {p.delay})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
