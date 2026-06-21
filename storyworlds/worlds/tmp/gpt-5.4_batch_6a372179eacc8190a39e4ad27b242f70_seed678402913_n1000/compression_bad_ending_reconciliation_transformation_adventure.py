#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/compression_bad_ending_reconciliation_transformation_adventure.py
=============================================================================================

A standalone story world about a dangerous shortcut in an adventure tale:
a child uses a magical compression tool on something important, an expedition
goes wrong, feelings are hurt, and the ending depends on whether the team can
restore what changed in time.

The world is built around three requested features:

* Bad Ending: some valid parameter sets end with the adventure cut short.
* Reconciliation: after the mistake, the children must make up and work together.
* Transformation: the central object is literally transformed by compression,
  and the instigator is emotionally transformed by the lesson.

Run it
------
    python storyworlds/worlds/gpt-5.4/compression_bad_ending_reconciliation_transformation_adventure.py
    python storyworlds/worlds/gpt-5.4/compression_bad_ending_reconciliation_transformation_adventure.py --target rope_bridge
    python storyworlds/worlds/gpt-5.4/compression_bad_ending_reconciliation_transformation_adventure.py --target stone_gate
    python storyworlds/worlds/gpt-5.4/compression_bad_ending_reconciliation_transformation_adventure.py --response pull_hard
    python storyworlds/worlds/gpt-5.4/compression_bad_ending_reconciliation_transformation_adventure.py --all
    python storyworlds/worlds/gpt-5.4/compression_bad_ending_reconciliation_transformation_adventure.py --verify
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 6.0
CAUTIOUS_TRAITS = {"careful", "cautious", "patient", "steady"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    compressible: bool = False
    essential: bool = False
    safe_tool: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Theme:
    id: str
    scene: str
    path: str
    goal: str
    treasure: str
    opening_image: str
    ending_image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    source: str
    cry: str
    warning: str
    makes_compression: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class TargetCfg:
    id: str
    label: str
    the: str
    phrase: str
    use: str
    tiny_shape: str
    restore_image: str
    fragility: int
    compressible: bool = True
    essential: bool = True
    tags: set[str] = field(default_factory=set)

    @property
    def The(self) -> str:
        return self.the[0].upper() + self.the[1:]


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SupportTool:
    id: str
    label: str
    phrase: str
    use: str
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
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"instigator", "partner"}]

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


