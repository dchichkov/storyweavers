#!/usr/bin/env python3
"""A heartwarming helium-balloon storyworld about finding the courage to say hello."""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional


for _candidate in Path(__file__).resolve().parents:
    if _candidate.name == "storyworlds" and (_candidate / "results.py").is_file():
        sys.path.insert(0, str(_candidate.parent))
        sys.path.insert(0, str(_candidate))
        break
else:
    raise RuntimeError("Could not find storyworlds/results.py beside this storyworld.")

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Item:
    id: str
    label: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    friend: Item
    helper: Item
    balloon: Item
    card: Item
    place: str
    trouble: str
    seed: int
    color: str
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    friend: str
    helper: str
    place: str
    trouble: str
    seed: Optional[int] = None


NAMES = ("Ari", "Mira", "Theo", "Nia", "Leo", "Sasha", "June", "Owen")
FRIENDS = ("Bea", "Cal", "Dara", "Emil", "Finn", "Kit", "Luz", "Robin")
HELPERS = ("Ms. Rowan", "Grandpa Eli", "Aunt Nia", "Mr. Solis")
PLACES = (
    "the neighborhood picnic lawn",
    "the little library green",
    "the school garden picnic area",
)
TROUBLES = ("branch", "awning", "gate")
COLORS = ("blue", "gold", "red", "green")


ASP_RULES = r"""
brave(H) :- worried(H), asked_help(H).
safe_return(H) :- balloon_recovered(H), adult_help(H), ground_level(H).
welcomed(H) :- greeted_friend(H), friend_present(H).
complete(H) :- brave(H), safe_return(H), welcomed(H).
reasonable :- complete(hero).

:- chosen_name(N), not registered_name(N).
:- chosen_friend(N), not registered_friend(N).
:- chosen_helper(N), not registered_helper(N).
:- chosen_place(P), not registered_place(P).
:- chosen_trouble(T), not registered_trouble(T).
:- not reasonable.

#show brave/1.
#show safe_return/1.
#show welcomed/1.
#show complete/1.
#show reasonable/0.
"""


def asp_facts(world: Optional[World] = None) -> str:
    """Emit registry facts and, when supplied, the facts for one generated world."""
    import asp

    lines = []
    for name in NAMES:
        lines.append(asp.fact("registered_name", name))
    for name in FRIENDS:
        lines.append(asp.fact("registered_friend", name))
    for name in HELPERS:
        lines.append(asp.fact("registered_helper", name))
    for place in PLACES:
        lines.append(asp.fact("registered_place", place))
    for trouble in TROUBLES:
        lines.append(asp.fact("registered_trouble", trouble))

    if world is not None:
        lines.extend(
            [
                asp.fact("chosen_name", world.hero.label),
                asp.fact("chosen_friend", world.friend.label),
                asp.fact("chosen_helper", world.helper.label),
                asp.fact("chosen_place", world.place),
                asp.fact("chosen_trouble", world.trouble),
            ]
        )
        facts = world.facts
        for key, predicate in (
            ("felt_worry", "worried"),
            ("asked_for_help", "asked_help"),
            ("adult_helped", "adult_help"),
            ("ground_level_method", "ground_level"),
            ("balloon_recovered", "balloon_recovered"),
            ("greeted_friend", "greeted_friend"),
            ("friend_present", "friend_present"),
        ):
            if facts.get(key):
                lines.append(asp.fact(predicate, "hero"))

    return "\n".join(lines)


def asp_program(world: World) -> str:
    return f"{asp_facts(world)}\n{ASP_RULES}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming storyworld about helium, bravery, and saying hello."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", choices=FRIENDS)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--trouble", choices=TROUBLES)
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
    name = args.name or rng.choice(NAMES)
    friend_choices = tuple(candidate for candidate in FRIENDS if candidate != name)
    friend = args.friend or rng.choice(friend_choices)
    return StoryParams(
        name=name,
        friend=friend,
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(PLACES),
        trouble=args.trouble or rng.choice(TROUBLES),
    )


