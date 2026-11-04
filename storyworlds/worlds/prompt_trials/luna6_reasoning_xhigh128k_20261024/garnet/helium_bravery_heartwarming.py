#!/usr/bin/env python3
"""
A heartwarming storyworld about helium, a stuck welcome balloon, and the
bravery it takes to ask for help and make someone feel at home.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional


_here = os.path.abspath(os.path.dirname(__file__))
_storyworlds_dir = _here
while not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _parent = os.path.dirname(_storyworlds_dir)
    if _parent == _storyworlds_dir:
        break
    _storyworlds_dir = _parent
if os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str = "Lena"
    helper_name: str = "Ms. Rowan"
    newcomer_name: str = "June"
    setting: str = "the library courtyard"
    activity: str = "laying out story blankets"
    balloon_color: str = "sky-blue"
    snag_point: str = "the low willow trellis"
    rescue_tool: str = "soft_loop"
    seed: Optional[int] = None


@dataclass
class World:
    hero: Entity
    helper: Entity
    newcomer: Entity
    helium: Entity
    balloon: Entity
    setting: str
    params: StoryParams
    seed: int
    facts: dict = field(default_factory=dict)


NAMES = ["Lena", "Milo", "Nia", "Tavi", "Rosa", "Owen", "Amir", "Pip"]
NEWCOMER_NAMES = ["June", "Sol", "Eli", "Mara", "Bea", "Noor", "Kit", "Sam"]
HELPER_NAMES = ["Ms. Rowan", "Mr. Ellis", "Aunt Bea", "Coach Sal"]
SETTINGS = [
    "the library courtyard",
    "the school garden",
    "the park picnic shelter",
    "the neighborhood hall",
]
ACTIVITIES = [
    "laying out story blankets",
    "setting out paper cups for the welcome picnic",
    "sorting picture books for a swap",
    "placing name cards on a table",
]
BALLOON_COLORS = ["sky-blue", "butter-yellow", "berry-red", "mint-green"]
SNAG_POINTS = [
    "the low willow trellis",
    "the wooden welcome arch",
    "the sturdy fence rail",
]
RESCUE_TOOLS = {
    "soft_loop": "soft-loop pole",
    "long_net": "long-handled net",
}

PARAMETER_REGISTRIES = {
    "name": NAMES,
    "helper_name": HELPER_NAMES,
    "newcomer_name": NEWCOMER_NAMES,
    "setting": SETTINGS,
    "activity": ACTIVITIES,
    "balloon_color": BALLOON_COLORS,
    "snag_point": SNAG_POINTS,
    "rescue_tool": list(RESCUE_TOOLS),
}


ASP_RULES = r"""
floats(balloon) :-
    gas(balloon, helium),
    anchor_knot_slips(balloon),
    breeze.

snagged(balloon) :-
    floats(balloon),
    low_catch(balloon).

asks_for_help(hero) :-
    feels_fear(hero),
    calls_for_help(hero),
    helper_nearby(helper).

brave(hero) :-
    feels_fear(hero),
    asks_for_help(hero).

safe_tool(soft_loop).
safe_tool(long_net).

safe_retrieval(balloon) :-
    snagged(balloon),
    brave(hero),
    helper_nearby(helper),
    has_tool(helper, Tool),
    uses_tool(helper, Tool),
    safe_tool(Tool),
    feet_on_ground(hero).

welcomed(newcomer) :-
    safe_retrieval(balloon),
    invites(hero, newcomer).

secure(balloon) :-
    safe_retrieval(balloon),
    tied_safely(balloon).

belonging(newcomer) :-
    welcomed(newcomer),
    answers(newcomer, hero).

