#!/usr/bin/env python3
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
    kind: str = "character"
    animal: str = "animal"
    label: str = ""
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.animal in {"cat", "kitten", "fox", "rabbit", "mouse"}:
            table = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.animal in {"dog", "puppy", "bear", "goat", "frog"}:
            table = {"subject": "he", "object": "him", "possessive": "his"}
        else:
            table = {"subject": "they", "object": "them", "possessive": "their"}
        return table[case]

    def noun(self) -> str:
        return self.label or self.animal


@dataclass
class Place:
    name: str
    indoor: bool = False
    afford: set[str] = field(default_factory=set)


@dataclass
class Thing:
    id: str
    label: str
    phrase: str
    type: str
    fragile: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)


@dataclass
class Plan:
    id: str
    label: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = "input"
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    plan: str
    prize: str
    hero: str
    hero_kind: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.things: dict[str, Thing] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_thing(self, t: Thing) -> Thing:
        self.things[t.id] = t
        return t

    def get_entity(self, eid: str) -> Entity:
        return self.entities[eid]

    def get_thing(self, tid: str) -> Thing:
        return self.things[tid]

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.things = copy.deepcopy(self.things)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters.get("mess", 0.0) < THRESHOLD:
            continue
        for thing in world.things.values():
            if thing.used_by != ent.id or not thing.fragile:
                continue
            sig = ("spill", ent.id, thing.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            thing.meters["mess"] = thing.meters.get("mess", 0.0) + 1
            thing.meters["dirty"] = thing.meters.get("dirty", 0.0) + 1
            out.append(f"{thing.label} got messy.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for thing in world.things.values():
        if thing.meters.get("dirty", 0.0) < THRESHOLD or not thing.caretaker:
            continue
        sig = ("worry", thing.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get_entity(thing.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for ent in world.entities.values():
        if ent.memes.get("stubborn", 0.0) < THRESHOLD or ent.memes.get("held_back", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["conflict"] = ent.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_r_spill, _r_worry, _r_conflict):
            sents = rule(world)
            if sents:
                changed = True
                out.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World, hero: Entity, plan: Plan, prize_id: str) -> dict:
    sim = world.copy()
    do_plan(sim, sim.get_entity(hero.id), plan, narrate=False)
    prize = sim.get_thing(prize_id)
    return {
        "dirty": prize.meters.get("dirty", 0.0) >= THRESHOLD,
        "worry": sim.get_entity(sim.get_thing(prize_id).caretaker).memes.get("worry", 0.0) if prize.caretaker else 0.0,
    }


def do_plan(world: World, hero: Entity, plan: Plan, narrate: bool = True) -> None:
    if plan.id not in world.place.afford:
        return
    hero.meters["mess"] = hero.meters.get("mess", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.noun()} who loved busy days and neat little jobs.")


def love_plan(world: World, hero: Entity, plan: Plan) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {plan.gerund}, because it made the barn feel alive.")


def prize_line(world: World, hero: Entity, prize: Thing) -> None:
    world.say(f"{hero.id} also loved {hero.pronoun('possessive')} {prize.label} and used it every day.")


def arrive(world: World, hero: Entity) -> None:
    if world.place.indoor:
        world.say(f"One day, {hero.id} padded into {world.place.name}, where the floor shone softly.")
    else:
        world.say(f"One day, {hero.id} went to {world.place.name}, where the air felt bright and open.")


def wants(world: World, hero: Entity, plan: Plan) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {plan.verb} right away, but {hero.pronoun('possessive')} paws hovered near the big red input lever.")


def warn(world: World, helper: Entity, hero: Entity, plan: Plan, prize: Thing) -> bool:
    pred = predict(world, hero, plan, prize.id)
    if not pred["dirty"]:
        return False
    world.facts["predicted_dirty"] = True
    world.say(f'"You\'ll get your {prize.label} {plan.soil}," {helper.label} said. "Let\'s choose carefully."')
    return True


def defy(world: World, hero: Entity, plan: Plan) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"{hero.id} still wanted to try. {hero.pronoun().capitalize()} dashed toward the input lever.")


def hold_back(world: World, helper: Entity, hero: Entity, plan: Plan) -> None:
    hero.memes["held_back"] = hero.memes.get("held_back", 0.0) + 1
    propagate(world, narrate=False)
    world.say(f"Then {helper.id} held up a gentle paw and said, \"We can do it the safe way.\"")


def compromise(world: World, helper: Entity, hero: Entity, plan: Plan, prize: Thing) -> None:
    world.say(f"{helper.id} pointed to a small input tray instead of the big lever.")
    world.say(f'"How about we {plan.rush} together, then use the tray for the rest?" {helper.id} asked.')
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s ears perked up. \"Okay!\" {hero.pronoun()} said, and {hero.pronoun()} smiled at {helper.id}.")
    world.say(f"Soon {hero.id} was {plan.gerund}, {prize.label} stayed clean, and the little input tray did its job just right.")


def make_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add_entity(Entity(id=params.hero, animal=params.hero_kind, label=params.hero.lower()))
    helper = world.add_entity(Entity(id="helper", animal=params.helper, label="the helper"))
    prize_cfg = PRIZES[params.prize]
    prize = world.add_thing(Thing(
        id="prize",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        type=prize_cfg.type,
        fragile=True,
        owner=hero.id,
        caretaker=helper.id,
    ))
    plan = PLANS[params.plan]

    intro(world, hero)
    love_plan(world, hero, plan)
    prize_line(world, hero, prize)
    world.para()
    arrive(world, hero)
    wants(world, hero, plan)
    warn(world, helper, hero, plan, prize)
    defy(world, hero, plan)
    hold_back(world, helper, hero, plan)
    world.para()
    compromise(world, helper, hero, plan, prize)

    world.facts.update(hero=hero, helper=helper, prize=prize, plan=plan, place=place)
    return world


PLACES = {
    "barn": Place(name="the barn", afford={"input"}),
    "yard": Place(name="the yard", afford={"input"}),
    "garden": Place(name="the garden", afford={"input"}),
}

PLANS = {
    "input": Plan(
        id="input",
        label="the input lever",
        verb="pull the input lever",
        gerund="pulling the input lever",
        rush="tap the input lever",
        mess="mess",
        soil="in a big mess",
        zone={"floor"},
        keyword="input",
        tags={"input", "conflict"},
    )
}

PRIZES = {
    "bag": Thing(id="bag", label="seed bag", phrase="a seed bag with a bright tag", type="bag", fragile=True),
    "tray": Thing(id="tray", label="snack tray", phrase="a snack tray with a shiny rim", type="tray", fragile=True),
    "bell": Thing(id="bell", label="little bell", phrase="a little bell tied with twine", type="bell", fragile=True),
}

HEROES = {
    "rabbit": ["Pip", "Milo", "Nina", "Luna"],
    "fox": ["Fina", "Ruby", "Poppy", "Tess"],
    "cat": ["Mimi", "Cleo", "Mochi", "Sunny"],
    "dog": ["Benny", "Toby", "Rufus", "Buddy"],
}

HELPERS = {
    "rabbit": "rabbit",
    "fox": "fox",
    "cat": "cat",
    "dog": "dog",
}


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, plan, prize) for place in PLACES for plan in PLACES[place].afford for prize in PRIZES]


