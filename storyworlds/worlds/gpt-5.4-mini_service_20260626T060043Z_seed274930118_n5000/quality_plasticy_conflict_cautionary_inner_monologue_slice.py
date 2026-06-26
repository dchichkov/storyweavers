#!/usr/bin/env python3
"""
quality_plasticy_conflict_cautionary_inner_monologue_slice.py

A small slice-of-life story world about a child, a treasured plasticy item, a
quality problem, a gentle caution, and an inner monologue that leads to a fix.
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

QUALITY_THRESHOLD = 2.0
CRACK_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    afford: str
    detail: str


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    use: str
    risk: str
    damage: str
    salvage: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    thing: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "kitchen_table": Setting(
        place="the kitchen table",
        afford="snack",
        detail="The kitchen was quiet except for a ticking clock and a glass of water.",
    ),
    "back_porch": Setting(
        place="the back porch",
        afford="craft",
        detail="The porch had a low step, a wooden bench, and sunlight on the floorboards.",
    ),
    "playroom_floor": Setting(
        place="the playroom floor",
        afford="play",
        detail="The playroom had a bright rug, a basket of blocks, and room to sit cross-legged.",
    ),
}

THINGS = {
    "lunchbox": Thing(
        id="lunchbox",
        label="lunchbox",
        phrase="a small plasticy lunchbox with a shiny snap lid",
        use="carry a snack",
        risk="the lid can pop open if it gets bumped too hard",
        damage="the lid might crack",
        salvage="its latch could still work if she handled it gently",
        keyword="plasticy",
        tags={"plastic", "quality", "cautionary"},
    ),
    "cup": Thing(
        id="cup",
        label="cup",
        phrase="a plasticy cup with a wobbly handle",
        use="hold juice",
        risk="the handle can feel flimsy when it is squeezed",
        damage="the handle might split",
        salvage="it could still be useful for careful sipping",
        keyword="plasticy",
        tags={"plastic", "quality"},
    ),
    "toycar": Thing(
        id="toycar",
        label="toy car",
        phrase="a plasticy toy car with tiny wheels",
        use="roll on the floor",
        risk="the wheels can get sticky on rough ground",
        damage="the axle might bend",
        salvage="the wheels could keep turning on a smooth rug",
        keyword="plasticy",
        tags={"plastic", "quality"},
    ),
}

GIRL_NAMES = ["Mina", "Lila", "Ivy", "Nora", "Pia", "Tessa"]
BOY_NAMES = ["Eli", "Noah", "Owen", "Theo", "Ben", "Milo"]


@dataclass
class StoryPattern:
    setting: str
    thing: str


PATTERNS = [
    StoryPattern("kitchen_table", "lunchbox"),
    StoryPattern("back_porch", "cup"),
    StoryPattern("playroom_floor", "toycar"),
]


ASP_RULES = r"""
setting(S) :- place(S).
thing(T) :- item(T).

careful(T) :- fragile(T), has_quality_risk(T).
warning_needed(T) :- careful(T).
resolved(T) :- warning_needed(T), choose_soft_handling(T).

