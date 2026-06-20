#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/barbaric_teamwork_curiosity_lesson_learned_fairy_tale.py
=========================================================================================

A small fairy-tale storyworld about a curious child, a tiny castle problem, and
a teamwork solution that teaches a lesson learned. The seed word "barbaric" is
used in-story as a rough way to describe mean, clumsy behavior, but the ending
shows a kinder way.

This script is standalone and stdlib-only. It implements the shared Storyweavers
contract: StoryParams, registries, build_parser, resolve_params, generate, emit,
and main; it supports --all, -n, --seed, --trace, --qa, --json, --asp, --verify,
and --show-asp.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
LESSON_THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "woman"}
        male = {"boy", "father", "king", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    id: str
    place: str
    tone: str


@dataclass
class Quest:
    id: str
    goal: str
    dark: str
    clue: str
    risk: str


@dataclass
class Tool:
    id: str
    label: str
    use: str
    is_kind: bool = True


@dataclass
class Response:
    id: str
    power: int
    text: str
    fail: str


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_alarm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("box").meters["open"] >= THRESHOLD and world.get("room").meters["messy"] >= THRESHOLD:
        sig = ("alarm",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("room").memes["worry"] += 1
            world.get("hero").memes["worry"] += 1
            world.get("friend").memes["worry"] += 1
            out.append("__alarm__")
    return out


def _r_lesson(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").memes["helped"] >= THRESHOLD and world.get("friend").memes["helped"] >= THRESHOLD:
        sig = ("lesson",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("hero").memes["lesson"] += 1
            world.get("friend").memes["lesson"] += 1
            out.append("__lesson__")
    return out


CAUSAL_RULES = [Rule("alarm", _r_alarm), Rule("lesson", _r_lesson)]


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


def predict(world: World, quest: Quest) -> dict:
    sim = world.copy()
    _open_box(sim, narrate=False)
    return {"messy": sim.get("room").meters["messy"] >= THRESHOLD}


def _open_box(world: World, narrate: bool = True) -> None:
    world.get("box").meters["open"] += 1
    world.get("room").meters["messy"] += 1
    world.get("hero").memes["curious"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, hero: Entity, friend: Entity, elder: Entity, setting: Setting, quest: Quest) -> None:
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.say(
        f"Once upon a time, in {setting.place}, {hero.id} and {friend.id} found a little gate beneath a rose bush."
    )
    world.say(
        f"Beyond it stood {quest.dark}, and a wooden box with a sign that said '{quest.clue}'."
    )


def wonder(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["curious"] += 1
    world.say(
        f"{hero.id} tilted {hero.pronoun('possessive')} head. \"What is inside the box?\" {hero.pronoun()} whispered."
    )
    world.say(
        f"Everybody warned that the place looked {quest.risk}, but {hero.id}'s curiosity sparkled like a lantern."
    )


def rude_act(world: World, elder: Entity, quest: Quest) -> None:
    elder.memes["stern"] += 1
    world.say(
        f"Then a grumpy guard called the idea barbaric and tried to slam the box shut with a loud bang."
    )


def teamwork(world: World, hero: Entity, friend: Entity, elder: Entity, quest: Quest) -> None:
    hero.memes["helped"] += 1
    friend.memes["helped"] += 1
    world.say(
        f"But {hero.id} and {friend.id} worked together. One held the latch, and the other steadied the lid so it would not break."
    )
    world.say(
        f"{elder.id} saw their kindness and helped them move the box carefully, one small step at a time."
    )


def resolve(world: World, hero: Entity, friend: Entity, quest: Quest, response: Response) -> None:
    world.get("box").meters["open"] = 0.0
    world.get("room").meters["messy"] = 0.0
    hero.memes["calm"] += 1
    friend.memes["calm"] += 1
    world.say(
        f"Together they {response.text}, and the tiny mess was fixed without a single thing being broken."
    )
    world.say(
        f"In the box was only a silver key, meant to open {quest.goal} for the spring feast."
    )


def lesson(world: World, hero: Entity, friend: Entity, elder: Entity, quest: Quest) -> None:
    hero.memes["lesson"] += 1
    friend.memes["lesson"] += 1
    world.say("For a moment, everyone was quiet.")
    world.say(
        f"Then {elder.id} smiled and said, \"Curiosity is good, but teamwork and patience are better than being barbaric.\""
    )
    world.say(
        f"{hero.id} and {friend.id} promised to ask kindly next time, and the castle felt bright again."
    )


SETTINGS = {
    "castle": Setting("castle", "an old castle at the edge of the woods", "fairy-tale"),
    "garden": Setting("garden", "a moonlit garden behind the castle", "fairy-tale"),
}

QUESTS = {
    "key": Quest("key", "the big garden gate", "a locked wooden chest", "Do not pry", "fragile"),
    "bell": Quest("bell", "the tower door", "a painted box under the roses", "Be gentle", "mysterious"),
}

TOOLS = {
    "hands": Tool("hands", "small hands", "lift the lid carefully"),
    "rope": Tool("rope", "a soft ribbon rope", "steady the box together"),
    "gloves": Tool("gloves", "soft garden gloves", "protect their fingers"),
}

RESPONSES = {
    "careful_lift": Response("careful_lift", 3, "lifted the lid together and set it down gently", "pulled too hard and made a bigger mess"),
    "steady_hold": Response("steady_hold", 3, "held the box steady and cleaned up the tiny spill", "were too rough and could not fix it"),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Ivy", "Nora", "Elena"]
BOY_NAMES = ["Robin", "Otis", "Bram", "Milo", "Theo", "Galen"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for q in QUESTS:
            for r in RESPONSES:
                combos.append((s, q, r))
    return combos


@dataclass
class StoryParams:
    setting: str
    quest: str
    response: str
    hero: str
    hero_gender: str
    friend: str
    friend_gender: str
    elder: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about curiosity, teamwork, and a lesson learned.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--friend")
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
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
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.setting and args.quest and args.response and (args.response not in RESPONSES):
        raise StoryError("Unknown response.")
    setting = args.setting or rng.choice(list(SETTINGS))
    quest = args.quest or rng.choice(list(QUESTS))
    response = args.response or rng.choice(list(RESPONSES))
    hero_gender = args.hero_gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or ("boy" if hero_gender == "girl" and rng.random() < 0.5 else "girl")
    hero = args.hero or _pick_name(rng, hero_gender)
    friend = args.friend or _pick_name(rng, friend_gender)
    elder = args.elder or ("Queen Maren" if rng.random() < 0.5 else "Old Rowan")
    return StoryParams(setting, quest, response, hero, hero_gender, friend, friend_gender, elder)


def tell(params: StoryParams) -> World:
    w = World()
    hero = w.add(Entity("hero", kind="character", type=params.hero_gender, label=params.hero, role="curious"))
    friend = w.add(Entity("friend", kind="character", type=params.friend_gender, label=params.friend, role="helper"))
    elder = w.add(Entity("elder", kind="character", type="woman" if "Queen" in params.elder else "man", label=params.elder, role="guide"))
    room = w.add(Entity("room", type="room", label="the castle room"))
    box = w.add(Entity("box", type="thing", label="the little box"))
    setting = SETTINGS[params.setting]
    quest = QUESTS[params.quest]
    response = RESPONSES[params.response]

    setup(w, hero, friend, elder, setting, quest)
    w.para()
    wonder(w, hero, quest)
    predict(w, quest)
    rude_act(w, elder, quest)
    _open_box(w, narrate=True)
    w.say(f"The room grew messy, and everyone gasped.")
    w.para()
    teamwork(w, hero, friend, elder, quest)
    resolve(w, hero, friend, quest, response)
    lesson(w, hero, friend, elder, quest)

    w.facts.update(hero=hero, friend=friend, elder=elder, setting=setting, quest=quest, response=response)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy-tale story for a child that includes the word "barbaric" and shows curiosity, teamwork, and a lesson learned.',
        f"Tell a gentle castle story where {f['hero'].id} and {f['friend'].id} work together to fix a small problem after a curious mistake.",
        f'Write a short fairy tale where a grown-up warns that rough behavior is barbaric, but kindness and teamwork solve the problem.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.facts["hero"]
    friend = world.facts["friend"]
    elder = world.facts["elder"]
    return [
        QAItem(
            question="Why did the little problem happen?",
            answer=f"It happened because {hero.id} was curious and opened the box. That curiosity made the room messy, so everyone had to slow down and work together."
        ),
        QAItem(
            question="How did the children solve it?",
            answer=f"{hero.id} and {friend.id} used teamwork. They held the box steady, fixed the mess carefully, and listened when {elder.id} reminded them to be gentle."
        ),
        QAItem(
            question="What lesson did they learn?",
            answer="They learned that curiosity is good, but they should be gentle and ask for help instead of acting barbaric. Working together is kinder and smarter."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What does teamwork mean?", "Teamwork means people help each other and do a job together."),
        QAItem("What is curiosity?", "Curiosity is the wish to learn, look, and ask questions about new things."),
        QAItem("Why should people be gentle with old things?", "Old things can be fragile, so rough hands may break them."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== Prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    parts.append("== Story QA ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== World QA ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:6} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,Q,R) :- setting(S), quest(Q), response(R).
"""
def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for q in QUESTS:
        lines.append(asp.fact("quest", q))
    for r in RESPONSES:
        lines.append(asp.fact("response", r))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH in valid_combos()")
    try:
        s = generate(resolve_params(argparse.Namespace(setting=None, quest=None, response=None, hero=None, hero_gender=None, friend=None, friend_gender=None, elder=None, seed=None), random.Random(7)))
        _ = s.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    print("OK: ASP parity passed." if py == cl else "ASP parity failed.")
    return 0 if ok else 1


CURATED = [
    StoryParams("castle", "key", "careful_lift", "Lina", "girl", "Robin", "boy", "Queen Maren"),
    StoryParams("garden", "bell", "steady_hold", "Milo", "boy", "Ivy", "girl", "Old Rowan"),
]


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
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations.")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i + 1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
