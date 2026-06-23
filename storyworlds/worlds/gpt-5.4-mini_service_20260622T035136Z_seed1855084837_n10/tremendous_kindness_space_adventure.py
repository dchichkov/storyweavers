#!/usr/bin/env python3
"""
storyworlds/worlds/gpt_5_4_mini_service_20260622T035136Z_seed1855084837_n10/tremendous_kindness_space_adventure.py
===============================================================================================================

A small storyworld about a space adventure powered by kindness.

A child or two travels in a tiny starship, meets someone in trouble, and uses a
kind, practical help to solve the problem. The world is deliberately compact:
typed entities with physical meters and emotional memes, a short forward causal
chain, a reasonableness gate, and a prose renderer that follows world state.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

THIS_FILE = Path(__file__).resolve()
for parent in THIS_FILE.parents:
    if (parent / "results.py").exists():
        sys.path.insert(0, str(parent))
        break
    if (parent / "storyworlds" / "results.py").exists():
        sys.path.insert(0, str(parent / "storyworlds"))
        break

from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    location: str = ""
    portable: bool = False
    broken: bool = False
    hungry: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Setting:
    id: str
    place: str
    starfield: str
    view: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    action: str
    risk: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Need:
    id: str
    label: str
    phrase: str
    location: str
    problem: str
    tags: set[str] = field(default_factory=set)


@dataclass
class KindGift:
    id: str
    label: str
    phrase: str
    use: str
    helps: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    setting: str
    mission: str
    need: str
    gift: str
    name: str
    sidekick: str
    seed: Optional[int] = None


SETTINGS = {
    "moonport": Setting("moonport", "the moonport", "moon dust glittered under the windows", "The dome looked out on a field of stars", {"repair", "share"}),
    "orbital_garden": Setting("orbital_garden", "the orbital garden", "tiny lights blinked among the plants", "The station's glass roof showed a huge blue planet", {"repair", "share"}),
    "star_dock": Setting("star_dock", "the star dock", "silver hulls waited in neat rows", "The dock lights shimmered on polished metal", {"repair", "share"}),
}

MISSIONS = {
    "rescue_drone": Mission("rescue_drone", "help the little rescue drone", "helping the little rescue drone", "fix the drone's broken antenna", "the drone could not answer the beacon", {"antennas", "repair", "kindness"}),
    "share_lunch": Mission("share_lunch", "share lunch with the hungry mechanic", "sharing lunch with the hungry mechanic", "share a warm lunch box", "the mechanic had missed lunch", {"food", "share", "kindness"}),
    "guide_lost_bot": Mission("guide_lost_bot", "guide the lost bot home", "guiding the lost bot home", "show the bot the right hall", "the bot kept taking the wrong turns", {"map", "guide", "kindness"}),
}

NEEDS = {
    "antenna": Need("antenna", "antenna", "a broken antenna", "near the launch pad", "the drone could not send its signal", {"antennas", "repair"}),
    "lunch": Need("lunch", "lunch box", "a lunch box with soup and bread", "by the service hatch", "the mechanic's stomach was rumbling", {"food"}),
    "map": Need("map", "map", "a blinking hallway map", "in the main corridor", "the bot was lost", {"map"}),
}

GIFTS = {
    "spare_wire": KindGift("spare_wire", "spare wire", "a coil of spare wire", "wrap the antenna back together", {"antennas"}, {"repair", "kindness"}),
    "hot_soup": KindGift("hot_soup", "hot soup", "a thermos of hot soup", "warm someone up and share it", {"food"}, {"share", "kindness"}),
    "glow_sticker": KindGift("glow_sticker", "glow sticker", "a sheet of glow stickers", "mark the right hallway", {"map"}, {"guide", "kindness"}),
}

GIRL_NAMES = ["Ava", "Mia", "Zoe", "Luna", "Nora", "Ivy"]
BOY_NAMES = ["Leo", "Ben", "Max", "Eli", "Theo", "Owen"]
SIDEKICKS = ["robot", "friend", "little pilot", "crew mate"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mission in MISSIONS.items():
            for nid, need in NEEDS.items():
                for gid, gift in GIFTS.items():
                    if need.id in gift.helps and need.tags & mission.tags:
                        if mission.id in setting.affords:
                            combos.append((sid, mid, nid, gid))
    return combos


def explain_rejection(setting: Setting, mission: Mission, need: Need, gift: KindGift) -> str:
    return (
        f"(No story: {gift.label} does not honestly solve {need.phrase} during "
        f"{mission.gerund} at {setting.place}. Try a gift that fits the need.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space-adventure kindness storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--need", choices=NEEDS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("-n", "--n", type=int, default=1)
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
              and (args.mission is None or c[1] == args.mission)
              and (args.need is None or c[2] == args.need)
              and (args.gift is None or c[3] == args.gift)]
    if args.setting and args.mission and args.need and args.gift and not combos:
        raise StoryError(explain_rejection(SETTINGS[args.setting], MISSIONS[args.mission], NEEDS[args.need], GIFTS[args.gift]))
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mission, need, gift = rng.choice(sorted(combos))
    name = args.name or rng.choice(GIRL_NAMES + BOY_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, mission=mission, need=need, gift=gift, name=name, sidekick=sidekick)


def _setup_world(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity(id="hero", kind="character", type="girl" if params.name in GIRL_NAMES else "boy", label=params.name, role="pilot"))
    buddy = w.add(Entity(id="buddy", kind="character", type="robot", label=params.sidekick, role="helper"))
    station = w.add(Entity(id="station", kind="thing", type="place", label=SETTINGS[params.setting].place, location=SETTINGS[params.setting].place))
    need = NEEDS[params.need]
    mission = MISSIONS[params.mission]
    gift = GIFTS[params.gift]
    need_ent = w.add(Entity(id="need", kind="thing", type="problem", label=need.label, phrase=need.phrase, location=need.location, broken=True, tags=set(need.tags)))
    gift_ent = w.add(Entity(id="gift", kind="thing", type="gift", label=gift.label, phrase=gift.phrase, portable=True, tags=set(gift.tags)))
    w.facts.update(hero=hero, buddy=buddy, station=station, need_ent=need_ent, gift_ent=gift_ent, setting=SETTINGS[params.setting], mission=mission, need=need, gift=gift)
    return w


def _solve_need(world: World, narrate: bool = True) -> None:
    need: Need = world.facts["need"]
    gift: KindGift = world.facts["gift"]
    mission: Mission = world.facts["mission"]
    hero: Entity = world.facts["hero"]
    need_ent: Entity = world.get("need")
    gift_ent: Entity = world.get("gift")
    sig = ("solve", need.id, gift.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    if need.id == "antenna":
        need_ent.meters["fixed"] += 1
        need_ent.broken = False
    elif need.id == "lunch":
        need_ent.meters["shared"] += 1
        need_ent.hungry = False
    else:
        need_ent.meters["guided"] += 1
    hero.memes["kindness"] += 1
    hero.memes["relief"] += 1
    gift_ent.location = need.location
    if narrate:
        world.say(f"{hero.label_word} used {gift.phrase} to {gift.use}.")
        if need.id == "antenna":
            world.say("The little signal light blinked back on at once.")
        elif need.id == "lunch":
            world.say("Warm soup filled the hatch with a cozy smell.")
        else:
            world.say("The hallway map glowed softly and pointed the way home.")


def tell(world: World) -> World:
    hero: Entity = world.facts["hero"]
    buddy: Entity = world.facts["buddy"]
    setting: Setting = world.facts["setting"]
    mission: Mission = world.facts["mission"]
    need: Need = world.facts["need"]
    gift: KindGift = world.facts["gift"]
    hero.memes["wonder"] += 1
    buddy.memes["kindness"] += 1
    world.say(f"{hero.label_word} and the {buddy.label_word} drifted into {setting.place}.")
    world.say(f"{setting.view} {setting.starfield}.")
    world.say(f"They saw {need.phrase}, and that made the day feel {mission.risk} and important.")
    world.para()
    world.say(f"{hero.label_word} had a tremendous idea: be kind first.")
    world.say(f"Instead of rushing past, {hero.label_word} chose to help with {gift.phrase}.")
    _solve_need(world)
    world.para()
    world.say(f"By the end, the {mission.label_word if hasattr(mission, 'label_word') else mission.id.replace('_', ' ')} was no longer a problem.")
    if need.id == "antenna":
        world.say("The drone chirped a happy thanks and sent its beacon again.")
    elif need.id == "lunch":
        world.say("The mechanic smiled, sat down, and ate with a full heart.")
    else:
        world.say("The lost bot rolled home beside the glowing map.")
    world.say(f"{hero.label_word} and the {buddy.label_word} flew on, feeling kind and proud.")
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(_setup_world(params))
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
        f'Write a short space adventure story for a young child that uses the word "tremendous" and shows kindness solving a problem.',
        f"Tell a gentle story about {f['hero'].label_word} and a space helper who find {f['need_ent'].phrase} and use kindness to fix it.",
        f"Write a child-friendly space adventure where a tremendous act of kindness helps at {f['setting'].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    buddy: Entity = f["buddy"]
    need: Need = f["need"]
    gift: KindGift = f["gift"]
    setting: Setting = f["setting"]
    return [
        QAItem(question=f"Who was in the space adventure at {setting.place}?", answer=f"It was about {hero.label_word} and the {buddy.label_word}. They drifted through {setting.place} and found a problem that needed kindness."),
        QAItem(question=f"What problem did they see in the story?", answer=f"They saw {need.phrase}, which was a problem because {need.problem}. That made kindness the best choice."),
        QAItem(question=f"How did {hero.label_word} help?", answer=f"{hero.label_word} used {gift.phrase} and chose to help first. That kind choice fixed the problem and made the ending feel tremendous."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    if f["need"].id == "antenna":
        return [QAItem(question="What does an antenna do on a space drone?", answer="An antenna helps a drone send and receive signals so it can ask for help or talk to others.")]
    if f["need"].id == "lunch":
        return [QAItem(question="Why is sharing lunch kind?", answer="Sharing lunch helps someone who is hungry. It gives them food and shows you care about them.")]
    return [QAItem(question="Why use a glowing map in space?", answer="A glowing map helps you see where to go in the dark. It makes travel safer and easier to follow.")]


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
        if e.label:
            bits.append(f"label={e.label}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(setting="moonport", mission="rescue_drone", need="antenna", gift="spare_wire", name="Ava", sidekick="helper"),
    StoryParams(setting="orbital_garden", mission="share_lunch", need="lunch", gift="hot_soup", name="Leo", sidekick="robot"),
    StoryParams(setting="star_dock", mission="guide_lost_bot", need="map", gift="glow_sticker", name="Mia", sidekick="crew mate"),
]


ASP_RULES = r"""
valid(S,M,N,G) :- setting(S), mission(M), need(N), gift(G), mission_affords(S,M), helps(G,N), fits(M,N).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for m in sorted(s.affords):
            lines.append(asp.fact("mission_affords", sid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for t in sorted(m.tags):
            lines.append(asp.fact("mission_tag", mid, t))
    for nid, n in NEEDS.items():
        lines.append(asp.fact("need", nid))
        for t in sorted(n.tags):
            lines.append(asp.fact("need_tag", nid, t))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        for n in sorted(g.helps):
            lines.append(asp.fact("helps", gid, n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = True
    if set(asp_valid_combos()) != set(valid_combos()):
        ok = False
        print("MISMATCH: ASP and Python valid_combos differ.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, mission=None, need=None, gift=None, name=None, sidekick=None), random.Random(7)))
        if not sample.story.strip():
            ok = False
            print("MISMATCH: generated story is empty.")
    except Exception as err:
        ok = False
        print(f"MISMATCH: normal generation failed: {err}")
    if ok:
        print("OK: ASP/Python parity and generation smoke test passed.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
