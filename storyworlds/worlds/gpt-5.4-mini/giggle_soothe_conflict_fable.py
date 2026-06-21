#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/giggle_soothe_conflict_fable.py
===============================================================

A small, standalone storyworld in a fable-like style.

Domain:
- One animal character learns that a careless giggle can start conflict.
- Another character uses a calm soothe to repair the hurt.
- The ending proves a change in state: conflict eases, trust grows, and the
  characters share a kinder sound at the end.

This script follows the Storyweavers storyworld contract:
- stdlib only
- typed entities with physical meters and emotional memes
- Python reasonableness gate plus inline ASP twin
- story / QA / world knowledge generation from simulated state
- CLI support for default runs, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
CONFLICT_LIMIT = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
class Creature:
    id: str
    type: str
    label: str
    habitat: str
    gift: str
    flaw: str
    fix: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters["hurt"] < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["conflict"] += 1
        for other in list(world.entities.values()):
            if other.id != ent.id and other.kind == "character":
                other.memes["uneasy"] += 1
        out.append("__conflict__")
    return out


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("soothed"):
        for ent in list(world.entities.values()):
            if ent.kind == "character" and ent.meters["conflict"] >= THRESHOLD:
                sig = ("calm", ent.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                ent.meters["conflict"] = 0.0
                ent.memes["peace"] += 1
                out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("conflict", "social", _r_conflict),
    Rule("soothe", "social", _r_soothe),
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


def reasonableness_gate(spark: Creature, target: Creature, helper: Creature) -> bool:
    return spark.id != target.id and helper.fix == "soothe" and spark.flaw in {"taunt", "snicker"} and target.flaw in {"pride", "worry"}


def severity_of(spark: Creature) -> int:
    return 2 if spark.flaw == "taunt" else 1


def can_soothe(helper: Creature, severity: int) -> bool:
    return helper.fix == "soothe" and severity <= 2


def setup(world: World, spark: Entity, target: Entity, helper: Entity, setting: Creature) -> None:
    world.say(
        f"In a little fable village by the river, {spark.id} the {setting.id} "
        f"and {target.id} the {helper.attrs['creature'].habitat} often crossed paths."
    )
    world.say(
        f"{spark.id} loved a bright giggle, and {target.id} loved a quiet path. "
        f"That made the morning easy until one sharp remark bent the air."
    )


def start_conflict(world: World, spark: Entity, target: Entity) -> None:
    spark.memes["pride"] += 1
    target.meters["hurt"] += 1
    target.memes["sad"] += 1
    world.say(
        f"{spark.id} let out a teasing giggle. The sound was small, but it stung "
        f"{target.id} like a thorn."
    )
    world.say(
        f"{target.id} stepped back, hurt and cross. Soon there was conflict, and "
        f"even the birds in the hedge grew quiet."
    )
    propagate(world, narrate=False)


def soothe(world: World, helper: Entity, spark: Entity, target: Entity, setting: Creature) -> None:
    world.facts["soothed"] = True
    helper.memes["kindness"] += 1
    helper.memes["peace"] += 1
    world.say(
        f"Then {helper.id} came softly to the middle and spoke in a low voice. "
        f'"Let us not grow hard over one bad moment," {helper.pronoun()} said.'
    )
    world.say(
        f"{helper.id} told {spark.id} how to mend the hurt and asked {target.id} "
        f"to breathe with the trees. The village path felt gentle again."
    )
    propagate(world, narrate=False)


def resolve(world: World, spark: Entity, target: Entity, helper: Entity, setting: Creature) -> None:
    spark.memes["shame"] += 1
    spark.memes["kindness"] += 1
    target.memes["trust"] += 1
    target.memes["relief"] += 1
    world.say(
        f"{spark.id} lowered {spark.pronoun('possessive')} head and offered a true "
        f"apology. {target.id} listened, and the two of them shared a small smile."
    )
    world.say(
        f"After that, the same lane by the river felt new: the giggle was no longer "
        f"a thorn, but a light sound with no sting."
    )
    world.say(
        f"By sunset, {spark.id}, {target.id}, and {helper.id} walked home together, "
        f"and the whole village seemed kinder for it."
    )


def tell(setting: Creature, spark: Creature, target: Creature, helper: Creature) -> World:
    world = World()
    a = world.add(Entity(id=spark.id, kind="character", type="boy" if spark.id in {"Fox", "Crow"} else "girl", role="spark"))
    b = world.add(Entity(id=target.id, kind="character", type="girl" if target.id in {"Hare", "Mole"} else "boy", role="target"))
    c = world.add(Entity(id=helper.id, kind="character", type="girl" if helper.id in {"Badger", "Heron"} else "boy", role="helper"))
    c.attrs["creature"] = helper

    setup(world, a, b, c, setting)
    world.para()
    start_conflict(world, a, b)
    world.para()
    soothe(world, c, a, b, setting)
    resolve(world, a, b, c, setting)
    world.facts.update(setting=setting, spark=a, target=b, helper=c, severity=severity_of(spark), outcome="soothed")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fable for a young child that uses the words "giggle" and "soothe" and shows conflict turning into peace.',
        f"Tell a gentle animal fable where {f['spark'].id} makes a hurtful giggle, {f['target'].id} feels upset, and {f['helper'].id} soothes them back together.",
        f'Write a small moral story with a river path, a conflict, and a calm soothing ending that teaches kinder speech.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b, c = f["spark"], f["target"], f["helper"]
    return [
        QAItem(
            question="What started the conflict?",
            answer=f"{a.id} made a teasing giggle, and it hurt {b.id}'s feelings. That small sound turned the morning tense."
        ),
        QAItem(
            question="How was the hurt fixed?",
            answer=f"{c.id} soothed the two of them by speaking softly and asking everyone to breathe. That calm helped the conflict melt away."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with an apology, a shared smile, and a peaceful walk home. The village felt kinder than before."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does soothe mean?",
            answer="To soothe means to make someone feel calmer and less upset. A soft voice, a gentle touch, or kind words can soothe."
        ),
        QAItem(
            question="Why can a teasing giggle cause trouble?",
            answer="A giggle can cause trouble if it is meant to mock or tease. Even a small sound can hurt feelings and start conflict."
        ),
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story, often with animals, that teaches a lesson. It usually ends by showing what kind behavior looks like."
        ),
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


@dataclass
@dataclass
class StoryParams:
    setting: str
    spark: str
    target: str
    helper: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


SETTINGS = {
    "river": Creature("River", "place", "river village", "riverbank", "quiet path", "noise", "soothe", {"fable"}),
    "meadow": Creature("Meadow", "place", "meadow village", "grass lane", "soft trail", "noise", "soothe", {"fable"}),
    "orchard": Creature("Orchard", "place", "orchard lane", "tree row", "gentle track", "noise", "soothe", {"fable"}),
}

CHARACTERS = {
    "Fox": Creature("Fox", "fox", "fox", "woods", "bright giggle", "taunt", "soothe", {"giggle"}),
    "Crow": Creature("Crow", "crow", "crow", "sky", "sharp giggle", "snicker", "soothe", {"giggle"}),
    "Hare": Creature("Hare", "hare", "hare", "field", "quiet worry", "pride", "soothe", {"conflict"}),
    "Mole": Creature("Mole", "mole", "mole", "burrow", "small worry", "pride", "soothe", {"conflict"}),
    "Badger": Creature("Badger", "badger", "badger", "den", "calm voice", "kindness", "soothe", {"soothe"}),
    "Heron": Creature("Heron", "heron", "heron", "marsh", "soft words", "kindness", "soothe", {"soothe"}),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for spark_id in ["Fox", "Crow"]:
            for target_id in ["Hare", "Mole"]:
                for helper_id in ["Badger", "Heron"]:
                    if reasonableness_gate(CHARACTERS[spark_id], CHARACTERS[target_id], CHARACTERS[helper_id]):
                        combos.append((sid, spark_id, target_id, helper_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world of giggles, soothing, and repaired conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spark", choices=["Fox", "Crow"])
    ap.add_argument("--target", choices=["Hare", "Mole"])
    ap.add_argument("--helper", choices=["Badger", "Heron"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.spark is None or c[1] == args.spark)
              and (args.target is None or c[2] == args.target)
              and (args.helper is None or c[3] == args.helper)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, spark, target, helper = rng.choice(sorted(combos))
    return StoryParams(setting, spark, target, helper)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHARACTERS[params.spark], CHARACTERS[params.target], CHARACTERS[params.helper])
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
conflict(X) :- hurt(X).
peace(X) :- soothed.
valid(S, A, B, H) :- setting(S), spark(A), target(B), helper(H), A != B, soothed_by(H).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHARACTERS:
        lines.append(asp.fact("character", cid))
    lines.append(asp.fact("soothed_by", "Badger"))
    lines.append(asp.fact("soothed_by", "Heron"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate.")
        print("only in asp:", sorted(a - b))
        print("only in py:", sorted(b - a))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: smoke-tested default story generation.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("river", "Fox", "Hare", "Badger"),
    StoryParams("meadow", "Crow", "Mole", "Heron"),
    StoryParams("orchard", "Fox", "Mole", "Badger"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
            i += 1
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
