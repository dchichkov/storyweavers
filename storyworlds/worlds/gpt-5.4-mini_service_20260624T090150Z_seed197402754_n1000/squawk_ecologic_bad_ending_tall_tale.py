#!/usr/bin/env python3
"""
squawk_ecologic_bad_ending_tall_tale.py
=======================================

A small storyworld about a tall-tale bird crew, an ecologic promise, and a
bad ending when the promise goes sideways.

Premise:
- A child hears a grand squawking claim about helping the wetlands stay ecologic.
- The helper birds start with a heroic plan: gather shiny trash, clear reeds,
  and free a little pond.
- Their pride gets ahead of their judgment.
- The plan backfires, and the bad ending proves the damage by the final image.

This world is intentionally tight: only a few combinations are reasonable, and
the story is driven by the simulated state rather than a frozen template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
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
class Place:
    name: str
    outdoors: bool = True
    affords: set[str] = field(default_factory=set)
    water: bool = False
    reeds: bool = False


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    harm: str
    spread: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w


def _mess_rule(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("squawk", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("ecologic", 0.0) < THRESHOLD:
            continue
        if world.place.name not in {"the marsh", "the riverbend"}:
            continue
        sig = ("mess", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        if world.place.water:
            world.zone.update({"water", "reeds", "shore"})
            out.append(f"Their great squawk startled the reeds and sent a splash across the pond.")
            out.append(f"The water turned cloudy, and the little fish had no clear place to hide.")
        else:
            world.zone.update({"ground", "reeds"})
            out.append(f"Their great squawk shook the cattails so hard that mud leaped onto the bank.")
            out.append(f"The wet ground went slick, and the bright path lost its easy shine.")
    return out


def _damage_rule(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.kind != "thing":
            continue
        if item.location not in world.zone:
            continue
        if item.meters.get("dirty", 0.0) >= THRESHOLD:
            continue
        sig = ("damage", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
        item.meters["broken"] = item.meters.get("broken", 0.0) + 1
        out.append(f"That left {item.label} worse off than before.")
    return out


def _sad_rule(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("loss", 0.0) < THRESHOLD:
            continue
        sig = ("sad", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["regret"] = actor.memes.get("regret", 0.0) + 1
        out.append(f"{actor.id} felt a heavy hush after the trouble.")
    return out


RULES = [_mess_rule, _damage_rule, _sad_rule]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def ecologic_story(place: Place, hero_name: str, helper_name: str) -> World:
    world = World(place)
    child = world.add(Entity(id=hero_name, kind="character", type="boy", traits=["wide-eyed", "careful"]))
    helper = world.add(Entity(id=helper_name, kind="character", type="bird", label="the big squawking bird"))
    prize = world.add(Entity(
        id="pond-sign",
        type="sign",
        label="the painted pond sign",
        phrase="the painted pond sign that told visitors to keep the water clean",
        caretaker=child.id,
        location="shore",
    ))
    reeds = world.add(Entity(
        id="reeds",
        type="reeds",
        label="the tall reeds",
        phrase="the tall reeds along the water",
        caretaker=helper.id,
        location="reeds",
    ))
    fish = world.add(Entity(
        id="fish",
        type="fish",
        label="the little fish",
        phrase="the little fish in the pond",
        location="water",
        plural=True,
    ))

    child.meters["hope"] = 1
    helper.meters["squawk"] = 1
    helper.meters["ecologic"] = 1

    world.say(f"{child.id} once met {helper.pronoun('object')} {helper.label if helper.label else 'the bird'} by the marsh.")
    world.say(f"{helper.id} was a tall-tale bird with a voice like a tin horn and a wish to be ecologic.")
    world.say(f"{helper.id} cried, \"I can clean this whole place with one grand squawk!\"")

    world.para()
    world.say(f"{child.id} looked at {helper.id} and hoped the boast might be true.")
    world.say(f"The day was bright on {place.name}, and the pond sat still as a glass cup.")
    world.say(f"Then {helper.id} lifted {helper.pronoun('possessive')} beak and let out a squawk so big it rattled the cattails.")

    helper.meters["squawk"] += 1
    helper.meters["ecologic"] += 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"At first, {helper.id} thought the noisy plan was working.")
    world.say(f"But the squawk blew mud into the water, bent the reeds, and scared the fish into the far corner.")
    prize.meters["dirty"] = prize.meters.get("dirty", 0.0) + 1
    reeds.meters["dirty"] = reeds.meters.get("dirty", 0.0) + 1
    fish.meters["loss"] = fish.meters.get("loss", 0.0) + 1
    child.meters["loss"] = child.meters.get("loss", 0.0) + 1
    propagate(world, narrate=True)

    world.para()
    world.say(f"{child.id} asked for a gentler plan, but the great bird wanted one more heroic squawk.")
    world.say(f"So {helper.id} tried again, and this time the muddy bank slipped under {helper.pronoun('possessive')} feet.")
    world.say(f"The sign fell face-down in the muck, the reeds bowed crooked, and the pond stayed cloudy.")
    world.say(f"That was the bad ending: the place that was meant to be ecologic looked worn out instead.")

    world.facts.update(
        child=child,
        helper=helper,
        prize=prize,
        reeds=reeds,
        fish=fish,
        place=place,
        bad_ending=True,
    )
    return world


PLACES = {
    "marsh": Place(name="the marsh", outdoors=True, affords={"squawk", "ecologic"}, water=True, reeds=True),
    "riverbend": Place(name="the riverbend", outdoors=True, affords={"squawk", "ecologic"}, water=True, reeds=True),
}

ACTIVITIES = {
    "squawk": Action(
        id="squawk",
        verb="squawk",
        gerund="squawking",
        rush="flap and holler",
        mess="noise",
        harm="scare the fish",
        spread={"water", "reeds", "shore"},
        keyword="squawk",
        tags={"bird", "noise"},
    ),
    "ecologic": Action(
        id="ecologic",
        verb="work ecologic",
        gerund="being ecologic",
        rush="rush to fix everything",
        mess="mud",
        harm="bend the reeds",
        spread={"water", "reeds", "shore"},
        keyword="ecologic",
        tags={"ecologic", "water"},
    ),
}

PRIZES = {
    "sign": Prize(id="sign", label="pond sign", phrase="the pond sign", region="shore"),
    "reeds": Prize(id="reeds", label="reeds", phrase="the reeds", region="reeds", plural=True),
}

GEAR = [
    Gear(id="quiet-feathers", label="quiet-feathers", helps={"squawk"}, covers={"water", "shore"}, prep="try a quieter call first", tail="took a softer turn"),
    Gear(id="mud-boards", label="mud boards", helps={"ecologic"}, covers={"shore", "reeds"}, prep="lay mud boards across the bank", tail="walked carefully on the boards"),
]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    helper: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, p in PLACES.items():
        for act_id in p.affords:
            for prize_id in PRIZES:
                combos.append((place, act_id, prize_id))
    return combos


def explain_rejection(activity: Action, prize: Prize) -> str:
    return f"(No story: {activity.id} does not make a believable bad ending for {prize.label}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale storyworld with squawk, ecologic, and a bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, prize = rng.choice(sorted(combos))
    name = args.name or rng.choice(["Cal", "June", "Milo", "Pip"])
    helper = args.helper or rng.choice(["Big Blue", "Old Beak", "Captain Caw"])
    return StoryParams(place=place, activity=activity, prize=prize, name=name, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-sized tall tale about a {f["helper"].label if f["helper"].label else "bird"} who wants to be ecologic and keeps shouting "squawk."',
        f"Tell a story set at {f['place'].name} where {f['child'].id} watches a giant bird try to fix the marsh and make a bad mess.",
        "Write a simple tall tale with a big voice, a wet place, and a bad ending that proves the plan went wrong.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = f["child"]
    helper: Entity = f["helper"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Who is the story mainly about at {place.name}?",
            answer=f"The story is about {child.id} and the big squawking bird, but {child.id} is the child who watches what happens.",
        ),
        QAItem(
            question=f"What did {helper.id} want to be?",
            answer=f"{helper.id} wanted to be ecologic, which means trying to help the place stay clean and healthy.",
        ),
        QAItem(
            question=f"Why was the ending bad?",
            answer=f"The ending was bad because the huge squawk scared the fish, muddied the bank, and left the pond looking worse instead of better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ecologic mean?",
            answer="Ecologic means helping nature stay healthy, clean, and safe for plants and animals.",
        ),
        QAItem(
            question="What is a squawk?",
            answer="A squawk is a loud bird noise, sharp and squeaky like a trumpet with a feather on it.",
        ),
        QAItem(
            question="Why can loud noises scare animals?",
            answer="Loud noises can startle animals because their ears notice the sound quickly and they may think danger is near.",
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
    lines.append("== (3) World-knowledge questions ==")
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
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="marsh", activity="squawk", prize="sign", name="Cal", helper="Big Blue"),
    StoryParams(place="riverbend", activity="ecologic", prize="reeds", name="June", helper="Old Beak"),
]


def generate(params: StoryParams) -> StorySample:
    world = ecologic_story(PLACES[params.place], params.name, params.helper)
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
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.water:
            lines.append(asp.fact("water", pid))
        if p.reeds:
            lines.append(asp.fact("reeds_place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
        for r in sorted(a.spread):
            lines.append(asp.fact("spreads_to", aid, r))
    for pr in PRIZES.values():
        lines.append(asp.fact("prize", pr.id))
        lines.append(asp.fact("worn_on", pr.id, pr.region))
        if pr.plural:
            lines.append(asp.fact("plural", pr.id))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, h))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
bad_ending(P,A) :- affords(P,A), activity(A), spreads_to(A,R), worn_on(Prize,R), prize(Prize).
compatible(P,A,G) :- affords(P,A), gear(G), helps(G,A), covers(G,R), worn_on(Prize,R), prize(Prize).
valid_story(P,A,Prize) :- bad_ending(P,A), prize(Prize).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
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


def build_sample(args: argparse.Namespace, rng: random.Random) -> StorySample:
    params = resolve_params(args, rng)
    sample = generate(params)
    sample.params.seed = params.seed
    return sample


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, activity, prize) combos:\n")
        for c in combos:
            print("  ", c)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
