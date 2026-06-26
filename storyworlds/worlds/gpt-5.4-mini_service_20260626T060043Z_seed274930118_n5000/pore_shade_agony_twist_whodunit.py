#!/usr/bin/env python3
"""
storyworlds/worlds/pore_shade_agony_twist_whodunit.py
=====================================================

A small whodunit storyworld about a careful child-detective, a shady place,
and a twist that turns suspicion into a kinder answer.

The seed image:
---
Pore, a small curious child, notices that the garden shade looks strange.
Someone in the yard seems to be in agony, and there is a mystery to solve.
The clues point one way, then another, until a Twist reveals the truth:
the "culprit" was not a villain at all, but a helper with a painful problem.

World model:
---
* Characters have meters (physical) and memes (emotional).
* Suspicion rises from clues.
* Wrong guesses can deepen the tension.
* A Twist can lower suspicion and relieve agony when the real cause is found.
* The final image must prove what changed in the world.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    shade: str = "shade"


@dataclass
class Clue:
    id: str
    label: str
    detail: str
    suspicion: float = 0.0


@dataclass
class StoryParams:
    place: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    culprit_name: str
    culprit_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


def _add_suspicion(world: World, amount: float, reason: str) -> None:
    world.facts.setdefault("clue_log", []).append(reason)
    world.facts["suspicion"] = float(world.facts.get("suspicion", 0.0)) + amount


def _relieve_agony(world: World, culprit: Entity) -> None:
    culprit.memes["agony"] = 0.0
    culprit.meters["pain"] = 0.0
    world.facts["twist_resolved"] = True


def _set_agony(world: World, culprit: Entity) -> None:
    culprit.memes["agony"] = 2.0
    culprit.meters["pain"] = 2.0


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)

    detective = world.add(Entity(id=params.detective_name, kind="character", type=params.detective_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    culprit = world.add(Entity(id=params.culprit_name, kind="character", type=params.culprit_type))
    shade = world.add(Entity(id="Shade", kind="thing", type="shade", label="shade patch", phrase="a cool patch of shade"))
    pore = world.add(Entity(id="Pore", kind="thing", type="pore", label="pore", phrase="a tiny pore in a leaf"))
    clue_note = world.add(Entity(id="ClueNote", kind="thing", type="note", label="note", phrase="a short note with one bent corner"))

    world.facts.update(
        detective=detective,
        helper=helper,
        culprit=culprit,
        shade=shade,
        pore=pore,
        setting=setting,
    )

    # Act 1: setup.
    detective.memes["curiosity"] = 1.0
    helper.memes["worry"] = 1.0
    culprit.memes["agony"] = 2.0
    culprit.meters["pain"] = 2.0

    world.say(
        f"{detective.id} was a small detective who loved noticing tiny things, even a pore in a leaf."
    )
    world.say(
        f"One afternoon, {detective.id} walked to {setting.place}, where a strange shade rested under the branches."
    )
    world.say(
        f"There, {culprit.id} was in agony and trying hard not to show it."
    )

    world.para()

    # Act 2: clues and suspicion.
    clue_note.meters["torn"] = 1.0
    clue_note.meters["smudged"] = 1.0
    _add_suspicion(world, 1.0, "a torn note near the shade")
    world.say(
        f"{detective.id} found {clue_note.phrase} near the shade, and that made the case feel suspicious."
    )
    world.say(
        f"The note said, 'Meet me under the shade,' but the words were smudged, so nobody could trust them yet."
    )

    # The helper's torn sleeve looks like guilt, but it's only a practical clue.
    helper.meters["sleeve"] = 1.0
    helper.memes["nervous"] = 1.0
    _add_suspicion(world, 0.5, "the helper's torn sleeve")
    world.say(
        f"{helper.id} had a torn sleeve, which looked odd at first and made {detective.id} frown."
    )
    world.say(
        f"{detective.id} looked from the sleeve to the shade and wondered who was hiding a secret."
    )

    world.para()

    # The twist: the helper is not the culprit; the helper is trying to help.
    world.say(
        f"Then came the Twist: {helper.id} was not the sneaky one at all."
    )
    world.say(
        f"{helper.id} had found {culprit.id} hurt by a hidden thorn, and the torn sleeve came from pulling the thorn out."
    )
    world.say(
        f"The bent note was only a warning left to keep others away from the sharp branch under the shade."
    )
    _relieve_agony(world, culprit)

    # Resolution.
    detective.memes["joy"] = 1.0
    detective.memes["relief"] = 1.0
    helper.memes["relief"] = 1.0
    world.facts["suspicion"] = max(0.0, float(world.facts.get("suspicion", 0.0)) - 1.5)

    world.say(
        f"{detective.id} nodded at last and thanked {helper.id} for the rescue."
    )
    world.say(
        f"With the thorn gone, {culprit.id}'s agony faded, the shade felt calm, and the little pore in the leaf looked ordinary again."
    )
    world.say(
        f"The mystery ended not with a villain, but with kindness under the shade."
    )

    return world


SETTING_REGISTRY = {
    "garden": Setting(place="the garden", indoor=False, shade="tree shade"),
    "yard": Setting(place="the yard", indoor=False, shade="porch shade"),
    "greenhouse": Setting(place="the greenhouse", indoor=True, shade="glass shade"),
}

DETECTIVES = [
    ("Pore", "boy"),
    ("Mira", "girl"),
    ("Noah", "boy"),
    ("Nina", "girl"),
]

HELPERS = [
    ("Ivy", "girl"),
    ("Ben", "boy"),
    ("Lena", "girl"),
    ("Tom", "boy"),
]

CULPRITS = [
    ("Milo", "boy"),
    ("Ruby", "girl"),
    ("Otis", "boy"),
    ("Dina", "girl"),
]


@dataclass
class StoryConfig:
    setting: str
    detective_name: str
    detective_type: str
    helper_name: str
    helper_type: str
    culprit_name: str
    culprit_type: str
    seed: Optional[int] = None


ASP_RULES = r"""
% A story is coherent if a detective exists, a helper exists, and the culprit
% begins in agony. The twist resolves the agony.
detective_ok :- detective(_,_).
helper_ok :- helper(_,_).
culprit_in_agony :- agony(culprit).

