#!/usr/bin/env python3
"""
dusty_forest_forest_trail_magic_conflict_superhero_6.py
=======================================================

A TinyStories-style StoryWorld for this seed:

    words: dusty forest
    setting: forest trail
    features: Magic, Conflict
    style: Superhero Story

Internal source tale:
On a dusty forest trail, a child superhero hurries to deliver healing supplies.
A magical trail warden mistakes the fast-moving hero for a threat and seals the
path with stormy dust. The hero tries a bold superhero blast first, which makes
the conflict worse. A helper reveals the warden's hidden hurt, and the hero
changes from force to care. With the right magic, the hero heals the hurt,
opens the trail, and reaches the waiting family, while the last image shows the
forest itself resting safely again.
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
    closing_image: str
    wardens: tuple[str, ...]


@dataclass(frozen=True)
class Hero:
    key: str
    child_name: str
    hero_name: str
    subject: str
    object: str
    possessive: str
    costume: str
    arrival_line: str
    rash_move: str
    gentle_style: str


@dataclass(frozen=True)
class Warden:
    key: str
    title: str
    entrance: str
    barrier: str
    hidden_hurt: str
    fear_reason: str
    backlash: str
    needed_power: str
    needed_phrase: str
    healing_result: str
    ending_pose: str


@dataclass(frozen=True)
class Relic:
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
    reveal_action: str


@dataclass(frozen=True)
class Mission:
    key: str
    package: str
    recipient: str
    need_line: str
    delivery_result: str


@dataclass
class StoryParams:
    trail: str
    hero: str
    warden: str
    relic: str
    helper: str
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
    hero_cfg: Hero
    warden_cfg: Warden
    relic_cfg: Relic
    helper_cfg: Helper
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


TRAILS: dict[str, Trail] = {
    "switchback_stones": Trail(
        key="switchback_stones",
        phrase="the switchback stones of the dusty forest trail",
        landmark="a row of flat stones beside a split cedar stump",
        dust_color="amber",
        closing_image="Amber dust rested in still rings around the split cedar stump, and the trail looked gentle enough for little boots again.",
        wardens=("dust_dragon", "root_guardian"),
    ),
    "fern_hollow": Trail(
        key="fern_hollow",
        phrase="the fern hollow on the dusty forest trail",
        landmark="a bent arch of fern stems over the path",
        dust_color="gold",
        closing_image="Gold dust slept softly under the fern arch, and the bend shone like a quiet promise that the way home was safe.",
        wardens=("dust_dragon", "lantern_stag"),
    ),
    "star_log_curve": Trail(
        key="star_log_curve",
        phrase="the star-log curve of the dusty forest trail",
        landmark="a fallen log painted with old star marks",
        dust_color="silver",
        closing_image="Silver dust settled along the star-marked log, and the curve no longer looked fierce at all.",
        wardens=("root_guardian", "lantern_stag"),
    ),
}

HEROES: dict[str, Hero] = {
    "nova_fern": Hero(
        key="nova_fern",
        child_name="Lia",
        hero_name="Nova Fern",
        subject="she",
        object="her",
        possessive="her",
        costume="a bright green cape with a silver leaf clasp",
        arrival_line="Lia hurried between the roots so lightly that tiny sparks skipped over the dust behind her boots.",
        rash_move="She thrust both hands forward and sent a bright burst of hero light at the trouble.",
        gentle_style="slow breaths and careful promises",
    ),
    "cedar_flash": Hero(
        key="cedar_flash",
        child_name="Omar",
        hero_name="Cedar Flash",
        subject="he",
        object="him",
        possessive="his",
        costume="a red scarf and bark-brown gloves that glimmered at the seams",
        arrival_line="Omar bounded from root to root with the quick steps that made everyone call him Cedar Flash.",
        rash_move="He leaped first and struck the danger with a crackling superhero dash.",
        gentle_style="steady hands and a calm voice",
    ),
    "trail_star": Hero(
        key="trail_star",
        child_name="Paz",
        hero_name="Trail Star",
        subject="they",
        object="them",
        possessive="their",
        costume="a yellow hood and a round shield painted like a sunrise",
        arrival_line="Paz strode up the path with a warm glow under their shoes and their yellow hood fluttering like a banner.",
        rash_move="They flung a hard star-shield flash to shove the conflict out of the way.",
        gentle_style="patient listening and brave kindness",
    ),
}

WARDENS: dict[str, Warden] = {
    "dust_dragon": Warden(
        key="dust_dragon",
        title="the Dust Dragon",
        entrance="a long dragon made of swirling leaves and dust uncoiled across the path",
        barrier="Its wings beat up a dusty wall so thick the next turn vanished behind it.",
        hidden_hurt="One wing held a burning burr that glowed blue and made the whole dragon flinch.",
        fear_reason="it thought a rushing stranger would drive the burning burr deeper into its wing",
        backlash="The wall of dust climbed higher, and the dragon's tail lashed worried circles through the air.",
        needed_power="cool_mist",
        needed_phrase="a cool mist spell",
        healing_result="The blue burr dimmed under the cool magic, the dragon folded its sore wing, and the dust wall sighed back to the ground.",
        ending_pose="The Dust Dragon curled beside the trail like a great sleepy kite, guarding the path without blocking it.",
    ),
    "root_guardian": Warden(
        key="root_guardian",
        title="the Root Guardian",
        entrance="a giant wooden keeper pushed up from the roots and spread broad arms over the trail",
        barrier="Thick roots stitched themselves across the path until the whole trail looked tied shut.",
        hidden_hurt="A cracked acorn heart pulsed in its chest, and every cracked line made the roots jerk with pain.",
        fear_reason="it thought any fast hero had come to smash the cracked acorn heart the rest of the way open",
        backlash="More roots snapped out of the ground, and the stitched trail pulled even tighter.",
        needed_power="mending_glow",
        needed_phrase="a warm mending glow",
        healing_result="The cracked acorn heart sealed with a honey-colored shine, and the roots slowly untied themselves from the path.",
        ending_pose="The Root Guardian rested one hand beside the trail like a living gate, strong and peaceful now.",
    ),
    "lantern_stag": Warden(
        key="lantern_stag",
        title="the Lantern Stag",
        entrance="a tall stag with branch antlers stepped from the brush and filled the trail with shaking golden light",
        barrier="Its antlers cast spinning lantern-rings that trapped the path inside bright, confusing circles.",
        hidden_hurt="One lantern hanging from its antlers was cracked, and each shake of light made the stag wince.",
        fear_reason="it thought a loud stranger would shatter the cracked lantern and darken the whole trail",
        backlash="The lantern-rings spun faster, and bright shadows hopped over every stone.",
        needed_power="true_song",
        needed_phrase="a clear true-song",
        healing_result="The cracked lantern answered the true-song with one clean note, and the circling rings melted into a warm path of light.",
        ending_pose="The Lantern Stag stood beside the path with calm antlers lifted high, lighting the way instead of trapping it.",
    ),
}

RELICS: dict[str, Relic] = {
    "mist_orb": Relic(
        key="mist_orb",
        name="the Mist Orb",
        power="cool_mist",
        activation="Cool silver mist poured from the orb and wrapped the hurt place without a single harsh spark.",
    ),
    "sun_ribbon": Relic(
        key="sun_ribbon",
        name="the Sun Ribbon",
        power="mending_glow",
        activation="Golden thread-light streamed from the ribbon and stitched the damage together with gentle warmth.",
    ),
    "echo_seed": Relic(
        key="echo_seed",
        name="the Echo Seed",
        power="true_song",
        activation="A bright steady note rang from the little seed and held in the air like a kind hand showing the way.",
    ),
}

HELPERS: dict[str, Helper] = {
    "moss_squirrel": Helper(
        key="moss_squirrel",
        name="Tavi",
        kind="moss squirrel",
        warning="Fast feet are useful, but gentle eyes find the real hurt first.",
        reveal_action="Tavi brushed the dust aside with a fern tail until the hidden hurt showed clearly.",
    ),
    "brook_sprite": Helper(
        key="brook_sprite",
        name="Nim",
        kind="brook sprite",
        warning="The trail is not only shouting. It is also trying to explain itself.",
        reveal_action="Nim flicked tiny drops through the dust so the wounded place gleamed in the light.",
    ),
    "glow_moth": Helper(
        key="glow_moth",
        name="Pip",
        kind="glow moth",
        warning="Big magic is not always the right magic.",
        reveal_action="Pip circled the hurt with a soft gold glow until the hero could not miss it.",
    ),
}

MISSIONS: dict[str, Mission] = {
    "bandage_bundle": Mission(
        key="bandage_bundle",
        package="a bundle of moon-leaf bandages",
        recipient="Ranger Sol",
        need_line="Ranger Sol needed the bandages before sunset so scraped hikers could be helped at once.",
        delivery_result="Ranger Sol tied the moon-leaf bandages to a rail post and smiled because the next hurt child would not have to wait.",
    ),
    "rain_tea": Mission(
        key="rain_tea",
        package="a kettle of rainmint tea",
        recipient="Grandma Yara",
        need_line="Grandma Yara was waiting at her trail cabin with a sore throat and needed the warm tea before the evening chill came down.",
        delivery_result="Grandma Yara held the warm cup in both hands while minty steam curled around her smile.",
    ),
    "spark_lanterns": Mission(
        key="spark_lanterns",
        package="a stack of spark lanterns",
        recipient="the dusk class at Pine Path School",
        need_line="the dusk class at Pine Path School needed the lanterns before their forest lesson began.",
        delivery_result="The children at Pine Path School hung the lanterns in a row, and their lesson glowed with brave little stars.",
    ),
}


def valid_combo(trail: str, warden: str, relic: str) -> bool:
    return warden in TRAILS[trail].wardens and WARDENS[warden].needed_power == RELICS[relic].power


def invalid_reason(trail: str, warden: str, relic: str) -> str:
    if warden not in TRAILS[trail].wardens:
        return f"No story: {WARDENS[warden].title} does not belong on {TRAILS[trail].phrase}."
    if WARDENS[warden].needed_power != RELICS[relic].power:
        return (
            f"No story: {RELICS[relic].name} cannot calm {WARDENS[warden].title}; "
            f"it needs {WARDENS[warden].needed_phrase}."
        )
    return "No story: that combination is not reasonable."


def valid_combos() -> list[tuple[str, str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str, str]] = []
    for trail in sorted(TRAILS):
        for hero in sorted(HEROES):
            for warden in sorted(WARDENS):
                for relic in sorted(RELICS):
                    if not valid_combo(trail, warden, relic):
                        continue
                    for helper in sorted(HELPERS):
                        for mission in sorted(MISSIONS):
                            rows.append((trail, hero, warden, relic, helper, mission))
    return rows


def filtered_combos(args: argparse.Namespace) -> list[tuple[str, str, str, str, str, str]]:
    rows = []
    for combo in valid_combos():
        if args.trail and combo[0] != args.trail:
            continue
        if args.hero and combo[1] != args.hero:
            continue
        if args.warden and combo[2] != args.warden:
            continue
        if args.relic and combo[3] != args.relic:
            continue
        if args.helper and combo[4] != args.helper:
            continue
        if args.mission and combo[5] != args.mission:
            continue
        rows.append(combo)
    return rows


def setup_world(params: StoryParams) -> World:
    world = World(
        params=params,
        trail_cfg=TRAILS[params.trail],
        hero_cfg=HEROES[params.hero],
        warden_cfg=WARDENS[params.warden],
        relic_cfg=RELICS[params.relic],
        helper_cfg=HELPERS[params.helper],
        mission_cfg=MISSIONS[params.mission],
    )
    world.add(
        "trail",
        Entity(
            name=world.trail_cfg.phrase,
            kind="trail",
            location=world.trail_cfg.landmark,
            tags={"landmark": world.trail_cfg.landmark, "dust_color": world.trail_cfg.dust_color},
            meters={"safe": 0, "blocked": 1, "dust": 3},
            memes={"wonder": 0.4, "hope": 0.2},
        ),
    )
    world.add(
        "hero",
        Entity(
            name=world.hero_cfg.hero_name,
            kind="hero",
            location=world.trail_cfg.phrase,
            tags={"child_name": world.hero_cfg.child_name, "costume": world.hero_cfg.costume},
            meters={"energy": 5, "patience": 1, "mistake": 0},
            memes={"courage": 0.8, "care": 0.4, "restraint": 0.2},
        ),
    )
    world.add(
        "warden",
        Entity(
            name=world.warden_cfg.title,
            kind="warden",
            location=world.trail_cfg.phrase,
            tags={"needed_power": world.warden_cfg.needed_power},
            meters={"alarm": 4, "trust": 0, "hurt": 3},
            memes={"fear": 0.8, "pain": 0.7},
        ),
    )
    world.add(
        "relic",
        Entity(
            name=world.relic_cfg.name,
            kind="relic",
            location=world.trail_cfg.phrase,
            tags={"power": world.relic_cfg.power},
            meters={"charge": 3},
            memes={"magic": 0.9},
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
            memes={"trust": 0.7, "care": 0.6},
        ),
    )
    world.add(
        "mission",
        Entity(
            name=world.mission_cfg.package,
            kind="mission",
            location=world.trail_cfg.phrase,
            tags={"recipient": world.mission_cfg.recipient},
            meters={"secure": 3, "delivered": 0},
            memes={"care": 0.9},
        ),
    )
    return world


def dust_mood(world: World) -> str:
    trail = world.get("trail")
    dust = trail.meter("dust")
    if dust >= 6:
        return f"{world.trail_cfg.dust_color.capitalize()} dust roared around the trees like a stormy cape."
    if dust >= 4:
        return f"{world.trail_cfg.dust_color.capitalize()} dust spun in jumpy circles over the path."
    return f"{world.trail_cfg.dust_color.capitalize()} dust rested softly around the roots."


def hero_turn_line(world: World) -> str:
    hero = world.get("hero")
    if hero.meme("care") >= 1.0 and hero.meter("patience") >= 3:
        return (
            f"{world.hero_cfg.child_name} understood that being a superhero did not mean hitting harder. "
            f"It meant noticing what hurt and helping it safely."
        )
    return (
        f"{world.hero_cfg.child_name} paused at last and tried to understand the trouble before racing at it again."
    )


def ending_image_line(world: World) -> str:
    trail = world.get("trail")
    warden = world.get("warden")
    if trail.meter("safe") == 1 and warden.meter("trust") >= 3:
        return world.trail_cfg.closing_image
    return "The trail was calmer than before, but the dust still looked uncertain."


def opening_scene(world: World) -> None:
    hero = world.hero_cfg
    mission = world.mission_cfg
    world.say(
        f"{hero.child_name}, known on rescue days as {hero.hero_name}, hurried along {world.trail_cfg.phrase} in {hero.costume}."
    )
    world.say(hero.arrival_line)
    world.say(
        f"{hero.subject.capitalize()} carried {mission.package} close to {hero.possessive} chest because {mission.need_line}"
    )
    world.note(
        "opening",
        hero=hero.hero_name,
        package=mission.package,
        recipient=mission.recipient,
        trail=world.trail_cfg.key,
    )
    world.para()


def conflict_scene(world: World) -> None:
    trail = world.get("trail")
    warden = world.get("warden")
    world.say(f"At {world.trail_cfg.landmark}, {world.warden_cfg.entrance}.")
    world.say(world.warden_cfg.barrier)
    trail.set_meter("blocked", 2)
    trail.add_meter("dust", 2)
    warden.add_meter("alarm", 1)
    warden.add_meme("fear", 0.2)
    world.say(dust_mood(world))
    world.note("warden_blocks_trail", warden=world.warden_cfg.key, landmark=world.trail_cfg.landmark)
    world.para()


def mistake_scene(world: World) -> None:
    hero = world.get("hero")
    warden = world.get("warden")
    mission = world.get("mission")
    trail = world.get("trail")
    world.say(f"{world.hero_cfg.rash_move} {world.warden_cfg.backlash}")
    world.say(
        f"The big move looked brave, but it did not help. It only made {world.warden_cfg.title} more frightened, and {world.mission_cfg.package} nearly slipped from the hero's arms."
    )
    hero.set_meter("mistake", 1)
    hero.add_meter("energy", -1)
    hero.add_meter("patience", -1)
    hero.add_meme("care", -0.1)
    hero.add_meme("restraint", -0.1)
    warden.add_meter("alarm", 2)
    warden.add_meter("hurt", 1)
    warden.add_meme("pain", 0.1)
    mission.add_meter("secure", -1)
    trail.add_meter("dust", 1)
    world.note("rash_move_fails", move=world.hero_cfg.rash_move, warden=world.warden_cfg.key)
    world.para()


def clue_scene(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    world.say(f"Then {world.helper_cfg.name} the {world.helper_cfg.kind} called, \"{world.helper_cfg.warning}\"")
    world.say(world.helper_cfg.reveal_action)
    world.say(world.warden_cfg.hidden_hurt)
    world.say(hero_turn_line(world))
    world.say(
        f"{world.hero_cfg.child_name} finally saw that {world.warden_cfg.title} was not being mean at all. {world.warden_cfg.fear_reason.capitalize()}."
    )
    hero.add_meter("patience", 3)
    hero.add_meme("care", 0.5)
    hero.add_meme("restraint", 0.6)
    helper.add_meme("trust", 0.1)
    world.fired_rules.append("clue_reframes_conflict")
    world.note("clue_revealed", hurt=world.warden_cfg.hidden_hurt, need=world.warden_cfg.needed_power)
    world.para()


def healing_scene(world: World) -> None:
    hero = world.get("hero")
    warden = world.get("warden")
    relic = world.get("relic")
    trail = world.get("trail")
    world.say(
        f"{world.hero_cfg.child_name} lifted {world.relic_cfg.name} and chose {world.hero_cfg.gentle_style} instead of another attack."
    )
    world.say(world.relic_cfg.activation)
    world.say(world.warden_cfg.healing_result)
    hero.add_meme("care", 0.5)
    hero.add_meme("restraint", 0.3)
    hero.add_meme("courage", 0.1)
    warden.set_meter("alarm", 0)
    warden.set_meter("trust", 4)
    warden.set_meter("hurt", 0)
    warden.add_meme("fear", -0.6)
    warden.add_meme("pain", -0.6)
    relic.add_meter("charge", -1)
    trail.set_meter("blocked", 0)
    trail.set_meter("safe", 1)
    trail.set_meter("dust", max(1, trail.meter("dust") - 4))
    trail.add_meme("hope", 0.5)
    trail.add_meme("wonder", 0.3)
    world.fired_rules.append("right_magic_heals")
    world.note("warden_healed", relic=world.relic_cfg.key, warden=world.warden_cfg.key)
    world.para()


def ending_scene(world: World) -> None:
    mission = world.get("mission")
    world.say(
        f"With the way open at last, {world.hero_cfg.hero_name} hurried on and delivered {world.mission_cfg.package} to {world.mission_cfg.recipient}."
    )
    world.say(world.mission_cfg.delivery_result)
    world.say(world.warden_cfg.ending_pose)
    world.say(ending_image_line(world))
    mission.set_meter("delivered", 1)
    mission.set_meter("secure", max(1, mission.meter("secure")))
    world.note(
        "mission_complete",
        package=world.mission_cfg.package,
        recipient=world.mission_cfg.recipient,
        ending=ending_image_line(world),
    )
    world.para()


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    opening_scene(world)
    conflict_scene(world)
    mistake_scene(world)
    clue_scene(world)
    healing_scene(world)
    ending_scene(world)
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        (
            f"Write a superhero story set on a dusty forest trail where {world.hero_cfg.hero_name} must deliver "
            f"{world.mission_cfg.package} to {world.mission_cfg.recipient}."
        ),
        (
            f"Include a magical conflict with {world.warden_cfg.title}, a wrong first move, and a better rescue using {world.relic_cfg.name}."
        ),
        (
            f"End with a concrete image near {world.trail_cfg.landmark} that proves the forest trail is safe again."
        ),
    ]


def _sentence_start(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def _require_event(world: World, event: str) -> dict[str, str]:
    for row in world.history:
        if row["event"] == event:
            return row
    raise StoryError(f"Missing required world event: {event}")


def story_qa_rows(world: World) -> list[tuple[str, str]]:
    _require_event(world, "opening")
    _require_event(world, "clue_revealed")
    _require_event(world, "warden_healed")
    _require_event(world, "mission_complete")
    return [
        (
            f"Why was {world.hero_cfg.hero_name} hurrying down the forest trail?",
            (
                f"{world.hero_cfg.hero_name} was hurrying because {world.hero_cfg.subject} needed to deliver {world.mission_cfg.package} to {world.mission_cfg.recipient}. "
                f"{_sentence_start(world.mission_cfg.need_line)}"
            ),
        ),
        (
            "Why did the first superhero attack make the conflict worse?",
            (
                f"The first attack made the conflict worse because {world.warden_cfg.title} was already scared and hurting. "
                f"The flashy move made the warden think the hero was another danger instead of someone who could help."
            ),
        ),
        (
            "What clue showed the hero what the real problem was?",
            (
                f"The clue was this: {world.warden_cfg.hidden_hurt} "
                f"That showed the hero the warden needed {world.warden_cfg.needed_phrase}, not a fight."
            ),
        ),
        (
            f"How did {world.hero_cfg.hero_name} finally make the trail safe again?",
            (
                f"{world.hero_cfg.hero_name} used {world.relic_cfg.name} gently and healed the hidden hurt instead of pushing harder. "
                f"Once the hurt was gone, the warden trusted the hero and opened the trail."
            ),
        ),
    ]


def world_qa_rows(world: World) -> list[tuple[str, str]]:
    trail = world.get("trail")
    hero = world.get("hero")
    warden = world.get("warden")
    mission = world.get("mission")
    return [
        (
            f"What kind of magic does {world.relic_cfg.name} use?",
            (
                f"{_sentence_start(world.relic_cfg.name)} uses {world.warden_cfg.needed_phrase}. "
                f"In this world, that magic helps because it repairs the true hurt instead of only forcing danger aside."
            ),
        ),
        (
            f"What lesson did {world.hero_cfg.hero_name} learn?",
            (
                f"{world.hero_cfg.hero_name} learned that real superhero strength needs care as well as courage. "
                f"The hero only solved the problem after slowing down, noticing the clue, and choosing the right magic."
            ),
        ),
        (
            "How can you tell the ending is fully resolved?",
            (
                "You can tell because the mission package was delivered, the warden's hidden hurt was healed, and the trail changed from blocked to safe. "
                f"The final image also shows the dust resting quietly instead of attacking the path."
            ),
        ),
        (
            f"Who helped turn the story around on {world.trail_cfg.phrase}?",
            (
                f"{world.helper_cfg.name} the {world.helper_cfg.kind} helped turn the story around. "
                f"{world.helper_cfg.name} revealed the hidden hurt, which gave {world.hero_cfg.hero_name} a way to help instead of fight."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.trail not in TRAILS:
        raise StoryError(f"No story: unknown trail {params.trail!r}.")
    if params.hero not in HEROES:
        raise StoryError(f"No story: unknown hero {params.hero!r}.")
    if params.warden not in WARDENS:
        raise StoryError(f"No story: unknown warden {params.warden!r}.")
    if params.relic not in RELICS:
        raise StoryError(f"No story: unknown relic {params.relic!r}.")
    if params.helper not in HELPERS:
        raise StoryError(f"No story: unknown helper {params.helper!r}.")
    if params.mission not in MISSIONS:
        raise StoryError(f"No story: unknown mission {params.mission!r}.")
    if not valid_combo(params.trail, params.warden, params.relic):
        raise StoryError(invalid_reason(params.trail, params.warden, params.relic))
    world = tell(params)
    story = world.story_text()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa_rows(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_qa_rows(world)],
        world=world,
    )


ASP_RULES = r"""
combo(T,H,W,R,U,M) :-
    trail(T),
    hero(H),
    warden(W),
    relic(R),
    helper(U),
    mission(M),
    supports(T,W),
    warden_need(W,N),
    relic_power(R,N).

