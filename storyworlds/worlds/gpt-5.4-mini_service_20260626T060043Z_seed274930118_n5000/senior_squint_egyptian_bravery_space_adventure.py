#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/senior_squint_egyptian_bravery_space_adventure.py
=============================================================================================================

A tiny Space Adventure storyworld about a senior explorer, a harsh glare,
an Egyptian relic, and a brave choice.

Seed-imagined source tale:
---
An old space pilot named Mina loved visiting strange planets. On one bright day
she squinted at a desert moon and found an Egyptian star map in a half-buried
crate. Her little rover could not cross the hot glass dunes, and the map pointed
to a lost beacon on a far ridge. Mina felt nervous, but she put on her visor,
told herself to be brave, and walked the long way with her helper drone. In the
end she reached the beacon, and the map glowed like treasure in the dust.

World model sketch:
---
- A senior explorer can carry a little bravery meme that grows when she faces
  the unknown.
- Harsh glare or blowing dust can cause squinting.
- An Egyptian relic may be fragile or buried, and a careful choice can protect
  it.
- Courage is not superhuman: it is a state change caused by a hard but doable
  action that leads to rescue or discovery.
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
    caretakers: list[str] = field(default_factory=list)
    plural: bool = False
    worn_by: Optional[str] = None
    held_by: Optional[str] = None
    located_in: str = ""
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"woman", "girl", "mother", "pilot"}
        male = {"man", "boy", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the crimson moon"
    kind: str = "desert"
    glare: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mission:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Relic:
    label: str
    phrase: str
    type: str
    fragile: bool = False
    ancient: bool = False
    culture: str = "egyptian"
    buried: bool = False


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    protects: set[str] = field(default_factory=set)


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

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_squint(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("glare", 0.0) < THRESHOLD:
            continue
        sig = ("squint", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["squint"] = 1.0
        out.append(f"{e.id} had to squint at the bright shine.")
    return out


def _r_brave(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("fear", 0.0) < THRESHOLD:
            continue
        if e.memes.get("bravery", 0.0) < THRESHOLD:
            continue
        sig = ("brave", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["fear"] = 0.0
        e.memes["bravery"] += 1.0
        out.append(f"{e.id} steadied her breath and kept going anyway.")
    return out


def _r_reach_relic(world: World) -> list[str]:
    out: list[str] = []
    explorer = world.facts.get("explorer")
    relic = world.facts.get("relic")
    if not explorer or not relic:
        return out
    if explorer.memes.get("courage_action", 0.0) < THRESHOLD:
        return out
    sig = ("reach", explorer.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    relic.meters["found"] = 1.0
    out.append(f"At last, the Egyptian relic was safely in her hands.")
    return out


CAUSAL_RULES = [
    Rule("squint", _r_squint),
    Rule("brave", _r_brave),
    Rule("reach", _r_reach_relic),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                produced.extend(sents)
                changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_reward(world: World, explorer: Entity, mission: Mission) -> bool:
    sim = world.copy()
    sim.get(explorer.id).meters["glare"] += 1.0
    sim.get(explorer.id).memes["fear"] += 1.0
    sim.get(explorer.id).memes["bravery"] += 1.0
    sim.get(explorer.id).memes["courage_action"] += 1.0
    propagate(sim, narrate=False)
    relic = sim.facts["relic"]
    return bool(relic.meters.get("found", 0.0) >= THRESHOLD)


def introduce(world: World, explorer: Entity) -> None:
    trait = next((t for t in explorer.traits if t != "senior"), "senior")
    world.say(
        f"{explorer.id} was a senior {trait} explorer who loved quiet missions among the stars."
    )


def setup(world: World, explorer: Entity, mission: Mission, relic: Entity) -> None:
    world.say(
        f"One day, {explorer.id} landed at {world.setting.place} and found a trail that looked far too bright."
    )
    world.say(
        f"She wanted to {mission.verb}, because the clue pointed toward {relic.phrase}."
    )


def warning(world: World, explorer: Entity, mission: Mission, relic: Entity) -> None:
    explorer.meters["glare"] += 1.0
    explorer.memes["fear"] += 1.0
    world.say(
        f"The glare made {explorer.id} squint, and the hot wind made the path feel long."
    )
    if relic.buried:
        world.say(
            f"Somewhere ahead, the {relic.label} was still buried in the dust."
        )
    if not predict_reward(world, explorer, mission):
        raise StoryError("The mission does not have a believable brave turn.")


def choose_bravery(world: World, explorer: Entity, mission: Mission, tool: Entity) -> None:
    explorer.memes["bravery"] += 1.0
    explorer.memes["courage_action"] += 1.0
    world.say(
        f"{explorer.id} took a deep breath, held up the {tool.label}, and decided to be brave."
    )


def travel(world: World, explorer: Entity, mission: Mission, tool: Entity) -> None:
    world.say(
        f"Instead of turning back, she used the {tool.label} and kept walking {mission.rush}."
    )
    propagate(world, narrate=True)


def finish(world: World, explorer: Entity, relic: Entity, tool: Entity) -> None:
    world.say(
        f"In the end, {explorer.id} found the {relic.label}, brushed off the dust, and smiled at the gold glow."
    )
    if tool.label:
        world.say(
            f"Her {tool.label} was still warm from the sun, but her heart felt braver than before."
        )


SETTINGS = {
    "moonbase": Setting(place="the moon base ridge", kind="moon", glare=True, affords={"relic_hunt"}),
    "desertmoon": Setting(place="the desert moon", kind="desert", glare=True, affords={"relic_hunt"}),
    "starport": Setting(place="the starport yard", kind="spaceport", glare=False, affords={"relic_hunt"}),
}

MISSIONS = {
    "relic_hunt": Mission(
        id="relic_hunt",
        verb="follow the map to the beacon",
        gerund="following the map",
        rush="toward the far ridge",
        hazard="glare",
        risk="hard to see",
        keyword="bravery",
        tags={"space", "bravery", "egyptian"},
    ),
    "sample_search": Mission(
        id="sample_search",
        verb="collect the glowing sample",
        gerund="collecting samples",
        rush="across the bright dust",
        hazard="glare",
        risk="hard to see",
        keyword="bravery",
        tags={"space", "bravery"},
    ),
}

RELICS = {
    "star_map": Relic(
        label="star map",
        phrase="an Egyptian star map",
        type="map",
        fragile=True,
        ancient=True,
        culture="egyptian",
        buried=True,
    ),
    "scarab_box": Relic(
        label="scarab box",
        phrase="an Egyptian scarab box",
        type="box",
        fragile=True,
        ancient=True,
        culture="egyptian",
        buried=True,
    ),
}

TOOLS = {
    "visor": Tool(
        id="visor",
        label="visor",
        prep="put on the visor",
        tail="the visor kept the glare off her eyes",
        helps={"glare"},
        protects={"eyes"},
    ),
    "drone": Tool(
        id="drone",
        label="helper drone",
        prep="send the helper drone ahead",
        tail="the helper drone lit the path",
        helps={"navigation"},
    ),
    "shade_cloak": Tool(
        id="shade_cloak",
        label="shade cloak",
        prep="wrap on the shade cloak",
        tail="the shade cloak softened the sun",
        helps={"glare"},
        protects={"eyes", "face"},
    ),
}

GIRL_NAMES = ["Mina", "Nora", "Lina", "Ivy", "Zara"]
BOY_NAMES = ["Omar", "Noah", "Theo", "Eli", "Jude"]
TRAITS = ["steady", "curious", "kind", "brave", "patient"]


@dataclass
class StoryParams:
    place: str
    mission: str
    relic: str
    name: str
    gender: str
    trait: str
    tool: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos: list[tuple[str, str, str, str]] = []
    for place, setting in SETTINGS.items():
        for mission_id in setting.affords:
            for relic_id, relic in RELICS.items():
                if relic.culture == "egyptian":
                    for tool_id, tool in TOOLS.items():
                        if "glare" in tool.helps:
                            combos.append((place, mission_id, relic_id, tool_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Space Adventure story about "{f["hero"].id}" and the word "bravery".',
        f"Tell a gentle space story where {f['hero'].id} must be brave to reach {f['relic'].phrase}.",
        f"Write a child-friendly adventure in the stars with a squinting explorer, an Egyptian relic, and a brave choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    relic: Entity = f["relic"]
    mission: Mission = f["mission"]
    tool: Entity = f["tool"]
    qa = [
        QAItem(
            question=f"Who was the senior explorer in the story?",
            answer=f"{hero.id} was the senior explorer, and she was the one who kept going in the bright space light.",
        ),
        QAItem(
            question=f"What made {hero.id} squint at the start of the adventure?",
            answer=f"The bright glare on the moon or desert made {hero.id} squint before she could finish the mission.",
        ),
        QAItem(
            question=f"What Egyptian thing was {hero.id} trying to find?",
            answer=f"{hero.id} was trying to find {relic.phrase}, and it was the treasure at the end of the map.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did the {tool.label} help {hero.id} be brave?",
                answer=f"The {tool.label} helped by softening the harsh glare, so {hero.id} could keep walking {mission.rush} and reach the relic.",
            )
        )
        qa.append(
            QAItem(
                question=f"What changed in {hero.id} by the end?",
                answer=f"{hero.id} started nervous, but she chose bravery, found the relic, and ended the story feeling proud and steady.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something hard or scary even when your knees feel wobbly, because you know it is the right thing to do.",
        ),
        QAItem(
            question="Why do explorers wear visors in bright places?",
            answer="Explorers wear visors to keep sharp light and glare out of their eyes so they can see the path more clearly.",
        ),
        QAItem(
            question="What is an Egyptian relic?",
            answer="An Egyptian relic is an old object from ancient Egypt, like a map, box, statue, or charm that people keep safe because it is special.",
        ),
    ]


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
        if e.located_in:
            bits.append(f"located_in={e.located_in}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
% A hero squints when glare is present.
squints(H) :- hero(H), glare(H).

% Bravery can overcome fear when the hero chooses the mission anyway.
brave(H) :- hero(H), fear(H), courage(H).

% The relic is found when the brave action happens.
found_relic(R) :- relic(R), brave(H), mission(H, R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.glare:
            lines.append(asp.fact("glare_place", sid))
        for m in sorted(s.affords):
            lines.append(asp.fact("affords", sid, m))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission_def", mid))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic_def", rid))
        if r.culture:
            lines.append(asp.fact("culture", rid, r.culture))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_def", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure story world about bravery and an Egyptian relic.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--tool", choices=TOOLS)
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
    filtered = [
        c for c in combos
        if (args.place is None or c[0] == args.place)
        and (args.mission is None or c[1] == args.mission)
        and (args.relic is None or c[2] == args.relic)
        and (args.tool is None or c[3] == args.tool)
    ]
    if not filtered:
        raise StoryError("(No valid combination matches the given options.)")
    place, mission, relic, tool = rng.choice(sorted(filtered))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, relic=relic, name=name, gender=gender, trait=trait, tool=tool)


def make_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type="woman" if params.gender == "girl" else "man", traits=["senior", params.trait]))
    relic_def = RELICS[params.relic]
    relic = world.add(Entity(id="relic", type=relic_def.type, label=relic_def.label, phrase=relic_def.phrase, buried=relic_def.buried, located_in=world.setting.place))
    tool_def = TOOLS[params.tool]
    tool = world.add(Entity(id=tool_def.id, type="tool", label=tool_def.label))
    mission = MISSIONS[params.mission]
    world.facts.update(hero=hero, relic=relic, tool=tool, mission=mission)
    return world


def tell(params: StoryParams) -> World:
    world = make_world(params)
    hero: Entity = world.facts["hero"]
    relic: Entity = world.facts["relic"]
    tool: Entity = world.facts["tool"]
    mission: Mission = world.facts["mission"]

    introduce(world, hero)
    world.para()
    setup(world, hero, mission, relic)
    warning(world, hero, mission, relic)
    choose_bravery(world, hero, mission, tool)
    travel(world, hero, mission, tool)
    finish(world, hero, relic, tool)
    hero.memes["resolved"] = 1.0
    world.facts["resolved"] = True
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams(place="desertmoon", mission="relic_hunt", relic="star_map", name="Mina", gender="girl", trait="brave", tool="visor"),
    StoryParams(place="moonbase", mission="relic_hunt", relic="scarab_box", name="Omar", gender="boy", trait="steady", tool="shade_cloak"),
    StoryParams(place="starport", mission="sample_search", relic="star_map", name="Nora", gender="girl", trait="curious", tool="visor"),
]


def explain_invalid() -> str:
    return "(No valid combination matches the given options.)"


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
            header = f"### {p.name}: {p.mission} at {p.place} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
