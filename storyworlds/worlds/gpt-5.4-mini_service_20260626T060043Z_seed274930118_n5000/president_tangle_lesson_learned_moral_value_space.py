#!/usr/bin/env python3
"""
storyworlds/worlds/president_tangle_lesson_learned_moral_value_space.py
=======================================================================

A small space-adventure storyworld about a president, a troublesome tangle,
and a lesson learned that becomes a moral value.

Seed premise:
- A president leads a tiny starship mission.
- A navigation cable tangle threatens the ship's route.
- The crew must choose patience, teamwork, and careful hands over rushing.
- The ending should show the lesson learned: when problems knot up, calm
  cooperation and honesty untangle them.

The world is constraint-checked: we only generate stories where the tangle is
real, the president can meaningfully help, and the resolution changes the
physical and emotional state of the ship and crew.
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
    wears: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"president", "captain", "man", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def cap_pronoun(self, case: str = "subject") -> str:
        return self.pronoun(case).capitalize()


@dataclass
class Setting:
    place: str
    star: str
    affords: set[str] = field(default_factory=set)
    inside: bool = True


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    fixes: set[str]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.tangled: bool = False
        self.trace_notes: list[str] = []

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.tangled = self.tangled
        return c


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    tool: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "orbital_station": Setting(place="the orbital station", star="a blue star", affords={"antenna_tangle", "cable_tangle", "star_chart"}),
    "moon_dock": Setting(place="the moon dock", star="a bright planet", affords={"rope_tangle", "cable_tangle"}),
    "rocket_lab": Setting(place="the rocket lab", star="a red star", affords={"cable_tangle", "wire_tangle"}),
}

ACTIVITIES = {
    "cable_tangle": Activity(
        id="cable_tangle",
        verb="untangle the navigation cables",
        gerund="untangling the navigation cables",
        rush="grab the cables in a hurry",
        mess="tangled",
        soil="hard to read",
        risk="the route would be blocked",
        keyword="tangle",
        tags={"tangle", "space", "cable"},
    ),
    "wire_tangle": Activity(
        id="wire_tangle",
        verb="fix the control wires",
        gerund="carefully sorting the control wires",
        rush="pull the wires apart fast",
        mess="tangled",
        soil="snarled",
        risk="the console would stop answering",
        keyword="tangle",
        tags={"tangle", "space", "wire"},
    ),
    "rope_tangle": Activity(
        id="rope_tangle",
        verb="free the docking rope",
        gerund="loosening the docking rope",
        rush="yank the rope loose",
        mess="tangled",
        soil="knotted tight",
        risk="the ship would stay stuck",
        keyword="tangle",
        tags={"tangle", "space", "rope"},
    ),
    "antenna_tangle": Activity(
        id="antenna_tangle",
        verb="straighten the antenna lines",
        gerund="straightening the antenna lines",
        rush="shake the lines free",
        mess="tangled",
        soil="crossed up",
        risk="the signal would blur",
        keyword="tangle",
        tags={"tangle", "space", "signal"},
    ),
    "star_chart": Activity(
        id="star_chart",
        verb="arrange the star chart",
        gerund="laying out the star chart",
        rush="flip the chart around",
        mess="rumpled",
        soil="creased",
        risk="the map would be harder to follow",
        keyword="lesson",
        tags={"map", "space"},
    ),
}

PRIZES = {
    "map": Prize(label="map", phrase="a crisp navigation map", type="map", tags={"map"}),
    "badge": Prize(label="badge", phrase="a shiny presidential badge", type="badge", tags={"leadership"}),
    "gloves": Prize(label="gloves", phrase="a pair of white command gloves", type="gloves", tags={"gear"}),
}

TOOLS = [
    Tool(id="gloves", label="care gloves", prep="put on careful gloves first", tail="worked slowly with the gloves on", fixes={"tangled"}),
    Tool(id="clips", label="magnetic clips", prep="use magnetic clips to hold each cable", tail="used the clips to hold the lines apart", fixes={"tangled"}),
    Tool(id="guide", label="a star guide", prep="open a star guide and follow the lines one by one", tail="followed the guide line by line", fixes={"rumpled"}),
]

NAMES = {
    "girl": ["Mina", "Tara", "Nia", "Zoe", "Iris"],
    "boy": ["Ezra", "Leo", "Milo", "Finn", "Noah"],
}

TRAITS = ["calm", "brave", "curious", "careful", "steady"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = ACTIVITIES[act_id]
            for prize_id in PRIZES:
                if act.mess == "tangled" and prize_id in {"map", "gloves"}:
                    out.append((place, act_id, prize_id))
                if act.id == "star_chart" and prize_id == "map":
                    out.append((place, act_id, prize_id))
    return sorted(set(out))


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return activity.mess == "tangled" and prize.label in {"map", "badge"}


def select_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if activity.mess in tool.fixes:
            return tool
    return None


def reasonableness_check(place: str, act: str, prize: str) -> None:
    if not prize_at_risk(ACTIVITIES[act], PRIZES[prize]):
        raise StoryError("That prize would not be meaningfully threatened by this space tangle.")
    if not select_tool(ACTIVITIES[act], PRIZES[prize]):
        raise StoryError("No sensible tool exists in this world to resolve that tangle.")


def _step_tangle(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.kind != "character":
            continue
        if ent.meters.get("tangled", 0.0) < THRESHOLD:
            continue
        if ("tangle", ent.id) in world.fired:
            continue
        world.fired.add(("tangle", ent.id))
        ent.memes["stress"] = ent.memes.get("stress", 0.0) + 1
        out.append(f"{ent.id} felt the knot of the problem getting tighter.")
    return out


def _step_solution(world: World) -> list[str]:
    out = []
    if not world.tangled:
        return out
    if world.facts.get("tool_used") and world.facts.get("lesson_chosen"):
        for ent in world.entities.values():
            if ent.kind == "character":
                ent.memes["relief"] = ent.memes.get("relief", 0.0) + 1
                ent.memes["trust"] = ent.memes.get("trust", 0.0) + 1
        world.tangled = False
        out.append("The knot loosened, and the ship could breathe again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in (_step_tangle, _step_solution):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["tangled"] = 1.0
    sim.tangled = True
    propagate(sim, narrate=False)
    prize_risk = prize_at_risk(activity, PRIZES[prize_id])
    return {"tangled": sim.tangled, "prize_risk": prize_risk}


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    president = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="the president"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=president.id))
    tool = None

    world.say(f"{president.id} was the president of a tiny starship crew, and {president.pronoun('possessive')} heart liked solving hard things.")
    world.say(f"{president.cap_pronoun()} was {trait} and trusted the crew to keep the ship steady when the stars looked far away.")
    world.say(f"On board, {president.id} kept {prize.phrase} close, because it helped guide the next jump through space.")

    world.para()
    world.say(f"One day at {setting.place}, the crew found {activity.gerund}.")
    world.say(f"The knot sat across the controls, and {activity.risk}.")
    world.say(f"{president.id} wanted to {activity.verb}, but {president.pronoun('possessive')} hands stopped when the wires looked too tight.")
    if predict_mess(world, president, activity, prize_cfg.label)["prize_risk"]:
        world.say(f'"If we rush," {president.pronoun("possessive")} helper said, "the {prize.label} will end up {activity.soil}."')
    world.say(f"{president.id} nodded, because {prize.label} was too important to spoil with hurry.")

    world.para()
    president.meters["tangled"] = 1.0
    world.tangled = True
    propagate(world, narrate=True)
    world.say(f"Instead of pulling harder, {president.id} took a slow breath and asked everyone to look at one line at a time.")
    world.say(f"{president.id} told {helper.id} to hold the loose ends while {president.pronoun('subject')} kept the middle still.")
    tool = select_tool(activity, prize_cfg)
    if not tool:
        raise StoryError("No tool fits this story; the tangle cannot be solved reasonably.")
    world.facts["tool_used"] = tool.id
    world.say(f"Then {president.id} chose to {tool.prep}, because careful work beats a quick tug in space.")
    world.say(f"{helper.id} smiled and did {tool.tail}, until the knot gave way.")

    world.para()
    world.facts["lesson_chosen"] = True
    propagate(world, narrate=True)
    president.memes["confidence"] = president.memes.get("confidence", 0.0) + 1
    helper.memes["pride"] = helper.memes.get("pride", 0.0) + 1
    world.say(f"In the end, the ship's route shone clear again, and {prize.label} stayed safe and bright.")
    world.say(f"{president.id} learned a lesson learned the hard way: some tangles only open when calm hands work together.")
    world.say(f"That became the crew's moral value too — be patient, tell the truth, and untie trouble one careful loop at a time.")

    world.facts.update(
        hero=president,
        helper=helper,
        prize=prize,
        activity=activity,
        setting=setting,
        tool=tool,
        lesson="patience",
        moral="teamwork",
    )
    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    act = f["activity"]
    return [
        f'Write a short Space Adventure story for a young child about {hero.id}, a president, and a {act.keyword} problem in space.',
        f"Tell a gentle story where {hero.id} learns a lesson learned from a tangled ship and chooses a moral value like patience.",
        f'Write a simple story that includes the words "president" and "{act.keyword}" and ends with a clear lesson learned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    prize = f["prize"]
    act = f["activity"]
    tool = f["tool"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, who is the president of a tiny starship crew.",
        ),
        QAItem(
            question=f"What problem did the crew find at {world.setting.place}?",
            answer=f"They found {act.gerund}, and the tangled wires made the route risky.",
        ),
        QAItem(
            question=f"Why did {hero.id} not rush to pull the knot apart?",
            answer=f"Because rushing could have ruined {prize.label} and made the tangle worse, so {hero.id} chose careful hands instead.",
        ),
        QAItem(
            question=f"What did {hero.id} use to help fix the tangle?",
            answer=f"{hero.id} used {tool.label} and asked {helper.id} to help hold the loose ends steady.",
        ),
        QAItem(
            question=f"What lesson learned did the president remember at the end?",
            answer="The lesson learned was that calm teamwork solves hard problems better than rushing.",
        ),
        QAItem(
            question=f"What moral value did the crew decide to follow?",
            answer="Their moral value was patience and teamwork, because those help everyone untie trouble safely.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a president?",
            answer="A president is a leader who helps make decisions and guide a group, country, or crew.",
        ),
        QAItem(
            question="What is a tangle?",
            answer="A tangle is a messy knot of things wrapped around each other, like wires or string.",
        ),
        QAItem(
            question="Why is patience helpful?",
            answer="Patience helps because it gives people time to think, slow down, and make careful choices.",
        ),
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help each other and do a job together instead of all struggling alone.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Story prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  tangled={world.tangled}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="orbital_station", activity="cable_tangle", prize="map", tool="clips", name="Mina", gender="girl", helper="assistant", trait="careful"),
    StoryParams(place="moon_dock", activity="rope_tangle", prize="badge", tool="gloves", name="Leo", gender="boy", helper="mate", trait="steady"),
    StoryParams(place="rocket_lab", activity="wire_tangle", prize="map", tool="clips", name="Iris", gender="girl", helper="engineer", trait="brave"),
]


KNOWLEDGE_ORDER = ["president", "tangle", "patience", "teamwork"]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for tag in sorted(a.tags):
            lines.append(asp.fact("tags", aid, tag))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        for tag in sorted(p.tags):
            lines.append(asp.fact("prize_tag", pid, tag))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for f in sorted(t.fixes):
            lines.append(asp.fact("fixes", t.id, f))
    return "\n".join(lines)


ASP_RULES = r"""
prize_risk(A,P) :- activity(A), prize(P), mess_of(A,tangled), prize_tag(P,map).
fix(A,P,T) :- prize_risk(A,P), tool(T), fixes(T,tangled).
valid(Place,A,P) :- affords(Place,A), prize_risk(A,P), fix(A,P,_).
valid_story(Place,A,P,T) :- valid(Place,A,P), tool(T), fix(A,P,T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space Adventure storyworld about a president, a tangle, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["assistant", "engineer", "mate"])
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.activity and args.prize:
        reasonableness_check(args.place, args.activity, args.prize)
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.activity is None or c[1] == args.activity)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid space story matches the chosen options.")
    place, activity, prize = rng.choice(combos)
    tool = args.tool or rng.choice([t.id for t in TOOLS if ACTIVITIES[activity].mess in t.fixes])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(NAMES[gender])
    helper = args.helper or rng.choice(["assistant", "engineer", "mate"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, tool=tool, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        ACTIVITIES[params.activity],
        PRIZES[params.prize],
        params.name,
        "president",
        params.helper,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=story_prompts(world),
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
        print(asp_program("#show valid_story/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = valid_combos_asp()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible combos ({len(stories)} with tool):")
        for place, act, prize in combos:
            tools = sorted(set(t for p, a, pr, t in stories if (p, a, pr) == (place, act, prize)))
            print(f"  {place:14} {act:14} {prize:8}  [{', '.join(tools)}]")
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.activity} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
