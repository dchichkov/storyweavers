#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/egocentric_ground_large_bad_ending_humor_adventure.py
==============================================================================================================================

A tiny adventure storyworld about an egocentric explorer, a big piece of ground,
and a joke that goes sideways.

Seed-shaped premise:
- egocentric: the hero thinks the whole adventure should revolve around them
- ground: the action happens on and under the ground
- large: the world includes something oversized enough to matter
- bad ending: the plan does not fully succeed
- humor: the failure is funny, not grim
- adventure: the story feels like a small quest

The world model tracks:
- physical meters: distance, size, dirt, wobble, stuckness, etc.
- emotional memes: pride, worry, teamwork, embarrassment, laughter, etc.

The stories are intentionally small and constraint-driven:
- a hero wants to claim some large ground-feature as their own
- the world pushes back through a simple hazard
- a helper or tool can improve things, but the ending still goes wrong in a
  funny, child-friendly way
- the ending image proves what changed
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

# ---------------------------------------------------------------------------
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0

PLACES = {
    "field": {
        "label": "the field",
        "ground": "soft earth",
        "hazards": {"burrow", "mud"},
        "large_things": {"hill", "mound"},
    },
    "garden": {
        "label": "the garden",
        "ground": "crumbly soil",
        "hazards": {"burrow", "slip"},
        "large_things": {"root", "mound"},
    },
    "playground": {
        "label": "the playground",
        "ground": "packed sand",
        "hazards": {"trench", "slip"},
        "large_things": {"slide", "drum"},
    },
    "shore": {
        "label": "the shore",
        "ground": "wet sand",
        "hazards": {"hole", "slip"},
        "large_things": {"shell", "driftwood"},
    },
}

OBJECTS = {
    "treasure_map": {
        "label": "treasure map",
        "phrase": "a wrinkled treasure map",
        "region": "hands",
        "risk": {"mud", "wet"},
        "fix": "map_tube",
        "bad_end": "got soggy and stuck to a boot",
    },
    "crown": {
        "label": "paper crown",
        "phrase": "a bright paper crown",
        "region": "head",
        "risk": {"wind", "wet"},
        "fix": "hood",
        "bad_end": "tilted sideways and looked silly",
    },
    "lantern": {
        "label": "lantern",
        "phrase": "a little tin lantern",
        "region": "hands",
        "risk": {"mud", "drop"},
        "fix": "strap",
        "bad_end": "went out with a soft puff",
    },
    "sandwich": {
        "label": "picnic sandwich",
        "phrase": "a big picnic sandwich",
        "region": "hands",
        "risk": {"mud", "wet"},
        "fix": "cloth_wrap",
        "bad_end": "became a crunchy mystery",
    },
}

TOOLS = [
    {"id": "map_tube", "label": "a map tube", "covers": {"hands"}, "guards": {"mud", "wet"},
     "prep": "put the map in a tube first", "tail": "packed the map in a tube"},
    {"id": "hood", "label": "a rain hood", "covers": {"head"}, "guards": {"wind", "wet"},
     "prep": "pull on a rain hood first", "tail": "pulled on the rain hood"},
    {"id": "strap", "label": "a neck strap", "covers": {"hands"}, "guards": {"drop"},
     "prep": "tie the lantern to a neck strap", "tail": "tied the lantern to a neck strap"},
    {"id": "cloth_wrap", "label": "a cloth wrap", "covers": {"hands"}, "guards": {"mud", "wet"},
     "prep": "wrap the sandwich in cloth", "tail": "wrapped the sandwich in cloth"},
]

