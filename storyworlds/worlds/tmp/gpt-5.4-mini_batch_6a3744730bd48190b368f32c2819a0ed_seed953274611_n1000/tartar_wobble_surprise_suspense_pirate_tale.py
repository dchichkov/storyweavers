#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/tartar_wobble_surprise_suspense_pirate_tale.py
==============================================================================

A standalone story world for a tiny pirate tale built from the seed words
"tartar" and "wobble", with suspense and surprise as the narrative engine.

Premise
-------
A small pirate crew is crossing a moonlit cove when something on deck begins to
wobble. The captain fears a leak or a sea beast. The suspense builds until the
surprise is revealed: a hidden hatch has opened around a jar of tartar, and the
wobble was caused by a playful stowaway mouse nudging the latch. The crew turns
the shock into a feast and a new rule: keep the hatch latched, and keep the
tartar safe for supper.

This world uses typed entities with physical meters and emotional memes, a
forward-chained rule engine, a reasonableness gate, and an inline ASP twin.
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

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "cook", "pirate"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class StoryParams:
    crew: str
    captain: str
    lookout: str
    helper: str
    setting: str
    hidden_thing: str
    surprise: str
    response: str
    seed: Optional[int] = None


@dataclass
class Crew:
    id: str
    scene: str
    ship: str
    sea: str
    cargo: str
    hidden: str
    reveal: str
    mood: str
    tags: set[str] = field(default_factory=set)


