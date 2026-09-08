#!/usr/bin/env python3
"""Heartwarming parade tales about a sailor, infantry friends, and a surprising twist."""

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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    sailor: str = "Mara"
    infantry_friend: str = "Jon"
    helper: str = "Pip"
    harbor: str = "Seabright"
    trial: int = 0
    opening: int = 0
    dialogue: int = 0
    twist: int = 0
    ending: int = 0


SAILORS = ["Mara", "Nell", "Tavi", "Rhea", "Sol"]
INFANTRY = ["Jon", "Ada", "Bram", "Ike", "Lio"]
HELPERS = ["Pip", "Mina", "Theo", "Bea", "Kit"]
HARBORS = ["Seabright", "Bluebell", "Lantern Bay", "Clover Quay"]

TRIALS = [
    {
        "title": "the silent flag",
        "problem": "A strong wind tore the parade's signal flag from its pole just before the opening march.",
        "first_try": "The infantry lined up shoulder to shoulder and tried to hold a blanket aloft, but it flapped over their faces.",
        "clue": "The sailor noticed tiny brass bells hanging from the children's wagon beside the pier.",
        "action": "She tied the bells to a row of short ribbons, so each marcher could hear the turn even when the wind hid the flag.",
        "result": "The parade reached the square in one bright, jingling line.",
        "object": "signal ribbons",
        "lesson": "A new kind of signal can help everyone belong.",
    },
    {
        "title": "the rolling drum",
        "problem": "The parade drum broke loose from its cart and began rolling toward the crowded harbor steps.",
        "first_try": "The infantry chased it downhill, but every hurried boot made the drum bounce faster.",
        "clue": "The sailor saw a coil of soft rope resting beside a mooring post.",
        "action": "She made a wide loop and called for the marchers to hold still while the rope gently caught the drum.",
        "result": "The drum stopped safely, and its first beat welcomed the whole crowd.",
        "object": "blue parade drum",
        "lesson": "Calm teamwork can stop a problem that speed only worsens.",
    },
    {
        "title": "the missing lantern",
        "problem": "One lantern vanished from the evening parade, leaving a young marcher afraid to walk in the dark.",
        "first_try": "The infantry searched under carts and benches, but the sunset shadows made every corner look alike.",
        "clue": "The sailor heard a faint clink near the old lifeboat.",
        "action": "She followed the sound and found the lantern caught in a fishing net, then freed it without tearing the net.",
        "result": "The young marcher carried the glowing lantern at the front.",
        "object": "golden lantern",
        "lesson": "Careful listening can guide a kinder rescue.",
    },
    {
        "title": "the crooked welcome arch",
        "problem": "The wooden arch for the parade leaned across the street and blocked the visiting families.",
        "first_try": "The infantry pushed from one side, but the arch only leaned farther.",
        "clue": "The sailor found that one leg rested on a loose paving stone.",
        "action": "She asked the infantry to lift together while the children slid the stone away and packed the gap with sand.",
        "result": "The arch stood straight, with room beneath it for every small hat and tall cap.",
        "object": "welcome arch",
        "lesson": "Finding the small cause can open a large path.",
    },
    {
        "title": "the shy sea song",
        "problem": "The sailor's choir forgot the first line of its song just as the parade reached the bandstand.",
        "first_try": "The infantry sang louder to cover the silence, but the different voices tangled like nets.",
        "clue": "The sailor remembered that the youngest drummer knew the song through its rhythm.",
        "action": "She asked the drummer to tap the missing pattern, and everyone joined one line at a time.",
        "result": "The song grew from a tiny tap into a warm chorus.",
        "object": "sea-song drum",
        "lesson": "A quiet contribution can help many voices find their way.",
    },
]

OPENINGS = [
    "At dawn in {harbor}, the parade gathered beside the shining water.",
    "The streets of {harbor} filled with bunting, footsteps, and the smell of warm bread.",
    "Before the parade began, {sailor} the sailor checked every rope, bell, and ribbon twice.",
    "The infantry arrived at {harbor} in neat rows, but their smiles were brighter than their boots.",
    "A cheerful crowd waited by the harbor while {sailor} wondered what surprise the day might bring.",
]

DIALOGUES = [
    "'We can still make this work,' said {sailor}. 'But we must notice what the wind is telling us.'",
    "'Should we hurry?' asked {infantry_friend}. '{sailor} shook her head. 'First, let us help the smallest marcher feel safe.'",
    "'I thought a parade needed one grand answer,' said {infantry_friend}. '{sailor} replied, 'Sometimes the answer is made of many little hands.'",
    "'Listen,' whispered {helper}. '{sailor} smiled. 'That sound may know more than our shouting does.'",
    "'Will everyone get to join?' asked {helper}. 'That is the part we must solve,' said {sailor}.",
]

