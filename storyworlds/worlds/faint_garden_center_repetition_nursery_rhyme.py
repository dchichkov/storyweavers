#!/usr/bin/env python3
"""
storyworlds/worlds/faint_garden_center_repetition_nursery_rhyme.py
==================================================================

Seed prompt used:
    Write a story that includes the following words and narrative instruments.
    Words: faint
    Setting: garden center
    Features: Repetition
    Style: Nursery Rhyme

Source tale written from the seed:
    At Daisy Bell Garden Center, a child helping a grown-up hears a faint little
    repeat-sound from one plant bench. The sound is never a floating mystery:
    it comes from a physical plant problem in the garden center itself. The
    child listens, matches the right care to the right plant, and the repeated
    nursery-rhyme line changes at the end to prove the world has changed too.

This script keeps the story grounded in a tiny world model. A bed, a plant
problem, and a care action must fit one another. The repeated nursery-rhyme
refrain is driven by physical state: the signal is faint while the plant still
needs help, and it goes quiet once the right care is embedded in the world.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


GARDEN_CENTER_NAME = "Daisy Bell Garden Center"


@dataclass(frozen=True)
class Bed:
    key: str
    phrase: str
    opening_image: str
    ending_image: str
    plant_label: str
    allowed_cares: tuple[str, ...]


@dataclass(frozen=True)
class Problem:
    key: str
    label: str
    bed: str
    signal_text: str
    refrain: str
    observation: str
    cause: str
    need: str
    consequence: str
    after_refrain: str
    final_image: str
    compatible_cares: tuple[str, ...]


@dataclass(frozen=True)
class Care:
    key: str
    phrase: str
    action_text: str
    why_it_fits: str
    fixes_need: str


@dataclass
class StoryParams:
    bed: str
    problem: str
    care: str
    hero: str
    hero_kind: str
    helper: str
    seed: int | None = None


@dataclass
class Entity:
    name: str
    kind: str
    phrase: str
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind in {"girl", "mother", "grandmother", "aunt", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind in {"boy", "father", "grandfather", "uncle", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    params: StoryParams
    bed_cfg: Bed
    problem_cfg: Problem
    care_cfg: Care
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: list[str] = field(default_factory=list)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.name] = ent
        return ent

    def get(self, name: str) -> Entity:
        return self.entities[name]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  bed={self.bed_cfg.key}")
        rows.append(f"  problem={self.problem_cfg.key}")
        rows.append(f"  care={self.care_cfg.key}")
        for ent in self.entities.values():
            rows.append(
                f"  {ent.name}<{ent.kind}> location={ent.location} "
                f"meters={dict(ent.meters)} memes={dict(ent.memes)}"
            )
        rows.append(f"  facts={self.facts}")
        rows.append(f"  fired={self.fired}")
        return "\n".join(rows)


BEDS: dict[str, Bed] = {
    "seedling_bench": Bed(
        key="seedling_bench",
        phrase="the seedling bench by the glass wall",
        opening_image="tiny cups stood in rows like buttons on a green coat",
        ending_image="the seedling bench shone with dark soil and bright round faces",
        plant_label="the marigold tray",
        allowed_cares=("sprinkle_can",),
    ),
    "fern_corner": Bed(
        key="fern_corner",
        phrase="the fern corner under the mist pipe",
        opening_image="soft fronds hung in layers like feather fans in a song",
        ending_image="the fern corner looked cool again, with drops resting on every curled tip",
        plant_label="the silver fern basket",
        allowed_cares=("draw_shade",),
    ),
    "rose_rack": Bed(
        key="rose_rack",
        phrase="the rose rack beside the lattice gate",
        opening_image="pink buds peeped through leaves like ribbons peeking from a pocket",
        ending_image="the rose rack stood neat and still, with one straight stem holding up its pink cups",
        plant_label="the climbing rose pot",
        allowed_cares=("tie_ribbon",),
    ),
}

PROBLEMS: dict[str, Problem] = {
    "thirsty_tray": Problem(
        key="thirsty_tray",
        label="the marigold tray",
        bed="seedling_bench",
        signal_text="a faint tap-tap from the tin watering can beside the tray",
        refrain='"Faint, faint, faint," went the tap-tap tin. "Drink, drink, drink, let the roots begin."',
        observation="The soil looked pale and crumbly, and the little marigold heads had started to bow.",
        cause="the cups had gone light and dry after a warm morning under the glass",
        need="water at the roots",
        consequence="The flowers would droop farther if no one listened soon.",
        after_refrain='"Hush, hush, hush," went the now-still tin. "Sip, sip, sip, let the stems grin."',
        final_image="Tiny orange faces lifted again above the damp, dark soil.",
        compatible_cares=("sprinkle_can",),
    ),
    "warm_fronds": Problem(
        key="warm_fronds",
        label="the silver fern basket",
        bed="fern_corner",
        signal_text="a faint sigh-sigh from the warm fronds near the sunniest pane",
        refrain='"Faint, faint, faint," sighed the fern in the light. "Shade, shade, shade, make the noon grow slight."',
        observation="The top fronds had curled at the edges, and the basket felt warmer than the cool pipe above it.",
        cause="a stripe of strong noon light had slipped past the glass and stayed on the basket too long",
        need="cooler shade over the leaves",
        consequence="The fern would keep wilting if the hot stripe stayed there.",
        after_refrain='"Soft, soft, soft," sighed the fern in the shade. "Cool, cool, cool, what a gentle glade."',
        final_image="Silver-green fronds loosened and hung easy again, each one holding a tiny bead of mist.",
        compatible_cares=("draw_shade",),
    ),
    "leaning_rose": Problem(
        key="leaning_rose",
        label="the climbing rose pot",
        bed="rose_rack",
        signal_text="a faint clink-clink where a loose stem touched its bamboo stake",
        refrain='"Faint, faint, faint," clinked the rose by the post. "Tie, tie, tie, hold me up the most."',
        observation="One long stem had leaned away from the lattice and kept nudging the bamboo with every little breeze.",
        cause="the new stem had grown tall and had no soft ribbon holding it steady yet",
        need="a gentle tie to the stake",
        consequence="The stem could bend harder or scrape its bloom if it kept knocking.",
        after_refrain='"Still, still, still," stood the rose by the post. "Bloom, bloom, bloom, now I sway the least."',
        final_image="The pink buds rested high and calm, and the bamboo stake stopped clicking at the pot.",
        compatible_cares=("tie_ribbon",),
    ),
}

CARES: dict[str, Care] = {
    "sprinkle_can": Care(
        key="sprinkle_can",
        phrase="tip the little rose can and count one, two, three",
        action_text=(
            "{hero} tipped the little rose can while {helper} held the tray steady, and together they counted one, two, three. "
            "The water went low and slow, right where the roots could drink."
        ),
        why_it_fits="dry cups need water at the roots, not a wild splash on the petals.",
        fixes_need="water at the roots",
    ),
    "draw_shade": Care(
        key="draw_shade",
        phrase="pull the reed shade low and count one, two, three",
        action_text=(
            "{helper} pulled the reed shade low while {hero} counted one, two, three and watched the bright stripe slide away. "
            "Cooler dimness settled over the basket instead of harsh noon glare."
        ),
        why_it_fits="hot light is eased by shade, not by tugging on the leaves themselves.",
        fixes_need="cooler shade over the leaves",
    ),
    "tie_ribbon": Care(
        key="tie_ribbon",
        phrase="loop a soft ribbon round the stem and count one, two, three",
        action_text=(
            "{hero} looped a soft ribbon round the leaning stem while {helper} held the bamboo stake still, and together they counted one, two, three. "
            "The knot stayed loose enough for growing and strong enough for support."
        ),
        why_it_fits="a leaning stem needs gentle support, not a hard pull or a sharp twist.",
        fixes_need="a gentle tie to the stake",
    ),
}

HERO_NAMES: dict[str, tuple[str, ...]] = {
    "girl": ("Mina", "Poppy", "Nell", "Tessa"),
    "boy": ("Theo", "Benji", "Ollie", "Ravi"),
}

HELPERS = ("Gran Poppy", "Aunt Junie", "Uncle Reed", "Mama Lark")


def _pick_hero(hero_kind: str, rng: random.Random) -> str:
    return rng.choice(HERO_NAMES[hero_kind])


def _pick_helper(rng: random.Random) -> str:
    return rng.choice(HELPERS)


def valid_combo(bed_key: str, problem_key: str, care_key: str) -> bool:
    if bed_key not in BEDS or problem_key not in PROBLEMS or care_key not in CARES:
        return False
    bed = BEDS[bed_key]
    problem = PROBLEMS[problem_key]
    care = CARES[care_key]
    return (
        problem.bed == bed.key
        and care.key in bed.allowed_cares
        and care.key in problem.compatible_cares
        and care.fixes_need == problem.need
    )


def invalid_reason(bed_key: str, problem_key: str, care_key: str) -> str:
    if bed_key not in BEDS:
        return f"No story: unknown bed {bed_key!r}."
    if problem_key not in PROBLEMS:
        return f"No story: unknown problem {problem_key!r}."
    if care_key not in CARES:
        return f"No story: unknown care {care_key!r}."

    bed = BEDS[bed_key]
    problem = PROBLEMS[problem_key]
    care = CARES[care_key]

    if problem.bed != bed.key:
        return (
            f"No story: {problem.label} does not belong at {bed.phrase}. "
            f"It belongs at {BEDS[problem.bed].phrase}."
        )
    if care.key not in bed.allowed_cares:
        return (
            f"No story: {bed.phrase} does not support the care {care.key!r}. "
            f"Try one of: {', '.join(bed.allowed_cares)}."
        )
    if care.key not in problem.compatible_cares or care.fixes_need != problem.need:
        return (
            f"No story: {care.phrase} does not solve {problem.label}. "
            f"That problem needs {problem.need}."
        )
    return "No story: invalid combination."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for bed_key in sorted(BEDS):
        for problem_key in sorted(PROBLEMS):
            for care_key in sorted(CARES):
                if valid_combo(bed_key, problem_key, care_key):
                    combos.append((bed_key, problem_key, care_key))
    return combos


def _matching_combos(args: argparse.Namespace) -> list[tuple[str, str, str]]:
    combos = valid_combos()
    filtered = [
        combo
        for combo in combos
        if (args.bed is None or combo[0] == args.bed)
        and (args.problem is None or combo[1] == args.problem)
        and (args.care is None or combo[2] == args.care)
    ]
    if args.bed and args.problem and args.care and not filtered:
        raise StoryError(invalid_reason(args.bed, args.problem, args.care))
    if not filtered:
        if args.bed or args.problem or args.care:
            raise StoryError("No story: no valid bed/problem/care combination matches the requested filters.")
        return combos
    return filtered


def _params_from_combo(
    args: argparse.Namespace,
    combo: tuple[str, str, str],
    index: int = 0,
) -> StoryParams:
    rng = random.Random(args.seed + index)
    hero_kind = args.hero_kind or rng.choice(sorted(HERO_NAMES))
    hero = args.hero or _pick_hero(hero_kind, rng)
    helper = args.helper or _pick_helper(rng)
    bed_key, problem_key, care_key = combo
    return StoryParams(
        bed=bed_key,
        problem=problem_key,
        care=care_key,
        hero=hero,
        hero_kind=hero_kind,
        helper=helper,
        seed=args.seed + index,
    )


def reasonableness_gate(params: StoryParams) -> None:
    if not valid_combo(params.bed, params.problem, params.care):
        raise StoryError(invalid_reason(params.bed, params.problem, params.care))


def build_world(params: StoryParams) -> World:
    reasonableness_gate(params)

    bed_cfg = BEDS[params.bed]
    problem_cfg = PROBLEMS[params.problem]
    care_cfg = CARES[params.care]
    world = World(params=params, bed_cfg=bed_cfg, problem_cfg=problem_cfg, care_cfg=care_cfg)

    hero = world.add(
        Entity(
            name=params.hero,
            kind=params.hero_kind,
            phrase=f"little {params.hero_kind}",
            location=bed_cfg.key,
            meters={"steps": 0.0, "listening": 1.0},
            memes={"care": 0.8, "curiosity": 0.7, "worry": 0.1, "relief": 0.0},
        )
    )
    helper = world.add(
        Entity(
            name=params.helper,
            kind="adult",
            phrase="trusted grown-up",
            location=bed_cfg.key,
            meters={"steadiness": 1.0},
            memes={"calm": 1.2, "care": 1.1},
        )
    )
    world.add(
        Entity(
            name=bed_cfg.key,
            kind="bed",
            phrase=bed_cfg.phrase,
            location="garden_center",
            meters={"quiet": 0.9, "order": 1.0},
            memes={"cozy": 1.0},
        )
    )
    world.add(
        Entity(
            name=problem_cfg.key,
            kind="plant_problem",
            phrase=problem_cfg.label,
            location=bed_cfg.key,
            meters={"signal": 1.0, "resolved": 0.0, "risk": 1.0},
            memes={"need": 1.0, "comfort": 0.2},
        )
    )
    world.add(
        Entity(
            name=care_cfg.key,
            kind="tool",
            phrase=care_cfg.phrase,
            location=bed_cfg.key,
            meters={"ready": 1.0},
            memes={"help": 1.0},
        )
    )

    hero.meters["steps"] += 1.0
    world.facts.update(
        {
            "setting": "garden_center",
            "style": "nursery_rhyme",
            "feature": "repetition",
            "seed_word": "faint",
            "hero": hero.name,
            "helper": helper.name,
            "bed": bed_cfg.key,
            "problem": problem_cfg.key,
            "care": care_cfg.key,
            "refrain": problem_cfg.refrain,
            "after_refrain": problem_cfg.after_refrain,
            "need": problem_cfg.need,
            "seed": str(params.seed),
        }
    )
    world.fired.append(f"opened_at_{bed_cfg.key}")
    return world


def _hero(world: World) -> Entity:
    return world.get(world.params.hero)


def _helper(world: World) -> Entity:
    return world.get(world.params.helper)


def _problem_ent(world: World) -> Entity:
    return world.get(world.problem_cfg.key)


def _bed_ent(world: World) -> Entity:
    return world.get(world.bed_cfg.key)


def _introduce(world: World) -> None:
    hero = _hero(world)
    bed = world.bed_cfg
    world.say(
        f"At {GARDEN_CENTER_NAME}, {hero.name} walked beside {world.params.helper} to {bed.phrase}. "
        f"There, {bed.opening_image}."
    )
    world.say(
        f"{hero.name} liked the hush of the garden center, because a kind child can hear even a faint little thing in such a place."
    )


def _hear_signal(world: World) -> None:
    hero = _hero(world)
    problem = world.problem_cfg
    problem_ent = _problem_ent(world)
    bed_ent = _bed_ent(world)

    hero.memes["curiosity"] += 0.5
    hero.memes["worry"] += 0.4
    problem_ent.meters["signal"] = 1.2
    bed_ent.meters["quiet"] = 0.4
    world.fired.append(f"heard_{problem.key}")

    world.para()
    world.say(
        f"Then {hero.name} heard {problem.signal_text}. {problem.refrain}"
    )
    world.say(
        f"{problem.observation} That was because {problem.cause}. {problem.consequence}"
    )


def _apply_care(world: World) -> None:
    hero = _hero(world)
    helper = _helper(world)
    problem = world.problem_cfg
    care = world.care_cfg
    problem_ent = _problem_ent(world)

    hero.memes["care"] += 0.5
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 0.2)
    helper.memes["care"] += 0.1
    problem_ent.meters["risk"] = 0.4
    world.fired.append(f"used_{care.key}")

    world.para()
    world.say(care.action_text.format(hero=hero.name, helper=helper.name))
    world.say(f"It fit because {care.why_it_fits}")
    world.say(f"{hero.name} listened to the problem before choosing the fix.")
    world.say(
        f"For one more tiny moment the bench still seemed to sing, {problem.refrain}"
    )


def _resolve(world: World) -> None:
    hero = _hero(world)
    problem = world.problem_cfg
    problem_ent = _problem_ent(world)
    bed_ent = _bed_ent(world)

    problem_ent.meters["signal"] = 0.0
    problem_ent.meters["risk"] = 0.0
    problem_ent.meters["resolved"] = 1.0
    problem_ent.memes["need"] = 0.0
    problem_ent.memes["comfort"] = 1.2
    bed_ent.meters["quiet"] = 1.2
    hero.memes["relief"] += 1.0
    hero.memes["care"] += 0.2
    world.fired.append(f"resolved_{problem.key}")

    world.para()
    world.say(problem.after_refrain)
    world.say(problem.final_image)
    world.say(
        f"When they closed up {GARDEN_CENTER_NAME}, {world.bed_cfg.ending_image}. "
        f"{hero.name} learned that a faint little warning is easiest to mend when patient hands listen early."
    )


def simulate(world: World) -> World:
    _introduce(world)
    _hear_signal(world)
    _apply_care(world)
    _resolve(world)
    return world


def _prompts(world: World) -> list[str]:
    return [
        f"Write a nursery-rhyme-style story set at a garden center, especially {world.bed_cfg.phrase}.",
        f"Include the word faint and use repetition through the refrain {world.problem_cfg.refrain}",
        f"Let the child solve a real plant problem by choosing {world.care_cfg.phrase} and end on a concrete closing image.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    helper = world.params.helper
    problem = world.problem_cfg
    care = world.care_cfg
    return [
        QAItem(
            "What was the faint signal in this story?",
            f"The faint signal was {problem.signal_text}. "
            f"It mattered because the sound came from a real plant problem instead of from an imaginary mystery.",
        ),
        QAItem(
            f"How did {hero} know what the plant needed?",
            f"{hero} looked and listened before acting, and then noticed that {problem.observation.lower()} "
            f"That showed the real cause: {problem.cause}.",
        ),
        QAItem(
            f"How did {hero} and {helper} solve the problem?",
            f"They chose to {care.phrase}. "
            f"That worked because {care.why_it_fits}",
        ),
        QAItem(
            "How did the ending prove that the world had changed?",
            f"The ending proved the change because the faint refrain gave way to a calmer one: {problem.after_refrain} "
            f"Then {world.bed_cfg.ending_image}, so the bench itself showed that the trouble was over.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    problem = world.problem_cfg
    care = world.care_cfg
    return [
        QAItem(
            "Why would this world reject the wrong care action?",
            f"It would reject the wrong care because each plant problem needs one believable kind of help. "
            f"In this sample, {problem.label} needs {problem.need}, so the action must physically provide that fix.",
        ),
        QAItem(
            "What object carries the problem in this story world?",
            f"The problem is carried by a real plant setup at the bench, not by a free-floating feeling. "
            f"Here that carrier is {problem.label}, which is why the cause and the cure both stay concrete.",
        ),
        QAItem(
            "How is repetition grounded instead of decorative here?",
            f"The repeated line is grounded in the plant's faint signal while the problem still exists. "
            f"Once the right care is applied, the refrain changes, so the repeated words reflect the new world state.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    world = simulate(build_world(params))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
combo(B,P,C) :-
    bed(B),
    problem(P),
    care(C),
    problem_at(P,B),
    bed_allows(B,C),
    problem_allows(P,C),
    care_fixes(C,N),
    problem_needs(P,N).

ok :- chosen(B,P,C), combo(B,P,C).

#show combo/3.
#show ok/0.
"""


