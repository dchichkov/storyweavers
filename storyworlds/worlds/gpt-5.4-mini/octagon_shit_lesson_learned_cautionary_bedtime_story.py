#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/octagon_shit_lesson_learned_cautionary_bedtime_story.py
======================================================================================

A small standalone storyworld for a bedtime-style cautionary tale about a child,
a glowing octagon-shaped night-light, a smelly mess on the path, and a lesson
learned before bed.

The domain is deliberately tiny: a child wants one last bedtime errand, meets a
badly placed hazard, calls for help, and learns a safer habit for next time.
Stories are simulated from state, not assembled from a frozen paragraph.

Seed words: octagon, shit
Style: bedtime story
Features: lesson learned, cautionary
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
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
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Setting:
    id: str
    place: str
    bedtime: bool = True


@dataclass
class Hazard:
    id: str
    label: str
    smell: str
    near: str
    grossness: int = 1
    tags: set[str] = field(default_factory=set)


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    glow: str = ""
    safe: bool = False
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_smudge(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    haz = world.get("hazard")
    if child.meters["muddied"] >= THRESHOLD and haz.meters["tracked"] < THRESHOLD:
        sig = ("smudge", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            haz.meters["tracked"] += 1
            out.append("__smudge__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    mom = world.get("mom")
    if child.meters["muddied"] >= THRESHOLD and mom.memes["worry"] < THRESHOLD:
        sig = ("worry", child.id)
        if sig not in world.fired:
            world.fired.add(sig)
            mom.memes["worry"] += 1
            out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("smudge", "physical", _r_smudge), Rule("worry", "social", _r_worry)]


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


def hazard_at_risk(hazard: Hazard, item: Item) -> bool:
    return True if hazard.id == "dog_shit" and item.id == "feet" else False


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def is_contained(response: Response, hazard: Hazard, delay: int) -> bool:
    return response.power >= hazard.grossness + delay


def _do_walk(world: World, child: Entity, narrate: bool = True) -> None:
    child.meters["muddied"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, child: Entity, mom: Entity, setting: Setting) -> None:
    child.memes["curiosity"] += 1
    child.memes["comfort"] += 1
    world.say(
        f"At bedtime, {child.id} was still awake in {setting.place}. "
        f"The room felt soft and sleepy, and a small {NIGHTLIGHT.label} glowed "
        f"like a quiet star."
    )


def need_help(world: World, child: Entity, hazard: Hazard, item: Item) -> None:
    world.say(
        f"{child.id} wanted to tiptoe to the door for one last good-night check. "
        f"But near {hazard.near}, there was a dark, smelly spot of {hazard.label}."
    )
    world.say(
        f'"Ew," {child.id} whispered. "{item.label.capitalize()} on the floor? '
        f'I need my {item.label} before I go any farther."'
    )


def warn(world: World, mom: Entity, child: Entity, hazard: Hazard) -> None:
    mom.memes["care"] += 1
    world.say(
        f'{mom.id} sat up and spoke gently. "{child.id}, stop right there. '
        f"{hazard.label.capitalize()} is dirty, and it can make your feet gross. "
        f"Call me before you step in it.""
    )


def step_in(world: World, child: Entity, hazard: Hazard) -> None:
    child.memes["oops"] += 1
    child.meters["muddied"] += 1
    world.say(
        f"{child.id} took one step too far and went straight into the mess. "
        f"{child.id} made a face, then froze."
    )


def cry_out(world: World, child: Entity, mom: Entity, hazard: Hazard) -> None:
    world.say(
        f'"Mom!" {child.id} called. "I stepped in {hazard.label}!"'
    )
    world.say(f'"I am here," {mom.id} answered at once.')


def rescue(world: World, mom: Entity, response: Response, hazard: Hazard) -> None:
    child = world.get("child")
    child.meters["muddied"] = 0.0
    body = response.text.replace("{hazard}", hazard.label)
    world.say(f"In a blink, {mom.id} {body}.")
    world.say(
        f"The bad spot was gone, the path was clean again, and the little "
        f"bedtime room felt calm."
    )


def lesson(world: World, mom: Entity, child: Entity, hazard: Hazard) -> None:
    child.memes["lesson"] += 1
    child.memes["relief"] += 1
    world.say(
        f"{mom.id} hugged {child.id} and said, "
        f'"That is why we look first and ask for help. {hazard.label.capitalize()} '
        f"isn't a toy, and it is kinder to keep away from it."'
    )
    world.say(
        f'{child.id} nodded hard. "I will call you first," {child.id} promised.'
    )


def safe_end(world: World, child: Entity, mom: Entity, item: Item) -> None:
    child.memes["joy"] += 1
    world.say(
        f"Then {mom.id} handed over {item.phrase}. {item.glow} "
        f"And together they finished the tiny bedtime task the safe way."
    )
    world.say(
        f"{child.id} went back to bed warm and calm, and the little {item.label} "
        f"rested by the pillow like a friendly moon."
    )


def tell(setting: Setting, hazard: Hazard, item: Item, response: Response,
         child_name: str = "Milo", child_gender: str = "boy",
         mom_name: str = "Mom") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    mom = world.add(Entity(id=mom_name, kind="character", type="mother", role="parent"))
    world.add(Entity(id="hazard", type="thing", label=hazard.label))
    world.add(Entity(id="item", type="thing", label=item.label))
    setup(world, child, mom, setting)
    world.para()
    need_help(world, child, hazard, item)
    warn(world, mom, child, hazard)
    step_in(world, child, hazard)
    cry_out(world, child, mom, hazard)
    world.para()
    if is_contained(response, hazard, 0):
        rescue(world, mom, response, hazard)
        lesson(world, mom, child, hazard)
        world.para()
        safe_end(world, child, mom, item)
        outcome = "contained"
    else:
        world.say(
            f"{mom.id} tried to help, but the mess was already too big. "
            f"She scooped {child.id} up and led {child.id} back inside."
        )
        world.say(
            f"After that, the hallway stayed closed and the bedtime plan changed."
        )
        child.memes["lesson"] += 1
        outcome = "burned"
    world.facts.update(child=child, mom=mom, hazard=hazard, item=item, response=response, outcome=outcome)
    return world


SETTINGS = {
    "bedroom": Setting("bedroom", "the bedroom"),
    "hallway": Setting("hallway", "the hallway"),
    "porch": Setting("porch", "the porch"),
}

HAZARDS = {
    "dog_shit": Hazard("dog_shit", "dog shit", "very smelly", "the front gate", grossness=2, tags={"mess", "bad"}),
}

ITEMS = {
    "slippers": Item("slippers", "slippers", "a pair of soft slippers", glow="They were warm and easy to slip on.", tags={"safe"}),
    "flashlight": Item("flashlight", "flashlight", "a little flashlight", glow="It clicked on bright and gentle.", safe=True, tags={"safe", "light"}),
    "sock": Item("sock", "sock", "a clean sock", glow="It was tucked by the bed.", tags={"safe"}),
}

NIGHTLIGHT = Item("octagon_light", "octagon night-light", "an octagon-shaped night-light", glow="Its eight corners shone softly.", safe=True, tags={"octagon", "light"})

RESPONSES = {
    "cleaner": Response("cleaner", 3, 3, "used a paper towel and a warm cloth to clean the spot", "tried to clean it, but it spread too much", "cleaned the spot with a paper towel and a warm cloth", tags={"clean"}),
    "soap": Response("soap", 2, 2, "used soapy water and wiped the floor until it was clean", "used soapy water, but the mess was too big", "used soapy water and wiped the floor clean", tags={"clean"}),
    "outside": Response("outside", 4, 4, "opened the door, kept the child away from the mess, and cleaned it outside", "opened the door, but the child had already stepped in it again", "kept the child away and cleaned the mess outside", tags={"clean"}),
}

SENSE_MIN = 2

CURATED = [
    ("bedroom", "dog_shit", "flashlight", "cleaner", "Milo", "boy"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for hazard in HAZARDS:
            for item in ITEMS:
                if hazard_at_risk(HAZARDS[hazard], ITEMS["slippers"]):
                    combos.append((setting, hazard, item))
    return combos


@dataclass
class StoryParams:
    setting: str
    hazard: str
    item: str
    response: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a bedtime story for a small child that includes the words "octagon" and "{f["hazard"].label}".',
        f"Tell a cautionary bedtime story where {f['child'].id} is warned away from {f['hazard'].label} and learns a safer habit.",
        f"Write a gentle lesson-learned story about a sleepy child, a glowing octagon night-light, and a smelly mess on the path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, mom, hazard, item = f["child"], f["mom"], f["hazard"], f["item"]
    qa = [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {child.id} at bedtime, {mom.id}, and a smelly {hazard.label} on the path. The little octagon night-light made the room feel safe and soft."
        ),
        QAItem(
            question=f"Why did {child.id} need help?",
            answer=f"{child.id} was trying to tiptoe past {hazard.near}, but the {hazard.label} was in the way. {mom.id} needed to stop {child.id} before the mess got on {child.pronoun('possessive')} feet."
        ),
    ]
    if f["outcome"] == "contained":
        qa.append(
            QAItem(
                question="How was the problem solved?",
                answer=f"{mom.id} cleaned the mess right away and kept {child.id} away from it. Then {child.id} got to finish bedtime with {item.phrase} and a calmer room."
            )
        )
        qa.append(
            QAItem(
                question="What did the child learn?",
                answer=f"{child.id} learned to look first and call for help before stepping toward a dirty place. {mom.id}'s gentle warning helped turn the scary moment into a safe bedtime lesson."
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an octagon?",
            answer="An octagon is a shape with eight sides. It can look like a stop sign or a neat little night-light frame."
        ),
        QAItem(
            question="Why should children stay away from dog shit?",
            answer="Dog shit is dirty and smelly, and it can carry germs. Children should not touch it and should call a grown-up to clean it up."
        ),
        QAItem(
            question="What does a flashlight do?",
            answer="A flashlight gives light without a flame. It helps people see in the dark and is safe to hold."
        ),
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


def explain_rejection(hazard: Hazard, item: Item) -> str:
    return f"(No story: {item.label} is not the right kind of thing for this hazard.)"


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    better = " / ".join(sorted(r.id for r in sensible_responses()))
    return f"(Refusing response '{rid}': it is too weak for the story. Try: {better}.)"


ASP_RULES = r"""
valid(S, H, I) :- setting(S), hazard(H), item(I), risky(H, I).
contained(R) :- response(R), sense(R, S), sense_min(M), S >= M.
outcome(contained) :- contained(_).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for hid in HAZARDS:
        lines.append(asp.fact("hazard", hid))
        lines.append(asp.fact("risky", hid, "slippers"))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid_combos()")
        rc = 1
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, hazard=None, item=None, response=None, child_name=None, child_gender=None), random.Random(1)))
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny bedtime cautionary storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--hazard", choices=HAZARDS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
        raise StoryError(explain_response(args.response))
    setting = args.setting or rng.choice(list(SETTINGS))
    hazard = args.hazard or rng.choice(list(HAZARDS))
    item = args.item or rng.choice(list(ITEMS))
    response = args.response or rng.choice([r.id for r in sensible_responses()])
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Milo", "Nina", "Ruby", "Theo"])
    return StoryParams(setting, hazard, item, response, name, gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], HAZARDS[params.hazard], ITEMS[params.item], RESPONSES[params.response], params.child_name, params.child_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q.question, q.answer) for q in story_qa(world)],
        world_qa=[QAItem(q.question, q.answer) for q in world_knowledge_qa(world)],
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
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples = []
    if args.all:
        samples = [generate(StoryParams(*c)) for c in CURATED]
    else:
        for i in range(args.n):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
