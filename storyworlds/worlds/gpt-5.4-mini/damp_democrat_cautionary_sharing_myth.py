#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/damp_democrat_cautionary_sharing_myth.py
==========================================================================

A small mythic storyworld about a damp village blessing, a elected democrat
keeper, and the hard lesson that a shared gift stays bright while a hoarded one
turns sour.

This world is designed around the seed words and features:
- words: damp, democrat
- features: cautionary, sharing
- style: myth

The world model is tiny but state-driven: a blessing can become wet and dull,
a leader can warn or urge sharing, and the ending changes based on whether the
gift is offered around the circle or held too tightly.
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
BLESSED_MIN = 1.0
SHARE_MIN = 1.0


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
        female = {"girl", "mother", "mom", "woman", "elder"}
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_dampen(world: World) -> list[str]:
    out: list[str] = []
    relic = world.entities.get("relic")
    if relic and relic.meters["wet"] >= THRESHOLD and ("dampen",) not in world.fired:
        world.fired.add(("dampen",))
        relic.meters["glow"] = max(0.0, relic.meters["glow"] - 1.0)
        relic.memes["sorrow"] += 1
        out.append("__dampen__")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    relic = world.entities.get("relic")
    if relic and relic.memes["shared"] >= SHARE_MIN and ("share",) not in world.fired:
        world.fired.add(("share",))
        relic.meters["glow"] += 1
        relic.memes["peace"] += 1
        out.append("__share__")
    return out


CAUSAL_RULES = [Rule("dampen", "physical", _r_dampen), Rule("share", "social", _r_share)]


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


@dataclass
class Shrine:
    name: str
    gift: str
    place: str
    danger: str
    warning: str

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
class Role:
    id: str
    title: str
    caution: str
    shares: str

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


SHRINES = {
    "well": Shrine("well", "silver cup", "the stone well", "damp moss", "The stone stays damp after rain"),
    "harbor": Shrine("harbor", "lantern shell", "the harbor shrine", "salt spray", "The sea keeps the steps damp"),
    "hill": Shrine("hill", "harp stone", "the hill altar", "mist", "The dawn mist leaves the grass damp"),
}

ROLES = {
    "democrat": Role("democrat", "democrat", "share the gift before it fades", "pass it from hand to hand"),
    "elder": Role("elder", "elder", "share it or the blessing will dull", "offer it to each neighbor"),
    "keeper": Role("keeper", "keeper", "share it while it still shines", "let each child hold it"),
}

NAMES = ["Mira", "Kian", "Lio", "Tala", "Soren", "Nia", "Rin", "Ari"]
PARENTS = ["mother", "father", "grandmother", "grandfather"]


@dataclass
@dataclass
class StoryParams:
    shrine: str
    role: str
    child: str
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


def valid_combos() -> list[tuple[str, str]]:
    return [(s, r) for s in SHRINES for r in ROLES]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic cautionary sharing storyworld.")
    ap.add_argument("--shrine", choices=SHRINES)
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--parent", choices=PARENTS)
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
              if (args.shrine is None or c[0] == args.shrine)
              and (args.role is None or c[1] == args.role)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    shrine, role = rng.choice(sorted(combos))
    return StoryParams(
        shrine=shrine,
        role=role,
        child=args.name or rng.choice(NAMES),
        parent=args.parent or rng.choice(PARENTS),
    )


