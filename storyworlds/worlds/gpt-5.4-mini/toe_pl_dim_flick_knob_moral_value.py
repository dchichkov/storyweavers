#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/toe_pl_dim_flick_knob_moral_value.py
====================================================================

A standalone storyworld for a tiny nursery-rhyme-like domain: a child, a dim
toe-pl-dim room, a tempting flick, a stubborn knob, and a clear moral value
about honesty and asking for help.

The seed words are woven into the world model:
- toe-pl-dim: the dim little place where the story happens
- flick: a risky, forbidden way to make light
- knob: the safe, ordinary thing the child can turn instead
- Moral Value: the story's social turn is about choosing the honest, safer path
- Style: Nursery Rhyme

The world is intentionally small and classical:
- a child wants light in a dim nook
- a tempting flick could cause trouble
- a careful warning changes the choice
- the child uses a knob safely instead
- the ending image proves the change: the nook is bright, calm, and kind

The script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- StoryParams, build_parser, resolve_params, generate, emit, main
- -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- Python + ASP reasonableness gate
- three QA sets grounded in world state
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
MORAL_MIN = 1.0


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
    can_flick: bool = False
    has_knob: bool = False
    gives_light: bool = False

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
class Setting:
    id: str
    place: str
    rhyme: str
    dim_spot: str
    ending_image: str

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
class Spark:
    id: str
    label: str
    phrase: str
    risky: bool = True
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
class Knob:
    id: str
    label: str
    phrase: str
    action: str
    result: str
    safe: bool = True
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
    setting: Setting
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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


