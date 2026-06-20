#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/sleepy_temple_blank_hair_salon_sharing_adventure.py
================================================================================

A standalone storyworld built from the seed:

    Words: sleepy, temple, blank
    Setting: hair salon
    Features: Sharing
    Style: Adventure

Internal source tale
--------------------
Early in the morning, a sleepy child arrives at a neighborhood hair salon for
Adventure Day. A stylist has left a blank quest card for a temple hairstyle
challenge, but the child's friend cannot help finish it because the needed tool
is missing. The child wakes up enough to focus, shares the exact tool the
friend needs, and together they turn the blank card into a route map and a
finished hairstyle. The ending image is the mirror proof that sharing changed
both the task and the child's mood.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
for base in (ROOT,):
    if str(base) not in sys.path:
        sys.path.insert(0, str(base))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


BASE_ENERGY = 2


@dataclass(frozen=True)
class Salon:
    key: str
    phrase: str
    time_phrase: str
    counter_phrase: str
    chair_phrase: str
    mirror_phrase: str
    adventure_frame: str


@dataclass(frozen=True)
class TempleStyle:
    key: str
    phrase: str
    needed_share: str
    required_energy: int
    route_phrase: str
    problem_phrase: str
    finish_image: str
    buddy_job: str


@dataclass(frozen=True)
class ShareItem:
    key: str
    phrase: str
    material: str
    solve_text: str


@dataclass(frozen=True)
class WakeMethod:
    key: str
    phrase: str
    energy_gain: int
    detail: str
    afterglow: str


@dataclass
class StoryParams:
    style: str
    share_item: str
    wake_method: str
    hero: str
    buddy: str
    gender: str
    seed: int | None = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    location: str
    attrs: dict[str, str] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        gender = self.attrs.get("gender", "child")
        if gender == "boy":
            table = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            table = {"subject": "she", "object": "her", "possessive": "her"}
        return table[case]


@dataclass(frozen=True)
class Event:
    tag: str
    actor: str
    detail: str


@dataclass
class World:
    params: StoryParams
    salon: Salon
    style: TempleStyle
    share_item: ShareItem
    wake_method: WakeMethod
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[Event] = field(default_factory=list)
    story: str = ""

    def trace(self) -> str:
        lines = ["--- world model state ---"]
        lines.append(f"  salon={self.salon.key}")
        lines.append(f"  style={self.style.key}")
        lines.append(f"  share_item={self.share_item.key}")
        lines.append(f"  wake_method={self.wake_method.key}")
        for ent_id, ent in self.entities.items():
            lines.append(f"  entity {ent_id}: {ent.label} ({ent.kind}) @ {ent.location}")
            if ent.inventory:
                lines.append(f"    inventory={', '.join(ent.inventory)}")
            if ent.meters:
                meters = ", ".join(f"{k}={v:g}" for k, v in sorted(ent.meters.items()))
                lines.append(f"    meters={meters}")
            if ent.memes:
                memes = ", ".join(f"{k}={v:g}" for k, v in sorted(ent.memes.items()))
                lines.append(f"    memes={memes}")
        if self.history:
            lines.append("  history:")
            for event in self.history:
                lines.append(f"    - {event.tag}: {event.actor} -> {event.detail}")
        return "\n".join(lines)


SALONS: dict[str, Salon] = {
    "comet_comb": Salon(
        key="comet_comb",
        phrase="Comet Comb Hair Salon",
        time_phrase="very early in the morning",
        counter_phrase="the front counter beside a jar of bright combs",
        chair_phrase="the round styling chair under the silver dryer hood",
        mirror_phrase="the wide mirror at the end of the braid station",
        adventure_frame="a little temple trail camp hidden inside a hair salon",
    ),
}

