#!/usr/bin/env python3
"""
dusty_forest_forest_trail_magic_conflict_superhero_3.py
=======================================================

A TinyStories-style StoryWorld for this seed:

    words: dusty forest
    setting: forest trail
    features: Magic, Conflict
    style: Superhero Story

Source tale, implemented as state instead of a frozen paragraph:
A young superhero carries supplies along a dusty forest trail. A magical forest
threat blocks the way. The hero first rushes in with flashy force and makes the
problem worse, then notices the threat's real need, uses the right magic, and
reopens the trail. The ending image proves the forest changed.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Trail:
    key: str
    phrase: str
    landmark: str
    ending_image: str
    supports: tuple[str, ...]


@dataclass(frozen=True)
class HeroProfile:
    key: str
    name: str
    alias: str
    subject: str
    object: str
    possessive: str
    costume: str
    signature: str


@dataclass(frozen=True)
class Threat:
    key: str
    title: str
    need: str
    need_phrase: str
    entrance: str
    problem: str
    clue: str
    backfire: str
    soothed: str
    ending_pose: str


@dataclass(frozen=True)
class Relic:
    key: str
    label: str
    power: str
    action_line: str


@dataclass(frozen=True)
class Companion:
    key: str
    name: str
    advice: str
    helper_line: str


@dataclass(frozen=True)
class Mission:
    key: str
    cargo: str
    beneficiary: str
    lesson: str


@dataclass
class StoryParams:
    trail: str
    hero: str
    threat: str
    relic: str
    companion: str
    mission: str
    seed: int


@dataclass
class Entity:
    name: str
    kind: str
    location: str
    tags: dict[str, str] = field(default_factory=dict)
    meters: dict[str, int] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> int:
        return self.meters.get(key, 0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.meme(key) + amount, 2)


@dataclass
class World:
    params: StoryParams
    trail_cfg: Trail
    hero_cfg: HeroProfile
    threat_cfg: Threat
    relic_cfg: Relic
    companion_cfg: Companion
    mission_cfg: Mission
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[dict[str, str]] = field(default_factory=list)
    paragraphs: list[list[str]] = field(default_factory=list)
    current_paragraph: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)

    def add(self, entity_id: str, entity: Entity) -> Entity:
        self.entities[entity_id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        self.current_paragraph.append(text.strip())

    def para(self) -> None:
        if self.current_paragraph:
            self.paragraphs.append(self.current_paragraph[:])
            self.current_paragraph.clear()

    def note(self, event: str, **facts: str) -> None:
        row = {"event": event}
        row.update({k: str(v) for k, v in facts.items()})
        self.history.append(row)

    def story_text(self) -> str:
        self.para()
        return "\n\n".join(" ".join(lines) for lines in self.paragraphs)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        for entity_id, ent in sorted(self.entities.items()):
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            detail = []
            if tags:
                detail.append(tags)
            if meters:
                detail.append(f"meters[{meters}]")
            if memes:
                detail.append(f"memes[{memes}]")
            suffix = f" {'; '.join(detail)}" if detail else ""
            rows.append(f"  {entity_id:<10} ({ent.kind:<10}) @ {ent.location}{suffix}")
        rows.append(f"  fired rules: {', '.join(self.fired_rules) if self.fired_rules else '(none)'}")
        rows.append(f"  history events: {[row['event'] for row in self.history]}")
        return "\n".join(rows)


TRAILS: dict[str, Trail] = {
    "cedar_turn": Trail(
        "cedar_turn",
        "the cedar turn of the dusty forest trail",
        "a split cedar sign",
        "Dust lay in soft rings around fresh fern shoots, and the trail looked open enough for even tiny boots.",
        ("dust_wisp", "briar_ogre"),
    ),
    "pine_switchback": Trail(
        "pine_switchback",
        "the pine switchback on the dusty forest trail",
        "a flat stone mile marker",
        "The air shone clean between the pines, and the trail curled ahead like a bright ribbon instead of a trap.",
        ("dust_wisp", "ember_moths"),
    ),
    "creek_overlook": Trail(
        "creek_overlook",
        "the creek overlook stretch of the dusty forest trail",
        "a dry stepping log above the creek",
        "The creek flashed silver under the open path, and even the dust smelled washed and calm.",
        ("briar_ogre", "ember_moths"),
    ),
}

HEROES: dict[str, HeroProfile] = {
    "comet_kid": HeroProfile(
        "comet_kid",
        "Ari",
        "Comet Kid",
        "he",
        "him",
        "his",
        "a blue cape with silver leaves",
        "Ari's boots sparked as he landed",
    ),
    "fern_flash": HeroProfile(
        "fern_flash",
        "Lina",
        "Fern Flash",
        "she",
        "her",
        "her",
        "a green cape with a gold clasp",
        "Lina skidded to a stop in a spray of glowing pebbles",
    ),
    "nova_robin": HeroProfile(
        "nova_robin",
        "Milo",
        "Nova Robin",
        "he",
        "him",
        "his",
        "a red scarf that snapped like a banner",
        "Milo landed light as a robin on the rail",
    ),
}

THREATS: dict[str, Threat] = {
    "dust_wisp": Threat(
        "dust_wisp",
        "the Dust Wisp",
        "calm_mist",
        "a cool silver mist",
        "a spinning little storm rose from the dirt",
        "It whipped sand over the path until nobody could see the next step.",
        "a cracked water gourd was hidden under the leaves at the center of the spinning dust",
        "The harder the hero slapped at the storm, the bigger and meaner the cloud became.",
        "When the silver mist touched the cracked gourd, the Dust Wisp slowed down and folded itself into a quiet ribbon of sand.",
        "The Dust Wisp hovered above the trail like a friendly sash instead of a storm.",
    ),
    "briar_ogre": Threat(
        "briar_ogre",
        "the Briar Ogre",
        "healing_light",
        "a warm mending light",
        "a thorny giant stomped out from the brush",
        "Its branches locked together and built a prickly wall across the trail.",
        "one huge thorn paw was split, and each painful step made the branches snarl tighter",
        "A hard tackle only shook loose more thorns and sealed the wall even more tightly.",
        "When the warm light reached the split thorn paw, the Briar Ogre sighed, opened its hands, and pulled the wall apart branch by branch.",
        "The Briar Ogre stood beside the path, holding the new leaves still so they would not snag anyone.",
    ),
    "ember_moths": Threat(
        "ember_moths",
        "the Ember Moths",
        "guiding_glow",
        "a steady guiding glow",
        "a wild cloud of glowing moths burst from the brush",
        "They swarmed in bright circles that made every turn look like the wrong one.",
        "a broken trail lantern lay dark in the weeds, and the moths kept crashing toward it",
        "Swinging wildly at them only scattered sparks into the dust and made the swarm panic harder.",
        "When the guiding glow lit the broken lantern's chimney, the Ember Moths settled into a calm shining stream that showed the true way forward.",
        "The Ember Moths lined the trail like floating stars, marking every safe step.",
    ),
}

RELICS: dict[str, Relic] = {
    "cloud_glove": Relic(
        "cloud_glove",
        "the Cloud Glove",
        "calm_mist",
        "{alias} lifted the Cloud Glove, and cool silver mist drifted over the dusty forest trail without pushing anyone around.",
    ),
    "sun_badge": Relic(
        "sun_badge",
        "the Sun Badge",
        "healing_light",
        "{alias} pressed the Sun Badge to {possessive} chest, and warm gold light spread over the forest trail like a careful bandage.",
    ),
    "star_lantern": Relic(
        "star_lantern",
        "the Star Lantern",
        "guiding_glow",
        "{alias} raised the Star Lantern, and a steady line of starlight reached down the dusty forest trail to show the next true step.",
    ),
}

COMPANIONS: dict[str, Companion] = {
    "pip_fox": Companion(
        "pip_fox",
        "Pip the fox",
        "Pip the fox tugged the cape and tapped the ground with one neat paw.",
        "Pip trotted beside the hero and watched the path for the smallest clue.",
    ),
    "ranger_nia": Companion(
        "ranger_nia",
        "Ranger Nia",
        'Ranger Nia whispered, "Look before you blast."',
        "Ranger Nia walked close beside the supplies and kept one eye on the frightened magic.",
    ),
}

MISSIONS: dict[str, Mission] = {
    "bandages": Mission(
        "bandages",
        "a satchel of bandage rolls",
        "the squirrel clinic beyond the bend",
        "helping fast is good, but helping right is better",
    ),
    "seed_crate": Mission(
        "seed_crate",
        "a crate of glow seeds",
        "Grandma Maple's garden gate",
        "real heroes grow things after they stop danger",
    ),
    "soup_pot": Mission(
        "soup_pot",
        "a warm soup pot with a tight silver lid",
        "the tired hikers at Pine Rest",
        "a brave rescue should end with someone cared for",
    ),
}


def valid_combo(trail: str, threat: str, relic: str) -> bool:
    if trail not in TRAILS or threat not in THREATS or relic not in RELICS:
        return False
    if threat not in TRAILS[trail].supports:
        return False
    return THREATS[threat].need == RELICS[relic].power


def invalid_reason(trail: str, threat: str, relic: str) -> str:
    if trail not in TRAILS:
        return f"No story: unknown trail {trail!r}."
    if threat not in THREATS:
        return f"No story: unknown threat {threat!r}."
    if relic not in RELICS:
        return f"No story: unknown relic {relic!r}."
    trail_cfg = TRAILS[trail]
    threat_cfg = THREATS[threat]
    relic_cfg = RELICS[relic]
    if threat not in trail_cfg.supports:
        return f"No story: {trail_cfg.phrase} does not fit {threat_cfg.title}."
    if threat_cfg.need != relic_cfg.power:
        return (
            f"No story: {relic_cfg.label} brings {relic_cfg.power.replace('_', ' ')}, "
            f"but {threat_cfg.title} needs {threat_cfg.need_phrase}."
        )
    return "No story: the requested superhero conflict is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str, str]] = []
    for trail in sorted(TRAILS):
        for hero in sorted(HEROES):
            for threat in sorted(THREATS):
                for relic in sorted(RELICS):
                    if not valid_combo(trail, threat, relic):
                        continue
                    for companion in sorted(COMPANIONS):
                        for mission in sorted(MISSIONS):
                            rows.append((trail, hero, threat, relic, companion, mission))
    return rows


def build_world(params: StoryParams) -> World:
    world = World(
        params=params,
        trail_cfg=TRAILS[params.trail],
        hero_cfg=HEROES[params.hero],
        threat_cfg=THREATS[params.threat],
        relic_cfg=RELICS[params.relic],
        companion_cfg=COMPANIONS[params.companion],
        mission_cfg=MISSIONS[params.mission],
    )
    world.add(
        "hero",
        Entity(
            world.hero_cfg.name,
            "hero",
            world.trail_cfg.key,
            tags={"alias": world.hero_cfg.alias, "costume": world.hero_cfg.costume, "role": "protector"},
            meters={"rushed": 0, "understood": 0},
            memes={"bravery": 1.0, "care": 0.5, "fear": 0.0, "focus": 0.0},
        ),
    )
    world.add(
        "companion",
        Entity(
            world.companion_cfg.name,
            "companion",
            world.trail_cfg.key,
            tags={"role": "helper"},
            meters={"helped": 0},
            memes={"trust": 0.5},
        ),
    )
    world.add(
        "trail",
        Entity(
            "trail",
            "place",
            world.trail_cfg.key,
            tags={"setting": "dusty forest", "landmark": world.trail_cfg.landmark},
            meters={"blocked": 0, "safe": 1, "dust": 1},
            memes={"peace": 0.4},
        ),
    )
    world.add(
        "threat",
        Entity(
            world.threat_cfg.title,
            "threat",
            world.trail_cfg.key,
            tags={"need": world.threat_cfg.need, "role": "obstacle"},
            meters={"active": 0, "soothed": 0},
            memes={"fear": 0.7, "anger": 0.6},
        ),
    )
    world.add(
        "relic",
        Entity(
            world.relic_cfg.label,
            "relic",
            world.trail_cfg.key,
            tags={"power": world.relic_cfg.power},
            meters={"charged": 1, "used": 0},
            memes={"wonder": 0.8},
        ),
    )
    world.add(
        "cargo",
        Entity(
            world.mission_cfg.cargo,
            "cargo",
            world.trail_cfg.key,
            tags={"for": world.mission_cfg.beneficiary},
            meters={"delivered": 0},
            memes={"hope": 0.7},
        ),
    )
    return world


def propagate(world: World) -> None:
    trail = world.get("trail")
    threat = world.get("threat")
    hero = world.get("hero")
    cargo = world.get("cargo")
    companion = world.get("companion")

    if threat.meter("active") and not threat.meter("soothed"):
        trail.meters["blocked"] = 1
        trail.meters["safe"] = 0
        trail.meters["dust"] = 3 if hero.meter("rushed") else 2
        trail.memes["peace"] = 0.1
    if threat.meter("soothed"):
        trail.meters["blocked"] = 0
        trail.meters["safe"] = 1
        trail.meters["dust"] = 1
        trail.memes["peace"] = 1.2
        cargo.meters["delivered"] = 1
        companion.meters["helped"] = 1


def introduce(world: World) -> None:
    hero_cfg = world.hero_cfg
    mission_cfg = world.mission_cfg
    companion_cfg = world.companion_cfg
    world.say(
        f"One afternoon, {hero_cfg.name} clipped on {hero_cfg.costume} and became {hero_cfg.alias} for a supply run through {world.trail_cfg.phrase}."
    )
    world.say(
        f"{hero_cfg.signature}, carrying {mission_cfg.cargo} for {mission_cfg.beneficiary}. {companion_cfg.helper_line}"
    )
    world.note("beginning", hero=hero_cfg.alias, cargo=mission_cfg.cargo, place=world.trail_cfg.phrase)


def reveal_conflict(world: World) -> None:
    threat = world.get("threat")
    trail = world.get("trail")
    hero = world.get("hero")
    threat.meters["active"] = 1
    trail.meters["safe"] = 0
    trail.meters["blocked"] = 1
    hero.add_meme("fear", 0.5)
    propagate(world)
    world.para()
    world.say(
        f"Near {world.trail_cfg.landmark}, {world.threat_cfg.entrance}. {world.threat_cfg.problem}"
    )
    world.say(
        f"The magic relic in {hero.name}'s hands hummed, but the forest trail was shut tight by conflict instead of opened by it."
    )
    world.note("conflict", threat=world.threat_cfg.title, landmark=world.trail_cfg.landmark)


def rush_and_fail(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    hero.meters["rushed"] = 1
    hero.add_meme("fear", 0.3)
    hero.add_meme("focus", -0.2)
    companion.add_meme("trust", -0.1)
    propagate(world)
    world.say(
        f"{world.hero_cfg.alias} tried the fastest answer first, charging ahead with bright superhero energy."
    )
    world.say(world.threat_cfg.backfire)
    world.note("failed_first_move", reason="rushed", threat=world.threat_cfg.title)


def discover_turn(world: World) -> None:
    hero = world.get("hero")
    companion = world.get("companion")
    hero.meters["rushed"] = 0
    hero.meters["understood"] = 1
    hero.add_meme("focus", 1.1)
    hero.add_meme("care", 0.7)
    companion.add_meme("trust", 0.4)
    world.para()
    world.say(
        f"{world.companion_cfg.advice} Then {world.hero_cfg.name} noticed that {world.threat_cfg.clue}."
    )
    world.say(
        f"That was the turn in the whole adventure. The hero finally understood that the problem needed {world.threat_cfg.need_phrase}, not a louder crash."
    )
    world.say(
        f"Saving the day meant protecting the trail and still carrying {world.mission_cfg.cargo} to {world.mission_cfg.beneficiary}."
    )
    world.note("turn", need=world.threat_cfg.need, clue=world.threat_cfg.clue)


def use_magic(world: World) -> None:
    threat = world.get("threat")
    relic = world.get("relic")
    hero = world.get("hero")
    relic.meters["used"] = 1
    threat.meters["soothed"] = 1
    hero.add_meme("bravery", 0.4)
    hero.add_meme("care", 0.3)
    propagate(world)
    world.para()
    world.say(
        world.relic_cfg.action_line.format(alias=world.hero_cfg.alias, possessive=world.hero_cfg.possessive)
    )
    world.say(world.threat_cfg.soothed)
    world.note("magic_used", relic=world.relic_cfg.label, power=world.relic_cfg.power)


def close_story(world: World) -> None:
    cargo = world.get("cargo")
    trail = world.get("trail")
    world.say(
        f"With the way clear again, {world.hero_cfg.name} carried {world.mission_cfg.cargo} to {world.mission_cfg.beneficiary} before it was too late."
    )
    if cargo.meter("delivered") and trail.meter("safe"):
        world.say(world.threat_cfg.ending_pose)
        world.say(world.trail_cfg.ending_image)
        world.say(
            f"{world.hero_cfg.alias} grinned because {world.mission_cfg.lesson}. In the dusty forest, even the ending looked like a rescue."
        )
        world.note("ending", delivered=world.mission_cfg.cargo, status="safe")
    else:
        raise StoryError("Broken story state: the trail did not become safe after the matching magic was used.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    reveal_conflict(world)
    rush_and_fail(world)
    discover_turn(world)
    use_magic(world)
    close_story(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a superhero story for children that uses the words "dusty forest" and takes place on a forest trail.',
        f"Tell a magical conflict story where {world.hero_cfg.name} becomes {world.hero_cfg.alias} and carries {world.mission_cfg.cargo}.",
        f"Make the obstacle {world.threat_cfg.title}, and let the ending image prove that the trail became safe again.",
    ]


def story_qa_rows(world: World) -> list[tuple[str, str]]:
    hero_cfg = world.hero_cfg
    mission_cfg = world.mission_cfg
    threat_cfg = world.threat_cfg
    relic_cfg = world.relic_cfg
    companion_cfg = world.companion_cfg
    trail_cfg = world.trail_cfg
    return [
        (
            "Who is the superhero in this story?",
            f"The superhero is {hero_cfg.name}, who becomes {hero_cfg.alias}. {hero_cfg.alias} uses magic to protect {trail_cfg.phrase} while carrying {mission_cfg.cargo}.",
        ),
        (
            "What caused the main conflict?",
            f"The main conflict started when {threat_cfg.title} blocked the trail. {threat_cfg.problem}",
        ),
        (
            "Why did the first quick move fail?",
            f"The first quick move failed because the hero rushed before understanding the threat's real need. That flashy mistake made the danger bigger instead of calming it.",
        ),
        (
            "How did the hero know what magic to use?",
            f"{companion_cfg.name} slowed the hero down, and then the hidden clue became clear. Once {hero_cfg.name} noticed that {threat_cfg.clue}, the right answer was {threat_cfg.need_phrase}.",
        ),
        (
            "How was the trail made safe again?",
            f"{hero_cfg.alias} used {relic_cfg.label}, which carries {relic_cfg.power.replace('_', ' ')}. That magic matched the threat, soothed it, and opened the trail so the supplies could be delivered.",
        ),
        (
            "What proves the ending is different from the beginning?",
            f"At the end, the cargo reaches {mission_cfg.beneficiary} and the trail is safe again. {trail_cfg.ending_image}",
        ),
    ]


def world_qa_rows(world: World) -> list[tuple[str, str]]:
    rows = [
        (
            "Why can rushing make a rescue harder?",
            "Rushing can hide the real problem. A helper who stops to look first is more likely to choose the right tool.",
        ),
        (
            "Why does a trail matter in a forest rescue story?",
            "A trail decides who can move safely through the woods. If it is blocked, help and supplies cannot reach the people waiting ahead.",
        ),
        (
            "Why is matching magic to the problem important?",
            "Magic works best when it fits the need instead of showing off. The wrong power can make a frightened place or creature even more upset.",
        ),
    ]
    if world.threat_cfg.key == "dust_wisp":
        rows.append(
            (
                "Why would mist help with flying dust?",
                "Mist makes dust heavier and calmer. It can also help a dry, crackly place stop spinning so wildly.",
            )
        )
    if world.threat_cfg.key == "briar_ogre":
        rows.append(
            (
                "Why would healing light calm a thorn creature?",
                "A hurting creature may lash out because it is in pain. If the pain is gently mended, it no longer needs to guard itself so fiercely.",
            )
        )
    if world.threat_cfg.key == "ember_moths":
        rows.append(
            (
                "Why would guiding light help confused moths?",
                "Moths often fly toward light when they need direction. A steady glow is easier to follow than a burst of wild sparks.",
            )
        )
    return rows


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.trail, params.threat, params.relic):
        raise StoryError(invalid_reason(params.trail, params.threat, params.relic))
    if params.hero not in HEROES:
        raise StoryError(f"No story: unknown hero {params.hero!r}.")
    if params.companion not in COMPANIONS:
        raise StoryError(f"No story: unknown companion {params.companion!r}.")
    if params.mission not in MISSIONS:
        raise StoryError(f"No story: unknown mission {params.mission!r}.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.story_text(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa_rows(world)],
        world_qa=[QAItem(q, a) for q, a in world_qa_rows(world)],
        world=world,
    )


ASP_RULES = r"""
combo(T,H,X,R,C,M) :-
    trail(T),
    hero(H),
    threat(X),
    relic(R),
    companion(C),
    mission(M),
    supports(T,X),
    threat_need(X,N),
    relic_power(R,N).

