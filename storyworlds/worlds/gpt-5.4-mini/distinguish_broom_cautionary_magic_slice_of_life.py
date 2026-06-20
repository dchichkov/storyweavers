#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/distinguish_broom_cautionary_magic_slice_of_life.py
===================================================================================

A standalone story world for a small slice-of-life cautionary magic tale:

- A child tidies a room.
- A magical broom seems helpful.
- The child must distinguish between ordinary cleaning and a spell that makes a mess.
- A gentle adult cautions them, the child corrects the mistake, and the room ends
  calmer and tidier than before.

The world is built from typed entities with physical meters and emotional memes.
State drives the prose, and the story always has a real beginning, middle turn,
and ending image.

Seed words: distinguish, broom
Features: cautionary, magic
Style: slice of life
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
from typing import Optional

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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad", "aunt": "aunt", "uncle": "uncle"}.get(self.type, self.type)



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
    cozy_detail: str
    afternoon_detail: str

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
class Tool:
    id: str
    label: str
    phrase: str
    magic: bool = False
    safe: bool = True
    tags: set[str] = field(default_factory=set)

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
class Mess:
    id: str
    label: str
    phrase: str
    makes: str
    cleanup: str
    spread: int = 1
    messy: bool = True
    tags: set[str] = field(default_factory=set)

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
class Response:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)

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

    def characters(self) -> list[Entity]:
        return [e for e in list(self.entities.values()) if e.kind == "character"]

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


