#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mould_bad_ending_comedy.py
=======================================================================================================

A small standalone story world about mould, meant to stay close to comedy and
end with a bad ending.

The seed tale behind this world is simple:
a child finds something mouldy, makes a silly attempt to deal with it, and the
day goes a little wrong in a funny way.

This script follows the Storyweavers contract:
- self-contained stdlib script under storyworlds/worlds/
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate, emit,
  and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp

The world model uses physical meters and emotional memes:
- mould spreads through damp things
- attempted cleaning can make the mess funnier or worse
- the ending is intentionally not a happy fix
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    damp: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    type: str
    risk: set[str]
    spoil: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)

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
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.facts = _copy.deepcopy(self.facts)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w


def _get_meter(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _set_meter(ent: Entity, key: str, val: float) -> None:
    ent.meters[key] = val


def _add_meter(ent: Entity, key: str, delta: float) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + delta


def _add_meme(ent: Entity, key: str, delta: float) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + delta


def _rule_mould_spread(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if _get_meter(ent, "mould") < THRESHOLD:
            continue
        sig = ("spread", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if ent.type in {"bread", "cake", "cheese"}:
            _add_meter(ent, "gross", 1)
        if ent.caretaker:
            caretaker = world.get(ent.caretaker)
            _add_meme(caretaker, "disgust", 1)
        out.append(f"The mould on {ent.label} spread into a bigger spot.")
    return out


def _rule_sticky_hands(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _get_meter(actor, "mould") < THRESHOLD:
            continue
        sig = ("hands", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        _add_meme(actor, "embarrassment", 1)
        out.append(f"{actor.id} ended up with sticky fingers and a very silly face.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_rule_mould_spread, _rule_sticky_hands):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def item_at_risk(activity: Activity, item: Item) -> bool:
    return bool(activity.zone & item.risk)


def valid_combo(setting: str, activity: str, item: str) -> bool:
    s = SETTINGS[setting]
    a = ACTIVITIES[activity]
    i = ITEMS[item]
    return activity in s.affords and item_at_risk(a, i)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for a in SETTINGS[s].affords:
            for i in ITEMS:
                if valid_combo(s, a, i):
                    out.append((s, a, i))
    return out


def predict_mess(world: World, actor: Entity, activity: Activity, item_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    item = sim.get(item_id)
    return {"mouldy": _get_meter(item, "mould") >= THRESHOLD,
            "gross": _get_meter(item, "gross") >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    _add_meter(actor, "mould", 1)
    _add_meme(actor, "joy", 1)
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved finding funny surprises in the kitchen.")


def loves_mould(world: World, hero: Entity) -> None:
    _add_meme(hero, "curiosity", 1)
    world.say(f"{hero.pronoun().capitalize()} thought the spotted green mould looked both gross and fascinating.")


def discovers(world: World, hero: Entity, item: Entity) -> None:
    world.say(f"Then {hero.id} spotted {hero.pronoun('possessive')} {item.label} hiding at the back of the shelf.")


def warns(world: World, parent: Entity, hero: Entity, activity: Activity, item: Entity) -> None:
    pred = predict_mess(world, hero, activity, item.id)
    world.facts["predicted"] = pred
    if pred["mouldy"]:
        world.say(
            f'"Don't eat that," {parent.pronoun("possessive")} {parent.label} said. '
            f'"It looks mouldy, and mould is not a snack."'
        )


def silly_plan(world: World, hero: Entity, item: Entity) -> None:
    _add_meme(hero, "boldness", 1)
    world.say(f"{hero.id} decided the serious answer was to wipe it with a napkin and hope for the best.")


def messy_fail(world: World, hero: Entity, item: Entity) -> None:
    _add_meter(item, "mould", 1)
    _add_meter(item, "gross", 1)
    _add_meme(hero, "oops", 1)
    world.say(f"But the napkin only smeared the mould into a bigger, sillier blotch on {item.label}.")


def ending_bad(world: World, hero: Entity, parent: Entity, item: Entity) -> None:
    _add_meme(parent, "disgust", 1)
    _add_meme(hero, "sadness", 1)
    world.say(
        f"In the end, {parent.id} tossed the {item.label} into the bin, "
        f"and {hero.id}'s tummy growled because the snack was gone."
    )
    world.say(
        f"The kitchen smelled like a compost joke, {hero.id} still had sticky fingers, "
        f"and nobody got a treat."
    )


SETTINGS = {
    "kitchen": Setting(place="the kitchen", damp=False, affords={"snack"}),
    "pantry": Setting(place="the pantry", damp=False, affords={"snack"}),
    "basement": Setting(place="the basement", damp=True, affords={"snack", "search"}),
    "shed": Setting(place="the shed", damp=True, affords={"search"}),
}

ACTIVITIES = {
    "snack": Activity(
        id="snack",
        verb="eat the snack",
        gerund="snacking",
        rush="grab the snack",
        mess="mould",
        zone={"mouth", "hands"},
        keyword="mould",
        tags={"mould", "food"},
    ),
    "search": Activity(
        id="search",
        verb="search for hidden treats",
        gerund="searching",
        rush="dash to the shelf",
        mess="mould",
        zone={"hands"},
        keyword="mould",
        tags={"mould"},
    ),
}

ITEMS = {
    "bread": Item(
        id="bread",
        label="bread",
        phrase="a loaf of bread",
        type="bread",
        risk={"mouth", "hands"},
        spoil="mouldy and stale",
    ),
    "cake": Item(
        id="cake",
        label="cake",
        phrase="a little cake",
        type="cake",
        risk={"mouth", "hands"},
        spoil="mouldy and crumbly",
    ),
    "cheese": Item(
        id="cheese",
        label="cheese",
        phrase="a block of cheese",
        type="cheese",
        risk={"mouth", "hands"},
        spoil="mouldy and smelly",
    ),
}

NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Max"]
TRAITS = ["curious", "cheerful", "silly", "brave", "bouncy"]
PARENTS = ["mother", "father"]


@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comedy story world about mould and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=PARENTS)
    ap.add_argument("--name")
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
              and (args.activity is None or c[1] == args.activity)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("No valid mould story matches those options.")
    place, activity, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    parent = args.parent or rng.choice(PARENTS)
    trait = rng.choice(TRAITS)
    if args.gender and args.name is None:
        if args.gender == "girl" and name in {"Leo", "Ben", "Max"}:
            name = rng.choice([n for n in NAMES if n not in {"Leo", "Ben", "Max"}])
        if args.gender == "boy" and name in {"Mia", "Nora", "Ava"}:
            name = rng.choice([n for n in NAMES if n not in {"Mia", "Nora", "Ava"}])
    return StoryParams(place=place, activity=activity, item=item, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    activity = ACTIVITIES[params.activity]
    item_cfg = ITEMS[params.item]
    world = World(setting)

    hero_type = params.gender
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    item = world.add(Entity(
        id="item",
        type=item_cfg.type,
        label=item_cfg.label,
        phrase=item_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    world.say(f"{hero.id} was a little {params.trait} {hero.type} who lived for strange little adventures.")
    world.say(f"{hero.pronoun().capitalize()} noticed {item.phrase} on a shelf and thought mould was a very funny-looking monster.")
    world.para()

    discovers(world, hero, item)
    loves_mould(world, hero)
    warns(world, parent, hero, activity, item)
    silly_plan(world, hero, item)
    _do_activity(world, hero, activity)
    messy_fail(world, hero, item)

    world.para()
    ending_bad(world, hero, parent, item)

    world.facts.update(hero=hero, parent=parent, item=item, activity=activity, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, item, activity = f["hero"], f["parent"], f["item"], f["activity"]
    return [
        f'Write a short funny story for a child about "{activity.keyword}" and a mouldy {item.label}.',
        f"Tell a comedy story where {hero.id} tries to deal with mould, but {parent.label} warns {hero.pronoun('object')} not to eat the spoiled snack.",
        f"Write a small child-friendly story about {hero.id}, {parent.label}, and a bad ending involving mould.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, item, activity = f["hero"], f["parent"], f["item"], f["activity"]
    return [
        QAItem(
            question=f"Who found the mouldy {item.label}?",
            answer=f"{hero.id} found the mouldy {item.label} in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did {parent.label} tell {hero.id} not to eat it?",
            answer=f"{parent.label} warned {hero.id} because the {item.label} was mouldy, and mould is not safe to eat.",
        ),
        QAItem(
            question=f"What silly thing did {hero.id} try to do with the {item.label}?",
            answer=f"{hero.id} tried to wipe it with a napkin, but that only made the mould look even funnier and messier.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended badly: the {item.label} was thrown away, and {hero.id} did not get the snack.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mould?",
            answer="Mould is a fuzzy growth that can appear on old food or in damp places, and it means the food should not be eaten.",
        ),
        QAItem(
            question="Why is mouldy food not good to eat?",
            answer="Mouldy food can make a person sick, so grown-ups throw it away instead of serving it.",
        ),
        QAItem(
            question="Why can damp places grow mould?",
            answer="Damp places stay wet longer, and mould likes wet places because they help it grow.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World QA ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, I) :- activity(A), item(I), splashes(A, R), risk(I, R).
valid_story(P, A, I) :- setting(P), affords(P, A), prize_at_risk(A, I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.damp:
            lines.append(asp.fact("damp", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for iid, i in ITEMS.items():
        lines.append(asp.fact("item", iid))
        for r in sorted(i.risk):
            lines.append(asp.fact("risk", iid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="kitchen", activity="snack", item="bread", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="basement", activity="search", item="cake", name="Leo", gender="boy", parent="father", trait="silly"),
    StoryParams(place="pantry", activity="snack", item="cheese", name="Nora", gender="girl", parent="mother", trait="cheerful"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
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
            header = f"### {p.name}: {p.activity} in {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