@dataclass
class StoryParams:
    place: str
    plan: str
    prize: str
    hero: str
    hero_kind: str
    helper: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with conflict and a gentle input compromise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero-kind", choices=HEROES)
    ap.add_argument("--hero")
    ap.add_argument("--helper", choices=HELPERS)
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
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.plan:
        combos = [c for c in combos if c[1] == args.plan]
    if args.prize:
        combos = [c for c in combos if c[2] == args.prize]
    if not combos:
        raise StoryError("No valid animal story matches those options.")
    place, plan, prize = rng.choice(sorted(combos))
    kind = args.hero_kind or rng.choice(sorted(HEROES))
    hero = args.hero or rng.choice(HEROES[kind])
    helper = args.helper or kind
    return StoryParams(place=place, plan=plan, prize=prize, hero=hero, hero_kind=kind, helper=helper)


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, plan, prize = f["hero"], f["helper"], f["plan"], f["prize"]
    return [
        QAItem(
            question=f"Why did {helper.id} worry when {hero.id} wanted to {plan.verb}?",
            answer=f"{helper.id} worried because {hero.id} might get {prize.label} {plan.soil} if the big input lever was used too soon.",
        ),
        QAItem(
            question=f"What did {hero.id} do after {helper.id} held up a paw?",
            answer=f"{hero.id} stopped rushing, listened, and agreed to use the small input tray instead.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and {prize.label}?",
            answer=f"{hero.id} finished {plan.gerund}, and {prize.label} stayed clean while everyone felt glad.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is input?", answer="Input is something you give to a machine or a plan so it knows what to do next."),
        QAItem(question="What does a helper do in a conflict?", answer="A helper can slow things down, point out a safer choice, and help everyone agree."),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story for young children that uses the word "input" and shows a small conflict.',
        f"Tell a gentle story about {f['hero'].label} the {f['hero'].animal} wanting to {f['plan'].verb} while another animal worries about {f['prize'].label}.",
        f"Write a short Animal Story with a beginning, a tense middle, and a happy compromise around the input lever.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: {dict(e.meters)} {dict(e.memes)}")
    for t in world.things.values():
        lines.append(f"{t.id}: {dict(t.meters)} {dict(t.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(P) :- prize(P).
valid_story(Place, Plan, Prize) :- place(Place), plan(Plan), prize(Prize), affords(Place, Plan), prize_at_risk(Prize).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for a in sorted(PLACES[p].afford):
            lines.append(asp.fact("affords", p, a))
    for p in PLANS:
        lines.append(asp.fact("plan", p))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="barn", plan="input", prize="bag", hero="Pip", hero_kind="rabbit", helper="rabbit"),
    StoryParams(place="yard", plan="input", prize="tray", hero="Fina", hero_kind="fox", helper="fox"),
    StoryParams(place="garden", plan="input", prize="bell", hero="Mimi", hero_kind="cat", helper="cat"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(vals)} compatible stories")
        for v in vals:
            print(v)
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
            header = f"### {p.hero}: {p.plan} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