def _validate_params(params: StoryParams) -> None:
    registries = (
        ("name", params.name, NAMES),
        ("friend", params.friend, FRIENDS),
        ("helper", params.helper, HELPERS),
        ("place", params.place, PLACES),
        ("trouble", params.trouble, TROUBLES),
    )
    for field_name, value, choices in registries:
        if value not in choices:
            raise StoryError(
                f"Invalid {field_name} {value!r}; choose one of: {', '.join(choices)}."
            )
    if params.name == params.friend:
        raise StoryError("The hero and the new friend need different names.")


def build_world(params: StoryParams) -> World:
    _validate_params(params)
    seed = params.seed
    if seed is None:
        seed = sum(
            ord(char)
            for char in (
                f"{params.name}|{params.friend}|{params.helper}|"
                f"{params.place}|{params.trouble}"
            )
        )
    rng = random.Random(seed ^ 0x48E11A)
    color = rng.choice(COLORS)

    hero = Item(
        id="hero",
        label=params.name,
        kind="character",
        meters={"height_m": 0.0},
        memes={"worry": 0.82, "courage": 0.18, "belonging": 0.22},
    )
    friend = Item(
        id="friend",
        label=params.friend,
        kind="character",
        meters={"height_m": 0.0},
        memes={"worry": 0.68, "courage": 0.30, "belonging": 0.24},
    )
    helper = Item(
        id="helper",
        label=params.helper,
        kind="character",
        meters={"height_m": 0.0},
        memes={"care": 0.90, "confidence": 0.88},
    )
    balloon = Item(
        id="helium_balloon",
        label=f"{color} helium balloon",
        kind="balloon",
        owner="hero",
        meters={"height_m": 2.25, "tether_length_m": 1.8},
        memes={"buoyancy": 0.95, "welcome": 0.80},
    )
    card = Item(
        id="welcome_card",
        label=f"welcome card for {params.friend}",
        kind="card",
        owner="hero",
        meters={"height_m": 2.05},
        memes={"welcome": 0.95},
    )
    return World(
        hero=hero,
        friend=friend,
        helper=helper,
        balloon=balloon,
        card=card,
        place=params.place,
        trouble=params.trouble,
        seed=seed,
        color=color,
        facts={
            "felt_worry": True,
            "asked_for_help": False,
            "adult_helped": False,
            "ground_level_method": False,
            "balloon_recovered": False,
            "greeted_friend": False,
            "friend_present": True,
        },
    )


def _finish_world(
    world: World,
    *,
    story: str,
    cause: str,
    discovery: str,
    resolution: str,
    ending: str,
) -> str:
    world.facts.update(
        story=story,
        cause=cause,
        discovery=discovery,
        resolution=resolution,
        ending=ending,
        asked_for_help=True,
        adult_helped=True,
        ground_level_method=True,
        balloon_recovered=True,
        greeted_friend=True,
        friend_present=True,
    )
    world.hero.memes.update(worry=0.20, courage=0.86, belonging=0.91)
    world.friend.memes.update(worry=0.24, courage=0.67, belonging=0.88)
    world.balloon.meters.update(height_m=1.30, tether_length_m=1.1)
    world.balloon.memes.update(welcome=0.99, safely_tethered=1.0)
    world.card.owner = "hero_and_friend"
    world.card.meters["height_m"] = 1.10
    return story


