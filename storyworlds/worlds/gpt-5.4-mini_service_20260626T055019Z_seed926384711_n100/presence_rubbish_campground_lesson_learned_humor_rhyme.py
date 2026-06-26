#!/usr/bin/env python3
"""
storyworlds/worlds/presence_rubbish_campground_lesson_learned_humor_rhyme.py
============================================================================

A compact folk-tale story world set in a campground, built around the seed
words "presence" and "rubbish" with a lesson-learned turn, a little humor, and
a rhyme-friendly ending.

The premise is simple: a child at a campground notices a strange presence near
some rubbish. The worry turns into a funny discovery, and the ending proves the
lesson: keep the campsite clean, or the nighttime visitors will come sniffing.

This world is intentionally small and constraint-driven. Only a few plausible
combinations are allowed, and the story is simulated from state rather than
being a frozen paragraph with swapped nouns.
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
MESS_KINDS = {"litter", "spilled", "crumbled"}


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
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Site:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    tags: set[str] = field(default_factory=set)


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
    def __init__(self, site: Site) -> None:
        self.site = site
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
        return any(g.protective and region in getattr(g, "covers", set()) for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.site)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dirty_rubbish(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.entities.values():
                if item.owner != actor.id or item.protective:
                    continue
                sig = ("dirty", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["dirty"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} things got grubby in the campground.")
    return out


def _r_watchful_presence(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["unease"] < THRESHOLD:
            continue
        sig = ("presence", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["presence_felt"] += 1
        return ["__presence__"]
    return []


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["lesson"] < THRESHOLD:
            continue
        sig = ("lesson", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.id} remembered the lesson and smiled at the tidy fire ring.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("dirty_rubbish", "physical", _r_dirty_rubbish),
    Rule("watchful_presence", "social", _r_watchful_presence),
    Rule("lesson", "social", _r_lesson),
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
                produced.extend(s for s in sents if s != "__presence__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.site.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def predict_rubbish(world: World, actor: Entity, activity: Activity, rubbish_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    rub = sim.entities.get(rubbish_id)
    return {"dirty": bool(rub and rub.meters["dirty"] >= THRESHOLD)}


def site_detail(site: Site, activity: Activity) -> str:
    if site.place == "the campground":
        return "The pines stood like old watchmen, and the fire ring waited in a tidy circle."
    if activity.id == "picnic":
        return "The picnic table was bright with crumbs and sunlight."
    return f"{site.place.capitalize()} felt calm and open."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved campfire stories and pine-scented air.")


def loves_place(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.pronoun().capitalize()} loved {activity.gerund} by the tents, where every sound felt like a tale.")


def bring_rubbish(world: World, parent: Entity, hero: Entity, rubbish: Entity) -> None:
    world.say(f"That evening, {hero.id}'s {parent.pronoun('possessive') if parent.type in {'mother','father'} else 'grown-up'} pack held {hero.pronoun('object')} {rubbish.phrase}.")
    rubbish.worn_by = hero.id


def loves_rubbish(world: World, hero: Entity, rubbish: Entity) -> None:
    hero.memes["care"] += 1
    world.say(f"{hero.id} meant to carry {rubbish.it()} back to the bin, just as the old campers always said.")


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    world.say(f"One dusk, {hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.site.place}.")
    world.say(site_detail(world.site, activity))


def notices_presence(world: World, hero: Entity, rubbish: Entity) -> None:
    hero.memes["unease"] += 1
    world.say(f"Then {hero.id} noticed a strange presence near the rubbish and gasped, 'Who's there by my snack wrapper?'")
    world.say("The lantern flickered, and the shadows bobbed like a goat in boots.")
    world.say(f"'{rubbish.label} in the grass can make a campsite frown,' whispered the wind, with a tiny round sound.")


def warns(world: World, parent: Entity, hero: Entity, activity: Activity, rubbish: Entity) -> None:
    pred = predict_rubbish(world, hero, activity, rubbish.id)
    if pred["dirty"]:
        world.facts["predicted_dirty"] = True
        world.say(f'"Careful," said {parent.id}. "If that rubbish stays out, the campground will grow a nose for trouble."')


def fixes(world: World, parent: Entity, hero: Entity, rubbish: Entity) -> Gear:
    gear = world.add(Entity(
        id="bag",
        type="thing",
        label="trash bag",
        phrase="a sturdy trash bag",
        protective=True,
    ))
    gear.worn_by = hero.id
    hero.memes["lesson"] += 1
    world.say(f"{parent.id} laughed and said, 'Let's give that rubbish a ride home in a trash bag, my little bright-eyed guide.'")
    world.say(f"{hero.id} tugged the bag open, and the silly wrapper slid in as neat as a secret in a sleeve.")
    return Gear(id="bag", label="trash bag", covers={"hands"}, guards={"litter", "spilled", "crumbled"}, prep="pack the rubbish away", tail="packed the rubbish away", plural=False)


def accept(world: World, parent: Entity, hero: Entity, activity: Activity, rubbish: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["lesson"] += 1
    world.say(f"{hero.id} grinned and said, 'A clean camp is a kind camp, and a kind camp helps dreams not damp.'")
    world.say(f"Together they {gear_def.tail}. Soon {hero.id} was {activity.gerund}, {rubbish.label} tucked safely away, and the campground felt lighter than a feather in spring.")


def tale(world: World, hero: Entity, parent: Entity, activity: Activity, rubbish: Entity) -> None:
    world.say(f"At the end, the moon peeped down and found a tidy ring of stones.")
    world.say(f"{hero.id} learned that rubbish left behind can turn a quiet place queer, but rubbish picked up lets a friendly presence appear.")
    world.say(f"And so the camp kept its rhyme: 'Pack it out, and smile about; leave it there, and sniffs beware.'")


SETTINGS = {
    "campground": Site(place="the campground", indoor=False, affords={"picnic", "walk"}),
    "pine_trail": Site(place="the pine trail", indoor=False, affords={"walk"}),
}


ACTIVITIES = {
    "picnic": Activity(
        id="picnic",
        verb="have a picnic",
        gerund="sharing a picnic",
        rush="spread the blanket",
        mess="litter",
        soil="messy with crumbs",
        zone={"hands"},
        keyword="rubbish",
        tags={"rubbish", "camp", "clean"},
    ),
    "walk": Activity(
        id="walk",
        verb="walk the campground path",
        gerund="walking the path",
        rush="dash down the path",
        mess="crumbled",
        soil="scuffed with pine dust",
        zone={"feet"},
        keyword="presence",
        tags={"presence", "camp", "walk"},
    ),
}

RUBBISHES = {
    "wrapper": Entity(id="wrapper", type="thing", label="wrapper", phrase="a shiny cookie wrapper", owner="Mira"),
    "tin": Entity(id="tin", type="thing", label="tin", phrase="a dented tin cup", owner="Mira"),
    "crusts": Entity(id="crusts", type="thing", label="crumbs", phrase="some stale crusts", owner="Mira", plural=True),
}

GIRL_NAMES = ["Mira", "Nina", "Tessa", "Ruby", "Annie"]
BOY_NAMES = ["Owen", "Jasper", "Finn", "Milo", "Eli"]
TRAITS = ["brave", "curious", "bright", "cheerful", "small"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, site in SETTINGS.items():
        for act_id in site.affords:
            act = ACTIVITIES[act_id]
            for rid in RUBBISHES:
                combos.append((place, act_id, rid))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    rubbish: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, rub = f["hero"], f["parent"], f["activity"], f["rubbish"]
    return [
        f'Write a short folk tale for a child about "{act.keyword}" at a campground.',
        f"Tell a gentle story where {hero.id} and {hero.pronoun('possessive')} {parent.label} notice {rub.label} and learn to keep the campground clean.",
        f"Write a story with a rhyme, a funny campsite surprise, and a lesson learned about rubbish.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, rub, act = f["hero"], f["parent"], f["rubbish"], f["activity"]
    qa = [
        QAItem(
            question=f"Who is the story about at the campground?",
            answer=f"It is about {hero.id}, a little {next(t for t in hero.traits if t != 'little')} {hero.type}, and {parent.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} notice near the rubbish?",
            answer=f"{hero.id} noticed a strange presence near the rubbish, and that made the little camper stop and look around.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn in the end?",
            answer=f"{hero.id} learned that rubbish should be packed out and kept tidy, because a clean campground is kinder for everyone.",
        ),
        QAItem(
            question=f"How did the story turn from worry into a happy ending?",
            answer=f"At first the presence felt spooky, but it turned out to be a funny campsite surprise. Then {parent.id} helped {hero.id} use a trash bag, and the campsite grew neat again.",
        ),
    ]
    if f.get("predicted_dirty"):
        qa.append(QAItem(
            question=f"Why did {parent.id} warn {hero.id} about the rubbish?",
            answer=f"{parent.id} warned {hero.id} because leaving the rubbish out would have made the campground dirty and sniffed over by curious nighttime visitors.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is rubbish?",
            answer="Rubbish is trash or unwanted things people should throw away or pack out so a place stays clean.",
        ),
        QAItem(
            question="What is a campground?",
            answer="A campground is a place where people sleep outdoors in tents, cook simple meals, and share quiet nights near the trees.",
        ),
        QAItem(
            question="What does 'lesson learned' mean?",
            answer="A lesson learned is a helpful idea someone understands after an experience teaches it to them.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, which makes a song or story easy to remember.",
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
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="campground", activity="picnic", rubbish="wrapper", name="Mira", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="campground", activity="walk", rubbish="tin", name="Owen", gender="boy", parent="father", trait="cheerful"),
]


def explain_rejection(activity: Activity, rubbish: Entity) -> str:
    return f"(No story: {activity.gerund} does not fit this rubbish-and-presence tale.)"


ASP_RULES = r"""
rubbish_at_risk(A, R) :- activity(A), rubbish(R).
valid(Place, A, R) :- affords(Place, A), rubbish(R), rubbish_at_risk(A, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid in RUBBISHES:
        lines.append(asp.fact("rubbish", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A campground folk tale with presence, rubbish, humor, rhyme, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--rubbish", choices=RUBBISHES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if args.activity and args.rubbish:
        if (args.place or "campground") not in SETTINGS:
            raise StoryError("(No valid campground setting.)")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.rubbish is None or c[2] == args.rubbish)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, rubbish = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, rubbish=rubbish, name=name, gender=gender, parent=parent, trait=trait)


def tell(site: Site, activity: Activity, rubbish_cfg: Entity, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(site)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + hero_traits))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="grown-up"))
    rubbish = world.add(copy.deepcopy(rubbish_cfg))
    rubbish.owner = hero.id
    introduce(world, hero)
    loves_place(world, hero, activity)
    bring_rubbish(world, parent, hero, rubbish)
    loves_rubbish(world, hero, rubbish)
    world.para()
    arrive(world, hero, parent, activity)
    notices_presence(world, hero, rubbish)
    warns(world, parent, hero, activity, rubbish)
    _do_activity(world, hero, activity, narrate=True)
    world.para()
    gear_def = fixes(world, parent, hero, rubbish)
    accept(world, parent, hero, activity, rubbish, gear_def)
    world.para()
    tale(world, hero, parent, activity, rubbish)
    world.facts.update(hero=hero, parent=parent, rubbish=rubbish, activity=activity, site=site)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], RUBBISHES[params.rubbish], params.name, params.gender, [params.trait], params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, rubbish) combos:\n")
        for place, act, rub in combos:
            print(f"  {place:10} {act:8} {rub:8}")
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
            header = f"### {p.name}: {p.activity} at {p.place} (rubbish: {p.rubbish})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
