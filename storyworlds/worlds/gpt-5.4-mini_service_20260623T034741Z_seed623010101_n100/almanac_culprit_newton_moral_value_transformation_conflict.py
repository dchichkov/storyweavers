#!/usr/bin/env python3
"""
storyworlds/worlds/almanac_culprit_newton_moral_value_transformation_conflict.py
==============================================================================

A small rhyming storyworld about a missing almanac page, a blamed culprit, and a
gentle transformation from conflict into honesty and repair.

Seed premise:
- A child studies an old almanac, a page goes missing, and the room turns tense.
- The suspected culprit is found through state, not guesswork.
- A truth-telling turn changes the emotional weather.
- The ending proves that honesty, repair, and kindness transformed the scene.

This script follows the Storyweavers contract:
- standalone stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for --seed, -n, --all, --trace, --qa, --json, --asp, --verify, --show-asp
- world model with physical meters and emotional memes
- inline ASP twin plus Python reasonableness gate
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
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    indoors: bool
    affords: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspicion:
    id: str
    label: str
    phrase: str
    cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Repair:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    label: str
    phrase: str
    joy_gain: float
    calm_gain: float
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    if child.memes.get("blame", 0.0) >= THRESHOLD and child.memes.get("hurt", 0.0) >= THRESHOLD:
        sig = ("conflict", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["conflict"] = child.memes.get("conflict", 0.0) + 1.0
            out.append("Tense words began to bite.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    child = world.get("child")
    if culprit.memes.get("truth", 0.0) >= THRESHOLD and culprit.memes.get("regret", 0.0) >= THRESHOLD:
        sig = ("transform", culprit.id)
        if sig not in world.fired:
            world.fired.add(sig)
            culprit.memes["courage"] = culprit.memes.get("courage", 0.0) + 1.0
            child.memes["conflict"] = 0.0
            child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0
            out.append("Honest hearts began to bloom.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    culprit = world.get("culprit")
    child = world.get("child")
    almanac = world.get("almanac")
    if culprit.memes.get("repair", 0.0) >= THRESHOLD and almanac.meters.get("page_fixed", 0.0) >= THRESHOLD:
        sig = ("repair", almanac.id)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["warmth"] = child.memes.get("warmth", 0.0) + 1.0
            out.append("The page was made right again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_conflict, _r_transformation, _r_repair):
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for suspicion_id in SUSPICIONS:
            for repair_id in REPAIRS:
                if place.affords & {"reading", "searching", "repairing"}:
                    combos.append((place_id, suspicion_id, repair_id))
    return combos


@dataclass
class StoryParams:
    place: str
    suspicion: str
    repair: str
    child_name: str
    child_gender: str
    culprit_name: str
    culprit_gender: str
    seed: Optional[int] = None


PLACES = {
    "study": Place(
        id="study",
        label="the quiet study",
        indoors=True,
        affords={"reading", "searching", "repairing"},
        tags={"book", "quiet"},
    ),
    "attic": Place(
        id="attic",
        label="the dusty attic",
        indoors=True,
        affords={"reading", "searching", "repairing"},
        tags={"dust", "searching"},
    ),
    "kitchen": Place(
        id="kitchen",
        label="the sunny kitchen",
        indoors=True,
        affords={"reading", "searching", "repairing"},
        tags={"home", "searching"},
    ),
}

SUSPICIONS = {
    "missing_page": Suspicion(
        id="missing_page",
        label="missing page",
        phrase="a page that had gone astray",
        cause="a torn corner on the desk",
        tags={"almanac", "page", "missing"},
    ),
    "ink_smudge": Suspicion(
        id="ink_smudge",
        label="ink smudge",
        phrase="a dark smudge in the almanac",
        cause="inky fingertips on the table",
        tags={"almanac", "ink"},
    ),
    "scribble_note": Suspicion(
        id="scribble_note",
        label="scribble note",
        phrase="a scribble note tucked inside",
        cause="a little note stuck under the cover",
        tags={"almanac", "note"},
    ),
}

REPAIRS = {
    "tape_page": Repair(
        id="tape_page",
        label="tape repair",
        phrase="tape to mend the torn page",
        effect="the page could stay put",
        tags={"repair", "tape"},
    ),
    "glue_corner": Repair(
        id="glue_corner",
        label="glue repair",
        phrase="glue for the torn corner",
        effect="the corner could lie flat again",
        tags={"repair", "glue"},
    ),
}

TRANSFORMS = {
    "soften": Transformation(
        id="soften",
        label="softening",
        phrase="a softening of the room",
        joy_gain=1.0,
        calm_gain=1.0,
        tags={"moral_value", "conflict"},
    ),
}


GIRL_NAMES = ["Mia", "Nora", "Lina", "Ava", "Rose"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Theo", "Owen"]


class StoryLogic:
    pass


def _init_entity_meters() -> dict[str, float]:
    return {
        "tear": 0.0,
        "mess": 0.0,
        "page_fixed": 0.0,
    }


def _init_entity_memes() -> dict[str, float]:
    return {
        "curiosity": 0.0,
        "blame": 0.0,
        "hurt": 0.0,
        "conflict": 0.0,
        "truth": 0.0,
        "regret": 0.0,
        "repair": 0.0,
        "courage": 0.0,
        "trust": 0.0,
        "warmth": 0.0,
    }


def tell(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=params.child_gender, label=params.child_name, meters=_init_entity_meters(), memes=_init_entity_memes()))
    culprit = world.add(Entity(id="culprit", kind="character", type=params.culprit_gender, label=params.culprit_name, meters=_init_entity_meters(), memes=_init_entity_memes()))
    almanac = world.add(Entity(id="almanac", type="book", label="the almanac", phrase="an old almanac", meters=_init_entity_meters(), memes=_init_entity_memes(), tags={"almanac"}))

    world.facts["child"] = child
    world.facts["culprit"] = culprit
    world.facts["almanac"] = almanac
    world.facts["place"] = place
    world.facts["suspicion"] = SUSPICIONS[params.suspicion]
    world.facts["repair"] = REPAIRS[params.repair]
    world.facts["transformation"] = TRANSFORMS["soften"]

    child.memes["curiosity"] = 1.0
    child.memes["hurt"] = 1.0
    almanac.meters["tear"] = 1.0
    child.meters["mess"] = 0.0
    culprit.memes["blame"] = 1.0
    culprit.memes["regret"] = 1.0

    world.say(
        f"In {place.label}, {child.label} found {almanac.phrase}, "
        f"and wondered what story it would tell."
    )
    world.say(
        f"But something felt wrong: {SUSPICIONS[params.suspicion].phrase}, "
        f"and the air grew tight with a little frown."
    )

    world.para()
    world.say(
        f"{child.label} asked in a rhyme, with a careful little tone, "
        f"\"Who moved the page? Who left it lone?\""
    )
    world.say(
        f"The blame fell soft, then turned to sting; the room became a twangy string."
    )

    child.memes["blame"] = 1.0
    propagate(world, narrate=True)

    world.para()
    culprit.memes["truth"] = 1.0
    world.say(
        f"Then {culprit.label} spoke up true and plain: \"I borrowed it and caused the pain.\""
    )
    world.say(
        f"\"I hid the page to make a game, but now I see my foolish shame.\""
    )

    propagate(world, narrate=True)

    world.para()
    culprit.memes["repair"] = 1.0
    almanac.meters["page_fixed"] = 1.0
    world.say(
        f"Together they used {REPAIRS[params.repair].phrase}, "
        f"so {REPAIRS[params.repair].effect}."
    )
    world.say(
        f"The almanac stood neat and right, no longer bent, but snug and bright."
    )

    propagate(world, narrate=True)

    child.memes["warmth"] = child.memes.get("warmth", 0.0) + 1.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1.0

    world.say(
        f"{child.label} forgave {culprit.label}, and smiled with calm delight; "
        f"the quarrel thinned like morning light."
    )
    world.say(
        f"By the final line, the lesson shone: a truthful heart makes wrong things known, "
        f"and what began as sharp and sore became a kinder room once more."
    )

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    c = world.facts["child"]
    culprit = world.facts["culprit"]
    place = world.facts["place"]
    return [
        f"Write a rhyming story about {c.label}, an almanac, and a culprit in {place.label}.",
        f"Tell a moral tale where {culprit.label} confesses after a conflict over the almanac.",
        f"Write a short rhyming story that begins with a missing page and ends with repair and forgiveness.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    culprit = world.facts["culprit"]
    suspicion = world.facts["suspicion"]
    repair = world.facts["repair"]
    almanac = world.facts["almanac"]
    return [
        QAItem(
            question=f"Why did {c.label} feel upset at first?",
            answer=(
                f"{c.label} felt upset because the almanac had a {suspicion.label} and the room felt tense. "
                f"The missing part made it seem like something important had been taken."
            ),
        ),
        QAItem(
            question=f"Who turned out to be the culprit?",
            answer=(
                f"{culprit.label} was the culprit, because {culprit.label} admitted what happened. "
                f"That honest confession changed the conflict into a calmer moment."
            ),
        ),
        QAItem(
            question=f"How was the almanac made right again?",
            answer=(
                f"They used {repair.phrase}, so the almanac could be repaired and look neat again. "
                f"That fix proved the problem was not left hanging."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an almanac?",
            answer=(
                "An almanac is a little book of useful facts, like weather or dates. "
                "People keep it nearby because it helps them plan and learn."
            ),
        ),
        QAItem(
            question="What does a culprit mean?",
            answer=(
                "A culprit is the person who caused a problem or did something wrong. "
                "Finding the culprit helps people fix the trouble and tell the truth."
            ),
        ),
        QAItem(
            question="What is a moral value?",
            answer=(
                "A moral value is a good rule for how to treat people, like honesty or kindness. "
                "It helps a story teach what should matter when there is a choice."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}")
    return "\n".join(out)


def valid_story(params: StoryParams) -> bool:
    return params.place in PLACES and params.suspicion in SUSPICIONS and params.repair in REPAIRS


CURATED = [
    StoryParams(place="study", suspicion="missing_page", repair="tape_page", child_name="Mia", child_gender="girl", culprit_name="Newton", culprit_gender="boy"),
    StoryParams(place="attic", suspicion="ink_smudge", repair="glue_corner", child_name="Noah", child_gender="boy", culprit_name="Newton", culprit_gender="boy"),
]


def explain_rejection() -> str:
    return "(No story: the chosen parts do not form a plausible almanac conflict.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming almanac storyworld with a culprit, moral value, transformation, and conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspicion", choices=SUSPICIONS)
    ap.add_argument("--repair", choices=REPAIRS)
    ap.add_argument("--child-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--culprit-name")
    ap.add_argument("--culprit-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.suspicion is None or c[1] == args.suspicion)
              and (args.repair is None or c[2] == args.repair)]
    if not combos:
        raise StoryError(explain_rejection())
    place, suspicion, repair = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    culprit_gender = args.culprit_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    culprit_name = args.culprit_name or "Newton"
    return StoryParams(
        place=place,
        suspicion=suspicion,
        repair=repair,
        child_name=child_name,
        child_gender=child_gender,
        culprit_name=culprit_name,
        culprit_gender=culprit_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if not valid_story(params):
        raise StoryError(explain_rejection())
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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
    for s in SUSPICIONS.values():
        lines.append(asp.fact("suspicion", s.id))
    for r in REPAIRS.values():
        lines.append(asp.fact("repair", r.id))
    lines.append(asp.fact("value", "honesty"))
    lines.append(asp.fact("value", "kindness"))
    lines.append(asp.fact("feature", "moral_value"))
    lines.append(asp.fact("feature", "transformation"))
    lines.append(asp.fact("feature", "conflict"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,S,R) :- place(P), suspicion(S), repair(R).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import traceback
    try:
        gate_ok = set(asp_valid_combos()) == set(valid_combos())
    except Exception:
        traceback.print_exc()
        return 1
    if not gate_ok:
        print("MISMATCH between ASP and Python valid_combos()")
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            print("Smoke test failed: empty story")
            return 1
    except Exception:
        traceback.print_exc()
        return 1
    print("OK: ASP gate matches Python, and generation smoke test passed.")
    return 0


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
