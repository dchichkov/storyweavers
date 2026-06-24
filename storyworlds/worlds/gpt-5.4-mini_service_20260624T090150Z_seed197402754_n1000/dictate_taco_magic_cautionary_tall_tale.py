#!/usr/bin/env python3
"""
storyworlds/worlds/dictate_taco_magic_cautionary_tall_tale.py
=============================================================

A tiny cautionary tall-tale world about a bossy caller who tries to dictate a
magic taco into behaving like an ordinary supper.

Seed tale idea:
---
A tall, windy storyteller warned that in a little desert town, a child named
Nico found a shimmering taco from an old wagon. Nico wanted to dictate how the
taco should change the whole day: "Be bigger! Be hotter! Be louder!" But the
magic taco answered to its own curious rules. It grew tall, tipped salsa, and
sent pepper sparks across the table. Nico learned to speak gently, ask first,
and let magic stay magic.

World model:
---
- Physical meters track height, heat, sparkle, spill, and mess.
- Emotional memes track impatience, pride, caution, relief, and awe.
- A dictate action can raise pride and impatience, but also provoke magical
  turbulence when the taco is treated roughly.
- Respecting the taco's own rhythm calms the magic, clears the mess, and leaves
  a grand final image.

This script is intentionally small, self-contained, and constraint-checked.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

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

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    outdoor: bool = True
    weather: str = ""
    affords: set[str] = field(default_factory=set)


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    effect: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Gear:
    id: str
    label: str
    covers: set[str]
    blocks: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable


def _r_turmoil(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    taco = world.entities.get("taco")
    if not hero or not taco:
        return out
    if hero.memes.get("impatience", 0) < THRESHOLD:
        return out
    if taco.held_by != hero.id:
        return out
    if hero.memes.get("dictating", 0) < THRESHOLD:
        return out
    sig = ("turmoil",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    taco.meters["sparkle"] = taco.meters.get("sparkle", 0) + 1
    taco.meters["spill"] = taco.meters.get("spill", 0) + 1
    hero.memes["awe"] = hero.memes.get("awe", 0) + 1
    hero.memes["caution"] = hero.memes.get("caution", 0) + 1
    out.append("The taco flashed like a lantern and shook loose a ribbon of salsa.")
    return out


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    taco = world.entities.get("taco")
    bowl = world.entities.get("bowl")
    if not taco or not bowl:
        return out
    if taco.meters.get("spill", 0) < THRESHOLD:
        return out
    sig = ("mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bowl.meters["mess"] = bowl.meters.get("mess", 0) + 1
    out.append("Salsa dotted the bowl and made a bright little mess on the table.")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    taco = world.entities.get("taco")
    if not hero or not taco:
        return out
    if hero.memes.get("caution", 0) < THRESHOLD:
        return out
    if hero.memes.get("respect", 0) < THRESHOLD:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    taco.meters["sparkle"] = max(0, taco.meters.get("sparkle", 0) - 1)
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    out.append("Once Nico spoke soft and slow, the taco settled down and glowed kindly.")
    return out


RULES = [Rule("turmoil", _r_turmoil), Rule("mess", _r_mess), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_turmoil(world: World, hero: Entity, taco: Entity) -> dict:
    sim = world.copy()
    sim_hero = sim.get(hero.id)
    sim_taco = sim.get(taco.id)
    sim_hero.memes["impatience"] = sim_hero.memes.get("impatience", 0) + 1
    sim_hero.memes["dictating"] = sim_hero.memes.get("dictating", 0) + 1
    sim_taco.held_by = sim_hero.id
    propagate(sim, narrate=False)
    return {
        "spilled": sim_taco.meters.get("spill", 0) >= THRESHOLD,
        "mess": sim.entities["bowl"].meters.get("mess", 0) >= THRESHOLD,
    }


def setting_detail(setting: Setting) -> str:
    if setting.weather:
        return f"The air was {setting.weather}, and the whole place seemed to hum."
    return f"{setting.place.capitalize()} stood open and bright beneath a wide sky."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "stubborn")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved tall stories and odd surprises."
    )


def show_taco(world: World, taco: Entity) -> None:
    world.say(
        f"One day, {world.facts['hero'].id} found {taco.phrase}, and the taco looked as if it had been born for a parade."
    )


def want_to_dictate(world: World, hero: Entity, taco: Entity) -> None:
    hero.memes["impatience"] = hero.memes.get("impatience", 0) + 1
    hero.memes["dictating"] = hero.memes.get("dictating", 0) + 1
    world.say(
        f"{hero.id} wanted to dictate every bit of it: bigger shell, hotter steam, louder sparkle."
    )


def warn(world: World, caretaker: Entity, hero: Entity, taco: Entity, bowl: Entity) -> None:
    pred = predict_turmoil(world, hero, taco)
    if pred["spilled"] or pred["mess"]:
        hero.memes["caution"] = hero.memes.get("caution", 0) + 1
        world.facts["predicted_spill"] = True
        world.say(
            f'"Easy now," {caretaker.label_word} said. "If you boss that magic taco, it may flip the salsa right into the bowl."'
        )


def command(world: World, hero: Entity, taco: Entity) -> None:
    world.say(
        f'{hero.id} pointed a finger and said, "Taco, grow tall! Taco, glow bright! Taco, obey!"'
    )


def reaction(world: World, taco: Entity, hero: Entity) -> None:
    taco.meters["height"] = taco.meters.get("height", 0) + 1
    taco.meters["sparkle"] = taco.meters.get("sparkle", 0) + 1
    taco.held_by = hero.id
    propagate(world, narrate=True)


def cautionary_turn(world: World, hero: Entity, taco: Entity) -> None:
    hero.memes["awe"] = hero.memes.get("awe", 0) + 1
    world.say(
        f"The magic taco stood straighter than a fence post in a thunderstorm, and {hero.id} blinked at the tumble of glitter."
    )


def apology_and_softening(world: World, hero: Entity, taco: Entity, caretaker: Entity) -> None:
    hero.memes["respect"] = hero.memes.get("respect", 0) + 1
    hero.memes["caution"] = hero.memes.get("caution", 0) + 1
    world.say(
        f'{hero.id} took a breath and said, "I am sorry, taco. You may be magic your own way."'
    )
    world.say(
        f"{caretaker.label_word} smiled and handed over a clean napkin, like a flag for calmer country."
    )
    taco.meters["sparkle"] = max(0, taco.meters.get("sparkle", 0) - 1)
    propagate(world, narrate=True)


def ending(world: World, hero: Entity, taco: Entity) -> None:
    world.say(
        f"In the end, {hero.id} ate the taco slowly, and the little lantern-glow of it made the evening seem taller than the mesas."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str,
         hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id="hero", kind="character", type=hero_type, label=hero_name,
        traits=["little", trait, "stubborn"],
    ))
    caretaker = world.add(Entity(id="caretaker", kind="character", type=parent_type, label="the grown-up"))
    taco = world.add(Entity(
        id="taco", type="taco", label="magic taco", phrase="a magic taco that glimmered with pepper-light",
        owner=hero.id,
    ))
    bowl = world.add(Entity(id="bowl", type="bowl", label="bowl", phrase="a blue bowl on the table"))

    world.facts.update(hero=hero, caretaker=caretaker, taco=taco, bowl=bowl, activity=activity, prize=prize_cfg)

    introduce(world, hero)
    world.para()
    world.say(setting_detail(setting))
    show_taco(world, taco)
    want_to_dictate(world, hero, taco)
    warn(world, caretaker, hero, taco, bowl)
    command(world, hero, taco)
    reaction(world, taco, hero)
    world.para()
    cautionary_turn(world, hero, taco)
    apology_and_softening(world, hero, taco, caretaker)
    ending(world, hero, taco)
    return world


SETTINGS = {
    "mesa_town": Setting(place="the mesa town square", weather="warm and windy", affords={"dictate"}),
    "canyon_kitchen": Setting(place="the canyon kitchen", weather="golden and quiet", affords={"dictate"}),
    "traveling_wagon": Setting(place="the traveling wagon stop", weather="dusty and bright", affords={"dictate"}),
}

ACTIVITIES = {
    "dictate": Activity(
        id="dictate",
        verb="dictate",
        gerund="dictating",
        rush="point and command",
        effect="make the taco act bigger than itself",
        zone={"torso"},
        keyword="dictate",
        tags={"dictate", "cautionary"},
    ),
}

PRIZES = {
    "taco": Prize(
        label="taco",
        phrase="a magic taco that glimmered with pepper-light",
        type="taco",
        region="torso",
    ),
}

GIRL_NAMES = ["Mina", "Lola", "June", "Rita"]
BOY_NAMES = ["Nico", "Tomas", "Eli", "Jasper"]
TRAITS = ["bold", "curious", "spirited", "stubborn"]

KNOWLEDGE = {
    "dictate": [
        (
            "What does it mean to dictate something?",
            "To dictate means to tell someone or something exactly what to do, like giving orders in a bossy way.",
        )
    ],
    "taco": [
        (
            "What is a taco?",
            "A taco is a food with a folded shell or tortilla that holds tasty fillings inside.",
        )
    ],
    "cautionary": [
        (
            "What is a cautionary story?",
            "A cautionary story is a tale that warns about a mistake so someone can learn to do better next time.",
        )
    ],
    "magic": [
        (
            "What is magic in a story?",
            "Magic is something impossible in real life that can happen in a story, like glowing or speaking food.",
        )
    ],
    "tall_tale": [
        (
            "What is a tall tale?",
            "A tall tale is a funny story that makes things sound bigger, stronger, or stranger than normal.",
        )
    ],
}


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    return [
        f'Write a short tall tale for a child about a magical taco and a warning against trying to dictate it.',
        f"Tell a cautionary story where {hero.label_word} tries to dictate a magic taco, learns a softer way, and the taco still shines.",
        f'Write a simple story with the words "dictate" and "taco" that ends with a child showing respect to something magical.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, caretaker, taco = f["hero"], f["caretaker"], f["taco"]
    return [
        QAItem(
            question=f"What did {hero.label_word} try to do to the taco?",
            answer=f"{hero.label_word} tried to dictate how the magic taco should change, as if it were an ordinary thing.",
        ),
        QAItem(
            question=f"Why did {caretaker.label_word} warn {hero.label_word}?",
            answer=f"{caretaker.label_word} warned {hero.label_word} because bossing the magic taco could make it spill salsa and make a mess.",
        ),
        QAItem(
            question=f"What changed after {hero.label_word} became more careful?",
            answer=f"{hero.label_word} became more respectful, and the taco settled down and glowed kindly instead of tossing peppery sparks everywhere.",
        ),
        QAItem(
            question=f"How did the story end for {hero.label_word} and the taco?",
            answer=f"They ended peacefully, with {hero.label_word} eating the taco slowly and the evening feeling tall and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for tag in ["dictate", "taco", "magic", "cautionary", "tall_tale"]:
        if tag in KNOWLEDGE:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="mesa_town", activity="dictate", prize="taco", name="Nico", gender="boy", parent="mother", trait="bold"),
    StoryParams(place="canyon_kitchen", activity="dictate", prize="taco", name="Mina", gender="girl", parent="father", trait="curious"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.weather:
            lines.append(asp.fact("weather", sid, s.weather))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("verb", aid, a.verb))
        lines.append(asp.fact("keyword", aid, a.keyword))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A,P) :- zone(A,R), worn_on(P,R).
valid_story(S,A,P,G) :- setting(S), affords(S,A), at_risk(A,P), wears(G,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary tall-tale world about dictating a magic taco.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    activity = args.activity or "dictate"
    prize = args.prize or "taco"
    gender = args.gender or rng.choice(["girl", "boy"])
    if args.gender and args.gender not in PRIZES[prize].genders:
        raise StoryError("Invalid gender for this story.")
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIVITIES[params.activity], PRIZES[params.prize], params.name, params.gender, params.parent, params.trait)
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


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = {(p.place, p.activity, p.prize, g) for p in CURATED for g in [p.gender]}
    if clingo_set == python_set:
        print(f"OK: clingo gate matches curated story set ({len(clingo_set)} stories).")
        return 0
    print("MISMATCH between clingo and curated set.")
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for s in stories:
            print(" ", s)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name}: {p.activity} with {p.prize} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