def _r_compression_danger(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["compressed"] < THRESHOLD:
            continue
        sig = ("compressed", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.essential:
            if "path" in world.entities:
                world.get("path").meters["blocked"] += 1
            for kid in world.kids():
                kid.memes["fear"] += 1
            out.append("__danger__")
    return out


def _r_restored_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["restored"] < THRESHOLD:
            continue
        sig = ("restored", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if "path" in world.entities:
            world.get("path").meters["blocked"] = 0.0
        for kid in world.kids():
            if kid.memes["fear"] >= THRESHOLD:
                kid.memes["fear"] = 0.0
            kid.memes["hope"] += 1
        out.append("__relief__")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule(name="compression_danger", tag="physical", apply=_r_compression_danger),
    Rule(name="restored_relief", tag="physical", apply=_r_restored_relief),
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


THEMES = {
    "jungle": Theme(
        id="jungle",
        scene="a green jungle where parrots flashed like scraps of paint",
        path="a cliff path above a rushing river",
        goal="the moon-coin chamber",
        treasure="the moon coins hidden behind the waterfall",
        opening_image="Vines swung over the path, and the river sparkled far below.",
        ending_image="The waterfall shone silver, and the path looked brave again.",
        tags={"jungle", "adventure"},
    ),
    "desert": Theme(
        id="desert",
        scene="a golden desert where the wind drew lines in the sand",
        path="a ridge path between two tall rocks",
        goal="the whispering arch",
        treasure="the star shells tucked inside the old arch",
        opening_image="The sun painted the rocks orange, and a hawk circled high above.",
        ending_image="The ridge glowed pink in the evening, and the wind sounded softer.",
        tags={"desert", "adventure"},
    ),
    "ice": Theme(
        id="ice",
        scene="a blue ice valley where the walls shone like glass",
        path="a snowy ledge above a frozen pool",
        goal="the lantern cave",
        treasure="the crystal lanterns sleeping in the cave",
        opening_image="Snow glittered like sugar, and the cold air made every breath puff white.",
        ending_image="The cave mouth glittered, and the snow looked calm instead of sharp.",
        tags={"ice", "adventure"},
    ),
}

ARTIFACTS = {
    "compression_charm": Artifact(
        id="compression_charm",
        label="the compression charm",
        phrase="a brass compression charm shaped like a curled leaf",
        source="in the guide's satchel",
        cry="A compression charm!",
        warning="It is for careful packing by grown explorers, never for guessing games.",
        tags={"compression", "magic"},
    ),
    "squeeze_flute": Artifact(
        id="squeeze_flute",
        label="the squeeze flute",
        phrase="a little squeeze flute carved from bone",
        source="wrapped in cloth beside the map",
        cry="The squeeze flute!",
        warning="Its tune can shrink gear that ought to stay full-sized.",
        tags={"compression", "music", "magic"},
    ),
}

TARGETS = {
    "rope_bridge": TargetCfg(
        id="rope_bridge",
        label="rope bridge",
        the="the rope bridge",
        phrase="the swaying rope bridge",
        use="cross the roaring gap",
        tiny_shape="a tight little coil no bigger than a scarf ring",
        restore_image="The ropes stretched long again and the boards knocked gently in the wind",
        fragility=3,
        compressible=True,
        essential=True,
        tags={"bridge", "rope", "adventure"},
    ),
    "canoe": TargetCfg(
        id="canoe",
        label="canoe",
        the="the canoe",
        phrase="the narrow red canoe",
        use="glide across the dark river",
        tiny_shape="a toy boat small enough to sit in a palm",
        restore_image="The hull widened and the painted sides gleamed with river drops",
        fragility=2,
        compressible=True,
        essential=True,
        tags={"boat", "river", "adventure"},
    ),
    "glider": TargetCfg(
        id="glider",
        label="cloth glider",
        the="the cloth glider",
        phrase="the cliff glider with bright stitched wings",
        use="sail over the last wide crack",
        tiny_shape="a folded scrap with wings pressed flat as leaves",
        restore_image="The wings opened broad and bright, catching the wind at once",
        fragility=2,
        compressible=True,
        essential=True,
        tags={"glider", "wind", "adventure"},
    ),
    "stone_gate": TargetCfg(
        id="stone_gate",
        label="stone gate",
        the="the stone gate",
        phrase="the heavy stone gate",
        use="open the way",
        tiny_shape="",
        restore_image="",
        fragility=0,
        compressible=False,
        essential=True,
        tags={"stone"},
    ),
}

RESPONSES = {
    "release_song": Response(
        id="release_song",
        sense=3,
        power=4,
        text="lifted the artifact high and sang the old release song until the squeezed shape unfurled",
        fail="sang the release song with all the right notes, but the compressed shape only trembled and stayed tiny",
        qa_text="used the release song to undo the compression",
        tags={"release_song", "music", "magic"},
    ),
    "spring_water": Response(
        id="spring_water",
        sense=3,
        power=3,
        text="poured cold spring water over the tiny shape and spoke the waking words until it swelled back to its true form",
        fail="poured spring water over the tiny shape, but it stayed pinched and small",
        qa_text="used spring water and waking words to restore it",
        tags={"spring_water", "magic"},
    ),
    "pull_hard": Response(
        id="pull_hard",
        sense=1,
        power=1,
        text="pulled at the tiny shape until it somehow opened again",
        fail="pulled at the tiny shape, but tugging only made everyone more frightened",
        qa_text="pulled at it until it opened",
        tags={"force"},
    ),
}

SUPPORT_TOOLS = {
    "pack_frame": SupportTool(
        id="pack_frame",
        label="pack frame",
        phrase="a wooden pack frame",
        use="carry the gear the slow, safe way",
        tags={"packing", "adventure"},
    ),
    "haul_rope": SupportTool(
        id="haul_rope",
        label="haul rope",
        phrase="a coil of hauling rope",
        use="lower the gear carefully instead of shrinking it",
        tags={"rope", "adventure"},
    ),
    "sled": SupportTool(
        id="sled",
        label="sled",
        phrase="a little trail sled",
        use="slide the gear over rough ground without changing its shape",
        tags={"sled", "adventure"},
    ),
}

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Lucy", "Anna", "Maya", "Nora", "Rose"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Jack", "Finn", "Noah", "Eli", "Theo"]
TRAITS = ["careful", "curious", "bold", "patient", "cautious", "eager"]
GUIDE_NAMES = ["Aunt Mara", "Captain Ivo", "Guide Nia", "Uncle Rian"]


def hazard_at_risk(artifact: Artifact, target: TargetCfg) -> bool:
    return artifact.makes_compression and target.compressible and target.essential


def sensible_responses() -> list[Response]:
    return [resp for resp in RESPONSES.values() if resp.sense >= SENSE_MIN]


def compression_severity(target: TargetCfg, delay: int) -> int:
    return target.fragility + delay


def is_restored(response: Response, target: TargetCfg, delay: int) -> bool:
    return response.power >= compression_severity(target, delay)


def initial_caution(trait: str) -> float:
    return 5.0 if trait in CAUTIOUS_TRAITS else 3.0


def would_avert(relation: str, instigator_age: int, partner_age: int, trait: str) -> bool:
    partner_older = relation == "siblings" and partner_age > instigator_age
    authority = initial_caution(trait) + 1.0 + (4.0 if partner_older else 0.0)
    return partner_older and authority > BRAVERY_INIT


def predict_compression(world: World, target_id: str) -> dict:
    sim = world.copy()
    _do_compress(sim, sim.get(target_id), narrate=False)
    return {
        "blocked": sim.get("path").meters["blocked"],
        "tiny": sim.get(target_id).meters["compressed"],
    }


def _do_compress(world: World, target: Entity, narrate: bool = True) -> None:
    target.meters["compressed"] += 1
    target.meters["usable"] = 0.0
    target.meters["tiny"] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, a: Entity, b: Entity, guide: Entity, theme: Theme, target: TargetCfg) -> None:
    for kid in (a, b):
        kid.memes["wonder"] += 1
    world.say(
        f"{theme.opening_image} {a.id}, {b.id}, and {guide.id} were on an adventure in {theme.scene}."
    )
    world.say(
        f"They were following {theme.path} to reach {theme.goal}, where {theme.treasure} waited."
    )
    world.say(
        f"To get there, they still needed {target.phrase} to {target.use}."
    )


def need_shortcut(world: World, a: Entity, b: Entity, target: TargetCfg) -> None:
    world.say(
        f"After a long climb, {target.the} felt awkward and heavy, and {a.id} wished for a faster trick."
    )
    world.say(
        f'{b.id} brushed dust from {b.pronoun("possessive")} knees and said, "Slow can still be brave."'
    )


def tempt(world: World, a: Entity, artifact: Artifact, guide: Entity) -> None:
    a.memes["bravado"] += 1
    world.say(
        f'Then {a.id} spotted {artifact.phrase} {artifact.source}. "{artifact.cry}" {a.pronoun()} whispered.'
    )
    world.say(
        f"For one bright second, using a little compression magic seemed smarter than carrying anything the hard way."
    )
    world.say(
        f"{guide.id} had already warned them: {artifact.warning}"
    )


def warn(world: World, b: Entity, a: Entity, artifact: Artifact, target: TargetCfg) -> None:
    pred = predict_compression(world, "target")
    b.memes["caution"] += 1
    world.facts["predicted_blocked"] = pred["blocked"]
    world.say(
        f'{b.id} shook {b.pronoun("possessive")} head. "{a.id}, if you use {artifact.label}, '
        f'{target.the} could turn tiny, and then we could not {target.use}. The whole path would stop right here."'
    )


def defy(world: World, a: Entity, b: Entity, artifact: Artifact) -> None:
    a.memes["defiance"] += 1
    older = a.attrs.get("relation") == "siblings" and a.age > b.age
    if older:
        world.say(
            f'"I can fix it after," {a.id} said, sounding far too sure. Because {a.id} was '
            f'{b.pronoun("possessive")} older sibling, {b.id} could not stop {a.pronoun("object")} in time.'
        )
    else:
        world.say(
            f'"I can fix it after," {a.id} said, and before anyone else could reach over, {a.pronoun()} used the magic.'
        )


def back_down(world: World, a: Entity, b: Entity, guide: Entity, tool: SupportTool, artifact: Artifact) -> None:
    a.memes["bravery"] = 0.0
    a.memes["relief"] += 1
    b.memes["relief"] += 1
    world.say(
        f'{a.id} looked at {b.id} for a long moment, then slowly put {artifact.label} back. '
        f'"All right," {a.pronoun()} said. "No guessing."'
    )
    world.say(
        f'{guide.id} smiled and handed them {tool.phrase}. Together they chose to {tool.use}.'
    )


def compress_scene(world: World, a: Entity, target_ent: Entity, target: TargetCfg) -> None:
    _do_compress(world, target_ent)
    world.say(
        f"A silver squeeze ran over {target.the}. In a blink, it transformed into {target.tiny_shape}."
    )
    world.say(
        f"{target.The} was no longer big enough to help them {target.use}."
    )


def alarm(world: World, b: Entity, guide: Entity, target: TargetCfg) -> None:
    world.say(
        f'"{target.The}!" {b.id} cried. "{guide.id}, it is tiny!"'
    )


def bad_realization(world: World, a: Entity, b: Entity, target: TargetCfg) -> None:
    a.memes["shame"] += 1
    b.memes["hurt"] += 1
    world.say(
        f"The adventure seemed to shrink with it. The wind felt sharper, and the brave path suddenly looked lonely."
    )
    world.say(
        f'{a.id} swallowed hard. "{b.id}, I was trying to help," {a.pronoun()} said, but the words came out small.'
    )


def reconcile(world: World, a: Entity, b: Entity) -> None:
    a.memes["sorry"] += 1
    b.memes["forgiveness"] += 1
    a.memes["care"] += 1
    b.memes["care"] += 1
    world.say(
        f'{b.id} took a shaky breath. "I was scared," {b.pronoun()} said. "{target_pronoun_line(world)}"'
    )
    world.say(
        f'"I know," {a.id} answered. "I should have listened. I am sorry."'
    )
    world.say(
        f"They touched hands, and the anger between them softened into a plan."
    )


def target_pronoun_line(world: World) -> str:
    target = world.facts["target_cfg"]
    return f"We needed {target.the}, not a trick."


def restore(world: World, guide: Entity, response: Response, target_ent: Entity, target: TargetCfg) -> None:
    target_ent.meters["compressed"] = 0.0
    target_ent.meters["tiny"] = 0.0
    target_ent.meters["restored"] += 1
    target_ent.meters["usable"] = 1.0
    propagate(world, narrate=False)
    world.say(
        f"{guide.id} knelt beside the tiny shape and {response.text}."
    )
    world.say(
        f"{target.restore_image}. {target.The} had transformed back at last."
    )


def transform_hero(world: World, a: Entity) -> None:
    a.memes["lesson"] += 1
    a.memes["shame"] = 0.0
    a.memes["patience"] += 1
    world.say(
        f"{a.id} still loved adventure, but not the showy kind anymore. Something inside {a.pronoun('object')} had changed shape too."
    )


def triumph(world: World, a: Entity, b: Entity, guide: Entity, theme: Theme, target: TargetCfg) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
        kid.memes["trust"] += 1
    world.say(
        f"Side by side, they used {target.the} to {target.use}, and at last they reached {theme.goal}."
    )
    world.say(
        f"There, with {theme.ending_image} {a.id} let {b.id} choose the next careful step, and {b.id} grinned back."
    )


def fail_restore(world: World, guide: Entity, response: Response, target: TargetCfg) -> None:
    if "path" in world.entities:
        world.get("path").meters["blocked"] += 1
    world.say(
        f"{guide.id} {response.fail}."
    )
    world.say(
        f"{target.The} stayed tiny, and the way ahead stayed closed."
    )


def retreat(world: World, a: Entity, b: Entity, guide: Entity, theme: Theme) -> None:
    for kid in (a, b):
        kid.memes["sadness"] += 1
        kid.memes["lesson"] += 1
    world.say(
        f"There would be no treasure that day. {guide.id} turned the party around and led them back along {theme.path} before dark."
    )
    world.say(
        f"The adventure had a bad ending: not because anyone was mean, but because one reckless choice had changed the day too much."
    )
    world.say(
        f"Even so, {a.id} walked beside {b.id} instead of ahead, and neither of them let go."
    )


def safe_end(world: World, guide: Entity, tool: SupportTool, theme: Theme) -> None:
    world.say(
        f"By sunset they had reached {theme.goal} the safe way, using {tool.phrase} to {tool.use}."
    )
    world.say(
        f"The children laughed softly this time, as if the whole adventure had learned to breathe more gently."
    )


def tell(
    theme: Theme,
    artifact: Artifact,
    target: TargetCfg,
    response: Response,
    support: SupportTool,
    instigator: str = "Tom",
    instigator_gender: str = "boy",
    partner: str = "Lily",
    partner_gender: str = "girl",
    guide_name: str = "Guide Nia",
    guide_type: str = "mother",
    trait: str = "careful",
    delay: int = 0,
    instigator_age: int = 6,
    partner_age: int = 4,
    relation: str = "siblings",
) -> World:
    world = World()
    a = world.add(Entity(
        id=instigator,
        kind="character",
        type=instigator_gender,
        role="instigator",
        traits=["bold"],
        age=instigator_age,
        attrs={"relation": relation},
    ))
    b = world.add(Entity(
        id=partner,
        kind="character",
        type=partner_gender,
        role="partner",
        traits=[trait],
        age=partner_age,
        attrs={"relation": relation},
    ))
    guide = world.add(Entity(
        id=guide_name,
        kind="character",
        type=guide_type,
        role="guide",
        label="the guide",
    ))
    world.add(Entity(id="path", type="path", label="the path"))
    world.add(Entity(id="artifact", type="artifact", label=artifact.label, tags=set(artifact.tags)))
    tgt = world.add(Entity(
        id="target",
        type="target",
        label=target.label,
        phrase=target.phrase,
        tags=set(target.tags),
        compressible=target.compressible,
        essential=target.essential,
    ))
    world.add(Entity(
        id="support",
        type="tool",
        label=support.label,
        phrase=support.phrase,
        safe_tool=True,
        tags=set(support.tags),
    ))

    a.memes["bravery"] = BRAVERY_INIT
    b.memes["caution"] = initial_caution(trait)

    introduce(world, a, b, guide, theme, target)
    need_shortcut(world, a, b, target)

    world.para()
    tempt(world, a, artifact, guide)
    warn(world, b, a, artifact, target)

    averted = would_avert(relation, a.age, b.age, trait)
    if averted:
        back_down(world, a, b, guide, support, artifact)
        world.para()
        safe_end(world, guide, support, theme)
        severity = 0
        contained = True
    else:
        defy(world, a, b, artifact)

        world.para()
        compress_scene(world, a, tgt, target)
        alarm(world, b, guide, target)
        bad_realization(world, a, b, target)

        world.para()
        reconcile(world, a, b)
        severity = compression_severity(target, delay)
        contained = is_restored(response, target, delay)

        if contained:
            restore(world, guide, response, tgt, target)
            transform_hero(world, a)
            world.para()
            triumph(world, a, b, guide, theme, target)
        else:
            fail_restore(world, guide, response, target)
            transform_hero(world, a)
            world.para()
            retreat(world, a, b, guide, theme)

    outcome = "averted" if averted else ("restored" if contained else "lost")
    world.facts.update(
        theme=theme,
        artifact=artifact,
        target_cfg=target,
        response=response,
        support=support,
        instigator=a,
        partner=b,
        guide=guide,
        target=tgt,
        relation=relation,
        delay=delay,
        severity=severity,
        outcome=outcome,
        transformed=tgt.meters["compressed"] >= THRESHOLD or tgt.meters["restored"] >= THRESHOLD,
        restored=tgt.meters["restored"] >= THRESHOLD,
        promised=a.memes["lesson"] >= THRESHOLD,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    if not sensible_responses():
        return combos
    for theme_id in THEMES:
        for artifact_id, artifact in ARTIFACTS.items():
            for target_id, target in TARGETS.items():
                if hazard_at_risk(artifact, target):
                    combos.append((theme_id, artifact_id, target_id))
    return combos


@dataclass
class StoryParams:
    theme: str
    artifact: str
    target: str
    response: str
    support: str
    instigator: str
    instigator_gender: str
    partner: str
    partner_gender: str
    guide_name: str
    guide_type: str
    trait: str
    delay: int = 0
    instigator_age: int = 6
    partner_age: int = 4
    relation: str = "siblings"
    seed: Optional[int] = None


KNOWLEDGE = {
    "compression": [
        (
            "What does compression mean?",
            "Compression means pressing something so it takes up less space. In stories with magic, a compression spell can squeeze a big thing into a much smaller shape."
        )
    ],
    "bridge": [
        (
            "What is a rope bridge?",
            "A rope bridge is a bridge made with ropes and boards. It helps people cross a gap when there is no solid path."
        )
    ],
    "boat": [
        (
            "What is a canoe?",
            "A canoe is a small, narrow boat. People paddle it across water."
        )
    ],
    "glider": [
        (
            "What is a glider?",
            "A glider is something with wings that rides through the air. It can sail on wind instead of using an engine."
        )
    ],
    "release_song": [
        (
            "Why would a magic release song help?",
            "A release song is a gentle way to undo a spell. In make-believe adventures, the right words or music can change magic back."
        )
    ],
    "spring_water": [
        (
            "Why is spring water special in adventure stories?",
            "Spring water is often shown as fresh, pure, and powerful. In a magical story, it can wake things up or break a spell."
        )
    ],
    "apology": [
        (
            "What does it mean to reconcile with someone?",
            "To reconcile means to make peace after hurt feelings or a fight. It usually starts with telling the truth, saying sorry, and choosing kindness again."
        )
    ],
    "adventure": [
        (
            "What makes something an adventure?",
            "An adventure has a journey, a problem, and brave choices along the way. The characters are changed by what happens."
        )
    ],
}
KNOWLEDGE_ORDER = [
    "compression",
    "bridge",
    "boat",
    "glider",
    "release_song",
    "spring_water",
    "apology",
    "adventure",
]


def pair_noun(a: Entity, b: Entity, relation: str) -> str:
    if relation == "siblings":
        if a.type == "boy" and b.type == "boy":
            return "two brothers"
        if a.type == "girl" and b.type == "girl":
            return "two sisters"
        return "a brother and a sister"
    return "two young explorers"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    artifact = f["artifact"]
    target = f["target_cfg"]
    theme = f["theme"]
    outcome = f["outcome"]
    base = (
        f'Write an adventure story for a 3-to-5-year-old that includes the word "compression", '
        f'where children on a quest use magic badly and learn from it.'
    )
    if outcome == "lost":
        return [
            base,
            f"Tell a child-friendly adventure where {a.id} wrongly uses {artifact.label} on {target.the}, "
            f"the quest ends sadly, and the children reconcile on the way home.",
            f"Write a story with a bad ending, reconciliation, and transformation, set on the way to {theme.goal}.",
        ]
    if outcome == "averted":
        return [
            base,
            f"Tell a near-miss adventure where {b.id} stops {a.id} from using {artifact.label}, and the team reaches {theme.goal} the safe way.",
            f"Write a gentle quest story about children choosing patience instead of a dangerous shortcut.",
        ]
    return [
        base,
        f"Tell an adventure where {a.id} uses {artifact.label} on {target.the}, the object transforms, the children reconcile, and a guide restores it.",
        f"Write a story with reconciliation and transformation that ends with the quest continuing safely toward {theme.goal}.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["instigator"]
    b = f["partner"]
    guide = f["guide"]
    target = f["target_cfg"]
    artifact = f["artifact"]
    theme = f["theme"]
    response = f["response"]
    support = f["support"]
    relation = f["relation"]
    pair = pair_noun(a, b, relation)

    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {pair}, {a.id} and {b.id}, and {guide.id}, who led them on an adventure. They were trying to reach {theme.goal}."
        ),
        (
            f"Why was {target.the} important?",
            f"It was important because the explorers needed it to {target.use}. Without it, the way to the treasure could not be finished."
        ),
        (
            f"What mistake did {a.id} make?",
            f"{a.id} used {artifact.label} as a shortcut even after being warned not to. That compression magic transformed {target.the} into a tiny shape that could not help the group anymore."
        ),
    ]
    if f["outcome"] == "averted":
        qa.append(
            (
                f"How did the problem get solved before anything went wrong?",
                f"{b.id} warned {a.id} in time, and {a.id} listened. Then the guide gave them {support.phrase}, so they could {support.use} instead of shrinking anything."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended safely, with the team reaching {theme.goal} the slow, careful way. The ending shows that patience can be part of an adventure too."
            )
        )
        return qa

    qa.append(
        (
            f"How did {a.id} and {b.id} reconcile?",
            f"They talked honestly after the mistake. {b.id} said the magic had been scary, and {a.id} apologized for not listening, so they could make a plan together."
        )
    )

    if f["outcome"] == "restored":
        qa.append(
            (
                f"How did {guide.id} fix the transformation?",
                f"{guide.id} {response.qa_text}. That changed {target.the} back into something the group could really use again."
            )
        )
        qa.append(
            (
                f"How was {a.id} transformed by the end?",
                f"{a.id} was still adventurous, but more patient and humble. The story shows that the biggest transformation was not only in {target.the}, but also in how {a.id} chose to act."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"After the object was restored, the team went on to {theme.goal} together. The final image feels hopeful because the path and the friendship were both repaired."
            )
        )
    else:
        qa.append(
            (
                f"Could the group restore {target.the} in time?",
                f"No. {guide.id} tried, but the magic stayed stuck, so the way ahead remained closed. That is why the adventure ended sadly."
            )
        )
        qa.append(
            (
                "Did the children stay angry with each other?",
                f"No. Even with the bad ending, they reconciled and walked back together. The treasure was lost, but the friendship was not."
            )
        )
        qa.append(
            (
                "How did the story end?",
                f"It ended with the group turning back before dark instead of reaching the treasure. The ending is sad, but it still shows care because the children stay together and learn from the mistake."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = {"compression", "apology", "adventure"}
    target = f["target_cfg"]
    response = f["response"]
    if target.id == "rope_bridge":
        tags.add("bridge")
    if target.id == "canoe":
        tags.add("boat")
    if target.id == "glider":
        tags.add("glider")
    if response.id == "release_song":
        tags.add("release_song")
    if response.id == "spring_water":
        tags.add("spring_water")
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
        bits = []
        if ent.role:
            bits.append(f"role={ent.role}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if ent.age:
            bits.append(f"age={ent.age}")
        if ent.attrs:
            shown = {k: v for k, v in ent.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        flags = []
        if ent.compressible:
            flags.append("compressible")
        if ent.essential:
            flags.append("essential")
        if ent.safe_tool:
            flags.append("safe_tool")
        if flags:
            bits.append(f"flags={flags}")
        lines.append(f"  {ent.id:8} ({ent.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="jungle",
        artifact="compression_charm",
        target="rope_bridge",
        response="release_song",
        support="haul_rope",
        instigator="Tom",
        instigator_gender="boy",
        partner="Lily",
        partner_gender="girl",
        guide_name="Guide Nia",
        guide_type="mother",
        trait="careful",
        delay=0,
        instigator_age=6,
        partner_age=4,
        relation="siblings",
    ),
    StoryParams(
        theme="desert",
        artifact="squeeze_flute",
        target="canoe",
        response="spring_water",
        support="pack_frame",
        instigator="Mia",
        instigator_gender="girl",
        partner="Ben",
        partner_gender="boy",
        guide_name="Captain Ivo",
        guide_type="father",
        trait="patient",
        delay=1,
        instigator_age=5,
        partner_age=7,
        relation="siblings",
    ),
    StoryParams(
        theme="ice",
        artifact="compression_charm",
        target="glider",
        response="spring_water",
        support="sled",
        instigator="Sam",
        instigator_gender="boy",
        partner="Zoe",
        partner_gender="girl",
        guide_name="Aunt Mara",
        guide_type="mother",
        trait="curious",
        delay=2,
        instigator_age=7,
        partner_age=5,
        relation="friends",
    ),
]


def explain_rejection(artifact: Artifact, target: TargetCfg) -> str:
    if not target.compressible:
        return (
            f"(No story: {artifact.label} can squeeze soft or folding gear, but {target.the} is not something this magic can reasonably compress. "
            f"Pick a target like a rope bridge, canoe, or glider.)"
        )
    if not artifact.makes_compression:
        return f"(No story: {artifact.label} does not create compression magic.)"
    return "(No story: this combination has no meaningful adventure hazard.)"


def explain_response(rid: str) -> str:
    resp = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return (
        f"(Refusing response '{rid}': it scores too low on common sense "
        f"(sense={resp.sense} < {SENSE_MIN}). Try: {better}.)"
    )


def outcome_of(params: StoryParams) -> str:
    if would_avert(params.relation, params.instigator_age, params.partner_age, params.trait):
        return "averted"
    contained = is_restored(RESPONSES[params.response], TARGETS[params.target], params.delay)
    return "restored" if contained else "lost"


ASP_RULES = r"""
hazard(A, T) :- makes_compression(A), compressible(T), essential(T).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(Th, A, T) :- theme(Th), artifact(A), target(T), hazard(A, T).

cautious_now(T) :- trait(T), is_cautious(T).
init_caution(5) :- trait(T), cautious_now(T).
init_caution(3) :- trait(T), not cautious_now(T).
partner_older :- relation(siblings), instigator_age(IA), partner_age(PA), PA > IA.
bonus(4) :- partner_older.
bonus(0) :- not partner_older.
authority(C + 1 + B) :- init_caution(C), bonus(B).
averted :- partner_older, authority(A), bravery_init(BR), A > BR.

severity(F + D) :- chosen_target(T), fragility(T, F), delay(D).
resp_power(P) :- chosen_response(R), power(R, P).
restored :- resp_power(P), severity(V), P >= V.

outcome(averted) :- averted.
outcome(restored) :- not averted, restored.
outcome(lost) :- not averted, not restored.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for theme_id in THEMES:
        lines.append(asp.fact("theme", theme_id))
    for artifact_id, artifact in ARTIFACTS.items():
        lines.append(asp.fact("artifact", artifact_id))
        if artifact.makes_compression:
            lines.append(asp.fact("makes_compression", artifact_id))
    for target_id, target in TARGETS.items():
        lines.append(asp.fact("target", target_id))
        if target.compressible:
            lines.append(asp.fact("compressible", target_id))
        if target.essential:
            lines.append(asp.fact("essential", target_id))
        lines.append(asp.fact("fragility", target_id, target.fragility))
    for response_id, response in RESPONSES.items():
        lines.append(asp.fact("response", response_id))
        lines.append(asp.fact("sense", response_id, response.sense))
        lines.append(asp.fact("power", response_id, response.power))
    for trait in sorted(CAUTIOUS_TRAITS):
        lines.append(asp.fact("is_cautious", trait))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    lines.append(asp.fact("bravery_init", int(BRAVERY_INIT)))
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

    extra = "\n".join(
        [
            asp.fact("chosen_target", params.target),
            asp.fact("chosen_response", params.response),
            asp.fact("delay", params.delay),
            asp.fact("relation", params.relation),
            asp.fact("instigator_age", params.instigator_age),
            asp.fact("partner_age", params.partner_age),
            asp.fact("trait", params.trait),
        ]
    )
    model = asp.one_model(asp_program(extra, "#show outcome/1."))
    out = asp.atoms(model, "outcome")
    return out[0][0] if out else "?"


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

    bad = sum(1 for params in cases if asp_outcome(params) != outcome_of(params))
    if bad == 0:
        print(f"OK: outcome model matches outcome_of() on {len(cases)} scenarios.")
    else:
        rc = 1
        print(f"MISMATCH: {bad}/{len(cases)} outcomes differ.")

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("generated empty story")
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True, header="### smoke")
        print("OK: smoke test generate()/emit() passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: compression magic, reconciliation, and adventure."
    )
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--artifact", choices=ARTIFACTS)
    ap.add_argument("--target", choices=TARGETS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--support", choices=SUPPORT_TOOLS)
    ap.add_argument("--guide-type", choices=["mother", "father"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2], help="how long the object stays compressed before a fix is tried")
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP reasoner matches the Python logic")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = [n for n in (GIRL_NAMES if gender == "girl" else BOY_NAMES) if n != avoid]
    return rng.choice(pool), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.target and not TARGETS[args.target].compressible:
        artifact = ARTIFACTS[args.artifact] if args.artifact else next(iter(ARTIFACTS.values()))
        raise StoryError(explain_rejection(artifact, TARGETS[args.target]))
    if args.artifact and args.target:
        artifact = ARTIFACTS[args.artifact]
        target = TARGETS[args.target]
        if not hazard_at_risk(artifact, target):
            raise StoryError(explain_rejection(artifact, target))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))

    combos = [
        combo
        for combo in valid_combos()
        if (args.theme is None or combo[0] == args.theme)
        and (args.artifact is None or combo[1] == args.artifact)
        and (args.target is None or combo[2] == args.target)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    theme, artifact, target = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    support = args.support or rng.choice(sorted(SUPPORT_TOOLS))
    instigator, instigator_gender = _pick_kid(rng)
    partner, partner_gender = _pick_kid(rng, avoid=instigator)
    guide_name = rng.choice(GUIDE_NAMES)
    guide_type = args.guide_type or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    delay = args.delay if args.delay is not None else rng.randint(0, 2)
    relation = rng.choice(["siblings", "friends"])
    instigator_age, partner_age = rng.sample([3, 4, 5, 6, 7], 2)

    return StoryParams(
        theme=theme,
        artifact=artifact,
        target=target,
        response=response,
        support=support,
        instigator=instigator,
        instigator_gender=instigator_gender,
        partner=partner,
        partner_gender=partner_gender,
        guide_name=guide_name,
        guide_type=guide_type,
        trait=trait,
        delay=delay,
        instigator_age=instigator_age,
        partner_age=partner_age,
        relation=relation,
    )


def generate(params: StoryParams) -> StorySample:
    try:
        theme = THEMES[params.theme]
        artifact = ARTIFACTS[params.artifact]
        target = TARGETS[params.target]
        response = RESPONSES[params.response]
        support = SUPPORT_TOOLS[params.support]
    except KeyError as exc:
        raise StoryError(f"(Invalid parameter key: {exc})") from None

    if not hazard_at_risk(artifact, target):
        raise StoryError(explain_rejection(artifact, target))
    if response.sense < SENSE_MIN:
        raise StoryError(explain_response(response.id))

    world = tell(
        theme=theme,
        artifact=artifact,
        target=target,
        response=response,
        support=support,
        instigator=params.instigator,
        instigator_gender=params.instigator_gender,
        partner=params.partner,
        partner_gender=params.partner_gender,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
        trait=params.trait,
        delay=params.delay,
        instigator_age=params.instigator_age,
        partner_age=params.partner_age,
        relation=params.relation,
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        print(f"{len(combos)} compatible (theme, artifact, target) combos:\n")
        for theme, artifact, target in combos:
            print(f"  {theme:8} {artifact:18} {target}")
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
            params = sample.params
            header = (
                f"### {params.instigator} & {params.partner}: {params.artifact} on "
                f"{params.target} ({params.theme}, {params.response}, {outcome_of(params)})"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
