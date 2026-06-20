#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hypothesis_whisk_suspense_bad_ending_nursery_rhyme.py
======================================================================================

A standalone story world in a nursery-rhyme style: a small kitchen scene,
a careful guess, a whisk as the key object, a suspenseful turn, and a bad
ending. The world is tiny on purpose: one child, one helper, one risky place,
and one object that should not be used the wrong way.

The required seed words are included as living parts of the model:
- hypothesis
- whisk

The world is designed to generate short, rhymey, child-facing stories with
a suspense beat and a bad ending.
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
    risky: bool = False
    safe: bool = False

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)



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
    dim: str
    rhyme_tail: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class ObjectCfg:
    id: str
    label: str
    risky: bool = False
    safe: bool = False

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class ActionCfg:
    id: str
    verb: str
    suspense_line: str
    danger: str
    power: int

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
class ResponseCfg:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
        clone = World()
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
@dataclass
class StoryParams:
    setting: str
    object: str
    action: str
    response: str
    child_name: str
    child_gender: str
    helper_name: str
    helper_gender: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = defaultdict(float)
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
    "kitchen": Setting("kitchen", "the little kitchen", "bright", "by the stove"),
    "pantry": Setting("pantry", "the pantry nook", "small", "behind the tall door"),
    "cellar": Setting("cellar", "the cellar stair", "dark", "down the wooden stair"),
}

OBJECTS = {
    "whisk": ObjectCfg("whisk", "the whisk", risky=True),
    "candles": ObjectCfg("candles", "the candles", risky=True),
    "jam": ObjectCfg("jam", "the jam jar", safe=False),
    "ladle": ObjectCfg("ladle", "the ladle", safe=True),
}

ACTIONS = {
    "reach": ActionCfg("reach", "reach for it", "The air went still and the clock ticked slow.", "the way was risky", 2),
    "peer": ActionCfg("peer", "peer inside", "The shadow stayed long and the hush grew deep.", "the dark looked steep", 1),
    "climb": ActionCfg("climb", "climb up", "Up went the feet; down went the breath.", "the shelf could tip", 3),
}

RESPONSES = {
    "call_mom": ResponseCfg("call_mom", 3, 4, "called Mom and waited by the door", "called Mom, but the trouble had grown too large to mend", "called Mom and waited by the door"),
    "grab_stool": ResponseCfg("grab_stool", 1, 1, "grabbed a stool and tried too late to help", "grabbed a stool, but it wobbled and made things worse", "grabbed a stool"),
    "shout_stop": ResponseCfg("shout_stop", 2, 2, "shouted 'Stop!' and ran for help", "shouted 'Stop!', but the whisper of danger was already gone", "shouted 'Stop!' and ran for help"),
}