def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for bed_key, bed in sorted(BEDS.items()):
        rows.append(fact("bed", bed_key))
        for care_key in bed.allowed_cares:
            rows.append(fact("bed_allows", bed_key, care_key))
    for problem_key, problem in sorted(PROBLEMS.items()):
        rows.append(fact("problem", problem_key))
        rows.append(fact("problem_at", problem_key, problem.bed))
        rows.append(fact("problem_needs", problem_key, problem.need))
        for care_key in problem.compatible_cares:
            rows.append(fact("problem_allows", problem_key, care_key))
    for care_key, care in sorted(CARES.items()):
        rows.append(fact("care", care_key))
        rows.append(fact("care_fixes", care_key, care.fixes_need))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.bed, params.problem, params.care) + "\n"
    return asp_facts() + chosen + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
    for model in solve(asp_program(), models=0):
        combos.update(atoms(model, "combo"))
    return combos


def _asp_accepts(params: StoryParams) -> bool:
    from storyworlds.asp import atoms, one_model

    model = one_model(asp_program(params))
    return bool(atoms(model, "ok"))


def verify() -> str:
    python_set = set(valid_combos())
    asp_set = asp_valid_combos()
    if python_set != asp_set:
        only_python = sorted(python_set - asp_set)
        only_asp = sorted(asp_set - python_set)
        raise StoryError(f"ASP/Python mismatch. only_python={only_python} only_asp={only_asp}")

    for index, combo in enumerate(sorted(python_set), 1):
        params = StoryParams(
            bed=combo[0],
            problem=combo[1],
            care=combo[2],
            hero=HERO_NAMES["girl"][0],
            hero_kind="girl",
            helper=HELPERS[0],
            seed=index,
        )
        if not _asp_accepts(params):
            raise StoryError(f"ASP failed to accept valid combo {combo!r}.")

        sample = generate(params)
        lower_story = sample.story.lower()
        if "garden center" not in lower_story:
            raise StoryError(f"Generated story for {combo!r} forgot the garden center setting.")
        if "faint" not in lower_story:
            raise StoryError(f"Generated story for {combo!r} forgot the seed word 'faint'.")
        if lower_story.count("faint, faint, faint") < 2:
            raise StoryError(f"Generated story for {combo!r} lost the repetition feature.")
        if "{" in sample.story or "}" in sample.story:
            raise StoryError(f"Generated story for {combo!r} leaked a template field.")
        if sample.story.count("\n\n") < 3:
            raise StoryError(f"Generated story for {combo!r} is missing a full beginning, turn, or ending.")
        if len(sample.prompts) != 3:
            raise StoryError(f"Generated story for {combo!r} has the wrong number of prompts.")
        if len(sample.story_qa) < 4 or len(sample.world_qa) < 3:
            raise StoryError(f"Generated story for {combo!r} has incomplete QA sets.")
        for qa in sample.story_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"Story QA answer is too thin for {combo!r}: {qa.question!r}")
        for qa in sample.world_qa:
            if qa.answer.count(".") < 2:
                raise StoryError(f"World QA answer is too thin for {combo!r}: {qa.question!r}")

    return f"OK: {len(python_set)} valid combos; ASP parity holds; generated stories pass quality checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate faint nursery-rhyme garden-center stories.")
    parser.add_argument("--bed", choices=sorted(BEDS), default=None)
    parser.add_argument("--problem", choices=sorted(PROBLEMS), default=None)
    parser.add_argument("--care", choices=sorted(CARES), default=None)
    parser.add_argument("--hero", default=None)
    parser.add_argument("--hero-kind", choices=sorted(HERO_NAMES), default=None)
    parser.add_argument("--helper", choices=HELPERS, default=None)
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


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    combo = rng.choice(_matching_combos(args))
    return _params_from_combo(args, combo, index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Story prompts ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story Q&A ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World Q&A ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for bed_key, problem_key, care_key in sorted(asp_valid_combos()):
        print(f"{bed_key}\t{problem_key}\t{care_key}")


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

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

        samples: list[StorySample] = []
        if args.all:
            combos = _matching_combos(args)
            for index, combo in enumerate(combos, 1):
                samples.append(generate(_params_from_combo(args, combo, index)))
        else:
            count = max(1, args.n)
            for index in range(count):
                rng = random.Random(args.seed + index)
                samples.append(generate(resolve_params(args, rng, index)))

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
            return 0

        for index, sample in enumerate(samples, 1):
            header = ""
            if args.all:
                p = sample.params
                header = f"### {p.bed} / {p.problem} / {p.care}"
            elif len(samples) > 1:
                header = f"### variant {index}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index != len(samples):
                print("\n" + "=" * 72 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
