#!/usr/bin/env python3
"""
storyworlds/worlds/fourteenth_horrendous_peach_sound_effects_tall_tale.py
=========================================================================

A standalone story world for a small Tall Tale flavored domain about a
fourteenth peach, horrendous sound effects, and a noisy mistake that turns into
a kinder ending.

Seed image:
---
On the fourteenth peach of the season, a child discovered that every tap, bump,
and bounce made a horrendous sound effect. The orchard shook with boings and
thunks, the grown-ups frowned, and the child had to find a way to carry the
peach without waking the whole town.

World idea:
---
A peach is physically large, slippery, and loud when moved. The child wants to
carry it home or show it off, but the sound effects spook nearby animals and
annoy the adults. A blanket, straw, or crate can muffle the noise if it is the
right fit. The story resolves when the child uses the right carrier and the
peach finally reaches its destination without the horrendous racket.

This world is intentionally small and constraint-checked rather than open-ended.
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
    carried_by: Optional[str] = None
    protective: bool = False
    muffles: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

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
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Peach:
    label: str
    phrase: str
    size: str
    noise: str
    spill: str
    keyword: str = "peach"
    tags: set[str] = field(default_factory=set)


@dataclass
class Carrier:
    id: str
    label: str
    phrase: str
    fits: set[str]
    quiets: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sound_zone: bool = False

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
        clone.sound_zone = self.sound_zone
        clone.paragraphs = [[]]
        return clone

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


def _r_noise_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("struggle", 0.0) < THRESHOLD:
            continue
        for item in world.carried_items(actor):
            if item.protective:
                continue
            if not world.sound_zone:
                continue
            sig = ("noise", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["noise"] = item.meters.get("noise", 0.0) + 1
            out.append(f"The {item.label} made a horrendous sound.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters.get("noise", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1
        out.append(f"That gave {carer.label} a worried look.")
    return out


CAUSAL_RULES = [_r_noise_spill, _r_worry]


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


def predict_noise(world: World, actor: Entity, peach: Peach, peach_id: str) -> bool:
    sim = world.copy()
    sim.get(actor.id).meters["struggle"] = 1
    sim.get(peach_id).carried_by = actor.id
    sim.sound_zone = True
    propagate(sim, narrate=False)
    return sim.get(peach_id).meters.get("noise", 0.0) >= THRESHOLD


def can_use_carrier(peach: Peach, carrier: Carrier) -> bool:
    return peach.size in carrier.fits and "noise" in carrier.quiets


def select_carrier(peach: Peach, carrier_options: list[Carrier]) -> Optional[Carrier]:
    for c in carrier_options:
        if can_use_carrier(peach, c):
            return c
    return None


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.label} was a little {hero.type} with a big curiosity and a bigger grin.")


def peach_detail(peach: Peach) -> str:
    return {
        "small": "small as a teacup",
        "medium": "round and lively",
        "large": "large as a lantern",
        "huge": "huge as a wagon wheel",
    }.get(peach.size, "full of country magic")


def setting_detail(setting: Setting) -> str:
    if setting.place == "the orchard":
        return "The orchard was lined with old trees, and every branch seemed to whisper."
    if setting.place == "the county fair":
        return "The county fair sparkled with ribbons, pies, and wagons everywhere."
    return f"{setting.place.capitalize()} looked wide-open and ready for a tall tale."


def wants_peach(world: World, hero: Entity, peach: Peach) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} spotted the {peach.label}, a {peach_detail(peach)} "
        f"{peach.phrase}, and wanted to take {peach.it()} home."
    )


def warn(world: World, grownup: Entity, hero: Entity, peach: Peach) -> bool:
    if not predict_noise(world, hero, peach, "peach"):
        return False
    world.facts["predicted_noise"] = peach.noise
    world.say(
        f'"If you bump that {peach.label}, it will go {peach.noise}," '
        f"{grownup.label} said. \"That would be horrendous for the whole block.\""
    )
    return True


def struggle(world: World, hero: Entity, peach: Peach) -> None:
    hero.meters["struggle"] = hero.meters.get("struggle", 0.0) + 1
    world.sound_zone = True
    world.say(
        f"{hero.label} tried to lift the {peach.label} anyway, and the fruit gave a "
        f"boingy little bounce."
    )
    propagate(world, narrate=True)


def offer_fix(world: World, grownup: Entity, hero: Entity, peach: Peach) -> Optional[Carrier]:
    carrier = select_carrier(peach, CARRIERS)
    if carrier is None:
        return None
    world.say(
        f'{grownup.label} tapped a finger on a crate and said, '
        f"\"How about we {carrier.prep}?\""
    )
    return carrier


def accept_fix(world: World, hero: Entity, peach: Peach, carrier: Carrier) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0
    peach_item = world.get("peach")
    peach_item.carried_by = hero.id
    peach_item.protective = True
    peach_item.meters["noise"] = 0.0
    world.sound_zone = False
    world.say(
        f"{hero.label} wrapped the {peach.label} in the {carrier.label}, and the sound "
        f"turned soft as a pillow. They {carrier.tail}."
    )
    world.say(
        f"In the end, {hero.label} carried {peach.it()} proudly, and the fourteenth "
        f"peach rolled along without waking the town."
    )


def tell(setting: Setting, peach: Peach, hero_name: str = "Mabel", hero_type: str = "girl",
         grownup_type: str = "grandmother") -> World:
    world = World(setting)

    hero = world.add(Entity(
        id="hero",
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"struggle": 0.0},
        memes={"joy": 0.0, "want": 0.0, "worry": 0.0},
    ))
    grownup = world.add(Entity(
        id="grownup",
        kind="character",
        type=grownup_type,
        label="Grandma June",
        memes={"worry": 0.0},
    ))
    peach_item = world.add(Entity(
        id="peach",
        type="peach",
        label=peach.label,
        phrase=peach.phrase,
        owner=hero.id,
        caretaker=grownup.id,
        meters={"noise": 0.0},
    ))

    world.say(f"{hero.label} and {grownup.label} were at {setting.place}.")
    world.say(setting_detail(setting))
    world.say(f"It was the fourteenth peach of the season, and everybody called it {peach.label}.")

    world.para()
    introduce(world, hero)
    wants_peach(world, hero, peach)
    warn(world, grownup, hero, peach)
    struggle(world, hero, peach)

    world.para()
    carrier = offer_fix(world, grownup, hero, peach)
    if carrier:
        accept_fix(world, hero, peach, carrier)

    world.facts.update(
        hero=hero,
        grownup=grownup,
        peach=peach_item,
        peach_cfg=peach,
        carrier=carrier,
        setting=setting,
    )
    return world


SETTINGS = {
    "orchard": Setting(place="the orchard", affords={"carry"}),
    "fair": Setting(place="the county fair", affords={"carry"}),
    "porch": Setting(place="the porch", affords={"carry"}),
}

PEACHES = {
    "big": Peach(
        label="fourteenth peach",
        phrase="a horrendous peach with a glossy orange cheek",
        size="large",
        noise="boing-clatter",
        spill="spilled its juice",
        tags={"peach", "sound"},
    ),
    "giant": Peach(
        label="fourteenth peach",
        phrase="a giant peach with a wobbling stem",
        size="huge",
        noise="THWUNK-BOING",
        spill="dripped peach juice everywhere",
        tags={"peach", "sound"},
    ),
    "fat": Peach(
        label="fourteenth peach",
        phrase="a fat peach with a warm sunny smell",
        size="medium",
        noise="bumpety-bump",
        spill="splashed juice on the boards",
        tags={"peach", "sound"},
    ),
}

CARRIERS = [
    Carrier(
        id="blanket",
        label="a thick blanket",
        phrase="a thick blanket",
        fits={"large", "huge", "medium"},
        quiets={"noise"},
        prep="wrap it in a thick blanket first",
        tail="carried the peach home in a soft bundle",
    ),
    Carrier(
        id="crate",
        label="a straw crate",
        phrase="a straw crate",
        fits={"large", "huge", "medium"},
        quiets={"noise"},
        prep="set it in a straw crate first",
        tail="rolled the crate along carefully",
    ),
    Carrier(
        id="basket",
        label="a deep basket",
        phrase="a deep basket",
        fits={"small", "medium"},
        quiets={"noise"},
        prep="nestle it in a deep basket first",
        tail="walked with the basket held high",
    ),
]

GIRL_NAMES = ["Mabel", "June", "Nell", "Ruby", "Sadie", "Ivy"]
BOY_NAMES = ["Hank", "Toby", "Owen", "Bennie", "Cal", "Jasper"]
TRAITS = ["brave", "curious", "cheerful", "stubborn", "lively"]


@dataclass
class StoryParams:
    setting: str
    peach: str
    name: str
    gender: str
    grownup: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sname, setting in SETTINGS.items():
        if "carry" not in setting.affords:
            continue
        for pname, peach in PEACHES.items():
            if select_carrier(peach, CARRIERS):
                combos.append((sname, pname))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, grownup, peach = f["hero"], f["grownup"], f["peach_cfg"]
    return [
        'Write a short tall tale for a child about the fourteenth peach and a '
        f'horrendous sound effect at {f["setting"].place}.',
        f"Tell a big-hearted story where {hero.label} wants to carry the {peach.label} "
        f"but {grownup.label} worries about the noise.",
        f'Write a story with the words "fourteenth", "horrendous", and "peach" '
        f"that ends with a quieter way to move the fruit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, grownup, peach = f["hero"], f["grownup"], f["peach_cfg"]
    place = f["setting"].place
    qa = [
        QAItem(
            question=f"Who wanted to carry the fourteenth peach at {place}?",
            answer=f"{hero.label} wanted to carry the fourteenth peach at {place}.",
        ),
        QAItem(
            question=f"Why did {grownup.label} worry about the peach?",
            answer=f"{grownup.label} worried because the peach would go {peach.noise} and make a horrendous racket.",
        ),
        QAItem(
            question="What changed at the end of the story?",
            answer=f"{hero.label} used {f['carrier'].label} so the peach could travel quietly instead of making a horrendous sound.",
        ),
    ]
    if f.get("carrier"):
        qa.append(QAItem(
            question=f"How did {f['carrier'].label} help?",
            answer=f"It held the peach snugly and muffled the noise, which let {hero.label} carry it home.",
        ))
    return qa


KNOWLEDGE = {
    "peach": [
        ("What is a peach?", "A peach is a soft, juicy fruit with fuzzy skin and a big pit in the middle."),
    ],
    "sound": [
        ("What is a sound effect?", "A sound effect is a made-up or noticeable noise that helps something feel lively or dramatic."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["peach_cfg"].tags)
    out: list[QAItem] = []
    for tag in ("peach", "sound"):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.protective:
            bits.append(f"protective={e.protective}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(P) :- peach(P), carried(P), noisy(P).
needs_fix(P) :- at_risk(P), carrier(C), muffles(C, noise), fits(C, P).
valid_story(S, P) :- setting(S), peach(P), affords(S, carry), needs_fix(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sname, s in SETTINGS.items():
        lines.append(asp.fact("setting", sname))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sname, a))
    for pname, p in PEACHES.items():
        lines.append(asp.fact("peach", pname))
        lines.append(asp.fact("size", pname, p.size))
        lines.append(asp.fact("noisy", pname))
    for c in CARRIERS:
        lines.append(asp.fact("carrier", c.id))
        for f in sorted(c.fits):
            lines.append(asp.fact("fits", c.id, f))
        for m in sorted(c.quiets):
            lines.append(asp.fact("muffles", c.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: a fourteenth peach and horrendous sound effects.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--peach", choices=PEACHES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["grandmother", "grandfather"])
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.peach is None or c[1] == args.peach)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, peach = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = args.grownup or rng.choice(["grandmother", "grandfather"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, peach=peach, name=name, gender=gender, grownup=grownup, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], PEACHES[params.peach], params.name,
                 params.gender, params.grownup)
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
    StoryParams(setting="orchard", peach="big", name="Mabel", gender="girl", grownup="grandmother", trait="brave"),
    StoryParams(setting="fair", peach="giant", name="Hank", gender="boy", grownup="grandfather", trait="curious"),
    StoryParams(setting="porch", peach="fat", name="Ruby", gender="girl", grownup="grandmother", trait="cheerful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
