#!/usr/bin/env python3
"""
A small fable storyworld about Blonde-Dim and Smidge, where curiosity opens
a difficult question and reconciliation repairs a friendship.
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
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class StoryParams:
    name: str
    companion: str
    object_name: str
    setting: str
    curiosity: str
    reconciliation: str
    seed: Optional[int] = None


@dataclass(frozen=True)
class CuriosityPath:
    key: str
    question: str
    clue: str
    action: str


@dataclass(frozen=True)
class ReconciliationPath:
    key: str
    hurt: str
    repair: str
    lesson: str


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


NAMES = ["Luna", "Mara", "Pip", "Tessa", "Nell"]
COMPANIONS = ["Smidge", "Bram", "Fenn", "Moss"]
OBJECTS = ["a silver thimble", "a blue acorn", "a tiny brass key", "a red ribbon"]
SETTINGS = [
    "the hill behind the old mill",
    "the mossy edge of the village pond",
    "the orchard beneath the crooked pear tree",
    "the path beside the whispering brook",
]
CURIOSITIES = ["hidden_sound", "mysterious_mark", "missing_shadow", "closed_box"]
RECONCILIATIONS = ["honest_words", "shared_search", "patient_listening", "returned_trust"]


CURIOSITY_PATHS = [
    CuriosityPath(
        "hidden_sound",
        "What made the soft tapping under the roots?",
        "a hollow root answered each breeze with a wooden tap",
        "place an ear near the root and listen before lifting it",
    ),
    CuriosityPath(
        "mysterious_mark",
        "Why did three silver marks shine on the flat stone?",
        "the marks were tiny maps scratched by rain and beetle feet",
        "follow the marks slowly instead of scraping them away",
    ),
    CuriosityPath(
        "missing_shadow",
        "Where had the little shadow gone at noon?",
        "a broad leaf had folded over the sunlit patch",
        "look above the ground as well as below it",
    ),
    CuriosityPath(
        "closed_box",
        "What could be inside the small box with no latch?",
        "the box was a seed pod waiting for the right warmth to open",
        "hold it gently in a patch of sunlight",
    ),
]


RECONCILIATION_PATHS = [
    ReconciliationPath(
        "honest_words",
        "Blonde-Dim had hurried ahead and left Smidge feeling forgotten.",
        "Blonde-Dim admitted the mistake, apologized plainly, and waited for Smidge to answer.",
        "A true apology opens a door only pride keeps shut.",
    ),
    ReconciliationPath(
        "shared_search",
        "Blonde-Dim had grabbed the clue without asking, and Smidge felt pushed aside.",
        "They divided the search, gave each other a turn, and celebrated the answer together.",
        "A discovery grows brighter when it is shared.",
    ),
    ReconciliationPath(
        "patient_listening",
        "Blonde-Dim had laughed at Smidge's first idea before hearing the whole thought.",
        "Blonde-Dim listened carefully, repeated the idea kindly, and asked what Smidge had noticed.",
        "Listening can mend a tear that cleverness made.",
    ),
    ReconciliationPath(
        "returned_trust",
        "Blonde-Dim had promised to protect the little object but carried it away alone.",
        "Blonde-Dim brought it back, explained the choice, and asked Smidge to guard it together.",
        "Trust returns by small faithful steps.",
    ),
]


def _pick(items, key: str):
    for item in items:
        if item.key == key:
            return item
    raise StoryError(f"Unknown story choice: {key}")


def validate_params(params: StoryParams) -> None:
    if not params.name.strip():
        raise StoryError("The protagonist needs a name.")
    if not params.companion.strip():
        raise StoryError("The companion needs a name.")
    if params.name.lower() == params.companion.lower():
        raise StoryError("The protagonist and companion must have different names.")
    if not params.object_name.strip():
        raise StoryError("The story needs a concrete object.")
    if not params.setting.strip():
        raise StoryError("The story needs a setting.")
    _pick(CURIOSITY_PATHS, params.curiosity)
    _pick(RECONCILIATION_PATHS, params.reconciliation)


def build_world(params: StoryParams) -> World:
    validate_params(params)
    curiosity = _pick(CURIOSITY_PATHS, params.curiosity)
    reconciliation = _pick(RECONCILIATION_PATHS, params.reconciliation)

    world = World()
    child = world.add(Entity(
        id="blonde_dim",
        kind="character",
        label=params.name,
        meters={"curiosity": 1.0, "hurt": 0.0, "trust": 1.0},
        memes={"wonder": 1.0, "pride": 0.5},
    ))
    smidge = world.add(Entity(
        id="smidge",
        kind="character",
        label=params.companion,
        meters={"curiosity": 1.0, "hurt": 0.0, "trust": 1.0},
        memes={"care": 1.0, "patience": 1.0},
    ))
    treasure = world.add(Entity(
        id="object",
        kind="thing",
        label=params.object_name,
        owner=None,
        meters={"mystery": 1.0},
        memes={"meaning": 0.0},
    ))

    world.facts.update(
        child=child,
        smidge=smidge,
        treasure=treasure,
        curiosity=curiosity,
        reconciliation=reconciliation,
        params=params,
        resolution=False,
    )
    return world


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child = world.facts["child"]
    smidge = world.facts["smidge"]
    treasure = world.facts["treasure"]
    curiosity = world.facts["curiosity"]
    reconciliation = world.facts["reconciliation"]

    world.say(
        f"In {params.setting}, {child.label}, whom the village called Blonde-Dim "
        f"because bright thoughts sometimes arrived through a dim little pause, "
        f"walked with {smidge.label}, a smidge-sized keeper of careful questions."
    )
    world.say(
        f"Near the path they found {treasure.label}. It seemed ordinary until "
        f"{curiosity.question.lower()} {curiosity.clue}."
    )
    world.say(
        f'"I must find out!" said {child.label}. '
        f'"Then let us find out together," said {smidge.label}.'
    )
    world.para()

    child.meters["curiosity"] += 1
    child.memes["wonder"] += 1
    world.say(
        f"{child.label} began to {curiosity.action}, but excitement made the "
        f"question feel bigger than the path."
    )
    world.say(
        f"{child.label} hurried forward with {treasure.label}, while "
        f"{smidge.label} stopped behind. {reconciliation.hurt}"
    )
    child.meters["hurt"] += 1
    smidge.meters["hurt"] += 1
    child.memes["pride"] += 1
    world.say(
        f'"Wait," called {smidge.label}. "A mystery is not worth losing a friend." '
        f'"I thought speed would help," answered {child.label}, "but I did not ask what you needed."'
    )
    world.para()

    world.say(
        f"{reconciliation.repair} Together they returned to {params.setting} "
        f"and examined {treasure.label} with gentle hands."
    )
    child.meters["hurt"] -= 1
    smidge.meters["hurt"] -= 1
    child.meters["trust"] += 1
    smidge.meters["trust"] += 1
    child.memes["pride"] -= 1
    treasure.memes["meaning"] += 1
    world.say(
        f"Because they listened to one another, the clue became clear: "
        f"{curiosity.clue.capitalize()}. The answer was small, but their repaired "
        f"friendship felt large enough to hold it."
    )
    world.facts["resolution"] = True
    world.para()

    world.say(
        f"{treasure.label} rested between {child.label} and {smidge.label} as "
        f"they walked home side by side."
    )
    world.say(f"The fable's lesson was simple: {reconciliation.lesson}")
    return world


def story_qa(world: World) -> list[QAItem]:
    params = world.facts["params"]
    child = world.facts["child"]
    smidge = world.facts["smidge"]
    treasure = world.facts["treasure"]
    curiosity = world.facts["curiosity"]
    reconciliation = world.facts["reconciliation"]
    return [
        QAItem(
            question=f"What did {child.label} and {smidge.label} discover in {params.setting}?",
            answer=f"They discovered {treasure.label}, whose mystery was explained when they learned that {curiosity.clue}."
        ),
        QAItem(
            question=f"What did {child.label} do that hurt {smidge.label}?",
            answer=reconciliation.hurt
        ),
        QAItem(
            question=f"How did {child.label} and {smidge.label} reconcile?",
            answer=reconciliation.repair
        ),
        QAItem(
            question="What lesson did the fable teach?",
            answer=reconciliation.lesson
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to learn why something happens or what may be hidden."
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is making peace after hurt by speaking honestly, listening, and repairing trust."
        ),
        QAItem(
            question="Why is it useful to ask questions before acting?",
            answer="Asking questions can reveal important clues and help people avoid causing needless harm."
        ),
        QAItem(
            question="Why can an apology help a friendship?",
            answer="An apology names the hurt and shows that someone is ready to make a better choice."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    params = world.facts["params"]
    curiosity = world.facts["curiosity"]
    reconciliation = world.facts["reconciliation"]
    return [
        f"Write a child-friendly fable about blonde-dim and smidge in {params.setting}.",
        f"Include Curiosity through the question '{curiosity.question}' and reveal the concrete clue.",
        f"Include Reconciliation through this repair: {reconciliation.repair}",
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("domain", "fable"),
        asp.fact("character", "blonde_dim"),
        asp.fact("character", "smidge"),
        asp.fact("feature", "curiosity"),
        asp.fact("feature", "reconciliation"),
        asp.fact("requires", "honest_words"),
        asp.fact("requires", "shared_search"),
    ])


ASP_RULES = r"""
good_fable :-
    domain(fable),
    character(blonde_dim),
    character(smidge),
    feature(curiosity),
    feature(reconciliation).

