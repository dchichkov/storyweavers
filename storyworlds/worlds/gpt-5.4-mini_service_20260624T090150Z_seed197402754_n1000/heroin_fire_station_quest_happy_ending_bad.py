#!/usr/bin/env python3
"""
storyworlds/worlds/heroin_fire_station_quest_happy_ending_bad.py
===============================================================

A small comedy storyworld set in a fire station.

Seed tale:
---
At the fire station, a tiny heroine named Heroin wanted a quest.
She wanted to find the shiny bell rope, but the station captain said it was the
wrong time. A silly bad ending seemed near when the hose cart rolled away.
Then the crew turned it into a joke, found the missing bell, and the quest ended
in a happy ending with everyone laughing.

World idea:
---
- Physical meters: locations, objects, motion, readiness, mess
- Emotional memes: worry, pride, joy, surprise, courage, silliness
- A quest is a small mission through the fire station.
- A bad ending is possible when the quest loses the key item.
- A happy ending is possible when the crew uses a clever, comic fix.

This script is self-contained and follows the Storyweavers contract:
- StoryParams and registries
- build_parser, resolve_params, generate, emit, main
- inline ASP rules and fact emission
- verify mode checking ASP/Python parity
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
    carried_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister", "heroine"}
        male = {"boy", "man", "father", "brother", "hero"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the fire station"
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    title: str
    goal: str
    path: str
    snag: str
    keyword: str = "quest"
    tags: set[str] = field(default_factory=set)


@dataclass
class Prize:
    label: str
    phrase: str
    type: str
    location: str
    plural: bool = False


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    prep: str
    finish: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trail: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trail.append(text)

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
        clone.paragraphs = [[]]
        return clone


def _clamp(x: float) -> float:
    return 0.0 if x < 0 else x


def _quest_risk(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(world.facts["hero"].id)
    quest = world.facts["quest"]
    prize = world.facts["prize"]
    if hero.meters.get("lost", 0) >= THRESHOLD and world.facts.get("snagged") and not world.facts.get("tool_used"):
        sig = ("bad", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["worry"] = hero.memes.get("worry", 0) + 1
            out.append("The quest looked like a bad ending for a moment.")
    if hero.meters.get("find", 0) >= THRESHOLD and not world.facts.get("prize_recovered"):
        sig = ("recover", prize.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["prize_recovered"] = True
            prize.location = "in the captain's hand"
            hero.memes["joy"] = hero.memes.get("joy", 0) + 1
            out.append("The missing thing turned up at the perfect silly moment.")
    if world.facts.get("prize_recovered") and not world.facts.get("happy_end"):
        sig = ("happy", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            world.facts["happy_end"] = True
            hero.memes["pride"] = hero.memes.get("pride", 0) + 1
            out.append("The crew laughed, and the quest ended happily.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = _quest_risk(world)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return "The fire station smelled like soap, boots, and warm toast from the kitchen."


def introduce(world: World, hero: Entity, captain: Entity) -> None:
    world.say(
        f"{hero.id} was a tiny comedy-loving {hero.type} who acted like a bold heroine on a quest."
    )
    world.say(
        f"At the station, {captain.label} kept an eye on the ladders, the helmets, and the shiny bell rope."
    )


def desire(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    world.say(
        f"{hero.id} wanted a {quest.title} and pointed at {quest.goal}, because {hero.pronoun('possessive')} heart was full of brave silliness."
    )
    world.say(
        f"{hero.pronoun().capitalize()} wanted to {quest.path}, but the prize was not easy to reach."
    )


def stumble(world: World, hero: Entity, quest: Quest, prize: Entity) -> None:
    hero.meters["lost"] = hero.meters.get("lost", 0) + 1
    world.facts["snagged"] = True
    world.say(
        f"Then the plan went a little bad ending-shaped: the little cart rolled, and the prize slipped out of sight."
    )
    world.say(
        f"{hero.id} froze, then giggled nervously, because even a heroic quest can wobble like a spoon."
    )


def warn(world: World, captain: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"\"Easy now,\" {captain.label} said. \"No one needs a giant disaster; we just need a calm look around.\""
    )
    world.say(
        f"{hero.id} listened, because {hero.pronoun('possessive')} wish for the prize was big, but the station was bigger."
    )


def tool_offer(world: World, captain: Entity, hero: Entity, tool_def: Tool, quest: Quest) -> Entity:
    tool = world.add(Entity(
        id=tool_def.id,
        type="tool",
        label=tool_def.label,
        owner=hero.id,
    ))
    tool.carried_by = hero.id
    world.facts["tool_used"] = True
    world.say(
        f"{captain.label} smiled and said, \"How about we {tool_def.prep}?\""
    )
    return tool


def comic_fix(world: World, hero: Entity, captain: Entity, tool_def: Tool, prize: Entity) -> None:
    hero.meters["find"] = hero.meters.get("find", 0) + 1
    world.say(
        f"{hero.id} followed the clue with {tool_def.label}, peeked behind a helmet stack, and found the missing prize."
    )
    world.say(
        f"{tool_def.finish}, and the whole station gave a happy snort-laugh."
    )
    propagate(world, narrate=True)


def ending(world: World, hero: Entity, prize: Entity, quest: Quest) -> None:
    world.say(
        f"In the end, {hero.id} was still a small heroine, but now {hero.pronoun('subject')} had finished the {quest.keyword} and kept the station cheerful."
    )
    world.say(
        f"The prize stayed safe, the bad ending never won, and the fire station felt like the silliest victory parade in town."
    )


SETTING = Setting(place="the fire station", affords={"quest"})

QUESTS = {
    "bell": Quest(
        id="bell",
        title="bell hunt",
        goal="the shiny station bell rope",
        path="search the hall and climb the little step stool",
        snag="the rope is hidden",
        keyword="quest",
        tags={"bell", "metal", "station"},
    ),
    "badge": Quest(
        id="badge",
        title="badge rescue",
        goal="the captain's spare badge",
        path="check the coat hooks and look under the couch",
        snag="the badge is missing",
        keyword="quest",
        tags={"badge", "metal", "station"},
    ),
    "cookie": Quest(
        id="cookie",
        title="cookie quest",
        goal="the last kitchen cookie",
        path="tiptoe to the kitchen and ask kindly",
        snag="the cookie is gone",
        keyword="quest",
        tags={"cookie", "kitchen", "station"},
    ),
}

PRIZES = {
    "bellrope": Prize(
        label="bell rope",
        phrase="the shiny bell rope",
        type="rope",
        location="by the bell",
    ),
    "badge": Prize(
        label="badge",
        phrase="the captain's spare badge",
        type="badge",
        location="on the desk",
    ),
    "cookie": Prize(
        label="cookie",
        phrase="the last kitchen cookie",
        type="cookie",
        location="in the kitchen",
    ),
}

TOOLS = [
    Tool(
        id="flashlight",
        label="a tiny flashlight",
        helps={"bell", "badge"},
        prep="use a tiny flashlight and check the dark corners",
        finish="Its beam made the shadows look funny instead of scary",
    ),
    Tool(
        id="hook",
        label="a toy hook",
        helps={"bell"},
        prep="use a toy hook to reach up high",
        finish="The hook snagged the rope on the first try",
    ),
    Tool(
        id="napkin",
        label="a folded napkin",
        helps={"cookie"},
        prep="put the cookie on a folded napkin and carry it carefully",
        finish="The napkin made the cookie feel like treasure",
    ),
]

HERO_NAMES = ["Heroin", "Mina", "Pip", "Luna", "Toby", "Nia"]
CAPTAIN_NAMES = ["Captain Brick", "Captain Margo", "Captain Bolt"]
TRAITS = ["curious", "brave", "silly", "cheerful"]


@dataclass
class StoryParams:
    quest: str
    prize: str
    name: str
    captain: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for q in QUESTS:
        for p in PRIZES:
            if q == "bell" and p == "bellrope":
                combos.append(("the fire station", q, p))
            if q == "badge" and p == "badge":
                combos.append(("the fire station", q, p))
            if q == "cookie" and p == "cookie":
                combos.append(("the fire station", q, p))
    return combos


def choose_tool(quest: Quest, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if quest.id in tool.helps:
            return tool
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld set in a fire station.")
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--captain", choices=CAPTAIN_NAMES)
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
    if args.quest and args.prize:
        if ("the fire station", args.quest, args.prize) not in combos:
            raise StoryError("No story: that quest and prize do not fit this fire station tale.")
    filtered = [c for c in combos if (not args.quest or c[1] == args.quest) and (not args.prize or c[2] == args.prize)]
    if not filtered:
        raise StoryError("No valid combination matches the given options.")
    _, quest, prize = rng.choice(sorted(filtered))
    name = args.name or rng.choice(HERO_NAMES)
    captain = args.captain or rng.choice(CAPTAIN_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(quest=quest, prize=prize, name=name, captain=captain, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    quest = QUESTS[params.quest]
    prize_cfg = PRIZES[params.prize]
    hero = world.add(Entity(id=params.name, kind="character", type="heroine", label=params.name))
    captain = world.add(Entity(id=params.captain, kind="character", type="captain", label=params.captain))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        location=prize_cfg.location,
    ))
    world.facts.update(hero=hero, captain=captain, quest=quest, prize=prize, prize_cfg=prize_cfg)

    introduce(world, hero, captain)
    world.para()
    world.say(setting_detail(world.setting))
    desire(world, hero, quest, prize)
    stumble(world, hero, quest, prize)
    warn(world, captain, hero, prize)
    tool_def = choose_tool(quest, prize_cfg)
    if tool_def is None:
        raise StoryError("No reasonable tool exists for this quest.")
    tool = tool_offer(world, captain, hero, tool_def, quest)
    comic_fix(world, hero, captain, tool_def, prize)
    ending(world, hero, prize, quest)
    world.facts["tool"] = tool
    world.facts["happy_end"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    quest = f["quest"]
    prize = f["prize"]
    return [
        f'Write a short comedy story set in a fire station about a child named {hero.id} and a {quest.title}.',
        f'Tell a story where {hero.id} wants to complete a {quest.keyword} but a bad ending almost happens before a happy ending arrives.',
        f'Write a simple fire-station story that includes {prize.label}, a clever tool, and a silly joke at the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    captain = f["captain"]
    quest = f["quest"]
    prize = f["prize"]
    tool = f["tool"]
    qa = [
        QAItem(
            question=f"Who was the story about at the fire station?",
            answer=f"It was about {hero.id}, a small heroine who went on a {quest.title}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to find?",
            answer=f"{hero.id} wanted to find {prize.phrase} during the quest.",
        ),
        QAItem(
            question=f"Who helped {hero.id} when the plan started to go wrong?",
            answer=f"{captain.label} helped by suggesting {tool.label} and keeping the search calm.",
        ),
        QAItem(
            question=f"What kind of ending did the story have?",
            answer="It had a happy ending, even though a bad ending seemed possible for a moment.",
        ),
    ]
    if world.facts.get("happy_end"):
        qa.append(
            QAItem(
                question=f"How did the story avoid the bad ending?",
                answer=f"They used {tool.label}, found the missing prize, and turned the whole thing into a joke-filled happy ending.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fire station?",
            answer="A fire station is a place where firefighters keep their trucks, tools, and gear, and where they wait to help people.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a mission or search for something important, often with a problem to solve along the way.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the story finishes in a good, cheerful way.",
        ),
        QAItem(
            question="What is a bad ending?",
            answer="A bad ending is when things seem to go wrong and the problem does not get fixed the way everyone hoped.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
quest_valid("the fire station", Q, P) :- quest(Q), prize(P), allowed(Q, P).
allowed(bell, bellrope).
allowed(badge, badge).
allowed(cookie, cookie).

has_happy_end(Q, P) :- quest_valid("the fire station", Q, P).
has_bad_end(Q, P) :- quest(Q), prize(P), not allowed(Q, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "the fire station"))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for p in PRIZES:
        lines.append(asp.fact("prize", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show quest_valid/3."))
    return sorted(set(asp.atoms(model, "quest_valid")))


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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show quest_valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid quest/prize combinations:\n")
        for row in combos:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        for _, q, p in valid_combos():
            params = StoryParams(
                quest=q,
                prize=p,
                name="Heroin",
                captain="Captain Brick",
                trait="silly",
            )
            params.seed = base_seed
            samples.append(generate(params))
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
            header = f"### {p.name}: {p.quest} / {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