def _branch_story(world: World, rng: random.Random) -> str:
    hero, friend, helper = world.hero.label, world.friend.label, world.helper.label
    place = world.place
    color = world.color
    cause = (
        "a gust lifted the helium balloon until its ribbon curled around a low maple branch"
    )
    discovery = (
        "helium kept the balloon floating upward, while the ribbon was what caught on the branch"
    )
    resolution = (
        f"{hero} asked {helper} to help, and {helper} freed the ribbon from the ground with a long-handled hook"
    )
    ending = (
        f"the {color} balloon bobbed above the picnic basket while {hero} and {friend} held the welcome card together"
    )
    lines = [
        f"At {place}, {hero} had filled a {color} balloon with helium and tied it to a card that read, "
        f'"Welcome, {friend}!" {hero} hoped the balloon could say hello first, because meeting a new neighbor felt scary.',
        "A gust lifted the balloon into a low maple branch, and its ribbon curled around a twig just above the picnic table.",
        f'"Is that card for me?" {friend} asked at the garden gate.',
        f'"It is," {hero} said. "I wanted to say hello, but now I feel too nervous to call out."',
        f'"I was nervous about coming over, too," said {friend}. "Could we ask {helper} together?"',
        f'{hero} took a breath. "{helper}, would you help us reach the ribbon, please?"',
        f'"Of course," {helper} replied. "We will keep both feet on the grass." {helper} used a long-handled hook to ease the ribbon free.',
        f"The balloon drifted down, and {hero} tied its ribbon securely to the picnic basket.",
        f'"Hello, {friend}," {hero} said, holding out one side of the card. "Would you hold this with me?"',
        f'"Hello, {hero}. I would like that," {friend} answered.',
        f"By the time the picnic began, {ending}.",
    ]
    story = " ".join(lines)
    return _finish_world(
        world,
        story=story,
        cause=cause,
        discovery=discovery,
        resolution=resolution,
        ending=ending,
    )


def _awning_story(world: World, rng: random.Random) -> str:
    hero, friend, helper = world.hero.label, world.friend.label, world.helper.label
    place = world.place
    color = world.color
    cause = (
        "a breeze pushed the helium balloon beneath the picnic shelter and looped its ribbon over a wooden beam"
    )
    discovery = (
        "the balloon floated because it was filled with helium, but the wind and the beam trapped its ribbon"
    )
    resolution = (
        f"{hero} asked {helper} for help, and {helper} used a long-handled hook from the ground to lift the ribbon over the beam"
    )
    ending = (
        f"the {color} balloon floated safely above two chairs pulled side by side, with the welcome card between them"
    )
    lines = [
        f"At {place}, {hero} had made a welcome card for {friend} and tied it beneath a {color} helium balloon.",
        f"{hero} had practiced saying hello in a whisper, but a breeze carried the balloon under the picnic shelter and looped its ribbon over a wooden beam.",
        f'{friend} arrived and looked up. "I think that card has my name on it," {friend} said.',
        f'"Yes," {hero} answered. "I was hoping the balloon would help me say hello. Now it is stuck, and I am afraid to ask anyone."',
        f'"I almost turned around at the gate," {friend} admitted. "Maybe we can be brave together."',
        f'"{helper}, could you help us get the ribbon down?" {hero} called, surprised by how clear the words sounded.',
        f'"You asked just right," {helper} said. Staying on the ground, {helper} raised a long-handled hook and lifted the ribbon over the beam.',
        f"The helium balloon floated down into {hero}'s hands. {hero} tied it firmly to the picnic basket, where the wind could not whisk it away.",
        f'"I am glad you came," {hero} told {friend}. "Would you like to help me welcome everyone?"',
        f'"Yes," said {friend}. "Now I know someone here."',
        f"Soon the picnic was full of greetings, and {ending}.",
    ]
    story = " ".join(lines)
    return _finish_world(
        world,
        story=story,
        cause=cause,
        discovery=discovery,
        resolution=resolution,
        ending=ending,
    )


