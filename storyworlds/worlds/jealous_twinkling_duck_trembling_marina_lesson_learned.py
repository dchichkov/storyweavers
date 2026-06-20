#!/usr/bin/env python3
"""
jealous_twinkling_duck_trembling_marina_lesson_learned.py
=========================================================

A small StoryWorld for the seed:

    words: jealous, twinkling duck, trembling
    setting: marina
    feature: Lesson Learned
    style: Folk Tale

Internal source tale:
    A child at a marina mistakes a sparkling duck for a show-off and grows
    jealous. When the child edges closer, both child and duck are trembling:
    the child from the swaying dock, the duck from being snagged in old gear.
    The child frees the duck with a gentle harbor trick and learns that
    jealousy can hide another creature's trouble.
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Marina:
    key: str
    phrase: str
    landmark: str
    water_name: str
    supports: tuple[str, ...]
    ending_image: str


@dataclass(frozen=True)
class Snag:
    key: str
    caught_on: str
    sparkle: str
    trap_phrase: str
    safe_methods: tuple[str, ...]
    release_goal: str
    helper_object: str


@dataclass(frozen=True)
class Method:
    key: str
    phrase: str
    action: str
    calming_detail: str


@dataclass
class StoryParams:
    marina: str
    snag: str
    method: str
    hero: str
    gender: str
    elder: str
    seed: int


@dataclass
class Entity:
    name: str
    kind: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: dict[str, str] = field(default_factory=dict)

    def set_meter(self, key: str, value: float) -> None:
        self.meters[key] = round(value, 2)

    def add_meter(self, key: str, amount: float) -> None:
        self.set_meter(key, self.meters.get(key, 0.0) + amount)

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = round(self.memes.get(key, 0.0) + amount, 2)


@dataclass
class World:
    params: StoryParams
    marina: Marina
    snag: Snag
    method: Method
    entities: dict[str, Entity] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    fired_rules: list[str] = field(default_factory=list)
    lesson: str = ""

    def note(self, text: str) -> None:
        self.history.append(text)

    def trace(self) -> str:
        rows = ["--- world model state ---"]
        rows.append(f"  marina: {self.marina.key} -> {self.marina.phrase}")
        rows.append(f"  snag: {self.snag.key} on {self.snag.caught_on}")
        rows.append(f"  method: {self.method.key} -> {self.method.phrase}")
        for name, ent in self.entities.items():
            tags = ", ".join(f"{k}={v}" for k, v in sorted(ent.tags.items()))
            rows.append(
                f"  {name:<9} ({ent.kind:<8}) meters={ent.meters} memes={ent.memes}"
                + (f" tags={{{tags}}}" if tags else "")
            )
        rows.append(f"  lesson: {self.lesson}")
        rows.append(f"  fired rules: {self.fired_rules}")
        return "\n".join(rows)


MARINAS: dict[str, Marina] = {
    "lantern_slip": Marina(
        "lantern_slip",
        "the lantern slip of the old marina",
        "a post with a copper bell",
        "the black-green harbor water",
        ("net_post", "cleat"),
        "the duck gliding past the bell while the copper light shook in little stars",
    ),
    "gull_walk": Marina(
        "gull_walk",
        "the gull walk of the weathered marina",
        "a heap of coiled rope",
        "the tide under the bobbing planks",
        ("cleat", "bead_hook"),
        "the duck leaving a bright ribbon of ripples beneath the crying gulls",
    ),
    "anchor_steps": Marina(
        "anchor_steps",
        "the anchor steps beside the sleepy marina",
        "an iron ring dark with salt",
        "the moon-smoothed inlet",
        ("net_post", "bead_hook"),
        "the duck circling the iron ring while the inlet held the stars still",
    ),
}

SNAGS: dict[str, Snag] = {
    "shell_net": Snag(
        "shell_net",
        "net_post",
        "shell chips and spray-light twinkling in its feathers",
        "an old shell net hanging over one wing",
        ("loosen_knot", "steady_cloth"),
        "open water beyond the pilings",
        "the shell net",
    ),
    "silver_twine": Snag(
        "silver_twine",
        "cleat",
        "silver mooring twine flashing at its ankle",
        "a loop of silver twine pulled tight around one foot",
        ("lift_loop", "steady_cloth"),
        "the quiet water beside the boats",
        "the silver twine",
    ),
    "lantern_beads": Snag(
        "lantern_beads",
        "bead_hook",
        "little lantern beads sparkling against its chest",
        "a string of lantern beads snagged under its breast",
        ("loosen_knot", "lift_loop"),
        "the calm lane between the moored boats",
        "the lantern beads",
    ),
}

METHODS: dict[str, Method] = {
    "loosen_knot": Method(
        "loosen_knot",
        "patient fingers on a wet knot",
        "worked the wet knot loose strand by strand",
        "The child breathed slowly so the bobbing boards would not hurry the hands.",
    ),
    "lift_loop": Method(
        "lift_loop",
        "a careful lift over the iron catch",
        "raised the shining loop and eased it over the iron catch",
        "The child planted both feet and moved only when the dock stopped rocking.",
    ),
    "steady_cloth": Method(
        "steady_cloth",
        "a folded cloth and a still palm",
        "covered the frightened wings with a folded cloth and slipped the snag free",
        "The soft cloth kept the duck calm long enough for kindness to do its work.",
    ),
}

HEROES = {
    "girl": ("Mira", "Nella", "Tilda", "Wren", "Elsie"),
    "boy": ("Tomas", "Rowan", "Pavel", "Ivo", "Milo"),
}

ELDERS = ("grandmother", "boatwright uncle", "harbor aunt", "grandfather")


def _pronouns(gender: str) -> tuple[str, str, str]:
    if gender == "boy":
        return ("he", "his", "him")
    return ("she", "her", "her")


def _article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


def _with_article(text: str) -> str:
    if text.startswith(("a ", "an ", "the ")):
        return text
    return f"{_article(text)} {text}"


def valid_combo(marina: str, snag: str, method: str) -> bool:
    if marina not in MARINAS or snag not in SNAGS or method not in METHODS:
        return False
    return SNAGS[snag].caught_on in MARINAS[marina].supports and method in SNAGS[snag].safe_methods


def invalid_reason(marina: str, snag: str, method: str) -> str:
    if marina not in MARINAS:
        return f"No story: unknown marina {marina!r}."
    if snag not in SNAGS:
        return f"No story: unknown snag {snag!r}."
    if method not in METHODS:
        return f"No story: unknown method {method!r}."
    marina_obj = MARINAS[marina]
    snag_obj = SNAGS[snag]
    if snag_obj.caught_on not in marina_obj.supports:
        return (
            f"No story: {marina_obj.phrase} has no {snag_obj.caught_on.replace('_', ' ')} "
            f"for {snag_obj.helper_object} to catch on."
        )
    if method not in snag_obj.safe_methods:
        safe = ", ".join(sorted(snag_obj.safe_methods))
        return (
            f"No story: {METHODS[method].phrase} is not a safe answer to {snag_obj.helper_object}; "
            f"try {safe}."
        )
    return "No story: the requested marina rescue is not reasonable."


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for marina in MARINAS:
        for snag in SNAGS:
            for method in METHODS:
                if valid_combo(marina, snag, method):
                    combos.append((marina, snag, method))
    return combos


def _r_envy_misreads_sparkle(world: World) -> bool:
    hero = world.entities["Hero"]
    duck = world.entities["Duck"]
    dock = world.entities["Dock"]
    hero.add_meme("jealousy", 1.0)
    hero.add_meme("wonder", 0.3)
    hero.set_meter("distance_to_duck", 3.0)
    hero.set_meter("balance", 0.65)
    duck.add_meme("fear", 0.7)
    duck.set_meter("distance_to_water", 1.4)
    duck.set_meter("entangled", 1.0)
    dock.set_meter("sway", 0.6)
    world.note(
        f"{hero.name} first thought the twinkling duck was showing off because of {world.snag.sparkle}."
    )
    return True


def _r_trembling_reveals_truth(world: World) -> bool:
    hero = world.entities["Hero"]
    duck = world.entities["Duck"]
    hero.add_meme("jealousy", -0.5)
    hero.add_meme("pity", 0.8)
    hero.add_meme("courage", 0.4)
    hero.add_meter("distance_to_duck", -1.8)
    duck.add_meme("fear", 0.3)
    duck.tags["status"] = "trembling"
    world.note(
        f"When {hero.name} stepped closer, the duck was trembling because {world.snag.trap_phrase}."
    )
    return True


def _r_gentle_rescue_teaches_lesson(world: World) -> bool:
    hero = world.entities["Hero"]
    duck = world.entities["Duck"]
    dock = world.entities["Dock"]
    hero.add_meme("jealousy", -0.5)
    hero.add_meme("humility", 1.0)
    hero.add_meme("care", 0.9)
    hero.set_meter("balance", 0.95)
    duck.add_meme("fear", -0.6)
    duck.add_meme("trust", 0.8)
    duck.set_meter("entangled", 0.0)
    duck.set_meter("distance_to_water", 0.0)
    duck.tags["status"] = "free"
    dock.tags["helped_with"] = world.method.key
    world.lesson = (
        "Jealousy makes bright things look like prizes to take, but a quiet heart can see who needs help."
    )
    world.note(
        f"{hero.name} {world.method.action}, and the duck slipped toward {world.snag.release_goal}."
    )
    return True


RULES = [
    ("envy_misreads_sparkle", _r_envy_misreads_sparkle),
    ("trembling_reveals_truth", _r_trembling_reveals_truth),
    ("gentle_rescue_teaches_lesson", _r_gentle_rescue_teaches_lesson),
]


def build_world(params: StoryParams) -> World:
    marina = MARINAS[params.marina]
    snag = SNAGS[params.snag]
    method = METHODS[params.method]
    world = World(params=params, marina=marina, snag=snag, method=method)
    world.entities["Hero"] = Entity(
        params.hero,
        params.gender,
        meters={"warmth": 0.8},
        memes={"curiosity": 0.5},
        tags={"role": "child"},
    )
    world.entities["Duck"] = Entity(
        "duck",
        "duck",
        meters={"light": 0.7},
        memes={"fear": 0.2},
        tags={"kind": "twinkling duck"},
    )
    world.entities["Elder"] = Entity(
        params.elder.title(),
        "elder",
        meters={"steadiness": 1.0},
        memes={"wisdom": 1.0},
        tags={"role": "guide"},
    )
    world.entities["Dock"] = Entity(
        "dock",
        "marina",
        meters={"sway": 0.2},
        memes={},
        tags={"landmark": marina.landmark},
    )
    for name, rule in RULES:
        if rule(world):
            world.fired_rules.append(name)
    return world


def _render_story(world: World) -> str:
    p = world.params
    he, his, _him = _pronouns(p.gender)
    marina = world.marina
    snag = world.snag
    method = world.method

    opening = (
        f"Once, in {marina.phrase}, {p.hero} walked at dusk beside {his} {p.elder}. "
        f"Lamps were waking one by one, and their light danced over the ropes and masts. "
        f"Near {marina.landmark}, a twinkling duck shone so brightly that {p.hero} grew jealous."
    )
    tension = (
        f"{p.hero} thought the duck had stolen all the prettiest glimmers for itself. "
        f"But when {he} edged onto the swaying dock, {he} felt {his} knees trembling, and then {he} saw the truth: "
        f"the duck was trembling too, for it had {snag.trap_phrase}, with {snag.sparkle}."
    )
    turn = (
        f"\"Bright things are not always happy things,\" said {his} {p.elder}. "
        f"Then {p.hero} knelt low and {method.action}. {method.calming_detail} "
        f"Soon the duck was free to reach {snag.release_goal}."
    )
    ending = (
        f"The twinkling duck did not flee. It glided once around the child as if in thanks, and then there it was: {marina.ending_image}. "
        f"{p.hero} went home with salt on {his} sleeves and a lesson in {his} heart: {world.lesson}"
    )
    return "\n\n".join([opening, tension, turn, ending])


def _prompts(world: World) -> list[str]:
    return [
        'Write a folk tale for children set in a marina using the words "jealous", "twinkling duck", and "trembling".',
        f"Tell a lesson-learned tale where {world.params.hero} mistakes a sparkling duck for a proud one, then frees it with {world.method.phrase}.",
        "Write a child-facing marina story where jealousy turns into kindness after a frightened animal is understood.",
    ]


def _story_qa(world: World) -> list[QAItem]:
    p = world.params
    _he, his, _him = _pronouns(p.gender)
    return [
        QAItem(
            "Why was the child jealous at the beginning?",
            f"{p.hero} saw the twinkling duck shining in the marina light and thought the bird was keeping all the prettiest sparkle for itself. The jealousy came from a wrong guess before the child understood the trouble.",
        ),
        QAItem(
            "Why were both the child and the duck trembling?",
            f"{p.hero} was trembling because the dock swayed under small careful feet. The duck was trembling because it had {world.snag.trap_phrase} and could not get back to safe water.",
        ),
        QAItem(
            "How was the duck helped?",
            f"{p.hero} {world.method.action}. That gentle method matched the snag and let the duck reach {world.snag.release_goal}.",
        ),
        QAItem(
            "What did the elder mean by saying bright things are not always happy things?",
            f"The elder meant that sparkle can hide pain instead of pride. The duck looked grand from far away, but up close the shining bits were part of its trap.",
        ),
        QAItem(
            "What lesson was learned at the end?",
            f"The lesson was that jealousy can make someone judge too quickly. When {p.hero} chose kindness over envy, the real story became clear.",
        ),
    ]


def _world_qa(world: World) -> list[QAItem]:
    items = [
        QAItem(
            "Why can marina docks make someone feel unsteady?",
            "Marina docks float and sway with the water, so even a careful child can feel a wobble in the knees. Moving slowly helps a person keep balance.",
        ),
        QAItem(
            "Why is a gentle rescue better than grabbing a frightened bird?",
            "A frightened bird may flap harder if someone grabs at it suddenly. Gentle hands and calm motion make it safer to remove a snag.",
        ),
        QAItem(
            "Why do shiny things look brighter near water at dusk?",
            "Water catches lamplight and sends it moving in little flashes. Wet feathers, rope, shells, or beads can sparkle more because the light keeps shifting.",
        ),
    ]
    if world.snag.key == "shell_net":
        items.append(
            QAItem(
                "Why is old netting dangerous for birds?",
                "Loose netting can catch a wing or foot and keep a bird from swimming away. Even something light can become a trap when it tightens in a struggle.",
            )
        )
    if world.snag.key == "silver_twine":
        items.append(
            QAItem(
                "Why is twine risky around a bird's foot?",
                "Twine can tighten when a bird pulls against it. That makes walking and swimming harder until someone safely loosens the loop.",
            )
        )
    if world.snag.key == "lantern_beads":
        items.append(
            QAItem(
                "Why might beads attract attention before anyone notices danger?",
                "Beads catch light quickly, so people notice the sparkle first. The trouble becomes visible only when someone looks carefully at how the beads are caught.",
            )
        )
    return items


def generate(params: StoryParams) -> StorySample:
    if not valid_combo(params.marina, params.snag, params.method):
        raise StoryError(invalid_reason(params.marina, params.snag, params.method))
    world = build_world(params)
    return StorySample(
        params=params,
        story=_render_story(world),
        prompts=_prompts(world),
        story_qa=_story_qa(world),
        world_qa=_world_qa(world),
        world=world,
    )


ASP_RULES = r"""
combo(M,S,T) :-
    marina(M),
    snag(S),
    method(T),
    snag_on(S,Support),
    marina_support(M,Support),
    safe_method(S,T).

