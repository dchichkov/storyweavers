#!/usr/bin/env python3
"""A child-facing tall tale about a tenement passage, a hutch, and sharing."""

from __future__ import annotations

# Locate the shared StoryWorld helpers from any batch depth.
from pathlib import Path as _StoryPath
import sys as _StorySys
_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents
                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())
_StorySys.path.insert(0, str(_storyworlds_root.parent))
_StorySys.path.insert(0, str(_storyworlds_root))


import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class Scene:
    place: str
    mood: str
    weather: str


@dataclass
class StoryParams:
    place: str
    helper: str
    animal: str
    treat: str
    name: str = "Luna"
    route: str = "doorway"
    seed: Optional[int] = None


@dataclass(frozen=True)
class TallTale:
    trouble: str
    joke: str
    discovery: str
    repair: str
    lesson: str
    ending: str


PLACES = {
    "tenement": Scene("the old tenement", "lively", "rain drummed on the tin roof"),
    "passage": Scene("the narrow passage", "echoing", "a warm wind raced through the doors"),
    "hutch": Scene("the sunny hutch", "homey", "golden dust floated in the light"),
}
HELPERS = {"Bram": "boy", "Nia": "girl", "Pip": "boy", "Rosa": "girl"}
ANIMALS = {"rabbit": "rabbit", "hen": "hen", "mouse": "mouse", "goat": "goat"}
TREATS = {
    "apple_cakes": "a tower of apple cakes",
    "jam_buns": "a basket of jam buns",
    "corn_muffins": "a mountain of corn muffins",
    "honey_toast": "a stack of honey toast",
}
ROUTES = ("doorway", "rooftop", "staircase", "laundry", "bell", "window")

TALES = {
    "apple_cakes": TallTale(
        "the apple cakes grew so tall that the hutch roof wore crumbs like snow",
        "the passage bell rang whenever the goat sneezed",
        "a loose laundry line had hoisted the cake tower through the open window",
        "lowered the cakes with a broom, then sliced them for every neighbor",
        "a tall problem becomes smaller when everyone gets a helping hand",
        "the whole tenement shared apple cakes while the goat wore a paper crown",
    ),
    "jam_buns": TallTale(
        "the jam buns rolled down the passage in a red and sticky parade",
        "the mouse claimed it had become the mayor of breakfast",
        "a broom cart had nudged the basket beneath the hutch door",
        "blocked the passage with cushions and gathered every bun into one clean basket",
        "a good laugh helps, but careful hands finish the job",
        "neighbors ate jam buns in a circle while the mouse guarded one tiny crumb",
    ),
    "corn_muffins": TallTale(
        "the corn muffins made the hutch wobble like a ship at sea",
        "the hen announced that it was captain of the breakfast fleet",
        "a rain-swollen board had tipped the muffin tray toward the passage",
        "propped the board, steadied the hutch, and passed muffins from door to door",
        "sharing the load can steady even a rocking home",
        "the hen strutted on a cushion while warm muffins crossed the tenement",
    ),
    "honey_toast": TallTale(
        "the honey toast stuck together and stretched from the hutch to the stairs",
        "the rabbit said it had discovered a golden bridge to Tuesday",
        "a warm kettle had softened the honey while a draft pulled the toast away",
        "closed the window, separated the slices, and shared them before they cooled",
        "a sticky surprise is easier with patience and a friend",
        "the passage smelled sweet as everyone crossed the toast bridge one bite at a time",
    ),
}


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tall tale about Luna in a tenement passage.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--treat", choices=sorted(TREATS))
    ap.add_argument("--name", default="Luna")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [
        (place, helper, animal, treat)
        for place in sorted(PLACES)
        for helper in sorted(HELPERS)
        for animal in sorted(ANIMALS)
        for treat in sorted(TREATS)
    ]


