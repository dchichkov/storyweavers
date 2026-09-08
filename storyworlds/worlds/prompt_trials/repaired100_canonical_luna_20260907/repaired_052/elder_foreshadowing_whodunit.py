#!/usr/bin/env python3
"""
A small standalone Whodunit storyworld about an elder who leaves a clue before
a treasured object disappears.
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

STORYWORLDS_ROOT = Path(__file__).resolve().parents[2]
if str(STORYWORLDS_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYWORLDS_ROOT))

from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    type: str
    label: str
    location: str
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)


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
    elder: str
    young_detective: str
    manor: str
    heirloom: str
    seed: Optional[int] = None
    case: Optional[str] = None
    telling_mode: Optional[str] = None


@dataclass(frozen=True)
class Case:
    key: str
    opening: str
    object_description: str
    disappearance: str
    suspects: tuple[str, str, str]
    false_clue: str
    foreshadowing: str
    discovery: str
    motive: str
    repair: str
    ending: str
    lesson: str


ELDER_NAMES = ["Alden", "Beatrice", "Cora", "Edwin", "Mabel", "Nora"]
DETECTIVE_NAMES = ["Finn", "Ivy", "Leo", "Mina", "Pia", "Theo"]
MANORS = [
    "Willow House",
    "Foxglove Hall",
    "Mossy Manor",
    "The Lantern Cottage",
]
HEIRLOOMS = [
    "a silver pocket watch",
    "a blue glass bird",
    "an amber brooch",
    "a brass music box",
]

CASES = [
    Case(
        key="pocket_watch",
        opening="The elder had invited three neighbors to hear an old pocket watch sing its tiny noon chime.",
        object_description="The watch had a moon-shaped lid and belonged to the elder's mother.",
        disappearance="Just before noon, the watch vanished from its velvet cushion.",
        suspects=("the baker", "the gardener", "the librarian"),
        false_clue="A dusting of flour led from the table toward the pantry.",
        foreshadowing="At breakfast, the elder had said, 'When the clock forgets the hour, look where the house keeps its warmest breath.'",
        discovery="The warmest breath came from the kitchen stove, where the watch rested inside a mitten on the cooling shelf.",
        motive="The baker had moved it there to protect it from a sudden draft, then forgot to tell anyone.",
        repair="The baker returned the watch, apologized, and placed a bright note beside the cushion.",
        ending="At noon, the watch chimed from its cushion, and everyone laughed when the elder called the mitten its first hiding place.",
        lesson="An old clue may seem odd until careful listening gives it a place.",
    ),
    Case(
        key="glass_bird",
        opening="The elder was preparing a window-light party at the manor.",
        object_description="The blue glass bird was a keepsake that glittered whenever the sun touched its wings.",
        disappearance="When the curtains opened, the bird was gone from the windowsill.",
        suspects=("the painter", "the stable boy", "the visiting cousin"),
        false_clue="A wet blue footprint crossed the floor beneath the empty sill.",
        foreshadowing="The elder had warned, 'If the bird leaves the sky, follow the color that does not belong outdoors.'",
        discovery="The strange color led to a paint room, where the bird stood safely inside a clean wooden crate.",
        motive="The painter had moved it away from a falling ladder and planned to return after the room was safe.",
        repair="The painter admitted the move, helped clean the footprint, and secured the ladder.",
        ending="The glass bird returned to the sunny sill, shining beside the repaired ladder.",
        lesson="A careful question can separate a protective act from a theft.",
    ),
    Case(
        key="amber_brooch",
        opening="The elder wore an amber brooch while telling family stories in the library.",
        object_description="The brooch held a tiny pressed flower from the elder's first garden.",
        disappearance="During a noisy game, the brooch disappeared from the elder's coat.",
        suspects=("the drummer", "the housekeeper", "the mail carrier"),
        false_clue="A torn gold thread was caught on the library door.",
        foreshadowing="Before the guests arrived, the elder had murmured, 'Flowers remember where they first felt sunlight.'",
        discovery="Sunlight fell across the greenhouse, where the brooch lay beneath a garden hat.",
        motive="The housekeeper had found it on the floor and placed it near the elder's favorite flowers for safekeeping.",
        repair="The housekeeper returned it, and the elder added a small clasp so it could not slip free again.",
        ending="The amber brooch glowed in the greenhouse sun while the pressed flower looked newly awake.",
        lesson="A remembered phrase can guide a search without blaming anyone.",
    ),
    Case(
        key="music_box",
        opening="The elder planned to play a brass music box for the children at supper.",
        object_description="The music box played a waltz the elder had learned as a child.",
        disappearance="The box was missing when the supper bell rang.",
        suspects=("the violinist", "the tailor", "the quiet neighbor"),
        false_clue="A trail of tiny brass shavings ran beneath the sideboard.",
        foreshadowing="The elder had said, 'When a song goes quiet, listen for the place where tools sleep.'",
        discovery="The sound of a loose spring led to the workshop, where the music box sat open on a workbench.",
        motive="The tailor had repaired a bent hinge after noticing it could snap, but had been called away before explaining.",
        repair="The tailor finished the repair and placed a red ribbon on the box to show it was safe.",
        ending="The music box played its waltz, and the children danced around the red ribbon.",
        lesson="Evidence becomes useful when it is joined to what people noticed earlier.",
    ),
]

TELLING_MODES = ["arrival", "warning", "question", "quiet", "dialogue"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Elderly foreshadowing Whodunit storyworld.")
    parser.add_argument("--elder", choices=ELDER_NAMES)
    parser.add_argument("--young-detective", choices=DETECTIVE_NAMES)
    parser.add_argument("--manor", choices=MANORS)
    parser.add_argument("--heirloom", choices=HEIRLOOMS)
    parser.add_argument("--case", choices=[c.key for c in CASES])
    parser.add_argument("--telling-mode", choices=TELLING_MODES)
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
    elder = args.elder or rng.choice(ELDER_NAMES)
    detective = args.young_detective or rng.choice(
        [name for name in DETECTIVE_NAMES if name != elder]
    )
    return StoryParams(
        elder=elder,
        young_detective=detective,
        manor=args.manor or rng.choice(MANORS),
        heirloom=args.heirloom or rng.choice(HEIRLOOMS),
        seed=args.seed,
        case=args.case or rng.choice(CASES).key,
        telling_mode=args.telling_mode or rng.choice(TELLING_MODES),
    )


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("domain", "whodunit"),
            asp.fact("feature", "foreshadowing"),
            asp.fact("role", "elder"),
            asp.fact("role", "detective"),
            asp.fact("object", "heirloom"),
            asp.fact("rule", "clue_before_reveal"),
        ]
    )


ASP_RULES = r"""
evidence(clue_before_reveal) :- feature(foreshadowing), rule(clue_before_reveal).
case_has(clue, clue_before_reveal) :- evidence(clue_before_reveal).
#show domain/1.
#show feature/1.
#show role/1.
#show object/1.
#show case_has/2.
"""


def asp_program(show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show feature/1.\n#show case_has/2."))
    features = asp.atoms(model, "feature")
    cases = asp.atoms(model, "case_has")
    if features == [("foreshadowing",)] and cases == [("clue", "clue_before_reveal")]:
        print("OK: ASP foreshadowing facts and rule agree.")
        return 0
    print("MISMATCH: ASP foreshadowing parity failed.")
    print(f"features={features} cases={cases}")
    return 1


def _opening(params: StoryParams, case: Case) -> list[str]:
    elder = params.elder
    detective = params.young_detective
    mode = params.telling_mode or "arrival"
    if mode == "warning":
        return [
            f'"Keep your eyes open," {elder} warned {detective} at {params.manor}.',
            case.opening,
        ]
    if mode == "question":
        return [
            f'"Why did you polish the empty cushion?" {detective} asked {elder}.',
            case.opening,
        ]
    if mode == "quiet":
        return [
            f"At {params.manor}, the elder spoke softly while rain tapped the windows.",
            case.opening,
        ]
    if mode == "dialogue":
        return [
            f'"Will there be a mystery today?" {detective} asked.',
            f'"Only if someone forgets to watch carefully," {elder} replied. {case.opening}',
        ]
    return [
        f"{detective} arrived at {params.manor} just as {elder} opened the front door.",
        case.opening,
    ]


def generate(params: StoryParams) -> StorySample:
    if params.elder not in ELDER_NAMES:
        raise StoryError("elder must be selected from the elder registry")
    if params.young_detective not in DETECTIVE_NAMES:
        raise StoryError("young detective must be selected from the detective registry")
    if params.elder == params.young_detective:
        raise StoryError("elder and young detective must have different names")

    rng = random.Random(params.seed)
    case = next((item for item in CASES if item.key == params.case), None)
    if case is None:
        raise StoryError(f"unknown case: {params.case}")

    world = World()
    elder = world.add(
        Entity(
            id="elder",
            type="elder",
            label=params.elder,
            location=params.manor,
            meters={"age": 1.0, "steadiness": 0.9},
            memes={"memory": 1.0, "patience": 1.0},
            traits=["observant", "kind"],
        )
    )
    detective = world.add(
        Entity(
            id="detective",
            type="detective",
            label=params.young_detective,
            location=params.manor,
            meters={"curiosity": 1.0, "care": 0.8},
            memes={"reasoning": 1.0, "trust": 0.7},
            traits=["careful", "curious"],
        )
    )
    heirloom = world.add(
        Entity(
            id="heirloom",
            type="heirloom",
            label=params.heirloom,
            location="velvet cushion",
            owner="elder",
            meters={"fragility": 0.8, "value": 1.0},
            memes={"memory": 1.0, "mystery": 1.0},
        )
    )
    clue = world.add(
        Entity(
            id="foreshadowing_clue",
            type="clue",
            label="the elder's early warning",
            location="memory",
            meters={"relevance": 1.0},
            memes={"foreshadowing": 1.0},
        )
    )
    world.facts.update(
        case=case.key,
        elder=elder.label,
        detective=detective.label,
        heirloom=params.heirloom,
        clue=case.foreshadowing,
        reveal=case.discovery,
        suspects=list(case.suspects),
        solved=False,
    )

    for sentence in _opening(params, case):
        world.say(sentence)
    world.say(case.object_description)
    world.say(f'"Remember my words from earlier," {elder.label} said. "{case.foreshadowing}"')

    world.para()
    world.say(case.disappearance)
    world.say(f"The three possible suspects were {case.suspects[0]}, {case.suspects[1]}, and {case.suspects[2]}.")
    world.say(case.false_clue)
    world.say(
        f'"The flour, paint, thread, or metal may tell us where something went," '
        f"{detective.label} said, \"but it does not tell us who meant harm.\""
    )
    world.say(
        f'"Good," {elder.label} replied. "A real detective follows facts without rushing to blame."'
    )

    world.para()
    world.say(
        f"{detective.label} repeated the elder's earlier words and compared them with the room."
    )
    world.say(f"The clue pointed away from the obvious trail: {case.discovery}")
    world.say(
        f'"So the hidden place matches your warning," {detective.label} said.'
    )
    world.say(
        f'"And now we must ask why it was moved," {elder.label} answered.'
    )
    world.say(f"They learned that {case.motive}")

    world.para()
    world.say(f"{case.repair}")
    world.say(
        f"The mystery ended without a shouted accusation because {detective.label} had listened "
        "to the clue before deciding what it meant."
    )
    world.say(f"{case.ending}")
    world.say(f"The elder's lesson stayed with everyone: {case.lesson}")

    heirloom.location = "returned safely"
    heirloom.meters["risk"] = 0.0
    heirloom.memes["understood"] = 1.0
    clue.location = "explained"
    detective.memes["confidence"] = 1.0
    world.facts["solved"] = True
    world.facts["resolution"] = "truth found without blame"

    prompts = [
        f"Write a gentle Whodunit in which an elder named {params.elder} leaves a clue before {params.heirloom} disappears.",
        f"Tell a child-friendly mystery at {params.manor} using foreshadowing before the reveal.",
        f"Write a story where {params.young_detective} solves a case by asking why an object was moved instead of blaming a suspect.",
    ]
    story_qa = [
        QAItem(
            question=f"What disappeared from {params.manor}?",
            answer=f"{params.heirloom} disappeared from its place. It was an heirloom connected to {params.elder}'s memories.",
        ),
        QAItem(
            question="What was the foreshadowing clue?",
            answer=f"Before the disappearance, the elder said, “{case.foreshadowing}” That early warning pointed toward the later hiding place.",
        ),
        QAItem(
            question=f"How did {params.young_detective} avoid blaming the wrong person?",
            answer=f"{params.young_detective} treated {case.false_clue} as evidence about a location, not proof of guilt, and asked why the heirloom had been moved.",
        ),
        QAItem(
            question="Where was the missing heirloom found?",
            answer=f"It was found because {case.discovery} The place matched the elder's earlier foreshadowing.",
        ),
        QAItem(
            question="How was the mystery resolved?",
            answer=f"The truth was that {case.motive} Then {case.repair}",
        ),
    ]
    world_qa = [
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is an early detail or warning that becomes meaningful later in a story.",
        ),
        QAItem(
            question="What does a Whodunit usually ask?",
            answer="A Whodunit asks who caused a puzzling event and invites the reader to weigh clues before the reveal.",
        ),
        QAItem(
            question="Why should a clue be checked before someone is blamed?",
            answer="A clue may show where something happened without proving who caused it, so careful questions help protect innocent people.",
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
        print("--- world model state ---")
        for entity in sample.world.entities.values():
            details = [f"location={entity.location}"]
            if entity.owner:
                details.append(f"owner={entity.owner}")
            if entity.meters:
                details.append(f"meters={entity.meters}")
            if entity.memes:
                details.append(f"memes={entity.memes}")
            print(f"  {entity.id}: {entity.type} " + " ".join(details))
        print(f"  facts: {sample.world.facts}")
    if qa:
        print("\n== prompts ==")
        for index, prompt in enumerate(sample.prompts, 1):
            print(f"{index}. {prompt}")
        print("\n== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        print("\n== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show feature/1.\n#show case_has/2."))
        return
    if args.verify:
        result = asp_verify()
        if result:
            sys.exit(result)
        test_params = StoryParams(
            elder="Alden",
            young_detective="Finn",
            manor="Willow House",
            heirloom="a silver pocket watch",
            seed=19,
            case="pocket_watch",
            telling_mode="dialogue",
        )
        sample = generate(test_params)
        if "foreshadowing" not in sample.story.lower() or not sample.world.facts["solved"]:
            print("MISMATCH: generated story did not exercise the solved foreshadowing case.")
            sys.exit(1)
        print("OK: generated story exercises the Python world model.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams("Alden", "Finn", "Willow House", "a silver pocket watch", 101, "pocket_watch", "dialogue"),
            StoryParams("Beatrice", "Ivy", "Foxglove Hall", "a blue glass bird", 202, "glass_bird", "warning"),
            StoryParams("Cora", "Leo", "Mossy Manor", "an amber brooch", 303, "amber_brooch", "question"),
            StoryParams("Edwin", "Mina", "The Lantern Cottage", "a brass music box", 404, "music_box", "quiet"),
        ]
        samples = [generate(params) for params in curated]
    else:
        seen: set[str] = set()
        attempt = 0
        while len(samples) < max(1, args.n):
            attempt += 1
            seed = base_seed + attempt
            params = resolve_params(args, random.Random(seed))
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show feature/1.\n#show case_has/2."))
        print(json.dumps({"feature": asp.atoms(model, "feature"), "case_has": asp.atoms(model, "case_has")}, indent=2))
        return

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([sample.to_dict() for sample in samples], indent=2, ensure_ascii=False))
        return

    for index, sample in enumerate(samples):
        header = ""
        if args.all:
            header = f"### {sample.params.elder} and {sample.params.young_detective}"
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
