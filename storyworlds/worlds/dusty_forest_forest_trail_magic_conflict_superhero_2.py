#!/usr/bin/env python3
"""
A standalone storyworld for this seed:

    Words: dusty forest
    Setting: forest trail
    Features: Magic, Conflict
    Style: Superhero Story

Internal source tale:
In a dusty forest, a child superhero tries to carry a helpful delivery down a
forest trail. A magical threat blocks the path, and the hero's first fast move
only makes the dust worse. By listening to a small companion and using the
right kind of magic, the hero solves the conflict and leaves the trail visibly
changed at the end.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

ACTIVE = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    location: str = ""
    owner: str = ""

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "heroine"}
        male = {"boy", "man", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass(frozen=True)
class Trail:
    id: str
    phrase: str
    opening_image: str
    landmark: str
    dust_line: str
    ending_image: str
    affords: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class HeroProfile:
    id: str
    name: str
    alias: str
    type: str
    cape: str
    signature: str
    opening_vow: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Companion:
    id: str
    name: str
    type: str
    skill: str
    opening_line: str
    advice: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Threat:
    id: str
    title: str
    entrance: str
    problem: str
    need: str
    need_phrase: str
    clue: str
    backfire: str
    soothed: str
    ending_pose: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Relic:
    id: str
    label: str
    solves: set[str]
    virtues: set[str]
    power: str
    use_template: str
    tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Mission:
    id: str
    cargo: str
    beneficiary: str
    lesson: str
    urgency: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, trail_cfg: Trail) -> None:
        self.trail_cfg = trail_cfg
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.history: list[dict[str, str]] = []
        self.fired: set[tuple[str, str]] = set()
        self.facts: dict[str, object] = {}

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

    def note(self, kind: str, **data: str) -> None:
        row = {"kind": kind}
        row.update({k: str(v) for k, v in data.items()})
        self.history.append(row)

    def render(self) -> str:
        return "\n\n".join(" ".join(part for part in para if part) for para in self.paragraphs if para)


@dataclass
class Rule:
    name: str
    apply: Callable[[World], bool]


TRAILS = {
    "cedar_switchback": Trail(
        "cedar_switchback",
        "the cedar switchback forest trail",
        "Brown dust puffed around the cedar roots each time a shoe touched the ground.",
        "the split cedar arch",
        "The dusty forest smelled like warm bark and sun-baked needles.",
        "Dust settled into quiet rings around the cedar roots, and the whole trail looked brushed clean by gold light.",
        {"dust_drake", "ash_owl"},
        {"dusty_forest", "forest_trail", "cedar"},
    ),
    "fern_bend": Trail(
        "fern_bend",
        "the fern-bend forest trail",
        "Dry fern flakes floated over the path like sleepy green confetti in the dusty forest.",
        "the bent fern gate",
        "Every step sent a soft brown sigh across the narrow trail.",
        "The ferns lifted their green edges again, and the trail showed a clear line all the way to the next bend.",
        {"dust_drake", "thorn_phantom"},
        {"dusty_forest", "forest_trail", "fern"},
    ),
    "moonstone_path": Trail(
        "moonstone_path",
        "the moonstone forest trail",
        "Silver pebbles hid under a fine coat of dust, so the path looked like a tucked-in star blanket.",
        "the moonstone marker",
        "The dusty forest held its breath under the branches, as if even the birds were waiting.",
        "Moonstones winked through the last soft dust, and the trail shone like a line of tiny stars under glass.",
        {"thorn_phantom", "ash_owl"},
        {"dusty_forest", "forest_trail", "moonstone"},
    ),
}

HEROES = {
    "iris": HeroProfile(
        "iris",
        "Iris",
        "Star Pine",
        "girl",
        "a pine-green cape stitched with tiny silver stars",
        "She could leap stump to stump so quickly that her cape drew a bright green arc behind her.",
        "She promised to use her gifts to keep small travelers safe.",
        {"superhero", "magic", "brave"},
    ),
    "leo": HeroProfile(
        "leo",
        "Leo",
        "Moss Falcon",
        "boy",
        "a moss-dark cape with copper leaves at the collar",
        "He could spin a fast ring of wind around himself when danger burst out of nowhere.",
        "He believed a hero should leave every path kinder than he found it.",
        {"superhero", "magic", "brave"},
    ),
    "nora": HeroProfile(
        "nora",
        "Nora",
        "Comet Fern",
        "girl",
        "a fern-blue cape with a comet sewn across the back",
        "She could spring over roots in one bright blur and land without dropping a single pebble.",
        "She liked to say that courage was brightest when it helped somebody else.",
        {"superhero", "magic", "brave"},
    ),
}

COMPANIONS = {
    "brook": Companion(
        "brook",
        "Brook",
        "frog",
        "cooling",
        "Brook the frog bounced beside the hero with calm eyes and a satchel knot tied neatly around one shoulder.",
        '"Hot magic needs relief before it can listen," Brook whispered.',
        {"forest_friend", "cooling", "care"},
    ),
    "glint": Companion(
        "glint",
        "Glint",
        "firefly",
        "light",
        "Glint the firefly floated at shoulder height, blinking like a small lantern with opinions.",
        '"Shadows grab when they cannot see. Show them the path," Glint buzzed.',
        {"forest_friend", "light", "focus"},
    ),
    "moss": Companion(
        "moss",
        "Moss",
        "fox",
        "calm",
        "Moss the fox padded close enough to brush the hero's boot with a soft tail-tip.",
        '"A scared heartbeat gets quiet before it gets kind," Moss said in a low voice.',
        {"forest_friend", "calm", "gentleness"},
    ),
}

THREATS = {
    "dust_drake": Threat(
        "dust_drake",
        "Dust Drake",
        "A Dust Drake slithered out from the brush and coiled across the trail like a living storm scarf.",
        "Every hot sneeze spun the dust into stinging rings, and no one could see where to step.",
        "cooling",
        "cool relief",
        "the drake kept scraping its hot throat against a stump and wincing after each dusty sneeze",
        "The blast only made the hot dust whirl faster, and the brown ring swallowed the stepping stones one by one.",
        "The drake drank the cool magic, sighed, and uncrossed the trail so the dust could drift back down.",
        "The Dust Drake used its tail to brush the last dust off the stepping stones.",
        {"conflict", "magic", "dust", "cooling"},
    ),
    "thorn_phantom": Threat(
        "thorn_phantom",
        "Thorn Phantom",
        "A Thorn Phantom rose from the blackberry shadows and knitted a wall of vines over the trail.",
        "The darker the path became, the faster the thorns tugged at capes, baskets, and paws.",
        "light",
        "clear guiding light",
        "the vines loosened every time one brave sunbeam touched them",
        "The quick charge only tangled the thorns tighter, and even the brave gold patches of sun vanished.",
        "Warm light threaded through the vines until they opened like a green curtain instead of a trap.",
        "The Thorn Phantom turned into a shining vine arch with fireflies tucked into its leaves.",
        {"conflict", "magic", "dust", "light"},
    ),
    "ash_owl": Threat(
        "ash_owl",
        "Ash Owl",
        "An Ash Owl burst from the branches and beat clouds of gray dust across the trail.",
        "Its frightened wingbeats hid every marker and made the path sound like a storm in a bucket.",
        "calm",
        "a calm, gentle rhythm",
        "one bright feather trembled each time the owl heard a loud voice",
        "The rushing move startled the owl worse, and dust swallowed the trail markers all over again.",
        "The owl's wings slowed, and the gray dust floated down instead of flying up.",
        "The Ash Owl perched above the trail and watched it quietly like a soft-feathered guard.",
        {"conflict", "magic", "dust", "calm"},
    ),
}

RELICS = {
    "rain_leaf_gauntlet": Relic(
        "rain_leaf_gauntlet",
        "the Rain-Leaf Gauntlet",
        {"cooling"},
        {"care", "patience"},
        "pearled blue rain ribbons",
        "{hero_alias} opened the Rain-Leaf Gauntlet, and pearled blue rain ribbons cooled the air around the Dust Drake's burning throat.",
        {"magic", "relic", "care", "cooling"},
    ),
    "sunseed_lantern": Relic(
        "sunseed_lantern",
        "the Sunseed Lantern",
        {"light"},
        {"focus", "hope"},
        "a gold path-light",
        "{hero_alias} lifted the Sunseed Lantern, and a gold path-light poured through the thorns until every branch could see where to curl.",
        {"magic", "relic", "focus", "light"},
    ),
    "hush_bell_cloak": Relic(
        "hush_bell_cloak",
        "the Hush-Bell Cloak",
        {"calm"},
        {"gentleness", "listening"},
        "soft silver calm",
        "{hero_alias} spread the Hush-Bell Cloak, and soft silver calm rolled outward like a song without words through the branches.",
        {"magic", "relic", "gentleness", "calm"},
    ),
}

MISSIONS = {
    "clinic_water": Mission(
        "clinic_water",
        "a flask of moonwater",
        "the rabbit clinic at the far end of the trail",
        "care",
        "The rabbits were waiting for the moonwater to soothe scratchy throats before sunset.",
        {"care", "helping"},
    ),
    "school_badge": Mission(
        "school_badge",
        "the sun badge",
        "the little fawn school beyond the bend",
        "focus",
        "The fawn class needed the badge before the path-light lesson could begin.",
        {"focus", "helping"},
    ),
    "nest_ribbon": Mission(
        "nest_ribbon",
        "a silver bell ribbon",
        "the sleepy nest nursery past the tall pines",
        "gentleness",
        "The nursery needed the ribbon before the youngest birds could settle down to rest.",
        {"gentleness", "helping"},
    ),
}


@dataclass
class StoryParams:
    trail: str
    hero: str
    threat: str
    relic: str
    companion: str
    mission: str
    seed: Optional[int] = None


KNOWLEDGE = {
    "dusty_forest": [
        ("What is a dusty forest?", "A dusty forest is a forest where the ground is dry enough for fine dust to lift when something moves."),
    ],
    "forest_trail": [
        ("What is a forest trail?", "A forest trail is a narrow path that helps people or animals move safely through the woods."),
    ],
    "superhero": [
        ("What makes someone a superhero in a story?", "A superhero uses special gifts or brave choices to protect others and solve problems."),
    ],
    "magic": [
        ("What does magic do in a story?", "Magic lets unusual things happen, but it still works best when a character uses it with care."),
    ],
    "conflict": [
        ("What is a conflict in a story?", "A conflict is the trouble that blocks a character and forces them to make choices."),
    ],
    "care": [
        ("Why is care helpful during a problem?", "Care helps a person notice what is hurting and fix it gently instead of making it worse."),
    ],
    "focus": [
        ("Why does focus matter?", "Focus helps a hero look at the real problem instead of getting distracted by the loudest part."),
    ],
    "gentleness": [
        ("Why can gentleness be strong?", "Gentleness can calm fear and make room for a better choice, even in a scary moment."),
    ],
    "cooling": [
        ("Why might cooling magic help?", "Cooling magic can calm something that is overheated or hurting from too much heat."),
    ],
    "light": [
        ("Why is light useful on a trail?", "Light helps everyone see where to go and can make hidden dangers easier to understand."),
    ],
    "calm": [
        ("Why does calm help during fear?", "Calm slows panic down so a creature can notice safety again."),
    ],
}
KNOWLEDGE_ORDER = [
    "dusty_forest",
    "forest_trail",
    "superhero",
    "magic",
    "conflict",
    "care",
    "focus",
    "gentleness",
    "cooling",
    "light",
    "calm",
]


def threat_accepts_relic(threat: Threat, relic: Relic) -> bool:
    return threat.need in relic.solves


def companion_reads_threat(threat: Threat, companion: Companion) -> bool:
    return companion.skill == threat.need


def mission_matches_relic(mission: Mission, relic: Relic) -> bool:
    return mission.lesson in relic.virtues


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str]] = []
    for trail_id, trail in TRAILS.items():
        for threat_id in sorted(trail.affords):
            threat = THREATS[threat_id]
            for relic_id, relic in RELICS.items():
                if not threat_accepts_relic(threat, relic):
                    continue
                for companion_id, companion in COMPANIONS.items():
                    if not companion_reads_threat(threat, companion):
                        continue
                    for mission_id, mission in MISSIONS.items():
                        if mission_matches_relic(mission, relic):
                            combos.append((trail_id, threat_id, relic_id, companion_id, mission_id))
    return sorted(combos)


def _r_block_trail(world: World) -> bool:
    trail = world.get("trail")
    threat = world.get("threat")
    if threat.meters["active"] < ACTIVE or trail.meters["blocked"] >= ACTIVE:
        return False
    trail.meters["blocked"] = 1
    trail.meters["safe"] = 0
    trail.meters["dust"] += 1
    world.note("trail_blocked", trail=trail.label, threat=threat.label)
    return True


def _r_rush_backfires(world: World) -> bool:
    hero = world.get("hero")
    threat = world.get("threat")
    trail = world.get("trail")
    if hero.meters["rushed"] < ACTIVE or threat.meters["active"] < ACTIVE:
        return False
    sig = ("backfire", threat.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    threat.memes["fear"] += 1
    threat.memes["anger"] += 1
    trail.meters["dust"] += 1
    world.note("rush_backfire", hero=hero.label, threat=threat.label)
    return True


def _r_matching_magic_resolves(world: World) -> bool:
    hero = world.get("hero")
    trail = world.get("trail")
    threat = world.get("threat")
    relic = world.get("relic")
    cargo = world.get("cargo")
    if relic.meters["used"] < ACTIVE or threat.meters["active"] < ACTIVE:
        return False
    threat_cfg: Threat = world.facts["threat_cfg"]  # type: ignore[assignment]
    relic_cfg: Relic = world.facts["relic_cfg"]  # type: ignore[assignment]
    companion_cfg: Companion = world.facts["companion_cfg"]  # type: ignore[assignment]
    mission_cfg: Mission = world.facts["mission_cfg"]  # type: ignore[assignment]
    if not (
        threat_accepts_relic(threat_cfg, relic_cfg)
        and companion_reads_threat(threat_cfg, companion_cfg)
        and mission_matches_relic(mission_cfg, relic_cfg)
    ):
        return False
    threat.meters["active"] = 0
    threat.meters["calm"] = 1
    trail.meters["blocked"] = 0
    trail.meters["safe"] = 1
    trail.meters["dust"] = max(0.0, trail.meters["dust"] - 1)
    cargo.meters["delivered"] = 1
    hero.memes["courage"] += 1
    hero.memes["trust"] += 1
    world.note("conflict_resolved", hero=hero.label, relic=relic.label, threat=threat.label)
    return True


CAUSAL_RULES = [
    Rule("block_trail", _r_block_trail),
    Rule("rush_backfires", _r_rush_backfires),
    Rule("matching_magic_resolves", _r_matching_magic_resolves),
]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def introduce(world: World, hero_cfg: HeroProfile, companion_cfg: Companion,
              mission_cfg: Mission, trail_cfg: Trail) -> None:
    hero = world.add(
        Entity(
            "hero",
            kind="character",
            type=hero_cfg.type,
            label=hero_cfg.name,
            role="hero",
            traits=[hero_cfg.alias],
            location=trail_cfg.id,
        )
    )
    companion = world.add(
        Entity(
            "companion",
            kind="character",
            type="animal",
            label=companion_cfg.name,
            role="companion",
            traits=[companion_cfg.type],
            location=trail_cfg.id,
        )
    )
    trail = world.add(
        Entity(
            "trail",
            kind="place",
            type="trail",
            label=trail_cfg.phrase,
            role="setting",
            location=trail_cfg.id,
        )
    )
    cargo = world.add(
        Entity(
            "cargo",
            kind="thing",
            type="delivery",
            label=mission_cfg.cargo,
            role="cargo",
            owner=hero_cfg.name,
            location=trail_cfg.id,
        )
    )
    hero.memes["duty"] = 1
    hero.memes["courage"] = 1
    companion.memes["trust"] = 1
    trail.meters["safe"] = 1
    cargo.meters["packed"] = 1
    world.say(
        f"In the dusty forest, {hero_cfg.name} hurried along {trail_cfg.phrase} carrying {mission_cfg.cargo} for {mission_cfg.beneficiary}."
    )
    world.say(
        f"{trail_cfg.opening_image} {trail_cfg.dust_line} When trouble called, {hero_cfg.name} became {hero_cfg.alias}, wearing {hero_cfg.cape}."
    )
    world.say(f"{hero_cfg.signature} {hero_cfg.opening_vow}")
    world.say(f"{companion_cfg.opening_line} {mission_cfg.urgency}")
    world.note(
        "intro",
        hero=hero_cfg.name,
        alias=hero_cfg.alias,
        trail=trail_cfg.phrase,
        cargo=mission_cfg.cargo,
        beneficiary=mission_cfg.beneficiary,
    )


def reveal_conflict(world: World, threat_cfg: Threat, relic_cfg: Relic, trail_cfg: Trail) -> None:
    threat = world.add(
        Entity(
            "threat",
            kind="character",
            type="creature",
            label=threat_cfg.title,
            role="threat",
            location=trail_cfg.id,
        )
    )
    relic = world.add(
        Entity(
            "relic",
            kind="thing",
            type="magic_relic",
            label=relic_cfg.label,
            role="tool",
            location=trail_cfg.id,
        )
    )
    threat.meters["active"] = 1
    threat.memes["fear"] = 1
    relic.meters["ready"] = 1
    propagate(world)
    world.para()
    world.say(
        f"At {trail_cfg.landmark}, {threat_cfg.entrance} {threat_cfg.problem}"
    )
    world.say(
        f"Inside the hero's satchel, {relic_cfg.label} hummed, but the path was already blocked."
    )
    world.note("conflict", threat=threat_cfg.title, need=threat_cfg.need, relic=relic_cfg.label)


def rush_and_fail(world: World, hero_cfg: HeroProfile, threat_cfg: Threat) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    hero.meters["rushed"] = 1
    hero.memes["fear"] += 1
    companion.memes["worry"] += 1
    propagate(world)
    world.say(
        f"{hero_cfg.alias} tried the fastest answer first, charging ahead before asking what the magic creature needed."
    )
    world.say(
        f"{hero_cfg.signature} {threat_cfg.backfire}"
    )
    world.note("failed_first_move", hero=hero_cfg.alias, reason="rushed")


def discover_turn(world: World, hero_cfg: HeroProfile, companion_cfg: Companion,
                  threat_cfg: Threat, mission_cfg: Mission) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    hero.meters["rushed"] = 0
    hero.memes["focus"] += 1
    companion.memes["trust"] += 1
    world.para()
    world.say(
        f"{companion_cfg.advice} {hero_cfg.name} looked carefully and saw that {threat_cfg.clue}."
    )
    world.say(
        f"{hero_cfg.name} finally understood the turn in the problem. A superhero was not supposed to win a dust fight by being louder. {hero.pronoun('subject').capitalize()} was supposed to notice the hurt and answer it with {threat_cfg.need_phrase}."
    )
    world.say(
        f"That matched the reason for carrying {mission_cfg.cargo}: this trip was about helping, not showing off."
    )
    world.note("insight", need=threat_cfg.need, lesson=mission_cfg.lesson, companion=companion_cfg.name)


def use_magic(world: World, hero_cfg: HeroProfile, threat_cfg: Threat, relic_cfg: Relic) -> None:
    relic = world.get("relic")
    relic.meters["used"] = 1
    world.say(relic_cfg.use_template.format(hero_alias=hero_cfg.alias))
    propagate(world)
    world.say(threat_cfg.soothed)
    world.note("magic_used", relic=relic_cfg.label, power=relic_cfg.power)


def close_story(world: World, hero_cfg: HeroProfile, threat_cfg: Threat,
                mission_cfg: Mission, trail_cfg: Trail) -> None:
    cargo = world.get("cargo")
    trail = world.get("trail")
    world.para()
    if trail.meters["safe"] >= ACTIVE and cargo.meters["delivered"] >= ACTIVE:
        world.say(
            f"{hero_cfg.name} carried {mission_cfg.cargo} the rest of the way to {mission_cfg.beneficiary}, and everyone there cheered when the delivery arrived on time."
        )
        world.say(
            f"{threat_cfg.ending_pose} {trail_cfg.ending_image}"
        )
        world.say(
            f"{hero_cfg.alias} smiled because the forest trail was open again, and the ending looked different from the beginning in every direction."
        )
        world.note("ending", status="safe", delivered=mission_cfg.cargo, image=trail_cfg.ending_image)
    else:
        world.say(
            f"{hero_cfg.name} stepped back from the blocked trail and promised to return with a wiser plan."
        )
        world.note("ending", status="blocked")


def tell(params: StoryParams) -> World:
    trail_cfg = TRAILS[params.trail]
    hero_cfg = HEROES[params.hero]
    threat_cfg = THREATS[params.threat]
    relic_cfg = RELICS[params.relic]
    companion_cfg = COMPANIONS[params.companion]
    mission_cfg = MISSIONS[params.mission]
    world = World(trail_cfg)
    world.facts.update(
        trail_cfg=trail_cfg,
        hero_cfg=hero_cfg,
        threat_cfg=threat_cfg,
        relic_cfg=relic_cfg,
        companion_cfg=companion_cfg,
        mission_cfg=mission_cfg,
    )
    introduce(world, hero_cfg, companion_cfg, mission_cfg, trail_cfg)
    reveal_conflict(world, threat_cfg, relic_cfg, trail_cfg)
    rush_and_fail(world, hero_cfg, threat_cfg)
    discover_turn(world, hero_cfg, companion_cfg, threat_cfg, mission_cfg)
    use_magic(world, hero_cfg, threat_cfg, relic_cfg)
    close_story(world, hero_cfg, threat_cfg, mission_cfg, trail_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    hero_cfg: HeroProfile = world.facts["hero_cfg"]  # type: ignore[assignment]
    trail_cfg: Trail = world.facts["trail_cfg"]  # type: ignore[assignment]
    mission_cfg: Mission = world.facts["mission_cfg"]  # type: ignore[assignment]
    threat_cfg: Threat = world.facts["threat_cfg"]  # type: ignore[assignment]
    return [
        'Write a superhero story for young children set in a dusty forest on a forest trail.',
        f"Tell a magical conflict story where {hero_cfg.name} becomes {hero_cfg.alias} to carry {mission_cfg.cargo} through {trail_cfg.phrase}.",
        f"Use {threat_cfg.title} as the obstacle, but let the ending prove the trail changed for the better.",
    ]


def story_qa_rows(world: World) -> list[tuple[str, str]]:
    hero_cfg: HeroProfile = world.facts["hero_cfg"]  # type: ignore[assignment]
    trail_cfg: Trail = world.facts["trail_cfg"]  # type: ignore[assignment]
    threat_cfg: Threat = world.facts["threat_cfg"]  # type: ignore[assignment]
    relic_cfg: Relic = world.facts["relic_cfg"]  # type: ignore[assignment]
    companion_cfg: Companion = world.facts["companion_cfg"]  # type: ignore[assignment]
    mission_cfg: Mission = world.facts["mission_cfg"]  # type: ignore[assignment]
    return [
        (
            "Who is the superhero in this story?",
            f"The superhero is {hero_cfg.name}, who becomes {hero_cfg.alias} on {trail_cfg.phrase}. {hero_cfg.name} uses that brave identity to protect the dusty forest trail while carrying {mission_cfg.cargo}.",
        ),
        (
            "What caused the main conflict on the trail?",
            f"The main conflict began when {threat_cfg.title} blocked the trail. {threat_cfg.problem}",
        ),
        (
            "Why did the first quick move fail?",
            f"The first quick move failed because the hero rushed before understanding the real problem. That made the dust worse and frightened {threat_cfg.title} even more.",
        ),
        (
            "How did the hero solve the conflict?",
            f"{hero_cfg.alias} solved the conflict with {relic_cfg.label}. {companion_cfg.name}'s advice helped the hero notice that the threat needed {threat_cfg.need_phrase}, so the magic matched the problem instead of fighting it blindly.",
        ),
        (
            "What proves the ending changed the world?",
            f"The ending is proven by the open trail and the finished delivery to {mission_cfg.beneficiary}. {trail_cfg.ending_image}",
        ),
    ]


def world_knowledge_rows(world: World) -> list[tuple[str, str]]:
    trail_cfg: Trail = world.facts["trail_cfg"]  # type: ignore[assignment]
    hero_cfg: HeroProfile = world.facts["hero_cfg"]  # type: ignore[assignment]
    threat_cfg: Threat = world.facts["threat_cfg"]  # type: ignore[assignment]
    relic_cfg: Relic = world.facts["relic_cfg"]  # type: ignore[assignment]
    mission_cfg: Mission = world.facts["mission_cfg"]  # type: ignore[assignment]
    tags = (
        set(trail_cfg.tags)
        | set(hero_cfg.tags)
        | set(threat_cfg.tags)
        | set(relic_cfg.tags)
        | set(mission_cfg.tags)
    )
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story world ==")
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
        if ent.location:
            bits.append(f"loc={ent.location}")
        if ent.owner:
            bits.append(f"owner={ent.owner}")
        if ent.traits:
            bits.append(f"traits={ent.traits}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {ent.id:10} ({ent.type:12}) {' '.join(bits)}")
    lines.append("  history:")
    for event in world.history:
        lines.append(f"    - {event}")
    return "\n".join(lines)


def explain_rejection(
    trail_cfg: Optional[Trail],
    threat_cfg: Optional[Threat],
    relic_cfg: Optional[Relic],
    companion_cfg: Optional[Companion],
    mission_cfg: Optional[Mission],
) -> str:
    if trail_cfg and threat_cfg and threat_cfg.id not in trail_cfg.affords:
        return f"(No story: {threat_cfg.title} does not belong on {trail_cfg.phrase}.)"
    if threat_cfg and relic_cfg and not threat_accepts_relic(threat_cfg, relic_cfg):
        return (
            f"(No story: {relic_cfg.label} cannot solve {threat_cfg.title}; "
            f"the threat needs {threat_cfg.need_phrase}.)"
        )
    if threat_cfg and companion_cfg and not companion_reads_threat(threat_cfg, companion_cfg):
        return (
            f"(No story: {companion_cfg.name} reads {companion_cfg.skill} magic, "
            f"but {threat_cfg.title} needs {threat_cfg.need_phrase}.)"
        )
    if mission_cfg and relic_cfg and not mission_matches_relic(mission_cfg, relic_cfg):
        return (
            f"(No story: {mission_cfg.cargo} asks for {mission_cfg.lesson}, "
            f"but {relic_cfg.label} does not carry that virtue.)"
        )
    return "(No story: the selected dusty-forest pieces do not form a reasonable superhero story.)"


ASP_RULES = r"""
valid(Trail, Threat, Relic, Companion, Mission) :-
    trail(Trail),
    threat(Threat),
    relic(Relic),
    companion(Companion),
    mission(Mission),
    affords(Trail, Threat),
    threat_need(Threat, Need),
    solves(Relic, Need),
    reads(Companion, Need),
    mission_lesson(Mission, Virtue),
    virtue(Relic, Virtue).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for trail_id, trail in TRAILS.items():
        lines.append(asp.fact("trail", trail_id))
        for threat_id in sorted(trail.affords):
            lines.append(asp.fact("affords", trail_id, threat_id))
    for threat_id, threat in THREATS.items():
        lines.append(asp.fact("threat", threat_id))
        lines.append(asp.fact("threat_need", threat_id, threat.need))
    for relic_id, relic in RELICS.items():
        lines.append(asp.fact("relic", relic_id))
        for need in sorted(relic.solves):
            lines.append(asp.fact("solves", relic_id, need))
        for virtue in sorted(relic.virtues):
            lines.append(asp.fact("virtue", relic_id, virtue))
    for companion_id, companion in COMPANIONS.items():
        lines.append(asp.fact("companion", companion_id))
        lines.append(asp.fact("reads", companion_id, companion.skill))
    for mission_id, mission in MISSIONS.items():
        lines.append(asp.fact("mission", mission_id))
        lines.append(asp.fact("mission_lesson", mission_id, mission.lesson))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def verify_story_samples() -> int:
    combos = valid_combos()
    if not combos:
        print("FAIL: no valid dusty-forest superhero combos exist.")
        return 1
    hero_ids = sorted(HEROES)
    for i, combo in enumerate(combos):
        params = StoryParams(
            trail=combo[0],
            hero=hero_ids[i % len(hero_ids)],
            threat=combo[1],
            relic=combo[2],
            companion=combo[3],
            mission=combo[4],
            seed=i,
        )
        sample = generate(params)
        if "dusty forest" not in sample.story or "forest trail" not in sample.story:
            print(f"FAIL: missing seed words in generated story for {params}.")
            return 1
        if not sample.story_qa or not sample.world_qa:
            print(f"FAIL: QA missing for {params}.")
            return 1
        if "{" in sample.story or "}" in sample.story:
            print(f"FAIL: unresolved template marker in story for {params}.")
            return 1
        if sample.world is None:
            print(f"FAIL: world trace missing for {params}.")
            return 1
        trail = sample.world.get("trail")
        cargo = sample.world.get("cargo")
        if trail.meters["safe"] < ACTIVE or cargo.meters["delivered"] < ACTIVE:
            print(f"FAIL: story did not reach a safe resolved ending for {params}.")
            return 1
    print(f"OK: exercised {len(combos)} generated superhero stories.")
    return 0


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between ASP and Python valid combo sets:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))
        return 1
    print(f"OK: ASP parity matches Python ({len(clingo_set)} combos).")
    return verify_story_samples()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: dusty forest trail, magic conflict, superhero rescue."
    )
    ap.add_argument("--trail", choices=TRAILS)
    ap.add_argument("--hero", choices=HEROES)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--mission", choices=MISSIONS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    trail_cfg = TRAILS[args.trail] if args.trail else None
    threat_cfg = THREATS[args.threat] if args.threat else None
    relic_cfg = RELICS[args.relic] if args.relic else None
    companion_cfg = COMPANIONS[args.companion] if args.companion else None
    mission_cfg = MISSIONS[args.mission] if args.mission else None
    if any([trail_cfg, threat_cfg, relic_cfg, companion_cfg, mission_cfg]):
        if any(
            [
                trail_cfg and threat_cfg and threat_cfg.id not in trail_cfg.affords,
                threat_cfg and relic_cfg and not threat_accepts_relic(threat_cfg, relic_cfg),
                threat_cfg and companion_cfg and not companion_reads_threat(threat_cfg, companion_cfg),
                mission_cfg and relic_cfg and not mission_matches_relic(mission_cfg, relic_cfg),
            ]
        ):
            raise StoryError(explain_rejection(trail_cfg, threat_cfg, relic_cfg, companion_cfg, mission_cfg))
    combos = [
        combo
        for combo in valid_combos()
        if (args.trail is None or combo[0] == args.trail)
        and (args.threat is None or combo[1] == args.threat)
        and (args.relic is None or combo[2] == args.relic)
        and (args.companion is None or combo[3] == args.companion)
        and (args.mission is None or combo[4] == args.mission)
    ]
    if not combos:
        raise StoryError("(No valid dusty-forest superhero story matches the given options.)")
    trail_id, threat_id, relic_id, companion_id, mission_id = rng.choice(combos)
    hero_id = args.hero or rng.choice(sorted(HEROES))
    return StoryParams(
        trail=trail_id,
        hero=hero_id,
        threat=threat_id,
        relic=relic_id,
        companion=companion_id,
        mission=mission_id,
        seed=None if args.seed is None else args.seed + index,
    )


def all_params() -> list[StoryParams]:
    hero_ids = sorted(HEROES)
    rows: list[StoryParams] = []
    for i, combo in enumerate(valid_combos()):
        rows.append(
            StoryParams(
                trail=combo[0],
                hero=hero_ids[i % len(hero_ids)],
                threat=combo[1],
                relic=combo[2],
                companion=combo[3],
                mission=combo[4],
                seed=i,
            )
        )
    return rows


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa_rows(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_rows(world)],
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
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (trail, threat, relic, companion, mission) combos:\n")
        for row in combos:
            print("  " + " ".join(f"{part:18}" for part in row))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(params) for params in all_params()]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 60, 60):
            seed = base_seed + attempts
            attempts += 1
            try:
                params = resolve_params(args, random.Random(seed), attempts - 1)
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
            header = f"### {HEROES[p.hero].alias}: {p.trail} / {p.threat} / {p.relic} / {p.mission}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
