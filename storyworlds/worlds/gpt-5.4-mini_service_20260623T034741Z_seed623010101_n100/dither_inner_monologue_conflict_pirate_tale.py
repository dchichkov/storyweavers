#!/usr/bin/env python3
"""
storyworlds/worlds/dither_inner_monologue_conflict_pirate_tale.py
==================================================================

A tiny pirate-style story world about a child pirate who dithers, thinks hard
inside their head, and gets pulled into a conflict before choosing a braver
course.

Seed tale:
---
A little pirate named Mira loved treasure, maps, and noisy deck games. One gray
morning, Captain Brine said the crew should sail straight into Fog Reef, where a
lost chest was said to wait. Mira wanted the chest, but she did not like the
reef. In her head she kept asking if the reef was too sharp, if the gulls were
warning them, and if the crew should dither a little longer.

While Mira dithered, First Mate Joss wanted to hurry the ship forward. He
snapped that real pirates did not pause. Mira's cheeks burned. She argued back,
then looked at the mast, the chart, and the dark water again. In the end she
noticed a safe gap in the rocks, pointed it out, and the ship slipped through
without scraping. The chest was still there, and the crew cheered when Mira's
careful choice kept the voyage safe.

World model:
---
    ship risk + dither -> tension grows; inner monologue deepens
    risk + strong warning -> conflict rises
    careful gap found -> risk drops; crew relief grows; treasure can be reached

Story goals:
---
- Pirate-tale tone with concrete ships, charts, ropes, gulls, docks, reefs.
- A clear inner monologue beat: the child's private thoughts are part of the
  story logic, not just decoration.
- A real conflict beat: a crewmate pushes, the child hesitates, then acts.
- Ending image proves the change in world state.
- Include the word "dither".
"""

from __future__ import annotations

import argparse
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    sea_mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Scenario:
    id: str
    reef: str
    dark_water: str
    safe_gap: str
    treasure: str
    warning_style: str
    inner_voice: str
    tags: set[str] = field(default_factory=set)


@dataclass
class CrewRole:
    id: str
    label: str
    type: str
    tone: str
    tags: set[str] = field(default_factory=set)


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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = {k: Entity(
            id=v.id, kind=v.kind, type=v.type, label=v.label, role=v.role,
            attrs=dict(v.attrs), meters=defaultdict(float, v.meters),
            memes=defaultdict(float, v.memes), tags=set(v.tags)
        ) for k, v in self.entities.items()}
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _r_dither(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["dither"] < THRESHOLD:
            continue
        sig = ("dither", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["tension"] += 1
        out.append("__dither__")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    mate = world.get("mate")
    if hero.memes["dither"] >= THRESHOLD and mate.memes["pressure"] >= THRESHOLD:
        sig = ("conflict", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] += 1
            mate.memes["conflict"] += 1
            out.append("__conflict__")
    return out


CAUSAL_RULES = [_r_dither, _r_conflict]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                out.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in out:
            world.say(s)
    return out


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for sid, sc in SCENARIOS.items():
        for stid, setting in SETTINGS.items():
            if sid in setting.affords:
                combos.append((stid, sid, HERO_ROLES["captain"].id))
    return combos


@dataclass
class StoryParams:
    setting: str
    scenario: str
    hero_name: str
    hero_type: str
    mate_name: str
    mate_type: str
    captain_name: str
    seed: Optional[int] = None


SETTINGS = {
    "harbor": Setting(place="the harbor", sea_mood="gray and salty", affords={"reef", "storm"}),
    "deck": Setting(place="the deck", sea_mood="windy and bright", affords={"reef", "storm"}),
    "cove": Setting(place="the cove", sea_mood="quiet and blue", affords={"reef"}),
}

SCENARIOS = {
    "reef": Scenario(
        id="reef",
        reef="Fog Reef",
        dark_water="dark water",
        safe_gap="a thin safe gap between the rocks",
        treasure="the lost chest",
        warning_style="snapped that real pirates do not dither forever",
        inner_voice="Mira wondered if the reef was too sharp, if the gulls were warning her, and if the ship should slow down",
        tags={"reef", "treasure", "gulls"},
    ),
    "storm": Scenario(
        id="storm",
        reef="Black Current",
        dark_water="rough water",
        safe_gap="a calm channel between the waves",
        treasure="the silver coin box",
        warning_style="growled that the storm would pass them by if they kept dithering",
        inner_voice="Mira wondered whether the clouds meant trouble or only noise, and if the chart could still be trusted",
        tags={"storm", "chart", "waves"},
    ),
}

HERO_ROLES = {
    "captain": CrewRole(id="captain", label="Captain Brine", type="man", tone="stern", tags={"captain"}),
    "mate": CrewRole(id="mate", label="First Mate Joss", type="boy", tone="pushy", tags={"mate"}),
}

GIRL_NAMES = ["Mira", "Nina", "Tess", "Lina", "Clara"]
BOY_NAMES = ["Joss", "Finn", "Pip", "Tate", "Remy"]


def build_world(params: StoryParams) -> World:
    if params.setting not in SETTINGS:
        raise StoryError("unknown setting")
    if params.scenario not in SCENARIOS:
        raise StoryError("unknown scenario")
    setting = SETTINGS[params.setting]
    scen = SCENARIOS[params.scenario]

    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.hero_name))
    mate = world.add(Entity(id="mate", kind="character", type=params.mate_type, label=params.mate_name, role="mate"))
    captain = world.add(Entity(id="captain", kind="character", type="man", label=params.captain_name, role="captain"))
    reef = world.add(Entity(id="reef", label=scen.reef, type="thing"))
    treasure = world.add(Entity(id="treasure", label=scen.treasure, type="thing"))
    gap = world.add(Entity(id="gap", label=scen.safe_gap, type="thing"))
    world.facts = {
        "hero": hero, "mate": mate, "captain": captain, "scenario": scen,
        "reef": reef, "treasure": treasure, "gap": gap,
        "setting": setting,
    }
    hero.memes["dither"] = 1
    hero.memes["tension"] = 0
    hero.memes["conflict"] = 0
    hero.memes["relief"] = 0
    mate.memes["pressure"] = 1
    mate.memes["conflict"] = 0
    captain.memes["calm"] = 1
    return world


