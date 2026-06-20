#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/influence_moral_value_reconciliation_surprise_tall_tale.py
===========================================================================================

A standalone storyworld for a tiny tall-tale domain about a boastful helper,
a surprising misunderstanding, a moral turn, and a reconciliation ending.

Premise:
- A kid in a big, windy place wants to impress others by using "influence" to
  steer a crowd, a bell, a rumor, or a friend.
- The story turns on a surprise: what they think is power is really only a
  small push, a loud voice, or a lucky coincidence.
- The moral value is simple and child-facing: truth and kindness matter more
  than bragging.
- Reconciliation closes the tale: a hurt friend is mended, a secret is shared,
  and the ending image proves the change.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose
- QA from world state, not from rendered English
- Python reasonableness gate plus inline ASP twin
- --verify smoke-tests generation and parity
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
SENSE_MIN = 2


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
class Place:
    id: str
    label: str
    wide: bool = False
    windy: bool = False
    crowdable: bool = True
    surprise_kind: str = ""

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
class InfluenceTool:
    id: str
    label: str
    force: int
    kind: str
    moral: bool
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
class Surprise:
    id: str
    label: str
    cause: str
    reveal: str
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


def _r_humility(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.memes["shame"] < THRESHOLD or e.memes["truth"] < THRESHOLD:
            continue
        sig = ("humility", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["humble"] += 1
        out.append("__humble__")
    return out


def _r_reconcile(world: World) -> list[str]:
    out: list[str] = []
    a = world.get("hero")
    b = world.get("friend")
    if a.memes["apology"] >= THRESHOLD and b.memes["forgiveness"] >= THRESHOLD:
        sig = ("reconcile",)
        if sig not in world.fired:
            world.fired.add(sig)
            a.memes["peace"] += 1
            b.memes["peace"] += 1
            out.append("__peace__")
    return out


CAUSAL_RULES = [Rule("humility", "social", _r_humility), Rule("reconcile", "social", _r_reconcile)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(x for x in s if not x.startswith("__"))
    if narrate:
        for t in produced:
            world.say(t)
    return produced


def reasonableness_gate(place: Place, tool: InfluenceTool, surprise: Surprise) -> bool:
    return place.crowdable and tool.force >= 1 and bool(surprise.cause)


def influence_turn(world: World, hero: Entity, friend: Entity, tool: InfluenceTool, place: Place) -> None:
    hero.memes["pride"] += 1
    world.say(
        f"At {place.label}, {hero.id} claimed {hero.pronoun('possessive')} "
        f"{tool.label} could influence anything that listened."
    )


def surprise_reveal(world: World, hero: Entity, friend: Entity, surprise: Surprise) -> None:
    hero.meters["stunned"] += 1
    friend.meters["stunned"] += 1
    hero.memes["shame"] += 1
    friend.memes["hurt"] += 1
    world.say(
        f"Then came the surprise: {surprise.reveal}, not the grand triumph "
        f"{hero.id} had boasted about."
    )


def moral_turn(world: World, hero: Entity, friend: Entity) -> None:
    hero.memes["truth"] += 1
    hero.memes["apology"] += 1
    friend.memes["forgiveness"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} looked at {friend.id} and said the honest thing at last: "
        f"the brag had been bigger than the truth."
    )


def reconcile(world: World, hero: Entity, friend: Entity) -> None:
    world.say(
        f"{friend.id} smiled back, and the two of them shook hands under the wide sky."
    )
    world.say(
        f"By evening they were laughing again, sharing the same hat and the same secret."
    )


def tell(place: Place, tool: InfluenceTool, surprise: Surprise,
         hero_name: str = "Milo", hero_type: str = "boy",
         friend_name: str = "June", friend_type: str = "girl") -> World:
    world = World()
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, role="boaster"))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, role="friend"))
    world.add(Entity(id="place", type="place", label=place.label))
    world.add(Entity(id="tool", type="tool", label=tool.label))
    world.add(Entity(id="surprise", type="surprise", label=surprise.label))

    world.say(
        f"{hero.id} and {friend.id} lived at the edge of a tall, windy town where every story "
        f"grew four feet taller before supper."
    )
    world.say(
        f"{hero.id} loved to brag about {hero.pronoun('possessive')} {tool.label}, the little thing "
        f"that could influence a crowd if the crowd was already half-minded to listen."
    )

    world.para()
    influence_turn(world, hero, friend, tool, place)
    world.say(
        f"{friend.id} frowned, because the words sounded grand but not quite kind."
    )

    world.para()
    surprise_reveal(world, hero, friend, surprise)
    moral_turn(world, hero, friend)

    world.para()
    reconcile(world, hero, friend)

    world.facts.update(
        hero=hero,
        friend=friend,
        place=place,
        tool=tool,
        surprise=surprise,
        moral_value=True,
        reconciliation=True,
        surprise_happened=True,
        ending="reconciled",
    )
    return world


PLACES = {
    "market": Place("market", "the market square", wide=True, windy=True, crowdable=True, surprise_kind="banner"),
    "dock": Place("dock", "the old dock", wide=True, windy=True, crowdable=True, surprise_kind="boat"),
    "hill": Place("hill", "the big hill", wide=True, windy=True, crowdable=True, surprise_kind="kite"),
}

