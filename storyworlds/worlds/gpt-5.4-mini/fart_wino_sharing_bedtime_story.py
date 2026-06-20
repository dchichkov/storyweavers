#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/fart_wino_sharing_bedtime_story.py
===================================================================

A small bedtime-story world about sharing a treasured toy at night, with a
gentle embarrassing moment, a caring fix, and a cozy ending.

Premise:
- A child wants to keep a beloved bedtime pillow only for themselves.
- Another child wants to share it for comfort.
- A sudden fart makes the room awkward and tense.
- A kind adult helps them solve the problem with sharing, fresh air, and a
  calming bedtime swap.

The world is intentionally tiny and classical:
- Typed entities with meters and memes.
- A state-driven causal engine.
- A reasonableness gate.
- Story QA grounded in simulated state.
- Inline ASP twin for parity checks.
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
class BedtimeSetting:
    id: str
    place: str
    mood: str
    quiet_detail: str


@dataclass
class SharingThing:
    id: str
    label: str
    phrase: str
    comfort: str
    shareable: bool = True
    soft: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Aroma:
    id: str
    label: str
    phrase: str
    source: str
    embarrassing: bool = True
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


def _r_embarrass(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    for e in world.entities.values():
        if e.meters["fart"] >= THRESHOLD and ("embarrass", e.id) not in world.fired:
            world.fired.add(("embarrass", e.id))
            room.meters["awkward"] += 1
            for kid in world.entities.values():
                if kid.role in {"sharer", "keeper"}:
                    kid.memes["shy"] += 1
            out.append("__awkward__")
    return out


def _r_soothe(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    if room.meters["fresh_air"] >= THRESHOLD and ("soothe",) not in world.fired:
        world.fired.add(("soothe",))
        room.meters["awkward"] = 0
        for kid in world.entities.values():
            if kid.role in {"sharer", "keeper"}:
                kid.memes["calm"] += 1
                kid.memes["love"] += 1
        out.append("__calm__")
    return out


CAUSAL_RULES = [
    Rule("embarrass", "social", _r_embarrass),
    Rule("soothe", "social", _r_soothe),
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


def reasonableness_gate(thing: SharingThing, aroma: Aroma) -> bool:
    return thing.shareable and aroma.embarrassing


def good_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def is_resolved(response: Response, mood: str) -> bool:
    return response.power >= MOOD_LEVELS[mood]


SETTINGS = {
    "moon_room": BedtimeSetting("moon_room", "the moonlit bedroom", "soft and sleepy", "the window glowed like milk"),
    "nest_room": BedtimeSetting("nest_room", "the nest-like bedroom", "warm and hushy", "the blankets were piled like a little hill"),
    "storybook": BedtimeSetting("storybook", "the storybook room", "gentle and quiet", "a lamp made a small yellow pond"),
}

THINGS = {
    "pillow": SharingThing("pillow", "pillow", "a big starry pillow", "rest"),
    "blanket": SharingThing("blanket", "blanket", "a fluffy blanket", "warmth"),
    "stuffie": SharingThing("stuffie", "stuffie", "a soft bunny stuffie", "comfort"),
}

AROMAS = {
    "fart": Aroma("fart", "fart", "a silly fart", "tummy", tags={"fart"}),
    "wino": Aroma("wino", "wino", "the wino smell", "someone's coat", tags={"wino"}),
}

RESPONSES = {
    "open_window": Response("open_window", 3, 3, "opened the window and let the fresh night air drift in", "opened the window, but the smell stayed stuck", "opened the window and let the fresh night air drift in", tags={"air"}),
    "share_blanket": Response("share_blanket", 3, 2, "spread the blanket wider so both children could tuck in together", "spread the blanket wider, but the room still felt upset", "spread the blanket wider so both children could tuck in together", tags={"sharing"}),
    "tell_story": Response("tell_story", 2, 1, "began a calm bedtime story and waited for the giggles to settle", "tried to tell a story, but the room needed more than that", "began a calm bedtime story and waited for the giggles to settle", tags={"story"}),
    "fan_air": Response("fan_air", 3, 4, "fanned the air gently until the room felt clean again", "fanned the air, but it was too little for the smell", "fanned the air gently until the room felt clean again", tags={"air"}),
}

MOOD_LEVELS = {"soft": 1, "warm": 2, "gentle": 1}
GIRL_NAMES = ["Lila", "Maya", "Nina", "Ava", "Ivy", "Rose"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Noah", "Eli", "Ben"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid in SETTINGS:
        for tid, thing in THINGS.items():
            for aid, aroma in AROMAS.items():
                if reasonableness_gate(thing, aroma):
                    out.append((sid, tid, aid))
    return out


@dataclass
class StoryParams:
    setting: str
    thing: str
    aroma: str
    response: str
    sharer: str
    sharer_gender: str
    keeper: str
    keeper_gender: str
    parent: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime sharing storyworld with fart and wino.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--aroma", choices=AROMAS)
    ap.add_argument("--response", choices=RESPONSES)
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


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and args.aroma and not reasonableness_gate(THINGS[args.thing], AROMAS[args.aroma]):
        raise StoryError("(No story: this thing does not make sense for a sharing bedtime smell story.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.thing is None or c[1] == args.thing)
              and (args.aroma is None or c[2] == args.aroma)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, thing, aroma = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    sharer_gender = rng.choice(["girl", "boy"])
    keeper_gender = "boy" if sharer_gender == "girl" else "girl"
    sharer = _pick_name(rng, sharer_gender)
    keeper = _pick_name(rng, keeper_gender)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, thing, aroma, response, sharer, sharer_gender, keeper, keeper_gender, parent)


def _do_make_mess(world: World, aroma: Aroma) -> None:
    world.get("room").meters["awkward"] += 1
    world.get("room").meters[aroma.id] += 1
    for kid in world.entities.values():
        if kid.role in {"sharer", "keeper"}:
            kid.memes["embarrassed"] += 1
    propagate(world, narrate=False)


def tell(params: StoryParams) -> World:
    world = World()
    setting = SETTINGS[params.setting]
    thing = THINGS[params.thing]
    aroma = AROMAS[params.aroma]
    response = RESPONSES[params.response]
    sharer = world.add(Entity(params.sharer, kind="character", type=params.sharer_gender, role="sharer"))
    keeper = world.add(Entity(params.keeper, kind="character", type=params.keeper_gender, role="keeper"))
    parent = world.add(Entity("Parent", kind="character", type=params.parent, role="parent", label="the parent"))
    room = world.add(Entity("room", type="room", label=setting.place))
    world.facts["setting"] = setting
    world.facts["thing"] = thing
    world.facts["aroma"] = aroma
    world.facts["response"] = response
    world.facts["sharer"] = sharer
    world.facts["keeper"] = keeper
    world.facts["parent"] = parent

    world.say(f"At bedtime, {sharer.id} and {keeper.id} curled up in {setting.place}. {setting.quiet_detail}.")
    world.say(f"They shared {thing.phrase}, because it was the kind of soft treasure that made the room feel safe.")

    world.para()
    world.say(f"Then {sharer.id}'s tummy gave a silly fart, and the room went very still.")
    _do_make_mess(world, aroma)
    if aroma.id == "fart":
        world.say(f"The fart puffed out before anyone could hide it, and {keeper.id} made a surprised face.")
    else:
        world.say(f"Even the wino smell from the old coat drifted in, and both children wrinkled their noses.")

    world.para()
    world.say(f'{keeper.id} leaned toward {sharer.id} and whispered, "Can we still share?"')
    response_text = response.text
    room.meters["fresh_air"] = 0.0
    if response.id == "open_window":
        room.meters["fresh_air"] += 1
    elif response.id == "fan_air":
        room.meters["fresh_air"] += 2
    elif response.id == "share_blanket":
        room.meters["shared_warmth"] += 1
    elif response.id == "tell_story":
        room.meters["calm_story"] += 1

    resolved = is_resolved(response, "warm" if response.id in {"open_window", "fan_air"} else "soft")
    if resolved:
        propagate(world)
        world.say(f"{parent.label_word.capitalize()} came in, smiled, and {response_text}.")
        world.say(f"Then {parent.pronoun()} helped them share the {thing.label} so both could rest.")
        sharer.memes["joy"] += 1
        keeper.memes["joy"] += 1
        sharer.memes["sharing"] += 1
        keeper.memes["sharing"] += 1
        world.say(f"Soon {sharer.id} and {keeper.id} were side by side, under the {thing.label}, sleepy and calm.")
    else:
        world.say(f"{parent.label_word.capitalize()} came in, tried to help, and {response.fail}.")
        world.say(f"So the children opened the window, held the {thing.label} together, and waited until the room felt gentle again.")
        room.meters["fresh_air"] += 1
        propagate(world)

    world.facts["resolved"] = resolved
    world.facts["outcome"] = "shared"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a 3-to-5-year-old that includes the words "{f["aroma"].label}" and "sharing".',
        f"Tell a soft bedtime story where {f['sharer'].id} and {f['keeper'].id} try to share {f['thing'].phrase} after a silly {f['aroma'].label}.",
        f'Write a gentle story that teaches sharing, includes the word "{f["aroma"].label}", and ends with cozy sleep.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    sharer, keeper, parent, thing, aroma, response = f["sharer"], f["keeper"], f["parent"], f["thing"], f["aroma"], f["response"]
    ans1 = f"It is about {sharer.id} and {keeper.id}, two children in {f['setting'].place}, and their {parent.label_word}."
    ans2 = f"They were sharing {thing.phrase} at bedtime, which made the room feel cozy before the embarrassing moment."
    ans3 = f"A silly {aroma.label} happened, and then the grown-up helped them calm down and keep sharing."
    out = [
        ("Who is the story about?", ans1),
        ("What were the children doing before the silly smell?", ans2),
        (f"What happened after the {aroma.label}?", ans3),
    ]
    if f["resolved"]:
        out.append((f"How did {parent.label_word} help?", f"{parent.label_word.capitalize()} {response.qa_text}. That made it easy for the children to share again and settle down."))
        out.append(("How did the story end?", f"The children stayed together, shared the {thing.label}, and fell asleep feeling close and safe."))
    else:
        out.append((f"How did {parent.label_word} help?", f"{parent.label_word.capitalize()} tried to help, but the room needed more fresh air first. The children opened the window and kept sharing until everything felt calm."))
        out.append(("How did the story end?", f"The room became gentle again, and the children kept the {thing.label} between them while they got sleepy."))
    return out


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    tags = set(f["aroma"].tags) | {"sharing"}
    if f["response"].id in {"open_window", "fan_air"}:
        tags.add("air")
    if f["response"].id == "share_blanket":
        tags.add("blanket")
    if f["thing"].id == "pillow":
        tags.add("pillow")
    return [
        ("What is sharing?", "Sharing means two or more people use, enjoy, or keep something together instead of one person keeping it all to themselves."),
        ("Why open a window after a bad smell?", "Opening a window lets fresh air move through the room, and that helps push the bad smell away."),
        ("What is a bedtime blanket for?", "A bedtime blanket keeps you warm and cozy while you rest."),
    ]


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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
awkward(room) :- entity(room), farted(F), F >= 1.
calm(room) :- fresh_air(room), not awkward(room).
resolved(R) :- response(R), power(R,P), need(N), P >= N.
need(1).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if t.shareable:
            lines.append(asp.fact("shareable", tid))
    for aid, a in AROMAS.items():
        lines.append(asp.fact("aroma", aid))
        if a.embarrassing:
            lines.append(asp.fact("embarrassing", aid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show resolved/1."))
    asp_res = sorted(set(asp.atoms(model, "resolved")))
    py_res = sorted([r.id for r in RESPONSES.values() if r.power >= 1 and r.sense >= 2])
    ok = True
    if not set(asp_res) == set((r,) for r in py_res):
        ok = False
        print("MISMATCH in ASP resolution gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        return 1
    return 0 if ok else 1


def asp_choices() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show response/1."))
    return sorted(r for (r,) in asp.atoms(model, "response"))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
    StoryParams("moon_room", "pillow", "fart", "open_window", "Lila", "girl", "Milo", "boy", "mother"),
    StoryParams("nest_room", "blanket", "wino", "share_blanket", "Theo", "boy", "Nina", "girl", "father"),
    StoryParams("storybook", "stuffie", "fart", "fan_air", "Ava", "girl", "Ben", "boy", "mother"),
]


def explain_rejection(thing: SharingThing, aroma: Aroma) -> str:
    return f"(No story: {thing.label} does not fit the sharing bedtime smell setup.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.thing and args.aroma and not reasonableness_gate(THINGS[args.thing], AROMAS[args.aroma]):
        raise StoryError(explain_rejection(THINGS[args.thing], AROMAS[args.aroma]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.thing is None or c[1] == args.thing)
              and (args.aroma is None or c[2] == args.aroma)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, thing, aroma = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(RESPONSES))
    sharer_gender = rng.choice(["girl", "boy"])
    keeper_gender = "boy" if sharer_gender == "girl" else "girl"
    sharer = rng.choice(GIRL_NAMES if sharer_gender == "girl" else BOY_NAMES)
    keeper = rng.choice(GIRL_NAMES if keeper_gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, thing, aroma, response, sharer, sharer_gender, keeper, keeper_gender, parent)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show response/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("\n".join(asp_choices()))
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.sharer} & {p.keeper}: {p.aroma} with {p.thing} ({p.setting})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
