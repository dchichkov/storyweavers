#!/usr/bin/env python3
"""
A small fairy-tale storyworld about Ferris learning that friendship matters,
even after a bad ending.
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
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None


@dataclass
class StoryParams:
    name: str = "Ferris"
    friend: str = "Pip"
    creature: str = "fox"
    treasure: str = "moonberry crown"
    lesson: str = "friendship"
    ending: str = "bad_ending"
    style: str = "fairy_tale"
    seed: Optional[int] = None


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


NAMES = ["Ferris", "Luna", "Milo", "Tansy", "Orin"]
FRIENDS = ["Pip", "Nell", "Bram", "Daisy", "Rowan"]
CREATURES = ["fox", "badger", "rabbit", "raven"]
TREASURES = ["moonberry crown", "silver acorn", "glass slipper", "sunlit key"]


def validate(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("Ferris needs a name.")
    if params.name.lower() != "ferris":
        raise StoryError("This canonical fairy tale requires the hero to be Ferris.")
    if params.friend.lower() == params.name.lower():
        raise StoryError("Ferris and the friend must be different characters.")
    if params.lesson != "friendship":
        raise StoryError("This story's lesson must be friendship.")
    if params.ending != "bad_ending":
        raise StoryError("This trial must keep its bad ending.")
    if params.style != "fairy_tale":
        raise StoryError("This story must use Fairy Tale style.")
    if params.creature not in CREATURES:
        raise StoryError(f"Unknown forest creature: {params.creature}.")
    if params.treasure not in TREASURES:
        raise StoryError(f"Unknown treasure: {params.treasure}.")


def build_world(params: StoryParams) -> World:
    validate(params)
    w = World()
    ferris = w.add(Entity(
        id="ferris",
        kind="child",
        label="Ferris",
        meters={"courage": 1.0, "pride": 1.0, "loneliness": 0.0},
        memes={"friendship": 0.0, "lesson": 0.0},
    ))
    friend = w.add(Entity(
        id="friend",
        kind="friend",
        label=params.friend,
        meters={"trust": 1.0, "hurt": 0.0},
        memes={"friendship": 1.0},
    ))
    creature = w.add(Entity(
        id="creature",
        kind="forest_creature",
        label=f"the little {params.creature}",
        meters={"speed": 1.0},
        memes={"forest_wisdom": 1.0},
    ))
    treasure = w.add(Entity(
        id="treasure",
        kind="treasure",
        label=params.treasure,
        owner=None,
        meters={"brightness": 2.0},
        memes={"temptation": 1.0},
    ))
    w.facts.update(
        params=params,
        ferris=ferris,
        friend=friend,
        creature=creature,
        treasure=treasure,
        path="the Briarwood path",
        tower="the crooked wishing tower",
        lesson="A treasure is cold comfort when it costs a friend.",
    )
    return w


def tell(params: StoryParams) -> World:
    w = build_world(params)
    f = w.facts["ferris"]
    friend = w.facts["friend"]
    creature = w.facts["creature"]
    treasure = w.facts["treasure"]
    p = w.facts["params"]

    w.say(
        f"Once, beneath a moon as round as a silver plate, Ferris walked the Briarwood path "
        f"with {friend.label}, who was his dearest friend."
    )
    w.say(
        f"At the crooked wishing tower, a little {p.creature} showed them a {p.treasure} "
        f"glowing on a stone step."
    )
    w.para()

    f.meters["pride"] += 1
    f.meters["loneliness"] += 1
    w.say(
        f'"I found it first," said Ferris, clutching the {p.treasure}. '
        f'"Then it should be mine alone."'
    )
    w.say(
        f'"Please wait," said {friend.label}. "The tower bridge is broken, and I know a safer way."'
    )
    w.say(
        f'Ferris shook his head. "I can reach the gate faster without stopping for anyone."'
    )
    w.say(
        f"The little {p.creature} flicked its tail. \"Fast feet do not always find a good road,\" it warned."
    )
    w.para()

    f.meters["courage"] += 1
    f.meters["pride"] += 1
    friend.meters["hurt"] += 1
    friend.meters["trust"] -= 1
    w.say(
        f"Ferris hurried into the tower. He crossed the cracked bridge, but the {p.treasure} "
        f"grew heavy in his hands."
    )
    w.say(
        f"Behind him, {friend.label} called, \"Ferris, take my hand! We can carry it together!\""
    )
    w.say(
        f'"I do not need help!" Ferris shouted. The bridge groaned, and he ran on alone.'
    )
    w.say(
        f"At the tower gate, the {p.treasure} turned to a lump of gray stone. The gate slammed shut, "
        f"and the path behind him filled with thorns."
    )
    w.para()

    w.say(
        f"Ferris pressed his palms to the cold gate. " 
        f'"Open, please!" he begged. "I will share the treasure now."'
    )
    w.say(
        f"The little {p.creature} answered, \"A promise after a hurt is a seed. It still needs time to grow.\""
    )
    w.say(
        f"Ferris looked back. {friend.label} stood safely beyond the thorns, but the friend would not come closer."
    )
    w.say(
        f'"I was afraid of losing the treasure," Ferris said. "But I lost something better."'
    )
    w.say(
        f'"You lost my trust," said {friend.label}. "You may earn it again, one careful choice at a time."'
    )
    w.para()

    f.meters["pride"] -= 1
    f.meters["loneliness"] += 1
    f.memes["friendship"] += 1
    f.memes["lesson"] += 1
    treasure.memes["temptation"] = 0
    w.say(
        f"The tower kept its gray stone, and the moonberry crown never shone again. "
        f"It was a truly bad ending for Ferris's greedy quest."
    )
    w.say(
        f"Yet Ferris did not blame the thorns. He gave {friend.label} his best walking stick "
        f"and began clearing a new path, slowly, without asking for praise."
    )
    w.say(
        f"The little {p.creature} watched from a fern as Ferris learned the lesson: "
        f"{w.facts['lesson']}"
    )
    w.say(
        f"That night, Ferris walked home alone beneath the pale moon, carrying no treasure, "
        f"but carrying the first honest step toward friendship."
    )
    return w


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    friend = world.facts["friend"]
    creature = world.facts["creature"]
    treasure = world.facts["treasure"]
    return [
        QAItem(
            question=f"What did Ferris find with {friend.label} on the Briarwood path?",
            answer=f"Ferris found a {p.treasure} glowing on a stone step at the crooked wishing tower."
        ),
        QAItem(
            question=f"Why did {friend.label} become hurt during Ferris's quest?",
            answer=f"{friend.label} became hurt because Ferris refused the offered help and hurried into the tower alone."
        ),
        QAItem(
            question=f"What warning did the little {p.creature} give Ferris?",
            answer=f"The little {p.creature} warned that fast feet do not always find a good road."
        ),
        QAItem(
            question="What lesson did Ferris learn from the bad ending?",
            answer="Ferris learned that a treasure is cold comfort when it costs a friend, and that friendship matters more than owning something bright."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a caring bond in which people help, trust, and listen to one another."
        ),
        QAItem(
            question="What is a lesson learned in a story?",
            answer="A lesson learned is an idea a character understands after an important choice or consequence."
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a story that may include magic, talking creatures, quests, and a meaningful ending."
        ),
        QAItem(
            question="Can a bad ending still teach something useful?",
            answer="Yes. A bad ending can show the consequence of a poor choice and help a character choose better later."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a Fairy Tale about Ferris, a {p.creature}, and a {p.treasure}.",
        "Include a Lesson Learned about Friendship and a clear Bad Ending.",
        "Use dialogue in which a friend warns Ferris, and end with Ferris beginning to repair the friendship.",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("hero", "ferris"),
        asp.fact("feature", "lesson_learned"),
        asp.fact("feature", "friendship"),
        asp.fact("feature", "bad_ending"),
        asp.fact("style", "fairy_tale"),
        asp.fact("requires", "dialogue"),
        asp.fact("requires", "consequence"),
    ])


ASP_RULES = r"""
compatible_story :-
    hero(ferris),
    feature(lesson_learned),
    feature(friendship),
    feature(bad_ending),
    style(fairy_tale),
    requires(dialogue),
    requires(consequence).