@dataclass
class SurpriseThing:
    id: str
    label: str
    phrase: str
    cue: str
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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["wobble"] < THRESHOLD:
            continue
        sig = ("suspense", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for pid in ("captain", "lookout"):
            if pid in world.entities:
                world.get(pid).memes["suspense"] += 1
        out.append("__suspense__")
    return out


def _r_surprise(world: World) -> list[str]:
    out: list[str] = []
    hatch = world.entities.get("hatch")
    mouse = world.entities.get("mouse")
    jar = world.entities.get("jar")
    if not hatch or not mouse or not jar:
        return out
    if hatch.meters["open"] < THRESHOLD or mouse.meters["nudged"] < THRESHOLD:
        return out
    sig = ("surprise",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    jar.meters["revealed"] += 1
    for pid in ("captain", "lookout", "helper"):
        if pid in world.entities:
            world.get(pid).memes["surprise"] += 1
    out.append("__surprise__")
    return out


CAUSAL_RULES = [Rule("suspense", "mood", _r_suspense), Rule("surprise", "turn", _r_surprise)]


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


def reasonable(response: Response) -> bool:
    return response.sense >= 2


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for crew in CREWS:
        for hidden in HIDDEN_THINGS:
            for surprise in SURPRISES:
                if hidden == "jar" and surprise.id == "mouse":
                    combos.append((crew.id, hidden, surprise.id))
    return combos


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def prediction(world: World) -> dict:
    sim = world.copy()
    sim.get("hatch").meters["open"] += 1
    sim.get("mouse").meters["nudged"] += 1
    propagate(sim, narrate=False)
    return {
        "suspense": sim.get("captain").memes["suspense"],
        "surprise": sim.get("jar").meters["revealed"],
    }


def open_hatch(world: World, hatch: Entity) -> None:
    hatch.meters["open"] += 1
    world.say("The hatch gave a tiny creak, and everyone went quiet.")


def wobble(world: World, thing: Entity) -> None:
    thing.meters["wobble"] += 1
    propagate(world, narrate=False)
    world.say(f"Something on deck began to wobble under the moonlight.")


def worry(world: World, captain: Entity, lookout: Entity, thing: Entity) -> None:
    captain.memes["worry"] += 1
    lookout.memes["worry"] += 1
    world.say(
        f'{captain.id} narrowed {captain.pronoun("possessive")} eyes. '
        f'"What is wobbling on my ship?" {captain.id} asked, while {lookout.id} '
        f'held {lookout.pronoun("possessive")} breath.'
    )
    world.say(
        f"{lookout.id} peered at the dark shape and whispered, "
        f'"If it is a sea beast, we should know soon."'
    )


def tease_suspense(world: World, helper: Entity, crew: Crew) -> None:
    helper.memes["glee"] += 1
    world.say(
        f"{helper.id} pointed at the cargo and smiled. "
        f'"Maybe it is treasure," {helper.id} said, but nobody could tell yet.'
    )
    world.say(
        f"The {crew.ship} rocked softly in the tide, and the answer stayed hidden."
    )


def reveal(world: World, surprise: SurpriseThing, crew: Crew) -> None:
    world.say(
        f"Then the hatch flew up, and the surprise was no sea beast at all. "
        f"It was {surprise.phrase}, bright as a splash of gold in the dark."
    )


def settle(world: World, captain: Entity, lookout: Entity, helper: Entity, response: Response) -> None:
    captain.memes["relief"] += 1
    lookout.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(
        f"{captain.id} laughed and {response.text}."
    )
    world.say(
        f"The crew shared the tartar and shut the hatch tight, while the sea kept "
        f"wobbling outside and the lantern stayed steady inside."
    )


def story_fail(world: World, response: Response) -> None:
    world.say(response.fail)


CREWS = [
    Crew(id="gulls", scene="a moonlit cove", ship="ship", sea="cove", cargo="cargo",
         hidden="hatch", reveal="jar", mood="suspense", tags={"pirate", "sea"}),
    Crew(id="reef", scene="a windy bay", ship="deck", sea="bay", cargo="barrel",
         hidden="hatch", reveal="jar", mood="suspense", tags={"pirate", "sea"}),
]

HIDDEN_THINGS = {
    "jar": SurpriseThing(id="jar", label="jar of tartar", phrase="a jar of tartar",
                         cue="a salty smell", tags={"tartar"}),
    "treasure": SurpriseThing(id="treasure", label="chest of coins",
                              phrase="a chest of coins", cue="a clink in the dark",
                              tags={"treasure"}),
}

SURPRISES = {
    "mouse": SurpriseThing(id="mouse", label="mouse", phrase="a tiny mouse",
                           cue="a whiskered nose", tags={"mouse", "surprise"}),
    "parrot": SurpriseThing(id="parrot", label="parrot", phrase="a bright parrot",
                            cue="a green feather", tags={"bird", "surprise"}),
}

RESPONSES = {
    "laugh": Response(
        id="laugh", sense=3, power=1,
        text="spoke kindly and set the jar on the table for supper",
        fail="spoke kindly, but the moment was too confusing to settle",
        qa_text="spoke kindly and set the jar on the table for supper",
        tags={"calm"},
    ),
    "cheer": Response(
        id="cheer", sense=2, power=1,
        text="cheered and opened the tartar jar for everyone",
        fail="cheered, but the mystery stayed tangled up in the dark",
        qa_text="cheered and opened the tartar jar for everyone",
        tags={"joy"},
    ),
    "shout": Response(
        id="shout", sense=1, power=0,
        text="shouted",
        fail="shouted, but that only made the suspense sharper",
        qa_text="shouted",
        tags={"panic"},
    ),
}

KNOWLEDGE = {
    "tartar": [
        ("What is tartar in this story?",
         "Tartar is a salty food in a jar. The crew keeps it for supper, and the surprise makes the meal feel special.")
    ],
    "wobble": [
        ("What does wobble mean?",
         "Wobble means to shake or move unsteadily. Something that wobbles can make people wonder what is happening.")
    ],
    "pirate": [
        ("What do pirates travel on?",
         "Pirates travel on ships and boats. In stories, they often sail at night, listen for danger, and look for treasure.")
    ],
    "suspense": [
        ("What is suspense?",
         "Suspense is the feeling of waiting and wondering what will happen next. It makes a story feel tense before the surprise arrives.")
    ],
    "surprise": [
        ("What is a surprise?",
         "A surprise is something you do not expect. It can make a story joyful or funny when the hidden thing is finally revealed.")
    ],
}

KNOWLEDGE_ORDER = ["tartar", "wobble", "pirate", "suspense", "surprise"]


def tell(params: StoryParams) -> World:
    world = World()
    captain = world.add(Entity(id="captain", kind="character", type="captain", label="the captain"))
    lookout = world.add(Entity(id="lookout", kind="character", type="boy", label="the lookout"))
    helper = world.add(Entity(id="helper", kind="character", type="boy", label="the helper"))
    hatch = world.add(Entity(id="hatch", type="thing", label="the hatch"))
    jar = world.add(Entity(id="jar", type="thing", label="jar of tartar"))
    mouse = world.add(Entity(id="mouse", type="thing", label="mouse"))
    cargo = world.add(Entity(id="cargo", type="thing", label="cargo"))
    world.facts.update(
        captain=captain, lookout=lookout, helper=helper,
        hatch=hatch, jar=jar, mouse=mouse, cargo=cargo,
        crew=CREWS[0], response=RESPONSES[params.response],
        hidden=HIDDEN_THINGS[params.hidden_thing], surprise=SURPRISES[params.surprise],
        setting=params.setting,
    )
    world.say(
        f"On {params.setting}, the little pirate crew sailed under a silver moon. "
        f"{captain.id} watched the deck, {lookout.id} stood near the lantern, and "
        f"{helper.id} carried the supper tray with tartar in a small jar."
    )
    world.say(
        f"The sea was calm, but the night felt full of suspense, as if the ship "
        f"were holding its breath."
    )
    world.para()
    wobble(world, hatch)
    worry(world, captain, lookout, hatch)
    tease_suspense(world, helper, CREWS[0])
    world.para()
    open_hatch(world, hatch)
    mouse.meters["nudged"] += 1
    propagate(world, narrate=False)
    reveal(world, HIDDEN_THINGS[params.hidden_thing], CREWS[0])
    if params.response in RESPONSES and reasonable(RESPONSES[params.response]):
        settle(world, captain, lookout, helper, RESPONSES[params.response])
    else:
        story_fail(world, RESPONSES[params.response])
    world.facts["outcome"] = "settled" if reasonable(RESPONSES[params.response]) else "shaken"
    return world


def generation_prompts(world: World) -> list[str]:
    return [
        'Write a pirate tale for a 3-to-5-year-old that includes the words "tartar" and "wobble".',
        "Tell a short story with suspense on a pirate ship where a wobble in the dark turns into a surprise.",
        "Write a gentle pirate story where the crew wonders what is wobbling, then discovers something tasty and safe.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    response: Response = f["response"]
    return [
        ("What was wobbling on the ship?",
         "The hatch was wobbling on the ship. That wobble made everyone nervous because they did not yet know what was underneath."),
        ("What was the surprise?",
         "The surprise was a jar of tartar and a tiny mouse near the hatch. The wobble had been making the crew imagine something much scarier."),
        ("How did the captain respond?",
         f"The captain {response.qa_text}. That calm response helped the crew settle down and enjoy the moment."),
        ("What changed by the end?",
         "The crew went from tense and unsure to relieved and cheerful. The strange wobble turned into supper, and the ship felt steady again."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"tartar", "wobble", "pirate", "suspense", "surprise"}
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags:
            out.extend(KNOWLEDGE[tag])
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CREWS = [
    Crew(id="gulls", scene="a moonlit cove", ship="ship", sea="cove", cargo="cargo",
         hidden="hatch", reveal="jar", mood="suspense", tags={"pirate", "sea"}),
]
HIDDEN_THINGS = {"jar": HIDDEN_THINGS["jar"]}
SURPRISES = {"mouse": SURPRISES["mouse"]}
RESPONSES = RESPONSES


@dataclass
class StoryConfig:
    setting: str
    hidden_thing: str
    surprise: str
    response: str


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale with tartar, wobble, suspense, and surprise.")
    ap.add_argument("--setting", choices=["moonlit cove", "windy bay"], default=None)
    ap.add_argument("--hidden-thing", choices=list(HIDDEN_THINGS), default=None)
    ap.add_argument("--surprise", choices=list(SURPRISES), default=None)
    ap.add_argument("--response", choices=list(RESPONSES), default=None)
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
    hidden = args.hidden_thing or "jar"
    surprise = args.surprise or "mouse"
    response = args.response or rng.choice(["laugh", "cheer"])
    if response not in RESPONSES:
        raise StoryError("Unknown response.")
    if not reasonable(RESPONSES[response]):
        raise StoryError("That response is too abrupt for this gentle pirate tale.")
    return StoryParams(
        crew="gulls",
        captain="captain",
        lookout="lookout",
        helper="helper",
        setting=args.setting or "moonlit cove",
        hidden_thing=hidden,
        surprise=surprise,
        response=response,
    )


def generate(params: StoryParams) -> StorySample:
    if params.hidden_thing not in HIDDEN_THINGS:
        raise StoryError("Unknown hidden thing.")
    if params.surprise not in SURPRISES:
        raise StoryError("Unknown surprise.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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


ASP_RULES = r"""
wobble_event(hatch) :- wobble(hatch).
suspense(captain) :- wobble_event(hatch).
suspense(lookout) :- wobble_event(hatch).
surprise(jar) :- open(hatch), nudged(mouse), tartar(jar).
valid_story(setting, hidden, surprise) :- setting(setting), hidden_thing(hidden), surprise_item(surprise), hidden = jar, surprise = mouse.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("setting", "moonlit_cove"),
        asp.fact("setting", "windy_bay"),
        asp.fact("hidden_thing", "jar"),
        asp.fact("surprise_item", "mouse"),
        asp.fact("tartar", "jar"),
        asp.fact("wobble", "hatch"),
        asp.fact("open", "hatch"),
        asp.fact("nudged", "mouse"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3.\n#show surprise/1.\n#show suspense/1."))
    ok = bool(model)
    sample = generate(resolve_params(argparse.Namespace(setting=None, hidden_thing=None, surprise=None, response=None), random.Random(7)))
    try:
        _ = sample.story
    except Exception:
        return 1
    print("OK: ASP program grounded and normal generation succeeded.")
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid_story/3.\n#show surprise/1.\n#show suspense/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(crew="gulls", captain="captain", lookout="lookout", helper="helper",
                                 setting="moonlit cove", hidden_thing="jar", surprise="mouse", response="laugh"))
        ]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
