#!/usr/bin/env python3
"""
Standalone storyworld: a friendship adventure about a shaking afghan and a
mystery to solve.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    location: str = ""
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
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def get(self, entity_id: str) -> Entity:
        if entity_id not in self.entities:
            raise StoryError(f"Unknown entity: {entity_id}")
        return self.entities[entity_id]

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
    friend_name: str
    afghan_name: str = "the Star Path afghan"
    scenario: int = 0
    opening: int = 0
    dialogue: int = 0
    ending: int = 0
    seed: Optional[int] = None


NAMES = ["Luna", "Mira", "Tavi", "Nell", "Oren", "Pia", "Sami", "Wren"]
FRIEND_NAMES = ["Bea", "Jun", "Kai", "Milo", "Zara", "Pip", "Ivy", "Sol"]
GIRL_NAMES = {"Luna", "Mira", "Nell", "Pia", "Bea", "Zara", "Ivy"}
BOY_NAMES = {"Tavi", "Oren", "Sami", "Jun", "Kai", "Milo", "Pip", "Sol"}

SCENARIOS = [
    {
        "place": "the old mountain observatory",
        "mystery": "a brass star token vanished from the cupboard before the night expedition",
        "clue": "a trail of blue wool led from the cupboard toward the windy dome",
        "danger": "the dome door had begun to swing in the storm",
        "discovery": "the token was tucked beneath a loose floor mat, where the wind had pushed it",
        "repair": "they pinned the afghan over the doorway, searched together, and returned the token to its velvet box",
        "result": "the telescope opened, and the friends found the first star of the evening",
        "image": "the afghan rested across both friends' shoulders while starlight shone through the dome",
    },
    {
        "place": "a hidden forest cabin",
        "mystery": "the cabin's tiny silver key disappeared before the friends could enter",
        "clue": "fresh pine needles lay in a line beneath the window",
        "danger": "the trail outside was filling with snow",
        "discovery": "a curious squirrel had carried the key beneath a hollow log",
        "repair": "they wrapped the afghan around the chilly lock box, followed the needles, and freed the key",
        "result": "the cabin door opened just before the path vanished under snow",
        "image": "the warm afghan hung by the fire as two muddy boots rested safely inside the cabin",
    },
    {
        "place": "the lantern bridge above a rushing river",
        "mystery": "the bridge's guiding lantern refused to light",
        "clue": "a faint thread of red wool caught on the lantern hook",
        "danger": "mist was hiding the stepping stones below",
        "discovery": "the lantern wick had slipped into a crack beside the fuel tin",
        "repair": "they used a corner of the afghan as a clean grip, found the wick, and secured it without leaning over the rail",
        "result": "the bridge glowed, showing a safe path to the far bank",
        "image": "the afghan fluttered like a flag while golden lanterns marked the river crossing",
    },
    {
        "place": "the cliffside keeper's hut",
        "mystery": "a map showing the way home had gone missing",
        "clue": "sand sprinkled from the map shelf to a narrow chimney ledge",
        "danger": "wind was rising around the cliff",
        "discovery": "the map had been lifted by a gust and caught behind the chimney stone",
        "repair": "they shook the afghan gently to clear sand, used a pole from the hearth, and pulled the map free together",
        "result": "they could guide the supply boat through the safe channel",
        "image": "the rescued map lay flat beneath the afghan while the sea turned silver below the hut",
    },
]

OPENINGS = [
    "At dawn, Luna and her friend set out while the hills still wore caps of mist.",
    "Before breakfast, the two friends packed courage, a lantern, and one wonderfully soft afghan.",
    "The trail began beneath a sky so blue that even the ravens seemed ready for an adventure.",
    "Rain had washed the path clean, leaving every pebble bright as a secret.",
    "Beyond the last garden gate, the forest whispered as if it knew a mystery was waiting.",
]

DIALOGUES = [
    '"We will solve this together," said {name}. "And we will listen to every clue."',
    '"Do not pull me away from the mystery," said {friend}. "Pull me closer to the truth."',
    '"A good friend shares the search," {name} replied. "Even when the path shakes."',
    '"First we stay safe, then we investigate," said {friend}.',
    '"The clue is small," said {name}, "but small clues can open big doors."',
]

ENDINGS = [
    "They walked home slowly, letting the solved mystery glow between them.",
    "The wind quieted, as though it too was pleased with their teamwork.",
    "From that day on, the afghan was their official adventure blanket.",
    "They laughed so loudly that the nearby crows copied them all the way home.",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A friendship adventure about a shaking afghan and a mystery to solve."
    )
    parser.add_argument("--name")
    parser.add_argument("--friend-name")
    parser.add_argument("--afghan-name", default="the Star Path afghan")
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
    name = args.name or rng.choice(NAMES)
    friend = args.friend_name or rng.choice([x for x in FRIEND_NAMES if x != name] or FRIEND_NAMES)
    return StoryParams(
        name=name,
        friend_name=friend,
        afghan_name=args.afghan_name or "the Star Path afghan",
        scenario=rng.randrange(len(SCENARIOS)),
        opening=rng.randrange(len(OPENINGS)),
        dialogue=rng.randrange(len(DIALOGUES)),
        ending=rng.randrange(len(ENDINGS)),
    )


def build_world(params: StoryParams) -> World:
    scenario = SCENARIOS[params.scenario % len(SCENARIOS)]
    world = World(setting=scenario["place"])
    name_type = "girl" if params.name in GIRL_NAMES else "boy" if params.name in BOY_NAMES else "person"
    friend_type = "girl" if params.friend_name in GIRL_NAMES else "boy" if params.friend_name in BOY_NAMES else "person"
    world.add(Entity("Luna", kind="character", type=name_type, label=params.name, location=scenario["place"]))
    world.add(Entity("Friend", kind="character", type=friend_type, label=params.friend_name, location=scenario["place"]))
    world.add(Entity("Afghan", type="blanket", label=params.afghan_name, phrase=params.afghan_name, owner="Luna"))
    world.add(Entity("Mystery", type="clue", label="the mystery", location=scenario["place"]))
    world.facts.update(params=params, scenario=scenario, solved=False, friendship="strong")
    return world


def tell(world: World) -> None:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    hero = world.get("Luna")
    friend = world.get("Friend")
    afghan = world.get("Afghan")

    world.say(OPENINGS[params.opening % len(OPENINGS)])
    world.say(
        f"{hero.label} and {friend.label} carried {afghan.phrase} toward {scenario['place']}. "
        f"It was a patchwork afghan with stars, rivers, and little red doors sewn into it."
    )
    world.say(f"They had a mystery to solve: {scenario['mystery']}.")
    world.para()

    hero.memes["curious"] = 1
    friend.memes["brave"] = 1
    afghan.meters["shaking"] = 1
    world.say(f"The wind made the afghan shake, and {scenario['danger']}.")
    world.say(DIALOGUES[params.dialogue % len(DIALOGUES)].format(name=hero.label, friend=friend.label))
    world.say(f"They did not rush. Instead, they noticed that {scenario['clue']}.")
    world.say(
        f"{hero.label} held one corner of the afghan while {friend.label} followed the clue. "
        f"Together, they discovered that {scenario['discovery']}."
    )
    world.para()

    afghan.meters["shaking"] = 0
    afghan.meters["anchored"] = 1
    world.say(f"They {scenario['repair']}.")
    world.say(f"Then {scenario['result']}.")
    world.facts["solved"] = True
    world.facts["clue"] = scenario["clue"]
    world.facts["discovery"] = scenario["discovery"]
    world.facts["repair"] = scenario["repair"]
    world.say(
        f"{hero.label} and {friend.label} smiled at each other. The mystery had been solved, "
        "but their friendship had become the brightest part of the adventure."
    )
    world.para()
    world.say(f"In the final picture, {scenario['image']}.")
    world.say(ENDINGS[params.ending % len(ENDINGS)])


def generation_prompts(world: World) -> list[str]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        f"Write an adventure for children about {params.name}, {params.friend_name}, and an afghan that begins to shake.",
        f"Tell a Mystery to Solve story set at {scenario['place']}, using this clue: {scenario['clue']}.",
        "Show how friendship changes the adventure through honest dialogue, careful observation, and teamwork.",
    ]


def story_qa(world: World) -> list[QAItem]:
    params: StoryParams = world.facts["params"]
    scenario = world.facts["scenario"]
    return [
        QAItem(
            question="What mystery did the friends need to solve?",
            answer=f"They needed to solve the mystery of {scenario['mystery'].replace('a ', '', 1)}.",
        ),
        QAItem(
            question="Why did the afghan shake?",
            answer=f"The afghan shook because the wind was rising while the friends were at {scenario['place']}.",
        ),
        QAItem(
            question="What clue helped the friends?",
            answer=f"They noticed that {scenario['clue']}. This small detail showed them where to search.",
        ),
        QAItem(
            question=f"How did {params.name} and {params.friend_name} work as friends?",
            answer=f"They worked together when {scenario['repair']}. Sharing the search helped them solve the mystery safely.",
        ),
        QAItem(
            question="What happened after the mystery was solved?",
            answer=f"{scenario['result']}. The friends also felt closer because they had faced the adventure together.",
        ),
        QAItem(
            question="What final image showed the change?",
            answer=f"The ending showed that {scenario['image']}. The calm afghan and the safe scene showed that the danger was over.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an afghan?",
            answer="An afghan is a warm blanket, often made from knitted or crocheted pieces.",
        ),
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a question or hidden problem that people investigate using clues.",
        ),
        QAItem(
            question="Why is friendship useful during an adventure?",
            answer="Friendship is useful because friends can share ideas, encourage one another, and stay safer by working together.",
        ),
        QAItem(
            question="What does a clue do?",
            answer="A clue gives information that helps someone understand what happened or decide where to look.",
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
    lines = ["--- world trace ---", f"setting: {world.setting}"]
    for entity in world.entities.values():
        details = []
        if entity.meters:
            details.append(f"meters={entity.meters}")
        if entity.memes:
            details.append(f"memes={entity.memes}")
        lines.append(f"{entity.id}: {' '.join(details) if details else '(quiet)'}")
    lines.append(f"solved: {world.facts.get('solved', False)}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_search :- friendship, clue.
solved :- clue, teamwork.
calm_afghan :- anchored.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("friendship"),
            asp.fact("clue"),
            asp.fact("teamwork"),
            asp.fact("anchored"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(
        asp_program("#show safe_search/0. #show solved/0. #show calm_afghan/0.")
    )
    names = {f"{atom.name}/{len(atom.arguments)}" for atom in model}
    required = {"safe_search/0", "solved/0", "calm_afghan/0"}
    if not required.issubset(names):
        raise StoryError("ASP parity failed: expected friendship, clue, teamwork, and anchored rules.")
    for params in CURATED:
        sample = generate(params)
        if not sample.world or not sample.world.facts.get("solved"):
            raise StoryError("Python generation failed to solve a curated mystery.")
        if "afghan" not in sample.story.lower() or "friend" not in sample.story.lower():
            raise StoryError("Generated story lost required domain language.")
    print("OK: ASP and Python story checks passed.")
    return 0


def asp_valid() -> str:
    return asp_program("#show safe_search/0. #show solved/0. #show calm_afghan/0.")


CURATED = [
    StoryParams(name="Luna", friend_name="Bea", afghan_name="the Star Path afghan", scenario=0, opening=0, dialogue=0, ending=0),
    StoryParams(name="Mira", friend_name="Jun", afghan_name="the Blue River afghan", scenario=1, opening=2, dialogue=3, ending=1),
    StoryParams(name="Tavi", friend_name="Zara", afghan_name="the Red Door afghan", scenario=3, opening=4, dialogue=2, ending=3),
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
        print(asp_program("#show safe_search/0. #show solved/0. #show calm_afghan/0."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        print("\n".join(str(atom) for atom in asp.one_model(asp_valid())))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for index in range(max(args.n, 0)):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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
        header = ""
        if args.all:
            header = f"### {sample.params.name} and {sample.params.friend_name}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
