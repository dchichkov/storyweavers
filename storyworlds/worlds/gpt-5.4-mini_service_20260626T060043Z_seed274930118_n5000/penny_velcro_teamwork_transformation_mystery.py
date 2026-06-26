#!/usr/bin/env python3
"""
storyworlds/worlds/penny_velcro_teamwork_transformation_mystery.py
===================================================================

A small mystery storyworld about a missing penny, a velcro clue, and a
teamwork-driven transformation.

A seed tale behind the model:
---
A child notices one penny missing from a tin of coins. The child and a helper
look for clues around a playroom and hallway. A velcro strip on a bag, shoe,
or notebook makes a soft ripping sound and points to the hiding place. Together
they move a few small things, and the missing penny is found. The search turns
into a happy little detective team, and the child feels transformed from puzzled
to proud.

World shape:
- Physical meters track where the penny is, whether clues are stuck, and how
  much searching has happened.
- Emotional memes track puzzlement, teamwork, suspicion, and relief.
- The story should feel like a mystery: a missing object, a clue, a search,
  a reveal, and a change in the characters.

This script is self-contained and uses only the stdlib plus the shared
storyworlds/results.py and storyworlds/asp.py helpers.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Scene:
    place: str
    affordances: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    place: str
    reveal: str
    action: str


@dataclass
class StoryParams:
    place: str
    clue: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.scene)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "playroom": Scene(place="the playroom", affordances={"search"}),
    "hallway": Scene(place="the hallway", affordances={"search"}),
    "kitchen": Scene(place="the kitchen", affordances={"search"}),
    "closet": Scene(place="the closet", affordances={"search"}),
}

CLUES = {
    "velcro_bag": Clue(
        id="velcro_bag",
        label="a velcro bag",
        place="playroom",
        reveal="a penny stuck to the fuzzy flap",
        action="open the flap carefully",
    ),
    "velcro_shoe": Clue(
        id="velcro_shoe",
        label="a velcro shoe strap",
        place="hallway",
        reveal="the penny had clicked under the strap",
        action="lift the strap gently",
    ),
    "velcro_notebook": Clue(
        id="velcro_notebook",
        label="a velcro notebook pocket",
        place="kitchen",
        reveal="the penny had slipped into the pocket",
        action="peel the pocket apart",
    ),
    "velcro_box": Clue(
        id="velcro_box",
        label="a velcro puzzle box",
        place="closet",
        reveal="the penny hid in the box lining",
        action="open the box and look inside",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe", "Ella"]
BOY_NAMES = ["Ben", "Leo", "Max", "Theo", "Finn", "Sam"]
HELPERS = ["mother", "father", "grandma", "big sister", "big brother"]
MYSTERY_WORDS = ["mystery", "clue", "search", "hidden", "discover", "puzzle"]


def narration_phrase(place: str) -> str:
    return {
        "the playroom": "The playroom was full of toy bins and soft carpet squares.",
        "the hallway": "The hallway was narrow, with shoes lined up like quiet guards.",
        "the kitchen": "The kitchen smelled warm, and little things waited on the counter.",
        "the closet": "The closet was dim and still, with boxes stacked like sleeping blocks.",
    }[place]


def pronoun_for_gender(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def possessive_for_gender(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def prize_risk(clue: Clue) -> bool:
    return clue.label.startswith("a velcro")


def select_transform(clue: Clue) -> str:
    return {
        "velcro_bag": "a tidy detective bag with a clear pocket",
        "velcro_shoe": "a careful pair of shoes with no loose strap",
        "velcro_notebook": "a clue notebook with a neat front flap",
        "velcro_box": "a tiny treasure box with a bright label",
    }[clue.id]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, scene in SETTINGS.items():
        if "search" not in scene.affordances:
            continue
        for clue_id, clue in CLUES.items():
            if clue.place == place:
                combos.append((place, clue_id))
    return combos


def _search(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    hero.memes["puzzlement"] = hero.memes.get("puzzlement", 0.0) + 1
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} counted the pennies and found one was missing. "
        f"{hero.pronoun().capitalize()} felt puzzled and looked around {world.scene.place}."
    )
    world.say(
        f"{helper.label_word.capitalize()} came to help, and together they started a small {clue.label} mystery."
    )
    world.facts["search_started"] = True


def _clue(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    if world.facts.get("clue_found"):
        return
    world.facts["clue_found"] = True
    world.facts["clue"] = clue
    hero.memes["suspicion"] = hero.memes.get("suspicion", 0.0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1
    world.say(
        f"They noticed {clue.label}. It made a soft velcro sound, which felt like a clue."
    )


def _reveal(world: World, hero: Entity, helper: Entity, clue: Clue) -> None:
    if world.facts.get("reveal_done"):
        return
    world.facts["reveal_done"] = True
    world.facts["transform"] = select_transform(clue)
    hero.memes["teamwork"] = hero.memes.get("teamwork", 0.0) + 1
    helper.memes["teamwork"] = helper.memes.get("teamwork", 0.0) + 1
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    hero.memes["puzzlement"] = 0.0
    world.say(f"Together they {clue.action}, and the missing penny appeared.")
    world.say(
        f"It had been hiding because {clue.reveal}. The little mystery was solved."
    )


def _transform(world: World, hero: Entity, helper: Entity) -> None:
    if world.facts.get("transformed"):
        return
    world.facts["transformed"] = True
    world.say(
        f"Then they used the discovery to transform the old search into something better: "
        f"{world.facts['transform']}."
    )
    world.say(
        f"{hero.id} stopped feeling confused and started feeling like a real detective, with {helper.label_word} smiling beside {hero.pronoun('object')}."
    )


def tell(scene: Scene, clue: Clue, hero_name: str, gender: str, helper_kind: str) -> World:
    world = World(scene)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_kind))
    penny = world.add(Entity(id="penny", type="coin", label="penny", phrase="a small copper penny"))

    world.facts.update(hero=hero, helper=helper, clue=clue, penny=penny, scene=scene)

    world.say(
        f"{hero.id} found a tin with a penny missing, and {hero.pronoun('possessive')} eyes went wide."
    )
    world.say(narration_phrase(scene.place))

    world.para()
    _search(world, hero, helper, clue)
    world.say(
        f"{hero.id} and {helper.label_word} moved slowly, because a mystery needs careful looking."
    )

    world.para()
    _clue(world, hero, helper, clue)
    _reveal(world, hero, helper, clue)

    world.para()
    _transform(world, hero, helper)
    world.say(
        f"In the end, the penny was back where it belonged, and the little team had changed a plain search into a happy discovery."
    )

    return world


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, scene in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(scene.affordances):
            lines.append(asp.fact("affords", sid, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_at", cid, clue.place))
        lines.append(asp.fact("velcro_clue", cid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Clue) :- affords(Place, search), clue_at(Clue, Place), velcro_clue(Clue).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery storyworld about a penny and a velcro clue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place or args.clue:
        combos = [
            (p, c) for p, c in combos
            if (args.place is None or p == args.place)
            and (args.clue is None or c == args.clue)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, clue_id = rng.choice(sorted(combos))
    clue = CLUES[clue_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, clue=clue_id, name=name, gender=gender, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    clue = f["clue"]
    return [
        f'Write a short mystery story for a young child about a missing penny and {clue.label}.',
        f"Tell a gentle teamwork story where {hero.id} and {f['helper'].label_word} solve a penny mystery with a velcro clue.",
        f"Write a child-facing story that begins with a missing penny, includes velcro, and ends with a happy transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    clue = f["clue"]
    qa = [
        QAItem(
            question=f"What was missing at the start of the story?",
            answer="A penny was missing, so the search began like a little mystery.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for the penny?",
            answer=f"{helper.label_word.capitalize()} helped {hero.id}, and they searched together as a team.",
        ),
        QAItem(
            question=f"What clue did they notice?",
            answer=f"They noticed {clue.label}, and the velcro sound made it feel important.",
        ),
        QAItem(
            question=f"What happened when they used the clue?",
            answer=f"They found the penny and the search transformed into a solved mystery.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is velcro?",
            answer="Velcro is a fastener that sticks together and makes a soft ripping sound when pulled apart.",
        ),
        QAItem(
            question="What is a penny?",
            answer="A penny is a small coin.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that people try to figure out by looking for clues.",
        ),
        QAItem(
            question="What does transformation mean?",
            answer="Transformation means something changes into a new form or becomes different in an important way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        CLUES[params.clue],
        params.name,
        params.gender,
        params.helper,
    )
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


CURATED = [
    StoryParams(place="playroom", clue="velcro_bag", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="hallway", clue="velcro_shoe", name="Leo", gender="boy", helper="father"),
    StoryParams(place="kitchen", clue="velcro_notebook", name="Nora", gender="girl", helper="grandma"),
    StoryParams(place="closet", clue="velcro_box", name="Ben", gender="boy", helper="big sister"),
]


def explain_rejection() -> str:
    return "(No story: this mystery needs a velcro clue in the same place as the search.)"


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, clue) combos:\n")
        for place, clue in combos:
            print(f"  {place:9} {clue}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: clue={p.clue}, place={p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
