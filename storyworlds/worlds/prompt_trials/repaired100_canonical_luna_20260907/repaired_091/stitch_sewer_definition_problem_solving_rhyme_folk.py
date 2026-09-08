#!/usr/bin/env python3
"""
Story world: a stitch, a sewer, and a definition solved through rhyme in a folk tale.
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
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from storyworlds.results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    type: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    village: str = "Willowmere"
    hero: str = "Luna"
    helper: str = "Pip"
    sewer: str = "the old stone sewer"
    seed: Optional[int] = None


@dataclass
class World:
    village: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, str] = field(default_factory=dict)
    events: list[str] = field(default_factory=list)

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


SCENARIOS = (
    {
        "name": "the moon-thread gate",
        "problem": "the village moon-banner tore just before the lantern feast",
        "clue": "a silver thread led from the torn banner toward the sewer grate",
        "cause": "water rising through the sewer had snagged the banner on a rough iron tooth",
        "repair": "Luna tied a bright stitch around the weak place while the mason smoothed the iron tooth",
        "rhyme": '"A stitch that holds, a drain that flows; mend the truth, and homeward goes."',
        "ending": "the repaired banner floated above the feast like a pale moon that had learned to smile",
        "lesson": "a small clue can open a large answer when patient hands follow it",
        "definition": "A sewer is a covered channel that carries dirty water away from homes and streets.",
    },
    {
        "name": "the missing blue stitch",
        "problem": "the mayor's blue cloak opened at the shoulder whenever she crossed the market bridge",
        "clue": "the loose thread was wet with droplets that smelled of the sewer",
        "cause": "a hidden pipe leak beneath the bridge had weakened the old stitch",
        "repair": "Pip marked the damp stones, and Luna replaced the stitch after the bridge keeper closed the path",
        "rhyme": '"Where water creeps beneath the street, mend the thread and dry your feet."',
        "ending": "the mayor crossed safely, her blue cloak fastened by a stitch bright as a kingfisher",
        "lesson": "repairing the right cause is wiser than hiding the first sign of trouble",
        "definition": "A stitch is a loop of thread used to join or hold pieces of cloth together.",
    },
    {
        "name": "the riddle under the grating",
        "problem": "a basket of winter apples vanished whenever it was left beside the old sewer",
        "clue": "apple leaves floated back through the grating in a narrow line",
        "cause": "the basket's loose bottom had dropped into a dry side channel below the grate",
        "repair": "the villagers lifted the basket with a hooked pole and repaired its bottom with three strong stitches",
        "rhyme": '"Three stitches tight, one basket sound; seek the stream beneath the ground."',
        "ending": "the apples rested in a dry shed, and the repaired basket held together through the winter",
        "lesson": "good problem solving asks where a thing went, not only who took it",
        "definition": "A grating is a strong frame of bars that covers an opening while letting water pass.",
    },
    {
        "name": "the thread in the bell",
        "problem": "the chapel bell gave a muffled note whenever the dawn wind blew",
        "clue": "a red stitch clung to the bell rope, and the rope smelled of damp stone",
        "cause": "the rope had brushed a torn festival cloth caught beside the sewer's upper vent",
        "repair": "Luna followed the thread, and the sexton removed the cloth without entering the sewer",
        "rhyme": '"Follow the thread, heed what it shows; clear the path where the cold wind blows."',
        "ending": "the bell rang clear over Willowmere, and the red stitch became a charm on Luna's sleeve",
        "lesson": "evidence is useful when it is followed carefully and safely",
        "definition": "A vent is an opening that lets air move in or out of a covered place.",
    },
)

OPENINGS = (
    "Long ago, when roofs were thatched and every good answer began with a question, Luna lived in Willowmere.",
    "In the little village of Willowmere, people trusted old songs, bright thread, and careful eyes.",
    "One autumn morning, a trouble appeared in Willowmere that was too small for a hero's sword and too important to ignore.",
    "At the edge of Willowmere stood an old stone sewer, and near it began a puzzle no one could explain.",
)

BRIDGES = (
    "Luna did not blame the first person who came to mind. She measured, listened, and looked for what had changed.",
    "Pip wanted to guess at once, but Luna held up one finger. A guess was only a door; the clue had to show which door.",
    "Together they compared the wet stones, the loose thread, and the direction of the water.",
    "The villagers brought lamps and stayed on the dry path, because solving a problem did not mean stepping into danger.",
)

QA_PATTERNS = (
    (
        "What problem did Luna face?",
        "What clue helped Luna and Pip?",
        "What caused the trouble?",
        "How was the problem repaired?",
        "What does the story teach?",
    ),
    (
        "Why did the villagers need Luna's help?",
        "Where did the useful evidence lead?",
        "What was the real answer?",
        "What careful action solved the puzzle?",
        "What lesson did Luna carry home?",
    ),
)


def validate_params(params: StoryParams) -> None:
    for name in ("village", "hero", "helper", "sewer"):
        value = getattr(params, name)
        if not isinstance(value, str) or not value.strip():
            raise StoryError(f"{name} must be a non-empty name")
    if params.hero.strip().lower() == params.helper.strip().lower():
        raise StoryError("hero and helper must have different names")
    if params.seed is not None and not isinstance(params.seed, int):
        raise StoryError("seed must be an integer")


def tell(params: StoryParams) -> World:
    validate_params(params)
    rng = random.Random(params.seed if params.seed is not None else 0)
    scenario = SCENARIOS[rng.randrange(len(SCENARIOS))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))]
    bridge = BRIDGES[rng.randrange(len(BRIDGES))]
    style = rng.randrange(len(QA_PATTERNS))

    world = World(params.village)
    hero = world.add(
        Entity(
            id="hero",
            kind="person",
            type="girl",
            label=params.hero,
            meters={"distance_to_sewer": 8.0, "problem_progress": 0.0},
            memes={"curiosity": 1.0, "courage": 1.0, "confidence": 0.0},
            traits=["patient", "observant"],
        )
    )
    helper = world.add(
        Entity(
            id="helper",
            kind="person",
            type="boy",
            label=params.helper,
            meters={"distance_to_sewer": 9.0, "problem_progress": 0.0},
            memes={"friendship": 1.0, "worry": 1.0, "confidence": 0.0},
            traits=["loyal", "quick-thinking"],
        )
    )
    sewer = world.add(
        Entity(
            id="sewer",
            kind="place",
            type="sewer",
            label=params.sewer,
            meters={"water_flow": 1.0, "safety": 1.0},
            memes={"mystery": 1.0},
            traits=["covered", "stone-lined"],
        )
    )
    stitch = world.add(
        Entity(
            id="stitch",
            kind="thing",
            type="stitch",
            label="the telling stitch",
            meters={"strength": 0.0},
            memes={"meaning": 1.0},
            traits=["silver-threaded"],
        )
    )

    world.facts = {
        "scenario": scenario["name"],
        "problem": scenario["problem"],
        "clue": scenario["clue"],
        "cause": scenario["cause"],
        "repair": scenario["repair"],
        "rhyme": scenario["rhyme"],
        "ending": scenario["ending"],
        "lesson": scenario["lesson"],
        "definition": scenario["definition"],
        "hero": hero.label,
        "helper": helper.label,
        "sewer": sewer.label,
        "style": str(style),
    }

    world.say(opening)
    world.say(
        f"{hero.label} was known for solving problems with a needle, a question, and a steady mind. "
        f"{helper.label} was her friend, though he preferred a quick answer to a careful one."
    )
    world.say(f"That day, {scenario['problem']}.")
    world.para()

    world.say(
        f'"Perhaps the sewer swallowed the missing piece," {helper.label} said. '
        f'"Perhaps," said {hero.label}, "but a definition tells us what a thing is, while a clue tells us what happened."'
    )
    world.say(bridge)
    world.say(f"The first useful clue was this: {scenario['clue']}.")
    world.say(f"{hero.label} knelt beside the dry path and recited, {scenario['rhyme']}")
    world.events.append("clue_found")
    hero.meters["problem_progress"] = 0.45
    helper.meters["problem_progress"] = 0.35
    helper.memes["worry"] = 0.3
    world.para()

    world.say(f"The clue pointed to the truth: {scenario['cause']}.")
    world.say(
        f'"Now we know where to mend," said {helper.label}. '
        f'"And we know where not to wander," answered {hero.label}. '
        f"They asked the village workers to handle the grate and stayed safely above the stones."
    )
    world.say(f"{scenario['repair']}.")
    world.events.append("safe_repair")
    stitch.meters["strength"] = 1.0
    hero.meters["problem_progress"] = 1.0
    helper.meters["problem_progress"] = 1.0
    hero.memes["confidence"] = 1.0
    helper.memes["confidence"] = 1.0
    sewer.memes["mystery"] = 0.0
    world.para()

    world.say(
        f"{hero.label} explained the definition plainly: {scenario['definition']} "
        f"Then {helper.label} repeated the rhyme so the children of Willowmere would remember both the word and the wisdom."
    )
    world.say(
        f"Their friendship changed as well. {helper.label} learned that a careful question could be faster than a wild guess, "
        f"and {hero.label} learned to welcome his bold ideas before testing them."
    )
    world.say(f"They carried home this lesson: {scenario['lesson']}.")
    world.say(f"By sunset, {scenario['ending']}.")
    world.events.append("story_resolved")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly folk tale in {f['scenario']} with {f['hero']}, {f['helper']}, a stitch, and {f['sewer']}.",
        f"Use problem solving to show how the clue '{f['clue']}' reveals that {f['cause']}.",
        f"Include a memorable rhyme and explain this definition naturally: {f['definition']}",
    ]


def make_story_qa(world: World) -> list[QAItem]:
    f = world.facts
    prompts = QA_PATTERNS[int(f["style"])]
    return [
        QAItem(prompts[0], f"{f['hero']} had to solve this problem: {f['problem']}."),
        QAItem(prompts[1], f"The important clue was that {f['clue']}."),
        QAItem(prompts[2], f"The real cause was that {f['cause']}."),
        QAItem(prompts[3], f"The villagers stayed safe while {f['repair']}."),
        QAItem(prompts[4], f"The lesson was that {f['lesson']}."),
    ]


def make_world_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            "What is a stitch?",
            "A stitch is a loop of thread used to join or hold pieces of cloth together.",
        ),
        QAItem(
            "What is a sewer?",
            f"{f['definition']}",
        ),
        QAItem(
            "Why should people stay out of an old sewer?",
            "An old sewer may have deep water, weak surfaces, poor air, or hidden dangers, so trained workers should inspect it.",
        ),
        QAItem(
            "Why is a rhyme useful in a folk tale?",
            "A rhyme makes an idea easy to remember and can carry a lesson from one person to another.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---", f"events: {', '.join(world.events)}"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


ASP_RULES = r"""
character(hero).
character(helper).
place(sewer).
thing(stitch).
has_clue(hero).
observes(helper).
safe(sewer).
problem_found(hero) :- character(hero), has_clue(hero).
definition_known(hero) :- problem_found(hero), thing(stitch).
repair_possible(hero) :- definition_known(hero), safe(sewer), thing(stitch).
solved(hero) :- repair_possible(hero), observes(helper).
friendship_grows(hero,helper) :- solved(hero).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join(
        [
            asp.fact("character", "hero"),
            asp.fact("character", "helper"),
            asp.fact("place", "sewer"),
            asp.fact("thing", "stitch"),
            asp.fact("has_clue", "hero"),
            asp.fact("observes", "helper"),
            asp.fact("safe", "sewer"),
        ]
    )


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp

    model = asp.one_model(
        asp_program(
            "#show problem_found/1.\n"
            "#show definition_known/1.\n"
            "#show repair_possible/1.\n"
            "#show solved/1.\n"
            "#show friendship_grows/2.\n"
        )
    )
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    expected = {
        ("problem_found", 1),
        ("definition_known", 1),
        ("repair_possible", 1),
        ("solved", 1),
        ("friendship_grows", 2),
    }
    if not expected.issubset(atoms):
        print("MISMATCH: ASP rules did not produce the expected solution chain.")
        return 1
    for seed in range(3):
        sample = generate(
            StoryParams(
                village="Willowmere",
                hero="Luna",
                helper="Pip",
                sewer="the old stone sewer",
                seed=seed,
            )
        )
        required = ("stitch", "sewer", "definition")
        if not all(word in sample.story.lower() for word in required):
            print("MISMATCH: generated story omitted a required narrative instrument.")
            return 1
        if len(sample.story_qa) < 5:
            print("MISMATCH: generated story lacks grounded questions.")
            return 1
    print("OK: ASP parity and generated story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A folk tale about a stitch, a sewer, a definition, and problem solving through rhyme."
    )
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    parser.add_argument("--village", default="Willowmere")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--helper", default=None)
    parser.add_argument("--sewer", default="the old stone sewer")
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.hero or rng.choice(["Luna", "Mira", "Nell", "Rose"])
    helper = args.helper or rng.choice(["Pip", "Tom", "Ash", "Robin"])
    if hero.lower() == helper.lower():
        helper = "Pip" if hero.lower() != "pip" else "Ash"
    return StoryParams(
        village=args.village,
        hero=hero,
        helper=helper,
        sewer=args.sewer,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=make_story_qa(world),
        world_qa=make_world_qa(world),
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

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    if args.show_asp:
        print(
            asp_program(
                "#show problem_found/1.\n"
                "#show definition_known/1.\n"
                "#show repair_possible/1.\n"
                "#show solved/1.\n"
                "#show friendship_grows/2."
            )
        )
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp

        model = asp.one_model(
            asp_program(
                "#show problem_found/1.\n"
                "#show definition_known/1.\n"
                "#show repair_possible/1.\n"
                "#show solved/1.\n"
                "#show friendship_grows/2."
            )
        )
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(SCENARIOS) if args.all else args.n
    samples: list[StorySample] = []
    seen: set[str] = set()
    attempt = 0

    while len(samples) < count and attempt < max(100, count * 30):
        seed = base_seed + attempt
        rng = random.Random(seed)
        params = resolve_params(args, rng)
        params.seed = seed
        sample = generate(params)
        if sample.story not in seen:
            seen.add(sample.story)
            samples.append(sample)
        attempt += 1

    if not samples:
        raise StoryError("could not generate a story")

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
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    try:
        main()
    except StoryError as exc:
        print(f"StoryError: {exc}", file=sys.stderr)
        raise SystemExit(2)