STYLES: dict[str, TempleStyle] = {
    "temple_braid": TempleStyle(
        key="temple_braid",
        phrase="a temple-trail braid",
        needed_share="ribbon_roll",
        required_energy=5,
        route_phrase="past the pretend shampoo river and around the dryer cave",
        problem_phrase="the braid would slip loose without a tie at the end",
        finish_image="two smiling faces in the mirror, each braid tied with one bright ribbon tip",
        buddy_job="held the braid steady while the last loop was tucked in",
    ),
    "temple_twist": TempleStyle(
        key="temple_twist",
        phrase="a temple-lantern twist",
        needed_share="moon_comb",
        required_energy=6,
        route_phrase="between the towel tower and the long mirror wall",
        problem_phrase="the hair part would wander crooked without the right comb",
        finish_image="a smooth twist near each temple, shining like a tiny lantern path",
        buddy_job="used the comb to draw an even line before the twist was wrapped",
    ),
    "temple_crown": TempleStyle(
        key="temple_crown",
        phrase="a temple-crown braid",
        needed_share="star_clips",
        required_energy=8,
        route_phrase="under the dryer drum and up to the mirror hill",
        problem_phrase="the crown loops would fall before the mirror check without strong clips",
        finish_image="a neat little crown shape above the temples, pinned with two star clips",
        buddy_job="snapped the clips in place so the crown shape could hold",
    ),
}

SHARES: dict[str, ShareItem] = {
    "ribbon_roll": ShareItem(
        key="ribbon_roll",
        phrase="a ribbon roll",
        material="soft blue ribbon",
        solve_text="gave the braid a final tie so the route on the quest card could match the real hair",
    ),
    "moon_comb": ShareItem(
        key="moon_comb",
        phrase="a moon comb",
        material="a pale crescent comb",
        solve_text="made a clean part so the blank card could turn into a careful map instead of a guess",
    ),
    "star_clips": ShareItem(
        key="star_clips",
        phrase="star clips",
        material="two bright silver clips",
        solve_text="held the crown loops in place long enough for the mirror check to prove the style was finished",
    ),
}

WAKE_METHODS: dict[str, WakeMethod] = {
    "warm_towel": WakeMethod(
        key="warm_towel",
        phrase="a warm towel wake-up",
        energy_gain=2,
        detail="stood by the sink while a warm towel and a slow count helped the yawns shrink",
        afterglow="The warmth made the child feel steadier, but only for simple careful work.",
    ),
    "citrus_mist": WakeMethod(
        key="citrus_mist",
        phrase="a bright citrus mist",
        energy_gain=4,
        detail="breathed in a bright citrus mist, stretched both arms high, and blinked at the salon lights until the eyes felt clearer",
        afterglow="The fresh scent turned the morning fog into alert, careful focus.",
    ),
    "dryer_drum": WakeMethod(
        key="dryer_drum",
        phrase="a dryer-drum march",
        energy_gain=7,
        detail="marched beside the dryer drum while it hummed like adventure music, and each step chased the sleep away",
        afterglow="The rhythm gave the child enough focus for the most careful salon challenge.",
    ),
}

HEROES: dict[str, tuple[str, ...]] = {
    "girl": ("Mira", "Lena", "Nia", "Tessa", "Ruby"),
    "boy": ("Leo", "Owen", "Milo", "Rafi", "Jude"),
}

BUDDIES: dict[str, tuple[str, ...]] = {
    "girl": ("June", "Pia", "Cora", "Skye", "Nell"),
    "boy": ("Finn", "Toby", "Arlo", "Beck", "Sami"),
}


def valid_combo(style_key: str, share_key: str, wake_key: str) -> bool:
    if style_key not in STYLES or share_key not in SHARES or wake_key not in WAKE_METHODS:
        return False
    style = STYLES[style_key]
    wake = WAKE_METHODS[wake_key]
    if style.needed_share != share_key:
        return False
    return BASE_ENERGY + wake.energy_gain >= style.required_energy


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for style_key in sorted(STYLES):
        for share_key in sorted(SHARES):
            for wake_key in sorted(WAKE_METHODS):
                if valid_combo(style_key, share_key, wake_key):
                    combos.append((style_key, share_key, wake_key))
    return combos


