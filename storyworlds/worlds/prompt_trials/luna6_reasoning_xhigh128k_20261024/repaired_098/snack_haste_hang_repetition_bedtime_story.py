#!/usr/bin/env python3
"""A gentle bedtime story about a snack hung in haste and a helpful refrain."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next((parent for parent in HERE.parents if (parent / "results.py").is_file()), None)
if ROOT is None:
    raise RuntimeError("Could not find storyworlds/results.py")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Creature:
    name: str
    species: str
    role: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Place:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Treat:
    name: str
    meters: dict[str, float] = field(default_factory=dict)


@dataclass
class Pouch:
    material: str
    hanging: bool = False
    hang_site: str = ""
    meters: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class SnackChoice:
    name: str
    weight_g: float
    warmth: float


@dataclass(frozen=True)
class Episode:
    hang_site: str
    problem: str
    worry: str
    first_guess: str
    test_action: str
    test_result: str
    clue: str
    cause: str
    safe_method: str
    repair: str
    ending_image: str
    lesson: str
    hang_height_m: float
    initial_sway_cm: float
    cause_from_haste: bool = True
    test_discriminates: bool = True
    safe_from_ground: bool = True
    climb_required: bool = False


@dataclass
class StoryParams:
    seed: Optional[int] = None
    traveler_name: str = "Miri"
    helper_name: str = "Tansy"
    place: str = "moonseed_garden"
    snack: str = "honey_oat_biscuit"
    episode: str = "sliding_loop"
    route: str = "moonrise"


@dataclass
class World:
    traveler: Creature
    helper: Creature
    place: Place
    snack: Treat
    pouch: Pouch
    episode_id: str
    episode: Episode
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(paragraph) for paragraph in self.paragraphs if paragraph)


PLACES = {
    "moonseed_garden": "Moonseed Garden",
    "quiet_orchard": "Quiet Orchard",
    "blue_cottage_garden": "the garden behind the little blue cottage",
}

SNACKS = {
    "honey_oat_biscuit": SnackChoice("honey-oat biscuit", 18.0, 0.35),
    "pear_tartlet": SnackChoice("pear tartlet", 24.0, 0.25),
    "warm_seed_roll": SnackChoice("warm seed roll", 28.0, 0.7),
}

NAME_PAIRS = (
    ("Miri", "Tansy"),
    ("Pip", "Mallow"),
    ("Nell", "Bramble"),
)

ROUTES = ("moonrise", "promise", "hush")

EPISODES = {
    "sliding_loop": Episode(
        hang_site="a smooth willow branch above the violet bed",
        problem="the pouch began to sway over the dew-wet violets",
        worry="one stronger swing might drop the snack into the dew",
        first_guess="a night breeze was rocking the pouch",
        test_action="held a loose leaf beside the branch and watched the leaf and pouch",
        test_result="the leaf stayed still, but the pouch crept lower",
        clue="the loose end of the hurried knot had grown longer as it slid over the smooth bark",
        cause="the single loop, tied in haste, was slipping along the smooth bark",
        safe_method=(
            "They placed a shallow basket under the pouch and used a curved reed "
            "to lift the loose loop off the branch."
        ),
        repair=(
            "They retied the pouch in two snug loops around a low wooden peg "
            "and gave it one gentle test."
        ),
        ending_image=(
            "The {food} stayed tucked in the pouch on the low peg, while "
            "moonlight silvered the still violet bed."
        ),
        lesson="a quick knot deserves a careful check before it can be trusted",
        hang_height_m=1.25,
        initial_sway_cm=14.0,
    ),
    "bending_twig": Episode(
        hang_site="a slender hazel twig above the pebble path",
        problem="the pouch sagged lower each time the twig bent",
        worry="the bending twig might let the pouch bump the stones",
        first_guess="a night breeze was pushing the pouch down",
        test_action="watched the little lantern flame and the leaves nearest the twig",
        test_result="the flame stayed straight and the leaves barely stirred, but the twig bowed",
        clue="the thin twig bent under the pouch while a thicker branch beside it stayed firm",
        cause="in haste, they had chosen a twig too slender to hold the pouch",
        safe_method=(
            "They held a basket under the pouch and used a long reed to guide its "
            "handle free while keeping their feet on the path."
        ),
        repair=(
            "They set the pouch in a basket on the low garden bench, where no twig "
            "had to carry its weight."
        ),
        ending_image=(
            "The {food} sat safely in the basket on the bench as the hazel twig "
            "lifted toward the stars."
        ),
        lesson="a sturdy resting place is kinder than asking a slender twig to hold too much",
        hang_height_m=1.1,
        initial_sway_cm=9.0,
    ),
    "twisted_handle": Episode(
        hang_site="the low plum arch above a patch of violets",
        problem="the pouch tipped sideways and swung toward the damp violets",
        worry="a loose crumb might spill onto the wet ground",
        first_guess="the pouch's bow had come undone",
        test_action="held the little basket beneath the pouch and watched the bow without pulling",
        test_result="the bow stayed closed, but the handle twisted each time the pouch swayed",
        clue="the handle had caught around a small bark nub and turned the pouch on its side",
        cause="in haste, they looped the handle over the bark nub without noticing its twist",
        safe_method=(
            "They slid the basket beneath the pouch, then used a smooth reed to lift "
            "the twisted handle back over the bark nub."
        ),
        repair=(
            "They placed the pouch in the waiting basket on the porch step and "
            "checked that its bow was closed."
        ),
        ending_image=(
            "The {food} rested in a little basket on the porch step; beneath the "
            "plum arch, the violets stayed dry."
        ),
        lesson="looking closely can keep a small mistake from becoming a spilled snack",
        hang_height_m=1.0,
        initial_sway_cm=11.0,
    ),
}

REFRAIN = "Slow breath, soft paws, safe hands."


ASP_RULES = r"""
low_enough(E) :- hang_height_cm(E,H), H <= 180.
resolved(E) :- episode(E), haste_cause(E), test_discriminates(E),
               decisive_clue(E), safe_from_ground(E), no_climb_required(E),
               has_repair(E), has_ending(E), low_enough(E).
