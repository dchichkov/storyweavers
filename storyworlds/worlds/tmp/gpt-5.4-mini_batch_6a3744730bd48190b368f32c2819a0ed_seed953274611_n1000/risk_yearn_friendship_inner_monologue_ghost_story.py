#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/risk_yearn_friendship_inner_monologue_ghost_story.py
====================================================================================

A small storyworld built from the seed words ``risk`` and ``yearn`` with the
instruments of friendship and inner monologue, in a ghost-story style.

Premise
-------
A child and a friend enter a quiet old place at dusk. One of them yearns to
prove the place is not scary. The other senses a risk, listens inwardly, and
speaks up at the right time. The "ghost" turns out to be a harmless presence
with a small need, and the friendship changes from teasing bravado into careful
kindness.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- a forward-chained world model
- a Python reasonableness gate plus inline ASP twin
- three Q&A sets grounded in state, not by parsing rendered English
- CLI support for default run, -n, --all, --seed, --trace, --qa, --json,
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SENSE_MIN = 2
BRAVERY_INIT = 5.0
YEARN_INIT = 4.0


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
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Place:
    id: str
    label: str
    darkness: str
    yearned_for: str
    risk_kind: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Ghost:
    id: str
    label: str
    sound: str
    need: str
    harmless: bool = True
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


