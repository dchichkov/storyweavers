#!/usr/bin/env python3
"""
Standalone storyworld: Elude Quest Transformation Reconciliation Rhyming Story.

A tiny classical simulation in a rhyming tale style:
- a small hero goes on a quest
- the hero transforms through the journey
- conflict is resolved with reconciliation
- the central action includes eluding a pursuer

The world is intentionally narrow so the prose, state changes, and Q&A all stay
grounded in the same simulated facts.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"distance": 0.0, "travel": 0.0}
        if not self.memes:
            self.memes = {"hope": 0.0, "fear": 0.0, "joy": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mouse", "fox", "rabbit", "bird"}
        male = {"boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    id: str
    label: str
    rhyme: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    verb: str
    reward: str
    risk: str
    rhyme_word: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Transformation:
    id: str
    from_state: str
    to_state: str
    cue: str
    rhyme_word: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Reconciliation:
    id: str
    offer: str
    response: str
    closing: str
    rhyme_word: str
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace_lines: list[str] = []

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
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    pursuer: str
    quest: str
    transformation: str
    reconciliation: str
    seed: Optional[int] = None


PLACES = {
    "moonlane": Place(id="moonlane", label="Moon Lane", rhyme="glow lane", affords={"quest", "elude"}),
    "brook": Place(id="brook", label="Bluebrook", rhyme="crook brook", affords={"quest", "elude"}),
    "meadow": Place(id="meadow", label="Green Meadow", rhyme="gleam meadow", affords={"quest", "elude"}),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        goal="find the lost lantern",
        verb="seek the lost lantern",
        reward="the road would shine",
        risk="the dark would bite",
        rhyme_word="gleam",
        tags={"light", "search"},
    ),
    "key": Quest(
        id="key",
        goal="bring back the silver key",
        verb="fetch the silver key",
        reward="the gate would swing",
        risk="the gate would stay shut",
        rhyme_word="key",
        tags={"search", "door"},
    ),
    "seed": Quest(
        id="seed",
        goal="carry the golden seed",
        verb="carry the golden seed",
        reward="the garden would sing",
        risk="the seed might slip away",
        rhyme_word="sprout",
        tags={"garden", "care"},
    ),
}

TRANSFORMATIONS = {
    "brave": Transformation(
        id="brave",
        from_state="small and shy",
        to_state="brave and steady",
        cue="a warm little tune",
        rhyme_word="light",
        meters={"courage": 1.0},
        memes={"hope": 1.0, "fear": -1.0},
    ),
    "swift": Transformation(
        id="swift",
        from_state="slow and stuck",
        to_state="swift as a breeze",
        cue="the path began to sing",
        rhyme_word="flight",
        meters={"speed": 1.0},
        memes={"hope": 1.0},
    ),
    "kind": Transformation(
        id="kind",
        from_state="cross and tense",
        to_state="kind and calm",
        cue="a softer word from the heart",
        rhyme_word="glow",
        meters={"softness": 1.0},
        memes={"joy": 1.0, "conflict": -1.0},
    ),
}

RECONCILIATIONS = {
    "song": Reconciliation(
        id="song",
        offer="hum a shared song",
        response="the other side would soften",
        closing="they walked on together, side by side",
        rhyme_word="tune",
        meters={"distance": -1.0},
        memes={"joy": 1.0, "conflict": -1.0},
    ),
    "share": Reconciliation(
        id="share",
        offer="share the prize",
        response="the worry would melt away",
        closing="they laughed, and the road felt wide",
        rhyme_word="glow",
        meters={"distance": -1.0},
        memes={"joy": 1.0, "conflict": -1.0},
    ),
    "guide": Reconciliation(
        id="guide",
        offer="guide the pursuer home",
        response="the chase would end in peace",
        closing="their feet found a friendly stride",
        rhyme_word="hive",
        meters={"distance": -1.0},
        memes={"joy": 1.0, "conflict": -1.0},
    ),
}

HERO_NAMES = ["Mina", "Luna", "Pip", "Nori", "Tavi", "Iris"]
PURSUER_NAMES = ["Moss", "Rowan", "Kit", "Wren", "Sage", "Toby"]
HERO_TYPES = ["girl", "mouse", "rabbit", "bird", "boy"]


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def valid_combo(place: str, quest: str, trans: str, rec: str) -> bool:
    return place in PLACES and quest in QUESTS and trans in TRANSFORMATIONS and rec in RECONCILIATIONS


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    quest = args.quest or rng.choice(list(QUESTS))
    transformation = args.transformation or rng.choice(list(TRANSFORMATIONS))
    reconciliation = args.reconciliation or rng.choice(list(RECONCILIATIONS))
    if not valid_combo(place, quest, transformation, reconciliation):
        raise StoryError("Invalid story options.")
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    hero = args.hero or rng.choice(HERO_NAMES)
    pursuer = args.pursuer or rng.choice(PURSUER_NAMES)
    return StoryParams(
        place=place,
        hero=hero,
        hero_type=hero_type,
        pursuer=pursuer,
        quest=quest,
        transformation=transformation,
        reconciliation=reconciliation,
    )


def _state_change(entity: Entity, meters: dict[str, float] | None = None, memes: dict[str, float] | None = None) -> None:
    if meters:
        for k, v in meters.items():
            entity.meters[k] = entity.meters.get(k, 0.0) + v
    if memes:
        for k, v in memes.items():
            entity.memes[k] = entity.memes.get(k, 0.0) + v


def tell(world: World, params: StoryParams) -> World:
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    pursuer = world.add(Entity(id=params.pursuer, kind="character", type="fox" if params.pursuer not in {"Moss", "Wren"} else "rabbit"))
    quest = QUESTS[params.quest]
    trans = TRANSFORMATIONS[params.transformation]
    rec = RECONCILIATIONS[params.reconciliation]

    hero.memes["hope"] += 1.0
    hero.memes["fear"] += 1.0

    world.say(
        f"On {world.place.label}, where the night wind blew bright and free, "
        f"{hero.id} set out softly, as small as small could be."
    )
    world.say(
        f"{hero.id} would {quest.verb}, for {quest.reward}, and save the day with glee."
    )

    world.para()
    world.say(
        f"But {pursuer.id} came near with a watchful eye, and called, "
        f"\"Come back, come back!\" in a voice so sly."
    )
    world.say(
        f"So {hero.id} chose to elude the trail, by slipping through reeds and under a rail."
    )
    hero.meters["distance"] += 1.0
    hero.memes["fear"] += 1.0
    pursuer.memes["conflict"] += 1.0
    world.facts["eluded"] = True

    world.para()
    _state_change(hero, meters=trans.meters, memes=trans.memes)
    world.say(
        f"Then came a change, as changes do: {trans.cue}, and the moon shone through."
    )
    world.say(
        f"{hero.id} felt {trans.from_state} become {trans.to_state}, with courage blooming anew."
    )

    world.para()
    _state_change(hero, meters={"distance": -0.5}, memes={"joy": 1.0, "conflict": -1.0})
    _state_change(pursuer, memes={"joy": 1.0, "conflict": -1.0})
    world.say(
        f"At last {hero.id} turned with a kindly grin and said, "
        f"\"Let us mend this chase from within.\""
    )
    world.say(
        f"{hero.id} chose to {rec.offer}, and {pursuer.id} saw the warmth begin."
    )
    world.say(
        f"{rec.closing}, and the quarrel floated away like a feather in the rain."
    )

    world.para()
    hero.memes["hope"] += 1.0
    hero.memes["joy"] += 1.0
    world.say(
        f"So {hero.id} brought home {quest.goal}, now {trans.to_state} and bright, "
        f"and the road behind them shimmered with reconciled light."
    )
    world.say(
        f"By the end, the quest was done, the heart was won, and every step felt right."
    )

    world.facts.update(
        hero=hero,
        pursuer=pursuer,
        quest=quest,
        transformation=trans,
        reconciliation=rec,
        place=world.place,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    trans = f["transformation"]
    rec = f["reconciliation"]
    return [
        f"Write a rhyming story for a young child about {hero.id} on a quest to {quest.goal}.",
        f"Tell a gentle tale where a small hero must elude a pursuer, grow through {trans.to_state}, and end in reconciliation.",
        f"Make a short rhyming story set on {world.place.label} that ends with kindness after a chase.",
        f"Write a child-friendly story that includes a quest, a transformation, and a peaceful ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    pursuer: Entity = f["pursuer"]
    quest: Quest = f["quest"]
    trans: Transformation = f["transformation"]
    rec: Reconciliation = f["reconciliation"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do on {world.place.label}?",
            answer=f"{hero.id} was on a quest to {quest.goal}. {hero.id} wanted to {quest.verb} so the day would feel bright and glad.",
        ),
        QAItem(
            question=f"How did {hero.id} stay safe when {pursuer.id} came near?",
            answer=f"{hero.id} chose to elude the chase by slipping away through the path, instead of running straight into trouble.",
        ),
        QAItem(
            question=f"What change happened to {hero.id} during the story?",
            answer=f"{hero.id} changed from {trans.from_state} to {trans.to_state}. That transformation helped {hero.id} feel steadier and braver.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {pursuer.id}?",
            answer=f"They reached reconciliation when {hero.id} chose to {rec.offer}. After that, the chase ended and they moved on in peace.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "quest": [
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to find, fix, or bring back something important.",
        )
    ],
    "transform": [
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a big change, like becoming braver, calmer, or stronger.",
        )
    ],
    "reconcile": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop fighting and make peace again.",
        )
    ],
    "elude": [
        QAItem(
            question="What does elude mean?",
            answer="To elude means to slip away or avoid being caught.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(WORLD_KNOWLEDGE["quest"])
    out.extend(WORLD_KNOWLEDGE["transform"])
    out.extend(WORLD_KNOWLEDGE["reconcile"])
    out.extend(WORLD_KNOWLEDGE["elude"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in world.entities.values():
        meters = {k: v for k, v in ent.meters.items() if abs(v) > 1e-9}
        memes = {k: v for k, v in ent.memes.items() if abs(v) > 1e-9}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        lines.append(f"{ent.id} ({ent.type}): " + ", ".join(parts))
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for a in sorted(PLACES[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TRANSFORMATIONS:
        lines.append(asp.fact("transformation", tid))
    for rid in RECONCILIATIONS:
        lines.append(asp.fact("reconciliation", rid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,Q,T,R) :- place(P), quest(Q), transformation(T), reconciliation(R), affords(P, quest).
#show valid/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted((p, q, t, r) for p in PLACES for q in QUESTS for t in TRANSFORMATIONS for r in RECONCILIATIONS if valid_combo(p, q, t, r))
    cl = asp_valid()
    if py == cl:
        print(f"OK: ASP and Python agree on {len(py)} combinations.")
        return 0
    print("Mismatch between ASP and Python.")
    print("Python only:", sorted(set(py) - set(cl)))
    print("ASP only:", sorted(set(cl) - set(py)))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with quest, transformation, and reconciliation.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--quest", choices=list(QUESTS))
    ap.add_argument("--transformation", choices=list(TRANSFORMATIONS))
    ap.add_argument("--reconciliation", choices=list(RECONCILIATIONS))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--pursuer")
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


CURATED = [
    StoryParams(place="moonlane", hero="Mina", hero_type="mouse", pursuer="Moss", quest="lantern", transformation="brave", reconciliation="song"),
    StoryParams(place="brook", hero="Pip", hero_type="rabbit", pursuer="Kit", quest="key", transformation="swift", reconciliation="guide"),
    StoryParams(place="meadow", hero="Luna", hero_type="bird", pursuer="Wren", quest="seed", transformation="kind", reconciliation="share"),
]


def generate(params: StoryParams) -> StorySample:
    world = World(PLACES[params.place])
    tell(world, params)
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


def resolve_all_samples() -> list[StoryParams]:
    return CURATED


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} valid combinations")
        for c in combos:
            print(c)
        return

    rng_base = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in resolve_all_samples()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 30):
            i += 1
            rng = random.Random(rng_base + i)
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = rng_base + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} on {p.place} ({p.quest} / {p.transformation} / {p.reconciliation})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
