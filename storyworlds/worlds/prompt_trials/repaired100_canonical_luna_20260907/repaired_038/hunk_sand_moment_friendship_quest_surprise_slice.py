#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a friendship quest on a sandy day.

The simulated state follows a child and a friend as they search for a missing
sand-castle flag. A surprising hunk of wet sand reveals that the quest is not
about winning, but about noticing one another's help.
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass(frozen=True)
class SandSpot:
    id: str
    label: str
    clue: str


@dataclass(frozen=True)
class Quest:
    id: str
    title: str
    object_name: str
    object_phrase: str
    surprise: str
    ending: str


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[str] = field(default_factory=set)

    def add(self, entity: Entity) -> Entity:
        self.entities[entity.id] = entity
        return entity

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


NAMES = ["Luna", "Milo", "Nia", "Theo", "Mara", "Ivo"]
FRIEND_NAMES = ["Pip", "Jules", "Ari", "Bea", "Noah", "Tess"]
TRAITS = ["curious", "patient", "cheerful", "thoughtful", "hopeful"]
OPENINGS = [
    "On a warm afternoon",
    "After lunch",
    "Just before the tide came in",
    "During a quiet beach walk",
    "Near the end of the sunny day",
]
SPOTS = {
    "driftwood": SandSpot("driftwood", "the driftwood bench", "a line of tiny wet footprints"),
    "shells": SandSpot("shells", "the shell path", "a blue shell pressed into the sand"),
    "towel": SandSpot("towel", "the striped towel", "a square mark where something had rested"),
    "jetty": SandSpot("jetty", "the little jetty", "a ribbon caught on a low post"),
}
QUESTS = {
    "flag": Quest(
        "flag",
        "the missing flag quest",
        "red flag",
        "a little red flag from their sand castle",
        "a smooth hunk of sand held something bright inside",
        "Their castle stood taller because both friends had helped it stay together.",
    ),
    "shell": Quest(
        "shell",
        "the secret shell quest",
        "spiral shell",
        "a special spiral shell for their collection",
        "a buried hunk of sand opened to show two shells instead of one",
        "They made room in the collection for both shells and walked home side by side.",
    ),
    "note": Quest(
        "note",
        "the beach note quest",
        "folded note",
        "a folded note that had blown from their picnic bag",
        "a damp hunk of sand protected the note like a little envelope",
        "The note became a shared memory, even though its corner was sandy.",
    ),
}


@dataclass
class StoryParams:
    quest: str
    spot: str
    name: str
    friend: str
    trait: str
    opening: int
    reflection: int
    seed: Optional[int] = None


def _change(entity: Entity, meter: str, amount: float) -> None:
    entity.meters[meter] = entity.meter(meter) + amount


def _feel(entity: Entity, meme: str, amount: float) -> None:
    entity.memes[meme] = entity.meme(meme) + amount


def tell(params: StoryParams) -> World:
    quest = QUESTS[params.quest]
    spot = SPOTS[params.spot]
    opening = OPENINGS[params.opening % len(OPENINGS)]
    reflections = [
        "A good friend listens before choosing the next step.",
        "A quest feels lighter when two people carry the questions together.",
        "The best surprise was finding that help had been nearby all along.",
        "Friendship is sometimes a small pause that lets another person speak.",
        "They learned that solving a problem together mattered more than being first.",
    ]
    reflection = reflections[params.reflection % len(reflections)]

    world = World()
    hero = world.add(Entity(params.name, "child", params.name))
    friend = world.add(Entity(params.friend, "friend", params.friend))
    sand = world.add(Entity("sand", "material", "sand"))
    hero.meters.update(quest=0.0, patience=0.0, confidence=0.0)
    friend.meters.update(clue=0.0, patience=0.0, support=0.0)
    sand.meters.update(loose=1.0, wet=0.0, shaped=0.0, revealed=0.0)
    hero.memes.update(worry=0.0, wonder=0.0, relief=0.0, friendship=0.0)
    friend.memes.update(worry=0.0, relief=0.0, friendship=0.0)

    world.facts.update(
        hero=hero,
        friend=friend,
        sand=sand,
        quest=quest,
        spot=spot,
        reflection=reflection,
    )

    world.say(
        f"{opening}, {params.name}, a {params.trait} child, met {params.friend} beside "
        "the beach sand."
    )
    world.say(
        f"They had built a small castle together, but the {quest.object_name} was gone. "
        f"It had been {quest.object_phrase}."
    )
    _change(hero, "quest", 1.0)
    _feel(hero, "wonder", 0.5)
    world.para()

    world.say(
        f'"Let us look near {spot.label}," said {params.friend}. '
        f'"I noticed {spot.clue}."'
    )
    world.say(
        f'"I was going to search the other way," said {params.name}, '
        '"but your clue sounds worth following."'
    )
    _change(friend, "clue", 1.0)
    _change(hero, "patience", 1.0)
    _feel(hero, "friendship", 1.0)
    _feel(friend, "friendship", 1.0)

    world.say(
        f"They walked to {spot.label}, checking the sand without kicking it away. "
        "For a moment, nothing appeared."
    )
    world.say(
        f"{params.name} sighed and scooped up a heavy hunk of sand. "
        f"The sand was cooler and darker underneath."
    )
    _change(sand, "wet", 1.0)
    _change(sand, "shaped", 1.0)
    _feel(hero, "worry", 1.0)
    world.para()

    world.say(
        f'"Maybe the quest is over," said {params.name}. '
        '"Maybe we were looking in the wrong place."'
    )
    world.say(
        f'"Wait," said {params.friend}. "That hunk moved when you lifted it. '
        'Let us try together, slowly."'
    )
    _change(friend, "support", 1.0)
    _change(hero, "patience", 1.0)
    _feel(friend, "relief", 0.5)

    world.say(
        f"They loosened the sand with two careful fingers. "
        f"Under the hunk was a surprise: {quest.surprise}."
    )
    _change(sand, "revealed", 1.0)
    _change(hero, "confidence", 1.0)
    _feel(hero, "wonder", 1.0)
    _feel(hero, "relief", 1.0)
    _feel(friend, "relief", 1.0)

    world.say(
        f'"You saw the clue," said {params.name}. '
        '"And you listened," said {params.friend}. '
        '"That is how we found it."'
    )
    _change(hero, "quest", 1.0)
    _feel(hero, "friendship", 1.0)
    _feel(friend, "friendship", 1.0)
    world.say(
        f"They carried the find back to the castle. {quest.ending} "
        f"{reflection}"
    )
    world.para()
    world.say(
        f"For one quiet moment, the beach held only the soft hush of sand. "
        f"{params.name} and {params.friend} smiled at the small surprise between them."
    )
    world.facts["resolved"] = True
    world.facts["quest_complete"] = True
    return world