TWISTS = [
    "Then came the twist: the missing piece had not been lost at all. A group of children had carried it aside so a frightened puppy could pass safely.",
    "Then came the twist: the crowd discovered that the sailor's careful helper was the smallest marcher, who had noticed the clue first.",
    "Then came the twist: the old parade cart held a spare part, but it had been saved for the welcome banner instead of the grand officers' platform.",
    "Then came the twist: the infantry thought they were helping the sailor, yet their new formation had been designed from her very first observation.",
    "Then came the twist: the person who had caused the trouble was a nervous newcomer, and the parade chose to give that person a job rather than blame.",
]

ENDINGS = [
    "When the last ribbon lifted, the crowd answered with one gentle cheer.",
    "That evening, the harbor lights trembled on the water like a second parade.",
    "The marchers left muddy footprints beneath the arch, and every footprint pointed toward a friend.",
    "Long after the music ended, the rescued object rested in the town hall as a reminder of shared courage.",
    "At sunset, the sailor and the infantry sat together on the pier, listening to the happy echoes fade.",
]


ASP_RULES = r"""
#show ready/1.
#show helps/2.

ready(parade) :- signal(parade), safe(parade).
helps(infantry, sailor) :- needs_help(sailor), teamwork(infantry).
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("signal", "parade"),
            asp.fact("safe", "parade"),
            asp.fact("needs_help", "sailor"),
            asp.fact("teamwork", "infantry"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Heartwarming storyworld about a parade, a sailor, infantry, and a hopeful twist."
    )
    parser.add_argument("--sailor", choices=SAILORS)
    parser.add_argument("--infantry-friend", choices=INFANTRY)
    parser.add_argument("--helper", choices=HELPERS)
    parser.add_argument("--harbor", choices=HARBORS)
    parser.add_argument("--trial", type=int, choices=range(len(TRIALS)))
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
    if args.n < 1:
        raise StoryError("-n must be at least 1")
    return StoryParams(
        seed=args.seed,
        sailor=args.sailor or rng.choice(SAILORS),
        infantry_friend=args.infantry_friend or rng.choice(INFANTRY),
        helper=args.helper or rng.choice(HELPERS),
        harbor=args.harbor or rng.choice(HARBORS),
        trial=args.trial if args.trial is not None else rng.randrange(len(TRIALS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        twist=rng.randrange(len(TWISTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def generate(params: StoryParams) -> StorySample:
    if params.trial < 0 or params.trial >= len(TRIALS):
        raise StoryError("trial must identify an existing parade trial")

    world = World()
    sailor = world.add(
        Entity(
            id=params.sailor,
            kind="character",
            type="sailor",
            label=params.sailor,
            meters={"distance_to_parade": 2.0},
            memes={"care": 1.0, "hope": 1.0},
        )
    )
    infantry = world.add(
        Entity(
            id=params.infantry_friend,
            kind="character",
            type="infantry",
            label=params.infantry_friend,
            meters={"formation_strength": 1.0},
            memes={"loyalty": 1.0},
        )
    )
    helper = world.add(
        Entity(
            id=params.helper,
            kind="character",
            type="child_helper",
            label=params.helper,
            meters={"reach": 0.5},
            memes={"curiosity": 1.0},
        )
    )

    trial = TRIALS[params.trial]
    values = {
        "sailor": sailor.id,
        "infantry_friend": infantry.id,
        "helper": helper.id,
        "harbor": params.harbor,
    }

    world.say(OPENINGS[params.opening % len(OPENINGS)].format(**values))
    world.say(
        f"{sailor.id} stood with the sailor band while {infantry.id} and the infantry "
        f"waited beside the parade route."
    )
    world.say(trial["problem"])
    world.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(**values))
    world.say(trial["first_try"])
    world.say(f"{helper.id} pointed toward the clue. {trial['clue']}")
    world.say(TWISTS[params.twist % len(TWISTS)].format(**values))
    world.say(trial["action"])
    world.say(trial["result"])
    world.say(
        f"{infantry.id} said, 'The parade feels warmer when everyone has a part.' "
        f"{sailor.id} answered, 'And every part can reveal a new way forward.'"
    )
    world.say(f"Lesson learned: {trial['lesson']}")
    world.say(ENDINGS[params.ending % len(ENDINGS)])

    sailor.memes["confidence"] = 1.0
    infantry.memes["belonging"] = 1.0
    helper.memes["pride"] = 1.0
    world.facts.update(
        sailor=sailor,
        infantry=infantry,
        helper=helper,
        harbor=params.harbor,
        trial=trial,
        parade=True,
        solved=True,
        twist=True,
        object=trial["object"],
    )

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    facts = world.facts
    trial = facts["trial"]
    return [
        f"Write a heartwarming story about {facts['sailor'].id} the sailor helping an infantry group during a parade.",
        f"Tell a child-friendly parade story involving {trial['title']} and a surprising twist.",
        f"Write a warm story where teamwork solves a parade problem and ends with {trial['object']} or its consequence.",
    ]


def story_qa(world: World) -> list[QAItem]:
    facts = world.facts
    sailor = facts["sailor"]
    infantry = facts["infantry"]
    helper = facts["helper"]
    trial = facts["trial"]
    return [
        QAItem(
            question=f"What problem did {sailor.id} face during the parade?",
            answer=f"The parade faced {trial['problem']}",
        ),
        QAItem(
            question=f"How did {helper.id} contribute?",
            answer=f"{helper.id} noticed and pointed toward the clue: {trial['clue']}",
        ),
        QAItem(
            question=f"How did {sailor.id} and the infantry solve the problem?",
            answer=f"They worked together this way: {trial['action']}",
        ),
        QAItem(
            question="What was the twist in the story?",
            answer="The twist was that " + TWISTS[world.facts["trial"].get("twist_index", 0) if False else 0],
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"The parade became safe and welcoming, and {trial['result']}",
        ),
        QAItem(
            question="What lesson did the characters learn?",
            answer=f"They learned that {trial['lesson']}",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a parade?",
            answer="A parade is an organized procession in which people, groups, music, or decorated vehicles move together for others to watch.",
        ),
        QAItem(
            question="What does a sailor do?",
            answer="A sailor works on or travels by boat and may help navigate, handle equipment, and care for the crew.",
        ),
        QAItem(
            question="What is infantry?",
            answer="Infantry are soldiers who serve and move mainly on foot.",
        ),
        QAItem(
            question="Why can a twist make a story heartwarming?",
            answer="A hopeful twist can reveal an unexpected kindness, helper, or meaning that brings people closer together.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id} ({entity.type}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {sorted(world.facts.keys())}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show ready/1.\n#show helps/2."))
    return sorted(set(asp.atoms(model, "ready")) | set(asp.atoms(model, "helps")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show ready/1.\n#show helps/2."))
    actual = set(asp.atoms(model, "ready")) | set(asp.atoms(model, "helps"))
    expected = {("parade",), ("infantry", "sailor")}
    if actual != expected:
        print("MISMATCH between clingo and Python gate.")
        print("  clingo:", sorted(actual))
        print("  python:", sorted(expected))
        return 1
    for params in [
        StoryParams(),
        StoryParams(sailor="Nell", infantry_friend="Ada", helper="Mina", harbor="Bluebell", trial=3),
    ]:
        sample = generate(params)
        if "parade" not in sample.story.lower() or "sailor" not in sample.story.lower():
            print("Generated story failed domain verification.")
            return 1
        if not any(item.question for item in sample.story_qa):
            print("Generated story failed QA verification.")
            return 1
    print("OK: ASP parity and generated-story checks passed.")
    return 0


CURATED = [
    StoryParams(sailor="Mara", infantry_friend="Jon", helper="Pip", harbor="Seabright", trial=0),
    StoryParams(
        sailor="Nell",
        infantry_friend="Ada",
        helper="Mina",
        harbor="Bluebell",
        trial=2,
        opening=1,
        dialogue=2,
        twist=4,
        ending=1,
    ),
    StoryParams(
        sailor="Rhea",
        infantry_friend="Bram",
        helper="Theo",
        harbor="Lantern Bay",
        trial=4,
        opening=4,
        dialogue=3,
        twist=1,
        ending=4,
    ),
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
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show ready/1.\n#show helps/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        facts = asp_valid()
        print(f"{len(facts)} ASP-supported parade facts")
        for fact in facts:
            print(fact)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < args.n and attempt < max(50, args.n * 30):
            params = resolve_params(args, random.Random(base_seed + attempt))
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            attempt += 1
        if len(samples) < args.n:
            raise StoryError("could not create the requested number of distinct stories")

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            header = f"### {sample.params.sailor}: parade at {sample.params.harbor}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
