#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T000000Z_seed1245732883_n10/multirise_chuckle_mystery_to_solve_bad_ending.py
====================================================================================================

A small tall-tale storyworld about a mystery that should be solved, but can end
badly when the clues are missed or the fix comes too late.

Seed words: multirise, chuckle
Features: Mystery to Solve, Bad Ending
Style: Tall Tale
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

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
        return self.label or self.id


@dataclass
class Setting:
    id: str
    name: str
    place_desc: str
    mystery_desc: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Mystery:
    id: str
    clue: str
    cause: str
    risk: str
    solve_action: str
    fail_action: str
    solve_text: str
    fail_text: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    helpful_for: set[str] = field(default_factory=set)
    risky_for: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out = []
    lantern = world.entities.get("lantern")
    if not lantern:
        return out
    if lantern.meters["glow"] >= THRESHOLD and not world.facts.get("solved"):
        sig = ("alarm",)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        world.get("crowd").memes["worry"] += 1
        out.append("The lantern glow made the whole lane uneasy.")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm)]


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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            for tid, tool in TOOLS.items():
                if mystery.solve_action in tool.helpful_for and mystery.risk in tool.risky_for:
                    combos.append((sid, mid, tid))
    return combos


@dataclass
class StoryParams:
    setting: str
    mystery: str
    tool: str
    hero: str
    hero_gender: str
    helper: str
    helper_gender: str
    ending: str
    seed: Optional[int] = None


SETTINGS = {
    "river_town": Setting(
        id="river_town",
        name="the river town",
        place_desc="a little town with crooked bridges and bright docks",
        mystery_desc="the water kept climbing the steps one inch at a time",
        tags={"river", "town", "multirise"},
    ),
    "hill_fair": Setting(
        id="hill_fair",
        name="the hill fair",
        place_desc="a fair on a windy hill with tin roofs and striped tents",
        mystery_desc="the fairground bell rang by itself every sunrise",
        tags={"hill", "fair", "multirise"},
    ),
    "orchard": Setting(
        id="orchard",
        name="the old orchard",
        place_desc="an orchard full of twisting trees and apple carts",
        mystery_desc="a ladder rose higher each time anybody looked away",
        tags={"orchard", "mystery"},
    ),
}

MYSTERIES = {
    "rises": Mystery(
        id="rises",
        clue="a ladder of scratch marks on the wall",
        cause="the moon-tide under the floorboards",
        risk="dry_wood",
        solve_action="seal the cellar",
        fail_action="leave the cellar open",
        solve_text="sealed the cellar door with pine boards and quiet rope",
        fail_text="kept guessing until the water got bold and climbed through the boards",
        tags={"multirise", "water"},
    ),
    "bell": Mystery(
        id="bell",
        clue="a bell that rang with no hand to touch it",
        cause="a hidden string in the rafters",
        risk="frayed_rope",
        solve_action="find the string",
        fail_action="ignore the rafters",
        solve_text="found the string and tied it off before it could ring again",
        fail_text="never found the string, so the bell kept its wild old song",
        tags={"chuckle", "bell"},
    ),
    "lantern": Mystery(
        id="lantern",
        clue="a lantern that dimmed whenever someone lied",
        cause="soot in the glass and storm-salt in the wick",
        risk="storm_glass",
        solve_action="clean the lantern",
        fail_action="leave the glass dirty",
        solve_text="cleaned the lantern glass until it shone like a coin",
        fail_text="left the lantern dirty, and the dark had the last chuckle",
        tags={"chuckle", "light"},
    ),
}

TOOLS = {
    "boards": Tool("boards", "pine boards", helpful_for={"seal the cellar"}, risky_for={"leave the cellar open"}, tags={"wood"}),
    "string": Tool("string", "a spool of twine", helpful_for={"find the string"}, risky_for={"ignore the rafters"}, tags={"rope"}),
    "cloth": Tool("cloth", "a soft cloth", helpful_for={"clean the lantern"}, risky_for={"leave the glass dirty"}, tags={"clean"}),
}

