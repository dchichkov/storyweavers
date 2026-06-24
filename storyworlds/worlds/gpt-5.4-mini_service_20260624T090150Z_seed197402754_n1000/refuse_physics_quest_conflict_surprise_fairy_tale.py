#!/usr/bin/env python3
"""
storyworlds/worlds/refuse_physics_quest_conflict_surprise_fairy_tale.py
======================================================================

A tiny fairy-tale storyworld about a quest, a conflict, and a surprise
resolution grounded in simple physics.

Premise:
A young page or apprentice is sent on a small quest through a magical place.
They want a quick, impossible shortcut, but a mentor refuses because physics
still matters in fairy tales: heavy things fall, levers move, and bridges need
support. The surprise is that a clever, gentle solution exists.

This script models:
- a quest object that must travel from start to finish,
- a risky shortcut that violates the world's physics,
- an emotional conflict between desire and refusal,
- a surprise helper or hidden tool that makes the quest succeed.

The prose is story-driven from the world state, not a frozen template.
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
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "mother", "woman", "fairy"}
        male = {"boy", "prince", "king", "father", "man", "wizard", "knight"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    feature: str
    supports: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    end_goal: str
    risk: str
    weight: str
    lesson: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps: set[str]
    surprise_line: str


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.physics: dict[str, float] = {
            "heavy_pull": 1.0,
            "bridge_support": 1.0,
            "drop_risk": 0.0,
            "balance": 1.0,
        }

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
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.physics = dict(self.physics)
        return clone


def simple_physics_law(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get(world.facts.get("hero_id", ""))
    quest = world.entities.get(world.facts.get("quest_id", ""))
    if not hero or not quest:
        return out
    if hero.memes.get("refuse", 0.0) >= THRESHOLD and quest.meters.get("risk", 0.0) >= THRESHOLD:
        sig = ("stubborn_conflict", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1
            out.append("__conflict__")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for sent in simple_physics_law(world):
            if sent:
                changed = True
                if sent != "__conflict__":
                    produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


SETTINGS = {
    "forest": Setting(place="the moonlit forest", feature="a narrow wooden bridge", supports={"bridge", "lever", "rope"}),
    "hill": Setting(place="the windy hill", feature="a stone archway", supports={"lever", "rope", "basket"}),
    "castle": Setting(place="the old castle courtyard", feature="a high stair", supports={"rope", "basket"}),
}

QUESTS = {
    "lantern": Quest(
        id="lantern",
        verb="carry the lantern to the far gate",
        end_goal="the far gate",
        risk="the lantern could slip into the stream",
        weight="small but fragile",
        lesson="small things can still need careful physics",
        tags={"light", "bridge"},
    ),
    "apple": Quest(
        id="apple",
        verb="deliver the golden apple to the queen",
        end_goal="the queen",
        risk="the apple could roll away",
        weight="round and easy to lose",
        lesson="round things roll downhill unless someone stops them",
        tags={"roll", "balance"},
    ),
    "crown": Quest(
        id="crown",
        verb="bring the silver crown to the tower",
        end_goal="the tower",
        risk="the crown could tip off the tray",
        weight="shiny and unsteady",
        lesson="a steady base matters more than a proud rush",
        tags={"balance", "tray"},
    ),
}

TOOLS = [
    Tool(
        id="counterweight",
        label="a counterweight basket",
        use="balance the load",
        helps={"balance", "tray"},
        surprise_line="A hidden basket hung on the other side, and its weight kept the tray steady.",
    ),
    Tool(
        id="ropebridge",
        label="a rope bridge",
        use="cross safely over the water",
        helps={"bridge"},
        surprise_line="A small rope bridge was tucked behind the reeds, waiting like a secret path.",
    ),
    Tool(
        id="lever",
        label="a wooden lever",
        use="lift the heavy gate",
        helps={"lever"},
        surprise_line="Under a fern lay a smooth lever board, just the right size for a careful push.",
    ),
]

GIRL_NAMES = ["Ava", "Mina", "Luna", "Elin", "Tessa", "Nora"]
BOY_NAMES = ["Finn", "Owen", "Theo", "Bram", "Eli", "Pip"]


@dataclass
class StoryParams:
    setting: str
    quest: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None


def quest_is_at_risk(quest: Quest, setting: Setting) -> bool:
    if quest.id == "lantern":
        return "bridge" in setting.supports
    if quest.id == "apple":
        return "balance" in setting.supports
    if quest.id == "crown":
        return "lever" in setting.supports or "basket" in setting.supports
    return False


def select_tool(quest: Quest, setting: Setting) -> Optional[Tool]:
    for tool in TOOLS:
        if quest.tags & tool.helps and quest_is_at_risk(quest, setting):
            return tool
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale quest storyworld with refusal, physics, conflict, and surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "fairy", "owl"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for qid, quest in QUESTS.items():
            if quest_is_at_risk(quest, setting) and select_tool(quest, setting):
                combos.append((sid, qid, "valid"))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.quest:
        setting = SETTINGS[args.setting]
        quest = QUESTS[args.quest]
        if not (quest_is_at_risk(quest, setting) and select_tool(quest, setting)):
            raise StoryError("This quest has no honest surprise solution in that setting.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.quest is None or c[1] == args.quest)]
    if not combos:
        raise StoryError("No valid fairy-tale quest matches the chosen options.")
    setting_id, quest_id, _ = rng.choice(sorted(combos))
    quest = QUESTS[quest_id]
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father", "fairy", "owl"])
    return StoryParams(setting=setting_id, quest=quest_id, name=name, gender=gender, helper=helper)


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"Long ago, in {world.setting.place}, there lived a little {hero.type} named {hero.id}."
    )


def quest_call(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["purpose"] = hero.memes.get("purpose", 0.0) + 1
    world.say(
        f"{hero.id} was sent on a quest to {quest.verb}."
    )


def refusal(world: World, helper: Entity, hero: Entity, quest: Quest) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    hero.memes["refuse"] = hero.memes.get("refuse", 0.0) + 1
    world.facts["refused"] = True
    world.say(
        f"{hero.id} wanted a quick shortcut, but {helper.pronoun('subject')} refused and said, "
        f"\"Not that way. Physics will not be fooled.\""
    )


def conflict_turn(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["frustration"] = hero.memes.get("frustration", 0.0) + 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} frowned and tried to prove the shortcut would work, even though the stones wobbled."
    )
    world.say(
        f"Then the path gave a tiny warning creak, and the conflict felt as big as a storm cloud."
    )


def surprise_solution(world: World, helper: Entity, hero: Entity, quest: Quest, tool: Tool) -> None:
    hero.memes["surprise"] = hero.memes.get("surprise", 0.0) + 1
    world.say(tool.surprise_line)
    world.say(
        f"{helper.pronoun('subject').capitalize()} smiled and showed how {tool.use}."
    )


def resolution(world: World, hero: Entity, quest: Quest, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(
        f"At last, {hero.id} chose the careful way, and the quest was completed: {quest.end_goal} was reached."
    )
    world.say(
        f"{hero.id} learned that {quest.lesson}, and the fairy-tale road stayed safe beneath {hero.pronoun('possessive')} feet."
    )


def tell(setting: Setting, quest: Quest, hero_name: str, gender: str, helper_kind: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl" if gender == "girl" else "boy"))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_kind, label=helper_kind))
    goal = world.add(Entity(id="QuestItem", kind="thing", type=quest.id, label=quest.id, carried_by=hero.id))
    world.facts["hero_id"] = hero.id
    world.facts["quest_id"] = goal.id
    world.facts["helper_id"] = helper.id

    introduce(world, hero)
    world.para()
    quest_call(world, hero, quest)
    refusal(world, helper, hero, quest)
    conflict_turn(world, hero, quest)
    world.para()
    tool = select_tool(quest, setting)
    if tool is None:
        raise StoryError("No tool can complete this quest in the selected setting.")
    world.facts["tool_id"] = tool.id
    surprise_solution(world, helper, hero, quest, tool)
    resolution(world, hero, quest, tool)
    world.facts.update(hero=hero, helper=helper, quest=quest, tool=tool)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]
    quest: Quest = f["quest"]
    helper: Entity = f["helper"]
    return [
        f'Write a fairy tale about {hero.id} on a quest to {quest.verb}, where a helper refuses a bad shortcut.',
        f'Tell a short story for a child in which {hero.id} learns that physics matters even in a magical forest.',
        f'Write a story with a quest, a conflict, and a surprise solution using the word "refuse".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    tool: Tool = f["tool"]
    return [
        QAItem(
            question=f"What was {hero.id}'s quest in the story?",
            answer=f"{hero.id} was on a quest to {quest.verb}.",
        ),
        QAItem(
            question=f"Why did {helper.label or helper.type} refuse the shortcut?",
            answer=f"{helper.pronoun('subject').capitalize()} refused because the shortcut did not work with physics and would have made the quest unsafe.",
        ),
        QAItem(
            question=f"What surprise helped {hero.id} finish the quest?",
            answer=f"{tool.label.capitalize()} helped, because it let {hero.id} {tool.use} in a safe way.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"By the end, {hero.id} stopped arguing, chose the careful path, and finished the quest successfully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is physics?",
            answer="Physics is the way things move and behave in the world, like how heavy things fall and how bridges need support.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or task with a goal that someone must complete, often with a challenge along the way.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that you did not know would happen until it appears.",
        ),
        QAItem(
            question="What does it mean to refuse?",
            answer="To refuse means to say no to something or not agree to do it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
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
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  physics={world.physics}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="forest", quest="lantern", name="Mina", gender="girl", helper="fairy"),
    StoryParams(setting="hill", quest="apple", name="Finn", gender="boy", helper="owl"),
    StoryParams(setting="castle", quest="crown", name="Luna", gender="girl", helper="mother"),
]


ASP_RULES = r"""
quest(Q) :- quest_name(Q).
setting(S) :- setting_name(S).
valid(S,Q) :- supports(S,bridge), quest_tags(Q,bridge).
valid(S,Q) :- supports(S,lever), quest_tags(Q,lever).
valid(S,Q) :- supports(S,balance), quest_tags(Q,balance).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting_name", sid))
        for s in sorted(setting.supports):
            lines.append(asp.fact("supports", sid, s))
    for qid, quest in QUESTS.items():
        lines.append(asp.fact("quest_name", qid))
        for t in sorted(quest.tags):
            lines.append(asp.fact("quest_tags", qid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set((s, q) for s, q, _ in valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_sample(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], QUESTS[params.quest], params.name, params.gender, params.helper)
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


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.quest} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
