#!/usr/bin/env python3
"""
storyworlds/worlds/tonsil_smart_dawn_conflict_mystery.py
=========================================================

A standalone story world for a tiny mystery with a dawn setting, a smart helper,
and a clear conflict that turns into a gentle resolution.

Seed tale premise:
---
At dawn, a child wakes with a sore throat and a worried feeling. A smart parent
notices one tonsil looks red. The child insists nothing is wrong, but there is a
small mystery: why does swallowing hurt? Together they look for the clue, find a
tiny popcorn shell from last night, and the child feels better after a warm
drink and a careful check.

The world is intentionally small:
- one child
- one smart helper
- one place
- one mystery clue
- one conflict beat
- one resolution beat

It models physical meters and emotional memes, and the prose is driven by state,
not by a fixed paragraph template.
"""

from __future__ import annotations

import argparse
import copy
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

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


@dataclass
class Setting:
    place: str = "the little kitchen"
    dawn: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    label: str
    phrase: str
    kind: str
    found_in: str
    explains: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Remedy:
    id: str
    label: str
    phrase: str
    effect: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.clue_found: bool = False
        self.mystery_solved: bool = False

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.clue_found = self.clue_found
        clone.mystery_solved = self.mystery_solved
        return clone


def _symptom_rule(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    tonsil = world.entities.get("tonsil")
    if not child or not tonsil:
        return out
    if child.meters.get("sore_throat", 0.0) < THRESHOLD:
        return out
    if tonsil.meters.get("red", 0.0) < THRESHOLD:
        return out
    sig = ("symptom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] = child.memes.get("worry", 0.0) + 1
    out.append("A sore throat and a red tonsil made the mystery feel real.")
    return out


def _clue_rule(world: World) -> list[str]:
    child = world.entities.get("child")
    clue = world.entities.get("clue")
    if not child or not clue:
        return []
    if not world.clue_found:
        return []
    sig = ("clue",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    return [f"The clue was a tiny {clue.label}, just where the smart helper expected it."]


def _resolution_rule(world: World) -> list[str]:
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    remedy = world.entities.get("remedy")
    clue = world.entities.get("clue")
    if not child or not helper or not remedy or not clue:
        return []
    if not world.clue_found:
        return []
    if child.meters.get("relief", 0.0) >= THRESHOLD:
        return []
    sig = ("resolve",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.meters["relief"] = 1.0
    child.memes["worry"] = 0.0
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1
    world.mystery_solved = True
    return [f"{helper.label} gave {child.pronoun('object')} {remedy.phrase}, and the mystery finally made sense."]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_symptom_rule, _clue_rule, _resolution_rule):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "kitchen": Setting(place="the little kitchen", dawn=True, affords={"breakfast_mystery"}),
    "porch": Setting(place="the front porch", dawn=True, affords={"breakfast_mystery"}),
    "hall": Setting(place="the quiet hall", dawn=True, affords={"breakfast_mystery"}),
}

CLUES = {
    "popcorn_shell": Clue(
        id="popcorn_shell",
        label="popcorn shell",
        phrase="a tiny popcorn shell",
        kind="food",
        found_in="the child's shirt collar",
        explains="why the throat felt scratchy",
        tags={"food", "tiny", "dawn"},
    ),
    "crumb": Clue(
        id="crumb",
        label="toast crumb",
        phrase="a dry toast crumb",
        kind="food",
        found_in="the breakfast nook",
        explains="why swallowing felt odd",
        tags={"food", "tiny"},
    ),
    "dust": Clue(
        id="dust",
        label="dust speck",
        phrase="a little dust speck",
        kind="dust",
        found_in="the sunlit shelf",
        explains="why the air felt itchy",
        tags={"tiny"},
    ),
}

REMEDIES = {
    "warm_tea": Remedy(
        id="warm_tea",
        label="warm tea",
        phrase="a mug of warm tea",
        effect="soothe",
        tags={"warm", "gentle"},
    ),
    "honey_water": Remedy(
        id="honey_water",
        label="honey water",
        phrase="a cup of honey water",
        effect="soothe",
        tags={"warm", "gentle"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Nora", "Ivy", "Tia"]
BOY_NAMES = ["Owen", "Ezra", "Theo", "Milo", "Finn"]
HELPER_NAMES = ["Mom", "Dad", "Aunt June", "Grandpa"]

TRAITS = ["smart", "careful", "patient", "quick-thinking", "kind"]


@dataclass
class StoryParams:
    place: str
    clue: str
    remedy: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny dawn mystery with conflict and a smart helper.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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


def reasonableness_gate(params: StoryParams) -> None:
    if params.clue == "dust" and params.remedy == "honey_water":
        return
    if params.clue == "popcorn_shell" and params.remedy not in {"warm_tea", "honey_water"}:
        raise StoryError("The remedy must actually soothe the scratchy throat in this mystery.")
    if params.place not in SETTINGS:
        raise StoryError("That place does not fit the dawn mystery.")
    if params.clue not in CLUES:
        raise StoryError("That clue is not part of this small mystery world.")


def render_story(world: World) -> None:
    child = world.get("child")
    helper = world.get("helper")
    clue = world.get("clue")
    remedy = world.get("remedy")

    world.say(f"At dawn, {child.id} woke in {world.setting.place} with a scratchy throat and a worried feeling.")
    world.say(f"{helper.label} was smart enough to notice that one tonsil looked red.")
    world.para()
    world.say(f"{child.id} did not want to sit still. {child.pronoun().capitalize()} insisted it was nothing, even though swallowing hurt.")
    world.say(f"That made the morning feel tense, because {helper.label} wanted to solve the mystery before breakfast.")

    world.clue_found = True
    world.para()
    world.say(f"After a careful look, {helper.label} found {clue.phrase} {clue.found_in}.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"{helper.label} gave {child.pronoun('object')} {remedy.phrase}, and {child.id} sat by the window while the first light reached the floor.")
    world.say(f"The red tonsil was still there, but the mystery had a clue now, and the worry had gone quiet.")
    propagate(world, narrate=True)

    if world.meters().get("relief", 0.0) < THRESHOLD:
        world.meters()["relief"] = 1.0


def _meters_world(world: World) -> dict:
    return {"relief": world.get("child").meters.get("relief", 0.0)}


def generate_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child_type = params.gender
    child_name = params.name
    helper_label = params.helper
    clue = CLUES[params.clue]
    remedy = REMEDIES[params.remedy]

    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        traits=["little", params.trait, "curious"],
        meters={"sore_throat": 1.0, "relief": 0.0},
        memes={"worry": 1.0, "curiosity": 0.0, "trust": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type="parent",
        label=helper_label,
        traits=["smart", "gentle"],
        meters={},
        memes={"care": 1.0},
    ))
    world.add(Entity(
        id="tonsil",
        kind="body",
        type="body_part",
        label="tonsil",
        phrase="a red tonsil",
        meters={"red": 1.0},
    ))
    world.add(Entity(
        id="clue",
        kind="thing",
        type=clue.kind,
        label=clue.label,
        phrase=clue.phrase,
    ))
    world.add(Entity(
        id="remedy",
        kind="thing",
        type="drink",
        label=remedy.label,
        phrase=remedy.phrase,
    ))
    world.facts = {
        "child": child,
        "helper": helper,
        "clue": clue,
        "remedy": remedy,
        "place": params.place,
        "trait": params.trait,
    }
    render_story(world)
    return world


def story_qa(world: World) -> list[QAItem]:
    child = world.get("child")
    helper = world.get("helper")
    clue = world.get("clue")
    remedy = world.get("remedy")
    return [
        QAItem(
            question=f"Why was {child.id} worried at dawn?",
            answer=f"{child.id} was worried because swallowing hurt, one tonsil looked red, and nobody liked the scratchy feeling."
        ),
        QAItem(
            question=f"What clue did {helper.label} find?",
            answer=f"{helper.label} found {clue.phrase} {clue.found_in}. That clue helped explain the sore throat."
        ),
        QAItem(
            question=f"What did {helper.label} give {child.id}?",
            answer=f"{helper.label} gave {child.id} {remedy.phrase}. That helped the child feel calmer and more comfortable."
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tonsil?",
            answer="A tonsil is a soft part at the back of the throat. Tonsils can get red and sore when a throat feels sick or irritated."
        ),
        QAItem(
            question="What does smart mean?",
            answer="Smart means good at noticing things and solving problems carefully."
        ),
        QAItem(
            question="What is dawn?",
            answer="Dawn is the time early in the morning when the sun first begins to light up the sky."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    helper = f["helper"]
    return [
        f"Write a short mystery story for young children about {child.id} waking at dawn with a sore throat.",
        f"Tell a gentle story where {helper.label} is smart enough to notice a clue and help solve the throat mystery.",
        f"Write a child-friendly dawn mystery that includes a red tonsil, a small clue, and a calm ending.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  clues: found={world.clue_found} solved={world.mystery_solved}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", clue="popcorn_shell", remedy="warm_tea", name="Mina", gender="girl", helper="Mom", trait="smart"),
    StoryParams(place="porch", clue="crumb", remedy="honey_water", name="Owen", gender="boy", helper="Dad", trait="careful"),
    StoryParams(place="hall", clue="dust", remedy="honey_water", name="Nora", gender="girl", helper="Aunt June", trait="patient"),
]


ASP_RULES = r"""
child_worried(C) :- sore_throat(C), red_tonsil(C).
clue_explains(C, K) :- clue(K), found(K), helps(K, C).
solved(C) :- child_worried(C), clue_explains(C, _), remedy_given(C).
#show child_worried/1.
#show clue_explains/2.
#show solved/1.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for name, setting in SETTINGS.items():
        lines.append(asp.fact("setting", name))
        if setting.dawn:
            lines.append(asp.fact("dawn_setting", name))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", name, a))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("found", cid))
        for t in sorted(clue.tags):
            lines.append(asp.fact("tagged", cid, t))
    for rid, remedy in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        for t in sorted(remedy.tags):
            lines.append(asp.fact("remedy_tag", rid, t))
    lines.append(asp.fact("sore_throat", "child"))
    lines.append(asp.fact("red_tonsil", "child"))
    lines.append(asp.fact("remedy_given", "child"))
    lines.append(asp.fact("helps", "popcorn_shell", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show solved/1.\n#show child_worried/1.\n#show clue_explains/2."))
    atoms = set((sym.name, tuple(a.name if a.type == a.type.Function and not a.arguments else a.string if a.type == a.type.String else a.number for a in sym.arguments)) for sym in model)
    ok = True
    if not any(name == "child_worried" for name, _ in atoms):
        ok = False
    if not any(name == "solved" for name, _ in atoms):
        ok = False
    if ok:
        print("OK: ASP twin produces the expected mystery-resolution atoms.")
        return 0
    print("ASP verification failed.")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    clue = args.clue or rng.choice(list(CLUES))
    remedy = args.remedy or rng.choice(list(REMEDIES))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(HELPER_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    params = StoryParams(place=place, clue=clue, remedy=remedy, name=name, gender=gender, helper=helper, trait=trait)
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("#show solved/1.\n#show child_worried/1.\n#show clue_explains/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show solved/1.\n#show child_worried/1.\n#show clue_explains/2."))
        print("ASP atoms:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