def _r_flick_risk(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    room = world.get("room")
    spark = world.get("spark")
    if child.meters["flicking"] < THRESHOLD or spark.meters["lit"] < THRESHOLD:
        return out
    sig = ("flick_risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.memes["worry"] += 1
    child.memes["tempted"] += 1
    out.append("__risk__")
    return out


def _r_knob_light(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    room = world.get("room")
    knob = world.get("knob")
    if child.meters["turning"] < THRESHOLD or knob.meters["turned"] < THRESHOLD:
        return out
    sig = ("knob_light",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    room.meters["bright"] += 1
    out.append("__bright__")
    return out


CAUSAL_RULES = [
    Rule("flick_risk", "physical", _r_flick_risk),
    Rule("knob_light", "physical", _r_knob_light),
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


def use_flick(world: World, child: Entity, spark: Entity) -> None:
    child.meters["flicking"] += 1
    spark.meters["lit"] += 1
    child.memes["brave"] += 1
    propagate(world, narrate=False)


def turn_knob(world: World, child: Entity, knob: Entity) -> None:
    child.meters["turning"] += 1
    knob.meters["turned"] += 1
    child.memes["pride"] += 1
    propagate(world, narrate=False)


def speak_setup(world: World, child: Entity, parent: Entity) -> None:
    world.say(
        f"By a toe-pl-dim little window, {child.id} sat in the nook and hummed a hum. "
        f"The room was dim, and the day was young, and {child.id} wanted light to come."
    )
    world.say(
        f'{child.id} saw a flick and thought, "A flick! A flick! That may do." '
        f"But {parent.label_word} at once said, 'A flick is not for you.'"
    )


def warn(world: World, parent: Entity, child: Entity, spark: Spark, knob: Knob) -> None:
    child.memes["listening"] += 1
    world.say(
        f'"Dear little one," {parent.label_word} said soft, "the flick may bite, '
        f"and little trouble may be quick. But turn the {knob.label} and let it glow, "
        f"for safe bright light is the kind we know."
    )
    world.say(f"{child.id} looked from the flick to the {knob.label} and paused a spell.")


def moral_turn(world: World, child: Entity, parent: Entity) -> None:
    child.memes["honest"] += 1
    child.memes["kind"] += 1
    world.say(
        f'{child.id} nodded, then said, "I will not hide. I want the safe way by your side." '
        f"{parent.label_word} smiled, for honesty made the little room feel wide."
    )


def ending(world: World, child: Entity, knob: Knob, setting: Setting) -> None:
    world.say(
        f"{child.id} turned the {knob.label} just so, and {knob.action}. "
        f"At once {knob.result}, and the dim spot learned to glow."
    )
    world.say(
        f"In the toe-pl-dim nook the {setting.ending_image}, and {child.id} "
        f"sat calm and proud, with a kinder heart to show."
    )


def tell(setting: Setting, spark: Spark, knob: Knob, child_name: str = "Mina",
         child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, role="parent", label="the parent"))
    spark_ent = world.add(Entity(id="spark", type="thing", label=spark.label, can_flick=True))
    knob_ent = world.add(Entity(id="knob", type="thing", label=knob.label, has_knob=True))
    room = world.add(Entity(id="room", type="room", label=setting.place))
    room.meters["dim"] = 1.0

    speak_setup(world, child, parent)
    world.para()
    warn(world, parent, child, spark_ent, knob)
    child.memes["want"] += 1

    if spark.risky:
        use_flick(world, child, spark_ent)
        if world.get("room").memes["worry"] >= THRESHOLD:
            world.say(f"{child.id} felt the worry and stopped short, because a good heart can hear.")
    world.para()
    moral_turn(world, child, parent)
    turn_knob(world, child, knob_ent)
    ending(world, child, knob, setting)

    world.facts.update(
        child=child,
        parent=parent,
        spark=spark_ent,
        knob=knob_ent,
        setting=setting,
        outcome="kind",
        moral="honesty",
        turned=True,
        bright=room.meters["bright"] >= THRESHOLD,
    )
    return world


SETTINGS = {
    "nook": Setting("nook", "the toe-pl-dim nook", "a hush and hum", "little corner", "moonbeam on the wall"),
    "room": Setting("room", "the little room", "a soft song", "dim table", "sun on the sill"),
    "cottage": Setting("cottage", "the cozy cottage", "a warm tune", "shadow shelf", "lamp by the chair"),
}

SPARKS = {
    "flick": Spark("flick", "flick", "a flick"),
    "spark": Spark("spark", "spark", "a spark"),
    "flash": Spark("flash", "flash", "a flash"),
}

KNOBS = {
    "knob": Knob("knob", "knob", "the knob", "turned the lamp bright", "the lamp shone gold"),
    "dial": Knob("dial", "dial", "the little dial", "set the light to glow", "the glow became gentle"),
    "twist": Knob("twist", "twist", "the twist-knob", "made the lantern wake", "the lantern lit the shelf"),
}


@dataclass
@dataclass
class StoryParams:
    setting: str
    spark: str
    knob: str
    child: str
    child_gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(sid, spid, kid) for sid in SETTINGS for spid in SPARKS for kid in KNOBS if SPARKS[spid].risky and KNOBS[kid].safe]


def explain_rejection(spark: Spark, knob: Knob) -> str:
    return f"(No story: the little flick is too dangerous to pair with {knob.label} in this seed world.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a dim nook, a flick, and a safe knob.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spark", choices=SPARKS)
    ap.add_argument("--knob", choices=KNOBS)
    ap.add_argument("--child")
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
    combos = valid_combos()
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting) and (args.spark is None or c[1] == args.spark) and (args.knob is None or c[2] == args.knob)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, spark, knob = rng.choice(sorted(combos))
    child = args.child or rng.choice(["Mina", "Lula", "Nora", "Tilly", "Pippa"])
    gender = args.gender or rng.choice(["girl", "boy"])
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, spark, knob, child, gender, parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SPARKS[params.spark], KNOBS[params.knob], params.child, params.child_gender, params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story for a child named {f["child"].id} about a dim nook, a risky flick, and a safe knob.',
        f"Tell a moral-value story where {f['child'].id} chooses the safe knob instead of the flick, and ends with a bright little room.",
        f'Write a gentle story that includes the words "toe-pl-dim", "flick", and "knob", and teaches honesty and care.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    return [
        ("Who is the story about?", f"It is about {child.id} and {parent.label_word}, in a tiny toe-pl-dim nook."),
        ("What did the child first want to use?", f"{child.id} first wanted to use a flick for light, but that was the risky idea."),
        ("What safe choice did the child make?", f"{child.id} turned the knob instead. That choice was honest, careful, and kind."),
        ("How did the story end?", f"It ended with the little room bright and calm, which shows the safe choice worked."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a knob?", "A knob is a small round thing you turn with your hand. It can make a light or a switch work."),
        ("Why can a flick be risky?", "A flick can make a flame or a sudden bright spark. If it is used carelessly, it can cause trouble."),
        ("What is a moral value?", "A moral value is a good rule for how to act, like being honest, kind, careful, and brave."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], "", "== (2) Story questions =="]
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        if e.can_flick:
            bits.append("can_flick=True")
        if e.has_knob:
            bits.append("has_knob=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams("nook", "flick", "knob", "Mina", "girl", "mother"),
    StoryParams("room", "spark", "dial", "Tilly", "girl", "father"),
    StoryParams("cottage", "flash", "twist", "Nora", "girl", "mother"),
]


def valid_story(params: StoryParams) -> bool:
    return params.setting in SETTINGS and params.spark in SPARKS and params.knob in KNOBS


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for spid, sp in SPARKS.items():
        lines.append(asp.fact("spark", spid))
        if sp.risky:
            lines.append(asp.fact("risky", spid))
    for kid, knob in KNOBS.items():
        lines.append(asp.fact("knob", kid))
        if knob.safe:
            lines.append(asp.fact("safe", kid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, K) :- setting(S), spark(P), knob(K), risky(P), safe(K).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in the gate.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test succeeded.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, p, k in asp_valid_combos():
            print(f"  {s:8} {p:8} {k}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.spark} -> {p.knob} ({p.setting})"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a nursery-rhyme-style story for a child named {f["child"].id} about a dim nook, a risky flick, and a safe knob.',
        f"Tell a moral-value story where {f['child'].id} chooses the safe knob instead of the flick, and ends with a bright little room.",
        f'Write a gentle story that includes the words "toe-pl-dim", "flick", and "knob", and teaches honesty and care.',
    ]


if __name__ == "__main__":
    main()
