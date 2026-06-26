#!/usr/bin/env python3
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
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    owner: Optional[str] = None
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "character": {"subject": "they", "object": "them", "possessive": "their"},
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "crow": {"subject": "she", "object": "her", "possessive": "her"},
            "child": {"subject": "they", "object": "them", "possessive": "their"},
        }
        base = mapping.get(self.type, {"subject": "it", "object": "it", "possessive": "its"})
        return base[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Idea:
    id: str
    label: str
    verb: str
    object: str
    outcome: str
    mess: str
    emotion: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    used_for: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    covers: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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


@dataclass
class StoryParams:
    place: str
    idea: str
    prop: str
    name: str
    species: str
    seed: Optional[int] = None


SETTINGS = {
    "market": Setting(place="the market", affords={"peek", "test", "ask"}),
    "library": Setting(place="the library", affords={"peek", "test", "ask"}),
    "garden": Setting(place="the garden", affords={"peek", "test", "ask"}),
    "kitchen": Setting(place="the kitchen", affords={"peek", "test", "ask"}),
}

IDEAS = {
    "peek": Idea(
        id="peek",
        label="peek at the strange gadget",
        verb="peek at the strange gadget",
        object="the strange gadget",
        outcome="a little wobble",
        mess="sparkly",
        emotion="curiosity",
        keyword="peek",
        tags={"curiosity", "comedy", "stereotype"},
    ),
    "test": Idea(
        id="test",
        label="test the tiny machine",
        verb="test the tiny machine",
        object="the tiny machine",
        outcome="a silly beep",
        mess="noisy",
        emotion="curiosity",
        keyword="test",
        tags={"curiosity", "comedy", "expand"},
    ),
    "ask": Idea(
        id="ask",
        label="ask the odd question",
        verb="ask the odd question",
        object="the odd question",
        outcome="a surprising answer",
        mess="splashy",
        emotion="curiosity",
        keyword="ask",
        tags={"curiosity", "comedy", "stereotype", "expand"},
    ),
}

PROPS = {
    "hat": Prop(
        id="hat",
        label="hat",
        phrase="a polka-dot hat",
        type="hat",
        risk="top",
        used_for="head",
    ),
    "cup": Prop(
        id="cup",
        label="cup",
        phrase="a wobbly cup",
        type="cup",
        risk="hand",
        used_for="hands",
    ),
    "sign": Prop(
        id="sign",
        label="sign",
        phrase="a cardboard sign",
        type="sign",
        risk="eyes",
        used_for="reading",
        plural=False,
    ),
}

TOOLS = [
    Tool(
        id="notebook",
        label="notebook",
        phrase="a little notebook",
        helps={"ask", "peek"},
        covers={"eyes"},
    ),
    Tool(
        id="stool",
        label="stool",
        phrase="a sturdy stool",
        helps={"peek", "test"},
        covers={"feet"},
    ),
    Tool(
        id="gloves",
        label="gloves",
        phrase="tiny gloves",
        helps={"test"},
        covers={"hands"},
        plural=True,
    ),
]

NAMES = ["Milo", "Nia", "Pip", "Tess", "Luna", "Otto", "Cleo", "Bram"]
SPECIES = ["fox", "rabbit", "crow", "child"]
TRAITS = ["curious", "bright-eyed", "comic", "bold"]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("curiosity", 0.0) < THRESHOLD:
            continue
        if ent.meters.get("sparkly", 0.0) < THRESHOLD and ent.meters.get("noisy", 0.0) < THRESHOLD and ent.meters.get("splashy", 0.0) < THRESHOLD:
            continue
        sig = ("laugh", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["amusement"] = ent.memes.get("amusement", 0.0) + 1.0
        out.append(f"{ent.id} laughed at the result.")
    return out


def _r_expand(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    if not hero:
        return out
    if hero.memes.get("curiosity", 0.0) < THRESHOLD:
        return out
    if hero.memes.get("stereotype", 0.0) < THRESHOLD:
        return out
    sig = ("expand", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["understanding"] = hero.memes.get("understanding", 0.0) + 1.0
    hero.memes["stereotype"] = 0.0
    out.append("The old idea grew bigger and less silly.")
    return out


CAUSAL_RULES = [Rule("mess", _r_mess), Rule("expand", _r_expand)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def can_really_help(idea: Idea, prop: Prop) -> bool:
    return idea.keyword == "ask" or prop.risk in {"top", "hand", "eyes"}


def choose_tool(idea: Idea, prop: Prop) -> Optional[Tool]:
    for tool in TOOLS:
        if idea.id in tool.helps:
            return tool
    return None


def tell(place: Setting, idea: Idea, prop: Prop, name: str, species: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=species,
        label=name,
        traits=["curious", "comic"],
        membranes := {},
    ))
    parent = world.add(Entity(id="friend", kind="character", type="child", label="a friend"))
    thing = world.add(Entity(id="prop", type=prop.type, label=prop.label, phrase=prop.phrase))
    world.facts.update(hero=hero, friend=parent, prop=thing, idea=idea, setting=place)

    world.say(f"{hero.label} was a {hero.pronoun('subject')} with a {', '.join(hero.traits)} grin.")
    world.say(
        f"{hero.label} loved to {idea.verb}, because every odd little thing felt like a joke waiting to happen."
    )
    world.say(
        f"One day at {place.place}, {hero.label} noticed {thing.phrase} and decided to have a look."
    )
    world.para()
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    hero.memes["stereotype"] = hero.memes.get("stereotype", 0.0) + 1.0
    world.say(
        f"Somebody said, '{hero.label} always does the same kind of thing,' and that made {hero.label} wrinkle {hero.pronoun('possessive')} nose."
    )
    world.say(
        f"{hero.label} wanted to prove the day could {idea.outcome}, not just fit a tidy label."
    )
    if can_really_help(idea, prop):
        world.say(
            f"So {hero.label} tried to {idea.verb} with {thing.phrase}, and of course the first attempt made a {idea.outcome}."
        )
    tool = choose_tool(idea, prop)
    if tool:
        world.say(
            f"Then {hero.label} borrowed {tool.phrase} and used it like a tiny stage prop."
        )
    world.para()
    if idea.id == "peek":
        hero.meters["sparkly"] = hero.meters.get("sparkly", 0.0) + 1.0
        world.say(
            f"When {hero.label} peeked, a sparkly speck popped up on {hero.pronoun('possessive')} nose."
        )
    elif idea.id == "test":
        hero.meters["noisy"] = hero.meters.get("noisy", 0.0) + 1.0
        world.say(
            f"When {hero.label} tested it, the little machine gave a beep so cheerful it sounded like it had laughed first."
        )
    else:
        hero.meters["splashy"] = hero.meters.get("splashy", 0.0) + 1.0
        world.say(
            f"When {hero.label} asked the question, the answer bounced back with such a splash that even the spoon looked impressed."
        )
    propagate(world)
    world.para()
    if hero.memes.get("understanding", 0.0) >= THRESHOLD:
        world.say(
            f"In the end, {hero.label} had not become boring at all; {hero.pronoun('subject')} had only turned one small stereotype into a wider, funnier story."
        )
    else:
        world.say(
            f"In the end, {hero.label} laughed so hard that the label did not stick."
        )
    return world


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, idea in IDEAS.items():
        lines.append(asp.fact("idea", iid))
        for t in sorted(idea.tags):
            lines.append(asp.fact("tag", iid, t))
    for pid, prop in PROPS.items():
        lines.append(asp.fact("prop", pid))
        lines.append(asp.fact("risk", pid, prop.risk))
    for tid, tool in [(t.id, t) for t in TOOLS]:
        lines.append(asp.fact("tool", tid))
        for a in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, a))
    return "\n".join(lines)


ASP_RULES = r"""
shown_comedy(P, I, Pr) :- affords(P, I), idea(I), prop(Pr), risk(Pr, R), compatible(I, R).
compatible(I, R) :- helps(T, I), tool(T), cover(T, R).
expands_stereotype(I) :- tag(I, stereotype), tag(I, expand).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shown_comedy/3."))
    return sorted(set(asp.atoms(model, "shown_comedy")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for idea_id in setting.affords:
            idea = IDEAS[idea_id]
            for prop_id, prop in PROPS.items():
                if can_really_help(idea, prop):
                    combos.append((place, idea_id, prop_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    idea = f["idea"]
    prop = f["prop"]
    return [
        f'Write a short comedy story for a child named {hero.label} who wants to {idea.verb} at {world.setting.place}.',
        f'Write a funny story where a curious {hero.type} meets {prop.phrase} and turns a stereotype into something wider.',
        f'Create a gentle story about curiosity, a silly label, and a laugh-out-loud little discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    idea = f["idea"]
    prop = f["prop"]
    return [
        QAItem(
            question=f"What did {hero.label} want to do at {world.setting.place}?",
            answer=f"{hero.label} wanted to {idea.verb}.",
        ),
        QAItem(
            question=f"What object made the day feel extra silly for {hero.label}?",
            answer=f"{prop.phrase} made the day feel extra silly.",
        ),
        QAItem(
            question=f"What changed when the old label was challenged?",
            answer="The stereotype grew into a wider, funnier understanding instead of staying small.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, ask, and learn more about something new.",
        ),
        QAItem(
            question="Why can comedy make a story fun?",
            answer="Comedy makes stories fun because silly timing, odd surprises, and playful mistakes can make people laugh.",
        ),
        QAItem(
            question="What does it mean to expand an idea?",
            answer="To expand an idea means to make it bigger, broader, or more complete than it was before.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {e.label} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="market", idea="peek", prop="hat", name="Milo", species="fox"),
    StoryParams(place="library", idea="ask", prop="sign", name="Nia", species="crow"),
    StoryParams(place="garden", idea="test", prop="cup", name="Pip", species="rabbit"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy world about curiosity, stereotypes, and a small expansion of perspective.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--idea", choices=IDEAS)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--name")
    ap.add_argument("--species", choices=SPECIES)
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
              and (args.idea is None or c[1] == args.idea)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, idea, prop = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    species = args.species or rng.choice(SPECIES)
    return StoryParams(place=place, idea=idea, prop=prop, name=name, species=species)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], IDEAS[params.idea], PROPS[params.prop], params.name, params.species)
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
        print(asp_program("#show shown_comedy/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for item in triples:
            print(item)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
