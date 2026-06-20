#!/usr/bin/env python3
"""
dusty_forest_forest_trail_magic_conflict_superhero_4.py
=======================================================

A TinyStories-style StoryWorld for this seed:

    words: dusty forest
    setting: forest trail
    features: Magic, Conflict
    style: Superhero Story

Internal source tale:
A child superhero hurries along a dusty forest trail with supplies for someone
who is waiting. A magical forest guardian blocks the path and the hero first
tries a flashy attack, which makes the danger worse. A helper notices a clue
that reveals what the guardian actually needs. The hero switches from force to
care, uses the right magic, and proves the change by reopening the trail and
delivering the supplies.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Trail:
    key: str
    phrase: str
    landmark: str
    dust_color: str
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
    entry_line: str
    impulsive_move: str
    calming_style: str


@dataclass(frozen=True)
class Threat:
    key: str
    title: str
    kind: str
    copula: str
    entrance: str
    block_line: str
    clue: str
    backfire: str
    need: str
    need_phrase: str
    relief_line: str
    ending_pose: str


@dataclass(frozen=True)
class Relic:
    key: str
    label: str
    power: str
    activation_line: str


@dataclass(frozen=True)
class Companion:
    key: str
    name: str
    kind: str
    advice: str
    helper_line: str


@dataclass(frozen=True)
class Mission:
    key: str
    cargo: str
    recipient: str
    reason: str
    delivery_image: str


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

    def set_meter(self, key: str, value: int) -> None:
        self.meters[key] = value

    def add_meter(self, key: str, amount: int) -> None:
        self.meters[key] = self.meter(key) + amount

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
        row.update({key: str(value) for key, value in facts.items()})
        self.history.append(row)

    def story_text(self) -> str:
        self.para()
        return "\n\n".join(" ".join(lines) for lines in self.paragraphs)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        for entity_id, entity in sorted(self.entities.items()):
            tags = ", ".join(f"{key}={value}" for key, value in sorted(entity.tags.items()))
            meters = ", ".join(f"{key}={value}" for key, value in sorted(entity.meters.items()))
            memes = ", ".join(f"{key}={value}" for key, value in sorted(entity.memes.items()))
            suffix = []
            if tags:
                suffix.append(tags)
            if meters:
                suffix.append(f"meters[{meters}]")
            if memes:
                suffix.append(f"memes[{memes}]")
            tail = f" {'; '.join(suffix)}" if suffix else ""
            rows.append(f"  {entity_id:<10} ({entity.kind:<10}) @ {entity.location}{tail}")
        rows.append(f"  fired rules: {', '.join(self.fired_rules) if self.fired_rules else '(none)'}")
        rows.append(f"  history events: {[row['event'] for row in self.history]}")
        return "\n".join(rows)


TRAILS: dict[str, Trail] = {
    "cedar_arc": Trail(
        key="cedar_arc",
        phrase="the cedar arc of the dusty forest trail",
        landmark="a bent cedar sign",
        dust_color="golden",
        ending_image="Golden dust settled around tiny blue flowers, and the trail lay open in a clean curve past the cedar sign.",
        supports=("dust_serpent", "thorn_guardian"),
    ),
    "fern_rise": Trail(
        key="fern_rise",
        phrase="the fern rise on the dusty forest trail",
        landmark="a mossy stepping log",
        dust_color="amber",
        ending_image="Amber dust rested in neat stripes beside the stepping log, and the path looked safe enough for laughing children again.",
        supports=("dust_serpent", "echo_ravens"),
    ),
    "moonroot_bend": Trail(
        key="moonroot_bend",
        phrase="the moonroot bend of the dusty forest trail",
        landmark="a pale root arch",
        dust_color="silver",
        ending_image="Silver dust glimmered softly under the root arch, and the bend shone like a promise instead of a warning.",
        supports=("thorn_guardian", "echo_ravens"),
    ),
}

HEROES: dict[str, HeroProfile] = {
    "spark_fern": HeroProfile(
        key="spark_fern",
        name="Lina",
        alias="Spark Fern",
        subject="she",
        object="her",
        possessive="her",
        costume="a green cape lined with tiny stars",
        entry_line="Lina landed in a soft skid and sent bright leaf sparks around her boots.",
        impulsive_move="She threw a ring of hot green sparks straight at the danger.",
        calming_style="steady hands and a quiet superhero voice",
    ),
    "comet_branch": HeroProfile(
        key="comet_branch",
        name="Ari",
        alias="Comet Branch",
        subject="he",
        object="him",
        possessive="his",
        costume="a blue jacket with a silver branch on the chest",
        entry_line="Ari leaped from stump to stump until his boots flashed beside the trail.",
        impulsive_move="He rushed forward and struck the danger with a bright comet dash.",
        calming_style="slow breaths and careful listening",
    ),
    "trailshield": HeroProfile(
        key="trailshield",
        name="Mika",
        alias="Trailshield",
        subject="they",
        object="them",
        possessive="their",
        costume="a red scarf and a round bark-bright shield",
        entry_line="Mika planted their boots on the path and lifted a shield that gleamed like polished bark.",
        impulsive_move="They slammed their shield into the danger with a loud burst of light.",
        calming_style="gentle courage and patient words",
    ),
}

THREATS: dict[str, Threat] = {
    "dust_serpent": Threat(
        key="dust_serpent",
        title="the Dust Serpent",
        kind="guardian",
        copula="was",
        entrance="a long dust snake rose out of the trail and curled across the path",
        block_line="Its body whipped the dirt into a storm so thick that the next turn disappeared.",
        clue="At the center of the storm, a dry stone bowl rattled against the ground.",
        backfire="The storm only spun faster, and the serpent grew sharper and taller.",
        need="rain_song",
        need_phrase="a soft rain-song spell",
        relief_line="The dust serpent lowered its head, drank the silver drops, and unwound itself from the trail.",
        ending_pose="The Dust Serpent rested beside the path like a sleepy sandy rope instead of a threat.",
    ),
    "thorn_guardian": Threat(
        key="thorn_guardian",
        title="the Thorn Guardian",
        kind="guardian",
        copula="was",
        entrance="a giant bundle of thorns stomped up from the roots and spread its arms wide",
        block_line="Thick vines knitted into a wall across the trail and snagged every loose strap.",
        clue="One glowing splinter was stuck deep in its wooden palm.",
        backfire="The vines tightened, and more thorns scraped across the dusty ground.",
        need="healing_glow",
        need_phrase="a warm healing glow",
        relief_line="The glowing splinter slipped free, and the thorn giant let out a creaky sigh as the wall opened.",
        ending_pose="The Thorn Guardian stood to the side like a patient tree gate, no longer angry.",
    ),
    "echo_ravens": Threat(
        key="echo_ravens",
        title="the Echo Ravens",
        kind="guardian",
        copula="were",
        entrance="a flock of black ravens made of wind and glitter burst from the branches",
        block_line="Their cries bounced around the trail until every step sounded wrong and confusing.",
        clue="A cracked bell hung from a branch and trembled whenever the ravens screamed.",
        backfire="The louder the hero answered the noise, the wilder the flock whirled.",
        need="guiding_chime",
        need_phrase="a clear guiding chime",
        relief_line="A clean note rolled through the trees, and the ravens circled once before settling into quiet shadows.",
        ending_pose="The Echo Ravens perched above the trail like watchful dark feathers, calm and still.",
    ),
}

RELICS: dict[str, Relic] = {
    "rain_gauntlet": Relic(
        key="rain_gauntlet",
        label="the Rain Gauntlet",
        power="rain_song",
        activation_line="Cool silver drops rang from the gauntlet like a tiny cloud singing.",
    ),
    "sun_patch": Relic(
        key="sun_patch",
        label="the Sun Patch",
        power="healing_glow",
        activation_line="Warm gold light poured from the patch and wrapped the hurt place like a blanket.",
    ),
    "star_bell": Relic(
        key="star_bell",
        label="the Star Bell",
        power="guiding_chime",
        activation_line="One bright note floated out of the bell and held steady in the dusty air.",
    ),
}

COMPANIONS: dict[str, Companion] = {
    "moss_fox": Companion(
        key="moss_fox",
        name="Pip",
        kind="moss fox",
        advice="Super heroes do not always need a bigger blast. Sometimes they need a better question.",
        helper_line="Pip pawed at the clue and flicked dusty leaves away so the hero could see it clearly.",
    ),
    "glow_wren": Companion(
        key="glow_wren",
        name="Nim",
        kind="glow wren",
        advice="Listen to what the trail is trying to tell you before you try to win.",
        helper_line="Nim zipped through the dust and tapped the clue with a bright beak.",
    ),
    "brook_sprite": Companion(
        key="brook_sprite",
        name="Tala",
        kind="brook sprite",
        advice="Real strength can sound soft when it is fixing the right thing.",
        helper_line="Tala swept a ribbon of clear water over the clue so its shape stood out.",
    ),
}

MISSIONS: dict[str, Mission] = {
    "medicine_satchel": Mission(
        key="medicine_satchel",
        cargo="a satchel of moon-leaf medicine",
        recipient="Grandmother Suri",
        reason="Grandmother Suri was waiting at the ranger hut with a sore ankle.",
        delivery_image="Grandmother Suri smiled as the moon-leaf wraps cooled her ankle by the doorway.",
    ),
    "lantern_bundle": Mission(
        key="lantern_bundle",
        cargo="a bundle of star lanterns",
        recipient="the forest school",
        reason="the forest school needed the lanterns before sunset reading time.",
        delivery_image="The children at the forest school hung the little lanterns and made the room glow like a gentle sky.",
    ),
    "water_map": Mission(
        key="water_map",
        cargo="a rolled water map",
        recipient="Ranger Ivo",
        reason="Ranger Ivo needed the map to guide families to the safest spring.",
        delivery_image="Ranger Ivo spread the map on a stump and traced a safe line for every family to follow.",
    ),
}


def valid_combo(trail: str, threat: str, relic: str) -> bool:
    return threat in TRAILS[trail].supports and THREATS[threat].need == RELICS[relic].power


def invalid_reason(trail: str, threat: str, relic: str) -> str:
    if threat not in TRAILS[trail].supports:
        return f"No story: {THREATS[threat].title} does not belong on {TRAILS[trail].phrase}."
    if THREATS[threat].need != RELICS[relic].power:
        return (
            f"No story: {RELICS[relic].label} cannot solve {THREATS[threat].title}; "
            f"it needs {THREATS[threat].need_phrase}."
        )
    return "No story: that combination is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for trail in sorted(TRAILS):
        for hero in sorted(HEROES):
            for threat in sorted(THREATS):
                for relic in sorted(RELICS):
                    if not valid_combo(trail, threat, relic):
                        continue
                    for companion in sorted(COMPANIONS):
                        for mission in sorted(MISSIONS):
                            combos.append((trail, hero, threat, relic, companion, mission))
    return combos


def setup_world(params: StoryParams) -> World:
    trail_cfg = TRAILS[params.trail]
    hero_cfg = HEROES[params.hero]
    threat_cfg = THREATS[params.threat]
    relic_cfg = RELICS[params.relic]
    companion_cfg = COMPANIONS[params.companion]
    mission_cfg = MISSIONS[params.mission]
    world = World(
        params=params,
        trail_cfg=trail_cfg,
        hero_cfg=hero_cfg,
        threat_cfg=threat_cfg,
        relic_cfg=relic_cfg,
        companion_cfg=companion_cfg,
        mission_cfg=mission_cfg,
    )
    world.add(
        "trail",
        Entity(
            name=trail_cfg.phrase,
            kind="trail",
            location=trail_cfg.landmark,
            tags={"landmark": trail_cfg.landmark, "dust": trail_cfg.dust_color},
            meters={"safe": 0, "blocked": 1, "dust": 4},
            memes={"hope": 0.2},
        ),
    )
    world.add(
        "hero",
        Entity(
            name=hero_cfg.alias,
            kind="hero",
            location=trail_cfg.phrase,
            tags={"civilian_name": hero_cfg.name, "costume": hero_cfg.costume},
            meters={"energy": 5, "mistake": 0},
            memes={"bravery": 0.7, "care": 0.4, "patience": 0.2},
        ),
    )
    world.add(
        "threat",
        Entity(
            name=threat_cfg.title,
            kind=threat_cfg.kind,
            location=trail_cfg.phrase,
            tags={"need": threat_cfg.need},
            meters={"anger": 3, "calm": 0},
            memes={"fear": 0.6},
        ),
    )
    world.add(
        "relic",
        Entity(
            name=relic_cfg.label,
            kind="relic",
            location=trail_cfg.phrase,
            tags={"power": relic_cfg.power},
            meters={"charge": 3},
            memes={"wonder": 0.6},
        ),
    )
    world.add(
        "companion",
        Entity(
            name=companion_cfg.name,
            kind="companion",
            location=trail_cfg.phrase,
            tags={"kind": companion_cfg.kind},
            meters={"focus": 4},
            memes={"trust": 0.7},
        ),
    )
    world.add(
        "cargo",
        Entity(
            name=mission_cfg.cargo,
            kind="cargo",
            location=trail_cfg.phrase,
            tags={"recipient": mission_cfg.recipient},
            meters={"delivered": 0, "secure": 3},
            memes={"care": 0.8},
        ),
    )
    return world


def opening_scene(world: World) -> None:
    hero = world.hero_cfg
    trail = world.trail_cfg
    mission = world.mission_cfg
    world.say(
        f"{hero.name}, known on that dusty forest day as {hero.alias}, hurried along {trail.phrase} in {hero.costume}."
    )
    world.say(hero.entry_line)
    world.say(
        f"In {hero.possessive} arms was {mission.cargo}, because {mission.reason}"
    )
    world.note(
        "opening",
        hero=hero.alias,
        trail=trail.key,
        cargo=mission.cargo,
        recipient=mission.recipient,
    )
    world.para()


def threat_scene(world: World) -> None:
    threat = world.threat_cfg
    trail = world.get("trail")
    world.say(f"Near {world.trail_cfg.landmark}, {threat.entrance}.")
    world.say(threat.block_line)
    world.say(f"The whole forest trail shivered, and the dust turned {world.trail_cfg.dust_color} around the hero's boots.")
    trail.set_meter("blocked", 2)
    trail.set_meter("safe", 0)
    trail.add_meter("dust", 2)
    world.get("hero").add_meme("bravery", 0.2)
    world.get("hero").add_meme("patience", -0.1)
    world.note("threat_blocks_trail", threat=threat.key, landmark=world.trail_cfg.landmark)
    world.para()


def mistake_scene(world: World) -> None:
    hero_cfg = world.hero_cfg
    hero = world.get("hero")
    threat = world.get("threat")
    trail = world.get("trail")
    cargo = world.get("cargo")
    world.say(f"{hero_cfg.impulsive_move} {world.threat_cfg.backfire}")
    world.say("Dust slapped the hero's cape, and the cargo nearly slipped to the ground.")
    hero.set_meter("mistake", 1)
    hero.add_meter("energy", -1)
    hero.add_meme("care", -0.1)
    threat.add_meter("anger", 2)
    threat.add_meme("fear", 0.2)
    trail.add_meter("dust", 1)
    cargo.add_meter("secure", -1)
    world.note(
        "hero_mistake",
        move=hero_cfg.impulsive_move,
        backfire=world.threat_cfg.key,
        cargo=world.mission_cfg.cargo,
    )
    world.para()


def clue_scene(world: World) -> None:
    companion_cfg = world.companion_cfg
    hero_cfg = world.hero_cfg
    hero = world.get("hero")
    world.say(f"Then {companion_cfg.name} the {companion_cfg.kind} cried, \"{companion_cfg.advice}\"")
    world.say(companion_cfg.helper_line)
    world.say(world.threat_cfg.clue)
    world.say(
        f"{hero_cfg.name} stopped showing off, knelt in the dust, and understood that {world.threat_cfg.title} needed {world.threat_cfg.need_phrase}, not another hit."
    )
    hero.add_meme("patience", 0.6)
    hero.add_meme("care", 0.4)
    world.get("companion").add_meme("trust", 0.1)
    world.fired_rules.append("clue_reveals_need")
    world.note("clue_found", clue=world.threat_cfg.clue, need=world.threat_cfg.need)
    world.para()


def repair_scene(world: World) -> None:
    hero_cfg = world.hero_cfg
    hero = world.get("hero")
    threat = world.get("threat")
    trail = world.get("trail")
    relic = world.get("relic")
    world.say(
        f"{hero_cfg.name} lifted {world.relic_cfg.label} and used {hero_cfg.calming_style} instead of force."
    )
    world.say(world.relic_cfg.activation_line)
    world.say(world.threat_cfg.relief_line)
    trail.set_meter("blocked", 0)
    trail.set_meter("safe", 1)
    trail.set_meter("dust", max(1, trail.meter("dust") - 3))
    threat.set_meter("anger", 0)
    threat.set_meter("calm", 4)
    threat.add_meme("fear", -0.4)
    hero.add_meme("care", 0.5)
    hero.add_meme("patience", 0.4)
    relic.add_meter("charge", -1)
    world.fired_rules.append("right_magic_used")
    world.note(
        "trail_repaired",
        relic=world.relic_cfg.key,
        need=world.threat_cfg.need,
        threat=world.threat_cfg.key,
    )
    world.para()


def delivery_scene(world: World) -> None:
    hero_cfg = world.hero_cfg
    trail = world.get("trail")
    cargo = world.get("cargo")
    world.say(f"With the path clear, {hero_cfg.alias} ran on and delivered {world.mission_cfg.cargo} to {world.mission_cfg.recipient}.")
    world.say(world.mission_cfg.delivery_image)
    world.say(world.threat_cfg.ending_pose)
    world.say(world.trail_cfg.ending_image)
    cargo.set_meter("delivered", 1)
    cargo.set_meter("secure", max(1, cargo.meter("secure")))
    trail.add_meme("hope", 0.6)
    world.get("hero").add_meme("bravery", 0.2)
    world.get("hero").add_meme("care", 0.2)
    world.note(
        "delivery_complete",
        recipient=world.mission_cfg.recipient,
        cargo=world.mission_cfg.cargo,
        ending=world.trail_cfg.ending_image,
    )
    world.para()


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    opening_scene(world)
    threat_scene(world)
    mistake_scene(world)
    clue_scene(world)
    repair_scene(world)
    delivery_scene(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        (
            f"Tell a superhero story on a dusty forest trail where {world.hero_cfg.alias} must carry "
            f"{world.mission_cfg.cargo} to {world.mission_cfg.recipient}."
        ),
        (
            f"Include magical conflict with {world.threat_cfg.title}, a wrong first move, and a better solution "
            f"using {world.relic_cfg.label}."
        ),
        (
            f"End with a clear image that shows the forest trail is safe again near {world.trail_cfg.landmark}."
        ),
    ]


def _sentence_start(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _find_event(world: World, event: str) -> dict[str, str]:
    for row in world.history:
        if row["event"] == event:
            return row
    raise StoryError(f"Missing required world event: {event}")


def story_qa_rows(world: World) -> list[tuple[str, str]]:
    opening = _find_event(world, "opening")
    clue = _find_event(world, "clue_found")
    repaired = _find_event(world, "trail_repaired")
    delivered = _find_event(world, "delivery_complete")
    return [
        (
            f"Why was {world.hero_cfg.alias} walking on the dusty forest trail?",
            (
                f"{world.hero_cfg.alias} was carrying {world.mission_cfg.cargo} to {world.mission_cfg.recipient}. "
                f"{_sentence_start(world.mission_cfg.reason)}"
            ),
        ),
        (
            f"Why did the hero's first attack fail against {world.threat_cfg.title}?",
            (
                f"The first attack failed because {world.threat_cfg.title} {world.threat_cfg.copula} not looking for a fight. "
                f"The clue showed that it needed {world.threat_cfg.need_phrase}, so more force only made the trouble worse."
            ),
        ),
        (
            f"How did {world.hero_cfg.alias} fix the conflict on the forest trail?",
            (
                f"{world.hero_cfg.alias} stopped rushing, listened to {world.companion_cfg.name}, and used {world.relic_cfg.label}. "
                f"That magic matched the guardian's need, so the trail opened and the mission could continue."
            ),
        ),
        (
            "What changed by the end of the story?",
            (
                f"By the end, {world.mission_cfg.cargo} had been delivered and the trail was safe again. "
                f"{world.trail_cfg.ending_image}"
            ),
        ),
    ]


def world_qa_rows(world: World) -> list[tuple[str, str]]:
    hero = world.get("hero")
    threat = world.get("threat")
    trail = world.get("trail")
    cargo = world.get("cargo")
    return [
        (
            f"What does {world.relic_cfg.label} do in this world?",
            (
                f"{world.relic_cfg.label[0].upper() + world.relic_cfg.label[1:]} creates {world.threat_cfg.need_phrase}. "
                f"It is the right kind of magic for calming {world.threat_cfg.title} without hurting it."
            ),
        ),
        (
            f"What lesson did {world.hero_cfg.alias} learn?",
            (
                f"{world.hero_cfg.alias} learned that bravery works best with patience and care. "
                f"The hero only solved the conflict after listening to the clue instead of showing off."
            ),
        ),
        (
            "How can you tell the ending is truly resolved?",
            (
                f"You can tell because the cargo was delivered and the trail's safety changed from blocked to open. "
                f"The final image also shows the dusty forest resting peacefully instead of fighting back."
            ),
        ),
        (
            f"Who helped the hero notice the real problem?",
            (
                f"{world.companion_cfg.name} the {world.companion_cfg.kind} helped the hero notice it. "
                f"{world.companion_cfg.name} pointed out the clue so the hero could understand what the guardian needed."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.trail not in TRAILS:
        raise StoryError(f"No story: unknown trail {params.trail!r}.")
    if params.hero not in HEROES:
        raise StoryError(f"No story: unknown hero {params.hero!r}.")
    if params.threat not in THREATS:
        raise StoryError(f"No story: unknown threat {params.threat!r}.")
    if params.relic not in RELICS:
        raise StoryError(f"No story: unknown relic {params.relic!r}.")
    if params.companion not in COMPANIONS:
        raise StoryError(f"No story: unknown companion {params.companion!r}.")
    if params.mission not in MISSIONS:
        raise StoryError(f"No story: unknown mission {params.mission!r}.")
    if not valid_combo(params.trail, params.threat, params.relic):
        raise StoryError(invalid_reason(params.trail, params.threat, params.relic))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.story_text(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question, answer) for question, answer in story_qa_rows(world)],
        world_qa=[QAItem(question, answer) for question, answer in world_qa_rows(world)],
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
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError(f"Story sample is missing prompts or QA for combo {combo}.")
        if sample.world is None:
            raise StoryError(f"Story sample lost its world model for combo {combo}.")
        trail = sample.world.get("trail")
        cargo = sample.world.get("cargo")
        threat = sample.world.get("threat")
        hero = sample.world.get("hero")
        if trail.meter("safe") != 1 or trail.meter("blocked") != 0:
            raise StoryError(f"Trail did not resolve cleanly for combo {combo}.")
        if cargo.meter("delivered") != 1:
            raise StoryError(f"Cargo was not delivered for combo {combo}.")
        if threat.meter("calm") < 1 or hero.meter("mistake") != 1:
            raise StoryError(f"Expected turn structure missing for combo {combo}.")
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


def emit(sample: StorySample, args: argparse.Namespace, header: str | None = None) -> None:
    if args.json:
        print(sample.to_json())
        return
    if header:
        print(header)
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
                    header=(
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
            emit(sample, args, header=f"### variant {index + 1}" if count > 1 and not args.json else None)
            if index != count - 1 and not args.json:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
