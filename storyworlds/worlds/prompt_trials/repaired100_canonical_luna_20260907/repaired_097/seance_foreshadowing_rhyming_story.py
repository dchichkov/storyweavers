#!/usr/bin/env python3
"""
Standalone storyworld: a gentle séance of clues, told as a rhyming story.

A small moonlit mystery lets children notice foreshadowing, listen to a
friendly spirit, and solve a harmless problem with patience and kindness.
The séance is theatrical and safe: no one is harmed, frightened, or asked to
handle dangerous objects.
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
class StoryParams:
    seed: Optional[int] = None
    place: str = "moonlit parlor"
    protagonist: str = "Luna"
    protagonist_type: str = "girl"
    companion: str = "Theo"
    companion_type: str = "boy"
    medium: str = "Aunt Mira"
    medium_type: str = "woman"
    variant: int = 0
    rhyme_mode: int = 0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    location: str = ""

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)


@dataclass
class World:
    params: StoryParams
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
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
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


INCIDENTS = [
    {
        "title": "the silver bell",
        "premise": "Before the séance, a silver bell gave one soft ring though nobody touched its string.",
        "foreshadow": "A blue ribbon beside the bell kept fluttering toward the old window.",
        "problem": "the little bell vanished when the séance circle was ready",
        "spirit": "the bell is beneath the cushion where the moonbeam bends",
        "clue": "the same blue ribbon was caught on the cushion's wooden leg",
        "cause": "a draft had tugged the ribbon and nudged the bell beneath the cushion",
        "resolution": "Luna lifted the cushion only after Aunt Mira said it was safe, and the bell was found.",
        "ending": "The silver bell rang once more, not with a ghostly fright, but with a warm good-night.",
    },
    {
        "title": "the whispering card",
        "premise": "A message card whispered against the table before the séance began.",
        "foreshadow": "Its corner pointed again and again toward a basket of folded quilts.",
        "problem": "the card disappeared before the spirit could answer",
        "spirit": "look where the quilts make a hill, and listen for paper's trill",
        "clue": "a white corner peeped from the lowest folded quilt",
        "cause": "the window breeze had carried the card into the quilt basket",
        "resolution": "Theo asked before reaching in, and Aunt Mira safely retrieved the card.",
        "ending": "The card lay flat beneath the lamp, its moon drawn bright and grand.",
    },
    {
        "title": "the candle shadow",
        "premise": "A candle cast a long shadow shaped like a crooked key.",
        "foreshadow": "Each time the curtain swayed, the shadow slid toward a locked music box.",
        "problem": "the music box would not open for the séance's final sound",
        "spirit": "the key is near the place where the curtain sighs",
        "clue": "a brass glint shone beneath the curtain hem",
        "cause": "the key had slipped from Aunt Mira's pocket when she tied the curtain",
        "resolution": "Aunt Mira unlocked the box herself and played its gentle tune.",
        "ending": "The music box chimed, and the crooked shadow became a starry tune.",
    },
    {
        "title": "the three taps",
        "premise": "Three taps sounded under the séance table before anyone sat down.",
        "foreshadow": "A loose tablecloth rose each time the floorboard gave a tiny creak.",
        "problem": "the tapping seemed like a spirit's warning",
        "spirit": "check the board below, where a small spring may glow",
        "clue": "a toy drumstick rested beside a springy floorboard",
        "cause": "the house cat had batted the drumstick beneath the table",
        "resolution": "Luna and Theo moved away from the table while Aunt Mira checked the harmless toy.",
        "ending": "The cat curled by the hearth, and the table kept quiet all night.",
    },
]


RHYMES = [
    ("In moonlit rooms where soft lamps gleam,", "A séance starts beside a dream."),
    ("The night wore silver, calm and bright,", "And clues came tiptoeing through the light."),
    ("A quiet room can hold a clue,", "If patient eyes know what to do."),
    ("The stars looked down from velvet skies,", "While wonder opened sleepy eyes."),
]

LESSONS = [
    "A hint may whisper before the answer, but careful checking makes the truth shine clearer.",
    "A mysterious sound deserves a calm question before it earns a scary name.",
    "Good courage listens closely, asks permission, and follows evidence step by step.",
    "Foreshadowing is a tiny trail: notice it early, and the ending makes more sense.",
]


class ReasonError(StoryError):
    pass


def reason_gate(params: StoryParams) -> None:
    names = [params.protagonist.strip(), params.companion.strip(), params.medium.strip()]
    if not all(names):
        raise StoryError("all character names must be non-empty")
    if len(set(names)) != len(names):
        raise StoryError("the protagonist, companion, and medium must have different names")
    if params.place != "moonlit parlor":
        raise StoryError("this small séance domain takes place in the moonlit parlor")
    valid_types = {"girl", "boy", "woman", "man"}
    if params.protagonist_type not in valid_types:
        raise StoryError("invalid protagonist type")
    if params.companion_type not in valid_types:
        raise StoryError("invalid companion type")
    if params.medium_type not in valid_types:
        raise StoryError("invalid medium type")


def pronoun(kind: str, case: str = "subject") -> str:
    if kind in {"girl", "woman"}:
        return {"subject": "she", "object": "her", "possessive": "her"}[case]
    return {"subject": "he", "object": "him", "possessive": "his"}[case]


def build_world(params: StoryParams, incident: dict[str, str]) -> World:
    world = World(params)
    world.add(Entity(
        "hero", "character", params.protagonist_type, params.protagonist,
        memes={"curiosity": 1.0, "courage": 0.5}, location="parlor",
    ))
    world.add(Entity(
        "companion", "character", params.companion_type, params.companion,
        memes={"curiosity": 0.8, "trust": 0.5}, location="parlor",
    ))
    world.add(Entity(
        "medium", "character", params.medium_type, params.medium,
        memes={"calm": 1.0, "trust": 1.0}, location="parlor",
    ))
    world.add(Entity(
        "bell", "thing", "bell", "silver bell",
        meters={"visible": 1.0, "moved": 0.0}, location="table",
    ))
    world.add(Entity(
        "ribbon", "thing", "ribbon", "blue ribbon",
        meters={"flutter": 1.0}, location="window",
    ))
    world.add(Entity(
        "cushion", "thing", "cushion", "velvet cushion",
        meters={"shifted": 0.0}, location="chair",
    ))
    world.facts.update(
        title=incident["title"],
        premise=incident["premise"],
        foreshadow=incident["foreshadow"],
        problem=incident["problem"],
        spirit=incident["spirit"],
        clue=incident["clue"],
        cause=incident["cause"],
        resolution=incident["resolution"],
        ending=incident["ending"],
        lesson=LESSONS[(params.variant + params.rhyme_mode) % len(LESSONS)],
        solved=False,
    )
    return world


def tell(params: StoryParams) -> World:
    reason_gate(params)
    incident = INCIDENTS[params.variant % len(INCIDENTS)]
    world = build_world(params, incident)
    hero = world.entities["hero"]
    companion = world.entities["companion"]
    medium = world.entities["medium"]
    bell = world.entities["bell"]
    ribbon = world.entities["ribbon"]
    cushion = world.entities["cushion"]
    opening = RHYMES[params.rhyme_mode % len(RHYMES)]

    world.say(f"{opening[0]} {opening[1]}")
    world.say(
        f"In the {params.place}, {hero.label} sat with {companion.label} and {medium.label}. "
        f"It was a friendly séance, with a lamp, a bell, and questions spoken softly; "
        f"no one would touch anything unsafe or pretend that a mystery was proof of a ghost."
    )
    world.say(f"{incident['premise']} {incident['foreshadow']}")
    world.say(
        f"'That is our first hint,' said {hero.label}. 'Let us remember it, but not jump to a scary answer.'"
    )
    world.say(
        f"'I will watch the clues,' said {companion.label}. "
        f"'And I will keep my hands in my lap,' said {medium.label} with a smile."
    )

    world.para()
    world.say(
        f"Then came the puzzle: {incident['problem']}. "
        f"The room grew still, and {hero.label}'s curiosity rose while {medium.label} stayed calm."
    )
    hero.memes["curiosity"] += 1.0
    companion.memes["curiosity"] += 1.0
    bell.meters["visible"] = 0.0
    bell.meters["moved"] = 1.0

    world.say(
        f"'Spirit, if you are near, can you help us find it?' asked {medium.label}. "
        f"From somewhere close came a gentle answer: '{incident['spirit']}'"
    )
    world.say(
        f"'The words sound mysterious,' said {companion.label}, 'but the ribbon may tell us more.' "
        f"'Yes,' said {hero.label}. 'The early flutter is our foreshadowing clue.'"
    )
    world.say(
        f"They noticed {incident['clue']}. Nobody grabbed at once. "
        f"{hero.label} asked, 'May {medium.label} check the cushion?' and {medium.label} answered, "
        "'Yes, because asking first keeps a mystery safe.'"
    )
    ribbon.meters["flutter"] = 0.0
    cushion.meters["shifted"] = 1.0

    world.para()
    world.say(f"{incident['resolution']} {incident['cause'].capitalize()}.")
    world.facts["solved"] = True
    world.facts["answer"] = incident["cause"]
    world.say(
        f"{companion.label} laughed softly. 'So the séance gave us a clue, but careful looking gave us the answer.' "
        f"'And the first hint mattered,' said {hero.label}. 'It pointed us toward the ending.'"
    )
    world.say(
        f"{medium.label} nodded. 'That is the lesson: {world.facts['lesson']}'"
    )
    world.say(incident["ending"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly rhyming séance story about {f['title']}.",
        f"Use foreshadowing through {f['foreshadow']} before revealing {f['cause']}.",
        f"Show {f['lesson']}",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = world.entities["hero"].label
    companion = world.entities["companion"].label
    medium = world.entities["medium"].label
    return [
        QAItem(
            question=f"What happened during the séance in the story about {f['title']}?",
            answer=f"During the séance, {f['problem']}. The group stayed calm and searched for a real explanation.",
        ),
        QAItem(
            question=f"What was the foreshadowing clue in the story about {f['title']}?",
            answer=f"The foreshadowing clue was that {f['foreshadow']} It hinted at where the missing object could be found.",
        ),
        QAItem(
            question=f"What did the séance message say?",
            answer=f"The message said, '{f['spirit']}' The group treated it as a clue to investigate, not as proof of danger.",
        ),
        QAItem(
            question=f"How did {hero}, {companion}, and {medium} solve the mystery?",
            answer=f"They noticed {f['clue']}, asked permission before checking, and then learned that {f['cause']}.",
        ),
        QAItem(
            question="Why was the séance safe?",
            answer=f"{hero}, {companion}, and {medium} stayed calm, asked before touching anything, and let the responsible adult manage the search. {f['resolution']}",
        ),
        QAItem(
            question=f"What lesson did {hero} learn from {f['title']}?",
            answer=f"{hero} learned that {f['lesson']}",
        ),
    ]


WORLD_KNOWLEDGE = [
    QAItem(
        question="What is a séance?",
        answer="A séance is a meeting presented as a way to communicate with spirits. In a child-friendly story, it can be a pretend, gentle mystery activity guided by a responsible adult.",
    ),
    QAItem(
        question="What is foreshadowing?",
        answer="Foreshadowing is an early hint that prepares readers for something important later in a story.",
    ),
    QAItem(
        question="Why should people investigate a mysterious sound calmly?",
        answer="A calm investigation helps people notice ordinary causes and avoid frightening or blaming someone without evidence.",
    ),
]


def world_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        meters = {k: round(v, 3) for k, v in entity.meters.items() if v}
        memes = {k: round(v, 3) for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:10} ({entity.type:9}) "
            f"location={entity.location!r} meters={meters} memes={memes}"
        )
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
% The early ribbon movement is a foreshadowing clue.
foreshadows(ribbon, bell) :- fluttered(ribbon), missing(bell).

% A calm search is safe when an adult guides it.
safe_search :- adult(medium), asks_permission(hero), calm(medium).

% The mystery is coherent when the clue points to the hidden object.
coherent :- foreshadows(ribbon, bell), safe_search, found(bell).

#show coherent/0.
"""


