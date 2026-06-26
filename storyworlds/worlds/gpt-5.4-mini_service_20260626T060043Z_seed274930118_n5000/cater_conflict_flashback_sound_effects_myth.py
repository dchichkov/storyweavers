#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cater_conflict_flashback_sound_effects_myth.py
==============================================================================================================

A small mythic storyworld about a child of the valley who must cater a sacred
feast, faces conflict, remembers a flashback, and resolves the day with sound
and offering.
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "king"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"


@dataclass
class Setting:
    place: str
    afford: str
    mood: str


@dataclass
class Offering:
    id: str
    label: str
    phrase: str
    region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Ritual:
    id: str
    verb: str
    gerund: str
    sound: str
    risk: str
    weather: str
    cue: str


@dataclass
class Charm:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.flashback_used = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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
        clone.flashback_used = self.flashback_used
        return clone


def _resolve_article(text: str) -> str:
    return "an" if text[:1].lower() in "aeiou" else "a"


def _sound(text: str) -> str:
    return f"{text}."


def _predict(world: World, actor: Entity, ritual: Ritual, offering_id: str) -> dict:
    sim = world.copy()
    _do_ritual(sim, sim.get(actor.id), ritual, narrate=False)
    off = sim.get(offering_id)
    return {"soiled": bool(off.meters.get("ash", 0.0) >= THRESHOLD), "tension": actor.memes.get("conflict", 0.0)}


def _do_ritual(world: World, actor: Entity, ritual: Ritual, narrate: bool = True) -> None:
    actor.meters["ash"] = actor.meters.get("ash", 0.0) + 1
    actor.memes["duty"] = actor.memes.get("duty", 0.0) + 1
    world.zone = {"hands", "torso"}
    if narrate:
        world.say(_sound(f"{ritual.sound} the work began"))


