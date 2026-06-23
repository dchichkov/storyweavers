#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T035719Z_seed829048975_n10/ass_sorry_cautionary_kindness_whodunit.py
===============================================================================================================

A compact storyworld built from a tiny whodunit premise with cautionary kindness:
a child notices a missing thing, points a gentle suspicion at an ass (a donkey),
then learns to look for clues before blaming anyone. The ending turns on an
apology, a helpful act, and the real culprit being revealed.

The script is standalone, stdlib-only, and follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven story rendering
- three QA sets derived from simulated state
- a Python reasonableness gate plus inline ASP twin
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional

HERE = Path(__file__).resolve()
for parent in (HERE.parent, *HERE.parents):
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    attrs: dict[str, Any] = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "aunt"}
        male = {"boy", "father", "dad", "man", "brother", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def ref(self) -> str:
        return self.phrase or self.label or self.id

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Place:
    id: str
    label: str
    clue_kind: str
    hiding_spot: str
    supports: set[str] = field(default_factory=set)


@dataclass
class MissingThing:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Suspect:
    id: str
    label: str
    phrase: str
    sound: str
    kind: str


@dataclass
class StoryParams:
    place: str
    missing: str
    suspect: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple[str, ...]] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, Any] = {}

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

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = {k: _clone_entity(v) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _clone_entity(ent: Entity) -> Entity:
    return Entity(
        id=ent.id,
        kind=ent.kind,
        type=ent.type,
        label=ent.label,
        phrase=ent.phrase,
        traits=list(ent.traits),
        role=ent.role,
        owner=ent.owner,
        caretaker=ent.caretaker,
        plural=ent.plural,
        tags=set(ent.tags),
        attrs=dict(ent.attrs),
        meters=defaultdict(float, dict(ent.meters)),
        memes=defaultdict(float, dict(ent.memes)),
    )


def _rule_curiosity(world: World) -> list[str]:
    child = world.get("child")
    if child.memes["curiosity"] < THRESHOLD:
        return []
    sig = ("curious",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["suspicion"] += 1
    return []


def _rule_kindness(world: World) -> list[str]:
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["apology"] < THRESHOLD or helper.memes["kindness"] < THRESHOLD:
        return []
    sig = ("kindness",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["peace"] += 1
    helper.memes["warmth"] += 1
    return []


def propagate(world: World) -> None:
    _rule_curiosity(world)
    _rule_kindness(world)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for missing_id in MISSING_THINGS:
            for suspect_id in SUSPECTS:
                if place_id == "stable" and suspect_id != "ass":
                    continue
                combos.append((place_id, missing_id, suspect_id))
    return combos


def explain_rejection(place: str, missing: str, suspect: str) -> str:
    if place == "stable" and suspect != "ass":
        return "(No story: this stable story only works when the ass/donkey is the suspicious-looking animal in the yard.)"
    if missing == "bell" and suspect == "cat":
        return "(No story: the cat would be too obviously quick for this whodunit; choose a more surprising clue trail.)"
    return "(No story: the combination is not reasonable for this tiny whodunit.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = f["child"]
    missing: MissingThing = f["missing_cfg"]
    suspect: Suspect = f["suspect_cfg"]
    place: Place = f["place_cfg"]
    return [
        f'Write a gentle whodunit for a small child where {child.id} notices that {missing.phrase} is gone at {place.label}, and thinks the ass may know something.',
        f"Tell a cautionary kindness mystery where {child.id} says sorry before blaming {suspect.label}, then follows clues to the real answer.",
        f'Write a short story that uses the words "ass" and "sorry" and ends with a helpful apology, a clue, and the missing {missing.label} found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper_ent"]
    missing: MissingThing = f["missing_cfg"]
    suspect: Suspect = f["suspect_cfg"]
    place: Place = f["place_cfg"]
    answer1 = (
        f"It is about {child.id}, who found that {missing.phrase} was missing at {place.label}. "
        f"The mystery starts because {child.id} notices clues instead of the thing itself."
    )
    answer2 = (
        f"{child.id} first thought {suspect.label} might be involved, but {child.id} remembered to be careful. "
        f"That caution kept the story kind, because the real answer came from looking for clues."
    )
    answer3 = (
        f"At the end, {child.id} said sorry to {suspect.label} and thanked {helper.id} for helping. "
        f"The missing {missing.label} was found in {place.hiding_spot}, so nobody stayed blamed unfairly."
    )
    return [
        QAItem(
            question=f"Who is the whodunit about when something goes missing at {place.label}?",
            answer=answer1,
        ),
        QAItem(
            question=f"Why did {child.id} not keep blaming {suspect.label}?",
            answer=answer2,
        ),
        QAItem(
            question=f"How did the story end for {child.id}, {suspect.label}, and the missing {missing.label}?",
            answer=answer3,
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    suspect: Suspect = f["suspect_cfg"]
    missing: MissingThing = f["missing_cfg"]
    place: Place = f["place_cfg"]
    out = [
        QAItem(
            question="What is an ass?",
            answer="An ass is another word for a donkey. It is a sturdy farm animal with long ears and a patient way of standing still.",
        ),
        QAItem(
            question="Why is it good to say sorry in a mystery?",
            answer="Saying sorry helps when someone was blamed too quickly. It can open the way for kindness, which makes it easier to keep looking for the truth.",
        ),
        QAItem(
            question=f"What kind of place is {place.label} in this story?",
            answer=f"{place.label.capitalize()} is a small place where clues can hide in {place.hiding_spot}. It gives the mystery a clear corner to search.",
        ),
        QAItem(
            question=f"What does {missing.label} stand for in this story?",
            answer=f"{missing.label.capitalize()} is the thing that goes missing and starts the whodunit. The missing item gives the child a reason to look carefully.",
        ),
        QAItem(
            question=f"What does {suspect.label} sound like in the story?",
            answer=f"{suspect.label.capitalize()} makes a calm sound in this story: {suspect.sound}. That sound helps the child notice the suspect without making the story mean.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def tell(place: Place, missing: MissingThing, suspect: Suspect, name: str, gender: str, helper: str) -> World:
    world = World(place)
    child = world.add(Entity(id="child", kind="character", type=gender, label=name))
    helper_ent = world.add(Entity(id="helper", kind="character", type="girl" if helper == "mother" else "boy", label=helper))
    missing_ent = world.add(Entity(id="missing", type="thing", label=missing.label, phrase=missing.phrase))
    suspect_ent = world.add(Entity(id="suspect", type="animal", label=suspect.label, phrase=suspect.phrase))
    clue = world.add(Entity(id="clue", type="thing", label="clue", phrase="a muddy clue"))

    child.memes["curiosity"] += 1
    child.memes["worry"] += 1
    helper_ent.memes["kindness"] += 1

    world.facts.update(
        child=child,
        helper_ent=helper_ent,
        missing_cfg=missing,
        suspect_cfg=suspect,
        place_cfg=place,
        missing_ent=missing_ent,
        suspect_ent=suspect_ent,
        clue_ent=clue,
    )

    world.say(f"At {place.label}, {child.id} noticed that {missing.phrase} was gone.")
    world.say(f'\"Hmm,\" {child.id} said. \"I hope the ass did not take it.\"')

    world.para()
    child.memes["suspicion"] += 1
    world.say(f"{helper_ent.id} touched {child.id}'s shoulder and said, \"Let's be careful before we blame anyone.\"")
    world.say(f"{child.id} looked again and saw a muddy clue near {place.hiding_spot}.")

    world.para()
    world.say(f"{child.id} followed the clue to {place.hiding_spot}.")
    world.say(f"There, {missing.phrase} waited beside {suspect.sound} coming from the ass's stall.")
    world.say(f"{child.id} felt the truth click into place.")

    world.para()
    child.memes["apology"] += 1
    world.say(f"{child.id} turned to the ass and said, \"Sorry I blamed you too fast.\"")
    world.say(f"The ass just stood calmly while {helper_ent.id} smiled at the kind apology.")
    world.say(f"Then {child.id} carried {missing.phrase} home, and the mystery ended with everyone feeling better.")
    propagate(world)
    return world


PLACES = {
    "stable": Place(id="stable", label="the stable", clue_kind="mud", hiding_spot="a hay basket", supports={"ass", "mud"}),
    "garden": Place(id="garden", label="the garden", clue_kind="soil", hiding_spot="a tool box", supports={"spade", "soil"}),
    "kitchen": Place(id="kitchen", label="the kitchen", clue_kind="crumbs", hiding_spot="the bread box", supports={"crumbs", "cat"}),
}

MISSING_THINGS = {
    "bell": MissingThing(id="bell", label="bell", phrase="the little brass bell", tags={"metal"}),
    "ribbon": MissingThing(id="ribbon", label="ribbon", phrase="the bright ribbon", tags={"cloth"}),
    "key": MissingThing(id="key", label="key", phrase="the tiny key", tags={"metal"}),
}

SUSPECTS = {
    "ass": Suspect(id="ass", label="the ass", phrase="the patient ass", sound="hee-haw", kind="animal"),
    "cat": Suspect(id="cat", label="the cat", phrase="the sleepy cat", sound="mrrp", kind="animal"),
    "cook": Suspect(id="cook", label="the cook", phrase="the busy cook", sound="hmm-hmm", kind="person"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Leo", "Theo", "Sam", "Max"]
HELPERS = ["mother", "father", "aunt", "uncle"]


def valid_story_keys() -> list[tuple[str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small cautionary kindness whodunit storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--missing", choices=MISSING_THINGS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("-n", "--n", type=int, default=1)
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
              and (args.missing is None or c[1] == args.missing)
              and (args.suspect is None or c[2] == args.suspect)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, missing, suspect = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(place=place, missing=missing, suspect=suspect, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    for key, table in (("place", PLACES), ("missing", MISSING_THINGS), ("suspect", SUSPECTS)):
        if getattr(params, key) not in table:
            raise StoryError(f"Invalid {key}: {getattr(params, key)}")
    world = tell(PLACES[params.place], MISSING_THINGS[params.missing], SUSPECTS[params.suspect], params.name, params.gender, params.helper)
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


ASP_RULES = r"""
valid(P, M, S) :- place(P), missing(M), suspect(S), place_supports(P, S).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for s in sorted(p.supports):
            lines.append(asp.fact("place_supports", pid, s))
    for mid in MISSING_THINGS:
        lines.append(asp.fact("missing", mid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0 if py == cl else 1
    if rc == 0:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        print("Mismatch between ASP and Python combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"Smoke test failed: {exc}")
        return 1
    return rc


CURATED = [
    StoryParams(place="stable", missing="bell", suspect="ass", name="Mia", gender="girl", helper="mother"),
    StoryParams(place="garden", missing="ribbon", suspect="cat", name="Ben", gender="boy", helper="father"),
    StoryParams(place="kitchen", missing="key", suspect="cook", name="Lily", gender="girl", helper="aunt"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combos")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
