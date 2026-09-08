#!/usr/bin/env python3
"""
A tiny superhero storyworld about a banana, influence, surprise, repetition,
and friendship.

Luna learns that influence is not a superpower for bossing people around. It
is the gentle power to help a friend choose a brave, kind action.
"""

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
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "heroine":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "hero":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Mission:
    id: str
    danger: str
    clue: str
    surprise: str
    repeated_call: str
    friendship_action: str
    ending: str


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def note(self, text: str) -> None:
        self.trace.append(text)


@dataclass
class StoryParams:
    place: str
    banana: str
    influence: str
    name: str
    friend: str
    mission: str
    seed: Optional[int] = None


PLACES = {
    "rooftop_garden": "the rooftop garden",
    "moonlight_market": "the moonlight market",
    "sunny_schoolyard": "the sunny schoolyard",
}

BANANAS = {
    "golden_banana": "a golden banana",
    "blue_banana": "a blue banana",
    "tiny_banana": "a tiny banana",
}

INFLUENCES = {
    "kind_words": "kind words",
    "brave_example": "a brave example",
    "listening": "careful listening",
}

MISSIONS = {
    "runaway_cart": Mission(
        id="runaway_cart",
        danger="a snack cart began rolling toward the open stairway",
        clue="a yellow wheel mark curved across the tiles",
        surprise="the banana popped open and revealed a bright golden signal",
        repeated_call="Luna called, \"Friends, follow my count: one, two, help!\"",
        friendship_action="stood beside her friend and pushed the cart together",
        ending="the cart rested safely beneath a striped awning while the banana glowed like a little sun",
    ),
    "sleepy_dragon": Mission(
        id="sleepy_dragon",
        danger="a small cloud dragon sneezed sparks over the flower beds",
        clue="three warm circles appeared in the grass",
        surprise="the banana peeled itself into a tiny yellow umbrella",
        repeated_call="Luna repeated, \"Slow breaths, soft wings, safe friends.\"",
        friendship_action="shared the umbrella and helped the dragon breathe slowly",
        ending="the dragon slept beside the flowers, dreaming gentle silver clouds",
    ),
    "missing_lantern": Mission(
        id="missing_lantern",
        danger="the market lantern that guided everyone home vanished",
        clue="a trail of orange crumbs led behind the music stage",
        surprise="the banana rang like a bell when Luna lifted it",
        repeated_call="Luna called again and again, \"Listen for the bright sound!\"",
        friendship_action="searched with her friend instead of ordering the crowd around",
        ending="the lantern shone from a high branch, and every path looked friendly again",
    ),
    "whispering_bridge": Mission(
        id="whispering_bridge",
        danger="the little bridge began whispering that it could not hold the evening crowd",
        clue="one loose plank trembled beneath a fallen leaf",
        surprise="the banana became a bright bridge marker",
        repeated_call="Luna repeated, \"One careful step, then another.\"",
        friendship_action="crossed slowly with her friend while everyone waited their turn",
        ending="the bridge settled, marked by the cheerful banana flag",
    ),
}

NAMES = {
    "Luna": "heroine",
    "Maya": "heroine",
    "Zoe": "heroine",
    "Nia": "heroine",
    "Ivy": "heroine",
    "Kai": "hero",
    "Leo": "hero",
    "Milo": "hero",
    "Noah": "hero",
    "Sam": "child",
}