def _gate_story(world: World, rng: random.Random) -> str:
    hero, friend, helper = world.hero.label, world.friend.label, world.helper.label
    place = world.place
    color = world.color
    cause = (
        "a gust tugged the buoyant helium balloon against the wooden gate and wound its ribbon around the rounded latch"
    )
    discovery = (
        "helium made the balloon rise, and the breeze pulled its loose ribbon around the gate latch"
    )
    resolution = (
        f"{hero} asked {helper} to steady the gate; while {hero} held the basket, {helper} unwound the ribbon safely from the ground"
    )
    ending = (
        f"the {color} helium balloon bobbed above a weighted basket, and {hero} and {friend} sat together beneath its welcome card"
    )
    lines = [
        f"At {place}, {hero} had tied a welcome card for {friend} beneath a {color} helium balloon.",
        f"When a gust swept across the lawn, the balloon floated against the wooden gate and its ribbon wound around the rounded latch.",
        f'{friend} stopped just inside the gate. "Is the picnic still happening?" {friend} asked.',
        f'"Yes," said {hero}. "I made that card for you. I am worried about the balloon, and I am worried about saying hello."',
        f'"I was worried about walking in," {friend} replied. "We could ask {helper} to help us."',
        f'{hero} nodded and called, "{helper}, would you please steady the gate while we keep the basket from sliding?"',
        f'"Gladly," {helper} said. {helper} steadied the gate and gently unwound the ribbon while {hero} held the basket on the grass.',
        f"Once the balloon was free, {hero} tied it securely to the basket instead of letting the wind carry it away.",
        f'"I am happy you came," {hero} said. "Will you sit with me?"',
        f'"I will," {friend} said, smiling. "I am happy you asked."',
        f"At the picnic, {ending}.",
    ]
    story = " ".join(lines)
    return _finish_world(
        world,
        story=story,
        cause=cause,
        discovery=discovery,
        resolution=resolution,
        ending=ending,
    )


STORY_BUILDERS = {
    "branch": _branch_story,
    "awning": _awning_story,
    "gate": _gate_story,
}


def reasonableness_gate(world: World) -> bool:
    """Reject an unsafe or emotionally incomplete resolution."""
    if world.trouble not in TROUBLES:
        raise StoryError(f"Unknown balloon trouble {world.trouble!r}.")
    required = (
        "felt_worry",
        "asked_for_help",
        "adult_helped",
        "ground_level_method",
        "balloon_recovered",
        "greeted_friend",
        "friend_present",
    )
    missing = [fact for fact in required if not world.facts.get(fact)]
    if missing:
        raise StoryError(
            "The story needs a safe, complete bravery arc; missing state: "
            + ", ".join(missing)
            + "."
        )
    if world.balloon.meters.get("height_m", 99.0) > 1.6:
        raise StoryError("The balloon must be safely tethered near the picnic basket.")
    if not world.facts.get("story"):
        raise StoryError("The world has no rendered story.")
    return True


def asp_valid(world: World) -> bool:
    """The Python reasonableness gate, mirrored by ASP_RULES."""
    try:
        return reasonableness_gate(world)
    except StoryError:
        return False


