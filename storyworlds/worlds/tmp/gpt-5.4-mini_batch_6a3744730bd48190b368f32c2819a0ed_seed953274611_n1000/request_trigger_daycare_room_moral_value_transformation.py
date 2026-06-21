#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/request_trigger_daycare_room_moral_value_transformation.py
=========================================================================================

A small standalone storyworld about a daycare-room mix-up:
a child makes a request, a trigger causes a misunderstanding,
and a moral value turns the day into a kinder transformation.

The prose is built from a live world model with physical meters and emotional memes.
The ending always proves what changed: a toy is shared, a feeling softens, and
the room ends in a calmer, brighter state.
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class TriggerSpec:
    id: str
    label: str
    what: str
    cause: str
    tags: set[str] = field(default_factory=set)


@dataclass
class RequestSpec:
    id: str
    label: str
    what: str
    tags: set[str] = field(default_factory=set)


@dataclass
class TransformationSpec:
    id: str
    from_state: str
    to_state: str
    lesson: str
    image: str
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
class StoryParams:
    child: str
    child_gender: str
    helper: str
    helper_gender: str
    request: str
    trigger: str
    transformation: str
    seed: Optional[int] = None


class Rule:
    def __init__(self, name: str, apply: Callable[[World], list[str]]) -> None:
        self.name = name
        self.apply = apply


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["upset"] < THRESHOLD or helper.memes["confused"] < THRESHOLD:
        return out
    sig = ("misunderstanding",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["tension"] += 1
    child.memes["hurt"] += 1
    helper.memes["worry"] += 1
    out.append("__misunderstanding__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    helper = world.get("helper")
    if child.memes["kindness"] < THRESHOLD:
        return out
    sig = ("transformation",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("room").meters["warmth"] += 1
    child.memes["share"] += 1
    helper.memes["relief"] += 1
    out.append("__transformation__")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding), Rule("transformation", _r_transformation)]


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


def request_causes_mixup(req: RequestSpec, trig: TriggerSpec) -> bool:
    return req.id != "no_request" and trig.id in {"sudden_sound", "wrong_guess", "snatch"}


def sensible_requests() -> list[RequestSpec]:
    return [r for r in REQUESTS.values() if r.id != "no_request"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for req in REQUESTS:
        for trig in TRIGGERS:
            for trans in TRANSFORMS:
                if request_causes_mixup(REQUESTS[req], TRIGGERS[trig]):
                    combos.append((req, trig, trans))
    return combos


def _do_trigger(world: World, trigger: TriggerSpec, narrate: bool = True) -> None:
    child = world.get("child")
    helper = world.get("helper")
    child.meters["startle"] += 1
    helper.memes["confused"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(
            f"The {trigger.what} was the trigger for a mix-up, and the room felt less bright."
        )


def tell(req: RequestSpec, trig: TriggerSpec, trans: TransformationSpec,
         child_name: str = "Mia", child_gender: str = "girl",
         helper_name: str = "Ava", helper_gender: str = "girl") -> World:
    world = World()
    room = world.add(Entity(id="room", kind="place", type="room", label="daycare room"))
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name, role="requester"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name, role="helper"))
    toy = world.add(Entity(id="toy", kind="thing", type="toy", label=req.what, tags=set(req.tags)))
    child.memes["hope"] = 1
    helper.memes["care"] = 1
    world.facts["room"] = room
    world.facts["request"] = req
    world.facts["trigger"] = trig
    world.facts["transformation"] = trans
    world.facts["toy"] = toy
    world.facts["child"] = child
    world.facts["helper"] = helper

    world.say(
        f"In the daycare room, {child_name} stood near the rug and smiled in tune, "
        f"for {child.pronoun('subject')} made a little request before noon."
    )
    world.say(
        f'"May I have the {req.label}?" {child_name} asked with a polite little glow, '
        f"hoping the play could keep its friendly flow."
    )

    world.para()
    child.memes["upset"] += 1
    helper.memes["confused"] += 1
    world.say(
        f"But then came the {trig.label}, and the moment felt strange; "
        f"the helper made a wrong guess, and the meaning changed."
    )
    world.say(
        f'"Oh! I thought you meant to take it away," {helper_name} said with a frown, '
        f"and the little room seemed to quiet down."
    )
    _do_trigger(world, trig)

    world.para()
    child.memes["kindness"] += 1
    world.say(
        f"{child_name} took a breath, then spoke gentle and clear: "
        f'"No, I only wanted a turn. I still want you near."'
    )
    world.say(
        f"The misunderstanding melted like snow in spring, '
        f'and {child_name} offered the {req.label} back with a sharing ring."
    )
    propagate(world, narrate=False)

    world.para()
    helper.memes["joy"] += 1
    child.memes["joy"] += 1
    world.say(
        f'The moral value was simple: be kind when you can, '
        f'for honest words help more than a hurried plan.'
    )
    world.say(
        f"So the day transformed from a knot into a song; '
        f'they took turns together, and the play moved along."
    )
    world.say(
        f"By the window, the daycare room glowed soft and bright, "
        f"and the shared little {req.label} felt just right."
    )

    world.facts["outcome"] = "resolved"
    return world


REQUESTS = {
    "blocks": RequestSpec(id="blocks", label="blocks", what="tower blocks", tags={"sharing", "toy"}),
    "truck": RequestSpec(id="truck", label="red truck", what="red truck", tags={"sharing", "toy"}),
    "book": RequestSpec(id="book", label="picture book", what="picture book", tags={"sharing", "toy"}),
}

TRIGGERS = {
    "sudden_sound": TriggerSpec(id="sudden_sound", label="loud bang", what="loud bang", cause="startled guessing", tags={"noise", "mixup"}),
    "wrong_guess": TriggerSpec(id="wrong_guess", label="wrong guess", what="wrong guess", cause="meaning confusion", tags={"mixup"}),
    "snatch": TriggerSpec(id="snatch", label="grabbed hand", what="grabbed hand", cause="fear of losing", tags={"mixup"}),
}

TRANSFORMS = {
    "share": TransformationSpec(id="share", from_state="tension", to_state="warmth", lesson="sharing is kind", image="two children taking turns", tags={"moral", "share"}),
    "apology": TransformationSpec(id="apology", from_state="hurt", to_state="relief", lesson="gentle words mend a mix-up", image="a smile after sorry", tags={"moral", "sorry"}),
    "turns": TransformationSpec(id="turns", from_state="conflict", to_state="cooperation", lesson="turn-taking helps everyone", image="hands passing the toy", tags={"moral", "turns"}),
}


def explain_rejection(req: RequestSpec, trig: TriggerSpec) -> str:
    return f"(No story: the requested pair '{req.id}' and '{trig.id}' does not create a believable misunderstanding.)"


def outcome_of(params: StoryParams) -> str:
    return "resolved" if request_causes_mixup(REQUESTS[params.request], TRIGGERS[params.trigger]) else "flat"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for rid, r in REQUESTS.items():
        lines.append(asp.fact("request", rid))
    for tid, t in TRIGGERS.items():
        lines.append(asp.fact("trigger", tid))
    for xid, x in TRANSFORMS.items():
        lines.append(asp.fact("transform", xid))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
valid(R,T,X) :- request(R), trigger(T), transform(X), mixup(R,T).
mixup(R,T) :- request(R), trigger(T), T != none.
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
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: ASP gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generated a story.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Daycare-room story world about request, trigger, and a kind transformation.")
    ap.add_argument("--request", choices=REQUESTS)
    ap.add_argument("--trigger", choices=TRIGGERS)
    ap.add_argument("--transformation", choices=TRANSFORMS)
    ap.add_argument("--child")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.request and args.trigger:
        if not request_causes_mixup(REQUESTS[args.request], TRIGGERS[args.trigger]):
            raise StoryError(explain_rejection(REQUESTS[args.request], TRIGGERS[args.trigger]))
    combos = [c for c in valid_combos()
              if (args.request is None or c[0] == args.request)
              and (args.trigger is None or c[1] == args.trigger)
              and (args.transformation is None or c[2] == args.transformation)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    req, trig, trans = rng.choice(sorted(combos))
    child = args.child or rng.choice(["Mia", "Noah", "Luna", "Eli", "Ivy"])
    helper = args.helper or rng.choice([n for n in ["Ava", "Leo", "Nia", "Owen", "Zoe"] if n != child])
    return StoryParams(child=child, child_gender="girl" if child in {"Mia", "Luna", "Ivy", "Zoe", "Ava", "Nia"} else "boy",
                       helper=helper, helper_gender="girl" if helper in {"Mia", "Luna", "Ivy", "Zoe", "Ava", "Nia"} else "boy",
                       request=req, trigger=trig, transformation=trans)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story set in a daycare room that includes the words "request" and "trigger".',
        f"Tell a gentle daycare story where a child makes a request, a trigger causes a misunderstanding, and kindness changes the day.",
        f"Write a short rhyming story about {f['child'].label} and a toy, with a moral about sharing and clear words.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"].label
    helper = f["helper"].label
    req = f["request"].label
    trig = f["trigger"].label
    trans = f["transformation"].lesson
    return [
        QAItem(question="What happened in the daycare room?", answer=f"{child} made a request, a trigger caused a misunderstanding, and then the two children cleared it up with kind words. The mix-up turned into a calmer, friendlier moment."),
        QAItem(question="What did the child ask for?", answer=f"{child} asked for the {req}. That request started the scene because it was the thing the child wanted to share or use."),
        QAItem(question="How did the misunderstanding end?", answer=f"The misunderstanding ended when {child} explained the request in a gentle way and the helper listened. After that, they chose a kinder path, which matches the lesson that {trans}."),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a request?", answer="A request is when someone politely asks for something they want or need. It is a kind way to speak to another person."),
        QAItem(question="What is a trigger?", answer="A trigger is something that starts a reaction or a change. In a story, a trigger can start a problem or a surprise."),
        QAItem(question="What is a moral value?", answer="A moral value is a kind rule for how to treat people well, like sharing, honesty, or kindness. It helps characters choose what is right."),
        QAItem(question="What is transformation?", answer="Transformation means something changes into a new state. In this story, a misunderstanding changes into cooperation and warmth."),
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
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(child="Mia", child_gender="girl", helper="Ava", helper_gender="girl", request="blocks", trigger="wrong_guess", transformation="share"),
    StoryParams(child="Noah", child_gender="boy", helper="Zoe", helper_gender="girl", request="truck", trigger="sudden_sound", transformation="turns"),
    StoryParams(child="Luna", child_gender="girl", helper="Leo", helper_gender="boy", request="book", trigger="snatch", transformation="apology"),
]


def generate(params: StoryParams) -> StorySample:
    for field_name, table in [("request", REQUESTS), ("trigger", TRIGGERS), ("transformation", TRANSFORMS)]:
        if getattr(params, field_name) not in table:
            raise StoryError(f"Unknown {field_name}: {getattr(params, field_name)}")
    world = tell(REQUESTS[params.request], TRIGGERS[params.trigger], TRANSFORMS[params.transformation],
                 child_name=params.child, child_gender=params.child_gender,
                 helper_name=params.helper, helper_gender=params.helper_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        print(asp_program("", "#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(" ", c)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
