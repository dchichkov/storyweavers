#!/usr/bin/env python3
"""
A child-friendly mystery storyworld about a living hereditary goo and a family
conflict that can be repaired with careful observation and honest conversation.
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

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class MysteryCase:
    id: str
    place: str
    goo_color: str
    family_object: str
    clue: str
    false_belief: str
    conflict: str
    discovery: str
    dialogue_clue: str
    repair: str
    lesson: str
    ending: str


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


@dataclass
class StoryParams:
    place: str = "old_house"
    activity: str = "solve_mystery"
    name: str = "Luna"
    gender: str = "girl"
    cousin_name: str = "Milo"
    cousin_gender: str = "boy"
    trait: str = "curious"
    seed: Optional[int] = None


PLACES = {
    "old_house": "the old family house",
}

ACTIVITIES = {
    "solve_mystery": "solve a mystery",
}

GIRL_NAMES = ["Luna", "Mara", "Iris", "Nell", "Cora"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Owen", "Jude"]
TRAITS = ["curious", "patient", "brave", "careful", "thoughtful"]

CASES = [
    MysteryCase(
        "blue_jar",
        "the pantry",
        "blue",
        "a silver family jar",
        "a trail of blue drops leading beneath the bread shelf",
        "that someone had stolen the jar's old blue lid",
        "Luna blamed Milo, while Milo insisted that Luna had hidden it to win the investigation",
        "the drops glowed whenever the jar was near its lid",
        "Milo said, 'I saw the goo crawl under the shelf before either of us touched the jar.'",
        "they followed the living goo's trail and found the lid inside a warm basket",
        "evidence matters more than a quick accusation, especially when family history makes tempers hot",
        "the hereditary jar rested safely on the shelf while the blue goo curled around its lid like a tiny wave",
    ),
    MysteryCase(
        "attic_key",
        "the dusty attic",
        "green",
        "a brass key passed through the family",
        "three green fingerprints on the locked trunk",
        "that one cousin had taken the hereditary key and was pretending not to know",
        "Luna and Milo argued so loudly that the goo hid behind an old quilt",
        "the fingerprints ended at a loose floorboard, not at either child",
        "Milo said, 'The goo is showing us where it went. We should watch before we choose a culprit.'",
        "they lifted the board and found the key tucked beside a jar of sleeping goo",
        "a conflict becomes smaller when people pause, listen, and test an idea together",
        "the brass key shone beside the green goo, which blinked as if it had solved the mystery too",
    ),
    MysteryCase(
        "music_box",
        "the upstairs hall",
        "gold",
        "a hereditary music box",
        "a golden smear across the music box and a missing tune",
        "that the children had each secretly wound it too hard",
        "their grandmother's warning made both children fear they had broken a family treasure",
        "the goo pulsed in time with a hidden loose gear",
        "Milo said, 'Listen to the goo. It is humming only when the little gear turns.'",
        "they opened the back carefully and reseated the gear instead of blaming each other",
        "a mystery can reveal a shared problem when fear first makes everyone look for a person to blame",
        "the music box played a bright tune while the gold goo danced in a shining ring",
    ),
    MysteryCase(
        "garden_lock",
        "the moonlit garden",
        "violet",
        "an iron gate lock inherited by the family",
        "violet dots appearing on stones beside the gate",
        "that someone had marked the garden path without permission",
        "Luna thought Milo had made the marks, and Milo thought Luna had moved the stepping stones",
        "the dots formed a pattern pointing toward a buried seed pouch",
        "Milo said, 'The goo is not accusing us. It is drawing a map.'",
        "they dug up the pouch and planted the family's old moonflower seeds together",
        "curiosity can turn conflict into cooperation when clues are treated as invitations to learn",
        "violet blossoms opened beside the gate while the live goo glimmered among their roots",
    ),
    MysteryCase(
        "portrait_frame",
        "the quiet study",
        "amber",
        "a portrait frame carried down through generations",
        "amber goo beneath the frame and a torn paper corner",
        "that one child had tried to remove the portrait",
        "both children pulled the frame in opposite directions and nearly dropped it",
        "the torn corner matched a note hidden behind the portrait",
        "Milo said, 'The note may explain the goo. Let us put the frame down before we argue again.'",
        "they read the note and learned that the goo protected the family's secret history",
        "careful hands and shared reading can repair damage caused by a hurried struggle",
        "the portrait hung straight again, with amber goo glowing softly beside the hidden note",
    ),
]


@dataclass
class StoryState:
    case: MysteryCase
    child: Entity
    cousin: Entity
    goo: Entity
    suspicion: float = 0.0
    understanding: float = 0.0
    conflict: float = 0.0
    resolved: bool = False


def reasonable(params: StoryParams) -> bool:
    return (
        params.place in PLACES
        and params.activity in ACTIVITIES
        and params.name != params.cousin_name
        and params.gender in {"girl", "boy"}
        and params.cousin_gender in {"girl", "boy"}
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="A mystery storyworld about live hereditary goo and a repaired family conflict."
    )
    parser.add_argument("--place", choices=PLACES)
    parser.add_argument("--activity", choices=ACTIVITIES)
    parser.add_argument("--gender", choices=["girl", "boy"])
    parser.add_argument("--cousin-gender", dest="cousin_gender", choices=["girl", "boy"])
    parser.add_argument("--name")
    parser.add_argument("--cousin-name", dest="cousin_name")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("-n", type=int, default=1)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--trace", action="store_true")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--asp", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--show-asp", action="store_true")
    return parser


def names_for(gender: str) -> list[str]:
    return GIRL_NAMES if gender == "girl" else BOY_NAMES


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or "old_house"
    activity = args.activity or "solve_mystery"
    gender = args.gender or rng.choice(["girl", "boy"])
    cousin_gender = args.cousin_gender or ("boy" if gender == "girl" else "girl")
    name = args.name or rng.choice(names_for(gender))
    cousin_name = args.cousin_name or rng.choice(names_for(cousin_gender))
    if name == cousin_name:
        raise StoryError("The two family members must have different names.")
    return StoryParams(
        place=place,
        activity=activity,
        name=name,
        gender=gender,
        cousin_name=cousin_name,
        cousin_gender=cousin_gender,
        trait=rng.choice(TRAITS),
    )


def add_meter(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.meters[key] = entity.meters.get(key, 0.0) + amount


def add_meme(entity: Entity, key: str, amount: float = 1.0) -> None:
    entity.memes[key] = entity.memes.get(key, 0.0) + amount


def tell(params: StoryParams) -> World:
    rng_value = params.seed if params.seed is not None else sum(
        ord(c) for c in params.name + params.cousin_name
    )
    case = CASES[rng_value % len(CASES)]
    child = Entity(params.name, "character", params.gender)
    cousin = Entity(params.cousin_name, "character", params.cousin_gender)
    goo = Entity("living_goo", "creature", "goo", case.goo_color)
    world = World()
    world.add(child)
    world.add(cousin)
    world.add(goo)
    state = StoryState(case, child, cousin, goo)

    world.say(
        f"{params.trait.capitalize()} {params.name} visited {PLACES[params.place]} "
        f"to {ACTIVITIES[params.activity]} with {params.cousin_name}."
    )
    world.say(
        f"In {case.place}, they found {case.family_object}, a treasure that had belonged "
        "to their family for generations."
    )
    world.say(
        f"Beside it lived a small patch of {case.goo_color} goo. It was not ordinary goo: "
        "it could live, wiggle, and shine whenever an old family secret was near."
    )
    world.say(f"That morning, {case.clue}.")
    world.say(
        f'"You must have caused this," {params.name} said. {params.cousin_name} frowned. '
        f'"You always think the hereditary treasures belong to your side of the family."'
    )
    state.conflict += 1
    state.suspicion += 1
    add_meme(child, "suspicion")
    add_meme(cousin, "hurt")
    add_meter(goo, "movement")

    world.para()
    world.say(
        f"The conflict grew until {case.conflict}. Then the goo slipped from the object "
        "and left a glimmering trail across the floor."
    )
    world.say(
        f"{params.name} reached for it, but the goo darted away. {params.cousin_name} "
        f"noticed that {case.discovery}."
    )
    world.say(
        f'"Wait," {params.cousin_name} said. "{case.dialogue_clue}"'
    )
    world.say(
        f"{params.name} stopped pulling and watched. The clue did not point at either "
        "child; it pointed toward a hidden part of the old house."
    )
    add_meter(cousin, "attention")
    add_meter(child, "patience")
    add_meme(cousin, "kindness")
    state.suspicion -= 1
    state.understanding += 1

    world.para()
    world.say(
        f"Together, the children followed the goo. They {case.repair}."
    )
    world.say(
        f'"I am sorry I accused you," {params.name} said. '
        f'"I am sorry I accused you too," {params.cousin_name} replied. '
        '"Let us solve family mysteries by looking for clues before choosing sides."'
    )
    world.say(
        f"They understood that {case.lesson}. The living goo curled between them, "
        "warm and harmless now."
    )
    world.say(f"At last, {case.ending}")
    add_meter(child, "cooperation")
    add_meter(cousin, "cooperation")
    add_meme(child, "relief")
    add_meme(cousin, "trust")
    state.resolved = True

    world.facts.update(
        case=case,
        child=child,
        cousin=cousin,
        goo=goo,
        state=state,
        conflict_repaired=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    case = world.facts["case"]
    child = world.facts["child"]
    cousin = world.facts["cousin"]
    return [
        f"Write a child-friendly mystery in {case.place} about {child.id} and {cousin.id}.",
        f"Include live {case.goo_color} goo, a hereditary family object, and a conflict repaired by evidence.",
        f"End with a concrete image proving that the mystery and family conflict are resolved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    case = world.facts["case"]
    child = world.facts["child"]
    cousin = world.facts["cousin"]
    return [
        QAItem(
            f"What caused the conflict between {child.id} and {cousin.id}?",
            f"They blamed each other when {case.conflict}. Their fear about the hereditary object made them accuse one another before checking the clues.",
        ),
        QAItem(
            "What clue helped solve the mystery?",
            f"The important clue was that {case.discovery}. It showed that the living goo was leading them toward the truth rather than blaming either child.",
        ),
        QAItem(
            f"How did {child.id} and {cousin.id} repair their conflict?",
            f"They {case.repair}. Then they apologized and agreed to look for evidence before choosing sides.",
        ),
        QAItem(
            "What did the living goo do in the story?",
            f"The {case.goo_color} goo moved and glowed to guide the children toward the hidden clue connected with the family object.",
        ),
        QAItem(
            "What final image showed that everything was peaceful?",
            f"{case.ending} That image showed that the mystery was solved and the family conflict had been repaired.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            "What is a mystery?",
            "A mystery is a question or problem whose answer must be discovered by noticing clues and reasoning carefully.",
        ),
        QAItem(
            "What does hereditary mean?",
            "Hereditary means passed through a family from older generations to younger generations.",
        ),
        QAItem(
            "Why is it helpful to look for evidence during a conflict?",
            "Evidence helps people test what happened instead of blaming one another based only on fear or guesses.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    lines.extend(f"{i}. {prompt}" for i, prompt in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.extend([f"Q: {item.question}", f"A: {item.answer}"])
    return "\n".join(lines)


ASP_RULES = r"""
child(C) :- child_name(C).
cousin(K) :- cousin_name(K).
goo(G) :- goo_name(G).
mystery(C) :- child(C), goo(G).
conflict(C,K) :- child(C), cousin(K), accusation(C,K).
evidence_found(C) :- child(C), observes(C).
apology(C,K) :- child(C), cousin(K), conflict(C,K), speaks_kindly(C,K).
resolved(C,K) :- conflict(C,K), evidence_found(C), apology(C,K).
"""


def asp_facts() -> str:
    import asp

    return "\n".join(
        [
            asp.fact("child_name", "child"),
            asp.fact("cousin_name", "cousin"),
            asp.fact("goo_name", "goo"),
            asp.fact("accusation", "child", "cousin"),
            asp.fact("observes", "child"),
            asp.fact("speaks_kindly", "child", "cousin"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show resolved/2."))
    result = bool(asp.atoms(model, "resolved"))
    if result:
        print("OK: ASP and Python conflict-repair reasoning agree.")
        return 0
    print("MISMATCH between ASP and Python reasoning.")
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for entity in world.entities.values():
        meters = {k: v for k, v in entity.meters.items() if v}
        memes = {k: v for k, v in entity.memes.items() if v}
        lines.append(
            f"  {entity.id:12} ({entity.type:8}) meters={meters} memes={memes}"
        )
    state = world.facts["state"]
    lines.append(
        f"  conflict={state.conflict} suspicion={state.suspicion} "
        f"understanding={state.understanding} resolved={state.resolved}"
    )
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if not reasonable(params):
        raise StoryError(
            "This world requires the old family house, a mystery activity, and two different names."
        )
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def valid_story_params() -> list[StoryParams]:
    return [
        StoryParams(
            place="old_house",
            activity="solve_mystery",
            name="Luna",
            gender="girl",
            cousin_name="Milo",
            cousin_gender="boy",
            trait="curious",
        ),
        StoryParams(
            place="old_house",
            activity="solve_mystery",
            name="Theo",
            gender="boy",
            cousin_name="Iris",
            cousin_gender="girl",
            trait="patient",
        ),
    ]


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
        print(asp_program("#show resolved/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show resolved/2."))
        print("ASP model:", ", ".join(str(atom) for atom in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(params) for params in valid_story_params()]
    else:
        seen: set[str] = set()
        index = 0
        while len(samples) < args.n and index < max(50, args.n * 20):
            seed = base_seed + index
            index += 1
            try:
                params = resolve_params(args, random.Random(seed))
                params.seed = seed
                sample = generate(params)
            except StoryError as error:
                print(error)
                return
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
        header = ""
        if args.all:
            header = (
                f"### {sample.params.name} and {sample.params.cousin_name} "
                "solve a family mystery"
            )
        elif len(samples) > 1:
            header = f"### variant {index + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if index < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