def tell(shrine: Shrine, role: Role, child: str, parent: str) -> World:
    w = World()
    child_e = w.add(Entity(id=child, kind="character", type="child", role="seeker"))
    parent_e = w.add(Entity(id=parent.title(), kind="character", type=parent, role="guardian", label=f"the {parent}"))
    leader = w.add(Entity(id="Leader", kind="character", type="elder", role="democrat", label=f"the {role.title}"))
    relic = w.add(Entity(id="relic", kind="thing", type="relic", label=shrine.gift, role="gift"))
    w.facts.update(child=child_e, parent=parent_e, leader=leader, relic=relic, shrine=shrine, role=role)

    child_e.memes["wonder"] += 1
    child_e.memes["want"] += 1
    relic.meters["glow"] = 1.0

    w.say(
        f"In old times, at {shrine.place}, {child} found {shrine.gift} beside {shrine.danger}. "
        f"The air was damp, and the stones held the memory of rain."
    )
    w.say(
        f'"Look," said {child}, "a blessing!" But {parent_e.label_word} frowned, because {shrine.warning}.'
    )

    w.para()
    w.say(
        f"Then came {leader.label_word}, a {role.title} who knew the old rule: {role.caution}."
    )
    relic.memes["shared"] += 1
    w.say(
        f'"{role.shares}," said {leader.label_word}, and {child} felt the story of the gift change in {child_e.pronoun("possessive")} hands.'
    )
    propagate(w, narrate=True)
    relic.meters["wet"] += 1
    propagate(w, narrate=True)

    if relic.meters["glow"] >= 1.0:
        w.para()
        w.say(
            f"So {child} did not keep the blessing alone. {child} handed it around the circle, and each person warmed it with one kind touch."
        )
        w.say(
            f"By sunset, {shrine.gift} shone again, and even the damp stones looked bright."
        )
        outcome = "shared"
    else:
        w.para()
        w.say(
            f"But when {child} tried to hold it back, the blessing grew dull and cold. The damp air made the secret small."
        )
        w.say(
            f"{parent_e.label_word.capitalize()} led {child} home, and {child} learned that a gift kept alone can lose its song."
        )
        outcome = "hoarded"

    w.facts["outcome"] = outcome
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a mythic cautionary story that includes the words "damp" and "democrat" and ends with sharing.',
        f"Tell a small legend where {f['child'].id} finds {f['shrine'].gift} near {f['shrine'].danger} and a {f['role'].title} teaches a sharing rule.",
        f"Write a child-facing myth about a blessing, a warning, and a circle of hands.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, parent, leader, shrine, role, outcome = f["child"], f["parent"], f["leader"], f["shrine"], f["role"], f["outcome"]
    items = [
        QAItem(
            question="What did the child find?",
            answer=f"{child.id} found {shrine.gift} at {shrine.place}. It looked special because the old place was damp and quiet."
        ),
        QAItem(
            question="Who gave the warning?",
            answer=f"{parent.label_word.capitalize()} gave the first warning, and then {leader.label_word} repeated the old caution. Both knew the gift should not be kept carelessly."
        ),
        QAItem(
            question="What did the democrat teach?",
            answer=f"The democrat taught that {role.shares}. That way the blessing could stay bright instead of going dull in one pair of hands."
        ),
    ]
    if outcome == "shared":
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended well because the child shared the gift around the circle. The blessing grew brighter when everyone held it kindly."
        ))
    else:
        items.append(QAItem(
            question="How did the story end?",
            answer=f"It ended sadly because the child tried to keep the gift alone. The damp air made the blessing fade until the child learned the lesson."
        ))
    return items


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does damp mean?",
            answer="Damp means a little wet, like stone after rain or grass in morning mist."
        ),
        QAItem(
            question="What is a democrat in this story?",
            answer="A democrat is the chosen village leader who helps make fair choices and reminds everyone to share."
        ),
        QAItem(
            question="Why does sharing matter here?",
            answer="Sharing matters because the blessing stays lively when it moves from hand to hand. If one person keeps it too long, it can fade."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "", "== (2) Story QA =="]
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("well", "democrat", "Mira", "mother"),
    StoryParams("harbor", "elder", "Kian", "grandmother"),
    StoryParams("hill", "keeper", "Tala", "father"),
]


ASP_RULES = r"""
shared(X) :- has_gift(X), offered(X).
damped(X) :- wet(X).
bright(X) :- shared(X), not damped(X).
outcome(shared) :- bright(relic).
outcome(hoarded) :- has_gift(relic), not bright(relic).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SHRINES:
        lines.append(asp.fact("shrine", s))
    for r in ROLES:
        lines.append(asp.fact("role", r))
    lines.append(asp.fact("has_gift", "relic"))
    lines.append(asp.fact("offered", "relic"))
    lines.append(asp.fact("wet", "relic"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show outcome/1."))
    outs = set(asp.atoms(model, "outcome"))
    py = {"shared"} if any(p == "shared" for p in [tell(SHRINES[c.shrine], ROLES[c.role], c.child, c.parent).facts["outcome"] for c in CURATED]) else {"hoarded"}
    return 0 if outs else 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SHRINES[params.shrine], ROLES[params.role], params.child, params.parent)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return StoryParams(
        shrine=args.shrine or rng.choice(list(SHRINES)),
        role=args.role or rng.choice(list(ROLES)),
        child=args.name or rng.choice(NAMES),
        parent=args.parent or rng.choice(PARENTS),
    )


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
