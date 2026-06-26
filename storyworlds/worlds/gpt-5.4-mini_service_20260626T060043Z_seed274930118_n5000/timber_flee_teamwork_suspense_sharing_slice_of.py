#!/usr/bin/env python3
"""
A small slice-of-life storyworld about a timber stack, a sudden scare, and a
shared fix that only works when everyone helps.

Premise:
- A child and a friend are doing a quiet everyday task with timber.
- Their work is pleasant and ordinary: carrying planks, sorting pieces, sharing
  gloves and water, chatting about what they are making.

Turn:
- One plank shifts and the stack leans.
- The children feel suspense, then flee a few steps to stay safe.

Resolution:
- They return, share the load, and work together to steady the timber.
- The ending proves what changed: the stack is safe, the task is finished, and
  the friends are still together.

This world keeps the prose child-facing and grounded in physical state plus
simple emotions: meters for timber/stack safety, memes for worry, courage,
and teamwork.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    carries: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SharedItem:
    id: str
    label: str
    phrase: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.turn_started = False

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
        import copy as _copy

        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.turn_started = self.turn_started
        return c


def _inc(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _mem(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def _stack_tips(world: World) -> list[str]:
    out = []
    stack = world.get("timber_stack")
    if stack.meters.get("balance", 0.0) >= THRESHOLD and stack.meters.get("tipped", 0.0) < THRESHOLD:
        sig = ("tip",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        stack.meters["tipped"] = 1.0
        stack.meters["safe"] = 0.0
        for kid in world.characters():
            _mem(kid, "suspense", 1.0)
        out.append("The stack gave a small creak and leaned to one side.")
    return out


def _flee_rule(world: World) -> list[str]:
    out = []
    stack = world.get("timber_stack")
    if stack.meters.get("tipped", 0.0) < THRESHOLD:
        return out
    for kid in world.characters():
        if kid.memes.get("fear", 0.0) >= THRESHOLD and kid.meters.get("distance", 0.0) < 3.0:
            sig = ("flee", kid.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            kid.meters["distance"] = 3.0
            _mem(kid, "caution", 1.0)
            out.append(f"{kid.label.capitalize()} took a quick step back to stay safe.")
    return out


def _teamwork_rule(world: World) -> list[str]:
    out = []
    stack = world.get("timber_stack")
    if stack.meters.get("tipped", 0.0) < THRESHOLD:
        return out
    helpers = [k for k in world.characters() if k.meters.get("distance", 0.0) >= 3.0]
    if len(helpers) < 2:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    stack.meters["balance"] = 0.0
    stack.meters["tipped"] = 0.0
    stack.meters["safe"] = 1.0
    for kid in helpers:
        _mem(kid, "teamwork", 1.0)
        _mem(kid, "courage", 1.0)
        _mem(kid, "joy", 1.0)
    out.append("Together, they pushed the timber straight again.")
    return out


def _sharing_rule(world: World) -> list[str]:
    out = []
    snack = world.get("snack_bag")
    if snack.meters.get("shared", 0.0) >= THRESHOLD:
        return out
    if world.get("timber_stack").meters.get("safe", 0.0) < THRESHOLD:
        return out
    sig = ("sharing",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    snack.meters["shared"] = 1.0
    for kid in world.characters():
        _mem(kid, "calm", 1.0)
    out.append("After that, they shared the juice box and sat down to breathe.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    while changed:
        changed = False
        for rule in (_stack_tips, _flee_rule, _teamwork_rule, _sharing_rule):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_tip(world: World, actor: Entity, task: Task) -> bool:
    sim = world.copy()
    _do_task(sim, actor.id, task, narrate=False)
    return bool(sim.get("timber_stack").meters.get("tipped", 0.0) >= THRESHOLD)


def _do_task(world: World, actor_id: str, task: Task, narrate: bool = True) -> None:
    actor = world.get(actor_id)
    if task.id not in world.setting.affords:
        raise StoryError("That task doesn't fit this setting.")
    _inc(actor, task.mess, 1.0)
    _mem(actor, "enjoyment", 1.0)
    _inc(world.get("timber_stack"), "balance", 1.0)
    propagate(world, narrate=narrate)


SETTINGS = {
    "woodshop": Setting(place="the little woodshop", indoors=True, affords={"stack", "sort"}),
    "shed": Setting(place="the backyard shed", indoors=True, affords={"stack", "sort"}),
    "yard": Setting(place="the sunny yard", indoors=False, affords={"stack", "sort"}),
}

TASKS = {
    "stack": Task(
        id="stack",
        verb="stack the timber",
        gerund="stacking timber",
        rush="hurry to the stack",
        mess="dusty",
        keyword="timber",
        tags={"timber", "stack", "sharing"},
    ),
    "sort": Task(
        id="sort",
        verb="sort the timber",
        gerund="sorting timber",
        rush="run to the pile",
        mess="dusty",
        keyword="timber",
        tags={"timber", "sort", "sharing"},
    ),
}

SHARED = {
    "gloves": SharedItem(id="gloves", label="work gloves", phrase="a pair of work gloves", plural=True),
    "juice": SharedItem(id="juice", label="juice box", phrase="a cold juice box"),
    "cart": SharedItem(id="cart", label="little cart", phrase="a little rolling cart"),
}

GIRL_NAMES = ["Maya", "Lena", "Nora", "Ivy", "Zoe", "Elsa"]
BOY_NAMES = ["Theo", "Finn", "Owen", "Milo", "Eli", "Noah"]
TRAITS = ["quiet", "careful", "curious", "cheerful", "patient", "shy"]


@dataclass
class StoryParams:
    place: str
    task: str
    name: str
    friend: str
    gender: str
    seed: Optional[int] = None


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    friend = world.add(Entity(id="friend", kind="character", type="child", label=params.friend))
    stack = world.add(Entity(id="timber_stack", label="the timber stack", plural=False))
    snack = world.add(Entity(id="snack_bag", label="the snack bag"))
    gloves = world.add(Entity(id="gloves", label="work gloves", plural=True, owner=hero.id))
    cart = world.add(Entity(id="cart", label="little cart", owner=friend.id))

    stack.meters["balance"] = 0.0
    stack.meters["safe"] = 1.0
    hero.meters["distance"] = 0.0
    friend.meters["distance"] = 0.0
    hero.meters["dusty"] = 0.0
    friend.meters["dusty"] = 0.0

    task = TASKS[params.task]
    world.facts.update(hero=hero, friend=friend, task=task, stack=stack, snack=snack, gloves=gloves, cart=cart)

    world.say(f"{hero.label} and {friend.label} were in {world.setting.place}, helping with a small timber job.")
    world.say(f"They carried pieces one by one, and {hero.label} liked how the work felt calm and ordinary.")
    world.say(f"{hero.label} wore the work gloves, and {friend.label} rolled the little cart beside the stack.")

    world.para()
    world.say(f"Then {hero.label} wanted to {task.verb} a little faster.")
    if predict_tip(world, hero, task):
        _mem(hero, "fear", 1.0)
        _mem(friend, "fear", 1.0)
        world.say(f"A plank shifted, and suspense floated up like a tiny cloud.")
        world.say(f"{hero.label} and {friend.label} both {task.rush} and fled a few steps back.")
    _do_task(world, hero.id, task, narrate=True)

    world.para()
    world.say(f"They looked at each other, then at the leaning timber, and decided to handle it together.")
    _mem(hero, "sharing", 1.0)
    _mem(friend, "sharing", 1.0)
    if gloves.owner == hero.id:
        world.say(f"{hero.label} shared the gloves with {friend.label} when the next plank needed a careful grip.")
    if cart.owner == friend.id:
        world.say(f"{friend.label} shared the little cart so the heaviest pieces could roll instead of strain their arms.")
    propagate(world, narrate=True)

    world.para()
    if stack.meters.get("safe", 0.0) >= THRESHOLD:
        world.say(f"At the end, the timber stack stood straight again.")
    else:
        world.say(f"At the end, the timber stack was still a little wobbly, but they had learned to slow down together.")
    world.say(f"{hero.label} and {friend.label} sat side by side and shared the juice box, proud of the neat little job they had finished.")

    return world


def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, task = f["hero"], f["friend"], f["task"]
    return [
        f"Write a slice-of-life story about {hero.label} and {friend.label} working with timber, feeling a little suspense, and then helping each other.",
        f"Tell a gentle story where {hero.label} wants to {task.verb}, the timber stack shifts, and the children solve it through teamwork and sharing.",
        f"Write a short child-friendly story that includes timber, a quick flee for safety, and a calm ending with shared snacks.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, task, stack = f["hero"], f["friend"], f["task"], f["stack"]
    return [
        QAItem(
            question=f"What were {hero.label} and {friend.label} helping with?",
            answer=f"They were helping with a small timber job in {world.setting.place}, carrying pieces and sorting the stack.",
        ),
        QAItem(
            question=f"Why did {hero.label} and {friend.label} step back for a moment?",
            answer="A plank shifted and the timber stack leaned, so they took a quick step back to stay safe.",
        ),
        QAItem(
            question=f"What helped the timber stack become safe again?",
            answer="They worked together, used the cart and gloves carefully, and pushed the timber straight again.",
        ),
        QAItem(
            question=f"What did {hero.label} and {friend.label} share at the end?",
            answer="They shared the juice box after the work was done and sat down together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is timber?",
            answer="Timber is wood that has been cut into boards or beams for building and making things.",
        ),
        QAItem(
            question="Why do people use teamwork for heavy jobs?",
            answer="Teamwork helps because two or more people can carry, steady, and solve a hard job more safely and easily.",
        ),
        QAItem(
            question="What does sharing mean?",
            answer="Sharing means letting other people use or enjoy something together, like a snack or a tool.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
character(hero).
character(friend).
task(stack).
task(sort).

safe_if_steady :- balance(B), B >= 1.
tips :- balance(B), B >= 1, not safe_if_steady.
flee_needed :- tips.
teamwork :- flee_needed, helpers(2).
sharing :- safe_if_steady.

#show tips/0.
#show flee_needed/0.
#show teamwork/0.
#show sharing/0.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for task_id, task in TASKS.items():
        lines.append(asp.fact("task", task_id))
        lines.append(asp.fact("keyword", task_id, task.keyword))
    lines.append(asp.fact("balance", 1))
    lines.append(asp.fact("helpers", 2))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program("#show tips/0."))
    asp_has = any(sym.name == "tips" for sym in model)
    py_has = True
    if asp_has == py_has:
        print("OK: ASP and Python agree on the basic suspense trigger.")
        return 0
    print("MISMATCH: ASP and Python disagree.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life timber storyworld with teamwork, suspense, and sharing.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--task", choices=TASKS.keys())
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = args.place or rng.choice(list(SETTINGS.keys()))
    task = args.task or rng.choice(list(TASKS.keys()))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend_pool = [n for n in GIRL_NAMES + BOY_NAMES if n != name]
    friend = args.friend or rng.choice(friend_pool)
    return StoryParams(place=place, task=task, name=name, friend=friend, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show tips/0.\n#show flee_needed/0.\n#show teamwork/0.\n#show sharing/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp

        model = asp.one_model(asp_program("#show tips/0.\n#show flee_needed/0.\n#show teamwork/0.\n#show sharing/0."))
        print("ASP model:")
        for atom in model:
            print(atom)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="woodshop", task="stack", name="Maya", friend="Jon", gender="girl"),
            StoryParams(place="shed", task="sort", name="Theo", friend="Iris", gender="boy"),
            StoryParams(place="yard", task="stack", name="Lena", friend="Owen", gender="girl"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name} and {p.friend} at {p.place} ({p.task})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