TOOLS = {
    "whistle": InfluenceTool("whistle", "a whistle", force=2, kind="sound", moral=False, tags={"sound", "influence"}),
    "story": InfluenceTool("story", "a storybook speech", force=3, kind="words", moral=True, tags={"words", "influence"}),
    "banner": InfluenceTool("banner", "a bright banner", force=1, kind="signal", moral=False, tags={"signal", "influence"}),
}

SURPRISES = {
    "kite": Surprise("kite", "a kite", cause="the wind", reveal="a great kite had been following the wind all along", tags={"surprise", "kite"}),
    "goose": Surprise("goose", "a goose", cause="a hidden nest", reveal="a goose was tugging the banner loose from behind a crate", tags={"surprise", "bird"}),
    "bell": Surprise("bell", "a bell", cause="old ropes", reveal="the loud note had come from an old bell inside the market stall", tags={"surprise", "bell"}),
}

GIRL_NAMES = ["June", "Mina", "Ruby", "Clara", "Ivy", "Nora"]
BOY_NAMES = ["Milo", "Otis", "Bram", "Theo", "Evan", "Ezra"]
TRAITS = ["bold", "curious", "loud", "cheerful", "dreamy"]


@dataclass
@dataclass
class StoryParams:
    place: str
    tool: str
    surprise: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
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
    return [(p, t, s) for p in PLACES for t in TOOLS for s in SURPRISES if reasonableness_gate(PLACES[p], TOOLS[t], SURPRISES[s])]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld about influence, surprise, moral value, and reconciliation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--surprise", choices=SURPRISES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-type", choices=["boy", "girl"])
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
              if (args.place is None or c[0] == args.place)
              and (args.tool is None or c[1] == args.tool)
              and (args.surprise is None or c[2] == args.surprise)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, tool, surprise = rng.choice(sorted(combos))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    friend_type = args.friend_type or ("girl" if hero_type == "boy" else "boy")
    hero = args.hero or rng.choice(BOY_NAMES if hero_type == "boy" else GIRL_NAMES)
    friend = args.friend or rng.choice([n for n in (GIRL_NAMES if friend_type == "girl" else BOY_NAMES) if n != hero])
    return StoryParams(place, tool, surprise, hero, hero_type, friend, friend_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall tale for a child that includes the word "influence" and ends in reconciliation.',
        f"Tell a story about {f['hero'].id} trying to influence a crowd at {f['place'].label}, then being surprised and making things right.",
        f"Write a moral story where a boast becomes an honest apology, with a surprising reveal and a friendly ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, place, tool, surprise = f["hero"], f["friend"], f["place"], f["tool"], f["surprise"]
    return [
        QAItem(
            question="What did the hero try to do?",
            answer=f"{hero.id} tried to use {tool.label} to influence others at {place.label}. It sounded mighty, but it was mostly bragging.",
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was that {surprise.reveal}. That changed the story from boasting to honesty.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with {hero.id} telling the truth, apologizing, and making up with {friend.id}. They were reconciled and calm by the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does influence mean?",
            answer="Influence means having an effect on what someone thinks or does. In a story, it can be a strong voice, a good idea, or a gentle example.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good way to live, like telling the truth, being kind, or keeping a promise.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again. They may apologize, forgive, and start over kindly.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something you did not expect. It can change what the characters think is happening.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story Q&A ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge Q&A ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("market", "story", "goose", "Milo", "boy", "June", "girl"),
    StoryParams("dock", "whistle", "kite", "Nora", "girl", "Theo", "boy"),
    StoryParams("hill", "banner", "bell", "Ezra", "boy", "Ruby", "girl"),
]


def explain_rejection(place: Place, tool: InfluenceTool, surprise: Surprise) -> str:
    return "(No story: this combination does not make a strong enough tall-tale turn.)"


def outcome_of(params: StoryParams) -> str:
    return "reconciled"


ASP_RULES = r"""
valid(P,T,S) :- place(P), tool(T), surprise(S), crowdable(P), influence_tool(T), surprise_kind(S,_).
outcome(reconciled) :- valid(_,_,_).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        if PLACES[pid].crowdable:
            lines.append(asp.fact("crowdable", pid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("influence_tool", tid))
    for sid, s in SURPRISES.items():
        lines.append(asp.fact("surprise", sid))
        lines.append(asp.fact("surprise_kind", sid, s.cause))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid-combo gate.")
        print("only python:", sorted(py - cl))
        print("only clingo:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, tool=None, surprise=None, hero=None, hero_type=None, friend=None, friend_type=None), random.Random(7)))
        assert sample.story
        print("OK: smoke-tested generation.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TOOLS[params.tool], SURPRISES[params.surprise], params.hero, params.hero_type, params.friend, params.friend_type)
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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:\n")
        for p, t, s in asp_valid_combos():
            print(f"  {p:8} {t:8} {s}")
        return
    rng = random.Random(args.seed if args.seed is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random((args.seed or 0) + i))
            except StoryError as e:
                print(e)
                return
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
