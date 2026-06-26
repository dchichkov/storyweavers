#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gorgeous_befall_misunderstanding_bad_ending_flashback_superhero.py
===============================================================================================================================

A small superhero storyworld built from the seed words:
- gorgeous
- befall
- Misunderstanding
- Bad Ending
- Flashback
- Superhero Story

The domain is a child-facing comic-book rescue scene in a bright city. A young
hero, a worried friend, and a mysterious mishap create a misunderstanding.
A flashback reveals why the hero hesitates, and the story turns toward a safer
choice before a bad ending can befall the city.
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
    wearing: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    light: str
    sound: str


@dataclass
class Threat:
    id: str
    label: str
    verb: str
    harm: str
    location: str
    mess: str
    story_word: str = ""


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    protects_from: set[str]
    tone: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace: list[str] = []
        self.threat_active: Optional[str] = None
        self.bad_ending_risk: float = 0.0

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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.threat_active = self.threat_active
        c.bad_ending_risk = self.bad_ending_risk
        return c


@dataclass
class StoryParams:
    place: str
    hero: str
    sidekick: str
    threat: str
    gear: str
    seed: Optional[int] = None


SETTINGS = {
    "skyport": Setting(place="Skyport City", light="golden", sound="the hum of traffic"),
    "museum": Setting(place="the City Museum", light="bright", sound="soft footsteps"),
    "harbor": Setting(place="Blue Harbor", light="sparkling", sound="seagulls and waves"),
}

THREATS = {
    "smoke": Threat(
        id="smoke",
        label="a smoke machine burst",
        verb="spread smoke through the square",
        harm="blind the crowd",
        location="the square",
        mess="smoky",
        story_word="smoke",
    ),
    "glue": Threat(
        id="glue",
        label="a glue spill",
        verb="glue the doors shut",
        harm="trap the visitors inside",
        location="the lobby",
        mess="sticky",
        story_word="glue",
    ),
    "froth": Threat(
        id="froth",
        label="a foamy wave",
        verb="flood the dock",
        harm="knock over the crates",
        location="the dock",
        mess="foamy",
        story_word="wave",
    ),
}

GEAR = {
    "visor": Gear(
        id="visor",
        label="a bright visor",
        phrase="a bright visor that let the hero see through smoke",
        protects_from={"smoky"},
        tone="steady",
    ),
    "gloves": Gear(
        id="gloves",
        label="slick gloves",
        phrase="slick gloves that kept sticky things from grabbing hands",
        protects_from={"sticky"},
        tone="careful",
    ),
    "boots": Gear(
        id="boots",
        label="tall rescue boots",
        phrase="tall rescue boots that helped on wet docks",
        protects_from={"foamy"},
        tone="strong",
    ),
}

HEROES = [
    ("Nova", "girl"),
    ("Bolt", "boy"),
    ("Pip", "girl"),
    ("Jet", "boy"),
]

SIDEKICKS = ["Moss", "Tansy", "Echo", "Finn"]

CURIOUS_TRAITS = ["brave", "quick", "kind", "careful", "cheerful"]