ok :- chosen(T,H,X,R,C,M), combo(T,H,X,R,C,M).

#show combo/6.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for key, trail in sorted(TRAILS.items()):
        rows.append(fact("trail", key))
        for threat in trail.supports:
            rows.append(fact("supports", key, threat))
    for key in sorted(HEROES):
        rows.append(fact("hero", key))
    for key, threat in sorted(THREATS.items()):
        rows.append(fact("threat", key))
        rows.append(fact("threat_need", key, threat.need))
    for key, relic in sorted(RELICS.items()):
        rows.append(fact("relic", key))
        rows.append(fact("relic_power", key, relic.power))
    for key in sorted(COMPANIONS):
        rows.append(fact("companion", key))
    for key in sorted(MISSIONS):
        rows.append(fact("mission", key))
    if params is not None:
        rows.append(
            fact(
                "chosen",
                params.trail,
                params.hero,
                params.threat,
                params.relic,
                params.companion,
                params.mission,
            )
        )
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str, str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str, str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos


def asp_verify(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    return bool(atoms(one_model(asp_program(params)), "ok"))


def verify() -> str:
    py = set(valid_combos())
    asp = asp_valid_combos()
    if py != asp:
        only_py = sorted(py - asp)
        only_asp = sorted(asp - py)
        raise StoryError(f"ASP/Python mismatch. only_python={only_py} only_asp={only_asp}")
    for index, combo in enumerate(sorted(py), 1):
        params = StoryParams(
            trail=combo[0],
            hero=combo[1],
            threat=combo[2],
            relic=combo[3],
            companion=combo[4],
            mission=combo[5],
            seed=index,
        )
        sample = generate(params)
        if "dusty forest" not in sample.story or "forest trail" not in sample.story:
            raise StoryError(f"Story text lost the requested seed words for combo {combo}.")
        if not sample.story_qa or not sample.world_qa or not sample.prompts:
            raise StoryError(f"Story sample is missing QA or prompts for combo {combo}.")
        if sample.world is None:
            raise StoryError(f"Story sample lost its world model for combo {combo}.")
        trail = sample.world.get("trail")
        cargo = sample.world.get("cargo")
        if not trail.meter("safe") or not cargo.meter("delivered"):
            raise StoryError(f"Story failed to reach a resolved ending for combo {combo}.")
        if not asp_verify(params):
            raise StoryError(f"Chosen combo did not satisfy ASP verification: {combo}")
    return f"OK: clingo gate matches Python and {len(py)} valid stories execute with resolved endings."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate dusty-forest superhero storyworld samples.")
    parser.add_argument("--trail", choices=sorted(TRAILS))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--threat", choices=sorted(THREATS))
    parser.add_argument("--relic", choices=sorted(RELICS))
    parser.add_argument("--companion", choices=sorted(COMPANIONS))
    parser.add_argument("--mission", choices=sorted(MISSIONS))
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def _params_from_combo(combo: tuple[str, str, str, str, str, str], seed: int) -> StoryParams:
    return StoryParams(
        trail=combo[0],
        hero=combo[1],
        threat=combo[2],
        relic=combo[3],
        companion=combo[4],
        mission=combo[5],
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None, index: int = 0) -> StoryParams:
    rng = rng or random.Random(args.seed + index)
    if any([args.trail, args.hero, args.threat, args.relic, args.companion, args.mission]):
        trail = args.trail or rng.choice(sorted(TRAILS))
        hero = args.hero or rng.choice(sorted(HEROES))
        threat = args.threat or rng.choice(sorted(THREATS))
        relic = args.relic or rng.choice(sorted(RELICS))
        companion = args.companion or rng.choice(sorted(COMPANIONS))
        mission = args.mission or rng.choice(sorted(MISSIONS))
        if not valid_combo(trail, threat, relic):
            raise StoryError(invalid_reason(trail, threat, relic))
        return StoryParams(
            trail=trail,
            hero=hero,
            threat=threat,
            relic=relic,
            companion=companion,
            mission=mission,
            seed=args.seed + index,
        )
    combo = rng.choice(valid_combos())
    return _params_from_combo(combo, args.seed + index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Generation prompts ==")
    for idx, prompt in enumerate(sample.prompts, 1):
        print(f"{idx}. {prompt}")
    print("\n== (2) Story-grounded QA ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World-knowledge QA ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, args: argparse.Namespace, label: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if label:
        print(label)
    print(sample.story)
    if args.trace and sample.world is not None:
        print(sample.world.trace())
    if args.qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for combo in sorted(asp_valid_combos()):
        print("\t".join(combo))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.show_asp:
            print(asp_program())
            return 0
        if args.verify:
            print(verify())
            return 0
        if args.asp:
            _emit_asp_listing()
            return 0
        if args.all:
            combos = valid_combos()
            for idx, combo in enumerate(combos, 1):
                sample = generate(_params_from_combo(combo, args.seed + idx))
                emit(
                    sample,
                    args,
                    label=(
                        f"### {sample.params.hero} / {sample.params.threat} / "
                        f"{sample.params.relic} / {sample.params.mission}"
                    ),
                )
                if idx != len(combos) and not args.json:
                    print("\n" + "=" * 70 + "\n")
            return 0
        count = max(1, args.n)
        for index in range(count):
            sample = generate(resolve_params(args, index=index))
            emit(sample, args, label=f"### variant {index + 1}" if count > 1 and not args.json else None)
            if index != count - 1 and not args.json:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
