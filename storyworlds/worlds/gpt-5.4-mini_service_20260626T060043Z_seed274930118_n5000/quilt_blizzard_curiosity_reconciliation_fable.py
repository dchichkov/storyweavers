#!/usr/bin/env python3
"""
storyworlds/worlds/quilt_blizzard_curiosity_reconciliation_fable.py
====================================================================

A small fable-style storyworld about a quilt, a blizzard, curious choices,
and a warm reconciliation.

The seed picture behind this world is simple:
A careful child wants to know what the blizzard sounds like, slips outside,
loses the cozy quilt to the wind, and later makes peace with an elder by
helping restore warmth and trust.

This world keeps the simulation tiny and classical:
- a child, an elder, one beloved quilt, and one blizzard
- curiosity raises risk
- the blizzard can blow the quilt away if it is outside and uncovered
- reconciliation follows a gentle repair: searching together, then mending
  both the quilt and the mood

The prose is authored from world state, not from a frozen template.
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
    inside: bool = False
    protected: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("cold", "damage", "search", "warmth"):
            self.meters.setdefault(k, 0.0)
        for k in ("curiosity", "worry", "grief", "love", "reconciliation", "joy"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "elderwoman"}
        male = {"boy", "father", "man", "elderman"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the cabin"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quilt:
    label: str
    phrase: str
    warmth: float = 2.0


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def outside(self, actor: Entity) -> bool:
        return not actor.inside


def _blizzard_harms_quilt(world: World) -> list[str]:
    out: list[str] = []
    blizzard = world.facts["blizzard"]
    if not blizzard:
        return out
    for actor in world.characters():
        if actor.memes["curiosity"] < THRESHOLD:
            continue
        quilt = world.get("quilt")
        if quilt.worn_by != actor.id:
            continue
        if actor.inside:
            continue
        sig = ("blow", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["cold"] += 1.0
        quilt.meters["damage"] += 1.0
        actor.memes["worry"] += 1.0
        out.append(f"The wind worried the quilt and made the child shiver.")
    return out


def _damage_invites_repair(world: World) -> list[str]:
    out: list[str] = []
    quilt = world.get("quilt")
    elder = world.get("elder")
    child = world.get("child")
    if quilt.meters["damage"] < THRESHOLD or child.memes["worry"] < THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    elder.memes["grief"] += 1.0
    out.append(f"That left the elder with a heavy heart.")
    return out


def _reconciliation_follows_search(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    elder = world.get("elder")
    quilt = world.get("quilt")
    if child.meters["search"] < THRESHOLD:
        return out
    if quilt.meters["damage"] < THRESHOLD:
        return out
    sig = ("reconcile",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["reconciliation"] += 1.0
    elder.memes["reconciliation"] += 1.0
    child.memes["joy"] += 1.0
    elder.memes["love"] += 1.0
    out.append(f"At last, the child and the elder found the quilt and made peace.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_blizzard_harms_quilt, _damage_invites_repair, _reconciliation_follows_search):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "cabin": Setting(place="the cabin", affords={"blizzard"}),
    "porch": Setting(place="the porch", affords={"blizzard"}),
    "village": Setting(place="the village path", affords={"blizzard"}),
}

NAMES = {
    "girl": ["Mina", "Lena", "Ivy", "Nora", "Tess"],
    "boy": ["Owen", "Eli", "Finn", "Jonah", "Theo"],
}
TRAITS = ["curious", "quiet", "brave", "gentle", "thoughtful"]


QUILTS = {
    "patchwork": Quilt(label="patchwork quilt", phrase="a soft patchwork quilt"),
    "blue": Quilt(label="blue quilt", phrase="a blue quilt stitched with stars"),
    "grand": Quilt(label="grandmother's quilt", phrase="a grandmother's quilt with warm squares"),
}


@dataclass
class WorldFacts:
    child: Entity
    elder: Entity
    quilt: Entity
    setting: Setting
    blizzard: bool


ASP_RULES = r"""
% An object is at risk when the child is outside during the blizzard.
at_risk(Q,C) :- child(C), quilt(Q), blizzard, outside(C).

% Curiosity can lead the child outside.
curious(C) :- child(C), mind(C,curiosity).

% A damage event happens if the quilt is at risk.
damaged(Q,C) :- at_risk(Q,C).