def _soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("ash", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            sig = ("soak", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["ash"] = item.meters.get("ash", 0.0) + 1
            out.append(f"{actor.id}'s {item.label} took on a little ash.")
    return out


def _conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("slighted", 0.0) >= THRESHOLD and actor.memes.get("fear", 0.0) >= THRESHOLD:
            if ("conflict", actor.id) in world.fired:
                continue
            world.fired.add(("conflict", actor.id))
            actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
            return ["__conflict__"]
    return []


def _fixpoint(world: World, narrate: bool = True) -> None:
    changed = True
    while changed:
        changed = False
        for rule in (_soak, _conflict):
            sents = rule(world)
            if sents:
                changed = True
                if narrate:
                    for s in sents:
                        if s != "__conflict__":
                            world.say(s)


SETTINGS = {
    "temple": Setting(place="the hill temple", afford="feast", mood="stone-and-echo"),
    "grove": Setting(place="the moon grove", afford="feast", mood="leaf-and-silver"),
    "shore": Setting(place="the salt shore shrine", afford="feast", mood="wave-and-wind"),
}

RITUALS = {
    "feast": Ritual(
        id="feast",
        verb="cater the feast",
        gerund="catering the feast",
        sound="clatter",
        risk="ash and spice",
        weather="clear",
        cue="cater",
    )
}

OFFERINGS = {
    "bread": Offering("bread", "bread", "warm bread", "hands"),
    "milk": Offering("milk", "milk", "sweet milk", "torso"),
    "flowers": Offering("flowers", "flowers", "white flowers", "hands"),
}

CHARMS = [
    Charm("shawl", "a woven shawl", {"torso"}, {"ash"}, "wrap on a woven shawl", "walked back under the shawl"),
    Charm("gloves", "ash-cloth gloves", {"hands"}, {"ash"}, "pull on ash-cloth gloves", "went back for the gloves"),
    Charm("apron", "a cook's apron", {"torso"}, {"ash"}, "tie on a cook's apron", "came back with the apron"),
]

GIRL_NAMES = ["Mira", "Nara", "Ila", "Sera", "Tala"]
BOY_NAMES = ["Kian", "Ravi", "Aren", "Milo", "Bram"]
TRAITS = ["brave", "gentle", "curious", "steady", "hopeful"]


@dataclass
class StoryParams:
    place: str
    ritual: str
    offering: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for ritual_id in [setting.afford]:
            for off_id, off in OFFERINGS.items():
                if off.region in {"hands", "torso"}:
                    out.append((place, ritual_id, off_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic cater-conflict-flashback storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--offering", choices=OFFERINGS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.ritual is None or c[1] == args.ritual)
              and (args.offering is None or c[2] == args.offering)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, ritual, offering = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, ritual=ritual, offering=offering, name=name, gender=gender, parent=parent, trait=trait)


def tell(setting: Setting, ritual: Ritual, offering_cfg: Offering, hero_name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label=f"the {parent_type}"))
    offering = world.add(Entity(id="offering", type=offering_cfg.id, label=offering_cfg.label, phrase=offering_cfg.phrase, caretaker=parent.id, region=offering_cfg.region))
    charm = None

    hero.memes["love"] = 1
    hero.memes["duty"] = 1
    world.say(f"{hero.id} was a {trait} child of {world.setting.place}, and {hero.pronoun('possessive')} heart beat for sacred work.")
    world.say(f"{hero.id} loved to {_resolve_article(ritual.verb)} {ritual.verb}, because the temple lamps answered with a soft glow.")

    world.para()
    world.say(f"One evening, {hero.id} and {hero.pronoun('possessive')} {parent_type} went to {world.setting.place}.")
    world.say(f"The air hummed with promise, and {hero.id} wanted to {ritual.verb} at once.")
    pred = _predict(world, hero, ritual, offering.id)
    if pred["soiled"]:
        world.say(f'"If you hurry," {parent.label or parent.id} said, "your {offering.label} will be lost to {ritual.risk}."')
    hero.memes["fear"] = 1
    hero.memes["slighted"] = 1
    world.say(f"{hero.id} frowned. {hero.pronoun().capitalize()} tried to keep going, but the warning stung.")
    world.say(f"Then came a flashback: long ago, an elder had taught {hero.id}, "{_sound("thump")} slow hands keep holy things whole."")
    world.flashback_used = True

    world.para()
    world.say(f"{hero.id} remembered that lesson as {hero.pronoun('possessive')} hands moved more carefully.")
    world.say(f"{hero.id} lifted the {offering.label} away from the fire and looked for a better way.")
    charm = next(c for c in CHARMS if c.id == "gloves" if offering.region == "hands" else c.id in {"shawl", "apron"})
    world.add(Entity(id=charm.id, type="charm", label=charm.label, protective=True, worn_by=hero.id))
    world.say(f"{hero.id} chose to {charm.prep}.")
    _do_ritual(world, hero, ritual, narrate=True)
    _fixpoint(world, narrate=True)

    if offering.meters.get("ash", 0.0) >= THRESHOLD:
        world.say(f"But the charm held true, so {offering.label} stayed clean.")
    world.say(f"At last, {hero.id} finished {_sound(ritual.gerund)} and the shrine grew quiet.")
    world.say(f"{hero.id} smiled beside {hero.pronoun('possessive')} {parent_type}, and the night felt blessed again.")

    world.facts.update(hero=hero, parent=parent, offering=offering, ritual=ritual, setting=setting, charm=charm)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], RITUALS[params.ritual], OFFERINGS[params.offering], params.name, params.gender, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=[
            f'Write a mythic story about a child who must cater a feast and remembers an old lesson when conflict rises.',
            f'Tell a short story with a flashback, sound effects, and a sacred task at {world.setting.place}.',
            f'Write a child-friendly myth where {params.name} learns how to protect an offering while catering the feast.',
        ],
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, offering, ritual = f["hero"], f["parent"], f["offering"], f["ritual"]
    return [
        QAItem(question=f"What sacred work did {hero.id} want to do at {world.setting.place}?", answer=f"{hero.id} wanted to {ritual.verb}."),
        QAItem(question=f"What did the warning say might happen to the {offering.label}?", answer=f"The warning said the {offering.label} could get lost to {ritual.risk}."),
        QAItem(question=f"What old memory helped {hero.id} calm down?", answer=f"{hero.id} remembered the elder's lesson: \"thump slow hands keep holy things whole.\""),
        QAItem(question=f"How did {hero.id} solve the problem?", answer=f"{hero.id} put on {f['charm'].label if f.get('charm') else 'a protective charm'} and kept the {offering.label} safe while finishing the feast."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a feast?", answer="A feast is a special meal with many foods, shared to honor guests or a celebration."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is a moment when a story remembers something that happened earlier."),
        QAItem(question="Why do stories use sound effects?", answer="Sound effects help a story feel alive by making actions seem more vivid to the listener."),
    ]


ASP_RULES = r"""
place(P) :- setting(P).
ritual(R) :- ritual_def(R).
offering(O) :- offering_def(O).

valid(P,R,O) :- setting(P), ritual_def(R), offering_def(O).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for r in RITUALS:
        lines.append(asp.fact("ritual_def", r))
    for o, off in OFFERINGS.items():
        lines.append(asp.fact("offering_def", o))
        lines.append(asp.fact("offering_region", o, off.region))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - py_set))
    print("only in python:", sorted(py_set - clingo_set))
    return 1


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append("protective=True")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  flashback_used={world.flashback_used}")
    return "\n".join(lines)


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
    StoryParams(place="temple", ritual="feast", offering="bread", name="Mira", gender="girl", parent="mother", trait="brave"),
    StoryParams(place="grove", ritual="feast", offering="flowers", name="Kian", gender="boy", parent="father", trait="steady"),
    StoryParams(place="shore", ritual="feast", offering="milk", name="Tala", gender="girl", parent="mother", trait="hopeful"),
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
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