GIRL_NAMES = ["Lily", "Mabel", "Nora", "Mina", "Daisy", "Elsie"]
BOY_NAMES = ["Tom", "Robin", "Pip", "Finn", "Theo", "Jasper"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for s in SETTINGS:
        for o in OBJECTS.values():
            for a in ACTIONS.values():
                for r in RESPONSES.values():
                    if o.risky and a.power >= 1:
                        out.append((s, o.id, a.id, r.id))
    return out


def reasonableness_gate(obj: ObjectCfg, action: ActionCfg) -> bool:
    return obj.risky and action.power >= 1


def best_response() -> ResponseCfg:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def sensible_responses() -> list[ResponseCfg]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def severity(action: ActionCfg, delay: int) -> int:
    return action.power + delay


def can_contain(response: ResponseCfg, action: ActionCfg, delay: int) -> bool:
    return response.power >= severity(action, delay)


def _rule_suspense(world: World) -> list[str]:
    out = []
    child = world.get("child")
    if child.meters["worry"] < THRESHOLD:
        return out
    sig = ("suspense", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["fear"] += 1
    out.append("__suspense__")
    return out


CAUSAL_RULES: list[tuple[str, Callable[[World], list[str]]]] = [
    ("suspense", _rule_suspense),
]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for _, rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(line for line in lines if not line.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)


def predict(world: World, action: ActionCfg) -> dict:
    sim = world.copy()
    child = sim.get("child")
    child.meters["worry"] += 1
    propagate(sim, narrate=False)
    return {"fear": sim.get("child").memes["fear"]}


def tell(setting: Setting, obj: ObjectCfg, action: ActionCfg, response: ResponseCfg,
         child_name: str = "Mabel", child_gender: str = "girl",
         helper_name: str = "Mom", helper_gender: str = "girl",
         delay: int = 2) -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender, label=child_name,
                             role="child", traits=["tiny", "careful"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_gender, label=helper_name,
                              role="helper"))
    thing = world.add(Entity(id="whisk", kind="thing", type="thing", label=obj.label, risky=obj.risky))
    child.memes["hope"] = 1
    helper.memes["calm"] = 1
    world.facts["delay"] = delay
    world.facts["setting"] = setting
    world.facts["object"] = obj
    world.facts["action"] = action
    world.facts["response"] = response

    world.say(f"In {setting.place}, {child_name} was small as a seed and light as a song.")
    world.say(f"{helper_name} hummed a nursery rhyme while the kettle sang and the spoon made taps.")
    world.say(f"Then {child_name} noticed {obj.label} and made a little hypothesis: "
              f'"Maybe {obj.label} will help me find the shiny thing by the stairs."')
    world.para()
    world.say(f"But {setting.rhyme_tail} hid the shadows deep, and the room grew still.")
    world.say(f"{child_name} reached for {obj.label}, and the clock went tick, tick, tick.")
    child.meters["worry"] += 1
    propagate(world, narrate=False)
    world.say(f'"{action.suspense_line}" whispered the house.')
    world.para()

    if can_contain(response, action, delay):
        world.say(f"{helper_name} came at once and {response.text}.")
        world.say(f"The little worry passed, and {obj.label} stayed safe and bright on the table.")
        world.say(f"By moonlight, {child_name} tucked the whisk away and sang a soft tune to the cat.")
    else:
        world.say(f"{helper_name} came running, but {response.fail}.")
        world.say(f"The whisk clattered down, the shadows jumped, and the little kitchen lost its brave song.")
        world.say(f"At last the candle went out, and the night kept its secret.")
        child.meters["broken"] += 1
        thing.meters["dropped"] += 1

    outcome = "contained" if can_contain(response, action, delay) else "bad"
    world.facts["outcome"] = outcome
    world.facts["child"] = child
    world.facts["helper"] = helper
    world.facts["thing"] = thing
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c, h, o, a = f["child"], f["helper"], f["object"], f["action"]
    return [
        f'Write a nursery-rhyme style suspense story that includes the words "hypothesis" and "{o.label_word if hasattr(o, "label_word") else "whisk"}".',
        f"Tell a small kitchen story where {c.label} makes a hypothesis about {o.label}, then a shadowy moment happens and {h.label} tries to help.",
        f"Write a short rhyme for a child where the whisk, the stairs, and a bad ending all appear in one tense scene.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, obj, action, resp = f["child"], f["helper"], f["object"], f["action"], f["response"]
    story = [
        QAItem(
            question=f"What did {child.label} think the whisk might do?",
            answer=f"{child.label} made a little hypothesis that {obj.label} might help find a shiny thing by the stairs. It was a guess, but it led {child.label} closer to the dark place."
        ),
        QAItem(
            question="Why did the room feel suspenseful?",
            answer=f"The room got quiet, the clock ticked slow, and the stairs stayed dark. That hush made the moment feel tense before anyone could act."
        ),
    ]
    if f["outcome"] == "bad":
        story.append(QAItem(
            question="What happened at the end?",
            answer=f"The help came too late, so the whisk clattered down and the little kitchen lost its brave song. The ending is sad because the danger was not fixed in time."
        ))
    else:
        story.append(QAItem(
            question="How did the helper respond?",
            answer=f"{helper.label} came at once and {resp.text}. That quick help kept the whisk safe and settled the worry."
        ))
    return story


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hypothesis?",
            answer="A hypothesis is a guess about what might happen or what something might mean. People use it to think before they decide."
        ),
        QAItem(
            question="What is a whisk?",
            answer="A whisk is a kitchen tool with loops of wire for mixing food. It is not a toy, and it should stay where grown-ups keep it."
        ),
        QAItem(
            question="What should a child do when something feels scary?",
            answer="A child should call for a grown-up right away and stay away from the danger. Getting help fast is the safest choice."
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
    for e in list(world.entities.values()):
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
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "whisk", "reach", "call_mom", "Mabel", "girl", "Mom", "girl", delay=2),
    StoryParams("pantry", "candles", "peer", "shout_stop", "Tom", "boy", "Mom", "girl", delay=1),
    StoryParams("cellar", "whisk", "climb", "grab_stool", "Nora", "girl", "Dad", "boy", delay=2),
]


def explain_rejection(obj: ObjectCfg, action: ActionCfg) -> str:
    return f"(No story: {obj.label} and {action.verb} do not make a plausible suspense beat here.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme suspense story world with a bad ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child-name")
    ap.add_argument("--helper-name")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--delay", type=int, choices=[0, 1, 2, 3], default=2)
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
    if args.object and args.action:
        if not reasonableness_gate(OBJECTS[args.object], ACTIONS[args.action]):
            raise StoryError(explain_rejection(OBJECTS[args.object], ACTIONS[args.action]))
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object is None or c[1] == args.object)
              and (args.action is None or c[2] == args.action)
              and (args.response is None or c[3] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj, action, response = rng.choice(sorted(combos))
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    helper_gender = args.helper_gender or "girl"
    helper_name = args.helper_name or ("Mom" if helper_gender == "girl" else "Dad")
    return StoryParams(setting, obj, action, response, child_name, child_gender, helper_name, helper_gender, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        OBJECTS[params.object],
        ACTIONS[params.action],
        RESPONSES[params.response],
        params.child_name,
        params.child_gender,
        params.helper_name,
        params.helper_gender,
        params.delay,
    )
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


ASP_RULES = r"""
suspense(C) :- child(C), worry(C), clock_slow.
bad_end :- suspense(C), not helped_in_time.
helped_in_time :- response(R), sense(R,S), sense_min(M), S >= M.
valid(S,O,A,R) :- setting(S), risky_object(O), action(A), response(R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        if o.risky:
            lines.append(asp.fact("risky_object", oid))
    for aid in ACTIONS:
        lines.append(asp.fact("action", aid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH in valid combos")
        rc = 1
    sample = generate(CURATED[0])
    if not sample.story or "hypothesis" not in sample.story or "whisk" not in sample.story:
        print("MISMATCH: story smoke test failed")
        rc = 1
    print("OK: verification smoke test completed.")
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("", "#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
        for c in combos:
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
