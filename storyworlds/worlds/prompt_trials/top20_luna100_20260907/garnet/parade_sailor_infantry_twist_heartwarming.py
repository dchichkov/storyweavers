#!/usr/bin/env python3
"""
A heartwarming storyworld about a parade, a sailor, and an infantry drummer
who discover that a quiet act of courage can lead the whole town.
"""

from __future__ import annotations

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
    sailor: Item
    infantry: Item
    parade: Item
    place: str
    seed: int
    facts: dict = field(default_factory=dict)

    def render(self) -> str:
        return self.facts.get("story", "")


@dataclass
class StoryParams:
    name: str
    sailor_name: str
    infantry_name: str
    place: str
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Nia", "Tessa", "Owen", "Pia", "Sam", "Ravi"]
SAILORS = ["Sailor June", "Sailor Theo", "Sailor Mae", "Sailor Ben", "Sailor Rosa"]
INFANTRY = ["Corporal Reed", "Private Ellis", "Sergeant Vale", "Corporal Mina", "Private Jo"]
PLACES = [
    "the harbor square",
    "the seaside town",
    "the bright waterfront",
    "the old lighthouse road",
    "the market by the pier",
]


ASP_RULES = r"""
#show ready/1.
#show brave/1.
#show together/1.

ready(H) :- hears_signal(H).
brave(H) :- helps_parade(H).
together(H) :- shares_place(H).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hears_signal", "hero"),
            asp.fact("helps_parade", "hero"),
            asp.fact("shares_place", "hero"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(
        asp_program("#show ready/1.\n#show brave/1.\n#show together/1.")
    )
    atoms = set()
    for atom in model:
        if atom.name not in {"ready", "brave", "together"}:
            continue
        args = tuple(
            a.number if a.type == a.type.Number else a.string if a.type == a.type.String else a.name
            for a in atom.arguments
        )
        atoms.add((atom.name, args))
    expected = {
        ("ready", ("hero",)),
        ("brave", ("hero",)),
        ("together", ("hero",)),
    }
    if atoms == expected:
        print("OK: ASP parity verified.")
        return 0
    print("MISMATCH between ASP and Python expectations.")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming storyworld about a parade, a sailor, and infantry."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--sailor-name", choices=SAILORS)
    parser.add_argument("--infantry-name", choices=INFANTRY)
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
        infantry_name=args.infantry_name or rng.choice(INFANTRY),
        place=args.place or rng.choice(PLACES),
    )


def build_world(params: StoryParams) -> World:
    hero = Item(
        id="hero",
        label=params.name,
        phrase=f"young {params.name}",
        kind="child",
        meters={"energy": 0.8, "distance": 0.0},
        memes={"hope": 0.7, "courage": 0.5},
    )
    sailor = Item(
        id="sailor",
        label=params.sailor_name,
        phrase=params.sailor_name,
        kind="sailor",
        meters={"distance": 0.0, "balance": 0.8},
        memes={"kindness": 0.8, "homesickness": 0.3},
    )
    infantry = Item(
        id="infantry",
        label=params.infantry_name,
        phrase=params.infantry_name,
        kind="infantry",
        meters={"rhythm": 0.8, "distance": 0.0},
        memes={"duty": 0.8, "tenderness": 0.4},
    )
    parade = Item(
        id="parade",
        label="parade",
        phrase="the town parade",
        kind="event",
        meters={"length": 0.0, "crowd": 0.4},
        memes={"joy": 0.8, "belonging": 0.5},
    )
    seed = params.seed
    if seed is None:
        seed = sum(
            ord(ch)
            for ch in f"{params.name}|{params.sailor_name}|{params.infantry_name}|{params.place}"
        )
    return World(
        hero=hero,
        sailor=sailor,
        infantry=infantry,
        parade=parade,
        place=params.place,
        seed=seed,
    )


def _choice(rng: random.Random, values: list[str]) -> str:
    return values[rng.randrange(len(values))]


def _record_story(
    world: World,
    *,
    arc: str,
    discovery: str,
    trouble: str,
    cause: str,
    resolution: str,
    ending: str,
    lesson: str,
    lines: list[str],
) -> str:
    world.facts.update(
        arc=arc,
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        shared=True,
    )
    world.hero.memes["courage"] = 0.95
    world.parade.meters["length"] = float(len(lines))
    world.parade.memes["belonging"] = 0.95
    return " ".join(lines)


def _missing_flag_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    s = world.sailor.label
    i = world.infantry.label
    p = world.place
    flag = _choice(rng, ["a blue harbor flag", "a little red pennant", "a white signal cloth"])
    discovery = f"the parade's missing flag had been tucked beneath {s}'s folded coat"
    trouble = "the parade could not begin because its flag bearer had not arrived"
    cause = f"{s} had found the flag in the wind and was holding it safe while searching for its owner"
    resolution = f"{h} asked the crowd whose flag it was, and {i} recognized it as the welcome flag for sailors returning home"
    ending = f"{h} carried {flag} at the front while {s} and {i} marched beside the child"
    lesson = "someone who seems late may be quietly protecting something important"
    lines = [
        f"On parade morning at {p}, {h} polished the brass bell for the town parade.",
        f"The band was ready, the infantry line stood straight, and {s} waited near the pier, but the parade flag was nowhere to be seen.",
        f'"Without the flag, how will the sailors know we welcome them?" asked {h}.',
        f'"We can wait one more minute," said {i}. "A parade should make room for people who are finding their way."',
        f"Just then, {h} noticed a corner of cloth beneath {s}'s coat. The sailor had caught {flag} when a gust tore it from its pole.",
        f'"I thought it belonged to someone who needed it more than I did," {s} explained. "I was trying to find its home."',
        f"{h} called everyone closer, and {i} recognized the old welcome mark stitched into the cloth.",
        f"The child thanked {s}, tied the flag to the tallest pole, and gave the first marching step. The infantry drum answered, and the sailors lifted their caps.",
        f"By sunset, {ending}. The parade had begun late, but every person in town felt exactly on time.",
    ]
    return _record_story(
        world,
        arc="missing_flag",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _quiet_drum_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    s = world.sailor.label
    i = world.infantry.label
    p = world.place
    sound = _choice(rng, ["a soft tap", "a warm heartbeat", "three gentle beats"])
    discovery = f"the infantry drum had gone quiet because {i} was saving its last strength for a child who needed courage"
    trouble = "the parade stopped when the drummer could no longer keep the marching rhythm"
    cause = f"{i} had noticed a frightened child near the crowd and used the drum slowly to help that child breathe"
    resolution = f"{h} invited the crowd to clap the rhythm while {s} helped carry the drum and {i} walked at an easier pace"
    ending = "the whole parade moved with a shared beat, and the drum sounded stronger because nobody was carrying it alone"
    lesson = "a gentle pause can help everyone move forward"
    lines = [
        f"At {p}, {h} stood beside the parade route with a paper star pinned to a bright coat.",
        f"{i} led the infantry with a proud drumbeat, while {s} waved from a sailor's blue row.",
        f"Then the drum slowed. Tap. Tap. Silence.",
        f'"Did the parade forget its song?" whispered {h}.',
        f'"No," said {i}. "I saw a little one trembling in the crowd, so I played {sound} until their breathing grew calm."',
        f"{s} stepped from the sailor line. \"Then we will make a softer song,\" said the sailor.",
        f"{h} began clapping slowly. The crowd joined in, and soon every person could hear the gentle rhythm without shouting over it.",
        f"{i} smiled, placed one hand on the drum, and marched beside {s} while the people carried the beat together.",
        f"At the harbor gate, {ending}. The parade's loudest moment was the kindness everyone could hear.",
    ]
    return _record_story(
        world,
        arc="quiet_drum",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _sailor_bear_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    s = world.sailor.label
    i = world.infantry.label
    p = world.place
    toy = _choice(rng, ["a stuffed seal", "a cloth whale", "a tiny wooden boat"])
    discovery = f"the sailor carrying the banner was secretly carrying {toy} for a homesick child"
    trouble = "the sailor stepped out of line when a small child began crying beside the parade"
    cause = f"{s} recognized the child's lost {toy} and left the marching line to return it"
    resolution = f"{h} asked {i} to hold the banner while {s} knelt and returned {toy}, then the child joined the parade"
    ending = "the banner, the sailor, and the newly smiling child reached the square together"
    lesson = "stopping to care for one person can make a celebration larger"
    lines = [
        f"The parade glittered through {p}, and {h} counted every sailor's button as the music passed.",
        f"{s} carried the town banner while {i} kept the infantry line steady behind the brass band.",
        f"Suddenly, a child near the curb began to cry. The child had lost {toy}.",
        f'"Please keep marching," said {h}. "I will help look."',
        f'"I know that toy," said {s}. "I saw it near the fountain before the parade began."',
        f"{s} stepped from the line, and the banner drooped. {i} caught the pole before it touched the ground.",
        f"Near the fountain, {s} found {toy} beneath a bench and carried it back with both hands.",
        f'"You left the parade for me," said the child.',
        f'"A parade is not a parade if someone is left behind," answered {s}.',
        f"{h} took the child's hand, and {i} held the banner high while everyone made space.",
        f"By the time they reached the square, {ending}. The crowd cheered most warmly for the sailor who had stopped.",
    ]
    return _record_story(
        world,
        arc="sailor_bear",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _backward_march_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    s = world.sailor.label
    i = world.infantry.label
    p = world.place
    object_name = _choice(rng, ["a lost mitten", "a fallen paper crown", "a small silver whistle"])
    discovery = f"the infantry unit was marching backward so {i} could watch for {object_name} along the road"
    trouble = "the crowd laughed when the infantry appeared to be marching the wrong way"
    cause = f"{i} was guiding the parade back toward a quiet child who had dropped {object_name}"
    resolution = f"{h} explained the plan, and {s} led the sailors in turning the parade around to help retrieve {object_name}"
    ending = "the infantry marched forward again, with the recovered treasure held high above the cheering crowd"
    lesson = "a strange-looking choice may be a careful way to help"
    lines = [
        f"At {p}, the parade began with flags, bells, and the bright boots of the infantry.",
        f"But suddenly {i} and the soldiers started marching backward.",
        f'"Are they going the wrong way?' asked {h}.',
        f'"Wait and watch," said {s}. "Good sailors look twice before they steer a ship."',
        f"The crowd giggled, but {h} saw {i} looking carefully along the street.",
        f"Near a fountain sat a quiet child, staring sadly at {object_name}.",
        f"{i} had been marching backward to keep the lost treasure in sight without pushing through the crowd.",
        f'"Now we know why," said {h}. "The odd way was the helpful way."',
        f"{s} raised a hand, and the sailors turned with the band. Together they made a gentle circle around the child.",
        f"{h} picked up {object_name} and returned it. Then {i} gave one crisp signal.",
        f"At last, {ending}. The crowd cheered for the parade that had known when to turn around.",
    ]
    return _record_story(
        world,
        arc="backward_march",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


def _empty_chair_arc(world: World, rng: random.Random) -> str:
    h = world.hero.label
    s = world.sailor.label
    i = world.infantry.label
    p = world.place
    meal = _choice(rng, ["warm soup", "apple buns", "corn cakes"])
    discovery = f"the empty chair at the parade stand was saved for a sailor's grandmother who could not walk far"
    trouble = "the celebration seemed to have a missing guest and a lonely place at the front"
    cause = f"{s} had carried {meal} to the chair and was waiting for an elder who needed a short rest"
    resolution = f"{h} and {i} brought the chair closer to the parade while {s} welcomed the elder without making a fuss"
    ending = "the empty chair became the best seat in the square, because it held a story and made room for one more neighbor"
    lesson = "making room is a way of saying that someone belongs"
    lines = [
        f"The parade was ready at {p}, but one bright chair stood empty near the front.",
        f"{h} wondered about it while {i} checked the infantry drums and {s} straightened a sailor's blue scarf.",
        f'"Who is that chair for?" asked {h}.',
        f'"For someone who wants to come," said {s}. "Wanting is sometimes the first step, but not always the easiest one."',
        f"An elderly woman appeared at the end of the street, leaning carefully on a cane.",
        f"{s} had saved the chair for his grandmother and placed {meal} beside it.",
        f"{i} moved the parade rope back, and {h} carried the chair a little nearer to the musicians.",
        f'"I feared I would miss everything," said the grandmother.',
        f'"You will not miss us," said {h}. "We will bring the parade to you."',
        f"The band played softly as the sailors and infantry passed close by, then everyone shared the food.",
        f"Before the sun touched the rooftops, {ending}. Even the marching drums seemed to make room.",
    ]
    return _record_story(
        world,
        arc="empty_chair",
        discovery=discovery,
        trouble=trouble,
        cause=cause,
        resolution=resolution,
        ending=ending,
        lesson=lesson,
        lines=lines,
    )


ARC_BUILDERS = [
    _missing_flag_arc,
    _quiet_drum_arc,
    _sailor_bear_arc,
    _backward_march_arc,
    _empty_chair_arc,
]


def generate_story(world: World) -> str:
    rng = random.Random(world.seed ^ 0x51A17)
    builder = ARC_BUILDERS[world.seed % len(ARC_BUILDERS)]
    return builder(world, rng)


def story_qa(world: World) -> list[QAItem]:
    h = world.hero.label
    facts = world.facts
    return [
        QAItem(
            question=f"What did {h} discover during the parade?",
            answer=f"{h} discovered that {facts['discovery']}.",
        ),
        QAItem(
            question="What caused the trouble?",
            answer=f"The trouble began because {facts['cause']}.",
        ),
        QAItem(
            question=f"How did {h} help solve the problem?",
            answer=f"{facts['resolution']}.",
        ),
        QAItem(
            question="What heartwarming idea does the story show?",
            answer=f"The story shows that {facts['lesson']}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    common = [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people walk or move together, often with music, flags, and decorations.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works or travels on a boat or ship and helps care for it and the people aboard.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move mainly on foot.",
        ),
    ]
    arc_items = {
        "missing_flag": QAItem(
            question="Why are flags useful in a parade?",
            answer="Flags help people recognize a group, show welcome or celebration, and make the procession easy to see.",
        ),
        "quiet_drum": QAItem(
            question="Why might a parade use a drum?",
            answer="A drum gives people a steady rhythm so they can march together.",
        ),
        "sailor_bear": QAItem(
            question="Why should a parade make room for someone who is left behind?",
            answer="Making room lets everyone feel included and allows the celebration to become safer and kinder.",
        ),
        "backward_march": QAItem(
            question="Why might someone move backward while helping?",
            answer="Moving backward can let a person watch a place or object carefully while guiding others in the right direction.",
        ),
        "empty_chair": QAItem(
            question="What does an empty chair at a celebration sometimes show?",
            answer="An empty chair can show that someone is expected, remembered, or being welcomed even before they arrive.",
        ),
    }
    return common + [arc_items[world.facts["arc"]]]


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a heartwarming story for young children about a parade, a sailor, and infantry.",
        f"Tell a gentle story set at {world.place} where a parade reveals a surprising act of kindness.",
        "Create a simple story with a clear twist in which a sailor or infantry member is helping in an unexpected way.",
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in [world.hero, world.sailor, world.infantry, world.parade]:
        lines.append(
            f"  {ent.id:9} {ent.kind:9} label={ent.label!r} owner={ent.owner!r} "
            f"meters={ent.meters} memes={ent.memes}"
        )
    lines.append(f"  place={world.place!r}")
    lines.append(f"  arc={world.facts.get('arc', '')!r}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for number, prompt in enumerate(sample.prompts, 1):
        out.append(f"{number}. {prompt}")
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


def _validate_args(args: argparse.Namespace) -> None:
    if args.n < 1:
        raise StoryError("-n must be at least 1.")
    if args.all and any(
        value is not None
        for value in [args.name, args.sailor_name, args.infantry_name, args.place]
    ):
        raise StoryError("--all cannot be combined with explicit character or place choices.")


def main() -> None:
    args = build_parser().parse_args()
    try:
        _validate_args(args)
    except StoryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(2)

    if args.show_asp:
        print(asp_program("#show ready/1.\n#show brave/1.\n#show together/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("3 compatible logical atoms: ready(hero), brave(hero), together(hero)")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                name="Luna",
                sailor_name="Sailor June",
                infantry_name="Corporal Reed",
                place="the harbor square",
            ),
            StoryParams(
                name="Milo",
                sailor_name="Sailor Theo",
                infantry_name="Private Ellis",
                place="the seaside town",
            ),
            StoryParams(
                name="Nia",
                sailor_name="Sailor Mae",
                infantry_name="Sergeant Vale",
                place="the bright waterfront",
            ),
            StoryParams(
                name="Tessa",
                sailor_name="Sailor Ben",
                infantry_name="Corporal Mina",
                place="the old lighthouse road",
            ),
            StoryParams(
                name="Owen",
                sailor_name="Sailor Rosa",
                infantry_name="Private Jo",
                place="the market by the pier",
            ),
        ]
        for index, params in enumerate(curated):
            params.seed = base_seed + index
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        limit = max(50, args.n * 20)
        while len(samples) < args.n and index < limit:
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not produce enough distinct story variants.")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
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
