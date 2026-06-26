#!/usr/bin/env python3
"""
Story world: a small adventure about teamwork, a tricky task, and a bright win.

Seed words:
- exasperate
- win
- brilliant

This world models a tiny adventure crew who must work together to cross a
challenge, avoid a bad choice that would exasperate the leader, and finally win
with a brilliant team plan.
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affordance: str = "a narrow path"


@dataclass
class Challenge:
    id: str
    name: str
    task: str
    danger: str
    turn: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    prep: str
    finish: str
    plural: bool = False


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
        clone.facts = dict(self.facts)
        return clone

    def team(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable


def _r_exasperate(world: World) -> list[str]:
    out: list[str] = []
    leader = world.entities.get("Leader")
    if not leader:
        return out
    for hero in world.team():
        if hero.memes.get("bravado", 0.0) < THRESHOLD:
            continue
        sig = ("exasperate", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        leader.memes["exasperation"] = leader.memes.get("exasperation", 0.0) + 1
        out.append(f"{leader.id} gave a long sigh; one careless move had nearly ruined the plan.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    crew = world.team()
    if len(crew) < 2:
        return out
    cooperation = sum(e.memes.get("help", 0.0) for e in crew)
    if cooperation < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in crew:
        e.memes["confidence"] = e.memes.get("confidence", 0.0) + 1
    out.append("The crew worked together, and the whole plan felt lighter and brighter.")
    return out


def _r_win(world: World) -> list[str]:
    out: list[str] = []
    goal = world.entities.get("Goal")
    leader = world.entities.get("Leader")
    if not goal or not leader:
        return out
    if goal.meters.get("progress", 0.0) < THRESHOLD:
        return out
    sig = ("win",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    leader.memes["joy"] = leader.memes.get("joy", 0.0) + 1
    out.append("At last, the goal was reached, and the crew won with a brilliant finish.")
    return out


RULES = [
    Rule("exasperate", _r_exasperate),
    Rule("teamwork", _r_teamwork),
    Rule("win", _r_win),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    setting: str
    challenge: str
    hero: str
    sidekick: str
    leader: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "forest": Setting(place="the green forest", indoor=False, affordance="a winding trail"),
    "cave": Setting(place="the echoing cave", indoor=False, affordance="a rocky tunnel"),
    "island": Setting(place="the little island", indoor=False, affordance="a sandy shore"),
}


CHALLENGES = {
    "bridge": Challenge(
        id="bridge",
        name="the broken bridge",
        task="cross the broken bridge",
        danger="the boards could slip",
        turn="find a safer way across",
        clue="a bright rope line tied to a tree",
        tags={"rope", "wood", "gap"},
    ),
    "river": Challenge(
        id="river",
        name="the rushing river",
        task="cross the rushing river",
        danger="the water pulled hard at the feet",
        turn="build a small raft",
        clue="flat sticks and vines on the bank",
        tags={"water", "raft", "sticks"},
    ),
    "tower": Challenge(
        id="tower",
        name="the hill tower",
        task="reach the hill tower",
        danger="the hill was steep and tiring",
        turn="carry supplies in pairs",
        clue="a lantern path up the hill",
        tags={"hill", "lantern", "stone"},
    ),
}


TOOLS = [
    Tool(
        id="rope",
        label="a sturdy rope",
        phrase="a sturdy rope",
        helps_with={"bridge", "river"},
        prep="tie the rope between safe spots",
        finish="followed the rope line carefully",
    ),
    Tool(
        id="raft",
        label="a small raft",
        phrase="a small raft",
        helps_with={"river"},
        prep="build a small raft from sticks and vines",
        finish="floated across together",
    ),
    Tool(
        id="lantern",
        label="a bright lantern",
        phrase="a bright lantern",
        helps_with={"tower"},
        prep="light the lantern and watch the path",
        finish="climbed by lantern-light",
    ),
]


TRAITS = ["brave", "curious", "spirited", "quick", "kind"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid, setting in SETTINGS.items():
        for cid, ch in CHALLENGES.items():
            if sid == "forest" and cid in {"bridge", "river"}:
                out.append((sid, cid))
            if sid == "cave" and cid in {"bridge", "tower"}:
                out.append((sid, cid))
            if sid == "island" and cid in {"river", "bridge"}:
                out.append((sid, cid))
    return out


def story_tool(challenge: Challenge) -> Optional[Tool]:
    for tool in TOOLS:
        if challenge.id in tool.helps_with:
            return tool
    return None


def tell(setting: Setting, challenge: Challenge, hero_name: str, sidekick_name: str,
         leader_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="boy", traits=[trait, "eager"]))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="girl", traits=["helpful"]))
    leader = world.add(Entity(id="Leader", kind="character", type="woman", label=leader_name, traits=["calm"]))
    goal = world.add(Entity(id="Goal", kind="thing", type="goal", label=challenge.name))

    world.facts.update(hero=hero, sidekick=sidekick, leader=leader, goal=goal, challenge=challenge, setting=setting)
    tool = story_tool(challenge)
    world.facts["tool"] = tool

    world.say(f"{hero.id} and {sidekick.id} were exploring {setting.place}, where {setting.affordance} led onward.")
    world.say(f"They had come to {challenge.task}, but {challenge.danger}.")

    world.para()
    hero.memes["bravado"] = 1
    world.say(f"{hero.id} wanted to rush ahead, and that would only exasperate {leader.label}.")
    world.say(f"{leader.label} pointed to {challenge.clue} and said, \"Let's use our heads and work as a team.\"")
    propagate(world)

    if tool is None:
        raise StoryError("No reasonable tool exists for this challenge.")
    if challenge.id == "bridge":
        tool_user = hero
    else:
        tool_user = sidekick
    tool_user.memes["help"] = tool_user.memes.get("help", 0.0) + 1
    world.say(f"{leader.label} showed them {tool.phrase}. {leader.label} said to {tool.prep}.")
    world.say(f"{hero.id} and {sidekick.id} listened, and the plan felt brilliant.")
    if challenge.id == "bridge":
        goal.meters["progress"] = 1
        world.say(f"They {tool.finish}, and the gap no longer looked scary.")
    elif challenge.id == "river":
        goal.meters["progress"] = 1
        world.say(f"They {tool.finish}, and the river could not stop them.")
    else:
        goal.meters["progress"] = 1
        world.say(f"They {tool.finish}, and the tower shone like a prize at the top of the hill.")

    world.para()
    propagate(world)
    if leader.memes.get("joy", 0.0) >= 1:
        world.say(f"In the end, the crew reached {goal.label}, and {leader.label} smiled at their brilliant win.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    ch: Challenge = f["challenge"]
    return [
        f'Write a short adventure story for a child about teamwork, where the phrase "{ch.task}" appears.',
        f"Tell a bright, child-friendly adventure where a brave helper learns not to rush and instead uses teamwork to win.",
        f"Write a story with the words exasperate, win, and brilliant, ending with a happy team plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    sidekick: Entity = f["sidekick"]
    leader: Entity = f["leader"]
    ch: Challenge = f["challenge"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"Who explored {world.setting.place} together?",
            answer=f"{hero.id} and {sidekick.id} explored {world.setting.place} together with {leader.label} guiding them.",
        ),
        QAItem(
            question=f"Why was {leader.label} worried at first?",
            answer=f"{leader.label} was worried because the team wanted to {ch.task}, and {ch.danger}.",
        ),
        QAItem(
            question=f"What helped the team make a brilliant plan?",
            answer=f"{tool.phrase} helped the team choose a safe way forward, so they could work together instead of rushing.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The crew reached {ch.name} and won at the end, with {leader.label} smiling at their teamwork.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other and do a job together so it becomes easier and better.",
        ),
        QAItem(
            question="What does brilliant mean?",
            answer="Brilliant means very clever, bright, or especially good.",
        ),
        QAItem(
            question="What does it mean to win?",
            answer="To win means to succeed at the goal or finish first in a game, race, or challenge.",
        ),
        QAItem(
            question="What does exasperate mean?",
            answer="To exasperate someone means to annoy them very much or make them feel frustrated.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("\n== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid, ch in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
        for tag in sorted(ch.tags):
            lines.append(asp.fact("tag", cid, tag))
    for tid, tool in [(t.id, t) for t in TOOLS]:
        lines.append(asp.fact("tool", tid))
        for c in sorted(tool.helps_with):
            lines.append(asp.fact("helps", tid, c))
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(S, C) :- setting(S), challenge(C).
helpful(T, C) :- tool(T), helps(T, C).
brilliant_plan(C) :- challenge(C), helpful(T, C).
win_story(S, C) :- valid_combo(S, C), brilliant_plan(C).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show win_story/2."))
    clingo_set = set(asp.atoms(model, "win_story"))
    python_set = set((s, c) for s, c in valid_combos() if story_tool(CHALLENGES[c]) is not None)
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure teamwork story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--leader")
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
    if args.setting and args.challenge:
        if (args.setting, args.challenge) not in combos:
            raise StoryError("That setting and challenge do not make a reasonable adventure.")
    possible = [c for c in combos
                if (not args.setting or c[0] == args.setting)
                and (not args.challenge or c[1] == args.challenge)]
    if not possible:
        raise StoryError("No valid story matches the given options.")
    setting, challenge = rng.choice(sorted(possible))
    hero = args.hero or rng.choice(["Ari", "Nico", "Mina", "Tess", "Pip", "Kai"])
    sidekick = args.sidekick or rng.choice(["Bea", "Rin", "Lola", "Jude", "Noa", "Zee"])
    leader = args.leader or rng.choice(["Captain Pine", "Ms. Stone", "Aunt Maren"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting=setting, challenge=challenge, hero=hero, sidekick=sidekick, leader=leader, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], CHALLENGES[params.challenge],
                 params.hero, params.sidekick, params.leader, params.trait)
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
    StoryParams(setting="forest", challenge="bridge", hero="Ari", sidekick="Bea", leader="Captain Pine", trait="brave"),
    StoryParams(setting="cave", challenge="tower", hero="Mina", sidekick="Jude", leader="Ms. Stone", trait="curious"),
    StoryParams(setting="island", challenge="river", hero="Kai", sidekick="Lola", leader="Aunt Maren", trait="spirited"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show win_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show win_story/2."))
        print(sorted(set(asp.atoms(model, "win_story"))))
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
