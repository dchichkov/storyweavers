#!/usr/bin/env python3
"""
storyworlds/worlds/telegraph_fiery_program_foreshadowing_magic_dialogue_myth.py
===============================================================================

A standalone story world for a small mythic domain with a telegraph, a fiery
program, foreshadowing, magic, and dialogue.

Premise:
- A young hero wants to put on a grand fiery program.
- The hero's elder foresees a problem through foreshadowing.
- A telegraph brings an urgent sign from afar.
- Magic and dialogue lead to a safer plan that still feels wondrous.

The story engine models a tiny simulated world with physical meters and
emotional memes. The prose is driven by state changes, not a static template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    traits: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "queen", "priestess"}
        male = {"boy", "man", "king", "priest"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def is_plural(self) -> bool:
        return self.type.endswith("s")


@dataclass
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    sign: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    label: str
    phrase: str
    type: str
    risk_region: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Charm:
    id: str
    label: str
    protects_against: set[str]
    fits_risk: set[str]
    prep: str
    tail: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}
        self.foreshadowed: bool = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.weather = self.weather
        c.paragraphs = [[]]
        c.foreshadowed = self.foreshadowed
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_heat(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters.get("fire", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.worn_by != e.id:
                continue
            if item.meters.get("safe", 0.0) >= THRESHOLD:
                continue
            sig = ("heat", e.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scorched"] = item.meters.get("scorched", 0.0) + 1
            out.append(f"The heat brushed {item.label or item.id}.")
    return out


def _r_telegraph(world: World) -> list[str]:
    for e in world.characters():
        if e.memes.get("dread", 0.0) < THRESHOLD or e.memes.get("hope", 0.0) < THRESHOLD:
            continue
        sig = ("telegraph", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        return ["__telegraph__"]
    return []


def _r_magic(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("ward", 0.0) < THRESHOLD:
            continue
        sig = ("magic", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["calm"] = e.memes.get("calm", 0.0) + 1
        out.append("A soft magic settled over the circle.")
    return out


CAUSAL_RULES = [
    Rule("heat", "physical", _r_heat),
    Rule("telegraph", "social", _r_telegraph),
    Rule("magic", "social", _r_magic),
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
                produced.extend(s for s in out if s != "__telegraph__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_risk(world: World, hero: Entity, action: Action, relic_id: str) -> dict:
    sim = world.copy()
    do_action(sim, sim.get(hero.id), action, narrate=False)
    relic = sim.get(relic_id)
    return {
        "scorched": relic.meters.get("scorched", 0.0) >= THRESHOLD,
        "ward": sum(e.meters.get("ward", 0.0) for e in sim.characters()),
    }


def place_line(setting: Setting, action: Action) -> str:
    if "sea" in setting.place:
        return f"The wind over {setting.place} sounded like a low flute."
    if action.weather == "storm":
        return f"The sky over {setting.place} flashed like an old silver drum."
    return f"{setting.place.capitalize()} waited in a hush, as if it knew a tale was coming."


def tell(world: World, hero_name: str, hero_type: str, parent_type: str,
         action: Action, relic_cfg: Relic, charm_def: Optional[Charm]) -> World:
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["young", "brave"]))
    elder = world.add(Entity(id="Elder", kind="character", type=parent_type, label="the elder"))
    relic = world.add(Entity(id="relic", type=relic_cfg.type, label=relic_cfg.label,
                             phrase=relic_cfg.phrase, owner=hero.id,
                             caretaker=elder.id))
    if charm_def:
        charm = world.add(Entity(id=charm_def.id, type="charm", label=charm_def.label, owner=hero.id))
        charm.worn_by = hero.id
        charm.meters["ward"] = 1.0
    else:
        charm = None

    world.weather = action.weather

    world.say(f"{hero.id} was a young {hero_type} who loved old wonders and bright songs.")
    world.say(f"{hero.pronoun().capitalize()} dreamed of a {action.gerund} {action.verb} in {world.setting.place}, and the whole village listened.")
    world.say(f"The elder kept {hero.pronoun('possessive')} {relic.label} safe, because {hero.id} had been given {relic.phrase} only for the great night.")

    world.para()
    world.say(place_line(world.setting, action))
    world.say(f"Then the telegraph at the gate clicked once, twice, and three times.")
    world.say(f"{hero.id} hurried to the wire, but the message made {hero.pronoun('object')} slow down.")
    world.say(f'"{action.sign}," the telegraph seemed to say.')
    world.foreshadowed = True

    world.para()
    hero.memes["dread"] = 1.0
    hero.memes["hope"] = 1.0
    world.say(f"{hero.id} wanted the fiery program to begin at once, yet {hero.pronoun('possessive')} heart thudded with worry.")
    pred = predict_risk(world, hero, action, relic.id)
    if pred["scorched"]:
        world.say(f'"If the flames leap too high, {hero.pronoun("possessive")} {relic.label} will be ruined," said the elder.')
        world.say(f'{hero.id} frowned and asked, "Then how can the program still shine like a myth?"')
        hero.memes["dread"] += 1
        elder.memes["wisdom"] = 1.0
        if charm is None:
            charm = world.add(Entity(id="charm", type="charm", label="a moon charm", owner=hero.id))
            charm.worn_by = hero.id
            charm.meters["ward"] = 1.0
        world.say(f'The elder lifted {charm.label} and whispered, "{charm_def.prep if charm_def else "let the charm guard the road"}."')
        world.say(f"{hero.id} held still while the magic warmed the air like a lantern behind a curtain.")
        hero.meters["ward"] = 1.0
        propagate(world, narrate=True)
        world.say(f'"We will keep the fire, but we will shape it," said {hero.id}, and the elder nodded.')
    else:
        world.say(f"The elder smiled, because the sign had warned of danger, but the charm had already made room for safety.")
        hero.meters["ward"] = 1.0
        propagate(world, narrate=True)

    world.para()
    if charm is not None:
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        hero.memes["dread"] = 0.0
        world.say(f"{hero.id} stepped into the circle wearing {charm.label}.")
        world.say(f"{charm.tail}.")
        world.say(f"Then the fiery program began: sparks leaped, drums answered, and the story of the hill glowed without hurting the relic.")
        world.say(f"{hero.id} laughed with the elder, and the telegraph stayed quiet at last, as if it were pleased.")
    else:
        world.say(f"The program began, and the relic stayed safe by luck alone.")
    world.facts.update(
        hero=hero,
        elder=elder,
        relic=relic,
        action=action,
        charm=charm,
        setting=world.setting,
        conflict=True,
        resolved=True,
    )
    return world


SETTINGS = {
    "hill": Setting(place="the hill", affords={"fire_program"}),
    "temple": Setting(place="the temple courtyard", affords={"fire_program"}),
    "harbor": Setting(place="the harbor steps", affords={"fire_program"}),
}

ACTIONS = {
    "fire_program": Action(
        id="fire_program",
        verb="stage",
        gerund="staging",
        risk="fire",
        sign="Beware the flame, and do not let the relic singe",
        weather="storm",
        tags={"fiery", "program", "magic", "dialogue", "foreshadowing"},
    ),
}

RELICS = {
    "scroll": Relic(label="scroll", phrase="an ember-edged scroll", type="scroll", risk_region="hands"),
    "banner": Relic(label="banner", phrase="a bright ritual banner", type="banner", risk_region="cloth"),
    "crown": Relic(label="crown", phrase="a gold wreath from the old kings", type="crown", risk_region="head"),
}

CHARMS = [
    Charm(id="moon_shield", label="a moon shield", protects_against={"fire"}, fits_risk={"hands", "cloth", "head"},
          prep="let the moon shield drink the heat first", tail="walked to the ring with the shield held high"),
    Charm(id="river_cloak", label="a river cloak", protects_against={"fire"}, fits_risk={"hands", "cloth", "head"},
          prep="wrap the river cloak around the relic and trust its cool threads", tail="moved as if the river were walking beside them"),
]

HERO_NAMES = ["Iris", "Milo", "Nera", "Tavi", "Arin", "Lena"]
TRAITS = ["curious", "bold", "gentle", "spirited", "wise"]


@dataclass
class StoryParams:
    place: str
    action: str
    relic: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for relic_id, relic in RELICS.items():
                if relic.risk_region in {"hands", "cloth", "head"}:
                    combos.append((place, act, relic_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic telegraph storyworld with fiery program, magic, dialogue, and foreshadowing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["elder", "mother", "father"])
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
              and (args.action is None or c[1] == args.action)
              and (args.relic is None or c[2] == args.relic)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, action, relic = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(HERO_NAMES)
    parent = args.parent or "elder"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, relic=relic, name=name, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a child about a telegraph, a fiery program, and a wise warning in {f["setting"].place}.',
        f"Tell a short story where {f['hero'].id} stages a fiery program, hears a telegraph, and finds a magical safer way.",
        f'Write a gentle myth with dialogue and foreshadowing that uses the word "telegraph" and ends in a bright, safe fire.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    elder = f["elder"]
    relic = f["relic"]
    action = f["action"]
    charm = f["charm"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a young {hero.type}, and {elder.label}, who helped keep the old relic safe.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {action.verb} a fiery program in {world.setting.place}.",
        ),
        QAItem(
            question=f"Why did the elder worry about the {relic.label}?",
            answer=f"The elder worried because the fire might singe {relic.phrase} while the program was happening.",
        ),
        QAItem(
            question=f"What magical thing helped in the end?",
            answer=f"{charm.label} helped by guarding the danger and letting the program stay bright without hurting the relic.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a telegraph?",
            answer="A telegraph is a machine that sends messages over a wire using clicks and signals.",
        ),
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives small hints early on that something important or surprising may happen later.",
        ),
        QAItem(
            question="What is magic in a myth?",
            answer="Magic is a wondrous power that can change what happens in a story in a special way.",
        ),
        QAItem(
            question="Why do stories use dialogue?",
            answer="Dialogue lets characters speak to each other, so readers can hear their worries, plans, and feelings directly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "",
           "== (2) Story questions ==", *[f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa], "",
           "== (3) World-knowledge questions ==", *[f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa]]
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(hill).
setting(temple).
setting(harbor).

affords(hill,fire_program).
affords(temple,fire_program).
affords(harbor,fire_program).

action(fire_program).
risk_of(fire_program,fire).

relic(scroll).
relic(banner).
relic(crown).

worn_on(scroll,hands).
worn_on(banner,cloth).
worn_on(crown,head).

charm(moon_shield).
charm(river_cloak).

protects(moon_shield,fire).
protects(river_cloak,fire).

valid(Place,Action,Relic) :- affords(Place,Action), risk_of(Action,R), worn_on(Relic,Region), protects(_,R), Region=hands; Region=cloth; Region=head.
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
        for a in SETTINGS[p].affords:
            lines.append(asp.fact("affords", p, a))
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
        lines.append(asp.fact("risk_of", a, ACTIONS[a].risk))
    for r, relic in RELICS.items():
        lines.append(asp.fact("relic", r))
        lines.append(asp.fact("worn_on", r, relic.risk_region))
    for c in CHARMS:
        lines.append(asp.fact("charm", c.id))
        for x in c.protects_against:
            lines.append(asp.fact("protects", c.id, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print(" only in clingo:", sorted(a - b))
    if b - a:
        print(" only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    action = ACTIONS[params.action]
    relic = RELICS[params.relic]
    charm = random.choice(CHARMS)
    world = tell(world, params.name, params.gender, params.parent, action, relic, charm)
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
    StoryParams(place="hill", action="fire_program", relic="scroll", name="Iris", gender="girl", parent="elder", trait="wise"),
    StoryParams(place="temple", action="fire_program", relic="banner", name="Nera", gender="girl", parent="elder", trait="gentle"),
    StoryParams(place="harbor", action="fire_program", relic="crown", name="Tavi", gender="boy", parent="elder", trait="bold"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.verify:
        sys.exit(asp_verify())

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.action} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