SETTING = Setting("kitchen", "the kitchen", "sunlight on the table", "a kettle humming softly")
TOOLS = {
    "broom": Tool("broom", "broom", "a broom", magic=False, safe=True, tags={"broom", "clean"}),
    "sparkbroom": Tool("sparkbroom", "sparkly broom", "a sparkly broom", magic=True, safe=False, tags={"broom", "magic"}),
    "wand": Tool("wand", "wand", "a tiny wand", magic=True, safe=False, tags={"magic"}),
}
MESS = {
    "crumbs": Mess("crumbs", "crumbs", "crumbs", "scatter", "sweep", 1, True, {"clean"}),
    "glitter": Mess("glitter", "glitter", "glitter", "sprinkle", "sweep", 2, True, {"magic"}),
    "soapbubbles": Mess("soapbubbles", "soap bubbles", "soap bubbles", "bubble", "wipe", 1, True, {"magic"}),
}
RESPONSES = {
    "dustpan": Response("dustpan", 3, 3, "set the broom aside, found the dustpan, and swept the crumbs into a neat pile", "tried to clean up, but the mess only slid around", "set the broom aside and swept the crumbs into a neat pile", {"clean"}),
    "cloth": Response("cloth", 2, 2, "used a damp cloth to gather the glitter into one tidy corner", "wiped and wiped, but the glitter kept spreading", "used a damp cloth to gather the glitter into one tidy corner", {"clean"}),
    "pause": Response("pause", 2, 2, "paused, took a breath, and chose the plain broom instead", "waited too long and the room stayed messy", "paused and chose the plain broom instead", {"clean"}),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Ben"]
TRAITS = ["careful", "curious", "thoughtful", "gentle", "patient"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    tool: str
    mess: str
    response: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    trait: str
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


def hazard(tool: Tool, mess: Mess) -> bool:
    return tool.magic and mess.messy


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in [SETTING.id]:
        for tid, t in TOOLS.items():
            for mid, m in MESS.items():
                if hazard(t, m):
                    for rid, r in RESPONSES.items():
                        if r.sense >= SENSE_MIN:
                            combos.append((sid, tid, mid))
    return sorted(set(combos))


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", SETTING.id),
        asp.fact("safe", "broom"),
        asp.fact("magic_tool", "sparkbroom"),
        asp.fact("magic_tool", "wand"),
    ]
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.magic:
            lines.append(asp.fact("magic", tid))
    for mid, m in MESS.items():
        lines.append(asp.fact("mess", mid))
        if m.messy:
            lines.append(asp.fact("messy", mid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
hazard(T, M) :- magic(T), messy(M).
sensible(R) :- response(R), sense(R, S), sense_min(M), S >= M.
valid(S, T, M) :- setting(S), tool(T), mess(M), hazard(T, M), sensible(_).
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program(show="#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH in valid_combos().")
    if set(asp_sensible()) != {r.id for r in sensible_responses()}:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE FAIL: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def predict(world: World, tool_id: str, mess_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get("child"), TOOLS[tool_id], MESS[mess_id], narrate=False)
    return {
        "messy": sim.get("room").meters["messy"] >= THRESHOLD,
        "stress": sim.get("child").memes["stress"],
    }


def _do_action(world: World, child: Entity, tool: Tool, mess: Mess, narrate: bool = True) -> None:
    if tool.id not in world.facts["allowed_tools"]:
        return
    child.meters["tidying"] += 1
    if tool.magic:
        child.memes["wonder"] += 1
        child.meters["sparkles"] += 1
    if mess.id == "glitter" and tool.magic:
        world.get("room").meters["messy"] += 1
        child.meters["messy"] += 1
    else:
        world.get("room").meters["messy"] += mess.spread
    if narrate:
        propagate(world)


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    if world.get("room").meters["messy"] >= THRESHOLD and "mess" not in world.fired:
        world.fired.add(("mess",))
        world.get("child").memes["worry"] += 1
        produced.append("__mess__")
    if narrate:
        for s in produced:
            if not s.startswith("__"):
                world.say(s)
    return produced


def introduce(world: World, child: Entity) -> None:
    world.say(f"On a quiet afternoon, {child.id} stood in {SETTING.place} and noticed how the sunlight made every crumb easy to see.")


def temptation(world: World, child: Entity, tool: Tool) -> None:
    if tool.magic:
        world.say(f"{child.id} spotted {tool.phrase} by the wall. It looked helpful, and a little bit magical.")
    else:
        world.say(f"{child.id} picked up {tool.phrase} and felt ready to tidy the room.")


def caution(world: World, adult: Entity, child: Entity, tool: Tool, mess: Mess) -> None:
    child.memes["curiosity"] += 1
    world.facts["predicted"] = predict(world, tool.id, mess.id)
    world.say(f'"{child.id}," {adult.label_word} said gently, "you should distinguish between a helpful broom and a trick that only makes more sparkle."')


def choose_plain(world: World, child: Entity) -> None:
    child.memes["resolve"] += 1
    world.say(f"{child.id} blinked, nodded, and reached for the plain broom instead.")


def finish(world: World, child: Entity, adult: Entity, mess: Mess, response: Response) -> None:
    world.get("room").meters["messy"] = 0
    child.memes["relief"] += 1
    adult.memes["relief"] += 1
    body = response.qa_text
    world.say(f"{adult.label_word.capitalize()} smiled and {body}.")
    world.say(f"Soon the kitchen was calm again, with the broom leaning in the corner and the table shining in the afternoon light.")


def tell(tool: Tool, mess: Mess, response: Response, child_name: str, child_gender: str, adult_type: str, adult_gender: str, trait: str) -> World:
    world = World()
    child = world.add(Entity(child_name, "character", child_gender, role="child", traits=[trait]))
    adult = world.add(Entity("Parent", "character", adult_type, role="adult"))
    room = world.add(Entity("room", "room", "room", label="the room"))
    world.facts["allowed_tools"] = {"broom", "sparkbroom", "wand"}
    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["tool"] = tool
    world.facts["mess"] = mess
    world.facts["response"] = response
    introduce(world, child)
    world.para()
    temptation(world, child, tool)
    caution(world, adult, child, tool, mess)
    choose_plain(world, child)
    world.para()
    finish(world, child, adult, mess, response)
    world.facts["room"] = room
    world.facts["outcome"] = "clean"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a slice-of-life cautionary story that includes the words "distinguish" and "broom".',
        f"Tell a gentle story where {f['child'].id} learns to distinguish between a magical tool and a real broom while tidying a kitchen.",
        f"Write a small everyday story about a child, a broom, and a magical mistake that gets corrected calmly.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    adult = f["adult"]
    tool = f["tool"]
    mess = f["mess"]
    return [
        QAItem("What was the child doing?", f"{child.id} was tidying the kitchen on a quiet afternoon."),
        QAItem("What did the child need to distinguish?", f"{child.id} needed to distinguish between a magical broom trick and the plain broom that really cleans."),
        QAItem("What did the grown-up say?", f'{adult.label_word.capitalize()} said to distinguish between a helpful broom and a trick that only makes more sparkle.'),
        QAItem("How did the story end?", f"The room ended calm and clean, and {child.id} used the plain broom instead of the magical mistake."),
        QAItem("What would have happened if the magic had continued?", f"The {mess.label} would have spread more, so the tidy work would have taken longer."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a broom for?", "A broom is used for sweeping up crumbs and dust from the floor."),
        QAItem("What does distinguish mean?", "Distinguish means to tell one thing from another by noticing what makes each one different."),
        QAItem("Why can magic be tricky?", "Magic can be tricky because something that looks fun may do the wrong thing if you are not careful."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={dict(meters)}")
        if memes:
            parts.append(f"memes={dict(memes)}")
        if e.role:
            parts.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("kitchen", "sparkbroom", "glitter", "dustpan", "Mia", "girl", "mother", "mother", "careful"),
    StoryParams("kitchen", "wand", "soapbubbles", "cloth", "Eli", "boy", "father", "father", "thoughtful"),
    StoryParams("kitchen", "sparkbroom", "crumbs", "pause", "Nora", "girl", "aunt", "aunt", "gentle"),
]


def explain_rejection(tool: Tool, mess: Mess) -> str:
    return f"(No story: {tool.label} and {mess.label} do not make a cautionary magic problem that can be solved cleanly.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a small magical, cautionary slice-of-life tidying tale.")
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--mess", choices=MESS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--child")
    ap.add_argument("--adult", choices=["mother", "father", "aunt", "uncle"])
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
    combos = valid_combos()
    if args.tool and args.mess and not hazard(TOOLS[args.tool], MESS[args.mess]):
        raise StoryError(explain_rejection(TOOLS[args.tool], MESS[args.mess]))
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError("(No story: the chosen response is too weak to count as a sensible fix.)")
    tool = args.tool or rng.choice(sorted(TOOLS))
    mess = args.mess or rng.choice(sorted(MESS))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    if (SETTING.id, tool, mess) not in combos:
        if not hazard(TOOLS[tool], MESS[mess]):
            raise StoryError(explain_rejection(TOOLS[tool], MESS[mess]))
    gender = args.gender or rng.choice(["girl", "boy"])
    child = args.child or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    adult = args.adult or rng.choice(["mother", "father", "aunt", "uncle"])
    trait = rng.choice(TRAITS)
    return StoryParams(SETTING.id, tool, mess, response, child, gender, adult, "woman" if adult in {"mother", "aunt"} else "man", trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(TOOLS[params.tool], MESS[params.mess], RESPONSES[params.response], params.child, params.child_gender, params.adult, params.adult_gender, params.trait)
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
        print(asp_program(show="#show valid/3.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}")
        print()
        for item in asp_valid_combos():
            print(item)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            i += 1
            seed = base_seed + i
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
