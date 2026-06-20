#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/sweeper_reason_drama_conflict_cautionary_kindness_heartwarming.py
==================================================================================================

A standalone storyworld for a heartwarming, conflict-shaped tiny tale:
children argue over a sweeper, a careful warning changes the plan, and a kind
solution turns the drama into a warm ending.

The seed words are woven into the domain itself:
- sweeper: a small floor sweeper used to clean a room
- reason: the careful explanation that prevents a mistake
- drama: the emotional flare when the plan feels urgent and tense

The world stays child-facing and state-driven: physical mess, attention, fear,
relief, trust, and kindness all evolve through the simulation.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
CAUTION_MIN = 2


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: {})
    memes: dict[str, float] = field(default_factory=lambda: {})

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "fear": 0.0, "trust": 0.0, "kindness": 0.0,
                          "drama": 0.0, "reason": 0.0, "relief": 0.0}

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
class Room:
    id: str
    label: str
    meters: dict[str, float] = field(default_factory=lambda: {"mess": 0.0, "calm": 1.0})
    memes: dict[str, float] = field(default_factory=lambda: {"warmth": 0.0})


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    noise: str
    gentle: bool = False
    catches_small_bits: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Mess:
    id: str
    label: str
    phrase: str
    risky: bool = False
    sticky: bool = False
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
        self.room: Room = Room("room", "the room")
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
        c.room = copy.deepcopy(self.room)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_mess_spread(world: World) -> list[str]:
    out: list[str] = []
    if world.room.meters["mess"] < THRESHOLD:
        return out
    sig = ("room_mess",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for e in world.entities.values():
        if e.kind == "character":
            e.memes["drama"] += 1
    world.room.meters["calm"] = max(0.0, world.room.meters["calm"] - 0.5)
    return out


CAUSAL_RULES = [Rule("mess_spread", _r_mess_spread)]


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            if rule.apply(world):
                changed = True


def reasonableness_gate(tool: Tool, mess: Mess) -> bool:
    return tool.catches_small_bits and (not mess.risky or tool.gentle)


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= CAUTION_MIN]


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def can_contain(response: Response, mess: Mess) -> bool:
    return response.power >= (2 if mess.sticky else 1)


def build_story(world: World, child: Entity, sibling: Entity, parent: Entity,
                tool: Tool, mess: Mess, response: Response, room: Room,
                delay: int = 0) -> World:
    child.memes["joy"] += 1
    sibling.memes["trust"] += 1
    sibling.memes["kindness"] += 1
    world.say(
        f"On a quiet afternoon, {child.id} and {sibling.id} were in {room.label}. "
        f"A little mess lay by the door, and {tool.phrase} waited in the closet."
    )
    world.say(
        f"{child.id} wanted to use the {tool.label} right away. "
        f"The room felt too busy for waiting, and the idea turned into drama."
    )
    world.para()
    child.memes["drama"] += 1
    sibling.memes["reason"] += 1
    world.say(
        f'{sibling.id} took a breath and said, "Wait. Here is the reason: '
        f"that {mess.label} is sticky, and if we rush, we might smear it around."'
    )
    if delay > 0:
        child.memes["fear"] += 1
    if tool.gentle and reasonableness_gate(tool, mess):
        world.say(
            f"{child.id} looked at the {tool.label}, then at {sibling.id}, and nodded. "
            f"The sweep could be careful instead of loud."
        )
        world.para()
        room.meters["mess"] += 1
        if can_contain(response, mess):
            room.meters["mess"] = 0.0
            room.meters["calm"] = 1.0
            child.memes["relief"] += 1
            sibling.memes["relief"] += 1
            world.say(
                f"{parent.label_word.capitalize()} came over and {response.text}."
            )
            world.say(
                f"The floor grew clean again, and the tiny {tool.label} hummed softly "
                f"while {child.id} and {sibling.id} worked side by side."
            )
            world.say(
                f"After that, {child.id} smiled, {sibling.id} smiled back, and the room "
                f"felt warm and safe."
            )
            outcome = "kind"
        else:
            world.say(
                f"{parent.label_word.capitalize()} tried to help, but the {mess.label} "
                f"kept smudging and the room stayed messy."
            )
            outcome = "messy"
    else:
        world.say(
            f"{child.id} nearly grabbed the {tool.label}, but {sibling.id}'s caution "
            f"turned the moment into a kinder plan."
        )
        world.para()
        room.meters["mess"] = max(room.meters["mess"], 1.0)
        if can_contain(response, mess):
            room.meters["mess"] = 0.0
            child.memes["relief"] += 1
            sibling.memes["relief"] += 1
            world.say(
                f"{parent.label_word.capitalize()} chose {response.qa_text}."
            )
            world.say(
                f"Together they cleaned the little {mess.label}, and the drama faded like "
                f"a cloud after rain."
            )
            world.say(
                f"{child.id} thanked {sibling.id} for the reason, and that kindness made "
                f"the whole room brighter."
            )
            outcome = "kind"
        else:
            world.say(
                f"The plan did not work well, and everyone had to stop and rethink."
            )
            outcome = "messy"
    world.room.meters["calm"] = 1.0 if outcome == "kind" else 0.5
    world.facts.update(
        child=child, sibling=sibling, parent=parent, tool=tool, mess=mess,
        response=response, room=room, outcome=outcome, delay=delay
    )
    propagate(world)
    return world