ASP_RULES = """
valid(Place,Helper,Animal,Treat) :-
    place(Place), helper(Helper), animal(Animal), treat(Treat).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        *(asp.fact("place", value) for value in PLACES),
        *(asp.fact("helper", value) for value in HELPERS),
        *(asp.fact("animal", value) for value in ANIMALS),
        *(asp.fact("treat", value) for value in TREATS),
    ])


def asp_program(show: str = "#show valid/4.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    return sorted(set(asp.atoms(asp.one_model(asp_program()), "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combinations).")
        return 0
    print("MISMATCH:", sorted(py - clingo), sorted(clingo - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    choices = [
        combo for combo in valid_combos()
        if not args.place or combo[0] == args.place
        if not args.helper or combo[1] == args.helper
        if not args.animal or combo[2] == args.animal
        if not args.treat or combo[3] == args.treat
    ]
    if not choices:
        raise StoryError("No reasonable tenement tale fits those options.")
    place, helper, animal, treat = rng.choice(choices)
    return StoryParams(
        place=place,
        helper=helper,
        animal=animal,
        treat=treat,
        name=args.name,
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(value) for value in (
        params.seed, params.place, params.helper, params.animal,
        params.treat, params.name, params.route,
    ))
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    tale = TALES[params.treat]
    rng = story_rng(params)
    world = World(scene)

    luna = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl",
        meters={"reach": 1.4, "kindness": 8},
        memes={"curiosity": 7, "courage": 6},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=HELPERS[params.helper],
        meters={"reach": 1.3, "kindness": 7},
        memes={"humor": 7, "trust": 6},
    ))
    animal = world.add(Entity(
        id=params.animal,
        kind="animal",
        type=ANIMALS[params.animal],
        meters={"wiggle": 5},
        memes={"hunger": 6, "pride": 5},
    ))

    opening = {
        "doorway": f"In {scene.place}, where {scene.weather}, {luna.id} opened the hutch door and discovered {tale.trouble}.",
        "rooftop": f"From the roof of {scene.place}, {luna.id} heard a breakfast rumble below. In the passage, {tale.trouble}.",
        "staircase": f"{luna.id} was halfway down the staircase of {scene.place} when {tale.trouble}.",
        "laundry": f"Sheets flapped over {scene.place}, and beneath them {luna.id} found {tale.trouble}.",
        "bell": f"The bell in {scene.place} gave three enormous rings. In the hutch, {luna.id} learned why: {tale.trouble}.",
        "window": f"Through the window of {scene.place}, {luna.id} saw crumbs marching toward the passage. Behind them came {tale.trouble}.",
    }
    world.say(opening[params.route])
    world.say(rng.choice([
        f"{params.helper} hurried over, carrying a wooden spoon as if it were a heroic sword.",
        f"{params.helper} arrived in slippers and declared the passage officially too exciting for breakfast.",
        f"{params.helper} peered into the hutch and took notes on an upside-down envelope.",
    ]))
    world.para()

    world.say(f'The {animal.label or params.animal} had climbed beside the food, and everyone began talking at once.')
    world.say(
        f'"I can fix this," said {luna.id}. "But I cannot reach the highest crumb alone." '
        f'"Then I will be your tall helper," said {params.helper}. "I have long arms and a very short fear of muffins."'
    )
    world.say(f"The joke made the {params.animal} twitch its whiskers, feathers, or ears, but the trouble still filled the passage.")
    animal.memes["worried"] = 1
    luna.memes["asking_for_help"] = 1
    world.para()

    world.say(f"{params.helper} held the hutch steady while {luna.id} checked the window, the floor, and the passage.")
    world.say(f"Together they discovered that {tale.discovery}.")
    world.say(
        f'"That means the food was not lost," said {luna.id}. "It only needs many careful hands." '
        f'"And perhaps one careful spoon," added {params.helper}.'
    )
    world.say(f"The {params.animal} squeaked, clucked, or bleated as if voting yes.")
    animal.memes["worried"] = 0
    luna.meters["problem_solving"] = 3
    helper.meters["helping"] = 3
    world.para()

    world.say(f"First, {luna.id} and {params.helper} {tale.repair}.")
    world.say(
        f"They invited every neighbor in the tenement to share the food, including the "
        f"{params.animal}, who received the smallest safe portion and the biggest welcome."
    )
    world.say(
        f'"No one gets the whole tower," {luna.id} explained. '
        f'"That is how towers become crumbs," said {params.helper}.'
    )
    luna.memes["generosity"] = 9
    helper.memes["generosity"] = 8
    animal.memes["included"] = 1
    world.para()

    world.say(f"{luna.id} remembered the lesson: {tale.lesson}.")
    world.say(rng.choice([
        f"By evening, {tale.ending}.",
        f"When the rain stopped, {tale.ending}.",
        f"At last, the passage grew quiet, and {tale.ending}.",
    ]))

    world.facts.update(
        luna=luna,
        helper=helper,
        animal=animal,
        scene=scene,
        tale=tale,
        treat=TREATS[params.treat],
        discovery=tale.discovery,
        repair=tale.repair,
        lesson=tale.lesson,
        ending=tale.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    return [
        f"Write a tall tale for children about {facts['luna'].id} in {facts['scene'].place}, where {facts['treat']} causes a comic problem.",
        f"Include dialogue between {facts['luna'].id} and {facts['helper'].id}, then reveal that {facts['discovery']}.",
        f"End with a sharing scene in which {facts['animal'].id} is included and {facts['ending']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What surprising trouble did {f['luna'].id} find in {f['scene'].place}?",
            answer=f"{f['luna'].id} found that {f['tale'].trouble}.",
        ),
        QAItem(
            question=f"How did {f['helper'].id}'s dialogue change what {f['luna'].id} did?",
            answer=f"{f['helper'].id} offered to help, so {f['luna'].id} stopped trying alone and worked with a friend to solve the problem.",
        ),
        QAItem(
            question=f"What caused the food trouble in the passage?",
            answer=f"The cause was that {f['discovery']}.",
        ),
        QAItem(
            question=f"How did the neighbors repair the hutch and the passage?",
            answer=f"They {f['repair']}, then shared the food safely with the neighbors and the {f['animal'].id}.",
        ),
        QAItem(
            question=f"What lesson did {f['luna'].id} learn?",
            answer=f"{f['luna'].id} learned that {f['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why can sharing help solve a large problem?",
            answer="Sharing gives people more hands, ideas, and care, so a difficult task can become manageable for everyone.",
        ),
        QAItem(
            question="Why is dialogue useful during a disagreement?",
            answer="Dialogue lets people explain what they know, listen to another idea, and choose a safer action together.",
        ),
        QAItem(
            question="What makes a tall tale different from an ordinary story?",
            answer="A tall tale uses playful exaggeration, surprising events, and humor while still showing a clear problem and a satisfying solution.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("\n== story qa ==")
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.append("\n== world qa ==")
    for item in sample.world_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.kind}/{entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  discovery={world.facts['discovery']}")
    lines.append(f"  repair={world.facts['repair']}")
    return "\n".join(lines)


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
        print("\n" + format_qa(sample))


CURATED = [
    StoryParams(
        place="tenement",
        helper="Bram",
        animal="goat",
        treat="apple_cakes",
        name="Luna",
        route="doorway",
        seed=101,
    ),
    StoryParams(
        place="passage",
        helper="Nia",
        animal="mouse",
        treat="jam_buns",
        name="Luna",
        route="laundry",
        seed=202,
    ),
    StoryParams(
        place="hutch",
        helper="Pip",
        animal="hen",
        treat="corn_muffins",
        name="Luna",
        route="bell",
        seed=303,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:\n")
        for place, helper, animal, treat in combos[:40]:
            print(f"  {place:10} {helper:6} {animal:7} {treat}")
        if len(combos) > 40:
            print(f"  ... and {len(combos) - 40} more")
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
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as error:
                print(error)
                return
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
            print(json.dumps(
                [sample.to_dict() for sample in samples],
                indent=2,
                ensure_ascii=False,
            ))
        return

    for index, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=(
                "### curated story"
                if args.all
                else f"### variant {index + 1}" if len(samples) > 1 else ""
            ),
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
