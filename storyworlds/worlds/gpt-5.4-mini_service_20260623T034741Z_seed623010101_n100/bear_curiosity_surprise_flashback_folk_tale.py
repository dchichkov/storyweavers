#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/bear_curiosity_surprise_flashback_folk_tale.py
=======================================================================================================================

A standalone folk-tale storyworld about a curious bear, a surprising discovery,
and a flashback that changes what the bear chooses next.

The tiny domain is built around:
- a bear in a forest
- a curious walk to a special place
- an unexpected surprise
- a remembered flashback that explains the surprise
- a gentle ending that proves the bear changed what it does next

This script follows the Storyweavers contract:
- stdlib-only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily in ASP helpers
- defines StoryParams, build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and an inline ASP twin
- generates three QA sets grounded in world state
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
    role: str = ""
    location: str = ""
    owner: str = ""
    gives: str = ""
    hears: str = ""
    remembers: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"bear"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def noun(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    has: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Wonder:
    id: str
    label: str
    reveal: str
    surprise: str
    flashback: str
    at: str
    at_time: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gift:
    id: str
    label: str
    phrase: str
    use: str
    can_fit: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    apply: callable


def _r_surprise(world: World) -> list[str]:
    out = []
    bear = world.get("bear")
    wonder = world.facts["wonder"]
    if bear.memes["curiosity"] < THRESHOLD:
        return out
    sig = ("surprise", wonder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bear.memes["surprise"] += 1
    out.append("__surprise__")
    return out


def _r_flashback(world: World) -> list[str]:
    out = []
    bear = world.get("bear")
    wonder = world.facts["wonder"]
    if bear.memes["surprise"] < THRESHOLD:
        return out
    sig = ("flashback", wonder.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bear.memes["memory"] += 1
    out.append("__flashback__")
    return out


CAUSAL_RULES = [
    Rule("surprise", _r_surprise),
    Rule("flashback", _r_flashback),
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


def reasonableness(place: Place, wonder: Wonder, gift: Gift) -> bool:
    return wonder.at in place.has and wonder.surprise in {"surprise", "hidden"} and gift.use in {"safe keeping", "sharing", "remembering"}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for wid, wonder in WONDERS.items():
            for gid, gift in GIFTS.items():
                if reasonableness(place, wonder, gift):
                    combos.append((pid, wid, gid))
    return combos


def _tell(world: World, wonder: Wonder, gift: Gift) -> None:
    bear = world.get("bear")
    elder = world.get("elder")
    bear.memes["curiosity"] += 1
    world.say(
        f"In the green forest, there lived a bear named Brownie who loved to ask why the moss was soft and the wind was wise."
    )
    world.say(
        f"One morning Brownie walked to {world.place.label}, because {wonder.label} was said to rest there."
    )
    world.say(
        f"{bear.pronoun().capitalize()} found {wonder.reveal}, and {wonder.surprise} made {bear.noun()} stop in wonder."
    )
    world.para()
    bear.memes["surprise"] += 1
    world.say(
        f"At first Brownie only stared, but then a flashback came like a song from an old hearth."
    )
    world.say(
        f"Brownie remembered {wonder.flashback}, when {elder.noun()} had promised that {gift.phrase} would stay for the right time."
    )
    propagate(world, narrate=False)
    bear.memes["change"] += 1
    world.para()
    world.say(
        f"So Brownie did not snatch or spoil the {gift.label}. {bear.pronoun().capitalize()} left it where it belonged, and took a kinder path home."
    )
    world.say(
        f"By sunset, Brownie was carrying only a basket of berries, while the forest kept its secret and its peace."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale for a child about a bear named {f["bear_name"]} who follows curiosity into the forest, meets a surprise, and remembers an old lesson.',
        f"Tell a gentle story where {f['bear_name']} the bear sees {f['wonder'].label}, has a flashback, and chooses the respectful way home.",
        f'Write a folk-tale style story that includes the word "bear" and ends with {f["bear_name"]} doing the wiser thing after a surprising discovery.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    bear: Entity = f["bear"]
    wonder: Wonder = f["wonder"]
    gift: Gift = f["gift"]
    elder: Entity = f["elder"]
    return [
        QAItem(
            question=f"Why did {bear.id} go to {world.place.label}?",
            answer=f"{bear.id} went there because {bear.pronoun('subject').capitalize()} was curious about {wonder.label}. The bear wanted to see what was hidden in the forest and understand why everyone whispered about it.",
        ),
        QAItem(
            question=f"What made {bear.id} stop and stare?",
            answer=f"{wonder.reveal} made {bear.id} stop and stare. It was a surprise, and that surprise pushed the story into a quiet moment of wonder.",
        ),
        QAItem(
            question=f"What did {bear.id} remember after the surprise?",
            answer=f"{bear.id} remembered {wonder.flashback}. The memory explained why {elder.id} had told {bear.id} to leave {gift.label} for the right time.",
        ),
        QAItem(
            question=f"How did the story end for {bear.id} and the {gift.label}?",
            answer=f"{bear.id} left the {gift.label} alone and walked home gently. That ending shows the bear chose respect instead of taking what did not belong there.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["wonder"].tags) | set(world.facts["gift"].tags) | {"bear", "forest", "curiosity", "surprise", "flashback"}
    bank = {
        "bear": [("What is a bear?", "A bear is a large wild animal with fur and strong paws. Bears can be curious, but they should stay safe and respectful in the forest.")],
        "forest": [("What is a forest?", "A forest is a place with many trees, plants, and animals. It can feel quiet, green, and full of hidden things.")],
        "curiosity": [("What is curiosity?", "Curiosity is the wish to know more and explore. It helps a child or animal ask questions and look carefully.")],
        "surprise": [("What is a surprise?", "A surprise is something unexpected that makes you stop and pay attention. It can be exciting or startling.")],
        "flashback": [("What is a flashback?", "A flashback is a memory that comes back into your mind. It can explain why something matters now.")],
        "berries": [("What are berries?", "Berries are small juicy fruits that grow on plants. Many animals and people enjoy them.")],
        "honey": [("What is honey?", "Honey is a sweet food made by bees. It is sticky and golden.")],
        "trail": [("What is a trail?", "A trail is a path made by feet, hooves, or paws. It helps someone walk through woods or fields.")],
    }
    order = ["bear", "forest", "curiosity", "surprise", "flashback", "berries", "honey", "trail"]
    out: list[QAItem] = []
    for key in order:
        if key in tags:
            out.extend(QAItem(q, a) for q, a in bank[key])
    return out


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
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


@dataclass
class StoryParams:
    place: str = "forest"
    wonder: str = "hollow"
    gift: str = "honey"
    seed: Optional[int] = None


PLACES = {
    "forest": Place(id="forest", label="the old forest", has={"hollow", "clearing", "stream"}, tags={"forest"}),
    "grove": Place(id="grove", label="the moonlit grove", has={"hollow", "path"}, tags={"forest"}),
    "hill": Place(id="hill", label="the berry hill", has={"hollow", "berries"}, tags={"forest"}),
}

WONDERS = {
    "hollow": Wonder(id="hollow", label="a hollow oak tree", reveal="a hollow oak tree with a nest of shiny feathers", surprise="surprise", flashback="the day the birds asked for a quiet home", at="hollow", at_time="once",
                    tags={"surprise", "flashback", "forest"}),
    "stone": Wonder(id="stone", label="a round stone with carvings", reveal="a round stone marked with bright carvings", surprise="surprise", flashback="the day the elder showed how to read old signs", at="path", at_time="long ago",
                    tags={"surprise", "flashback", "trail"}),
    "honey": Wonder(id="honey", label="a little honey jar", reveal="a little honey jar tucked under roots", surprise="surprise", flashback="the day the bees and the bear shared the meadow", at="hollow", at_time="spring",
                    tags={"surprise", "flashback", "honey"}),
}

GIFTS = {
    "honey": Gift(id="honey", label="honey", phrase="a jar of honey", use="safe keeping", can_fit={"hollow"}, tags={"honey"}),
    "berries": Gift(id="berries", label="berries", phrase="a basket of berries", use="sharing", can_fit={"berries"}, tags={"berries"}),
    "song": Gift(id="song", label="song", phrase="a song from the elders", use="remembering", can_fit={"path"}, tags={"trail"}),
}


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


CURATED = [
    StoryParams(place="forest", wonder="hollow", gift="honey"),
    StoryParams(place="grove", wonder="stone", gift="song"),
    StoryParams(place="hill", wonder="honey", gift="berries"),
]


def explain_rejection(place: str, wonder: str, gift: str) -> str:
    p = PLACES[place]
    w = WONDERS[wonder]
    g = GIFTS[gift]
    return f"(No story: {w.label} does not fit the tale in {p.label}, or the gift {g.label} doesn't match the hidden lesson.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world sketch: a curious bear, a surprise, and a flashback in folk-tale style.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--wonder", choices=WONDERS)
    ap.add_argument("--gift", choices=GIFTS)
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
    combos = [c for c in valid_story_combos()
              if (args.place is None or c[0] == args.place)
              and (args.wonder is None or c[1] == args.wonder)
              and (args.gift is None or c[2] == args.gift)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, wonder, gift = rng.choice(sorted(combos))
    return StoryParams(place=place, wonder=wonder, gift=gift)


def tell(place: Place, wonder: Wonder, gift: Gift) -> World:
    world = World(place)
    bear = world.add(Entity(id="bear", kind="character", type="bear", label="Brownie"))
    elder = world.add(Entity(id="elder", kind="character", type="elder", label="the old keeper"))
    world.facts["bear_name"] = bear.id
    world.facts["bear"] = bear
    world.facts["elder"] = elder
    world.facts["wonder"] = wonder
    world.facts["gift"] = gift
    _tell(world, wonder, gift)
    return world


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.wonder not in WONDERS or params.gift not in GIFTS:
        raise StoryError("Invalid parameters.")
    world = tell(PLACES[params.place], WONDERS[params.wonder], GIFTS[params.gift])
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


ASP_RULES = r"""
valid(P,W,G) :- place(P), wonder(W), gift(G), has(P,H), at(W,H), use(G,U), ok_use(U).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for h in sorted(p.has):
            lines.append(asp.fact("has", pid, h))
    for wid, w in WONDERS.items():
        lines.append(asp.fact("wonder", wid))
        lines.append(asp.fact("at", wid, w.at))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("use", gid, g.use))
    lines.append(asp.fact("ok_use", "safe keeping"))
    lines.append(asp.fact("ok_use", "sharing"))
    lines.append(asp.fact("ok_use", "remembering"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python gates.")
        ok = False
    try:
        with redirect_stdout(io.StringIO()):
            sample = generate(CURATED[0])
            _ = sample.story
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        ok = False
    if ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    return 1


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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for t in asp_valid_combos():
            print(t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