ACTIVITIES = {
    "dig": {
        "verb": "dig at the ground",
        "gerund": "digging at the ground",
        "rush": "dig faster",
        "hazard": "mud",
        "damage": "muddy",
        "zone": {"hands", "feet"},
        "keyword": "ground",
        "tags": {"ground", "mud"},
    },
    "crawl": {
        "verb": "crawl under the hill",
        "gerund": "crawling under the hill",
        "rush": "crawl under the dirt",
        "hazard": "mud",
        "damage": "muddy",
        "zone": {"hands", "knees"},
        "keyword": "large",
        "tags": {"ground", "large"},
    },
    "climb": {
        "verb": "climb the large mound",
        "gerund": "climbing the mound",
        "rush": "scramble up the mound",
        "hazard": "slip",
        "damage": "dusty",
        "zone": {"hands", "feet"},
        "keyword": "large",
        "tags": {"large", "ground"},
    },
    "dash": {
        "verb": "dash across the ground",
        "gerund": "dashing across the ground",
        "rush": "dash even faster",
        "hazard": "drop",
        "damage": "scuffed",
        "zone": {"hands", "feet"},
        "keyword": "egocentric",
        "tags": {"ground", "egocentric"},
    },
}

NAMES = ["Milo", "Pia", "Toby", "Nina", "Jules", "Ivy", "Rory", "Bea"]
TRAITS = ["egocentric", "bold", "curious", "loud", "proud", "reckless"]
HELPERS = ["a kind friend", "a patient sibling", "a grinning neighbor", "a small guide dog"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    region: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class StoryParams:
    place: str
    activity: str
    object: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place_id: str):
        self.place_id = place_id
        self.place = PLACES[place_id]
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.hazard: str = ""

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

    def copy(self) -> "World":
        c = World(self.place_id)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.zone = set(self.zone)
        c.hazard = self.hazard
        return c


def choose_tool(activity: dict, obj: dict) -> Optional[dict]:
    for tool in TOOLS:
        if obj["region"] in tool["covers"] and activity["hazard"] in tool["guards"]:
            return tool
    return None


def risk_applies(activity: dict, obj: dict) -> bool:
    return activity["hazard"] in obj["risk"]


