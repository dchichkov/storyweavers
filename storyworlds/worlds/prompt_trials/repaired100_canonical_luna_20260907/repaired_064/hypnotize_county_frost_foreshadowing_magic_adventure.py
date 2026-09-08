#!/usr/bin/env python3
"""A child-facing magical adventure about frost, a county spell, and brave choices."""

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
    charm: str
    name: str
    helper: str
    animal: str
    quest: str = ""
    route: str = ""
    seed: Optional[int] = None


@dataclass(frozen=True)
class Adventure:
    danger: str
    warning: str
    test: str
    setback: str
    foreshadow: str
    truth: str
    magic: str
    repair: str
    lesson: str
    ending: str


PLACES = {
    "county_gate": Scene("the county gate", "blue and quiet", "frost feathered the iron bars"),
    "hill_tower": Scene("the hill tower", "windy and bright", "frost glittered on the stone steps"),
    "pine_road": Scene("the pine road", "shadowy and silver", "frost crackled under every boot"),
}

CHARMS = {
    "bell": "a tiny silver bell",
    "lantern": "a blue lantern",
    "feather": "a warm golden feather",
    "key": "a moon-shaped key",
}

HELPERS = {"Mara": "girl", "Owen": "boy", "Tavi": "boy", "Nia": "girl"}
ANIMALS = {"fox": "fox", "owl": "owl", "hare": "hare", "badger": "badger"}

ADVENTURES = {
    "sleeping_county": Adventure(
        "a spell was making the county villagers walk toward the frozen clock",
        "the frost formed little arrows pointing to the clock tower",
        "followed the arrows only after checking a ribbon tied to a safe pine",
        "the first path ended at a glittering pond that reflected the wrong road",
        "three warm sparks appeared whenever the silver bell rang near the frost",
        "the county clock was not evil; a lonely winter spirit had hypnotized it to call for company",
        "the bell could wake sleeping wishes when its sound was shared by two brave friends",
        "rang the bell together and invited the spirit to warm the empty tower",
        "a warning can guide an adventurer without deciding everything for them",
        "the county clock chimed gently while frost melted into shining drops",
    ),
    "vanished_snow": Adventure(
        "all the county's snow had vanished, leaving frozen fields bare",
        "frosty footprints ended beneath a crooked sign marked with a star",
        "measured the footprints and compared them with the tracks of a real hare",
        "the first tracks were too deep for any small animal and led nowhere",
        "a pale snowflake glowed whenever the blue lantern was turned toward the hill",
        "a hidden cloud giant had gathered the snow while trying to build a soft bed",
        "the lantern could hypnotize a cloud only long enough to show its hidden path",
        "guided the cloud giant to return the snow in gentle flakes",
        "magic works best when curiosity is kinder than accusation",
        "snow covered the county again, and the giant's cloud became a harmless pillow",
    ),
    "frozen_song": Adventure(
        "the song that kept the county's winter bridge awake had stopped",
        "frost covered every music note except one bright mark",
        "hummed the marked note beside the bridge and listened for an answer",
        "the bridge groaned, but it did not wake; the note was only part of the tune",
        "the moon-shaped key warmed whenever someone sang the missing rhythm",
        "a river spirit had hidden the rhythm after hearing too many lonely songs",
        "the key opened a crystal music box beneath the ice",
        "played the full tune with the river spirit and woke the bridge",
        "a forgotten piece may be a doorway to cooperation",
        "the bridge hummed as travelers crossed safely over the silver river",
    ),
    "lost_star": Adventure(
        "the county's guiding star had fallen behind the frost hills",
        "a trail of blue sparks pointed away from the sky",
        "followed the sparks while tying golden feathers to the path",
        "a gust scattered the feathers, and the trail seemed to disappear",
        "one feather stayed warm beside a stone shaped like a sleeping eye",
        "the star had landed in a cave where a dreaming giant unknowingly guarded it",
        "a gentle song could hypnotize the giant's worry without controlling its body",
        "asked the giant to return the star and promised visits in daylight",
        "gentle courage can wake a friend better than force",
        "the guiding star rose above the county while the giant waved from the cave",
    ),
    "frost_garden": Adventure(
        "the county garden had frozen around one unopened golden flower",
        "frost made a circle around the flower like a small crown",
        "placed the warm charm nearby and waited instead of pulling the petals",
        "the flower stayed closed, and the cold grew thicker around their boots",
        "a tiny green pulse beat under the ice whenever the helper spoke kindly",
        "the flower was a doorway for a spring sprite trapped by a winter spell",
        "the moon key could melt one safe line through the frost",
        "opened the line and let the sprite choose when to bloom",
        "patience can be a magical form of bravery",
        "the golden flower opened as bees found the first warm morning",
    ),
}