TOOLS = {
    "sweeper": Tool(
        "sweeper", "sweeper", "a little floor sweeper", "soft whirr",
        gentle=True, catches_small_bits=True, tags={"sweeper", "clean"}
    ),
    "broom": Tool(
        "broom", "broom", "a broom", "swish",
        gentle=False, catches_small_bits=True, tags={"broom", "clean"}
    ),
    "cloth": Tool(
        "cloth", "cloth", "a soft cloth", "pat pat",
        gentle=True, catches_small_bits=False, tags={"cloth", "clean"}
    ),
}

MESSES = {
    "crumbs": Mess("crumbs", "crumbs", "a trail of crumbs", risky=False, sticky=False, tags={"crumbs"}),
    "spill": Mess("spill", "spill", "a sticky spill", risky=True, sticky=True, tags={"spill", "sticky"}),
    "glitter": Mess("glitter", "glitter", "sparkly glitter", risky=False, sticky=True, tags={"glitter"}),
}

RESPONSES = {
    "gentle_sweep": Response(
        "gentle_sweep", 3, 3,
        "picked up the little sweeper and guided the mess into a neat pile",
        "tried to sweep too fast, but the mess only spread farther",
        "gently swept the mess into a neat pile",
        tags={"sweeper", "clean"}
    ),
    "together_wipe": Response(
        "together_wipe", 3, 2,
        "took the cloth and wiped the floor clean, one careful stroke at a time",
        "wiped quickly, but the sticky spots stayed behind",
        "wiped the floor clean together",
        tags={"cloth", "clean"}
    ),
    "pause_and_sort": Response(
        "pause_and_sort", 2, 1,
        "paused, sorted the little pieces, and then cleaned them one by one",
        "paused, but the mess still needed another plan",
        "sorted the pieces first and cleaned them after",
        tags={"reason", "kindness"}
    ),
    "too_noisy": Response(
        "too_noisy", 1, 1,
        "turned on the sweeper and made a noisy rush",
        "made a noisy rush, but it did not help",
        "used the noisy sweeper",
        tags={"sweeper"}
    ),
}

NAMES = ["Mia", "Noah", "Lina", "Eli", "Nora", "Finn", "Ava", "Leo"]
TAGS = ["kind", "careful", "thoughtful", "gentle", "brave", "patient"]


@dataclass
class StoryParams:
    child: str
    sibling: str
    parent: str
    tool: str
    mess: str
    response: str
    trait: str
    delay: int = 0
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for t in TOOLS.values():
        for m in MESSES.values():
            if reasonableness_gate(t, m):
                for _name in NAMES:
                    combos.append((t.id, m.id, "kind"))
    return combos


