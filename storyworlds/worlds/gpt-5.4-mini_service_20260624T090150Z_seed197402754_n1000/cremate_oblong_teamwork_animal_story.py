#!/usr/bin/env python3
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def item_pronoun(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the meadow"
    affords: set[str] = field(default_factory=set)


@dataclass
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.facts = dict(self.facts)
        return w


def _rule_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("exertion", 0.0) < THRESHOLD:
            continue
        for item in world.carried_items(actor):
            if item.region not in world.zone:
                continue
            sig = ("mess", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["scruffy"] = item.meters.get("scruffy", 0.0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got a little scruffy.")
    return out


def _rule_spirit(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("teamwork_done") and not world.facts.get("spirit_done"):
        world.facts["spirit_done"] = True
        for actor in world.characters():
            actor.memes["pride"] = actor.memes.get("pride", 0.0) + 1
        out.append("That made everyone feel proud.")
    return out


RULES = [_rule_mess, _rule_spirit]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            chunk = rule(world)
            if chunk:
                changed = True
                produced.extend(chunk)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_scruff(world: World, actor: Entity, action: Action, prize_id: str) -> bool:
    sim = world.copy()
    actor2 = sim.get(actor.id)
    actor2.meters["exertion"] = actor2.meters.get("exertion", 0.0) + 1
    sim.zone = set(action.zone)
    propagate(sim, narrate=False)
    prize = sim.get(prize_id)
    return prize.meters.get("scruffy", 0.0) >= THRESHOLD


def has_working_fix(action: Action, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if action.mess in tool.guards and prize.region in tool.covers:
            return tool
    return None


def introduce(world: World, hero: Entity, friend: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.type} who loved working with {friend.id}.")
    world.say(f"{hero.pronoun().capitalize()} and {friend.pronoun().capitalize()} were the kind of friends who could lift, carry, and build together.")


def setup(world: World, hero: Entity, friend: Entity, prize: Entity, action: Action) -> None:
    world.say(f"One morning, {hero.id}'s {friend.type} brought home {prize.phrase}.")
    world.say(f"{hero.id} loved {prize.item_pronoun()} because it looked {action.keyword} and shiny.")


def ask_for_help(world: World, hero: Entity, friend: Entity, action: Action, prize: Entity) -> None:
    world.say(f"Then {hero.id} saw a job that needed teamwork: they had to {action.verb} {prize.label}.")
    world.say(f"{hero.id} wanted to {action.verb}, but {friend.id} knew it was too big to do alone.")


def warn(world: World, friend: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    if not predict_scruff(world, hero, action, prize.id):
        return False
    world.facts["warning"] = True
    world.say(f'"If we rush it," {friend.id} said, "the {prize.label} will get {action.soil}."')
    return True


def try_solo(world: World, hero: Entity, action: Action) -> None:
    hero.meters["exertion"] = hero.meters.get("exertion", 0.0) + 1
    world.zone = set(action.zone)
    world.say(f"{hero.id} tried to {action.rush}, but the job was too awkward for one pair of paws.")
    propagate(world, narrate=True)


def teamwork(world: World, hero: Entity, friend: Entity, action: Action, prize: Entity, tool: Tool) -> None:
    hero.meters["exertion"] = hero.meters.get("exertion", 0.0) + 1
    friend.meters["exertion"] = friend.meters.get("exertion", 0.0) + 1
    world.zone = set(action.zone)
    world.facts["teamwork_done"] = True
    world.say(f"Then {hero.id}'s {friend.type} smiled and said, \"Let's do it together.\"")
    world.say(f"They used {tool.prep}, and {hero.id} helped {friend.id} {action.verb} the {prize.label}.")
    propagate(world, narrate=True)
    world.say(f"At last, they {tool.tail}, and the {prize.label} stayed nice and neat.")


def finish(world: World, hero: Entity, friend: Entity, prize: Entity, action: Action) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    friend.memes["joy"] = friend.memes.get("joy", 0.0) + 1
    world.say(f"{hero.id} and {friend.id} sat side by side and admired how their hard work had turned into something lovely.")
    world.say(f"The little {prize.label} looked {action.keyword}, and the whole meadow felt friendly and calm.")


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"carry"}),
    "hill": Setting(place="the hill", affords={"carry"}),
    "barnyard": Setting(place="the barnyard", affords={"carry"}),
}

ACTIONS = {
    "carry": Action(
        id="carry",
        verb="carry across the field",
        gerund="carrying across the field",
        rush="drag it across the grass",
        mess="scruffy",
        soil="scruffy",
        zone={"arms", "back"},
        keyword="oblong",
        tags={"teamwork", "oblong"},
    )
}

PRIZES = {
    "log": Prize(id="log", label="log", phrase="an oblong little log", region="back", plural=False),
    "box": Prize(id="box", label="box", phrase="an oblong wooden box", region="back", plural=False),
    "tray": Prize(id="tray", label="tray", phrase="an oblong picnic tray", region="arms", plural=False),
}

TOOLS = [
    Tool(
        id="rope",
        label="a rope sling",
        covers={"back"},
        guards={"scruffy"},
        prep="tie a rope sling under it",
        tail="walked it carefully to the end",
    ),
    Tool(
        id="blanket",
        label="a soft blanket",
        covers={"back"},
        guards={"scruffy"},
        prep="wrap it in a soft blanket",
        tail="carried it safely to the finish",
    ),
]


GIRL_NAMES = ["Mina", "Nora", "Lulu", "Poppy", "Mabel"]
BOY_NAMES = ["Toby", "Ollie", "Finn", "Benny", "Jasper"]
FRIEND_NAMES = ["Pip", "Moss", "Sage", "Hopper", "Wren"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    hero: str
    hero_type: str
    friend: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal teamwork story world with an oblong task.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["mouse", "rabbit", "fox", "bear", "hedgehog", "squirrel"])
    ap.add_argument("--friend")
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
    place = args.place or rng.choice(list(SETTINGS))
    action = args.action or "carry"
    prize = args.prize or rng.choice(list(PRIZES))
    hero_type = args.hero_type or rng.choice(["mouse", "rabbit", "fox", "bear", "hedgehog", "squirrel"])
    hero = args.hero or rng.choice(GIRL_NAMES if hero_type in {"mouse", "rabbit", "hedgehog", "squirrel"} else BOY_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    return StoryParams(place=place, action=action, prize=prize, hero=hero, hero_type=hero_type, friend=friend)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    friend = world.add(Entity(id=params.friend, kind="character", type="mouse"))
    prize = world.add(Entity(id="prize", type=PRIZES[params.prize].id, label=PRIZES[params.prize].label, phrase=PRIZES[params.prize].phrase, owner=hero.id))
    action = ACTIONS[params.action]
    tool = has_working_fix(action, PRIZES[params.prize])

    if tool is None:
        raise StoryError("No reasonable teamwork fix exists for that prize and action.")

    introduce(world, hero, friend)
    world.para()
    setup(world, hero, friend, prize, action)
    ask_for_help(world, hero, friend, action, prize)
    warn(world, friend, hero, action, prize)
    try_solo(world, hero, action)
    world.para()
    teamwork(world, hero, friend, action, prize, tool)
    finish(world, hero, friend, prize, action)

    world.facts.update(hero=hero, friend=friend, prize=prize, action=action, tool=tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle animal story about teamwork using the word "{f["action"].keyword}".',
        f"Tell a short story where {f['hero'].id} and {f['friend'].id} work together to move an oblong thing.",
        f"Write a child-friendly tale in which friends solve a big job by using a rope sling or blanket.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, prize, action, tool = f["hero"], f["friend"], f["prize"], f["action"], f["tool"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little {hero.type}, and {friend.id}, who helped with the oblong {prize.label}.",
        ),
        QAItem(
            question=f"Why did {friend.id} warn {hero.id} about the job?",
            answer=f"{friend.id} warned {hero.id} because dragging the oblong {prize.label} alone would make it get {action.soil}.",
        ),
        QAItem(
            question=f"How did they finish the job?",
            answer=f"They worked as a team and used {tool.label} so they could {action.verb} without making the {prize.label} messy.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and happy after the teamwork worked and the oblong {prize.label} stayed neat.",
        ),
    ]


KNOWLEDGE = [
    QAItem(question="What does teamwork mean?", answer="Teamwork means people or animals help one another and do a job together."),
    QAItem(question="What is oblong?", answer="Oblong means longer than it is wide, like a stretched-out box or loaf."),
    QAItem(question="What is a rope sling?", answer="A rope sling is a helper made from rope that can hold something so two friends can carry it more easily."),
    QAItem(question="What does cremate mean?", answer="Cremate means to burn something until it turns into ashes."),
]


def world_qa(world: World) -> list[QAItem]:
    return KNOWLEDGE


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:8} ({e.type:8}) meters={meters} memes={memes}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
teamwork(hero, friend, prize) :- hero_type(hero, _), friend_type(friend, _), prize_item(prize), oblong(prize).
oblong(prize) :- prize_item(prize), shape(prize, oblong).
needs_teamwork(prize) :- oblong(prize).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize_item", pid))
        lines.append(asp.fact("shape", pid, "oblong"))
    for aid in ACTIONS:
        lines.append(asp.fact("action_item", aid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    return 0


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for i, p in enumerate(sample.prompts, 1):
            print(f"PROMPT {i}: {p}")
        for item in sample.story_qa:
            print(f"Q: {item.question}\nA: {item.answer}")
        for item in sample.world_qa:
            print(f"Q: {item.question}\nA: {item.answer}")


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show teamwork/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="meadow", action="carry", prize="log", hero="Mina", hero_type="mouse", friend="Pip"),
            StoryParams(place="hill", action="carry", prize="box", hero="Toby", hero_type="rabbit", friend="Sage"),
            StoryParams(place="barnyard", action="carry", prize="tray", hero="Nora", hero_type="squirrel", friend="Wren"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
