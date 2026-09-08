#!/usr/bin/env python3
"""
A tiny superhero storyworld about a mysterious correspondence, a brace, and
one very important noun.
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
    kind: str
    label: str
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    seed: Optional[int] = None
    hero_name: str = "Luna"
    sidekick_name: str = "Pip"
    city: str = "Moonbeam City"
    artifact: str = "the Silver Brace"
    scenario_id: int = 0
    telling_mode: int = 0
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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SCENARIOS = [
    {
        "title": "the backward letter",
        "threat": "the villainous Eraser had stolen every noun from the city's signs",
        "signal": "the library sign now said, 'Please return the to the'",
        "stakes": "without nouns, nobody could name the bridge, the bakery, or even the emergency button",
        "clue": "a silver comma glowed wherever the missing words had been taken",
        "action": "raised the brace over the glowing comma",
        "magic": "the brace pulled each lost noun back into its proper sentence",
        "lesson": "words need places, just as heroes need courage",
        "ending": "the city signs shone again, and the bakery proudly remembered that it sold pies",
    },
    {
        "title": "the unsigned message",
        "threat": "a magical correspondence from the future had arrived without its most important noun",
        "signal": "the letter warned, 'Save the before moonrise'",
        "stakes": "the heroes had no idea whether to save the cat, the cake, or the mayor",
        "clue": "the paper smelled like cinnamon and hummed whenever Luna touched the brace",
        "action": "held the brace against the letter",
        "magic": "a bright noun popped out of the parchment and landed with a polite plunk",
        "lesson": "asking a clear question is better than guessing loudly",
        "ending": "the letter revealed that the city needed saving, while Pip saved the cake for later",
    },
    {
        "title": "the runaway adjective",
        "threat": "a spell had made one boastful adjective chase every noun through downtown",
        "signal": "the fountain called itself 'sparkly,' but the pigeons were being called 'sparkly' too",
        "stakes": "the spell would soon rename every citizen Sparkly, including the mayor's dog",
        "clue": "the runaway word always hid behind the nearest noun",
        "action": "placed the brace around the fountain's stone noun",
        "magic": "the brace gently sorted every word back into its sentence",
        "lesson": "small words can cause large confusion when they refuse their proper jobs",
        "ending": "the fountain glittered, the pigeons cooed, and the mayor's dog kept its own name",
    },
]

JOKES = [
    "Pip put on a cape too large for him and immediately became a curtain.",
    "The emergency pigeon saluted, then sneezed into the mayor's hat.",
    "Luna tried a heroic landing and arrived with one boot in a flowerpot.",
    "The magic punctuation mark looked stern until it noticed it was upside down.",
]

FLASHBACKS = [
    "Luna remembered her first lesson from Captain Comma: even a tiny mark could hold a door open for meaning.",
    "For one blinking moment, Luna flashed back to the day she found the brace in a drawer labeled 'miscellaneous heroic equipment.'",
    "She remembered Pip's first rescue, when he saved a dictionary from a rain puddle and declared the dictionary grateful.",
]

WORLD_KNOWLEDGE = [
    QAItem(
        question="What is correspondence?",
        answer="Correspondence is communication, such as letters or messages, exchanged between people.",
    ),
    QAItem(
        question="What is a brace?",
        answer="A brace is something that supports, holds, or strengthens another thing.",
    ),
    QAItem(
        question="What is a noun?",
        answer="A noun is a word that names a person, place, thing, or idea.",
    ),
    QAItem(
        question="Why are nouns useful?",
        answer="Nouns make communication clearer because they tell us what person, place, thing, or idea we mean.",
    ),
]


ASP_RULES = r"""
supports(brace, correspondence).
protects(brace, noun).
requires(clear_message, noun).
magic_solution(brace, correspondence, noun) :-
    supports(brace, correspondence),
    protects(brace, noun),
    requires(clear_message, noun).
valid_story :-
    magic_solution(brace, correspondence, noun).
