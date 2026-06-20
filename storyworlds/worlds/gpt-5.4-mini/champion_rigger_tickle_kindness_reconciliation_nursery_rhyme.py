#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/champion_rigger_tickle_kindness_reconciliation_nursery_rhyme.py
================================================================================================

A standalone tiny storyworld in a nursery-rhyme style: a little champion and a
careful rigger have a playful row, a tickle goes wrong, kindness softens the
hurt, and reconciliation brings them back together.

Seed words: champion, rigger, tickle
Features: Kindness, Reconciliation
Style: Nursery Rhyme

This world keeps the simulated state small and concrete:
- typed entities with physical meters and emotional memes
- a forward-chained causal rule for upset, apology, and repair
- a reasonableness gate plus an inline ASP twin
- story-grounded QA and child-level world QA
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
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)
@dataclass
class Token:
    id: str
    label: str
    kind: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
            value = defaultdict(float)
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


def _r_upset(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("champion")
    b = world.entities.get("rigger")
    if not a or not b:
        return out
    if a.memes["boast"] >= THRESHOLD and b.memes["hurt"] >= THRESHOLD:
        sig = ("upset",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["guilt"] += 1
            b.memes["grump"] += 1
            out.append("__upset__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.entities.get("champion")
    b = world.entities.get("rigger")
    if not a or not b:
        return out
    if a.memes["kindness"] >= THRESHOLD and a.memes["apology"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["peace"] += 1
            b.memes["peace"] += 1
            b.memes["grump"] = 0.0
            out.append("__reconcile__")
    return out


CAUSAL_RULES = [
    Rule("upset", "social", _r_upset),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


@dataclass
class Setting:
    place: str
    detail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
@dataclass
class StoryParams:
    setting: str
    champion: str
    rigger: str
    token: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    "nursery": Setting("the nursery", "a bright little nursery with soft rugs and a toy shelf"),
    "garden": Setting("the garden", "a sleepy garden with daisies and a tiny bench"),
    "playroom": Setting("the playroom", "a cozy playroom with blocks and a painted kite"),
}

TOKENS = {
    "crown": Token("crown", "paper crown", "toy", {"bright", "proud"}),
    "kite": Token("kite", "blue kite", "toy", {"string", "wind"}),
    "stage": Token("stage", "tiny stage", "toy", {"rig", "show"}),
}

CHAMPIONS = ["Maya", "Lila", "Nora", "Ada", "Penny"]
RIGGERS = ["Pip", "Toby", "Finn", "Milo", "Theo"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TOKENS:
            combos.append((s, "champion", t))
    return combos


def reasonableness_gate(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.token not in TOKENS:
        raise StoryError("Unknown token.")
    if params.champion == params.rigger:
        raise StoryError("The champion and rigger must be different children.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about kindness and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--token", choices=TOKENS)
    ap.add_argument("--champion")
    ap.add_argument("--rigger")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    token = args.token or rng.choice(list(TOKENS))
    champ = args.champion or rng.choice(CHAMPIONS)
    rigger = args.rigger or rng.choice([n for n in RIGGERS if n != champ])
    params = StoryParams(setting, champ, rigger, token)
    reasonableness_gate(params)
    if params.champion == params.rigger:
        raise StoryError("The champion and rigger must be different children.")
    return params


def _do_tickle(world: World, champ: Entity, rigger: Entity, token: Token) -> None:
    champ.memes["boast"] += 1
    rigger.memes["hurt"] += 1
    champ.meters["tickle"] += 1
    world.say(f'{champ.id} the champion laughed, "I win!" and gave {rigger.id} a tickle.')
    world.say(f"{rigger.id} sniffled, and {token.label} wobbled on the little table.")
    propagate(world, narrate=False)


def _apology(world: World, champ: Entity, rigger: Entity) -> None:
    champ.memes["kindness"] += 1
    champ.memes["apology"] += 1
    world.say(f"Then {champ.id} grew gentle at heart. {champ.id} said, \"I was too rough.\"")
    world.say(f"{champ.id} held out a hand, and {rigger.id} held it back.")
    propagate(world, narrate=False)


def _repair(world: World, champ: Entity, rigger: Entity, token: Token) -> None:
    champ.memes["kindness"] += 1
    champ.memes["peace"] += 1
    rigger.memes["peace"] += 1
    world.say(f"{rigger.id} smiled again and fixed the {token.label}.")
    world.say(f"Together they made the little room neat, and the air felt soft as wool.")


def tell(setting: Setting, champ_name: str, rigger_name: str, token: Token) -> World:
    world = World()
    champ = world.add(Entity(id=champ_name, kind="character", type="girl", role="champion"))
    rigger = world.add(Entity(id=rigger_name, kind="character", type="boy", role="rigger"))
    prop = world.add(Entity(id=token.id, type="toy", label=token.label, attrs={"kind": token.kind}))

    champ.memes["pride"] = 1
    rigger.memes["care"] = 1

    world.say(f"In {setting.place}, under soft and sunny light, {champ.id} was the little champion of the day.")
    world.say(f"{rigger.id} was the rigger, setting up toys with tidy hands and a careful way.")
    world.say(f"{setting.detail}. {champ.id} wanted to play with the {prop.label}, for it looked so bright.")

    world.para()
    _do_tickle(world, champ, rigger, token)
    _apology(world, champ, rigger)

    world.para()
    _repair(world, champ, rigger, token)
    world.say(f"So the champion and the rigger sang and smiled, and all was well in the nursery mile.")

    world.facts.update(setting=setting, champion=champ, rigger=rigger, token=token, outcome="reconciled")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    champ = f["champion"]
    rigger = f["rigger"]
    token = f["token"]
    return [
        f'Write a nursery-rhyme-style story for a small child that includes the words '
        f'"champion", "rigger", and "tickle" and ends with kindness.',
        f"Tell a gentle rhyme about {champ.id}, the champion, and {rigger.id}, the rigger, who have a row but make up.",
        f'Write a soft, rhyming story where a tickle starts a small hurt, then kindness and reconciliation make the pair friends again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    champ = f["champion"]
    rigger = f["rigger"]
    token = f["token"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {champ.id}, the champion, and {rigger.id}, the rigger. They begin as playmates and end as friends again."
        ),
        QAItem(
            question=f"Why did {rigger.id} look sad for a moment?",
            answer=f"{champ.id} gave {rigger.id} a rough tickle, and that made {rigger.id} feel hurt. The hurt was small, but it was enough to start a little row."
        ),
        QAItem(
            question="How did they make things better?",
            answer=f"{champ.id} became kind, said sorry, and held out a hand. Then {rigger.id} smiled, fixed the {token.label}, and they were reconciled."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does kindness mean?", "Kindness means being gentle, caring, and helpful to someone else."),
        QAItem("What is reconciliation?", "Reconciliation is when people stop being upset and make friends again."),
        QAItem("What is a tickle?", "A tickle is a playful touch that can make someone laugh, though it can be too much if done roughly."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== Story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
upset :- boastful(champion), hurt(rigger).
reconciled :- kind(champion), apology(champion), upset.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid in TOKENS:
        lines.append(asp.fact("token", tid))
    lines.append(asp.fact("role", "champion"))
    lines.append(asp.fact("role", "rigger"))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    rc = 0
    model = asp.one_model(asp_program("", "#show setting/1."))
    if not asp.atoms(model, "setting"):
        print("MISMATCH: no settings from ASP.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story:
            raise RuntimeError("empty story")
        print("OK: generation smoke test passed.")
    except Exception as err:
        print(f"SMOKE FAIL: {err}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], params.champion, params.rigger, TOKENS[params.token])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
    StoryParams("nursery", "Maya", "Pip", "crown"),
    StoryParams("playroom", "Nora", "Theo", "kite"),
    StoryParams("garden", "Ada", "Finn", "stage"),
]


def resolve_params_from_curated(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if args.token and args.token not in TOKENS:
        raise StoryError("Unknown token.")
    return resolve_params(args, rng)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show setting/1.\n#show token/1.\n"))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("", "#show setting/1.\n#show token/1.\n"))
        print(f"settings: {', '.join(sorted(x[0] for x in asp.atoms(model, 'setting')))}")
        print(f"tokens: {', '.join(sorted(x[0] for x in asp.atoms(model, 'token')))}")
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
            header = f"### {p.champion} and {p.rigger}: {p.setting} / {p.token}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