"""


def asp_program(show: str = "#show compatible_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if not asp.atoms(model, "compatible_story"):
        print("MISMATCH: ASP gate failed.")
        return 1
    for seed in range(3):
        sample = generate(StoryParams(seed=seed))
        if "Ferris" not in sample.story or "friend" not in sample.story.lower():
            print("MISMATCH: generated story exercise failed.")
            return 1
    print("OK: ASP gate and generated-story checks passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ferris's friendship fairy-tale storyworld.")
    parser.add_argument("--name", default="Ferris")
    parser.add_argument("--friend", choices=FRIENDS, default=None)
    parser.add_argument("--creature", choices=CREATURES, default=None)
    parser.add_argument("--treasure", choices=TREASURES, default=None)
    parser.add_argument("--lesson", choices=["friendship"], default="friendship")
    parser.add_argument("--ending", choices=["bad_ending"], default="bad_ending")
    parser.add_argument("--style", choices=["fairy_tale"], default="fairy_tale")
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
    return StoryParams(
        name=args.name,
        friend=args.friend or rng.choice(FRIENDS),
        creature=args.creature or rng.choice(CREATURES),
        treasure=args.treasure or rng.choice(TREASURES),
        lesson=args.lesson,
        ending=args.ending,
        style=args.style,
        seed=args.seed,
    )


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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for entity in sample.world.entities.values():
            meters = {k: v for k, v in entity.meters.items() if v}
            memes = {k: v for k, v in entity.memes.items() if v}
            print(f"{entity.label}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(friend="Pip", creature="fox", treasure="moonberry crown"),
    StoryParams(friend="Nell", creature="badger", treasure="silver acorn"),
    StoryParams(friend="Bram", creature="raven", treasure="sunlit key"),
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
        print(asp.atoms(model, "compatible_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        seen: set[str] = set()
        for i in range(max(args.n, 1) * 20):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            params = resolve_params(args, rng)
            params.seed = base_seed + i
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
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
