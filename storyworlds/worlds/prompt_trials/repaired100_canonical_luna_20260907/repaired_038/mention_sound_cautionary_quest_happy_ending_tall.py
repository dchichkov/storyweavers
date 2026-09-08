#!/usr/bin/env python3
"""
A tall tale about Luna, a careful sound-seeker who learns that a warning is
worth hearing before a grand quest begins.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from results import QAItem, StoryError, StorySample


@dataclass(frozen=True)
class Bell:
    id: str
    name: str
    sound: str
    home: str
    secret: str
    danger: str
    safe_method: str
    happy_result: str


BELLS = {
    "moon_bell": Bell(
        "moon_bell",
        "the Moon Bell",
        "BOOOONG!",
        "the tallest hill",
        "it rings only when someone tells the truth",
        "its echo can loosen stones from the hill",
        "a padded mallet and three quiet steps",
        "its golden note guides every lost traveler home",
    ),
    "cloud_bell": Bell(
        "cloud_bell",
        "the Cloud Bell",
        "DING-a-drum!",
        "a tower above the clouds",
        "it answers a kind mention with a silver echo",
        "its thunderous answer can scatter the town's laundry",
        "a soft wool rope and a spoken thank-you",
        "its little rain song waters the valley gardens",
    ),
    "river_bell": Bell(
        "river_bell",
        "the River Bell",
        "KLOP-KLANG!",
        "a bridge over the roaring river",
        "it sounds when a brave helper is mentioned by name",
        "its vibration can shake loose the bridge planks",
        "a steady hand on the rope and a slow count to five",
        "its rhythm helps boats find the safe channel",
    ),
    "forest_bell": Bell(
        "forest_bell",
        "the Forest Bell",
        "WHOOM-whistle!",
        "an oak wider than a barn",
        "it repeats the name of anyone who listens carefully",
        "its booming reply can frighten birds from their nests",
        "a felt clapper and a whisper",
        "its gentle call brings the birds back at sunset",
    ),
}

TOOLS = {
    "mallet": ("a padded mallet", "tap the bell without striking it hard"),
    "rope": ("a soft wool rope", "hold the bell steady from a safe distance"),
    "clapper": ("a felt clapper", "make a quiet sound instead of a boom"),
}

NAMES = ["Luna", "Mara", "Tavi", "Pip", "Nell", "Orin"]
ROLES = ["small explorer", "young drummer", "village helper", "curious child"]
OPENINGS = [
    "Long ago, when hills wore hats of mist",
    "On a morning so bright that shadows wore sunglasses",
    "In the great valley of Gigglegrass",
    "When the village clock had just sneezed twelve times",
    "At the edge of a kingdom taller than a mountain",
]
MENTIONS = [
    "The mayor mentioned that the bell had gone quiet.",
    "An old shepherd mentioned that the bell was waiting for a careful listener.",
    "Luna's grandmother mentioned the bell while buttering a toast as wide as a door.",
    "A flock of blue geese mentioned the bell by honking its name.",
]
LESSONS = [
    "A warning is not a wall against adventure; it is a map for traveling wisely.",
    "The bravest quest is sometimes the one that slows down before it begins.",
    "A loud answer is not always a better answer.",
    "Careful listening can make a tall tale end safely.",
]


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    bell: Bell
    tool: str
    hero: Entity
    guide: Entity
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    bell: str
    tool: str
    name: str
    role: str
    opening: int
    mention: int
    lesson: int
    seed: Optional[int] = None


def _entity(world: World, eid: str) -> Entity:
    return world.entities[eid]


def tell(params: StoryParams) -> World:
    bell = BELLS[params.bell]
    tool_name, tool_action = TOOLS[params.tool]
    hero = Entity(params.name, "character", params.name)
    guide = Entity("guide", "character", "the old guide")
    world = World(bell, params.tool, hero, guide)
    world.entities = {
        hero.id: hero,
        guide.id: guide,
        bell.id: Entity(bell.id, "object", bell.name),
    }
    world.facts.update(
        bell=bell,
        tool=tool_name,
        tool_action=tool_action,
        hero=hero,
        guide=guide,
        lesson=LESSONS[params.lesson % len(LESSONS)],
    )

    world.say(
        f"{OPENINGS[params.opening % len(OPENINGS)]}, {params.name}, a {params.role}, "
        f"lived in a village where even spoons had heroic opinions."
    )
    world.say(MENTIONS[params.mention % len(MENTIONS)])
    world.say(
        f"The mention pointed toward {bell.home}, where {bell.name} had not made a sound "
        f"for seven whole market days."
    )
    world.para()
    world.say(
        f'"I shall find the missing sound!" cried {params.name}. '
        f'"That is a quest worthy of a very tall person, even if I am not tall yet."'
    )
    world.say(
        f'The old guide raised one finger. "I mention one caution: {bell.danger}. '
        f"Use {tool_name}, and listen before you act.\""
    )
    world.say(
        f'"I heard the caution," said {params.name}, "but I will remember it better once I am moving."'
    )
    world.para()

    hero.meters["hurry"] = 1.0
    hero.memes["excitement"] = 1.0
    guide.memes["worry"] = 1.0
    world.fired.add("warning")
    world.say(
        f"{params.name} hurried up the path, waving a hand at {bell.name}. "
        f"The hand brushed its rim."
    )
    world.say(f"The bell answered with a tremendous {bell.sound}")
    world.say(
        f"{bell.danger.capitalize()} Pebbles bounced, birds flapped, and the quest suddenly "
        "became much less splendid."
    )
    world.para()

    world.say(
        f"{params.name} ducked behind a barrel-sized fern. "
        f'"I acted before I listened," {params.name} admitted. '
        f'"Guide, what did you mean by the caution?"'
    )
    world.say(
        f'The old guide called back, "The bell gives a clue when treated gently. '
        f"Notice what changes when you stop.\""
    )
    world.say(
        f"{params.name} stopped. The echo faded. Beneath it came a tiny second sound, "
        f"like a mouse applauding: {bell.secret}."
    )
    world.say(
        f'"Then the sound is asking for patience," said {params.name}. '
        f'"I choose the safer method."'
    )
    world.para()

    world.say(
        f"{params.name} took {tool_name}, followed the guide's directions to "
        f"{tool_action}, and counted three quiet breaths."
    )
    hero.meters["hurry"] = 0.0
    hero.meters["care"] = 1.0
    hero.memes["worry"] = 0.0
    hero.memes["confidence"] = 1.0
    guide.memes["relief"] = 1.0
    world.fired.add("safe_action")
    world.say(
        f"This time the bell gave a small, friendly sound: {bell.sound.lower()} "
        "The stones settled, the birds returned, and the path became safe."
    )
    world.say(
        f"{bell.happy_result.capitalize()} The village cheered so loudly that three hats "
        "flew into next Tuesday."
    )
    world.para()
    world.say(
        f'The old guide smiled. "{world.facts["lesson"]}" '
        f"{params.name} carried the lesson home, along with the gentlest echo in the kingdom."
    )
    world.facts["resolved"] = True
    world.facts["cautionary"] = True
    world.facts["happy_ending"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(bell, tool) for bell in BELLS for tool in TOOLS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    bell = args.bell or rng.choice(sorted(BELLS))
    tool = args.tool or rng.choice(sorted(TOOLS))
    if (bell, tool) not in valid_combos():
        raise StoryError("That bell and tool do not make a reasonable quest.")
    return StoryParams(
        bell=bell,
        tool=tool,
        name=args.name or rng.choice(NAMES),
        role=args.role or rng.choice(ROLES),
        opening=rng.randrange(len(OPENINGS)),
        mention=rng.randrange(len(MENTIONS)),
        lesson=rng.randrange(len(LESSONS)),
    )


def generation_prompts(world: World) -> list[str]:
    bell: Bell = world.bell
    return [
        f"Write a tall tale about {bell.name}, its sound {bell.sound}, and a cautionary quest.",
        f"Tell a happy-ending story in which {world.hero.label} mentions and then safely investigates {bell.name}.",
        f"Create a child-facing quest where listening changes a dangerous choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    bell = world.bell
    hero = world.hero.label
    return [
        QAItem(
            f"Who went on the quest to find the missing sound?",
            f"{hero}, a {world.facts['hero'].kind}, went on the quest to find the missing sound of {bell.name}.",
        ),
        QAItem(
            f"What caution did the old guide mention?",
            f"The guide mentioned that {bell.danger}, so the bell needed to be approached with care.",
        ),
        QAItem(
            f"What sound did the bell make when {hero} hurried?",
            f"{bell.name} made the enormous sound {bell.sound}, which disturbed the hill and startled nearby creatures.",
        ),
        QAItem(
            f"What clue helped {hero} understand the bell?",
            f"When {hero} stopped, the echo faded and the bell revealed that {bell.secret}.",
        ),
        QAItem(
            f"How did {hero} finish the quest safely?",
            f"{hero} used {world.facts['tool']} and {world.facts['tool_action']}, allowing the stones and birds to settle.",
        ),
        QAItem(
            "How did the story end happily?",
            f"{bell.happy_result.capitalize()} The village celebrated because the bell was safe and its useful sound had returned.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "Why should a person listen to a caution?",
            "A caution can reveal a risk and suggest a safer way to continue.",
        ),
        QAItem(
            "What is a quest?",
            "A quest is a purposeful journey to find, help, learn, or solve something.",
        ),
        QAItem(
            "What is a sound?",
            "A sound is a vibration that travels through a material such as air and can be heard.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.label}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
bell(B) :- bell_registry(B).
tool(T) :- tool_registry(T).
quest(B,T) :- bell(B), tool(T).
cautionary(B,T) :- quest(B,T), cautionary_theme.
happy_ending(B,T) :- cautionary(B,T), resolved_ending.
valid_story(B,T) :- happy_ending(B,T).
"""