HEROES = {
    "boy": ["Pip", "Ned", "Milo", "Otis"],
    "girl": ["Marnie", "Penny", "Lola", "June"],
}
HELPERS = {
    "boy": ["Hank", "Bert", "Toby"],
    "girl": ["Clara", "Wren", "Dottie"],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale mystery world with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["boy", "girl"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["boy", "girl"])
    ap.add_argument("--ending", choices=["bad"], default="bad")
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(HEROES[gender])


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.setting and args.mystery and args.tool:
        if (args.setting, args.mystery, args.tool) not in combos:
            raise StoryError("That combination does not make a workable mystery.")
    combos = [c for c in combos if (args.setting is None or c[0] == args.setting)
              and (args.mystery is None or c[1] == args.mystery)
              and (args.tool is None or c[2] == args.tool)]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    setting, mystery, tool = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["boy", "girl"])
    helper_gender = args.helper_gender or ("girl" if hero_gender == "boy" else "boy")
    hero = args.hero or _pick_name(rng, hero_gender)
    helper = args.helper or _pick_name(rng, helper_gender)
    return StoryParams(setting=setting, mystery=mystery, tool=tool, hero=hero, hero_gender=hero_gender,
                       helper=helper, helper_gender=helper_gender, ending="bad")


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    mystery = MYSTERIES[params.mystery]
    tool = TOOLS[params.tool]
    w = World(setting)
    hero = w.add(Entity(id=params.hero, kind="character", type=params.hero_gender, role="hero"))
    helper = w.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    crowd = w.add(Entity(id="crowd", kind="character", type="crowd", label="the crowd"))
    clue = w.add(Entity(id="clue", label=mystery.clue, tags=set(mystery.tags)))
    lantern = w.add(Entity(id="lantern", label=tool.label, tags=set(tool.tags)))
    w.facts.update(hero=hero, helper=helper, crowd=crowd, setting=setting, mystery=mystery, tool=tool, clue=clue)
    hero.memes["curiosity"] = 2.0
    helper.memes["care"] = 2.0
    lantern.meters["glow"] = 1.0
    w.say(f"In {setting.name}, there was a mystery as tall as a church steeple and twice as sly.")
    w.say(f"{setting.place_desc.capitalize()}. {setting.mystery_desc.capitalize()}.")
    w.say(f"{params.hero} and {params.helper} spotted {mystery.clue}, and {params.hero} let out a little chuckle.")
    w.para()
    w.say(f"They guessed and gossiped like hens in a thunderstorm, but the answer stayed hidden.")
    w.say(f"{params.helper} wanted to {mystery.solve_action}, yet {params.hero} chose to keep peeking instead.")
    w.say(f"{mystery.fail_text.capitalize()}.")
    propagate(w, narrate=False)
    w.para()
    w.say(f"By dusk, the trouble had grown long in the tooth.")
    w.say(f"{params.helper} reached for {tool.label}, but it was too late for a tidy fix.")
    w.say(f"The final {mystery.fail_action} let the danger spread, and the whole town had to back away.")
    w.say("So the mystery was never neatly solved; it rose higher and higher until nobody could hold it.")
    w.say("And that is how the tall tale ended, with the dark having the last chuckle.")
    w.facts["solved"] = False
    w.facts["outcome"] = "bad"
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a tall tale about {f['setting'].name} where a mystery refuses to stay small.",
        f"Tell a story that includes the word multirise and the word chuckle, and ends badly.",
        f"Write a child-facing mystery story where {f['hero'].id} and {f['helper'].id} look for a clue but miss the right fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    m = f["mystery"]
    return [
        QAItem(
            question="What mystery did the children try to solve?",
            answer=f"They tried to solve a mystery about {m.clue}. It stayed puzzling because they never found the right fix in time.",
        ),
        QAItem(
            question="Why did the story end badly?",
            answer=f"It ended badly because the children kept guessing instead of solving the problem early. By the time they tried to act, {m.fail_text} and the danger had already grown too big.",
        ),
        QAItem(
            question="What did the helper try to do?",
            answer=f"{f['helper'].id} tried to {m.solve_action}. That was the right idea, but the delay made the ending turn sour.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a mystery?", "A mystery is something puzzling that you do not understand right away. People look for clues to solve it."),
        QAItem("What does a chuckle sound like?", "A chuckle is a soft little laugh. It sounds warm and sometimes a little sneaky."),
        QAItem("What does multirise suggest?", "Multirise suggests something rising again and again, or climbing higher in more than one step. It makes the trouble feel too tall to ignore."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,M,T) :- setting(S), mystery(M), tool(T),
                solve_action(M,A), helpful_for(T,A),
                risk(M,R), risky_for(T,R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("solve_action", mid, m.solve_action))
        lines.append(asp.fact("risk", mid, m.risk))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for a in t.helpful_for:
            lines.append(asp.fact("helpful_for", tid, a))
        for r in t.risky_for:
            lines.append(asp.fact("risky_for", tid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        assert sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        rc = 1
    return rc


CURATED = [
    StoryParams(setting="river_town", mystery="rises", tool="boards", hero="Pip", hero_gender="boy", helper="Clara", helper_gender="girl", ending="bad"),
    StoryParams(setting="hill_fair", mystery="bell", tool="string", hero="Marnie", hero_gender="girl", helper="Toby", helper_gender="boy", ending="bad"),
    StoryParams(setting="orchard", mystery="lantern", tool="cloth", hero="Ned", hero_gender="boy", helper="Wren", helper_gender="girl", ending="bad"),
]


def explain_rejection() -> str:
    return "That combination does not make a workable mystery."


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.mystery not in MYSTERIES or params.tool not in TOOLS:
        raise StoryError("Invalid story parameters.")
    if (params.setting, params.mystery, params.tool) not in valid_combos():
        raise StoryError(explain_rejection())
    world = tell(params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
