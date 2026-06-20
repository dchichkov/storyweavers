#!/usr/bin/env python3
"""
Dusty forest trail superhero storyworld.

A small classical simulation for child-facing superhero stories set on a dusty
forest trail. The world models one young hero, one magical conflict, and one
state-driven resolution that proves the trail changed.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STORYWORLDS = Path(__file__).resolve().parents[1]
for base in (ROOT, STORYWORLDS):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


SOURCE_TALE = (
    "A child superhero patrols a dusty forest trail and finds a magical creature "
    "blocking the path with dust and fear. Instead of charging in blindly, the "
    "hero uses the right power and the right helper object to protect the trail, "
    "understand the creature's motive, and clear the way. The ending image shows "
    "the trail bright, breathable, and safe again."
)


@dataclass(frozen=True)
class Trail:
    key: str
    phrase: str
    landmark: str
    width_m: float
    base_visibility_m: float
    dust_depth_cm: float
    forbidden_powers: tuple[str, ...]
    witness: str
    ending_image: str


@dataclass(frozen=True)
class Threat:
    key: str
    phrase: str
    action: str
    motive: str
    required_power_tags: tuple[str, ...]
    required_artifact_tags: tuple[str, ...]
    blocked_span_m: float
    dust_boost_m: float
    fear_target: str
    peace_action: str


@dataclass(frozen=True)
class Power:
    key: str
    phrase: str
    tags: tuple[str, ...]
    action_text: str
    visual_text: str
    finish_text: str


@dataclass(frozen=True)
class Artifact:
    key: str
    phrase: str
    tags: tuple[str, ...]
    use_text: str
    support_text: str


@dataclass(frozen=True)
class HeroSpec:
    name: str
    title: str
    gender: str


@dataclass
class StoryParams:
    trail: str
    threat: str
    power: str
    artifact: str
    hero: str
    title: str
    gender: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    state: dict[str, str] = field(default_factory=dict)


@dataclass
class World:
    params: StoryParams
    trail: Trail
    threat: Threat
    power: Power
    artifact: Artifact
    hero: HeroSpec
    entities: dict[str, Entity] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)
    lesson: str = ""
    final_image: str = ""
    story: str = ""

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  source_tale={SOURCE_TALE}")
        lines.append(f"  trail={self.trail.key}")
        lines.append(f"  threat={self.threat.key}")
        lines.append(f"  power={self.power.key}")
        lines.append(f"  artifact={self.artifact.key}")
        lines.append(f"  hero={self.hero.name}/{self.hero.title}")
        for key in sorted(self.entities):
            ent = self.entities[key]
            lines.append(f"  [{key}] {ent.name} ({ent.kind})")
            if ent.meters:
                meters = ", ".join(f"{k}={v:.2f}" for k, v in sorted(ent.meters.items()))
                lines.append(f"    meters: {meters}")
            if ent.memes:
                memes = ", ".join(f"{k}={v:.2f}" for k, v in sorted(ent.memes.items()))
                lines.append(f"    memes: {memes}")
            if ent.state:
                state = ", ".join(f"{k}={v}" for k, v in sorted(ent.state.items()))
                lines.append(f"    state: {state}")
        lines.append(f"  events: {', '.join(self.events) if self.events else 'none'}")
        lines.append(f"  lesson: {self.lesson}")
        lines.append(f"  final_image: {self.final_image}")
        return "\n".join(lines)


TRAILS: dict[str, Trail] = {
    "ember_pines": Trail(
        key="ember_pines",
        phrase="a dusty forest trail curling between ember-barked pines",
        landmark="a fallen cedar arch",
        width_m=2.4,
        base_visibility_m=10.0,
        dust_depth_cm=5.0,
        forbidden_powers=(),
        witness="three field mice huddled under the cedar arch",
        ending_image="clear paw prints crossed the bright dirt beside the cedar arch",
    ),
    "root_bridge": Trail(
        key="root_bridge",
        phrase="a dusty forest trail crossing a knuckled root bridge",
        landmark="a creek whispering below the roots",
        width_m=1.8,
        base_visibility_m=9.0,
        dust_depth_cm=4.0,
        forbidden_powers=("root_reach",),
        witness="a young fawn frozen beside the bridge rail of roots",
        ending_image="the root bridge showed clean boards of bark and the creek flashed silver below",
    ),
    "lantern_glen": Trail(
        key="lantern_glen",
        phrase="a dusty forest trail lit by blue lantern mushrooms",
        landmark="a ring of glowing caps",
        width_m=2.9,
        base_visibility_m=11.0,
        dust_depth_cm=6.0,
        forbidden_powers=("sun_shield",),
        witness="two rabbits blinking beside the lantern mushrooms",
        ending_image="the lantern mushrooms glowed softly through calm air and the trail looked easy to follow",
    ),
}


THREATS: dict[str, Threat] = {
    "dust_imp": Threat(
        key="dust_imp",
        phrase="a dust imp spinning brown clouds over the path",
        action="kept snatching the brass trail bell and hiding it inside its dust spiral",
        motive="it thought every loud footstep meant someone had come to chase it away",
        required_power_tags=("rain", "light"),
        required_artifact_tags=("cleanse", "herd"),
        blocked_span_m=5.0,
        dust_boost_m=6.0,
        fear_target="small animals near the bell post",
        peace_action="returned the bell to its post and let the path breathe again",
    ),
    "bramble_guardian": Threat(
        key="bramble_guardian",
        phrase="a bramble guardian stomping thorny vines across the trail",
        action="wove a spiky wall from root to root and would not let anyone pass",
        motive="it was trying to protect a robin nest but could not tell friends from foes",
        required_power_tags=("root", "shield"),
        required_artifact_tags=("map", "cleanse"),
        blocked_span_m=7.0,
        dust_boost_m=4.0,
        fear_target="travelers and nesting birds on both sides of the path",
        peace_action="lifted the thorn wall aside after the nest was made safe",
    ),
    "eclipse_moths": Threat(
        key="eclipse_moths",
        phrase="an eclipse moth swarm throwing silver grit through the air",
        action="whirled glittering dust in front of every glow on the trail until no one could see clearly",
        motive="the moths were dazzled and confused by too many lights at once",
        required_power_tags=("light", "rain"),
        required_artifact_tags=("focus", "herd"),
        blocked_span_m=4.0,
        dust_boost_m=7.0,
        fear_target="night creatures trying to cross the trail",
        peace_action="settled on high branches once the light was guided away from the path",
    ),
}


POWERS: dict[str, Power] = {
    "rain_call": Power(
        key="rain_call",
        phrase="a rain-call spell woven from the hero's silver cape",
        tags=("rain", "calm"),
        action_text="lifted both hands and called a soft ribbon of rain across the trail",
        visual_text="The rain darkened the dust, lowered the scratchy air, and turned the magic swirl into something the hero could finally face.",
        finish_text="With the dust settled, the hero could speak clearly and solve the real problem instead of fighting a cloud.",
    ),
    "sun_shield": Power(
        key="sun_shield",
        phrase="a sun-shield burst that opened like a golden umbrella",
        tags=("light", "shield"),
        action_text="snapped open a bright shield over the trail",
        visual_text="The shield held the grit away from frightened eyes and drew a clean circle in the messy air.",
        finish_text="Behind that shield, everyone had room to breathe, listen, and choose a gentler ending.",
    ),
    "root_reach": Power(
        key="root_reach",
        phrase="a root-reach spell that asked the forest floor for help",
        tags=("root", "steady"),
        action_text="pressed one palm to the earth and asked the roots to move with care",
        visual_text="Patient roots slid under the dust and lifted the trail into neat, safe lines.",
        finish_text="The moving roots turned a rough standoff into a careful path the hero could shape without harm.",
    ),
}


ARTIFACTS: dict[str, Artifact] = {
    "brook_charm": Artifact(
        key="brook_charm",
        phrase="a brook charm shaped like a blue pebble",
        tags=("cleanse", "cool"),
        use_text="The brook charm opened with a cool splash and painted wet lines across the danger.",
        support_text="That clean water showed where the dust was thickest and where gentle help had to go first.",
    ),
    "compass_acorn": Artifact(
        key="compass_acorn",
        phrase="a compass acorn with a tiny glowing needle",
        tags=("map", "focus"),
        use_text="The compass acorn spun once, then pointed exactly where the trail and the frightened creature both needed care.",
        support_text="Instead of guessing, the hero could aim the rescue at the true problem hiding inside the mess.",
    ),
    "owl_whistle": Artifact(
        key="owl_whistle",
        phrase="an owl whistle carved from pale wood",
        tags=("herd", "focus"),
        use_text="The owl whistle sent one clear note through the dusty trees.",
        support_text="That note gathered nervous animals to the safe edge of the trail and stopped panic from spreading.",
    ),
}


HEROES: dict[str, tuple[HeroSpec, ...]] = {
    "girl": (
        HeroSpec("Mira", "Trailglow", "girl"),
        HeroSpec("Nia", "Pineflare", "girl"),
        HeroSpec("Tessa", "Mossbeam", "girl"),
    ),
    "boy": (
        HeroSpec("Leo", "Branchguard", "boy"),
        HeroSpec("Ivo", "Dustlight", "boy"),
        HeroSpec("Ren", "Creekflash", "boy"),
    ),
}


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def _tags_match(have: tuple[str, ...], need_any: tuple[str, ...]) -> bool:
    return any(tag in have for tag in need_any)


def power_fits(trail: Trail, threat: Threat, power: Power) -> bool:
    if power.key in trail.forbidden_powers:
        return False
    return _tags_match(power.tags, threat.required_power_tags)


def artifact_fits(threat: Threat, artifact: Artifact) -> bool:
    return _tags_match(artifact.tags, threat.required_artifact_tags)


def valid_combo(trail_key: str, threat_key: str, power_key: str, artifact_key: str) -> bool:
    if trail_key not in TRAILS or threat_key not in THREATS or power_key not in POWERS or artifact_key not in ARTIFACTS:
        return False
    trail = TRAILS[trail_key]
    threat = THREATS[threat_key]
    power = POWERS[power_key]
    artifact = ARTIFACTS[artifact_key]
    return power_fits(trail, threat, power) and artifact_fits(threat, artifact)


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for trail_key in sorted(TRAILS):
        for threat_key in sorted(THREATS):
            for power_key in sorted(POWERS):
                for artifact_key in sorted(ARTIFACTS):
                    if valid_combo(trail_key, threat_key, power_key, artifact_key):
                        combos.append((trail_key, threat_key, power_key, artifact_key))
    return combos


def describe_rejection(trail_key: str, threat_key: str, power_key: str, artifact_key: str) -> str:
    if trail_key not in TRAILS:
        return f"No story: unknown trail {trail_key!r}."
    if threat_key not in THREATS:
        return f"No story: unknown threat {threat_key!r}."
    if power_key not in POWERS:
        return f"No story: unknown power {power_key!r}."
    if artifact_key not in ARTIFACTS:
        return f"No story: unknown artifact {artifact_key!r}."
    trail = TRAILS[trail_key]
    threat = THREATS[threat_key]
    power = POWERS[power_key]
    artifact = ARTIFACTS[artifact_key]
    if power.key in trail.forbidden_powers:
        return (
            f"No story: {power.phrase} is too unstable on {trail.phrase}, "
            f"so {trail.landmark} would turn the rescue reckless."
        )
    if not _tags_match(power.tags, threat.required_power_tags):
        needed = " or ".join(threat.required_power_tags)
        return (
            f"No story: {power.phrase} does not answer {threat.phrase}. "
            f"This conflict needs magic with {needed} strength."
        )
    if not _tags_match(artifact.tags, threat.required_artifact_tags):
        needed = " or ".join(threat.required_artifact_tags)
        return (
            f"No story: {artifact.phrase} does not support this rescue. "
            f"The hero needs an artifact with {needed} help."
        )
    return "No story: this superhero setup is not reasonable in the dusty forest."


def _pick_hero(gender: str, rng: random.Random) -> HeroSpec:
    return rng.choice(HEROES[gender])


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.trail, params.threat, params.power, params.artifact):
        raise StoryError(describe_rejection(params.trail, params.threat, params.power, params.artifact))

    trail = TRAILS[params.trail]
    threat = THREATS[params.threat]
    power = POWERS[params.power]
    artifact = ARTIFACTS[params.artifact]
    hero = HeroSpec(params.hero, params.title, params.gender)

    visibility_before = max(2.5, trail.base_visibility_m - threat.dust_boost_m)
    trail_entity = Entity(
        name="forest trail",
        kind="place",
        meters={
            "width_m": trail.width_m,
            "dust_depth_cm": trail.dust_depth_cm,
            "visibility_m": visibility_before,
            "blocked_span_m": threat.blocked_span_m,
        },
        memes={"calm": 0.22, "hope": 0.31},
        state={"landmark": trail.landmark, "air": "dusty", "status": "blocked"},
    )
    hero_entity = Entity(
        name=hero.name,
        kind="hero",
        meters={"distance_to_conflict_m": 6.0, "cape_glow_m": 1.5},
        memes={"courage": 0.72, "care": 0.87, "doubt": 0.34, "focus": 0.48},
        state={"title": hero.title, "stance": "ready", "plan": "observe before acting"},
    )
    threat_entity = Entity(
        name=threat.phrase,
        kind="threat",
        meters={"dust_cloud_m": threat.dust_boost_m, "blocked_span_m": threat.blocked_span_m},
        memes={"fear": 0.68, "anger": 0.74, "trust": 0.12},
        state={"goal": threat.motive, "status": "active"},
    )
    artifact_entity = Entity(
        name=artifact.phrase,
        kind="artifact",
        meters={"charge": 1.0},
        memes={"promise": 0.55},
        state={"status": "ready"},
    )

    world = World(
        params=params,
        trail=trail,
        threat=threat,
        power=power,
        artifact=artifact,
        hero=hero,
        entities={
            "trail": trail_entity,
            "hero": hero_entity,
            "threat": threat_entity,
            "artifact": artifact_entity,
        },
    )
    world.events.append("source-tale-instantiated")
    world.events.append("dusty-forest-trail-threatened")
    return world


def _turn_reason(world: World) -> str:
    hero = world.entities["hero"]
    if hero.memes["care"] > hero.memes["doubt"]:
        return "Because protecting others mattered more than looking flashy, the hero stopped to read the danger first."
    return "The hero paused long enough to notice what the trail needed."


def _resolution_line(world: World) -> str:
    if "rain" in world.power.tags:
        return "The softened air let the frightened magic creature hear a calm voice instead of another threat."
    if "light" in world.power.tags:
        return "The bright shelter made room for listening, which turned the conflict from panic into a choice."
    return "The careful moving roots changed the ground itself, which turned a fight into a safe path."


def simulate(world: World) -> None:
    trail = world.entities["trail"]
    hero = world.entities["hero"]
    threat = world.entities["threat"]
    artifact = world.entities["artifact"]

    world.events.append("hero-spots-conflict")
    world.events.append("hero-chooses-care-over-rush")

    hero.memes["doubt"] = max(0.08, hero.memes["doubt"] - 0.18)
    hero.memes["focus"] = min(1.0, hero.memes["focus"] + 0.34)
    artifact.meters["charge"] = 0.62
    artifact.state["status"] = "used"
    world.events.append(f"artifact:{world.artifact.key}")

    threat.meters["dust_cloud_m"] = max(0.6, threat.meters["dust_cloud_m"] - 3.5)
    trail.meters["visibility_m"] = min(18.0, trail.meters["visibility_m"] + 5.0)
    world.events.append(f"power:{world.power.key}")

    threat.memes["anger"] = max(0.14, threat.memes["anger"] - 0.42)
    threat.memes["fear"] = max(0.18, threat.memes["fear"] - 0.33)
    threat.memes["trust"] = min(0.92, threat.memes["trust"] + 0.56)
    trail.meters["blocked_span_m"] = 0.0
    trail.state["status"] = "open"
    trail.state["air"] = "clear"
    trail.memes["calm"] = 0.86
    trail.memes["hope"] = 0.91
    threat.state["status"] = "peaceful"
    hero.state["stance"] = "gentle victory"
    hero.meters["distance_to_conflict_m"] = 1.2

    world.lesson = (
        "A real superhero does not win by charging at the loudest problem. "
        "A real superhero notices who is scared, uses the right kind of magic, and leaves the place safer than before."
    )
    world.final_image = world.trail.ending_image
    world.events.append("trail-reopened")


def _opening(world: World, subject: str, possessive: str) -> list[str]:
    hero = world.hero
    trail = world.trail
    return [
        f"{hero.name}, the young superhero called {hero.title}, hurried along {trail.phrase} just as the afternoon dust began to glow.",
        f"{possessive.capitalize()} silver boots tapped past {trail.landmark}, and {trail.witness} made {hero.name} look up at once.",
        f"The path should have felt ordinary and safe, but the air was scratchy enough to make every breath sound worried.",
    ]


def _conflict(world: World, subject: str) -> list[str]:
    threat = world.threat
    hero = world.hero.name
    return [
        f"Right ahead stood {threat.phrase}, and it {threat.action}.",
        f"In only a moment, {threat.blocked_span_m:.0f} meters of trail disappeared behind dust, and {threat.fear_target} had nowhere easy to go.",
        f"{hero} felt the urge to dash straight in, but {subject} knew that a superhero who could not see clearly might scare the frightened creatures even more.",
    ]


def _turn(world: World, subject: str, possessive: str) -> list[str]:
    hero = world.hero.name
    threat = world.threat
    return [
        _turn_reason(world),
        f"{hero} reached for {world.artifact.phrase}. {world.artifact.use_text}",
        f"{world.artifact.support_text} Then {subject} {world.power.action_text}.",
        f"{world.power.visual_text} {world.power.finish_text}",
        f"When the noise dropped, {hero} finally understood the truth: {threat.motive}.",
    ]


def _ending(world: World, subject: str, possessive: str) -> list[str]:
    hero = world.hero.name
    return [
        f"{_resolution_line(world)} Then the creature {world.threat.peace_action}.",
        f"Soon {world.final_image}, and {hero} could hear easy footsteps instead of frightened scrambling.",
        f"{world.lesson}",
    ]


def _format_story(world: World) -> str:
    subject, possessive, object_pronoun = _pronouns(world.hero.gender)
    parts = [
        " ".join(_opening(world, subject, possessive)),
        " ".join(_conflict(world, subject)),
        " ".join(_turn(world, subject, possessive)),
        " ".join(_ending(world, subject, possessive)),
    ]
    return "\n\n".join(parts)


def _prompt_lines(world: World) -> list[str]:
    return [
        "Write a superhero story for children set on a dusty forest trail.",
        f"Use magic and conflict with {world.threat.phrase}, plus {world.power.phrase} and {world.artifact.phrase}.",
        f"End with a clear image that proves the trail changed near {world.trail.landmark}.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    return [
        QAItem(
            "Who was the hero, and where did the problem happen?",
            f"The hero was {hero.name}, a young superhero called {hero.title}. The problem happened on {world.trail.phrase}, near {world.trail.landmark}.",
        ),
        QAItem(
            "What made the trail dangerous at the start?",
            f"{world.threat.phrase.capitalize()} blocked about {world.threat.blocked_span_m:.0f} meters of trail with magic dust and confusion. That trapped {world.threat.fear_target} in a place where clear walking and clear seeing both became hard.",
        ),
        QAItem(
            "Why did the hero stop instead of rushing straight into the conflict?",
            f"{hero.name} saw that the dust hid the real problem and that frightened creatures were already nearby. Stopping to understand the danger kept the rescue from becoming another scare.",
        ),
        QAItem(
            "How did the artifact help the rescue?",
            f"{world.artifact.use_text} {world.artifact.support_text}",
        ),
        QAItem(
            "How did the magic power change the middle of the story?",
            f"{hero.name} used {world.power.phrase} when the conflict was at its worst. {world.power.visual_text} {world.power.finish_text}",
        ),
        QAItem(
            "What proved the trail was truly safe again at the end?",
            f"The ending image showed that {world.final_image}. That picture matters because it proves the air cleared and ordinary life could return to the path.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why can magic dust turn a forest trail into a real problem?",
            "Magic dust can hide the ground, shorten visibility, and frighten animals all at once. On a trail, that means a small magical mess can quickly become a blocked path and a rescue problem.",
        ),
        QAItem(
            "What makes a superhero response kind instead of reckless?",
            "A kind superhero protects the scared beings in the scene before showing off power. That usually means slowing down, reading the danger, and choosing a tool that lowers panic instead of raising it.",
        ),
        QAItem(
            "Why pair a power with a helper object in a rescue story?",
            "The power changes the big physical problem, but the helper object makes the action precise. Together they let the hero solve the danger without turning the whole place into a bigger fight.",
        ),
        QAItem(
            "What is a strong final image for a child-facing conflict story?",
            "A strong final image shows the setting working normally again, such as clear footprints, calm air, or animals moving safely. That concrete picture proves the change better than a vague sentence about everything being fine.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
    world.story = _format_story(world)
    return StorySample(
        params=params,
        story=world.story,
        prompts=_prompt_lines(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts"]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.extend(["", "== (2) Story questions"])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== (3) World-knowledge questions"])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dusty forest trail superhero storyworld.")
    parser.add_argument("--trail", choices=sorted(TRAILS))
    parser.add_argument("--threat", choices=sorted(THREATS))
    parser.add_argument("--power", choices=sorted(POWERS))
    parser.add_argument("--artifact", choices=sorted(ARTIFACTS))
    parser.add_argument("--hero")
    parser.add_argument("--title")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="list valid combinations from clingo")
    parser.add_argument("--verify", action="store_true", help="check ASP/Python parity and exercise generated stories")
    parser.add_argument("--show-asp", action="store_true", help="print the ASP rules and emitted facts")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.trail is None or combo[0] == args.trail)
        and (args.threat is None or combo[1] == args.threat)
        and (args.power is None or combo[2] == args.power)
        and (args.artifact is None or combo[3] == args.artifact)
    ]
    if not combos:
        raise StoryError(
            describe_rejection(
                args.trail or "ember_pines",
                args.threat or "dust_imp",
                args.power or "rain_call",
                args.artifact or "brook_charm",
            )
        )

    trail_key, threat_key, power_key, artifact_key = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HEROES))
    chosen = _pick_hero(gender, rng)
    hero_name = args.hero or chosen.name
    hero_title = args.title or chosen.title
    return StoryParams(
        trail=trail_key,
        threat=threat_key,
        power=power_key,
        artifact=artifact_key,
        hero=hero_name,
        title=hero_title,
        gender=gender,
        seed=(args.seed or 1000) + index,
    )


ASP_RULES = r"""
trail(T) :- trail_site(T).
threat(X) :- threat_kind(X).
power(P) :- power_kind(P).
artifact(A) :- artifact_kind(A).

