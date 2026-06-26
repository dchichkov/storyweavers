#!/usr/bin/env python3
"""
storyworlds/worlds/hickory_impound_mind_suspense_conflict_myth.py
==================================================================

A small mythic storyworld about a hickory staff, an impounded river, and a
troubled mind. The domain is shaped for suspense and conflict, with a turn from
fearful delay to a wise release.

The story premise:
- A young keeper guards a hickory staff.
- A river has been impounded behind a stone gate.
- The keeper's mind is burdened by a warning from the old shrine.
- The rising water creates suspense; a clash with an elder or spirit creates conflict.
- The ending proves a change in the world: water released, fear eased, and the
  hickory staff remembered as the tool that made the turn possible.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "priestess"}
        male = {"boy", "man", "father", "priest", "keeper"}
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
    affords: set[str] = field(default_factory=set)
    tone: str = "myth"


@dataclass
class Artifact:
    id: str
    label: str
    phrase: str
    region: str
    guards: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    acts_on: set[str] = field(default_factory=set)
    soothes: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.river_level: float = 0.0
        self.gate_closed: bool = True
        self.suspense: float = 0.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.river_level = self.river_level
        clone.gate_closed = self.gate_closed
        clone.suspense = self.suspense
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_rising_water(world: World) -> list[str]:
    out: list[str] = []
    if not world.gate_closed:
        return out
    world.river_level += 1
    world.suspense += 1
    if world.river_level >= THRESHOLD and ("rising",) not in world.fired:
        world.fired.add(("rising",))
        out.append("The impounded river pressed harder against the stone gate.")
    return out


def _r_mind_unsettled(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("fear", 0.0) >= THRESHOLD and e.memes.get("doubt", 0.0) >= THRESHOLD:
            sig = ("mind_unsettled", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["suspense"] = e.memes.get("suspense", 0.0) + 1
            out.append(f"{e.id}'s mind grew still and heavy with worry.")
    return out


def _r_release(world: World) -> list[str]:
    out: list[str] = []
    if world.gate_closed:
        return out
    if world.river_level <= 0:
        return out
    sig = ("release",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.river_level = 0
    out.append("The water rushed free and the basin fell quiet.")
    return out


CAUSAL_RULES = [
    Rule("rising_water", _r_rising_water),
    Rule("mind_unsettled", _r_mind_unsettled),
    Rule("release", _r_release),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def gate_compatible(setting: Setting, artifact: Artifact, tool: Tool) -> bool:
    return artifact.region in tool.acts_on and bool(tool.soothes & artifact.guards) and setting.place in {"the impound", "the river gate", "the stone basin"}


def predict_release(world: World, actor: Entity) -> dict:
    sim = world.copy()
    if "tool" in sim.facts:
        use_tool(sim, sim.get(actor.id), sim.facts["tool"], narrate=False)
    return {"released": not sim.gate_closed and sim.river_level == 0}


def use_tool(world: World, actor: Entity, tool: Tool, narrate: bool = True) -> None:
    if "hickory" not in tool.label:
        raise StoryError("Only the hickory staff can fit this mythic gate.")
    if world.setting.place not in {"the impound", "the river gate", "the stone basin"}:
        raise StoryError("This tale only unfolds at the river impound.")
    sig = ("use_tool", tool.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.gate_closed = False
    actor.memes["resolve"] = actor.memes.get("resolve", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} lifted the hickory staff and set it against the gate.")


def challenge(world: World, keeper: Entity, elder: Entity, artifact: Artifact) -> None:
    keeper.memes["fear"] = keeper.memes.get("fear", 0.0) + 1
    keeper.memes["doubt"] = keeper.memes.get("doubt", 0.0) + 1
    world.say(
        f"At the impound, {keeper.id} watched the water rise behind the stone wall, "
        f"and {keeper.pronoun('possessive')} mind filled with a hard, quiet fear."
    )
    world.say(
        f"{elder.id} warned that the gate should stay closed, for the old promise was not yet understood."
    )
    world.say(
        f"But the hickory staff in {keeper.pronoun('possessive')} hands felt warm, as if it remembered a wiser path."
    )
    world.suspense += 1


def resolution(world: World, keeper: Entity, elder: Entity, tool: Tool) -> None:
    if world.suspense >= THRESHOLD:
        world.say(
            f"{keeper.id} took one breath, met {elder.pronoun('possessive')} eyes, and chose the brave way."
        )
    use_tool(world, keeper, tool)
    propagate(world, narrate=True)
    keeper.memes["fear"] = max(0.0, keeper.memes.get("fear", 0.0) - 1)
    keeper.memes["doubt"] = max(0.0, keeper.memes.get("doubt", 0.0) - 1)
    keeper.memes["peace"] = keeper.memes.get("peace", 0.0) + 1
    world.say(
        f"The river slipped out in silver threads, and {keeper.id}'s mind grew clear like dawn after a storm."
    )


SETTINGS = {
    "impound": Setting(place="the impound", affords={"release"}),
    "river_gate": Setting(place="the river gate", affords={"release"}),
    "stone_basin": Setting(place="the stone basin", affords={"release"}),
}

ARTIFACTS = {
    "gate": Artifact(
        id="gate",
        label="stone gate",
        phrase="a stone gate over the impounded river",
        region="barrier",
        guards={"water", "fear"},
    )
}

TOOLS = {
    "hickory_staff": Tool(
        id="hickory_staff",
        label="a hickory staff",
        phrase="a hickory staff carved with old signs",
        acts_on={"barrier"},
        soothes={"water", "fear"},
    )
}

NAMES = ["Ari", "Nina", "Tarek", "Mira", "Soren", "Lina", "Kiran", "Ilya"]
ELDER_NAMES = ["Elder Thane", "Priestess Nera", "Old Orin", "Grandmother Vale"]
TRAITS = ["bold", "quiet", "thoughtful", "brave", "restless", "devout"]


@dataclass
class StoryParams:
    place: str
    name: str
    elder: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic tale of hickory, impound, and mind.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["elder", "priestess"])
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


def reasonableness_gate(place: str) -> None:
    if place not in SETTINGS:
        raise StoryError("The myth can only unfold at the impound, the river gate, or the stone basin.")


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(list(SETTINGS))
    reasonableness_gate(place)
    return StoryParams(
        place=place,
        name=args.name or rng.choice(NAMES),
        elder=args.elder or rng.choice(["elder", "priestess"]),
        trait=args.trait or rng.choice(TRAITS),
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    keeper = world.add(Entity(id=params.name, kind="character", type="keeper", traits=["young", params.trait]))
    elder = world.add(Entity(id=random.choice(ELDER_NAMES), kind="character", type="elder"))
    gate = world.add(Entity(id="gate", type="thing", label="stone gate", phrase="the stone gate"))
    staff = world.add(Entity(id="hickory_staff", type="thing", label="hickory staff", phrase="the hickory staff", owner=keeper.id))

    world.facts.update(keeper=keeper, elder=elder, gate=gate, tool=TOOLS["hickory_staff"], setting=setting)
    world.say(
        f"Long ago, {keeper.id} was a {params.trait} keeper who stood watch beside {setting.place}."
    )
    world.say(
        f"{keeper.id} guarded {staff.phrase}, a hickory staff that had been passed down through old hands."
    )
    world.say(
        f"Below the wall, the river was impounded, and everyone said its deep silence could turn to trouble."
    )

    world.para()
    challenge(world, keeper, elder, gate)
    world.para()
    resolution(world, keeper, elder, TOOLS["hickory_staff"])
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    keeper = f["keeper"]
    return [
        "Write a short mythic story for a child about a hickory staff and a trapped river.",
        f"Tell a suspenseful conflict story where {keeper.id} must face an impound and choose what the mind cannot decide alone.",
        "Make the ending feel like dawn after danger, with the river finally released.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    keeper = f["keeper"]
    elder = f["elder"]
    return [
        QAItem(
            question=f"Who guarded the hickory staff in the story?",
            answer=f"{keeper.id} guarded the hickory staff beside {world.setting.place}.",
        ),
        QAItem(
            question=f"What made {keeper.id}'s mind uneasy?",
            answer="The impounded river was rising behind the stone gate, and the elder warned that the old promise was not yet understood.",
        ),
        QAItem(
            question=f"What ended the conflict at the impound?",
            answer="The hickory staff was set against the gate, the water was released, and the fear in the keeper's mind loosened.",
        ),
        QAItem(
            question=f"Who argued for keeping the gate closed?",
            answer=f"{elder.id} argued that the gate should stay closed until the old promise was made clear.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is hickory?",
            answer="Hickory is a strong kind of wood often used for sturdy tools and staffs.",
        ),
        QAItem(
            question="What does impound mean?",
            answer="To impound water is to hold it back behind a barrier, like a gate or wall.",
        ),
        QAItem(
            question="What does it mean for a mind to be troubled?",
            answer="A troubled mind feels worried, unsure, or full of hard thoughts.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", pid)
        for pid in SETTINGS
    ]
    for pid in SETTINGS:
        lines.append(asp.fact("affords", pid, "release"))
    lines.append(asp.fact("artifact", "gate"))
    lines.append(asp.fact("artifact_region", "gate", "barrier"))
    lines.append(asp.fact("guards", "gate", "water"))
    lines.append(asp.fact("guards", "gate", "fear"))
    lines.append(asp.fact("tool", "hickory_staff"))
    lines.append(asp.fact("acts_on", "hickory_staff", "barrier"))
    lines.append(asp.fact("soothes", "hickory_staff", "water"))
    lines.append(asp.fact("soothes", "hickory_staff", "fear"))
    return "\n".join(lines)


ASP_RULES = r"""
valid_story(P) :- setting(P), affords(P, release), tool(hickory_staff), artifact(gate),
                  acts_on(hickory_staff, barrier), soothes(hickory_staff, water),
                  soothes(hickory_staff, fear).
#show valid_story/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/1."))
    asp_ok = bool(asp.atoms(model, "valid_story"))
    py_ok = True
    if asp_ok == py_ok:
        print("OK: ASP and Python reasonableness gates agree.")
        return 0
    print("MISMATCH: ASP and Python gates disagree.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"place={world.setting.place}")
    lines.append(f"river_level={world.river_level}")
    lines.append(f"gate_closed={world.gate_closed}")
    lines.append(f"suspense={world.suspense}")
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
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
    StoryParams(place="impound", name="Ari", elder="elder", trait="thoughtful"),
    StoryParams(place="river_gate", name="Mira", elder="priestess", trait="brave"),
    StoryParams(place="stone_basin", name="Tarek", elder="elder", trait="restless"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid_story/1."))
        print(asp.atoms(model, "valid_story"))
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
            header = f"### {p.name} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
