#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/competition_husband_staple_dialogue_moral_value_bedtime.py
=========================================================================================

A tiny bedtime storyworld about a child, a quiet home competition, and a harmless
staple that should never be treated like a toy.

Premise
-------
A child wants to win a pretend competition at bedtime by making a paper crown.
They reach for a stapler, but a caring husband notices the risk, speaks gently,
and shows a safer way to finish the craft. The story always ends with a calm
moral value: use gentle tools, ask for help, and keep little hands safe.

The world model keeps track of:
- who is present,
- which object is fragile or sharp,
- how the competition score changes,
- emotional state through simple memes,
- and whether the ending is safe, delayed, or rejected by common sense.

It includes:
- dialogue,
- a clear moral value,
- bedtime-story tone,
- a reasonableness gate,
- an inline ASP twin,
- and three separate Q&A sets generated from simulated world state.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/competition_husband_staple_dialogue_moral_value_bedtime.py
    python storyworlds/worlds/gpt-5.4-mini/competition_husband_staple_dialogue_moral_value_bedtime.py --qa
    python storyworlds/worlds/gpt-5.4-mini/competition_husband_staple_dialogue_moral_value_bedtime.py --all
    python storyworlds/worlds/gpt-5.4-mini/competition_husband_staple_dialogue_moral_value_bedtime.py --verify
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "husband"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "husband": "husband"}.get(self.type, self.type)



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Setting:
    id: str
    place: str
    bedtime: bool
    cozy_line: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Competition:
    id: str
    name: str
    prize: str
    verb: str
    win_line: str
    moral: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class StapleTool:
    id: str
    label: str
    phrase: str
    sharp: bool = True
    allowed: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class SafeTool:
    id: str
    label: str
    phrase: str
    glow: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
@dataclass
class StoryParams:
    setting: str
    competition: str
    staple: str
    safe_tool: str
    child: str
    child_gender: str
    husband: str
    husband_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


SETTINGS = {
    "bedroom": Setting("bedroom", "the cozy bedroom", True, "The room was warm, and a night-light glowed by the bed."),
    "nursery": Setting("nursery", "the nursery corner", True, "The nursery was soft and quiet, with a blanket tucked on the chair."),
    "playroom": Setting("playroom", "the playroom nook", False, "The playroom was calm, and paper hearts lay on the table."),
}

COMPETITIONS = {
    "paper_crown": Competition("paper_crown", "paper-crown competition", "a paper crown", "make a paper crown", "best crown wins", "be gentle with tools"),
    "bedtime_banner": Competition("bedtime_banner", "bedtime banner competition", "a banner", "make a bedtime banner", "the neatest banner wins", "choose safe hands"),
}

STAPLES = {
    "stapler": StapleTool("stapler", "stapler", "the stapler", sharp=True, allowed=False),
    "mini_stapler": StapleTool("mini_stapler", "mini stapler", "the mini stapler", sharp=True, allowed=False),
}

