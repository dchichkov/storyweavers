#!/usr/bin/env python3
"""
Standalone storyworld: a chipmunk whodunit told through an inner monologue.

A tiny acorn disappears from a woodland pantry. A chipmunk follows clues,
questions friends, and discovers that the mystery is less about a thief than
about a promise made in secret.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            raise StoryError(f"Unknown entity: {eid}")
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    chipmunk_name: str
    helper_name: str
    suspect_name: str
    acorn_name: str = "the Moon-Stripe Acorn"
    case: int = 0
    opening: int = 0
    clue: int = 0
    thought: int = 0
    ending: int = 0
    seed: Optional[int] = None


CASES = [
    {
        "place": "the old oak's pantry",
        "missing": "the Moon-Stripe Acorn",
        "accusation": "a magpie had snatched it for her shiny nest",
        "clue": "three damp fern beads beside the empty shelf",
        "truth": "the acorn had been carried to a hollow stump to feed a shivering field mouse",
        "resolution": "returned the acorn only after finding three ordinary seeds for the mouse",
        "image": "the Moon-Stripe Acorn rested on the pantry shelf while a small seed trail led kindly toward the stump",
        "lesson": "A good detective checks a story before placing blame.",
    },
    {
        "place": "a root cellar beneath the blackberry hedge",
        "missing": "the largest chestnut",
        "accusation": "a badger had rolled it away during the night",
        "clue": "a narrow golden thread caught on the cellar latch",
        "truth": "the chestnut had been tucked beneath a quilt by an old robin who wanted warmth for her eggs",
        "resolution": "moved the chestnut to a safe basket and lined the nest with soft grass instead",
        "image": "the chestnut gleamed in the basket as the robin's nest swayed safely above it",
        "lesson": "A clue can reveal a need hiding underneath a mistake.",
    },
    {
        "place": "the mossy bridge pantry",
        "missing": "a red-capped hazelnut",
        "accusation": "the twins had taken it to play a rolling game",
        "clue": "a line of tiny paw prints stopped at a puddle",
        "truth": "a young vole had borrowed it as a doorstop while rain rushed through his burrow",
        "resolution": "helped block the leak with bark and let the vole keep a smaller nut for his door",
        "image": "the red-capped hazelnut shone beside the dry burrow while raindrops clicked on the bark roof",
        "lesson": "Solving a mystery can mean solving the trouble that caused it.",
    },
    {
        "place": "the lantern mushroom's storehouse",
        "missing": "the silver-shelled acorn",
        "accusation": "a squirrel from the far hill had crossed the brook to steal it",
        "clue": "silver dust glittered on the floor and on the chipmunk's own whisker",
        "truth": "the chipmunk had hidden it himself while dreaming and forgotten the hiding place",
        "resolution": "found it beneath a loose leaf and made a map of the pantry shelves",
        "image": "the silver-shelled acorn sat under the lantern mushroom while a neat little map hung nearby",
        "lesson": "An honest detective must investigate every suspect, even himself.",
    },
]

OPENINGS = [
    "At dawn, the forest wore a coat of dew, and every spiderweb looked like a tiny locked window.",
    "Before breakfast, the oak trees whispered so loudly that the chipmunks suspected a secret meeting.",
    "A pale moon still hung above the bracken when the pantry bell gave one mysterious ping.",
    "Rain had just stopped, leaving the woodland shiny enough to reflect every suspicious footprint.",
    "The afternoon sun made long bars of light across the roots, like a detective's office with no walls.",
]

THOUGHTS = [
    "I must not let a clever guess dress up as a fact, Luna told herself.",
    "A clue is only useful when I look at it carefully, she thought.",
    "If I accuse the wrong friend, the truth may hide behind hurt feelings.",
    "My whiskers are trembling, but trembling is not proof of guilt.",
    "Perhaps the mystery is asking for patience before it asks for a name.",
]

DIALOGUES = [
    '"I saw the empty shelf," said {chipmunk}. "But I did not see who used it."',
    '"Ask me plainly," said {suspect}. "I would rather answer than be guessed at."',
    '"Then let us follow the clue together," said {helper}.',
    '"I was frightened, not sneaky," said {suspect}.',
    '"The truth should help someone, not merely win a puzzle," said {chipmunk}.',
]

ENDINGS = [
    "That night, Luna slept beside the pantry door, and her dreams had no locked windows.",
    "The forest kept the case's secret, but it repeated the lesson in every rustling leaf.",
    "From then on, the chipmunks called careful questions the gentlest kind of courage.",
    "The pantry bell never rang again without Luna checking the shelf, the floor, and her own memory.",
    "By sunset, the mystery was solved, and the woodland felt larger because everyone had made room for the truth.",
]

NAMES = ["Luna", "Pip", "Milo", "Clover", "Nell", "Tansy", "Bram", "Juniper"]
HELPERS = ["Otis", "Mira", "Fern", "Puck", "Hazel", "Wren"]
SUSPECTS = ["Mara", "Basil", "Nico", "Olive", "Rook", "Toby"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A chipmunk whodunit with an inner monologue.")
    parser.add_argument("--chipmunk-name")
    parser.add_argument("--helper-name")
    parser.add_argument("--suspect-name")
    parser.add_argument("--acorn-name", default="the Moon-Stripe Acorn")
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
    chipmunk = args.chipmunk_name or rng.choice(NAMES)
    helper = args.helper_name or rng.choice([n for n in HELPERS if n != chipmunk])
    suspect = args.suspect_name or rng.choice([n for n in SUSPECTS if n not in {chipmunk, helper}])
    return StoryParams(
        chipmunk_name=chipmunk,
        helper_name=helper,
        suspect_name=suspect,
        acorn_name=args.acorn_name,
        case=rng.randrange(len(CASES)),
        opening=rng.randrange(len(OPENINGS)),
        clue=rng.randrange(5),
        thought=rng.randrange(len(THOUGHTS)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    world = World()
    chipmunk = world.add(Entity("Chipmunk", "character", "girl", params.chipmunk_name))
    helper = world.add(Entity("Helper", "character", "person", params.helper_name))
    suspect = world.add(Entity("Suspect", "character", "person", params.suspect_name))
    acorn = world.add(Entity("Acorn", "object", "acorn", params.acorn_name))
    pantry = world.add(Entity("Pantry", "place", "pantry", "the pantry"))
    world.facts.update(
        params=params,
        chipmunk=chipmunk,
        helper=helper,
        suspect=suspect,
        acorn=acorn,
        pantry=pantry,
    )
    return world


def tell(world: World) -> None:
    params: StoryParams = world.facts["params"]
    chipmunk: Entity = world.facts["chipmunk"]
    helper: Entity = world.facts["helper"]
    suspect: Entity = world.facts["suspect"]
    case = CASES[params.case % len(CASES)]
    world.facts["case"] = case

    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"{chipmunk.label} the chipmunk kept the pantry ledger for {case['place']}. "
        f"She knew every seed, shell, and crumb, so she noticed at once that {case['missing']} was gone."
    )
    world.say(
        f"The empty place looked as serious as a black hole in the middle of the shelf. "
        f"{chipmunk.label} narrowed her eyes and began a quiet investigation."
    )

    world.para()
    world.say(f"Her first thought slipped through her mind: “{THOUGHTS[params.thought % len(THOUGHTS)]}”")
    world.say(
        f"{chipmunk.label} considered {case['accusation']}. "
        f"That was a possible story, but a possible story was not yet the truth."
    )
    world.say(f"She found the first clue: {case['clue']}.")
    world.say(
        f"{helper.label} arrived with a leaf notebook. “{DIALOGUES[params.clue % len(DIALOGUES)].format(chipmunk=chipmunk.label, helper=helper.label, suspect=suspect.label)}”
    )
    world.say(
        f"“{chipmunk.label}, I found {suspect.label} near the pantry,” {helper.label} added. "
        f"“But being nearby is not the same as taking anything.”"
    )

    world.para()
    world.say(
        f"{chipmunk.label} followed the clue instead of the rumor. "
        f"At the end of the trail, she discovered that {case['truth']}."
    )
    world.say(
        f"“{suspect.label}, did you know about this?” asked {chipmunk.label}. "
        f"“I did,” answered {suspect.label}, “but I was afraid everyone would call me a thief.”"
    )
    world.say(
        f"“Then let us tell the whole truth,” said {helper.label}. "
        f"{chipmunk.label} nodded. Her inner voice answered, “A mystery should end with understanding.”"
    )
    world.say(f"Together, they {case['resolution']}.")
    world.facts.update(
        resolved=True,
        clue=case["clue"],
        truth=case["truth"],
        resolution=case["resolution"],
    )

    world.para()
    world.say(case["lesson"])
    world.say(f"In the final scene, {case['image']}.")
    world.say(ENDINGS[params.ending % len(ENDINGS)])


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    case = world.facts["case"]
    return [
        f"Write a child-friendly whodunit about the chipmunk {params.chipmunk_name}, investigating a missing item.",
        f"Use an inner monologue to show {params.chipmunk_name} questioning an accusation and following the clue: {case['clue']}.",
        f"End with a clear resolution in which the mystery helps {params.chipmunk_name} understand {case['truth']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    case = world.facts["case"]
    return [
        QAItem(
            question="What disappeared from the pantry?",
            answer=f"{case['missing']} disappeared from {case['place']}, leaving an empty place on the shelf.",
        ),
        QAItem(
            question="What clue did the chipmunk discover?",
            answer=f"The chipmunk discovered {case['clue']}. She used that physical clue instead of relying only on a rumor.",
        ),
        QAItem(
            question=f"How did {params.chipmunk_name} use inner thoughts to solve the mystery?",
            answer=f"{params.chipmunk_name} reminded herself that a guess was not proof, so she followed the clue and questioned the story carefully.",
        ),
        QAItem(
            question="What was the real explanation?",
            answer=f"The real explanation was that {case['truth']}. The missing item was not taken for the reason people first imagined.",
        ),
        QAItem(
            question="How was the problem resolved?",
            answer=f"Everyone worked together and {case['resolution']}. They also spoke honestly so the suspect was no longer blamed unfairly.",
        ),
        QAItem(
            question="What final image showed that the case was settled?",
            answer=f"The ending showed that {case['image']}. That image proved both the mystery and the hurt feelings had been repaired.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a chipmunk?",
            answer="A chipmunk is a small striped mammal that gathers and stores food such as seeds and nuts.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story in which someone investigates clues to discover what happened.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private stream of thoughts a character has inside their mind.",
        ),
        QAItem(
            question="Why should a detective check evidence?",
            answer="A detective should check evidence because a quick guess can wrongly blame an innocent person.",
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
        bits = []
        if entity.meters:
            bits.append(f"meters={entity.meters}")
        if entity.memes:
            bits.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {' '.join(bits) if bits else '(quiet)'}")
    lines.append(f"facts: resolved={world.facts.get('resolved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
missing_item.
clue_found.
questioned.
truth_revealed :- clue_found, questioned.
resolved :- truth_revealed.
#show missing_item/0.
#show clue_found/0.
#show questioned/0.
#show truth_revealed/0.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("missing_item"),
            asp.fact("clue_found"),
            asp.fact("questioned"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {symbol.name for symbol in model}
    required = {"missing_item", "clue_found", "questioned", "truth_revealed", "resolved"}
    if not required.issubset(names):
        raise StoryError(f"ASP parity failed; expected {sorted(required)}, got {sorted(names)}")
    for params in CURATED:
        sample = generate(params)
        if not sample.story or not sample.story_qa:
            raise StoryError("Generated verification sample was incomplete")
        if "inner" not in sample.story.lower() and "thought" not in sample.story.lower():
            raise StoryError("Generated story lacks an inner-thought instrument")
    print("OK: Python stories and ASP twin agree on clue, questioning, truth, and resolution.")
    return 0


CURATED = [
    StoryParams("Luna", "Otis", "Mara", case=0, opening=0, clue=0, thought=0, ending=0),
    StoryParams("Pip", "Fern", "Basil", case=1, opening=2, clue=2, thought=2, ending=2),
    StoryParams("Clover", "Wren", "Olive", case=2, opening=3, clue=4, thought=4, ending=4),
    StoryParams("Juniper", "Mira", "Rook", case=3, opening=4, clue=1, thought=1, ending=3),
]


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
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

    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        print("\n".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples: list[StorySample] = []
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

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        if args.all:
            params = sample.params
            header = f"### {params.chipmunk_name}'s case"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        else:
            header = ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
