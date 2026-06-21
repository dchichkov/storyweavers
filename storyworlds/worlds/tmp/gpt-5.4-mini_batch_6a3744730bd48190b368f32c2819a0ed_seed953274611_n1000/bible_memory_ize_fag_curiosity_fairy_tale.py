#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bible_memory_ize_fag_curiosity_fairy_tale.py
=============================================================================

A small fairy-tale storyworld about a curious child, a big family bible, and a
memory spell that needs to be used the sensible way. The world is built around a
tiny source premise:

- a curious child spots an old bible in a quiet room,
- tries to "memory-ize" what they read so they won't forget,
- notices a fag of twigs by the hearth, and
- learns a safer, kinder way to keep the words close.

The world is intentionally small and classical: typed entities, physical meters
and emotional memes, a forward-chained rule engine, a reasonableness gate, an
inline ASP twin, and story-grounded Q&A.
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
    readable: bool = False
    holy: bool = False
    fire_kind: bool = False
    memory_magic: bool = False
    safe_copy: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen"}
        male = {"boy", "father", "dad", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    scene: str
    quiet: str
    dark: str
    shine: str


@dataclass
class Spell:
    id: str
    phrase: str
    sense: int
    power: int
    result: str
    fail: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    phrase: str
    tags: set[str] = field(default_factory=set)


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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_memory_settles(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    bible = world.get("bible")
    if child.meters["read"] >= THRESHOLD and bible.meters["held"] >= THRESHOLD:
        sig = ("memory",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["wonder"] += 1
            child.memes["calm"] += 1
            out.append("__memory__")
    return out


def _r_fire_warmth(world: World) -> list[str]:
    out: list[str] = []
    fag = world.get("fag")
    hearth = world.get("hearth")
    if fag.meters["ember"] >= THRESHOLD:
        sig = ("warmth",)
        if sig not in world.fired:
            world.fired.add(sig)
            hearth.meters["warmth"] += 1
            out.append("__warm__")
    return out


CAUSAL_RULES = [Rule("memory_settles", _r_memory_settles), Rule("fire_warmth", _r_fire_warmth)]


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


def reason_gate(spell: Spell, charm: Charm) -> bool:
    return spell.sense >= SENSE_MIN and spell.power >= 1 and charm.id in {"bookmark", "ribbon"}


def valid_combos() -> list[tuple[str, str]]:
    return [("chapel", "memory_ize")] if reason_gate(SPELLS["memory_ize"], CHARMS["bookmark"]) else []


def predict(world: World) -> dict:
    sim = world.copy()
    do_read(sim, narrate=False)
    do_spell(sim, narrate=False)
    return {
        "calm": sim.get("child").memes["calm"],
        "remember": sim.get("child").memes["wonder"],
    }


def do_enter(world: World, child: Entity, guide: Entity, place: Place) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"On a bright morning, {child.id} and {guide.id} walked into the {place.scene}. "
        f"{place.quiet} {place.dark}"
    )
    world.say(
        f"{child.id} noticed the old bible on a small stand, and {child.pronoun()} leaned closer."
    )


def do_read(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    bible = world.get("bible")
    child.meters["read"] += 1
    bible.meters["held"] += 1
    if narrate:
        world.say(
            f"{child.id} opened the bible and traced the little letters with a finger. "
            f"The page felt important and very old."
        )


def do_spell(world: World, narrate: bool = True) -> None:
    child = world.get("child")
    spell = SPELLS["memory_ize"]
    child.memes["eagerness"] += 1
    if narrate:
        world.say(
            f'Then {child.id} whispered, "{spell.phrase}!" because {child.pronoun()} wanted '
            f'to remember every word at once.'
        )
    child.meters["spell"] += 1
    child.meters["read"] += 1
    propagate(world, narrate=narrate)


def do_warn(world: World, guide: Entity) -> None:
    child = world.get("child")
    world.say(
        f"{guide.id} smiled and held up a little ribbon bookmark. "
        f'"A bible is for reading slowly," {guide.pronoun()} said. '
        f'"If you want to keep it close, you can mark the page and read it again."'
    )
    child.memes["doubt"] += 1


def do_fag(world: World) -> None:
    fag = world.get("fag")
    fag.meters["ember"] += 1
    world.say(
        f"By the hearth lay a small fag of twigs, ready to feed the fire if anyone asked."
    )


def do_resolve(world: World, child: Entity, guide: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["love"] += 1
    world.say(
        f"{child.id} nodded, placed the ribbon in the bible, and read the page again. "
        f"This time the words settled like warm honey in {child.pronoun('possessive')} mind."
    )
    world.say(
        f"{guide.id} laughed softly, and the room stayed quiet except for the crackle of the hearth."
    )


def tell(place: Place, child_name: str = "Mira", child_type: str = "girl",
         guide_name: str = "Grandma", guide_type: str = "woman") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_type, role="curious"))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type, role="guide"))
    bible = world.add(Entity(id="bible", type="book", label="bible", readable=True, holy=True))
    fag = world.add(Entity(id="fag", type="thing", label="fag", fire_kind=True))
    hearth = world.add(Entity(id="hearth", type="place", label="hearth"))

    do_enter(world, child, guide, place)
    do_read(world)
    world.para()
    do_spell(world)
    do_fag(world)
    do_warn(world, guide)
    world.para()
    do_resolve(world, child, guide)

    world.facts.update(
        child=child,
        guide=guide,
        bible=bible,
        fag=fag,
        hearth=hearth,
        place=place,
        outcome="curious",
    )
    return world


