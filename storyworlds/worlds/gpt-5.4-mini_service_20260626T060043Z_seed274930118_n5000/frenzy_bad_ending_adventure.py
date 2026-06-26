#!/usr/bin/env python3
"""
Standalone story world: a tiny adventure that can end badly when a frenzy
spreads through the scene.

Premise:
- A child explorer heads into a small ruin or grove with a map and a helper.
- A tempting object or clue promises adventure.
- A risky action can stir up a frenzy in a beast, crowd, or weatherlike force.
- The ending is intentionally "bad" in the sense that the goal is not achieved,
  but the story still resolves with a clear final image.

The world is state-driven:
- physical meters: noise, fear, frenzy, dust, damage, distance
- emotional memes: courage, worry, hope, relief, regret

The narrative is designed to stay close to classic adventure style:
- a quest
- a warning
- a daring move
- a burst of chaos
- a bad ending that still feels complete
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["noise", "fear", "frenzy", "dust", "damage", "distance"]:
            self.meters.setdefault(k, 0.0)
        for k in ["courage", "worry", "hope", "relief", "regret", "delight"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    rush: str
    sound: str
    result: str
    frenzy_kind: str
    triggers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class Goal:
    label: str
    phrase: str
    type: str
    origin: str
    fragile: bool = True


@dataclass
class Threat:
    id: str
    label: str
    phrase: str
    type: str
    awakens_on: str
    fury_gain: float
    fear_gain: float
    noise_trigger: float
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.zone: str = ""
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.zone = self.zone
        c.facts = copy.deepcopy(self.facts)
        return c

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def things(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind != "character"]


def _r_frenzy(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["noise"] < THRESHOLD:
            continue
        threat = world.facts.get("threat")
        if not threat:
            continue
        for beast in world.things():
            if beast.type != "beast":
                continue
            if beast.id != threat.id:
                continue
            if beast.meters["frenzy"] >= THRESHOLD and actor.meters["noise"] >= threat.noise_trigger:
                sig = ("frenzy", beast.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                beast.meters["frenzy"] += threat.fury_gain
                actor.meters["fear"] += threat.fear_gain
                out.append(f"The {beast.label} woke in a hard frenzy.")
    return out


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    goal = world.facts.get("goal")
    if not goal:
        return out
    for actor in world.characters():
        if actor.meters["fear"] < THRESHOLD:
            continue
        treasure = world.facts.get("goal_entity")
        if not treasure:
            continue
        if treasure.carried_by != actor.id:
            continue
        sig = ("damage", treasure.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        treasure.meters["damage"] += 1
        out.append(f"{actor.pronoun('possessive').capitalize()} {treasure.label} slipped in the panic.")
    return out


def _r_baden(d world: World) -> list[str]:
    return []


CAUSAL_RULES = [
    _r_frenzy,
    _r_damage,
]


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


def setup_world(world: World, hero: Entity, guide: Entity, goal: Entity, threat: Entity, action: Action) -> None:
    world.say(f"{hero.id} was a young explorer who loved {action.verb} and old maps.")
    world.say(f"{hero.id} carried {hero.pronoun('possessive')} {goal.label} as if it might lead to treasure.")
    world.say(f"{guide.id} warned that the {threat.label} could wake if the path got too loud.")

    world.para()
    world.say(f"At {world.setting.place}, the stones were dusty and the air felt still.")
    world.say(f"{hero.id} wanted to {action.verb}, and {hero.pronoun('possessive')} heart beat fast with hope.")

    world.para()
    hero.meters["noise"] += 1
    hero.memes["courage"] += 1
    world.say(f"{hero.id} made {action.sound}, then reached for the clue.")
    world.say(f"That was enough to {action.rush}.")
    threat.meters["frenzy"] += 1
    propagate(world)

    world.para()
    hero.memes["worry"] += 1
    guide.memes["worry"] += 1
    world.say(f"The {threat.label} surged closer in a frenzy.")
    world.say(f"{guide.id} grabbed {hero.id}'s sleeve and pulled {hero.id} back.")
    world.say(f"Too late, the path shook and the map tore in the scramble.")
    goal.meters["damage"] += 1
    hero.meters["fear"] += 1

    world.para()
    world.say(f"{hero.id} did not reach the treasure.")
    world.say(f"Instead, {hero.id} and {guide.id} fled into the dusk while the {threat.label} crashed behind them.")
    world.say(f"In the end, the adventure was brave, but it ended badly: the map was ruined and the prize stayed hidden.")

    world.facts.update(hero=hero, guide=guide, goal=goal, threat=threat, action=action)
    world.facts["bad_ending"] = True


def tell_story(setting: Setting, action: Action, goal_cfg: Goal, threat_cfg: Threat,
               hero_name: str, guide_name: str, hero_type: str = "boy", guide_type: str = "man") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guide = world.add(Entity(id=guide_name, kind="character", type=guide_type))
    goal = world.add(Entity(id="goal", type=goal_cfg.type, label=goal_cfg.label, phrase=goal_cfg.phrase, owner=hero.id, carried_by=hero.id))
    threat = world.add(Entity(id=threat_cfg.id, type="beast", label=threat_cfg.label, phrase=threat_cfg.phrase))
    world.facts.update(goal_entity=goal, threat=threat)
    setup_world(world, hero, guide, goal, threat, action)
    return world


SETTINGS = {
    "ruins": Setting(place="the old ruins", indoors=False, affords={"take_path", "lift_stone"}),
    "grove": Setting(place="the moonlit grove", indoors=False, affords={"take_path", "open_door"}),
    "cave": Setting(place="the narrow cave", indoors=True, affords={"light_torch", "take_path"}),
}

ACTIONS = {
    "take_path": Action(
        id="take_path",
        verb="follow the narrow path",
        rush="wake a sleeping danger",
        sound="a quick crunch of stones",
        result="the path shook underfoot",
        frenzy_kind="noise",
        triggers={"dust"},
        tags={"adventure", "frenzy"},
    ),
    "lift_stone": Action(
        id="lift_stone",
        verb="lift the carved stone",
        rush="call out through the chamber",
        sound="a loud scrape",
        result="the carving flashed in the dark",
        frenzy_kind="noise",
        triggers={"dust"},
        tags={"adventure"},
    ),
    "open_door": Action(
        id="open_door",
        verb="open the iron door",
        rush="echo through the hall",
        sound="a long creak",
        result="the hinges groaned",
        frenzy_kind="noise",
        triggers={"noise"},
        tags={"adventure", "frenzy"},
    ),
    "light_torch": Action(
        id="light_torch",
        verb="light a torch and creep forward",
        rush="stir the bats from the rafters",
        sound="a small spark",
        result="the flame threw jagged shadows",
        frenzy_kind="noise",
        triggers={"light"},
        tags={"adventure"},
    ),
}

GOALS = {
    "map": Goal(label="map", phrase="a folded map with a red trail", type="map", origin="the village"),
    "key": Goal(label="key", phrase="a brass key with tiny teeth", type="key", origin="the village"),
    "gem": Goal(label="gem", phrase="a green gem in a cloth wrap", type="gem", origin="the village"),
}

THREATS = {
    "boar": Threat(
        id="boar",
        label="wild boar",
        phrase="a wild boar with bristly fur",
        type="beast",
        awakens_on="noise",
        fury_gain=1.0,
        fear_gain=1.0,
        noise_trigger=1.0,
        tags={"beast", "frenzy"},
    ),
    "apes": Threat(
        id="apes",
        label="tree apes",
        phrase="a troop of tree apes",
        type="beast",
        awakens_on="noise",
        fury_gain=1.0,
        fear_gain=1.0,
        noise_trigger=1.0,
        tags={"beast", "frenzy"},
    ),
}

NAMES_BOY = ["Finn", "Leo", "Owen", "Milo", "Jasper"]
NAMES_GIRL = ["Nora", "Ivy", "Mara", "Lina", "Aria"]


@dataclass
class StoryParams:
    setting: str
    action: str
    goal: str
    threat: str
    hero_name: str
    guide_name: str
    hero_type: str = "boy"
    guide_type: str = "man"
    seed: Optional[int] = None


CURATED = [
    StoryParams(setting="ruins", action="take_path", goal="map", threat="boar", hero_name="Finn", guide_name="Tomas", hero_type="boy", guide_type="man"),
    StoryParams(setting="grove", action="open_door", goal="gem", threat="apes", hero_name="Mara", guide_name="Uncle Reed", hero_type="girl", guide_type="man"),
    StoryParams(setting="cave", action="light_torch", goal="key", threat="boar", hero_name="Ivy", guide_name="Aunt Sela", hero_type="girl", guide_type="woman"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tiny adventure story world with a bad ending and a frenzy.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--threat", choices=THREATS)
    ap.add_argument("--hero-name")
    ap.add_argument("--guide-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--guide-type", choices=["man", "woman"])
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
    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(sorted(SETTINGS[setting].affords))
    goal = args.goal or rng.choice(list(GOALS))
    threat = args.threat or rng.choice(list(THREATS))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    guide_type = args.guide_type or rng.choice(["man", "woman"])
    hero_name = args.hero_name or rng.choice(NAMES_GIRL if hero_type == "girl" else NAMES_BOY)
    guide_name = args.guide_name or rng.choice(["Aunt Sela", "Uncle Reed", "Mina", "Tomas"])
    if action not in SETTINGS[setting].affords:
        raise StoryError("That action does not fit the chosen setting.")
    return StoryParams(setting=setting, action=action, goal=goal, threat=threat, hero_name=hero_name, guide_name=guide_name, hero_type=hero_type, guide_type=guide_type)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(SETTINGS[params.setting], ACTIONS[params.action], GOALS[params.goal], THREATS[params.threat], params.hero_name, params.guide_name, params.hero_type, params.guide_type)
    story = world.render()
    prompts = [
        f"Write a short adventure story where {params.hero_name} goes into {SETTINGS[params.setting].place} and a frenzy ruins the quest.",
        f"Tell a child-friendly adventure with {params.hero_name}, {params.guide_name}, and a bad ending.",
        f"Write a story about a map, a warning, and a frenzy at {SETTINGS[params.setting].place}.",
    ]
    story_qa = [
        QAItem(
            question=f"Who went on the adventure with {params.hero_name}?",
            answer=f"{params.hero_name} went with {params.guide_name}. {params.guide_name} warned about the danger, but the trip still turned bad.",
        ),
        QAItem(
            question=f"What caused the trouble in the story?",
            answer=f"The trouble came when the {THREATS[params.threat].label} woke in a frenzy after the path got too noisy.",
        ),
        QAItem(
            question="What was the ending of the adventure?",
            answer="It was a bad ending. The map tore, the goal was lost, and the explorers had to run away empty-handed.",
        ),
    ]
    world_qa = [
        QAItem(question="What is a frenzy?", answer="A frenzy is a wild burst of excitement or anger that makes something hard to control."),
        QAItem(question="What does a map do?", answer="A map shows a path or the shape of a place so people can find their way."),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


ASP_RULES = r"""
#show valid/3.
valid(Setting,Action,Goal) :- affords(Setting,Action), goal(Goal).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for gid in GOALS:
        lines.append(asp.fact("goal", gid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = {(s, a, g) for s in SETTINGS for a in SETTINGS[s].affords for g in GOALS}
    if clingo_set == py_set:
        print(f"OK: ASP matches Python ({len(py_set)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    print("only in ASP:", sorted(clingo_set - py_set))
    print("only in Python:", sorted(py_set - clingo_set))
    return 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def build_valid_combos() -> list[tuple[str, str, str]]:
    return [(s, a, g) for s in SETTINGS for a in SETTINGS[s].affords for g in GOALS]


def resolve_story_choice(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    action = args.action or rng.choice(sorted(SETTINGS[setting].affords))
    goal = args.goal or rng.choice(list(GOALS))
    threat = args.threat or rng.choice(list(THREATS))
    hero_type = args.hero_type or rng.choice(["boy", "girl"])
    guide_type = args.guide_type or rng.choice(["man", "woman"])
    hero_name = args.hero_name or rng.choice(NAMES_GIRL if hero_type == "girl" else NAMES_BOY)
    guide_name = args.guide_name or rng.choice(["Aunt Sela", "Uncle Reed", "Mina", "Tomas"])
    if action not in SETTINGS[setting].affords:
        raise StoryError("That action does not fit the chosen setting.")
    return StoryParams(setting=setting, action=action, goal=goal, threat=threat, hero_name=hero_name, guide_name=guide_name, hero_type=hero_type, guide_type=guide_type)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos")
        for s, a, g in asp_valid_combos():
            print(s, a, g)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        for i in range(max(1, args.n * 20)):
            if len(samples) >= args.n:
                break
            rng = random.Random(base_seed + i)
            try:
                params = resolve_story_choice(args, rng)
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
            header = f"### {p.hero_name}: {p.action} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
