#!/usr/bin/env python3
"""
Story world: commit, bower, sound effects, teamwork, surprise, space adventure.

A child-friendly space-adventure simulation where a small crew tries to commit
to a repair mission, build a cozy bower in a station garden dome, and handle a
surprise without breaking the ship.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "captain_girl", "pilot_girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "captain_boy", "pilot_boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str
    detail: str
    afford: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    sound: str
    risk: str
    surprise: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)


@dataclass
class Reward:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    covers: set[str]
    guards: set[str]
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def crew(self) -> list[Entity]:
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone

    def wearers(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.role == "worn"]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(region in g.covers for g in self.wearers(actor) if g.label in {"space gloves", "sound shields", "repair cape"})


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "orbital_garden": Setting(
        place="the orbital garden",
        detail="A glass dome floated above the starboard hall, and a tiny bower of vines curled around a bright bench.",
        afford={"repair", "build", "listen"},
    ),
    "moon_base": Setting(
        place="the moon base",
        detail="Silver dust glimmered outside the hatch, and the base hummed like a sleepy drum.",
        afford={"repair", "build", "listen"},
    ),
    "cargo_ring": Setting(
        place="the cargo ring",
        detail="Boxes drifted in tidy rows, and the ring echoed every tap and thump.",
        afford={"repair", "listen"},
    ),
}

MISSIONS = {
    "repair_hatch": Mission(
        id="repair_hatch",
        verb="fix the jammed hatch",
        gerund="fixing the jammed hatch",
        sound="clank-clank",
        risk="the hatch could stay stuck",
        surprise="a tiny spark jumped out",
        zone={"hands", "torso"},
        tags={"space", "repair", "sound"},
    ),
    "build_bower": Mission(
        id="build_bower",
        verb="build a cozy bower",
        gerund="building the cozy bower",
        sound="swish-swish",
        risk="the vines could fall apart",
        surprise="a little robot bird zipped in",
        zone={"hands", "torso"},
        tags={"garden", "bower", "teamwork"},
    ),
    "sound_check": Mission(
        id="sound_check",
        verb="test the sound tubes",
        gerund="testing the sound tubes",
        sound="boop-boop",
        risk="the tubes could squeak too loud",
        surprise="the echo answered back",
        zone={"hands"},
        tags={"sound", "space"},
    ),
}

REWARDS = {
    "star_map": Reward(
        id="star_map",
        label="star map",
        phrase="a glowing star map",
        region="torso",
    ),
    "patch_patch": Reward(
        id="patch_patch",
        label="patch badge",
        phrase="a shiny patch badge",
        region="hands",
    ),
    "moon_flower": Reward(
        id="moon_flower",
        label="moon flower",
        phrase="a soft moon flower wreath",
        region="torso",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="space gloves",
        prep="put on space gloves first",
        tail="pulled on the space gloves and tried again",
        covers={"hands"},
        guards={"spark", "squeak"},
    ),
    Gear(
        id="shield",
        label="sound shields",
        prep="hold up the sound shields",
        tail="held up the sound shields and listened carefully",
        covers={"hands", "torso"},
        guards={"boom", "squeak", "clank"},
    ),
    Gear(
        id="cape",
        label="repair cape",
        prep="clip on the repair cape",
        tail="clipped on the repair cape and worked together",
        covers={"hands", "torso"},
        guards={"spark", "clank"},
    ),
]

GIRL_NAMES = ["Nova", "Luna", "Mira", "Ada", "Iris", "Zara"]
BOY_NAMES = ["Kai", "Orion", "Rex", "Pico", "Finn", "Jax"]
TRAITS = ["brave", "curious", "cheerful", "careful", "spirited", "kind"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
mission_ok(S, M, R) :- affords(S, M), risk_zone(M, Z), reward_zone(R, Z), fixable(M, R).
fixable(M, R) :- gear(G), guards(G, M), covers(G, Z), reward_zone(R, Z).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for z in sorted(m.zone):
            lines.append(asp.fact("risk_zone", mid, z))
    for rid, r in REWARDS.items():
        lines.append(asp.fact("reward", rid))
        lines.append(asp.fact("reward_zone", rid, r.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gd in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gd))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for mid, mission in MISSIONS.items():
            if mid not in setting.afford:
                continue
            for rid, reward in REWARDS.items():
                if reward.region in mission.zone:
                    if any(reward.region in g.covers and any(gd in mission.risk for gd in g.guards) for g in GEAR):
                        out.append((sid, mid, rid))
    return out


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show mission_ok/3."))
    return sorted(set(asp.atoms(model, "mission_ok")))


def asp_verify() -> int:
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


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mission: str
    reward: str
    name: str
    gender: str
    trait: str
    seed: Optional[int] = None


def mission_risky(mission: Mission, reward: Reward) -> bool:
    return reward.region in mission.zone


def select_gear(mission: Mission, reward: Reward) -> Optional[Gear]:
    for gear in GEAR:
        if reward.region in gear.covers and any(g in mission.risk for g in gear.guards):
            return gear
    return None


def predict(world: World, hero: Entity, mission: Mission, reward_id: str) -> dict:
    sim = world.copy()
    do_mission(sim, sim.get(hero.id), mission, narrate=False)
    reward = sim.get(reward_id)
    return {
        "ruined": reward.meters.get("scratched", 0) >= 1 or reward.meters.get("soggy", 0) >= 1,
        "teamwork": sim.facts.get("teamwork", 0),
    }


def do_mission(world: World, hero: Entity, mission: Mission, narrate: bool = True) -> None:
    world.zone = set(mission.zone)
    hero.meters[mission.id] = hero.meters.get(mission.id, 0) + 1
    hero.memes["focus"] = hero.memes.get("focus", 0) + 1
    if narrate:
        world.say(f"{hero.id} heard the {mission.sound} of the station and moved in carefully.")


def introduce(world: World, hero: Entity, mission: Mission) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'brave')} space kid who loved {mission.gerund}."
    )


def setup(world: World, hero: Entity, crewmate: Entity, reward: Entity) -> None:
    world.say(
        f"{hero.id} had a plan to commit to the mission, and {crewmate.id} carried {hero.pronoun('possessive')} {reward.label} in a padded pack."
    )


def arrive(world: World) -> None:
    world.say(f"At {world.setting.place}, {world.setting.detail}")


def want(world: World, hero: Entity, mission: Mission) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to {mission.verb}, because {mission.risk}.")


def warn(world: World, hero: Entity, mission: Mission, reward: Entity) -> bool:
    pred = predict(world, hero, mission, reward.id)
    if not pred["ruined"]:
        return False
    world.say(
        f'"Careful," {hero.pronoun("possessive")} teammate said. "If you {mission.verb}, {hero.pronoun("possessive")} {reward.label} might get bumped."'
    )
    world.facts["warning"] = True
    return True


def surprise_turn(world: World, hero: Entity, mission: Mission) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0) + 1
    world.say(f"Then, with a tiny {mission.sound}, {mission.surprise}.")


def teamwork_fix(world: World, hero: Entity, teammate: Entity, mission: Mission, reward: Entity) -> Optional[Gear]:
    gear = select_gear(mission, reward)
    if gear is None:
        return None
    world.say(
        f'{teammate.id} smiled and said, "Let us {gear.prep} and help together."'
    )
    if gear.label == "sound shields":
        world.say(f"{hero.id} and {teammate.id} stood side by side behind the shields.")
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    world.facts["teamwork"] = 1
    return gear


def finish(world: World, hero: Entity, teammate: Entity, mission: Mission, reward: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(
        f"Together they {gear.tail}. Soon {hero.id} was {mission.gerund}, {reward.phrase} stayed safe, and the bower felt warm and bright."
    )
    world.say(
        f"The little crew laughed at the last {mission.sound}, and the surprise became part of the fun."
    )


def build_world(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mission = MISSIONS[params.mission]
    reward_cfg = REWARDS[params.reward]

    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        role="hero",
        memes={"trait": params.trait},
    ))
    teammate = world.add(Entity(
        id="Moss",
        kind="character",
        type="they",
        role="teammate",
    ))
    reward = world.add(Entity(
        id="reward",
        type=reward_cfg.id,
        label=reward_cfg.label,
        phrase=reward_cfg.phrase,
        owner=hero.id,
    ))

    introduce(world, hero, mission)
    setup(world, hero, teammate, reward)
    world.para()
    arrive(world)
    want(world, hero, mission)
    warn(world, hero, mission, reward)
    surprise_turn(world, hero, mission)
    gear = teamwork_fix(world, hero, teammate, mission, reward)
    if gear is None:
        raise StoryError("No reasonable teamwork fix exists for this mission and reward.")
    world.para()
    finish(world, hero, teammate, mission, reward, gear)

    world.facts.update(
        hero=hero,
        teammate=teammate,
        reward=reward,
        mission=mission,
        gear=gear,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    return [
        f'Write a short space-adventure story about {hero.id} who wants to {mission.verb} in an orbital garden.',
        f"Tell a gentle story where teamwork helps {hero.id} handle a surprise while the ship makes {mission.sound} sounds.",
        f'Write a child-friendly story that uses the words "commit" and "bower" and ends with the crew working together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    mate = f["teammate"]
    reward = f["reward"]
    mission = f["mission"]
    gear = f["gear"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {mission.verb}, and the story showed that {mission.risk}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the surprise came?",
            answer=f"{mate.id} helped {hero.id}. They used teamwork so the mission could continue safely.",
        ),
        QAItem(
            question=f"What stayed safe while {hero.id} kept working?",
            answer=f"{reward.phrase} stayed safe because they chose {gear.label} and worked carefully together.",
        ),
        QAItem(
            question=f"Why did the crew commit to a safer way?",
            answer=f"They committed to a safer way because the surprise could have bumped or damaged the {reward.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a bower?",
            answer="A bower is a cozy little shelter or nook, often made from branches or vines, where something can feel tucked in and safe.",
        ),
        QAItem(
            question="What are sound effects?",
            answer="Sound effects are special sounds that help tell a story, like clangs, beeps, boops, and soft swishes.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together so the job is easier and safer.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that happens suddenly, like a tiny robot bird or a spark that was not planned.",
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
        memes = {k: v for k, v in e.memes.items() if v and k != "trait"}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure story world: commit, bower, sound effects, teamwork, surprise.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--reward", choices=REWARDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.place or args.mission or args.reward:
        combos = [
            c for c in combos
            if (args.place is None or c[0] == args.place)
            and (args.mission is None or c[1] == args.mission)
            and (args.reward is None or c[2] == args.reward)
        ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, reward = rng.choice(sorted(combos))
    if args.gender is None:
        gender = rng.choice(["girl", "boy"])
    else:
        gender = args.gender
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, reward=reward, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
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
    StoryParams(place="orbital_garden", mission="build_bower", reward="moon_flower", name="Nova", gender="girl", trait="kind"),
    StoryParams(place="moon_base", mission="repair_hatch", reward="star_map", name="Kai", gender="boy", trait="brave"),
    StoryParams(place="cargo_ring", mission="sound_check", reward="patch_patch", name="Mira", gender="girl", trait="curious"),
]


def explain_rejection() -> str:
    return "No story: this space setup has no honest teamwork fix for the requested mission and reward."


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show mission_ok/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        items = asp_valid_combos()
        print(f"{len(items)} compatible combos:")
        for item in items:
            print(" ", item)
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
            header = f"### {p.name}: {p.mission} at {p.place} (reward: {p.reward})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
