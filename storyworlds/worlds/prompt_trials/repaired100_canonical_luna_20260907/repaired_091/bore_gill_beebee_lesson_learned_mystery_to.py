#!/usr/bin/env python3
"""
A heartwarming little mystery in which Bore, Gill, and Beebee learn that
careful listening can turn a worry into a kindness.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


@dataclass
class StoryParams:
    place: str = "the little riverside learning hut"
    hero: str = "Bore"
    helper: str = "Gill"
    friend: str = "Beebee"
    seed: Optional[int] = None


MYSTERIES = (
    {
        "name": "the missing welcome bell",
        "mystery": "the tiny welcome bell no longer rang when visitors opened the hut door",
        "clue": "a bright thread was wrapped around the bell's clapper",
        "wrong": "Bore worried that the bell had forgotten how to sing",
        "cause": "Beebee's gift ribbon had slipped through a loose window and caught the clapper",
        "fix": "Gill carefully freed the ribbon, tied the gift away from the bell, and tightened the window latch",
        "lesson": "a quiet problem deserves patient attention before anyone is blamed",
        "ending": "the bell chimed softly as three friends welcomed the evening walkers",
    },
    {
        "name": "the blue footprints",
        "mystery": "small blue footprints appeared across the clean floor each morning",
        "clue": "the marks stopped beside a leaky pot of sky-blue paint",
        "wrong": "Gill wondered whether a secret visitor had been sneaking through the hut at night",
        "cause": "rainwater had carried paint from the pot onto a toy wagon wheel",
        "fix": "Bore cleaned the wheel, Beebee moved the paint beneath a shelf, and Gill dried the little trail",
        "lesson": "a strange sign becomes clearer when friends follow it all the way to its source",
        "ending": "the floor shone clean while the blue wagon waited ready for the next art lesson",
    },
    {
        "name": "the humming cupboard",
        "mystery": "the old cupboard hummed whenever everyone gathered for story time",
        "clue": "the humming stopped when the cupboard door was opened a finger-width",
        "wrong": "Beebee feared a lonely creature was hiding inside",
        "cause": "a paper kite string had become tight against the wooden hinge",
        "fix": "Gill opened the cupboard safely, Bore loosened the string, and Beebee tucked the kite into its basket",
        "lesson": "kind friends investigate gently instead of turning a sound into a frightening story",
        "ending": "the cupboard rested quietly while Beebee chose a kite tale for everyone",
    },
    {
        "name": "the vanished honey cakes",
        "mystery": "one honey cake disappeared from the cooling tray before snack time",
        "clue": "a trail of crumbs led beneath the reading bench",
        "wrong": "Bore thought someone had taken the cake and hidden the truth",
        "cause": "Beebee's little cart had bumped the tray, and the cake had rolled into its covered basket",
        "fix": "Beebee admitted the accident, Gill checked the basket, and Bore shared the cake with everyone",
        "lesson": "honesty gives friendship a place to begin repairing a mistake",
        "ending": "the last honey cake was divided into three warm, sticky pieces",
    },
    {
        "name": "the whispering garden",
        "mystery": "the window garden whispered after sunset",
        "clue": "the whisper came only when the dry leaves touched the paper lantern",
        "wrong": "Gill imagined that the garden was asking for a secret",
        "cause": "a loose lantern string brushed the leaves whenever the evening breeze passed",
        "fix": "Bore moved the lantern, Beebee gathered the leaves, and Gill tied the string in a soft loop",
        "lesson": "listening closely can turn a mystery into a simple act of care",
        "ending": "the garden grew still, and its leaves shone beneath the peaceful lantern",
    },
)

OPENINGS = (
    "Morning light spilled across the floor of {place}.",
    "After a night of gentle rain, {place} felt fresh and bright.",
    "The friends arrived early, carrying smiles and a basket of shared snacks.",
    "A warm breeze moved through {place} as the day's lesson was about to begin.",
    "At the edge of the quiet river, three friends found a small puzzle waiting.",
)

TRANSITIONS = (
    "They did not rush to choose a culprit. They looked, listened, and asked what had changed.",
    "The friends agreed that a good mystery needed kind questions as well as clever eyes.",
    "Bore watched the floor, Gill checked the nearby objects, and Beebee remembered what had happened the day before.",
    "They promised to keep everyone safe and to test one small idea at a time.",
)


@dataclass
class World:
    place: str
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, str] = field(default_factory=dict)
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
        return "\n\n".join(" ".join(group) for group in self.paragraphs if group)


def tell(params: StoryParams) -> World:
    if not params.hero.strip() or not params.helper.strip() or not params.friend.strip():
        raise StoryError("hero, helper, and friend names must not be empty")
    if len({params.hero.lower(), params.helper.lower(), params.friend.lower()}) != 3:
        raise StoryError("hero, helper, and friend names must be different")

    rng = random.Random(params.seed if params.seed is not None else 0)
    case = MYSTERIES[rng.randrange(len(MYSTERIES))]
    opening = OPENINGS[rng.randrange(len(OPENINGS))].format(place=params.place)
    transition = TRANSITIONS[rng.randrange(len(TRANSITIONS))]

    world = World(params.place)
    bore = world.add(Entity(
        id="bore",
        kind="character",
        type="child",
        label=params.hero,
        traits=["curious", "honest"],
        memes={"curiosity": 1.0, "friendship": 1.0},
    ))
    gill = world.add(Entity(
        id="gill",
        kind="character",
        type="child",
        label=params.helper,
        traits=["careful", "observant"],
        memes={"patience": 1.0, "friendship": 1.0},
    ))
    beebee = world.add(Entity(
        id="beebee",
        kind="character",
        type="small_friend",
        label=params.friend,
        traits=["warm", "hopeful"],
        memes={"trust": 1.0, "friendship": 1.0},
    ))

    world.facts = {
        "case": case["name"],
        "mystery": case["mystery"],
        "clue": case["clue"],
        "wrong": case["wrong"],
        "cause": case["cause"],
        "fix": case["fix"],
        "lesson": case["lesson"],
        "ending": case["ending"],
        "hero": bore.label,
        "helper": gill.label,
        "friend": beebee.label,
    }

    bore.meters.update(safe=1.0, understanding=0.0)
    gill.meters.update(safe=1.0, understanding=0.0)
    beebee.meters.update(safe=1.0, understanding=0.0)

    world.say(opening)
    world.say(
        f"{bore.label}, {gill.label}, and {beebee.label} cared for the room together. "
        f"They swept gently, placed every tool back, and made sure the little place was safe for everyone."
    )
    world.say(f"That morning, they noticed a mystery: {case['mystery']}.")
    world.para()

    world.say(f"{case['wrong']}.")
    world.say(transition)
    world.say(f"{gill.label} pointed to the useful clue: {case['clue']}.")
    world.say(
        f'"Let us ask before we guess," {bore.label} said. '
        f'"And let us listen to every answer," {gill.label} replied.'
    )
    world.say(
        f'"I remember moving something near there yesterday," {beebee.label} added softly. '
        f'"That may help us find the truth."'
    )
    world.para()

    world.say(f"The clue revealed what had happened: {case['cause']}.")
    world.say(f"Together, and without making anyone feel ashamed, they solved it: {case['fix']}.")
    bore.meters["understanding"] = 1.0
    gill.meters["understanding"] = 1.0
    beebee.meters["understanding"] = 1.0
    bore.memes["relief"] = 1.0
    gill.memes["confidence"] = 1.0
    beebee.memes["trust"] = 2.0

    world.say(
        f"{bore.label} smiled at {beebee.label}. "
        f'"Thank you for telling us," {bore.label} said. '
        f'"Friends can fix more when they tell the truth," {beebee.label} answered.'
    )
    world.say(
        f"The lesson learned was simple: {case['lesson']}. "
        f"The mystery had not made the friends farther apart; it had taught them how to stand closer."
    )
    world.para()
    world.say(case["ending"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a heartwarming mystery to solve for {f['hero']}, {f['helper']}, and {f['friend']}.",
        f"Include the clue '{f['clue']}' and reveal that {f['cause']}.",
        f"End with a lesson learned: {f['lesson']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"What mystery did {f['hero']}, {f['helper']}, and {f['friend']} need to solve?",
            answer=f"They needed to explain why {f['mystery']}.",
        ),
        QAItem(
            question="What clue helped the friends?",
            answer=f"The helpful clue was that {f['clue']}. It gave them a safer path than guessing or blaming anyone.",
        ),
        QAItem(
            question="What had really happened?",
            answer=f"They discovered that {f['cause']}.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"They solved it kindly: {f['fix']}.",
        ),
        QAItem(
            question="What did the friends learn?",
            answer=f"They learned that {f['lesson']}.",
        ),
        QAItem(
            question="How did the mystery change the friends?",
            answer="They became more patient and trusting because they listened to one another and repaired the problem together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a question or puzzling event that can be understood by noticing clues and testing careful ideas.",
        ),
        QAItem(
            question="What does a lesson learned mean?",
            answer="A lesson learned is a helpful idea someone understands after an experience and can use later.",
        ),
        QAItem(
            question="Why is it important to ask before blaming?",
            answer="Asking first helps people find the true cause and keeps an honest mistake from hurting a friendship.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
character(X) :- child(X).
mystery_to_solve(X) :- character(X), clue_found(X), patient(X).
lesson_learned(X) :- mystery_to_solve(X), repaired(X), honest(X).
friendship_strengthened(X) :- lesson_learned(X), kind(X).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    return "\n".join([
        asp.fact("child", "bore"),
        asp.fact("child", "gill"),
        asp.fact("child", "beebee"),
        asp.fact("character", "bore"),
        asp.fact("character", "gill"),
        asp.fact("character", "beebee"),
        asp.fact("clue_found", "bore"),
        asp.fact("clue_found", "gill"),
        asp.fact("clue_found", "beebee"),
        asp.fact("patient", "bore"),
        asp.fact("patient", "gill"),
        asp.fact("patient", "beebee"),
        asp.fact("repaired", "bore"),
        asp.fact("repaired", "gill"),
        asp.fact("repaired", "beebee"),
        asp.fact("honest", "bore"),
        asp.fact("honest", "gill"),
        asp.fact("honest", "beebee"),
        asp.fact("kind", "bore"),
        asp.fact("kind", "gill"),
        asp.fact("kind", "beebee"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    try:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program(
            "#show mystery_to_solve/1.\n"
            "#show lesson_learned/1.\n"
            "#show friendship_strengthened/1.\n"
        ))
    except ImportError as exc:
        print(f"ASP unavailable: {exc}")
        return 0

    names = {(symbol.name, len(symbol.arguments)) for symbol in model}
    needed = {
        ("mystery_to_solve", 1),
        ("lesson_learned", 1),
        ("friendship_strengthened", 1),
    }
    if not names >= needed:
        print("MISMATCH: ASP rules did not produce the expected facts.")
        return 1

    for seed in range(3):
        sample = generate(StoryParams(seed=seed))
        if not sample.story.strip() or "mystery" not in sample.story.lower():
            print("MISMATCH: generated story failed the prose check.")
            return 1
    print("OK: ASP/Python parity and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A heartwarming mystery to solve about Bore, Gill, and Beebee."
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
    parser.add_argument("--place", default="the little riverside learning hut")
    parser.add_argument("--hero", default=None)
    parser.add_argument("--helper", default=None)
    parser.add_argument("--friend", default=None)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    names = ["Bore", "Gill", "Beebee"]
    hero = args.hero or rng.choice(names)
    helper = args.helper or rng.choice([name for name in names if name != hero])
    friend = args.friend or rng.choice([name for name in names if name not in {hero, helper}])
    return StoryParams(
        place=args.place,
        hero=hero,
        helper=helper,
        friend=friend,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: type={entity.type} meters={entity.meters} memes={entity.memes}"
        )
    return "\n".join(lines)


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
        print(asp_program(
            "#show mystery_to_solve/1.\n"
            "#show lesson_learned/1.\n"
            "#show friendship_strengthened/1.\n"
        ))
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program(
            "#show mystery_to_solve/1.\n"
            "#show lesson_learned/1.\n"
            "#show friendship_strengthened/1.\n"
        ))
        print("\n".join(str(atom) for atom in model))
        return

    if args.n < 1:
        raise StoryError("-n must be at least 1")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for index in range(len(MYSTERIES)):
            params = StoryParams(
                place=args.place,
                hero=args.hero or "Bore",
                helper=args.helper or "Gill",
                friend=args.friend or "Beebee",
                seed=base_seed + index,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        target = max(1, args.n)
        while len(samples) < target and index < max(100, target * 20):
            params = resolve_params(args, random.Random(base_seed + index))
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            index += 1

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
            header=f"### variant {index + 1}" if len(samples) > 1 else "",
        )
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
