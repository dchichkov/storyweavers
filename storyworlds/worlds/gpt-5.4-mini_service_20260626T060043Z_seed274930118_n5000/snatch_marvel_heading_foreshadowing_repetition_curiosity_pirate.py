#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/snatch_marvel_heading_foreshadowing_repetition_curiosity_pirate.py
==============================================================================================================

A small pirate-tale story world about a curious crew, a snatched clue, and a
foreshadowed search that turns wonder into a safe sharing of treasure.

Seed tale premise:
- A young pirate wants to snatch a glittering thing from a rival chest.
- A captain notices repeating signs that something important is missing.
- Curiosity and a foreshadowed warning lead the crew to a better heading.
- The ending proves the change with a vivid, child-friendly pirate image.

This script is self-contained and follows the Storyweavers world contract.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

# Narrative thresholds
THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        mapping = {"subject": "it", "object": "it", "possessive": "its"}
        if self.type in {"girl", "woman", "mother"}:
            mapping = {"subject": "she", "object": "her", "possessive": "her"}
        elif self.type in {"boy", "man", "father"}:
            mapping = {"subject": "he", "object": "him", "possessive": "his"}
        return mapping[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class ShipSetting:
    place: str = "the harbor"
    afford: set[str] = field(default_factory=set)
    style: str = "pirate tale"


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    clue: str
    weather: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    protects: set[str]
    prep: str
    tail: str
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    hero_name: str
    hero_type: str
    captain_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: ShipSetting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.heading: str = ""
        self.weather: str = ""

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.heading = self.heading
        c.weather = self.weather
        return c


def _r_miss(world: World) -> list[str]:
    out = []
    for hero in world.characters():
        if hero.memes.get("curiosity", 0) < THRESHOLD:
            continue
        if hero.memes.get("snatched", 0) < THRESHOLD:
            continue
        sig = ("miss", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["worry"] = hero.memes.get("worry", 0) + 1
        out.append(f"A bit of worry grew when the clue went missing.")
    return out


def _r_foreshadow(world: World) -> list[str]:
    out = []
    if world.facts.get("repeated_signs", 0) >= 2 and not world.facts.get("foreshadowed"):
        world.facts["foreshadowed"] = True
        out.append("The old lantern on the bow had blinked twice before, like a hint waiting to be noticed.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_foreshadow, _r_miss):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_action(world: World, hero: Entity, action: Action, narrate: bool = True) -> None:
    world.heading = action.clue
    hero.meters[action.mess] = hero.meters.get(action.mess, 0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["snatched"] = hero.memes.get("snatched", 0) + 1
    propagate(world, narrate=narrate)


def predict(world: World, hero: Entity, action: Action) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(hero.id), action, narrate=False)
    return {"worry": sim.get(hero.id).memes.get("worry", 0), "foreshadowed": sim.facts.get("foreshadowed", False)}


def introduce(world: World, hero: Entity, captain: Entity) -> None:
    world.say(
        f"At {world.setting.place}, little {hero.id} was a keen pirate who loved to marvel at shiny things, "
        f"while {captain.label} kept watch with a calm eye."
    )


def repeat_sign(world: World, hero: Entity, action: Action) -> None:
    world.facts["repeated_signs"] = world.facts.get("repeated_signs", 0) + 1
    world.say(
        f"Again and again, {hero.id} glanced toward the same clue, because curiosity tugged at {hero.pronoun('possessive')} sleeve."
    )
    world.say(f"{hero.id} was heading toward {action.clue}, one careful step at a time.")


def snatch_event(world: World, hero: Entity, prize: Entity, action: Action) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"Then {hero.id} tried to snatch the {prize.label} from the captain's chest, and the whole deck seemed to hold its breath."
    )
    world.say(f"The stolen spark looked small, but it felt like a big marvel to {hero.id}.")


def warning(world: World, captain: Entity, hero: Entity, action: Action, prize: Entity) -> None:
    pred = predict(world, hero, action)
    if pred["worry"] >= THRESHOLD:
        world.say(
            f'"That glitter may lure ye on," {captain.label} said, "but a snatch can leave a crew with no map and no cheer."'
        )
        world.say(
            f"The captain pointed to the repeated signs, and {hero.id} finally looked where the clues were leading."
        )


def turn(world: World, hero: Entity, captain: Entity, action: Action, prize: Entity, gear: Gear) -> None:
    world.say(
        f"{hero.id} blinked, then nodded. {hero.pronoun().capitalize()} had been curious for treasure, but now {hero.pronoun('subject')} was curious about the safer heading."
    )
    world.say(f"{captain.label} smiled and said, \"Come on, matey, let us follow the map instead of the snatch.\"")
    world.say(
        f"They chose to use the {gear.label}, and the crew set off by {action.clue}, with the wind puffing like a kind old drum."
    )


def resolution(world: World, hero: Entity, captain: Entity, action: Action, prize: Entity, gear: Gear) -> None:
    hero.memes["worry"] = 0
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"At the end, {hero.id} was marveling at the real treasure: {gear.prep}, a bright map, and a friend who knew the right way to go."
    )
    world.say(
        f"The {prize.label} stayed safe, and the ship sailed on by the good heading, while the lantern shone like a tiny star over calm water."
    )


SETTINGS = {
    "harbor": ShipSetting(place="the harbor", afford={"snatch", "heading"}),
    "island": ShipSetting(place="a palm island", afford={"snatch", "heading"}),
    "cove": ShipSetting(place="a moonlit cove", afford={"snatch", "heading"}),
}

ACTIONS = {
    "snatch": Action(
        id="snatch",
        verb="snatch a glittering clue",
        gerund="snatching glittering clues",
        rush="dash for the chest",
        mess="ripple",
        soil="lost and askew",
        clue="the lantern path",
        weather="breezy",
        tags={"snatch", "curiosity", "foreshadowing"},
    ),
    "heading": Action(
        id="heading",
        verb="take the heading",
        gerund="heading toward safe water",
        rush="follow the map",
        mess="calm",
        soil="still and steady",
        clue="the marked course",
        weather="breezy",
        tags={"heading", "foreshadowing", "repetition"},
    ),
}

PRIZES = {
    "map": Prize(id="map", label="map", phrase="a salt-stained map", region="hands"),
    "compass": Prize(id="compass", label="compass", phrase="a brass compass", region="hands"),
    "coin": Prize(id="coin", label="coin", phrase="a golden coin", region="hands", plural=True),
}

GEAR = [
    Gear(id="lantern", label="lantern light", protects={"dark"}, prep="follow the lantern light", tail="kept the lantern steady"),
    Gear(id="map", label="the marked map", protects={"lost"}, prep="trust the marked map", tail="held the map open"),
]

GIRL_NAMES = ["Mira", "Nell", "Ruby", "Tess", "Pip"]
BOY_NAMES = ["Finn", "Jory", "Cal", "Mack", "Owen"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for a in setting.afford:
            for p in PRIZES:
                combos.append((place, a, p))
    return combos


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return True


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    hero_name: str
    hero_type: str
    captain_type: str
    seed: Optional[int] = None


def tell(setting: ShipSetting, action: Action, prize_cfg: Prize, hero_name: str, hero_type: str, captain_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    captain = world.add(Entity(id="Captain", kind="character", type=captain_type, label="Captain Brine"))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.id, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id))
    gear = world.add(Entity(id=GEAR[1].id, type="thing", label=GEAR[1].label))

    introduce(world, hero, captain)
    world.para()
    repeat_sign(world, hero, action)
    repeat_sign(world, hero, action)
    snatch_event(world, hero, prize, action)
    warning(world, captain, hero, action, prize)
    world.para()
    turn(world, hero, captain, action, prize, GEAR[1])
    resolution(world, hero, captain, action, prize, GEAR[1])

    world.facts.update(hero=hero, captain=captain, prize=prize, action=action, gear=GEAR[1], resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short pirate tale with the words "snatch", "marvel", and "heading".',
        f"Tell a child-friendly story about {f['hero'].id} the pirate, a snatched clue, and a safer heading.",
        f"Write a pirate story that uses repetition and foreshadowing and ends with a calm sea.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, captain, prize, action = f["hero"], f["captain"], f["prize"], f["action"]
    return [
        QAItem(
            question=f"Who was the story about on the harbor?",
            answer=f"It was about {hero.id}, a little pirate, and Captain Brine, who watched the deck while the clue was being chased.",
        ),
        QAItem(
            question=f"What did {hero.id} try to do with the {prize.label}?",
            answer=f"{hero.id} tried to snatch the {prize.label} from the captain's chest because the glitter made {hero.pronoun('object')} marvel.",
        ),
        QAItem(
            question=f"How did the crew finally keep going?",
            answer=f"They stopped the snatch, listened to the warning, and followed the heading on the map instead.",
        ),
        QAItem(
            question=f"Why was the captain's warning important?",
            answer="It reminded the crew that a shiny clue can lead them the wrong way, but a safe heading keeps everyone together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a compass help sailors do?",
            answer="A compass helps sailors find direction so they can choose a heading on the water.",
        ),
        QAItem(
            question="Why is a map useful on a ship?",
            answer="A map shows where to go, which helps a crew avoid getting lost.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  heading: {world.heading}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="harbor", action="snatch", prize="map", hero_name="Mira", hero_type="girl", captain_type="man"),
    StoryParams(place="island", action="snatch", prize="compass", hero_name="Finn", hero_type="boy", captain_type="woman"),
    StoryParams(place="cove", action="heading", prize="coin", hero_name="Nell", hero_type="girl", captain_type="man"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale storyworld with snatch, marvel, and heading.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--captain-type", choices=["woman", "man"])
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
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid pirate story matches the given options.")
    place, action, prize = rng.choice(combos)
    pr = PRIZES[prize]
    hero_type = args.hero_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    captain_type = args.captain_type or rng.choice(["woman", "man"])
    return StoryParams(place=place, action=action, prize=prize, hero_name=name, hero_type=hero_type, captain_type=captain_type)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], ACTIONS[params.action], PRIZES[params.prize], params.hero_name, params.hero_type, params.captain_type)
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
place(P) :- setting(P).
action(A) :- act(A).
prize(X) :- treasure(X).

valid(P,A,T) :- setting(P), act(A), treasure(T).
valid_story(P,A,T,G) :- valid(P,A,T), hero_gender(G).
#show valid/3.
#show valid_story/4.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for a in ACTIONS:
        lines.append(asp.fact("act", a))
    for t in PRIZES:
        lines.append(asp.fact("treasure", t))
    for g in ["girl", "boy"]:
        lines.append(asp.fact("hero_gender", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
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
