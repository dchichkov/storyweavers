#!/usr/bin/env python3
"""A quiet bedtime story about a nose, a secret sneeze, and sharing care.

The little world models a child, a soft toy, a bedtime room, and a growing
need for comfort. Foreshadowing appears as small clues before the turn:
a tickle, a rustle, and a tissue left nearby. Sharing then resolves the
worry when the child shares the tissue, the story, and a gentle goodnight.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path as _StoryPath
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
sys.path.insert(0, str(_storyworlds_root))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_meter(self, key: str, amount: float = 1.0) -> None:
        self.meters[key] = self.meter(key) + amount

    def add_meme(self, key: str, amount: float = 1.0) -> None:
        self.memes[key] = self.meme(key) + amount


@dataclass
class Event:
    kind: str
    actor: str
    target: str
    text: str
    cause: str = ""
    result: str = ""


@dataclass
class Room:
    label: str
    light: str
    sounds: str


@dataclass
class StoryParams:
    room: str
    child: str
    gender: str
    helper: str
    toy: str
    color: str
    mood: str
    problem: str = "tickle"
    solution: str = "share"
    seed: Optional[int] = None


class World:
    def __init__(self, room: Room) -> None:
        self.room = room
        self.entities: dict[str, Entity] = {}
        self.history: list[Event] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn = 0
        self.foreshadowing: list[str] = []
        self.shared = False
        self.resolved = False

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        return self.entities[entity_id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def record(
        self,
        kind: str,
        text: str,
        *,
        actor: str,
        target: str,
        cause: str = "",
        result: str = "",
    ) -> None:
        self.history.append(Event(kind, actor, target, text, cause, result))
        self.say(text)

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


ROOMS = {
    "window": Room("the little bedroom", "moonlight", "the soft hush of the house"),
    "attic": Room("the warm attic room", "a golden lamp", "the gentle creak of old boards"),
    "cabin": Room("the snug cabin bedroom", "a silver night-light", "the quiet whisper of trees"),
}

CHILDREN = {
    "Lina": ("girl", "thoughtful"),
    "Owen": ("boy", "gentle"),
    "Mara": ("girl", "dreamy"),
    "Theo": ("boy", "curious"),
    "Nell": ("girl", "cheerful"),
    "Sam": ("boy", "kind"),
}

HELPERS = {
    "mother": "Mom",
    "father": "Dad",
    "grandmother": "Grandma",
    "grandfather": "Grandpa",
}

TOYS = {
    "rabbit": "a floppy-eared rabbit",
    "bear": "a small brown bear",
    "fox": "a cloth fox with a bright tail",
    "owl": "a round-eyed owl",
}

COLORS = ["blue", "yellow", "green", "red", "silver"]
MOODS = ["sleepy", "thoughtful", "hopeful", "quietly brave"]

PROBLEMS = {
    "tickle": ("feels a tickle in the nose", "share"),
    "sneeze": ("has a sneeze that will not come out", "share"),
    "worry": ("worries that a stuffy nose will keep sleep away", "share"),
}

KNOWLEDGE = {
    "nose": [
        QAItem(
            "What does a nose help us do?",
            "A nose helps us breathe and notice smells, and it can also help us sneeze when something tickles inside.",
        )
    ],
    "sharing": [
        QAItem(
            "Why is sharing kind?",
            "Sharing lets someone else have help, comfort, or a turn, and it can make a small worry feel easier.",
        )
    ],
    "bedtime": [
        QAItem(
            "Why do people have bedtime routines?",
            "A bedtime routine gives the body calm, familiar steps that help it get ready for sleep.",
        )
    ],
    "foreshadowing": [
        QAItem(
            "What is a clue in a story?",
            "A clue is a small detail that hints at something that may happen later.",
        )
    ],
}


def valid_story(params: StoryParams) -> bool:
    return (
        params.room in ROOMS
        and params.child in CHILDREN
        and params.gender == CHILDREN[params.child][0]
        and params.helper in HELPERS
        and params.toy in TOYS
        and params.color in COLORS
        and params.mood in MOODS
        and params.problem in PROBLEMS
        and params.solution == "share"
    )


def build_world(params: StoryParams) -> World:
    if not valid_story(params):
        raise StoryError("The chosen bedtime details do not form a valid story.")

    room = ROOMS[params.room]
    world = World(room)
    child_type, child_trait = CHILDREN[params.child]

    child = world.add(
        Entity(
            id="child",
            kind="character",
            label=params.child,
            memes={"calm": 0.0, "worry": 0.0, "kindness": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="character",
            label=HELPERS[params.helper],
            memes={"care": 2.0},
        )
    )
    toy = world.add(
        Entity(
            id="toy",
            kind="toy",
            label=TOYS[params.toy],
            owner="child",
            memes={"comfort": 1.0},
        )
    )
    nose = world.add(
        Entity(
            id="nose",
            kind="body",
            label="nose",
            owner="child",
            meters={"tickle": 0.0, "air": 1.0},
        )
    )
    tissues = world.add(
        Entity(
            id="tissues",
            kind="object",
            label=f"a little box of {params.color} tissues",
            owner="helper",
            meters={"available": 1.0},
        )
    )

    world.facts.update(
        child=child,
        helper=helper,
        toy=toy,
        nose=nose,
        tissues=tissues,
        child_trait=child_trait,
        params=params,
    )
    return world


def foreshadow(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    toy: Entity = world.facts["toy"]  # type: ignore[assignment]
    tissues: Entity = world.facts["tissues"]  # type: ignore[assignment]
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]

    child.add_meme("worry", 1)
    world.foreshadowing.extend(["nose_tickle", "tissue_rustle", "toy_watch"])

    text = (
        f"Just as {params.child} tucked {toy.label} beneath the blanket, "
        f"{child.label.lower()}'s nose gave a tiny tickle. "
        f"Near the bed, {tissues.label} made one soft rustle in the quiet room. "
        f"{params.child} glanced at it, though there was no sneeze yet."
    )
    world.record(
        "foreshadow",
        text,
        actor="child",
        target="nose",
        cause="A small tickle and a nearby tissue hinted that bedtime might need one more gentle step.",
        result="The child noticed the clues and kept the tissue close.",
    )


def share_care(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    toy: Entity = world.facts["toy"]  # type: ignore[assignment]
    nose: Entity = world.facts["nose"]  # type: ignore[assignment]
    tissues: Entity = world.facts["tissues"]  # type: ignore[assignment]
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]

    if tissues.meter("available") < 1:
        raise StoryError("There is no tissue available to share.")
    nose.add_meter("tickle", 1)
    child.add_meme("worry", 1)
    tissues.add_meter("available", -1)
    world.shared = True

    cause = (
        f"When the tickle grew stronger, {params.child} shared the tissue "
        f"with the worried little nose instead of hiding beneath the blanket."
    )
    result = (
        f"{params.child} used it gently, then offered the clean corner to "
        f"{params.helper} so everyone could keep the bedside peaceful."
    )
    text = (
        f'"{params.helper}, my nose needs help," {params.child} whispered. '
        f"{cause} {result} {params.helper} smiled and thanked "
        f"{params.child.lower()} for sharing."
    )
    world.record(
        "share",
        text,
        actor="child",
        target="tissues",
        cause=cause,
        result=result,
    )

    child.add_meme("worry", -1)
    child.add_meme("kindness", 1)
    helper.add_meme("care", 1)
    nose.meters["tickle"] = 0
    toy.add_meme("comfort", 1)


def resolve(world: World) -> None:
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    helper: Entity = world.facts["helper"]  # type: ignore[assignment]
    toy: Entity = world.facts["toy"]  # type: ignore[assignment]
    nose: Entity = world.facts["nose"]  # type: ignore[assignment]
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]

    if not world.shared:
        raise StoryError("The bedtime worry needs a sharing action before it can resolve.")

    child.add_meme("calm", 2)
    nose.add_meter("air", 1)
    world.resolved = True
    world.para()

    cause = (
        f"After {params.child} shared the tissue and the worry, "
        f"the nose felt clear enough for slow, easy breaths."
    )
    result = (
        f"{params.child} settled beside {toy.label}, while {params.helper} "
        f"sat nearby and listened to the quiet breathing."
    )
    image = (
        f"The moonlight rested on the blanket like a pale feather, and "
        f"{toy.label} seemed to smile when {params.child} finally drifted to sleep."
    )
    world.record(
        "sleep",
        f"{cause} {result} {image}",
        actor="child",
        target="toy",
        cause=cause,
        result=result,
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child: Entity = world.facts["child"]  # type: ignore[assignment]
    toy: Entity = world.facts["toy"]  # type: ignore[assignment]

    world.record(
        "arrival",
        (
            f"In {world.room.label}, {params.child} climbed into bed with "
            f"{toy.label}. {world.room.light.capitalize()} touched the pillow, "
            f"and {world.room.sounds} curled around the room. "
            f"{params.child} felt {params.mood} and ready for a bedtime story."
        ),
        actor="child",
        target="toy",
        cause="The bedtime routine had begun.",
        result=f"{params.child} was tucked in with the toy close by.",
    )
    foreshadow(world)
    share_care(world)
    resolve(world)
    return world


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        (
            f"Write a gentle bedtime story about {params.child} and "
            f"{TOYS[params.toy]} whose nose begins to tickle. Include a small "
            f"clue before the turn, then show the child sharing care."
        ),
        (
            f"Tell a quiet story set in {ROOMS[params.room].label}. "
            f"{params.child} is getting sleepy, notices something about a nose, "
            f"and shares a tissue and a worry before falling asleep."
        ),
    ]


def story_qa(world: World) -> list[QAItem]:
    questions = {
        "arrival": "Where was the child, and who stayed close?",
        "foreshadow": "What clues hinted that the nose might need help?",
        "share": "How did the child share care?",
        "sleep": "Why was the child able to settle and sleep?",
    }
    out = []
    for event in world.history:
        if event.kind in questions:
            out.append(QAItem(questions[event.kind], f"{event.cause} {event.result}"))
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return KNOWLEDGE["nose"] + KNOWLEDGE["sharing"] + KNOWLEDGE["bedtime"] + KNOWLEDGE["foreshadowing"]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id}: {entity.label}; "
            f"meters={meters}; memes={memes}"
        )
    lines.append(f"  foreshadowing={world.foreshadowing}")
    lines.append(f"  shared={world.shared}; resolved={world.resolved}")
    lines.append("--- events ---")
    for event in world.history:
        lines.append(f"  {event.kind}: {event.text}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(nose) :- tickle(nose).
can_share(child, tissues) :- has_tissue(child, tissues).
resolved(child) :- can_share(child, tissues), gentle_use(nose).
sleeping(child) :- resolved(child), calm(child).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("tickle", "nose"),
            asp.fact("has_tissue", "child", "tissues"),
            asp.fact("gentle_use", "nose"),
            asp.fact("calm", "child"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show sleeping/1.\n"


def asp_verify() -> int:
    try:
        import asp

        model = asp.one_model(asp_program())
        sleeping = asp.atoms(model, "sleeping")
    except ImportError as exc:
        print(f"ASP verification unavailable: {exc}")
        return 1
    if sleeping != [("child",)]:
        print("MISMATCH: ASP did not derive sleeping(child).")
        return 1

    params = StoryParams(
        room="window",
        child="Lina",
        gender="girl",
        helper="mother",
        toy="rabbit",
        color="blue",
        mood="sleepy",
    )
    sample = generate(params)
    if not sample.world or not sample.world.resolved or not sample.world.shared:
        print("MISMATCH: generated story did not resolve through sharing.")
        return 1
    print("OK: ASP sharing gate and generated bedtime story agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a gentle bedtime story about a nose and sharing."
    )
    parser.add_argument("--room", choices=ROOMS)
    parser.add_argument("--child", choices=CHILDREN)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--toy", choices=TOYS)
    parser.add_argument("--color", choices=COLORS)
    parser.add_argument("--mood", choices=MOODS)
    parser.add_argument("--problem", choices=PROBLEMS)
    parser.add_argument("--solution", choices=["share"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    child = args.child or rng.choice(sorted(CHILDREN))
    gender = args.gender or CHILDREN[child][0]
    if gender != CHILDREN[child][0]:
        raise StoryError(f"{child} is not configured with gender {gender}.")

    problem = args.problem or rng.choice(sorted(PROBLEMS))
    solution = args.solution or "share"

    return StoryParams(
        room=args.room or rng.choice(sorted(ROOMS)),
        child=child,
        gender=gender,
        helper=args.helper or rng.choice(sorted(HELPERS)),
        toy=args.toy or rng.choice(sorted(TOYS)),
        color=args.color or rng.choice(COLORS),
        mood=args.mood or rng.choice(MOODS),
        problem=problem,
        solution=solution,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams("window", "Lina", "girl", "mother", "rabbit", "blue", "sleepy"),
    StoryParams("attic", "Owen", "boy", "grandmother", "bear", "yellow", "thoughtful"),
    StoryParams("cabin", "Mara", "girl", "father", "owl", "silver", "hopeful"),
    StoryParams("window", "Theo", "boy", "mother", "fox", "green", "quietly brave"),
]


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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if args.n < 1:
        raise SystemExit("-n must be at least 1")

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        print(asp_program())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for index in range(args.n):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
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
            header = f"### {sample.params.child}: bedtime nose story"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