def generate_story(world: World) -> str:
    builder = STORY_BUILDERS[world.trouble]
    rng = random.Random(world.seed ^ 0xC0A6E)
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero.label
    friend = world.friend.label
    facts = world.facts
    return [
        QAItem(
            question=f"Why did the helium balloon get stuck?",
            answer=f"It got stuck because {facts['cause']}.",
        ),
        QAItem(
            question=f"What did {hero} learn about the balloon?",
            answer=f"{hero} learned that {facts['discovery']}.",
        ),
        QAItem(
            question=f"How did {hero} show bravery?",
            answer=(
                f"{hero} felt nervous but asked for safe help, then greeted {friend} "
                "instead of letting the balloon speak for them."
            ),
        ),
        QAItem(
            question=f"How was the problem solved?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="What changed by the end of the story?",
            answer=f"By the end, {facts['ending']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is helium?",
            answer=(
                "Helium is a light gas that can fill a balloon and help it float upward. "
                "People should not breathe gas from balloons."
            ),
        ),
        QAItem(
            question="What does bravery mean?",
            answer=(
                "Bravery means doing something helpful or right even when you feel worried. "
                "Asking a trusted grown-up for help can be brave."
            ),
        ),
        QAItem(
            question="Why should a helium balloon be tied down?",
            answer=(
                "A helium balloon can float away if its ribbon is loose, so tying it to a "
                "secure weight helps keep it nearby."
            ),
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story for young children about helium and a brave choice.",
        (
            f"Tell a gentle story at {world.place} where {world.hero.label} feels nervous "
            f"about welcoming {world.friend.label}."
        ),
        "Show that bravery can mean asking for help and making someone feel welcome.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in (
        world.hero,
        world.friend,
        world.helper,
        world.balloon,
        world.card,
    ):
        lines.append(
            f"  {entity.id:14} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r} trouble={world.trouble!r} seed={world.seed}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        lines.append(f"{index}. {prompt}")
    lines.extend(["", "== Story QA =="])
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.extend(["", "== World QA =="])
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
    if not reasonableness_gate(world):
        raise StoryError("The generated story did not pass the reasonableness gate.")
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


def _python_atoms(world: World) -> set[tuple[str, tuple[str, ...]]]:
    if not reasonableness_gate(world):
        return set()
    return {
        ("brave", ("hero",)),
        ("safe_return", ("hero",)),
        ("welcomed", ("hero",)),
        ("complete", ("hero",)),
        ("reasonable", ()),
    }


def asp_verify() -> int:
    import asp

    for index, trouble in enumerate(TROUBLES):
        params = StoryParams(
            name=NAMES[index],
            friend=FRIENDS[index],
            helper=HELPERS[index],
            place=PLACES[index],
            trouble=trouble,
            seed=197 + index,
        )
        sample = generate(params)
        world = sample.world
        if world is None or not asp_valid(world):
            print(f"Python reasonableness gate failed for {trouble}.")
            return 1
        if not sample.story.strip() or '"Hello,' not in sample.story:
            print(f"Generated story did not exercise dialogue for {trouble}.")
            return 1
        model = asp.one_model(asp_program(world))
        shown_names = {"brave", "safe_return", "welcomed", "complete", "reasonable"}
        asp_atoms = {
            (name, args)
            for name in shown_names
            for args in asp.atoms(model, name)
        }
        python_atoms = _python_atoms(world)
        if asp_atoms != python_atoms:
            print(f"MISMATCH for {trouble}.")
            print("ASP:", sorted(asp_atoms))
            print("PY :", sorted(python_atoms))
            return 1
        if not sample.story_qa or not sample.world_qa:
            print(f"Generated story is missing QA for {trouble}.")
            return 1

    print("OK: Python/ASP parity verified for three generated helium-bravery stories.")
    return 0


def _make_samples(args: argparse.Namespace, base_seed: int) -> list[StorySample]:
    samples: list[StorySample] = []
    if args.all:
        curated = [
            ("Ari", "Bea", "Ms. Rowan", PLACES[0], "branch"),
            ("Theo", "Finn", "Grandpa Eli", PLACES[1], "awning"),
            ("Mira", "Luz", "Aunt Nia", PLACES[2], "gate"),
        ]
        for index, (name, friend, helper, place, trouble) in enumerate(curated):
            params = StoryParams(
                name=args.name or name,
                friend=args.friend or friend,
                helper=args.helper or helper,
                place=args.place or place,
                trouble=trouble,
                seed=base_seed + index,
            )
            samples.append(generate(params))
        return samples

    for index in range(args.n):
        seed = base_seed + index
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        samples.append(generate(params))
    return samples


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.n < 1 and not (args.all or args.verify or args.show_asp or args.asp):
        parser.error("-n must be at least 1.")

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.show_asp or args.asp:
        try:
            params = resolve_params(args, random.Random(base_seed))
            params.seed = base_seed
            sample = generate(params)
            world = sample.world
            if world is None:
                raise StoryError("Could not build a world for ASP.")
            if args.show_asp:
                print(asp_program(world))
            else:
                import asp

                model = asp.one_model(asp_program(world))
                print("ASP model:")
                for atom in sorted(str(symbol) for symbol in model):
                    print(f"  {atom}")
        except StoryError as exc:
            parser.error(str(exc))
        return

    try:
        samples = _make_samples(args, base_seed)
    except StoryError as exc:
        parser.error(str(exc))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.name} at {sample.params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