def asp_facts() -> str:
    import asp

    return "\n".join([
        asp.fact("fluttered", "ribbon"),
        asp.fact("missing", "bell"),
        asp.fact("adult", "medium"),
        asp.fact("asks_permission", "hero"),
        asp.fact("calm", "medium"),
        asp.fact("found", "bell"),
        asp.fact("character", "hero"),
    ])


def asp_program(show: str = "#show coherent/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    asp_ok = any(symbol.name == "coherent" for symbol in model)
    params = StoryParams()
    try:
        reason_gate(params)
        py_ok = True
    except StoryError:
        py_ok = False
    if asp_ok != py_ok:
        print("MISMATCH between ASP and Python reasonableness gate.")
        return 1
    sample = generate(params)
    checks = [
        bool(sample.story),
        "séance" in sample.story.lower(),
        "foreshadow" in sample.story.lower(),
        len(sample.story_qa) >= 3,
    ]
    if not all(checks):
        print("MISMATCH: generated story check failed.")
        return 1
    print("OK: ASP and Python reasonableness gate agree.")
    print("OK: generated story check passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A rhyming séance storyworld with foreshadowing."
    )
    parser.add_argument("--place", choices=["moonlit parlor"], default="moonlit parlor")
    parser.add_argument("--protagonist")
    parser.add_argument("--protagonist-type", choices=["girl", "boy", "woman", "man"], default="girl")
    parser.add_argument("--companion")
    parser.add_argument("--companion-type", choices=["girl", "boy", "woman", "man"], default="boy")
    parser.add_argument("--medium")
    parser.add_argument("--medium-type", choices=["girl", "boy", "woman", "man"], default="woman")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def resolve_params(
    args: argparse.Namespace,
    rng: random.Random,
    sample_seed: int,
) -> StoryParams:
    protagonist = args.protagonist or rng.choice(["Luna", "Mara", "Ivy", "Nell"])
    companion = args.companion or rng.choice(["Theo", "Pip", "Owen", "Sam"])
    medium = args.medium or rng.choice(["Aunt Mira", "Aunt June", "Mara's Nana", "Miss Sol"])
    if len({protagonist, companion, medium}) != 3:
        raise StoryError("chosen character names must be distinct")
    return StoryParams(
        seed=getattr(args, "seed", None),
        place=args.place,
        protagonist=protagonist,
        protagonist_type=args.protagonist_type,
        companion=companion,
        companion_type=args.companion_type,
        medium=medium,
        medium_type=args.medium_type,
        variant=sample_seed % len(INCIDENTS),
        rhyme_mode=(sample_seed // len(INCIDENTS)) % len(RHYMES),
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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(seed=base_seed, protagonist="Luna", companion="Theo", medium="Aunt Mira"),
            StoryParams(seed=base_seed + 1, protagonist="Ivy", companion="Pip", medium="Aunt June"),
            StoryParams(seed=base_seed + 2, protagonist="Mara", companion="Owen", medium="Miss Sol"),
            StoryParams(seed=base_seed + 3, protagonist="Nell", companion="Sam", medium="Mara's Nana"),
        ]
        for index, params in enumerate(curated):
            params.variant = index % len(INCIDENTS)
            params.rhyme_mode = index % len(RHYMES)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            sample_seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(sample_seed), sample_seed)
                params.seed = sample_seed
                sample = generate(params)
            except StoryError:
                continue
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
        header = f"### variant {index + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
