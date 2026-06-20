#!/usr/bin/env python3
"""
dusty_forest_forest_trail_magic_conflict_superhero_5.py
=======================================================

A TinyStories-style StoryWorld for this seed:

    words: dusty forest
    setting: forest trail
    features: Magic, Conflict
    style: Superhero Story

Internal source tale:
A young superhero races along a dusty forest trail with an urgent delivery.
A magical guardian mistakes the hero for a threat and seals the trail. The hero
tries a flashy power first and makes the danger worse. A helper spots the real
cause of the guardian's fear, and the hero changes from force to care. The hero
uses the right magic to heal what was wrong, calms the guardian, and finishes
the mission with a final image that proves the trail is safe again.
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
class TrailZone:
    key: str
    phrase: str
    marker: str
    dust_tone: str
    closing_image: str
    guardians: tuple[str, ...]


@dataclass(frozen=True)
class Hero:
    key: str
    civilian_name: str
    hero_name: str
    subject: str
    object: str
    possessive: str
    costume: str
    entrance_line: str
    rash_move: str
    gentler_method: str


@dataclass(frozen=True)
class Guardian:
    key: str
    title: str
    entrance: str
    barrier: str
    wound_clue: str
    fear_reason: str
    backlash: str
    needs_power: str
    needs_phrase: str
    healing_result: str
    ending_pose: str


@dataclass(frozen=True)
class Charm:
    key: str
    name: str
    power: str
    activation: str


@dataclass(frozen=True)
class Helper:
    key: str
    name: str
    kind: str
    warning: str
    action: str


@dataclass(frozen=True)
class Errand:
    key: str
    item: str
    recipient: str
    need_line: str
    delivery_result: str


@dataclass
class StoryParams:
    trail: str
    hero: str
    guardian: str
    charm: str
    helper: str
    errand: str
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
    trail_cfg: TrailZone
    hero_cfg: Hero
    guardian_cfg: Guardian
    charm_cfg: Charm
    helper_cfg: Helper
    errand_cfg: Errand
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
            tags = ", ".join(f"{k}={v}" for k, v in sorted(entity.tags.items()))
            meters = ", ".join(f"{k}={v}" for k, v in sorted(entity.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(entity.memes.items()))
            tail_parts = []
            if tags:
                tail_parts.append(tags)
            if meters:
                tail_parts.append(f"meters[{meters}]")
            if memes:
                tail_parts.append(f"memes[{memes}]")
            tail = f" {'; '.join(tail_parts)}" if tail_parts else ""
            rows.append(f"  {entity_id:<10} ({entity.kind:<10}) @ {entity.location}{tail}")
        rows.append(f"  fired rules: {', '.join(self.fired_rules) if self.fired_rules else '(none)'}")
        rows.append(f"  history events: {[row['event'] for row in self.history]}")
        return "\n".join(rows)


TRAILS: dict[str, TrailZone] = {
    "root_lantern_curve": TrailZone(
        key="root_lantern_curve",
        phrase="the root-lantern curve of the dusty forest trail",
        marker="a crooked lantern post wrapped in roots",
        dust_tone="bronze",
        closing_image="Bronze dust lay flat around the lantern post, and children could see the whole forest trail curling safely home.",
        guardians=("ash_manticore", "briar_colossus"),
    ),
    "moss_step_rise": TrailZone(
        key="moss_step_rise",
        phrase="the moss-step rise on the dusty forest trail",
        marker="a line of flat stepping stones",
        dust_tone="gold",
        closing_image="Gold dust rested in tidy lines beside the stepping stones, and the rise looked friendly instead of fierce.",
        guardians=("ash_manticore", "mirror_owl_swarm"),
    ),
    "hollow_arch_bend": TrailZone(
        key="hollow_arch_bend",
        phrase="the hollow-arch bend of the dusty forest trail",
        marker="a hollow tree arch with carved stars",
        dust_tone="silver",
        closing_image="Silver dust glowed under the hollow arch, and the bend shone like a promise that the way ahead was clear.",
        guardians=("briar_colossus", "mirror_owl_swarm"),
    ),
}

HEROES: dict[str, Hero] = {
    "ember_glade": Hero(
        key="ember_glade",
        civilian_name="Nia",
        hero_name="Ember Glade",
        subject="she",
        object="her",
        possessive="her",
        costume="a flame-bright cape with green leaf stitching",
        entrance_line="Nia skipped over the roots and left tiny sparks twinkling in the dust behind her boots.",
        rash_move="She snapped both hands forward and blasted a wheel of fire at the danger.",
        gentler_method="slow breaths and careful promises",
    ),
    "moss_comet": Hero(
        key="moss_comet",
        civilian_name="Jules",
        hero_name="Moss Comet",
        subject="he",
        object="him",
        possessive="his",
        costume="a dark green jacket with a comet stitched across the front",
        entrance_line="Jules dashed from stump to stump until his boots flashed at the edge of the trail.",
        rash_move="He lunged in with a bright comet punch before he understood the danger.",
        gentler_method="a calm voice and steady hands",
    ),
    "trail_lumen": Hero(
        key="trail_lumen",
        civilian_name="Rin",
        hero_name="Trail Lumen",
        subject="they",
        object="them",
        possessive="their",
        costume="a yellow scarf and a bark-bright shield on their back",
        entrance_line="Rin strode up the path with a steady glow under their boots and their scarf lifting like a banner.",
        rash_move="They slammed a burst of hard light into the trouble to force it aside.",
        gentler_method="patient courage and listening first",
    ),
}

GUARDIANS: dict[str, Guardian] = {
    "ash_manticore": Guardian(
        key="ash_manticore",
        title="the Ash Manticore",
        entrance="a huge lion-shaped cloud of ash leaped from the brush and landed across the trail",
        barrier="Its tail swept up a spinning wall of dust so thick the next turn vanished.",
        wound_clue="Under one smoky paw, a blue ember thorn hissed and would not go out.",
        fear_reason="it thought anyone rushing closer would drive the ember deeper",
        backlash="The dust wall roared higher, and the manticore's claws bit angry lines into the ground.",
        needs_power="cooling_mist",
        needs_phrase="a cooling mist spell",
        healing_result="The blue ember thorn dimmed, the manticore shook out a slow breath, and the wall of ash dropped back to the ground.",
        ending_pose="The Ash Manticore curled beside the path like a great sleepy cat guarding friends instead of blocking them.",
    ),
    "briar_colossus": Guardian(
        key="briar_colossus",
        title="the Briar Colossus",
        entrance="a giant of thorny vines rose from the roots and spread its arms across the trail",
        barrier="Briar ropes tied themselves from tree to tree until the whole path looked stitched shut.",
        wound_clue="A cracked moon seed glowed in its wooden chest and made every vine twitch with pain.",
        fear_reason="it thought strangers had come to break the seed open completely",
        backlash="More thorns burst out, and the stitched-up trail pulled even tighter.",
        needs_power="mending_light",
        needs_phrase="a warm mending light",
        healing_result="The cracked moon seed sealed with a soft glow, and the briar ropes loosened until the path breathed open again.",
        ending_pose="The Briar Colossus stood beside the bend like a living gate, strong but no longer angry.",
    ),
    "mirror_owl_swarm": Guardian(
        key="mirror_owl_swarm",
        title="the Mirror Owl Swarm",
        entrance="a whirl of silver owls burst from the branches and spun shining wings across the trail",
        barrier="Every flap threw back false footsteps, so the path echoed with tricks and confusion.",
        wound_clue="One little glass feather was cracked, and every owl kept circling it in panic.",
        fear_reason="they thought a fast-moving stranger would shatter the feather forever",
        backlash="The echoes grew louder, and the spinning wings boxed the hero in tighter.",
        needs_power="true_chime",
        needs_phrase="a clear true-chime",
        healing_result="The cracked feather rang with one clean note, and the silver owls settled into a quiet circle above the trail.",
        ending_pose="The Mirror Owl Swarm perched overhead like a row of silver lanterns, watchful and calm.",
    ),
}

CHARMS: dict[str, Charm] = {
    "mist_band": Charm(
        key="mist_band",
        name="the Mist Band",
        power="cooling_mist",
        activation="Cool silver mist poured from the band and wrapped the hurt place without a single harsh spark.",
    ),
    "sun_thread": Charm(
        key="sun_thread",
        name="the Sun Thread",
        power="mending_light",
        activation="Golden thread-light streamed from the charm and stitched the damage together with gentle warmth.",
    ),
    "bell_seed": Charm(
        key="bell_seed",
        name="the Bell Seed",
        power="true_chime",
        activation="A bright note rang from the tiny seed and held still in the dusty air like a line to follow.",
    ),
}

HELPERS: dict[str, Helper] = {
    "fern_kit": Helper(
        key="fern_kit",
        name="Timo",
        kind="fern kit",
        warning="Heroes are strongest when they notice what hurts before they start punching.",
        action="Timo brushed dust away with his tail until the real clue showed through.",
    ),
    "brook_pixie": Helper(
        key="brook_pixie",
        name="Vale",
        kind="brook pixie",
        warning="Listen to the trail first. It is trying to explain the fight to you.",
        action="Vale flicked clear drops across the ground so the clue shone sharply in the light.",
    ),
    "lantern_beetle": Helper(
        key="lantern_beetle",
        name="Pip",
        kind="lantern beetle",
        warning="Big light is not the same as the right light.",
        action="Pip circled the clue with a soft yellow glow until the hero could not miss it.",
    ),
}

ERRANDS: dict[str, Errand] = {
    "healing_tea": Errand(
        key="healing_tea",
        item="a kettle of cedar-bark healing tea",
        recipient="Grandma Iri",
        need_line="Grandma Iri was waiting at the trail cabin with a cold and needed the warm tea before sundown.",
        delivery_result="Grandma Iri held the warm cup in both hands and smiled as the steam curled around her scarf.",
    ),
    "spark_lanterns": Errand(
        key="spark_lanterns",
        item="a bundle of spark lanterns",
        recipient="the night class at Fern School",
        need_line="the night class at Fern School needed the lanterns before the woods lesson began.",
        delivery_result="The children at Fern School hung the lanterns in a row, and their lesson glowed with small brave stars.",
    ),
    "spring_map": Errand(
        key="spring_map",
        item="a folded map of the hidden spring",
        recipient="Ranger Olan",
        need_line="Ranger Olan needed the map so families could be guided to cool water before dark.",
        delivery_result="Ranger Olan spread the map on a stump and traced a safe water route for every family nearby.",
    ),
}


def valid_combo(trail: str, guardian: str, charm: str) -> bool:
    return guardian in TRAILS[trail].guardians and GUARDIANS[guardian].needs_power == CHARMS[charm].power


def invalid_reason(trail: str, guardian: str, charm: str) -> str:
    if guardian not in TRAILS[trail].guardians:
        return f"No story: {GUARDIANS[guardian].title} does not belong on {TRAILS[trail].phrase}."
    if GUARDIANS[guardian].needs_power != CHARMS[charm].power:
        return (
            f"No story: {CHARMS[charm].name} cannot calm {GUARDIANS[guardian].title}; "
            f"it needs {GUARDIANS[guardian].needs_phrase}."
        )
    return "No story: that combination is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    combos: list[tuple[str, str, str, str, str, str]] = []
    for trail in sorted(TRAILS):
        for hero in sorted(HEROES):
            for guardian in sorted(GUARDIANS):
                for charm in sorted(CHARMS):
                    if not valid_combo(trail, guardian, charm):
                        continue
                    for helper in sorted(HELPERS):
                        for errand in sorted(ERRANDS):
                            combos.append((trail, hero, guardian, charm, helper, errand))
    return combos


def setup_world(params: StoryParams) -> World:
    world = World(
        params=params,
        trail_cfg=TRAILS[params.trail],
        hero_cfg=HEROES[params.hero],
        guardian_cfg=GUARDIANS[params.guardian],
        charm_cfg=CHARMS[params.charm],
        helper_cfg=HELPERS[params.helper],
        errand_cfg=ERRANDS[params.errand],
    )
    world.add(
        "trail",
        Entity(
            name=world.trail_cfg.phrase,
            kind="trail",
            location=world.trail_cfg.marker,
            tags={"marker": world.trail_cfg.marker, "dust_tone": world.trail_cfg.dust_tone},
            meters={"safe": 0, "blocked": 1, "dust": 4},
            memes={"hope": 0.2, "wonder": 0.3},
        ),
    )
    world.add(
        "hero",
        Entity(
            name=world.hero_cfg.hero_name,
            kind="hero",
            location=world.trail_cfg.phrase,
            tags={"civilian": world.hero_cfg.civilian_name, "costume": world.hero_cfg.costume},
            meters={"energy": 5, "humility": 1, "mistake": 0},
            memes={"courage": 0.8, "care": 0.4, "restraint": 0.2},
        ),
    )
    world.add(
        "guardian",
        Entity(
            name=world.guardian_cfg.title,
            kind="guardian",
            location=world.trail_cfg.phrase,
            tags={"needs_power": world.guardian_cfg.needs_power},
            meters={"alarm": 4, "trust": 0},
            memes={"fear": 0.7, "pain": 0.7},
        ),
    )
    world.add(
        "charm",
        Entity(
            name=world.charm_cfg.name,
            kind="charm",
            location=world.trail_cfg.phrase,
            tags={"power": world.charm_cfg.power},
            meters={"charge": 3},
            memes={"magic": 0.8},
        ),
    )
    world.add(
        "helper",
        Entity(
            name=world.helper_cfg.name,
            kind="helper",
            location=world.trail_cfg.phrase,
            tags={"kind": world.helper_cfg.kind},
            meters={"focus": 4},
            memes={"trust": 0.7},
        ),
    )
    world.add(
        "errand",
        Entity(
            name=world.errand_cfg.item,
            kind="errand",
            location=world.trail_cfg.phrase,
            tags={"recipient": world.errand_cfg.recipient},
            meters={"secure": 3, "delivered": 0},
            memes={"care": 0.9},
        ),
    )
    return world


def opening_scene(world: World) -> None:
    hero = world.hero_cfg
    errand = world.errand_cfg
    world.say(
        f"{hero.civilian_name}, known in that moment as {hero.hero_name}, hurried along {world.trail_cfg.phrase} in {hero.costume}."
    )
    world.say(hero.entrance_line)
    world.say(
        f"{hero.subject.capitalize()} carried {errand.item} close to {hero.possessive} chest, because {errand.need_line}"
    )
    world.note(
        "opening",
        hero=hero.hero_name,
        errand=errand.item,
        recipient=errand.recipient,
        trail=world.trail_cfg.key,
    )
    world.para()


def guardian_scene(world: World) -> None:
    trail = world.get("trail")
    world.say(f"Near {world.trail_cfg.marker}, {world.guardian_cfg.entrance}.")
    world.say(world.guardian_cfg.barrier)
    world.say(
        f"The dusty forest trembled, and {world.trail_cfg.dust_tone} dust swirled so hard that even superhero eyes could barely see through it."
    )
    trail.set_meter("blocked", 2)
    trail.set_meter("safe", 0)
    trail.add_meter("dust", 2)
    world.get("guardian").add_meme("fear", 0.2)
    world.get("hero").add_meme("courage", 0.1)
    world.note("guardian_blocks_trail", guardian=world.guardian_cfg.key, marker=world.trail_cfg.marker)
    world.para()


def mistake_scene(world: World) -> None:
    hero = world.get("hero")
    guardian = world.get("guardian")
    errand = world.get("errand")
    trail = world.get("trail")
    world.say(f"{world.hero_cfg.rash_move} {world.guardian_cfg.backlash}")
    world.say(
        f"The blast did not help. It only made {world.guardian_cfg.title} more frightened, and {world.errand_cfg.item} nearly slipped from the hero's arms."
    )
    hero.set_meter("mistake", 1)
    hero.add_meter("energy", -1)
    hero.add_meter("humility", -1)
    hero.add_meme("restraint", -0.1)
    hero.add_meme("care", -0.1)
    guardian.add_meter("alarm", 2)
    guardian.add_meme("pain", 0.1)
    errand.add_meter("secure", -1)
    trail.add_meter("dust", 1)
    world.note("rash_magic_fails", move=world.hero_cfg.rash_move, guardian=world.guardian_cfg.key)
    world.para()


def clue_scene(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(f"Then {world.helper_cfg.name} the {world.helper_cfg.kind} called, \"{world.helper_cfg.warning}\"")
    world.say(world.helper_cfg.action)
    world.say(world.guardian_cfg.wound_clue)
    world.say(
        f"{world.hero_cfg.civilian_name} finally understood that {world.guardian_cfg.title} was not wicked at all. {world.guardian_cfg.fear_reason.capitalize()}."
    )
    helper.add_meme("trust", 0.1)
    hero.add_meter("humility", 2)
    hero.add_meme("care", 0.5)
    hero.add_meme("restraint", 0.6)
    world.fired_rules.append("clue_changes_plan")
    world.note("clue_revealed", clue=world.guardian_cfg.wound_clue, needs=world.guardian_cfg.needs_power)
    world.para()


def healing_scene(world: World) -> None:
    hero = world.get("hero")
    guardian = world.get("guardian")
    trail = world.get("trail")
    charm = world.get("charm")
    world.say(
        f"{world.hero_cfg.civilian_name} raised {world.charm_cfg.name} and chose {world.hero_cfg.gentler_method} instead of another attack."
    )
    world.say(world.charm_cfg.activation)
    world.say(world.guardian_cfg.healing_result)
    hero.add_meme("care", 0.5)
    hero.add_meme("restraint", 0.3)
    guardian.set_meter("alarm", 0)
    guardian.set_meter("trust", 4)
    guardian.add_meme("fear", -0.5)
    guardian.add_meme("pain", -0.5)
    charm.add_meter("charge", -1)
    trail.set_meter("blocked", 0)
    trail.set_meter("safe", 1)
    trail.set_meter("dust", max(1, trail.meter("dust") - 3))
    trail.add_meme("hope", 0.5)
    world.fired_rules.append("right_magic_heals")
    world.note("guardian_healed", charm=world.charm_cfg.key, guardian=world.guardian_cfg.key)
    world.para()


def ending_scene(world: World) -> None:
    hero = world.get("hero")
    errand = world.get("errand")
    trail = world.get("trail")
    world.say(
        f"With the way open, {world.hero_cfg.hero_name} hurried onward and delivered {world.errand_cfg.item} to {world.errand_cfg.recipient}."
    )
    world.say(world.errand_cfg.delivery_result)
    world.say(world.guardian_cfg.ending_pose)
    world.say(world.trail_cfg.closing_image)
    hero.add_meme("courage", 0.1)
    hero.add_meme("care", 0.2)
    errand.set_meter("delivered", 1)
    errand.set_meter("secure", max(1, errand.meter("secure")))
    trail.add_meme("wonder", 0.3)
    world.note(
        "delivery_done",
        item=world.errand_cfg.item,
        recipient=world.errand_cfg.recipient,
        image=world.trail_cfg.closing_image,
    )
    world.para()


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    opening_scene(world)
    guardian_scene(world)
    mistake_scene(world)
    clue_scene(world)
    healing_scene(world)
    ending_scene(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        (
            f"Write a superhero story set on a dusty forest trail where {world.hero_cfg.hero_name} must deliver "
            f"{world.errand_cfg.item} to {world.errand_cfg.recipient}."
        ),
        (
            f"Include magical conflict with {world.guardian_cfg.title}, a wrong first use of power, and a better fix using {world.charm_cfg.name}."
        ),
        (
            f"End with a concrete image near {world.trail_cfg.marker} that proves the forest trail is safe again."
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
    _find_event(world, "opening")
    _find_event(world, "clue_revealed")
    _find_event(world, "guardian_healed")
    _find_event(world, "delivery_done")
    return [
        (
            f"Why was {world.hero_cfg.hero_name} on the dusty forest trail?",
            (
                f"{world.hero_cfg.hero_name} was hurrying to bring {world.errand_cfg.item} to {world.errand_cfg.recipient}. "
                f"{_sentence_start(world.errand_cfg.need_line)}"
            ),
        ),
        (
            f"Why did the first attack make the conflict worse?",
            (
                f"The first attack made the conflict worse because {world.guardian_cfg.title} was already scared and hurt. "
                f"The flashy blast made the guardian think the hero was another danger instead of someone who could help."
            ),
        ),
        (
            f"What clue helped the hero understand the real problem?",
            (
                f"The clue was this: {world.guardian_cfg.wound_clue} "
                f"That showed the guardian needed {world.guardian_cfg.needs_phrase}, not a fight."
            ),
        ),
        (
            "How was the trail finally made safe again?",
            (
                f"The hero used {world.charm_cfg.name} with care and healed what was hurting the guardian. "
                f"Once the pain was gone, the guardian lowered the barrier and the mission could continue."
            ),
        ),
    ]


def world_qa_rows(world: World) -> list[tuple[str, str]]:
    trail = world.get("trail")
    guardian = world.get("guardian")
    hero = world.get("hero")
    errand = world.get("errand")
    return [
        (
            f"What kind of magic does {world.charm_cfg.name} use?",
            (
                f"{_sentence_start(world.charm_cfg.name)} uses {world.guardian_cfg.needs_phrase}. "
                f"It is useful in this world because it repairs the real hurt instead of simply pushing danger away."
            ),
        ),
        (
            f"What lesson did {world.hero_cfg.hero_name} learn?",
            (
                f"{world.hero_cfg.hero_name} learned that strength needs care and attention. "
                f"The hero only won after slowing down, noticing the clue, and choosing the right magic for the problem."
            ),
        ),
        (
            "How can you tell the ending is truly resolved?",
            (
                f"You can tell because the errand was delivered and the trail changed from blocked to safe. "
                f"The guardian is calm at the end, and the final image shows the dust settling instead of attacking."
            ),
        ),
        (
            f"Who helped the hero turn the story around?",
            (
                f"{world.helper_cfg.name} the {world.helper_cfg.kind} helped the hero turn it around. "
                f"{world.helper_cfg.name} pointed out the clue that explained why the guardian was fighting."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.trail not in TRAILS:
        raise StoryError(f"No story: unknown trail {params.trail!r}.")
    if params.hero not in HEROES:
        raise StoryError(f"No story: unknown hero {params.hero!r}.")
    if params.guardian not in GUARDIANS:
        raise StoryError(f"No story: unknown guardian {params.guardian!r}.")
    if params.charm not in CHARMS:
        raise StoryError(f"No story: unknown charm {params.charm!r}.")
    if params.helper not in HELPERS:
        raise StoryError(f"No story: unknown helper {params.helper!r}.")
    if params.errand not in ERRANDS:
        raise StoryError(f"No story: unknown errand {params.errand!r}.")
    if not valid_combo(params.trail, params.guardian, params.charm):
        raise StoryError(invalid_reason(params.trail, params.guardian, params.charm))
    world = tell(params)
    return StorySample(
        params=params,
        story=world.story_text(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_rows(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_qa_rows(world)],
        world=world,
    )


ASP_RULES = r"""
combo(T,H,G,C,U,E) :-
    trail(T),
    hero(H),
    guardian(G),
    charm(C),
    helper(U),
    errand(E),
    supports(T,G),
    guardian_need(G,N),
    charm_power(C,N).