def asp_facts() -> str:
    import asp

    lines = ["cautionary_theme.", "resolved_ending."]
    for bid, bell in BELLS.items():
        lines.append(asp.fact("bell_registry", bid))
        lines.append(asp.fact("bell_sound", bid, bell.sound))
    for tid in TOOLS:
        lines.append(asp.fact("tool_registry", tid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    actual = set(asp.atoms(model, "valid_story"))
    expected = set(valid_combos())
    if actual == expected:
        print(f"OK: ASP/Python parity verified for {len(expected)} quests.")
        for params in [
            StoryParams("moon_bell", "mallet", "Luna", "small explorer", 0, 0, 0)
        ]:
            sample = generate(params)
            if not sample.story or not sample.story_qa:
                print("Generated story exercise failed.")
                return 1
        print("OK: generated story exercise passed.")
        return 0
    print("ASP/Python mismatch.")
    print("Only Python:", sorted(expected - actual))
    print("Only ASP:", sorted(actual - expected))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Tall cautionary quests with sounds, mentions, and happy endings."
    )
    parser.add_argument("--bell", choices=sorted(BELLS))
    parser.add_argument("--tool", choices=sorted(TOOLS))
    parser.add_argument("--name")
    parser.add_argument("--role", choices=ROLES)
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


CURATED = [
    StoryParams("moon_bell", "mallet", "Luna", "small explorer", 0, 0, 0),
    StoryParams("cloud_bell", "rope", "Mara", "young drummer", 1, 1, 1),
    StoryParams("river_bell", "rope", "Tavi", "village helper", 2, 2, 2),
    StoryParams("forest_bell", "clapper", "Nell", "curious child", 3, 3, 3),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program())
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for index in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            if sample.story not in seen:
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
        if index + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
