#!/usr/bin/env python3
"""
A small adventure storyworld about a prickly trail, a worried puller, blame,
sharing a fix, and a lesson learned.

The source tale behind this world:
---
A little explorer named Pip loved finding strange things in the woods. One day
Pip and a friend found a shiny berry bush with tiny prickles all over it. Pip
wanted the berries, but the bush tugged at Pip's sleeve and left a stinging
prickle in the cloth. The friend blamed the puller stick they had been using to
reach the berries, but then noticed the puller had simply snagged the bush.

With a hush of suspense, they stopped, shared the puller, and worked together.
One held the branch, one used the stick more gently, and the berries came free
without any more stings. In the end, Pip learned that blaming too fast can hide
the real cause, and sharing a careful plan can make adventure safer.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Site:
    place: str = "the woods"
    affords: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    type: str
    risk: str
    region: str
    story_word: str


@dataclass
class Tool:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, site: Site) -> None:
        self.site = site
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
        clone = World(self.site)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_prickle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("pull", 0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.kind != "thing":
                continue
            if item.meters.get("snagged", 0) < THRESHOLD:
                continue
            sig = ("prickle", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            actor.meters["prickle"] = actor.meters.get("prickle", 0) + 1
            out.append(f"{actor.id} felt a sharp prickle when the {item.label} snagged.")
    return out


def _r_blame(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("blame", 0) < THRESHOLD:
            continue
        sig = ("blame", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0) + 1
        out.append(f"{actor.id} blamed the wrong thing at first.")
    return out


RULES = [Rule("prickle", _r_prickle), Rule("blame", _r_blame)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risky(item: Thing) -> bool:
    return item.risk in {"prickle", "snag"}


def select_tool(item: Thing) -> Optional[Tool]:
    for tool in TOOLS:
        if item.risk in tool.guards and item.region in tool.covers:
            return tool
    return None


def predict(world: World, actor: Entity, item: Thing) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["pull"] = 1
    sim.get(item.id).meters["snagged"] = 1
    propagate(sim, narrate=False)
    return {
        "prickle": sim.get(actor.id).meters.get("prickle", 0) >= THRESHOLD,
        "blame": sum(e.memes.get("blame", 0) for e in sim.characters()) > 0,
    }


def tell(site: Site, thing_cfg: Thing, hero_name: str, hero_type: str, friend_name: str, friend_type: str) -> World:
    world = World(site)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["brave", "curious"]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["quick", "helpful"]))
    item = world.add(Entity(
        id=thing_cfg.id, kind="thing", type=thing_cfg.type, label=thing_cfg.label,
        phrase=thing_cfg.phrase, owner=hero.id, caretaker=friend.id
    ))
    tool = world.add(Entity(id="puller", kind="thing", type="tool", label="puller stick", phrase="a puller stick"))
    tool.meters["ready"] = 1

    world.say(f"{hero.id} was a little {hero.type} who loved adventure in {site.place}.")
    world.say(f"{hero.id} and {friend.id} found {item.phrase}, and the trail grew suspenseful.")
    world.para()

    world.say(f"They wanted the berries, but the {item.label} could {thing_cfg.story_word} if pulled too hard.")
    world.say(f"{friend.id} took the puller stick and tried to reach in carefully.")
    hero.meters["pull"] = 1
    item.meters["snagged"] = 1

    pred = predict(world, hero, thing_cfg)
    if pred["prickle"]:
        hero.memes["blame"] = 1
        world.say(f"{hero.id} gasped and blamed the puller stick for the prickle.")
        propagate(world, narrate=True)

    world.para()
    tool_def = select_tool(thing_cfg)
    if tool_def is None:
        raise StoryError("This adventure has no careful sharing tool for that prickly thing.")

    world.say(f"Then they paused, shared the puller stick, and listened to one another.")
    world.say(f"{friend.id} held the branch steady while {hero.id} used the puller more gently.")
    item.meters["snagged"] = 0
    hero.meters["pull"] = 0
    hero.memes["blame"] = 0
    hero.memes["lesson"] = 1
    world.say(f"They {tool_def.tail}. The berries came free, and no one got another prickle.")
    world.say(f"{hero.id} learned that sharing a careful plan works better than blaming fast.")
    world.facts.update(hero=hero, friend=friend, item=item, tool=tool_def, thing_cfg=thing_cfg, site=site)
    return world


SETTINGS = {
    "woods": Site(place="the woods", affords={"prickle"}),
    "trail": Site(place="the mountain trail", affords={"prickle"}),
    "garden": Site(place="the thorn garden", affords={"prickle"}),
}

THINGS = {
    "berrybush": Thing(
        id="berrybush", label="berry bush", phrase="a shiny berry bush with tiny prickles",
        type="bush", risk="prickle", region="hands", story_word="prickle"
    ),
    "vine": Thing(
        id="vine", label="vine", phrase="a long green vine with stubborn thorns",
        type="vine", risk="snag", region="hands", story_word="prickle"
    ),
    "bramble": Thing(
        id="bramble", label="bramble", phrase="a dark bramble patch that hooked on sleeves",
        type="bush", risk="prickle", region="arms", story_word="prickle"
    ),
}

TOOLS = [
    Tool(id="puller", label="puller stick", guards={"snag", "prickle"}, covers={"hands", "arms"}, prep="share the puller stick and work together", tail="shared the puller stick and took turns", plural=False),
]

HERO_NAMES = ["Pip", "Milo", "Nina", "Tara", "Bea", "Jules"]
FRIEND_NAMES = ["Ollie", "Sage", "Ruby", "Finn", "Nora", "Theo"]
TRAITS = ["brave", "curious", "lively", "fearless", "gentle"]


@dataclass
class StoryParams:
    place: str
    thing: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld: prickle, puller, blame, sharing, lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--hero-name")
    ap.add_argument("--friend-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
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
    place = args.place or rng.choice(list(SETTINGS))
    thing = args.thing or rng.choice(list(THINGS))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    friend_type = args.friend_type or ("girl" if hero_type == "boy" else "boy")
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    friend_name = args.friend_name or rng.choice(FRIEND_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, thing=thing, hero_name=hero_name, hero_type=hero_type, friend_name=friend_name, friend_type=friend_type, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, item = f["hero"], f["friend"], f["item"]
    return [
        f'Write an adventure story for a young child about {hero.id}, {friend.id}, and a {item.label}.',
        f'Write a suspenseful but gentle story where a puller stick causes a prickle, someone blames it, and then the friends share a better plan.',
        f'Write a story that ends with a lesson learned about blaming too fast and sharing tools carefully.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, item = f["hero"], f["friend"], f["item"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {friend.id}, who went on an adventure together in {world.site.place}."
        ),
        QAItem(
            question=f"What caused the prickle in the story?",
            answer=f"The {item.label} snagged when they pulled too hard, and that made the prickle happen."
        ),
        QAItem(
            question=f"Why did {hero.id} blame the puller at first?",
            answer=f"{hero.id} thought the puller stick caused the trouble because the moment felt sudden and suspenseful, but the real problem was that the {item.label} snagged."
        ),
        QAItem(
            question=f"How did the friends fix the problem?",
            answer=f"They shared the puller stick, held the branch steady, and used the tool more gently so they could work together."
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that blaming too fast can hide the real cause, and that sharing a careful plan helps everyone."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a prickle?",
            answer="A prickle is a sharp little poke or sting that can happen when something thorny brushes your skin or clothes."
        ),
        QAItem(
            question="What is a puller for?",
            answer="A puller is a simple tool used to reach, tug, or hook something carefully when your hands need a little extra help."
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting someone else use something, or helping together instead of keeping the task for one person alone."
        ),
        QAItem(
            question="Why is suspense exciting in a story?",
            answer="Suspense is exciting because it makes you wonder what will happen next and whether the characters will be safe."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("woods", "berrybush", "Pip", "boy", "Mina", "girl", "curious"),
    StoryParams("trail", "vine", "Nina", "girl", "Ollie", "boy", "brave"),
    StoryParams("garden", "bramble", "Bea", "girl", "Theo", "boy", "gentle"),
]


def explain_invalid() -> str:
    return "No story: this seed needs a prickly thing, a puller, and a shareable fix."


ASP_RULES = r"""
thing(T) :- item(T).
hero(H) :- actor(H).
friend(F) :- actor(F), not hero(F).

problem(H,T) :- pull(H), snag(T), actor(H).
blame(H) :- problem(H,T), not shared(T).
lesson_learned(H) :- shared(_), problem(H,_).

valid_story(Place, Thing, HeroType, FriendType) :- setting(Place), item(Thing), hero_kind(HeroType), friend_kind(FriendType).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for t in THINGS:
        lines.append(asp.fact("item", t))
    lines.append(asp.fact("hero_kind", "boy"))
    lines.append(asp.fact("hero_kind", "girl"))
    lines.append(asp.fact("friend_kind", "boy"))
    lines.append(asp.fact("friend_kind", "girl"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    python_set = sorted((p, t, h, f) for p in SETTINGS for t in THINGS for h in ["boy", "girl"] for f in ["boy", "girl"])
    if atoms == python_set:
        print(f"OK: clingo gate matches Python registry cross-product ({len(atoms)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], THINGS[params.thing], params.hero_name, params.hero_type, params.friend_name, params.friend_type)
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero_name}: {p.thing} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
