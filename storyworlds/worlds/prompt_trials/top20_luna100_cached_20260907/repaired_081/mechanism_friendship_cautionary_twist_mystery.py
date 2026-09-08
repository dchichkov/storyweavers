#!/usr/bin/env python3
"""
A small mystery storyworld about a friendship, a hidden mechanism, and a
cautionary twist.
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
sys.path.insert(0, str(ROOT / "storyworlds"))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    hero_name: str = "Luna"
    friend_name: str = "Mira"
    object_name: str = "the little brass box"
    mystery: str = "a bell ringing inside the locked garden shed"
    telling_mode: str = "mystery opening"
    seed: Optional[int] = None


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    lines: list[str] = field(default_factory=list)

    def add(self, entity: Entity) -> None:
        self.entities[entity.id] = entity

    def say(self, text: str) -> None:
        self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


MYSTERIES = {
    "bell": {
        "premise": "Each afternoon, a tiny bell rang inside the locked garden shed.",
        "clue": "Luna noticed a thin copper wire running from the bell to a loose floorboard.",
        "mechanism": "Under the floorboard, they found a wind-up wheel connected to the wire; a draft from the cracked window pulled it just enough to ring.",
        "twist": "The sound had not been a ghostly warning at all. It was an old rain gauge mechanism, built to remind the gardener to check the thirsty plants.",
        "change": "They repaired the wheel, cleared the window, and placed a bright note on the shed door explaining the harmless mechanism.",
        "lesson": "look for a practical cause before deciding that a frightening mystery is dangerous",
        "ending": "That evening the bell rang once in the warm breeze, and Luna and Mira watered the garden together.",
    },
    "lantern": {
        "premise": "A dark lantern in the empty boathouse flashed whenever Luna and Mira walked past.",
        "clue": "Mira saw that the flashes happened when the tide rocked a small chain beneath the pier.",
        "mechanism": "The chain moved a hidden lever, which turned a mirror inside the lantern toward a strip of sunlight.",
        "twist": "The flashing was an old rescue signal, not a warning from someone hiding in the boathouse.",
        "change": "They cleaned the mirror, tied the chain safely, and told the harbor keeper what they had discovered.",
        "lesson": "a strange sign may have a useful history, but it still deserves a careful safety check",
        "ending": "The lantern gave one gentle flash across the water as the friends walked home in daylight.",
    },
    "clock": {
        "premise": "The clock in the closed library ticked loudly only after sunset.",
        "clue": "Luna found fresh dust beside a narrow vent beneath the clock.",
        "mechanism": "Cool air slipped through the vent and turned a tiny paddle attached to the clock's winding key.",
        "twist": "The clock was not counting down to a secret event; it was winding itself whenever the evening air changed.",
        "change": "They blocked the vent with a proper cover and asked the librarian to have the old clock inspected.",
        "lesson": "notice patterns and ask a trusted grown-up before touching an uncertain device",
        "ending": "The library became quiet again, ready for tomorrow's stories.",
    },
}


ASP_RULES = r"""
entity(E) :- entity_name(E).
mechanism_found(M) :- mechanism_name(M), discovered(M).
friendship_safe(A,B) :- friend(A), friend(B), trust(A,B), trust(B,A).
caution_learned(H) :- hero(H), learned(H).
mystery_solved(M) :- mechanism_found(M), explained(M).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("entity_name", "mystery"),
            asp.fact("mechanism_name", "hidden_mechanism"),
            asp.fact("friend", "hero"),
            asp.fact("friend", "friend"),
            asp.fact("hero", "hero"),
            asp.fact("trust", "hero", "friend"),
            asp.fact("trust", "friend", "hero"),
            asp.fact("discovered", "hidden_mechanism"),
            asp.fact("explained", "hidden_mechanism"),
            asp.fact("learned", "hero"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    shown = asp.one_model(
        asp_program(
            "#show mechanism_found/1.\n"
            "#show friendship_safe/2.\n"
            "#show caution_learned/1.\n"
            "#show mystery_solved/1."
        )
    )
    actual = {
        (symbol.name, tuple(
            a.string if a.type == a.type.String
            else a.number if a.type == a.type.Number
            else a.name
            for a in symbol.arguments
        ))
        for symbol in shown
    }
    expected = {
        ("mechanism_found", ("hidden_mechanism",)),
        ("friendship_safe", ("hero", "friend")),
        ("friendship_safe", ("friend", "hero")),
        ("caution_learned", ("hero",)),
        ("mystery_solved", ("hidden_mechanism",)),
    }
    if actual == expected:
        print("OK: ASP and Python parity looks good.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    print("ASP:", sorted(actual))
    print("PY :", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery about friendship, a mechanism, and a cautionary twist."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--object", dest="object_name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    hero = args.name or rng.choice(["Luna", "Nia", "Tessa", "Jo", "Milo"])
    friends = [name for name in ["Mira", "Ari", "Pax", "Zoe", "Finn"] if name != hero]
    friend = args.friend or rng.choice(friends)
    if friend == hero:
        raise StoryError("The friends must have different names.")
    return StoryParams(
        hero_name=hero,
        friend_name=friend,
        object_name=args.object_name or rng.choice(
            ["the little brass box", "the old lantern", "the dusty clock"]
        ),
        mystery=rng.choice(list(MYSTERIES)),
        telling_mode=rng.choice(["mystery opening", "quiet opening", "dialogue opening"]),
    )


def generate(params: StoryParams) -> StorySample:
    if params.mystery not in MYSTERIES:
        raise StoryError(f"Unknown mystery: {params.mystery}")
    if params.hero_name == params.friend_name:
        raise StoryError("Friendship requires two different characters.")

    rng = random.Random(
        params.seed
        if params.seed is not None
        else f"{params.hero_name}:{params.friend_name}:{params.mystery}"
    )
    case = MYSTERIES[params.mystery]
    world = World()

    hero = Entity(
        "hero",
        "character",
        params.hero_name,
        meters={"curiosity": 1.0, "danger": 0.0},
        memes={"worry": 0.0, "trust": 1.0},
    )
    friend = Entity(
        "friend",
        "character",
        params.friend_name,
        meters={"care": 1.0, "danger": 0.0},
        memes={"trust": 1.0, "patience": 1.0},
    )
    object_entity = Entity(
        "mystery_object",
        "thing",
        params.object_name,
        meters={"hidden": 1.0, "risk": 0.0},
        memes={"importance": 1.0},
    )
    world.add(hero)
    world.add(friend)
    world.add(object_entity)

    openings = {
        "mystery opening": f"Nobody knew why the {params.object_name} made a sound after sunset, but {params.hero_name} had begun to listen for it.",
        "quiet opening": f"At dusk, {params.hero_name} and {params.friend_name} walked past the garden and heard the {params.object_name} stir in the dark.",
        "dialogue opening": f'“Did you hear that?” {params.hero_name} whispered when the {params.object_name} sounded again.',
    }
    world.say(openings[params.telling_mode])
    world.say(case["premise"])
    world.say(
        f"{params.hero_name} wanted to open the shed at once, but {params.friend_name} held up a hand."
    )
    world.say(
        f'“We can solve a mystery without rushing into danger,” {params.friend_name} said. '
        f'“Let us look from the doorway first.”'
    )
    world.say(
        f'“You are right,” {params.hero_name} replied. “I will watch, and you can check the path.”'
    )
    world.say(
        f"The friends used a lantern from outside and kept the door between themselves and the dark room."
    )

    hero.meters["curiosity"] += 1.0
    friend.meters["care"] += 1.0
    world.say(case["clue"])
    world.say(
        f"{params.friend_name} pointed to the clue, and {params.hero_name} followed it without touching the loose board."
    )
    world.say(
        f"Together they asked the gardener for permission and waited while the grown-up lifted the board."
    )
    world.say(case["mechanism"])

    object_entity.meters["hidden"] = 0.0
    object_entity.meters["risk"] = 0.0
    object_entity.memes["understood"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["understanding"] = 1.0
    world.facts.update(
        mechanism_found=True,
        mystery_solved=True,
        friendship=True,
        caution=True,
        clue=case["clue"],
        mechanism=case["mechanism"],
    )

    world.say(case["twist"])
    world.say(case["change"])
    world.say(
        f"{params.hero_name} thanked {params.friend_name} for being brave enough to slow the mystery down."
    )
    world.say(
        f"{params.friend_name} smiled. “Friends do not just chase answers. They help each other reach them safely.”"
    )
    world.say(
        f"{params.hero_name} learned the cautionary lesson: {case['lesson']}."
    )
    world.say(case["ending"])

    prompts = [
        f"Write a child-friendly mystery about {params.hero_name} and {params.friend_name}.",
        f"Include a hidden mechanism that explains why {params.object_name} behaves strangely.",
        f"End with a friendship-based cautionary lesson and a surprising twist.",
    ]

    story_qa = [
        QAItem(
            question="What started the mystery?",
            answer=case["premise"],
        ),
        QAItem(
            question="What clue did the friends find?",
            answer=case["clue"],
        ),
        QAItem(
            question="What mechanism caused the strange event?",
            answer=case["mechanism"],
        ),
        QAItem(
            question="What was the twist?",
            answer=case["twist"],
        ),
        QAItem(
            question=f"What cautionary lesson did {params.hero_name} learn?",
            answer=f"{params.hero_name} learned to {case['lesson']}.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a mechanism?",
            answer="A mechanism is a set of connected parts that work together to make something happen.",
        ),
        QAItem(
            question="Why should friends investigate carefully?",
            answer="Careful friends can share clues, avoid unnecessary danger, and make better decisions together.",
        ),
        QAItem(
            question="What is a mystery twist?",
            answer="A mystery twist is a surprising change in what the reader thought was happening.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for key, entity in sample.world.entities.items():
            print(f"{key}: {entity.label} meters={entity.meters} memes={entity.memes}")
        print(f"facts: {sample.world.facts}")
    if qa:
        print("\n== prompts ==")
        for prompt in sample.prompts:
            print(prompt)
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(
            asp_program(
                "#show mechanism_found/1.\n"
                "#show friendship_safe/2.\n"
                "#show caution_learned/1.\n"
                "#show mystery_solved/1."
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for mystery in MYSTERIES:
            params = StoryParams(
                hero_name="Luna",
                friend_name="Mira",
                mystery=mystery,
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n) and attempt < max(50, args.n * 20):
            rng = random.Random(base_seed + attempt)
            params = resolve_params(args, rng)
            params.seed = base_seed + attempt
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            attempt += 1

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
