#!/usr/bin/env python3
"""
storyworlds/worlds/mere_shear_voyage_dialogue_bravery_cautionary_myth.py
========================================================================

A compact mythic storyworld about a brave voyage across a mere, a sharp shear
wind, and a cautionary choice made in dialogue.

The seed image:
A young traveler asks to cross the mere in a small boat. An elder warns that
the shear wind can turn a proud voyage into trouble. The traveler listens,
chooses a safer path, and the tale ends with brave restraint instead of ruin.

This script keeps the world small and state-driven:
- physical meters: wind, danger, distance, damage, shelter
- emotional memes: courage, caution, pride, trust, relief, fear

It supports the standard Storyweavers contract, including an inline ASP twin
for the reasonableness gate and verification.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "maiden"}
        male = {"boy", "father", "man", "king", "son", "traveler", "captain", "elder"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    land: str
    water: str
    afford_voyage: bool = True
    sheer_wind: bool = True


@dataclass
class Vessel:
    id: str
    label: str
    phrase: str
    can_sail: bool
    vulnerable_to_shear: bool
    shelter: str
    tail: str


@dataclass
class StoryParams:
    setting: str
    vessel: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None


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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic storyworld: a voyage, a mere, and a cautionary wind.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--vessel", choices=VESSELS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--guide", choices=["elder", "mother", "father", "captain"])
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


def _py_choice(rng: random.Random, items: list[str]) -> str:
    return items[rng.randrange(len(items))]


SETTINGS: dict[str, Setting] = {
    "mere": Setting(place="the mere", land="the shore", water="the still water", afford_voyage=True, sheer_wind=True),
    "cliffmere": Setting(place="the cliff above the mere", land="the high path", water="the dark water below", afford_voyage=True, sheer_wind=True),
    "harbor": Setting(place="the old harbor by the mere", land="the stone dock", water="the open water", afford_voyage=True, sheer_wind=False),
}

VESSELS: dict[str, Vessel] = {
    "skiff": Vessel(
        id="skiff",
        label="small skiff",
        phrase="a small skiff with a pine oar",
        can_sail=True,
        vulnerable_to_shear=True,
        shelter="a tarp shelter",
        tail="they drew the skiff under a reed shelter",
    ),
    "barge": Vessel(
        id="barge",
        label="wide barge",
        phrase="a wide barge with a flat deck",
        can_sail=True,
        vulnerable_to_shear=False,
        shelter="a rope awning",
        tail="they tied the barge beneath a rope awning",
    ),
    "raft": Vessel(
        id="raft",
        label="reed raft",
        phrase="a reed raft bound with cord",
        can_sail=False,
        vulnerable_to_shear=True,
        shelter="a willow screen",
        tail="they hauled the raft behind a willow screen",
    ),
}

TRAITS = ["brave", "curious", "gentle", "steadfast", "wary", "earnest"]

GIRL_NAMES = ["Asha", "Mira", "Nala", "Iris", "Sera", "Lina"]
BOY_NAMES = ["Aran", "Kiran", "Tovin", "Milo", "Bren", "Corin"]


def reasonableness(setting: Setting, vessel: Vessel) -> bool:
    return setting.afford_voyage and vessel.can_sail


def explain_rejection(setting: Setting, vessel: Vessel) -> str:
    return (
        f"(No story: {vessel.label} is not a fitting vessel for a voyage across {setting.place}. "
        f"Try a vessel that can truly sail.)"
    )


@dataclass
class Rule:
    name: str
    apply: callable


def _cliff_shear(world: World) -> list[str]:
    out: list[str] = []
    if not world.setting.sheer_wind:
        return out
    for ent in world.characters():
        if ent.meters.get("voyage", 0.0) < THRESHOLD:
            continue
        if ent.meters.get("windward", 0.0) < THRESHOLD:
            continue
        sig = ("shear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["danger"] = ent.meters.get("danger", 0.0) + 1
        ent.memes["fear"] = ent.memes.get("fear", 0.0) + 1
        out.append(f"The shear wind rose and made the water bite like a blade.")
    return out


def _caution_relief(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.memes.get("caution", 0.0) < THRESHOLD:
            continue
        sig = ("relief", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["relief"] = ent.memes.get("relief", 0.0) + 1
        out.append(f"That caution brought relief to the small party.")
    return out


RULES = [Rule("shear", _cliff_shear), Rule("relief", _caution_relief)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            items = rule.apply(world)
            if items:
                produced.extend(items)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def tell(setting: Setting, vessel: Vessel, hero_name: str, gender: str, guide_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, membranes if False else "", label=hero_name))
    hero.kind = "character"
    hero.type = gender
    hero.meters = {"voyage": 0.0, "danger": 0.0, "windward": 0.0}
    hero.memes = {"courage": 0.0, "caution": 0.0, "pride": 0.0, "trust": 0.0, "relief": 0.0, "fear": 0.0}

    guide = world.add(Entity(id="Guide", kind="character", type=guide_kind, label=guide_kind))
    guide.memes = {"caution": 0.0, "trust": 0.0}

    boat = world.add(Entity(id=vessel.id, kind="thing", type="vessel", label=vessel.label, phrase=vessel.phrase))
    boat.meters = {"damage": 0.0}
    boat.memes = {}

    world.say(f"{hero_name} was a {trait} young traveler who loved old tales of the sea and the sky.")
    world.say(f"{hero_name} longed for a voyage across {setting.place}, where the water lay quiet as a dream.")
    world.say(f"Their guide was a {guide_kind} who had seen the mere in fair weather and in shear wind alike.")
    world.say(f"They had a {vessel.phrase}, and the boat waited by the shore like a small promise.")

    world.para()
    world.say(f"At dawn, {hero_name} and the {guide_kind} stepped to {setting.land}.")
    hero.meters["voyage"] += 1
    hero.meters["windward"] += 1
    hero.memes["courage"] += 1
    world.say(f'"Will the mere be kind today?" {hero_name} asked.')
    world.say(f'"Kindness is not the only thing a traveler needs," the {guide_kind} answered. "A steady heart matters more."')
    hero.memes["pride"] += 1

    if not setting.sheer_wind:
        world.say(f"The water stayed smooth, and the voyage could have begun at once.")
    else:
        world.say(f"The sky looked bright, but a shear wind slept beyond the far reeds.")

    world.para()
    if setting.sheer_wind:
        world.say(f'"Then we should wait," {hero_name} said, watching the reeds bend.')
        hero.memes["caution"] += 1
        guide.memes["trust"] += 1
        propagate(world)
        world.say(f'"Bravery is not only to row," the {guide_kind} said. "Bravery is also to pause when the wind grows sharp."')
        world.say(f'{hero_name} nodded and chose the safer path, leaving the brave noise of rashness behind.')
    else:
        world.say(f'"Let us go," {hero_name} said, and the {guide_kind} agreed.')
        hero.meters["voyage"] += 1
        world.say(f"They crossed the mere in peace, with the boat gliding like a feather on dark glass.")
        hero.memes["relief"] += 1

    world.para()
    if setting.sheer_wind:
        world.say(f"At last the shear wind rushed over the water, but it found no foolish sail to tear.")
        world.say(f"They kept to the shore, and the voyage became a lesson instead of a wound.")
        world.say(f"{hero_name} returned home with courage in the chest and caution in the hands.")
    else:
        world.say(f"By evening they reached the far bank, and the mere shone behind them like a remembered star.")
        world.say(f"{hero_name} returned with wet boots, calm eyes, and a tale of safe passage.")

    world.facts = {
        "hero": hero,
        "guide": guide,
        "vessel": boat,
        "setting": setting,
        "vessel_cfg": vessel,
        "trait": trait,
        "gender": gender,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children about a voyage across {f["setting"].place} that includes the word "mere".',
        f'Write a gentle story where {f["hero"].id} must decide whether to travel in a {f["vessel_cfg"].label} when a shear wind threatens the journey.',
        f'Write a mythic dialogue story about bravery and caution on a voyage, ending with a wise choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guide = f["guide"]
    vessel = f["vessel_cfg"]
    setting = f["setting"]
    qa = [
        QAItem(
            question=f"Who wanted to make the voyage across {setting.place}?",
            answer=f"{hero.id} wanted the voyage, and the {guide.type} traveled with them.",
        ),
        QAItem(
            question=f"What kind of boat did they have for the journey?",
            answer=f"They had {vessel.phrase} for the journey.",
        ),
        QAItem(
            question=f"What did the guide say about the shear wind?",
            answer=f"The {guide.type} warned that bravery also meant waiting when the wind grew sharp.",
        ),
        QAItem(
            question=f"How did {hero.id} show bravery in the end?",
            answer=f"{hero.id} showed bravery by listening, choosing caution, and refusing to rush into danger.",
        ),
    ]
    if setting.sheer_wind:
        qa.append(
            QAItem(
                question=f"Why did the voyage stay safe near {setting.place}?",
                answer=f"The voyage stayed safe because {hero.id} and the guide chose to wait instead of sailing into the shear wind.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mere?",
            answer="A mere is a lake or pond, a body of water that can lie still or turn rough in the wind.",
        ),
        QAItem(
            question="What does shear mean when we talk about wind?",
            answer="Shear wind means a sharp, strong wind that can pull and tear at sails or make travel hard.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery means doing what is right even when you feel worried or afraid.",
        ),
        QAItem(
            question="What is caution?",
            answer="Caution means paying attention to danger and choosing carefully so harm can be avoided.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.kind:7}/{e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({name for name, _ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="mere", vessel="skiff", name="Asha", gender="girl", guide="elder", trait="brave"),
    StoryParams(setting="cliffmere", vessel="skiff", name="Aran", gender="boy", guide="elder", trait="wary"),
    StoryParams(setting="harbor", vessel="barge", name="Mira", gender="girl", guide="captain", trait="steadfast"),
]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s_id, s in SETTINGS.items():
        for v_id, v in VESSELS.items():
            if reasonableness(s, v):
                combos.append((s_id, v_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.vessel:
        if not reasonableness(SETTINGS[args.setting], VESSELS[args.vessel]):
            raise StoryError(explain_rejection(SETTINGS[args.setting], VESSELS[args.vessel]))
    combos = [
        (s, v) for (s, v) in valid_combos()
        if (args.setting is None or s == args.setting)
        and (args.vessel is None or v == args.vessel)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, vessel = rng.choice(sorted(combos))
    gender = args.gender or _py_choice(rng, ["girl", "boy"])
    name = args.name or _py_choice(rng, GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = args.guide or _py_choice(rng, ["elder", "captain", "mother", "father"])
    trait = args.trait or _py_choice(rng, TRAITS)
    return StoryParams(setting=setting, vessel=vessel, name=name, gender=gender, guide=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], VESSELS[params.vessel], params.name, params.gender, params.guide, params.trait)
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
setting(mere). setting(cliffmere). setting(harbor).
affords(mere,voyage). affords(cliffmere,voyage). affords(harbor,voyage).

vessel(skiff). vessel(barge). vessel(raft).
can_sail(skiff). can_sail(barge).
vulnerable_to_shear(skiff). vulnerable_to_shear(raft).

reasonably_valid(S,V) :- affords(S,voyage), can_sail(V).
#show reasonably_valid/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.afford_voyage:
            lines.append(asp.fact("affords", sid, "voyage"))
        if s.sheer_wind:
            lines.append(asp.fact("sheer_wind", sid))
    for vid, v in VESSELS.items():
        lines.append(asp.fact("vessel", vid))
        if v.can_sail:
            lines.append(asp.fact("can_sail", vid))
        if v.vulnerable_to_shear:
            lines.append(asp.fact("vulnerable_to_shear", vid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_valid/2."))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show reasonably_valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible voyage settings and vessels:\n")
        for s, v in combos:
            print(f"  {s:10} {v}")
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
            header = f"### {p.name}: voyage at {p.setting} (vessel: {p.vessel})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