def explain_rejection(tool: Tool, mess: Mess) -> str:
    return (
        f"(No story: the {tool.label} and the {mess.label} do not make a good "
        f"heartwarming conflict. Pick a gentler tool and a mess it can truly help with.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story that includes the words "sweeper", "reason", and "drama".',
        f"Tell a short child-friendly story where {f['child'].id} wants to clean a mess, "
        f"but {f['sibling'].id} offers a reason to slow down and choose kindness.",
        f"Write a calming story with conflict and a gentle ending about a {f['tool'].label} "
        f"and a child learning to listen.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, sibling, parent = f["child"], f["sibling"], f["parent"]
    tool, mess, resp = f["tool"], f["mess"], f["response"]
    return [
        QAItem(
            question=f"Why was there drama at first?",
            answer=(
                f"There was drama because {child.id} wanted to hurry and use the {tool.label} "
                f"before thinking it through. {sibling.id} noticed the mess could spread, so the "
                f"moment felt tense."
            ),
        ),
        QAItem(
            question=f"What was {sibling.id}'s reason for slowing things down?",
            answer=(
                f"{sibling.id} said the {mess.label} could smear or spread if they rushed. "
                f"That careful reason helped everyone choose a kinder plan."
            ),
        ),
        QAItem(
            question="How did the ending turn out?",
            answer=(
                f"{parent.label_word.capitalize()} helped with {resp.qa_text}. "
                f"After that, the floor was clean, the tension was gone, and the children felt proud."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    qa = [
        QAItem(
            question="What is a sweeper?",
            answer="A sweeper is a tool that helps gather small bits from the floor into one place."
        ),
        QAItem(
            question="Why can reason be helpful during a conflict?",
            answer="Reason helps people slow down, notice what could go wrong, and choose a safer, kinder plan."
        ),
        QAItem(
            question="What does kindness change in a story?",
            answer="Kindness can turn an argument into teamwork, so everyone feels safer and more cared for."
        ),
    ]
    if f["mess"].id == "spill":
        qa.append(QAItem(
            question="Why is a sticky spill tricky?",
            answer="A sticky spill can smear when you hurry, so it often needs a careful, gentle cleanup."
        ))
    return qa


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        bits.append(f"role={e.role}" if e.role else "")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(b for b in bits if b)}")
    lines.append(f"  room     (room   ) meters={world.room.meters} memes={world.room.memes}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming sweeper storyworld.")
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mess", choices=MESSES)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--sibling")
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TAGS)
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
    tool = args.tool or rng.choice(list(TOOLS))
    mess = args.mess or rng.choice(list(MESSES))
    response = args.response or rng.choice(list(RESPONSES))
    if not reasonableness_gate(TOOLS[tool], MESSES[mess]):
        raise StoryError(explain_rejection(TOOLS[tool], MESSES[mess]))
    child = args.child or rng.choice(NAMES)
    sibling = args.sibling or rng.choice([n for n in NAMES if n != child])
    parent = args.parent or rng.choice(["mother", "father"])
    trait = args.trait or rng.choice(TAGS)
    return StoryParams(child, sibling, parent, tool, mess, response, trait)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(params.child, kind="character", type="child", role="instigator", traits=[params.trait]))
    sibling = world.add(Entity(params.sibling, kind="character", type="child", role="cautioner", traits=["kind", params.trait]))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    tool = world.add(Entity(params.tool, type="tool", label=TOOLS[params.tool].label))
    mess = world.add(Entity(params.mess, type="mess", label=MESSES[params.mess].label))
    response = RESPONSES[params.response]
    build_story(world, child, sibling, parent, TOOLS[params.tool], MESSES[params.mess], response, world.room, params.delay)
    world.facts.update(child=child, sibling=sibling, parent=parent, tool=tool, mess=mess, response=response)
    return world


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in story_qa(world)]],
        world_qa=[QAItem(q, a) for q, a in [(i.question, i.answer) for i in world_knowledge_qa(world)]],
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


def asp_facts() -> str:
    import asp
    lines = []
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    for mid in MESSES:
        lines.append(asp.fact("mess", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", CAUTION_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
valid(T,M,R) :- tool(T), mess(M), sensible(R).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(x for (x,) in asp.atoms(model, "sensible"))


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH: sensible responses.")
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: valid combos.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


CURATED = [
    StoryParams("Mia", "Noah", "mother", "sweeper", "crumbs", "gentle_sweep", "kind"),
    StoryParams("Lina", "Eli", "father", "sweeper", "spill", "together_wipe", "careful"),
    StoryParams("Ava", "Nora", "mother", "cloth", "glitter", "pause_and_sort", "thoughtful"),
]


def outcome_of(params: StoryParams) -> str:
    return "kind"


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for t, m, r in asp_valid_combos():
            print(f"{t:8} {m:8} {r}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                p = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child} & {p.sibling}: {p.tool} / {p.mess} ({outcome_of(p)})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
