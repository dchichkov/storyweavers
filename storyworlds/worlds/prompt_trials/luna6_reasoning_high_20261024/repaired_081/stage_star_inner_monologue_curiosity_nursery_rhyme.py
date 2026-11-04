#!/usr/bin/env python3
"""
A nursery-rhyme storyworld about a paper star on a little stage.

A curious young performer notices that the star shows its plain back to the
audience. By asking questions and following a small clue, the children discover
that its ribbon has twisted, then turn and secure the star so it can shine.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


STYLE = "Nursery Rhyme"
FEATURES = ("Inner Monologue", "Curiosity")


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    type: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Stage:
    name: str
    description: str


@dataclass
class StoryParams:
    stage: str = "Willowbend Stage"
    hero_name: str = "Mira"
    helper_name: str = "Tavi"
    seed: Optional[int] = None


class World:
    def __init__(self, stage: Stage) -> None:
        self.stage = stage
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.lines: list[str] = []

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return "\n\n".join(self.lines)


STAGE_REGISTRY = {
    "Willowbend Stage": Stage(
        "Willowbend Stage", "a little wooden stage beneath a willow-tree sign"
    ),
    "Bluebell Hall Stage": Stage(
        "Bluebell Hall Stage", "a small stage in a bright village hall"
    ),
    "Little Lantern Stage": Stage(
        "Little Lantern Stage", "a puppet stage beside a row of lantern-shaped windows"
    ),
}

CHARACTER_NAMES = ["Mira", "Tavi", "Nell", "Ollie", "Pip", "Zara"]


ASP_RULES = r"""
selected_stage :- requested_stage(S), stage_name(S).
cast_distinct :- requested_hero(H), hero_name(H),
                 requested_helper(K), helper_name(K), H != K.
