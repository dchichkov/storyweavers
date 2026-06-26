#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bonk_prawn_prescription_sound_effects_sharing_rhyming.py
==============================================================================================================

A small standalone story world for a rhyming, sound-effect-rich sharing tale.

Premise:
- A child wants to share a snack at a simple setting.
- A prescription must stay safe and dry.
- A bonk sound marks the moment the plan could go wrong.
- A gentle helper offers a soft fix so sharing can still happen.

This world is intentionally narrow: it models a few carefully reasoned variants
instead of a broad grab-bag of unrelated stories.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters.setdefault("risk", 0.0)
        self.meters.setdefault("mess", 0.0)
        self.meters.setdefault("safe", 0.0)
        self.meters.setdefault("shared", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("care", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_plural(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Snack:
    id: str
    label: str
    phrase: str
    mess: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Container:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
    plural: bool = False
    soft: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    snack: str
    carrier: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "picnic": Setting(place="the picnic table", indoors=False, affords={"share"}),
    "kitchen": Setting(place="the kitchen table", indoors=True, affords={"share"}),
    "porch": Setting(place="the porch bench", indoors=False, affords={"share"}),
}

SNACKS = {
    "prawn": Snack(
        id="prawn",
        label="prawn",
        phrase="a little plate of prawns",
        mess="sticky",
        tags={"prawn", "share", "food"},
    ),
    "crackers": Snack(
        id="crackers",
        label="crackers",
        phrase="a bowl of crisp crackers",
        mess="crumbly",
        tags={"share", "food"},
    ),
    "berries": Snack(
        id="berries",
        label="berries",
        phrase="a cup of bright berries",
        mess="juicy",
        tags={"share", "food"},
    ),
}

CONTAINERS = {
    "case": Container(
        id="case",
        label="a padded prescription case",
        prep="slide the prescription into a padded case",
        tail="slid the prescription into the padded case",
        covers={"paper"},
        guards={"bonk"},
        soft=True,
    ),
    "pouch": Container(
        id="pouch",
        label="a soft pouch",
        prep="put the prescription in a soft pouch",
        tail="put the prescription in the soft pouch",
        covers={"paper"},
        guards={"bonk"},
        soft=True,
    ),
    "folder": Container(
        id="folder",
        label="a sturdy folder",
        prep="tuck the prescription in a sturdy folder",
        tail="tucked the prescription in the sturdy folder",
        covers={"paper"},
        guards={"bonk"},
        soft=False,
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Rose", "Nia", "Pia", "Ava"]
BOY_NAMES = ["Owen", "Finn", "Max", "Toby", "Leo", "Sam"]
TRAITS = ["cheery", "kind", "merry", "bright", "gentle", "spry"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_bonk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["risk"] < THRESHOLD:
            continue
        if "paper" not in world.zone:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.kind == "prescription" and item.meters["safe"] < THRESHOLD:
                sig = ("bonk", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.memes["worry"] += 1
                out.append("bonk!")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["shared"] < THRESHOLD:
            continue
        sig = ("share", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"{actor.id} shared the snack with a grin.")
    return out


RULES = [Rule("bonk", _r_bonk), Rule("share", _r_share)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for bit in produced:
            if bit != "bonk!":
                world.say(bit)
    return produced


def choose_container(snack: Snack) -> Container:
    for c in CONTAINERS.values():
        if "bonk" in c.guards:
            return c
    raise StoryError("No reasonable container exists for this story.")


def story_rhyme(name: str, snack: Snack, place: str) -> str:
    return (
        f"{name} came to {place} with a snack to share, "
        f"and a prescription to keep safe with care. "
        f"\"Let's snack and sing,\" {name} said with a wink, "
        f"\"and keep everything neat in a blink and a blink.\""
    )


def tell(setting: Setting, snack: Snack, carrier: str, hero_name: str, hero_type: str,
         helper_type: str, trait: str) -> World:
    world = World(setting)

    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"risk": 0.0, "mess": 0.0, "safe": 0.0, "shared": 0.0},
        memes={"worry": 0.0, "joy": 0.0, "care": 1.0},
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=helper_type,
        label=f"the {helper_type}",
        memes={"worry": 0.0, "joy": 0.0, "care": 1.0},
    ))
    prescription = world.add(Entity(
        id="prescription",
        kind="thing",
        type="prescription",
        label="prescription",
        phrase="the prescription",
        owner=hero.id,
        caretaker=helper.id,
        meters={"risk": 0.0, "mess": 0.0, "safe": 0.0},
        memes={"worry": 0.0, "joy": 0.0},
    ))
    snack_ent = world.add(Entity(
        id=snack.id,
        kind="thing",
        type=snack.id,
        label=snack.label,
        phrase=snack.phrase,
        owner=hero.id,
        meters={"shared": 0.0, "mess": 0.0},
    ))
    carrier_ent = world.add(Entity(
        id=carrier,
        kind="thing",
        type=carrier,
        label=carrier.replace("_", " "),
        phrase=f"a {carrier.replace('_', ' ')}",
        owner=hero.id,
    ))

    world.say(f"{hero.id} was a {trait} little {hero.type} who loved to share.")
    world.say(
        f"{hero.id} had {snack.phrase} and {prescription.label} to bring along."
    )
    world.para()
    world.say(
        f"At {setting.place}, the day felt light, with a hop and a play and a sway."
    )
    world.say(
        f"{hero.id} wanted to share {snack.label} and keep the prescription in {carrier_ent.label}."
    )
    hero.meters["shared"] += 1
    hero.meters["risk"] += 1
    prescription.meters["safe"] += 0.0
    world.zone = {"paper"}
    propagate(world, narrate=True)

    world.para()
    world.say(
        f"Then came a bump and a bonk and a clink, as the bag tipped over the brink."
    )
    if "bonk!" in propagate(world, narrate=False):
        world.say(f"bonk! The prescription wobbled, but did not fall.")
        helper.memes["worry"] += 1

    container = choose_container(snack)
    world.say(
        f"{hero.id}'s {helper.type} smiled and said, "
        f"\"Let's {container.prep}, and share with delight.\""
    )
    prescription.meters["safe"] += 1
    world.say(
        f"{hero.id} nodded and {container.tail}, then shared the snack in the warm afternoon light."
    )
    world.say(
        f"{hero.id} passed the prawns around one by one, and all went well in a happy little spell."
    )
    hero.memes["joy"] += 1
    hero.meters["shared"] += 1
    world.facts.update(
        hero=hero,
        helper=helper,
        prescription=prescription,
        snack=snack_ent,
        carrier=carrier_ent,
        container=container,
        setting=setting,
        trait=trait,
    )
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for snack_id in SNACKS:
            for carrier in CONTAINERS:
                combos.append((place, snack_id, carrier))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    snack = f["snack"]
    return [
        f"Write a short rhyming story for a small child about {hero.id} sharing {snack.label} safely.",
        f"Tell a gentle rhyme with a bonk sound, a prescription, and a sharing moment at {f['setting'].place}.",
        f"Write a simple story where a child keeps a prescription safe while sharing {snack.phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prescription = f["prescription"]
    snack = f["snack"]
    place = f["setting"].place
    container = f["container"]
    return [
        QAItem(
            question=f"Who was sharing the snack at {place}?",
            answer=f"{hero.id} was sharing {snack.label} at {place}.",
        ),
        QAItem(
            question="What important thing had to stay safe?",
            answer=f"The prescription had to stay safe and not get knocked about.",
        ),
        QAItem(
            question="What sound happened when things bumped?",
            answer="The story made a bonk sound when the bag tipped and bumped.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} helped by using {container.label} so the prescription could stay safe while the snack was shared.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end?",
            answer=f"{hero.id} shared the snack happily after the prescription was tucked away safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving some of what you have to someone else so they can enjoy it too.",
        ),
        QAItem(
            question="What is a prescription?",
            answer="A prescription is a doctor’s note that tells you what medicine or care you should use.",
        ),
        QAItem(
            question="What is a bonk sound?",
            answer="A bonk sound is a light bumping sound, like when something taps into another thing.",
        ),
        QAItem(
            question="What is a prawn?",
            answer="A prawn is a small sea creature that people often cook and eat as food.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story questions =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== Prompts ==")
    for p in sample.prompts:
        lines.append(p)
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in world.entities.values():
        out.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={dict(e.meters)} memes={dict(e.memes)}"
        )
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for item in sorted(setting.affords):
            lines.append(asp.fact("affords", place, item))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        for tag in sorted(snack.tags):
            lines.append(asp.fact("tag", sid, tag))
    for cid, c in CONTAINERS.items():
        lines.append(asp.fact("container", cid))
        for g in sorted(c.guards):
            lines.append(asp.fact("guards", cid, g))
        for cov in sorted(c.covers):
            lines.append(asp.fact("covers", cid, cov))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Snack, Carrier) :- setting(Place), snack(Snack), container(Carrier), affords(Place, share).
compatible(Place, Snack, Carrier) :- valid(Place, Snack, Carrier), guards(Carrier, bonk), covers(Carrier, paper).
#show valid/3.
#show compatible/3.
"""


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
        print(f"OK: ASP matches Python for {len(py)} combos.")
        return 0
    print("MISMATCH:")
    if py - asp_set:
        print(" only in python:", sorted(py - asp_set))
    if asp_set - py:
        print(" only in ASP:", sorted(asp_set - py))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.snack and args.snack not in SNACKS:
        raise StoryError("Unknown snack.")
    if args.place and args.place not in SETTINGS:
        raise StoryError("Unknown place.")
    if args.carrier and args.carrier not in CONTAINERS:
        raise StoryError("Unknown carrier.")

    combos = [
        c for c in valid_combos()
        if (args.place is None or c[0] == args.place)
        and (args.snack is None or c[1] == args.snack)
        and (args.carrier is None or c[2] == args.carrier)
    ]
    if not combos:
        raise StoryError("No valid story matches those options.")

    place, snack_id, carrier = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        snack=snack_id,
        carrier=carrier,
        name=name,
        gender=gender,
        helper=helper,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        SNACKS[params.snack],
        params.carrier,
        params.name,
        params.gender,
        params.helper,
        params.trait,
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rhyming story world with bonks, prawns, and a prescription.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--carrier", choices=CONTAINERS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams(place="picnic", snack="prawn", carrier="case", name="Mia", gender="girl", helper="mother", trait="cheery"),
    StoryParams(place="kitchen", snack="crackers", carrier="pouch", name="Leo", gender="boy", helper="father", trait="gentle"),
    StoryParams(place="porch", snack="berries", carrier="folder", name="Nia", gender="girl", helper="mother", trait="merry"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3.\n#show compatible/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.snack} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
