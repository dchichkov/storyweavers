#!/usr/bin/env python3
"""
storyworlds/worlds/opa_modify_soothe_teamwork_conflict_friendship_myth.py
=========================================================================

A small mythic story world about Opa, a needed modification, and a soothing
choice that turns conflict into friendship and teamwork.

Seed tale:
---
Long ago, by a silver river, a child and their Opa kept a small village safe.
A stone gate that guarded the lantern path began to crack. The villagers wanted
to rush in and force it open, but Opa said the gate could be modified with a
new rope hinge if everyone worked together.

The river spirit was angry because the old latch kept slamming in the wind.
The child wanted to soothe the spirit with a song, but one impatient friend
feared the river would swallow the path before dawn. At last, the child, Opa,
and the friend braided reeds, modified the gate, and soothed the spirit. The
river calmed, the path opened, and friendship grew stronger than the quarrel.
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
    kind: str = "thing"  # character | thing | spirit
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ("broken", "fixed", "calm", "linked"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "fear", "anger", "teamwork", "conflict", "friendship", "soothe"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother", "opa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the river gate"
    affords: set[str] = field(default_factory=set)


@dataclass
class Challenge:
    id: str
    name: str
    trouble: str
    fix: str
    soothe_target: str
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.state: dict[str, float] = {"tension": 0.0, "calm": 0.0, "repair": 0.0}
        self.scenes: list[str] = []

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
        clone.state = dict(self.state)
        clone.scenes = list(self.scenes)
        return clone


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes["conflict"] < THRESHOLD:
            continue
        sig = ("conflict", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.state["tension"] += 1
        out.append(f"The air grew sharp around {hero.id}.")
    return out


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    for spirit in world.entities.values():
        if spirit.kind != "spirit" or spirit.memes["soothe"] < THRESHOLD:
            continue
        sig = ("soothe", spirit.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        spirit.meters["calm"] += 1
        world.state["calm"] += 1
        out.append(f"The spirit's shoulders softened like rain settling into earth.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    gate = world.entities.get("gate")
    if not gate:
        return out
    if gate.meters["fixed"] >= THRESHOLD:
        return out
    if world.state["repair"] < THRESHOLD:
        return out
    sig = ("repair", gate.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    gate.meters["fixed"] += 1
    gate.meters["broken"] = max(0.0, gate.meters["broken"] - 1)
    out.append(f"The cracked gate remembered its shape and stood whole again.")
    return out


CAUSAL_RULES = [_r_conflict, _r_soothe, _r_repair]


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


def predict_repair(world: World, hero: Entity, challenge: Challenge, tool: Tool) -> bool:
    sim = world.copy()
    do_modify(sim, sim.get(hero.id), challenge, tool, narrate=False)
    return sim.entities["gate"].meters["fixed"] >= THRESHOLD


def do_modify(world: World, hero: Entity, challenge: Challenge, tool: Tool, narrate: bool = True) -> None:
    if challenge.id not in world.setting.affords:
        raise StoryError(f"(No story: {world.setting.place} cannot host the {challenge.name}.)")
    gate = world.get("gate")
    world.scenes.append("modify")
    hero.memes["teamwork"] += 1
    world.state["repair"] += 1
    gate.meters["broken"] += 0.25
    if narrate:
        world.say(
            f"{hero.id} and {world.facts['opa'].id} used {tool.label} to modify the gate with patient hands."
        )
    propagate(world, narrate=narrate)


def do_soothe(world: World, hero: Entity, spirit: Entity, narrate: bool = True) -> None:
    hero.memes["friendship"] += 1
    hero.memes["soothe"] += 1
    spirit.memes["soothe"] += 1
    world.state["calm"] += 1
    if narrate:
        world.say(
            f"{hero.id} lifted a small song to soothe {spirit.label}, and the notes drifted over the water."
        )
    propagate(world, narrate=narrate)


def opening(world: World, hero: Entity, opa: Entity, friend: Entity, challenge: Challenge) -> None:
    world.say(
        f"Long ago, {hero.id} lived beside {world.setting.place}, where {opa.id} told old stories about a gate that guarded the lantern path."
    )
    world.say(
        f"The people respected the gate, but {friend.id} feared the trouble in {challenge.trouble} and wanted the answer to come at once."
    )
    hero.memes["friendship"] += 1
    opa.memes["friendship"] += 1


def conflict_beats(world: World, hero: Entity, opa: Entity, friend: Entity, challenge: Challenge) -> None:
    hero.memes["conflict"] += 1
    friend.memes["conflict"] += 1
    world.state["tension"] += 1
    world.say(
        f"{friend.id} argued that the village should push the gate open, but {opa.id} shook his head and said the river would only fight back."
    )
    world.say(
        f"{hero.id} felt the quarrel rising like wind in reeds, yet remembered that a better answer might be to modify the gate instead of breaking it."
    )


def resolution(world: World, hero: Entity, opa: Entity, friend: Entity, spirit: Entity, challenge: Challenge, tool: Tool) -> None:
    world.para()
    world.say(
        f"{hero.id} called everyone close. {opa.id} brought the {tool.label}, and {friend.id} held the lantern steady."
    )
    do_modify(world, hero, challenge, tool, narrate=True)
    do_soothe(world, hero, spirit, narrate=True)
    friend.memes["friendship"] += 1
    opa.memes["friendship"] += 1
    hero.memes["joy"] += 1
    world.say(
        f"In the end, the gate opened without anger, the spirit grew calm, and the three stood together in warm friendship beside the shining river."
    )


SETTINGS = {
    "river_gate": Setting(place="the river gate", affords={"bridge"}),
    "moon_road": Setting(place="the moon road", affords={"bridge"}),
    "stone_hall": Setting(place="the stone hall", affords={"door"}),
}

CHALLENGES = {
    "bridge": Challenge(
        id="bridge",
        name="broken bridge",
        trouble="the old rope bridge had a split in its center",
        fix="a new rope binding",
        soothe_target="river spirit",
        keyword="modify",
    ),
    "door": Challenge(
        id="door",
        name="sealed door",
        trouble="the great door had jammed with age",
        fix="a braided hinge",
        soothe_target="watching spirit",
        keyword="soothe",
    ),
}

TOOLS = {
    "rope": Tool(id="rope", label="rope", phrase="a sturdy rope", helps="binding"),
    "reed": Tool(id="reed", label="reeds", phrase="fresh reeds", helps="braiding"),
}

HERO_NAMES = ["Lina", "Mara", "Suri", "Nia", "Tavi", "Ena"]
FRIEND_NAMES = ["Pell", "Rin", "Koa", "Jori", "Mik"]
TRAITS = ["brave", "gentle", "curious", "steadfast", "bright"]

CURATED = [
    ("river_gate", "bridge", "rope"),
    ("moon_road", "bridge", "reed"),
]

KNOWLEDGE = {
    "opa": [
        ("Who is an opa?",
         "An opa is a grandfather, and in a story he can be the wise elder who remembers old ways and helps the family."),
    ],
    "modify": [
        ("What does it mean to modify something?",
         "To modify something means to change it a little so it works better for a new need."),
    ],
    "soothe": [
        ("What does it mean to soothe someone?",
         "To soothe someone means to help them feel calm, safe, and less upset."),
    ],
    "teamwork": [
        ("What is teamwork?",
         "Teamwork is when people help each other and do a job together so it becomes easier and better."),
    ],
    "conflict": [
        ("What is conflict?",
         "Conflict is a disagreement or struggle between people who want different things."),
    ],
    "friendship": [
        ("What is friendship?",
         "Friendship is a kind relationship where people care about each other and want to help."),
    ],
}


@dataclass
class StoryParams:
    setting: str
    challenge: str
    tool: str
    hero: str
    friend: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world of Opa, modify, soothe, teamwork, conflict, and friendship.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for cid in setting.affords:
            for tid in TOOLS:
                out.append((sid, cid, tid))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.challenge is None or c[1] == args.challenge)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, challenge, tool = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, challenge=challenge, tool=tool, hero=hero, friend=friend, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.setting])
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", label=params.hero))
    opa = world.add(Entity(id="Opa", kind="character", type="opa", label="Opa"))
    friend = world.add(Entity(id=params.friend, kind="character", type="boy", label=params.friend))
    gate = world.add(Entity(id="gate", kind="thing", type="gate", label="the gate"))
    spirit = world.add(Entity(id="river-spirit", kind="spirit", type="spirit", label="the river spirit"))
    tool = world.add(Entity(id=params.tool, kind="thing", type=params.tool, label=TOOLS[params.tool].label))
    world.facts.update(hero=hero, opa=opa, friend=friend, gate=gate, spirit=spirit, tool=tool, challenge=CHALLENGES[params.challenge], params=params)
    gate.meters["broken"] = 1.0
    spirit.meters["calm"] = 0.0
    opening(world, hero, opa, friend, CHALLENGES[params.challenge])
    world.para()
    conflict_beats(world, hero, opa, friend, CHALLENGES[params.challenge])
    resolution(world, hero, opa, friend, spirit, CHALLENGES[params.challenge], tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, chal = f["hero"], f["friend"], f["challenge"]
    return [
        f'Write a short myth for a child that includes the words "opa", "modify", and "soothe".',
        f"Tell a gentle myth where {hero.id}, Opa, and {friend.id} face {chal.name}, argue for a moment, and solve it with teamwork.",
        f"Write a small story about conflict turning into friendship after a wise elder helps modify something and soothe a worried spirit.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, opa, friend, chal, tool = f["hero"], f["opa"], f["friend"], f["challenge"], f["tool"]
    return [
        QAItem(
            question=f"Who helped {hero.id} fix the problem at {world.setting.place}?",
            answer=f"{hero.id}, Opa, and {friend.id} all helped together, so the problem became a teamwork story instead of a lonely job."
        ),
        QAItem(
            question=f"What did they do to the gate in order to {chal.keyword} it?",
            answer=f"They used {tool.label} and careful hands to modify the gate, which means they changed it a little so it could work better."
        ),
        QAItem(
            question=f"Why was there conflict before the happy ending?",
            answer=f"There was conflict because {friend.id} wanted to push ahead quickly, while Opa wanted a safer way and the child had to decide whom to follow."
        ),
        QAItem(
            question=f"How was the river spirit soothed?",
            answer=f"{hero.id} sang softly to soothe the river spirit, and that calm song helped the spirit relax and let the story end peacefully."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"opa", "modify", "soothe", "teamwork", "conflict", "friendship"}
    out: list[QAItem] = []
    for tag in ["opa", "modify", "soothe", "teamwork", "conflict", "friendship"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  state: {world.state}")
    return "\n".join(lines)


ASP_RULES = r"""
tension(H) :- conflict(H).
calm(S) :- soothed(S).
teamwork(H,O,F) :- hero(H), opa(O), friend(F).
resolves(G) :- teamwork(H,O,F), fixed(G), soothed(spirit).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        lines.append(asp.fact("keyword", cid, c.keyword))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show affords/2."))
    asp_set = set(asp.atoms(model, "affords"))
    py_set = {(sid, a) for sid, s in SETTINGS.items() for a in s.affords}
    return 0 if asp_set == py_set else 1


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show affords/2."))
    return sorted(set(asp.atoms(model, "affords")))


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show affords/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(len(valid_combos()))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for setting, challenge, tool in CURATED:
            params = StoryParams(setting=setting, challenge=challenge, tool=tool,
                                 hero="Lina", friend="Pell", trait="gentle", seed=base_seed)
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