#show valid_story/0.
"""


def build_world(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    scene = SCENARIOS[params.scenario_id % len(SCENARIOS)]
    world = World()

    hero = world.add(Entity(
        id="hero",
        kind="superhero",
        label=params.hero_name,
        traits=["brave", "magical", "word-wise"],
        meters={"heroism": 1.0, "confusion": 0.0},
        memes={"hope": 1.0, "humor": 0.5},
    ))
    sidekick = world.add(Entity(
        id="sidekick",
        kind="sidekick",
        label=params.sidekick_name,
        traits=["cheerful", "easily distracted"],
        meters={"helpfulness": 0.8},
        memes={"worry": 0.2, "humor": 1.0},
    ))
    brace = world.add(Entity(
        id="brace",
        kind="artifact",
        label=params.artifact,
        traits=["silver", "enchanted"],
        meters={"magic": 1.0},
        memes={"purpose": 1.0},
    ))
    letter = world.add(Entity(
        id="correspondence",
        kind="message",
        label="the mysterious correspondence",
        traits=["glowing", "incomplete"],
        meters={"clarity": 0.2},
        memes={"urgency": 1.0},
    ))

    world.say(
        f"In {params.city}, {hero.label} was the superhero who protected language, "
        f"which was harder than it sounded because language often refused to wear a cape."
    )
    world.say(
        f"{sidekick.label}, the hero's cheerful sidekick, carried {params.artifact}, "
        f"a magical brace that could support a broken sentence."
    )
    world.say(rng.choice(JOKES))

    world.para()
    world.say(f"One bright morning, {scene['threat']}.")
    world.say(f"{scene['signal'].capitalize()}.")
    world.say(f"The trouble was serious: {scene['stakes']}.")
    world.say(f"{sidekick.label} gulped. \"Should I save the cake first?\"")
    world.say(
        f"\"Only if the cake is the noun in danger,\" {hero.label} said. "
        f"\"First, we need to understand the message.\""
    )
    world.say(f"{scene['clue'].capitalize()}.")

    world.para()
    world.say(rng.choice(FLASHBACKS))
    world.say(
        f"The memory gave {hero.label} an idea. "
        f"Instead of blasting the problem with superhero lightning, {hero.label} {scene['action']}."
    )
    world.say(
        f"The {params.artifact.lower()} flashed. {scene['magic'].capitalize()}."
    )
    world.say(
        f"Every missing word rushed home, and the correspondence became clear enough "
        f"for even {sidekick.label} to read without standing on his head."
    )
    world.say(
        f"\"I understand now,\" {sidekick.label} said. "
        f"\"A noun is not just a fancy word for a sandwich.\""
    )
    world.say(
        f"\"Correct,\" said {hero.label}. \"Though a sandwich can be a noun, especially at lunchtime.\""
    )

    world.para()
    hero.meters["heroism"] += 1.0
    hero.meters["confusion"] = 0.0
    hero.memes["hope"] += 1.0
    letter.meters["clarity"] = 1.0
    brace.meters["magic"] = 0.0
    world.say(f"The spell faded, and {scene['lesson'].capitalize()}.")
    world.say(
        f"{sidekick.label} carefully copied the repaired correspondence, "
        f"putting every noun where it belonged."
    )
    world.say(f"When evening came, {scene['ending'].capitalize()}.")
    world.say(
        f"{hero.label} smiled beneath the moonlit clouds, while {sidekick.label} "
        f"gave the brace a snack and was gently reminded that magical tools preferred commas."
    )

    world.facts.update(
        hero=hero,
        sidekick=sidekick,
        brace=brace,
        letter=letter,
        scene=scene,
        resolved=True,
        lesson=scene["lesson"],
        ending=scene["ending"],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a humorous superhero story about correspondence, a magical brace, and a missing noun.",
        f"Tell a child-friendly adventure in which {f['hero'].label} repairs a dangerous message using magic.",
        "Include a flashback, a brief dialogue exchange, and an ending image showing that language has been restored.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    scene = f["scene"]
    return [
        QAItem(
            question=f"What problem did {hero.label} solve?",
            answer=f"{hero.label} solved the problem that {scene['threat']}. The missing or confused nouns made the correspondence unclear and put the city at risk.",
        ),
        QAItem(
            question="How did the magical brace help?",
            answer=f"The magical brace supported the damaged correspondence and {scene['magic']}.",
        ),
        QAItem(
            question=f"What did {sidekick.label} learn about nouns?",
            answer=f"{sidekick.label} learned that a noun names a person, place, thing, or idea, so it helps a message say exactly what is meant.",
        ),
        QAItem(
            question="What did the flashback contribute to the rescue?",
            answer="The flashback reminded the hero that small marks and careful word placement can hold meaning together, which inspired the correct magical repair.",
        ),
        QAItem(
            question="How did the ending prove the problem was fixed?",
            answer=f"The ending showed that {scene['ending']}. The restored signs or message gave concrete proof that the magical repair worked.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_KNOWLEDGE)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp

    return "\n".join([
        asp.fact("supports", "brace", "correspondence"),
        asp.fact("protects", "brace", "noun"),
        asp.fact("requires", "clear_message", "noun"),
    ])


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def python_reasonable(params: StoryParams) -> None:
    if not params.hero_name or not params.sidekick_name:
        raise StoryError("The superhero and sidekick both need names.")
    if params.hero_name == params.sidekick_name:
        raise StoryError("The superhero and sidekick must have different names.")
    if not params.city:
        raise StoryError("The city needs a name.")
    if not params.artifact:
        raise StoryError("The magical brace needs a name.")


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    atoms = set(asp.atoms(model, "valid_story"))
    if atoms == {()}:
        print("OK: ASP gate matches Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP did not find the valid correspondence-brace-noun pattern.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A humorous superhero storyworld about correspondence, a brace, and a noun."
    )
    parser.add_argument("--hero-name")
    parser.add_argument("--sidekick-name")
    parser.add_argument("--city")
    parser.add_argument("--artifact")
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
    names = ["Luna", "Nova", "Mira", "Comet", "Zara"]
    sidekicks = ["Pip", "Bloop", "Dot", "Noodle", "Quill"]
    cities = ["Moonbeam City", "Bright Button Borough", "Comma Cove"]
    artifacts = ["the Silver Brace", "the Golden Word-Brace", "the Moonlit Brace"]

    params = StoryParams(
        seed=None,
        hero_name=args.hero_name or rng.choice(names),
        sidekick_name=args.sidekick_name or rng.choice(sidekicks),
        city=args.city or rng.choice(cities),
        artifact=args.artifact or rng.choice(artifacts),
        scenario_id=rng.randrange(len(SCENARIOS)),
        telling_mode=rng.randrange(4),
        detail_variant=rng.randrange(8),
    )
    python_reasonable(params)
    return params


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:13} ({entity.kind:10}) "
            f"meters={meters} memes={memes} traits={entity.traits}"
        )
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(hero_name="Luna", sidekick_name="Pip", city="Moonbeam City", scenario_id=0),
    StoryParams(hero_name="Nova", sidekick_name="Quill", city="Comma Cove", scenario_id=1),
    StoryParams(hero_name="Mira", sidekick_name="Bloop", city="Bright Button Borough", scenario_id=2),
]


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
        matches = asp.atoms(model, "valid_story")
        print(f"{len(matches)} valid story pattern(s) found.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(
            sample,
            trace=args.trace,
            qa=args.qa,
            header=f"### variant {i + 1}" if len(samples) > 1 else "",
        )
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
