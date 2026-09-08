#!/usr/bin/env python3
"""
Story world: a bedroom detective story about passion, country, and a ratchet.

Luna's curiosity and passion for a country model lead to a friendship test when
a tiny ratchet disappears. A hurried accusation creates conflict, but careful
clues and honest conversation repair the room and the friendship.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = HERE
while ROOT != os.path.dirname(ROOT):
    if os.path.exists(os.path.join(ROOT, "results.py")):
        break
    ROOT = os.path.dirname(ROOT)
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Character:
    name: str
    role: str
    meters: dict[str, float] = field(default_factory=lambda: {"room": 0.0})
    memes: dict[str, float] = field(
        default_factory=lambda: {
            "friendship": 0.0,
            "curiosity": 0.0,
            "conflict": 0.0,
            "passion": 0.0,
        }
    )


@dataclass
class Object:
    name: str
    kind: str
    owner: str
    location: str
    meters: dict[str, float] = field(default_factory=lambda: {"distance": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"importance": 0.0})
    found: bool = False


@dataclass
class World:
    setting: str
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    characters: dict[str, Character] = field(default_factory=dict)
    objects: dict[str, Object] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def add_character(self, character: Character) -> Character:
        self.characters[character.name] = character
        return character

    def add_object(self, obj: Object) -> Object:
        self.objects[obj.name] = obj
        return obj


@dataclass
class StoryParams:
    seed: Optional[int] = None
    name: str = "Luna"
    friend_name: str = "Milo"
    country: str = "Peru"
    ratchet_name: str = "silver ratchet"
    bedroom: str = "bedroom"


COUNTRIES = ["Peru", "Kenya", "Japan", "Greece", "Brazil", "India"]
NAMES = ["Luna", "Nia", "Tessa", "Mara", "Zuri", "Pia"]
FRIENDS = ["Milo", "Noah", "Sami", "Iris", "Theo", "Ravi"]

ARCS = [
    {
        "key": "blanket_tunnel",
        "clue": "a line of silver dust ran from the model country to the edge of the blanket fort",
        "wrong": "searched Milo's backpack first and announced that the missing tool must be there",
        "consequence": "Milo's face tightened, and the friendship felt as wobbly as the fort",
        "careful": "placed three paper flags along the silver trail and checked each flag in order",
        "cause": "the ratchet had rolled beneath a blanket fold when the model's little bridge was moved",
        "fix": "lifted the blanket with Milo while Luna reached beneath the fold",
        "ending": "the blanket fort became a quiet museum tunnel beside the shining model",
        "lesson": "curiosity should collect evidence before it points a finger",
    },
    {
        "key": "music_box",
        "clue": "the country model's flag made a tiny click whenever the music box played",
        "wrong": "wound the music box again and again, hoping the missing tool would sing out",
        "consequence": "the tune raced, the room grew noisy, and the useful click vanished",
        "careful": "listened to one slow tune and counted the clicks with Milo",
        "cause": "the ratchet had slipped into the music box's open drawer when the model was dusted",
        "fix": "waited for the tune to stop, then opened the drawer with both hands",
        "ending": "the music box played gently while the country flag stood straight",
        "lesson": "patient listening can turn a strange sound into a helpful clue",
    },
    {
        "key": "under_bed_map",
        "clue": "a fresh wrinkle crossed the map beside the bed, exactly where a wheel had rolled",
        "wrong": "dragged the map out quickly and blamed the nearest toy for hiding the tool",
        "consequence": "the map tore at one corner and the real trail became harder to see",
        "careful": "taped the corner, studied the wheel mark, and followed it toward the bed",
        "cause": "the ratchet had rolled under the bed after Luna used it to tighten a tiny wagon",
        "fix": "asked Milo to hold a flashlight while Luna guided a ruler beneath the bed",
        "ending": "the repaired map showed a bright route from the country to the toy wagon",
        "lesson": "repairing a mistake can make careful work possible again",
    },
    {
        "key": "pillow_signal",
        "clue": "two small dents in a pillow matched the teeth of the ratchet",
        "wrong": "shook every pillow at once and shouted that someone had moved the evidence",
        "consequence": "feathers floated through the room and everyone forgot which pillow had dents",
        "careful": "marked the two dents with thread and compared the pillows one at a time",
        "cause": "the ratchet had been tucked under a pillow when the friends built a pretend country station",
        "fix": "opened the marked pillowcase carefully and returned the tool to Luna's work tray",
        "ending": "the pillow station reopened with a neat sign and no feathers in the air",
        "lesson": "a careful comparison is kinder and stronger than a noisy guess",
    },
]

OPENINGS = [
    "Rain tapped the bedroom window while",
    "Late sunlight crossed the bedroom floor as",
    "Just before supper,",
    "A cool breeze stirred the curtains while",
    "The bedroom clock gave a soft tick when",
]

DIALOGUE = [
    (
        '"My passion for this country model makes every missing piece feel enormous," Luna said.',
        '"Then let us make our clues precise," Milo replied. "Friends solve problems together."',
    ),
    (
        '"I am curious, but I am also angry," Luna admitted.',
        '"Tell me what you know and what you only fear," Milo said.',
    ),
    (
        '"I made a fast accusation," Luna said. "I am sorry."',
        '"I was hurt," Milo answered, "but I will help you check the facts."',
    ),
]

ENDINGS = [
    "Luna and Milo labeled the tool tray together, and their friendship felt steadier than before.",
    "The friends drew the solved clue trail on the bedroom wall and laughed at their first wild guess.",
    "Before bedtime, Luna tightened the model's bridge while Milo held the country flag upright.",
]


def build_world(params: StoryParams) -> World:
    if params.bedroom != "bedroom":
        raise StoryError("This storyworld is set in a bedroom.")
    if params.country not in COUNTRIES:
        raise StoryError("Choose a country from the registered country list.")
    if params.name == params.friend_name:
        raise StoryError("The detective and friend need different names.")
    world = World(setting="bedroom")
    hero = world.add_character(Character(params.name, "young detective"))
    friend = world.add_character(Character(params.friend_name, "friend"))
    model = world.add_object(
        Object(
            f"{params.country} country model",
            "country model",
            params.name,
            "desk",
            memes={"importance": 0.9},
        )
    )
    ratchet = world.add_object(
        Object(
            params.ratchet_name,
            "ratchet",
            params.name,
            "tool tray",
            memes={"importance": 1.0},
        )
    )
    world.facts.update(hero=hero, friend=friend, model=model, ratchet=ratchet)
    return world


def narrate_story(world: World, seed: int) -> None:
    rng = random.Random(seed ^ 0xA19E28)
    params = world.facts
    hero: Character = params["hero"]
    friend: Character = params["friend"]
    model: Object = params["model"]
    ratchet: Object = params["ratchet"]
    arc = rng.choice(ARCS)
    opening = rng.choice(OPENINGS)
    hero_line, friend_line = rng.choice(DIALOGUE)
    ending = rng.choice(ENDINGS)

    hero.memes["passion"] = 1.0
    hero.memes["curiosity"] = 1.0
    friend.memes["friendship"] = 1.0
    world.facts.update(arc=arc, ending=ending)

    world.say(f"{opening} {hero.name} inspected the {model.name} on the desk.")
    world.say(
        f"{hero.name} had a deep passion for learning about {model.name}, "
        f"so every bridge, flag, and painted road mattered to the young detective."
    )
    world.say(
        f"When {hero.name} reached for the {ratchet.name}, it was gone. "
        f"The bedroom suddenly felt like a locked case."
    )
    world.say(f"Near the model, {hero.name} noticed {arc['clue']}.")

    world.para()
    world.say(hero_line)
    world.say(friend_line)
    world.say(f"Still, the conflict pulled {hero.name} toward a quick answer: {hero.name} {arc['wrong']}.")
    hero.memes["conflict"] = 1.0
    world.say(f"{arc['consequence']}.")
    world.say(f"Milo stepped back, and the missing {ratchet.name} seemed to grow heavier than a suitcase.")

    world.para()
    world.say(f"Milo took a breath. \"We can disagree without becoming enemies,\" {friend.name} said.")
    world.say(f"Luna looked again. \"You are right. I need to test the clue, not test our friendship.\"")
    world.say(f"Together, they {arc['careful']}.")
    world.say(f"The clue pointed to the cause: {arc['cause']}.")
    hero.memes["curiosity"] = 2.0
    friend.memes["friendship"] = 2.0

    world.para()
    world.say(f"To fix the problem, they {arc['fix']}.")
    ratchet.location = "work tray"
    ratchet.found = True
    world.say(f"The recovered {ratchet.name} flashed in the lamplight.")
    world.say(f"{hero.name} apologized for the accusation, and {friend.name} accepted the apology.")
    world.say(f"They learned that {arc['lesson']}.")
    world.say(f"{arc['ending']}.")
    world.say(ending)


def generation_prompts(world: World) -> list[str]:
    hero: Character = world.facts["hero"]
    model: Object = world.facts["model"]
    ratchet: Object = world.facts["ratchet"]
    return [
        f"Write a Detective Story set in a bedroom about {hero.name}, whose passion is a country model.",
        f"Include a missing {ratchet.name}, strong curiosity, friendship, and conflict resolved through evidence.",
        f"Use the words passion, country, and ratchet naturally in a complete child-facing story.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Character = world.facts["hero"]
    friend: Character = world.facts["friend"]
    model: Object = world.facts["model"]
    ratchet: Object = world.facts["ratchet"]
    arc = world.facts["arc"]
    return [
        QAItem(
            f"What was {hero.name}'s passion?",
            f"{hero.name}'s passion was learning about the {model.name} and caring for its tiny details.",
        ),
        QAItem(
            f"What went missing in the bedroom?",
            f"The missing object was the {ratchet.name}, a tool used with the country model.",
        ),
        QAItem(
            f"How did the conflict between {hero.name} and {friend.name} begin?",
            f"It began when {hero.name} made a quick accusation instead of checking the clues carefully.",
        ),
        QAItem(
            "How did the friends solve the mystery?",
            f"They followed the clue step by step and discovered that {arc['cause']}. Then they worked together to recover the ratchet.",
        ),
        QAItem(
            "What lesson did the detective learn?",
            f"The lesson was that {arc['lesson']}. Honest conversation also helped repair the friendship.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a ratchet?",
            "A ratchet is a tool or mechanism with teeth that helps turn or hold something in one direction.",
        ),
        QAItem(
            "What is curiosity?",
            "Curiosity is a desire to learn more by asking questions and examining what is happening.",
        ),
        QAItem(
            "Why is friendship useful during a conflict?",
            "Friendship can help people speak honestly, listen to one another, and solve a problem without treating each other as enemies.",
        ),
        QAItem(
            "What makes a detective story?",
            "A detective story presents a mystery, clues, mistaken ideas or obstacles, and a careful discovery that explains what happened.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
setting(bedroom).
hero(H) :- hero_name(H).
friend(F) :- friend_name(F).
country_model(C) :- model_name(C).
ratchet(R) :- ratchet_name(R).

mystery(missing_ratchet) :- setting(bedroom), ratchet(_).
curiosity(H) :- hero(H), clue_observed(H).
friendship_repaired(H,F) :- hero(H), friend(F), apology(H), careful_search(H).
conflict(H,F) :- hero(H), friend(F), rushed_accusation(H).
solved(missing_ratchet) :- mystery(missing_ratchet), careful_search(_), ratchet_found.

#show mystery/1.
#show curiosity/1.
#show friendship_repaired/2.
#show conflict/2.
#show solved/1.
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("hero_name", "luna"),
            asp.fact("friend_name", "milo"),
            asp.fact("model_name", "country_model"),
            asp.fact("ratchet_name", "ratchet"),
            asp.fact("clue_observed", "luna"),
            asp.fact("rushed_accusation", "luna"),
            asp.fact("apology", "luna"),
            asp.fact("careful_search", "luna"),
            asp.fact("ratchet_found"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    show = "\n".join(
        [
            "#show mystery/1.",
            "#show curiosity/1.",
            "#show friendship_repaired/2.",
            "#show conflict/2.",
            "#show solved/1.",
        ]
    )
    model = asp.one_model(asp_program(show))
    actual = {(sym.name, tuple(str(arg) for arg in sym.arguments)) for sym in model}
    expected = {
        ("mystery", ("missing_ratchet",)),
        ("curiosity", ("luna",)),
        ("friendship_repaired", ("luna", "milo")),
        ("conflict", ("luna", "milo")),
        ("solved", ("missing_ratchet",)),
    }
    if actual == expected:
        print("OK: ASP gate matches Python story facts.")
        return 0
    print("MISMATCH between ASP and Python facts.")
    print("ASP atoms:", sorted(actual))
    print("Expected:", sorted(expected))
    return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Bedroom detective story about passion, country, ratchet, and friendship."
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
    parser.add_argument("--name", choices=NAMES)
    parser.add_argument("--friend", dest="friend_name", choices=FRIENDS)
    parser.add_argument("--country", choices=COUNTRIES)
    return parser


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([x for x in FRIENDS if x != name])
    country = args.country or rng.choice(COUNTRIES)
    return StoryParams(
        seed=args.seed,
        name=name,
        friend_name=friend,
        country=country,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    narrate_story(world, params.seed if params.seed is not None else 0)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for character in world.characters.values():
        lines.append(
            f"{character.name}: role={character.role} memes={dict(character.memes)}"
        )
    for obj in world.objects.values():
        lines.append(
            f"{obj.name}: kind={obj.kind} owner={obj.owner} "
            f"location={obj.location} found={obj.found}"
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
        print(
            asp_program(
                "\n".join(
                    [
                        "#show mystery/1.",
                        "#show curiosity/1.",
                        "#show friendship_repaired/2.",
                        "#show conflict/2.",
                        "#show solved/1.",
                    ]
                )
            )
        )
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp

        model = asp.one_model(
            asp_program(
                "\n".join(
                    [
                        "#show mystery/1.",
                        "#show curiosity/1.",
                        "#show friendship_repaired/2.",
                        "#show conflict/2.",
                        "#show solved/1.",
                    ]
                )
            )
        )
        for symbol in model:
            print(symbol)
        return

    if args.n < 1:
        raise StoryError("The number of stories must be at least one.")

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(
                seed=base_seed,
                name="Luna",
                friend_name="Milo",
                country="Peru",
            ),
            StoryParams(
                seed=base_seed + 1,
                name="Nia",
                friend_name="Theo",
                country="Japan",
            ),
            StoryParams(
                seed=base_seed + 2,
                name="Mara",
                friend_name="Ravi",
                country="Kenya",
            ),
            StoryParams(
                seed=base_seed + 3,
                name="Zuri",
                friend_name="Iris",
                country="Greece",
            ),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(100, args.n * 30):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
                samples.append(sample)
                seen.add(sample.story)
            index += 1

    if len(samples) < args.n and not args.all:
        raise StoryError("Could not create enough distinct story variants.")

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
