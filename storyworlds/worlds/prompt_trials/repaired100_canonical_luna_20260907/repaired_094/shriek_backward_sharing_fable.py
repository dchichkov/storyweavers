#!/usr/bin/env python3
"""
A small fable about sharing a sound and learning to listen backward.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
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


@dataclass
class StoryParams:
    name: str
    companion: str
    animal: str
    route: int = 0
    seed: Optional[int] = None


NAMES = ["Luna", "Milo", "Tara", "Pip", "Nia", "Oren"]
COMPANIONS = ["Grandma Fern", "Uncle Sol", "Aunt Bea", "Father Rowan", "Mother Mae"]
ANIMALS = ["a small fox", "a patient badger", "a bright crow", "a sleepy hedgehog"]


FABLES = [
    {
        "place": "the hill of echoing stones",
        "gift": "a silver bell",
        "sound": "a sharp shriek",
        "cause": "a hawk's feather had caught in the bell rope",
        "share": "showed the animal how to ring the bell gently",
        "lesson": "A sound becomes less frightening when friends share the truth behind it.",
        "image": "the bell gave one soft note while the fox and Luna watched the sunset together",
    },
    {
        "place": "the old orchard",
        "gift": "a red wooden whistle",
        "sound": "a sudden shriek",
        "cause": "wind had pushed the whistle through a hollow branch",
        "share": "passed the whistle around so every creature could try a quiet tune",
        "lesson": "A treasure grows kinder when it is shared instead of guarded.",
        "image": "the whistle rested in the middle of the picnic blanket, ready for its next friend",
    },
    {
        "place": "the mossy bridge",
        "gift": "a tiny drum",
        "sound": "a squealing shriek",
        "cause": "a loose reed had rubbed against the drum's skin",
        "share": "let the worried animal hold the drum while they fixed the reed",
        "lesson": "Listening backward from an effect to its cause can turn fear into help.",
        "image": "the repaired drum made a warm little beat beneath the bridge",
    },
    {
        "place": "the moonlit garden",
        "gift": "a blue music box",
        "sound": "a piercing shriek",
        "cause": "a thorn had jammed the music box lid",
        "share": "opened the box together and gave each garden friend one turn",
        "lesson": "When we share both work and wonder, a frightening mystery becomes a friendship.",
        "image": "the music box played softly as moths circled like tiny stars",
    },
]


ASP_RULES = r"""
backward_cause :- heard_shriek, examined_source.
shared_gift :- backward_cause, offered_turn.
calm :- shared_gift.
"""


def build_world(params: StoryParams) -> World:
    if not params.name.strip():
        raise StoryError("name must not be empty")
    if not params.companion.strip():
        raise StoryError("companion must not be empty")
    if not params.animal.strip():
        raise StoryError("animal must not be empty")

    fable = FABLES[params.route % len(FABLES)]
    world = World()
    child = world.add(Entity(
        "hero", "child", params.name,
        meters={"steps": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "kindness": 0.0},
    ))
    companion = world.add(Entity(
        "companion", "helper", params.companion,
        meters={"patience": 1.0},
        memes={"wisdom": 1.0},
    ))
    creature = world.add(Entity(
        "creature", "animal", params.animal,
        memes={"fear": 1.0, "trust": 0.0},
    ))
    gift = world.add(Entity(
        "gift", "object", fable["gift"],
        owner=child.id,
        meters={"distance": 0.0},
        memes={"shared": 0.0},
    ))

    world.facts.update(
        hero=child,
        companion=companion,
        creature=creature,
        gift=gift,
        fable=fable,
        place=fable["place"],
        heard_shriek=False,
        examined_source=False,
        backward_cause=False,
        offered_turn=False,
        shared_gift=False,
        calm=False,
    )
    return world


def generate_story(params: StoryParams) -> World:
    world = build_world(params)
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    creature: Entity = f["creature"]
    gift: Entity = f["gift"]
    data = f["fable"]

    world.say(
        f"Once, {hero.label} carried {data['gift']} to {f['place']}, where "
        f"{creature.label} lived beneath a crooked tree."
    )
    world.say(
        f"The creature had never touched such a treasure, but it kept its distance "
        f"until the gift made {data['sound']}."
    )
    f["heard_shriek"] = True
    hero.memes["worry"] += 1.0
    creature.memes["fear"] += 1.0
    world.say(f"{hero.label} stepped backward. “That sound frightened you,” {companion.label} said.")
    world.say(f"“Should I hide the {data['gift']}?” asked {hero.label}. “First, listen backward,” said {companion.label}.")
    world.para()

    world.say(
        f"Together they followed the sound backward, from the startled creature to the "
        f"{data['gift']}, and from the gift to its tangled edge."
    )
    world.say(f"They discovered that {data['cause']}.")
    f["examined_source"] = True
    f["backward_cause"] = True
    hero.meters["steps"] += 3.0
    hero.memes["curiosity"] += 1.0
    creature.memes["fear"] -= 1.0
    world.para()

    world.say(f"{hero.label} did not keep the {data['gift']} tucked under an arm.")
    world.say(f"“Would you like a turn?” {hero.label} asked. “Only if you stay beside me,” said {creature.label}.")
    world.say(f"{hero.label} {data['share']}.")
    f["offered_turn"] = True
    f["shared_gift"] = True
    gift.memes["shared"] = 1.0
    creature.memes["trust"] += 1.0
    hero.memes["kindness"] += 1.0
    world.para()

    world.say(
        f"The {data['gift']} no longer seemed like a monster's voice. "
        f"It became a small gift that friends could understand and share."
    )
    world.say(f"{data['lesson']}")
    world.say(f"At dusk, {data['image']}.")
    f["calm"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly fable about sharing {f['gift'].label} after a shriek at {f['place']}.",
        f"Tell a story in which a child listens backward from a frightening sound to its cause.",
        f"Create a gentle fable showing how sharing changes fear into trust.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    creature: Entity = f["creature"]
    companion: Entity = f["companion"]
    gift: Entity = f["gift"]
    data = f["fable"]
    return [
        QAItem(
            question=f"Why did {creature.label} become afraid?",
            answer=f"{creature.label} became afraid when {gift.label} made {data['sound']}. The sound seemed dangerous until its cause was examined.",
        ),
        QAItem(
            question=f"What did {companion.label} mean by listening backward?",
            answer=f"{companion.label} meant that {hero.label} should follow the frightening sound back to its source instead of guessing what it meant.",
        ),
        QAItem(
            question=f"How did {hero.label} share the gift?",
            answer=f"{hero.label} {data['share']}, so the frightened creature could take a safe turn.",
        ),
        QAItem(
            question="What changed by the end of the fable?",
            answer=f"The sound was understood, the creature's fear became trust, and {gift.label} became something friends could enjoy together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting another person or creature use, enjoy, or help with something instead of keeping it only for yourself.",
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals or nature, that teaches a useful lesson.",
        ),
        QAItem(
            question="What does it mean to listen backward?",
            answer="It means tracing an event from what happened back to the thing that caused it.",
        ),
        QAItem(
            question="What is a shriek?",
            answer="A shriek is a very loud, high sound that can come from fear, surprise, or a noisy object.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id:10} ({entity.kind:8}) "
            f"meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("heard_shriek"),
        asp.fact("examined_source"),
        asp.fact("offered_turn"),
    ])


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle fable about sharing, a shriek, and listening backward."
    )
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--animal")
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--seed", type=int)
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
        companion=args.companion or rng.choice(COMPANIONS),
        animal=args.animal or rng.choice(ANIMALS),
        route=rng.randrange(len(FABLES)),
    )


def generate(params: StoryParams) -> StorySample:
    world = generate_story(params)
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


def asp_verify() -> int:
    import asp
    program = asp_program(
        "#show backward_cause/0.\n#show shared_gift/0.\n#show calm/0."
    )
    model = asp.one_model(program)
    names = {symbol.name for symbol in model}
    expected = {"backward_cause", "shared_gift", "calm"}
    if expected <= names:
        print("OK: ASP twin matches the sharing resolution.")
        return 0
    print("MISMATCH: ASP twin did not derive the expected resolution.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program(
            "#show backward_cause/0.\n#show shared_gift/0.\n#show calm/0."
        ))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program(
            "#show backward_cause/0.\n#show shared_gift/0.\n#show calm/0."
        ))
        print("ASP atoms:", " ".join(sorted(symbol.name for symbol in model)))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = 5 if args.all else max(1, args.n)
    samples: list[StorySample] = []

    for index in range(count):
        seed = base_seed + index
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        samples.append(generate(params))

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
