#!/usr/bin/env python3
"""
storyworlds/worlds/cheap_breaker_reconciliation_mystery_to_solve_quest.py
=========================================================================

A standalone story world for a gentle ghost story with a small mystery, a quest,
and a reconciliation at the end.

Seed premise:
- A child finds a cheap breaker box in an old house.
- A ghostly mystery must be solved by following clues.
- The quest ends in reconciliation: the ghost and the living family make peace.
- The story must use the words "cheap" and "breaker".

The world models:
- typed entities with physical meters and emotional memes
- a simple forward-chaining causal engine
- a predict-then-warn beat
- reasonableness gates for valid story combinations
- three Q&A sets grounded in world state
- an inline ASP twin for the same gates and outcome logic
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    haunted: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    reveal: str
    method: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    helps: set[str] = field(default_factory=set)
    cheap: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Spirit:
    id: str
    name: str
    label: str
    wants: str
    room: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Quest:
    id: str
    goal: str
    end_image: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.turn_tokens: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.turn_tokens = list(self.turn_tokens)
        return clone

    def children(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_lonely(world: World) -> list[str]:
    out = []
    ghost = world.facts["ghost"]
    child = world.facts["child"]
    if ghost.memes["lonely"] < THRESHOLD:
        return out
    sig = ("lonely", ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["unease"] += 1
    out.append("A lonely hush drifted through the hallway.")
    return out


def _r_secret(world: World) -> list[str]:
    out = []
    breaker = world.facts["breaker"]
    mystery = world.facts["mystery"]
    child = world.facts["child"]
    if breaker.meters["clicked"] < THRESHOLD or mystery.meters["noticed"] < THRESHOLD:
        return out
    sig = ("secret", breaker.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1
    mystery.meters["active"] += 1
    out.append("A secret puzzle seemed to hum behind the wall.")
    return out


def _r_reconcile(world: World) -> list[str]:
    out = []
    ghost = world.facts["ghost"]
    family = world.facts["family"]
    if ghost.memes["heard"] < THRESHOLD or family.memes["kindness"] < THRESHOLD:
        return out
    sig = ("reconcile", ghost.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    ghost.memes["peace"] += 1
    family.memes["peace"] += 1
    out.append("The cold in the room softened at last.")
    return out


CAUSAL_RULES = [
    Rule("lonely", "social", _r_lonely),
    Rule("secret", "mystery", _r_secret),
    Rule("reconcile", "social", _r_reconcile),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mystery(world: World, child: Entity, breaker: Entity) -> dict:
    sim = world.copy()
    sim.get(breaker.id).meters["clicked"] += 1
    propagate(sim, narrate=False)
    return {
        "mystery": sim.facts["mystery"].meters["active"] >= THRESHOLD,
        "unease": sim.get(child.id).memes["unease"],
    }


def complaint(world: World, child: Entity, spirit: Entity, mystery: Mystery) -> None:
    child.memes["unease"] += 1
    world.say(
        f"{child.id} found a cheap breaker box in the old house and heard a soft tap behind the wall."
    )
    world.say(
        f'"This room feels strange," {child.id} whispered. "I think {spirit.label} is trying to tell us something."'
    )


def inspect(world: World, child: Entity, breaker: Entity, mystery: Mystery) -> None:
    breaker.meters["clicked"] += 1
    mystery.meters["noticed"] += 1
    world.say(
        f"{child.id} pressed the breaker and listened. The cheap panel gave a tiny click, and the hallway fell quiet again."
    )
    propagate(world, narrate=True)


def ask_for_help(world: World, child: Entity, parent: Entity, tool: Tool, mystery: Mystery) -> None:
    pred = predict_mystery(world, child, world.facts["breaker"])
    world.facts["predicted_mystery"] = pred["mystery"]
    if pred["mystery"]:
        world.say(
            f'"Can we use the {tool.label} to follow the clue?" {child.id} asked, and {parent.label_word} nodded toward the dark hallway.'
        )


def quest_step(world: World, child: Entity, spirit: Entity, quest: Quest, tool: Tool, mystery: Mystery) -> None:
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} took the {tool.label} and walked the hallway quest step by step, looking for the source of the tapping."
    )
    if tool.cheap:
        world.say(
            f"The cheap little light was enough to show a loose latch, a bent nail, and a note tucked beside the breaker."
        )
    mystery.meters["solved"] += 1
    spirit.meters["seen"] += 1
    world.say(
        f"The note matched the clue: {mystery.reveal}. At the end of the quest, {spirit.name} was no longer hiding."
    )


def reconcile(world: World, family: Entity, spirit: Entity, quest: Quest) -> None:
    family.memes["kindness"] += 1
    spirit.memes["heard"] += 1
    spirit.memes["peace"] += 1
    family.memes["peace"] += 1
    world.say(
        f"{family.label_word.capitalize()} spoke softly to {spirit.name}, and {spirit.name} answered with a sad little sigh."
    )
    world.say(
        f"They promised to leave the old house lamp on each night, and the room felt warmer, as if the walls had finally forgiven the dark."
    )
    world.say(quest.end_image)


SETTINGS = {
    "hall": Setting(id="hall", place="the old hallway", mood="quiet", affords={"inspect", "quest"}),
    "attic": Setting(id="attic", place="the attic room", mood="dusty", affords={"inspect", "quest"}),
    "basement": Setting(id="basement", place="the basement stairs", mood="echoing", affords={"inspect", "quest"}),
    "porch": Setting(id="porch", place="the porch room", mood="moonlit", affords={"inspect", "quest"}),
}

MYSTERIES = {
    "tap": Mystery(
        id="tap",
        clue="a tiny tap behind the wall",
        reveal="the tap came from a loose latch knocking in the breeze",
        method="listen for the click and follow the sound",
        tags={"mystery", "sound"},
    ),
    "glow": Mystery(
        id="glow",
        clue="a pale glow under the floorboard",
        reveal="the glow was a lantern hiding under a loose board",
        method="lift the board and find the light",
        tags={"mystery", "light"},
    ),
    "note": Mystery(
        id="note",
        clue="a folded note beside the breaker",
        reveal="the note belonged to the ghost and asked for the lamp to be fixed",
        method="find the note and read it aloud",
        tags={"mystery", "message"},
    ),
}

TOOLS = {
    "cheap_lamp": Tool(
        id="cheap_lamp",
        label="cheap lamp",
        phrase="a cheap lamp",
        use="shine a little light",
        helps={"quest", "mystery"},
        cheap=True,
        tags={"cheap", "light"},
    ),
    "breaker": Tool(
        id="breaker",
        label="breaker",
        phrase="the breaker",
        use="switch the lights on",
        helps={"quest", "light"},
        cheap=False,
        tags={"breaker", "power"},
    ),
    "lantern": Tool(
        id="lantern",
        label="lantern",
        phrase="a lantern",
        use="light the hallway",
        helps={"quest", "light"},
        cheap=False,
        tags={"light"},
    ),
}

SPIRITS = {
    "nora": Spirit(
        id="nora",
        name="Nora",
        label="Nora",
        wants="the house to feel remembered",
        room="hall",
        tags={"ghost", "reconciliation"},
    ),
    "milo": Spirit(
        id="milo",
        name="Milo",
        label="Milo",
        wants="the lamp to be fixed",
        room="attic",
        tags={"ghost", "reconciliation"},
    ),
    "ivy": Spirit(
        id="ivy",
        name="Ivy",
        label="Ivy",
        wants="someone to read the hidden note",
        room="basement",
        tags={"ghost", "reconciliation"},
    ),
}

QUESTS = {
    "listen": Quest(
        id="listen",
        goal="solve the mystery",
        end_image="By morning, the hallway looked calm and still, with the breaker set straight and the cheap lamp glowing like a small star.",
        tags={"quest", "mystery"},
    ),
    "find_note": Quest(
        id="find_note",
        goal="follow the clue",
        end_image="By morning, the note rested on the table, and the hallway was no longer dark enough to frighten anyone.",
        tags={"quest", "mystery"},
    ),
    "repair": Quest(
        id="repair",
        goal="make peace with the ghost",
        end_image="By morning, the old house felt settled, and the breaker box hummed gently without a single shiver in the walls.",
        tags={"quest", "reconciliation"},
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Tess", "Iris", "Nina", "June", "Rosa", "Wren"]
BOY_NAMES = ["Owen", "Theo", "Finn", "Leo", "Evan", "Milo", "Noah", "Jude"]
TRAITS = ["brave", "curious", "careful", "gentle", "bright"]


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    spirit: str
    quest: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for s in SETTINGS:
        for m in MYSTERIES:
            for t in TOOLS:
                for sp in SPIRITS:
                    for q in QUESTS:
                        if "quest" in QUESTS[q].tags and "ghost" in SPIRITS[sp].tags:
                            combos.append((s, m, t, sp, q))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with mystery, quest, and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--spirit", choices=SPIRITS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
              if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)
              and (args.spirit is None or c[3] == args.spirit)
              and (args.quest is None or c[4] == args.quest)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, mystery, tool, spirit, quest = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, mystery=mystery, tool=tool, spirit=spirit, quest=quest, name=name, gender=gender, parent=parent, trait=trait)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    spirit = SPIRITS[params.spirit]
    quest = QUESTS[params.quest]
    world = World(setting)

    child = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent, label="the parent"))
    ghost = world.add(Entity(id=spirit.id, kind="character", type="thing", label=spirit.name, role="ghost", haunted=True))
    breaker = world.add(Entity(id="breaker", type="thing", label="breaker", phrase="the breaker box"))
    mystery_ent = world.add(Entity(id="mystery", type="thing", label="mystery"))
    family = world.add(Entity(id="family", kind="character", type=params.parent, label="the family"))

    ghost.memes["lonely"] = 1.0
    family.memes["kindness"] = 0.0
    mystery_ent.meters["noticed"] = 0.0
    mystery_ent.meters["active"] = 0.0
    mystery_ent.meters["solved"] = 0.0
    breaker.meters["clicked"] = 0.0
    child.memes["curiosity"] = 0.0
    child.memes["unease"] = 0.0
    child.memes["bravery"] = 0.0
    ghost.memes["heard"] = 0.0
    ghost.memes["peace"] = 0.0
    family.memes["peace"] = 0.0

    world.facts.update(child=child, parent=parent, ghost=ghost, breaker=breaker, mystery=mystery_ent,
                       family=family, setting=setting, mystery_cfg=mystery, tool=tool, spirit=spirit, quest=quest)
    world.say(f"{child.id} and {parent.label_word} went into {setting.place}, where the air felt {setting.mood} and a ghost story seemed to wait in every corner.")
    world.say(f"Somebody had left behind a cheap breaker box and a mystery clue: {mystery.clue}.")
    world.para()
    complaint(world, child, ghost, mystery)
    inspect(world, child, breaker, mystery)
    ask_for_help(world, child, parent, tool, mystery)
    world.para()
    quest_step(world, child, ghost, quest, tool, mystery)
    reconcile(world, family, ghost, quest)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle ghost story for a young child about {f["child"].id}, a cheap breaker box, and a mystery clue in {f["setting"].place}.',
        f"Tell a quest story where {f['child'].id} follows {f['mystery_cfg'].method} and makes peace with {f['spirit'].name} at the end.",
        f'Write a spooky-but-kind story that includes the words "cheap" and "breaker" and ends with reconciliation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    spirit = f["spirit"]
    mystery = f["mystery_cfg"]
    quest = f["quest"]
    tool = f["tool"]
    parent = f["parent"]
    return [
        QAItem(
            f"Who goes looking for the mystery in {f['setting'].place}?",
            f"{child.id} goes looking with {parent.label_word}, and the two of them follow the strange clue together.",
        ),
        QAItem(
            f"What clue starts the quest?",
            f"The clue is {mystery.clue}. It is what makes the ghost story turn into a mystery to solve.",
        ),
        QAItem(
            f"Why does the cheap breaker matter in the story?",
            f"It gives {child.id} a place to listen for the hidden problem. The cheap breaker click helps point the quest toward the right wall and the right answer.",
        ),
        QAItem(
            f"How does {child.id} finish the quest with {spirit.name}?",
            f"{child.id} follows the clue, solves the mystery, and speaks kindly to {spirit.name}. That turns the spooky feeling into reconciliation.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a mystery?", "A mystery is a question you do not know the answer to yet. You solve it by looking closely and following clues."),
        QAItem("What is a quest?", "A quest is a journey to reach a goal. A quest usually has steps to follow and a problem to solve."),
        QAItem("What is reconciliation?", "Reconciliation means making peace after a disagreement or a sad feeling. It can happen when people listen and speak kindly."),
        QAItem("Why can an old house feel spooky?", "An old house can feel spooky because it creaks, echoes, and has dark corners. Those sounds can make someone imagine a ghost story."),
        QAItem("What does cheap mean?", "Cheap means something does not cost much money. It can still be useful even if it is simple."),
        QAItem("What is a breaker?", "A breaker is a switch that helps control electricity in a house. It can turn power on or off."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.haunted:
            bits.append("haunted=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,T,Sp,Q) :- setting(S), mystery(M), tool(T), spirit(Sp), quest(Q).
solves(Q) :- quest(Q), mystery(M), tool(T), spirit(Sp), setting(S), valid(S,M,T,Sp,Q).
reconciles(Sp) :- spirit(Sp), ghost(Sp).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for t, obj in TOOLS.items():
        lines.append(asp.fact("tool", t))
        if obj.cheap:
            lines.append(asp.fact("cheap", t))
    for sp in SPIRITS:
        lines.append(asp.fact("spirit", sp))
        lines.append(asp.fact("ghost", sp))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    try:
        combos = set(valid_combos())
        clingo = set(asp_valid_combos())
    except Exception as e:
        print(f"VERIFY FAILED: {e}")
        return 1
    if combos != clingo:
        print("MISMATCH between Python and ASP valid combos.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    print(f"OK: verify passed ({len(combos)} combos).")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        raise StoryError("Unknown setting.")
    if params.mystery not in MYSTERIES:
        raise StoryError("Unknown mystery.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.spirit not in SPIRITS:
        raise StoryError("Unknown spirit.")
    if params.quest not in QUESTS:
        raise StoryError("Unknown quest.")
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


CURATED = [
    StoryParams(setting="hall", mystery="tap", tool="cheap_lamp", spirit="nora", quest="listen", name="Mina", gender="girl", parent="mother", trait="curious"),
    StoryParams(setting="attic", mystery="glow", tool="lantern", spirit="milo", quest="find_note", name="Owen", gender="boy", parent="father", trait="gentle"),
    StoryParams(setting="basement", mystery="note", tool="breaker", spirit="ivy", quest="repair", name="Tess", gender="girl", parent="mother", trait="brave"),
    StoryParams(setting="porch", mystery="tap", tool="cheap_lamp", spirit="ivy", quest="repair", name="Jude", gender="boy", parent="father", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for row in asp_valid_combos():
            print(row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.setting} / {p.mystery} / {p.quest}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