has_repair :-
    good_fable,
    requires(honest_words).
has_repair :-
    good_fable,
    requires(shared_search).

compatible_story :-
    good_fable,
    has_repair.
"""


def asp_program(show: str = "#show compatible_story/0.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    if not asp.atoms(model, "compatible_story"):
        print("MISMATCH: ASP gate failed.")
        return 1
    for seed in range(5):
        params = resolve_params(build_parser().parse_args(["--seed", str(seed)]), random.Random(seed))
        sample = generate(params)
        if not sample.story or "Blonde-Dim" not in sample.story:
            print("MISMATCH: generated story failed.")
            return 1
        if "Smidge" not in sample.story:
            print("MISMATCH: companion failed.")
            return 1
    print("OK: ASP gate and generated stories agree.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A fable about Blonde-Dim, Smidge, curiosity, and reconciliation.")
    parser.add_argument("--name")
    parser.add_argument("--companion")
    parser.add_argument("--object-name")
    parser.add_argument("--setting", choices=SETTINGS)
    parser.add_argument("--curiosity", choices=CURIOSITIES)
    parser.add_argument("--reconciliation", choices=RECONCILIATIONS)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--seed", type=int)
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
        name=args.name or "Luna",
        companion=args.companion or "Smidge",
        object_name=args.object_name or rng.choice(OBJECTS),
        setting=args.setting or rng.choice(SETTINGS),
        curiosity=args.curiosity or rng.choice(CURIOSITIES),
        reconciliation=args.reconciliation or rng.choice(RECONCILIATIONS),
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
            meters = {key: value for key, value in entity.meters.items() if value}
            memes = {key: value for key, value in entity.memes.items() if value}
            print(f"{entity.label}: meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("Luna", "Smidge", "a silver thimble", SETTINGS[0], "hidden_sound", "honest_words"),
    StoryParams("Mara", "Smidge", "a blue acorn", SETTINGS[1], "mysterious_mark", "shared_search"),
    StoryParams("Pip", "Smidge", "a tiny brass key", SETTINGS[2], "closed_box", "patient_listening"),
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
        print(asp.atoms(model, "compatible_story"))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        samples = []
        for index in range(args.n):
            seed = base_seed + index
            rng = random.Random(seed)
            params = resolve_params(args, rng)
            params.seed = seed
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