ok :- chosen(T,H,W,R,U,M), combo(T,H,W,R,U,M).

#show combo/6.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for key, trail in sorted(TRAILS.items()):
        rows.append(fact("trail", key))
        for warden in trail.wardens:
            rows.append(fact("supports", key, warden))
    for key in sorted(HEROES):
        rows.append(fact("hero", key))
    for key, warden in sorted(WARDENS.items()):
        rows.append(fact("warden", key))
        rows.append(fact("warden_need", key, warden.needed_power))
    for key, relic in sorted(RELICS.items()):
        rows.append(fact("relic", key))
        rows.append(fact("relic_power", key, relic.power))
    for key in sorted(HELPERS):
        rows.append(fact("helper", key))
    for key in sorted(MISSIONS):
        rows.append(fact("mission", key))
    if params is not None:
        rows.append(
            fact(
                "chosen",
                params.trail,
                params.hero,
                params.warden,
                params.relic,
                params.helper,
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
        raise StoryError(f"ASP/Python mismatch. only_python={sorted(py - asp)} only_asp={sorted(asp - py)}")
    for index, combo in enumerate(sorted(py), 1):
        params = StoryParams(
            trail=combo[0],
            hero=combo[1],
            warden=combo[2],
            relic=combo[3],
            helper=combo[4],
            mission=combo[5],
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
        warden = sample.world.get("warden")
        mission = sample.world.get("mission")
        hero = sample.world.get("hero")
        if trail.meter("safe") != 1 or trail.meter("blocked") != 0:
            raise StoryError(f"Trail did not resolve cleanly for combo {combo}.")
        if warden.meter("trust") < 1 or warden.meter("alarm") != 0 or warden.meter("hurt") != 0:
            raise StoryError(f"Warden did not calm correctly for combo {combo}.")
        if mission.meter("delivered") != 1 or hero.meter("mistake") != 1:
            raise StoryError(f"Expected turn structure missing for combo {combo}.")
        if not asp_verify(params):
            raise StoryError(f"Chosen combo did not satisfy ASP verification: {combo}")
    return f"OK: clingo gate matches Python and {len(py)} valid stories execute with resolved endings."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate dusty forest superhero storyworld samples.")
    parser.add_argument("--trail", choices=sorted(TRAILS))
    parser.add_argument("--hero", choices=sorted(HEROES))
    parser.add_argument("--warden", choices=sorted(WARDENS))
    parser.add_argument("--relic", choices=sorted(RELICS))
    parser.add_argument("--helper", choices=sorted(HELPERS))
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
        warden=combo[2],
        relic=combo[3],
        helper=combo[4],
        mission=combo[5],
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random | None = None, index: int = 0) -> StoryParams:
    rng = rng or random.Random(args.seed + index)
    matches = filtered_combos(args)
    if matches:
        return _params_from_combo(rng.choice(matches), args.seed + index)
    if args.trail and args.warden and args.relic:
        raise StoryError(invalid_reason(args.trail, args.warden, args.relic))
    raise StoryError("No story: those requested options do not make a reasonable dusty forest superhero story.")


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
            combos = filtered_combos(args) if any(
                [args.trail, args.hero, args.warden, args.relic, args.helper, args.mission]
            ) else valid_combos()
            if not combos:
                raise StoryError("No story: no valid combinations matched the requested filters.")
            for idx, combo in enumerate(combos, 1):
                sample = generate(_params_from_combo(combo, args.seed + idx))
                emit(
                    sample,
                    args,
                    header=(
                        f"### {sample.params.hero} / {sample.params.warden} / "
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
        print(f"StoryError: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
