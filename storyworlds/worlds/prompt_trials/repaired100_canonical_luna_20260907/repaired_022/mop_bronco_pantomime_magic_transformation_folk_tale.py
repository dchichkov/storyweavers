#!/usr/bin/env python3
"""
A small folk-tale storyworld about a mop, a bronco, and a pantomime magic trick.

A humble stable mop is transformed by kindness and imagination into a brave
bronco for a village pantomime. The simulated world tracks physical meters and
emotional memes, while the prose follows a clear problem, turn, and resolution.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve()
ROOT = next(parent for parent in HERE.parents if (parent / "results.py").is_file())
sys.path.insert(0, str(ROOT))
from results import QAItem, StoryError, StorySample  # noqa: E402


NAMES = ["Luna", "Mira", "Talia", "Nora", "Pia", "Elsa", "Rina", "Ada"]
HELPERS = ["Grandmother", "the baker", "the stable keeper", "a little brother"]
VILLAGE_PLACES = ["the old barn", "the village square", "the moonlit stable", "the harvest yard"]
PANTOMIME_ROLES = ["a brave rider", "a wandering princess", "a young herder", "a moon messenger"]

TALES = [
    {
        "title": "The Mop That Ran Like Thunder",
        "goal": "play the brave rider in the village pantomime",
        "problem": "the real bronco lost its voice and would not leave the shadowed stall",
        "failed": "waved the mop like a sword and tried to make the empty costume seem grand",
        "consequence": "The audience saw a mop, a worried rider, and a very long silence.",
        "clue": "the mop's wooden handle fit the old saddle blanket as neatly as a horse's back",
        "helper_action": "tied a red ribbon to the mop and showed Luna how to bow before every proud step",
        "plan": "turn the mop into a pantomime bronco, give it a name, and let the audience's imagination do the galloping",
        "child_action": "wrapped the mop in the saddle blanket, named it Thunderbroom, and practiced a bold pantomime trot",
        "dialogue": '"A true bronco begins with a brave heart," said the helper. "The hooves may be imaginary."',
        "resolution": "When Luna lifted the ribbon, the mop seemed to prance across the boards, and every child heard invisible hooves.",
        "ending": "After the show, Thunderbroom rested by the stable door, its red ribbon glowing like a tiny sunset.",
        "object": "the enchanted mop",
    },
    {
        "title": "The Bronco Behind the Curtain",
        "goal": "lead the opening scene of the harvest pantomime",
        "problem": "the painted bronco prop cracked just before the curtain rose",
        "failed": "held the broken prop together while pretending that a missing leg was part of the dance",
        "consequence": "The painted bronco leaned sideways, and the villagers began whispering instead of clapping.",
        "clue": "the old mop still had a strong handle and a fringe that swayed like a mane",
        "helper_action": "polished the handle, tucked straw into the fringe, and placed a bell around its neck",
        "plan": "transform the mop into a lively bronco and teach the first three hoofbeats",
        "child_action": "polished the handle, named it Bristlehoof, and taught it three jaunty hoofbeats",
        "dialogue": '"A broken picture can still hold a whole horse," said the helper. "Show them with your hands."',
        "resolution": "The pantomime bronco bowed, bucked, and spun so merrily that the villagers forgot the cracked prop.",
        "ending": "The bell on Bristlehoof chimed beside the curtain while the harvest moon climbed above the square.",
        "object": "the painted bronco",
    },
    {
        "title": "The Moon's Wooden Horse",
        "goal": "carry a silver moon lantern through the final pantomime scene",
        "problem": "the village bronco was too tired to perform after pulling the grain cart",
        "failed": "whispered commands to the tired horse and hurried through the opening gesture",
        "consequence": "The lantern sagged, the music stopped, and Luna nearly tripped over the painted moon.",
        "clue": "the mop's soft strands could shine like a mane beneath the lantern light",
        "helper_action": "wrapped the mop in blue cloth and fastened the moon lantern to its handle",
        "plan": "make a gentle magical bronco from the mop and move slowly enough for the moon to follow",
        "child_action": "wrapped the mop in blue cloth, called it Moonmane, and moved in a slow silver circle",
        "dialogue": '"Magic does not always roar," said the helper. "Sometimes it swishes softly."',
        "resolution": "The audience watched the mop become a moonlit bronco, and the final scene glowed with quiet wonder.",
        "ending": "At dawn, a silver thread still clung to Moonmane's fringe as if the moon had left a blessing.",
        "object": "the moon lantern",
    },
    {
        "title": "The Pantomime of the Golden Hoof",
        "goal": "win the village prize for the finest pantomime",
        "problem": "the costume horse tore while Luna was dressing for the contest",
        "failed": "hid the tear behind a curtain and tried to gallop without showing the missing cloth",
        "consequence": "The horse costume flapped like a little sail, and Luna's grand entrance became a stumble.",
        "clue": "the mop's long fringe could cover the tear and make a splendid tail",
        "helper_action": "stitched the fringe into the costume and painted a golden hoof on the handle",
        "plan": "let the mop become the horse's tail, turn the tear into a design, and dance with confidence",
        "child_action": "stitched the fringe into the costume, painted a golden hoof, and danced into the square",
        "dialogue": '"A tear is only a doorway for a new idea," said the helper. "Step through it proudly."',
        "resolution": "The judges praised the golden hoof, and the repaired costume won the village prize.",
        "ending": "The golden hoof shone on the wall all winter, while the mop waited below for its next adventure.",
        "object": "the golden hoof",
    },
]


@dataclass
class StoryParams:
    name: str = "Luna"
    helper: str = "Grandmother"
    place: str = "the old barn"
    role: str = "a brave rider"
    seed: Optional[int] = None


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for key in ["dust", "distance", "ribbon", "costume_wear"]:
            self.meters.setdefault(key, 0.0)
        for key in ["worry", "courage", "wonder", "relief", "kindness"]:
            self.memes.setdefault(key, 0.0)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        return "\n\n".join(" ".join(part) for part in self.paragraphs if part)


def stable_seed(params: StoryParams) -> int:
    if params.seed is not None:
        return params.seed
    return sum(ord(ch) for ch in "|".join([params.name, params.helper, params.place, params.role]))


def capitalize_label(value: str) -> str:
    return value[:1].upper() + value[1:] if value else value


def tell_world(params: StoryParams) -> World:
    rng = random.Random(stable_seed(params))
    tale = TALES[stable_seed(params) % len(TALES)]
    w = World(place=params.place)

    child = w.add(Entity("child", "character", params.name))
    helper = w.add(Entity("helper", "character", params.helper))
    mop = w.add(Entity("mop", "tool", "the mop"))
    bronco = w.add(Entity("bronco", "animal", "the bronco"))
    prop = w.add(Entity("prop", "stage_prop", tale["object"]))

    w.facts.update(
        params=params,
        tale=tale,
        child=child,
        helper=helper,
        mop=mop,
        bronco=bronco,
        prop=prop,
        title=tale["title"],
        magic=True,
        transformation=True,
        pantomime=True,
    )

    child.memes["courage"] = 1
    child.meters["distance"] = 2
    mop.meters["dust"] = 3
    mop.memes["wonder"] = 1
    bronco.memes["worry"] = 2

    w.say(f"In {params.place}, {params.name} prepared to {tale['goal']}.")
    w.say(f"The village pantomime was to begin at sunset, with {params.name} playing {params.role}.")
    w.say(f"Beside the stage lay {tale['object']}, and near the stable waited a quiet bronco.")
    w.para()

    child.memes["worry"] += 2
    w.say(f"But {tale['problem']}.")
    w.say(f"Trying not to disappoint anyone, {params.name} {tale['failed']}.")
    w.say(tale["consequence"])
    w.facts["problem"] = tale["problem"]
    w.facts["consequence"] = tale["consequence"]
    w.para()

    helper.memes["kindness"] = 2
    w.say(f"{capitalize_label(params.helper)} noticed the trouble and {tale['helper_action']}.")
    w.say(tale["dialogue"])
    w.say(f"{params.name} listened, then discovered that {tale['clue']}.")
    w.say(f"So {params.name} decided to {tale['plan']}.")
    w.say(f"With a little stage magic, {tale['child_action']}.")
    w.para()

    mop.meters["dust"] = 0
    mop.meters["ribbon"] = 1
    mop.memes["wonder"] = 3
    child.memes["worry"] = 0
    child.memes["courage"] += 2
    child.memes["relief"] = 2
    bronco.memes["worry"] = 0
    w.say(tale["resolution"])
    w.say(f"{capitalize_label(params.helper)} bowed, and {params.name} bowed too.")
    w.para()
    w.say(tale["ending"])

    w.facts.update(
        clue=tale["clue"],
        solution=tale["child_action"],
        resolution=tale["resolution"],
        ending=tale["ending"],
        resolved=True,
    )
    return w


def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]
    tale = world.facts["tale"]
    return [
        f"Tell a folk tale about {p.name} using a mop, a bronco, and a pantomime.",
        f"Write a magical transformation story in which a humble mop helps {p.name} save a village performance.",
        f"Create a child-friendly folk tale set in {p.place}, with a clear problem, helpful advice, stage magic, and a changed ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    tale = world.facts["tale"]
    return [
        QAItem(
            f"What was {p.name} preparing to do?",
            f"{p.name} was preparing to {tale['goal']}.",
        ),
        QAItem(
            "What problem threatened the pantomime?",
            f"{tale['problem'].capitalize()}.",
        ),
        QAItem(
            "What clue led to the magical transformation?",
            f"The clue was that {tale['clue']}.",
        ),
        QAItem(
            f"How did {p.name} and {p.helper} solve the problem?",
            f"{capitalize_label(p.helper)} {tale['helper_action']}. Then {p.name} {tale['child_action']}, and {tale['resolution'][0].lower() + tale['resolution'][1:]}",
        ),
        QAItem(
            "What showed that the story had a happy ending?",
            tale["ending"],
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a pantomime?",
            "A pantomime is a performance that tells a story through movement, gestures, and imagination.",
        ),
        QAItem(
            "What is a bronco?",
            "A bronco is a lively horse, especially one known for bucking or spirited movement.",
        ),
        QAItem(
            "Why can an ordinary object become magical in a folk tale?",
            "An ordinary object can become magical in a folk tale because courage, kindness, and imagination give it a new purpose.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 3) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id} ({entity.kind}) meters={meters} memes={memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


ASP_RULES = r"""
% A valid magical pantomime needs all three story instruments.
valid_story :- has_mop, has_bronco, has_pantomime, magic, transformation.
transformed(mop, bronco) :- valid_story.
happy_ending :- transformed(mop, bronco).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("has_mop"),
            asp.fact("has_bronco"),
            asp.fact("has_pantomime"),
            asp.fact("magic"),
            asp.fact("transformation"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import asp
    except Exception as err:
        print(f"ASP unavailable: {err}")
        return 1

    model = asp.one_model(
        asp_program("#show valid_story/0.\n#show transformed/2.\n#show happy_ending/0.")
    )
    valid = set(asp.atoms(model, "valid_story"))
    transformed = set(asp.atoms(model, "transformed"))
    happy = set(asp.atoms(model, "happy_ending"))
    if valid == {()} and transformed == {("mop", "bronco")} and happy == {()}:
        for seed in range(4):
            sample = generate(StoryParams(seed=seed))
            if not sample.world or not sample.world.facts.get("resolved"):
                print("Generated story verification failed.")
                return 1
        print("OK: ASP parity and generated-story checks pass.")
        return 0

    print("MISMATCH between ASP and Python expectations.")
    print("  valid:", sorted(valid))
    print("  transformed:", sorted(transformed))
    print("  happy:", sorted(happy))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk-tale world of a mop, a bronco, and pantomime magic."
    )
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--place", choices=VILLAGE_PLACES)
    parser.add_argument("--role", choices=PANTOMIME_ROLES)
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
        helper=args.helper or rng.choice(HELPERS),
        place=args.place or rng.choice(VILLAGE_PLACES),
        role=args.role or rng.choice(PANTOMIME_ROLES),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_world(params)
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/0.\n#show transformed/2.\n#show happy_ending/0."))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program("#show valid_story/0.\n#show transformed/2.\n#show happy_ending/0.")
        )
        print(sorted(asp.atoms(model, "valid_story")))
        print(sorted(asp.atoms(model, "transformed")))
        print(sorted(asp.atoms(model, "happy_ending")))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index, place in enumerate(VILLAGE_PLACES):
            params = StoryParams(
                name=NAMES[index % len(NAMES)],
                helper=HELPERS[index % len(HELPERS)],
                place=place,
                role=PANTOMIME_ROLES[index % len(PANTOMIME_ROLES)],
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            seed = base_seed + index
            index += 1
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not generate enough distinct stories")

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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
