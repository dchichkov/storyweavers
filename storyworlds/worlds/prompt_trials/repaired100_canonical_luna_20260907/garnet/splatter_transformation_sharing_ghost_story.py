#!/usr/bin/env python3
"""
A gentle ghost story about splatter, transformation, and sharing.
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str = "thing"
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    hero: Item
    ghost: Item
    lantern: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    ghost_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Toby", "Ivy", "Pip", "Ruby", "Otis"]
GHOSTS = ["Boo", "Murmur", "Wisp", "Whisker", "Moonbell", "Puff"]
PLACES = [
    "the old garden",
    "the moonlit schoolhouse",
    "the quiet mill",
    "the lantern orchard",
    "the little hill cemetery",
]

ASP_RULES = r"""
#show splattered/1.
#show transformed/1.
#show shared/1.

splattered(hero) :- ghost_spills_paint.
transformed(hero) :- paint_becomes_stars.
shared(hero) :- lantern_shared.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("ghost_spills_paint"),
            asp.fact("paint_becomes_stars"),
            asp.fact("lantern_shared"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_atom_tuple(atom):
    values = []
    for arg in atom.arguments:
        if arg.type.name == "Number":
            values.append(arg.number)
        elif arg.type.name == "String":
            values.append(arg.string)
        else:
            values.append(arg.name)
    return atom.name, tuple(values)


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program(
            "#show splattered/1.\n"
            "#show transformed/1.\n"
            "#show shared/1."
        )
    )
    actual = {_asp_atom_tuple(atom) for atom in model}
    expected = {
        ("splattered", ("hero",)),
        ("transformed", ("hero",)),
        ("shared", ("hero",)),
    }
    if actual == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about splatter, transformation, and sharing."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--ghost-name", choices=GHOSTS)
    parser.add_argument("--place", choices=PLACES)
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
    return StoryParams(
        name=args.name or rng.choice(NAMES),
        ghost_name=args.ghost_name or rng.choice(GHOSTS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    if params.name == params.ghost_name:
        raise StoryError("The living child and the ghost must have different names.")
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        meters={"height": 1.25, "distance_to_lantern": 2.0},
        memes={"curiosity": 0.8, "worry": 0.2, "kindness": 0.7},
    )
    ghost = Item(
        id="ghost",
        label=params.ghost_name,
        phrase=f"the ghost called {params.ghost_name}",
        kind="ghost",
        meters={"height": 1.1, "float_height": 0.4},
        memes={"loneliness": 0.9, "shyness": 0.8, "hope": 0.3},
    )
    lantern = Item(
        id="lantern",
        label="lantern",
        phrase="an old glass lantern",
        owner="ghost",
        meters={"brightness": 0.5, "distance_to_gate": 3.0},
        memes={"warmth": 0.6, "welcome": 0.2},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.ghost_name}|{params.place}")
    return World(
        hero=hero,
        ghost=ghost,
        lantern=lantern,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    cause: str,
    transformation: str,
    resolution: str,
    ending: str,
    splatter: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        cause=cause,
        transformation=transformation,
        resolution=resolution,
        ending=ending,
        splatter=splatter,
        transformed=True,
        shared=True,
        story=" ".join(lines),
    )
    world.hero.memes["worry"] = 0.05
    world.hero.memes["kindness"] = 1.0
    world.ghost.memes["loneliness"] = 0.05
    world.ghost.memes["hope"] = 1.0
    world.lantern.meters["brightness"] = 1.0
    world.lantern.memes["welcome"] = 1.0
    return world.facts["story"]


def _paint_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.ghost.label
    p = world.place
    color = _choice(rng, ["blue", "violet", "silver", "green"])
    shape = _choice(rng, ["stars", "little moons", "feathery clouds", "bright fish"])
    splatter = f"{color} paint splattered across {h}'s coat and the dusty floor"
    discovery = f"{g} could not hold the old paint tin without making {splatter}"
    cause = "the ghost's transparent fingers slipped through the tin, and its lonely fright made the paint jump"
    transformation = f"when {h} shared a steady hand and a kind laugh, the splatter transformed into {shape}"
    resolution = (
        f"{h} invited {g} to paint together, holding the tin while {g} guided the brush "
        f"through the new {shape}"
    )
    ending = f"the coat became a bright picture, and the {shape} glimmered whenever {h} and {g} shared the lantern"
    lines = [
        f"At {p}, {h} found a cold lantern beside a locked door and heard a soft sniffle behind it.",
        f"The sniffle belonged to {g}, a shy ghost clutching an old tin of {color} paint.",
        f'"Please do not come closer," whispered {g}. "I always make a mess."',
        f'"Then we can make the mess together," said {h}. "You do not have to be alone."',
        f"Before {g} could answer, the tin slipped through its fingers. SPLAT! {splatter}.",
        f"{h} jumped, but did not run. The child noticed that every frightened splatter made {g} fade a little paler.",
        f'"Take my hand," said {h}. "We will try slowly."',
        f"{g} placed one chilly hand over {h}'s warm one. The paint stopped jumping, and {splatter} slowly transformed into {shape}.",
        f"The ghost stared. Then {g} laughed, and the laugh sounded like wind chimes in a jar.",
        f"{h} invited {g} to paint together. They shared the lantern, the brush, and the last clean patch of wall.",
        f"By midnight, {ending}. The old place no longer felt empty; it had room for two gentle friends.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        transformation=transformation,
        resolution=resolution,
        ending=ending,
        splatter=splatter,
        lines=lines,
    )


def _berry_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.ghost.label
    p = world.place
    fruit = _choice(rng, ["moonberries", "red currants", "black plums", "glowing cherries"])
    pattern = _choice(rng, ["a smiling face", "a silver crown", "a flock of birds", "a friendly doorway"])
    splatter = f"{fruit} splattered the white tablecloth like tiny red raindrops"
    discovery = f"{g} had gathered {fruit}, but every ghostly touch made {splatter}"
    cause = "the berries were too full and the ghost's fingers passed through their skins"
    transformation = f"sharing a bowl and a song transformed the splatter into {pattern}"
    resolution = (
        f"{h} showed {g} how to roll the berries down a wooden board into a bowl, "
        f"and then they offered half to the sleeping neighbors"
    )
    ending = f"the tablecloth held {pattern}, while a full bowl of {fruit} waited for anyone who felt hungry"
    lines = [
        f"One moonlit evening at {p}, {h} heard dishes clinking in the empty kitchen.",
        f"{g} floated above a table covered with {fruit}. The ghost looked embarrassed.",
        f'"I wanted to leave a feast," said {g}, "but I cannot hold anything."',
        f'"Maybe holding is not the only way to share," said {h}.',
        f"{g} reached for a berry. SPLAT! {splatter}.",
        f"The child placed a bowl beneath a wooden board and showed the ghost how to roll each berry gently.",
        f'"You push from that side," said {h}. "I will guide from this side."',
        f"As they worked together, the messy marks joined into {pattern}. The transformation made the ghost shine instead of fade.",
        f"{g} carried the bowl toward the sleeping neighbors, while {h} carried the tablecloth.",
        f"At dawn, {ending}. Even the quiet kitchen seemed to say thank you.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        transformation=transformation,
        resolution=resolution,
        ending=ending,
        splatter=splatter,
        lines=lines,
    )


def _chalk_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.ghost.label
    p = world.place
    message = _choice(rng, ["WELCOME", "PLAY WITH US", "YOU ARE SAFE", "COME BACK TOMORROW"])
    splatter = "white chalk splattered across the floor in a cloud of ghostly dust"
    discovery = f"{g} was trying to write {message}, but could not keep the chalk solid"
    cause = "the ghost's fading hand squeezed too hard whenever it felt unseen"
    transformation = "the dusty splatter transformed into a clear trail of glowing letters"
    resolution = (
        f"{h} shared the chalk by drawing one letter at a time and asking {g} "
        f"which word should come next"
    )
    ending = f"the final letters of {message} shone beside the doorway, inviting every lonely visitor inside"
    lines = [
        f"At {p}, {h} noticed white footprints leading from the gate to an empty classroom.",
        f"In the room, {g} floated beside a box of chalk and tried to write a message.",
        f'"I want people to know this place is friendly," said {g}.',
        f'"Then let us make the letters together," said {h}.',
        f"{g} squeezed the chalk. CRACK! {splatter}.",
        f"{h} brushed the dust into a small circle and offered half of the chalk to the ghost.",
        f'"You choose the first letter," said {h}. "I will choose the next."',
        f"They took turns. The ghost's hand grew steadier, and the dusty splatter transformed into a clear trail of glowing letters.",
        f"When the last letter was finished, the classroom filled with a soft golden hum.",
        f"By morning, {ending}. {g} no longer hid behind the blackboard.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        transformation=transformation,
        resolution=resolution,
        ending=ending,
        splatter=splatter,
        lines=lines,
    )


def _soap_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    g = world.ghost.label
    p = world.place
    bubbles = _choice(rng, ["blue bubbles", "pearly bubbles", "gold bubbles", "green bubbles"])
    splatter = "soapy water splattered over the stones and made the path slippery"
    discovery = f"{g} had been trying to wash the old lantern, but made {splatter}"
    cause = "the ghost could not feel the cloth, so each cleaning stroke became a wild splash"
    transformation = f"the splatter transformed into {bubbles} when the lantern's flame warmed the water"
    resolution = (
        f"{h} shared a soft cloth with {g}, guiding the ghost's hand in small circles "
        f"around the lantern glass"
    )
    ending = f"the clean lantern shone through {bubbles}, and its warm light showed both friends the way home"
    lines = [
        f"Near midnight at {p}, {h} saw an old lantern wobbling beside a puddle.",
        f"{g} hovered over it, rubbing the glass with a cloth that kept passing through the handle.",
        f'"I want the lantern to shine," said {g}, "but everything slips away from me."',
        f'"You can borrow my hands," said {h}. "We can clean it together."',
        f"{g} tried alone once more. SPLASH! {splatter}.",
        f"The stones shone, the ghost gasped, and the lantern went dark.",
        f"{h} shared the cloth and showed {g} how to move slowly from one edge of the glass to the other.",
        f"As they worked, the water caught the returning flame. {splatter} transformed into {bubbles}.",
        f"The bubbles floated around {g}, who became solid enough to hold the lantern for one whole breath.",
        f"At the end of the path, {ending}. The ghost's smile stayed bright after the flame was covered.",
    ]
    return _record(
        world,
        discovery=discovery,
        cause=cause,
        transformation=transformation,
        resolution=resolution,
        ending=ending,
        splatter=splatter,
        lines=lines,
    )


ARC_BUILDERS = [_paint_arc, _berry_arc, _chalk_arc, _soap_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A77E)
    return ARC_BUILDERS[world.seed % len(ARC_BUILDERS)](world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    g = world.ghost.label
    f = world.facts
    return [
        QAItem(
            question=f"What did {h} discover about {g}?",
            answer=f"{h} discovered that {f['discovery']}.",
        ),
        QAItem(
            question="What caused the splatter?",
            answer=f"The splatter happened because {f['cause']}.",
        ),
        QAItem(
            question="How did the splatter transform?",
            answer=f"The splatter transformed because {f['transformation']}.",
        ),
        QAItem(
            question=f"How did {h} and {g} share the solution?",
            answer=f"They shared the solution when {f['resolution']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost in a story?",
            answer="A ghost is a spirit or imaginary figure from a story. Ghost stories can be spooky, mysterious, or gentle.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means that something changes into a different form, shape, condition, or appearance.",
        ),
        QAItem(
            question="Why can sharing help solve a problem?",
            answer="Sharing lets people combine their ideas, tools, time, or care, so a difficult task can become easier together.",
        ),
        QAItem(
            question="What is splatter?",
            answer="Splatter is a scattering of drops or small pieces caused when liquid or another messy material hits a surface.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle ghost story for young children about splatter, transformation, and sharing.",
        f"Tell a child-facing ghost story set at {world.place}, where {world.hero.label} helps {world.ghost.label} transform a messy accident.",
        "Create a warm story in which a frightening-looking splatter becomes something beautiful through cooperation.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.hero, world.ghost, world.lantern]:
        lines.append(
            f"  {entity.id:7} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    output = ["== Generation prompts =="]
    for index, prompt in enumerate(sample.prompts, 1):
        output.append(f"{index}. {prompt}")
    output.append("")
    output.append("== Story QA ==")
    for item in sample.story_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    output.append("")
    output.append("== World QA ==")
    for item in sample.world_qa:
        output.append(f"Q: {item.question}")
        output.append(f"A: {item.answer}")
    return "\n".join(output)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    story = generate_story(world)
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


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show splattered/1.\n"
                "#show transformed/1.\n"
                "#show shared/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: "
            "splattered(hero), transformed(hero), shared(hero)"
        )
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                ghost_name="Boo",
                place="the old garden",
                seed=base_seed,
            ),
            StoryParams(
                name="Milo",
                ghost_name="Wisp",
                place="the moonlit schoolhouse",
                seed=base_seed + 1,
            ),
            StoryParams(
                name="Nia",
                ghost_name="Murmur",
                place="the quiet mill",
                seed=base_seed + 2,
            ),
            StoryParams(
                name="Ruby",
                ghost_name="Moonbell",
                place="the lantern orchard",
                seed=base_seed + 3,
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

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
            params = sample.params
            header = f"### {params.name} and {params.ghost_name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
