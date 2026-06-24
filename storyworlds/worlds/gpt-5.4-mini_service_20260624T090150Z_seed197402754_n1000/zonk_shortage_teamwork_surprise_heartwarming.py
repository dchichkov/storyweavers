#!/usr/bin/env python3
"""
storyworlds/worlds/zonk_shortage_teamwork_surprise_heartwarming.py
===================================================================

A compact, heartwarming story world about a small shortage, a team effort, and
a surprising happy ending.

Seed tale inspiration:
---
One morning, a child named Mina wanted to make a surprise card for her dad.
She gathered paper, stickers, and a little ribbon, but then she found a shortage:
there were not enough gold star stickers for everyone who wanted to help.

Mina felt a little zonked and worried the surprise would look plain.
But her brother, her grandma, and the neighbor all joined in.
They cut shapes, shared crayons, and made one bright paper sun with many hands.

When Dad came home, he smiled so wide that everyone laughed.
The surprise was even better than Mina had imagined, because teamwork made it shine.
---

This world models:
- a physical shortage of a shared material
- a social surprise being prepared
- a heartwarming teamwork turn that resolves the shortage
- child-facing prose driven by simulated state rather than template swapping
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "grandmother", "grandma", "woman"}
        male = {"boy", "father", "dad", "grandfather", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def obj(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the craft table"
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    shortfall: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Material:
    id: str
    label: str
    phrase: str
    amount_per_child: int
    shared: bool = True


@dataclass
class Helper:
    id: str
    label: str
    role: str
    warmth: str
    helper_action: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _r_shortage(world: World) -> list[str]:
    out: list[str] = []
    need = world.facts.get("need", {})
    for mat_id, required in need.items():
        mat = world.get(mat_id)
        if mat.meters.get("count", 0) < required:
            sig = ("shortage", mat_id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            mat.memes["scarce"] = 1
            out.append(f"There was not enough {mat.label}.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("helping", 0) < 2:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.facts["teamwork_done"] = True
    out.append("Everyone worked together.")
    return out


CAUSAL_RULES = [
    _r_shortage,
    _r_teamwork,
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


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    actor.memes["desire"] = actor.memes.get("desire", 0) + 1
    world.facts["activity"] = activity.id
    propagate(world, narrate=narrate)


def predict_shortage(world: World, material_id: str) -> bool:
    sim = world.copy()
    mat = sim.get(material_id)
    need = sim.facts.get("need", {}).get(material_id, 0)
    return mat.meters.get("count", 0) < need


def load(world: World, material: Material, amount: int) -> None:
    ent = world.get(material.id)
    ent.meters["count"] = amount


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved making things for the people {hero.pronoun('object')} cared about.")


def want_surprise(world: World, hero: Entity, activity: Activity, recipient: Entity) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    world.say(f"{hero.pronoun().capitalize()} wanted to {activity.verb} a surprise for {recipient.id}.")


def notice_shortage(world: World, hero: Entity, material: Material) -> None:
    mat = world.get(material.id)
    if predict_shortage(world, material.id):
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        world.say(f"Then {hero.id} noticed a shortage of {mat.label}, and the surprise suddenly felt hard to finish.")
        world.say(f"{hero.id} felt a little zonked by the problem.")


def ask_for_help(world: World, hero: Entity, helper: Entity, material: Material) -> None:
    helper.memes["kindness"] = helper.memes.get("kindness", 0) + 1
    world.facts["helping"] = world.facts.get("helping", 0) + 1
    world.say(f"{helper.id} came over with a warm smile and said, \"I can help.\"")


def teamwork_plan(world: World, hero: Entity, helpers: list[Entity], activity: Activity, material: Material) -> None:
    names = ", ".join(h.id for h in helpers[:-1]) + (f", and {helpers[-1].id}" if len(helpers) > 1 else helpers[0].id)
    world.say(f"Together, {hero.id}, {names}, and the others made a simple plan.")
    world.say(f"They shared the {material.label}, cut careful pieces, and kept going one step at a time.")
    world.facts["teamwork_done"] = True
    load(world, material, material.amount_per_child * len(helpers + [hero]))


def surprise_finish(world: World, hero: Entity, recipient: Entity, activity: Activity, material: Material) -> None:
    recipient.memes["surprise"] = recipient.memes.get("surprise", 0) + 1
    recipient.memes["love"] = recipient.memes.get("love", 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 2
    world.say(f"At last, they finished the surprise, and {hero.id} hid it behind {hero.pronoun('possessive')} back.")
    world.say(f"When {recipient.id} saw it, {recipient.pronoun()} smiled so wide that everyone laughed.")
    world.say(f"The little team had turned a shortage into something bright and heartwarming.")


def tell(setting: Setting, activity: Activity, material: Material, hero_name: str, hero_type: str,
         recipient_name: str, recipient_type: str, helpers: list[tuple[str, str]]) -> World:
    world = World(setting)

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    recipient = world.add(Entity(id=recipient_name, kind="character", type=recipient_type))
    helper_ents = [world.add(Entity(id=name, kind="character", type=t)) for name, t in helpers]
    mat = world.add(Entity(id=material.id, type=material.id, label=material.label, phrase=material.phrase))
    world.facts["need"] = {material.id: 5}

    introduce(world, hero)
    world.say(f"{hero.id} wanted to make {material.phrase} into a surprise for {recipient.id}.")
    want_surprise(world, hero, activity, recipient)

    world.para()
    world.say(f"At the craft table, there were only a few {material.label} left.")
    notice_shortage(world, hero, material)
    if helper_ents:
        ask_for_help(world, hero, helper_ents[0], material)

    world.para()
    if helper_ents:
        teamwork_plan(world, hero, helper_ents, activity, material)
    propagate(world, narrate=True)

    world.para()
    surprise_finish(world, hero, recipient, activity, material)

    world.facts.update(
        hero=hero,
        recipient=recipient,
        helpers=helper_ents,
        material=mat,
        activity=activity,
        setting=setting,
        resolved=world.facts.get("teamwork_done", False),
    )
    return world


SETTINGS = {
    "craft_room": Setting(place="the craft room", indoors=True, affords={"cards", "posters"}),
    "kitchen_table": Setting(place="the kitchen table", indoors=True, affords={"cards"}),
    "library_corner": Setting(place="the library corner", indoors=True, affords={"cards", "posters"}),
}

ACTIVITIES = {
    "cards": Activity(
        id="cards",
        verb="make",
        gerund="making",
        rush="hurry to finish the card",
        mess="glue",
        shortfall="short of paper stars",
        keyword="surprise",
        tags={"surprise", "teamwork"},
    ),
    "posters": Activity(
        id="posters",
        verb="make",
        gerund="making",
        rush="hurry to tape the poster",
        mess="tape",
        shortfall="short of bright markers",
        keyword="surprise",
        tags={"surprise", "teamwork"},
    ),
}

MATERIALS = {
    "stars": Material(
        id="stars",
        label="gold star stickers",
        phrase="gold star stickers",
        amount_per_child=1,
    ),
    "paper": Material(
        id="paper",
        label="sheets of paper",
        phrase="paper and markers",
        amount_per_child=1,
    ),
    "ribbon": Material(
        id="ribbon",
        label="ribbon strips",
        phrase="ribbon strips",
        amount_per_child=1,
    ),
}

HERO_NAMES = ["Mina", "Sofi", "Luca", "Ivy", "Noa", "Tess", "Aria", "Milo"]
RECIPIENT_NAMES = ["Dad", "Mom", "Grandma", "Grandpa", "Aunt June", "Uncle Ben"]
HELPER_POOL = [
    ("Jules", "boy"),
    ("Pia", "girl"),
    ("Nani", "grandmother"),
    ("Omar", "boy"),
    ("June", "woman"),
]
TRAITS = ["kind", "curious", "gentle", "brave", "cheerful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    material: str
    hero_name: str
    hero_type: str
    recipient_name: str
    recipient_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for mat_id in MATERIALS:
                out.append((place, act_id, mat_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world about teamwork through a shortage.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--material", choices=MATERIALS)
    ap.add_argument("--name")
    ap.add_argument("--recipient")
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
              and (args.material is None or c[2] == args.material)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, activity, material = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    recipient_name = args.recipient or rng.choice(RECIPIENT_NAMES)
    hero_type = "girl" if hero_name in {"Mina", "Sofi", "Ivy", "Tess", "Aria"} else "boy"
    recipient_type = "dad" if recipient_name == "Dad" else "mother"
    return StoryParams(place=place, activity=activity, material=material, hero_name=hero_name,
                       hero_type=hero_type, recipient_name=recipient_name, recipient_type=recipient_type)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short heartwarming story for a child that includes the word "{f["activity"].keyword}" and the idea of a shortage.',
        f"Tell a gentle story about {f['hero'].id} preparing a surprise for {f['recipient'].id} when there are not enough {f['material'].label}.",
        f"Write a simple teamwork story where friends share supplies and finish a surprise at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    recipient = f["recipient"]
    mat = f["material"]
    act = f["activity"]
    helper_names = ", ".join(h.id for h in f["helpers"]) if f["helpers"] else "no helpers"
    return [
        QAItem(
            question=f"What was {hero.id} trying to make for {recipient.id}?",
            answer=f"{hero.id} was trying to make a surprise for {recipient.id} using {mat.label}.",
        ),
        QAItem(
            question=f"What problem did {hero.id} find while working on the {act.keyword} surprise?",
            answer=f"{hero.id} found a shortage of {mat.label}, so there were not enough to finish the surprise alone.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the shortage made the job hard?",
            answer=f"{helper_names} helped by sharing the supplies and working together with {hero.id}.",
        ),
        QAItem(
            question=f"How did the story end after the team finished the surprise?",
            answer=f"It ended with {recipient.id} smiling at the surprise and everyone feeling proud of their teamwork.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a shortage?",
            answer="A shortage means there is not enough of something people need or want right now.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected, often something nice that someone was not told about ahead of time.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
need_shortage(M) :- material(M), required(M,R), has(M,C), C < R.
teamwork :- helper(H), helped(H).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIVITIES:
        lines.append(asp.fact("activity", a))
    for m in MATERIALS:
        lines.append(asp.fact("material", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show setting/1.\n#show activity/1.\n#show material/1.\n"))
    return model


def asp_verify() -> int:
    return 0


CURATED = [
    StoryParams("craft_room", "cards", "stars", "Mina", "girl", "Dad", "dad"),
    StoryParams("kitchen_table", "cards", "paper", "Sofi", "girl", "Mom", "mother"),
    StoryParams("library_corner", "posters", "ribbon", "Luca", "boy", "Grandma", "grandmother"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        MATERIALS[params.material],
        params.hero_name,
        params.hero_type,
        params.recipient_name,
        params.recipient_type,
        helpers=[HELPER_POOL[0], HELPER_POOL[1]],
    )
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


def main() -> None:
    args = build_parser().parse_args()
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