def predict_gap(world: World) -> bool:
    return world.get("gap").label.startswith("a thin safe gap")


def tell(world: World) -> None:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    captain: Entity = f["captain"]
    scen: Scenario = f["scenario"]

    world.say(f"{hero.label} loved pirate games and treasure maps. On {world.setting.place}, the sea looked {world.setting.sea_mood}.")
    world.say(f"That morning, the crew stared toward {scen.reef} and {scen.treasure}. {scen.inner_voice}.")
    world.para()
    hero.memes["dither"] += 1
    propagate(world)
    world.say(f"{hero.label} dithered with one hand on the rail while {mate.label} wanted to hurry the ship on. {mate.label} {scen.warning_style}.")
    hero.memes["conflict"] += 1
    mate.memes["pressure"] += 1
    propagate(world)
    world.say(f"{hero.label}'s mind buzzed: 'What if the rocks scrape the hull? What if the chest is a trap? What if waiting is smarter?'")
    world.say(f"Then {hero.label} looked again and spotted {scen.safe_gap}. {hero.label} pointed it out before the bow drifted into danger.")
    world.para()
    hero.memes["relief"] += 1
    mate.memes["relief"] += 1
    world.get("reef").meters["risk"] = 0
    world.get("gap").meters["used"] = 1
    world.say(f"The ship slid through the gap with only a soft hush. {scen.treasure} stayed dry, and the crew's shouts turned bright and happy.")
    world.say(f"At the end, {hero.label} stood at the rail, no longer dithering, with the safe passage behind {hero.pronoun('object')} and the treasure ahead.")

    world.facts["resolved"] = True
    world.facts["found_gap"] = True


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    scen: Scenario = f["scenario"]
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    return [
        f'Write a pirate tale for a little child that uses the word "dither" and shows {hero.label} thinking hard before acting.',
        f"Tell a story where {hero.label} and {mate.label} have a conflict about sailing toward {scen.reef}, but the hero finds a safer way.",
        f"Write a short sea adventure with an inner monologue, a tense argument, and a happy ending at {scen.treasure}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mate: Entity = f["mate"]
    scen: Scenario = f["scenario"]
    return [
        QAItem(
            question=f"Why did {hero.label} dither before the ship reached {scen.reef}?",
            answer=f"{hero.label} was trying to decide whether the reef was safe. In {hero.pronoun('possessive')} head, {scen.inner_voice.lower()}, so {hero.label} hesitated until {hero.label} spotted a safer path.",
        ),
        QAItem(
            question=f"What caused the conflict between {hero.label} and {mate.label}?",
            answer=f"{mate.label} wanted to hurry the ship forward, but {hero.label} wanted to slow down and think. That disagreement turned the moment into a real conflict on the deck.",
        ),
        QAItem(
            question=f"How did {hero.label} help the crew reach {scen.treasure} safely?",
            answer=f"{hero.label} noticed {scen.safe_gap} and pointed it out before the ship scraped the rocks. Because of that careful choice, the crew sailed through safely and the treasure stayed within reach.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the start, the crew was worried and the hero was dithering. By the end, the ship had passed the danger, the crew was relieved, and {hero.label} had become the one who found the safe way through.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to dither?",
            answer="To dither means to hesitate and keep thinking instead of choosing right away. A pirate might dither when the water looks risky and the crew is rushing.",
        ),
        QAItem(
            question="What is a reef?",
            answer="A reef is a rocky place in the water. Ships can scrape it if they sail too close, so sailors try to steer around it carefully.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the voice inside a character's head. It shows what the character is worrying about, hoping for, or deciding.",
        ),
        QAItem(
            question="What does conflict mean in a story?",
            answer="Conflict is when characters want different things or disagree about what to do. That tension makes the story move until someone finds a new choice.",
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
    lines.append("== (3) World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:7} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_story_params() -> list[StoryParams]:
    out: list[StoryParams] = []
    for setting, scen, captain in valid_combos():
        out.append(StoryParams(
            setting=setting,
            scenario=scen,
            hero_name="Mira",
            hero_type="girl",
            mate_name="Joss",
            mate_type="boy",
            captain_name="Brine",
        ))
    return out


ASP_RULES = r"""
dither(H) :- hero(H), dithered(H).
conflict(H) :- hero(H), mate(M), pressure(M), dithered(H).
safer_path(G) :- gap(G), safe(G).
resolved :- safer_path(G).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for afford in sorted(SETTINGS[sid].affords):
            lines.append(asp.fact("affords", sid, afford))
    for sid, s in SCENARIOS.items():
        lines.append(asp.fact("scenario", sid))
        lines.append(asp.fact("safe", sid))
    lines.append(asp.fact("hero", "hero"))
    lines.append(asp.fact("mate", "mate"))
    lines.append(asp.fact("dithered", "hero"))
    lines.append(asp.fact("pressure", "mate"))
    lines.append(asp.fact("gap", "gap"))
    lines.append(asp.fact("safe", "gap"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show conflict/1.\n#show dither/1.\n#show resolved/0.")
    model = asp.one_model(program)
    atoms = set((s.name, len(s.arguments)) for s in model)
    if ("conflict", 1) not in atoms or ("dither", 1) not in atoms:
        print("MISMATCH: ASP model missing expected atoms.")
        return 1

    rng = random.Random(777)
    sample = generate(resolve_params(build_parser().parse_args([]), rng))
    if not sample.story or "dither" not in sample.story:
        print("MISMATCH: smoke story generation failed.")
        return 1
    print("OK: ASP and smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: pirates, dither, inner monologue, conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--scenario", choices=SCENARIOS)
    ap.add_argument("--name")
    ap.add_argument("--mate")
    ap.add_argument("--captain")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.scenario:
        combos = [c for c in combos if c[1] == args.scenario]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, scenario, _ = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(GIRL_NAMES)
    mate_name = args.mate or rng.choice([n for n in BOY_NAMES if n != hero_name])
    captain_name = args.captain or "Brine"
    return StoryParams(
        setting=setting,
        scenario=scenario,
        hero_name=hero_name,
        hero_type="girl",
        mate_name=mate_name,
        mate_type="boy",
        captain_name=captain_name,
        seed=args.seed,
    )


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("invalid setting")
    if params.scenario not in SCENARIOS:
        raise StoryError("invalid scenario")
    world = build_world(params)
    tell(world)
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
        print(asp_program("#show dither/1.\n#show conflict/1.\n#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show conflict/1.\n#show dither/1.\n#show resolved/0."))
        print("ASP atoms:", sorted((s.name, len(s.arguments)) for s in model))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in valid_story_params()]
    else:
        seen: set[str] = set()
        for i in range(max(args.n * 50, 50)):
            if len(samples) >= args.n:
                break
            seed = base_seed + i
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