def describe_rejection(style_key: str, share_key: str, wake_key: str) -> str:
    if style_key not in STYLES:
        return f"No story: unknown style {style_key!r}."
    if share_key not in SHARES:
        return f"No story: unknown share item {share_key!r}."
    if wake_key not in WAKE_METHODS:
        return f"No story: unknown wake method {wake_key!r}."
    style = STYLES[style_key]
    share_item = SHARES[share_key]
    wake = WAKE_METHODS[wake_key]
    if style.needed_share != share_key:
        needed = SHARES[style.needed_share].phrase
        return (
            f"No story: {style.phrase} needs {needed}, not {share_item.phrase}. "
            f"That is the missing tool for this salon challenge."
        )
    if BASE_ENERGY + wake.energy_gain < style.required_energy:
        return (
            f"No story: {wake.phrase} does not wake a sleepy child enough for {style.phrase}. "
            f"This challenge needs a stronger focus boost."
        )
    return "No story: this parameter set does not describe a reasonable salon adventure."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sleepy salon sharing adventure world.")
    parser.add_argument("--style", choices=sorted(STYLES))
    parser.add_argument("--share-item", choices=sorted(SHARES))
    parser.add_argument("--wake-method", choices=sorted(WAKE_METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--buddy")
    parser.add_argument("--gender", choices=sorted(HEROES))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true", help="render every valid style/share/wake combination")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true", help="list only ASP-valid combinations")
    parser.add_argument("--verify", action="store_true", help="verify ASP/Python parity and story exercise checks")
    parser.add_argument("--show-asp", action="store_true", help="print ASP facts and rules")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combos = [
        combo for combo in valid_combos()
        if (args.style is None or combo[0] == args.style)
        and (args.share_item is None or combo[1] == args.share_item)
        and (args.wake_method is None or combo[2] == args.wake_method)
    ]
    if not combos:
        raise StoryError(
            describe_rejection(
                args.style or "temple_braid",
                args.share_item or "ribbon_roll",
                args.wake_method or "citrus_mist",
            )
        )

    style_key, share_key, wake_key = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    buddy_pool = [name for name in BUDDIES[gender] if name != hero]
    buddy = args.buddy or rng.choice(buddy_pool)
    if hero == buddy:
        raise StoryError("No story: hero and buddy must be different children.")
    return StoryParams(
        style=style_key,
        share_item=share_key,
        wake_method=wake_key,
        hero=hero,
        buddy=buddy,
        gender=gender,
        seed=(args.seed or 1000) + index,
    )


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.style, params.share_item, params.wake_method):
        raise StoryError(describe_rejection(params.style, params.share_item, params.wake_method))
    if params.gender not in HEROES:
        raise StoryError(f"No story: unsupported gender group {params.gender!r}.")
    if params.hero == params.buddy:
        raise StoryError("No story: hero and buddy must be different children.")

    salon = SALONS["comet_comb"]
    style = STYLES[params.style]
    share_item = SHARES[params.share_item]
    wake_method = WAKE_METHODS[params.wake_method]
    world = World(
        params=params,
        salon=salon,
        style=style,
        share_item=share_item,
        wake_method=wake_method,
    )

    hero = Entity(
        id="hero",
        kind="child",
        label=params.hero,
        location=salon.counter_phrase,
        inventory=[share_item.phrase],
        attrs={"gender": params.gender},
    )
    hero.meters["energy"] = BASE_ENERGY
    hero.meters["hair_progress"] = 0
    hero.meters["steps"] = 0
    hero.memes["bravery"] = 5
    hero.memes["sharing"] = 4
    hero.memes["sleepiness"] = 8

    buddy = Entity(
        id="buddy",
        kind="child",
        label=params.buddy,
        location=salon.chair_phrase,
        attrs={"gender": params.gender},
    )
    buddy.meters["hair_progress"] = 0
    buddy.meters["readiness"] = 2
    buddy.memes["trust"] = 4
    buddy.memes["gratitude"] = 2

    card = Entity(
        id="quest_card",
        kind="object",
        label="quest card",
        location=salon.counter_phrase,
    )
    card.meters["blankness"] = 10
    card.meters["marks"] = 0

    mirror = Entity(
        id="mirror",
        kind="object",
        label="salon mirror",
        location=salon.mirror_phrase,
    )
    mirror.meters["shine"] = 6

    world.entities = {
        "hero": hero,
        "buddy": buddy,
        "quest_card": card,
        "mirror": mirror,
    }

    _simulate(world)
    return world