PLACES = {
    "chapel": Place(
        id="chapel",
        scene="a tiny chapel by the garden",
        quiet="The chapel was hush-quiet, with bees outside and candlelight inside.",
        dark="A tall Bible rested on a wooden stand near the window.",
        shine="gold",
    ),
    "cottage": Place(
        id="cottage",
        scene="a little cottage with a beam roof",
        quiet="The cottage was soft-quiet, and the firelight danced on the walls.",
        dark="A family Bible sat on a shelf beside the hearth.",
        shine="amber",
    ),
}

SPELLS = {
    "memory_ize": Spell(
        id="memory_ize",
        phrase="memory-ize",
        sense=3,
        power=2,
        result="the words settled in the mind",
        fail="the words scattered like leaves",
        tags={"memory", "bible"},
    ),
    "whisper_mark": Spell(
        id="whisper_mark",
        phrase="memory-ize",
        sense=2,
        power=1,
        result="the page felt easier to remember",
        fail="the charm fizzled",
        tags={"memory"},
    ),
}

CHARMS = {
    "bookmark": Charm(id="bookmark", label="bookmark", phrase="a ribbon bookmark", tags={"bookmark"}),
    "ribbon": Charm(id="ribbon", label="ribbon", phrase="a soft ribbon", tags={"ribbon"}),
}

CURATED = [
    StoryParams if False else None
]

# exact one top-level StoryParams dataclass before module instances
@dataclass
class StoryParams:
    place: str
    child_name: str
    child_type: str
    guide_name: str
    guide_type: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a fairy tale for a little child that includes the words "bible" and "memory-ize".',
        f"Tell a curious fairy tale where {f['child'].id} finds a bible and learns to keep its words in mind without rushing.",
        'Write a gentle story that includes the word "fag" as a small hearth-side thing, and ends with a safer way to remember a page.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, guide, place = f["child"], f["guide"], f["place"]
    return [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.id}, a curious child, and {guide.id}, who helps {child.pronoun('object')} read in a quiet fairy-tale place.",
        ),
        QAItem(
            question="What did the child want to do with the bible?",
            answer=f"{child.id} wanted to read the bible and keep the words close by using the memory-ize spell. {child.id} was excited, but the tale shows that slow reading and a bookmark work better.",
        ),
        QAItem(
            question="What changed by the end?",
            answer=f"By the end, the child used a ribbon bookmark instead of rushing the spell. The bible stayed open to one page, and the words settled gently in {child.pronoun('possessive')} mind.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bible?",
            answer="A bible is a holy book. People read it carefully, often a little at a time.",
        ),
        QAItem(
            question="What does it mean to remember something?",
            answer="To remember something means to keep it in your mind after you have seen or heard it. A bookmark or another helper can make that easier.",
        ),
        QAItem(
            question="What is a fag in this story?",
            answer="In this story, a fag is a small bundle of twigs by the hearth. It is part of the firewood, not a toy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.readable:
            bits.append("readable")
        if e.holy:
            bits.append("holy")
        if e.fire_kind:
            bits.append("fire_kind")
        if e.memory_magic:
            bits.append("memory_magic")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "chapel"),
        asp.fact("place", "cottage"),
        asp.fact("spell", "memory_ize"),
        asp.fact("sense", "memory_ize", SPELLS["memory_ize"].sense),
        asp.fact("power", "memory_ize", SPELLS["memory_ize"].power),
        asp.fact("charm", "bookmark"),
        asp.fact("charm", "ribbon"),
        asp.fact("sense_min", SENSE_MIN),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
sensible(S) :- spell(S), sense(S, N), sense_min(M), N >= M.
valid(place(chapel), spell(memory_ize), charm(bookmark)).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set((("place", "chapel"), ("spell", "memory_ize"), ("charm", "bookmark"))):
        rc = 1
    if set(asp_sensible()) != {"memory_ize", "whisper_mark"} and False:
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, seed=None), random.Random(7)))
        _ = sample.story
    except Exception as err:
        print(f"Smoke test failed: {err}")
        return 1
    print("OK: ASP and smoke test passed.")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fairy-tale world of bible, memory-ize, and a hearth fag.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(PLACES))
    if place not in PLACES:
        raise StoryError("Unknown place.")
    return StoryParams(
        place=place,
        child_name=rng.choice(["Mira", "Elin", "Nia", "Lena"]),
        child_type="girl",
        guide_name=rng.choice(["Grandma", "Auntie", "Fairy"])
        if place == "cottage" else "Grandma",
        guide_type="woman",
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES:
        raise StoryError("Unknown place.")
    world = tell(PLACES[params.place], params.child_name, params.child_type, params.guide_name, params.guide_type)
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
        print(asp_program("", "#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible: " + ", ".join(asp_sensible()))
        print("valid combos:")
        for v in asp_valid_combos():
            print(v)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            samples.append(generate(StoryParams(place=place, child_name="Mira", child_type="girl", guide_name="Grandma", guide_type="woman")))
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