@dataclass
class StoryParams:
    place: str
    ghost: str
    response: str
    child: str
    child_gender: str
    friend: str
    friend_gender: str
    risk_level: int = 0
    friendship: int = 6
    seed: Optional[int] = None


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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_dread(world: World) -> list[str]:
    out: list[str] = []
    for e in world.entities.values():
        if e.meters["dread"] < THRESHOLD:
            continue
        sig = ("dread", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for c in world.entities.values():
            if c.kind == "character":
                c.memes["unease"] += 1
        out.append("__dread__")
    return out


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    if "ghost" not in world.entities or "child" not in world.entities:
        return out
    g = world.get("ghost")
    c = world.get("child")
    if g.meters["seen"] < THRESHOLD or c.memes["kindness"] < THRESHOLD:
        return out
    sig = ("soften",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    g.meters["lonely"] = max(0.0, g.meters["lonely"] - 1.0)
    c.memes["brave"] += 1
    out.append("__soften__")
    return out


CAUSAL_RULES = [
    Rule("dread", "mood", _r_dread),
    Rule("soften", "mood", _r_soften),
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


def reasonableness(place: Place, ghost: Ghost, response: Response) -> bool:
    return ghost.harmless and response.sense >= SENSE_MIN and place.risk_kind == "darkness"


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def risk_of(place: Place, level: int) -> int:
    return 1 + level


def outcome_of(params: StoryParams) -> str:
    if params.friendship >= 7 and params.risk_level == 0:
        return "friendship"
    if params.risk_level >= 2:
        return "fear"
    return "softened"


def predict(world: World, place_id: str) -> dict:
    sim = world.copy()
    _enter_place(sim, sim.get(place_id), narrate=False)
    return {
        "dread": sim.get("ghost").meters["dread"],
        "lonely": sim.get("ghost").meters["lonely"],
    }


def _enter_place(world: World, place: Place, narrate: bool = True) -> None:
    world.get("ghost").meters["dread"] += risk_of(place, int(world.facts.get("risk_level", 0)))
    world.get("ghost").meters["seen"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, friend: Entity, place: Place) -> None:
    child.memes["yearn"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"At dusk, {child.id} and {friend.id} went to {place.label}. "
        f"The windows looked black, and the hall kept its own quiet."
    )
    world.say(
        f"{child.id} yearned to prove there was nothing to fear there, "
        f"while {friend.id} walked more slowly beside {child.pronoun('object')}."
    )


def whisper(world: World, child: Entity, place: Place) -> None:
    world.say(
        f"In {place.darkness}, {child.id} heard a thin little whisper. "
        f'"Something is here," {child.pronoun()} thought, "and maybe it is waiting."'
    )


def monologue(world: World, friend: Entity, place: Place, ghost: Ghost) -> None:
    friend.memes["yearn"] += 1
    world.say(
        f"{friend.id} swallowed hard and listened to {friend.pronoun('possessive')} own thoughts: "
        f'"If I rush in, I might risk hurting someone. If I stay kind, maybe the dark will answer."'
    )
    world.say(
        f'{friend.id} looked at the {place.label_word if hasattr(place, "label_word") else place.label} and said, '
        f'"I think we should be careful."'
    )


def reveal(world: World, ghost: Ghost) -> None:
    ghost.meters["seen"] += 1
    ghost.meters["lonely"] += 1
    world.say(
        f"Then the ghost showed itself: {ghost.label}, all pale light and a soft sound. "
        f'It did not howl. It only said, "{ghost.sound}"'
    )


def warn(world: World, friend: Entity, ghost: Ghost, place: Place) -> None:
    friend.memes["caution"] += 1
    world.say(
        f'{friend.id} bit {friend.pronoun("possessive")} lip. "That is a risk," '
        f'{friend.pronoun()} whispered. "But maybe it is a lonely kind of risk."'
    )


def touch_heart(world: World, child: Entity, friend: Entity, ghost: Ghost) -> None:
    child.memes["kindness"] += 1
    friend.memes["kindness"] += 1
    ghost.meters["lonely"] = max(0.0, ghost.meters["lonely"] - 1.0)
    world.say(
        f"{child.id} took a slow breath and answered the whisper kindly. "
        f"{friend.id} stood close, and together they saw the ghost was not hungry for fright."
    )


def end_image(world: World, child: Entity, friend: Entity, place: Place, ghost: Ghost) -> None:
    world.say(
        f"By the end, the hall was still dark, but it did not feel empty anymore. "
        f"{child.id} and {friend.id} left a small lamp on the sill for {ghost.label}, "
        f"and the pale shape drifted near it like a sleepy ribbon."
    )
    world.say(
        f"{child.id} no longer yearned to test the dark. {child.id} yearned to be kind in it."
    )


def tell(params: StoryParams, place: Place, ghost: Ghost) -> World:
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    spook = world.add(Entity(id="ghost", kind="thing", type="ghost", label=ghost.label))
    hall = world.add(Entity(id="place", kind="thing", type="place", label=place.label))
    world.facts["risk_level"] = params.risk_level
    world.facts["place"] = place
    world.facts["ghost_cfg"] = ghost

    setup(world, child, friend, place)
    world.para()
    whisper(world, child, place)
    monologue(world, friend, place, ghost)
    warn(world, friend, ghost, place)

    world.para()
    if params.risk_level >= 2 and params.friendship < 5:
        world.get("ghost").meters["dread"] += 1
        reveal(world, ghost)
        world.say("For a moment, fear won and the room went cold.")
        world.say("Then the children backed away and promised to return with a grown-up.")
    else:
        reveal(world, ghost)
        touch_heart(world, child, friend, ghost)
        end_image(world, child, friend, place, ghost)

    world.facts.update(child=child, friend=friend, ghost=spook, hall=hall, outcome=outcome_of(params))
    return world


PLACES = {
    "old_house": Place(
        id="old_house",
        label="the old house",
        darkness="the long upstairs hall",
        yearned_for="answers",
        risk_kind="darkness",
        tags={"ghost", "dark", "risk"},
    ),
    "school_attic": Place(
        id="school_attic",
        label="the school attic",
        darkness="the dusty attic stairs",
        yearned_for="courage",
        risk_kind="darkness",
        tags={"ghost", "dark", "risk"},
    ),
    "quiet_park_room": Place(
        id="quiet_park_room",
        label="the little room at the park",
        darkness="the shadowed back room",
        yearned_for="company",
        risk_kind="darkness",
        tags={"ghost", "dark", "risk"},
    ),
}

GHOSTS = {
    "lantern_ghost": Ghost(
        id="lantern_ghost",
        label="the lantern ghost",
        sound="Please, do not leave me in the dark",
        need="a little light",
        harmless=True,
        tags={"ghost", "light"},
    ),
    "pocket_ghost": Ghost(
        id="pocket_ghost",
        label="the pocket ghost",
        sound="I only wanted someone to notice me",
        need="a friend",
        harmless=True,
        tags={"ghost", "friendship"},
    ),
    "window_ghost": Ghost(
        id="window_ghost",
        label="the window ghost",
        sound="I am small and lost and not scary at all",
        need="someone kind",
        harmless=True,
        tags={"ghost", "friendship"},
    ),
}

RESPONSES = {
    "lantern": Response(
        id="lantern",
        sense=3,
        power=2,
        text="set a little lamp near the window and waited until the pale shape drifted closer",
        fail="set down a lamp, but the dark stayed too thick to calm anyone",
        qa_text="set a little lamp near the window and let the ghost come closer",
        tags={"light", "kindness"},
    ),
    "speak_softly": Response(
        id="speak_softly",
        sense=3,
        power=2,
        text="spoke softly and asked what the ghost needed",
        fail="spoke softly, but the fear had already grown too big to answer back",
        qa_text="spoke softly and asked what the ghost needed",
        tags={"friendship", "kindness"},
    ),
    "call_grownup": Response(
        id="call_grownup",
        sense=2,
        power=4,
        text="called for a grown-up and kept everyone safely back",
        fail="called for a grown-up, but the waiting felt endless and the dark only deepened",
        qa_text="called for a grown-up and kept everyone safely back",
        tags={"safety", "risk"},
    ),
}

CHILD_NAMES = ["Mia", "Noah", "Lena", "Owen", "Ava", "Theo", "Iris", "Finn"]
FRIEND_NAMES = ["June", "Milo", "Bea", "Eli", "Nora", "Kai", "Rose", "Jude"]
TRAITS = ["curious", "gentle", "brave", "thoughtful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for p in PLACES:
        for g in GHOSTS:
            if reasonableness(PLACES[p], GHOSTS[g], RESPONSES["lantern"]):
                combos.append((p, g))
    return combos


def explain_rejection(place: Place, ghost: Ghost) -> str:
    return f"(No story: this place and ghost setup is not reasonable enough for a gentle ghost story.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost-story world about risk, yearn, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("The chosen response is too unsafely timid for this storyworld.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.ghost is None or c[1] == args.ghost)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, ghost = rng.choice(sorted(combos))
    child_gender = args.gender or rng.choice(["girl", "boy"])
    friend_gender = args.friend_gender or rng.choice(["girl", "boy"])
    child = args.name or rng.choice(CHILD_NAMES)
    friend = args.friend or rng.choice([n for n in FRIEND_NAMES if n != child])
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    return StoryParams(
        place=place,
        ghost=ghost,
        response=response,
        child=child,
        child_gender=child_gender,
        friend=friend,
        friend_gender=friend_gender,
        risk_level=rng.randint(0, 2),
        friendship=rng.randint(4, 8),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    place = f["place"]
    ghost = f["ghost_cfg"]
    return [
        f'Write a gentle ghost story for a 3-to-5-year-old that includes the words "risk" and "yearn".',
        f"Tell a friendship story in a spooky old place where {f['child'].id} yearns to be brave, but a friend notices the risk and responds kindly.",
        f'Write a child-friendly ghost story set in {place.label} where the ghost is lonely, not mean, and the ending feels safe.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, friend, ghost, place = f["child"], f["friend"], f["ghost"], f["place"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and {friend.id}, two friends who go into {place.label}. Their friendship matters because they listen to each other when the hall feels strange."),
        ("What did {0.id} yearn to do?".format(child),
         f"{child.id} yearned to prove the place was not scary. That wish pushed the story forward, even while the dark hallway made the risk feel bigger."),
        ("Why did the friend speak up?",
         f"{friend.id} noticed the risk and did not want either child to rush into the dark. The friend listened inwardly first, then used that careful thought to help."),
    ]
    if f["outcome"] == "fear":
        qa.append((
            "What happened at the scariest moment?",
            f"The ghost seemed too big for comfort, so the children backed away and got ready to call for help. That ending shows the risk became more important than the game."
        ))
    else:
        qa.append((
            "How did the children and the ghost change by the end?",
            f"They were kinder and less afraid by the end. The ghost felt less lonely, and the friends stopped treating the dark like a dare."
        ))
        qa.append((
            "How did the story end?",
            f"It ended with a small lamp near the window and the ghost drifting close like a sleepy ribbon. The hall was still dark, but the friendship made it feel warm instead of empty."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["ghost_cfg"].tags) | set(f["place"].tags) | {"risk", "friendship"}
    out = []
    if "ghost" in tags:
        out.append(("What is a ghost in a story?", "A ghost is often a pale, floating figure in a spooky story. In a gentle story, a ghost can be lonely or misunderstood instead of mean."))
    if "friendship" in tags:
        out.append(("What is friendship?", "Friendship is when people care about each other, listen, and help each other feel safe. Good friends can make scary places feel less scary."))
    if "risk" in tags:
        out.append(("What does risk mean?", "Risk means something might be unsafe or might go wrong. It is smart to pause and think before taking a risk."))
    out.append(("Why do people carry lamps in dark places?", "A lamp helps people see in the dark. It can also make a strange place feel calmer and less mysterious."))
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
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def tell_story(params: StoryParams) -> World:
    place = PLACES[params.place]
    ghost = GHOSTS[params.ghost]
    response = RESPONSES[params.response]
    if not reasonableness(place, ghost, response):
        raise StoryError(explain_rejection(place, ghost))
    world = World()
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender, role="child"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_gender, role="friend"))
    spook = world.add(Entity(id="ghost", kind="thing", type="ghost", label=ghost.label))
    world.facts["risk_level"] = params.risk_level
    world.add(Entity(id="place", kind="thing", type="place", label=place.label))

    setup(world, child, friend, place)
    world.para()
    whisper(world, child, place)
    monologue(world, friend, place, ghost)
    warn(world, friend, ghost, place)
    world.para()
    reveal(world, ghost)
    if params.risk_level >= 2 and params.friendship < 5:
        world.say(
            f"The risk felt too sharp, so {child.id} and {friend.id} backed away slowly."
        )
        world.say(
            f"They did not run. They just promised to return with a grown-up and a better plan."
        )
    else:
        touch_heart(world, child, friend, ghost)
        end_image(world, child, friend, place, ghost)
    world.facts.update(child=child, friend=friend, ghost=spook, place=place, outcome=outcome_of(params))
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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
    StoryParams(place="old_house", ghost="lantern_ghost", response="lantern", child="Mia", child_gender="girl", friend="Jude", friend_gender="boy", risk_level=0, friendship=7),
    StoryParams(place="school_attic", ghost="pocket_ghost", response="speak_softly", child="Noah", child_gender="boy", friend="Rose", friend_gender="girl", risk_level=1, friendship=6),
    StoryParams(place="quiet_park_room", ghost="window_ghost", response="call_grownup", child="Ava", child_gender="girl", friend="Finn", friend_gender="boy", risk_level=2, friendship=4),
]


ASP_RULES = r"""
harmless(G) :- ghost(G), not dangerous(G).
good_response(R) :- response(R), sense(R,S), sense_min(M), S >= M.
risk_place(P) :- place(P), darkness_place(P).
safe_story(P,G) :- place(P), ghost(G), harmless(G), good_response(_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("darkness_place", pid))
    for gid, g in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        if g.harmless:
            lines.append(asp.fact("harmless", gid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/2."))
    return sorted(set(asp.atoms(model, "safe_story")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show good_response/1."))
    return sorted(r for (r,) in asp.atoms(model, "good_response"))


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        print("MISMATCH in sensible responses.")
        rc = 1
    if rc == 0:
        try:
            sample = generate(CURATED[0])
            _ = sample.story
            print("OK: generation smoke test passed.")
        except Exception as e:  # pragma: no cover
            print(f"SMOKE TEST FAILED: {e}")
            rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small ghost story world about risk, yearn, and friendship.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
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


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show safe_story/2.\n#show good_response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("sensible responses: " + ", ".join(asp_sensible()))
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
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