FRIENDS = {
    "Pip": "child",
    "Ari": "child",
    "Tess": "child",
    "Bo": "child",
    "Mina": "heroine",
    "Finn": "hero",
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [
        (place, banana, mission)
        for place in PLACES
        for banana in BANANAS
        for mission in MISSIONS
    ]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    for field_name, registry in (
        ("place", PLACES),
        ("banana", BANANAS),
        ("mission", MISSIONS),
        ("influence", INFLUENCES),
    ):
        value = getattr(args, field_name, None)
        if value is not None and value not in registry:
            raise StoryError(
                f"Unknown {field_name} {value!r}. Choose one of: "
                + ", ".join(registry)
            )

    place = args.place or rng.choice(list(PLACES))
    banana = args.banana or rng.choice(list(BANANAS))
    mission = args.mission or rng.choice(list(MISSIONS))
    influence = args.influence or rng.choice(list(INFLUENCES))
    name = args.name or rng.choice(list(NAMES))
    friend = args.friend or rng.choice(list(FRIENDS))

    if name == friend:
        raise StoryError("The hero and friend must have different names.")

    return StoryParams(
        place=place,
        banana=banana,
        influence=influence,
        name=name,
        friend=friend,
        mission=mission,
    )


def build_world(params: StoryParams) -> World:
    world = World(PLACES[params.place])
    hero = world.add(Entity("hero", NAMES.get(params.name, "child"), params.name))
    friend = world.add(Entity("friend", FRIENDS.get(params.friend, "child"), params.friend))
    banana = world.add(Entity("banana", "object", BANANAS[params.banana]))
    world.facts.update(
        {
            "hero": hero,
            "friend": friend,
            "banana": banana,
            "influence": INFLUENCES[params.influence],
            "mission": MISSIONS[params.mission],
            "danger_active": True,
        }
    )
    hero.memes["courage"] = 1.0
    friend.memes["trust"] = 1.0
    banana.meters["ordinary"] = 1.0
    return world


def _rng(params: StoryParams) -> random.Random:
    if params.seed is not None:
        return random.Random(params.seed ^ 0xBADA55)
    text = "|".join(
        (params.place, params.banana, params.influence, params.name, params.friend, params.mission)
    )
    return random.Random(sum((i + 1) * ord(ch) for i, ch in enumerate(text)))


def _influence_phrase(params: StoryParams, hero: Entity, friend: Entity) -> str:
    if params.influence == "kind_words":
        return (
            f"{hero.label} used {INFLUENCES[params.influence]}: "
            f"\"We can do this together, {friend.label}.\""
        )
    if params.influence == "brave_example":
        return (
            f"{hero.label} used {INFLUENCES[params.influence]} by taking one "
            f"careful step first."
        )
    return (
        f"{hero.label} used {INFLUENCES[params.influence]} and waited until "
        f"{friend.label} finished speaking."
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.banana not in BANANAS:
        raise StoryError(f"Unknown banana: {params.banana}")
    if params.influence not in INFLUENCES:
        raise StoryError(f"Unknown influence: {params.influence}")
    if params.mission not in MISSIONS:
        raise StoryError(f"Unknown mission: {params.mission}")

    world = build_world(params)
    hero = world.entities["hero"]
    friend = world.entities["friend"]
    banana = world.entities["banana"]
    mission = MISSIONS[params.mission]
    rng = _rng(params)

    opening = rng.choice(
        [
            f"On the highest roof of {world.place}, {hero.label} wore a red cape and guarded {BANANAS[params.banana]}.",
            f"{hero.label} was the neighborhood superhero, and today the patrol began at {world.place} with {BANANAS[params.banana]} in one pocket.",
            f"The sky was bright above {world.place}. {hero.label} lifted {BANANAS[params.banana]} and promised to use its strange power wisely.",
        ]
    )
    discovery = rng.choice(
        [
            f"Then {mission.danger}.",
            f"Suddenly, {mission.danger}, and {friend.label} froze beside the nearest planter.",
            f"A warning bell rang. {mission.danger.capitalize()}.",
        ]
    )
    clue = f"{hero.label} spotted the clue: {mission.clue}."
    dialogue_one = (
        f"\"Should I tell everyone what to do?\" asked {friend.label}. "
        f"\"You can help choose,\" said {hero.label}. \"What do you notice?\""
    )
    answer = f"{friend.label} looked carefully and answered, \"The safest way is to work together.\""
    surprise = (
        f"Just then, {mission.surprise}. "
        f"The {banana.label} no longer seemed ordinary."
    )
    repeated = (
        f"{hero.label} did not shout orders. Instead, {mission.repeated_call} "
        f"Each repetition made the plan clearer."
    )
    influence = _influence_phrase(params, hero, friend)
    action = f"Because of that friendship, they {mission.friendship_action}."
    dialogue_two = (
        f"\"Your idea helped us,\" said {hero.label}. "
        f"\"And your courage helped me,\" replied {friend.label}."
    )
    resolution = (
        f"The danger passed. The friends laughed, and {mission.ending}. "
        f"{hero.label} learned that influence is strongest when it leaves room "
        f"for another person to be brave."
    )

    hero.memes["influence"] = 1.0
    friend.memes["influence"] = 1.0
    banana.meters["ordinary"] = 0.0
    banana.meters["surprising"] = 1.0
    friend.memes["confidence"] = 1.0
    world.facts["danger_active"] = False
    world.facts["lesson"] = "Friendship turns influence into cooperation."
    world.note("The danger created a choice.")
    world.note("The friend contributed an observation.")
    world.note("Repetition made the shared plan memorable.")
    world.note("The banana changed from ordinary object to surprising helper.")
    world.note("Friendship completed the rescue.")

    story = "\n\n".join(
        [
            opening,
            discovery + " " + clue,
            dialogue_one + " " + answer,
            surprise,
            repeated + " " + influence,
            action + " " + dialogue_two,
            resolution,
        ]
    )

    prompts = [
        "Write a child-friendly superhero story with a banana, influence, surprise, repetition, and friendship.",
        f"Tell a story in {world.place} where {params.name} learns that influence means helping a friend choose bravely.",
        "Create a gentle superhero rescue in which repeated words make a shared plan clear.",
    ]
    story_qa = [
        QAItem(
            question="What danger did the superhero face?",
            answer=f"The superhero faced this danger: {mission.danger}.",
        ),
        QAItem(
            question="What surprising thing happened to the banana?",
            answer=f"{mission.surprise.capitalize()}.",
        ),
        QAItem(
            question=f"How did {params.friend} help?",
            answer=f"{params.friend} noticed what was safest and then {mission.friendship_action}.",
        ),
        QAItem(
            question="How did repetition help?",
            answer=f"The repeated call, “{mission.repeated_call.strip('\"')},” made the plan clearer so the friends could act together.",
        ),
        QAItem(
            question="What did the hero learn about influence?",
            answer="The hero learned that influence is strongest when it helps another person become brave instead of ordering that person around.",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is influence?",
            answer="Influence is the power to affect what someone thinks or does, and it is kindest when it supports good choices without taking away freedom.",
        ),
        QAItem(
            question="Why can repetition help during a rescue?",
            answer="Repetition can make an important message easy to remember when people feel surprised or worried.",
        ),
        QAItem(
            question="What makes friendship useful in a difficult moment?",
            answer="Friendship lets people listen, share ideas, and work together instead of facing a problem alone.",
        ),
        QAItem(
            question="What kind of superhero was Luna?",
            answer="Luna was a superhero who used courage, careful listening, and friendship to help others.",
        ),
    ]
    return StorySample(
        params=params,
        story=story,
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place: {world.place}")
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.label}: kind={entity.kind}, meters={meters}, memes={memes}"
        )
    for item in world.trace:
        lines.append(f"  event: {item}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
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
        print()
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


ASP_RULES = r"""
valid(Place, Banana, Mission) :-
    setting(Place),
    banana(Banana),
    mission(Mission).

influence_kind(kind_words).
influence_kind(brave_example).
influence_kind(listening).

safe_story(Place, Banana, Mission) :-
    valid(Place, Banana, Mission).
"""


def asp_facts() -> str:
    import asp

    facts: list[str] = []
    for place in PLACES:
        facts.append(asp.fact("setting", place))
    for banana in BANANAS:
        facts.append(asp.fact("banana", banana))
    for mission in MISSIONS:
        facts.append(asp.fact("mission", mission))
    return "\n".join(facts)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set != clingo_set:
        print("MISMATCH between Python and ASP combinations.")
        print("Only in Python:", sorted(python_set - clingo_set))
        print("Only in ASP:", sorted(clingo_set - python_set))
        return 1

    print(f"OK: ASP matches Python ({len(python_set)} combinations).")
    check = StoryParams(
        place="rooftop_garden",
        banana="golden_banana",
        influence="kind_words",
        name="Luna",
        friend="Pip",
        mission="runaway_cart",
        seed=7,
    )
    sample = generate(check)
    required = ("banana", "influence", "surprise", "friendship")
    lower = sample.story.lower()
    missing = [word for word in required if word not in lower]
    if missing:
        print("Generated-story check failed; missing:", ", ".join(missing))
        return 1
    print("OK: generated story exercises the required narrative instruments.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a gentle superhero story about banana-powered influence."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--banana", choices=BANANAS)
    parser.add_argument("--influence", choices=INFLUENCES)
    parser.add_argument("--mission", choices=MISSIONS)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        try:
            raise SystemExit(asp_verify())
        except ImportError as exc:
            print(f"ASP verification unavailable: {exc}", file=sys.stderr)
            raise SystemExit(1)

    if args.asp:
        try:
            combinations = asp_valid_combos()
        except ImportError as exc:
            print(f"ASP mode unavailable: {exc}", file=sys.stderr)
            raise SystemExit(1)
        print(f"{len(combinations)} compatible combinations:")
        for combination in combinations:
            print(" ", combination)
        return

    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, (place, banana, mission) in enumerate(valid_combos()):
            params = StoryParams(
                place=place,
                banana=banana,
                influence=list(INFLUENCES)[index % len(INFLUENCES)],
                name="Luna",
                friend="Pip",
                mission=mission,
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempts = 0
        while len(samples) < args.n and attempts < max(50, args.n * 50):
            seed = base_seed + attempts
            attempts += 1
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)

        if len(samples) < args.n:
            raise SystemExit("Could not generate the requested number of distinct stories.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
