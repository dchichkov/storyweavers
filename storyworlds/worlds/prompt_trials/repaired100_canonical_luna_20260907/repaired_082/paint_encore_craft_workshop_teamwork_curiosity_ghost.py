#!/usr/bin/env python3
"""
A gentle ghost story about paint, an encore, and teamwork in a craft workshop.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str
    label: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "ghost":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass(frozen=True)
class Setting:
    id: str
    place: str
    affordances: tuple[str, ...]


@dataclass(frozen=True)
class Tool:
    id: str
    label: str
    purpose: str


@dataclass(frozen=True)
class Encore:
    id: str
    title: str
    color: str
    clue: str


SETTINGS = {
    "workshop": Setting(
        "workshop",
        "the old craft workshop",
        ("mix_paint", "share_tools", "make_banner", "listen"),
    )
}

TOOLS = {
    "brush": Tool("brush", "a broad paintbrush", "covering cloth"),
    "bell": Tool("bell", "a little silver bell", "calling everyone together"),
    "thread": Tool("thread", "a spool of blue thread", "joining loose pieces"),
}

ENCORES = {
    "moonlit_mural": Encore(
        "moonlit_mural",
        "the Moonlit Mural",
        "blue and silver",
        "three pale fingerprints beside the unfinished moon",
    ),
    "lantern_banner": Encore(
        "lantern_banner",
        "the Lantern Banner",
        "gold and red",
        "a tiny star painted on the back of the cloth",
    ),
}

NAMES = ["Luna", "Mara", "Pip", "Nell"]
HELPERS = ["Theo", "Milo", "Jun", "Sage"]


@dataclass(frozen=True)
class StoryParams:
    setting: str = "workshop"
    encore: str = "moonlit_mural"
    name: str = "Luna"
    helper: str = "Theo"
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]

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


def validate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError(f"Unknown setting '{params.setting}'; this story uses the craft workshop.")
    if params.encore not in ENCORES:
        raise StoryError(f"Unknown encore '{params.encore}'; choose a registered workshop encore.")
    if not params.name.strip() or not params.helper.strip():
        raise StoryError("The maker and helper must both have names.")
    if params.name.strip().lower() == params.helper.strip().lower():
        raise StoryError("The maker and helper need different names so their teamwork can be heard.")


def build_story(params: StoryParams) -> World:
    validate(params)
    setting = SETTINGS[params.setting]
    encore = ENCORES[params.encore]
    world = World(setting)

    luna = world.add(Entity(params.name, "girl", params.name))
    helper = world.add(Entity(params.helper, "child", params.helper))
    ghost = world.add(Entity("pale_ghost", "ghost", "the pale ghost"))
    brush = world.add(Entity("brush", "tool", "the broad paintbrush"))
    bell = world.add(Entity("bell", "tool", "the little silver bell"))

    luna.meters.update({"curiosity": 1.0, "paint": 1.0})
    helper.meters.update({"teamwork": 1.0, "care": 1.0})
    ghost.memes["lonely"] = 1.0

    world.say(
        f"At dusk, {params.name} and {params.helper} stayed late in {setting.place}, "
        f"where jars of paint shone like small moons."
    )
    world.say(
        f"They were preparing {encore.title}, an encore for the workshop's little puppet show. "
        f"The final picture needed {encore.color} paint, but the last moon was still blank."
    )

    world.para()
    world.say(
        f"Then a cold brushstroke curled across the cloth by itself. "
        f"{params.name} leaned closer and saw {encore.clue}."
    )
    world.say(
        f"\"Did you make that mark?\" asked {params.name}. "
        f"\"No,\" said {params.helper}, \"but we can find out together.\""
    )
    world.say(
        f"The pale ghost appeared beside the drying rack. It held no brush, yet a wet shine followed its fingers."
    )
    world.say(
        f"\"Please do not hide,\" said {params.helper}. \"Show us what you need.\""
    )
    world.say(
        f"The ghost pointed toward the bell and then toward the empty paint tray. "
        f"{params.name}'s curiosity became a plan: the ghost wanted an encore too."
    )

    world.para()
    world.say(
        f"{params.name} mixed {encore.color} paint while {params.helper} steadied the cloth. "
        f"Together they gave the ghost the broad paintbrush."
    )
    world.say(
        f"\"One careful stroke,\" said {params.name}. \"Then we all step back.\" "
        f"\"One careful stroke,\" agreed {params.helper}."
    )
    world.say(
        f"The ghost painted a shining moon, and the children added stars around it. "
        f"Their teamwork turned a lonely smudge into {encore.title}."
    )
    world.say(
        f"When {params.helper} rang the little silver bell, the ghost bowed. "
        f"Then it faded into the painted moon, leaving one bright fingerprint behind."
    )

    world.para()
    world.say(
        f"At the show, the curtain rose again for an encore. The painted moon glowed softly, "
        f"and nobody laughed at the strange extra handprint."
    )
    world.say(
        f"{params.name} and {params.helper} smiled at each other. Curiosity had opened the door, "
        f"and teamwork had made room for a friend."
    )
    world.say(
        f"After everyone went home, the workshop grew quiet. The moon on the cloth gave one tiny wink, "
        f"and a fresh dot of paint appeared beside it."

    )
    world.events.extend(["curiosity_noticed_clue", "ghost_invited", "paint_shared", "encore_completed"])
    world.facts.update(
        maker=luna,
        helper=helper,
        ghost=ghost,
        brush=brush,
        bell=bell,
        encore=encore,
        clue=encore.clue,
        teamwork=True,
        curiosity=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    encore: Encore = world.facts["encore"]
    maker: Entity = world.facts["maker"]
    return [
        f"Write a gentle ghost story in a craft workshop about {maker.label}, paint, and {encore.title}.",
        "Show curiosity discovering what a friendly ghost needs, then let teamwork solve the problem.",
        "End with an encore and a small magical image proving the ghost was grateful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    maker: Entity = world.facts["maker"]
    helper: Entity = world.facts["helper"]
    ghost: Entity = world.facts["ghost"]
    encore: Encore = world.facts["encore"]
    return [
        QAItem(
            f"What did {maker.label} notice on the unfinished craft?",
            f"{maker.label} noticed {encore.clue}, a clue that the ghost had touched the unfinished {encore.title}.",
        ),
        QAItem(
            f"How did {helper.label} respond to the ghost?",
            f"{helper.label} invited {ghost.label} to show what it needed instead of hiding.",
        ),
        QAItem(
            "How did teamwork help finish the paint project?",
            f"They mixed the {encore.color} paint, steadied the cloth, shared the brush, and painted the moon and stars together.",
        ),
        QAItem(
            "What happened during the encore?",
            f"The painted moon glowed softly while the children and the ghost's work became part of the encore.",
        ),
        QAItem(
            "What proved the ghost was still friendly at the end?",
            "A tiny wink came from the painted moon, followed by a fresh dot of paint beside it.",
        ),
    ]


WORLD_QA = [
    QAItem(
        "Why do artists mix paint?",
        "Artists mix paint to create new colors and shades for their pictures or crafts.",
    ),
    QAItem(
        "What does teamwork mean?",
        "Teamwork means people cooperate, share jobs, and help one another reach a goal.",
    ),
    QAItem(
        "What is curiosity?",
        "Curiosity is a wish to learn more by noticing, wondering, and asking careful questions.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        lines.append(
            f"  {entity.id}: kind={entity.kind}, meters={entity.meters}, memes={entity.memes}"
        )
    lines.append(f"  events: {world.events}")
    lines.append(f"  affordances: {world.setting.affordances}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str]]:
    return [(setting, encore) for setting in SETTINGS for encore in ENCORES]


ASP_RULES = r"""
valid(S,E) :- setting(S), encore(E), hosts(S,E).
#show valid/2.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for encore in ENCORES:
            if "make_banner" in setting.affordances:
                lines.append(asp.fact("hosts", sid, encore))
    for eid in ENCORES:
        lines.append(asp.fact("encore", eid))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        py = set(valid_combos())
        clingo_rows = set(asp_valid_combos())
    except ImportError:
        print("ASP verification unavailable: clingo is not installed.")
        return 0
    if py != clingo_rows:
        print("MISMATCH:")
        print("python only:", sorted(py - clingo_rows))
        print("clingo only:", sorted(clingo_rows - py))
        return 1
    for params in (
        StoryParams(seed=3),
        StoryParams(encore="lantern_banner", name="Mara", helper="Jun", seed=8),
    ):
        sample = generate(params)
        if "paint" not in sample.story.lower() or "encore" not in sample.story.lower():
            print("Generated-story exercise failed.")
            return 1
    print(f"OK: ASP matches Python ({len(py)} combinations), and stories exercised.")
    return 0


