#!/usr/bin/env python3
"""
storyworlds/worlds/culprit_spay_gypped_reconciliation_pirate_tale.py
=====================================================================

A small pirate tale storyworld about a hidden culprit, a crew that feels
gypped, and a reconciliation at the end.

The seed words are woven into the world:
- culprit
- spay
- gypped

The story keeps to a classic pirate-tale shape:
setup -> loss and accusation -> reveal -> reconciliation.
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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "captain"}
        male = {"boy", "father", "man", "pirate", "mate", "sailor"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Harbor:
    place: str = "the harbor"
    aboard: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class ObjectDef:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class ActionDef:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class GearDef:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]


class World:
    def __init__(self, setting: Harbor) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.type == "gear"]


SETTINGS = {
    "ship": Harbor(place="the pirate ship", aboard=True, affords={"spay", "search", "sail"}),
    "dock": Harbor(place="the dock", aboard=False, affords={"spay", "search"}),
}

ACTIONS = {
    "spay": ActionDef(
        id="spay",
        verb="spay the sail line",
        gerund="spaying the sail line",
        rush="rush to the rigging",
        mess="tangled",
        soil="tangled and torn",
        zone={"hands"},
        keyword="spay",
        tags={"rope", "sail"},
    ),
    "search": ActionDef(
        id="search",
        verb="search for the missing chest",
        gerund="searching for the missing chest",
        rush="dash below deck",
        mess="shaken",
        soil="shaken and upset",
        zone={"heart"},
        keyword="culprit",
        tags={"chest", "treasure"},
    ),
    "sail": ActionDef(
        id="sail",
        verb="sail into the moonlit bay",
        gerund="sailing into the moonlit bay",
        rush="run up the deck",
        mess="sprayed",
        soil="sprayed with salt",
        zone={"face", "hands"},
        keyword="gypped",
        tags={"sea", "moon"},
    ),
}

OBJECTS = {
    "chest": ObjectDef(
        id="chest",
        label="treasure chest",
        phrase="a little treasure chest with a brass latch",
        region="hands",
    ),
    "map": ObjectDef(
        id="map",
        label="map",
        phrase="a torn map with an X in red ink",
        region="hands",
    ),
    "hat": ObjectDef(
        id="hat",
        label="hat",
        phrase="a jaunty pirate hat",
        region="head",
    ),
}

GEAR = [
    GearDef(
        id="gloves",
        label="sail gloves",
        prep="put on sail gloves",
        tail="slipped on the sail gloves",
        covers={"hands"},
        guards={"tangled"},
    ),
    GearDef(
        id="bandana",
        label="a salt bandana",
        prep="tie on a salt bandana",
        tail="tied on the salt bandana",
        covers={"face"},
        guards={"sprayed"},
    ),
]

GIRL_NAMES = ["Mira", "Nell", "Tess", "Ivy"]
BOY_NAMES = ["Finn", "Bram", "Joss", "Kai"]
TRAITS = ["brave", "cheery", "stubborn", "lively"]


@dataclass
class StoryParams:
    place: str
    action: str
    item: str
    name: str
    gender: str
    parent: str = "captain"
    trait: str = "brave"
    seed: Optional[int] = None


ASP_RULES = r"""
at_risk(A,O) :- action(A), zone(A,R), object(O), region(O,R).
has_fix(A,O) :- at_risk(A,O), gear(G), covers(G,R), zone(A,R), guards(G,M), mess_of(A,M).
valid_story(P,A,O,G) :- place(P), affords(P,A), at_risk(A,O), has_fix(A,O), gender_uses(G,O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.aboard:
            lines.append(asp.fact("aboard", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("region", oid, o.region))
        lines.append(asp.fact("gender_uses", "girl", oid))
        lines.append(asp.fact("gender_uses", "boy", oid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIONS[act_id]
            for oid, obj in OBJECTS.items():
                if obj.region in act.zone:
                    if any(obj.region in g.covers and act.mess in g.guards for g in GEAR):
                        combos.append((place, act_id, oid))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.action is None or c[1] == args.action)
              and (args.item is None or c[2] == args.item)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, item = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, item=item, name=name, gender=gender, parent=args.parent or "captain", trait=trait)


def predict_soil(world: World, actor: Entity, action: ActionDef, item: Entity) -> bool:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    return bool(sim.get(item.id).memes.get("gypped", 0) >= THRESHOLD)


def _do_action(world: World, actor: Entity, action: ActionDef, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        raise StoryError("The chosen action does not fit the setting.")
    world.zone = set(action.zone)
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1
    actor.memes["trouble"] = actor.memes.get("trouble", 0.0) + 1


def tell(setting: Harbor, action: ActionDef, obj_def: ObjectDef, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    parent = world.add(Entity(id="Captain", kind="character", type=parent_type, label="the captain"))
    culprit = world.add(Entity(id="Culprit", kind="character", type="pirate", label="the culprit"))
    obj = world.add(Entity(id=obj_def.id, type=obj_def.label, label=obj_def.label, phrase=obj_def.phrase, owner=hero.id, caretaker=parent.id))

    world.say(f"{hero.id} was a little {trait} pirate who loved the salty air and the creak of the rigging.")
    world.say(f"One day, {hero.id}'s {parent.label} gave {hero.id} {obj.phrase}, and {hero.id} treasured it.")
    world.para()
    world.say(f"Then {hero.id} and the crew went to {setting.place} to {action.verb}.")
    world.say(f"But something went wrong, and the crew felt gypped when the treasure chest was gone.")
    world.say(f"Everyone looked for the culprit, while the wind rattled the mast like a warning.")

    # Reveal and reconciliation
    world.para()
    culprit.memes["guilt"] = 1.0
    world.say(f"At last, the culprit came back with the chest and whispered that {culprit.id} had only hidden it to keep it safe from a splashy spill.")
    world.say(f"{hero.id} stared for a moment, then sighed and nodded.")
    world.say(f'"We were gypped by a fright, not a thief," {hero.id} said. "Let us make peace and share the deck."')
    world.say(f"The crew forgave the culprit, and the ship felt calm again.")
    world.say(f"By sunset, {hero.id} was smiling beside {obj.label}, and even the culprit was helping tie the lines.")

    world.facts.update(hero=hero, parent=parent, culprit=culprit, obj=obj, action=action, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    action = f["action"]
    obj = f["obj"]
    return [
        f'Write a short pirate tale for a child that includes the words "culprit", "spay", and "gypped".',
        f"Tell a gentle pirate story where {hero.id} wants to {action.verb} but the crew thinks they were gypped.",
        f"Write a story about a culprit on a ship, a missing {obj.label}, and a reconciliation at sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    culprit = f["culprit"]
    obj = f["obj"]
    action = f["action"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little pirate who loved the sea and the treasure chest.",
        ),
        QAItem(
            question=f"What did the crew think at first when the {obj.label} was missing?",
            answer=f"They thought they had been gypped, because the {obj.label} was gone and nobody knew where it had gone.",
        ),
        QAItem(
            question=f"Who turned out to be the culprit?",
            answer=f"The culprit was {culprit.id}, who had hidden the {obj.label} to keep it safe.",
        ),
        QAItem(
            question=f"How did the story end after the problem was solved?",
            answer=f"{hero.id} forgave the culprit, and the crew made peace in a reconciliation by the deck.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a culprit?",
            answer="A culprit is the person or creature who is responsible for a wrong action or a problem.",
        ),
        QAItem(
            question="What does gypped mean?",
            answer="Gypped means someone feels cheated, tricked, or unfairly left out of something they expected.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people who were upset make peace and become friendly again.",
        ),
        QAItem(
            question="What is a spay?",
            answer="In this storyworld, Spay is a pirate ship name and a word that helps give the tale its salty flavor.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    parts = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts.append(f"{e.id} ({e.type}) meters={meters} memes={memes}")
    return "\n".join(parts)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIONS[params.action],
        OBJECTS[params.item],
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--item", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["captain"])
    ap.add_argument("--name")
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        for place, action, item in sorted(valid_combos()):
            params = StoryParams(place=place, action=action, item=item, name="Mira", gender="girl")
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
