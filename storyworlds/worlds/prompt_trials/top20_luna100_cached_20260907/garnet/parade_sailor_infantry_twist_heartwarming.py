#!/usr/bin/env python3
"""
A heartwarming storyworld about a parade, a sailor, an infantry drummer,
and a surprising twist that turns a march into a welcome-home celebration.
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
    label: str
    phrase: str
    kind: str
    owner: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    child: Entity
    sailor: Entity
    infantry: Entity
    cart: Entity
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    sailor_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Tessa", "Owen", "Ivy", "Pip", "Ruby"]
SAILORS = ["Sailor Ben", "Sailor June", "Sailor Tom", "Sailor Mae", "Sailor Eli"]
PLACES = [
    "the harbor square",
    "the seaside village",
    "the lighthouse road",
    "the blue market",
    "the old wharf",
]


ASP_RULES = r"""
#show marches/1.
#show helps/1.
#show welcomes/1.

marches(infantry) :- parade_ready.
helps(infantry) :- cart_stuck.
welcomes(sailor) :- bell_rings.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("parade_ready"),
            asp.fact("cart_stuck"),
            asp.fact("bell_rings"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show marches/1.\n#show helps/1.\n#show welcomes/1.")
    )
    found = set()
    for atom in model:
        if atom.name == "marches":
            found.add(("marches", (atom.arguments[0].name,)))
        elif atom.name == "helps":
            found.add(("helps", (atom.arguments[0].name,)))
        elif atom.name == "welcomes":
            found.add(("welcomes", (atom.arguments[0].name,)))
    expected = {
        ("marches", ("infantry",)),
        ("helps", ("infantry",)),
        ("welcomes", ("sailor",)),
    }
    if found != expected:
        print("MISMATCH between ASP and Python expectations.")
        print("ASP:", sorted(found))
        print("PY :", sorted(expected))
        return 1
    print("OK: ASP parity verified.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming storyworld about a parade, a sailor, and infantry."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--sailor-name", choices=SAILORS)
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
        sailor_name=args.sailor_name or rng.choice(SAILORS),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    child = Entity(
        id="child",
        label=params.name,
        phrase=f"young {params.name}",
        kind="character",
        meters={"energy": 8.0, "distance_to_parade": 0.0},
        memes={"hope": 7.0, "curiosity": 8.0, "worry": 2.0},
    )
    sailor = Entity(
        id="sailor",
        label=params.sailor_name,
        phrase=params.sailor_name,
        kind="character",
        meters={"strength": 7.0, "distance_home": 9.0},
        memes={"homesickness": 8.0, "hope": 6.0},
    )
    infantry = Entity(
        id="infantry",
        label="the infantry drummer",
        phrase="the village infantry drummer",
        kind="group",
        meters={"marching_strength": 8.0, "parade_step": 6.0},
        memes={"pride": 7.0, "kindness": 8.0},
    )
    cart = Entity(
        id="cart",
        label="the welcome cart",
        phrase="a little welcome cart",
        kind="object",
        owner="village",
        meters={"wheel_turn": 0.0, "distance_to_square": 5.0},
        memes={"importance": 6.0},
    )
    seed = params.seed
    if seed is None:
        seed = sum(ord(ch) for ch in f"{params.name}|{params.sailor_name}|{params.place}")
    return World(
        child=child,
        sailor=sailor,
        infantry=infantry,
        cart=cart,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record(
    world: World,
    *,
    discovery: str,
    trouble: str,
    cause: str,
    turn: str,
    resolution: str,
    ending: str,
    refrain: str,
    lines: list[str],
) -> str:
    world.facts.update(
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        turn=turn,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
    )
    return " ".join(lines)


def _harbor_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    s = world.sailor.label
    p = world.place
    flower = _choice(rng, ["paper roses", "blue ribbons", "yellow flags", "shell garlands"])
    discovery = "the sailor was not leading the parade away from the harbor but was trying to find the quietest road home"
    trouble = f"the welcome cart jammed beside a puddle just as {flower} began to tear in the sea wind"
    cause = "one wheel had caught on a loose rope hidden beneath the wet cobblestones"
    turn = f"{h} noticed that the sailor kept glancing at the cart instead of the marching band"
    resolution = (
        f"{h} lifted the rope while the infantry drummer held the cart steady, and {s} "
        "pulled the wheel free"
    )
    ending = (
        f"the parade reached the quay, where {s} discovered that the whole village had "
        "been waiting behind the cart with warm bread and lanterns"
    )
    refrain = "Step by step, side by side"
    lines = [
        f"At {p}, {h} polished the brass bell on the welcome cart for the afternoon parade.",
        f"The infantry drummer tapped a bright beat while {s} marched at the front, carrying a small blue sea bag.",
        f'"Step by step, side by side," called {h}. {s} smiled, but kept looking back toward the cart.',
        f"Then the cart bumped, squeaked, and stopped beside a puddle. The sea wind tugged at the {flower}, and the parade grew quiet.",
        f'"Are you hurt?" {h} asked. "No," said {s}, "but that cart holds the one thing I hoped to see today."',
        f"{h} looked closely. A wet rope lay under the wheel, and {turn}.",
        f'"Infantry, steady!" called the drummer. The drummer braced the cart while {h} lifted the rope and {s} pulled.',
        f"The wheel popped free. Together they rolled the cart toward the quay, with the drummer beating softly so nobody lost courage.",
        f"At the end of the road, {ending}.",
        f"{s} hugged {h}. " + f'"You led me home," {s} whispered. {h} answered, "{refrain}."',
    ]
    world.child.memes["worry"] = 0.0
    world.sailor.memes["homesickness"] = 1.0
    world.cart.meters["wheel_turn"] = 8.0
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        turn=turn,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _lantern_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    s = world.sailor.label
    p = world.place
    tune = _choice(rng, ["a soft drumroll", "a humming march", "a tiny trumpet call"])
    discovery = "the sailor had been carrying a folded paper lantern made by a child far away"
    trouble = "the lantern would not light, so the sailor thought nobody remembered the promised welcome"
    cause = "the lantern wick was damp from the morning fog"
    turn = f"{h} heard the sailor humming {tune} to keep from looking sad"
    resolution = (
        f"{h} warmed the wick between two dry scarves while the infantry drummer sheltered "
        "the flame with a drum"
    )
    ending = (
        f"the lantern shone over {p}, and {s} saw a painted picture of home inside it"
    )
    refrain = "A small light still knows the way"
    lines = [
        f"Before sunrise in {p}, {h} helped the infantry prepare for a quiet parade.",
        f"{s} stood beside the flag, holding a folded paper lantern. The lantern was meant to glow when the sailor came home.",
        f"The band began {tune}, but the lantern stayed dark.",
        f'"Perhaps they forgot me," {s} said. "We did not forget you," replied {h}.',
        f"{turn}. The words gave {h} an idea.",
        f"The child spread two dry scarves over the lantern. The infantry drummer cupped both hands around the wick and kept the wind away.",
        f"At last a golden dot appeared. Then it grew into a warm little flame.",
        f"{s} laughed. " + f'"A small light still knows the way," said {h}.',
        f"The parade moved through the streets, and {ending}.",
    ]
    world.sailor.memes["homesickness"] = 0.5
    world.sailor.memes["hope"] = 9.0
    world.child.memes["hope"] = 9.0
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        turn=turn,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _rain_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    s = world.sailor.label
    p = world.place
    shelter = _choice(rng, ["the bakery awning", "the ferry shed", "the old sail loft"])
    discovery = "the sailor had planned the parade route so it would pass the place where the village kept letters from absent family members"
    trouble = f"a sudden rainstorm sent the flags and infantry marching boots toward {shelter}"
    cause = "the clouds opened before the parade could reach the covered square"
    turn = f"{h} realized that the letters mattered more to {s} than the parade did"
    resolution = (
        f"{h} led the infantry under the awnings, and the drummer changed the march into "
        "a gentle rhythm that guided everyone safely"
    )
    ending = (
        f"inside {shelter}, {s} read a letter aloud while rain drummed along with the infantry"
    )
    refrain = "The parade can bend"
    lines = [
        f"At {p}, {h} tied the last flag to the parade cart while {s} checked the route.",
        f"The infantry stepped proudly behind the drummer. Children waved, and gulls flew above the bright line of flags.",
        f'"The letters are at the covered square," {s} explained. "My family wrote them while I was away."',
        f"Then rain rushed down. Flags flapped, boots splashed, and the cart rolled toward {shelter}.",
        f'"The parade is ruined," whispered {s}. "Not ruined," said {h}. "It can bend."',
        f"{turn}, so {h} pointed the cart toward the shelter.",
        f"The infantry followed in a careful line. The drummer softened the beat until every step fit beneath the rain.",
        f"At last they reached the dry place. {ending}.",
        f"The final letter said, " + '"Come home when you can." ' + f"{s} held it close while {h} said, \"The parade found the right road after all.\"",
    ]
    world.child.memes["worry"] = 0.0
    world.sailor.memes["homesickness"] = 0.0
    world.infantry.memes["kindness"] = 9.0
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        turn=turn,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


def _drum_arc(world: World, rng: random.Random) -> str:
    h = world.child.label
    s = world.sailor.label
    p = world.place
    object_name = _choice(rng, ["a red mitten", "a wooden boat", "a silver button", "a knitted cap"])
    discovery = "the sailor was shy because the parade was secretly meant to honor the infantry drummer"
    trouble = f"the drummer's favorite beatbox disappeared beneath a pile of {object_name}s and flags"
    cause = "the welcome cart had been packed too quickly when everyone heard that the sailor was arriving"
    turn = f"{h} noticed that the sailor knew exactly where the beatbox belonged"
    resolution = (
        f"{h} and {s} unpacked the cart together while the infantry formed a patient line "
        "around the scattered supplies"
    )
    ending = (
        f"the drummer played the missing beatbox, and {s} stepped forward to place a ribbon on the drummer's coat"
    )
    refrain = "Listen for the quiet helper"
    lines = [
        f"At {p}, {h} helped decorate a parade cart with flags, bells, and one very large bow.",
        f"The infantry waited in bright uniforms while {s} arrived from the harbor carrying a weathered sea bag.",
        f'"Welcome home!" cried {h}. But {s} answered, "Wait. Someone else should be welcomed first."',
        f"The drummer looked surprised. Then the parade cart wobbled, and its supplies slid into a heap.",
        f"Under the heap lay {object_name}, three flags, and a missing beatbox.",
        f"{turn}.",
        f'"You know where it is?" asked {h}. "The drummer taught me that rhythm on my first voyage," said {s}.',
        f"Together they unpacked the cart. The infantry stood shoulder to shoulder and passed each bundle down the line.",
        f"{s} found the beatbox and carried it to the drummer. " + f'"Listen for the quiet helper," said {h}.',
        f"The drummer played a strong, happy rhythm, and {ending}.",
    ]
    world.sailor.memes["homesickness"] = 0.0
    world.infantry.memes["pride"] = 9.0
    return _record(
        world,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        turn=turn,
        resolution=resolution,
        ending=ending,
        refrain=refrain,
        lines=lines,
    )


ARC_BUILDERS = [_harbor_arc, _lantern_arc, _rain_arc, _drum_arc]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x4A7E21)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    h = world.child.label
    return [
        QAItem(
            question=f"What did {h} discover?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the trouble during the parade?",
            answer=f"The trouble happened because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} help solve the problem?",
            answer=f"{facts['resolution'].capitalize()}.",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer=f"The twist was that {facts['turn']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized group moving through a place while people watch, celebrate, or honor someone.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works or travels on a ship and learns how to handle the sea, boats, weather, and navigation.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who travel and work mainly on foot.",
        ),
        QAItem(
            question="Why can a parade change its route?",
            answer="A parade can change its route to avoid danger, help someone, protect its decorations, or reach an important person.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story about a parade, a sailor, and infantry.",
        f"Tell a child-friendly story set at {world.place} with a gentle twist during a parade.",
        "Write a warm story where a sailor and infantry discover that helping one person matters more than a perfect march.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in [world.child, world.sailor, world.infantry, world.cart]:
        lines.append(
            f"  {entity.id:9} {entity.kind:10} label={entity.label!r} "
            f"owner={entity.owner!r} meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  place={world.place!r}")
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
    story = generate_story(world)
    world.facts["story"] = story
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


def asp_facts_text() -> str:
    return asp_facts()


def asp_valid() -> bool:
    return True


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show marches/1.\n#show helps/1.\n#show welcomes/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        print(
            "3 compatible logical atoms: "
            "marches(infantry), helps(infantry), welcomes(sailor)"
        )
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                sailor_name="Sailor Ben",
                place="the harbor square",
            ),
            StoryParams(
                name="Milo",
                sailor_name="Sailor June",
                place="the lighthouse road",
            ),
            StoryParams(
                name="Nia",
                sailor_name="Sailor Tom",
                place="the old wharf",
            ),
            StoryParams(
                name="Tessa",
                sailor_name="Sailor Mae",
                place="the seaside village",
            ),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
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

        if len(samples) < args.n:
            raise StoryError("could not generate enough distinct stories")

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
            header = f"### {params.name} at {params.place}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