#show floats/1.
#show snagged/1.
#show asks_for_help/1.
#show brave/1.
#show safe_retrieval/1.
#show welcomed/1.
#show secure/1.
#show belonging/1.
"""


def _stable_seed(params: StoryParams) -> int:
    text = "|".join(
        str(getattr(params, field_name))
        for field_name in (
            "name",
            "helper_name",
            "newcomer_name",
            "setting",
            "activity",
            "balloon_color",
            "snag_point",
            "rescue_tool",
        )
    )
    return sum((i + 1) * ord(char) for i, char in enumerate(text))


def validate_params(params: StoryParams) -> None:
    for field_name, choices in PARAMETER_REGISTRIES.items():
        value = getattr(params, field_name)
        if value not in choices:
            if field_name == "rescue_tool":
                raise StoryError(
                    f"Unsafe or unknown rescue tool {value!r}. "
                    "The children must stay on the ground; choose 'soft_loop' "
                    "or 'long_net' so a nearby helper can retrieve the balloon."
                )
            raise StoryError(
                f"Invalid {field_name} {value!r}. Choose one of: "
                + ", ".join(repr(choice) for choice in choices)
                + "."
            )
    if params.name == params.newcomer_name:
        raise StoryError("The hero and newcomer need different names.")
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("The seed must be an integer or None.")


def build_world(params: StoryParams) -> World:
    validate_params(params)
    seed = params.seed if params.seed is not None else _stable_seed(params)

    hero = Entity(
        id="hero",
        label=params.name,
        kind="child",
        meters={"feet_on_ground": 1.0},
        memes={"worry": 0.82, "courage": 0.18, "belonging": 0.35},
    )
    helper = Entity(
        id="helper",
        label=params.helper_name,
        kind="helper",
        meters={"nearby": 1.0, "available": 1.0},
        memes={"care": 0.9, "patience": 0.9},
    )
    newcomer = Entity(
        id="newcomer",
        label=params.newcomer_name,
        kind="child",
        meters={"at_welcome_gate": 1.0},
        memes={"worry": 0.62, "belonging": 0.2},
    )
    helium = Entity(
        id="helium",
        label="helium",
        kind="gas",
        owner="balloon",
        meters={"relative_lift": 0.92},
        memes={"wonder": 0.4},
    )
    balloon = Entity(
        id="balloon",
        label=f"{params.balloon_color} balloon",
        kind="balloon",
        owner="welcome_table",
        meters={"height_m": 1.25, "tether_strength": 1.0, "secured": 1.0},
        memes={"hope": 0.6, "belonging": 0.25},
    )
    return World(
        hero=hero,
        helper=helper,
        newcomer=newcomer,
        helium=helium,
        balloon=balloon,
        setting=params.setting,
        params=params,
        seed=seed,
    )


def reasonableness_gate(world: World) -> dict[str, bool]:
    """Check physical and emotional causes before accepting a story outcome."""
    p = world.params
    validate_params(p)
    facts = world.facts

    if facts.get("gas") != "helium":
        raise StoryError("The balloon needs helium for this story's lift.")
    if not facts.get("anchor_knot_slips") or not facts.get("breeze"):
        raise StoryError("The balloon can drift only if its anchor loosens in a breeze.")
    if not facts.get("low_catch") or world.balloon.meters.get("height_m", 99) > 2.0:
        raise StoryError(
            "The balloon must snag somewhere low enough for a helper to reach safely."
        )
    if facts.get("hero_fear_before", 0.0) < 0.5:
        raise StoryError("The bravery turn needs the hero to feel a real worry first.")
    if not facts.get("calls_for_help") or world.helper.meters.get("available", 0.0) < 1.0:
        raise StoryError("The hero needs to ask an available helper for support.")
    if p.rescue_tool not in RESCUE_TOOLS:
        raise StoryError(
            "The children must not climb after the balloon; a nearby helper needs "
            "a safe reach tool."
        )
    if not facts.get("helper_uses_tool") or not facts.get("feet_on_ground"):
        raise StoryError("The balloon must be retrieved with the children safely grounded.")
    if not facts.get("hero_invites") or not facts.get("newcomer_answers"):
        raise StoryError("The resolution needs a real welcome and a response.")

    floats = facts["gas"] == "helium" and facts["anchor_knot_slips"] and facts["breeze"]
    snagged = floats and facts["low_catch"]
    asks_for_help = (
        facts["hero_fear_before"] >= 0.5
        and facts["calls_for_help"]
        and world.helper.meters["available"] >= 1.0
    )
    brave = facts["hero_fear_before"] >= 0.5 and asks_for_help
    safe_retrieval = (
        snagged
        and brave
        and facts["helper_uses_tool"]
        and p.rescue_tool in RESCUE_TOOLS
        and facts["feet_on_ground"]
    )
    welcomed = safe_retrieval and facts["hero_invites"]
    secure = safe_retrieval and facts["balloon_tied_safely"]
    belonging = welcomed and facts["newcomer_answers"]

    outcomes = {
        "floats": bool(floats),
        "snagged": bool(snagged),
        "asks_for_help": bool(asks_for_help),
        "brave": bool(brave),
        "safe_retrieval": bool(safe_retrieval),
        "welcomed": bool(welcomed),
        "secure": bool(secure),
        "belonging": bool(belonging),
    }
    failed = [name for name, value in outcomes.items() if not value]
    if failed:
        raise StoryError(
            "The story's cause-and-effect chain is incomplete: "
            + ", ".join(failed)
            + "."
        )
    return outcomes


def prepare_world(world: World) -> None:
    if world.facts.get("prepared"):
        return

    rng = random.Random(world.seed ^ 0x4E31A7)
    facts = world.facts
    facts.update(
        gas="helium",
        breeze=True,
        anchor_knot_slips=True,
        low_catch=True,
        snag_point=world.params.snag_point,
        rescue_tool=world.params.rescue_tool,
        rescue_tool_label=RESCUE_TOOLS[world.params.rescue_tool],
        hero_fear_before=world.hero.memes["worry"],
        calls_for_help=True,
        helper_uses_tool=True,
        feet_on_ground=True,
        hero_invites=True,
        newcomer_answers=True,
        balloon_tied_safely=True,
        card_message=f"Welcome, {world.newcomer.label}!",
        task_activity=world.params.activity,
        color=world.params.balloon_color,
        reassurance=rng.choice(
            [
                "We can ask together.",
                "I'll stand beside you.",
                "Your voice can be small; I'll still hear it.",
            ]
        ),
        helper_reply=rng.choice(
            [
                "I'm here. Tell me where the ribbon is.",
                "Of course. Point it out, and we'll bring it down gently.",
                "You did the right thing by calling. Show me the snag.",
            ]
        ),
        direction=rng.choice(
            ["A little to your left, please!", "Just above the ribbon!", "Slowly—you're almost there!"]
        ),
        newcomer_reply=rng.choice(
            [
                "I would. You can do the first hello, and I'll do the second.",
                "Yes, please. I'd like to welcome someone with you.",
                "I'd like that. My voice gets small sometimes, too.",
            ]
        ),
        image=rng.choice(
            [
                "The two chairs stood close together beneath the steady balloon.",
                "The welcome card rested beside two cups on the table.",
                "A fresh card lay ready for the next name beside the ribbon.",
            ]
        ),
    )

    world.balloon.meters.update(height_m=1.72, tether_strength=0.2, secured=0.0)
    facts["balloon_recovered"] = True
    facts["balloon_tied_safely"] = True
    outcomes = reasonableness_gate(world)
    facts["outcomes"] = outcomes

    world.balloon.meters.update(height_m=1.35, tether_strength=1.0, secured=1.0)
    world.hero.memes["courage"] = min(1.0, world.hero.memes["courage"] + 0.55)
    world.hero.memes["worry"] = max(0.0, world.hero.memes["worry"] - 0.24)
    world.newcomer.memes["belonging"] = min(
        1.0, world.newcomer.memes["belonging"] + 0.62
    )
    world.newcomer.memes["worry"] = max(0.0, world.newcomer.memes["worry"] - 0.32)
    facts["prepared"] = True


def render_story(world: World) -> str:
    prepare_world(world)
    h = world.hero.label
    helper = world.helper.label
    newcomer = world.newcomer.label
    f = world.facts
    tool = f["rescue_tool_label"]

    lines = [
        f"At {world.setting}, {h} was {f['task_activity']} for the welcome afternoon.",
        (
            f"A {f['color']} helium balloon bobbed above the welcome table, "
            f"its ribbon holding a little card that read, “{f['card_message']}”"
        ),
        (
            f"When {newcomer} stepped through the gate, {h} had just begun to practice "
            "a hello; speaking where everyone could hear still felt hard."
        ),
        (
            f"A breeze tugged the knot anchoring the balloon to the table. Freed from "
            f"its tie, the helium lifted it until the ribbon caught on {f['snag_point']}."
        ),
        (
            f"“That's my name,” {newcomer} said softly. “I hoped someone might say hello.” "
            f"{h} looked at the caught ribbon. “Will you stay beside me while I call "
            f"{helper}?” “{f['reassurance']}” {newcomer} replied."
        ),
        (
            f"With cheeks warm, {h} called, “{helper}, could you help us bring the "
            f"balloon down?” {helper} answered, “{f['helper_reply']}”"
        ),
        (
            f"{helper} brought a {tool} to the low snag. Keeping both feet on the ground, "
            f"{h} pointed and called, “{f['direction']}” The ribbon slipped free, and "
            "the balloon came down without anyone climbing."
        ),
        (
            f"Together they tied it firmly to the table again. {h} turned to {newcomer}: "
            f"“Would you like to help me welcome the next person?” “{f['newcomer_reply']}”"
        ),
        (
            f"{f['image']} When another family came through the gate, {h} said hello "
            f"first, with {newcomer} beside {h}."
        ),
    ]
    return " ".join(lines)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    newcomer = world.newcomer.label
    f = world.facts
    return [
        QAItem(
            question="Why did the balloon rise?",
            answer=(
                "The balloon was filled with helium, a light gas, and a breeze lifted it "
                "after the knot anchoring it to the table slipped."
            ),
        ),
        QAItem(
            question=f"What did {h} do that showed bravery?",
            answer=(
                f"{h} still felt worried, but called {world.helper.label} for help and "
                "guided the safe retrieval while keeping both feet on the ground."
            ),
        ),
        QAItem(
            question=f"How did {newcomer} become part of the welcome afternoon?",
            answer=(
                f"{h} invited {newcomer} to help welcome the next person, and "
                f"{newcomer} agreed to stand beside {h}."
            ),
        ),
        QAItem(
            question="How was the balloon brought down safely?",
            answer=(
                f"{world.helper.label} used a {f['rescue_tool_label']} to free its ribbon "
                f"from {f['snag_point']}, while the children stayed on the ground."
            ),
        ),
    ]


def world_qa(_world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is helium?",
            answer=(
                "Helium is a very light gas. A balloon filled with helium can rise through "
                "the air when it is not held down."
            ),
        ),
        QAItem(
            question="What does bravery mean?",
            answer=(
                "Bravery can mean taking a careful, kind step even while feeling worried. "
                "Asking someone trustworthy for help can be brave, too."
            ),
        ),
        QAItem(
            question="Why can a helium balloon float upward?",
            answer=(
                "Helium is less dense than the air around it, so the surrounding air "
                "pushes up on a helium-filled balloon."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story for young children about helium and a brave choice.",
        (
            f"Tell a gentle story set at {world.setting} where a child asks for help "
            "and welcomes someone new."
        ),
        (
            "Show that bravery can mean speaking up while still feeling nervous, "
            "and end with a concrete image of belonging."
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (world.hero, world.helper, world.newcomer, world.helium, world.balloon):
        lines.append(
            f"  {entity.id:8} {entity.kind:8} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  setting={world.setting!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, prompt in enumerate(sample.prompts, 1):
        out.append(f"{i}. {prompt}")
    out.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.extend(["", "== World QA =="])
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    prepare_world(world)
    story = render_story(world)
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


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
        print()
        print(format_qa(sample))


def _asp_helper():
    try:
        import asp
    except ImportError as exc:
        raise StoryError(
            "ASP mode needs the optional clingo dependency used by storyworlds/asp.py."
        ) from exc
    return asp


def asp_facts(world: Optional[World] = None) -> str:
    asp = _asp_helper()
    if world is None:
        world = build_world(StoryParams())
        prepare_world(world)
    f = world.facts
    facts = [
        asp.fact("gas", "balloon", f["gas"]),
        asp.fact("anchor_knot_slips", "balloon"),
        asp.fact("breeze"),
        asp.fact("low_catch", "balloon"),
        asp.fact("feels_fear", "hero"),
        asp.fact("calls_for_help", "hero"),
        asp.fact("helper_nearby", "helper"),
        asp.fact("has_tool", "helper", f["rescue_tool"]),
        asp.fact("uses_tool", "helper", f["rescue_tool"]),
        asp.fact("feet_on_ground", "hero"),
        asp.fact("invites", "hero", "newcomer"),
        asp.fact("answers", "newcomer", "hero"),
        asp.fact("tied_safely", "balloon"),
    ]
    return "\n".join(facts)


def asp_program(world: Optional[World] = None) -> str:
    return f"{asp_facts(world)}\n\n{ASP_RULES}"


ASP_ATOM_ARGUMENTS = {
    "floats": ("balloon",),
    "snagged": ("balloon",),
    "asks_for_help": ("hero",),
    "brave": ("hero",),
    "safe_retrieval": ("balloon",),
    "welcomed": ("newcomer",),
    "secure": ("balloon",),
    "belonging": ("newcomer",),
}


def python_atoms(world: World) -> set[tuple[str, tuple[str, ...]]]:
    return {
        (predicate, arguments)
        for predicate, arguments in ASP_ATOM_ARGUMENTS.items()
        if world.facts["outcomes"].get(predicate, False)
    }


def asp_atoms(world: World) -> set[tuple[str, tuple[str, ...]]]:
    asp = _asp_helper()
    model = asp.one_model(asp_program(world))
    if not model:
        raise StoryError("The ASP rules did not produce a model.")
    actual: set[tuple[str, tuple[str, ...]]] = set()
    for predicate in ASP_ATOM_ARGUMENTS:
        for arguments in asp.atoms(model, predicate):
            actual.add((predicate, tuple(str(value) for value in arguments)))
    return actual


def asp_valid(world: Optional[World] = None) -> bool:
    try:
        if world is None:
            world = build_world(StoryParams())
            prepare_world(world)
        reasonableness_gate(world)
        return True
    except StoryError:
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming helium-and-bravery storyworld."
    )
    parser.add_argument("--name")
    parser.add_argument("--helper-name")
    parser.add_argument("--newcomer-name")
    parser.add_argument("--setting")
    parser.add_argument("--activity")
    parser.add_argument("--balloon-color")
    parser.add_argument("--snag-point")
    parser.add_argument("--rescue-tool")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name if args.name is not None else rng.choice(NAMES)
    helper_name = (
        args.helper_name
        if args.helper_name is not None
        else rng.choice(HELPER_NAMES)
    )
    if args.newcomer_name is not None:
        newcomer_name = args.newcomer_name
    else:
        possible_newcomers = [n for n in NEWCOMER_NAMES if n != name]
        newcomer_name = rng.choice(possible_newcomers)
    params = StoryParams(
        name=name,
        helper_name=helper_name,
        newcomer_name=newcomer_name,
        setting=args.setting if args.setting is not None else rng.choice(SETTINGS),
        activity=args.activity if args.activity is not None else rng.choice(ACTIVITIES),
        balloon_color=(
            args.balloon_color
            if args.balloon_color is not None
            else rng.choice(BALLOON_COLORS)
        ),
        snag_point=(
            args.snag_point if args.snag_point is not None else rng.choice(SNAG_POINTS)
        ),
        rescue_tool=(
            args.rescue_tool
            if args.rescue_tool is not None
            else rng.choice(list(RESCUE_TOOLS))
        ),
    )
    validate_params(params)
    return params


def _curated_params(seed: int) -> list[StoryParams]:
    return [
        StoryParams(
            name="Lena",
            helper_name="Ms. Rowan",
            newcomer_name="June",
            setting="the library courtyard",
            activity="laying out story blankets",
            balloon_color="sky-blue",
            snag_point="the low willow trellis",
            rescue_tool="soft_loop",
            seed=seed,
        ),
        StoryParams(
            name="Milo",
            helper_name="Mr. Ellis",
            newcomer_name="Sol",
            setting="the school garden",
            activity="setting out paper cups for the welcome picnic",
            balloon_color="butter-yellow",
            snag_point="the wooden welcome arch",
            rescue_tool="long_net",
            seed=seed + 1,
        ),
        StoryParams(
            name="Nia",
            helper_name="Aunt Bea",
            newcomer_name="Kit",
            setting="the park picnic shelter",
            activity="sorting picture books for a swap",
            balloon_color="berry-red",
            snag_point="the sturdy fence rail",
            rescue_tool="soft_loop",
            seed=seed + 2,
        ),
        StoryParams(
            name="Owen",
            helper_name="Coach Sal",
            newcomer_name="Noor",
            setting="the neighborhood hall",
            activity="placing name cards on a table",
            balloon_color="mint-green",
            snag_point="the low willow trellis",
            rescue_tool="long_net",
            seed=seed + 3,
        ),
    ]


def _story_is_complete(sample: StorySample) -> bool:
    world = sample.world
    if world is None:
        return False
    if not sample.story.endswith("."):
        return False
    if "helium" not in sample.story.lower():
        return False
    if sample.story.count("“") != sample.story.count("”"):
        return False
    if sample.story.count("“") < 6:
        return False
    if "{" in sample.story or "}" in sample.story:
        return False
    if not all(world.facts["outcomes"].values()):
        return False
    if not sample.story_qa or not sample.world_qa:
        return False
    return all(item.answer.strip().endswith(".") for item in sample.story_qa)


def asp_verify() -> int:
    try:
        asp = _asp_helper()
        cases = _curated_params(4100)
        for params in cases:
            sample = generate(params)
            if not _story_is_complete(sample):
                print(f"Story exercise failed for {params.name}.")
                return 1
            expected = python_atoms(sample.world)
            model = asp.one_model(asp_program(sample.world))
            if not model:
                print(f"ASP produced no model for {params.name}.")
                return 1
            actual: set[tuple[str, tuple[str, ...]]] = set()
            for predicate in ASP_ATOM_ARGUMENTS:
                for arguments in asp.atoms(model, predicate):
                    actual.add((predicate, tuple(str(value) for value in arguments)))
            if actual != expected:
                print(f"Mismatch for {params.name}.")
                print("ASP:", sorted(actual))
                print("PY :", sorted(expected))
                return 1
        print("OK: ASP/Python parity and generated-story checks verified.")
        return 0
    except StoryError as exc:
        print(str(exc), file=sys.stderr)
        return 2


def _params_for_args(args: argparse.Namespace, seed: int) -> StoryParams:
    params = resolve_params(args, random.Random(seed))
    params.seed = seed
    validate_params(params)
    return params


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.verify:
            raise SystemExit(asp_verify())

        if args.n < 1:
            raise StoryError("-n must be at least 1.")

        base_seed = args.seed if args.seed is not None else random.randrange(2**31)

        if args.show_asp:
            params = _params_for_args(args, base_seed)
            sample = generate(params)
            print(asp_program(sample.world))
            return

        if args.asp:
            params = _params_for_args(args, base_seed)
            sample = generate(params)
            expected = python_atoms(sample.world)
            actual = asp_atoms(sample.world)
            if expected != actual:
                print("Mismatch between ASP and Python expectations.")
                print("ASP:", sorted(actual))
                print("PY :", sorted(expected))
                raise SystemExit(1)
            print("ASP model:")
            for predicate, arguments in sorted(actual):
                print(f"  {predicate}({', '.join(arguments)})")
            return

        if args.all:
            samples = [generate(params) for params in _curated_params(base_seed)]
        else:
            samples = []
            seen: set[str] = set()
            attempt = 0
            while len(samples) < args.n and attempt < max(100, args.n * 30):
                seed = base_seed + attempt
                params = _params_for_args(args, seed)
                sample = generate(params)
                attempt += 1
                if sample.story in seen:
                    continue
                seen.add(sample.story)
                samples.append(sample)
            if len(samples) != args.n:
                raise StoryError(
                    "Could not produce the requested number of distinct stories."
                )

        if args.json:
            if len(samples) == 1:
                print(samples[0].to_json())
            else:
                print(
                    json.dumps(
                        [sample.to_dict() for sample in samples],
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            return

        for index, sample in enumerate(samples):
            header = ""
            if args.all:
                header = f"### {sample.params.name} at {sample.params.setting}"
            elif len(samples) > 1:
                header = f"### variant {index + 1}"
            emit(sample, trace=args.trace, qa=args.qa, header=header)
            if index < len(samples) - 1:
                print("\n" + "=" * 70 + "\n")
    except StoryError as exc:
        print(f"Story error: {exc}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