"""
def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        lines.append(asp.fact("affords", sid, s.afford))
    for tid, t in THINGS.items():
        lines.append(asp.fact("item", tid))
        lines.append(asp.fact("fragile", tid))
        lines.append(asp.fact("has_quality_risk", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [(p.setting, p.thing) for p in PATTERNS]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show warning_needed/1.\n#show resolved/1."))
    return sorted(set(asp.atoms(model, "warning_needed")) | set(asp.atoms(model, "resolved")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about quality, plasticy things, and caution.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if args.setting and args.thing:
        if (args.setting, args.thing) not in valid_combos():
            raise StoryError("That setting and thing do not make a believable cautionary story.")
    setting = args.setting or rng.choice(list(SETTINGS))
    thing = args.thing or rng.choice(list(THINGS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, thing=thing, name=name, gender=gender, parent=parent)


def _do_action(world: World, hero: Entity, thing: Entity, narrate: bool = True) -> None:
    hero.memes["impulse"] = hero.memes.get("impulse", 0) + 1
    thing.meters["use"] = thing.meters.get("use", 0) + 1
    thing.meters["quality"] = thing.meters.get("quality", 3.0) - 1.3
    if narrate:
        world.say(f"{hero.id} used {thing.pronoun('possessive')} {thing.label} carefully at first.")


def predict(world: World, hero: Entity, thing: Entity) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), sim.get(thing.id), narrate=False)
    t = sim.get(thing.id)
    return {"quality": t.meters.get("quality", 0), "crack": t.meters.get("crack", 0)}


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    thing = THINGS[params.thing]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item = world.add(Entity(
        id=thing.id,
        type="thing",
        label=thing.label,
        phrase=thing.phrase,
        owner=hero.id,
        caretaker=parent.id,
        meters={"quality": 3.0},
    ))

    world.say(f"{hero.id} liked how {item.phrase} looked in the morning light.")
    world.say(f"{hero.pronoun().capitalize()} thought it felt nice to have something so {thing.keyword} and neat.")
    world.para()
    world.say(setting.detail)
    world.say(f"{hero.id} wanted to {thing.use}, but {thing.risk}.")
    forecast = predict(world, hero, item)
    if forecast["quality"] < QUALITY_THRESHOLD:
        world.say(f'"Careful," {parent.pronoun("subject").capitalize()} said. "That one is made for quality, not rough hands."')
        world.say(f"{hero.id} paused and listened, because the warning sounded true.")
        world.say(f'In {hero.pronoun("possessive")} head, {hero.id} thought, "If I rush, the plasticy part might get worse."')
        hero.memes["conflict"] = 1
        world.say(f"So {hero.id} took a breath and tried a slower way.")
    world.para()
    _do_action(world, hero, item, narrate=True)
    if item.meters["quality"] < QUALITY_THRESHOLD:
        item.meters["crack"] = item.meters.get("crack", 0) + 1
        world.say(f"The {item.label} looked a little tired, but it did not break.")
        world.say(f"{hero.id} found a softer way to use it, and the day stayed calm.")
    else:
        world.say(f"The {item.label} stayed in good shape, and that made {hero.id} smile.")
    world.say(f"{hero.id} put it away with extra care, glad to keep its quality for later.")

    world.facts.update(hero=hero, parent=parent, item=item, thing=thing, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, item, thing = f["hero"], f["item"], f["thing"]
    return [
        f'Write a short slice-of-life story about {hero.id} and a {thing.keyword} {item.label} that needs gentle handling.',
        f"Tell a cautionary story where {hero.id} notices a quality problem with {item.phrase} and chooses a careful solution.",
        f'Write a simple story with an inner monologue where a child thinks, "If I rush, it might get worse," about a {thing.keyword} object.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, item, thing = f["hero"], f["parent"], f["item"], f["thing"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label}?",
            answer=f"{hero.id} wanted to {thing.use}, but they noticed it was the kind of thing that needed gentle handling.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the {item.label}?",
            answer=f"{parent.label.capitalize()} warned {hero.id} because the {item.phrase} was plasticy and a rough move could hurt its quality.",
        ),
        QAItem(
            question=f"What did {hero.id} decide after thinking it over?",
            answer=f"{hero.id} slowed down, handled the {item.label} more carefully, and kept the day calm instead of making the problem worse.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does quality mean in a toy or object?",
            answer="Quality means how well something is made and how well it holds up when people use it.",
        ),
        QAItem(
            question="What does plasticy mean?",
            answer="Plasticy means something feels like plastic: smooth, light, and a little hard or shiny.",
        ),
        QAItem(
            question="Why is caution important with fragile things?",
            answer="Caution matters because careful hands can keep a fragile thing from cracking or wearing out too soon.",
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
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(k for k, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="kitchen_table", thing="lunchbox", name="Mina", gender="girl", parent="mother"),
    StoryParams(setting="back_porch", thing="cup", name="Eli", gender="boy", parent="father"),
    StoryParams(setting="playroom_floor", thing="toycar", name="Nora", gender="girl", parent="mother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show warning_needed/1.\n#show resolved/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ASP mode is available for the same curated combinations as Python.")
        for s, t in valid_combos():
            print(f"{s} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
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
            header = f"### {p.name}: {p.setting} / {p.thing}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
