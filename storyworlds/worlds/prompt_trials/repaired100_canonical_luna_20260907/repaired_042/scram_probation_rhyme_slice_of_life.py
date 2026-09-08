#!/usr/bin/env python3
"""
A small slice-of-life storyworld about Scram, probation, and a rhyme that turns
an ordinary morning into a careful second chance.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    held: Optional[str] = None


@dataclass
class StoryParams:
    seed: Optional[int] = None
    scram_name: str = "Scram"
    helper_name: str = "Mara"
    place: str = "the little neighborhood bakery"
    rhyme: str = "Slow hands, warm plans"
    scenario_id: int = 0
    detail_variant: int = 0


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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


RHYMES = [
    "Slow hands, warm plans",
    "Check the tray, save the day",
    "Kind and neat, work is sweet",
    "Pause and see, then agree",
]

SCENES = [
    {
        "ordinary": "Scram was on probation at the bakery, learning to help without rushing.",
        "mistake": "Scram stacked a tray of warm buns too high and hurried toward the front counter",
        "risk": "the top buns could slide onto the floor and make the morning harder for everyone",
        "clue": "a soft wobble traveled through the tray each time Scram took a fast step",
        "action": "Mara steadied the tray while Scram lowered the buns one row at a time",
        "change": "the tray became safe, and the buns reached the counter warm and whole",
        "lesson": "probation was not a punishment to escape; it was time to practice trust",
        "ending": "Scram placed the last bun on the shelf and smiled at the small, steady stack",
    },
    {
        "ordinary": "Scram was on probation at the community garden, learning which tools belonged where.",
        "mistake": "Scram left a hose across the garden path and hurried off to fetch a bright red bucket",
        "risk": "someone could trip before the morning watering was finished",
        "clue": "a line of damp footprints stopped exactly beside the hidden hose",
        "action": "Mara asked Scram to coil the hose while she moved the bucket out of the way",
        "change": "the path cleared, and the young plants received their water without a stumble",
        "lesson": "being trusted meant noticing small dangers before someone else found them",
        "ending": "Scram hung the hose on its hook, where it made a neat green circle in the sun",
    },
    {
        "ordinary": "Scram was on probation at the library, learning to return books gently and on time.",
        "mistake": "Scram pushed a tall cart too quickly around the reading-room corner",
        "risk": "the cart could bump a quiet reader or spill books across the floor",
        "clue": "the wheels squeaked whenever the cart leaned toward the corner",
        "action": "Mara showed Scram how to stop, look, and guide the cart with both hands",
        "change": "the cart rolled smoothly, and every book arrived at the right shelf",
        "lesson": "a careful pause could protect both people and the work they shared",
        "ending": "Scram slid the final book into place beneath a patch of afternoon light",
    },
]

WORLD_KNOWLEDGE = [
    QAItem(
        question="What does probation mean?",
        answer="Probation is a period when someone follows extra rules and practices responsibility while others watch their progress.",
    ),
    QAItem(
        question="What does scram mean?",
        answer="Scram is an informal word meaning to leave quickly, though in this story Scram is also a character's name.",
    ),
    QAItem(
        question="Why can a rhyme help someone remember a lesson?",
        answer="A short rhyme is easy to repeat, so its rhythm can help a person remember what to do.",
    ),
    QAItem(
        question="What is a slice-of-life story?",
        answer="A slice-of-life story focuses on an ordinary moment and shows how a small choice matters.",
    ),
]

ASP_RULES = r"""
safe_action :- probation(scram), helper(mara), rhyme_rule.
rhyme_rule :- reminder(slow_hands_warm_plans).
valid_story :- safe_action.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("probation", "scram"),
            asp.fact("helper", "mara"),
            asp.fact("reminder", "slow_hands_warm_plans"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n#show valid_story/0.\n"


def python_reasonable(params: StoryParams) -> None:
    if not params.scram_name.strip():
        raise StoryError("Scram needs a name.")
    if not params.helper_name.strip():
        raise StoryError("The helper needs a name.")
    if params.scram_name.strip().lower() == params.helper_name.strip().lower():
        raise StoryError("Scram and the helper must have different names.")
    if params.rhyme not in RHYMES:
        raise StoryError("Choose a rhyme from the available reminders.")
    if not 0 <= params.scenario_id < len(SCENES):
        raise StoryError("The chosen everyday scene does not exist.")


def build_world(params: StoryParams) -> World:
    python_reasonable(params)
    rng = random.Random(params.seed if params.seed is not None else 17)
    scene = SCENES[params.scenario_id]
    world = World()

    scram = world.add(
        Entity(
            id="scram",
            type="character",
            label=params.scram_name,
            traits=["curious", "on probation"],
            meters={"care": 0.4, "rush": 0.7},
            memes={"worry": 0.5, "hope": 0.6, "trust": 0.2},
        )
    )
    helper = world.add(
        Entity(
            id="mara",
            type="character",
            label=params.helper_name,
            traits=["patient", "observant"],
            meters={"patience": 1.0},
            memes={"trust": 0.7},
        )
    )

    openings = [
        f"Morning came softly to {params.place}.",
        f"The first light rested on the windows of {params.place}.",
        f"At {params.place}, the day began with ordinary sounds.",
    ]
    world.say(rng.choice(openings))
    world.say(scene["ordinary"])
    world.say(
        f"{scram.label} kept repeating the reminder, “{params.rhyme},” although the words felt easier to say than to follow."
    )

    world.para()
    world.say(f"Then {scene['mistake']}.")
    world.say(f"{scene['risk'].capitalize()}.")
    scram.meters["rush"] += 0.3
    scram.memes["worry"] += 0.3
    world.say(f"{helper.label} called, “{scram.label}, wait a moment.”")
    world.say(f"“I need to scram before I make another mistake,” {scram.label} said.")
    world.say(
        f"{helper.label} answered, “Leaving is not the only way to stop. What do you notice?”"
    )
    world.say(f"{scene['clue'].capitalize()}.")
    world.say(f"{scram.label} repeated the rhyme more slowly: “{params.rhyme}.”")

    world.para()
    world.say(f"Together, {scene['action'].lower()}.")
    scram.meters["care"] += 0.8
    scram.meters["rush"] -= 0.5
    scram.memes["worry"] -= 0.3
    scram.memes["trust"] += 0.5
    helper.memes["trust"] += 0.2
    world.say(f"{scene['change'].capitalize()}.")
    world.say(
        f"“You stayed and fixed the problem,” {helper.label} said. “That is the work probation is for.”"
    )
    world.say(f"“I thought probation meant everyone expected me to fail,” {scram.label} replied.")
    world.say(
        f"“It means you get a fair chance to show what you can learn,” {helper.label} said."
    )
    world.say(f"{scene['lesson'].capitalize()}.")

    world.para()
    world.say(f"{scram.label} thanked {helper.label} and practiced the rhyme once more.")
    world.say(f"{scene['ending'].capitalize()}.")
    world.say(
        f"The morning had not become grand or dramatic. It had simply become one careful day in which {scram.label} chose to stay, notice, and try again."
    )

    world.facts.update(
        scram=scram,
        helper=helper,
        scene=scene,
        rhyme=params.rhyme,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly slice-of-life story about {f['scram'].label} on probation.",
        f"Use the rhyme “{f['rhyme']}” to help {f['scram'].label} change a choice.",
        "Show an ordinary mistake, a brief conversation, and a concrete sign of growing trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    scram = f["scram"]
    helper = f["helper"]
    scene = f["scene"]
    return [
        QAItem(
            question=f"What problem did {scram.label} cause?",
            answer=f"{scram.label} acted too quickly: {scene['mistake']}. That created the risk that {scene['risk']}.",
        ),
        QAItem(
            question=f"How did {helper.label} help {scram.label}?",
            answer=f"{helper.label} did not simply scold {scram.label}. The helper asked a question, pointed out the clue, and then helped {scene['action'].lower()}.",
        ),
        QAItem(
            question=f"What did {scram.label} learn during probation?",
            answer=f"{scram.label} learned that {scene['lesson']}. Probation gave Scram a chance to practice responsibility and rebuild trust.",
        ),
        QAItem(
            question="What did the rhyme remind Scram to do?",
            answer=f"The rhyme was “{f['rhyme']}.” It reminded Scram to pause, notice the problem, and choose a careful action instead of rushing away.",
        ),
        QAItem(
            question="How did the ending show that things had changed?",
            answer=f"At the end, {scene['ending']}. The neat result showed that Scram had handled the ordinary task with more care.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


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


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "valid_story"))
    if atoms == {()}:
        print("OK: ASP gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH between ASP and Python gates.")
    print("  ASP:", sorted(atoms))
    print("  PY :", [()])
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:6} ({entity.type}) "
            f"meters={entity.meters} memes={entity.memes} traits={entity.traits}"
        )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A slice-of-life storyworld about Scram, probation, and a useful rhyme."
    )
    parser.add_argument("--scram-name", default=None)
    parser.add_argument("--helper-name", default=None)
    parser.add_argument("--place", default=None)
    parser.add_argument("--rhyme", choices=RHYMES, default=None)
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
    places = [
        "the little neighborhood bakery",
        "the community garden",
        "the town library",
    ]
    names = ["Scram", "Sam", "Toby", "Rory"]
    helpers = ["Mara", "June", "Pia", "Ari"]
    params = StoryParams(
        seed=None,
        scram_name=args.scram_name or rng.choice(names),
        helper_name=args.helper_name or rng.choice(helpers),
        place=args.place or rng.choice(places),
        rhyme=args.rhyme or rng.choice(RHYMES),
        scenario_id=rng.randrange(len(SCENES)),
        detail_variant=rng.randrange(4),
    )
    python_reasonable(params)
    return params


CURATED = [
    StoryParams(
        scram_name="Scram",
        helper_name="Mara",
        place="the little neighborhood bakery",
        rhyme="Slow hands, warm plans",
        scenario_id=0,
    ),
    StoryParams(
        scram_name="Scram",
        helper_name="June",
        place="the community garden",
        rhyme="Check the tray, save the day",
        scenario_id=1,
    ),
    StoryParams(
        scram_name="Scram",
        helper_name="Pia",
        place="the town library",
        rhyme="Pause and see, then agree",
        scenario_id=2,
    ),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return

    if args.verify:
        code = asp_verify()
        if code:
            sys.exit(code)
        for params in CURATED:
            generate(params)
        print("OK: generated stories pass.")
        return

    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print("ASP model:", sorted(asp.atoms(model, "valid_story")))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n:
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
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
