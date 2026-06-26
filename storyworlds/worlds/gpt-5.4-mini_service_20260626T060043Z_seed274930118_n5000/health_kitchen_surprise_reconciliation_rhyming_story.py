#!/usr/bin/env python3
"""
storyworlds/worlds/health_kitchen_surprise_reconciliation_rhyming_story.py
=========================================================================

A small kitchen story world about health, surprise, and reconciliation,
styled like a rhyming story for young children.

Seed tale:
---
A child in the kitchen wants a fun sweet treat.
A parent worries it won't be healthy to eat.
Then a surprise appears: a bright basket of fruit.
The child and parent reconcile and make a kinder route.

World model:
---
* Characters have physical meters and emotional memes.
* Kitchen activities can raise mess and healthful feelings.
* A surprise can shift the plan, and reconciliation clears tension.
* The ending proves the change with a concrete image: the healthy food is made,
  the worry is gone, and the shared joy is visible.

This script follows the Storyweavers contract:
- self-contained stdlib script
- eager import of storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- build_parser, resolve_params, generate, emit, main
- support default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "health": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "surprise": 0.0, "reconcile": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "grandma"}
        male = {"boy", "father", "dad", "man", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class KitchenSetting:
    place: str = "the kitchen"
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    health: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: KitchenSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["mess"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                continue
            sig = ("spill", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["mess"] += 1
            out.append(f"{actor.id}'s {item.label} got speckled and spry.")
    return out


def _r_health(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["reconcile"] < THRESHOLD:
            continue
        sig = ("health", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["health"] += 1
        out.append(f"{actor.id} felt brighter, lighter, and glad to be free.")
    return out


CAUSAL_RULES = [
    _r_spill,
    _r_health,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    import copy
    sim.entities = copy.deepcopy(world.entities)
    sim.fired = set(world.fired)
    sim.zone = set(activity.zone)
    sim_actor = sim.get(actor.id)
    sim_actor.meters["mess"] += 1
    spill = False
    prize = sim.entities.get(prize_id)
    if prize and prize.region in activity.zone and not any(
        g.protective and prize.region in g.covers and g.worn_by == sim_actor.id
        for g in sim.worn_items(sim_actor)
    ):
        spill = True
    return {"soiled": spill, "health": sim_actor.meters["health"]}


def intro(world: World, hero: Entity) -> None:
    world.say(f"In the kitchen bright, with spoons that sing, {hero.id} was a child in spring.")


def loves(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["joy"] += 1
    world.say(f"{hero.pronoun().capitalize()} loved to {activity.verb}; it made the room hum and ring.")


def surprise(world: World, helper: Entity, hero: Entity, prize: Entity, activity: Activity) -> None:
    hero.memes["surprise"] += 1
    helper.memes["surprise"] += 1
    world.say(
        f"Then {helper.id} came in with a basket so neat, "
        f"full of {prize.phrase} that smelled fresh and sweet."
    )
    world.say(
        f'"A healthy surprise," {helper.pronoun("subject")} said with a grin, '
        f'"let us make something better to share and begin."'
    )


def want_treat(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 1
    world.say(
        f"{hero.id} wanted a sugary snack, quick and bright, "
        f"but the parent worried it would not be right."
    )
    world.say(
        f'"Too much sugar can wobble the body," {hero.pronoun("possessive")} parent said, '
        f'"so let us choose fruit instead, with berries and red."'
    )


def reconcile(world: World, parent: Entity, hero: Entity, prize: Entity, gear: Gear) -> None:
    hero.memes["reconcile"] += 1
    parent.memes["reconcile"] += 1
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} softened at once, and the frown slipped away; "
        f"{hero.id} nodded and smiled, ready to play."
    )
    world.say(
        f'"Okay," {hero.id} said, "let us use {gear.label} too, '
        f"then the fruit can be stirred, and our shirts stay new.""
    )
    world.say(
        f"They {gear.tail}. Soon {hero.id} was {prize.label}-happy and full of good cheer, "
        f"making a bowl of bright fruit that everyone held dear."
    )


def tell(setting: KitchenSetting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", helper_type: str = "grandma") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="grandma"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    intro(world, hero)
    loves(world, hero, activity)
    want_treat(world, hero, activity)
    world.para()
    surprise(world, helper, hero, prize, activity)
    world.say(f"The bowl sat on the table, all shiny and keen, and the air felt clean and green.")
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label} was wary and lean.")
    pred = predict_mess(world, hero, activity, prize.id)
    if pred["soiled"]:
        world.say(f'"You could splatter that {prize.label}," {parent.pronoun("subject")} said with care, "and then I would need to scrub everywhere."')
    gear = select_gear(activity, prize)
    if gear is None:
        raise StoryError("No reasonable kitchen gear fits this activity and prize.")
    gear_ent = world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), plural=gear.plural))
    gear_ent.worn_by = hero.id
    world.para()
    reconcile(world, parent, hero, prize, gear)
    hero.meters["health"] += 1
    hero.meters["mess"] += 1
    propagate(world, narrate=False)
    world.say(
        f"In the end, they mixed fruit with a spoon, and the kitchen glowed like a sunny tune. "
        f"The sweet surprise became a healthy delight, and parent and child were friends again that night."
    )

    world.facts.update(
        hero=hero,
        parent=parent,
        helper=helper,
        prize=prize,
        activity=activity,
        gear=gear,
        setting=setting,
        conflict=True,
        resolved=True,
        predicted_soil=activity.health,
    )
    return world


SETTINGS = {
    "kitchen": KitchenSetting(place="the kitchen", affords={"smoothie", "fruit_bowl", "salad"}),
}

ACTIVITIES = {
    "smoothie": Activity(
        id="smoothie",
        verb="blend a fruity smoothie",
        gerund="blending a fruity smoothie",
        rush="dash for the blender",
        mess="splashy",
        health="healthy",
        zone={"torso"},
        keyword="health",
        tags={"health", "fruit"},
    ),
    "fruit_bowl": Activity(
        id="fruit_bowl",
        verb="make a fruit bowl",
        gerund="making a fruit bowl",
        rush="grab the strawberries",
        mess="splashy",
        health="healthy",
        zone={"torso"},
        keyword="health",
        tags={"health", "fruit"},
    ),
    "salad": Activity(
        id="salad",
        verb="toss a salad",
        gerund="tossing a salad",
        rush="reach for the lettuce",
        mess="splashy",
        health="healthy",
        zone={"torso"},
        keyword="health",
        tags={"health", "greens"},
    ),
}

PRIZES = {
    "shirt": Prize(label="shirt", phrase="a clean white shirt", type="shirt", region="torso"),
    "apron": Prize(label="apron", phrase="a bright apron", type="apron", region="torso"),
}

GEAR = [
    Gear(id="apron", label="a bright apron", covers={"torso"}, guards={"splashy"}, prep="tie on the bright apron", tail="tied on the bright apron"),
]

NAMES = ["Mina", "Luna", "Toby", "Milo", "Nora", "Eli"]
TRAITS = ["gentle", "curious", "cheery", "bouncy"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    helper: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, prize = f["hero"], f["parent"], f["activity"], f["prize"]
    return [
        f'Write a short rhyming story about {hero.id} in {world.setting.place} with the word "health".',
        f"Tell a gentle kitchen story where {hero.id} wants to {act.verb} but {parent.label} worries about {prize.phrase}.",
        f"Write a surprise-and-reconciliation story that ends with a healthy snack and a happy family.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, helper, prize, act = f["hero"], f["parent"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the kitchen at first?",
            answer=f"{hero.id} wanted to {act.verb}, but the parent worried it might get messy and not feel healthy enough.",
        ),
        QAItem(
            question=f"Who brought the surprise in the story?",
            answer=f"{helper.id} brought the surprise basket of fruit and helped turn the moment into something kind and cheerful.",
        ),
        QAItem(
            question=f"How did {hero.id} and the parent reconcile?",
            answer=f"They agreed to use {f['gear'].label} and make a healthy fruit treat together, so the worry faded away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does healthy food do for your body?",
            answer="Healthy food helps your body grow, gives you energy, and can help you feel strong and ready to play.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something you did not expect to happen, so it can make you gasp, smile, or laugh.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and make peace again, often by talking kindly and sharing a new plan.",
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
    lines.append("== (3) World knowledge questions ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", activity="smoothie", prize="shirt", name="Mina", gender="girl", parent="mother", helper="grandma", trait="curious"),
    StoryParams(place="kitchen", activity="fruit_bowl", prize="shirt", name="Toby", gender="boy", parent="father", helper="grandma", trait="gentle"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.gerund} would not reasonably threaten {prize.phrase} in this kitchen setup.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.activity and args.prize:
        act, pr = ACTIVITIES[args.activity], PRIZES[args.prize]
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            raise StoryError(explain_rejection(act, pr))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    helper = args.helper or "grandma"
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.helper)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        lines.append(asp.fact("health_of", aid, a.health))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming kitchen story about health, surprise, and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--helper")
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
            header = f"### {p.name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
