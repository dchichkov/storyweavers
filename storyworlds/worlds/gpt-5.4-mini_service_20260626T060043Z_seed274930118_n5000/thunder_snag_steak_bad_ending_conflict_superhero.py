#!/usr/bin/env python3
"""
storyworlds/worlds/thunder_snag_steak_bad_ending_conflict_superhero.py
======================================================================

A small superhero-story world with thunder, a snag, and a steak.

Premise:
- A young hero wants to help during a stormy day.
- The hero is proud, fast, and eager to do one brave thing.
- Thunder makes the scene feel urgent, but a snag in the hero's cape can turn
  a rescue into a mess.
- A steak dinner is the precious prize: the hero wants to protect it, deliver
  it, or keep it safe.

Conflict:
- The hero rushes into action.
- The cape or harness catches on something sharp or high.
- Thunder startles the hero at the worst moment.
- The steak gets dropped, ruined, or lost.

Bad ending:
- The hero does not fully fix the problem.
- A helper may arrive too late, or the hero may have to leave the steak behind.
- The last image proves what changed: the storm still rumbles, the snag still
  hurts, and the steak is gone or spoiled.

This world keeps the style close to a small, concrete superhero tale while
staying classical and constraint-checked.
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
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "heroine"}
        male = {"boy", "man", "father", "dad", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the city square"
    affords: set[str] = field(default_factory=set)


@dataclass
class Threat:
    id: str
    label: str
    verb: str
    mess: str
    zone: set[str]
    weather: str
    keyword: str


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Gear:
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.weather: str = ""
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.zone = set(self.zone)
        return clone


def _r_thunder(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("fear", 0.0) < THRESHOLD:
            continue
        sig = ("thunder", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["shaken"] = hero.memes.get("shaken", 0.0) + 1
        out.append("The thunder cracked so loudly that even the brave hero flinched.")
    return out


def _r_snag(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("rush", 0.0) < THRESHOLD:
            continue
        sig = ("snag", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["trouble"] = hero.memes.get("trouble", 0.0) + 1
        out.append("The cape snagged hard on a bent metal sign.")
    return out


def _r_drop_steak(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("trouble", 0.0) < THRESHOLD:
            continue
        for item in world.entities.values():
            if item.type != "steak":
                continue
            if item.worn_by != hero.id:
                continue
            sig = ("drop", hero.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
            item.meters["lost"] = item.meters.get("lost", 0.0) + 1
            out.append("The steak slipped away before anyone could catch it.")
    return out


CAUSAL_RULES = [_r_thunder, _r_snag, _r_drop_steak]


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


def hero_intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little superhero who loved helping people before the storm could do any harm.")


def setup(world: World, hero: Entity, friend: Entity, prize: Entity, threat: Threat) -> None:
    hero.memes["hope"] = 1
    world.say(f"One day, {hero.id} and {friend.label} stood in {world.setting.place} while {threat.label} rolled in over the rooftops.")
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {prize.label} carefully, because it was meant for a late dinner after the rescue.")


def want_help(world: World, hero: Entity, threat: Threat) -> None:
    hero.memes["rush"] = 1
    hero.memes["fear"] = 1
    world.say(f"{hero.id} wanted to save the day right away, even though the thunder already sounded close.")
    world.say(f"{hero.pronoun().capitalize()} sped toward the broken sign and the flashing wires.")


def snag_event(world: World, hero: Entity) -> None:
    world.say(f"At the worst moment, {hero.pronoun('possessive')} cape caught on a sharp edge.")
    propagate(world, narrate=True)


def bad_ending(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    if prize.meters.get("lost", 0.0) >= THRESHOLD:
        world.say(
            f"{friend.label} reached out, but it was too late. The steak was already ruined, and the storm kept rumbling above them."
        )
        world.say(
            f"{hero.id} looked at the empty hand and the torn cape, then had to head home without the dinner."
        )
    else:
        world.say(f"The rescue ended too late, and the dinner still could not be saved.")


def tell(setting: Setting, threat: Threat, prize_cfg: Prize, hero_name: str, sidekick_name: str) -> World:
    world = World(setting)
    world.weather = threat.weather

    hero = world.add(Entity(id=hero_name, kind="character", type="hero"))
    friend = world.add(Entity(id=sidekick_name, kind="character", type="friend", label=sidekick_name))
    prize = world.add(Entity(
        id="steak",
        type="steak",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=friend.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    cape = world.add(Entity(
        id="cape",
        type="cape",
        label="cape",
        phrase="a bright red cape",
        owner=hero.id,
        worn_by=hero.id,
        protective=False,
        region="back",
    ))

    hero_intro(world, hero)
    world.para()
    setup(world, hero, friend, prize, threat)
    want_help(world, hero, threat)
    snag_event(world, hero)
    world.para()
    bad_ending(world, hero, friend, prize)

    world.facts.update(
        hero=hero,
        friend=friend,
        prize=prize,
        cape=cape,
        threat=threat,
        setting=setting,
        bad_end=True,
        conflict=hero.memes.get("trouble", 0.0) >= THRESHOLD,
    )
    return world


SETTINGS = {
    "city": Setting(place="the city square", affords={"thunder"}),
    "rooftop": Setting(place="the rooftop garden", affords={"thunder"}),
    "bridge": Setting(place="the old bridge", affords={"thunder"}),
}

THREATS = {
    "thunder": Threat(
        id="thunder",
        label="thunder",
        verb="boomed",
        mess="noise",
        zone={"back", "hands"},
        weather="stormy",
        keyword="thunder",
    ),
}

PRIZES = {
    "steak": Prize(
        label="steak",
        phrase="a warm steak dinner",
        type="steak",
        region="hands",
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Iris", "Zoe"]
BOY_NAMES = ["Finn", "Leo", "Eli", "Max"]
FRIEND_NAMES = ["Ari", "Jo", "Pip", "Sam"]


@dataclass
class StoryParams:
    place: str
    threat: str
    prize: str
    name: str
    friend: str
    seed: Optional[int] = None


def reasonableness_gate(place: str, threat: str, prize: str) -> bool:
    return place in SETTINGS and threat in THREATS and prize in PRIZES


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, threat, prize) for place in SETTINGS for threat in THREATS for prize in PRIZES if reasonableness_gate(place, threat, prize)]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short superhero story for a child that includes thunder, a snag, and steak.',
        f"Tell a stormy superhero tale where {f['hero'].id} tries to help at {f['setting'].place} but the cape snags and the steak is lost.",
        "Write a bad-ending conflict story about a brave hero, thunder, and a dinner that cannot be saved.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    friend = f["friend"]
    prize = f["prize"]
    threat = f["threat"]
    place = f["setting"].place
    return [
        QAItem(
            question=f"Who tried to help in {place} when the thunder rolled in?",
            answer=f"{hero.id} tried to help in {place} while {threat.label} rumbled overhead.",
        ),
        QAItem(
            question=f"What got snagged during the rescue?",
            answer=f"{hero.pronoun('possessive').capitalize()} cape got snagged on a bent sign.",
        ),
        QAItem(
            question=f"What important dinner was the hero carrying?",
            answer=f"{hero.id} was carrying {hero.pronoun('possessive')} {prize.label}.",
        ),
        QAItem(
            question=f"Why was the ending a bad one?",
            answer=f"The ending was bad because the steak was lost and the hero had to go home without fixing everything.",
        ),
        QAItem(
            question=f"Who arrived too late to save the dinner?",
            answer=f"{friend.label} arrived too late to save the dinner.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is thunder?", answer="Thunder is the loud sound that comes after lightning flashes in a storm."),
        QAItem(question="What does it mean when something snags?", answer="When something snags, it catches on a rough edge and gets stuck."),
        QAItem(question="What is a steak?", answer="A steak is a thick piece of meat that people can cook and eat for dinner."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Threat, Prize) :- place(Place), threat(Threat), prize(Prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for t in THREATS:
        lines.append(asp.fact("threat", t))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: thunder, snag, steak, and a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    if args.place and args.place not in SETTINGS:
        raise StoryError("Invalid place.")
    if args.threat and args.threat not in THREATS:
        raise StoryError("Invalid threat.")
    if args.prize and args.prize not in PRIZES:
        raise StoryError("Invalid prize.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.threat is None or c[1] == args.threat)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, threat, prize = rng.choice(combos)
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, threat=threat, prize=prize, name=name, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], THREATS[params.threat], PRIZES[params.prize], params.name, params.friend)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_program("#show valid/3."))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for place, threat, prize in valid_combos():
            params = StoryParams(place=place, threat=threat, prize=prize, name="Maya", friend="Ari")
            samples.append(generate(params))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
