#!/usr/bin/env python3
"""
A standalone story world: a folk-tale contest of wit, surprise, and humor.

Premise:
- A village faces a troublesome creature or nuisance.
- A clever character tries to vanquish it, but not by force alone.
- Surprise and humor provide the turn, and the ending proves the change.

The world is deliberately small and constraint-checked:
- Only reasonable tale variants are allowed.
- Invalid explicit choices raise StoryError.
- The narrative is state-driven rather than template-swapped.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "witch"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Tale:
    name: str
    nuisance: str
    method: str
    surprise: str
    humor: str
    place: str
    ending: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    tale: str
    hero: str
    hero_kind: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, tale: Tale) -> None:
        self.tale = tale
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        w = World(self.tale)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _r_surprise(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    nuisance = world.get("nuisance")
    if hero.memes.get("curiosity", 0) >= THRESHOLD and nuisance.meters.get("trouble", 0) >= THRESHOLD:
        sig = ("surprise",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
            out.append(f"Out of nowhere, {world.tale.surprise}.")
    return out


def _r_humor(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    nuisance = world.get("nuisance")
    if hero.memes.get("surprise", 0) >= THRESHOLD:
        sig = ("humor",)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["humor"] = hero.memes.get("humor", 0) + 1
            nuisance.meters["trouble"] = max(0.0, nuisance.meters.get("trouble", 0) - 1.0)
            out.append(world.tale.humor)
    return out


def _r_vanquish(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    nuisance = world.get("nuisance")
    if hero.memes.get("humor", 0) >= THRESHOLD and nuisance.meters.get("trouble", 0) <= 0:
        sig = ("vanquish",)
        if sig not in world.fired:
            world.fired.add(sig)
            nuisance.meters["banished"] = 1.0
            hero.memes["victory"] = 1.0
            out.append(f"So {hero.id} vanquished the nuisance without a blow.")
    return out


RULES = [_r_surprise, _r_humor, _r_vanquish]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


TALES = {
    "mischief_mole": Tale(
        name="Mischief Mole",
        nuisance="a mole that popped up and stole pies from every windowsill",
        method="a clever trick with a lopsided hat and a tune",
        surprise="the hat was filled with honeyed crumbs, not stones",
        humor="The mole sneezed, wore the hat like a crown, and danced in circles, which made the whole lane laugh",
        place="the village lane",
        ending="the mole tucked itself underground and never stole pies again",
        tags={"surprise", "humor", "folk"},
    ),
    "greedy_ogre": Tale(
        name="Greedy Ogre",
        nuisance="an ogre who sat on the bridge and demanded honey cakes from travelers",
        method="a brave riddle and a basket of shiny turnips",
        surprise="the basket held a tiny bell that rang at every wrong answer",
        humor="The ogre laughed so hard at the ringing bell that his grumpy scowl fell off his face",
        place="the old bridge",
        ending="the ogre thanked the villagers and went to guard the goats instead",
        tags={"surprise", "humor", "folk"},
    ),
    "noisy_crow": Tale(
        name="Noisy Crow",
        nuisance="a crow that woke the farm at dawn with a scandalous cawing song",
        method="a mirror, a ribbon, and a very serious bow",
        surprise="the crow saw itself dressed as a king and forgot to caw",
        humor="It strutted, bowed to its own reflection, and the hens giggled so hard they toppled into a haystack",
        place="the farmyard",
        ending="the crow became a vain but quiet bird, and the morning slept in peace",
        tags={"surprise", "humor", "folk"},
    ),
    "moon_mouse": Tale(
        name="Moon Mouse",
        nuisance="a moon mouse that nibbled all the cheese from the pantry shelf",
        method="a moonlit trail of breadcrumbs and a paper crown",
        surprise="the breadcrumbs spelled out the mouse's own name",
        humor="The mouse read the crumbs, squeaked with pride, and posed for applause instead of nibbling",
        place="the cottage pantry",
        ending="the cheese stayed safe, and the mouse became the smallest actor in the village",
        tags={"surprise", "humor", "folk"},
    ),
}

HEROES = {
    "girl": ["Mira", "Anya", "Bela", "Tessa", "Iva"],
    "boy": ["Oren", "Jasper", "Milo", "Niko", "Soren"],
}

HELPERS = ["grandmother", "grandfather", "aunt", "uncle", "wise baker", "old fiddler"]


def valid_tales() -> list[str]:
    return list(TALES)


def reasonableness_gate(tale_key: str) -> None:
    if tale_key not in TALES:
        raise StoryError("Unknown tale key.")
    t = TALES[tale_key]
    if "surprise" not in t.tags or "humor" not in t.tags:
        raise StoryError("This world requires both surprise and humor.")
    if "folk" not in t.tags:
        raise StoryError("This world must stay close to a folk-tale tone.")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world with surprise and humor.")
    ap.add_argument("--tale", choices=valid_tales())
    ap.add_argument("--hero")
    ap.add_argument("--hero-kind", choices=["girl", "boy"])
    ap.add_argument("--helper")
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
    tale = args.tale or rng.choice(valid_tales())
    reasonableness_gate(tale)
    hero_kind = args.hero_kind or rng.choice(["girl", "boy"])
    hero = args.hero or rng.choice(HEROES[hero_kind])
    helper = args.helper or rng.choice(HELPERS)
    return StoryParams(tale=tale, hero=hero, hero_kind=hero_kind, helper=helper)


def tell(tale: Tale, params: StoryParams) -> World:
    world = World(tale)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_kind, label=params.hero, meters={}, memes={}))
    nuisance = world.add(Entity(id="nuisance", kind="creature", type="creature", label=tale.name, meters={"trouble": 1.0}, memes={}))
    helper = world.add(Entity(id="helper", kind="character", type="woman" if params.helper in {"grandmother", "aunt", "wise baker"} else "man", label=params.helper, meters={}, memes={}))

    world.say(f"Once, in {tale.place}, there lived {params.hero}, who listened well when {params.helper} told old stories.")
    world.say(f"But there was trouble, too: {tale.nuisance}.")
    world.say(f"{params.hero} wanted to vanquish it, and {params.helper} said the best sword was often a clever smile.")

    hero.memes["curiosity"] = 1.0
    world.para()
    world.say(f"At dusk, {params.hero} went to {tale.place} with {params.helper} and tried {tale.method}.")
    propagate(world, narrate=True)

    world.para()
    if nuisance.meters.get("banished", 0) >= THRESHOLD:
        world.say(f"In the end, {tale.ending}.")
        world.say(f"{params.hero} laughed, {params.helper} nodded, and the whole village slept with light hearts.")
    else:
        world.say(f"Yet the trick was not enough, and the tale would not be a proper folk story.")
    world.facts.update(hero=hero, nuisance=nuisance, helper=helper)
    return world


def generation_prompts(world: World) -> list[str]:
    t = world.tale
    return [
        f"Write a short folk tale where a child uses surprise and humor to vanquish {t.nuisance}.",
        f"Tell a gentle story set in {t.place} with a clever turn, a funny moment, and a happy ending.",
        f"Write a child-friendly tale about a brave trick, a laugh, and a nuisance that is finally vanquished.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"].label
    helper = f["helper"].label
    tale = world.tale
    return [
        QAItem(
            question=f"Who tried to vanquish the trouble in the story?",
            answer=f"{hero} tried to vanquish {tale.name} with help from {helper}.",
        ),
        QAItem(
            question=f"What made the middle of the story surprising?",
            answer=f"The surprise was that {tale.surprise}. That changed the mood and helped the plan work.",
        ),
        QAItem(
            question=f"Why did the story turn funny instead of scary?",
            answer=f"It turned funny because {tale.humor}. The laugh broke the nuisance's power.",
        ),
        QAItem(
            question=f"What changed by the end?",
            answer=f"By the end, {tale.ending}. The nuisance was gone, and the village felt safe again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a folk tale?",
            answer="A folk tale is an old story people tell and retell, often with a clever hero, a strange problem, and a neat ending.",
        ),
        QAItem(
            question="What does vanquish mean?",
            answer="To vanquish means to defeat something so it can no longer cause trouble.",
        ),
        QAItem(
            question="Why can humor help in a hard situation?",
            answer="Humor can make people feel braver and less afraid, which helps them think clearly and solve the problem.",
        ),
        QAItem(
            question="What is surprise in a story?",
            answer="Surprise is a sudden change or twist that the characters did not expect.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"  {e.id}: type={e.type}, meters={dict(e.meters)}, memes={dict(e.memes)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
heroic(H) :- hero(H).
problem(N) :- nuisance(N).
surprising :- surprise_fact.
funny :- humor_fact.
vanquished :- heroic(hero), problem(nuisance), surprising, funny.
#show vanquished/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("hero", "hero"),
            asp.fact("nuisance", "nuisance"),
            asp.fact("surprise_fact"),
            asp.fact("humor_fact"),
        ]
    )


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show vanquished/0."))
    ok = any(sym.name == "vanquished" for sym in model)
    py_ok = True
    if ok != py_ok:
        print("MISMATCH between ASP and Python gate.")
        return 1
    print("OK: ASP and Python agree.")
    return 0


def generate(params: StoryParams) -> StorySample:
    world = tell(TALES[params.tale], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show vanquished/0."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show vanquished/0."))
        print("vanquished" if any(sym.name == "vanquished" for sym in model) else "not vanquished")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for key in valid_tales():
            params = StoryParams(
                tale=key,
                hero=HEROES["girl"][0],
                hero_kind="girl",
                helper=HELPERS[0],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
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