curious_turn :- question_asked, clue_seen, inspection_done.
star_ready :- face_audience, fastened, lamp_lit, stage_clear.
reasonable_story :- selected_stage, cast_distinct, curious_turn, star_ready.
"""


def reasonableness_gate(params: StoryParams) -> None:
    """Reject choices that cannot describe this small stage story."""
    if params.stage not in STAGE_REGISTRY:
        raise StoryError(
            f"Unknown stage {params.stage!r}. Choose one of: "
            + ", ".join(STAGE_REGISTRY)
        )
    if params.hero_name not in CHARACTER_NAMES:
        raise StoryError(f"Unknown hero name {params.hero_name!r}.")
    if params.helper_name not in CHARACTER_NAMES:
        raise StoryError(f"Unknown helper name {params.helper_name!r}.")
    if params.hero_name == params.helper_name:
        raise StoryError("The hero and helper must be different characters.")


def asp_facts(params: Optional[StoryParams] = None) -> str:
    """Emit registry and generated-world facts for the inline ASP twin."""
    import asp

    selected = params or StoryParams()
    lines: list[str] = []

    for stage_name in STAGE_REGISTRY:
        lines.append(asp.fact("stage_name", stage_name))
    for name in CHARACTER_NAMES:
        lines.append(asp.fact("hero_name", name))
        lines.append(asp.fact("helper_name", name))

    lines.extend(
        [
            asp.fact("requested_stage", selected.stage),
            asp.fact("requested_hero", selected.hero_name),
            asp.fact("requested_helper", selected.helper_name),
            asp.fact("question_asked"),
            asp.fact("clue_seen"),
            asp.fact("inspection_done"),
            asp.fact("face_audience"),
            asp.fact("fastened"),
            asp.fact("lamp_lit"),
            asp.fact("stage_clear"),
        ]
    )
    return "\n".join(lines)


def asp_program(
    params: Optional[StoryParams] = None,
    show: str = "#show reasonable_story/0.\n#show curious_turn/0.\n#show star_ready/0.",
) -> str:
    return f"{asp_facts(params)}\n{ASP_RULES}\n{show}\n"


def asp_check(params: StoryParams) -> tuple[bool, set[str]]:
    """Return whether ASP agrees with the Python gate and its shown conclusions."""
    import asp

    model = asp.one_model(asp_program(params))
    shown = {
        predicate
        for predicate in ("reasonable_story", "curious_turn", "star_ready")
        if asp.atoms(model, predicate)
    }
    expected = {"reasonable_story", "curious_turn", "star_ready"}
    return shown == expected, shown


def asp_verify() -> int:
    """Compare both reasoners and exercise generated stories across the registry."""
    exercised = 0
    for index, stage_name in enumerate(STAGE_REGISTRY):
        hero = CHARACTER_NAMES[index]
        helper = CHARACTER_NAMES[(index + 1) % len(CHARACTER_NAMES)]
        params = StoryParams(
            stage=stage_name,
            hero_name=hero,
            helper_name=helper,
            seed=100 + index,
        )

        try:
            reasonableness_gate(params)
            sample = generate(params)
        except StoryError as exc:
            print(f"Python story check failed: {exc}")
            return 1

        world = sample.world
        if (
            world is None
            or not world.facts.get("star_ready")
            or "wondered" not in sample.story
            or "said" not in sample.story
            or "clipped" not in sample.story
        ):
            print(f"Generated-story check failed for {stage_name}.")
            return 1

        try:
            matches, shown = asp_check(params)
        except Exception as exc:
            print(f"ASP verification could not run: {exc}")
            return 1
        if not matches:
            print(f"MISMATCH for {stage_name}. ASP showed: {sorted(shown)}")
            return 1
        exercised += 1

    try:
        reasonableness_gate(StoryParams(hero_name="Mira", helper_name="Mira"))
    except StoryError:
        pass
    else:
        print("Python gate failed to reject a hero and helper with the same name.")
        return 1

    print(
        "OK: ASP and Python agree; "
        f"{exercised} generated stage stories passed their story checks."
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "A nursery-rhyme storyworld about curiosity, a little stage, "
            "and a star."
        )
    )
    parser.add_argument("--stage", choices=list(STAGE_REGISTRY))
    parser.add_argument("--name")
    parser.add_argument("--helper")
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
    hero = args.name or rng.choice(CHARACTER_NAMES)
    helper = args.helper or rng.choice(
        [name for name in CHARACTER_NAMES if name != hero]
    )
    params = StoryParams(
        stage=args.stage or rng.choice(list(STAGE_REGISTRY)),
        hero_name=hero,
        helper_name=helper,
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.stage}:{params.hero_name}:{params.helper_name}"
    )
    stage = STAGE_REGISTRY[params.stage]
    world = World(stage)

    hero = world.add(
        Entity(
            id="hero",
            kind="character",
            label=params.hero_name,
            type="child",
            meters={"attention": 0.2, "careful_action": 0.0},
            memes={"curiosity": 0.3, "worry": 0.5, "pride": 0.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=params.helper_name,
            type="child",
            meters={"steady_hands": 0.0},
            memes={"patience": 0.8, "confidence": 0.5},
        )
    )
    stage_entity = world.add(
        Entity(
            id="stage",
            kind="place",
            label=stage.name,
            type="performance_stage",
            meters={"clear_floor": 1.0, "lamp_on": 1.0},
            memes={"welcome": 1.0},
        )
    )
    star = world.add(
        Entity(
            id="star",
            kind="prop",
            label="gold-paper star",
            type="stage_decoration",
            owner=hero.id,
            meters={
                "face_toward_audience": 0.0,
                "ribbon_twisted": 1.0,
                "fastened": 0.0,
                "shine": 0.0,
            },
            memes={"hope": 1.0, "shyness": 0.6},
        )
    )

    openings = [
        (
            f"At {stage.name}, blue curtains were ready to sway, "
            f"as {params.hero_name} set a gold-paper star for the play."
        ),
        (
            f"On {stage.name}, the puppets stood ready in line, "
            f"while {params.hero_name} hung a star with a bright golden shine."
        ),
        (
            f"The little stage waited beneath curtains of blue, "
            f"and {params.hero_name} brought a gold star for the show, too."
        ),
    ]
    world.say(rng.choice(openings))
    world.say(
        "But though the small stage lamp cast a warm, steady glow, "
        "the star showed its plain paper back to the row."
    )
    world.say(
        f"“Why doesn't our gold side shine for the show?” asked {params.hero_name}. "
        f"“The plain side faces the seats in a row.”"
    )
    world.say(
        f"“Don't tug at the ribbon; let's find what went wrong,” said {params.helper_name}. "
        f"“Watch while I hold it; we'll look all along.”"
    )

    hero.meters["attention"] = 1.0
    hero.memes["curiosity"] = 1.0
    hero.memes["worry"] = 0.2
    helper.meters["steady_hands"] = 1.0
    world.say(
        f"{params.hero_name} wondered, *What clue can I find? "
        "I'll follow the ribbon and use eyes, not a tugging hand.*"
    )
    world.say(
        f"With a careful small step and a curious look, {params.hero_name} "
        "traced the loop like a page in a book."
    )
    world.say(
        "A fleck of warm gold winked on curtain-blue cloth; "
        "the star's shiny face pointed away from the lot."
    )
    world.say(
        f"“That glint on the curtain tells where it must face,” said {params.helper_name}. "
        f"“Let's turn it toward everyone, right in its place.”"
    )
    world.say(
        f"“Yes, and two clips will keep it from spinning,” said {params.hero_name}. "
        "“Then all the small seats can see it there gleaming.”"
    )

    # The observation changes the plan: the children turn the star rather than
    # pulling its ribbon, then secure it so the same problem cannot return.
    hero.meters["careful_action"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["pride"] = 1.0
    helper.memes["confidence"] = 1.0
    star.meters["face_toward_audience"] = 1.0
    star.meters["ribbon_twisted"] = 0.0
    star.meters["fastened"] = 1.0
    star.meters["shine"] = 1.0
    star.memes["shyness"] = 0.0
    world.say(
        "They turned the bright side toward the seats in the hall, "
        "and clipped its soft ribbon so it couldn't twirl at all."
    )
    world.say(
        "Now lamp-light ran over the gold like a stream, "
        "and the puppets below wore a starry bright gleam."
    )

    endings = [
        (
            "The curtain swung wide and the puppets stepped out, "
            "while the star shone above them and smiled at the crowd."
        ),
        (
            "The play began softly; the blue curtains drew near, "
            "and one steady gold star glowed bright and clear."
        ),
        (
            "The little play danced in a warm golden glow, "
            "while the star watched the story unfolding below."
        ),
    ]
    world.say(rng.choice(endings))

    world.facts.update(
        hero=hero,
        helper=helper,
        stage=stage_entity,
        star=star,
        question_asked=True,
        clue_seen=True,
        inspection_done=True,
        star_ready=(
            star.meters["face_toward_audience"] == 1.0
            and star.meters["fastened"] == 1.0
            and star.meters["shine"] == 1.0
            and stage_entity.meters["clear_floor"] == 1.0
        ),
        clue="A fleck of gold on the curtain showed that the star faced away from the audience.",
        transformation="The children turned the gold face toward the seats and secured the ribbon with two clips.",
        lesson="Observe a problem before changing something; a small clue can show what to do.",
    )

    prompts = [
        (
            f"Write a {STYLE.lower()} about {params.hero_name} and "
            f"{params.helper_name} preparing a star for {stage.name}."
        ),
        (
            "Use inner monologue and curiosity: let a small clue change the "
            "children's plan from tugging to careful looking."
        ),
        (
            "End with a clear image showing how the turned and secured star "
            "changes the little performance."
        ),
    ]
    story_qa = [
        QAItem(
            question="What was wrong with the star at first?",
            answer=(
                "The star's plain paper back faced the audience because its "
                "ribbon had twisted, so the gold side could not shine toward the seats."
            ),
        ),
        QAItem(
            question=f"What clue helped {params.hero_name} understand the problem?",
            answer=(
                f"{params.hero_name} and {params.helper_name} noticed a fleck of "
                "gold on the curtain, which showed that the shiny side of the star "
                "was turned away from the audience."
            ),
        ),
        QAItem(
            question="How did the children fix the star?",
            answer=(
                "They gently turned its gold face toward the seats and used two "
                "clips to keep its ribbon from twisting the star around again."
            ),
        ),
        QAItem(
            question="What did the children learn from looking closely?",
            answer=(
                "They learned to observe a problem before changing anything, "
                "because a small clue can point to a safe and useful solution."
            ),
        ),
        QAItem(
            question="How could everyone tell the repair worked?",
            answer=(
                "The stage lamp shone across the star's gold face, and the star "
                "stayed bright above the puppets instead of turning back toward "
                "the curtain."
            ),
        ),
    ]
    world_qa = [
        QAItem(
            question="What is a stage?",
            answer=(
                "A stage is a raised or marked place where performers can act, "
                "play music, or show a puppet story to an audience."
            ),
        ),
        QAItem(
            question="Why might a star on a stage need clips?",
            answer=(
                "Clips can hold a light decoration in place so it does not twist "
                "or swing away from the audience during a performance."
            ),
        ),
        QAItem(
            question="What is curiosity?",
            answer=(
                "Curiosity is a desire to find out more, often by asking a "
                "question and looking carefully for clues."
            ),
        ),
        QAItem(
            question="What is an inner monologue?",
            answer=(
                "An inner monologue is a character's unspoken thought, which lets "
                "readers know what the character is wondering or deciding."
            ),
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(
    sample: StorySample,
    *,
    trace: bool = False,
    qa: bool = False,
    header: str = "",
    asp_result: Optional[tuple[bool, set[str]]] = None,
) -> None:
    if header:
        print(header)
    if asp_result is not None:
        matches, shown = asp_result
        if matches:
            print("ASP check: the curious turn and ready star are supported.")
        else:
            print(f"ASP/Python mismatch: ASP showed {sorted(shown)}")
    print(sample.story)

    if trace and sample.world is not None:
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(
                f"{key}: {entity.label} "
                f"meters={entity.meters} memes={entity.memes}"
            )
        print(f"world facts: {sample.world.facts}")

    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.n < 1 and not args.all:
        parser.error("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, stage_name in enumerate(STAGE_REGISTRY):
            hero = args.name or CHARACTER_NAMES[index]
            default_helper = next(
                name for name in CHARACTER_NAMES if name != hero
            )
            helper = args.helper or default_helper
            params = StoryParams(
                stage=stage_name,
                hero_name=hero,
                helper_name=helper,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            samples.append(generate(params))

    asp_results: list[Optional[tuple[bool, set[str]]]] = []
    if args.asp:
        for sample in samples:
            try:
                asp_results.append(asp_check(sample.params))
            except Exception as exc:
                raise StoryError(f"Could not run the ASP check: {exc}") from exc
    else:
        asp_results = [None] * len(samples)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=header,
            asp_result=asp_results[index],
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