coherent_story :- detective_ok, helper_ok, culprit_in_agony.
twist_resolves :- twist, coherent_story.

#show coherent_story/0.
#show twist_resolves/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTING_REGISTRY:
        lines.append(asp.fact("setting", sid))
    for name, typ in DETECTIVES:
        lines.append(asp.fact("detective", name, typ))
    for name, typ in HELPERS:
        lines.append(asp.fact("helper", name, typ))
    for name, typ in CULPRITS:
        lines.append(asp.fact("culprit", name, typ))
    lines.append(asp.fact("agony", "culprit"))
    lines.append(asp.fact("twist"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    program = asp_program("#show coherent_story/0. #show twist_resolves/0.")
    model = asp.one_model(program)
    atoms = {(sym.name, len(sym.arguments)) for sym in model}
    needed = {("coherent_story", 0), ("twist_resolves", 0)}
    if needed.issubset(atoms):
        print("OK: ASP gate accepts the seeded whodunit structure.")
        return 0
    print("MISMATCH: ASP gate did not derive the expected story shape.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A child-friendly whodunit storyworld with a twist."
    )
    ap.add_argument("--place", choices=SETTING_REGISTRY)
    ap.add_argument("--detective-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--culprit-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryConfig:
    setting = args.place or rng.choice(list(SETTING_REGISTRY))
    dname, dtype = rng.choice(DETECTIVES)
    hname, htype = rng.choice(HELPERS)
    cname, ctype = rng.choice(CULPRITS)

    if args.detective_name:
        dname = args.detective_name
    if args.helper_name:
        hname = args.helper_name
    if args.culprit_name:
        cname = args.culprit_name

    if dname == hname or dname == cname or hname == cname:
        raise StoryError("Choose different names for the detective, helper, and culprit.")

    return StoryConfig(
        setting=setting,
        detective_name=dname,
        detective_type=dtype,
        helper_name=hname,
        helper_type=htype,
        culprit_name=cname,
        culprit_type=ctype,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    culprit = f["culprit"]
    setting = f["setting"]
    return [
        f'Write a short whodunit for a child where {detective.id} notices a pore and a strange shade at {setting.place}.',
        f"Tell a mystery where {detective.id} thinks {helper.id} might be guilty, but a twist proves the truth.",
        f"Create a gentle detective story in which someone in agony is helped under the shade, and the clue turns out to be kinder than it first seemed.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = f["detective"]
    helper = f["helper"]
    culprit = f["culprit"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who solved the mystery at {setting.place}?",
            answer=f"{detective.id} solved it by noticing the clues and asking careful questions.",
        ),
        QAItem(
            question=f"Why did {helper.id} seem suspicious at first?",
            answer=f"{helper.id} had a torn sleeve, which looked suspicious before the Twist explained it.",
        ),
        QAItem(
            question=f"What was wrong with {culprit.id} before the truth came out?",
            answer=f"{culprit.id} was in agony because a hidden thorn was hurting them.",
        ),
        QAItem(
            question="What was the Twist?",
            answer=f"The Twist was that {helper.id} was helping {culprit.id}, not causing trouble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pore?",
            answer="A pore is a tiny opening in a skin, leaf, or other surface.",
        ),
        QAItem(
            question="What is shade?",
            answer="Shade is a cooler, darker place made when something blocks the sun.",
        ),
        QAItem(
            question="What is agony?",
            answer="Agony is very strong pain or suffering.",
        ),
        QAItem(
            question="What does a twist do in a mystery story?",
            answer="A twist changes what the reader thought was true and reveals a new, surprising answer.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  facts={world.facts}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING_REGISTRY[params.setting], params)
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


def _asp_mode() -> None:
    import asp

    program = asp_program("#show coherent_story/0. #show twist_resolves/0.")
    model = asp.one_model(program)
    print("ASP facts and rules accepted.")
    print(f"Derived atoms: {', '.join(str(a) for a in model)}")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show coherent_story/0. #show twist_resolves/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        _asp_mode()
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryConfig("garden", "Pore", "boy", "Ivy", "girl", "Milo", "boy"),
            StoryConfig("yard", "Mira", "girl", "Ben", "boy", "Ruby", "girl"),
            StoryConfig("greenhouse", "Noah", "boy", "Lena", "girl", "Otis", "boy"),
        ]
        samples = [generate(StoryParams(**c.__dict__)) for c in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            seed = base_seed + i
            try:
                cfg = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            cfg.seed = seed
            sample = generate(StoryParams(**cfg.__dict__))
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
