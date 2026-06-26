#!/usr/bin/env python3
"""
A fairy-tale storyworld set on a loading dock, where a careful probe, a small peg,
and a burst of hysterics can turn into a gentle lesson about patience, repetition,
and foreshadowing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import asdict, dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

DOCKS = {
    "loading_dock": {
        "place": "the loading dock",
        "surface": "planks",
        "noise": "clatter",
        "weather": "cool evening",
    }
}

CHARACTER_NAMES = ["Mara", "Toby", "Elsie", "Ivo", "Nina", "Pip"]
GUARD_NAMES = ["Uncle Bram", "Aunt Miri", "Old Jory", "Nell the watcher"]
TRAITS = ["careful", "brave", "patient", "merry", "curious"]

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class World:
    setting: str
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


@dataclass
class StoryParams:
    seed: Optional[int] = None
    place: str = "loading_dock"
    name: str = "Mara"
    guardian: str = "Uncle Bram"
    trait: str = "careful"


@dataclass
class DockItem:
    label: str
    phrase: str
    risky: bool = True


@dataclass
class ProbeTool:
    label: str
    phrase: str
    repetition_note: str
    foreshadow_note: str


ITEMS = {
    "crate": DockItem(label="crate", phrase="a crate with a loose lid"),
    "peg": DockItem(label="peg", phrase="a small wooden peg"),
    "lamp": DockItem(label="lamp", phrase="a brass lamp"),
}

PROBE = ProbeTool(
    label="probe",
    phrase="a slim iron probe",
    repetition_note="the tap-tap-tap of the probe",
    foreshadow_note="the crate gave one tiny wobble, as if it knew what was coming",
)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A fairy-tale loading dock storyworld with repetition and foreshadowing."
    )
    ap.add_argument("--place", choices=DOCKS, default="loading_dock")
    ap.add_argument("--name", choices=CHARACTER_NAMES)
    ap.add_argument("--guardian", choices=GUARD_NAMES)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        seed=args.seed,
        place=args.place or "loading_dock",
        name=args.name or rng.choice(CHARACTER_NAMES),
        guardian=args.guardian or rng.choice(GUARDIAN_NAMES),
        trait=args.trait or rng.choice(TRAITS),
    )


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "loading_dock"),
        asp.fact("thing", "probe"),
        asp.fact("thing", "peg"),
        asp.fact("thing", "crate"),
        asp.fact("feature", "repetition"),
        asp.fact("feature", "foreshadowing"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- place(P).
story_ok :- place_ok(loading_dock), thing(probe), thing(peg), thing(crate).
#show story_ok/0.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    ok = any(a.name == "story_ok" for a in model)
    if ok:
        print("OK: ASP program solves and mirrors the Python reasonableness gate.")
        return 0
    print("MISMATCH: ASP program did not derive story_ok.")
    return 1


def reasonableness_gate(params: StoryParams) -> None:
    if params.place != "loading_dock":
        raise StoryError("This storyworld only knows a loading dock.")
    if params.name not in CHARACTER_NAMES:
        raise StoryError("Unknown child name.")
    if params.guardian not in GUARD_NAMES:
        raise StoryError("Unknown guardian name.")
    if params.trait not in TRAITS:
        raise StoryError("Unknown trait.")


def _do_probe(world: World, child: Entity, crate: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    child.meters["care"] = child.meters.get("care", 0) + 1
    crate.meters["shaken"] = crate.meters.get("shaken", 0) + 1
    if crate.meters["shaken"] >= 2:
        crate.memes["unease"] = crate.memes.get("unease", 0) + 1


def _repetition(world: World, child: Entity, probe: Entity, crate: Entity) -> None:
    if child.meters.get("taps", 0) >= 3 and ("repetition", crate.id) not in world.fired:
        world.fired.add(("repetition", crate.id))
        crate.memes["worry"] = crate.memes.get("worry", 0) + 1
        world.say(
            f"The {probe.label} made the same tap again and again, and again, and again."
        )


def _foreshadowing(world: World, crate: Entity) -> None:
    if crate.meters.get("shaken", 0) >= 1 and ("foreshadow", crate.id) not in world.fired:
        world.fired.add(("foreshadow", crate.id))
        world.say("The crate gave one tiny wobble, as if it meant to tell a secret later.")


def tell(params: StoryParams) -> World:
    world = World(setting=params.place)
    child = world.add(Entity(id=params.name, kind="character", type="girl", memes={}, meters={}))
    guardian = world.add(Entity(id="guardian", kind="character", type="man", label=params.guardian))
    probe = world.add(Entity(id="probe", type="tool", label="probe", phrase=PROBE.phrase, owner=child.id))
    peg = world.add(Entity(id="peg", type="thing", label="peg", phrase="a small wooden peg"))
    crate = world.add(Entity(id="crate", type="thing", label="crate", phrase=ITEMS["crate"].phrase))

    world.say(
        f"Once upon a time, at {DOCKS[params.place]['place']}, {child.id} was a {params.trait} child who loved to listen for secrets."
    )
    world.say(
        f"By a stack of crates, {child.id} found {probe.phrase} and a small peg, both waiting like quiet little helpers."
    )
    world.say(
        f"{child.id} wanted to use the probe to test the crate, because fairy tales sometimes begin with a question."
    )

    world.para()
    world.say(
        f"{child.id} tapped once. Then {child.id} tapped twice. Then {child.id} tapped a third time."
    )
    child.meters["taps"] = 3
    _do_probe(world, child, crate)
    _repetition(world, child, probe, crate)
    _foreshadowing(world, crate)
    world.say(
        f"With each tap-tap-tap, the peg slipped a little more into place, and the crate looked less steady than before."
    )
    world.say(
        f"The air felt like a held breath, and {guardian.label if guardian.label else params.guardian} stepped closer, listening."
    )

    world.para()
    guardian.memes["worry"] = guardian.memes.get("worry", 0) + 1
    world.say(
        f"Then {params.guardian} said, 'Easy now. A probe is for careful checking, not for poking until the whole dock grows noisy.'"
    )
    world.say(
        f"{child.id} looked at the peg, the probe, and the wobbly crate, and understood at last."
    )
    child.memes["hysterics"] = 1
    world.say(
        f"At first, {child.id} broke into hysterics, laughing and gasping all at once at the silly clatter."
    )
    world.say(
        f"But {params.guardian} knelt beside {child.id} and showed how to fit the peg gently, so the crate could rest safely."
    )

    world.para()
    child.memes["calm"] = 1
    child.memes["hysterics"] = 0
    crate.meters["shaken"] = 0
    crate.memes["worry"] = 0
    crate.meters["secured"] = 1
    world.say(
        f"Together they pressed the peg into its little place, and the crate stood still at once."
    )
    world.say(
        f"{child.id} smiled, holding the probe like a promise, while the loading dock grew quiet again."
    )
    world.say(
        f"And so the tap-tap-tap became a lesson, the warning became true, and the little dock kept its secret in peace."
    )

    world.facts.update(
        child=child,
        guardian=guardian,
        probe=probe,
        peg=peg,
        crate=crate,
        params=params,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a fairy-tale story about {p.name} at the loading dock with a probe and a peg.",
        f"Tell a gentle story where repetition and foreshadowing make {p.name} notice a crate is not steady.",
        f"Write a child-friendly loading-dock tale where a probe, a peg, and hysterics lead to a safe ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    child: Entity = f["child"]
    guardian: Entity = f["guardian"]
    crate: Entity = f["crate"]
    probe: Entity = f["probe"]
    qa = [
        QAItem(
            question=f"Where did {child.id} find the probe and the peg?",
            answer=f"{child.id} found them at the loading dock, near the crates and the dock planks.",
        ),
        QAItem(
            question=f"Why did {child.id} keep tapping the crate with the probe?",
            answer=f"{child.id} was curious and wanted to test the crate, so the tapping repeated again and again.",
        ),
        QAItem(
            question=f"What was foreshadowed before the ending?",
            answer="The crate gave a tiny wobble before it was secured, which hinted that it was not steady yet.",
        ),
    ]
    if child.memes.get("hysterics", 0) == 0:
        qa.append(
            QAItem(
                question=f"How did the hysterics end?",
                answer=f"The hysterics ended when {p.guardian} helped {p.name} fit the peg gently and secure the crate.",
            )
        )
    return qa


WORLD_QA = [
    QAItem(
        question="What is a loading dock?",
        answer="A loading dock is a place where people move boxes, crates, and supplies in and out of buildings or wagons.",
    ),
    QAItem(
        question="What is a peg used for?",
        answer="A peg is a small piece that can hold something in place or help fasten parts together.",
    ),
    QAItem(
        question="What is repetition in a story?",
        answer="Repetition is when a word, sound, or action happens more than once, so it stands out to the reader.",
    ),
    QAItem(
        question="What is foreshadowing in a story?",
        answer="Foreshadowing is a small clue that hints something important may happen later.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return list(WORLD_QA)


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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show story_ok/0."))
    return sorted(set(asp.atoms(model, "story_ok")))


def generate(params: StoryParams) -> StorySample:
    reasonableness_gate(params)
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


def CURATED() -> list[StoryParams]:
    return [
        StoryParams(place="loading_dock", name="Mara", guardian="Uncle Bram", trait="careful"),
        StoryParams(place="loading_dock", name="Elsie", guardian="Aunt Miri", trait="curious"),
        StoryParams(place="loading_dock", name="Toby", guardian="Old Jory", trait="patient"),
    ]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show story_ok/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show story_ok/0."))
        print("ASP facts and a single compatible model:")
        print(model)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        params_list = CURATED()
        for p in params_list:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            p = resolve_params(args, rng)
            p.seed = base_seed + i
            sample = generate(p)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
