#!/usr/bin/env python3
"""
fluff_lesson_learned_surprise_adventure.py
==========================================

A small adventure storyworld built from this fixed source tale:

    A child explorer climbs a windy trail with a little pouch of dandelion
    fluff for reading the gusts. When the fluff gets loose, the child rushes
    into a trail mistake while a friend and guide quietly prepare a summit
    surprise. By slowing down, following grounded clues, and accepting help,
    the child reaches the reveal and learns that careful steps beat wild haste.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
STORYWORLDS = Path(__file__).resolve().parents[2]
for base in (ROOT, STORYWORLDS):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402

SOURCE_TALE = (
    "On a windy hill trail, a child carries a pouch of dandelion fluff to read "
    "the air like an explorer. A gust opens the pouch just as a friend and guide "
    "prepare a secret summit surprise. The child hurries, makes the trail harder, "
    "then learns to slow down, trust the clues, and finish the climb with wiser feet."
)

RIDGE_NAME = "Cloudstep Ridge"


@dataclass(frozen=True)
class Trail:
    key: str
    phrase: str
    intro_detail: str
    obstacle: str
    clue_route: str
    finish_spot: str
    reveal_spot: str
    adventure_name: str
    allowed_challenges: tuple[str, ...]
    supported_surprises: tuple[str, ...]
    gust_load: float


@dataclass(frozen=True)
class Challenge:
    key: str
    fluff_item: str
    trigger_line: str
    mistake_template: str
    clue_text: str
    clue_phrase: str
    search_goal: str
    lesson_template: str
    recovery_template: str
    allowed_surprises: tuple[str, ...]
    impatience_boost: float


@dataclass(frozen=True)
class Surprise:
    key: str
    phrase: str
    setup_template: str
    reveal_line_template: str
    ending_template: str
    afterglow: str
    wonder_boost: float


@dataclass
class StoryParams:
    trail: str
    challenge: str
    surprise: str
    hero: str
    gender: str
    friend: str
    guide: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    location: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    notes: dict[str, str] = field(default_factory=dict)


@dataclass
class Beat:
    stage: str
    location: str
    summary: str
    cause: str
    consequence: str


@dataclass
class World:
    params: StoryParams
    trail: Trail
    challenge: Challenge
    surprise: Surprise
    source_tale: str
    entities: dict[str, Entity] = field(default_factory=dict)
    beats: list[Beat] = field(default_factory=list)
    clue_found: str = ""
    challenge_seen: bool = False
    surprise_ready: bool = False
    lesson_learned: bool = False
    resolved: bool = False
    story: str = ""
    setup_phrase: str = ""
    reveal_line: str = ""
    mistake_text: str = ""
    lesson_text: str = ""
    recovery_text: str = ""
    final_image: str = ""
    tension_feeling: str = ""

    def hero(self) -> Entity:
        return self.entities["hero"]

    def friend(self) -> Entity:
        return self.entities["friend"]

    def guide(self) -> Entity:
        return self.entities["guide"]

    def pouch(self) -> Entity:
        return self.entities["pouch"]

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  ridge={RIDGE_NAME}")
        lines.append(f"  trail={self.trail.key}")
        lines.append(f"  challenge={self.challenge.key}")
        lines.append(f"  surprise={self.surprise.key}")
        lines.append(f"  challenge_seen={self.challenge_seen}")
        lines.append(f"  surprise_ready={self.surprise_ready}")
        lines.append(f"  lesson_learned={self.lesson_learned}")
        lines.append(f"  resolved={self.resolved}")
        lines.append(f"  clue_found={self.clue_found or 'none'}")
        lines.append(f"  lesson_text={self.lesson_text or 'none'}")
        for key, ent in self.entities.items():
            meters = ", ".join(f"{name}={value:.2f}" for name, value in sorted(ent.meters.items())) or "none"
            memes = ", ".join(f"{name}={value:.2f}" for name, value in sorted(ent.memes.items())) or "none"
            inventory = ", ".join(ent.inventory) if ent.inventory else "none"
            lines.append(f"  {key}: {ent.name} ({ent.kind}) @ {ent.location}")
            lines.append(f"    meters=[{meters}]")
            lines.append(f"    memes=[{memes}]")
            lines.append(f"    inventory=[{inventory}]")
        if self.beats:
            lines.append("  beats:")
            for beat in self.beats:
                lines.append(
                    f"    - {beat.stage} @ {beat.location}: {beat.summary} "
                    f"(cause={beat.cause}; consequence={beat.consequence})"
                )
        return "\n".join(lines)


TRAILS: dict[str, Trail] = {
    "rope_ridge": Trail(
        key="rope_ridge",
        phrase="Rope Ridge trail",
        intro_detail="blue rope markers, wind-bent grass, and flat stone arrows pointing uphill",
        obstacle="the swaying plank bridge",
        clue_route="the map post, the fence bend, and the lookout steps",
        finish_spot="the Eagle Lookout platform",
        reveal_spot="the bright canvas windbreak",
        adventure_name="a cliff-top expedition",
        allowed_challenges=("chase_gust", "skip_marker"),
        supported_surprises=("pennant_reveal", "summit_picnic"),
        gust_load=0.26,
    ),
    "fern_gully": Trail(
        key="fern_gully",
        phrase="Fern Gully trail",
        intro_detail="cool fern walls, drip-slick stones, and a rope rail beside a silver trickle",
        obstacle="the stepping stones over the silver trickle",
        clue_route="the fern tunnel, the pebble shelf, and the lantern nook",
        finish_spot="the Lantern Nook ledge",
        reveal_spot="the mossy lean-to",
        adventure_name="a hidden-gully expedition",
        allowed_challenges=("skip_marker", "hurry_alone"),
        supported_surprises=("summit_picnic", "sky_badge"),
        gust_load=0.22,
    ),
    "sun_arch": Trail(
        key="sun_arch",
        phrase="Sun Arch trail",
        intro_detail="gold grass, a tall stone arch, and bright flags ticking in the wind",
        obstacle="the echo arch climb",
        clue_route="the juniper bend, the stone arch shadow, and the bell stump",
        finish_spot="the Wind Bell stump",
        reveal_spot="the arch-side flag shelter",
        adventure_name="an archway quest",
        allowed_challenges=("chase_gust", "hurry_alone"),
        supported_surprises=("pennant_reveal", "sky_badge"),
        gust_load=0.31,
    ),
}

CHALLENGES: dict[str, Challenge] = {
    "chase_gust": Challenge(
        key="chase_gust",
        fluff_item="the little wind pouch full of dandelion fluff",
        trigger_line="A hard puff of wind flipped the pouch flap open.",
        mistake_template=(
            "{hero} ran after every flying bit of fluff instead of stopping to see "
            "where the strongest gust had really gone."
        ),
        clue_text="Most of the fluff had settled in a silver-white line beside the map post.",
        clue_phrase="a silver-white line of fluff beside the map post",
        search_goal="the map post",
        lesson_template=(
            "{hero} learned that quick feet can miss the truest clue, while calm eyes can read the whole trail."
        ),
        recovery_template=(
            "{friend} had already gathered the safest bits of fluff at the map post "
            "and tucked the pouch away before it could blow over the edge."
        ),
        allowed_surprises=("pennant_reveal", "summit_picnic"),
        impatience_boost=0.35,
    ),
    "skip_marker": Challenge(
        key="skip_marker",
        fluff_item="the little wind pouch full of dandelion fluff",
        trigger_line="A gust tugged the pouch loose and sent it skimming ahead of the markers.",
        mistake_template=(
            "{hero} hurried past the blue trail markers and picked a shortcut that only made the search longer."
        ),
        clue_text="A soft puff of fluff clung to the next blue marker under a fern leaf.",
        clue_phrase="a puff of fluff clinging to the next blue marker",
        search_goal="the next blue marker",
        lesson_template="{hero} learned that trail markers are tiny helpers, not slow-down signs.",
        recovery_template=(
            "{guide} had seen the pouch snag on the marked route and kept it safe "
            "while the surprise was being finished."
        ),
        allowed_surprises=("pennant_reveal", "summit_picnic", "sky_badge"),
        impatience_boost=0.30,
    ),
    "hurry_alone": Challenge(
        key="hurry_alone",
        fluff_item="the little wind pouch full of dandelion fluff",
        trigger_line="The pouch spun away just before the trickiest crossing.",
        mistake_template=(
            "{hero} tried to cross the hard part alone instead of waiting for a steady hand and the guide rope."
        ),
        clue_text="The pouch was looped around the safety rail, fluttering like a tiny white flag.",
        clue_phrase="the pouch fluttering from the safety rail like a tiny white flag",
        search_goal="the safety rail",
        lesson_template="{hero} learned that asking for help can be the bravest step on a hard path.",
        recovery_template=(
            "{friend} had spotted the fluttering pouch at the safety rail and handed it to {guide} "
            "while they kept the trail safe."
        ),
        allowed_surprises=("pennant_reveal", "sky_badge"),
        impatience_boost=0.37,
    ),
}

SURPRISES: dict[str, Surprise] = {
    "pennant_reveal": Surprise(
        key="pennant_reveal",
        phrase="a bright explorer pennant surprise",
        setup_template="a bright explorer pennant with {hero}'s name tied above the finish spot",
        reveal_line_template=(
            "They had made a pennant so {hero} could finish the trail like the leader of the whole adventure."
        ),
        ending_template=(
            "{hero} reached the finish with the pennant snapping overhead and the rescued fluff pouch warm in one hand."
        ),
        afterglow="The high wind sounded less wild now. It sounded like applause.",
        wonder_boost=0.38,
    ),
    "summit_picnic": Surprise(
        key="summit_picnic",
        phrase="a hidden summit picnic surprise",
        setup_template="a blanket with berry buns and warm cider cups behind the windbreak",
        reveal_line_template=(
            "They had carried a tiny picnic to the top so {hero} could celebrate the hard climb."
        ),
        ending_template=(
            "{hero} sat at the high blanket with pink cheeks, muddy shoes, and the fluff pouch safe beside the cup."
        ),
        afterglow="Even the cold air felt gentle once the blanket opened on the stones.",
        wonder_boost=0.35,
    ),
    "sky_badge": Surprise(
        key="sky_badge",
        phrase="a Sky Scout badge surprise",
        setup_template="a small badge box beside a blue ribbon near the finish marker",
        reveal_line_template=(
            "They had brought a Sky Scout badge because {hero} kept trying on days when the trail felt big."
        ),
        ending_template=(
            "{hero} touched the new badge at the finish and smiled at the little bits of fluff still shining on the ribbon."
        ),
        afterglow="The badge was tiny, but it made the whole climb feel taller.",
        wonder_boost=0.42,
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Ava", "Lina", "Nora", "Tali", "Zoe"),
    "boy": ("Eli", "Milo", "Noah", "Rory", "Tomas"),
}

FRIEND_NAMES: tuple[str, ...] = ("June", "Pip", "Sana", "Theo", "Mika", "Nell")
GUIDE_NAMES: tuple[str, ...] = ("Guide Wren", "Guide Moss", "Ranger Rue")


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def valid_combos() -> list[tuple[str, str, str]]:
    rows: list[tuple[str, str, str]] = []
    for trail in TRAILS.values():
        for challenge in CHALLENGES.values():
            if challenge.key not in trail.allowed_challenges:
                continue
            for surprise in SURPRISES.values():
                if surprise.key not in trail.supported_surprises:
                    continue
                if surprise.key not in challenge.allowed_surprises:
                    continue
                rows.append((trail.key, challenge.key, surprise.key))
    return sorted(rows)


def describe_rejection(trail_key: str, challenge_key: str, surprise_key: str) -> str:
    if trail_key not in TRAILS:
        raise StoryError(f"Unknown trail '{trail_key}'. Choose from {', '.join(sorted(TRAILS))}.")
    if challenge_key not in CHALLENGES:
        raise StoryError(f"Unknown challenge '{challenge_key}'. Choose from {', '.join(sorted(CHALLENGES))}.")
    if surprise_key not in SURPRISES:
        raise StoryError(f"Unknown surprise '{surprise_key}'. Choose from {', '.join(sorted(SURPRISES))}.")

    trail = TRAILS[trail_key]
    challenge = CHALLENGES[challenge_key]
    surprise = SURPRISES[surprise_key]
    if challenge.key not in trail.allowed_challenges:
        return (
            f"{trail.phrase} does not fit the {challenge.key} lesson challenge. "
            f"That trail supports {', '.join(trail.allowed_challenges)}."
        )
    if surprise.key not in trail.supported_surprises:
        return (
            f"{trail.phrase} cannot stage {surprise.phrase}. "
            f"That trail supports {', '.join(trail.supported_surprises)}."
        )
    if surprise.key not in challenge.allowed_surprises:
        return (
            f"The {challenge.key} challenge does not resolve cleanly with {surprise.phrase}. "
            f"It supports {', '.join(challenge.allowed_surprises)}."
        )
    return "That ridge adventure combination is not reasonable."


def build_world(params: StoryParams) -> World:
    if (params.trail, params.challenge, params.surprise) not in valid_combos():
        raise StoryError(describe_rejection(params.trail, params.challenge, params.surprise))

    trail = TRAILS[params.trail]
    challenge = CHALLENGES[params.challenge]
    surprise = SURPRISES[params.surprise]

    world = World(
        params=params,
        trail=trail,
        challenge=challenge,
        surprise=surprise,
        source_tale=SOURCE_TALE,
    )

    hero = Entity(
        name=params.hero,
        kind="child explorer",
        location="the trailhead",
        meters={"balance": 0.61, "breath": 0.74, "grip": 0.58},
        memes={"courage": 0.60, "patience": 0.55, "worry": 0.16, "trust": 0.72, "wonder": 0.49, "surprise": 0.0},
        inventory=[challenge.fluff_item],
        notes={"goal": trail.finish_spot},
    )
    friend = Entity(
        name=params.friend,
        kind="scout friend",
        location="the trailhead",
        meters={"speed": 0.66, "careful_hands": 0.69},
        memes={"care": 0.83, "secrecy": 0.36, "steadiness": 0.61},
        inventory=[],
    )
    guide = Entity(
        name=params.guide,
        kind="trail guide",
        location="the trailhead",
        meters={"voice": 0.71, "footing": 0.87},
        memes={"guidance": 0.93, "care": 0.89, "calm": 0.86},
        inventory=[],
    )
    pouch = Entity(
        name=challenge.fluff_item,
        kind="wind pouch",
        location="hero pack loop",
        meters={"lightness": 0.95, "safety": 0.60},
        memes={"importance": 0.72},
        inventory=[],
    )

    world.entities = {"hero": hero, "friend": friend, "guide": guide, "pouch": pouch}
    return world


def _record(world: World, stage: str, location: str, summary: str, cause: str, consequence: str) -> None:
    world.beats.append(Beat(stage=stage, location=location, summary=summary, cause=cause, consequence=consequence))


def _simulate(world: World) -> None:
    hero = world.hero()
    friend = world.friend()
    guide = world.guide()
    pouch = world.pouch()

    hero.location = world.trail.phrase
    friend.location = world.trail.phrase
    guide.location = world.trail.phrase
    pouch.location = hero.name
    world.setup_phrase = world.surprise.setup_template.format(hero=hero.name)
    world.reveal_line = world.surprise.reveal_line_template.format(hero=hero.name)
    world.mistake_text = world.challenge.mistake_template.format(hero=hero.name)
    world.lesson_text = world.challenge.lesson_template.format(hero=hero.name)
    world.recovery_text = world.challenge.recovery_template.format(
        hero=hero.name,
        friend=friend.name,
        guide=guide.name,
    )

    _record(
        world,
        "beginning",
        world.trail.phrase,
        f"{hero.name} started up {world.trail.phrase} with {pouch.name} clipped to the pack.",
        "A bright practice adventure had begun on the ridge.",
        f"{hero.name} aimed for {world.trail.finish_spot}.",
    )

    world.challenge_seen = True
    hero.inventory.clear()
    pouch.location = "the wind"
    friend.location = world.trail.reveal_spot
    guide.location = world.trail.reveal_spot
    hero.memes["worry"] += world.challenge.impatience_boost
    hero.memes["patience"] -= 0.17
    hero.memes["trust"] -= 0.09
    hero.meters["balance"] -= 0.07
    hero.meters["breath"] -= 0.09
    hero.meters["grip"] -= 0.04
    world.tension_feeling = "hot and jangly" if hero.memes["worry"] > 0.42 else "tight and shaky"
    _record(
        world,
        "challenge",
        "the windy trail",
        f"{world.challenge.trigger_line} {hero.name} lost hold of {pouch.name}.",
        "The ridge wind turned a small tool into a hard choice.",
        world.mistake_text,
    )

    world.clue_found = world.challenge.clue_text
    hero.location = world.trail.clue_route
    hero.meters["balance"] -= world.trail.gust_load * 0.20
    hero.meters["breath"] -= 0.06
    hero.meters["grip"] += 0.05
    hero.memes["courage"] += 0.12
    hero.memes["patience"] += 0.08
    _record(
        world,
        "search",
        world.trail.clue_route,
        f"{hero.name} followed {world.challenge.clue_phrase} through {world.trail.clue_route}.",
        "The first rushed choice did not solve the problem.",
        f"At {world.trail.obstacle}, {hero.name} had to slow down and place each step with care.",
    )

    hero.location = world.trail.reveal_spot
    friend.location = world.trail.reveal_spot
    guide.location = world.trail.reveal_spot
    pouch.location = hero.name
    hero.inventory = [pouch.name]
    world.surprise_ready = True
    world.lesson_learned = True
    hero.memes["trust"] += 0.22
    hero.memes["patience"] += 0.26
    hero.memes["wonder"] += world.surprise.wonder_boost
    hero.memes["surprise"] += 0.77
    hero.memes["worry"] = max(0.06, hero.memes["worry"] - 0.33)
    hero.meters["balance"] += 0.16
    hero.meters["grip"] += 0.08
    pouch.meters["safety"] += 0.28
    _record(
        world,
        "reveal",
        world.trail.reveal_spot,
        f"{hero.name} found {friend.name} and {guide.name} preparing {world.setup_phrase}.",
        world.recovery_text,
        world.reveal_line,
    )

    hero.location = world.trail.finish_spot
    friend.location = world.trail.finish_spot
    guide.location = world.trail.finish_spot
    hero.meters["breath"] += 0.07
    hero.memes["courage"] += 0.19
    hero.memes["wonder"] += 0.09
    world.resolved = True
    world.final_image = world.surprise.ending_template.format(hero=hero.name)
    _record(
        world,
        "ending",
        world.trail.finish_spot,
        f"{hero.name} crossed {world.trail.obstacle} and reached {world.trail.finish_spot}.",
        world.lesson_text,
        world.final_image,
    )


def _footing_phrase(world: World) -> str:
    balance = world.hero().meters["balance"]
    if balance < 0.45:
        return "very careful feet"
    if balance < 0.60:
        return "careful feet"
    return "steady feet"


def render_story(world: World) -> str:
    hero = world.hero()
    friend = world.friend()
    guide = world.guide()
    pouch = world.pouch()
    subj, poss, _obj = _pronouns(world.params.gender)
    footing = _footing_phrase(world)

    beginning = (
        f"At {RIDGE_NAME}, {hero.name} set out on the {world.trail.phrase} with {pouch.name} clipped to {poss} pack. "
        f"The trail held {world.trail.intro_detail}, and the whole hill felt like {world.trail.adventure_name}. "
        f"{hero.name} liked tossing a pinch of fluff into the air to read the wind before each hard step."
    )

    middle = (
        f"Then the wind changed. {world.challenge.trigger_line} In a blink, white fluff skipped away over the path. "
        f"{world.mistake_text} That choice made {poss} chest feel {world.tension_feeling}. "
        f"Still, {hero.name} noticed {world.challenge.clue_phrase} and followed it through {world.trail.clue_route}. "
        f"By the time {subj} reached {world.trail.obstacle}, {subj} knew the trail would only listen to {footing} and a calmer breath."
    )

    ending = (
        f"Near {world.trail.reveal_spot}, {hero.name} found {friend.name} and {guide.name} preparing {world.setup_phrase}. "
        f"{world.recovery_text} It was a surprise for {hero.name}. {world.reveal_line} "
        f"{world.lesson_text} "
        f"When {hero.name} started the last stretch again, the ridge no longer felt bossy or mean. "
        f"{world.final_image} {world.surprise.afterglow}"
    )

    return "\n\n".join([beginning, middle, ending])


def build_prompts(world: World) -> list[str]:
    hero = world.hero().name
    return [
        "Write a child-facing Adventure story that includes the word 'fluff.'",
        f"Set the story on a windy hill trail at {RIDGE_NAME} and center it on {hero}.",
        f"Include a trail mistake, a clear lesson learned, and end with {world.surprise.phrase}.",
    ]


def build_story_qa(world: World) -> list[QAItem]:
    hero = world.hero().name
    friend = world.friend().name
    guide = world.guide().name
    return [
        QAItem(
            question=f"Why did {hero} get into trouble on the trail?",
            answer=(
                f"{world.mistake_text} "
                f"That first fast choice made the climb harder and turned a small problem into a real adventure challenge."
            ),
        ),
        QAItem(
            question=f"What clue showed {hero} where to go next?",
            answer=(
                f"{world.clue_found} "
                f"That clue pointed toward {world.challenge.search_goal}, where the safest path forward became easier to see."
            ),
        ),
        QAItem(
            question=f"How did {world.trail.obstacle} change the way {hero} moved?",
            answer=(
                f"{hero} had to slow down at {world.trail.obstacle} and place each step with care. "
                f"The obstacle forced {hero} to trade panic for balance."
            ),
        ),
        QAItem(
            question=f"What surprise was waiting near {world.trail.reveal_spot}?",
            answer=(
                f"{friend} and {guide} were preparing {world.setup_phrase}. "
                f"The surprise was meant to celebrate the climb, not distract from it."
            ),
        ),
        QAItem(
            question=f"How was the missing fluff pouch recovered?",
            answer=(
                f"{world.recovery_text} "
                f"Because they acted early, the pouch stayed safe enough to return to {hero} at the reveal."
            ),
        ),
        QAItem(
            question=f"What lesson did {hero} learn by the end?",
            answer=(
                f"{world.lesson_text} "
                f"That lesson changed the ending because {hero} finished the trail with wiser choices instead of hurried ones."
            ),
        ),
    ]


def build_world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why might an explorer carry something light like fluff on a windy trail?",
            answer=(
                "A tiny bit of fluff shows which way the air is moving before a hard crossing. "
                "That can help a child notice a safer moment to step."
            ),
        ),
        QAItem(
            question="Why are trail markers useful during an adventure?",
            answer=(
                "Trail markers keep people from trading a safe path for a tempting shortcut. "
                "They save energy because they point toward the route that was checked ahead of time."
            ),
        ),
        QAItem(
            question="Why can asking for help be part of bravery instead of the opposite?",
            answer=(
                "Bravery is not only about moving first. "
                "Sometimes the bravest choice is to slow down, accept a steady hand, and protect everyone on the path."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    _simulate(world)
    world.story = render_story(world)
    return StorySample(
        params=params,
        story=world.story,
        prompts=build_prompts(world),
        story_qa=build_story_qa(world),
        world_qa=build_world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["--- prompts ---"]
    lines.extend(f"- {prompt}" for prompt in sample.prompts)
    lines.append("")
    lines.append("--- story qa ---")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
        lines.append("")
    lines.append("--- world qa ---")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


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
    parser = argparse.ArgumentParser(description="Windy trail fluff lesson surprise adventure world.")
    parser.add_argument("--trail", choices=sorted(TRAILS))
    parser.add_argument("--challenge", choices=sorted(CHALLENGES))
    parser.add_argument("--surprise", choices=sorted(SURPRISES))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--friend")
    parser.add_argument("--guide")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.trail is None or combo[0] == args.trail)
        and (args.challenge is None or combo[1] == args.challenge)
        and (args.surprise is None or combo[2] == args.surprise)
    ]
    if not combos:
        raise StoryError(
            describe_rejection(
                args.trail or "rope_ridge",
                args.challenge or "chase_gust",
                args.surprise or "pennant_reveal",
            )
        )

    trail, challenge, surprise = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or rng.choice(HERO_NAMES[gender])
    friend_choices = [name for name in FRIEND_NAMES if name != hero]
    friend = args.friend or rng.choice(friend_choices)
    guide = args.guide or rng.choice(GUIDE_NAMES)
    if friend == hero:
        raise StoryError("Friend and hero must be different people in this storyworld.")
    return StoryParams(
        trail=trail,
        challenge=challenge,
        surprise=surprise,
        hero=hero,
        gender=gender,
        friend=friend,
        guide=guide,
        seed=(args.seed or 1000) + index,
    )


ASP_RULES = r"""
combo(T,C,S) :-
  trail(T), challenge(C), surprise(S),
  trail_allows_challenge(T,C),
  trail_supports_surprise(T,S),
  challenge_supports_surprise(C,S).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for trail in TRAILS.values():
        rows.append(asp.fact("trail", trail.key))
        for challenge in trail.allowed_challenges:
            rows.append(asp.fact("trail_allows_challenge", trail.key, challenge))
        for surprise in trail.supported_surprises:
            rows.append(asp.fact("trail_supports_surprise", trail.key, surprise))
    for challenge in CHALLENGES.values():
        rows.append(asp.fact("challenge", challenge.key))
        for surprise in challenge.allowed_surprises:
            rows.append(asp.fact("challenge_supports_surprise", challenge.key, surprise))
    for surprise in SURPRISES.values():
        rows.append(asp.fact("surprise", surprise.key))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def exercise_generated_stories() -> list[str]:
    problems: list[str] = []
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            trail=combo[0],
            challenge=combo[1],
            surprise=combo[2],
            hero="Ava",
            gender="girl",
            friend="June",
            guide="Guide Wren",
            seed=700 + i,
        )
        sample = generate(params)
        story = sample.story.lower()
        if "fluff" not in story:
            problems.append(f"{combo}: story is missing the seed word 'fluff'")
        if "surprise" not in story:
            problems.append(f"{combo}: story never names the surprise")
        if "learned" not in story:
            problems.append(f"{combo}: story never states the lesson learned")
        if story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, middle, or ending paragraph")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world QA set is too small")
        if any(item.answer.count(".") < 2 for item in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if sample.world is None or not sample.world.resolved or not sample.world.lesson_learned:
            problems.append(f"{combo}: world never reaches a resolved lesson state")
        if not sample.world.final_image:
            problems.append(f"{combo}: story is missing a final image")
    return problems


def asp_verify() -> int:
    py = set(valid_combos())
    logic = set(asp_valid_combos())
    status = 0
    if py == logic:
        print(f"OK: ASP gate matches Python valid_combos() ({len(py)} combos).")
    else:
        print("MISMATCH between Python and ASP gate")
        if py - logic:
            print(f"  only python: {sorted(py - logic)}")
        if logic - py:
            print(f"  only asp: {sorted(logic - py)}")
        status = 1

    problems = exercise_generated_stories()
    if problems:
        print("Story exercise failures:")
        for item in problems:
            print(f"  {item}")
        status = 1
    else:
        print("OK: generated stories pass seed, structure, QA, lesson, and resolution checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    attempts = 0
    while len(samples) < target and attempts < target * 50:
        seed = base_seed + attempts
        attempts += 1
        params = resolve_params(args, random.Random(seed), index=attempts)
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Not enough unique fluff adventure stories from the current constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 41
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            trail=combo[0],
            challenge=combo[1],
            surprise=combo[2],
            hero=args.hero or "Ava",
            gender=args.gender or "girl",
            friend=args.friend or "June",
            guide=args.guide or "Guide Wren",
            seed=base_seed + i,
        )
        rows.append(generate(params))
    return rows


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(list(argv) if argv is not None else None)
    if args.show_asp:
        print(asp_program("#show combo/3."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    try:
        samples = _sample_all(args) if args.all else _sample_n(args)
        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for i, sample in enumerate(samples):
            header = ""
            if args.all:
                p = sample.params
                header = f"### trail={p.trail} challenge={p.challenge} surprise={p.surprise}"
            elif len(samples) > 1:
                header = f"### variant {i + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if i < len(samples) - 1:
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as err:
        print(err)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
