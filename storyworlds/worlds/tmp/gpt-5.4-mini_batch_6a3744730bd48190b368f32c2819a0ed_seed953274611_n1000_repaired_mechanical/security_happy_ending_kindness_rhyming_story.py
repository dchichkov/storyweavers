#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/security_happy_ending_kindness_rhyming_story.py
================================================================================

A small standalone storyworld about a child, a security gate, a mix-up, and a
kind helper who makes everything safe again.

The story is intentionally built as a tiny simulated world:
- typed entities with physical meters and emotional memes
- a forward-chaining causal model
- a reasonableness gate
- a happy-ending branch and a near-miss branch
- child-facing prose with a light rhyming style

Theme seed words:
- security
- Happy Ending
- Kindness
- Rhyming Story
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
SECURE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

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
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class SecurityRule:
    id: str
    label: str
    secure: int
    calm: int
    helper: str
    line: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    setting: str
    child_name: str
    child_type: str
    guide_name: str
    guide_type: str
    rule: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child or child.meters["worry"] < THRESHOLD:
        return out
    sig = ("worry",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("__worry__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    guide = world.entities.get("guide")
    if not child or not guide:
        return out
    if guide.meters["kindness"] < THRESHOLD or child.meters["worry"] < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["calm"] += 1
    guide.memes["kindness"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("worry", _r_worry), Rule("calm", _r_calm)]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    for s in produced:
        world.say(s)
    return produced


SETTINGS = {
    "gate": "the front gate",
    "door": "the little door",
    "desk": "the reception desk",
}

RULES = {
    "keycard": SecurityRule(
        id="keycard",
        label="a keycard",
        secure=3,
        calm=3,
        helper="guard",
        line="held a shiny keycard and waved it with a smile",
        tags={"card", "security", "door"},
    ),
    "badge": SecurityRule(
        id="badge",
        label="a badge",
        secure=2,
        calm=2,
        helper="guard",
        line="showed a bright badge and opened the way",
        tags={"badge", "security"},
    ),
    "code": SecurityRule(
        id="code",
        label="a code",
        secure=2,
        calm=2,
        helper="helper",
        line="typed a code with care and made the lock obey",
        tags={"code", "security"},
    ),
}

HELPERS = {
    "guard": ("guard", "a friendly guard"),
    "helper": ("helper", "a kind helper"),
}

NAMES = {
    "girl": ["Mia", "Lila", "Nora", "Ava", "Zoe"],
    "boy": ["Ben", "Theo", "Leo", "Max", "Finn"],
}


def valid_combos() -> list[tuple[str, str]]:
    return [(s, r) for s in SETTINGS for r in RULES if rule_is_reasonable(RULES[r])]


def rule_is_reasonable(rule: SecurityRule) -> bool:
    return rule.secure >= SECURE_MIN


def best_rule() -> SecurityRule:
    return max(RULES.values(), key=lambda r: (r.secure, r.calm))


def outcome_of(params: StoryParams) -> str:
    return "happy" if rule_is_reasonable(RULES[params.rule]) else "blocked"


def tell(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.rule not in RULES:
        raise StoryError("Unknown security rule.")
    rule = RULES[params.rule]
    if not rule_is_reasonable(rule):
        raise StoryError(f"(No story: {rule.label} is not secure enough for this world.)")

    world = World()
    child = world.add(Entity(id="child", kind="character", type=params.child_type, role="child"))
    guide = world.add(Entity(id="guide", kind="character", type=params.guide_type, role="guide", label="the guide"))
    gate = world.add(Entity(id="gate", kind="thing", type="gate", label=SETTINGS[params.setting]))

    child.memes["hope"] = 1
    guide.memes["kindness"] = 1

    world.say(
        f"At {SETTINGS[params.setting]}, {params.child_name} came to call, "
        f"and the air felt bright and small."
    )
    world.say(
        f"{params.child_name} wanted in with a happy spin, but the gate said, "
        f"\"Please be kind and wait.\""
    )

    world.para()
    child.meters["worry"] += 1
    child.memes["want"] += 1
    world.say(
        f"{params.child_name} peered near the lock and felt a little shock; "
        f"the way was shut, not open wide."
    )
    world.say(
        f"Then {params.guide_name} stepped near with a gentle cheer, "
        f"and said, \"Let us keep each other safe.\""
    )

    world.para()
    guide.meters["kindness"] += 1
    child.meters["worry"] += 1
    propagate(world)
    world.say(
        f'"I will help," said {params.guide_name}, and {rule.line}, '
        f"so the door could open right on time."
    )
    world.say(
        f"{params.child_name} smiled and stood a little taller; kindness made the day feel fine."
    )

    world.para()
    child.memes["joy"] += 1
    child.memes["calm"] += 1
    gate.meters["open"] += 1
    world.say(
        f"The gate swung wide, the clouds looked light, and everything felt right. "
        f"{params.child_name} walked through safe and slow."
    )
    world.say(
        f"With a thankful grin and a tiny spin, {params.child_name} waved goodbye, "
        f"and the day could glow."
    )

    world.facts.update(
        setting=params.setting,
        child_name=params.child_name,
        child_type=params.child_type,
        guide_name=params.guide_name,
        guide_type=params.guide_type,
        rule=params.rule,
        outcome="happy",
        rule_label=rule.label,
        gate=SETTINGS[params.setting],
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the word "security" and ends happily.',
        f"Tell a kindness-filled security story where {f['child_name']} is stopped at {f['gate']} and a guide helps with a smile.",
        f'Write a gentle rhyming story about being safe, kind, and patient around "security".',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child_name"]
    guide = f["guide_name"]
    gate = f["gate"]
    rule = RULES[f["rule"]]
    return [
        ("Who is the story about?",
         f"It is about {child} and {guide} at {gate}. The two of them make the security moment feel safe and kind."),
        ("What did the guide do?",
         f"{guide} helped with a smile and used {rule.label} to open the way. That kindness turned the worried moment into a happy one."),
        ("How did the story end?",
         f"It ended happily, with {child} walking through safely. The gate opened, and the day stayed bright and calm."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is security?",
         "Security is the work of keeping people safe and protected. It can mean a gate, a lock, or a person watching carefully."),
        ("Why is kindness important?",
         "Kindness helps people feel calm and cared for. A kind helper can turn a scary moment into a safe one."),
        ("What does a guard do?",
         "A guard watches a place and helps keep it safe. Guards often help people know where to go."),
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
secure_rule(R) :- rule(R), secure(R,S), secure_min(M), S >= M.
happy_end :- secure_rule(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for rid, rule in RULES.items():
        lines.append(asp.fact("rule", rid))
        lines.append(asp.fact("secure", rid, rule.secure))
    lines.append(asp.fact("secure_min", SECURE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show secure_rule/1."))
    return sorted(set(asp.atoms(model, "secure_rule")))


def asp_verify() -> int:
    import io
    import contextlib

    rc = 0
    if set(asp_valid_combos()) != set((r,) for _, r in valid_combos()):
        rc = 1
        print("MISMATCH in ASP parity.")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            sample = generate(resolve_params(argparse.Namespace(
                setting=None, child_name=None, child_type=None, guide_name=None,
                guide_type=None, rule=None, seed=None
            ), random.Random(777)))
            _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    try:
        emit(sample)
    except Exception as exc:
        print(f"EMIT SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: verify smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny security storyworld with kindness and happy endings.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--rule", choices=RULES)
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--guide-name")
    ap.add_argument("--guide-type", choices=["mother", "father", "woman", "man", "girl", "boy"])
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
    if args.rule and args.rule not in RULES:
        raise StoryError("Unknown rule.")
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.rule and not rule_is_reasonable(RULES[args.rule]):
        raise StoryError("That rule is not secure enough.")

    choices = [r for r in RULES if rule_is_reasonable(RULES[r])]
    rule = args.rule or rng.choice(choices)
    setting = args.setting or rng.choice(list(SETTINGS))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    guide_type = args.guide_type or rng.choice(["woman", "man", "girl", "boy", "mother", "father"])
    child_name = args.child_name or rng.choice(NAMES[child_type])
    guide_name = args.guide_name or rng.choice(["Rae", "Jo", "Sam", "Kai", "Pip"])
    return StoryParams(setting=setting, child_name=child_name, child_type=child_type,
                       guide_name=guide_name, guide_type=guide_type, rule=rule)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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


CURATED = [
    StoryParams(setting="gate", child_name="Mia", child_type="girl", guide_name="Rae", guide_type="woman", rule="keycard"),
    StoryParams(setting="door", child_name="Ben", child_type="boy", guide_name="Jo", guide_type="man", rule="badge"),
    StoryParams(setting="desk", child_name="Lila", child_type="girl", guide_name="Kai", guide_type="boy", rule="code"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show secure_rule/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("secure choices:", ", ".join(r for (r,) in asp_valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
