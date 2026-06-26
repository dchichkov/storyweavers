#!/usr/bin/env python3
"""
pantomime_slick_bravery_curiosity_adventure.py
===============================================

A small storyworld about a child, a pantomime, and a slick stage.

Seed-tale premise:
A curious child watches a silent pantomime performance. The stage floor is
slick, so the child is warned to be brave but careful. A prop slips away, the
child uses curiosity to notice a safer path, and bravery helps them cross the
stage, return the prop, and finish the show with a bright, triumphant bow.
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
    support: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    zone: set[str]
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prop:
    id: str
    label: str
    phrase: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(it.support == region for it in self.worn_items(actor))

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.lines = [[]]
        return w


def _r_fumble(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("slick", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.meters.get("held", 0.0) >= THRESHOLD:
                sig = ("fumble", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["slipped"] = 1.0
                out.append(f"{actor.id} lost hold of the {item.label}.")
    return out


def _r_rescue(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("curiosity", 0.0) < THRESHOLD or actor.meters.get("slick", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("rescue", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["focus"] = actor.memes.get("focus", 0.0) + 1.0
        out.append(f"{actor.id} looked for the safest step and moved with care.")
    return out


CAUSAL_RULES = [_r_fumble, _r_rescue]


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


def predict_wobble(world: World, actor: Entity, action: Action, prop: Prop) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    p = sim.get(prop.id)
    return {
        "lost_prop": p.meters.get("slipped", 0.0) >= THRESHOLD,
        "focus": sim.get(actor.id).memes.get("focus", 0.0),
    }


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.place.affords:
        raise StoryError(f"This place cannot host {action.id}.")
    world.zone = set(action.zone)
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity, trait: str) -> None:
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved big adventures in quiet places.")


def loves_show(world: World, hero: Entity, action: Action) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(f"{hero.pronoun().capitalize()} loved watching {action.keyword} because the silent motions felt like a treasure map.")


def buy_prop(world: World, child: Entity, prop: Entity) -> None:
    world.say(f"That day, {child.pronoun('possessive')} family gave {child.id} {prop.phrase} to carry to the show.")


def cherish_prop(world: World, hero: Entity, prop: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    prop.meters["held"] = 1.0
    world.say(f"{hero.id} held {hero.pronoun('possessive')} {prop.label} carefully and smiled at the shiny little details.")


def arrive(world: World, hero: Entity, guide: Entity, action: Action) -> None:
    world.say(f"One evening, {hero.id} and {hero.pronoun('possessive')} {guide.label} went to {world.place.name}.")
    world.say(f"The stage looked ready, but one patch near the curtain was slick with spilled water.")
    hero.meters["slick"] = 1.0


def warn(world: World, guide: Entity, hero: Entity, prop: Entity, action: Action) -> None:
    pred = predict_wobble(world, hero, action, prop)
    if pred["lost_prop"]:
        world.facts["warned"] = True
        world.say(f"\"Be brave, but take careful steps,\" {guide.pronoun('subject')} said. \"The slick floor could send your {prop.label} sliding.\"")


def want_to_help(world: World, hero: Entity, action: Action) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    world.say(f"{hero.id} wanted to help anyway, even though the slick stage made every step feel like a tiny cliff.")


def notice_path(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.say(f"{hero.id} noticed a dry line of boards along the edge, and {hero.pronoun('subject')} studied it like a map.")


def resolve(world: World, hero: Entity, guide: Entity, prop: Entity, action: Action) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    hero.meters["slick"] = 0.0
    hero.meters["careful_steps"] = 1.0
    world.say(f"With brave feet and curious eyes, {hero.id} crossed the stage by the dry boards and picked up the {prop.label}.")
    world.say(f"Then {hero.id} slipped the {prop.label} back to the actor, and the pantomime ended with a proud bow.")
    world.say(f"{guide.id} laughed softly and said the adventure was better because {hero.id} had noticed the safe way.")


def tell(place: Place, action: Action, prop_cfg: Prop, hero_name: str = "Nia", hero_type: str = "girl", guide_type: str = "mother", trait: str = "curious") -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guide = world.add(Entity(id="Guide", kind="character", type=guide_type, label="guide"))
    prop = world.add(Entity(id="prop", type=prop_cfg.label, label=prop_cfg.label, phrase=prop_cfg.phrase, owner=hero.id, caretaker=guide.id))
    intro(world, hero, trait)
    loves_show(world, hero, action)
    buy_prop(world, hero, prop)
    cherish_prop(world, hero, prop)
    world.para()
    arrive(world, hero, guide, action)
    warn(world, guide, hero, prop, action)
    want_to_help(world, hero, action)
    notice_path(world, hero)
    resolve(world, hero, guide, prop, action)
    world.facts.update(hero=hero, guide=guide, prop=prop, action=action, trait=trait)
    return world


PLACES = {
    "the old theater": Place("the old theater", indoors=True, affords={"pantomime"}),
    "the town hall stage": Place("the town hall stage", indoors=True, affords={"pantomime"}),
}

ACTIONS = {
    "pantomime": Action(
        id="pantomime",
        verb="watch the pantomime",
        gerund="watching the pantomime",
        rush="dash toward the stage",
        risk="slick",
        zone={"feet"},
        mess="slick",
        keyword="pantomime",
        tags={"pantomime", "adventure", "curiosity", "bravery"},
    ),
}

PROPS = {
    "mask": Prop(id="mask", label="mask", phrase="a bright paper mask", region="hands"),
    "lantern": Prop(id="lantern", label="lantern", phrase="a tiny lantern with a gold handle", region="hands"),
}

CURATED = [
    dict(place="the old theater", action="pantomime", prop="mask", name="Nia", gender="girl", guide="mother", trait="curious"),
    dict(place="the town hall stage", action="pantomime", prop="lantern", name="Owen", gender="boy", guide="father", trait="brave"),
]

GIRL_NAMES = ["Nia", "Mina", "Tess", "Lina", "Ivy", "Ava"]
BOY_NAMES = ["Owen", "Finn", "Theo", "Ezra", "Leo", "Max"]
TRAITS = ["curious", "brave", "bold", "spirited"]


@dataclass
class StoryParams:
    place: str
    action: str
    prop: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story for a child that includes the word "{f["action"].keyword}".',
        f"Tell a gentle tale where {f['hero'].id} uses curiosity and bravery at {world.place.name} to help during a pantomime.",
        f"Write a child-friendly story about a slick stage, a careful rescue, and a happy bow at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, prop, action = f["hero"], f["guide"], f["prop"], f["action"]
    return [
        QAItem(question=f"What kind of show was happening at {world.place.name}?", answer=f"It was a pantomime, a silent show with big motions and funny clues."),
        QAItem(question=f"Why did {hero.id} need to move carefully?", answer=f"{hero.id} needed to move carefully because the stage was slick and a slip could send the {prop.label} sliding."),
        QAItem(question=f"How did {hero.id} help in the end?", answer=f"{hero.id} used curiosity to spot a safe path, then bravery to cross the slick stage and return the {prop.label}."),
        QAItem(question=f"How did {guide.id} feel at the end?", answer=f"{guide.id} felt pleased and proud because {hero.id} stayed careful and finished the little adventure well."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is pantomime?", answer="Pantomime is a performance that tells a story with actions and gestures instead of spoken words."),
        QAItem(question="What does slick mean?", answer="Slick means slippery or smooth, so it can be easy to slide or lose your footing."),
        QAItem(question="What is curiosity?", answer="Curiosity is the wish to know more, notice details, and ask questions."),
        QAItem(question="What is bravery?", answer="Bravery is feeling afraid or careful but still doing what needs to be done."),
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


SETTINGS = {
    "the old theater": PLACES["the old theater"],
    "the town hall stage": PLACES["the town hall stage"],
}

ACTIVITIES = ACTIONS
PRIZES = PROPS


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in ACTIVITIES.values():
            if act.id not in setting.affords:
                continue
            for prop in PRIZES.values():
                combos.append((place, act.id, prop.id))
    return combos


def explain_rejection(action: Action, prop: Prop) -> str:
    return f"(No story: this world expects a pantomime on a stage, but the requested pair {action.id} and {prop.label} does not fit the small adventure premise.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child, a pantomime, a slick stage, and a brave curious rescue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIVITIES)
    ap.add_argument("--prop", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father"])
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
    if args.action and args.prop:
        if args.action == "pantomime" and args.prop not in PRIZES:
            raise StoryError("Invalid prop.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.prop is None or c[2] == args.prop)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, prop = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prop=prop, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.action], PRIZES[params.prop], params.name, params.gender, params.guide, params.trait)
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


ASP_RULES = r"""
place(P) :- setting(P).
valid(P,A,R) :- affords(P,A), action(A), prop(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for a in SETTINGS[p].affords:
            lines.append(asp.fact("affords", p, a))
    for a in ACTIVITIES.values():
        lines.append(asp.fact("action", a.id))
    for r in PRIZES.values():
        lines.append(asp.fact("prop", r.id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in python:", sorted(py - asp_set))
    print("  only in clingo:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(StoryParams(place=d["place"], action=d["action"], prop=d["prop"], name=d["name"], gender=d["gender"], guide=d["guide"], trait=d["trait"])) for d in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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
            header = f"### {p.name}: {p.action} at {p.place} (prop: {p.prop})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
