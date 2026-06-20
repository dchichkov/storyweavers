#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/asphalt_foreshadowing_transformation_ghost_story.py
===================================================================================

A standalone story world for a small ghost story domain built from the seed words:
* asphalt
* foreshadowing
* transformation

Premise:
--------
A child hears a spooky warning about a cracked asphalt path at dusk. The warning
foreshadows that something hidden beneath the road is awake. A gentle ghost helps
guide the child, and the final transformation reveals the path was protecting a
buried garden all along.

This world uses typed entities with accumulating physical meters and emotional
memes, a forward-chained rule engine, a prediction beat, a reasonableness gate,
and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVE_MIN = 5.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Place:
    id: str
    label: str
    atmosphere: str
    asphalt: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Omen:
    id: str
    signal: str
    line: str
    truth: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Transformation:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def _r_foreshadow(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    path = world.get("path")
    ghost = world.get("ghost")
    if child.meters["listening"] >= THRESHOLD and ("foreshadow" not in world.fired):
        world.fired.add(("foreshadow",))
        child.memes["worry"] += 1
        path.meters["cold"] += 1
        ghost.meters["near"] += 1
        out.append("__omen__")
    return out


def _r_transform(world: World) -> list[str]:
    out: list[str] = []
    if world.get("path").meters["uncovered"] >= THRESHOLD and ("transform" not in world.fired):
        world.fired.add(("transform",))
        world.get("garden").meters["revealed"] += 1
        world.get("ghost").memes["sadness"] += 0.5
        out.append("__transform__")
    return out


CAUSAL_RULES = [
    Rule("foreshadow", "social", _r_foreshadow),
    Rule("transform", "physical", _r_transform),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_transform(path: Place, trans: Transformation) -> bool:
    return path.asphalt and trans.sense >= SENSE_MIN


def best_transformation() -> Transformation:
    return max(TRANSFORMATIONS.values(), key=lambda t: t.sense)


def predict_path(world: World) -> dict:
    sim = world.copy()
    _open_path(sim, narrate=False)
    return {
        "revealed": sim.get("garden").meters["revealed"] >= THRESHOLD,
        "near": sim.get("ghost").meters["near"] >= THRESHOLD,
    }


def _open_path(world: World, narrate: bool = True) -> None:
    world.get("path").meters["uncovered"] += 1
    propagate(world, narrate=narrate)


def tell(place: Place, omen: Omen, trans: Transformation,
         child_name: str = "Mina", child_gender: str = "girl",
         parent_type: str = "mother", ghost_name: str = "Willow") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    ghost = world.add(Entity(id=ghost_name, kind="character", type="ghost", role="ghost", label="a small ghost"))
    path = world.add(Entity(id="path", type="path", label="the asphalt path"))
    garden = world.add(Entity(id="garden", type="place", label="the buried garden"))
    child.memes["bravery"] = BRAVE_MIN - 1
    child.memes["curiosity"] = 2
    world.facts["place"] = place
    world.facts["omen"] = omen
    world.facts["transformation"] = trans

    world.say(
        f"At dusk, {child.id} stood at {place.label} beside {place.atmosphere}. "
        f"The asphalt was dark and smooth, and one crack ran like a thin black vein."
    )
    world.say(
        f"{ghost_name} drifted near the fence and whispered, "
        f"'{omen.line}'"
    )
    world.say(
        f"The words felt like a warning. {child.id} looked down at the crack, "
        f"and {child.pronoun('possessive')} heart beat a little faster."
    )

    world.para()
    child.memes["listening"] += 1
    world.say(
        f"{parent.label_word.capitalize()} noticed the hush and said, "
        f'"Listen to the old road. Some things are hidden for a reason."'
    )
    pred = predict_path(world)
    world.facts["predicted"] = pred
    if pred["revealed"]:
        world.say(
            f"{child.id} crouched by the crack and heard a soft hum under the asphalt. "
            f"The ghost was not trying to scare {child.pronoun('object')} after all."
        )
    else:
        world.say(
            f"{child.id} only heard the night wind at first, but {child.pronoun('possessive')} "
            f"eyes stayed on the road."
        )

    world.para()
    if can_transform(place, trans):
        world.say(
            f"Then {child.id} brushed away the loose stones and lifted a broken patch. "
            f"The {trans.text}."
        )
        _open_path(world)
        world.say(
            f"The asphalt split open like a dark curtain, and underneath it lay "
            f"a tiny garden with pale flowers that had been sleeping in the earth."
        )
        world.say(
            f"{ghost_name} smiled, lighter than before, because the secret was not a curse. "
            f"It was a place changing back into itself."
        )
        child.memes["wonder"] += 2
        child.memes["fear"] = 0
        world.facts["outcome"] = "transformed"
    else:
        world.say(
            f"{child.id} did not dare touch the road, so the warning stayed a warning. "
            f"The asphalt remained closed and the night kept its secret."
        )
        world.facts["outcome"] = "still"

    world.para()
    if world.facts["outcome"] == "transformed":
        world.say(
            f"By the time the stars came out, {child.id} was no longer afraid of the crack. "
            f"{child.id} had found a hidden garden, and the ghost story had turned gentle."
        )
    else:
        world.say(
            f"{child.id} went inside with {child.pronoun('possessive')} parent, remembering "
            f"that some whispers are only meant to guide the living home."
        )

    world.facts.update(
        child=child,
        parent=parent,
        ghost=ghost,
        path=path,
        garden=garden,
        place=place,
        trans=trans,
    )
    return world


PLACES = {
    "alley": Place("alley", "the narrow alley", "the old brick wall", asphalt=True),
    "driveway": Place("driveway", "the long driveway", "the silent house", asphalt=True),
    "school": Place("school", "the empty schoolyard", "the locked gate", asphalt=True),
}

OMENS = {
    "whisper": Omen("whisper", "whisper", "The road remembers what was buried.", "The road hides old things.", {"ghost", "foreshadow"}),
    "hum": Omen("hum", "hum", "Something under the blacktop is awake.", "Something is hidden below the asphalt.", {"ghost", "foreshadow"}),
    "tap": Omen("tap", "tap", "Do not lift the stone, little one.", "A hidden place may not be safe to open carelessly.", {"ghost", "foreshadow"}),
}

TRANSFORMATIONS = {
    "reveal": Transformation("reveal", 3, 3, "the blacktop came up in a flap, and a soft green smell rose from below", "tried to open the road, but nothing would move", "lifted the broken patch and revealed the hidden garden", {"transform"}),
    "peel": Transformation("peel", 2, 2, "the cracked asphalt peeled back like old skin", "could not peel the road at all", "peeled back the cracked asphalt and found what slept beneath", {"transform"}),
}

NAME_POOL = ["Mina", "Lena", "Noah", "Theo", "Iris", "Ava", "Eli", "Nora"]


@dataclass
@dataclass
class StoryParams:
    place: str
    omen: str
    transformation: str
    child_name: str
    child_gender: str
    parent: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for o in OMENS:
            for t in TRANSFORMATIONS:
                if can_transform(PLACES[p], TRANSFORMATIONS[t]):
                    combos.append((p, o, t))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost story for a 3-to-5-year-old that includes the word "asphalt" and a quiet foreshadowing warning.',
        f"Tell a spooky-but-gentle story where {f['child'].id} hears a ghostly clue beside the asphalt and the road transforms to reveal a secret.",
        f'Write a short ghost story in which a hidden place under asphalt is foreshadowed early and then transformed in the ending.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    ghost = f["ghost"]
    place = f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id}, {ghost.label}, and {parent.label_word}. They are the ones who stand by the asphalt path at dusk."),
        ("What warning did the ghost give?",
         f"{ghost.id} gave a foreshadowing warning that the road remembered old things. That clue hinted that something hidden was waiting under the asphalt."),
    ]
    if f.get("outcome") == "transformed":
        qa.append((
            "What changed at the end?",
            "The cracked asphalt opened up and revealed a hidden garden. The scary-looking road turned into a secret place full of pale flowers."
        ))
        qa.append((
            "Why was the ghost no longer scary?",
            f"The ghost was actually guarding the secret under the road. Once {child.id} saw the garden, the ghost felt gentle instead of frightening."
        ))
    else:
        qa.append((
            "How did the story end?",
            f"{child.id} went back inside and left the asphalt closed. The warning stayed mysterious, and the night kept its secret."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["omen"].tags) | set(world.facts["transformation"].tags) | {"asphalt"}
    out: list[tuple[str, str]] = []
    if "asphalt" in tags:
        out.append(("What is asphalt?", "Asphalt is a dark, hard material used to make roads, driveways, and paths. It can crack when it gets old."))
    if "foreshadow" in tags:
        out.append(("What is foreshadowing?", "Foreshadowing is a clue early in a story that hints something important will happen later. It helps the reader feel a little curious or worried before the change arrives."))
    if "transform" in tags:
        out.append(("What is a transformation in a story?", "A transformation is a change from one form or state into another. In a ghost story, that change can reveal a hidden truth."))
    return out


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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("alley", "whisper", "reveal", "Mina", "girl", "mother"),
    StoryParams("driveway", "hum", "peel", "Noah", "boy", "father"),
    StoryParams("school", "tap", "reveal", "Iris", "girl", "mother"),
]