def valid_combos() -> list[tuple[str, str]]:
    return [(qid, sid) for qid in QUESTS for sid in SPOTS]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    quest = args.quest or rng.choice(sorted(QUESTS))
    spot = args.spot or rng.choice(sorted(SPOTS))
    if (quest, spot) not in valid_combos():
        raise StoryError("That quest and sand spot do not make a reasonable beach story.")
    name = args.name or rng.choice(NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != name])
    if name == friend:
        raise StoryError("The child and friend must have different names.")
    return StoryParams(
        quest=quest,
        spot=spot,
        name=name,
        friend=friend,
        trait=args.trait or rng.choice(TRAITS),
        opening=rng.randrange(len(OPENINGS)),
        reflection=rng.randrange(5),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    q: Quest = f["quest"]
    s: SandSpot = f["spot"]
    return [
        f"Write a slice-of-life friendship story about {q.title} near {s.label}.",
        f"Tell a small quest story in which {f['hero'].id} and {f['friend'].id} find {q.object_name} in the sand.",
        "Write a gentle story with a surprising hunk of sand and a warm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    q: Quest = f["quest"]
    s: SandSpot = f["spot"]
    return [
        QAItem(
            question=f"Who went on the {q.title}?",
            answer=f"{hero.id} and {friend.id} went on the quest together, searching the beach sand as friends.",
        ),
        QAItem(
            question=f"Where did they look first?",
            answer=f"They looked near {s.label}, because {friend.id} noticed {s.clue}.",
        ),
        QAItem(
            question="Why did they slow down while searching?",
            answer="They slowed down so they would not scatter the sand or miss the small clue hidden underneath it.",
        ),
        QAItem(
            question="What surprising thing did they find?",
            answer=f"They found that {q.surprise}.",
        ),
        QAItem(
            question="How did the friends solve the problem?",
            answer=f"{hero.id} listened to {friend.id}'s clue, and then they loosened the sand together with two careful fingers.",
        ),
        QAItem(
            question="What showed that their friendship had grown?",
            answer=f"They thanked each other for listening and helping, and {q.ending}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sand?",
            answer="Sand is made of many tiny grains of rock, shell, or other natural material.",
        ),
        QAItem(
            question="Why can wet sand hold a shape?",
            answer="Water helps the grains cling together, so wet sand can be pressed into a mound or a small castle.",
        ),
        QAItem(
            question="What makes a friendship strong?",
            answer="A friendship grows through kindness, listening, sharing, and helping one another.",
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
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(f"{entity.id}: meters={meters} memes={memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
quest(Q) :- quest_registry(Q).
spot(S) :- spot_registry(S).
valid_story(Q,S) :- quest(Q), spot(S), friendship_theme, surprise_theme.
resolved(Q,S) :- valid_story(Q,S), quest(Q), spot(S).
"""


def asp_facts() -> str:
    import asp
    lines = ["friendship_theme.", "surprise_theme."]
    for qid in QUESTS:
        lines.append(asp.fact("quest_registry", qid))
    for sid in SPOTS:
        lines.append(asp.fact("spot_registry", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    clingo_pairs = set(asp_valid_combos())
    if py == clingo_pairs:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combinations).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  only in Python:", sorted(py - clingo_pairs))
    print("  only in clingo:", sorted(clingo_pairs - py))
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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Slice-of-life friendship quest storyworld."
    )
    parser.add_argument("--quest", choices=QUESTS)
    parser.add_argument("--spot", choices=SPOTS)
    parser.add_argument("--name")
    parser.add_argument("--friend")
    parser.add_argument("--trait", choices=TRAITS)
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


CURATED = [
    StoryParams("flag", "driftwood", "Luna", "Pip", "curious", 0, 0),
    StoryParams("shell", "shells", "Milo", "Bea", "patient", 1, 1),
    StoryParams("note", "towel", "Nia", "Jules", "thoughtful", 2, 2),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 50):
            rng = random.Random(base_seed + index)
            params = resolve_params(args, rng)
            params.seed = base_seed + index
            sample = generate(params)
            index += 1
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