ok :- chosen(T,H,G,C,U,E), combo(T,H,G,C,U,E).

#show combo/6.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for key, trail in sorted(TRAILS.items()):
        rows.append(fact("trail", key))
        for guardian in trail.guardians:
            rows.append(fact("supports", key, guardian))
    for key in sorted(HEROES):
        rows.append(fact("hero", key))
    for key, guardian in sorted(GUARDIANS.items()):
        rows.append(fact("guardian", key))
        rows.append(fact("guardian_need", key, guardian.needs_power))
    for key, charm in sorted(CHARMS.items()):
        rows.append(fact("charm", key))
        rows.append(fact("charm_power", key, charm.power))
    for key in sorted(HELPERS):
        rows.append(fact("helper", key))
    for key in sorted(ERRANDS):
        rows.append(fact("errand", key))
    if params is not None:
        rows.append(
            fact(
                "chosen",
                params.trail,
                params.hero,
                params.guardian,
                params.charm,
                params.helper,
                params.errand,
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
        raise StoryError(f"ASP/Python mismatch. only_python={sorted(py - asp)} only_asp={sorted(asp - py)}")
    for index, combo in enumerate(sorted(py), 1):
        params = StoryParams(
            trail=combo[0],
            hero=combo[1],
            guardian=combo[2],
            charm=combo[3],
            helper=combo[4],
            errand=combo[5],
            seed=index,
        )
        sample = generate(params)
        if "dusty forest" not in sample.story or "forest trail" not in sample.story:
            raise StoryError(f"Story text lost the requested seed language for combo {combo}.")
        if not sample.prompts or not sample.story_qa or not sample.world_qa:
            raise StoryError(f"Story sample is missing prompts or QA for combo {combo}.")
        if sample.world is None:
            raise StoryError(f"Story sample lost its world model for combo {combo}.")
        trail = sample.world.get("trail")
        guardian = sample.world.get("guardian")
        hero = sample.world.get("hero")
        errand = sample.world.get("errand")
        if trail.meter("safe") != 1 or trail.meter("blocked") != 0:
            raise StoryError(f"Trail did not resolve cleanly for combo {combo}.")
        if guardian.meter("trust") < 1 or guardian.meter("alarm") != 0:
            raise StoryError(f"Guardian did not calm correctly for combo {combo}.")
        if errand.meter("delivered") != 1 or hero.meter("mistake") != 1:
            raise StoryError(f"Expected turn structure missing for combo {combo}.")
        if not asp_verify(params):
            raise StoryError(f"Chosen combo did not satisfy ASP verification: {combo}")
    return f"OK: clingo gate matches Python and {len(py)} valid stories execute with resolved endings."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate dusty forest superhero storyworld samples.")
    parser.add_argument("--trail", choices=sorted(TRAILS))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--guardian", choices=sorted(GUARDIANS))
    parser.add_argument("--charm", choices=sorted(CHARMS))
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("--errand", choices=sorted(ERRANDS))
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
        guardian=combo[2],
        charm=combo[3],
        helper=combo[4],
        errand=combo[5],
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None, index: int = 0) -> StoryParams:
    rng = rng or random.Random(args.seed + index)
    if any([args.trail, args.hero, args.guardian, args.charm, args.helper, args.errand]):
        trail = args.trail or rng.choice(sorted(TRAILS))
        hero = args.hero or rng.choice(sorted(HEROES))
        guardian = args.guardian or rng.choice(sorted(GUARDIANS))
        charm = args.charm or rng.choice(sorted(CHARMS))
        helper = args.helper or rng.choice(sorted(HELPERS))
        errand = args.errand or rng.choice(sorted(ERRANDS))
        if not valid_combo(trail, guardian, charm):
            raise StoryError(invalid_reason(trail, guardian, charm))
        return StoryParams(
            trail=trail,
            hero=hero,
            guardian=guardian,
            charm=charm,
            helper=helper,
            errand=errand,
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
                        f"### {sample.params.hero} / {sample.params.guardian} / "
                        f"{sample.params.charm} / {sample.params.errand}"
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
