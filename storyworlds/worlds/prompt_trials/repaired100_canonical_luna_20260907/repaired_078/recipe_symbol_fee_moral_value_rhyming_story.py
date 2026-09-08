#!/usr/bin/env python3
"""A child-facing rhyming storyworld about a recipe, a symbol, a fee, and moral value."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

STORYWORLDS_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(STORYWORLDS_DIR))
sys.path.insert(0, str(STORYWORLDS_DIR.parent))
from results import QAItem, StoryError, StorySample  # noqa: E402


TITLE = "The Recipe, the Symbol, and the Fair Fee"


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    baker: str = "Luna"
    recipe: str = "the moonberry muffin recipe"
    symbol: str = "a silver moon"
    fee: str = "one kind deed"
    place: str = "the village bake tent"
    seed: Optional[int] = None


@dataclass(frozen=True)
class Trial:
    name: str
    problem: str
    clue: str
    wrong_turn: str
    consequence: str
    exchange: str
    plan: str
    rhyme: str
    resolution: str
    ending: str
    helpers: tuple[str, str]


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple[str, str]] = field(default_factory=set)
    facts: dict[str, object] = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


TRIALS = [
    Trial(
        "the empty basket",
        "the recipe basket held only three berries instead of enough for every child",
        "a small sign showed that the fee was one helpful deed, not a coin",
        "offered a silver coin to buy the missing berries",
        "the coin could not fill the basket, and the waiting children grew quiet",
        '"Could money solve this?" asked Pip. Luna shook her head. "The symbol asks for kindness, so let us look for a kind deed."',
        "Pip gathered fallen berries, and the gardener shared ripe ones from the sunny row",
        "Pick and share, show that you care; kind deeds make the feast fair!",
        "the basket filled after the children helped gather and share the berries",
        "the moonberry muffins rose while every helper found a warm place at the table",
        ("Pip", "the gardener"),
    ),
    Trial(
        "the upside-down symbol",
        "the silver moon symbol had been hung upside down beside the recipe",
        "the little stars on its edge pointed toward the line that explained the fee",
        "guessed that the fee meant three shiny buttons",
        "the buttons distracted everyone from the recipe's careful order",
        '"The symbol has a secret direction," said Mira. "Then we should turn it gently," said Luna.',
        "Mira turned the symbol, and Luna read the recipe aloud while the children checked each step",
        "Turn and see, read carefully; fair work grows from clarity!",
        "the turned symbol revealed that the fee was helping one neighbor before taking a muffin",
        "the moon shone upright as children carried muffins to neighbors who needed a snack",
        ("Mira", "the children"),
    ),
    Trial(
        "the missing spoon",
        "the mixing bowl was ready, but the recipe's wooden spoon had vanished",
        "a flour trail curved from the bowl toward the community wash stand",
        "blamed the youngest helper for taking it",
        "the blame made the helper hide instead of joining the search",
        '"I saw flour by the wash stand," said Jo. "Let us ask before we accuse," Luna replied.',
        "Jo followed the flour trail, and the youngest helper washed the spoon for everyone",
        "Ask, then seek; be kind, not bleak; truth helps every friend speak!",
        "the spoon was found, and the helper who washed it was welcomed back",
        "the muffins tasted sweeter because apology and help had joined the batter",
        ("Jo", "the youngest helper"),
    ),
    Trial(
        "the tall price",
        "a painted board announced a fee larger than any family could afford",
        "the recipe card carried a moon symbol beside the words 'value is not price'",
        "told families that only rich visitors could enter",
        "several hungry children turned away from the bake tent",
        '"The board feels unfair," said Nia. Luna answered, "Let us change the fee to a deed everyone can offer."',
        "Nia rewrote the board so visitors could sweep, share, teach, or help",
        "Not too high, let kindness fly; fair fees let all come by!",
        "the new deed fee welcomed families without pretending that money measured a person's worth",
        "the tent filled with music, and every small good deed became part of the feast",
        ("Nia", "the families"),
    ),
    Trial(
        "the copied recipe",
        "someone had copied the recipe but left out the reason for the silver moon symbol",
        "the original card said the symbol reminded cooks to include people who were left out",
        "copied only the ingredient list",
        "the muffins looked fine, but one shy child received no invitation",
        '"A recipe needs more than ingredients," said Luna. "It needs the reason we share," said Sol.',
        "Sol added the symbol's meaning, and Luna invited the shy child to stir",
        "Write the why, let kindness grow high; shared meaning helps us try!",
        "the completed recipe joined its steps to the moral value of inclusion",
        "the shy child stirred the final bowl, and the silver moon gleamed over a larger circle",
        ("Sol", "the shy child"),
    ),
    Trial(
        "the crooked measure",
        "the measuring cups made the recipe seem to ask for different amounts",
        "each cup bore a matching dot, and the symbol showed which cup belonged to each line",
        "picked the biggest cup because it looked generous",
        "too much flour made the first batter heavy and lumpy",
        '"Generous does not mean careless," said Bea. Luna replied, "We can measure fairly and begin again."',
        "Bea matched the dots, and Luna measured each ingredient with patient hands",
        "Match and weigh, be fair and straight; care makes every batch taste great!",
        "the team used the symbol to match every measure and mixed a smooth new batter",
        "round muffins cooled in a row, each one made with care rather than guesswork",
        ("Bea", "the team"),
    ),
    Trial(
        "the locked cupboard",
        "the best berries were behind a cupboard whose key was held by the fee collector",
        "the collector's ledger showed that the fee was meant to repair the public oven",
        "tried to sneak the key away",
        "the cupboard stayed locked and trust in the bake tent began to crack",
        '"A hidden key will not make a fair fee," said Luna. "Then we should ask openly," said Taro.',
        "Taro asked the collector, and the children helped clean the oven before receiving berries",
        "Clean and ask, do every task; honest hands can share the flask!",
        "the children earned the berries through an open, useful deed",
        "the repaired oven glowed, and the berry muffins baked for everyone to enjoy",
        ("Taro", "the fee collector"),
    ),
    Trial(
        "the silent visitor",
        "a visitor who could not read the recipe waited outside the tent",
        "the silver moon symbol appeared beside picture instructions",
        "said the visitor would have to leave",
        "the visitor lowered their head and missed the chance to help",
        '"Pictures can speak," said Aya. Luna smiled. "We can show the recipe and welcome another pair of hands."',
        "Aya used the symbol cards, and the visitor helped fold paper cups",
        "Show the sign, make welcome shine; every friend can join the line!",
        "the picture recipe and a welcoming deed opened the tent to the visitor",
        "paper cups circled the table as new hands helped pass the warm muffins",
        ("Aya", "the visitor"),
    ),
]


PLACES = ["the village bake tent", "the moonlit market", "the school courtyard"]
BAKERS = ["Luna", "Milo", "Nia", "Sol"]
RECIPES = ["the moonberry muffin recipe", "the honey-cake recipe", "the starlight biscuit recipe"]
SYMBOLS = ["a silver moon", "a blue star", "a golden heart"]
FEES = ["one kind deed", "a helpful hour", "a promise to share"]


def choose_trial(params: StoryParams) -> tuple[Trial, int]:
    seed = params.seed if params.seed is not None else 0
    return TRIALS[seed % len(TRIALS)], (seed // len(TRIALS)) % 4


def setup_world(params: StoryParams, trial: Trial, route_index: int) -> World:
    world = World(params.place)
    baker = world.add(Entity("baker", "character", "baker", params.baker, memes={"moral_value": 0.0}))
    recipe = world.add(Entity("recipe", "object", "recipe", params.recipe, owner=baker.id, meters={"complete": 0.0}))
    symbol = world.add(Entity("symbol", "object", "symbol", params.symbol, meters={"understood": 0.0}))
    fee = world.add(Entity("fee", "concept", "fee", params.fee, meters={"fair": 0.0}))
    world.facts.update(
        baker=baker,
        recipe=recipe,
        symbol=symbol,
        fee=fee,
        trial=trial,
        route_index=route_index,
        moral_value="fairness, kindness, and respect matter more than money or status",
    )
    return world


def tell(params: StoryParams) -> World:
    trial, route_index = choose_trial(params)
    world = setup_world(params, trial, route_index)
    baker = world.facts["baker"]
    recipe = world.facts["recipe"]
    symbol = world.facts["symbol"]
    fee = world.facts["fee"]

    openings = [
        f"In {world.place}, {baker.label} kept {recipe.label} beneath a cloth of blue.",
        f"At {world.place}, {baker.label} mixed hope with {recipe.label} as the morning dew.",
        f"By {world.place}, {baker.label} hung {symbol.label} where the warm oven shone.",
        f"Near {world.place}, {baker.label} set out {recipe.label} for neighbors to share at home.",
    ]
    world.say(openings[route_index])
    world.say(
        f"The recipe made a treat for every friend, and {symbol.label} reminded the bakers that "
        f"the moral value was to include people and treat them fairly. The fee was {fee.label}."
    )
    world.say("A small problem appeared, and the smooth plan began to sway.")
    world.para()

    world.say(f"Then {trial.problem}.")
    world.say(f"{trial.clue.capitalize()}.")
    world.say(trial.exchange)
    world.say(f"For one hurried moment, {baker.label} {trial.wrong_turn}. As a result, {trial.consequence}.")
    baker.memes["moral_value"] = 0.5
    recipe.meters["complete"] = 0.25
    world.fired.add(("hasty_choice", trial.name))
    world.para()

    world.say(f"{baker.label} lifted {symbol.label}. “Let us read the clue and choose what is fair.”")
    world.say(f"Together, {trial.plan}.")
    world.say(f"They sang, “{trial.rhyme}”")
    world.facts.update(
        clue=trial.clue,
        setback=trial.consequence,
        plan=trial.plan,
        helpers=trial.helpers,
    )
    world.fired.add(("moral_value_guided_plan", trial.name))
    world.para()

    symbol.meters["understood"] = 1.0
    fee.meters["fair"] = 1.0
    recipe.meters["complete"] = 1.0
    baker.memes["moral_value"] = 1.0
    world.say(f"Because they followed the clue, {trial.resolution}.")
    world.say(
        f"{baker.label} smiled. “A fee should open a door, not close one. "
        "The true value is in the good we do together.”"
    )
    world.say(f"At last, {trial.ending}.")
    world.fired.add(("recipe_shared_fairly", trial.name))
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a child-friendly rhyming story about {facts['baker'].label}, {facts['recipe'].label}, {facts['symbol'].label}, and a fee of {facts['fee'].label}.",
        "Show a problem, a spoken conversation, a moral choice, and a resolution where kindness changes what happens.",
        "Use the moral value that a person's worth is not measured by money, and end with a concrete image of sharing.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    trial: Trial = facts["trial"]  # type: ignore[assignment]
    baker: Entity = facts["baker"]  # type: ignore[assignment]
    recipe: Entity = facts["recipe"]  # type: ignore[assignment]
    symbol: Entity = facts["symbol"]  # type: ignore[assignment]
    fee: Entity = facts["fee"]  # type: ignore[assignment]
    helpers = f"{trial.helpers[0]} and {trial.helpers[1]}"
    return [
        QAItem(
            question=f"What was {recipe.label} used for?",
            answer=f"{baker.label} used {recipe.label} to prepare a shared treat at {world.place}, not just to make food for one person.",
        ),
        QAItem(
            question=f"What did {symbol.label} remind the bakers to do?",
            answer=f"It reminded them that the moral value was to include people and treat them fairly, especially when deciding how to use the fee.",
        ),
        QAItem(
            question="What was the fee?",
            answer=f"The fee was {fee.label}. It was meant to invite a useful, kind contribution rather than measure a person's worth with money.",
        ),
        QAItem(
            question="What went wrong before the team changed its plan?",
            answer=f"{trial.wrong_turn.capitalize()} This caused a setback: {trial.consequence}.",
        ),
        QAItem(
            question="How did the characters solve the problem?",
            answer=f"{helpers} helped by {trial.plan}. The team followed the clue instead of guessing or excluding someone.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"{trial.resolution.capitalize()} The recipe was complete, the symbol was understood, and the fee became fair.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a recipe?",
            answer="A recipe is a set of instructions that tells people what ingredients and steps to use when making something.",
        ),
        QAItem(
            question="What is a symbol?",
            answer="A symbol is a picture or mark that stands for an idea, object, or message.",
        ),
        QAItem(
            question="What is a fee?",
            answer="A fee is something requested in exchange for entering, receiving, or using something. A fair fee should not exclude people who cannot pay money.",
        ),
        QAItem(
            question="What moral value does this world teach?",
            answer="It teaches fairness, kindness, inclusion, and the idea that a person's moral worth is not measured by money.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== (2) Story questions =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== (3) World knowledge questions =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {key: value for key, value in entity.meters.items() if value}
        memes = {key: value for key, value in entity.memes.items() if value}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {entity.id:8} ({entity.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, _ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = ["recipe_world.", "moral_value.", "sharing."]
    for value in PLACES:
        lines.append(asp.fact("place", value))
    for value in RECIPES:
        lines.append(asp.fact("recipe", value))
    for value in SYMBOLS:
        lines.append(asp.fact("symbol", value))
    for value in FEES:
        lines.append(asp.fact("fee", value))
    return "\n".join(lines)


ASP_RULES = r"""
fair_fee(F) :- fee(F), moral_value, sharing.
symbol_guides(S) :- symbol(S), moral_value.
recipe_ready(R) :- recipe(R), fair_fee(_), symbol_guides(_).
good_story :- recipe_ready(_).
#show fair_fee/1.
#show symbol_guides/1.
#show recipe_ready/1.
#show good_story/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show good_story/0."))
    if asp.atoms(model, "good_story"):
        for seed in range(12):
            params = StoryParams(seed=seed)
            sample = generate(params)
            if not sample.story or "recipe" not in sample.story.lower():
                print("ASP verification failed: generated story missing recipe.")
                return 1
        print("OK: ASP parity and generated stories verified.")
        return 0
    print("ASP verification failed.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rhyming story world about a recipe, symbol, fee, and moral value.")
    parser.add_argument("--baker", choices=BAKERS, default=None)
    parser.add_argument("--recipe", choices=RECIPES, default=None)
    parser.add_argument("--symbol", choices=SYMBOLS, default=None)
    parser.add_argument("--fee", choices=FEES, default=None)
    parser.add_argument("--place", choices=PLACES, default=None)
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
    return StoryParams(
        baker=args.baker or rng.choice(BAKERS),
        recipe=args.recipe or rng.choice(RECIPES),
        symbol=args.symbol or rng.choice(SYMBOLS),
        fee=args.fee or rng.choice(FEES),
        place=args.place or rng.choice(PLACES),
        seed=args.seed,
    )


