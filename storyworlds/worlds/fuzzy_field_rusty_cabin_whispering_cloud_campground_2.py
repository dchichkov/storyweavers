#!/usr/bin/env python3
"""
fuzzy_field_rusty_cabin_whispering_cloud_campground_2.py
========================================================

Standalone StoryWorld for the seed:

    words: fuzzy field, rusty cabin, whispering cloud
    setting: campground
    features: Surprise, Humor
    style: Heartwarming

Internal source tale:
    A child at a campground hears a whispering cloud above a rusty cabin and
    thinks the sky is making silly jokes. The child and a funny animal helper
    search a fuzzy field, discover that a missing cabin part is making the
    whisper, and fix it just before a sprinkle. The surprise is that the cloud
    was not spooky at all; it was the wind carrying the cabin's problem in a
    funny voice.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Problem:
    key: str
    cabin_part: str
    missing_item: str
    symptom: str
    whisper_words: str
    find_spot: str
    repair_action: str
    ending_image: str
    accepts: tuple[str, ...]


@dataclass(frozen=True)
class Helper:
    key: str
    phrase: str
    name: str
    pronoun: str
    search_line: str
    comic_beat: str
    comfort_line: str


@dataclass(frozen=True)
class Mentor:
    key: str
    display: str
    cozy_action: str


@dataclass
class StoryParams:
    problem: str
    helper: str
    hero: str
    gender: str
    mentor: str
    seed: int


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = round(self.meters.get(key, 0.0) + amount, 2)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)


@dataclass
class Rule:
    name: str
    apply: Callable[["World"], bool]


@dataclass
class World:
    params: StoryParams
    problem: Problem
    helper: Helper
    mentor: Mentor
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    camp_name: str = "Fern Lantern Campground"
    whisper_heard: str = ""
    reveal: str = ""
    ending_note: str = ""
    drizzle_started: bool = False
    item_found: bool = False
    issue_fixed: bool = False

    def note(self, text: str) -> None:
        self.history.append(text)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        for name, ent in self.entities.items():
            meters = ", ".join(f"{k}={v}" for k, v in sorted(ent.meters.items()))
            memes = ", ".join(f"{k}={v}" for k, v in sorted(ent.memes.items()))
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            parts = []
            if meters:
                parts.append(f"meters[{meters}]")
            if memes:
                parts.append(f"memes[{memes}]")
            if tags:
                parts.append(f"tags[{tags}]")
            rows.append(f"  {name:<12} ({ent.kind:<10}) " + " ".join(parts))
        rows.append(f"  whisper: {self.whisper_heard}")
        rows.append(f"  reveal: {self.reveal}")
        rows.append(f"  ending: {self.ending_note}")
        rows.append(f"  fired rules: {self.fired_rules}")
        rows.append("  history:")
        for step in self.history:
            rows.append(f"    - {step}")
        return "\n".join(rows)


PROBLEMS: dict[str, Problem] = {
    "shutter": Problem(
        key="shutter",
        cabin_part="left shutter",
        missing_item="star latch",
        symptom="kept tapping the cabin wall and whistling through the gap",
        whisper_words="Button my nose",
        find_spot="under a drift of seed fluff beside the stepping stones",
        repair_action="clicked the star latch back onto the shutter peg and tied it snug with a strip of camp ribbon",
        ending_image="its left shutter resting still, like an eyelid after a long giggle",
        accepts=("pup", "raccoon"),
    ),
    "sign": Problem(
        key="sign",
        cabin_part="cocoa sign",
        missing_item="heart hook",
        symptom="kept clacking against the porch rail whenever the wind leaned in",
        whisper_words="Hold my smile",
        find_spot="caught low in the fuzzy grass near the cocoa stump",
        repair_action="hung the heart hook again and straightened the cocoa sign until it pointed proudly at the kettle shelf",
        ending_image="its cocoa sign swinging in one straight, happy line above the porch",
        accepts=("raccoon", "goose"),
    ),
    "chimney": Problem(
        key="chimney",
        cabin_part="tin chimney cap",
        missing_item="round pin",
        symptom="danced a rusty jig and made a flute sound in every puff of wind",
        whisper_words="Mind my hat",
        find_spot="tucked where the fuzzy field met the little woodpile",
        repair_action="slid the round pin back through the chimney cap and pressed it firm with the camp tongs",
        ending_image="its chimney cap sitting proper and polite above one warm ribbon of smoke",
        accepts=("pup", "goose"),
    ),
}

HELPERS: dict[str, Helper] = {
    "pup": Helper(
        key="pup",
        phrase="a bouncy pup named Button",
        name="Button",
        pronoun="he",
        search_line="Button zigzagged with his nose so close to the ground that his ears collected fuzz like two tiny mops",
        comic_beat="He sneezed once, blinked at the fluff on his snout, and wagged as if sneezing were expert detective work.",
        comfort_line="pressed his warm side against the child's knee",
    ),
    "raccoon": Helper(
        key="raccoon",
        phrase="a tidy raccoon named Pebble",
        name="Pebble",
        pronoun="he",
        search_line="Pebble paused at every sparkle and patted the fuzzy grass with careful paws, refusing to miss even the shyest glint",
        comic_beat="When he found something shiny, he polished it on his tummy first, as if the whole campground deserved a fancy repair.",
        comfort_line="chittered softly and pointed with one clever paw",
    ),
    "goose": Helper(
        key="goose",
        phrase="a waddly goose named Marmalade",
        name="Marmalade",
        pronoun="she",
        search_line="Marmalade marched in brave little loops through the fuzzy field and honked at every clump that looked suspiciously important",
        comic_beat="She accused three dandelions before throwing one triumphant honk at the real metal piece.",
        comfort_line="stood tall like a feathery guard at the cabin steps",
    ),
}

MENTORS: dict[str, Mentor] = {
    "aunt_bea": Mentor("aunt_bea", "Aunt Bea", "warmed cocoa in a dented blue pot"),
    "ranger_sol": Mentor("ranger_sol", "Ranger Sol", "hung dry socks beside the office lantern"),
    "grandpa_ivo": Mentor("grandpa_ivo", "Grandpa Ivo", "stacked kindling into a neat little tower"),
    "mama_tess": Mentor("mama_tess", "Mama Tess", "folded blankets for the chilly tent benches"),
}

HEROES = {
    "girl": ("Mira", "Nora", "June", "Lina", "Tess"),
    "boy": ("Theo", "Finn", "Eli", "Sam", "Noah"),
}


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def valid_combo(problem: str, helper: str) -> bool:
    if problem not in PROBLEMS or helper not in HELPERS:
        return False
    return helper in PROBLEMS[problem].accepts


def invalid_reason(problem: str, helper: str) -> str:
    if problem not in PROBLEMS:
        return f"No story: unknown cabin problem {problem!r}."
    if helper not in HELPERS:
        return f"No story: unknown helper {helper!r}."
    prob = PROBLEMS[problem]
    if helper not in prob.accepts:
        allowed = ", ".join(prob.accepts)
        return (
            f"No story: {HELPERS[helper].phrase} is not a good fit for the {prob.cabin_part} repair. "
            f"Try one of: {allowed}."
        )
    return "No story: that campground repair is not reasonable."


def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for problem in PROBLEMS:
        for helper in HELPERS:
            if valid_combo(problem, helper):
                combos.append((problem, helper))
    return combos


def _r_set_evening(world: World) -> bool:
    hero = world.entities["Hero"]
    field_ent = world.entities["Field"]
    cabin = world.entities["Cabin"]
    cloud = world.entities["Cloud"]
    hero.add_meter("steps", 8.0)
    hero.add_meme("curiosity", 0.7)
    field_ent.add_meter("fluff_depth", 0.8)
    field_ent.add_meme("softness", 0.6)
    cabin.add_meter("rust_level", 0.7)
    cabin.add_meme("worry", 0.5)
    cloud.add_meter("rain_load", 0.4)
    cloud.add_meter("height", 0.6)
    cloud.add_meme("mystery", 0.8)
    world.note(
        f"At {world.camp_name}, the hero arrived by the rusty cabin beside the fuzzy field while a whispering cloud drifted low."
    )
    return True


def _r_whisper_problem(world: World) -> bool:
    hero = world.entities["Hero"]
    cabin = world.entities["Cabin"]
    cloud = world.entities["Cloud"]
    problem = world.problem
    hero.add_meme("surprise", 0.9)
    hero.add_meme("humor", 0.5)
    cabin.add_meter("rattle", 1.0)
    cabin.tags["problem"] = problem.cabin_part
    cloud.tags["carried_words"] = problem.whisper_words
    world.whisper_heard = problem.whisper_words
    world.note(
        f"The wind crossed the {problem.cabin_part} and turned its rattle into the words '{problem.whisper_words}.'"
    )
    return True


def _r_search_field(world: World) -> bool:
    hero = world.entities["Hero"]
    helper = world.entities["Helper"]
    field_ent = world.entities["Field"]
    item = world.entities["Item"]
    hero.add_meter("steps", 14.0)
    hero.add_meme("care", 0.8)
    helper.add_meter("search_loops", 3.0)
    helper.add_meme("playfulness", 0.7)
    field_ent.add_meter("paths_pressed", 0.4)
    item.tags["found_spot"] = world.problem.find_spot
    item.tags["status"] = "found"
    item.add_meter("shine", 0.8)
    world.item_found = True
    world.note(
        f"The hero and {world.helper.name} searched the fuzzy field and found the {world.problem.missing_item} {world.problem.find_spot}."
    )
    return True


def _r_repair_and_rest(world: World) -> bool:
    hero = world.entities["Hero"]
    cabin = world.entities["Cabin"]
    cloud = world.entities["Cloud"]
    item = world.entities["Item"]
    camp = world.entities["Campground"]
    hero.add_meme("belonging", 0.9)
    hero.add_meme("humor", 0.4)
    cabin.add_meter("stability", 1.0)
    cabin.add_meme("relief", 1.0)
    cabin.tags["status"] = "repaired"
    cloud.add_meter("rain_load", 0.2)
    cloud.add_meme("gentleness", 0.7)
    item.tags["status"] = "installed"
    camp.add_meme("coziness", 1.1)
    world.drizzle_started = True
    world.issue_fixed = True
    world.reveal = (
        f"It was not a spooky voice at all. The wind was slipping through the loose {world.problem.cabin_part} and borrowing the cloud's whisper."
    )
    world.ending_note = world.problem.ending_image
    world.note(
        f"The hero repaired the {world.problem.cabin_part} with the {world.problem.missing_item}, and the drizzle that followed felt like a soft thank-you."
    )
    return True


RULES = [
    Rule("set_evening", _r_set_evening),
    Rule("whisper_problem", _r_whisper_problem),
    Rule("search_field", _r_search_field),
    Rule("repair_and_rest", _r_repair_and_rest),
]


def build_world(params: StoryParams) -> World:
    if not valid_combo(params.problem, params.helper):
        raise StoryError(invalid_reason(params.problem, params.helper))
    problem = PROBLEMS[params.problem]
    helper = HELPERS[params.helper]
    mentor = MENTORS[params.mentor]
    world = World(params=params, problem=problem, helper=helper, mentor=mentor)
    world.entities["Hero"] = Entity(
        params.hero,
        params.gender,
        meters={"pocket_ribbon": 1.0},
        memes={"hope": 0.4},
        tags={"role": "camper"},
    )
    world.entities["Helper"] = Entity(
        helper.name,
        helper.key,
        meters={"energy": 1.0},
        memes={"loyalty": 0.8},
        tags={"role": "helper"},
    )
    world.entities["Mentor"] = Entity(
        mentor.display,
        "mentor",
        meters={"cocoa_mugs": 2.0},
        memes={"calm": 1.0},
        tags={"role": "steady grownup"},
    )
    world.entities["Cabin"] = Entity(
        "cabin",
        "building",
        meters={"boards": 12.0},
        memes={"history": 0.9},
        tags={"state": "rusty"},
    )
    world.entities["Field"] = Entity(
        "field",
        "place",
        meters={"width_m": 16.0},
        memes={"welcome": 0.6},
        tags={"texture": "fuzzy"},
    )
    world.entities["Cloud"] = Entity(
        "cloud",
        "weather",
        meters={"span_m": 18.0},
        memes={"hush": 0.8},
        tags={"voice": "whispering"},
    )
    world.entities["Item"] = Entity(
        problem.missing_item,
        "part",
        meters={"size_cm": 8.0},
        memes={"importance": 0.7},
        tags={"status": "lost"},
    )
    world.entities["Campground"] = Entity(
        world.camp_name,
        "campground",
        meters={"lanterns": 4.0},
        memes={"community": 0.8},
        tags={"setting": "campground"},
    )
    for rule in RULES:
        if rule.apply(world):
            world.fired_rules.append(rule.name)
    return world


def _render_story(world: World) -> str:
    hero = world.params.hero
    helper = world.helper
    mentor = world.mentor
    problem = world.problem
    he, his, _him = _pronouns(world.params.gender)

    opening = (
        f"At {world.camp_name}, {hero} was carrying mugs past a rusty cabin beside a fuzzy field while "
        f"{mentor.display} {mentor.cozy_action}. Above the pine tops floated a whispering cloud, long and silver, "
        f"as if it knew every little secret in the campground."
    )
    tension = (
        f"Then the wind slipped across the cabin and the {problem.cabin_part} {problem.symptom}. "
        f'"{problem.whisper_words}," the cloud seemed to say. {hero} stopped so fast that {helper.phrase} almost bumped {his} boots, '
        f"and for one funny second {he} wondered whether the cabin had decided to talk."
    )
    search = (
        f"{mentor.display} listened once and said, \"That sounds more worried than spooky.\" "
        f"So {hero} and {helper.phrase} went searching through the fuzzy field. {helper.search_line}. "
        f"{helper.comic_beat}"
    )
    turn = (
        f"At last they found the missing {problem.missing_item} {problem.find_spot}. "
        f"{world.reveal} {helper.name} {helper.comfort_line}, and {hero} laughed because the whole mystery had sounded much scarier than it really was."
    )
    ending = (
        f"{hero} {problem.repair_action}. A tiny sprinkle began just after the fix, but now the cabin only gave a soft creak, "
        f"not a worried whistle. By supper time the rusty cabin looked peaceful, {problem.ending_image}, and the whispering cloud drifted away so softly "
        f"that it almost sounded like \"thank you.\""
    )
    return "\n\n".join([opening, tension, search, turn, ending])


def _prompts(world: World) -> list[str]:
    return [
        'Write a heartwarming campground story for children using the words "fuzzy field", "rusty cabin", and "whispering cloud".',
        f"Tell a funny surprise story where {world.params.hero} and {world.helper.phrase} solve a mystery around a cabin's {world.problem.cabin_part}.",
        "Write a cozy campsite tale where a child thinks a cloud is speaking, then discovers a small problem that can be fixed with kindness.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    hero = world.params.hero
    helper = world.helper
    mentor = world.mentor.display
    problem = world.problem
    return [
        QAItem(
            "What made the child stop and listen?",
            f"{hero} stopped when the {problem.cabin_part} started making the whisper '{problem.whisper_words}.' The sound was funny, but it also made the cabin seem like it needed help.",
        ),
        QAItem(
            "Why did the mystery feel surprising at first?",
            f"It sounded as if the whispering cloud were talking to the rusty cabin. The surprise was that the sound really came from wind slipping through the loose {problem.cabin_part}.",
        ),
        QAItem(
            "How did the helper animal contribute?",
            f"{helper.name} helped search the fuzzy field until the missing {problem.missing_item} was found. The helper also kept the moment light and brave, which helped {hero} stay cheerful instead of scared.",
        ),
        QAItem(
            "What did they find in the fuzzy field?",
            f"They found the missing {problem.missing_item} {problem.find_spot}. That little piece was exactly what the cabin needed to stop whistling in a silly voice.",
        ),
        QAItem(
            "How did the story end differently from the middle?",
            f"At first the cabin sounded worried and strange, almost as if it were whispering from the sky. By the end the repair was done, the drizzle felt gentle, and the campground became cozy again.",
        ),
        QAItem(
            "What role did the grownup play?",
            f"{mentor} helped by listening calmly and calling the sound worried instead of spooky. That steady reaction guided {hero} toward helping instead of panicking.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    problem = world.problem
    return [
        QAItem(
            "Why can wind make a cabin sound like it is whispering?",
            f"Wind can whistle when it slides through a loose gap or rattling part. In this world, the loose {problem.cabin_part} turned moving air into a silly voice.",
        ),
        QAItem(
            "Why might a fuzzy field hide a small metal piece?",
            "Soft seed fluff and tall grass can cover something small very quickly. A shiny part can fall low into the plants and disappear until someone searches carefully.",
        ),
        QAItem(
            "Why is fixing a campground cabin a kind thing to do?",
            "A shared cabin helps many campers stay comfortable and safe. Repairing one small problem can make the whole place feel welcoming again.",
        ),
        QAItem(
            "Why did the drizzle feel gentle instead of scary at the end?",
            "The main problem was already solved, so the weather no longer felt like a threat. Once the cabin was steady, the rain became part of the cozy ending instead of the mystery.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    if params.problem not in PROBLEMS:
        raise StoryError(f"No story: unknown cabin problem {params.problem!r}.")
    if params.helper not in HELPERS:
        raise StoryError(f"No story: unknown helper {params.helper!r}.")
    if params.mentor not in MENTORS:
        raise StoryError(f"No story: unknown mentor {params.mentor!r}.")
    if params.gender not in HEROES:
        raise StoryError(f"No story: unknown gender bucket {params.gender!r}.")
    if not valid_combo(params.problem, params.helper):
        raise StoryError(invalid_reason(params.problem, params.helper))
    world = build_world(params)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = """
combo(P,H) :-
    problem(P),
    helper(H),
    accepts(P,H).

ok :-
    chosen(P,H),
    combo(P,H).

#show combo/2.
#show ok/0.
"""


def asp_facts() -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for problem, data in PROBLEMS.items():
        rows.append(fact("problem", problem))
        for helper in data.accepts:
            rows.append(fact("accepts", problem, helper))
    for helper in HELPERS:
        rows.append(fact("helper", helper))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    chosen = ""
    if params is not None:
        from storyworlds.asp import fact

        chosen = fact("chosen", params.problem, params.helper) + "\n"
    return asp_facts() + chosen + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str]] = set()
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

    seed_checks = ("fuzzy field", "rusty cabin", "whispering cloud", "campground")
    for index, combo in enumerate(sorted(py), 1):
        params = StoryParams(
            problem=combo[0],
            helper=combo[1],
            hero="Mira",
            gender="girl",
            mentor="aunt_bea",
            seed=1000 + index,
        )
        if not asp_verify(params):
            raise StoryError(f"ASP verify failed for combo {combo}.")
        sample = generate(params)
        lowered = sample.story.lower()
        missing = [token for token in seed_checks if token not in lowered]
        if missing:
            raise StoryError(f"Generated story for {combo} missed required seed terms: {missing}")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 3:
            raise StoryError(f"Generated story for {combo} has incomplete QA.")
        if sample.world is None or not sample.world.issue_fixed or not sample.world.item_found:
            raise StoryError(f"Generated story for {combo} did not complete its world state.")
    return f"OK: clingo gate matches valid_combos() ({len(py)} combos) and all generated stories pass seed/state checks."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate fuzzy field campground StoryWorld samples.")
    parser.add_argument("--problem", choices=sorted(PROBLEMS))
    parser.add_argument("--helper", choices=sorted(HELPERS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES), default=None)
    parser.add_argument("--mentor", choices=sorted(MENTORS), default=None)
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


def _params_from_combo(
    combo: tuple[str, str],
    args: argparse.Namespace,
    rng: random.Random,
    *,
    seed: int,
) -> StoryParams:
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    mentor = args.mentor or rng.choice(sorted(MENTORS))
    return StoryParams(
        problem=combo[0],
        helper=combo[1],
        hero=hero,
        gender=gender,
        mentor=mentor,
        seed=seed,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    seed = args.seed + index
    local_rng = random.Random(seed)
    combos = valid_combos()
    if args.problem and args.helper:
        if not valid_combo(args.problem, args.helper):
            raise StoryError(invalid_reason(args.problem, args.helper))
        combo = (args.problem, args.helper)
    elif args.problem:
        options = [helper for helper in PROBLEMS[args.problem].accepts]
        combo = (args.problem, local_rng.choice(options))
    elif args.helper:
        options = [problem for problem, helper in combos if helper == args.helper]
        combo = (local_rng.choice(options), args.helper)
    else:
        combo = local_rng.choice(combos)
    return _params_from_combo(combo, args, local_rng, seed=seed)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Generation prompts -- asks that would produce this story ==")
    for index, prompt in enumerate(sample.prompts, 1):
        print(f"{index}. {prompt}")
    print("\n== (2) Story questions -- answerable from the story ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    as_json: bool = False,
    header: str = "",
) -> None:
    if as_json:
        print(sample.to_json())
        return
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for problem, helper in sorted(asp_valid_combos()):
        print(f"{problem}\t{helper}")


def main(argv: Iterable[str] | None = None) -> int:
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
            for index, combo in enumerate(combos, 1):
                sample = generate(
                    _params_from_combo(
                        combo,
                        args,
                        random.Random(args.seed + index),
                        seed=args.seed + index,
                    )
                )
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    as_json=args.json,
                    header="" if args.json else f"### {combo[0]} with {combo[1]}",
                )
                if index != len(combos) and not args.json:
                    print("\n" + "=" * 70 + "\n")
            return 0

        count = max(1, args.n)
        rng = random.Random(args.seed)
        for index in range(count):
            sample = generate(resolve_params(args, rng, index))
            emit(
                sample,
                trace=args.trace,
                qa=args.qa,
                as_json=args.json,
                header="" if args.json or count == 1 else f"### variant {index + 1}",
            )
            if index != count - 1 and not args.json:
                print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