ok :- chosen(M,S,T), combo(M,S,T).

#show combo/3.
#show ok/0.
"""


def asp_facts(params: StoryParams | None = None) -> str:
    from storyworlds.asp import fact

    rows: list[str] = []
    for key, marina in MARINAS.items():
        rows.append(fact("marina", key))
        for support in marina.supports:
            rows.append(fact("marina_support", key, support))
    for key, snag in SNAGS.items():
        rows.append(fact("snag", key))
        rows.append(fact("snag_on", key, snag.caught_on))
        for method in snag.safe_methods:
            rows.append(fact("safe_method", key, method))
    for key in METHODS:
        rows.append(fact("method", key))
    if params is not None:
        rows.append(fact("chosen", params.marina, params.snag, params.method))
    return "\n".join(rows) + "\n"


def asp_program(params: StoryParams | None = None) -> str:
    return asp_facts(params) + ASP_RULES


def asp_valid_combos() -> set[tuple[str, str, str]]:
    from storyworlds.asp import atoms, solve

    combos: set[tuple[str, str, str]] = set()
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
        raise StoryError(
            f"ASP/Python mismatch. only_python={sorted(py - asp)} only_asp={sorted(asp - py)}"
        )

    parser = build_parser()
    checked = 0
    for idx, combo in enumerate(sorted(py)):
        args = parser.parse_args([])
        args.seed = 100 + idx
        params = _params_from_combo(args, combo, random.Random(args.seed), index=idx)
        if not asp_verify(params):
            raise StoryError(f"ASP failed chosen combo {combo}.")
        sample = generate(params)
        story = sample.story.lower()
        for needle in ("jealous", "twinkling duck", "trembling", "marina"):
            if needle not in story:
                raise StoryError(f"Generated story missing required text {needle!r} for combo {combo}.")
        if "lesson" not in story:
            raise StoryError(f"Generated story did not surface a lesson for combo {combo}.")
        if len(sample.story_qa) < 5 or len(sample.world_qa) < 3 or len(sample.prompts) < 3:
            raise StoryError(f"Generated sample has incomplete QA/prompts for combo {combo}.")
        if "{" in sample.story or "}" in sample.story or "meters=" in sample.story:
            raise StoryError(f"Generated story leaked scaffold text for combo {combo}.")
        checked += 1
    return f"OK: clingo gate matches valid_combos() and exercised {checked} generated stories."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate jealous twinkling duck marina folk-tale samples.")
    parser.add_argument("--marina", choices=sorted(MARINAS))
    parser.add_argument("--snag", choices=sorted(SNAGS))
    parser.add_argument("--method", choices=sorted(METHODS))
    parser.add_argument("--hero")
    parser.add_argument("--gender", choices=sorted(HEROES), default=None)
    parser.add_argument("--elder", choices=ELDERS)
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
    args: argparse.Namespace,
    combo: tuple[str, str, str],
    rng: random.Random,
    index: int = 0,
) -> StoryParams:
    gender = args.gender or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[gender])
    elder = args.elder or rng.choice(ELDERS)
    marina, snag, method = combo
    return StoryParams(
        marina=marina,
        snag=snag,
        method=method,
        hero=hero,
        gender=gender,
        elder=elder,
        seed=args.seed + index,
    )


def resolve_params(args: argparse.Namespace, rng: random.Random, index: int = 0) -> StoryParams:
    if args.marina or args.snag or args.method:
        marina = args.marina or rng.choice(sorted(MARINAS))
        snag = args.snag or rng.choice(sorted(SNAGS))
        method = args.method or rng.choice(sorted(METHODS))
        if not valid_combo(marina, snag, method):
            raise StoryError(invalid_reason(marina, snag, method))
        combo = (marina, snag, method)
    else:
        combo = rng.choice(valid_combos())
    return _params_from_combo(args, combo, rng, index=index)


def _print_qa(sample: StorySample) -> None:
    print("\n== (1) Generation prompts -- asks that would produce this story ==")
    for i, prompt in enumerate(sample.prompts, 1):
        print(f"{i}. {prompt}")
    print("\n== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")
    print("\n== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        print(f"Q: {qa.question}")
        print(f"A: {qa.answer}")


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story if not sample.story.endswith("\n") else sample.story.rstrip("\n"))
    if trace and sample.world is not None:
        print(sample.world.trace())
    if qa:
        _print_qa(sample)


def _emit_asp_listing() -> None:
    for combo in sorted(asp_valid_combos()):
        print("\t".join(combo))


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
            for i, combo in enumerate(combos):
                rng = random.Random(args.seed + i)
                sample = generate(_params_from_combo(args, combo, rng, index=i))
                if args.json:
                    print(sample.to_json())
                else:
                    emit(
                        sample,
                        trace=args.trace,
                        qa=args.qa,
                        header=f"### {sample.params.hero}: {combo[1]} with {combo[2]} at {combo[0]}",
                    )
                    if i != len(combos) - 1:
                        print("\n" + "=" * 70 + "\n")
            return 0

        count = max(1, args.n)
        for i in range(count):
            rng = random.Random(args.seed + i)
            sample = generate(resolve_params(args, rng, index=i))
            if args.json:
                print(sample.to_json())
            else:
                emit(
                    sample,
                    trace=args.trace,
                    qa=args.qa,
                    header=f"### variant {i + 1}" if count > 1 else "",
                )
                if i != count - 1:
                    print("\n" + "=" * 70 + "\n")
        return 0
    except StoryError as exc:
        print(exc, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