def _simulate(world: World) -> None:
    hero = world.entities["hero"]
    buddy = world.entities["buddy"]
    card = world.entities["quest_card"]
    mirror = world.entities["mirror"]

    world.history.append(
        Event(
            "arrive",
            hero.label,
            f"arrived at {world.salon.phrase} {world.salon.time_phrase} with a plan for {world.style.phrase}",
        )
    )
    world.history.append(
        Event(
            "notice_blank_card",
            hero.label,
            f"found a blank quest card waiting at {world.salon.counter_phrase}",
        )
    )

    hero.meters["energy"] += world.wake_method.energy_gain
    hero.meters["steps"] += 4
    hero.memes["sleepiness"] = max(1, hero.memes["sleepiness"] - world.wake_method.energy_gain)
    world.history.append(
        Event(
            "wake",
            hero.label,
            world.wake_method.detail,
        )
    )

    world.history.append(
        Event(
            "missing_tool",
            buddy.label,
            f"admitted that {buddy.pronoun('subject')} had forgotten {world.share_item.phrase}",
        )
    )

    hero.inventory.remove(world.share_item.phrase)
    buddy.inventory.append(world.share_item.phrase)
    hero.memes["sharing"] += 4
    buddy.memes["trust"] += 3
    buddy.memes["gratitude"] += 6
    buddy.meters["readiness"] += 5
    card.meters["blankness"] = 0
    card.meters["marks"] = 10
    world.history.append(
        Event(
            "share",
            hero.label,
            f"shared {world.share_item.phrase} so {buddy.label} could help finish the salon quest",
        )
    )
    world.history.append(
        Event(
            "map_route",
            buddy.label,
            f"used the shared item to turn the blank card into a route {world.style.route_phrase}",
        )
    )

    hero.meters["hair_progress"] = 10
    buddy.meters["hair_progress"] = 10
    mirror.meters["shine"] = 10
    hero.memes["bravery"] += 2
    world.history.append(
        Event(
            "finish_style",
            buddy.label,
            world.style.buddy_job,
        )
    )
    world.history.append(
        Event(
            "mirror_proof",
            hero.label,
            world.style.finish_image,
        )
    )


def _opening(world: World) -> list[str]:
    hero = world.entities["hero"]
    buddy = world.entities["buddy"]
    return [
        f"{hero.label} stepped into {world.salon.phrase} {world.salon.time_phrase} with sleepy eyes and a brave plan for Adventure Day.",
        f"On {world.salon.counter_phrase} sat a blank quest card for {world.style.phrase}, and {buddy.label} waited by {world.salon.chair_phrase} hoping to join the mission.",
        f"The whole room felt like {world.salon.adventure_frame}, but the careful hairstyle still had to be earned.",
    ]


def _middle(world: World) -> list[str]:
    hero = world.entities["hero"]
    buddy = world.entities["buddy"]
    return [
        f"To wake up, {hero.label} {world.wake_method.detail}. {world.wake_method.afterglow}",
        f"Then {buddy.label} quietly admitted that {buddy.pronoun('subject')} had forgotten {world.share_item.phrase}, and {world.style.problem_phrase}.",
        f"Instead of keeping the tool, {hero.label} shared {world.share_item.phrase}. That generous choice let {buddy.label} help, and the blank card quickly filled with a route {world.style.route_phrase}.",
    ]


