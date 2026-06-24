#!/usr/bin/env python3
"""
tippy_astronomic_lesson_learned_tall_tale.py
=============================================

A small tall-tale storyworld about Tippy, an astronomic lesson learned, and a
wobbly load that must be made steady before the sky-gazing can begin.

Seed premise:
---
Tippy loved astronomic things: star maps, moon charts, and the giant brass
telescope on the hill. One windy evening, Tippy tried to carry a tall stack of
sky-books and a glass lantern up the ladder to the observatory. The stack
wobbled like a sleepy giraffe. Tippy's aunt warned that the load would tip and
spill all over the steps. Tippy wanted to hurry anyway, but then learned that
the wise way was to split the load, use a tray, and climb one careful step at a
time.

World idea:
---
This is a tiny simulation of balance, wobble, and a lesson learned. The hero
has a physical load, a tippy route, and a choice between rushing and steadiness.
The story resolves when the hero changes method and the load becomes safe.

The prose leans tall-tale: larger-than-life objects, big skies, bold voices,
and a clear moral at the end.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "aunt", "woman"}
        male = {"boy", "father", "uncle", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    wind: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Load:
    id: str
    label: str
    phrase: str
    weight: float
    wobble: float
    risk: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy
        other = World(self.setting)
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        return other

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def abs_balance(world: World, actor: Entity) -> float:
    return actor.meters.get("balance", 0.0) - actor.meters.get("wobble", 0.0)


def is_tippy(world: World, actor: Entity, load: Load) -> bool:
    return load.weight + load.wobble > abs_balance(world, actor) + 0.5


def select_gear(load: Load) -> Optional[Gear]:
    for gear in GEAR:
        if load.id in gear.helps or any(tag in gear.helps for tag in load.tags):
            return gear
    return None


def load_at_risk(load: Load) -> bool:
    return load.id in {"books", "lantern", "chart", "globe"}


def predict_failure(world: World, actor: Entity, load: Load) -> bool:
    sim = world.copy()
    _do_attempt(sim, sim.get(actor.id), load, narrate=False)
    return any(e.meters.get("dropped", 0.0) >= THRESHOLD for e in sim.entities.values())


def _do_attempt(world: World, actor: Entity, load: Load, narrate: bool = True) -> None:
    actor.meters["wobble"] = actor.meters.get("wobble", 0.0) + load.wobble
    actor.meters["balance"] = actor.meters.get("balance", 0.0) - 0.25
    if is_tippy(world, actor, load):
        actor.meters["tippy"] = actor.meters.get("tippy", 0.0) + 1.0
    if narrate:
        pass


def cause_drop(world: World, actor: Entity, load: Load) -> bool:
    sig = ("drop", actor.id, load.id)
    if sig in world.fired:
        return False
    world.fired.add(sig)
    if is_tippy(world, actor, load) and actor.meters.get("steady", 0.0) < THRESHOLD:
        actor.meters["dropped"] = actor.meters.get("dropped", 0.0) + 1.0
        return True
    return False


SETTINGS = {
    "hill": Setting(place="the windy hill", wind="windy", afford={"astronomic"}),
    "yard": Setting(place="the old yard", wind="breezy", afford={"astronomic"}),
    "observatory": Setting(place="the little observatory", wind="windy", afford={"astronomic"}),
}

LOADS = {
    "books": Load(
        id="books",
        label="sky-books",
        phrase="a tall stack of sky-books",
        weight=2.0,
        wobble=1.5,
        risk="spilled",
        lesson="slow and steady beats fast and tippy",
        tags={"astronomic", "lesson"},
    ),
    "lantern": Load(
        id="lantern",
        label="glass lantern",
        phrase="a glass lantern full of moonlight",
        weight=1.5,
        wobble=2.0,
        risk="shattered",
        lesson="a bright light needs a steady hand",
        tags={"astronomic", "lesson"},
    ),
    "chart": Load(
        id="chart",
        label="star chart",
        phrase="a big star chart rolled into a curl",
        weight=1.0,
        wobble=1.0,
        risk="creased",
        lesson="a careful grip keeps the stars in order",
        tags={"astronomic", "lesson"},
    ),
}

GEAR = [
    Gear(
        id="tray",
        label="a wide tray",
        helps={"books", "chart"},
        prep="put the load on a wide tray",
        tail="carried it on a wide tray",
    ),
    Gear(
        id="strap",
        label="a shoulder strap",
        helps={"lantern"},
        prep="hang the lantern from a shoulder strap",
        tail="kept the lantern swinging gentle and true",
    ),
    Gear(
        id="helper",
        label="two careful hands",
        helps={"astronomic", "lesson"},
        prep="ask for two careful hands",
        tail="shared the job with two careful hands",
        plural=True,
    ),
]

NAMES = ["Tippy", "Mabel", "Jory", "Nell", "Pip"]
KIN = ["aunt", "uncle", "mother", "father"]


@dataclass
class StoryParams:
    place: str
    load: str
    name: str
    kin: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="hill", load="books", name="Tippy", kin="aunt"),
    StoryParams(place="observatory", load="lantern", name="Tippy", kin="uncle"),
    StoryParams(place="yard", load="chart", name="Tippy", kin="mother"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: Tippy's astronomic lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--name")
    ap.add_argument("--kin", choices=KIN)
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
    load = args.load or rng.choice(list(LOADS))
    name = args.name or rng.choice(NAMES)
    kin = args.kin or rng.choice(KIN)
    return StoryParams(place=place, load=load, name=name, kin=kin)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a tall-tale story about Tippy, an astronomic mistake, and a lesson learned.',
        f"Tell a child-friendly story where {f['name']} tries to carry {f['load_phrase']} to {f['place']} and learns a steadier way.",
        f"Write a short story with the word 'astronomic' and end with the lesson {f['lesson']!r}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {f['name']}, who is called Tippy in the tale and goes on an astronomic errand.",
        ),
        QAItem(
            question=f"What did Tippy try to carry?",
            answer=f"Tippy tried to carry {f['load_phrase']} up toward {f['place']}.",
        ),
        QAItem(
            question=f"What lesson did Tippy learn?",
            answer=f"Tippy learned that {f['lesson']}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does astronomic mean?",
            answer="Astronomic means having to do with the stars, planets, and other things in the sky.",
        ),
        QAItem(
            question="What does tippy mean?",
            answer="Tippy means wobbly or likely to tip over if it is not held steady.",
        ),
        QAItem(
            question="Why can a tall stack be hard to carry?",
            answer="A tall stack can be hard to carry because it can wobble, lean, and fall unless it is balanced well.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def tell(setting: Setting, load: Load, name: str, kin: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type="boy", label=name))
    helper = world.add(Entity(id="Kin", kind="character", type=kin, label=f"the {kin}"))
    item = world.add(Entity(id=load.id, type="thing", label=load.label, phrase=load.phrase, owner=hero.id, caretaker=helper.id))
    hero.meters["balance"] = 0.8
    hero.meters["steady"] = 0.0
    hero.memes["eager"] = 1.0

    world.say(f"{hero.id} was a little fellow with a giant heart for astronomic things and a grin as wide as the sky.")
    world.say(f"{hero.id} loved {load.phrase}, especially when the stars came out over {setting.place}.")
    world.say(f"One windy evening, {hero.id} picked up {item.phrase} and started for {setting.place}.")

    world.para()
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(f"But the load was tippy as a fence on a freight train. Every step made it sway and bob.")
    world.say(f"'{hero.id}, that looks astronomic and risky,' said {helper.label}, holding up a warning hand.")

    if predict_failure(world, hero, load):
        hero.memes["warning"] = 1.0
        world.say(f"{hero.id} wanted to hurry anyway, because the sky was calling and the hill looked mighty close.")
        world.say(f"But the stack wobbled worse when {hero.id} rushed.")
        if cause_drop(world, hero, load):
            world.say(f"Down it came with a clatter and a clink, as if the whole moon cart had sneezed.")
        world.say(f"That was the moment {hero.id} learned the lesson: {load.lesson}.")
    else:
        world.say(f"The load stayed steady enough to tempt a shortcut, but {helper.label} still asked for a safer plan.")
        world.say(f"{hero.id} listened, because even a tall tale needs a wise ending.")
        world.say(f"They chose a steadier route and the load rode like a little king.")

    world.para()
    gear = select_gear(load)
    if gear is not None:
        hero.meters["steady"] += 1.0
        world.say(f"Then {helper.label} helped {hero.id} {gear.prep}.")
        world.say(f"At last, {hero.id} {gear.tail}, and the astronomic load reached {setting.place} without a tumble.")
    else:
        world.say(f"Then {helper.label} helped {hero.id} with two careful hands, and the load made it through.")
    world.say(f"By the time the sky turned deep blue, {hero.id} was smiling at the stars and remembering how to be steady.")

    world.facts.update(
        name=hero.id,
        kin=helper.label,
        place=setting.place,
        load=load.id,
        load_phrase=load.phrase,
        lesson=load.lesson,
        setting=setting,
        load_cfg=load,
        resolved=True,
    )
    return world


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        lines.append(asp.fact("risk", lid, l.risk))
        for t in sorted(l.tags):
            lines.append(asp.fact("tag", lid, t))
    for gid, g in enumerate(GEAR):
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, h))
    return "\n".join(lines)


ASP_RULES = r"""
tippy(L) :- load(L), risk(L, _).
lesson(L) :- load(L), tag(L, lesson).
compatible(L, G) :- load(L), gear(G), helps(G, L).
compatible(L, G) :- load(L), gear(G), helps(G, astronomic).
valid(Place, Load) :- affords(Place, astronomic), load(Load), tippy(Load), compatible(Load, _).
#show valid/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    asp_set = sorted(set(asp.atoms(model, "valid")))
    py_set = sorted((place, lid) for place, s in SETTINGS.items() for lid, l in LOADS.items() if "astronomic" in s.afford and select_gear(l) is not None)
    if set(asp_set) == set(py_set):
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} combos).")
        return 0
    print("MISMATCH:")
    print("asp:", asp_set)
    print("py:", py_set)
    return 1


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], LOADS[params.load], params.name, params.kin)
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

    if args.verify:
        sys.exit(asp_verify())
    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        print(sorted(set(asp.atoms(model, "valid"))))
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
            rng = random.Random(seed)
            params = resolve_params(args, rng)
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
            header = f"### {p.name}: {p.load} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
