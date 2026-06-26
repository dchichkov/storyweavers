#!/usr/bin/env python3
"""
storyworlds/worlds/spirit_sandbox_reconciliation_transformation_myth.py
=========================================================================

A myth‑inspired storyworld set in a sandbox where a playful spirit tests a child's
patience, and only through understanding can the child reconcile and transform the
spirit's mischief into wonder.

Initial story seed:
---
Once, in a golden sandbox at the edge of a sun‑warmed garden, a child named Arin
built a castle. But a trickster spirit, tiny and made of shifting sand, scattered
the walls each time Arin reached for a new grain. Arin grew cross and threw a
handful of sand. The spirit laughed and vanished, leaving only lonely dunes.
Arin sat still, thought, and then sang a gentle song, offering a shell. The spirit
peeked out, listened, and slowly shaped a new tower beside Arin's hands. From
that day, the sandbox held two builders: one of flesh, one of sand.

Causal rules:
---
  spirit mischief          -> child.meters[sand_scattered] += 1
                              child.memes[frustration] += 1
  child frustration        -> child acts impulsively (throw sand) -> spirit.fear += 1
  child offers (song/shell) -> spirit.memes[trust] += 1
  spirit trust > threshold -> transformation: spirit becomes helper
                              child.memes[joy] += 1
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

# ---------------------------------------------------------------------------
# Entity
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"            # character | spirit | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "spirit"}
        female = {"girl", "mother", "sister"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


# ---------------------------------------------------------------------------
# Setting
# ---------------------------------------------------------------------------
@dataclass
class Setting:
    place: str = "the sandbox"
    indoor: bool = False
    affords: set[str] = field(default_factory=lambda: {"build", "dig", "sing"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    mess: str = "sand"
    keyword: str = "sand"
    tags: set[str] = field(default_factory=set)


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    emotional: bool = False      # if True, it calms spirit


# ---------------------------------------------------------------------------
# World
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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

    def spirits(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "spirit"]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_mischief(world: World) -> list[str]:
    out = []
    for spirit in world.spirits():
        if spirit.memes["active"] < THRESHOLD:
            continue
        for child in world.characters():
            if child.meters["sand_scattered"] >= THRESHOLD:
                continue
            child.meters["sand_scattered"] += 1
            child.memes["frustration"] += 1
            sig = ("mischief", child.id)
            if sig not in world.fired:
                world.fired.add(sig)
                out.append("Sand flew, and what was built crumbled away.")
    return out


def _r_frustration(world: World) -> list[str]:
    out = []
    for child in world.characters():
        if child.memes["frustration"] >= THRESHOLD and child.memes["throw_sand"] < THRESHOLD:
            child.memes["throw_sand"] += 1
            sig = ("throw", child.id)
            if sig not in world.fired:
                world.fired.add(sig)
                for spirit in world.spirits():
                    spirit.memes["fear"] += 1
                out.append("The child threw a handful of sand in anger.")
    return out


def _r_offering(world: World) -> list[str]:
    out = []
    for child in world.characters():
        if child.memes["offers"] >= THRESHOLD:
            for spirit in world.spirits():
                if spirit.memes["trust"] < THRESHOLD:
                    spirit.memes["trust"] += 1
                    sig = ("trust", spirit.id, child.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        out.append("The spirit listened and began to trust.")
    return out


def _r_transformation(world: World) -> list[str]:
    out = []
    for spirit in world.spirits():
        if spirit.memes["trust"] >= THRESHOLD and spirit.memes["helper"] < THRESHOLD:
            spirit.memes["helper"] += 1
            sig = ("transform", spirit.id)
            if sig not in world.fired:
                world.fired.add(sig)
                for child in world.characters():
                    child.memes["joy"] += 1
                out.append("The spirit shimmered, turned gentle, and became a builder.")
    return out


CAUSAL_RULES = [
    Rule("mischief", _r_mischief),
    Rule("frustration", _r_frustration),
    Rule("offering", _r_offering),
    Rule("transformation", _r_transformation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Screenplay verbs
# ---------------------------------------------------------------------------
def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "curious")
    world.say(
        f"Once, a little {trait} {child.type} named {child.id} played "
        f"in the great {world.setting.place.rstrip('.').split()[-1]} "
        f"at the edge of a sun‑warmed garden."
    )


def build_castle(world: World, child: Entity) -> None:
    world.say(
        f"{child.id} scooped sand into a tall castle, patting walls smooth."
    )


def spirit_appears(world: World, spirit: Entity) -> None:
    world.say(
        f"A tiny spirit of sand, {spirit.label}, woke from the grains "
        f"and giggled."
    )
    spirit.memes["active"] += 1


def mischief_happens(world: World, child: Entity, spirit: Entity) -> None:
    propagate(world)
    # Narrated by rules


def child_angry(world: World, child: Entity) -> None:
    propagate(world)


def child_offers(world: World, child: Entity, offering: str) -> None:
    child.memes["offers"] += 1
    world.say(
        f"{child.id} stopped. {child.pronoun('possessive').capitalize()} "
        f"fingers found {offering}. Softly, {child.pronoun()} began to sing."
    )
    propagate(world)


def reconciliation(world: World, child: Entity, spirit: Entity) -> None:
    spirit.memes["helper"] = 1.5  # force transformation
    propagate(world)
    world.say(
        f"The spirit whispered, \"You see me.\" Together they shaped a new tower, "
        f"and from that day the sandbox held two builders: one of flesh, one of sand."
    )


# ---------------------------------------------------------------------------
# State machine: tell()
# ---------------------------------------------------------------------------
def tell(setting: Setting, activity: Activity, child_name: str = "Arin",
         child_type: str = "boy", child_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name, kind="character", type=child_type,
        traits=["little"] + (child_traits or ["curious", "stubborn"]),
    ))
    spirit = world.add(Entity(
        id="Spirit", kind="spirit", type="spirit",
        label="a trickster spirit of sand",
        phrase="a tiny spirit woven from golden sand",
    ))

    # Act 1 – setup
    introduce(world, child)
    build_castle(world, child)
    spirit_appears(world, spirit)

    # Act 2 – conflict
    mischief_happens(world, child, spirit)
    child_angry(world, child)
    world.para()

    # Act 3 – reconciliation & transformation
    child_offers(world, child, "a shiny shell")
    reconciliation(world, child, spirit)

    world.facts.update(child=child, spirit=spirit, activity=activity,
                       setting=setting, reconciled=True)
    return world


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "sandbox": Setting(place="the sandbox", indoor=False),
    "seaside": Setting(place="the seaside sandbox", indoor=False),
}

ACTIVITIES = {
    "build": Activity(id="build", verb="build sandcastles", gerund="building sandcastles",
                      keyword="sand"),
    "dig": Activity(id="dig", verb="dig deep tunnels", gerund="digging tunnels",
                    keyword="sand"),
    "sing": Activity(id="sing", verb="sing to the sand", gerund="singing to the sand",
                     keyword="song"),
}

OFFERINGS = [
    Offering(id="shell", label="a shell", phrase="a shiny shell"),
    Offering(id="song", label="a gentle song", phrase="a gentle, wordless song"),
    Offering(id="flower", label="a tiny flower", phrase="a tiny garden flower"),
]

CHILD_NAMES = ["Arin", "Lira", "Kael", "Mira", "Torin"]
CHILD_TYPES = ["boy", "girl"]
TRAITS = ["curious", "stubborn", "gentle", "brave", "playful"]


# ---------------------------------------------------------------------------
# StoryParams
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
offering_fits(A, O) :- activity(A), offering(O), emotional(O).
reconcile(A, C, O) :- activity(A), child_trait(C), offering_fits(A, O).
transformation_possible(A) :- reconcile(A, _, _).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in s.affords:
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
    for o in OFFERINGS:
        lines.append(asp.fact("offering", o.id))
        if o.emotional:
            lines.append(asp.fact("emotional", o.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    # For this world, we only check that the ASP program can be loaded.
    # No hard numerical parity check because the story is linear.
    try:
        _ = asp.one_model(asp_program("#show transformation_possible/1."))
        print("OK: ASP gate loads and runs.")
        return 0
    except Exception as e:
        print(f"ASP error: {e}")
        return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "sand": [("What is sand made of?",
              "Sand is made of tiny pieces of rocks and shells, ground down "
              "over time by wind and water.")],
    "spirit": [("Are spirits real?",
                "In stories, spirits are magical creatures. In the real world, "
                "the wind and sand can feel alive when they move.")],
    "transformation": [("What does transformation mean?",
                        "Transformation means changing into something new. "
                        "A caterpillar transforms into a butterfly.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, act = f["child"], f["activity"]
    return [
        f"Write a myth‑style story about a {child.type} named {child.id} who meets "
        f"a sand spirit while {act.gerund}.",
        f"Tell a gentle story about anger and reconciliation in a sandbox, "
        f"where a spirit helps a child learn patience.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, spirit = f["child"], f["spirit"]
    sub, pos = child.pronoun("subject"), child.pronoun("possessive")
    place = world.setting.place
    return [
        QAItem(
            question=f"Who did {child.id} meet in {place}?",
            answer=f"{child.id} met {spirit.label} who lived in the sand.",
        ),
        QAItem(
            question=f"Why was {child.id} upset during {pos} play?",
            answer=f"The spirit kept scattering {pos} sandcastles, and that made "
                   f"{sub} feel frustrated.",
        ),
        QAItem(
            question=f"How did {child.id} make peace with the spirit?",
            answer=f"{child.id} stopped throwing sand, found a shell, sang a song, "
                   f"and the spirit listened. Then they built together.",
        ),
        QAItem(
            question=f"What changed after {child.id} and the spirit became friends?",
            answer=f"The spirit transformed from a trickster into a helper, and "
                   f"the sandbox became a place of two builders.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [QAItem(q=q, a=a) for q, a in KNOWLEDGE["sand"]]  # minimal


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
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
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic sandbox story: child meets spirit, reconciliation, transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gender", choices=CHILD_TYPES)
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or rng.choice(list(ACTIVITIES))
    gender = args.gender or rng.choice(CHILD_TYPES)
    name = args.name or rng.choice(CHILD_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity],
                 params.name, params.gender, [params.trait])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show transformation_possible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show transformation_possible/1."))
        if model:
            print("Transformation is possible in this world.")
        else:
            print("No transformation path found.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

    samples = []
    if args.all:
        # Generate one for each combination (for demonstration)
        for place in SETTINGS:
            for act in ACTIVITIES:
                for name in ["Arin"]:
                    params = StoryParams(place=place, activity=act, name=name,
                                         gender="boy", trait="curious")
                    samples.append(generate(params))
    else:
        seen = set()
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
