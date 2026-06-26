#!/usr/bin/env python3
"""
storyworlds/worlds/fire_advise_dialogue_happy_ending_animal_story.py
====================================================================

A small animal-story simulation about fire, advice, dialogue, and a happy ending.

Seed tale shape:
- A young animal wants to get close to a fire.
- A worried adult gives clear advice in dialogue.
- The child tests the idea, hears why it matters, and chooses the safer way.
- The ending proves the change: warmth, treats, and a calm, happy scene.

The world is deliberately compact so the prose is state-driven rather than a frozen
template. The available variations come from the species, names, setting, snack,
and the specific fire-related activity.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {
            "cub": {"subject": "they", "object": "them", "possessive": "their"},
            "fox": {"subject": "he", "object": "him", "possessive": "his"},
            "rabbit": {"subject": "she", "object": "her", "possessive": "her"},
            "bear": {"subject": "they", "object": "them", "possessive": "their"},
            "mouse": {"subject": "she", "object": "her", "possessive": "her"},
            "deer": {"subject": "he", "object": "him", "possessive": "his"},
            "owl": {"subject": "she", "object": "her", "possessive": "her"},
            "badger": {"subject": "he", "object": "him", "possessive": "his"},
        }
        default = {"subject": "it", "object": "it", "possessive": "its"}
        return mapping.get(self.type, default)[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Snack:
    label: str
    phrase: str
    type: str
    region: str = "hands"
    plural: bool = False


@dataclass
class Safety:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.weather: str = ""
        self.facts: dict = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _safe_distance_ok(world: World, actor: Entity) -> bool:
    return actor.meters.get("distance", 0.0) >= 2.0


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("curious", 0.0) < THRESHOLD:
            continue
        if _safe_distance_ok(world, actor):
            continue
        sig = ("heat", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["warmth"] = actor.meters.get("warmth", 0.0) + 1
        actor.memes["uneasy"] = actor.memes.get("uneasy", 0.0) + 1
        out.append(f"The fire felt too hot that close.")
    return out


CAUSAL_RULES = []


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


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The room was cozy, and a little fireplace crackled nearby."
    if activity.id == "campfire":
        return f"{setting.place.capitalize()} smelled like wood smoke and pine."
    return f"{setting.place.capitalize()} waited quietly under the open sky."


def predict_harm(world: World, actor: Entity, activity: Activity) -> bool:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return sim.entities[actor.id].meters.get("burn_risk", 0.0) >= THRESHOLD


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters["curious"] = actor.meters.get("curious", 0.0) + 1
    actor.meters["burn_risk"] = actor.meters.get("burn_risk", 0.0) + 1
    actor.memes["want"] = actor.memes.get("want", 0.0) + 1
    if narrate:
        propagate(world, narrate=True)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "small")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved bright places and warm nights."
    )


def loves_fire(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["delight"] = hero.memes.get("delight", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, and the glow made {hero.pronoun('possessive')} eyes shine."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: Activity) -> None:
    day = "One evening, "
    world.say(
        f"{day}{hero.id} and {hero.pronoun('possessive')} {parent.label} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} paws were already itching to rush closer.")


def advise(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    hero.memes["advised"] = hero.memes.get("advised", 0.0) + 1
    world.say(
        f'"Please stay back," {parent.id} said. "The fire can bite your fur. We can still enjoy it safely."'
    )
    world.say(
        f'"How?" asked {hero.id}. "{parent.id}", \"we can sit on the log, and I can advise you on the safe way.\"'
    )


def step_too_close(world: World, hero: Entity, activity: Activity) -> None:
    hero.meters["distance"] = 1.0
    hero.meters["burn_risk"] = hero.meters.get("burn_risk", 0.0) + 1
    world.say(f"{hero.id} took one curious step too close.")
    world.say(f'"Ow, that feels hot," {hero.id} whispered, backing away.')


def resolve(world: World, parent: Entity, hero: Entity, activity: Activity, snack: Entity, safety: Safety) -> None:
    hero.meters["distance"] = 3.0
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f'"Let\'s use {safety.label} and stay near the log," {parent.id} said kindly.'
    )
    world.say(
        f'{hero.id} nodded, and {hero.pronoun("possessive")} worry melted into a smile.'
    )
    world.say(
        f"They {safety.tail}. Soon {hero.id} was {activity.gerund}, {snack.phrase} in {hero.pronoun('possessive')} paws, and the night felt safe and warm."
    )


def tell(
    setting: Setting,
    activity: Activity,
    snack_cfg: Snack,
    hero_name: str = "Pip",
    hero_type: str = "fox",
    parent_type: str = "rabbit",
    trait: Optional[str] = None,
) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=hero_type,
            traits=["little"] + ([trait] if trait else ["brave"]),
        )
    )
    parent = world.add(Entity(id="Guide", kind="character", type=parent_type, label="parent"))
    snack = world.add(
        Entity(
            id="snack",
            type=snack_cfg.type,
            label=snack_cfg.label,
            phrase=snack_cfg.phrase,
            owner=hero.id,
            caretaker=parent.id,
            plural=snack_cfg.plural,
        )
    )

    introduce(world, hero)
    loves_fire(world, hero, activity)
    arrive(world, hero, parent, activity)
    wants(world, hero, activity)
    advise(world, parent, hero, activity)
    step_too_close(world, hero, activity)
    world.para()
    safety = SAFETY[activity.id]
    resolve(world, parent, hero, activity, snack, safety)

    world.facts.update(
        hero=hero,
        parent=parent,
        snack=snack,
        activity=activity,
        setting=setting,
        safety=safety,
    )
    return world


SETTINGS = {
    "campsite": Setting(place="the campsite", indoor=False, affords={"campfire"}),
    "backyard": Setting(place="the backyard", indoor=False, affords={"campfire"}),
    "cabin": Setting(place="the cabin", indoor=True, affords={"hearth"}),
}

ACTIVITIES = {
    "campfire": Activity(
        id="campfire",
        verb="toast marshmallows by the fire",
        gerund="toasting marshmallows by the fire",
        rush="run closer to the flames",
        risk="the fire might singe fur and make paws too hot",
        weather="cool",
        zone={"hands", "face"},
        keyword="fire",
        tags={"fire", "warm", "smoke"},
    ),
    "hearth": Activity(
        id="hearth",
        verb="warm up by the hearth",
        gerund="warming up by the hearth",
        rush="lean toward the hearth",
        risk="the sparks might jump",
        weather="cool",
        zone={"hands", "face"},
        keyword="fire",
        tags={"fire", "warm"},
    ),
}

SNACKS = {
    "marshmallows": Snack(label="marshmallows", phrase="sweet marshmallows", type="marshmallows", plural=True),
    "apple_slices": Snack(label="apple slices", phrase="warm apple slices", type="apple_slices", plural=True),
    "corncakes": Snack(label="corncakes", phrase="little corncakes", type="corncakes", plural=True),
}

SAFETY = {
    "campfire": Safety(
        id="log_sit",
        label="the safe log seat",
        prep="sit on the log and hold the stick out straight",
        tail="sat on the log and held the stick safely away from the flames",
        guards={"fire"},
    ),
    "hearth": Safety(
        id="rug_sit",
        label="the rug by the hearth",
        prep="sit on the rug and keep a cozy cushion between us and the sparks",
        tail="sat on the rug and watched the fire from a safe spot",
        guards={"fire"},
    ),
}

GIRLISH = ["Pip", "Mina", "Luna", "Tilly", "Nora"]
BOYISH = ["Finn", "Toby", "Otis", "Bram", "Rex"]
NEUTRAL = ["Bea", "Scout", "Clover", "Junie", "Moss"]
TRAITS = ["curious", "playful", "brave", "sly", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for snack_id in SNACKS:
                combos.append((place, act_id, snack_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    snack: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, snack = f["hero"], f["parent"], f["activity"], f["snack"]
    return [
        f'Write a short animal story for a young child that uses the word "{act.keyword}" and includes a kind warning about fire.',
        f"Tell a gentle dialogue story where {hero.id}, a {hero.type}, wants to {act.verb} but {parent.id} advises {hero.pronoun('object')} to stay safe.",
        f"Write a happy-ending story about a {hero.pronoun('subject')} who learns to listen when someone advises them near a fire and then enjoys {snack.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, snack, safety = f["hero"], f["parent"], f["activity"], f["snack"], f["safety"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do near the fire?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Who advised {hero.id} to stay safe?",
            answer=f"{parent.id} advised {hero.id} to stay back and use the safe seat.",
        ),
        QAItem(
            question=f"What did {hero.id} enjoy at the end of the story?",
            answer=f"{hero.id} enjoyed {snack.phrase} while staying in {safety.label}.",
        ),
        QAItem(
            question=f"Why did {hero.id} move away from the flames?",
            answer=f"{hero.id} moved away because the fire felt too hot that close and the advice was good.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why should an animal child stay away from fire?",
            answer="Fire can be very hot, and staying a little farther away helps keep fur and paws safe.",
        ),
        QAItem(
            question="What does it mean to advise someone?",
            answer="To advise someone means to give helpful advice about what to do.",
        ),
        QAItem(
            question="Why do people sit near a campfire instead of inside it?",
            answer="People sit near a campfire because they want warmth and light without touching the flames.",
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
        lines.append(f"  {e.id:8} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="campsite", activity="campfire", snack="marshmallows", name="Pip", gender="boy", parent="mother", trait="curious"),
    StoryParams(place="backyard", activity="campfire", snack="apple_slices", name="Mina", gender="girl", parent="father", trait="playful"),
    StoryParams(place="cabin", activity="hearth", snack="corncakes", name="Moss", gender="boy", parent="mother", trait="gentle"),
]


def explain_rejection(activity: Activity) -> str:
    return f"(No story: the chosen fire scene does not make sense here, because {activity.risk}.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, a.keyword))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for nid, n in SNACKS.items():
        lines.append(asp.fact("snack", nid))
        if n.plural:
            lines.append(asp.fact("plural_snack", nid))
    for sid, s in SAFETY.items():
        lines.append(asp.fact("safety", sid))
        for g in sorted(s.guards):
            lines.append(asp.fact("guards", sid, g))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Act, Snack) :- affords(Place, Act), activity(Act), snack(Snack).
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
    ap = argparse.ArgumentParser(
        description="Animal story world: fire, advice, dialogue, and a happy ending."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gender", choices=["girl", "boy", "neutral"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.snack is None or c[2] == args.snack)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, snack = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy", "neutral"])
    if args.name:
        name = args.name
    else:
        name = rng.choice(GIRLISH if gender == "girl" else BOYISH if gender == "boy" else NEUTRAL)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, snack=snack, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], SNACKS[params.snack],
                 params.name, params.gender if params.gender != "neutral" else "fox",
                 params.parent, params.trait)
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible (place, activity, snack) combos:\n")
        for place, act, snack in combos:
            print(f"  {place:9} {act:10} {snack}")
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