SAFE_TOOLS = {
    "glue": SafeTool("glue", "glue stick", "a glue stick", "shone softly"),
    "tape": SafeTool("tape", "tape roll", "a tape roll", "unrolled neatly"),
    "string": SafeTool("string", "string", "a spool of string", "lay in a neat loop"),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Noah", "Theo", "Ben", "Eli", "Max", "Finn"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for cid in COMPETITIONS:
            for stapid, tool in STAPLES.items():
                if tool.sharp and not tool.allowed:
                    combos.append((sid, cid, stapid))
    return combos


def reasonableness_gate(staple: StapleTool) -> bool:
    return not staple.allowed and staple.sharp


def explain_rejection(staple: StapleTool) -> str:
    return f"(No story: {staple.label} is sharp, and little bedtime hands should not use it as a craft tool. Choose glue, tape, or string instead.)"


def parse_gendered_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def _predict_breakage(world: World, child_id: str, staple_id: str) -> dict:
    sim = world.copy()
    child = sim.get(child_id)
    child.memes["curiosity"] += 1
    if staple_id in sim.entities:
        sim.get(staple_id).meters["risk"] += 1
    return {
        "risk": sim.get(staple_id).meters["risk"] if staple_id in sim.entities else 0,
        "fear": child.memes["fear"],
    }


def _use_staple(world: World, child: Entity, tool: StapleTool) -> None:
    child.memes["risk"] += 1
    world.get("tool").meters["risk"] += 1


def _fix_with_safe_tool(world: World, child: Entity, helper: Entity, competition: Competition, safe: SafeTool) -> None:
    child.memes["joy"] += 1
    child.memes["safety"] += 1
    helper.memes["pride"] += 1
    world.say(f"{helper.id} smiled and handed over {safe.phrase}, which {safe.glow}.")
    world.say(f'"Try that," {helper.id} said softly. "It will hold the paper together without any sharp edges."')
    world.say(f'{child.id} nodded and used {safe.phrase} instead, so the {competition.prize} came together neatly.')


def setup(world: World, child: Entity, helper: Entity, competition: Competition) -> None:
    child.memes["hope"] += 1
    helper.memes["calm"] += 1
    world.say(f"At bedtime, {child.id} and {helper.id} had a tiny competition to {competition.verb}.")
    world.say(f'{competition.win_line.capitalize()}, and the winner would get to wear {competition.prize} to sleep.')
    world.say(world.setting.cozy_line)


def temptation(world: World, child: Entity, tool: StapleTool) -> None:
    child.memes["impulse"] += 1
    world.say(f'{child.id} looked at {tool.label} and whispered, "This will be fast."')
    world.say(f'"Fast is not always safe," came the gentle reply from the other side of the table.')


def warn(world: World, helper: Entity, child: Entity, tool: StapleTool) -> None:
    pred = _predict_breakage(world, child.id, tool.id)
    helper.memes["concern"] += 1
    world.say(f'"That {tool.label} is for grown-up papers," {helper.id} said. "It can pinch fingers."')
    if pred["risk"] > 0:
        world.say(f'"If you rush, you could get hurt before bedtime," {helper.id} added.')


def conflict(world: World, child: Entity) -> None:
    child.memes["defiance"] += 1
    world.say(f'{child.id} frowned. "But I want my crown to win," {child.id} said.')
    world.say(f'The room felt smaller for a moment, like the competition had become too serious.')


def turn_to_help(world: World, helper: Entity, child: Entity, tool: StapleTool, safe: SafeTool, competition: Competition) -> None:
    helper.memes["love"] += 1
    world.say(f'"Winning is nice," {helper.id} said, "but keeping your fingers safe matters more."')
    world.say(f'"Let me show you a kinder way," {helper.id} said, reaching for {safe.label}.')
    _fix_with_safe_tool(world, child, helper, competition, safe)


def ending(world: World, child: Entity, helper: Entity, competition: Competition) -> None:
    child.memes["joy"] += 1
    world.say(f'By the end, {child.id} had a neat {competition.prize}, and {helper.id} tucked the stapler away.')
    world.say(f'{child.id} smiled sleepily. "I learned something," {child.id} said.')
    world.say(f'"What did you learn?" {helper.id} asked.')
    world.say(f'"That being careful is part of winning," {child.id} whispered, and the lights grew dim and gentle.')


def tell(setting: Setting, competition: Competition, staple: StapleTool, safe: SafeTool,
         child: str = "Mia", child_gender: str = "girl",
         husband: str = "Jonah", husband_gender: str = "husband") -> World:
    world = World(setting)
    c = world.add(Entity(id=child, kind="character", type=child_gender, role="child"))
    h = world.add(Entity(id=husband, kind="character", type=husband_gender, role="husband"))
    tool = world.add(Entity(id=staple.id, kind="thing", type="tool", label=staple.label))
    world.add(Entity(id=safe.id, kind="thing", type="tool", label=safe.label))
    world.facts["competition"] = competition
    world.facts["staple"] = staple
    world.facts["safe"] = safe

    setup(world, c, h, competition)
    world.para()
    temptation(world, c, staple)
    warn(world, h, c, staple)
    conflict(world, c)
    world.para()
    turn_to_help(world, h, c, staple, safe, competition)
    ending(world, c, h, competition)

    world.facts.update(child=c, husband=h, tool=tool, outcome="safe")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c = f["child"]
    comp = f["competition"]
    staple = f["staple"]
    return [
        f'Write a bedtime story with dialogue that includes the words "competition", "{staple.label}", and "husband".',
        f"Tell a gentle moral-value story where {c.id} tries to win a {comp.name} and wants to use {staple.label}, but a kind husband helps them choose a safer tool.",
        f"Write a sleepy, child-friendly story about a competition, a stapler, and a lesson about being careful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c = f["child"]
    h = f["husband"]
    comp = f["competition"]
    staple = f["staple"]
    qa = [
        QAItem(question="Who is the story about?", answer=f"It is about {c.id} and {h.id}, who were sharing a bedtime competition. The child wanted to make something special, and the husband helped keep the moment safe."),
        QAItem(question="What did the child want to use?", answer=f"{c.id} wanted to use {staple.label}. {h.id} stopped that idea because it could pinch fingers and was not a safe craft tool."),
        QAItem(question="How was the problem solved?", answer=f"They solved it by choosing a safer tool and working together. That let the {comp.prize} get finished without any sharp edges."),
        QAItem(question="What moral did the story teach?", answer="It taught that being careful is more important than rushing to win. Gentle tools and kind help make bedtime crafts safer."),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a stapler?", answer="A stapler is a tool that joins paper with small metal pieces called staples. It is meant for papers, not for play."),
        QAItem(question="Why can a staple be dangerous?", answer="A staple is small but sharp, so it can poke or pinch fingers. Little children should ask a grown-up for help with it."),
        QAItem(question="What is a moral value?", answer="A moral value is a lesson about how to act kindly and wisely. It helps people choose what is safe, fair, and good."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines += [f"{i+1}. {p}" for i, p in enumerate(sample.prompts)]
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        bits.append(f"type={e.type}")
        out.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(out)


CURATED = [
    StoryParams("bedroom", "paper_crown", "stapler", "glue", "Mia", "girl", "Jonah", "husband"),
    StoryParams("nursery", "bedtime_banner", "mini_stapler", "tape", "Noah", "boy", "Evan", "husband"),
    StoryParams("playroom", "paper_crown", "stapler", "string", "Lily", "girl", "Owen", "husband"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.staple and not reasonableness_gate(STAPLES[args.staple]):
        raise StoryError(explain_rejection(STAPLES[args.staple]))
    if args.competition and args.setting and args.staple:
        pass
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.competition is None or c[1] == args.competition)
              and (args.staple is None or c[2] == args.staple)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting_id, comp_id, staple_id = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or parse_gendered_name(rng, gender)
    husband = args.husband or rng.choice(["Jonah", "Owen", "Evan", "Caleb", "Noah"])
    return StoryParams(setting_id, comp_id, staple_id, args.safe_tool or rng.choice(list(SAFE_TOOLS)), child, gender, husband, "husband")


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], COMPETITIONS[params.competition],
                 STAPLES[params.staple], SAFE_TOOLS[params.safe_tool],
                 params.child, params.child_gender, params.husband, params.husband_gender)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: competition, husband, and a staple.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--competition", choices=COMPETITIONS)
    ap.add_argument("--staple", choices=STAPLES)
    ap.add_argument("--safe-tool", choices=SAFE_TOOLS, dest="safe_tool")
    ap.add_argument("--child")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--husband")
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


ASP_RULES = r"""
sharp_tool(T) :- staple(T), sharp(T).
valid(S, C, T) :- setting(S), competition(C), staple(T), sharp_tool(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in COMPETITIONS:
        lines.append(asp.fact("competition", cid))
    for tid, t in STAPLES.items():
        lines.append(asp.fact("staple", tid))
        if t.sharp:
            lines.append(asp.fact("sharp", tid))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches valid_combos().")
    else:
        rc = 1
        print("MISMATCH: ASP and Python gates differ.")
    sample = generate(CURATED[0])
    if not sample.story.strip():
        rc = 1
        print("MISMATCH: generate() returned empty story.")
    else:
        print("OK: generate() smoke test passed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