def explain_rejection(place: Place) -> str:
    if not place.asphalt:
        return "(No story: the transformation only works on an asphalt place with a hidden crack.)"
    return "(No story: this combination does not support a credible ghost-story transformation.)"


def outcome_of(params: StoryParams) -> str:
    return "transformed" if can_transform(PLACES[params.place], TRANSFORMATIONS[params.transformation]) else "still"


ASP_RULES = r"""
valid(P, O, T) :- place(P), omen(O), transformation(T), asphalt_place(P), trans_ok(T).
outcome(transformed) :- chosen_place(P), chosen_transformation(T), asphalt_place(P), trans_ok(T).
outcome(still) :- chosen_place(P), not outcome(transformed).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].asphalt:
            lines.append(asp.fact("asphalt_place", pid))
    for oid in OMENS:
        lines.append(asp.fact("omen", oid))
    for tid, t in TRANSFORMATIONS.items():
        lines.append(asp.fact("transformation", tid))
        if t.sense >= SENSE_MIN:
            lines.append(asp.fact("trans_ok", tid))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_place", params.place), asp.fact("chosen_transformation", params.transformation)])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        print("MISMATCH in valid combos.")
        rc = 1
    samples = [generate(p) for p in CURATED]
    if all(sample.story and sample.story.strip() for sample in samples):
        print("OK: curated stories generate successfully.")
    else:
        print("MISMATCH: story generation failed.")
        rc = 1
    if all(asp_outcome(p) == outcome_of(p) for p in CURATED):
        print("OK: ASP and Python outcomes match.")
    else:
        print("MISMATCH: outcome parity failed.")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with asphalt, foreshadowing, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--transformation", choices=TRANSFORMATIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.omen is None or c[1] == args.omen)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, omen, trans = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAME_POOL)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place, omen, trans, name, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], OMENS[params.omen], TRANSFORMATIONS[params.transformation],
                 params.child_name, params.child_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for p, o, t in asp_valid_combos():
            print(f"  {p:10} {o:8} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