def _r_dirty(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if actor.meters.get(world.hazard, 0.0) < THRESHOLD:
                continue
            sig = ("dirty", actor.id, item.id, world.hazard)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters[world.hazard] = item.meters.get(world.hazard, 0.0) + 1.0
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {world.hazard} and dirty.")
    return out


def _r_stuck(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("bold", 0.0) < THRESHOLD:
            continue
        if actor.meters.get("dirty", 0.0) < THRESHOLD:
            continue
        sig = ("stuck", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["embarrassment"] = actor.memes.get("embarrassment", 0.0) + 1.0
        out.append("__stuck__")
    return out


def _r_laugh(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.memes.get("embarrassment", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("laughter", 0.0) >= THRESHOLD:
            continue
        actor.memes["laughter"] = 1.0
        out.append("The whole scene turned funny instead of scary.")
    return out


CAUSAL_RULES = [
    _r_dirty,
    _r_stuck,
    _r_laugh,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(s for s in lines if s != "__stuck__")
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def predict_problem(world: World, actor: Entity, activity: dict, obj: Entity) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {
        "dirty": bool(sim.get(obj.id).meters.get("dirty", 0.0) >= THRESHOLD),
        "stuck": bool(sim.get(actor.id).memes.get("embarrassment", 0.0) >= THRESHOLD),
    }


def do_activity(world: World, actor: Entity, activity: dict, narrate: bool = True) -> None:
    world.zone = set(activity["zone"])
    world.hazard = activity["hazard"]
    actor.meters[activity["hazard"]] = actor.meters.get(activity["hazard"], 0.0) + 1.0
    actor.memes["bold"] = actor.memes.get("bold", 0.0) + 1.0
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} with a very big idea.")
    world.say(f"{hero.pronoun().capitalize()} was {hero.memes.get('trait_word', 'egocentric')} enough to think the whole {world.place['label']} should cheer for {hero.id}.")


def setup(world: World, hero: Entity, helper: Entity, obj: Entity, activity: dict) -> None:
    world.say(f"On a bright day, {hero.id} found {obj.phrase} near {world.place['label']}.")
    world.say(f"{hero.id} wanted to {activity['verb']} and act like the captain of the adventure.")
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(f"Even {helper.label} had to follow {hero.id}'s very loud plan.")


def warning(world: World, hero: Entity, helper: Entity, obj: Entity, activity: dict) -> bool:
    pred = predict_problem(world, hero, activity, obj)
    if not pred["dirty"]:
        return False
    world.facts["predicted_dirty"] = True
    world.say(f'"If you {activity["verb"]}, your {obj.label} will get {activity["hazard"]}," {helper.label} said.')
    return True


def boast(world: World, hero: Entity, activity: dict) -> None:
    hero.memes["egocentric"] = hero.memes.get("egocentric", 0.0) + 1.0
    world.say(f'"Easy," {hero.id} said. "{hero.id} can handle the whole {activity["keyword"]} adventure alone."')


def slip_and_spot(world: World, hero: Entity, obj: Entity, activity: dict) -> None:
    world.say(f"{hero.id} rushed ahead and tried to {activity['rush']}.")
    world.say(f"That was the moment {obj.label} got {activity['bad_end']}.")


def offer_tool(world: World, helper: Entity, hero: Entity, obj: Entity, activity: dict) -> Optional[dict]:
    tool = choose_tool(activity, OBJECTS[world.facts["obj_id"]])
    if tool is None:
        return None
    tool_ent = world.add(Entity(
        id=tool["id"],
        kind="thing",
        type="tool",
        label=tool["label"],
        protective=True,
        covers=set(tool["covers"]),
        owner=hero.id,
        worn_by=hero.id,
    ))
    if predict_problem(world, hero, activity, obj)["dirty"]:
        tool_ent.worn_by = None
        del world.entities[tool_ent.id]
        return None
    world.say(f"Then {helper.label} suggested they {tool['prep']}.")
    return tool


def bad_ending(world: World, hero: Entity, obj: Entity, helper: Entity, activity: dict) -> None:
    hero.memes["embarrassment"] = hero.memes.get("embarrassment", 0.0) + 1.0
    hero.memes["laughter"] = hero.memes.get("laughter", 0.0) + 1.0
    world.say(
        f"{hero.id} ended up covered in {world.hazard} with a face that said, "
        f'"Well, that was not the grand victory I expected."'
    )
    world.say(
        f"{helper.label} laughed so hard they had to sit on a rock, and {hero.id} laughed too, "
        f"because the {obj.label} was ruined but the story was funny."
    )


def tell(place_id: str, activity_id: str, obj_id: str, hero_name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(place_id)
    activity = ACTIVITIES[activity_id]
    obj_cfg = OBJECTS[obj_id]
    helper = world.add(Entity(id="helper", kind="character", type="friend", label=helper_kind))
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, label=hero_name))
    obj = world.add(Entity(
        id="object",
        type="thing",
        label=obj_cfg["label"],
        phrase=obj_cfg["phrase"],
        region=obj_cfg["region"],
        owner=hero.id,
        caretaker=helper.id,
    ))
    hero.memes["trait_word"] = trait
    world.facts.update(
        hero=hero,
        helper=helper,
        obj=obj,
        obj_id=obj_id,
        activity=activity,
        place=world.place,
    )

    intro(world, hero)
    world.para()
    setup(world, hero, helper, obj, activity)
    warning(world, hero, helper, obj, activity)
    boast(world, hero, activity)
    slip_and_spot(world, hero, obj, activity)
    world.para()
    if offer_tool(world, helper, hero, obj, activity) is not None:
        world.say(f"They tried again, but the ground was too tricky and the whole plan still went wrong.")
    bad_ending(world, hero, obj, helper, activity)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["obj"]
    act = f["activity"]
    return [
        f'Write a short adventure story for a child about {hero.id}, an egocentric explorer, and a {obj.label}.',
        f"Tell a humorous story where {hero.id} wants to {act['verb']} but the ground makes the plan go badly.",
        f"Write a small adventure with a bad ending, a funny mishap, and a large ground feature.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    obj = f["obj"]
    act = f["activity"]
    place = f["place"]["label"]
    return [
        QAItem(
            question=f"Who wanted to be the captain of the adventure at {place}?",
            answer=f"{hero.id} wanted everything to revolve around {hero.id}, so {hero.id} acted like the captain.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do with the {obj.label}?",
            answer=f"{hero.id} wanted to {act['verb']}.",
        ),
        QAItem(
            question=f"Why did {helper.label} worry about the plan?",
            answer=f"{helper.label} worried that the {obj.label} would get {act['hazard']} if {hero.id} rushed ahead.",
        ),
        QAItem(
            question=f"How did the story end for {hero.id} and the {obj.label}?",
            answer=f"It ended badly but funny: the {obj.label} got {obj_cfg_text(obj.id, act)}, and everyone laughed anyway.",
        ),
    ]


def obj_cfg_text(obj_id: str, act: dict) -> str:
    return OBJECTS[obj_id]["bad_end"]


WORLD_KNOWLEDGE = {
    "ground": [
        QAItem(
            question="What is ground?",
            answer="Ground is the surface under your feet, like dirt, sand, grass, or stone.",
        )
    ],
    "large": [
        QAItem(
            question="What does large mean?",
            answer="Large means big enough to take up a lot of space.",
        )
    ],
    "egocentric": [
        QAItem(
            question="What does egocentric mean?",
            answer="Egocentric means a person thinks too much about themselves and forgets to share the spotlight.",
        )
    ],
    "mud": [
        QAItem(
            question="What is mud?",
            answer="Mud is wet dirt that can stick to shoes, hands, and clothes.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"]["tags"])
    out = []
    for tag in ["egocentric", "ground", "large", "mud"]:
        if tag in tags:
            out.extend(WORLD_KNOWLEDGE[tag])
    return out


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,O) :- hazard_of(A,H), risk_of(O,H).
fixable(A,O) :- risk(A,O), tool(T), guards(T,H), hazard_of(A,H), covers(T,R), region_of(O,R).
valid(Place,A,O) :- place(Place), activity(A), object(O), risk(A,O), fixable(A,O), affords(Place,A).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for h in sorted(p["hazards"]):
            lines.append(asp.fact("hazard", pid, h))
        for a in sorted(p["large_things"]):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("hazard_of", aid, a["hazard"]))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("region_of", oid, o["region"]))
        for r in sorted(o["risk"]):
            lines.append(asp.fact("risk_of", oid, r))
    for t in TOOLS:
        lines.append(asp.fact("tool", t["id"]))
        for g in sorted(t["guards"]):
            lines.append(asp.fact("guards", t["id"], g))
        for c in sorted(t["covers"]):
            lines.append(asp.fact("covers", t["id"], c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for act_id in place["large_things"] | place["hazards"]:
            if act_id not in ACTIVITIES:
                continue
            act = ACTIVITIES[act_id]
            for obj_id, obj in OBJECTS.items():
                if risk_applies(act, obj) and choose_tool(act, obj) is not None:
                    combos.append((place_id, act_id, obj_id))
    return sorted(set(combos))


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
    ap = argparse.ArgumentParser(description="An egocentric ground adventure with a humorous bad ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [(p, a, o) for p, a, o in valid_combos()
              if (args.place is None or p == args.place)
              and (args.activity is None or a == args.activity)
              and (args.object_ is None or o == args.object_)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, act, obj = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES)
    helper = args.helper or rng.choice(HELPERS)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=act, object=obj, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.place, params.activity, params.object, params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="field", activity="dig", object="treasure_map", name="Milo", gender="boy", helper="a grinning neighbor", trait="egocentric"),
    StoryParams(place="garden", activity="crawl", object="crown", name="Pia", gender="girl", helper="a patient sibling", trait="proud"),
    StoryParams(place="playground", activity="climb", object="lantern", name="Toby", gender="boy", helper="a kind friend", trait="reckless"),
    StoryParams(place="shore", activity="dash", object="sandwich", name="Ivy", gender="girl", helper="a small guide dog", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:\n")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