CURATED = [
    StoryParams(name="Luna", helper="Theo", encore="moonlit_mural", seed=1),
    StoryParams(name="Mara", helper="Jun", encore="lantern_banner", seed=2),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A gentle ghost story about paint and an encore in a craft workshop."
    )
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--encore", choices=ENCORES)
    parser.add_argument("--name")
    parser.add_argument("--helper")
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
    setting = args.setting or "workshop"
    encore = args.encore or rng.choice(list(ENCORES))
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice([value for value in HELPERS if value != name])
    params = StoryParams(
        setting=setting,
        encore=encore,
        name=name,
        helper=helper,
        seed=args.seed,
    )
    validate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = build_story(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        try:
            print(asp_program())
        except ImportError:
            print("ASP display unavailable: clingo is not installed.")
        return

    if args.verify:
        raise SystemExit(asp_verify())

    if args.asp:
        try:
            rows = asp_valid_combos()
        except ImportError:
            print("ASP mode unavailable: clingo is not installed.")
            return
        print(f"{len(rows)} compatible combinations:")
        for row in rows:
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in CURATED]
    else:
        seen: set[str] = set()
        for offset in range(max(args.n * 20, 20)):
            if len(samples) >= args.n:
                break
            seed = base_seed + offset
            local_args = argparse.Namespace(**vars(args))
            local_args.seed = seed
            params = resolve_params(local_args, random.Random(seed))
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
