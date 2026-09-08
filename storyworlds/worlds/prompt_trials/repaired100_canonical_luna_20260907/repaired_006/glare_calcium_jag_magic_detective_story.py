#!/usr/bin/env python3
"""
A gentle magic detective story about glare, calcium, and Jag.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    label: str
    kind: str = "thing"
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict[str, object] = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)
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


SETTINGS = (
    "the moonlit museum",
    "the old observatory",
    "the lantern-lit library",
    "the quiet clock tower",
)

DETECTIVE_NAMES = (
    ("Luna", "girl"),
    ("Milo", "boy"),
    ("Sage", "child"),
    ("Nia", "girl"),
)

JAG_LINES = (
    "a small silver jaguar with bright green eyes",
    "a striped jaguar cub wearing a blue ribbon",
    "a golden jaguar with velvet-soft paws",
)

MAGIC_TOOLS = (
    "a moonstone magnifying glass",
    "a wand tipped with a star",
    "a brass compass that hummed near spells",
)

CLUES = (
    (
        "three pale paw marks beside the locked display",
        "a sparkle of calcium dust beneath the reading table",
        "the enchanted moon-bone",
        "the moon-bone had been moved to keep its spell from cracking",
    ),
    (
        "a thin silver scratch across the velvet mat",
        "a white scale shining inside a teacup",
        "the calcium crown",
        "the crown had been carried away before the glare could fade its charm",
    ),
    (
        "a warm paw print on the window ledge",
        "a tiny calcium bead caught in the curtain",
        "the star-bone",
        "the star-bone had been hidden from a greedy beam of glare",
    ),
)

ENDINGS = (
    "By sunrise, the museum windows glowed softly, and the restored magic painted a safe silver path across the floor.",
    "The last spell settled like a feather, while Jag curled beside the case and Luna smiled at the quiet room.",
    "When the moon rose again, the display shone without glare, and every visitor could see the little bone sparkling inside.",
)


@dataclass
class StoryParams:
    seed: int | None = None
    detective_name: str = "Luna"
    detective_type: str = "girl"
    jag_description: str = JAG_LINES[0]
    magic_tool: str = MAGIC_TOOLS[0]
    setting: str = SETTINGS[0]
    first_clue: str = CLUES[0][0]
    second_clue: str = CLUES[0][1]
    treasure: str = CLUES[0][2]
    motive: str = CLUES[0][3]
    ending: str = ENDINGS[0]
    samples: list = field(default_factory=list)


def tell(params: StoryParams) -> World:
    if not params.detective_name.strip():
        raise StoryError("The detective needs a name.")
    world = World()
    detective = world.add(Entity(
        "detective",
        params.detective_name,
        "character",
        meters={"curiosity": 1.0, "steps": 0.0},
        memes={"worry": 1.0, "confidence": 0.0},
    ))
    jag = world.add(Entity(
        "jag",
        "Jag",
        "character",
        meters={"pawprints": 0.0},
        memes={"care": 1.0, "trust": 0.0},
    ))
    relic = world.add(Entity(
        "relic",
        params.treasure,
        "magical object",
        meters={"calcium": 1.0, "glare": 0.0},
        memes={"spell": 1.0, "safe": 0.0},
    ))
    world.facts.update(
        detective=detective,
        jag=jag,
        relic=relic,
        setting=params.setting,
        first_clue=params.first_clue,
        second_clue=params.second_clue,
        motive=params.motive,
        tool=params.magic_tool,
    )

    world.say(
        f"In {params.setting}, {params.detective_name} was the youngest magic detective in the city."
    )
    world.say(
        f"One evening, the enchanted {params.treasure} vanished from its glass case. "
        f"A sharp glare flashed across the empty velvet."
    )
    world.say(
        f"Jag, {params.jag_description}, padded into the room and sniffed the floor."
    )
    world.para()

    detective.meters["steps"] += 1
    detective.memes["worry"] = 0.0
    world.say(
        f'"Do not worry, Jag," {params.detective_name} said. '
        f'"We will follow the clues, not the glare."'
    )
    world.say(
        f'"Jag!" Jag answered, pointing with one paw toward {params.first_clue}.'
    )
    jag.meters["pawprints"] += 1
    jag.memes["trust"] += 1.0
    world.say(
        f"{params.detective_name} lifted {params.magic_tool} and found the first clue: "
        f"{params.first_clue}."
    )
    world.para()

    relic.meters["glare"] = 0.5
    world.say(
        f"Behind a curtain, they discovered {params.second_clue}. "
        f"The pale dust was calcium from the enchanted {params.treasure}."
    )
    world.say(
        f'"The magic is still alive," {params.detective_name} whispered. '
        f'"The calcium trail leads somewhere safe."'
    )
    world.say(
        f'"Jag," Jag replied, and his tail pointed toward the old storage room.'
    )
    detective.memes["confidence"] += 1.0
    world.para()

    relic.meters["glare"] = 0.0
    relic.memes["safe"] = 1.0
    world.fired.add("solved")
    world.say(
        f"In the storage room, {params.detective_name} found Jag curled beside the treasure."
    )
    world.say(
        f'"I moved it because {params.motive}," Jag seemed to say with a gentle growl.'
    )
    world.say(
        f"{params.detective_name} understood. Jag had protected the magic, not stolen it. "
        f"Together they returned the {params.treasure} to its case."
    )
    world.say(params.ending)
    jag.memes["trust"] += 1.0
    return world


ASP_RULES = r"""
missing(relic).
has_helper(jag).
has_clue(glare).
has_clue(calcium).
protects(jag, relic).
mystery(relic) :- missing(relic), has_helper(jag).
safe(relic) :- mystery(relic), has_clue(glare), has_clue(calcium), protects(jag, relic).
resolved(relic) :- safe(relic).
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("missing", "relic"),
        asp.fact("has_helper", "jag"),
        asp.fact("has_clue", "glare"),
        asp.fact("has_clue", "calcium"),
        asp.fact("protects", "jag", "relic"),
    ])


