#!/usr/bin/env python3
"""
A tiny nursery-rhyme storyworld about an egg-dim, a foreshadowed bit of magic,
and the warmth of sharing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", "..", ".."))
for path in (ROOT, os.path.join(ROOT, "storyworlds")):
    if path not in sys.path:
        sys.path.insert(0, path)

from storyworlds.results import QAItem, StoryError, StorySample


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    weather: str
    rhyme: str
    magic_sign: str


@dataclass
class World:
    scene: Scene
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    weather: str
    child_name: str
    child_type: str
    friend_name: str
    friend_type: str
    egg_kind: str
    seed: Optional[int] = None


PLACES = {
    "moonlit_nursery": Scene(
        "the moonlit nursery",
        "soft rain",
        "Hush-a-bye, glow nearby",
        "three silver taps",
    ),
    "cottage_garden": Scene(
        "the cottage garden",
        "a skipping breeze",
        "Tip-tap, petals clap",
        "a blue butterfly",
    ),
    "hilltop_bedroom": Scene(
        "the hilltop bedroom",
        "bright starlight",
        "Up and down, stars crown",
        "a bell in the wall",
    ),
}

WEATHERS = {"soft rain", "a skipping breeze", "bright starlight"}
EGGS = {
    "little golden egg": "golden",
    "little blue egg": "blue",
    "little moon egg": "moon-white",
}
CHILD_NAMES = ["Luna", "Milo", "Pip", "Nell", "Tessa", "Bram"]
FRIEND_NAMES = ["Poppy", "Theo", "Mina", "Kit", "Rose", "Finn"]
FEMALE_NAMES = {"Luna", "Nell", "Tessa", "Poppy", "Mina", "Rose"}
ARCS = (
    {
        "id": "three_taps",
        "need": "felt lonely while the rain pattered on the panes",
        "hint": "Three silver taps sounded each time the spoon touched the egg-dim.",
        "problem": "When the last tap came, the nursery lamp went dim and the little egg-dim slipped beneath the cot.",
        "turn": "Luna remembered that the taps had pointed toward the shadow under the cot.",
        "action": "Luna and Poppy shared the small lantern, then reached together instead of pulling apart.",
        "reveal": "Under the cot, the egg-dim opened a tiny golden door, and a warm star floated out.",
        "result": "The magic did not belong to one child; it grew bright when both friends shared its light.",
        "ending": "They passed the glowing star from palm to palm until the nursery shone like a kindly moon.",
    },
    {
        "id": "butterfly_path",
        "need": "wished for a friend to cheer the quiet garden",
        "hint": "A blue butterfly landed beside the egg-dim and lifted one wing whenever sharing was mentioned.",
        "problem": "A gust rolled the egg-dim down the garden path and scattered its bright crumbs among the flowers.",
        "turn": "Luna noticed that every crumb rested beside a flower with two open petals.",
        "action": "Luna and Poppy gathered the crumbs into one basket, giving half of each find to the other.",
        "reveal": "The egg-dim hummed, and the shared crumbs became a little bridge of blue light.",
        "result": "Their fair handfuls made a path that led the lonely butterfly back to its garden tree.",
        "ending": "The butterfly slept above the blue bridge while two friends sang, 'Tip-tap, petals clap.'",
    },
    {
        "id": "bell_in_the_wall",
        "need": "was afraid that a new room would feel strange",
        "hint": "A faint bell rang whenever two hands rested beside the egg-dim.",
        "problem": "The egg-dim rolled into a crack in the wall, and its soft glow began to fade.",
        "turn": "Luna heard the bell answer when Poppy hummed the nursery rhyme.",
        "action": "They hummed together and shared their ribbon, feeding one end through the crack.",
        "reveal": "The ribbon pulled the egg-dim free, and the bell opened a hidden cupboard of friendly stars.",
        "result": "The strange room became a welcoming place because courage and comfort had been shared.",
        "ending": "They tucked one star by the bed, where it winked whenever the rhyme was sung.",
    },
)


def pronoun(kind: str, case: str) -> str:
    if kind == "girl":
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def _choose_arc(rng: random.Random) -> dict[str, str]:
    return rng.choice(ARCS)


def simulate(params: StoryParams) -> World:
    if params.place not in PLACES:
        raise StoryError(f"Unknown place: {params.place}")
    if params.weather not in WEATHERS:
        raise StoryError(f"Unknown weather: {params.weather}")
    if params.egg_kind not in EGGS:
        raise StoryError(f"Unknown egg kind: {params.egg_kind}")
    if params.child_name == params.friend_name:
        raise StoryError("The child and friend must have different names.")

    scene = PLACES[params.place]
    world = World(scene)
    child = world.add(
        Entity(
            params.child_name,
            "character",
            params.child_type,
            params.child_name,
            location=scene.place,
        )
    )
    friend = world.add(
        Entity(
            params.friend_name,
            "character",
            params.friend_type,
            params.friend_name,
            location=scene.place,
        )
    )
    egg = world.add(
        Entity(
            "egg_dim",
            "thing",
            "egg-dim",
            params.egg_kind,
            owner=None,
            location=scene.place,
        )
    )
    star = world.add(
        Entity(
            "shared_star",
            "thing",
            "magic",
            "a small shared star",
            location="inside the egg-dim",
        )
    )

    rng = random.Random(params.seed if params.seed is not None else 0)
    arc = _choose_arc(rng)
    world.facts.update(child=child, friend=friend, egg=egg, star=star, arc=arc)

    world.say(
        f"In {scene.place}, {child.id} {arc['need']}. "
        f"{scene.rhyme}, sang the old nursery rhyme."
    )
    world.say(
        f"Beside {child.id} rested a {egg.label}, called an egg-dim because it glimmered "
        "only when a kind thought was near."
    )
    world.say(arc["hint"])
    world.para()

    egg.meters["foreshadowed"] = 1.0
    child.memes["hope"] = 1.0
    friend.memes["care"] = 1.0
    world.say(
        f"{friend.id} came softly into {scene.place}. "
        f'"What shall we do?" {friend.id} asked. '
        f'"We can share the watching," said {child.id}, "and share the wondering too."'
    )
    world.say(arc["problem"])
    egg.meters["hidden"] = 1.0
    world.para()

    child.memes["curious"] = 1.0
    friend.memes["brave"] = 1.0
    world.say(arc["turn"])
    world.say(
        f'"I will hold the light," said {friend.id}. '
        f'"And I will look," answered {child.id}. '
        f'"Together," they said, and together they did.'
    )
    world.say(arc["action"])
    egg.meters["shared"] = 1.0
    egg.meters["found"] = 1.0
    world.para()

    world.say(arc["reveal"])
    egg.meters["opened"] = 1.0
    star.meters["glowing"] = 1.0
    star.memes["magic"] = 1.0
    child.memes["wonder"] = 1.0
    friend.memes["wonder"] = 1.0
    world.say(
        f'{child.id} whispered, "Is the magic ours?" '
        f'{friend.id} replied, "It is ours because we shared it."'
    )
    world.say(arc["result"])
    world.para()

    child.memes["joy"] = 1.0
    friend.memes["joy"] = 1.0
    star.meters["shared"] = 1.0
    world.say(arc["ending"])
    world.say(f"{scene.rhyme}, sang the friends, and the egg-dim glowed until bedtime.")
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    friend: Entity = world.facts["friend"]
    egg: Entity = world.facts["egg"]
    return [
        f"Write a Nursery Rhyme story about {child.id}, {friend.id}, and a magical {egg.label}.",
        f"Use foreshadowing to show how an egg-dim becomes brighter through sharing.",
        f"Tell a gentle magic tale in {world.scene.place} with dialogue and a concrete glowing ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    child: Entity = world.facts["child"]
    friend: Entity = world.facts["friend"]
    egg: Entity = world.facts["egg"]
    arc: dict[str, str] = world.facts["arc"]
    return [
        QAItem(
            f"What did the early sign foreshadow about the egg-dim?",
            f"The early sign foreshadowed that the egg-dim held magic that would appear when {child.id} and {friend.id} worked and shared together: {arc['hint']}",
        ),
        QAItem(
            f"What problem did {child.id} and {friend.id} face?",
            arc["problem"],
        ),
        QAItem(
            f"How did {child.id} and {friend.id} solve the problem?",
            arc["action"],
        ),
        QAItem(
            "Why did the magic become stronger?",
            f"The magic became stronger because {child.id} and {friend.id} shared the light, the work, and the wonder instead of keeping them for one person.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is foreshadowing?",
            "Foreshadowing is an early clue that quietly prepares us for something that happens later.",
        ),
        QAItem(
            "Why is sharing helpful?",
            "Sharing lets people combine their care and abilities, so a task or a happy moment can become easier and warmer.",
        ),
        QAItem(
            "What is magic in a nursery rhyme?",
            "Magic in a nursery rhyme is a playful impossible change that helps reveal kindness, courage, or wonder.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
reasonable(C,F,E) :- child(C), friend(F), egg_dim(E), different(C,F).
foreshadowed(E) :- egg_dim(E), clue(E).
can_open(E) :- egg_dim(E), foreshadowed(E), shared(E).
magic_shared(E) :- egg_dim(E), shared(E), opened(E).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp

    lines = []
    for place in PLACES:
        lines.append(asp.fact("place", place))
    lines.extend(
        [
            asp.fact("child", "luna"),
            asp.fact("friend", "poppy"),
            asp.fact("egg_dim", "egg_dim"),
            asp.fact("clue", "egg_dim"),
            asp.fact("shared", "egg_dim"),
            asp.fact("opened", "egg_dim"),
            asp.fact("different", "luna", "poppy"),
        ]
    )
    return "\n".join(lines)


def asp_program(show: str = "#show magic_shared/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp

        model = asp.one_model(asp_program())
        atoms = set(asp.atoms(model, "magic_shared"))
        if ("egg_dim",) not in atoms:
            print("ASP verification failed: magic sharing was not derived.")
            return 1
        sample = generate(
            StoryParams(
                "moonlit_nursery",
                "soft rain",
                "Luna",
                "girl",
                "Poppy",
                "girl",
                "little golden egg",
                17,
            )
        )
        if "egg-dim" not in sample.story or "shared" not in sample.story:
            print("Python verification failed: required story features are absent.")
            return 1
        print("OK: ASP/Python parity and generated story checks passed.")
        return 0
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Egg-dim nursery-rhyme storyworld.")
    parser.add_argument("--place", choices=list(PLACES))
    parser.add_argument("--weather", choices=sorted(WEATHERS))
    parser.add_argument("--child-name", choices=CHILD_NAMES)
    parser.add_argument("--friend-name", choices=FRIEND_NAMES)
    parser.add_argument("--egg-kind", choices=list(EGGS))
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    scene = PLACES[place]
    weather = args.weather or scene.weather
    child_name = args.child_name or rng.choice(CHILD_NAMES)
    choices = [name for name in FRIEND_NAMES if name != child_name]
    friend_name = args.friend_name or rng.choice(choices)
    if friend_name == child_name:
        raise StoryError("Child and friend must be different people.")
    egg_kind = args.egg_kind or rng.choice(list(EGGS))
    return StoryParams(
        place=place,
        weather=weather,
        child_name=child_name,
        child_type="girl" if child_name in FEMALE_NAMES else "boy",
        friend_name=friend_name,
        friend_type="girl" if friend_name in FEMALE_NAMES else "boy",
        egg_kind=egg_kind,
        seed=rng.randrange(2**31),
    )


def generate(params: StoryParams) -> StorySample:
    world = simulate(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("\n--- trace ---")
        for entity in sample.world.entities.values():
            print(
                f"{entity.id}: type={entity.type}, "
                f"meters={entity.meters}, memes={entity.memes}"
            )
    if qa:
        print("\n" + format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp

            print(json.dumps([str(atom) for atom in asp.one_model(asp_program())], indent=2))
        except ImportError as exc:
            raise StoryError(f"ASP mode requires clingo: {exc}") from exc
        return

    seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        params_list = [
            StoryParams("moonlit_nursery", "soft rain", "Luna", "girl", "Poppy", "girl", "little golden egg", 101),
            StoryParams("cottage_garden", "a skipping breeze", "Milo", "boy", "Rose", "girl", "little blue egg", 202),
            StoryParams("hilltop_bedroom", "bright starlight", "Nell", "girl", "Finn", "boy", "little moon egg", 303),
        ]
    else:
        params_list = [
            resolve_params(args, random.Random(seed + i))
            for i in range(max(0, args.n))
        ]
    samples = [generate(params) for params in params_list]

    if args.json:
        payload = samples[0].to_dict() if len(samples) == 1 else [sample.to_dict() for sample in samples]
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### story {index + 1}" if len(samples) > 1 else "",
        )
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
