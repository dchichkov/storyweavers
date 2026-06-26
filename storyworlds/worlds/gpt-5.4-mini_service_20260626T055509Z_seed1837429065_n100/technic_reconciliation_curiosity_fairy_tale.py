#!/usr/bin/env python3
"""
storyworlds/worlds/technic_reconciliation_curiosity_fairy_tale.py
==================================================================

A tiny fairy-tale story world about curiosity, a delicate technic, and
reconciliation.

Seed premise:
- A curious child finds a little technic in a magical place.
- Using it carelessly causes a small mishap.
- A fairy guides a gentle reconciliation.
- The ending proves both the friendship and the technic were restored.

This world is intentionally small and constraint-checked:
- It models a single curious protagonist, a companion, and one fragile technic.
- Curiosity can cause a mishap only when the technic is delicate and in use.
- Reconciliation is possible only when the companion and protagonist both speak
  gently and the technic is repaired with fairy help.

The world is authored for child-facing, fairy-tale style prose and supports the
standard Storyweavers CLI, JSON, QA, trace, and ASP verification modes.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    fragile: bool = False
    repaired: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman", "fairy"}
        male = {"boy", "prince", "king", "father", "man", "wizard"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    magical: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Technic:
    id: str
    label: str
    phrase: str
    use_verb: str
    mishap: str
    repair_method: str
    tags: set[str] = field(default_factory=set)
    delicate: bool = True


@dataclass
class StoryParams:
    place: str
    technic: str
    name: str
    companion: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_events: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace_events.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _entity_mood(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _entity_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_mishap(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["hero"]
    tech = world.facts["technic"]
    if _entity_mood(child, "curiosity") < THRESHOLD:
        return out
    if tech.carried_by != child.id or tech.repaired:
        return out
    sig = ("mishap", tech.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.meters["trouble"] = child.meters.get("trouble", 0.0) + 1
    child.memes["regret"] = child.memes.get("regret", 0.0) + 1
    world.facts["mishap_happened"] = True
    out.append(f"The little technic gave a twinkling sigh, then slipped from {child.id}'s hands.")
    out.append(f"At once, a small mishap followed, and the magic in the room grew quiet.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    child = world.facts["hero"]
    companion = world.facts["companion"]
    fairy = world.facts["fairy"]
    tech = world.facts["technic"]
    if _entity_mood(child, "regret") < THRESHOLD:
        return out
    if _entity_mood(companion, "hurt") < THRESHOLD:
        return out
    if _entity_mood(companion, "forgive") < THRESHOLD:
        return out
    if tech.repaired:
        return out
    sig = ("reconcile", tech.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    tech.repaired = True
    child.memes["peace"] = child.memes.get("peace", 0.0) + 1
    companion.memes["peace"] = companion.memes.get("peace", 0.0) + 1
    fairy.meters["sparkles"] = fairy.meters.get("sparkles", 0.0) + 1
    world.facts["reconciled"] = True
    out.append(f"{fairy.id} touched the broken technic with a silver finger, and it shone whole again.")
    out.append(f"Then {child.id} and {companion.id} smiled at each other, for the sorry words had turned into kindness.")
    return out


CAUSAL_RULES = [_r_mishap, _r_reconcile]


SETTINGS = {
    "moon_garden": Setting(place="the moon garden", magical=True, affords={"inspect", "repair"}),
    "rose_tower": Setting(place="the rose tower", magical=True, affords={"inspect", "repair"}),
    "lantern_hall": Setting(place="the lantern hall", magical=True, affords={"inspect", "repair"}),
}


TECHNICS = {
    "music_box": Technic(
        id="music_box",
        label="music box",
        phrase="a tiny golden music box",
        use_verb="wind up",
        mishap="its song stuttered and stopped",
        repair_method="rewind it with a silver key",
        tags={"music", "golden", "song"},
    ),
    "glass_key": Technic(
        id="glass_key",
        label="glass key",
        phrase="a clear glass key",
        use_verb="turn",
        mishap="it cracked with a tiny chime",
        repair_method="glue it with moonlight",
        tags={"glass", "key", "moon"},
    ),
    "clockwork_seed": Technic(
        id="clockwork_seed",
        label="clockwork seed",
        phrase="a little clockwork seed",
        use_verb="open",
        mishap="its petals fell still",
        repair_method="wind it back with a warm breath",
        tags={"clockwork", "seed", "flower"},
    ),
}

NAMES = ["Mira", "Lina", "Tessa", "Nori", "Elin", "Ivy", "Pippa", "Sera"]
COMPANIONS = ["sister", "brother", "friend", "cousin"]
ROLES = ["curious", "gentle", "brave", "bright"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        for tech in TECHNICS:
            combos.append((place, tech))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: curiosity, a technic, and reconciliation in a fairy tale.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--technic", choices=TECHNICS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--role", choices=ROLES)
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
    if args.place and args.technic:
        if args.place not in SETTINGS or args.technic not in TECHNICS:
            raise StoryError("Unknown place or technic.")
    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.technic is None or c[1] == args.technic)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tech = rng.choice(sorted(combos))
    return StoryParams(
        place=place,
        technic=tech,
        name=args.name or rng.choice(NAMES),
        companion=args.companion or rng.choice(COMPANIONS),
        role=args.role or rng.choice(ROLES),
    )


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    tech_def = TECHNICS[params.technic]

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl",
        traits=[params.role, "curious"],
        memes={"curiosity": 1.0, "hope": 1.0},
    ))
    companion = world.add(Entity(
        id=params.companion,
        kind="character",
        type=params.companion if params.companion in {"sister", "brother"} else "friend",
        traits=["gentle"],
        memes={"hurt": 1.0, "forgive": 1.0},
    ))
    fairy = world.add(Entity(
        id="fairy",
        kind="character",
        type="fairy",
        traits=["wise"],
        memes={"kindness": 1.0},
    ))
    tech = world.add(Entity(
        id=tech_def.id,
        kind="thing",
        type=tech_def.label,
        label=tech_def.label,
        phrase=tech_def.phrase,
        fragile=True,
        carried_by=hero.id,
    ))
    world.facts.update(
        hero=hero,
        companion=companion,
        fairy=fairy,
        technic=tech,
        technic_def=tech_def,
        setting=setting,
    )
    return world


def tell_story(world: World) -> World:
    hero: Entity = world.facts["hero"]
    companion: Entity = world.facts["companion"]
    fairy: Entity = world.facts["fairy"]
    tech: Entity = world.facts["technic"]
    tech_def: Technic = world.facts["technic_def"]

    world.say(
        f"Once upon a time, in {world.setting.place}, there lived a curious little {hero.id}."
    )
    world.say(
        f"{hero.id} loved to look closely at curious things, especially {tech.phrase}."
    )
    world.say(
        f"{companion.id} had warned that the {tech.label} was delicate, but {hero.id} could not help wanting to {tech_def.use_verb} it."
    )
    world.para()
    world.say(
        f"So one bright morning, {hero.id} reached out to inspect the {tech.label}, and the little wonder slipped and went silent."
    )
    world.say(
        f"{tech_def.mishap.capitalize()}, and {companion.id} felt sad that the play had gone wrong."
    )
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"Then the fairy came softly through the air and said, 'A mistake can be mended when hearts are ready.'"
    )
    if world.facts.get("mishap_happened"):
        hero.memes["regret"] = hero.memes.get("regret", 0.0) + 1
    world.say(
        f"{hero.id} said sorry to {companion.id}, and {companion.id} listened."
    )
    world.say(
        f"Together, with {fairy.id}'s help, they chose to {tech_def.repair_method}."
    )
    propagate(world, narrate=True)
    if tech.repaired:
        world.say(
            f"At last, {hero.id} and {companion.id} laughed again as the {tech.label} sang its sweet little song."
        )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    tech_def: Technic = f["technic_def"]
    companion: Entity = f["companion"]
    return [
        f'Write a short fairy tale about a curious child who finds "{tech_def.phrase}" in {world.setting.place}.',
        f"Tell a gentle story where {hero.id} gets too curious about a {tech_def.label}, makes a small mistake, and reconciles with {companion.id}.",
        f'Write a simple story with the word "technic" where a broken thing is repaired after an apology and a kind fairy visit.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    companion: Entity = f["companion"]
    tech: Entity = f["technic"]
    tech_def: Technic = f["technic_def"]
    qa = [
        QAItem(
            question=f"What did {hero.id} find in {world.setting.place}?",
            answer=f"{hero.id} found {tech.phrase} in {world.setting.place}."
        ),
        QAItem(
            question=f"Why did the little mishap happen with the {tech.label}?",
            answer=f"It happened because {hero.id} was very curious and reached for the delicate {tech.label} too eagerly."
        ),
        QAItem(
            question=f"How did {hero.id} and {companion.id} make things right again?",
            answer=f"They said sorry, listened to each other, and let the fairy help repair the {tech.label}."
        ),
    ]
    if f.get("reconciled"):
        qa.append(
            QAItem(
                question=f"What changed after the reconciliation?",
                answer=f"The broken technic was repaired, and {hero.id} and {companion.id} were smiling together at the end."
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "music": [
        QAItem(
            question="What is a music box?",
            answer="A music box is a small box that plays a little tune when you wind it up.",
        )
    ],
    "glass": [
        QAItem(
            question="Why is glass easy to break?",
            answer="Glass can crack or break if it gets bumped or dropped because it is hard but fragile.",
        )
    ],
    "clockwork": [
        QAItem(
            question="What does clockwork mean?",
            answer="Clockwork means something is moved by little turning parts inside, like gears and springs.",
        )
    ],
    "fairy": [
        QAItem(
            question="What is a fairy in a fairy tale?",
            answer="A fairy is a small magical helper who often brings sparkle, kindness, or a bit of magic.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["technic_def"].tags)
    out: list[QAItem] = []
    for tag, items in WORLD_KNOWLEDGE.items():
        if tag in tags or tag == "fairy":
            out.extend(items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.fragile:
            bits.append("fragile=True")
        if e.repaired:
            bits.append("repaired=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
technic(T) :- tech(T).
curious(C) :- has_meme(C, curiosity).
fragile(T) :- tech(T), delicate(T).

mishap(C, T) :- curious(C), carried_by(T, C), fragile(T).
regret(C) :- mishap(C, _).
hurt(X) :- mishap(_, _), companion(X).
reconciled(C, X, T) :- regret(C), hurt(X), forgave(X), fairy(F), repairable(T).

#show valid/2.
valid(P, T) :- place(P), technic(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        lines.append(asp.fact("place", p))
    for tid, t in TECHNICS.items():
        lines.append(asp.fact("tech", tid))
        lines.append(asp.fact("technic", tid))
        lines.append(asp.fact("delicate", tid))
        if t.delicate:
            lines.append(asp.fact("fragile", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParams(place="moon_garden", technic="music_box", name="Mira", companion="sister", role="curious"),
    StoryParams(place="rose_tower", technic="glass_key", name="Lina", companion="friend", role="gentle"),
    StoryParams(place="lantern_hall", technic="clockwork_seed", name="Tessa", companion="brother", role="bright"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell_story(make_world(params))
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, technic) combos:\n")
        for place, tech in combos:
            print(f"  {place:12} {tech}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
            header = f"### {p.name}: {p.technic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
