#!/usr/bin/env python3
"""
Standalone storyworld: a small space-adventure tale about a worried crew, a
missing possession, and a dialogue-based fix.

Seed premise:
- A childlike space crew member treasures one special possession.
- The possession goes missing during a small ship mission.
- The crew talks it through, searches, and finds a clever, gentle resolution.

This world keeps the stories compact, concrete, and state-driven.
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
    keeper: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "captain"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "pilot"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    detail: str


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    risk: str
    risk_kind: str
    zone: set[str]
    keyword: str
    setting: str


@dataclass
class Possession:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})


@dataclass
class Fix:
    id: str
    label: str
    offer: str
    tail: str
    covers: set[str]
    guards: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)


SETTINGS = {
    "orbital_hab": Setting(
        place="the orbital habitat",
        detail="The station lights glowed soft blue over the wide window."
    ),
    "cargo_bay": Setting(
        place="the cargo bay",
        detail="Crates floated in neat rows, and a map screen blinked above them."
    ),
    "moon_dock": Setting(
        place="the moon dock",
        detail="Dust sparkled outside the airlock, and the dome shimmered in the dark."
    ),
    "comet_post": Setting(
        place="the comet post",
        detail="A bright tail of starlight streaked past the view panel."
    ),
}

MISSIONS = {
    "drift": Mission(
        id="drift",
        verb="drift through the station tunnel",
        gerund="drifting through the station tunnel",
        risk="float away",
        risk_kind="lost",
        zone={"hands"},
        keyword="drift",
        setting="orbital_hab",
    ),
    "walk": Mission(
        id="walk",
        verb="walk across the moon dock",
        gerund="walking across the moon dock",
        risk="slip into the dust",
        risk_kind="lost",
        zone={"feet"},
        keyword="moon",
        setting="moon_dock",
    ),
    "cargo": Mission(
        id="cargo",
        verb="help sort the cargo crates",
        gerund="sorting the cargo crates",
        risk="get tucked under a crate",
        risk_kind="lost",
        zone={"hands"},
        keyword="cargo",
        setting="cargo_bay",
    ),
    "comet": Mission(
        id="comet",
        verb="watch the comet pass",
        gerund="watching the comet pass",
        risk="slide under the bench",
        risk_kind="lost",
        zone={"hands"},
        keyword="comet",
        setting="comet_post",
    ),
}

POSSESSIONS = {
    "star_badge": Possession(
        id="star_badge",
        label="star badge",
        phrase="a tiny silver star badge",
        region="chest",
    ),
    "blue_glove": Possession(
        id="blue_glove",
        label="blue glove",
        phrase="a soft blue glove",
        region="hands",
        plural=False,
    ),
    "luck_string": Possession(
        id="luck_string",
        label="lucky string",
        phrase="a lucky string bracelet",
        region="wrist",
    ),
    "mug": Possession(
        id="mug",
        label="tea mug",
        phrase="a warm tea mug with a red rocket on it",
        region="hands",
    ),
}

FIXES = [
    Fix(
        id="pocket_clip",
        label="pocket clip",
        offer="clip the badge to a pocket strap",
        tail="clipped the badge safely to the pocket strap",
        covers={"chest"},
        guards={"lost"},
    ),
    Fix(
        id="glove_tether",
        label="glove tether",
        offer="tie a short tether around the glove",
        tail="tied the glove to a wrist loop",
        covers={"hands", "wrist"},
        guards={"lost"},
    ),
    Fix(
        id="crate_tag",
        label="crate tag",
        offer="tie a bright tag to the string bracelet",
        tail="tied a bright tag to the bracelet",
        covers={"wrist"},
        guards={"lost"},
    ),
    Fix(
        id="mug_hook",
        label="mug hook",
        offer="set the mug on a hook by the wall",
        tail="set the mug on a wall hook",
        covers={"hands"},
        guards={"lost"},
    ),
]

GIRL_NAMES = ["Mira", "Nova", "Luna", "Iris", "Zia", "Pia"]
BOY_NAMES = ["Kai", "Taro", "Finn", "Jett", "Arlo", "Rio"]
TRAITS = ["fine", "brave", "curious", "gentle", "quick", "bright"]


@dataclass
class StoryParams:
    place: str
    mission: str
    possession: str
    name: str
    gender: str
    companion: str
    trait: str
    seed: Optional[int] = None


def possession_at_risk(mission: Mission, possession: Possession) -> bool:
    return possession.region in mission.zone


def select_fix(mission: Mission, possession: Possession) -> Optional[Fix]:
    for fix in FIXES:
        if mission.risk_kind in fix.guards and possession.region in fix.covers:
            return fix
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid, mission in MISSIONS.items():
            if mission.setting != place:
                continue
            for pid, pos in POSSESSIONS.items():
                if possession_at_risk(mission, pos) and select_fix(mission, pos):
                    out.append((place, mid, pid))
    return out


def reason_rejection(mission: Mission, possession: Possession) -> str:
    if not possession_at_risk(mission, possession):
        return (
            f"(No story: {mission.gerund} does not truly threaten the {possession.label}. "
            f"Try a possession worn on {sorted(mission.zone)}.)"
        )
    return (
        f"(No story: no reasonable fix in this world covers the {possession.label} "
        f"for {mission.gerund}.)"
    )


def reason_gender(possession_id: str, gender: str) -> str:
    ok = " / ".join(sorted(POSSESSIONS[possession_id].genders))
    return f"(No story: that {POSSESSIONS[possession_id].label} is not a typical {gender}'s item here; try {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure storyworld with dialogue and a missing possession.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--possession", choices=POSSESSIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=["captain", "pilot"])
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
    if args.mission and args.possession:
        mission = MISSIONS[args.mission]
        possession = POSSESSIONS[args.possession]
        if not (possession_at_risk(mission, possession) and select_fix(mission, possession)):
            raise StoryError(reason_rejection(mission, possession))
    if args.gender and args.possession and args.gender not in POSSESSIONS[args.possession].genders:
        raise StoryError(reason_gender(args.possession, args.gender))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.possession is None or c[2] == args.possession)
              and (args.gender is None or args.gender in POSSESSIONS[c[2]].genders)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    place, mission, possession = rng.choice(sorted(combos))
    pos = POSSESSIONS[possession]
    gender = args.gender or rng.choice(sorted(pos.genders))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["captain", "pilot"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, possession=possession, name=name, gender=gender,
                       companion=companion, trait=trait)


def _dialogue(world: World, speaker: str, text: str) -> None:
    world.say(f'{speaker} said, "{text}"')


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    mission = MISSIONS[params.mission]
    possession = POSSESSIONS[params.possession]
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    companion = world.add(Entity(id="Companion", kind="character", type=params.companion, label=f"the {params.companion}"))
    item = world.add(Entity(id="Item", type=possession.id, label=possession.label, phrase=possession.phrase, owner=hero.id))
    item.worn_by = hero.id

    world.say(f"{hero.id} was a fine little {params.gender} who loved the quiet hum of the ship.")
    world.say(f"{hero.pronoun('subject').capitalize()} kept {hero.pronoun('possessive')} {possession.label} close, because it felt special.")
    world.say(f"On board {setting.place}, {params.name} and {companion.label} were ready for a small mission.")

    world.say(setting.detail)
    _dialogue(world, hero.id, f"I want to {mission.verb}.")
    _dialogue(world, companion.label, f"All right, but we must keep your {possession.label} safe.")
    hero.memes["want"] = 1.0
    hero.memes["worry"] = 0.0

    world.say(f"Then {hero.id} reached for the controls, and the {possession.label} slipped from {hero.pronoun('possessive')} hand.")
    item.meters["lost"] = 1.0
    hero.memes["panic"] = 1.0
    companion.memes["alert"] = 1.0

    _dialogue(world, hero.id, f"Oh no! My {possession.label}!")
    _dialogue(world, companion.label, f"Stay calm. We will look carefully.")
    world.say(f"{hero.id} looked under a seat and beside a crate, because the {possession.label} could {mission.risk} there.")
    world.say(f"{companion.label} shone a beam of light across the floor.")

    fix = select_fix(mission, possession)
    if fix is None:
        raise StoryError(reason_rejection(mission, possession))

    _dialogue(world, companion.label, f"I have an idea: let us {fix.offer}.")
    _dialogue(world, hero.id, f"That sounds fine.")
    world.say(f"They followed the plan and {fix.tail}.")
    item.meters["lost"] = 0.0
    item.owner = hero.id
    hero.memes["panic"] = 0.0
    hero.memes["relief"] = 1.0
    hero.memes["joy"] = 1.0

    world.say(f"At last, {hero.id} smiled, and the ship felt small and safe again.")
    world.say(f"{hero.id} went back to {mission.gerund}, with the {possession.label} secure and {companion.label} nearby.")

    world.facts = {
        "hero": hero,
        "companion": companion,
        "item": item,
        "mission": mission,
        "possession": possession,
        "fix": fix,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    mission = f["mission"]
    possession = f["possession"]
    return [
        f'Write a short space-adventure story for a young child about {hero.id}, a missing {possession.label}, and a kind conversation.',
        f'Write a gentle story set on {world.setting.place} where a child wants to {mission.verb} but keeps a precious {possession.label} safe.',
        f'Write a dialogue-rich story that includes the word "possession" and ends with a safe fix on a spaceship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    companion = f["companion"]
    mission = f["mission"]
    possession = f["possession"]
    fix = f["fix"]
    place = world.setting.place
    return [
        QAItem(
            question=f"What did {hero.id} almost lose during the mission at {place}?",
            answer=f"{hero.id} almost lost {hero.pronoun('possessive')} {possession.label} while trying to {mission.verb}.",
        ),
        QAItem(
            question=f"Why did {companion.label} tell {hero.id} to stay calm?",
            answer=f"{companion.label} wanted {hero.id} to look carefully, because the {possession.label} could hide where it would {mission.risk}.",
        ),
        QAItem(
            question=f"How did they solve the problem with the {possession.label}?",
            answer=f"They used a {fix.label} and {fix.tail}, so the {possession.label} stayed safe.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and happy, because the {possession.label} was found and the mission could continue.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "possession": [
        QAItem(
            question="What is a possession?",
            answer="A possession is something that belongs to someone, like a toy, a badge, or a bracelet."
        )
    ],
    "space": [
        QAItem(
            question="What is a spaceship for?",
            answer="A spaceship is a vehicle that carries people through space."
        )
    ],
    "dialogue": [
        QAItem(
            question="What is dialogue in a story?",
            answer="Dialogue is when characters speak to each other using words in quotation marks."
        )
    ],
    "wolverine": [
        QAItem(
            question="What is a wolverine?",
            answer="A wolverine is a strong, wild animal that lives in cold places."
        )
    ],
    "fine": [
        QAItem(
            question="What can the word fine mean?",
            answer="Fine can mean calm, okay, or small and neat, depending on how it is used."
        )
    ],
}


def world_qa(world: World) -> list[QAItem]:
    out = [WORLD_KNOWLEDGE["possession"][0], WORLD_KNOWLEDGE["space"][0], WORLD_KNOWLEDGE["dialogue"][0]]
    if "wolverine" in world.facts["mission"].keyword or "wolverine" in world.facts["possession"].label:
        out.append(WORLD_KNOWLEDGE["wolverine"][0])
    out.append(WORLD_KNOWLEDGE["fine"][0])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="orbital_hab", mission="drift", possession="star_badge", name="Mira", gender="girl", companion="captain", trait="fine"),
    StoryParams(place="cargo_bay", mission="cargo", possession="blue_glove", name="Kai", gender="boy", companion="pilot", trait="curious"),
    StoryParams(place="moon_dock", mission="walk", possession="luck_string", name="Luna", gender="girl", companion="captain", trait="brave"),
    StoryParams(place="comet_post", mission="comet", possession="mug", name="Finn", gender="boy", companion="pilot", trait="gentle"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_at", mid, m.setting))
        lines.append(asp.fact("risk_kind", mid, m.risk_kind))
        for z in sorted(m.zone):
            lines.append(asp.fact("zone", mid, z))
    for oid, p in POSSESSIONS.items():
        lines.append(asp.fact("possession", oid))
        lines.append(asp.fact("region", oid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, oid))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        lines.append(asp.fact("covers", fx.id, *sorted(fx.covers)))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(M, P) :- zone(M, R), region(P, R).
has_fix(M, P) :- at_risk(M, P), fix(F), guards(F, K), risk_kind(M, K), covers(F, R), region(P, R).
valid(Place, M, P) :- mission_at(M, Place), at_risk(M, P), has_fix(M, P).
valid_story(Place, M, P, G) :- valid(Place, M, P), wears(G, P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_stories_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def resolve_from_all(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.mission and args.possession:
        mission = MISSIONS[args.mission]
        possession = POSSESSIONS[args.possession]
        if not (possession_at_risk(mission, possession) and select_fix(mission, possession)):
            raise StoryError(reason_rejection(mission, possession))
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.mission is None or c[1] == args.mission)
              and (args.possession is None or c[2] == args.possession)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, possession = rng.choice(sorted(combos))
    pos = POSSESSIONS[possession]
    gender = args.gender or rng.choice(sorted(pos.genders))
    if args.gender and args.gender not in pos.genders:
        raise StoryError(reason_gender(possession, args.gender))
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = args.companion or rng.choice(["captain", "pilot"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, possession=possession, name=name, gender=gender, companion=companion, trait=trait)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = valid_combos_asp()
        stories = valid_stories_asp()
        print(f"{len(triples)} compatible (place, mission, possession) combos ({len(stories)} with gender):\n")
        for place, mid, pid in triples:
            genders = sorted(g for (p, m, pos, g) in stories if (p, m, pos) == (place, mid, pid))
            print(f"  {place:12} {mid:10} {pid:14} [{', '.join(genders)}]")
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
                params = resolve_from_all(args, random.Random(seed))
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
            header = f"### {p.name}: {p.mission} at {p.place} (possession: {p.possession})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