def _closing(world: World) -> list[str]:
    hero = world.entities["hero"]
    buddy = world.entities["buddy"]
    return [
        f"Working together, {hero.label} and {buddy.label} finished {world.style.phrase} and checked it in {world.salon.mirror_phrase}.",
        f"The ending image was {world.style.finish_image}.",
        f"{hero.label} was not sleepy anymore, because sharing had turned a careful hair salon task into a true little adventure.",
    ]


def _render_story(world: World) -> str:
    return "\n\n".join(
        [
            " ".join(_opening(world)),
            " ".join(_middle(world)),
            " ".join(_closing(world)),
        ]
    )


def _story_qa(world: World) -> list[QAItem]:
    hero = world.entities["hero"]
    buddy = world.entities["buddy"]
    return [
        QAItem(
            "Why did the story begin with a blank card on the counter?",
            f"The quest card began completely blank because the children had not planned the hairstyle path yet. It only filled in after the right shared tool reached the counter and they could map the salon adventure together.",
        ),
        QAItem(
            "How did the sleepy child become ready for the challenge?",
            f"{hero.label} used {world.wake_method.phrase} before touching the hairstyle plan. That wake-up step raised the child's focus enough for {world.style.phrase}, which is a careful job near the temple.",
        ),
        QAItem(
            "What was shared, and why did it matter?",
            f"{hero.label} shared {world.share_item.phrase} with {buddy.label}. That mattered because it {world.share_item.solve_text}, so the friend could help instead of standing aside.",
        ),
        QAItem(
            "How did the friend help after the sharing happened?",
            f"After receiving the shared tool, {buddy.label} {world.style.buddy_job}. The friend was part of the solution, not just a watcher, and that is what turned the blank plan into a finished result.",
        ),
        QAItem(
            "What showed that the adventure was complete at the end?",
            f"The proof came in {world.salon.mirror_phrase}, where the children saw {world.style.finish_image}. The mirror mattered because it showed that the careful work really held together.",
        ),
        QAItem(
            "Where did this story happen?",
            f"It happened in {world.salon.phrase}. The salon setting shaped the whole adventure because the counter, dryer, chair, and mirror all became parts of the quest.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why can sharing be important in a hair salon story?",
            "Salon tasks often depend on one small tool arriving at the right moment. Sharing lets another person join the careful work, which can change a stalled problem into a team solution.",
        ),
        QAItem(
            "Why does a temple hairstyle need calm attention?",
            "Hair near the temple is close to the face, so careless movement can ruin the shape or make the work uneven. A good story treats that as a reason for focus, not just decoration.",
        ),
        QAItem(
            "What can a blank planning card do in a child adventure?",
            "A blank card gives children a place to turn ideas into a visible plan. Once it is filled, everyone can see the route, the missing tool, and the next step clearly.",
        ),
        QAItem(
            "Why might an early-morning child need a wake-up step before careful styling?",
            "Sleepiness can make a child rush or lose focus during small, precise work. A wake-up step changes the body state first, which makes the later success feel earned.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    world.story = _render_story(world)
    prompts = [
        f"Write an adventure story in a hair salon where a sleepy child wants {world.style.phrase}.",
        f"Include a blank quest card and a sharing moment involving {world.share_item.phrase}.",
        f"Let the solution depend on {world.wake_method.phrase} and on both children finishing the task together.",
    ]
    return StorySample(
        params=params,
        story=world.story,
        prompts=prompts,
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts"]
    for i, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {prompt}")
    lines.extend(["", "== (2) Story questions"])
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.extend(["", "== (3) World-knowledge questions"])
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
        print()
        print(format_qa(sample))


ASP_RULES = r"""
style(S) :- style_need(S,_).
share_item(I) :- solves_style(I,_).
wake_method(W) :- wake_gain(W,_).

combo(S,I,W) :-
    style(S),
    share_item(I),
    wake_method(W),
    solves_style(I,S),
    base_energy(B),
    style_need(S,N),
    wake_gain(W,G),
    B + G >= N.

#show combo/3.
"""


def asp_facts() -> str:
    from storyworlds import asp

    rows = [asp.fact("base_energy", BASE_ENERGY)]
    for style in STYLES.values():
        rows.append(asp.fact("style_need", style.key, style.required_energy))
        rows.append(asp.fact("solves_style", style.needed_share, style.key))
    for wake in WAKE_METHODS.values():
        rows.append(asp.fact("wake_gain", wake.key, wake.energy_gain))
    return "\n".join(rows)


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    from storyworlds import asp

    model = asp.one_model(asp_program("#show combo/3."))
    return sorted(set(asp.atoms(model, "combo")))


def _exercise_sample(sample: StorySample) -> None:
    story_lower = sample.story.lower()
    required_tokens = ["sleepy", "temple", "blank", "hair salon"]
    for token in required_tokens:
        if token not in story_lower:
            raise StoryError(f"Verification failed: story is missing required token {token!r}.")
    if "{" in sample.story or "}" in sample.story:
        raise StoryError("Verification failed: story leaked unresolved template braces.")
    if sample.story.count("\n\n") < 2:
        raise StoryError("Verification failed: story is missing a clear beginning, middle, and ending break.")
    if not sample.prompts or not sample.story_qa or not sample.world_qa:
        raise StoryError("Verification failed: prompts or QA sets are empty.")
    world = sample.world
    if world is None:
        raise StoryError("Verification failed: world trace is missing.")
    if world.entities["quest_card"].meters["blankness"] != 0:
        raise StoryError("Verification failed: blank card did not resolve in world state.")
    if world.entities["hero"].meters["energy"] < world.style.required_energy:
        raise StoryError("Verification failed: hero never reached the needed focus state.")


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

    for index, combo in enumerate(sorted(python_set), start=1):
        params = StoryParams(
            style=combo[0],
            share_item=combo[1],
            wake_method=combo[2],
            hero="Mira",
            buddy="June",
            gender="girl",
            seed=700 + index,
        )
        _exercise_sample(generate(params))

    print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
    print(f"OK: exercised {len(python_set)} generated stories and QA sets.")
    return 0


def _emit_variants(samples: list[StorySample], args: argparse.Namespace) -> None:
    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### style={p.style} share_item={p.share_item} wake_method={p.wake_method}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 72 + "\n")


def _sample_all(args: argparse.Namespace) -> list[StorySample]:
    samples: list[StorySample] = []
    gender = args.gender or "girl"
    hero = args.hero or HEROES[gender][0]
    buddy = args.buddy or BUDDIES[gender][0]
    if hero == buddy:
        buddy = BUDDIES[gender][1]
    base_seed = args.seed or 7
    for index, combo in enumerate(valid_combos(), start=1):
        params = StoryParams(
            style=combo[0],
            share_item=combo[1],
            wake_method=combo[2],
            hero=hero,
            buddy=buddy,
            gender=gender,
            seed=base_seed + index,
        )
        samples.append(generate(params))
    return samples


def main() -> int:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show combo/3."))
        return 0
    if args.verify:
        return asp_verify()
    if args.asp:
        for combo in asp_valid_combos():
            print("\t".join(combo))
        return 0

    base_seed = args.seed if args.seed is not None else random.randrange(1, 1_000_000)

    try:
        if args.all:
            samples = _sample_all(args)
        else:
            samples: list[StorySample] = []
            seen: set[str] = set()
            attempts = 0
            while len(samples) < args.n and attempts < args.n * 80:
                params = resolve_params(args, random.Random(base_seed + attempts), index=attempts)
                sample = generate(params)
                attempts += 1
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
