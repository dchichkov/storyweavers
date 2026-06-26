#!/usr/bin/env python3
"""
A mythic storyworld about a small misunderstanding, a golden relic, a phonograph,
and a reconciliation reached through dialogue.

The seed image is a short source tale:
- A young listener finds a phonograph in a shrine.
- A guardian thinks the machine's gold horn must be sacred.
- They argue, then speak carefully and realize the phonograph preserves a song
  from an ancestor.
- The guardian and listener repair their bond by sharing the record and the
  meaning of the song.

The story engine models:
- physical state: possession, location, and object condition
- emotional state: admiration, confusion, pride, hurt, and peace
- dialogue as the main tension
- reconciliation as the resolution
"""

from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    held_by: Optional[str] = None
    precious: bool = False
    fragile: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "guardian", "elder", "priest", "king"}
        female = {"girl", "woman", "mother", "priestess", "queen", "singer"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    sacred: bool = False
    quiet: bool = True


@dataclass
class Relic:
    label: str
    phrase: str
    kind: str
    precious: bool = True
    fragile: bool = False


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    guardian_name: str
    guardian_type: str
    relic: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        c.events = list(self.events)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_confusion(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.memes.get("confusion", 0.0) < THRESHOLD:
            continue
        sig = ("confusion", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["hurt"] = e.memes.get("hurt", 0.0) + 1.0
        out.append(f"{e.id} looked hurt because {e.pronoun('subject')} did not yet understand.")
    return out


def _r_reconcile(world: World) -> list[str]:
    hero = world.facts.get("hero")
    guardian = world.facts.get("guardian")
    if not hero or not guardian:
        return []
    h = world.get(hero.id)
    g = world.get(guardian.id)
    if h.memes.get("peace", 0.0) >= THRESHOLD and g.memes.get("peace", 0.0) >= THRESHOLD:
        sig = ("reconcile", h.id, g.id)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        return ["__reconcile__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_confusion, _r_reconcile):
            out = rule(world)
            if out:
                changed = True
                produced.extend([x for x in out if x != "__reconcile__"])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def shrine_detail(place: Place) -> str:
    if place.name == "the old shrine":
        return "The old shrine stood under carved stone and vines, quiet as a held breath."
    if place.name == "the river temple":
        return "The river temple shone with wet steps and pale candles."
    return f"{place.name.capitalize()} waited in a still, mythic silence."


def hero_intro(hero: Entity) -> str:
    return f"{hero.id} was a young {hero.type} with a brave heart and curious ears."


def guardian_intro(guardian: Entity) -> str:
    return f"{guardian.id} was an elder {guardian.type} who guarded old things with care."


def relic_intro(relic: Entity) -> str:
    return f"They had found {relic.phrase}, and its gold gleam made it seem like a piece of dawn."


def seek(world: World, hero: Entity, guardian: Entity, relic: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(
        f"{hero.id} wandered into the shrine and stopped before {relic.phrase}. "
        f"{hero.pronoun('subject').capitalize()} wanted to touch it and see what song it held."
    )


def warn(world: World, guardian: Entity, hero: Entity, relic: Entity) -> None:
    guardian.memes["pride"] = guardian.memes.get("pride", 0.0) + 1.0
    hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1.0
    world.say(
        f"{guardian.id} said, 'Do not turn the gold horn so fast.' "
        f"'It belongs to the shrine, and you must first comprehend why it was left here.'"
    )


def argue(world: World, hero: Entity, guardian: Entity, relic: Entity) -> None:
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1.0
    guardian.memes["hurt"] = guardian.memes.get("hurt", 0.0) + 1.0
    world.say(
        f"{hero.id} frowned and asked, 'Why keep a phonograph hidden if no one may hear it?'"
    )
    world.say(
        f"{guardian.id} answered, 'Because not every sound is a toy; some sounds are a vow.'"
    )


def reveal(world: World, hero: Entity, guardian: Entity, relic: Entity) -> None:
    hero.memes["confusion"] = max(0.0, hero.memes.get("confusion", 0.0) - 1.0)
    hero.memes["wonder"] = hero.memes.get("wonder", 0.0) + 1.0
    world.say(
        f"At last, {guardian.id} lifted the needle with careful hands and played the record. "
        f"A thin song rose from the phonograph, bright and trembling, and {hero.id} listened."
    )
    world.say(
        f"'{relic.label} is not just gold,' {guardian.id} said. 'It is a memory the village can hear.'"
    )


def reconcile(world: World, hero: Entity, guardian: Entity, relic: Entity) -> None:
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1.0
    guardian.memes["peace"] = guardian.memes.get("peace", 0.0) + 1.0
    hero.memes["hurt"] = 0.0
    guardian.memes["hurt"] = 0.0
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} bowed and said, 'Now I comprehend. The song keeps the old promise alive.'"
    )
    world.say(
        f"{guardian.id} smiled and answered, 'And you helped me hear it with new ears.'"
    )
    world.say(
        f"Together they set the phonograph beside the altar, and its gold horn shone softly while they stood in peace."
    )


def tell(place: Place, hero_name: str, hero_type: str, guardian_name: str, guardian_type: str, relic_cfg: Relic) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        location=place.name,
        meters={"feet": 1.0},
        memes={"curiosity": 0.0, "confusion": 0.0, "hurt": 0.0, "peace": 0.0},
    ))
    guardian = world.add(Entity(
        id=guardian_name,
        kind="character",
        type=guardian_type,
        location=place.name,
        meters={"feet": 1.0},
        memes={"pride": 0.0, "hurt": 0.0, "peace": 0.0},
    ))
    relic = world.add(Entity(
        id="phonograph",
        kind="thing",
        type="phonograph",
        label="the phonograph",
        phrase=relic_cfg.phrase,
        location=place.name,
        precious=relic_cfg.precious,
        fragile=relic_cfg.fragile,
        meters={"gold": 1.0},
    ))
    record = world.add(Entity(
        id="record",
        kind="thing",
        type="record",
        label="the record",
        phrase="the black record",
        location=place.name,
        fragile=True,
        meters={"groove": 1.0},
    ))

    world.facts.update(hero=hero, guardian=guardian, relic=relic, record=record)

    world.say(hero_intro(hero))
    world.say(guardian_intro(guardian))
    world.say(relic_intro(relic))
    world.para()
    world.say(shrine_detail(place))
    seek(world, hero, guardian, relic)
    warn(world, guardian, hero, relic)
    argue(world, hero, guardian, relic)
    world.para()
    reveal(world, hero, guardian, relic)
    reconcile(world, hero, guardian, relic)
    return world


PLACES = {
    "old_shrine": Place(name="the old shrine", sacred=True, quiet=True),
    "river_temple": Place(name="the river temple", sacred=True, quiet=True),
    "hill_sanctum": Place(name="the hill sanctum", sacred=True, quiet=True),
}

RELICS = {
    "gold_phonograph": Relic(
        label="the gold phonograph",
        phrase="a gold phonograph",
        kind="phonograph",
        precious=True,
        fragile=True,
    ),
}

HERO_TYPES = ["girl", "boy"]
GUARDIAN_TYPES = ["guardian", "elder"]

GIRL_NAMES = ["Mira", "Lena", "Suri", "Asha", "Nia", "Ira"]
BOY_NAMES = ["Arin", "Bren", "Cai", "Darin", "Eno", "Ravi"]
GUARDIAN_NAMES = ["Koru", "Seth", "Mara", "Tovin", "Ilya", "Anu"]


@dataclass
class WorldSummary:
    place: str
    hero_name: str
    guardian_name: str
    relic: str


def reasonableness_gate(params: StoryParams) -> None:
    if params.relic not in RELICS:
        raise StoryError("Unknown relic choice.")
    if params.place not in PLACES:
        raise StoryError("Unknown place choice.")
    if params.hero_type not in HERO_TYPES:
        raise StoryError("Unknown hero type.")
    if params.guardian_type not in GUARDIAN_TYPES:
        raise StoryError("Unknown guardian type.")


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.sacred:
            lines.append(asp.fact("sacred", pid))
        if place.quiet:
            lines.append(asp.fact("quiet", pid))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        if relic.precious:
            lines.append(asp.fact("precious", rid))
        if relic.fragile:
            lines.append(asp.fact("fragile", rid))
        lines.append(asp.fact("kind", rid, relic.kind))
    lines.append(asp.fact("word", "gold"))
    lines.append(asp.fact("word", "comprehend"))
    lines.append(asp.fact("word", "phonograph"))
    lines.append(asp.fact("feature", "dialogue"))
    lines.append(asp.fact("feature", "reconciliation"))
    return "\n".join(lines)


ASP_RULES = r"""
featured(gold) :- word(gold).
featured(comprehend) :- word(comprehend).
featured(phonograph) :- word(phonograph).

mythic_story(P) :- place(P), sacred(P), quiet(P).
focus(dialogue) :- feature(dialogue).
focus(reconciliation) :- feature(reconciliation).

usable(P, gold_phonograph) :- mythic_story(P), featured(gold), featured(phonograph).
resolution(gold_phonograph) :- usable(P, gold_phonograph), focus(reconciliation), focus(dialogue).
#show featured/1.
#show focus/1.
#show usable/2.
#show resolution/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_focus() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show featured/1.\n#show focus/1."))
    return sorted(set(asp.atoms(model, "featured")) | set(asp.atoms(model, "focus")))


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show usable/2.\n#show resolution/1."))
    usable = set(asp.atoms(model, "usable"))
    res = set(asp.atoms(model, "resolution"))
    python_ok = {"gold_phonograph"}
    if usable == {("the old shrine", "gold_phonograph")} or usable == {("the river temple", "gold_phonograph")} or usable == {("the hill sanctum", "gold_phonograph")}:
        pass
    if res == {("gold_phonograph",)}:
        print("OK: ASP twin recognizes the mythic gold phonograph and its reconciliation arc.")
        return 0
    print("MISMATCH in ASP verification.")
    print("usable:", sorted(usable))
    print("resolution:", sorted(res))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mythic storyworld: dialogue, gold, phonograph, and reconciliation."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--guardian-type", choices=GUARDIAN_TYPES)
    ap.add_argument("--hero-name")
    ap.add_argument("--guardian-name")
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
    place = args.place or rng.choice(list(PLACES))
    relic = args.relic or "gold_phonograph"
    hero_type = args.hero_type or rng.choice(HERO_TYPES)
    guardian_type = args.guardian_type or rng.choice(GUARDIAN_TYPES)
    hero_name = args.hero_name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    guardian_name = args.guardian_name or rng.choice(GUARDIAN_NAMES)
    params = StoryParams(
        place=place,
        hero_name=hero_name,
        hero_type=hero_type,
        guardian_name=guardian_name,
        guardian_type=guardian_type,
        relic=relic,
    )
    reasonableness_gate(params)
    return params


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a child that includes the words "gold", "comprehend", and "phonograph".',
        f"Tell a gentle dialogue-driven myth where {f['hero'].id} and {f['guardian'].id} disagree about {f['relic'].label} and then reconcile.",
        f"Write a story set in {world.place.name} in which a gold phonograph helps someone comprehend an old song.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    relic = f["relic"]
    return [
        QAItem(
            question=f"Who found the phonograph in the shrine?",
            answer=f"{hero.id} found {relic.phrase} in {world.place.name}."
        ),
        QAItem(
            question=f"Why did {guardian.id} seem upset at first?",
            answer=f"{guardian.id} was worried because the gold phonograph was precious, and {hero.id} did not yet comprehend why it should be handled carefully."
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {guardian.id}?",
            answer=f"They spoke honestly, understood each other, and reached reconciliation while listening to the phonograph together."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a phonograph?",
            answer="A phonograph is an early machine that plays recorded sound from a record."
        ),
        QAItem(
            question="What does gold often suggest in stories?",
            answer="Gold often suggests treasure, value, brightness, or something sacred and important."
        ),
        QAItem(
            question="What does it mean to comprehend something?",
            answer="To comprehend something means to understand it clearly."
        ),
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
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.location:
            bits.append(f"location={e.location}")
        if e.precious:
            bits.append("precious=True")
        if e.fragile:
            bits.append("fragile=True")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        PLACES[params.place],
        params.hero_name,
        params.hero_type,
        params.guardian_name,
        params.guardian_type,
        RELICS[params.relic],
    )
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


CURATED = [
    StoryParams(
        place="old_shrine",
        hero_name="Mira",
        hero_type="girl",
        guardian_name="Koru",
        guardian_type="guardian",
        relic="gold_phonograph",
    ),
    StoryParams(
        place="river_temple",
        hero_name="Arin",
        hero_type="boy",
        guardian_name="Mara",
        guardian_type="elder",
        relic="gold_phonograph",
    ),
    StoryParams(
        place="hill_sanctum",
        hero_name="Nia",
        hero_type="girl",
        guardian_name="Anu",
        guardian_type="guardian",
        relic="gold_phonograph",
    ),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show usable/2.\n#show resolution/1."))
    return sorted(set(asp.atoms(model, "usable")) | set(asp.atoms(model, "resolution")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show usable/2.\n#show resolution/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP focus facts:")
        for atom in asp_focus():
            print(atom)
        print("\nASP story facts:")
        for atom in asp_valid_stories():
            print(atom)
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
            header = f"### {p.hero_name}: {p.place} with {p.relic}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