def validate_params(params: StoryParams) -> None:
    if params.baker not in BAKERS:
        raise StoryError(f"Unknown baker: {params.baker}")
    if params.recipe not in RECIPES:
        raise StoryError(f"Unknown recipe: {params.recipe}")
    if params.symbol not in SYMBOLS:
        raise StoryError(f"Unknown symbol: {params.symbol}")
    if params.fee not in FEES:
        raise StoryError(f"Unknown fee: {params.fee}")
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")


def generate(params: StoryParams) -> StorySample:
    validate_params(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(baker="Luna", recipe=RECIPES[0], symbol=SYMBOLS[0], fee=FEES[0], place=PLACES[0], seed=0),
    StoryParams(baker="Milo", recipe=RECIPES[1], symbol=SYMBOLS[1], fee=FEES[1], place=PLACES[1], seed=17),
    StoryParams(baker="Nia", recipe=RECIPES[2], symbol=SYMBOLS[2], fee=FEES[2], place=PLACES[2], seed=34),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("n must be at least 1")
    if args.show_asp:
        print(asp_program("#show fair_fee/1. #show symbol_guides/1. #show recipe_ready/1. #show good_story/0."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show fair_fee/1. #show symbol_guides/1. #show recipe_ready/1. #show good_story/0."))
        for predicate in ("fair_fee", "symbol_guides", "recipe_ready", "good_story"):
            print(asp.atoms(model, predicate))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(args.n * 50, 50):
            seed = base_seed + attempts
            attempts += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            params = sample.params
            header = f"### {params.baker} / {params.recipe} / {params.symbol}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
