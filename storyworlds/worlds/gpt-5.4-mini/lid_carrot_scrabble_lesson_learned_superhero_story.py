#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lid_carrot_scrabble_lesson_learned_superhero_story.py
=====================================================================================

A standalone storyworld for a tiny superhero-style lesson tale about a child,
a secret game, a stubborn lid, and a carrot that should not be used as a toy.
The world is small on purpose: one child wants to play with a scrabble set in a
superhero hideout, tries to open a snack container by force, and learns a kinder,
safer way to solve the problem after a grown-up helps.

The storyworld contract requires:
- a live world model with meters and memes
- a Python reasonableness gate plus an inline ASP twin
- story-driven QA sets from world state
- support for default run, -n, --all, --seed, --trace, --qa, --json,
  --asp, --verify, and --show-asp
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
    owner: str = ""
    caregiver: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

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
    label: str
    superhero_name: str
    hideout_name: str
    hero_goal: str
    backdrop: str


@dataclass
class ObjectThing:
    id: str
    label: str
    phrase: str
    kind: str
    can_open: bool = False
    can_snap: bool = False
    edible: bool = False
    safe_tool: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_sticky_lid(world: World) -> list[str]:
    out: list[str] = []
    hero = world.entities.get("hero")
    box = world.entities.get("snack_box")
    if not hero or not box:
        return out
    if hero.meters["forcing"] < THRESHOLD:
        return out
    sig = ("sticky", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    box.meters["scratched"] += 1
    hero.memes["frustration"] += 1
    out.append("__scrape__")
    return out


def _r_messy_counter(world: World) -> list[str]:
    out: list[str] = []
    box = world.entities.get("snack_box")
    if not box:
        return out
    if box.meters["scratched"] < THRESHOLD:
        return out
    sig = ("messy_counter", box.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    box.meters["open_risk"] += 1
    out.append("__risk__")
    return out


def _r_conflict(world: World) -> list[str]:
    hero = world.entities.get("hero")
    parent = world.entities.get("mentor")
    if not hero or not parent:
        return []
    if hero.memes["stubborn"] < THRESHOLD or parent.memes["concern"] < THRESHOLD:
        return []
    sig = ("conflict", hero.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["conflict"] += 1
    parent.memes["conflict"] += 1
    return ["__conflict__"]


CAUSAL_RULES = [
    Rule("sticky_lid", "physical", _r_sticky_lid),
    Rule("messy_counter", "physical", _r_messy_counter),
    Rule("conflict", "social", _r_conflict),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(setting: Setting, item: ObjectThing, response: Response) -> bool:
    return item.can_open and response.sense >= 2 and "carrot" in item.tags


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict(world: World, target_id: str) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["forcing"] += 1
    target = sim.get(target_id)
    target.meters["scratched"] += 1
    propagate(sim, narrate=False)
    return {
        "scratched": target.meters["scratched"] >= THRESHOLD,
        "conflict": sim.get("hero").memes["conflict"] >= THRESHOLD,
    }


def move_open(world: World, hero: Entity, item: Entity, setting: Setting) -> None:
    world.say(
        f"In the bright base under the moon, {hero.id} wore a red cape and watched "
        f"the {setting.backdrop}. {setting.superhero_name} had promised that the team "
        f"would finish one last rescue mission."
    )
    world.say(
        f"Near the shiny table sat a snack box with a {item.label}. Beside it was "
        f"the scrabble board, waiting for a word game after the mission."
    )


def want_snack(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["want"] += 1
    world.say(
        f'{hero.id} pointed at the box. "I can open it fast!" {hero.id} said. '
        f"\"If I get the {item.label} off, we can grab a carrot snack before the game.\""
    )


def warn(world: World, mentor: Entity, hero: Entity, item: Entity) -> None:
    hero.memes["stubborn"] += 1
    mentor.memes["concern"] += 1
    pred = predict(world, "snack_box")
    world.facts["predicted_scratched"] = pred["scratched"]
    world.say(
        f'{mentor.id} shook {mentor.pronoun("possessive")} head. "{hero.id}, do not '
        f"scrape the {item.label} with your gloves. It can crack the lid, and then "
        f"the snack box might spill everywhere."'
    )
    if pred["scratched"]:
        world.say(
            f'"Let me show you a safer way," {mentor.id} said, already reaching for '
            f"the latch."
        )


def defy(world: World, hero: Entity, item: Entity) -> None:
    hero.memes["stubborn"] += 1
    world.say(
        f'{hero.id} scrabbled at the lid anyway. The gloves slipped, and the {item.label} '
        f"gave a sharp little squeak."
    )


def rescue(world: World, mentor: Entity, hero: Entity, item: Entity) -> None:
    box = world.get("snack_box")
    box.meters["open"] = 1
    world.say(
        f"{mentor.id} came over calmly. In one quick move, {mentor.pronoun()} pressed "
        f"the latch and lifted the lid the gentle way."
    )
    world.say(
        f"The box opened cleanly. Inside was the carrot, still neat and bright, and "
        f"the scrabble tiles stayed on the table where they belonged."
    )


def lesson(world: World, mentor: Entity, hero: Entity, item: Entity) -> None:
    hero.memes["lesson"] += 1
    hero.memes["joy"] += 1
    mentor.memes["joy"] += 1
    world.say("For a moment, the room was quiet.")
    world.say(
        f"Then {mentor.id} knelt beside {hero.id} and smiled. \"A hero learns twice: "
        f"first from a mission, and then from a mistake,\" {mentor.id} said. "
        f"\"The lid is for opening, not scraping.\""
    )
    world.say(
        f'{hero.id} nodded. "I get it," {hero.id} said. "Next time I will ask first."'
    )


def finish(world: World, hero: Entity, setting: Setting) -> None:
    world.say(
        f"After that, {hero.id} sat down with the scrabble board, the carrot snack, "
        f"and {setting.superhero_name}'s map of the hideout. This time the hero used "
        f"words, not force, and the mission ended with a grin."
    )


def tell(setting: Setting, item: ObjectThing, response: Response,
         hero_name: str = "Mila", hero_gender: str = "girl",
         mentor_name: str = "Captain Bright", mentor_gender: str = "woman") -> World:
    world = World()
    hero = world.add(Entity("hero", kind="character", type=hero_gender, role="hero"))
    hero.id = hero_name
    mentor = world.add(Entity("mentor", kind="character", type=mentor_gender, role="mentor"))
    mentor.id = mentor_name
    snack_box = world.add(Entity("snack_box", type="box", label=item.label, role="container"))
    snack_box.meters["closed"] = 1
    world.facts["setting"] = setting
    world.facts["item"] = item
    world.facts["response"] = response
    world.facts["hero"] = hero
    world.facts["mentor"] = mentor

    move_open(world, hero, snack_box, setting)
    world.para()
    want_snack(world, hero, snack_box)
    warn(world, mentor, hero, snack_box)
    defy(world, hero, snack_box)
    world.para()
    rescue(world, mentor, hero, snack_box)
    lesson(world, mentor, hero, snack_box)
    finish(world, hero, setting)

    world.facts["outcome"] = "lesson_learned"
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "tower": Setting("tower", "the moon tower", "Captain Bright", "sky hideout", "finish the mission", "city lights"),
    "garage": Setting("garage", "the secret garage", "Captain Bright", "tool hideout", "find the safe snack", "workbench"),
    "rooftop": Setting("rooftop", "the rooftop base", "Captain Bright", "cloud hideout", "solve the puzzle", "night skyline"),
}

ITEMS = {
    "carrot": ObjectThing("carrot", "carrot", "a crisp carrot", "snack", edible=True, tags={"carrot", "snack"}),
    "lid": ObjectThing("lid", "lid", "a stubborn lid", "container_part", can_open=True, tags={"lid"}),
    "scrabble": ObjectThing("scrabble", "scrabble board", "a scrabble board", "game", safe_tool=True, tags={"scrabble", "game"}),
}

RESPONSES = {
    "gentle": Response("gentle", 3, 4, "opened the lid with a gentle push", "could not open the lid in time", "opened the lid with a gentle push"),
    "latch": Response("latch", 3, 5, "used the latch and lifted the lid carefully", "tried the latch, but the lid was stuck", "used the latch and lifted the lid carefully"),
    "ask": Response("ask", 2, 3, "asked for help and opened it the safe way", "waited too long and the snack box stayed shut", "asked for help and opened it the safe way"),
}

HERO_NAMES = ["Mila", "Zoe", "Nia", "Ava", "Lena", "June", "Theo", "Max", "Eli"]
MENTOR_NAMES = ["Captain Bright", "Star Guide", "Hero Mom", "Hero Dad"]
TRAITS = ["brave", "curious", "thoughtful", "stubborn", "careful"]


@dataclass
class StoryParams:
    setting: str
    item: str
    response: str
    hero_name: str
    hero_gender: str
    mentor_name: str
    mentor_gender: str
    trait: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for i in ITEMS:
            for r in RESPONSES:
                if reasonableness_gate(SETTINGS[s], ITEMS[i], RESPONSES[r]):
                    combos.append((s, i, r))
    return combos


KNOWLEDGE = {
    "lid": [("What is a lid?", "A lid is a top that closes a box or jar. It helps keep things inside until someone opens it.")],
    "carrot": [("What is a carrot?", "A carrot is a crunchy orange vegetable. People often eat it as a snack.")],
    "scrabble": [("What is Scrabble?", "Scrabble is a word game. Players make words out of letter tiles.")],
    "lesson": [("What does it mean to learn a lesson?", "It means you understand something better after what happened, and you do it a safer or kinder way next time.")],
    "hero": [("What is a superhero story?", "A superhero story often has brave helpers, a problem to solve, and a good choice at the end.")],
}


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.can_open:
            lines.append(asp.fact("can_open", iid))
        if item.edible:
            lines.append(asp.fact("edible", iid))
        if item.safe_tool:
            lines.append(asp.fact("safe_tool", iid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, I, R) :- setting(S), item(I), response(R), can_open(I), sense(R, S1), sense_min(M), S1 >= M.
"""


def asp_program(extra: str, show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid_combos disagree.")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, item=None, response=None, hero_name=None, hero_gender=None, mentor_name=None, mentor_gender=None, trait=None), random.Random(7)))
        _ = sample.story
        print("OK: normal generation smoke test passed.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero lesson storyworld with lid, carrot, and scrabble.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy", "woman", "man"])
    ap.add_argument("--mentor-name")
    ap.add_argument("--mentor-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.item is None or c[1] == args.item)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, response = rng.choice(sorted(combos))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    hero_name = args.hero_name or rng.choice(HERO_NAMES)
    mentor_gender = args.mentor_gender or rng.choice(["woman", "man"])
    mentor_name = args.mentor_name or rng.choice(MENTOR_NAMES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(setting, item, response, hero_name, hero_gender, mentor_name, mentor_gender, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a 3-to-5-year-old that includes the words "lid", "carrot", and "scrabble".',
        f"Tell a lesson-learned story where {f['hero'].id} wants a carrot snack in a superhero hideout, but first has to handle a stubborn lid the safe way.",
        f"Write a short heroic story where a child learns not to scrape at a lid and instead asks a grown-up, ending with scrabble tiles on the table.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    hero = f["hero"]
    mentor = f["mentor"]
    item = f["item"]
    qa = [
        ("Who is the story about?",
         f"It is about {hero.id} and {mentor.id}, who work together in a superhero hideout. The child starts the problem and the grown-up helps with the fix."),
        ("What did the child want?",
         f"{hero.id} wanted to open the snack box and get the carrot. {hero.pronoun('subject').capitalize()} also wanted to finish the mission and play scrabble afterward."),
        ("How was the problem solved?",
         f"{mentor.id} used the safe way to open the lid, and the box opened without breaking. That let the carrot stay neat and kept the scrabble board safe.")
    ]
    if f.get("resolved"):
        qa.append((
            "What lesson did the child learn?",
            f"{hero.id} learned to ask for help and use a gentle way with the lid. That was the best hero choice because it kept the snack and the game in good shape."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["item"].tags) | {"hero", "lesson"}
    out = []
    for key, items in KNOWLEDGE.items():
        if key in tags:
            out.extend(items)
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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], ITEMS[params.item], RESPONSES[params.response],
                 params.hero_name, params.hero_gender, params.mentor_name, params.mentor_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
    StoryParams("tower", "carrot", "latch", "Mila", "girl", "Captain Bright", "woman", "brave"),
    StoryParams("garage", "carrot", "gentle", "Theo", "boy", "Hero Dad", "man", "curious"),
    StoryParams("rooftop", "carrot", "ask", "Nia", "girl", "Star Guide", "woman", "thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for s, i, r in asp_valid_combos():
            print(f"  {s:10} {i:10} {r}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