% Reconciliation is possible only after search and damage have both occurred.
reconciled(C,E) :- child(C), elder(E), searched(C), damaged(_,C).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for qid in QUILTS:
        lines.append(asp.fact("quilt", qid))
    lines.append(asp.fact("child", "child"))
    lines.append(asp.fact("elder", "elder"))
    lines.append(asp.fact("blizzard"))
    lines.append(asp.fact("outside", "child"))
    lines.append(asp.fact("mind", "child", "curiosity"))
    lines.append(asp.fact("searched", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_places() -> list[str]:
    return sorted(SETTINGS)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in SETTINGS:
        combos.append((place, "blizzard"))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show at_risk/2.\n#show reconciled/2."))
    return sorted(set(asp.atoms(model, "at_risk")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set((p, a) for p, a in asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


def make_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    world = World(setting)
    world.weather = "blizzard"
    child = world.add(Entity(
        id="child",
        kind="character",
        type=params.gender,
        label=params.name,
        meters={"cold": 0.0, "damage": 0.0, "search": 0.0, "warmth": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "grief": 0.0, "love": 0.0, "reconciliation": 0.0, "joy": 0.0},
    ))
    elder = world.add(Entity(
        id="elder",
        kind="character",
        type=params.elder,
        label="the elder",
        meters={"cold": 0.0, "damage": 0.0, "search": 0.0, "warmth": 0.0},
    ))
    quilt_cfg = QUILTS["patchwork"]
    quilt = world.add(Entity(
        id="quilt",
        type="quilt",
        label=quilt_cfg.label,
        phrase=quilt_cfg.phrase,
        owner=child.id,
        caretaker=elder.id,
        worn_by=child.id,
        protected=False,
        meters={"cold": 0.0, "damage": 0.0, "search": 0.0, "warmth": quilt_cfg.warmth},
    ))
    world.facts = {
        "child": child,
        "elder": elder,
        "quilt": quilt,
        "setting": setting,
        "blizzard": True,
        "trait": params.trait,
    }
    return world


def tell(world: World, params: StoryParams) -> World:
    child = world.get("child")
    elder = world.get("elder")
    quilt = world.get("quilt")

    world.say(
        f"{child.label} was a {params.trait} child who loved the comfort of {quilt.phrase}."
    )
    world.say(
        f"The elder kept the quilt near the fire, because a warm thing should be treated with care."
    )
    world.para()
    world.say(
        f"One blizzard day, {child.label} went to {world.setting.place} and listened to the roaring wind."
    )
    world.say(
        f"{child.label} was full of curiosity and wanted to know what the storm sounded like up close."
    )
    child.memes["curiosity"] += 1.0
    child.inside = False
    world.say(
        f"{child.label} stepped outside with the quilt wrapped around {child.pronoun('object')}."
    )
    propagate(world, narrate=True)
    world.para()
    if quilt.meters["damage"] >= THRESHOLD:
        world.say(
            f"When the wind tugged the quilt loose, {child.label} hurried back, worried and cold."
        )
        child.meters["search"] += 1.0
        world.say(
            f"{child.label} and the elder searched together, following tiny drifts in the snow."
        )
        propagate(world, narrate=True)
        world.say(
            f"They found the quilt behind a drift, shook the snow from it, and mended the torn edge."
        )
        quilt.meters["damage"] = 0.0
        child.memes["reconciliation"] += 1.0
        elder.memes["reconciliation"] += 1.0
        child.meters["warmth"] += quilt.meters["warmth"]
        world.say(
            f"{child.label} thanked the elder for the patience to search, and the elder smiled at the wiser child."
        )
    else:
        world.say(
            f"Because the quilt stayed safe, the child learned that care matters even when curiosity calls."
        )

    world.facts["resolved"] = quilt.meters["damage"] < THRESHOLD
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    elder: Entity = f["elder"]
    quilt: Entity = f["quilt"]
    trait = f["trait"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {child.label}, a {trait} child, and the elder who cared for the quilt.",
        ),
        QAItem(
            question=f"What did {child.label} want to know during the blizzard?",
            answer=f"{child.label} wanted to know what the blizzard sounded like up close.",
        ),
        QAItem(
            question=f"What happened to the quilt after {child.label} went outside?",
            answer=(
                f"The wind tugged at {quilt.label}, and it got damaged before the child and the elder found it."
                if quilt.meters["damage"] < 1.0 else
                f"The wind worried the {quilt.label}, so the child had to search for it and mend it."
            ),
        ),
        QAItem(
            question=f"How did the child and the elder end the trouble?",
            answer="They searched together, found the quilt, mended it, and made peace again.",
        ),
    ]
    if world.facts.get("resolved"):
        qa.append(QAItem(
            question=f"What changed by the end of the story?",
            answer=(
                f"The child grew wiser, the elder felt comforted, and the quilt was repaired and warm again."
            ),
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to know or see more, even when something is a little unknown.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who had hurt feelings make peace again.",
        ),
        QAItem(
            question="What is a blizzard?",
            answer="A blizzard is a storm with blowing snow and strong, cold wind.",
        ),
        QAItem(
            question="What is a quilt?",
            answer="A quilt is a warm blanket made from stitched pieces of cloth.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    child: Entity = world.facts["child"]
    return [
        'Write a short fable for children about curiosity, a blizzard, and a warm quilt.',
        f"Tell a gentle story about {child.label} following curiosity into a blizzard and finding reconciliation afterward.",
        "Write a child-friendly tale where a quilt is nearly lost in the snow, then repaired through kindness and search.",
    ]


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
        if e.kind == "character":
            bits.append(f"inside={e.inside}")
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


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


def explain_rejection(place: str) -> str:
    return f"(No story: {place} is not a valid blizzard setting in this small world.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in SETTINGS:
        raise StoryError(explain_rejection(args.place))
    place = args.place or rng.choice(list(SETTINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    elder = args.elder or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    world = tell(world, params)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a fable of curiosity, a blizzard, a quilt, and reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["mother", "father", "grandmother", "grandfather"])
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


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reconciled/2."))
    return sorted(set(asp.atoms(model, "reconciled")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reconciled/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible combos ({len(stories)} with reconciliation):\n")
        for p, a in combos:
            print(f"  {p:10} {a:10}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if args.all:
        for place in SETTINGS:
            params = StoryParams(place=place, name="Mina", gender="girl", elder="grandmother", trait="curious")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 30, 30):
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
            header = f"### {p.name}: {p.place} ({p.trait})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
