#!/usr/bin/env python3
"""
Standalone storyworld: a curious trooper and a humorous animal helper.

This world tells small, child-facing Animal-Story-style tales about a trooper
animal who follows a curiosity, gets into a mild scrape, and finds a funny,
kind resolution. The state model tracks physical meters and emotional memes so
the prose is driven by simulated events rather than fixed templates.
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

ANIMALS = {
    "puppy": {
        "type": "puppy",
        "sound": "woof",
        "plural": False,
        "pronouns": {"subject": "he", "object": "him", "possessive": "his"},
    },
    "kitten": {
        "type": "kitten",
        "sound": "meow",
        "plural": False,
        "pronouns": {"subject": "she", "object": "her", "possessive": "her"},
    },
    "duckling": {
        "type": "duckling",
        "sound": "quack",
        "plural": False,
        "pronouns": {"subject": "they", "object": "them", "possessive": "their"},
    },
    "bear": {
        "type": "bear",
        "sound": "grr",
        "plural": False,
        "pronouns": {"subject": "he", "object": "him", "possessive": "his"},
    },
    "fox": {
        "type": "fox",
        "sound": "yip",
        "plural": False,
        "pronouns": {"subject": "she", "object": "her", "possessive": "her"},
    },
}

PLACES = {
    "nest": {"place": "the nest", "setting": "outdoors", "affords": {"peek", "hide"}},
    "meadow": {"place": "the meadow", "setting": "outdoors", "affords": {"peek", "chase"}},
    "barn": {"place": "the barn", "setting": "indoors", "affords": {"peek", "stack"}},
    "pond": {"place": "the pond", "setting": "outdoors", "affords": {"splash", "peek"}},
}

ACTIVITIES = {
    "peek": {
        "id": "peek",
        "verb": "peek behind the tall grass",
        "gerund": "peeking behind tall grass",
        "rush": "dash into the grass",
        "mess": "scruffy",
        "soil": "all dusty and scruffy",
        "zone": {"nose", "paws"},
        "keyword": "peek",
        "humor": "the grass tickled their nose",
        "tags": {"curiosity", "humor"},
    },
    "splash": {
        "id": "splash",
        "verb": "splash in the pond",
        "gerund": "splashing in the pond",
        "rush": "hop into the water",
        "mess": "wet",
        "soil": "dripping wet",
        "zone": {"paws", "belly"},
        "keyword": "splash",
        "humor": "the water made funny plip-plops",
        "tags": {"curiosity", "humor", "water"},
    },
    "chase": {
        "id": "chase",
        "verb": "chase a fluttering leaf",
        "gerund": "chasing fluttering leaves",
        "rush": "race after the leaf",
        "mess": "wind-tossed",
        "soil": "wind-tousled",
        "zone": {"paws", "tail"},
        "keyword": "leaf",
        "humor": "the leaf kept zipping away like it had little shoes",
        "tags": {"curiosity", "humor"},
    },
    "stack": {
        "id": "stack",
        "verb": "stack hay bales",
        "gerund": "stacking hay bales",
        "rush": "clamber onto the hay",
        "mess": "dusty",
        "soil": "dusty and golden",
        "zone": {"paws", "fur"},
        "keyword": "hay",
        "humor": "the hay kept wobbling like a sleepy tower",
        "tags": {"curiosity", "humor"},
    },
}

TREASURES = {
    "scarf": {
        "label": "scarf",
        "phrase": "a bright red scarf",
        "region": "neck",
        "plural": False,
    },
    "boots": {
        "label": "boots",
        "phrase": "shiny little boots",
        "region": "paws",
        "plural": True,
    },
    "hat": {
        "label": "hat",
        "phrase": "a tiny blue hat",
        "region": "head",
        "plural": False,
    },
    "vest": {
        "label": "vest",
        "phrase": "a neat yellow vest",
        "region": "torso",
        "plural": False,
    },
}

GEAR = [
    {
        "id": "rain_wrap",
        "label": "a rain wrap",
        "covers": {"torso", "neck"},
        "guards": {"wet"},
        "prep": "put on a rain wrap first",
        "tail": "went back for the rain wrap",
        "plural": False,
    },
    {
        "id": "paw_boots",
        "label": "paw boots",
        "covers": {"paws"},
        "guards": {"wet", "dusty", "scruffy"},
        "prep": "slip on paw boots",
        "tail": "trotted off with the paw boots",
        "plural": True,
    },
    {
        "id": "dust_cloak",
        "label": "a dust cloak",
        "covers": {"torso", "neck", "head"},
        "guards": {"dusty", "scruffy", "wind-tossed"},
        "prep": "wear a dust cloak",
        "tail": "came back with the dust cloak",
        "plural": False,
    },
]

NAMES = ["Toby", "Milo", "Nina", "Pip", "Dot", "Roo", "Buddy", "Luna", "Moss", "Sunny"]


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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if case == "subject":
            return self.meters.get("pronoun_subject", "it")
        if case == "object":
            return self.meters.get("pronoun_object", "it")
        return self.meters.get("pronoun_possessive", "its")

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    terrain: str
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
    keyword: str
    humor: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class GearDef:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    setting: str
    activity: str
    treasure: str
    animal: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
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


def pronounce_fields(ent: Entity, animal_type: str) -> None:
    p = ANIMALS[animal_type]["pronouns"]
    ent.meters["pronoun_subject"] = p["subject"]
    ent.meters["pronoun_object"] = p["object"]
    ent.meters["pronoun_possessive"] = p["possessive"]


def _r_soil(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mess in ("wet", "scruffy", "dusty", "wind-tossed"):
            if actor.meters.get(mess, 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0) + 1
                out.append(f"{actor.id}'s {item.label} got {mess}.")
    return out


def _r_workload(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.meters["workload"] = caretaker.meters.get("workload", 0) + 1
        out.append(f"That would mean more work for {caretaker.id}.")
    return out


CAUSAL_RULES = [_r_soil, _r_workload]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def prize_at_risk(activity: Activity, treasure: Treasure) -> bool:
    return treasure.region in activity.zone


def select_gear(activity: Activity, treasure: Treasure) -> Optional[GearDef]:
    for gear in GEAR:
        if activity.mess in gear["guards"] and treasure.region in gear["covers"]:
            return GearDef(**gear)
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, treasure_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{**vars(v), "meters": dict(v.meters), "memes": dict(v.memes), "covers": set(v.covers)}) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    a = sim.get(actor.id)
    a.meters[activity.mess] = a.meters.get(activity.mess, 0) + 1
    sim.zone = set(activity.zone)
    propagate(sim, narrate=False)
    treasure = sim.entities.get(treasure_id)
    return {"soiled": bool(treasure and treasure.meters.get("dirty", 0) >= THRESHOLD),
            "workload": sum(e.meters.get("workload", 0) for e in sim.characters())}


def activity_detail(activity: Activity) -> str:
    return activity.humor


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.terrain == "indoors":
        return f"Inside {setting.place}, the floor was smooth and the air felt quiet."
    return f"{setting.place.capitalize()} looked lively, and the {setting.terrain} fit {activity.gerund} perfectly."


def tell(setting: Setting, activity: Activity, treasure_cfg: Treasure, hero_name: str, animal: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=animal, label="trooper"))
    pronounce_fields(hero, animal)
    parent = world.add(Entity(id="Caretaker", kind="character", type="adult", label="the helper"))
    pronounce_fields(parent, "duckling")
    treasure = world.add(Entity(
        id="treasure", type=treasure_cfg.label, label=treasure_cfg.label,
        phrase=treasure_cfg.phrase, owner=hero.id, caretaker=parent.id,
        region=treasure_cfg.region, plural=treasure_cfg.plural,
    ))

    hero.memes["curiosity"] = 1
    hero.memes["humor"] = 1

    world.say(f"{hero.id} was a little trooper {hero.type} who loved surprises and silly moments.")
    world.say(f"{hero.pronoun().capitalize()} was full of Curiosity, and the day always felt brighter when {hero.pronoun()} noticed something new.")
    world.say(f"{hero.id} wore {hero.pronoun('possessive')} {treasure.label} and liked how it jingled when {hero.pronoun()} walked.")
    world.para()
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} helper went to {setting.place}.")
    world.say(setting_detail(setting, activity))
    world.say(f"{hero.id} wanted to {activity.verb}, because {activity_detail(activity)}.")
    pred = predict_mess(world, hero, activity, treasure.id)
    if pred["soiled"]:
        world.say(f'"If you do that, your {treasure.label} will get {activity.soil}," {parent.id} said.')
        world.say(f"{hero.id} still wiggled with curiosity and tried to {activity.rush}.")
    else:
        world.say(f"{parent.id} smiled, because this little adventure looked harmless.")
    world.zone = set(activity.zone)
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    propagate(world, narrate=True)
    if pred["soiled"]:
        hero.memes["humor"] = hero.memes.get("humor", 0) + 1
        world.say(f"{hero.id} made a funny face and laughed at the mess, which made the helper laugh too.")
        gear_def = select_gear(activity, treasure)
        if gear_def is None:
            raise StoryError("No reasonable gear can protect the treasure in this story.")
        gear = world.add(Entity(id=gear_def.id, kind="thing", type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers), plural=gear_def.plural, owner=hero.id, caretaker=parent.id))
        gear.worn_by = hero.id
        if predict_mess(world, hero, activity, treasure.id)["soiled"]:
            del world.entities[gear.id]
            raise StoryError("The selected gear did not actually solve the mess.")
        world.para()
        world.say(f'Then {parent.id} had a funny idea: "{gear_def.prep}."')
        world.say(f"{hero.id} grinned, because that sounded like a smart and silly plan.")
        world.say(f"They {gear_def.tail}, and this time {hero.id} could {activity.verb} without ruining {hero.pronoun('possessive')} {treasure.label}.")
        world.say(f"At the end, {hero.id} was {activity.gerund}, and {hero.pronoun('possessive')} {treasure.label} stayed clean.")
        hero.memes["curiosity"] += 1
        hero.memes["humor"] += 1
    else:
        world.para()
        world.say(f"Nothing got ruined, so {hero.id} and {parent.id} just laughed at the funny way the day turned out.")
        world.say(f"{hero.id} ended up {activity.gerund}, with a happy grin and a bright little twinkle in {hero.pronoun('possessive')} eyes.")

    world.facts.update(hero=hero, parent=parent, treasure=treasure, activity=activity, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, treasure = f["hero"], f["parent"], f["activity"], f["treasure"]
    return [
        f'Write a short Animal Story about a trooper {hero.type} named {hero.id} who is driven by Curiosity and Humor.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but {hero.pronoun('possessive')} helper worries about {treasure.phrase}.",
        f"Write a child-friendly story with a funny turn and a safe solution at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, treasure = f["hero"], f["parent"], f["activity"], f["treasure"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little trooper {hero.type} full of curiosity and humor.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {f['setting'].place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did the helper worry?",
            answer=f"The helper worried because {hero.pronoun('possessive')} {treasure.label} could get {act.soil}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} {act.gerund} and the {treasure.label} staying clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to look, learn, and ask questions about something new.",
        ),
        QAItem(
            question="What is humor?",
            answer="Humor is the feeling of something funny that makes people smile or laugh.",
        ),
        QAItem(
            question="What does a trooper mean in a story like this?",
            answer="A trooper is someone who keeps going bravely, even when the day gets a little messy.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a curious trooper animal with a funny, safe turn.")
    ap.add_argument("--setting", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--name", choices=NAMES)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, s in PLACES.items():
        for aid in s["affords"]:
            act = ACTIVITIES[aid]
            for tid, t in TREASURES.items():
                if prize_at_risk(act, Treasure(**t)) and select_gear(act, Treasure(**t)):
                    combos.append((sid, aid, tid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.activity is None or c[1] == args.activity)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, activity, treasure = rng.choice(sorted(combos))
    animal = args.animal or rng.choice(list(ANIMALS))
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting=setting, activity=activity, treasure=treasure, animal=animal, name=name)


def generate(params: StoryParams) -> StorySample:
    setting = Setting(place=PLACES[params.setting]["place"], terrain=PLACES[params.setting]["setting"], affords=set(PLACES[params.setting]["affords"]))
    activity = Activity(**ACTIVITIES[params.activity])
    treasure = Treasure(**TREASURES[params.treasure])
    world = tell(setting, activity, treasure, params.name, params.animal)
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
    StoryParams(setting="meadow", activity="peek", treasure="hat", animal="puppy", name="Toby"),
    StoryParams(setting="pond", activity="splash", treasure="scarf", animal="duckling", name="Pip"),
    StoryParams(setting="barn", activity="stack", treasure="vest", animal="bear", name="Sunny"),
]


ASP_RULES = r"""
prize_at_risk(A, T) :- splashes(A, R), worn_on(T, R).
protects(G, A, T) :- gear(G), prize_at_risk(A, T), mess_of(A, M), guards(G, M), covers(G, R), worn_on(T, R).
has_fix(A, T) :- protects(_, A, T).
valid(Setting, A, T) :- affords(Setting, A), prize_at_risk(A, T), has_fix(A, T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in PLACES.items():
        for a in sorted(s["affords"]):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a["mess"]))
        for r in sorted(a["zone"]):
            lines.append(asp.fact("splashes", aid, r))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("worn_on", tid, t["region"]))
    for g in GEAR:
        lines.append(asp.fact("gear", g["id"]))
        for m in sorted(g["guards"]):
            lines.append(asp.fact("guards", g["id"], m))
        for c in sorted(g["covers"]):
            lines.append(asp.fact("covers", g["id"], c))
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


def explain_rejection(activity: Activity, treasure: Treasure) -> str:
    return f"(No story: {activity.gerund} would not reasonably ruin a {treasure.label} in this world.)"


def explain_invalid_combo() -> str:
    return "(No valid combination matches the given options.)"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combinations:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []

    if args.all:
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen = set()
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
