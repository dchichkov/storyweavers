#!/usr/bin/env python3
"""
A standalone storyworld for a small friendship-quest mystery.

Seed premise:
A bothersome little mystery keeps interrupting a friend's quest, and the
characters have to notice clues, test them, and solve what is really causing
the trouble before they can keep going together.

The world is intentionally small and constraint-checked:
- a friend has a quest,
- something bothersome is happening in the setting,
- the mystery is solved by finding the true cause,
- the ending proves a change in state.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    worn_by: Optional[str] = None
    caretaker: Optional[str] = None
    place: str = ""
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    clue_word: str
    complication: str
    ending: str
    path: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    label: str
    symptom: str
    cause: str
    reveal: str
    clue: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helps: set[str]
    shows: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "library": Setting("the little library", indoors=True, affords={"search", "read"}),
    "garden": Setting("the moonlit garden", indoors=False, affords={"search", "follow"}),
    "station": Setting("the quiet station", indoors=True, affords={"search", "wait"}),
}

QUESTS = {
    "map": Quest(
        id="map",
        goal="find the missing map",
        clue_word="map",
        complication="the path keeps changing",
        ending="the map was tucked safely in a pocket",
        path="search the shelves and the corners",
        tags={"paper", "search"},
    ),
    "lantern": Quest(
        id="lantern",
        goal="bring the lantern home",
        clue_word="lantern",
        complication="the dark makes every shadow look strange",
        ending="the lantern was found glowing by the gate",
        path="follow the small lights",
        tags={"light", "follow"},
    ),
    "key": Quest(
        id="key",
        goal="recover the small key",
        clue_word="key",
        complication="every drawer sounds the same",
        ending="the key was inside a tiny cup",
        path="search the table and the floor",
        tags={"metal", "search"},
    ),
}

MYSTERIES = {
    "bump": Mystery(
        id="bump",
        label="the bothersome bumping sound",
        symptom="a bumping sound",
        cause="a loose wheel",
        reveal="the cart wheel was wobbling",
        clue="the sound got louder near the cart",
        tags={"wheel", "sound"},
    ),
    "rustle": Mystery(
        id="rustle",
        label="the bothersome rustling",
        symptom="a rustling sound",
        cause="a mouse in the curtains",
        reveal="the curtains were twitching because a mouse hid behind them",
        clue="the rustle followed the curtains",
        tags={"mouse", "sound"},
    ),
    "blink": Mystery(
        id="blink",
        label="the bothersome blinking light",
        symptom="a blinking light",
        cause="a loose battery",
        reveal="the lamp blinked because its battery was slipping",
        clue="the light blinked most near the lamp",
        tags={"light", "battery"},
    ),
}

TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="a little magnifying glass",
        helps={"search", "sound", "light"},
        shows="it made the small clues easy to see",
        tags={"see", "clue"},
    ),
    "string": Tool(
        id="string",
        label="a short string",
        helps={"follow", "search"},
        shows="it helped mark the path",
        tags={"path", "follow"},
    ),
    "lamp": Tool(
        id="lamp",
        label="a warm lamp",
        helps={"light"},
        shows="it made shadows stand still",
        tags={"light"},
    ),
}

HERO_NAMES = ["Maya", "Eli", "Nora", "Theo", "Luna", "Finn", "Ivy", "Leo"]
HELPER_NAMES = ["Pip", "June", "Noah", "Ari", "Milo", "Zoe", "Bea", "Owen"]
TRAITS = ["curious", "careful", "kind", "brave", "patient", "gentle"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def quest_can_fit(setting: Setting, quest: Quest) -> bool:
    return quest.id in {"map", "lantern", "key"} and bool(setting.affords)


def mystery_can_affect(setting: Setting, mystery: Mystery, quest: Quest) -> bool:
    if quest.id == "lantern":
        return "light" in mystery.tags or setting.indoors
    if quest.id == "map":
        return "sound" in mystery.tags or "paper" in quest.tags
    if quest.id == "key":
        return "sound" in mystery.tags or "metal" in quest.tags
    return False


def select_tool(quest: Quest, mystery: Mystery) -> Optional[Tool]:
    for tool in TOOLS.values():
        if quest.id == "lantern" and "light" in tool.helps:
            return tool
        if quest.id in {"map", "key"} and "search" in tool.helps:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s_id, s in SETTINGS.items():
        for q_id, q in QUESTS.items():
            if not quest_can_fit(s, q):
                continue
            for m_id, m in MYSTERIES.items():
                if mystery_can_affect(s, m, q) and select_tool(q, m):
                    out.append((s_id, q_id, m_id))
    return out


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------

def describe_setting(world: World, setting: Setting, quest: Quest) -> str:
    if setting.indoors:
        return f"The {setting.place.removeprefix('the ')} was quiet, and the air felt still."
    return f"The {setting.place.removeprefix('the ')} was dim and full of little shadows."
    

def predict_mystery(world: World, hero: Entity, mystery: Mystery) -> bool:
    return True


def introduce(world: World, hero: Entity, helper: Entity, quest: Quest, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a little {next(t for t in hero.memes if False)}"
    )


def tell_story_core(world: World, hero: Entity, helper: Entity, quest: Quest, mystery: Mystery, tool: Tool) -> None:
    hero_trait = next((t for t in hero.memes.get("traits", [])), "curious")
    world.say(
        f"{hero.id} was a little {hero_trait} {hero.type} who liked solving mysteries with friends."
    )
    world.say(
        f"{hero.id} and {helper.id} were on a quest to {quest.goal}, but {mystery.label} kept getting in the way."
    )
    world.para()
    world.say(describe_setting(world, world.setting, quest))
    world.say(
        f"Every time they tried to {quest.path}, {mystery.symptom} came back again."
    )
    world.say(
        f"{hero.id} said the sound was bothersome, and {helper.id} agreed that the clue needed careful looking."
    )
    world.para()
    world.say(
        f"They used {tool.label}; {tool.shows}."
    )
    world.say(
        f"That was the clue: {mystery.clue}. Soon they found that {mystery.reveal}."
    )
    world.para()
    world.say(
        f"When they fixed it, the bothersome trouble stopped. Then {quest.ending}, and {hero.id} and {helper.id} smiled because the quest could go on."
    )
    world.say(
        f"At the end, their friendship felt stronger, and the mystery had turned into a story they could tell together."
    )


# ---------------------------------------------------------------------------
# Parameterization
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    quest: str
    mystery: str
    hero_name: str
    helper_name: str
    hero_type: str
    helper_type: str
    trait: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small mystery storyworld about friendship and a quest.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
    combos = valid_combos()
    if args.setting or args.quest or args.mystery:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.quest is None or c[1] == args.quest)
            and (args.mystery is None or c[2] == args.mystery)
        ]
    if not combos:
        raise StoryError("No valid mystery-quest story matches those options.")
    setting, quest, mystery = rng.choice(sorted(combos))
    hero_type = args.gender or rng.choice(["girl", "boy"])
    helper_type = args.helper_gender or rng.choice(["girl", "boy"])
    hero_name = args.name or rng.choice(HERO_NAMES)
    helper_name = args.helper or rng.choice([n for n in HELPER_NAMES if n != hero_name])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, quest, mystery, hero_name, helper_name, hero_type, helper_type, trait)


# ---------------------------------------------------------------------------
# Generation and QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child about "{f["mystery"].label}" during a friendship quest.',
        f"Tell a gentle story where {f['hero'].id} and {f['helper'].id} solve a bothersome clue and keep going on their quest.",
        f'Write a story set in {world.setting.place} that ends with a solved mystery and a stronger friendship.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    quest = f["quest"]
    mystery = f["mystery"]
    return [
        QAItem(
            question=f"What were {hero.id} and {helper.id} trying to do?",
            answer=f"They were on a quest to {quest.goal}.",
        ),
        QAItem(
            question=f"What bothered them during the quest?",
            answer=f"{mystery.label} bothered them, and it kept interrupting their progress.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {f['tool'].label} to follow the clue and find the real cause: {mystery.cause}.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The mystery stopped, the quest could continue, and their friendship felt stronger.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that makes people ask questions and look for clues.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a goal or mission someone tries to finish, often by following clues or solving problems.",
        ),
        QAItem(
            question="What does a magnifying glass do?",
            answer="A magnifying glass makes small things look bigger so clues are easier to see.",
        ),
    ]


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    mystery = MYSTERIES[params.mystery]
    tool = select_tool(quest, mystery)
    if tool is None:
        raise StoryError("No tool can reasonably solve that quest and mystery.")
    world = World(setting)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, memes={"traits": [params.trait]}))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    world.facts = {
        "hero": hero,
        "helper": helper,
        "quest": quest,
        "mystery": mystery,
        "tool": tool,
    }
    tell_story_core(world, hero, helper, quest, mystery, tool)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(S) :- set(S).
quest(Q) :- q(Q).
mystery(M) :- m(M).
tool(T) :- t(T).

compatible(S,Q,M) :- affords(S,A), quest_act(Q,A), mystery_fits(S,Q,M), has_tool(Q,M).
mystery_fits(S,Q,M) :- setting(S), quest(Q), mystery(M), good_pair(Q,M).
has_tool(Q,M) :- quest(Q), mystery(M), tool_for(Q,T), tool_help(T,M).
valid_story(S,Q,M) :- compatible(S,Q,M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("set", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("q", qid))
        for tag in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, tag))
        if qid in {"map", "key"}:
            lines.append(asp.fact("quest_act", qid, "search"))
        if qid == "lantern":
            lines.append(asp.fact("quest_act", qid, "follow"))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("m", mid))
        for tag in sorted(m.tags):
            lines.append(asp.fact("myst_tag", mid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("t", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("tool_help", tid, h))
    for qid, q in QUESTS.items():
        for mid, m in MYSTERIES.items():
            if mystery_can_affect(SETTINGS["library"], m, q):
                lines.append(asp.fact("good_pair", qid, mid))
        for tid, t in TOOLS.items():
            if (qid == "lantern" and "light" in t.helps) or (qid in {"map", "key"} and "search" in t.helps):
                lines.append(asp.fact("tool_for", qid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def explain_rejection() -> str:
    return "No valid mystery-quest combination matches the given options."


CURATED = [
    StoryParams("library", "map", "bump", "Maya", "Pip", "girl", "boy", "curious"),
    StoryParams("garden", "lantern", "rustle", "Eli", "June", "boy", "girl", "careful"),
    StoryParams("station", "key", "blink", "Nora", "Ari", "girl", "boy", "kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for combo in combos:
            print(" ", combo)
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
                print(str(err))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
