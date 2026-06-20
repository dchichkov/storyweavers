#!/usr/bin/env python3
"""
shiny_cat_sandbox_repetition_curiosity_rhyming_story.py
=======================================================

A small StoryWorld for the seed:

    words: shiny cat
    setting: sandbox
    features: Repetition, Curiosity
    style: Rhyming Story

Internal source tale:
    A child is building in a sandbox when a shiny cat keeps repeating the same
    small clue at one part of the sand. The child grows curious instead of
    digging wildly, matches a careful search rhyme to the kind of clue, and
    uncovers a hidden little object. The ending image shows the sandbox changed
    from puzzling to peaceful because curiosity turned into a gentle answer.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class SandboxZone:
    key: str
    phrase: str
    landmark: str
    support_keys: tuple[str, ...]
    sand_depth_cm: float
    end_view: str


@dataclass(frozen=True)
class Secret:
    key: str
    phrase: str
    support_key: str
    hiding_spot: str
    cause: str
    recovery: str
    proof_image: str
    lesson: str


@dataclass(frozen=True)
class SearchMethod:
    key: str
    phrase: str
    chant: str
    action: str
    tool: str
    solves: tuple[str, ...]


@dataclass
class StoryParams:
    zone: str
    secret: str
    method: str
    hero: str
    gender: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = round(value, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)

    def set_tag(self, key: str, value: str) -> None:
        self.tags[key] = value


@dataclass
class World:
    params: StoryParams
    zone: SandboxZone
    secret: Secret
    method: SearchMethod
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    opening_text: str = ""
    clue_text: str = ""
    turn_text: str = ""
    ending_text: str = ""
    story: str = ""

    def note(self, text: str) -> None:
        self.history.append(text)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(
            f"zone={self.zone.key} secret={self.secret.key} method={self.method.key} "
            f"hero={self.params.hero} helper={self.params.helper}"
        )
        for name, ent in self.entities.items():
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            detail = "; ".join(part for part in (meters, memes, tags) if part)
            rows.append(f"  {name:<10} ({ent.kind:<10}) {detail}".rstrip())
        rows.append(f"  fired rules: {self.fired_rules}")
        rows.append("  history:")
        rows.extend(f"    - {item}" for item in self.history)
        return "\n".join(rows)


ZONES: dict[str, SandboxZone] = {
    "shell_rim": SandboxZone(
        key="shell_rim",
        phrase="the shell-bright rim of the sandbox",
        landmark="a ring of pale shells beside a red pail",
        support_keys=("glitter", "pawprint"),
        sand_depth_cm=6.0,
        end_view="the shell rim looked smooth and sunny around the red pail",
    ),
    "tunnel_curve": SandboxZone(
        key="tunnel_curve",
        phrase="the curved tunnel side of the sandbox",
        landmark="a sandy arch with a cool little hollow",
        support_keys=("echo", "pawprint"),
        sand_depth_cm=8.0,
        end_view="the tunnel curve stood neat again with no secret humming inside",
    ),
    "bucket_ring": SandboxZone(
        key="bucket_ring",
        phrase="the bucket ring in the middle of the sandbox",
        landmark="three stacked buckets around a flat tower",
        support_keys=("echo", "glitter"),
        sand_depth_cm=5.0,
        end_view="the bucket ring gleamed softly around the flat tower",
    ),
    "moat_edge": SandboxZone(
        key="moat_edge",
        phrase="the damp moat edge of the sandbox",
        landmark="a curving moat beside a lopsided sand castle",
        support_keys=("ripple", "glitter"),
        sand_depth_cm=4.0,
        end_view="the moat edge lay still beside the castle wall",
    ),
}

SECRETS: dict[str, Secret] = {
    "marble_glint": Secret(
        key="marble_glint",
        phrase="a sun-bright marble",
        support_key="glitter",
        hiding_spot="under a thin lid of pale sand",
        cause="a buried marble kept winking whenever the light brushed the top sand",
        recovery="sifted the loose sand into a pail lid until the round marble rolled free",
        proof_image="The marble shone on the castle wall like a tiny sun for fun.",
        lesson="Small flashes can lead to big answers when a child looks twice instead of once.",
    ),
    "shell_bell": Secret(
        key="shell_bell",
        phrase="a humming shell bell",
        support_key="echo",
        hiding_spot="inside a hollow sandy pocket",
        cause="a shell bell was tucked in a sandy pocket and hummed whenever a breeze crossed the hollow",
        recovery="hummed back, listened close, and lifted the shell bell from the cool hollow",
        proof_image="The shell bell rested by the tower, quiet and light in the afternoon light.",
        lesson="A repeated sound can become a map when someone pauses long enough to hear its shape.",
    ),
    "star_key": Secret(
        key="star_key",
        phrase="a star-shaped toy key",
        support_key="pawprint",
        hiding_spot="beneath a loop of tiny pawprints",
        cause="the shiny cat had paced the same circle because a toy key glittered just under its paws",
        recovery="followed the little paw marks, patted the sand, and lifted out the toy key",
        proof_image="The toy key hung from the pail handle, ready and steady.",
        lesson="Repeating tracks can show where to search if curiosity stays calm.",
    ),
    "silver_boat": Secret(
        key="silver_boat",
        phrase="a tiny silver boat",
        support_key="ripple",
        hiding_spot="just below the damp moat edge",
        cause="a trickle from the moat kept kissing the sand above a tiny silver boat",
        recovery="smoothed the wet sand in slow circles until the boat nose peeked free",
        proof_image="The silver boat gleamed by the moat, and the little ripples stayed still with no spill.",
        lesson="Gentle hands can read moving sand better than fast scoops can.",
    ),
}

METHODS: dict[str, SearchMethod] = {
    "pat_pat_peek": SearchMethod(
        key="pat_pat_peek",
        phrase="a soft pat-and-peek search",
        chant="Pat, pat, peek; the secret is meek.",
        action="pressed the sand with two slow pats and then peeped at the top layer",
        tool="careful hands",
        solves=("pawprint",),
    ),
    "hush_hum_hear": SearchMethod(
        key="hush_hum_hear",
        phrase="a hush-and-hum search",
        chant="Hush, hum, hear; the answer is near.",
        action="held still, hummed a little tune, and listened for the answer under the sand",
        tool="quiet ears",
        solves=("echo",),
    ),
    "sift_sift_shine": SearchMethod(
        key="sift_sift_shine",
        phrase="a sift-and-shine search",
        chant="Sift, sift, shine; the bright clue is mine.",
        action="let dry sand slip through open fingers until only the gleam stayed behind",
        tool="a pail lid",
        solves=("glitter",),
    ),
    "smooth_smooth_seek": SearchMethod(
        key="smooth_smooth_seek",
        phrase="a smooth-and-seek search",
        chant="Smooth, smooth, seek; the silver will speak.",
        action="smoothed the damp sand in small rings to see what the ripples were hiding",
        tool="flat fingertips",
        solves=("ripple",),
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Mina", "Ruth", "Tessa"),
    "boy": ("Owen", "Eli", "Noah"),
}

HELPERS: dict[str, str] = {
    "aunt_jo": "Aunt Jo",
    "dad": "Dad",
    "keeper_lee": "Keeper Lee",
}

CAT_NAME = "Glimmer"


def helper_name(key: str) -> str:
    return HELPERS[key]


def valid_combo(zone: str, secret: str, method: str) -> bool:
    if zone not in ZONES or secret not in SECRETS or method not in METHODS:
        return False
    need = SECRETS[secret].support_key
    return need in ZONES[zone].support_keys and need in METHODS[method].solves


def explain_rejection(zone: str, secret: str, method: str) -> str:
    if zone not in ZONES:
        return f"No story: unknown sandbox zone {zone!r}."
    if secret not in SECRETS:
        return f"No story: unknown hidden sandbox secret {secret!r}."
    if method not in METHODS:
        return f"No story: unknown search method {method!r}."
    need = SECRETS[secret].support_key
    if need not in ZONES[zone].support_keys:
        return (
            f"No story: {ZONES[zone].phrase} cannot hide {SECRETS[secret].phrase} in a grounded way; "
            f"that secret needs a {need} clue."
        )
    if need not in METHODS[method].solves:
        return (
            f"No story: {METHODS[method].phrase} does not fit {SECRETS[secret].phrase}; "
            f"try a method that can read a {need} clue."
        )
    return "No story: the sandbox choices do not form a reasonable tale."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for zone in sorted(ZONES):
        for secret in sorted(SECRETS):
            for method in sorted(METHODS):
                if valid_combo(zone, secret, method):
                    combos.append((zone, secret, method))
    return combos


def _pick_hero(rng: random.Random, gender: str) -> str:
    return rng.choice(HERO_NAMES[gender])


def build_world(params: StoryParams) -> World:
    zone = ZONES[params.zone]
    secret = SECRETS[params.secret]
    method = METHODS[params.method]
    hero = Entity(name=params.hero, kind="child")
    cat = Entity(name=CAT_NAME, kind="cat")
    sandbox = Entity(name="Sandbox", kind="place")
    hidden = Entity(name=secret.phrase, kind="hidden_object")
    helper = Entity(name=helper_name(params.helper), kind="helper")
    world = World(
        params=params,
        zone=zone,
        secret=secret,
        method=method,
        entities={
            "Hero": hero,
            "Cat": cat,
            "Sandbox": sandbox,
            "Secret": hidden,
            "Helper": helper,
        },
    )
    sandbox.set_meter("depth_cm", zone.sand_depth_cm)
    sandbox.set_tag("landmark", zone.landmark)
    hidden.set_tag("spot", secret.hiding_spot)
    hidden.set_meter("found", 0.0)
    return world


def _r_open_with_curiosity(world: World) -> bool:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    sandbox = world.entities["Sandbox"]

    hero.add_meme("curiosity", 1.1)
    hero.add_meme("patience", 0.5)
    hero.add_meter("steps_m", 1.8)
    cat.add_meme("focus", 1.0)
    cat.add_meme("wonder", 0.9)
    cat.set_meter("repeat_count", 3.0)
    sandbox.add_meme("mystery", 0.8)
    sandbox.add_meme("play", 0.7)

    world.opening_text = (
        f"In the sandbox, warm and wide, {world.params.hero} played beside a shiny cat named {CAT_NAME}. "
        f"By {world.zone.phrase}, the cat would not pounce or nap or chat; it watched one little place and came right back."
    )
    world.note(
        f"{world.params.hero} noticed that {CAT_NAME} kept returning to {world.zone.phrase} instead of wandering away."
    )
    return True


def _r_cat_repeats_the_clue(world: World) -> bool:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    hidden = world.entities["Secret"]

    hero.add_meme("curiosity", 0.7)
    hero.add_meme("care", 0.4)
    cat.add_meter("steps_m", 2.1)
    hidden.set_tag("cause", world.secret.cause)

    if world.secret.support_key == "pawprint":
        action = "step, step, circle"
        clue = "Three times the cat circled the same patch and left neat little pawprints in the sand."
    elif world.secret.support_key == "echo":
        action = "sit, hum, hear"
        clue = "Three times the cat tilted its ears while a tiny hum hid in the tunnel like a shy drum."
    elif world.secret.support_key == "glitter":
        action = "blink, blink, gleam"
        clue = "Three times the cat blinked at one bright wink in the sand, as if the sand itself had learned to gleam."
    else:
        action = "pat, pause, ripple"
        clue = "Three times the cat patted the damp edge and watched the same small ripple wiggle back."

    cat.set_tag("repeat_action", action)
    world.clue_text = (
        f"{clue} {world.params.hero} felt a curious tickle and thought, "
        f"\"If the shiny cat repeats a clue, I should repeat a careful clue-reader too.\""
    )
    world.note(world.clue_text)
    return True


def _r_match_method_to_clue(world: World) -> bool:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    sandbox = world.entities["Sandbox"]
    hidden = world.entities["Secret"]
    helper = world.entities["Helper"]

    hero.add_meme("patience", 0.9)
    hero.add_meme("curiosity", 0.4)
    hero.add_meme("confidence", 0.8)
    hero.add_meter("search_loops", 3.0)
    cat.add_meme("wonder", 0.3)
    sandbox.add_meme("mystery", -0.5)
    sandbox.add_meme("calm", 1.1)
    hidden.set_meter("found", 1.0)
    hidden.set_tag("recovery", world.secret.recovery)
    hidden.set_tag("proof_image", world.secret.proof_image)
    helper.add_meme("approval", 0.8)

    chant = world.method.chant
    world.turn_text = (
        f"So {world.params.hero} tried {world.method.phrase}. "
        f"\"{chant}\" came once, then twice, then thrice, while {world.params.hero} {world.method.action}. "
        f"That was the turn: {world.secret.cause}, and {world.params.hero} {world.secret.recovery}."
    )
    world.note(world.turn_text)
    return True


def _r_close_with_proof(world: World) -> bool:
    hero = world.entities["Hero"]
    cat = world.entities["Cat"]
    sandbox = world.entities["Sandbox"]
    hidden = world.entities["Secret"]
    helper = world.entities["Helper"]

    hero.add_meme("joy", 1.0)
    cat.add_meme("calm", 1.0)
    sandbox.add_meme("play", 0.6)
    hidden.set_tag("resolved", "yes")
    helper.set_tag("saw_result", "yes")

    world.ending_text = (
        f"{helper.name} smiled and said that gentle curiosity had solved the sandy riddle. "
        f"{world.secret.proof_image} Nearby, {CAT_NAME} curled up while {world.zone.end_view}, "
        f"and the sandbox felt less like a puzzle and more like a song."
    )
    world.note(world.ending_text)
    return True


RULES: tuple[tuple[str, Callable[[World], bool]], ...] = (
    ("open_with_curiosity", _r_open_with_curiosity),
    ("cat_repeats_the_clue", _r_cat_repeats_the_clue),
    ("match_method_to_clue", _r_match_method_to_clue),
    ("close_with_proof", _r_close_with_proof),
)


def run_world(world: World) -> World:
    for name, rule in RULES:
        fired = rule(world)
        if fired:
            world.fired_rules.append(name)
    return world


def render_story(world: World) -> str:
    middle = (
        f"{world.clue_text} Then {world.params.hero} chose care instead of a wild sand-fling, "
        f"because curiosity wanted the true small thing."
    )
    ending = (
        f"{world.turn_text} {world.ending_text} {world.secret.lesson}"
    )
    return "\n\n".join((world.opening_text, middle, ending))


def prompts_for(world: World) -> list[str]:
    return [
        f"Tell a rhyming sandbox story about {world.params.hero} and a shiny cat named {CAT_NAME}.",
        f"Use repetition by having the cat repeat {world.entities['Cat'].tags['repeat_action']} three times at {world.zone.phrase}.",
        f"Let curiosity guide {world.params.hero} to use {world.method.phrase} and end with {world.secret.proof_image}",
    ]


def story_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What made the child pay close attention to the sandbox spot?",
            answer=(
                f"{CAT_NAME}, the shiny cat, kept returning to the same place at {world.zone.phrase}. "
                f"That repetition made {world.params.hero} feel that the sandbox was trying to show a clue instead of just hiding a toy."
            ),
        ),
        QAItem(
            question="Why did curiosity help instead of causing a mess?",
            answer=(
                f"{world.params.hero} stayed gentle and matched a careful method to the clue instead of digging everywhere at once. "
                f"That calm choice protected the shape of the sandbox and made the hidden answer easier to notice."
            ),
        ),
        QAItem(
            question="How did the child search once the clue became clear?",
            answer=(
                f"{world.params.hero} used {world.method.phrase} and repeated the chant, \"{world.method.chant}\" three times. "
                f"The repeated rhyme slowed the search down and fit the clue type that the shiny cat had been showing."
            ),
        ),
        QAItem(
            question="What was hidden in the sand, and why was it there?",
            answer=(
                f"The hidden object was {world.secret.phrase}, tucked {world.secret.hiding_spot}. "
                f"It was found there because {world.secret.cause}."
            ),
        ),
        QAItem(
            question="What final image proves that the sandbox changed by the end?",
            answer=(
                f"The ending image is this: {world.secret.proof_image} "
                f"That picture proves the problem is over because the secret is out in the open and the sandbox is calm again."
            ),
        ),
    ]


def world_qa_for(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can repetition be useful when someone is searching for a small clue?",
            answer=(
                "Repetition helps a person notice which detail keeps returning instead of treating every detail as equally important. "
                "In a small place like a sandbox, the repeated clue often points toward the exact spot that deserves careful attention."
            ),
        ),
        QAItem(
            question="Why is a gentle search better than wild digging for a buried toy-sized object?",
            answer=(
                "Gentle searching keeps the clue pattern in place and lowers the chance of knocking the object deeper into the sand. "
                "Care also lets the finder match the method to the material, whether the clue is a print, a hum, a glitter, or a ripple."
            ),
        ),
        QAItem(
            question="Why is curiosity strongest when it stays calm?",
            answer=(
                "Calm curiosity keeps asking what the clue means instead of rushing to the first loud guess. "
                "That makes it easier to observe cause and effect, which is how small mysteries become understandable."
            ),
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.zone, params.secret, params.method):
        raise StoryError(explain_rejection(params.zone, params.secret, params.method))
    world = run_world(build_world(params))
    story = render_story(world)
    world.story = story
    return StorySample(
        params=params,
        story=story,
        prompts=prompts_for(world),
        story_qa=story_qa_for(world),
        world_qa=world_qa_for(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Prompts ==", *[f"{i}. {item}" for i, item in enumerate(sample.prompts, 1)], ""]
    lines.append("== (2) Story-grounded QA ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        print("\n")
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sandbox shiny-cat rhyming curiosity world.")
    parser.add_argument("--zone", choices=sorted(ZONES))
    parser.add_argument("--secret", choices=sorted(SECRETS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HERO_NAMES))
    parser.add_argument("--helper", choices=sorted(HELPERS))
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        combo
        for combo in valid_combos()
        if (args.zone is None or combo[0] == args.zone)
        and (args.secret is None or combo[1] == args.secret)
        and (args.method is None or combo[2] == args.method)
    ]
    if not combos:
        raise StoryError(
            explain_rejection(
                args.zone or "shell_rim",
                args.secret or "marble_glint",
                args.method or "sift_sift_shine",
            )
        )
    zone, secret, method = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(rng, gender)
    helper = args.helper or rng.choice(sorted(HELPERS))
    return StoryParams(
        zone=zone,
        secret=secret,
        method=method,
        hero=hero,
        gender=gender,
        helper=helper,
    )


ASP_RULES = r"""
combo(Z,S,M) :-
  zone(Z), secret(S), method(M),
  zone_support(Z,N), secret_need(S,N), method_solves(M,N).

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows: list[str] = []
    for zone in ZONES.values():
        rows.append(asp.fact("zone", zone.key))
        for support in zone.support_keys:
            rows.append(asp.fact("zone_support", zone.key, support))
    for secret in SECRETS.values():
        rows.append(asp.fact("secret", secret.key))
        rows.append(asp.fact("secret_need", secret.key, secret.support_key))
    for method in METHODS.values():
        rows.append(asp.fact("method", method.key))
        for support in method.solves:
            rows.append(asp.fact("method_solves", method.key, support))
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
            zone=combo[0],
            secret=combo[1],
            method=combo[2],
            hero="Mina",
            gender="girl",
            helper="aunt_jo",
            seed=1700 + i,
        )
        sample = generate(params)
        story = sample.story.lower()
        world = sample.world
        if "shiny cat" not in story:
            problems.append(f"{combo}: story is missing the seed phrase 'shiny cat'")
        if "sandbox" not in story:
            problems.append(f"{combo}: story is missing the sandbox setting")
        if sample.story.count("\n\n") < 2:
            problems.append(f"{combo}: story is missing a clear beginning, turn, or ending paragraph")
        if sample.story.lower().count(METHODS[combo[2]].chant.lower()) < 1:
            problems.append(f"{combo}: story does not render the search chant")
        if len(sample.story_qa) < 5:
            problems.append(f"{combo}: story-grounded QA set is too small")
        if len(sample.world_qa) < 3:
            problems.append(f"{combo}: world-knowledge QA set is too small")
        if any(answer.answer.count(".") < 2 for answer in sample.story_qa):
            problems.append(f"{combo}: a story-grounded QA answer is too short")
        if world is None:
            problems.append(f"{combo}: sample is missing its world model")
            continue
        if world.entities["Cat"].meters.get("repeat_count") != 3.0:
            problems.append(f"{combo}: repetition state was not recorded in the cat entity")
        if world.entities["Secret"].meters.get("found") != 1.0:
            problems.append(f"{combo}: hidden object was never marked as found")
        if world.entities["Secret"].tags.get("resolved") != "yes":
            problems.append(f"{combo}: hidden object never reached a resolved state")
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
        print("OK: generated stories pass seed, structure, QA, repetition, and resolution checks.")
    return status


def _sample_n(args: argparse.Namespace) -> list[StorySample]:
    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)
    samples: list[StorySample] = []
    seen: set[str] = set()
    target = max(1, args.n)
    attempts = 0
    while len(samples) < target and attempts < target * 40:
        seed = base_seed + attempts
        attempts += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        samples.append(sample)
    if len(samples) < target:
        raise StoryError("Not enough unique sandbox stories from the current constraints.")
    return samples


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    rows: list[StorySample] = []
    base_seed = args.seed if args.seed is not None else 31
    for i, combo in enumerate(valid_combos()):
        params = StoryParams(
            zone=combo[0],
            secret=combo[1],
            method=combo[2],
            hero="Mina",
            gender="girl",
            helper="aunt_jo",
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

    if args.all:
        samples = _sample_all(args)
    else:
        samples = _sample_n(args)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return 0

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