ROUTES = ("warning_first", "map_first", "dialogue_first", "charm_first", "quiet_first", "race_clock")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A magical frost adventure in a county.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--charm", choices=sorted(CHARMS))
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    for flag in ("all", "trace", "qa", "json", "asp", "verify", "show-asp"):
        ap.add_argument(f"--{flag}", action="store_true")
    return ap


def valid_combos() -> list[tuple[str, str]]:
    return [(p, c) for p in sorted(PLACES) for c in sorted(CHARMS)]


ASP_RULES = """
valid(Place, Charm) :- place(Place), charm(Charm).
safe(Place, Charm) :- valid(Place, Charm).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        *(asp.fact("place", p) for p in PLACES),
        *(asp.fact("charm", c) for c in CHARMS),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    symbols = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(symbols, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:", sorted(py - cl), sorted(cl - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if not args.place or c[0] == args.place
        if not args.charm or c[1] == args.charm
    ]
    if not combos:
        raise StoryError("No valid county adventure fits those options.")
    place, charm = rng.choice(combos)
    name = args.name or "Luna"
    helpers = [x for x in sorted(HELPERS) if x != name] or sorted(HELPERS)
    return StoryParams(
        place=place,
        charm=charm,
        name=name,
        helper=args.helper or rng.choice(helpers),
        animal=args.animal or rng.choice(sorted(ANIMALS)),
        quest=rng.choice(sorted(ADVENTURES)),
        route=rng.choice(ROUTES),
    )


def story_rng(params: StoryParams) -> random.Random:
    text = "|".join(str(x) for x in (
        params.seed, params.place, params.charm, params.name, params.helper,
        params.animal, params.quest, params.route,
    ))
    return random.Random(int.from_bytes(hashlib.sha256(text.encode()).digest()[:8], "big"))


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


def tell(params: StoryParams) -> World:
    scene = PLACES[params.place]
    quest = ADVENTURES[params.quest]
    rng = story_rng(params)
    world = World(scene)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="child",
        meters={"courage": 1.0, "distance": 0.0},
        memes={"curiosity": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type=HELPERS[params.helper],
        meters={"courage": 0.8},
        memes={"trust": 0.8},
    ))
    animal = world.add(Entity(
        id=params.animal,
        kind="animal",
        type=ANIMALS[params.animal],
        meters={"distance": 2.0},
        memes={"alertness": 1.0},
    ))
    charm = CHARMS[params.charm]

    openings = {
        "warning_first": (
            f"At {scene.place}, {params.name} found {scene.weather}. "
            f"An old county sign whispered, \"Do not follow every shining path.\" "
            f"Then {params.name} learned that {quest.danger}."
        ),
        "map_first": (
            f"{params.name} drew {scene.place} on a map, marking the frost, the gate, "
            f"and {charm}. The map's corner curled toward a danger: {quest.danger}."
        ),
        "dialogue_first": (
            f"\"Something strange is happening in the county,\" said {params.helper} at {scene.place}. "
            f"{params.name} looked down at the frost and discovered that {quest.danger}."
        ),
        "charm_first": (
            f"{params.name} lifted {charm} at {scene.place}. Its light made the frost sparkle, "
            f"and beneath the sparkle was the first sign that {quest.danger}."
        ),
        "quiet_first": (
            f"The county was unusually quiet at {scene.place}. {params.animal.capitalize()} "
            f"watched from a wall while {params.name} discovered that {quest.danger}."
        ),
        "race_clock": (
            f"Before the county clock struck noon, {params.name} and {params.helper} hurried to "
            f"{scene.place}. They had to act because {quest.danger}."
        ),
    }
    world.say(openings[params.route])
    world.say(rng.choice([
        f"{params.helper} carried a coil of red ribbon, while {params.name} carried {charm}.",
        f"The {params.animal} trotted beside them, stopping whenever the frost made a new shape.",
        f"{params.name} and {params.helper} agreed to stay together, even if the magic grew loud.",
    ]))
    world.para()

    world.say(f"The first warning was clear: {quest.warning}.")
    world.say(rng.choice([
        f"\"Should we turn back?\" asked {params.helper}. \"We can turn back from danger, but not from a puzzle,\" said {params.name}.",
        f"\"Magic can fool our eyes,\" said {params.name}. {params.helper} nodded. \"Then we will check what it changes.\"",
        f"{params.helper} pointed to the frost. \"It looks like a command.\" \"It may be a clue,\" replied {params.name}.",
    ]))
    world.say(f"Together they {quest.test}, but {quest.setback}.")
    hero.meters["distance"] = 1.0
    helper.meters["courage"] = 1.1
    hero.memes["doubt"] = 0.6
    world.say("The setback made the adventure harder, but it also showed them which bright idea was unsafe.")
    world.para()

    world.say(f"Then the foreshadowed sign returned: {quest.foreshadow}.")
    world.say(rng.choice([
        f"The {params.animal} tugged at the ribbon and revealed a second mark beneath the frost.",
        f"{charm.capitalize()} warmed in {params.name}'s hand, not to command the magic, but to reveal its shape.",
        f"{params.helper} remembered the old warning and looked where the shining path ended instead of where it began.",
    ]))
    world.say(f"They discovered the truth: {quest.truth}.")
    world.say(f"The magic was not a weapon. {quest.magic}.")
    hero.memes["understanding"] = 1.0
    animal.memes["trust"] = 1.0
    world.para()

    world.say(rng.choice([
        f"\"We will help, but no one gets controlled,\" said {params.name}. {params.helper} answered, \"A fair spell needs a choice.\"",
        f"\"Can the magic listen?\" asked {params.helper}. \"It can listen if we speak honestly,\" said {params.name}.",
        f"{params.name} held out {charm}. \"Come with us by your own choice.\" The hidden presence answered with a warm gust.",
    ]))
    world.say(f"Side by side, they {quest.repair}.")
    hero.meters["courage"] = 1.5
    hero.memes["kindness"] = 1.0
    world.say(f"{params.name} remembered the lesson: {quest.lesson}.")
    world.say(rng.choice([
        f"At sunset, {quest.ending}.",
        f"When the frost began to soften, {quest.ending.capitalize()}.",
        f"The adventure ended with a small promise kept: {quest.ending}.",
    ]))
    world.facts.update(
        hero=hero,
        helper=helper,
        animal=animal,
        charm=charm,
        scene=scene,
        quest=quest,
        truth=quest.truth,
        repair=quest.repair,
        lesson=quest.lesson,
        ending=quest.ending,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q = f["quest"]
    return [
        f"Write a short magical adventure for a child about {f['hero'].id}, {f['charm']}, and a frost-covered county.",
        f"Tell an adventure in which {f['hero'].id} and {f['helper'].id} use foreshadowing and careful choices to solve this problem: {q.danger}.",
        f"Write a gentle magic story revealing that {q.truth}, ending with {q.ending}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    q = f["quest"]
    return [
        QAItem(
            question=f"What danger did {f['hero'].id} discover in the county?",
            answer=f"{f['hero'].id} discovered that {q.danger}.",
        ),
        QAItem(
            question=f"What warning helped {f['hero'].id} and {f['helper'].id} make a safer choice?",
            answer=f"The warning was that {q.warning}. It reminded them not to trust a shining path without checking it.",
        ),
        QAItem(
            question=f"What setback changed the adventure's direction?",
            answer=f"They {q.test}, but {q.setback}. The failed attempt showed them which path or idea was unsafe.",
        ),
        QAItem(
            question=f"What foreshadowed clue revealed the truth about the county magic?",
            answer=f"The clue was that {q.foreshadow}. It helped them discover that {q.truth}.",
        ),
        QAItem(
            question=f"How did {f['hero'].id} and {f['helper'].id} resolve the magical danger?",
            answer=f"They {q.repair}. They learned that {q.lesson}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is frost?",
            answer="Frost is a thin layer of ice crystals that forms when water vapor freezes on a cold surface.",
        ),
        QAItem(
            question="Why should a person be careful with magic that can hypnotize?",
            answer="A spell that can hypnotize may affect a person's choices. A fair adventurer protects consent and uses magic to reveal or help, not to control.",
        ),
        QAItem(
            question="How does foreshadowing help an adventure?",
            answer="Foreshadowing plants an early warning, image, or detail that becomes meaningful later. It makes the later discovery feel prepared rather than random.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = [
        "== prompts ==",
        *(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)),
        "",
        "== story qa ==",
    ]
    for item in sample.story_qa:
        lines.extend((f"Q: {item.question}", f"A: {item.answer}"))
    lines.extend(("", "== world qa =="))
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
    lines.append(f"  truth={world.facts['truth']}")
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
        place="county_gate",
        charm="bell",
        name="Luna",
        helper="Mara",
        animal="fox",
        quest="sleeping_county",
        route="warning_first",
        seed=11,
    ),
    StoryParams(
        place="hill_tower",
        charm="lantern",
        name="Luna",
        helper="Owen",
        animal="owl",
        quest="vanished_snow",
        route="charm_first",
        seed=22,
    ),
    StoryParams(
        place="pine_road",
        charm="key",
        name="Luna",
        helper="Nia",
        animal="hare",
        quest="frozen_song",
        route="dialogue_first",
        seed=33,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, charm in combos:
            print(f"  {place:14} {charm}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
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

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=(
                "### curated story"
                if args.all
                else (f"### variant {i + 1}" if len(samples) > 1 else "")
            ),
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
