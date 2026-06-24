#!/usr/bin/env python3
"""
storyworlds/worlds/sticker_curiosity_reconciliation_space_adventure.py
======================================================================

A tiny space-adventure storyworld about a curious child, a beloved sticker, a
mistake in a small ship, and a reconciliation that repairs both the object and
the feelings.

Premise built from the seed:
- A child on a little space voyage has a favorite sticker.
- Curiosity leads them to peel, place, or test the sticker in the wrong place.
- The sticker loses its special spot, the child worries, and a helper helps fix
  things through apology, cleaning, and a new shared choice.
- The ending proves the sticker is back in a meaningful place and the feelings
  have cooled into reconciliation.

This script follows the Storyweavers storyworld contract:
- standalone stdlib script
- imports storyworlds/results.py eagerly
- lazy ASP helper import
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- default run, -n, --all, --seed, --trace, --qa, --json, --asp, --verify, --show-asp
- physical meters and emotional memes
- inline ASP twin plus Python reasonableness gate
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    placed_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)
    plural: bool = False

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
    place: str = "the tiny starship"
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectSpec:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class GearSpec:
    id: str
    label: str
    prep: str
    tail: str
    fixes: set[str]
    places: set[str]
    plural: bool = False


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    locus: str
    keyword: str
    tags: set[str] = field(default_factory=set)


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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _r_smudge(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.meters.get("curiosity", 0.0) < THRESHOLD:
            continue
        for obj in world.entities.values():
            if obj.worn_by != actor.id:
                continue
            if obj.placed_in != ACTIVITY_LOCUS.get(world.facts.get("activity", ""),""):
                continue
            sig = ("smudge", actor.id, obj.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            obj.meters["dirty"] = obj.meters.get("dirty", 0.0) + 1
            obj.meters["moved"] = obj.meters.get("moved", 0.0) + 1
            out.append(f"The sticker lost its neat spot and picked up a smudge.")
    return out


def _r_worry(world: World) -> list[str]:
    out = []
    for obj in world.entities.values():
        if obj.meters.get("dirty", 0.0) < THRESHOLD:
            continue
        sig = ("worry", obj.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        owner = world.get(obj.owner) if obj.owner else None
        if owner:
            owner.memes["worry"] = owner.memes.get("worry", 0.0) + 1
            out.append(f"{owner.id} felt a pinch in {owner.pronoun('possessive')} chest.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("apology", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("helped", 0.0) < THRESHOLD:
            continue
        sig = ("reconcile", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["peace"] = actor.memes.get("peace", 0.0) + 1
        actor.memes["worry"] = 0.0
        out.append(f"The room grew calm again.")
    return out


RULES = [_r_smudge, _r_worry, _r_reconcile]


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_sents: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                all_sents.extend(sents)
    if narrate:
        for s in all_sents:
            world.say(s)
    return all_sents


def clue_of(activity: Activity) -> str:
    return {
        "sticker": "the little sticker seemed to hold a whole galaxy in its shine",
        "panel": "the ship's panel hummed like a patient wall of stars",
        "window": "the window made the dark outside look endless and exciting",
        "map": "the map glowed with tiny dots and bright route lines",
    }[activity.keyword]


def predict_mess(world: World, actor: Entity, activity: Activity, sticker_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["curiosity"] = 1.0
    sim.get(sticker_id).placed_in = activity.locus
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    sticker = sim.get(sticker_id)
    return {"dirty": sticker.meters.get("dirty", 0.0) >= THRESHOLD}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["curiosity"] = actor.meters.get("curiosity", 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    sticker = next((e for e in world.entities.values() if e.type == "sticker"), None)
    if sticker:
        sticker.placed_in = activity.locus
    propagate(world, narrate=narrate)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for obj_id, obj in OBJECTS.items():
                if obj.location in {act.locus, "any"}:
                    combos.append((place, act_id, obj_id))
    return combos


def explain_rejection(activity: Activity, obj: ObjectSpec) -> str:
    return (
        f"(No story: {activity.gerund} doesn't naturally affect a sticker at {obj.location}. "
        f"Try the sticker on a panel, map, or window where curiosity can move it.)"
    )


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("locus", aid, act.locus))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for t in sorted(act.tags):
            lines.append(asp.fact("tag", aid, t))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("placed_on", oid, obj.location))
        if obj.plural:
            lines.append(asp.fact("plural", oid))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for m in sorted(gear.fixes):
            lines.append(asp.fact("fixes", gid, m))
        for p in sorted(gear.places):
            lines.append(asp.fact("covers_place", gid, p))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A,O) :- locus(A,L), placed_on(O,L).
can_fix(A,O) :- at_risk(A,O), gear(G), fixes(G,M), mess_of(A,M), covers_place(G,L), locus(A,L).
valid_story(P,A,O) :- affords(P,A), can_fix(A,O).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    p = set(valid_combos())
    a = set(asp_valid_combos())
    if p == a:
        print(f"OK: ASP gate matches valid_combos() ({len(p)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(p - a))
    print("only in asp:", sorted(a - p))
    return 1


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.traits[0]} astronaut aboard the tiny starship.")


def love_sticker(world: World, hero: Entity, sticker: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(f"{hero.id} loved {sticker.label} because {clue_of(ACTIVITIES['scan'])}.")


def setup_scene(world: World, hero: Entity, parent: Entity, sticker: Entity, activity: Activity) -> None:
    world.say(f"On a quiet drift through space, {hero.id} and {parent.id} floated past the control panel.")
    world.say(f"{hero.id} kept a {sticker.label} tucked near the console, and it shone like a tiny moon.")
    world.say(f"{hero.id} wanted to {activity.verb}, and curiosity buzzed in {hero.pronoun('possessive')} hands.")


def warn(world: World, parent: Entity, hero: Entity, sticker: Entity, activity: Activity) -> bool:
    if not predict_mess(world, hero, activity, sticker.id)["dirty"]:
        return False
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f'"Careful," {parent.id} said. "That sticker could get messy if you move it there."')
    return True


def mistake(world: World, hero: Entity, sticker: Entity, activity: Activity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    sticker.worn_by = hero.id
    sticker.placed_in = activity.locus
    world.say(f"But {hero.id} peeked closer and tried to {activity.rush}.")
    propagate(world, narrate=True)


def apologize(world: World, hero: Entity, parent: Entity) -> None:
    hero.memes["apology"] = hero.memes.get("apology", 0.0) + 1
    world.say(f"{hero.id} looked down and said sorry to {parent.id} and to the little sticker.")
    world.say(f"{parent.id} took a slow breath and listened.")
    hero.memes["helped"] = hero.memes.get("helped", 0.0) + 1


def fix(world: World, hero: Entity, parent: Entity, sticker: Entity, gear: GearSpec) -> None:
    sticker.meters["dirty"] = 0.0
    sticker.placed_in = gear.tail
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    world.say(f"They used {gear.label} to clean the mark and press the sticker back into a safe place.")
    world.say(f"{gear.tail.capitalize()}, and the sticker was bright again.")
    world.say(f"{hero.id} and {parent.id} smiled at each other, feeling steady and kind again.")


def tell(setting: Setting, activity: Activity, obj_spec: ObjectSpec, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["curious", "gentle"]))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, traits=["calm"]))
    sticker = world.add(Entity(
        id="sticker", type="sticker", label="favorite sticker", phrase="a tiny star sticker",
        owner=hero.id, caretaker=parent.id, placed_in=obj_spec.location,
    ))
    sticker.meters["sparkle"] = 1.0

    introduce(world, hero)
    love_sticker(world, hero, sticker)
    world.para()
    setup_scene(world, hero, parent, sticker, activity)
    warn(world, parent, hero, sticker, activity)
    mistake(world, hero, sticker, activity)
    world.para()
    apologize(world, hero, parent)
    fix(world, hero, parent, sticker, GEAR["glue_pad"])
    world.facts.update(hero=hero, parent=parent, sticker=sticker, activity=activity, obj=obj_spec)
    return world


SETTINGS = {
    "ship": Setting(place="the tiny starship", indoor=True, affords={"scan", "open", "twist"}),
    "dock": Setting(place="the moon dock", indoor=False, affords={"scan", "open"}),
    "cabin": Setting(place="the small cabin", indoor=True, affords={"scan", "arrange"}),
}

ACTIVITIES = {
    "scan": Activity(id="scan", verb="scan the panel", gerund="scanning the panel", rush="reach for the glowing panel", mess="smudged", soil="smudged", locus="panel", keyword="panel", tags={"panel", "curiosity"}),
    "open": Activity(id="open", verb="open the window", gerund="opening the window", rush="lean toward the window latch", mess="dusty", soil="dusty", locus="window", keyword="window", tags={"window", "curiosity"}),
    "twist": Activity(id="twist", verb="twist the map", gerund="twisting the map", rush="pull at the map edge", mess="creased", soil="creased", locus="map", keyword="map", tags={"map", "curiosity"}),
    "arrange": Activity(id="arrange", verb="arrange the stickers", gerund="arranging stickers", rush="shift the sticker cluster", mess="smudged", soil="smudged", locus="panel", keyword="sticker", tags={"sticker", "reconciliation"}),
}

OBJECTS = {
    "sticker": ObjectSpec(label="favorite sticker", phrase="a tiny star sticker", type="sticker", location="panel"),
    "windowsticker": ObjectSpec(label="window sticker", phrase="a bright comet sticker", type="sticker", location="window"),
    "mapsticker": ObjectSpec(label="map sticker", phrase="a little planet sticker", type="sticker", location="map"),
}

GEAR = {
    "glue_pad": GearSpec(id="glue_pad", label="a glue pad", prep="press the sticker flat", tail="the glue pad held it in place", fixes={"smudged", "dusty", "creased"}, places={"panel", "window", "map"}),
}

CURATED = [
    ("ship", "scan", "sticker", "Nova", "girl", "mother"),
    ("dock", "open", "windowsticker", "Pip", "boy", "father"),
    ("cabin", "arrange", "mapsticker", "Mira", "girl", "mother"),
]

GIRL_NAMES = ["Nova", "Mira", "Luna", "Tia", "Ada", "Zia"]
BOY_NAMES = ["Pip", "Kai", "Rex", "Tom", "Leo", "Milo"]


def valid_story_specs() -> list[tuple[str, str, str]]:
    out = []
    for p, s in SETTINGS.items():
        for a in s.affords:
            act = ACTIVITIES[a]
            for o, obj in OBJECTS.items():
                if obj.location == act.locus:
                    out.append((p, a, o))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.activity and args.obj:
        act = ACTIVITIES[args.activity]
        obj = OBJECTS[args.obj]
        if obj.location != act.locus:
            raise StoryError(explain_rejection(act, obj))
    combos = [c for c in valid_story_specs()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.obj is None or c[2] == args.obj)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, obj_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, activity=activity, obj=obj_id, name=name, gender=gender, parent=parent)


@dataclass
class StoryParams:
    place: str
    activity: str
    obj: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short space adventure about a curious child and a sticker that gets moved by mistake.',
        f"Tell a gentle story where {f['hero'].id} wants to {f['activity'].verb} but worries about {f['obj'].label}.",
        f"Write a child-friendly reconciliation story aboard {world.setting.place} that includes a sticker.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, sticker, activity = f["hero"], f["parent"], f["sticker"], f["activity"]
    return [
        QAItem(question=f"Who is the story about?", answer=f"It is about {hero.id}, a curious little astronaut, and {parent.id}, who helps make things right."),
        QAItem(question=f"What did {hero.id} want to do?", answer=f"{hero.id} wanted to {activity.verb}, but curiosity made the moment messy."),
        QAItem(question=f"What did they fix together?", answer=f"They fixed the sticker and put it back in a safe place, so it could shine again."),
        QAItem(question=f"How did the story end?", answer=f"It ended with apology, help, and a calm feeling between {hero.id} and {parent.id}."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a sticker?", answer="A sticker is a small picture with sticky backing that can be pressed onto a surface."),
        QAItem(question="What does curiosity mean?", answer="Curiosity means wanting to look, ask, and learn about something new."),
        QAItem(question="What is reconciliation?", answer="Reconciliation is when people fix a hurt feeling and become friendly again."),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.placed_in:
            bits.append(f"placed_in={e.placed_in}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"- {p}" for p in sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure sticker storyworld with curiosity and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--obj", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], OBJECTS[params.obj], params.name, params.gender, params.parent)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def asp_valid_stories() -> list[tuple]:
    return asp_valid_combos()


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:")
        for t in triples:
            print(" ", t)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        for p, a, o, name, gender, parent in CURATED:
            samples.append(generate(StoryParams(place=p, activity=a, obj=o, name=name, gender=gender, parent=parent)))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