power_answers(TX,P) :- threat_need_power(TX,Tag), power_tag(P,Tag).
artifact_answers(TX,A) :- threat_need_artifact(TX,Tag), artifact_tag(A,Tag).

invalid(T,TX,P,A) :- trail(T), threat(TX), power(P), artifact(A), trail_forbid_power(T,P).
invalid(T,TX,P,A) :- trail(T), threat(TX), power(P), artifact(A), not power_answers(TX,P).
invalid(T,TX,P,A) :- trail(T), threat(TX), power(P), artifact(A), not artifact_answers(TX,A).

valid(T,TX,P,A) :- trail(T), threat(TX), power(P), artifact(A), not invalid(T,TX,P,A).

#show valid/4.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for trail in TRAILS.values():
        rows.append(asp.fact("trail_site", trail.key))
        rows.append(asp.fact("trail_phrase", trail.key, trail.phrase))
        rows.append(asp.fact("trail_landmark", trail.key, trail.landmark))
        for power_key in trail.forbidden_powers:
            rows.append(asp.fact("trail_forbid_power", trail.key, power_key))
    for threat in THREATS.values():
        rows.append(asp.fact("threat_kind", threat.key))
        rows.append(asp.fact("threat_phrase", threat.key, threat.phrase))
        for tag in threat.required_power_tags:
            rows.append(asp.fact("threat_need_power", threat.key, tag))
        for tag in threat.required_artifact_tags:
            rows.append(asp.fact("threat_need_artifact", threat.key, tag))
    for power in POWERS.values():
        rows.append(asp.fact("power_kind", power.key))
        for tag in power.tags:
            rows.append(asp.fact("power_tag", power.key, tag))
    for artifact in ARTIFACTS.values():
        rows.append(asp.fact("artifact_kind", artifact.key))
        for tag in artifact.tags:
            rows.append(asp.fact("artifact_tag", artifact.key, tag))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> list[tuple[str, str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if python_set != asp_set:
        print("ASP/Python mismatch:")
        if python_set - asp_set:
            print("  only in Python:", sorted(python_set - asp_set))
        if asp_set - python_set:
            print("  only in ASP:", sorted(asp_set - python_set))
        return 1

    exercised = 0
    for index, combo in enumerate(sorted(python_set), start=1):
        params = StoryParams(
            trail=combo[0],
            threat=combo[1],
            power=combo[2],
            artifact=combo[3],
            hero="Mira",
            title="Trailglow",
            gender="girl",
            seed=10_000 + index,
        )
        sample = generate(params)
        if not sample.story.strip():
            print("Verification failed: generated empty story for", combo)
            return 1
        if not sample.story_qa or not sample.world_qa:
            print("Verification failed: missing QA for", combo)
            return 1
        if "{" in sample.story or "}" in sample.story:
            print("Verification failed: unresolved template text for", combo)
            return 1
        exercised += 1

    print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    print(f"OK: exercised generation for {exercised} valid dusty-forest superhero stories.")
    return 0


def _emit_variants(samples: list[StorySample], args: argparse.Namespace) -> None:
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = (
                f"### trail={p.trail} threat={p.threat} power={p.power} "
                f"artifact={p.artifact} hero={p.hero}/{p.title}"
            )
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed or 7
    hero = args.hero or "Mira"
    title = args.title or "Trailglow"
    gender = args.gender or "girl"
    samples: list[StorySample] = []
    for index, combo in enumerate(valid_combos(), start=1):
        params = StoryParams(
            trail=combo[0],
            threat=combo[1],
            power=combo[2],
            artifact=combo[3],
            hero=hero,
            title=title,
            gender=gender,
            seed=base_seed + index,
        )
        samples.append(generate(params))
    return samples


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    samples: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)

    try:
        if args.all:
            samples = _sample_all(args)
        else:
            seen: set[str] = set()
            i = 0
            while len(samples) < args.n and i < args.n * 80:
                params = resolve_params(args, random.Random(base_seed + i), index=i)
                sample = generate(params)
                i += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) < args.n:
                raise StoryError("Could not generate enough unique stories with this constraint set.")

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        _emit_variants(samples, args)
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