def asp_program(show: str = "#show mystery/1.\n#show resolved/1.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    mysteries = set(asp.atoms(model, "mystery"))
    resolved = set(asp.atoms(model, "resolved"))
    expected = {("relic",)}
    if mysteries == expected and resolved == expected:
        print("OK: ASP and Python agree on the magic detective mystery.")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP mystery:", sorted(mysteries))
    print("ASP resolved:", sorted(resolved))
    return 1


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        "Write a gentle magic detective story involving glare, calcium, and Jag.",
        f"Tell a mystery in {f['setting']} where a detective follows {f['first_clue']}.",
        f"Explain how Jag protected the enchanted treasure from {f['motive']}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    jag = f["jag"]
    return [
        QAItem(
            question=f"Who investigated the missing {f['relic'].label}?",
            answer=f"{detective.label} investigated it as a young magic detective, with help from Jag.",
        ),
        QAItem(
            question="What clues helped solve the mystery?",
            answer=f"The clues were {f['first_clue']} and {f['second_clue']}. They revealed a calcium trail and showed where the magic had gone.",
        ),
        QAItem(
            question=f"Why had Jag moved the {f['relic'].label}?",
            answer=f"Jag moved it because {f['motive']}. Jag was protecting the magical treasure rather than stealing it.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"The detective and Jag returned the treasure to its case, where its glare became gentle and safe. {world.paragraphs[-1][-1]}",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is calcium?",
            answer="Calcium is a mineral that helps build strong bones and teeth; in this magical story, it also leaves a pale clue behind.",
        ),
        QAItem(
            question="What is glare?",
            answer="Glare is a harsh, bright light that can make it difficult to see.",
        ),
        QAItem(
            question="What kind of animal is a jaguar?",
            answer="A jaguar is a powerful spotted wild cat native to the Americas.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.extend(["", "== story qa =="])
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.extend(["", "== world qa =="])
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for entity in world.entities.values():
        lines.append(
            f"{entity.id}: meters={entity.meters} memes={entity.memes}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


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
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A magic detective storyworld.")
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
    seed = args.seed if args.seed is not None else 0
    detective_name, detective_type = DETECTIVE_NAMES[seed % len(DETECTIVE_NAMES)]
    first_clue, second_clue, treasure, motive = CLUES[
        (seed // len(DETECTIVE_NAMES)) % len(CLUES)
    ]
    return StoryParams(
        seed=seed,
        detective_name=detective_name,
        detective_type=detective_type,
        jag_description=rng.choice(JAG_LINES),
        magic_tool=rng.choice(MAGIC_TOOLS),
        setting=rng.choice(SETTINGS),
        first_clue=first_clue,
        second_clue=second_clue,
        treasure=treasure,
        motive=motive,
        ending=rng.choice(ENDINGS),
    )


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
        print(sorted(set(asp.atoms(model, "mystery"))))
        print(sorted(set(asp.atoms(model, "resolved"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    count = len(CLUES) * len(DETECTIVE_NAMES) if args.all else args.n
    samples = []
    for index in range(count):
        seed = base_seed + index
        params = resolve_params(
            argparse.Namespace(seed=seed),
            random.Random(seed),
        )
        samples.append(generate(params))

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