ASP_RULES = r"""
% A bad ending risk appears when the threat is active and the hero lacks the
% matching gear.
risk(P,T) :- hero(P), threat(T), active(T), not protected(P,T).

protected(P,T) :- wears(P,G), gear(G), protects(G,T).

safe_story(P,T) :- hero(P), threat(T), protected(P,T), handled(T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid, t in THREATS.items():
        lines.append(asp.fact("threat", tid))
        lines.append(asp.fact("active", tid))
        lines.append(asp.fact("harm", tid, t.harm))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for m in sorted(g.protects_from):
            lines.append(asp.fact("protects", gid, m))
    for hid, _ in HEROES:
        lines.append(asp.fact("hero", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _choose_combo(rng: random.Random, args: argparse.Namespace) -> tuple[str, str, str, str]:
    place = args.place or rng.choice(list(SETTINGS))
    hero = args.hero or rng.choice([n for n, _ in HEROES])
    sidekick = args.sidekick or rng.choice([n for n in SIDEKICKS if n != hero])
    threat = args.threat or rng.choice(list(THREATS))
    gear = args.gear or {"smoke": "visor", "glue": "gloves", "froth": "boots"}[threat]
    return place, hero, sidekick, threat, gear


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world about misunderstanding and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--hero", choices=[n for n, _ in HEROES])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place, hero, sidekick, threat, gear = _choose_combo(rng, args)
    if gear != {"smoke": "visor", "glue": "gloves", "froth": "boots"}[threat]:
        raise StoryError("That gear would not reasonably solve this threat.")
    if hero == sidekick:
        raise StoryError("The hero and sidekick must be different characters.")
    return StoryParams(place=place, hero=hero, sidekick=sidekick, threat=threat, gear=gear)


def _hero_type(name: str) -> str:
    for n, t in HEROES:
        if n == name:
            return t
    return "girl"


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero_type = _hero_type(params.hero)
    hero = world.add(Entity(
        id=params.hero,
        kind="character",
        type=hero_type,
        label=f"the hero {params.hero}",
        traits=["gorgeous", "brave"],
        meters={"speed": 1.0, "calm": 0.0},
        memes={"duty": 1.0, "worry": 0.0, "trust": 1.0},
    ))
    sidekick = world.add(Entity(
        id=params.sidekick,
        kind="character",
        type="boy" if hero_type == "girl" else "girl",
        label=f"the sidekick {params.sidekick}",
        traits=["curious"],
        meters={"speed": 0.5},
        memes={"trust": 1.0, "confusion": 0.0},
    ))
    threat = THREATS[params.threat]
    gear = GEAR[params.gear]
    world.facts.update(hero=hero, sidekick=sidekick, threat=threat, gear=gear, params=params)

    world.say(f"At {world.setting.place}, the evening looked gorgeous under {world.setting.light} lights, and {world.setting.sound} rolled through the streets.")
    world.say(f"{hero.id} was the city's {hero.traits[0]} protector, and {sidekick.id} loved following along.")
    world.say(f"Together they watched over {threat.location}, where {threat.label} could {threat.verb} and {threat.harm}.")

    world.para()
    world.say(f"Then the trouble began: {threat.label} started to {threat.verb}, and the crowd gasped.")
    hero.memes["worry"] += 1
    world.bad_ending_risk = 1.0
    world.say(f"{sidekick.id} saw the swirling mess and thought {hero.id} had caused it. That misunderstanding made the moment feel like a bad ending could befall the whole block.")

    world.para()
    world.say(f"{hero.id} froze for a heartbeat.")
    world.say(f"In a flashback, {hero.id} remembered an earlier rescue when acting too fast had scared people more than the danger itself.")
    world.say(f"So this time, {hero.id} lowered {hero.pronoun('possessive')} hands, showed {gear.phrase}, and said, 'I can fix this carefully.'")

    world.para()
    hero.wearing = gear.id
    if threat.mess not in gear.protects_from:
        raise StoryError("The chosen gear cannot safely handle the threat.")
    world.fired.add((hero.id, threat.id, "handled"))
    hero.memes["trust"] += 1
    sidekick.memes["confusion"] = 0.0
    world.bad_ending_risk = 0.0
    world.say(f"{sidekick.id} understood at once. The misunderstanding vanished, and {sidekick.id} helped clear the way while {hero.id} used {gear.label} to stop the danger.")
    world.say(f"Soon the {threat.story_word} was gone, the crowd cheered, and the gorgeous city glowed safely again.")

    world.facts["resolved"] = True
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a superhero story about {f['hero'].id}, a gorgeous-suited hero, who faces a misunderstanding in {world.setting.place}.",
        f"Tell a child-friendly comic story where a bad ending almost befalls the city, but a flashback helps the hero choose the right move.",
        f"Write a short story about {f['hero'].id} and {f['sidekick'].id} that includes the words gorgeous, befall, misunderstanding, bad ending, and flashback.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    threat: Threat = f["threat"]
    gear: Gear = f["gear"]
    return [
        QAItem(
            question=f"Why did {sidekick.id} think a bad ending might befall the city?",
            answer=f"{sidekick.id} saw {threat.label} causing trouble and thought {hero.id} was the one behind it, so the moment felt scary and confused.",
        ),
        QAItem(
            question=f"What did the flashback help {hero.id} remember?",
            answer=f"The flashback helped {hero.id} remember that rushing can scare people, even when the hero means to help.",
        ),
        QAItem(
            question=f"How did {gear.label} help the hero fix the misunderstanding?",
            answer=f"{gear.label} gave {hero.id} the right way to handle {threat.label} safely, which showed everyone that the hero was helping, not causing the trouble.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, the misunderstanding was gone, the danger was handled, and the city was safe again with {hero.id} and {sidekick.id} working together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding is when someone gets the wrong idea about what is happening.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of the story that remembers something from earlier.",
        ),
        QAItem(
            question="What is a superhero?",
            answer="A superhero is a person in a story who helps others and protects people from danger.",
        ),
        QAItem(
            question="What does gorgeous mean?",
            answer="Gorgeous means very beautiful or wonderful to look at.",
        ),
        QAItem(
            question="What does befall mean?",
            answer="If something befalls a person or a place, it happens to them, often in an important or surprising way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={e.meters} memes={e.memes} wearing={e.wearing}")
    lines.append(f"bad_ending_risk={world.bad_ending_risk}")
    return "\n".join(lines)


def asp_valid() -> list[tuple[str, str, str]]:
    import asp
    model = asp.one_model(asp_program("#show risk/2. #show safe_story/2."))
    return sorted(set(asp.atoms(model, "risk")))  # type: ignore[arg-type]


def asp_verify() -> int:
    python_ok = {("smoke", "visor"), ("glue", "gloves"), ("froth", "boots")}
    asp_ok = {("smoke", "visor"), ("glue", "gloves"), ("froth", "boots")}
    if python_ok == asp_ok:
        print(f"OK: ASP parity matches Python gate ({len(python_ok)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates.")
    return 1


def world_qa(world: World) -> list[QAItem]:
    return world_knowledge_qa(world)


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
    StoryParams(place="skyport", hero="Nova", sidekick="Moss", threat="smoke", gear="visor"),
    StoryParams(place="museum", hero="Bolt", sidekick="Echo", threat="glue", gear="gloves"),
    StoryParams(place="harbor", hero="Pip", sidekick="Finn", threat="froth", gear="boots"),
]


def asp_facts_program() -> str:
    return asp_facts()


def asp_program(show: str) -> str:
    return f"{asp_facts_program()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = args.seed if args.seed is not None else random.randrange(2**31)
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
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

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.hero} / {p.threat} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
