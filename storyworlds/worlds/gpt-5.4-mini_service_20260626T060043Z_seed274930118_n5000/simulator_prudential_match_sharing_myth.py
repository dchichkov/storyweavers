#!/usr/bin/env python3
"""
storyworlds/worlds/simulator_prudential_match_sharing_myth.py
=============================================================

A small myth-style storyworld about a careful child, a single match, and the
wisdom of sharing.

The seed tale behind the world:
---
In an old hill-village, a child tended a little shrine lamp at dusk. The child
had only one match left, and the elder warned that a careless spark could waste
it. But the child also wanted to share the light with the neighbors who were
gathering in the dark.

So the child used a small simulator wheel carved from ash wood to judge the
wind, struck the match prudentially, and passed the flame from lamp to lamp
until the whole lane glowed.

World model:
---
- A candle or lamp can be lit by a match if the wind risk is low.
- A prudent choice reduces the chance of wasting the only match.
- Sharing the flame increases communal joy and peace, and it can leave the
  original lamp still lit if the story reaches a good turn.
- The elder's concern is driven by a forecast from the simulator.

This file follows the Storyweavers contract: it defines typed entities with
meters and memes, a forward-simulated world, a text generator, QA items, and an
inline ASP twin for the reasonableness gate.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    lit: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister", "daughter"}
        male = {"boy", "father", "dad", "man", "brother", "son"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    place: str
    indoor: bool = False
    wind_risk: int = 0
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    allows: set[str]
    shares: bool = False
    plural: bool = False


@dataclass
class StoryParams:
    place: str
    task: str
    prize: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


def need_match(task: str, prize: str) -> bool:
    return prize in {"lamp", "candle"} and task in {"light_lamp", "light_candle"}


def compatible_tool(task: str, prize: str) -> Optional[Tool]:
    for tool in TOOLS:
        if prize in tool.allows and tool.shares:
            return tool
    return None


def _do_light(world: World, actor: Entity, tool: Tool, narrate: bool = True) -> None:
    actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
    if world.setting.wind_risk >= 2:
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
    if narrate:
        world.say(f"{actor.id} held the {tool.label} close and waited for the smallest calm.")


def predict(world: World, actor: Entity, tool: Tool) -> dict:
    sim = world.copy()
    _do_light(sim, sim.get(actor.id), tool, narrate=False)
    return {
        "safe": sim.setting.wind_risk <= 1,
        "joy": sum(e.memes.get("joy", 0.0) for e in sim.characters()),
    }


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "gentle")
    world.say(f"{hero.id} was a little {trait} {hero.type} who listened to old winds and old songs.")


def setting_line(world: World, hero: Entity) -> None:
    if world.setting.indoor:
        world.say(f"Inside {world.setting.place}, the air was still and the shrine lamp waited by the wall.")
    else:
        world.say(f"At {world.setting.place}, the dusk wind moved like a thin wolf through the grass.")


def desire(world: World, hero: Entity, prize: Entity, task: str) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    if task == "light_lamp":
        world.say(f"{hero.id} wanted to light the {prize.label} so the path would not vanish into night.")
    else:
        world.say(f"{hero.id} wanted to light the {prize.label} so the hearth could greet everyone warmly.")


def warning(world: World, elder: Entity, hero: Entity, prize: Entity) -> None:
    hero.memes["heard_warning"] = hero.memes.get("heard_warning", 0.0) + 1
    if world.setting.wind_risk >= 2:
        world.say(f'"A lone spark can be lost," {elder.id} said. "Be prudential with the last match."')
    else:
        world.say(f'"Keep the flame small," {elder.id} said. "Even a careful hand should respect a match."')


def sharing_turn(world: World, hero: Entity, elder: Entity, tool: Tool, prize: Entity) -> None:
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1
    world.say(f"{hero.id} nodded. The child did not want to hoard the light; {hero.pronoun()} wanted to share it.")
    if tool.shares:
        world.say(f"So {hero.id} used the {tool.label} like a bridge, passing the same flame from one lamp to the next.")


def resolution(world: World, hero: Entity, elder: Entity, tool: Tool, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1
    prize.lit = True
    world.say(
        f"At last the {prize.label} burned steady, and the lane brightened as if the stars had leaned down to watch."
    )
    world.say(
        f"{hero.id} smiled at {elder.id}, because prudence had kept the match safe and sharing had made the light larger than one hand."
    )


def tell(setting: Setting, task: str, prize_cfg: Tool, hero_name: str = "Mira", hero_type: str = "girl",
         hero_traits: Optional[list[str]] = None, elder_type: str = "elder") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + (hero_traits or ["careful", "curious"])))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type, label="the elder"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        carried_by=hero.id,
        lit=False,
    ))
    hero.meters["match"] = 1
    hero.meters["prudence"] = 0
    world.facts.update(hero=hero, elder=elder, prize=prize, task=task, tool=prize_cfg, setting=setting)

    introduce(world, hero)
    setting_line(world, hero)
    desire(world, hero, prize, task)
    world.para()
    warning(world, elder, hero, prize)
    world.say(f"{hero.id} lifted the {prize_cfg.label} and thought about the simulator wheel carved from ash wood.")
    if setting.wind_risk >= 2:
        world.say(f"The simulator turned slowly, showing a restless breath of wind.")
    else:
        world.say(f"The simulator turned slowly, showing a calm that favored a careful flame.")
    world.para()
    sharing_turn(world, hero, elder, prize_cfg, prize)
    if prize_cfg.shares and compatible_tool(task, prize.label):
        hero.meters["prudence"] += 1
        resolution(world, hero, elder, prize_cfg, prize)
    else:
        raise StoryError("(No story: the chosen tool does not support a sharing-based myth turn.)")

    world.facts["resolved"] = True
    return world


SETTINGS = {
    "hill_village": Setting(place="the hill-village", indoor=False, wind_risk=2, affords={"light_lamp"}),
    "temple_yard": Setting(place="the temple yard", indoor=False, wind_risk=1, affords={"light_candle"}),
    "hearth_hall": Setting(place="the hearth hall", indoor=True, wind_risk=0, affords={"light_candle"}),
}

TOOLS = [
    Tool(id="match", label="match", phrase="a single match", allows={"lamp", "candle"}, shares=True),
    Tool(id="lantern", label="lantern", phrase="a bronze lantern", allows={"lamp"}, shares=True),
    Tool(id="sparkstone", label="sparkstone", phrase="a sparkstone", allows={"lamp", "candle"}, shares=False),
]

PRIZES = {
    "lamp": Tool(id="lamp", label="lamp", phrase="the shrine lamp", allows={"lamp"}, shares=True),
    "candle": Tool(id="candle", label="candle", phrase="the feast candle", allows={"candle"}, shares=True),
}

GIRL_NAMES = ["Mira", "Lina", "Sora", "Nia", "Asha", "Kiri"]
BOY_NAMES = ["Taro", "Eli", "Niko", "Arin", "Dara", "Rafi"]
TRAITS = ["careful", "curious", "brave", "gentle", "steady", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task in setting.affords:
            for prize_id, prize in PRIZES.items():
                if need_match(task, prize.label) and compatible_tool(task, prize.label):
                    out.append((place, task, prize_id))
    return out


KNOWLEDGE = {
    "match": [("What is a match?", "A match is a tiny stick that can make a small flame when struck carefully.")],
    "prudential": [("What does prudential mean?", "Prudential means careful and wise, especially when a choice could go wrong.")],
    "sharing": [("What is sharing?", "Sharing means letting other people use or enjoy something with you.")],
    "simulator": [("What is a simulator?", "A simulator is a model or machine that helps people imagine what might happen before they act.")],
    "myth": [("What is a myth?", "A myth is an old story that explains why things are special or why people should act wisely.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, elder, prize, task = f["hero"], f["elder"], f["prize"], f["task"]
    return [
        f'Write a short myth for a child about "{task}", a careful choice, and a single "{prize.label}".',
        f"Tell a story where {hero.id} and {elder.id} use a simulator and act prudentially with a match.",
        f"Write a gentle legend in which sharing makes one {prize.label} light many homes.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, prize, task = f["hero"], f["elder"], f["prize"], f["task"]
    qa = [
        QAItem(
            question=f"Who wanted to light the {prize.label} in the story?",
            answer=f"{hero.id} wanted to light the {prize.label} and share its flame with everyone nearby.",
        ),
        QAItem(
            question=f"Why did {elder.id} warn {hero.id} about the match?",
            answer=f"{elder.id} warned {hero.id} because the wind could waste a match if the child was not careful.",
        ),
        QAItem(
            question=f"What did the simulator help {hero.id} understand?",
            answer=f"The simulator helped {hero.id} understand whether the wind was calm enough for a careful flame.",
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question="How did sharing change the ending?",
                answer="Sharing let the child pass the flame from one lamp to another, so the light became larger and kinder instead of being kept for one person alone.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"simulator", "prudential", "sharing", "match", "myth"}
    out: list[QAItem] = []
    for tag in ["simulator", "prudential", "match", "sharing", "myth"]:
        if tag in tags:
            q, a = KNOWLEDGE[tag][0]
            out.append(QAItem(question=q, answer=a))
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.lit:
            bits.append("lit=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill_village", task="light_lamp", prize="lamp", name="Mira", gender="girl", elder="elder", trait="careful"),
    StoryParams(place="hearth_hall", task="light_candle", prize="candle", name="Taro", gender="boy", elder="elder", trait="gentle"),
]


ASP_RULES = r"""
% A task is compatible with a prize when the prize needs a match and the tool shares.
needs_match(light_lamp, lamp).
needs_match(light_candle, candle).

prize_ok(T, P) :- needs_match(T, P).
tool_ok(match, lamp).
tool_ok(match, candle).
shared(match).

valid(Place, Task, Prize) :- affords(Place, Task), prize_ok(Task, Prize), tool_ok(match, Prize), shared(match).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        lines.append(asp.fact("wind_risk", pid, s.wind_risk))
        for task in sorted(s.affords):
            lines.append(asp.fact("affords", pid, task))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        if tool.shares:
            lines.append(asp.fact("shared", tool.id))
        for allow in sorted(tool.allows):
            lines.append(asp.fact("allows", tool.id, allow))
    for task, prize in [("light_lamp", "lamp"), ("light_candle", "candle")]:
        lines.append(asp.fact("needs_match", task, prize))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic sharing story world with prudential choices and a simulator.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=["light_lamp", "light_candle"])
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=["elder"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.task is None or c[1] == args.task)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, task, prize = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = args.elder or "elder"
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task, prize=prize, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], params.task, PRIZES[params.prize], params.name, params.gender, [params.trait])
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