:- episode(E), not resolved(E).
"""


def reasonableness_reasons(episode: Episode) -> list[str]:
    reasons: list[str] = []
    required_text = (
        "hang_site",
        "problem",
        "worry",
        "first_guess",
        "test_action",
        "test_result",
        "clue",
        "cause",
        "safe_method",
        "repair",
        "ending_image",
        "lesson",
    )
    for field_name in required_text:
        if not getattr(episode, field_name).strip():
            reasons.append(f"{field_name} must not be empty")
    if not episode.cause_from_haste:
        reasons.append("the episode must connect the problem to haste")
    if not episode.test_discriminates:
        reasons.append("the test must help distinguish the first guess from the cause")
    if not episode.safe_from_ground:
        reasons.append("the recovery must be possible from the ground")
    if episode.climb_required:
        reasons.append("the recovery must not require climbing")
    if episode.hang_height_m <= 0 or episode.hang_height_m > 1.8:
        reasons.append("the hanging place must be reachable from the ground")
    if episode.initial_sway_cm < 0:
        reasons.append("initial sway cannot be negative")
    return reasons


def reasonableness_gate(episode_id: str) -> bool:
    episode = EPISODES.get(episode_id)
    return episode is not None and not reasonableness_reasons(episode)


def require_reasonable(episode_id: str) -> Episode:
    episode = EPISODES.get(episode_id)
    if episode is None:
        raise StoryError(f"Unknown snack episode: {episode_id}")
    reasons = reasonableness_reasons(episode)
    if reasons:
        raise StoryError(f"Unreasonable snack episode {episode_id}: {'; '.join(reasons)}")
    return episode


def validate_name(name: str, label: str) -> str:
    cleaned = name.strip()
    allowed = all(
        character.isalpha() or character in " -'’"
        for character in cleaned
    )
    if not cleaned or len(cleaned) > 32 or not allowed:
        raise StoryError(
            f"{label} must be a short name using letters, spaces, apostrophes, or hyphens."
        )
    return cleaned


def build_world(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown bedtime setting: {params.place}")
    if params.snack not in SNACKS:
        raise StoryError(f"Unknown snack: {params.snack}")
    if params.route not in ROUTES:
        raise StoryError(f"Unknown story route: {params.route}")

    episode = require_reasonable(params.episode)
    traveler_name = validate_name(params.traveler_name, "Traveler name")
    helper_name = validate_name(params.helper_name, "Helper name")
    if traveler_name.casefold() == helper_name.casefold():
        raise StoryError("The traveler and helper need different names.")

    snack_choice = SNACKS[params.snack]
    return World(
        traveler=Creature(
            name=traveler_name,
            species="dormouse",
            role="snack bearer",
            meters={"paw_reach_m": 0.65},
            memes={"anticipation": 0.6, "haste": 0.0, "worry": 0.0, "care": 0.4},
        ),
        helper=Creature(
            name=helper_name,
            species="dormouse",
            role="steady helper",
            meters={"paw_reach_m": 0.63},
            memes={"calm": 0.65, "attention": 0.4, "warmth": 0.7},
        ),
        place=Place(
            name=PLACES[params.place],
            kind="garden path",
            meters={"night_quiet": 0.9, "path_width_m": 0.8},
            memes={"hush": 0.8, "coziness": 0.7},
        ),
        snack=Treat(
            name=snack_choice.name,
            meters={"weight_g": snack_choice.weight_g, "warmth": snack_choice.warmth, "dry": 1.0},
        ),
        pouch=Pouch(
            material="soft cloth",
            meters={"height_m": 0.0, "sway_cm": 0.0, "loop_security": 0.0},
        ),
        episode_id=params.episode,
        episode=episode,
    )


def story_rng(params: StoryParams) -> random.Random:
    payload = json.dumps(asdict(params), sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def sentence(text: str) -> str:
    if not text:
        return text
    return text[0].upper() + text[1:]


def tell_story(world: World, params: StoryParams) -> None:
    traveler = world.traveler
    helper = world.helper
    episode = world.episode
    rng = story_rng(params)

    traveler.memes.update(anticipation=0.85, haste=0.8, worry=0.15, care=0.55)
    helper.memes.update(calm=0.8, attention=0.55, warmth=0.8)

    openings = {
        "moonrise": (
            f"The moon rose over {world.place.name}, laying a silver path between the sleepy flowers. "
            f"{traveler.name} and {helper.name}, two dormouse friends, were carrying a "
            f"{world.snack.name} home for their bedtime snack."
        ),
        "promise": (
            f"“One last snack before bed,” said {traveler.name}, patting the little cloth pouch. "
            f"{helper.name} lifted a lantern as they walked through {world.place.name}."
        ),
        "hush": (
            f"By bedtime, even the leaves in {world.place.name} seemed to whisper. "
            f"{traveler.name} and {helper.name} carried a {world.snack.name} along the quiet path."
        ),
    }
    opening = openings[params.route]
    if params.route == "moonrise" and rng.random() < 0.5:
        opening = (
            f"Moonlight made a silver ribbon through {world.place.name}. "
            f"{traveler.name} and {helper.name}, two dormouse friends, carried a "
            f"{world.snack.name} home for a quiet bedtime snack."
        )
    world.say(opening)
    world.say(
        f"At the garden gate, {traveler.name} needed both paws to lift the wooden latch. "
        f"“I'll hang the snack pouch here for a moment,” they said. In their haste, "
        f"they looped it over {episode.hang_site} without checking the knot."
    )

    world.pouch.hanging = True
    world.pouch.hang_site = episode.hang_site
    world.pouch.meters.update(
        height_m=episode.hang_height_m,
        sway_cm=episode.initial_sway_cm,
        loop_security=0.2,
    )
    world.facts.update(
        first_guess=episode.first_guess,
        test_action=episode.test_action,
        test_result=episode.test_result,
        clue=episode.clue,
        cause=episode.cause,
        worry=episode.worry,
        safe_method=episode.safe_method,
        repair=episode.repair,
        lesson=episode.lesson,
        solved=False,
        phase="hanging",
    )
    world.say(f"A moment later, {sentence(episode.problem)}.")
    world.say(f"They worried that {episode.worry}.")
    world.para()

    world.say(f"“I can tug it free,” said {traveler.name}.")
    world.say(
        f"“Wait. Let's find out why it is moving before we pull,” replied {helper.name}. "
        f"“The snack will be safer if we understand first.”"
    )
    world.say(f"{helper.name} held the lantern steady.")
    world.say(f"“{REFRAIN}” whispered {helper.name}, and the two friends stopped tugging.")
    world.say(
        f"They tested the guess that {episode.first_guess}: together, they {episode.test_action}."
    )
    world.say(f"The quiet test showed something else: {sentence(episode.test_result)}.")
    world.say(f"Then {helper.name} spotted the clue: {episode.clue}.")
    world.say(
        f"“I see it now,” said {traveler.name}. “{sentence(episode.cause)}. "
        f"We should lower it gently.”"
    )

    traveler.memes.update(haste=0.25, worry=0.55, care=0.9)
    helper.memes.update(calm=0.9, attention=0.95)
    world.facts["phase"] = "cause_found"
    world.para()

    world.say(f"“{REFRAIN}” repeated {traveler.name}. This time, the words helped them choose a careful plan.")
    world.say(
        f"“I'll hold the basket underneath,” said {helper.name}. "
        f"“I'll ease the handle free with the reed,” said {traveler.name}."
    )
    world.say(f"Together, they murmured, “{REFRAIN}”")
    world.say(episode.safe_method)
    world.pouch.hanging = False
    world.pouch.meters.update(height_m=0.0, sway_cm=0.0, loop_security=0.95)
    world.snack.meters["dry"] = 1.0
    world.say("The pouch came down without a spill, and not one crumb fell into the flowers.")
    world.say(sentence(episode.repair))
    world.facts["phase"] = "safe"
    world.facts["solved"] = True

    traveler.memes.update(haste=0.0, worry=0.1, care=1.0, confidence=0.85)
    helper.memes.update(calm=1.0, pride=0.7)
    world.place.memes.update(hush=1.0, coziness=0.95)
    world.place.meters["night_quiet"] = 1.0

    world.para()
    world.say(
        f"“I was in too much haste to check the loop,” said {traveler.name}. "
        f"“Next time, I'll set the pouch down before I lift the latch.”"
    )
    world.say(f"{helper.name} smiled. “And now we can share our bedtime snack.”")
    ending_image = episode.ending_image.format(food=world.snack.name)
    world.say(ending_image)
    world.say(
        f"They carried the pouch to the doorstep, opened it, and shared the "
        f"{world.snack.name} in small, quiet bites."
    )
    world.say(
        f"When the last crumb was gone, the two dormice curled beneath their quilts. "
        f"Outside, the garden was still, and the snack had a safe place for the night."
    )

    world.facts.update(
        traveler=traveler,
        helper=helper,
        place=world.place,
        snack=world.snack,
        episode=episode,
        ending=ending_image,
        solved=True,
        phase="bedtime",
    )


def generation_prompts(world: World) -> list[str]:
    return [
        (
            f"Write a gentle bedtime story about {world.traveler.name} and "
            f"{world.helper.name} carrying a {world.snack.name} through {world.place.name}."
        ),
        (
            f"Show how haste makes a snack pouch hang unsafely, then let the friends "
            f"use a careful test and a safe plan to bring it down."
        ),
        (
            f"Include the repeated bedtime refrain “{REFRAIN}” and end with the friends "
            f"safe and sleepy."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    traveler = world.traveler
    helper = world.helper
    episode = world.episode
    return [
        QAItem(
            question=f"Why did {traveler.name} hang the snack pouch at the garden gate?",
            answer=(
                f"{traveler.name} needed both paws to lift the wooden latch, so they hung "
                f"the pouch for a moment. In their haste, they did not check how securely "
                f"it was looped over {episode.hang_site}."
            ),
        ),
        QAItem(
            question=f"What did {traveler.name} and {helper.name} first think was moving the pouch?",
            answer=(
                f"They first wondered whether {episode.first_guess}. Their quiet test showed "
                f"that this guess did not explain what they saw: {episode.test_result}."
            ),
        ),
        QAItem(
            question=f"What clue showed the friends the real cause of the swinging pouch?",
            answer=(
                f"{helper.name} noticed that {episode.clue}. That clue showed them that "
                f"{episode.cause}."
            ),
        ),
        QAItem(
            question=f"How did the friends get the pouch down safely?",
            answer=(
                f"They stayed on the path and worked from the ground. {episode.safe_method} "
                f"They used a basket and a reed instead of climbing or yanking the pouch."
            ),
        ),
        QAItem(
            question="How did the night end after the pouch was safe?",
            answer=(
                f"The friends made a safer resting place for the pouch: {episode.repair} "
                f"Then they shared their snack and curled up beneath their quilts."
            ),
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does haste mean?",
            answer=(
                "Haste means doing something very quickly, sometimes without taking enough "
                "time to check whether it is safe or ready."
            ),
        ),
        QAItem(
            question="What is repetition in a story?",
            answer=(
                "Repetition is when a word, sound, or phrase returns more than once. "
                "A gentle repeated phrase can make a bedtime story feel soothing and easy to remember."
            ),
        ),
        QAItem(
            question="Why is it helpful to test a first guess?",
            answer=(
                "A first guess can be wrong. A calm, safe test lets people notice what is really "
                "happening before they decide what to do."
            ),
        ),
        QAItem(
            question="What is a dormouse?",
            answer=(
                "A dormouse is a small, furry animal that often rests or sleeps in a sheltered nest."
            ),
        ),
        QAItem(
            question="Why should someone avoid climbing after a hanging object?",
            answer=(
                "Climbing can add a new risk, especially in the dark. If an object can be reached "
                "safely from the ground, a steady tool and a helper are better choices."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place_id, place_name in PLACES.items():
        lines.append(asp.fact("place", place_id))
        lines.append(asp.fact("place_name", place_id, place_name))
    for snack_id, snack in SNACKS.items():
        lines.append(asp.fact("snack", snack_id))
        lines.append(asp.fact("snack_name", snack_id, snack.name))
    for route in ROUTES:
        lines.append(asp.fact("route", route))

    for episode_id, episode in EPISODES.items():
        lines.extend(
            (
                asp.fact("episode", episode_id),
                asp.fact("hang_site", episode_id, episode.hang_site),
                asp.fact("cause_text", episode_id, episode.cause),
                asp.fact("ending_text", episode_id, episode.ending_image),
                asp.fact("hang_height_cm", episode_id, int(round(episode.hang_height_m * 100))),
            )
        )
        if episode.cause_from_haste:
            lines.append(asp.fact("haste_cause", episode_id))
        if episode.test_discriminates and episode.test_action and episode.test_result:
            lines.append(asp.fact("test_discriminates", episode_id))
        if episode.clue:
            lines.append(asp.fact("decisive_clue", episode_id))
        if episode.safe_from_ground:
            lines.append(asp.fact("safe_from_ground", episode_id))
        if not episode.climb_required:
            lines.append(asp.fact("no_climb_required", episode_id))
        if episode.repair:
            lines.append(asp.fact("has_repair", episode_id))
        if episode.ending_image:
            lines.append(asp.fact("has_ending", episode_id))
    return "\n".join(lines)


def asp_program(show: str = "#show resolved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program("#show resolved/1."))
    except ImportError as exc:
        print(f"Cannot run ASP verification: {exc}")
        return 2

    asp_resolved = set(asp.atoms(model, "resolved"))
    python_resolved = {
        (episode_id,)
        for episode_id in EPISODES
        if reasonableness_gate(episode_id)
    }
    if asp_resolved != python_resolved:
        print("MISMATCH between clingo and Python reasonableness gates.")
        print("clingo:", sorted(asp_resolved))
        print("python:", sorted(python_resolved))
        return 1

    story_checks = 0
    try:
        for index, episode_id in enumerate(EPISODES):
            params = StoryParams(
                seed=9100 + index,
                traveler_name=("Miri", "Pip", "Nell")[index],
                helper_name=("Tansy", "Mallow", "Bramble")[index],
                place=tuple(PLACES)[index % len(PLACES)],
                snack=tuple(SNACKS)[index % len(SNACKS)],
                episode=episode_id,
                route=ROUTES[index % len(ROUTES)],
            )
            sample = generate(params)
            world = sample.world
            if world is None:
                raise AssertionError("generated sample did not retain its world")
            if sample.story.count(REFRAIN) != 3:
                raise AssertionError(f"{episode_id} did not repeat the bedtime refrain three times")
            if not world.facts.get("solved") or world.pouch.hanging:
                raise AssertionError(f"{episode_id} did not reach a safe resolved state")
            if world.pouch.meters.get("sway_cm") != 0.0:
                raise AssertionError(f"{episode_id} left the pouch swinging")
            if "“I can tug it free,”" not in sample.story or "“Wait." not in sample.story:
                raise AssertionError(f"{episode_id} is missing its spoken exchange")
            if episode_id in sample.story:
                raise AssertionError(f"{episode_id} leaked an internal identifier into the story")
            if "{{" in sample.story or "}}" in sample.story:
                raise AssertionError(f"{episode_id} left an unresolved template field")
            if any(not item.answer.strip() for item in sample.story_qa + sample.world_qa):
                raise AssertionError(f"{episode_id} produced an empty QA answer")
            story_checks += 1
    except (AssertionError, StoryError) as exc:
        print(f"Generated-story verification failed: {exc}")
        return 1

    print(
        "OK: clingo gate matches Python reasoning "
        f"({len(python_resolved)} episodes); generated-story checks passed ({story_checks})."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A quiet bedtime story about a snack pouch hung in haste."
    )
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--traveler-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--place", choices=sorted(PLACES))
    parser.add_argument("--snack", choices=sorted(SNACKS))
    parser.add_argument("--episode", choices=sorted(EPISODES))
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    default_traveler, default_helper = rng.choice(NAME_PAIRS)
    return StoryParams(
        seed=args.seed,
        traveler_name=args.traveler_name or default_traveler,
        helper_name=args.helper_name or default_helper,
        place=args.place or rng.choice(sorted(PLACES)),
        snack=args.snack or rng.choice(sorted(SNACKS)),
        episode=args.episode or rng.choice(sorted(EPISODES)),
        route=rng.choice(ROUTES),
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in (world.traveler, world.helper, world.place, world.snack, world.pouch):
        lines.append(
            f"{getattr(entity, 'name', getattr(entity, 'material', 'pouch'))}: "
            f"meters={entity.meters} memes={getattr(entity, 'memes', {})}"
        )
    lines.append(
        f"episode: site={world.pouch.hang_site!r} hanging={world.pouch.hanging} "
        f"cause={world.facts.get('cause')!r} phase={world.facts.get('phase')!r} "
        f"solved={world.facts.get('solved')}"
    )
    return "\n".join(lines)


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
) -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.show_asp:
            print(asp_program())
            return
        if args.verify:
            raise SystemExit(asp_verify())
        if args.asp:
            import asp

            model = asp.one_model(asp_program("#show resolved/1."))
            print(sorted(set(asp.atoms(model, "resolved"))))
            return
        if args.n < 1:
            raise StoryError("-n must be at least 1.")

        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        episode_ids = list(EPISODES) if args.all else []
        count = len(episode_ids) if args.all else args.n
        samples: list[StorySample] = []
        for index in range(count):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            if args.all:
                params.episode = episode_ids[index]
            samples.append(generate(params))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return

        for index, sample in enumerate(samples):
            header = f"### bedtime variant {index + 1}" if len(samples) > 1 else ""
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        parser.error(str(exc))
    except ImportError as exc:
        parser.error(f"ASP support is unavailable: {exc}")


if __name__ == "__main__":
    main()
