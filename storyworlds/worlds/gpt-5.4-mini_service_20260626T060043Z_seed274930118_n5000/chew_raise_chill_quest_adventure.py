#!/usr/bin/env python3
"""
A small Adventure-style storyworld about a Quest with chew, raise, and chill.

Seed premise:
- A child hero goes on a quest with a little problem to solve.
- The child wants to chew something helpful, raise something into place, and
  chill an overheated or worried thing.
- The quest should feel like a compact adventure: journey, obstacle, clever fix,
  and a clear ending image.

This world keeps the prose child-facing and state-driven: the story is built
from simulated meters and memes, not from a frozen paragraph with swapped nouns.
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
    worn_by: Optional[str] = None
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

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    outdoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    hazard: str
    cooling: str
    zone: set[str]
    keyword: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    covers: set[str]
    helps: set[str]
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


@dataclass
class StoryParams:
    place: str
    quest: str
    prize: str
    name: str
    gender: str
    helper: str
    trait: str
    seed: Optional[int] = None


SETTINGS = {
    "forest": Setting(place="the forest", outdoor=True, affords={"lantern", "bridge", "spring"}),
    "cave": Setting(place="the cave", outdoor=False, affords={"lantern", "bridge"}),
    "hill": Setting(place="the hill", outdoor=True, affords={"bridge", "spring"}),
}

QUESTS = {
    "chew": Quest(
        id="chew",
        verb="chew through the vines",
        gerund="chewing through vines",
        rush="dash at the vines",
        hazard="tangled and stuck",
        cooling="fresher",
        zone={"hands", "mouth"},
        keyword="chew",
    ),
    "raise": Quest(
        id="raise",
        verb="raise the broken gate",
        gerund="raising the gate",
        rush="pull up the gate",
        hazard="too heavy to lift",
        cooling="steady",
        zone={"hands", "arms"},
        keyword="raise",
    ),
    "chill": Quest(
        id="chill",
        verb="chill the hot stone",
        gerund="chilling the stone",
        rush="carry the hot stone",
        hazard="hot to hold",
        cooling="cool",
        zone={"hands"},
        keyword="chill",
    ),
}

PRIZES = {
    "lantern": Entity(id="lantern", type="lantern", label="lantern", phrase="a bright lantern"),
    "bridge": Entity(id="bridge", type="bridge", label="bridge", phrase="a little bridge"),
    "spring": Entity(id="spring", type="spring", label="spring", phrase="a clear spring"),
}

TOOLS = [
    Tool(
        id="gloves",
        label="gloves",
        phrase="a pair of sturdy gloves",
        covers={"hands"},
        helps={"chew", "raise"},
        prep="put on the gloves first",
        tail="put on the gloves and tried again",
        plural=True,
    ),
    Tool(
        id="mask",
        label="a scarf mask",
        phrase="a scarf mask",
        covers={"mouth"},
        helps={"chew"},
        prep="wrap a scarf mask around their mouth",
        tail="wrapped the scarf mask and chewed carefully",
    ),
    Tool(
        id="sling",
        label="a sling strap",
        phrase="a sling strap",
        covers={"arms"},
        helps={"raise"},
        prep="loop a sling strap under the gate",
        tail="looped the sling strap and lifted together",
    ),
    Tool(
        id="coolcloth",
        label="a cool cloth",
        phrase="a cool cloth",
        covers={"hands"},
        helps={"chill"},
        prep="wet a cool cloth in the spring",
        tail="used the cool cloth to carry the hot stone",
    ),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella", "Nora"]
BOY_NAMES = ["Leo", "Ben", "Max", "Sam", "Finn", "Theo"]
TRAITS = ["brave", "curious", "lively", "cheerful", "bold"]


def quest_at_risk(quest: Quest, prize_key: str) -> bool:
    return prize_key in SETTINGS["forest"].affords or prize_key in SETTINGS["cave"].affords or prize_key in SETTINGS["hill"].affords


def select_tool(quest: Quest) -> Optional[Tool]:
    for tool in TOOLS:
        if quest.id in tool.helps:
            return tool
    return None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure-style quest storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
    quest = args.quest or rng.choice(sorted(QUESTS))
    prize = args.prize or rng.choice(sorted(PRIZES))
    place = args.place or rng.choice(sorted(SETTINGS))
    if args.gender and args.prize and args.gender not in {"girl", "boy"}:
        raise StoryError("Invalid gender choice.")
    if args.gender and args.prize and args.gender == "boy" and prize == "spring":
        raise StoryError("That prize does not fit this hero choice.")
    name = args.name or rng.choice(GIRL_NAMES if (args.gender or rng.choice(["girl", "boy"])) == "girl" else BOY_NAMES)
    gender = args.gender or ("girl" if name in GIRL_NAMES else "boy")
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Quest, Optional[Tool]]:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    helper = world.add(Entity(id="Helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    prize = world.add(Entity(id=params.prize, type=params.prize, label=params.prize, phrase=PRIZES[params.prize].phrase))
    quest = QUESTS[params.quest]
    tool = select_tool(quest)
    return world, hero, helper, prize, quest, tool


def _run_story(world: World, hero: Entity, helper: Entity, prize: Entity, quest: Quest, tool: Optional[Tool]) -> None:
    hero.memes["hope"] = 1
    hero.memes["questing"] = 1
    world.say(f"{hero.id} was a {('little ' + next((t for t in [world.facts.get('trait', '')] if t), '')).strip()} adventurer who loved quests.")
    world.say(f"{hero.id} wanted to {quest.verb}, because the path ahead felt full of mystery.")
    world.say(f"One day, {hero.id} and {helper.label} went to {world.setting.place}.")
    world.say(f"There, {hero.id} found {prize.phrase}, and the quest began to feel real.")

    world.para()
    world.say(f"{hero.id} needed to {quest.verb}, but the task was {quest.hazard}.")
    if quest.id == "chew":
        hero.meters["blocked"] = 1
        world.say(f"The vines were twisted tight, and {hero.id} could not get past them.")
    elif quest.id == "raise":
        hero.meters["blocked"] = 1
        world.say(f"The gate sagged low, and even two hands could not lift it alone.")
    else:
        hero.meters["blocked"] = 1
        world.say(f"The stone felt hot, and {hero.id} had to let go and shake {hero.pronoun('possessive')} hands.")
    world.say(f"{hero.id} tried to {quest.rush}, but that was not enough.")

    world.para()
    helper.memes["care"] = 1
    world.say(f"{helper.label} saw the trouble and smiled.")
    if tool is not None:
        world.say(f'"How about we {tool.prep}?" {helper.label} asked.')
        world.say(f"{hero.id} agreed, and together they {tool.tail}.")
        hero.memes["joy"] = 1
        hero.meters["blocked"] = 0
        world.facts["tool"] = tool.id
    else:
        world.say(f'"Let us think of a gentler way," {helper.label} said.')
    world.say(f"After that, {hero.id} could {quest.verb} at last.")

    world.para()
    if tool is not None:
        if quest.id == "chew":
            world.say(f"The vines gave way, and the path opened wide.")
            world.say(f"{hero.id} went on, free and proud, with {prize.label} safe beside {hero.pronoun('object')}.")
        elif quest.id == "raise":
            world.say(f"The gate rose high and stayed open.")
            world.say(f"{hero.id} walked through the gate, and the little bridge beyond looked ready for adventure.")
        else:
            world.say(f"The stone grew cool, and {hero.id} held it without wincing.")
            world.say(f"{hero.id} set it down by the spring and laughed, because the quest was done.")
        world.say(f"At the end, {hero.id} felt brave, and {helper.label} looked pleased to see the calm finish.")
    else:
        world.say(f"Even without a tool, {hero.id} learned to slow down and try again.")
        world.say(f"The quest became a lesson, and the road home felt quieter.")

    world.facts.update(hero=hero, helper=helper, prize=prize, quest=quest, world=world)


def generate(params: StoryParams) -> StorySample:
    world, hero, helper, prize, quest, tool = _setup_world(params)
    world.facts["trait"] = params.trait
    _run_story(world, hero, helper, prize, quest, tool)
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
        f'Write a short Adventure-style story for a young child about a quest involving "{f["quest"].keyword}".',
        f"Tell a gentle adventure where {f['hero'].id} must {f['quest'].verb} with help from {f['helper'].label}.",
        f'Write a simple quest story that uses the word "{f["quest"].keyword}" and ends with a calm success.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    quest: Quest = f["quest"]
    prize: Entity = f["prize"]
    tool: Optional[Tool] = f.get("tool_obj")
    qs = [
        QAItem(
            question=f"What did {hero.id} want to do on the quest?",
            answer=f"{hero.id} wanted to {quest.verb}.",
        ),
        QAItem(
            question=f"Where did {hero.id} and {helper.label} go?",
            answer=f"They went to {world.setting.place} for the quest.",
        ),
        QAItem(
            question=f"What made the quest hard at first?",
            answer=f"It was hard because the task was {quest.hazard}.",
        ),
    ]
    if tool is not None:
        qs.append(QAItem(
            question=f"What helped {hero.id} finish the quest?",
            answer=f"{tool.label.capitalize()} helped {hero.id} because it made the task safer and easier.",
        ))
    return qs


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a quest?", answer="A quest is a journey or mission to find, fix, or do something important."),
        QAItem(question="What does it mean to chew something?", answer="To chew means to bite and grind something with your teeth."),
        QAItem(question="What does it mean to raise something?", answer="To raise something means to lift it up."),
        QAItem(question="What does chill mean?", answer="To chill something means to make it cool or less hot."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


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


CURATED = [
    StoryParams(place="forest", quest="chew", prize="lantern", name="Lily", gender="girl", helper="mother", trait="brave"),
    StoryParams(place="hill", quest="raise", prize="bridge", name="Leo", gender="boy", helper="father", trait="curious"),
    StoryParams(place="cave", quest="chill", prize="spring", name="Mia", gender="girl", helper="mother", trait="lively"),
]


ASP_RULES = r"""
quest_ok(Q) :- quest(Q).
tool_ok(T,Q) :- tool(T), helps(T,Q).
valid_story(P,Q,R) :- place(P), quest(Q), prize(R), quest_ok(Q), valid_pair(Q,R).
valid_pair(chew, lantern).
valid_pair(raise, bridge).
valid_pair(chill, spring).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in SETTINGS:
        lines.append(asp.fact("place", p))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for r in PRIZES:
        lines.append(asp.fact("prize", r))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    return [("forest", "chew", "lantern"), ("hill", "raise", "bridge"), ("cave", "chill", "spring")]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP matches Python.")
        return 0
    print("MISMATCH")
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.quest and args.prize:
        if (args.place, args.quest, args.prize) not in valid_combos():
            raise StoryError("That quest/prize/place combination is not a reasonable adventure.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.quest is None or c[1] == args.quest)
              and (args.prize is None or c[2] == args.prize)]
    if not combos:
        raise StoryError("No valid combo matches the requested options.")
    place, quest, prize = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = args.helper or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


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
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        triples = asp_valid_combos()
        for t in triples:
            print(" ".join(t))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
