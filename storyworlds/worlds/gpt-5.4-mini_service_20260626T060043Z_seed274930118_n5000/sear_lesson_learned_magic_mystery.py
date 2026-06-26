#!/usr/bin/env python3
"""
Standalone storyworld: a small mystery with magic and a lesson learned.

This world models a child-sized detective tale: something gets seared, a little
bit of magic helps uncover the truth, and the ending proves the lesson learned.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"soot": 0.0, "worry": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "fear": 0.0, "relief": 0.0, "lesson": 0.0}

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
    indoor: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    cause: str
    visible_sign: str
    hidden_truth: str
    clue_place: str
    risk: str
    lesson: str
    tag: str = "mystery"


@dataclass
class MagicTool:
    id: str
    label: str
    phrase: str
    reveal: str
    prep: str
    ending: str
    needs: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.magic_on: bool = False

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
        clone.magic_on = self.magic_on
        return clone


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    name: str
    gender: str
    sidekick: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting("the kitchen", True, {"crumbs", "light"}),
    "attic": Setting("the attic", True, {"dust", "shadow"}),
    "garden": Setting("the garden", False, {"ash", "light"}),
}

MYSTERIES = {
    "sear": Mystery(
        id="sear",
        cause="a too-hot lantern",
        visible_sign="a dark seared ring on the pancake",
        hidden_truth="the lantern tipped over and kissed the batter with heat",
        clue_place="the window ledge",
        risk="the burned smell would point to the wrong thing",
        lesson="do not guess before looking for clues",
    ),
    "smoke": Mystery(
        id="smoke",
        cause="a candle left near paper",
        visible_sign="a smoky streak on the page",
        hidden_truth="a candle warmed the page and left a smoky mark",
        clue_place="the desk drawer",
        risk="the mystery could blame the wrong person",
        lesson="slow down and check every corner",
    ),
    "glow": Mystery(
        id="glow",
        cause="moonlight through glass",
        visible_sign="a strange glow on the floor",
        hidden_truth="moonlight passed through a blue jar and painted the tiles",
        clue_place="the shelf",
        risk="the glow looked spooky until the truth was found",
        lesson="sometimes scary things are only ordinary things in disguise",
    ),
}

TOOLS = {
    "lens": MagicTool(
        id="lens",
        label="a magic lens",
        phrase="a magic lens with a silver rim",
        reveal="it made hidden marks shimmer into view",
        prep="held up the magic lens",
        ending="and the little shimmer pointed straight to the truth",
        needs={"mystery"},
    ),
    "chalk": MagicTool(
        id="chalk",
        label="a magic chalk stick",
        phrase="a magic chalk stick that glowed softly",
        reveal="it traced secret lines on the floor",
        prep="drew with the magic chalk",
        ending="and the glowing line led them to the answer",
        needs={"shadow", "mystery"},
    ),
    "bell": MagicTool(
        id="bell",
        label="a tiny magic bell",
        phrase="a tiny magic bell on a blue string",
        reveal="it rang when it was near the clue",
        prep="jingled the tiny magic bell",
        ending="and the soft ring showed where the clue had been hiding",
        needs={"mystery"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Nora", "Ivy", "Zoe", "Ella"]
BOY_NAMES = ["Leo", "Finn", "Theo", "Ben", "Max", "Owen"]
SIDEKICKS = ["cat", "dog", "sparrow", "mouse"]

TRAITS = ["careful", "curious", "brave", "gentle", "quick-thinking"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for m_id, m in MYSTERIES.items():
            for t_id, t in TOOLS.items():
                if "mystery" in t.needs and m.id:
                    out.append((s, m_id, t_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery world with a lesson learned and a touch of magic.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    if args.setting or args.mystery or args.tool:
        combos = [
            c for c in combos
            if (args.setting is None or c[0] == args.setting)
            and (args.mystery is None or c[1] == args.mystery)
            and (args.tool is None or c[2] == args.tool)
        ]
    if not combos:
        raise StoryError("(No valid mystery combination matches the given options.)")
    setting, mystery, tool = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    sidekick = args.sidekick or rng.choice(SIDEKICKS)
    return StoryParams(setting=setting, mystery=mystery, tool=tool, name=name, gender=gender, sidekick=sidekick)


def _intro(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who noticed tiny things, and {sidekick.label} was always nearby."
    )
    world.say(
        f"One day, {hero.id} found {mystery.visible_sign} in {world.setting.place}."
    )


def _investigate(world: World, hero: Entity, sidekick: Entity, mystery: Mystery, tool: MagicTool) -> None:
    hero.memes["curiosity"] += 1
    hero.meters["worry"] += 1
    world.say(
        f"{hero.id} felt curious but worried, because {mystery.risk}."
    )
    world.say(
        f"So {hero.id} {tool.prep} while {sidekick.label} watched closely."
    )
    world.magic_on = True
    if mystery.id == "sear":
        world.say(
            f"The air gave off a warm smell, and the magic lens {tool.reveal}."
        )
    elif mystery.id == "smoke":
        world.say(
            f"The magic chalk {tool.reveal}."
        )
    else:
        world.say(
            f"The tiny magic bell {tool.reveal}."
        )


def _reveal(world: World, hero: Entity, sidekick: Entity, mystery: Mystery) -> None:
    hero.meters["worry"] = max(0.0, hero.meters["worry"] - 1.0)
    hero.memes["relief"] += 1
    hero.memes["lesson"] += 1
    world.say(
        f"At last, they found the clue near {mystery.clue_place}, and the truth was simple: {mystery.hidden_truth}."
    )
    world.say(
        f"{hero.id} learned the lesson to {mystery.lesson}."
    )
    world.say(
        f"{hero.id} smiled, because the strange sign was not a monster at all, just an ordinary thing with a hidden cause."
    )


def tell(setting: Setting, mystery: Mystery, tool: MagicTool, hero_name: str, hero_type: str, sidekick: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    buddy = world.add(Entity(id=sidekick, kind="character", type=sidekick, label=f"the {sidekick}"))
    clue = world.add(Entity(id="clue", type="clue", label=mystery.visible_sign, owner=hero.id, region="floor"))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))
    world.facts.update(hero=hero, buddy=buddy, clue=clue, tool=tool_ent, mystery=mystery, setting=setting)
    _intro(world, hero, buddy, mystery)
    world.para()
    _investigate(world, hero, buddy, mystery, tool)
    world.para()
    _reveal(world, hero, buddy, mystery)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short mystery story for a child that includes the word "{f["mystery"].id}" and a little magic clue-finding tool.',
        f"Tell a gentle mystery where {f['hero'].id} notices {f['mystery'].visible_sign} in {f['setting'].place} and learns a lesson.",
        f"Write a child-facing story about a strange sign, magic, and discovering that the cause was only {f['mystery'].cause}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    mystery: Mystery = f["mystery"]
    tool: Entity = f["tool"]
    qa = [
        QAItem(
            question=f"What did {hero.id} find at the start of the mystery?",
            answer=f"{hero.id} found {mystery.visible_sign} in {world.setting.place}. It looked strange, so {hero.id} started to investigate.",
        ),
        QAItem(
            question=f"What magic tool did {hero.id} use to look for clues?",
            answer=f"{hero.id} used {tool.label}. It helped hidden marks shimmer and made the clue easier to notice.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn by the end?",
            answer=f"{hero.id} learned to {mystery.lesson}. After looking carefully, the scary-looking sign made sense.",
        ),
    ]
    if mystery.id == "sear":
        qa.append(
            QAItem(
                question=f"Why did the burned smell matter in the story?",
                answer=f"The burned smell was a clue. It pointed to heat from {mystery.cause}, instead of making the mystery seem bigger than it was.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    m: Mystery = world.facts["mystery"]
    tool: Entity = world.facts["tool"]
    out = []
    if m.id == "sear":
        out.append(QAItem(
            question="What does sear mean?",
            answer="To sear means to burn the outside of something quickly with very hot heat, so it can leave a dark mark or a crisp smell.",
        ))
    if "lens" in tool.id:
        out.append(QAItem(
            question="What can a magnifying or magic lens help you do?",
            answer="A lens can make small details easier to see, so it is helpful when you are searching for clues.",
        ))
    out.append(QAItem(
        question="What is a mystery?",
        answer="A mystery is something that seems puzzling at first, but careful looking and thinking can help explain it.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- setting(S).
mystery(M) :- mystery(M).
tool(T) :- tool(T).

valid(S,M,T) :- setting(S), mystery(M), tool(T).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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


def explain_rejection() -> str:
    return "(No story: that combination does not produce a coherent mystery.)"


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        MYSTERIES[params.mystery],
        TOOLS[params.tool],
        params.name,
        params.gender,
        params.sidekick,
    )
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


def CURATED() -> list[StoryParams]:
    return [
        StoryParams(setting="kitchen", mystery="sear", tool="lens", name="Mia", gender="girl", sidekick="cat"),
        StoryParams(setting="attic", mystery="smoke", tool="chalk", name="Leo", gender="boy", sidekick="mouse"),
        StoryParams(setting="garden", mystery="glow", tool="bell", name="Nora", gender="girl", sidekick="sparrow"),
    ]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED()]
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
            header = f"### {p.name}: {p.mystery} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
