#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/puggle_candied_magic_tall_tale.py
===============================================================================================================

A tiny tall-tale storyworld about a puggle, a candied treat, and a bit of magic.

The seed vibe:
- puggle
- candied
- Magic
- Tall Tale

The world model uses a small causal simulation:
- the puggle wants a candied treat from a magic stand
- the treat is too high and too sticky for a bare paw
- a grown-up warns that the magical sugar will tangle the puggle's whiskers and coat
- the puggle tries anyway, gets into a sticky scrape, then accepts a magical helper
- the ending proves the change in state: the treat is safely shared and the mess is cleaned

This is intentionally compact, classical, and child-facing.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"puggle"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Treat:
    id: str
    label: str
    phrase: str
    region: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class MagicHelper:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


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
class Rule:
    name: str
    apply: callable


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------
def _r_sticky(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["candied"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("sticky", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["candied"] += 1
            item.meters["messy"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} came away candied and sticky.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in world.entities.values():
        if item.meters["messy"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] += 1
        out.append(f"That meant more cleanup for {carer.label}.")
    return out


def _r_tangle(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("tangle", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["trouble"] += 1
        return ["__tangle__"]
    return []


CAUSAL_RULES = [
    Rule("sticky", _r_sticky),
    Rule("worry", _r_worry),
    Rule("tangle", _r_tangle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(s for s in out if s != "__tangle__")
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "market": Setting(place="the moonlit market", indoor=False, affords={"candied"}),
    "orchard": Setting(place="the sugar orchard", indoor=False, affords={"candied"}),
}

TREAT = Treat(
    id="candied_starfruit",
    label="candied starfruit",
    phrase="a shiny candied starfruit",
    region="mouth",
    mess="candied",
    soil="sticky and sugary",
    zone={"mouth", "paws", "whiskers"},
    keyword="candied",
    tags={"candied", "magic"},
)

MAGIC = [
    MagicHelper(
        id="spellnapkin",
        label="a spell napkin",
        covers={"mouth", "paws", "whiskers"},
        guards={"candied"},
        prep="unfurl a spell napkin first",
        tail="whiskered their way home with the spell napkin",
    ),
    MagicHelper(
        id="moonfork",
        label="a moonfork",
        covers={"mouth"},
        guards={"candied"},
        prep="lift it with a moonfork",
        tail="picked the treat up with the moonfork",
    ),
]

GROWNUPS = [
    ("mother", "Mabel"),
    ("father", "Otis"),
    ("aunt", "June"),
]

PUGGLE_NAMES = ["Pip", "Nibbles", "Mochi", "Gumdrop", "Penny"]


@dataclass
class StoryParams:
    place: str
    helper: str
    name: str
    grownup_type: str
    grownup_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(T) :- treat(T), splashes(T, R), worn_on(T, R).
compatible(H, T) :- helper(H), at_risk(T), guards(H, M), mess_of(T, M), covers(H, R), worn_on(T, R).
valid(Place, T) :- affords(Place, T), treat(T), at_risk(T), compatible(_, T).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    lines.append(asp.fact("treat", TREAT.id))
    lines.append(asp.fact("mess_of", TREAT.id, TREAT.mess))
    for r in sorted(TREAT.zone):
        lines.append(asp.fact("splashes", TREAT.id, r))
    for helper in MAGIC:
        lines.append(asp.fact("helper", helper.id))
        for m in sorted(helper.guards):
            lines.append(asp.fact("guards", helper.id, m))
        for c in sorted(helper.covers):
            lines.append(asp.fact("covers", helper.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        if TREAT.id in setting.affords:
            out.append((place, TREAT.id))
    return out


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def setting_line(setting: Setting) -> str:
    return f"{setting.place.capitalize()} glittered like a spoonful of moon sugar."


def predict_mess(world: World, actor: Entity, treat: Treat, treat_id: str) -> dict:
    sim = world.copy()
    do_action(sim, sim.get(actor.id), treat, narrate=False)
    treat_ent = sim.entities[treat_id]
    return {"messy": bool(treat_ent.meters["messy"] >= THRESHOLD), "worry": sum(e.memes["worry"] for e in sim.characters())}


def do_action(world: World, actor: Entity, treat: Treat, narrate: bool = True) -> None:
    world.zone = set(treat.zone)
    actor.meters[treat.mess] += 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little puggle with bright eyes and a nose for wonder.")


def love_magic(world: World, hero: Entity) -> None:
    hero.memes["wonder"] += 1
    world.say(f"{hero.id} loved magic most of all, especially the sort that made the air twinkle.")


def desire_treat(world: World, hero: Entity) -> None:
    world.say(f"One day, {hero.id} spotted a candied starfruit shining at the market stall.")
    hero.memes["desire"] += 1
    world.say(f"It was so shiny that {hero.id} forgot all about standing still.")


def warn(world: World, grownup: Entity, hero: Entity) -> bool:
    pred = predict_mess(world, hero, TREAT, TREAT.id)
    if not pred["messy"]:
        return False
    world.say(f'"That treat will leave you sticky as maple sap," {grownup.label} said.')
    world.say(f'"And then I would have to scrub your whiskers from dawn to dusk," {grownup.label} added.')
    world.facts["predicted_worry"] = pred["worry"]
    return True


def defy(world: World, hero: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(f"But {hero.id} gave a mighty sniff, as stubborn as a barn door in a windstorm.")
    world.say(f"{hero.id} trotted toward the candied starfruit anyway.")


def grab_and_tangle(world: World, grownup: Entity, hero: Entity) -> None:
    hero.memes["grabbed"] += 1
    propagate(world, narrate=False)
    world.say(f"Then {grownup.label} caught {hero.id} by the scruff and said,")
    world.say('"We can still have the treat, but we will use magic the sensible way."')


def offer_magic(world: World, grownup: Entity, hero: Entity, helper: MagicHelper) -> None:
    hero.memes["joy"] += 1
    hero.memes["defiance"] = 0.0
    helper_ent = world.add(
        Entity(
            id=helper.id,
            type="magic",
            label=helper.label,
            owner=hero.id,
            caretaker=grownup.id,
            protective=True,
            covers=set(helper.covers),
        )
    )
    helper_ent.worn_by = hero.id
    world.say(f"{grownup.label} {helper.prep}, and the little puggle blinked at the sparkle of it.")
    world.say(f"With the spellwork settled, {hero.id} could reach the treat without getting a coat full of sugar.")


def resolution(world: World, hero: Entity, grownup: Entity, helper: MagicHelper) -> None:
    hero.memes["love"] += 1
    world.say(
        f"{hero.id}'s whiskers twitched with relief, and {hero.id} nibbled the candied starfruit so neatly "
        f"that not a crumb escaped the moonfork's spell."
    )
    world.say(
        f"By the end, {hero.id} was happily {TREAT.keyword} and {grownup.label} was laughing, "
        f"because the magic had turned a sticky moment into a tidy tale."
    )
    world.say(
        f"They {helper.tail}, with {hero.id}'s paws clean and {hero.id}'s tail wagging like a flag in a fair breeze."
    )


def tell(setting: Setting, hero_name: str, grownup_type: str, grownup_name: str, helper: MagicHelper) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="puggle"))
    grownup = world.add(Entity(id=grownup_name, kind="character", type=grownup_type, label=grownup_name))
    treat = world.add(Entity(
        id=TREAT.id,
        type="treat",
        label=TREAT.label,
        phrase=TREAT.phrase,
        owner=hero.id,
        caretaker=grownup.id,
        region=TREAT.region,
    ))

    introduce(world, hero)
    love_magic(world, hero)
    world.say(setting_line(setting))
    desire_treat(world, hero)

    world.para()
    warn(world, grownup, hero)
    defy(world, hero)
    grab_and_tangle(world, grownup, hero)

    world.para()
    offer_magic(world, grownup, hero, helper)
    resolution(world, hero, grownup, helper)

    world.facts.update(
        hero=hero,
        grownup=grownup,
        treat=treat,
        helper=helper,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    grownup = f["grownup"]
    return [
        f'Write a short tall tale for a young child about a puggle named {hero.id} who loves magic and sees a candied treat.',
        f"Tell a story where {hero.id} wants a candied starfruit, but {grownup.label} worries it will make a sticky mess.",
        f"Write a gentle magical story that ends with a puggle and a grown-up choosing a safer, clever way to enjoy the candied treat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    grownup = f["grownup"]
    helper = f["helper"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about a little puggle named {hero.id}, who loves magic and gets into a candied scrape before the day is over.",
        ),
        QAItem(
            question=f"What did {hero.id} want at the market?",
            answer=f"{hero.id} wanted a shiny candied starfruit from the market stall.",
        ),
        QAItem(
            question=f"Why did {grownup.label} worry?",
            answer=f"{grownup.label} worried because the candied treat would make {hero.id} sticky, and then there would be a big scrubby cleanup.",
        ),
        QAItem(
            question=f"How did the problem get solved?",
            answer=f"They used {helper.label} to handle the treat the magical way, so {hero.id} could enjoy the candied starfruit without making a bigger mess.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} happy, clean, and nibbling the treat while {grownup.label} laughed at how a little magic fixed the tall-tale trouble.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does candied mean?",
            answer="Candied means covered with sugar or cooked in sugar so it tastes sweet and shiny.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic is something wonderful that can do surprising things, like make a tiny problem easier or turn an ordinary moment into an adventure.",
        ),
        QAItem(
            question="What is a puggle?",
            answer="In this story, a puggle is a small pet-like creature with a curious nose, bright eyes, and a big appetite for adventure.",
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: a puggle, a candied treat, and magic.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--name")
    ap.add_argument("--grownup", choices=[g[0] for g in GROWNUPS])
    ap.add_argument("--helper", choices=[h.id for h in MAGIC])
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


def valid_helper_for_story() -> list[str]:
    return [h.id for h in MAGIC]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS.keys()))
    setting = SETTINGS[place]
    if TREAT.id not in setting.affords:
        raise StoryError("No valid story for that place.")
    helper = args.helper or rng.choice(valid_helper_for_story())
    name = args.name or rng.choice(PUGGLE_NAMES)
    grownup_type, grownup_name = rng.choice(GROWNUPS)
    if args.grownup:
        for gt, gn in GROWNUPS:
            if gt == args.grownup:
                grownup_type, grownup_name = gt, gn
                break
    return StoryParams(place=place, helper=helper, name=name, grownup_type=grownup_type, grownup_name=grownup_name)


def generate(params: StoryParams) -> StorySample:
    helper = next(h for h in MAGIC if h.id == params.helper)
    world = tell(SETTINGS[params.place], params.name, params.grownup_type, params.grownup_name, helper)
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


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    lines.append(asp.fact("treat", TREAT.id))
    for r in sorted(TREAT.zone):
        lines.append(asp.fact("splashes", TREAT.id, r))
    lines.append(asp.fact("mess_of", TREAT.id, TREAT.mess))
    for h in MAGIC:
        lines.append(asp.fact("helper", h.id))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, c))
        for g in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        vals = asp_combos()
        print(f"{len(vals)} compatible story combo(s):")
        for p, t in vals:
            print(f"  {p} {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        presets = [
            StoryParams(place="market", helper="spellnapkin", name="Pip", grownup_type="mother", grownup_name="Mabel"),
            StoryParams(place="orchard", helper="moonfork", name="Mochi", grownup_type="aunt", grownup_name="June"),
        ]
        samples = [generate(p) for p in presets]
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
            header = f"### {p.name}: {p.place} with {p.helper}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


ASP_RULES = r"""
% A treat is at risk if it splashes the region it is worn on.
at_risk(T) :- treat(T), splashes(T, R), worn_on(T, R).

% A helper is compatible if it covers the at-risk region and guards the mess.
compatible(H, T) :- helper(H), at_risk(T), guards(H, M), mess_of(T, M), covers(H, R), worn_on(T, R).

valid(Place, T) :- affords(Place, T), treat(T), at_risk(T), compatible(_, T).
"""


if __name__ == "__main__":
    main()
