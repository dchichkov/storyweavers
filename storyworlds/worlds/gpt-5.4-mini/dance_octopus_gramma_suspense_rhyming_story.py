#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/dance_octopus_gramma_suspense_rhyming_story.py
===============================================================================

A small standalone story world for a suspenseful, rhyming, child-facing tale
about dance, an octopus, and gramma.

Premise
-------
A child prepares a little dance at home with gramma. A prized music box with an
octopus toy inside should stay closed, because opening it early would spoil the
surprise. Suspense comes from a wobbling lid, a creaky room, and the worry that
the surprise might be seen too soon. The calm turn is that gramma notices the
risk, helps steady the box, and guides the child to wait until the right moment.
The ending proves the change: the surprise stays hidden, then opens at last into
a happy dance.

This script follows the Storyweavers contract:
- typed entities with physical meters and emotional memes
- state-driven prose, not a swapped-noun template
- explicit invalid requests raise StoryError
- Python reasonableness gate plus inline ASP twin
- prompts, story QA, and world-knowledge QA from world state
- --verify runs parity checks and a smoke test
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "gramma", "grandma"}
        male = {"boy", "father", "dad", "man", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"gramma": "gramma", "grandma": "gramma", "mom": "mom", "dad": "dad"}.get(self.type, self.type)



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
    mood: str
    detail: str
    allowed: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
    phrase: str
    kind: str
    risky: bool
    hides: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
            value = __import__("collections").defaultdict(float)
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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
class Rule:
    name: str
    apply: Callable[[World], list[str]]

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(x for x in out if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _r_tense(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.memes["worry"] < THRESHOLD:
            continue
        sig = ("tense", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["suspense"] += 1
        out.append("__tense__")
    return out


def _r_steady(world: World) -> list[str]:
    out: list[str] = []
    box = world.entities.get("music_box")
    if not box or box.meters["shaking"] < THRESHOLD:
        return out
    sig = ("steady", "music_box")
    if sig in world.fired:
        return out
    world.fired.add(sig)
    box.meters["shaking"] = max(0.0, box.meters["shaking"] - 1.0)
    out.append("__steady__")
    return out


CAUSAL_RULES = [Rule("tense", _r_tense), Rule("steady", _r_steady)]


def object_at_risk(obj: ObjectCfg) -> bool:
    return obj.risky


def sensible_response_ids() -> list[str]:
    return [r.id for r in RESPONSES.values() if r.sense >= 2]


def is_reasonable(setting: Setting, obj: ObjectCfg, response: Response) -> bool:
    return object_at_risk(obj) and response.sense >= 2 and setting.id in SETTINGS


def best_response() -> Response:
    return max(RESPONSES.values(), key=lambda r: r.sense)


def predict(world: World, obj_id: str) -> dict:
    sim = world.copy()
    _jostle(sim, narrate=False)
    return {
        "shaking": sim.get(obj_id).meters["shaking"],
        "opened": sim.get(obj_id).meters.get("opened", 0.0),
    }


def _jostle(world: World, narrate: bool = True) -> None:
    box = world.get("music_box")
    box.meters["shaking"] += 1
    world.get("child").memes["worry"] += 1
    propagate(world, narrate=narrate)


def _open_box(world: World, narrate: bool = True) -> None:
    box = world.get("music_box")
    box.meters["opened"] += 1
    propagate(world, narrate=narrate)


def scene_setup(world: World, child: Entity, gramma: Entity, setting: Setting, obj: ObjectCfg) -> None:
    child.memes["joy"] += 1
    gramma.memes["calm"] += 1
    world.say(
        f"In {setting.place}, where {setting.mood} words could twirl, {child.id} and {gramma.id} "
        f"got ready to dance. {setting.detail}"
    )
    world.say(
        f"{child.id} held a little music box close, because inside it hid {obj.phrase}, "
        f"the octopus surprise they wanted to keep unseen."
    )


def suspense_beat(world: World, child: Entity, gramma: Entity, obj: ObjectCfg) -> None:
    pred = predict(world, "music_box")
    child.memes["worry"] += 1
    world.facts["predicted_shake"] = pred["shaking"]
    world.say(
        f"But the lid gave a tiny creak, and {child.id} went still. "
        f'"What if the box opens too soon?" {child.id} whispered.'
    )
    world.say(
        f'{gramma.id} put a hand on the lid. "{obj.hides} stay hidden till the song is sweet," '
        f"{gramma.pronoun()} said."
    )


def steady_and_wait(world: World, child: Entity, gramma: Entity, obj: ObjectCfg) -> None:
    gramma.memes["care"] += 1
    child.memes["trust"] += 1
    world.say(
        f"So {child.id} breathed slow as a boat on a bay, and {gramma.id} held the box steady. "
        f"The wobble quieted down, and the secret stayed snug inside."
    )


def dance_release(world: World, child: Entity, gramma: Entity, obj: ObjectCfg) -> None:
    _open_box(world, narrate=False)
    world.say(
        f"At last the right tune began to sway, and {child.id} opened the music box wide. "
        f"The little octopus popped up with a grin, and {child.id} and {gramma.id} spun into a dance."
    )
    world.say(
        f"They clapped and hopped, with {obj.label} shining bright, and the whole room felt light."
    )


def tell(setting: Setting, obj: ObjectCfg, response: Response, child_name: str, gramma_name: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type="boy", role="child"))
    gramma = world.add(Entity(id=gramma_name, kind="character", type="gramma", role="helper"))
    box = world.add(Entity(id="music_box", type="thing", label="music box"))
    toy = world.add(Entity(id="octopus_toy", type="octopus", label=obj.label))
    world.facts["obj"] = obj
    world.facts["response"] = response
    world.facts["setting"] = setting
    world.facts["child"] = child
    world.facts["gramma"] = gramma
    world.facts["toy"] = toy

    scene_setup(world, child, gramma, setting, obj)
    world.para()
    suspense_beat(world, child, gramma, obj)
    steady_and_wait(world, child, gramma, obj)
    world.para()
    dance_release(world, child, gramma, obj)

    world.facts.update(
        opened=box.meters["opened"] >= THRESHOLD,
        shaken=box.meters["shaking"] >= THRESHOLD,
        resolved=True,
    )
    return world


SETTINGS = {
    "parlor": Setting(
        id="parlor",
        place="the parlor",
        mood="gentle",
        detail="The lamp glowed low, and the rug held every soft step.",
        allowed={"dance"},
    ),
    "porch": Setting(
        id="porch",
        place="the front porch",
        mood="moonlit",
        detail="The night air hummed, and the porch boards knew every tiptoe.",
        allowed={"dance"},
    ),
    "kitchen": Setting(
        id="kitchen",
        place="the kitchen",
        mood="busy",
        detail="The chairs stood like listeners, and the clock kept time.",
        allowed={"dance"},
    ),
}

OBJECTS = {
    "music_box_octopus": ObjectCfg(
        id="music_box_octopus",
        label="octopus toy",
        phrase="an octopus toy with curly blue arms",
        kind="toy",
        risky=True,
        hides="little blue arms",
        tags={"octopus", "dance", "suspense"},
    ),
    "crown_octopus": ObjectCfg(
        id="crown_octopus",
        label="octopus toy",
        phrase="an octopus toy with a tiny paper crown",
        kind="toy",
        risky=True,
        hides="the crowned surprise",
        tags={"octopus", "dance", "suspense"},
    ),
}

RESPONSES = {
    "steady": Response(
        id="steady",
        sense=3,
        power=3,
        text="held the lid steady and kept the secret safe",
        fail="tried to hold the lid steady, but the little box wobbled open anyway",
        qa_text="held the lid steady and kept the secret safe",
        tags={"calm", "help"},
    ),
    "wait": Response(
        id="wait",
        sense=4,
        power=4,
        text="tapped the lid once and waited for the right song",
        fail="waited, but the box kept shaking in the child’s hands",
        qa_text="waited for the right song and kept the surprise hidden",
        tags={"calm", "help"},
    ),
    "gentle_touch": Response(
        id="gentle_touch",
        sense=2,
        power=2,
        text="used a gentle touch to settle the box",
        fail="used a gentle touch, but the lid still trembled",
        qa_text="used a gentle touch to settle the box",
        tags={"calm", "help"},
    ),
    "slam": Response(
        id="slam",
        sense=1,
        power=1,
        text="slam the lid shut",
        fail="slam the lid shut",
        qa_text="slam the lid shut",
        tags={"unsafe"},
    ),
}

CHILD_NAMES = ["Nina", "Milo", "June", "Arlo", "Penny", "Bea"]
GRAMMA_NAMES = ["Gramma Rose", "Gramma Joy", "Gramma June", "Gramma Mae"]


@dataclass
@dataclass
class StoryParams:
    setting: str
    object_id: str
    response: str
    child_name: str
    gramma_name: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for oid, o in OBJECTS.items():
            for rid, r in RESPONSES.items():
                if is_reasonable(s, o, r):
                    out.append((sid, oid, rid))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A suspenseful rhyming story world with dance, octopus, and gramma.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--gramma")
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
    if args.response and RESPONSES[args.response].sense < 2:
        raise StoryError("(No story: the chosen response is too silly for a suspenseful rescue.)")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.object_id is None or c[1] == args.object_id)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, object_id, response = rng.choice(sorted(combos))
    child_name = args.name or rng.choice(CHILD_NAMES)
    gramma_name = args.gramma or rng.choice(GRAMMA_NAMES)
    return StoryParams(setting, object_id, response, child_name, gramma_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], OBJECTS[params.object_id], RESPONSES[params.response],
                 params.child_name, params.gramma_name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a rhyming suspense story for a small child that includes the words "dance", "octopus", and "gramma".',
        f"Tell a gentle suspense story where {f['child'].id} and {f['gramma'].id} wait by a music box, keep an octopus surprise hidden, and end in a dance.",
        "Write a child-facing rhyme about a creaky little box, a calm gramma, and a happy reveal at the end.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child = f["child"]
    gramma = f["gramma"]
    obj = f["obj"]
    return [
        ("Who is the story about?",
         f"It is about {child.id} and {gramma.id}. They are the ones who prepare the surprise and keep the evening calm."),
        ("Why did the child feel suspense?",
         f"The music box gave a tiny creak, so {child.id} worried the surprise might open too soon. {gramma.id} noticed that worry and helped the child wait."),
        ("How did they solve the problem?",
         f"They held the box steady and waited for the right song. That kept {obj.label} hidden until it was time to dance."),
        ("How did the story end?",
         f"It ended with a happy dance after the octopus surprise came out safely. The waiting made the reveal feel extra sweet."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is dance?",
         "Dance is moving your body to music or a beat. It can be small and gentle or big and twirly."),
        ("What is an octopus?",
         "An octopus is a sea animal with eight arms. It can squirm and curl, which makes it look very funny."),
        ("Who is gramma?",
         "Gramma is a warm family word for a grandmother. She is often someone who helps, listens, and gives hugs."),
        ("What is suspense?",
         "Suspense is the nervous waiting feeling when you think something important might happen soon. It can make a story exciting without making it too scary."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


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
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for oid in OBJECTS:
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("risky", oid))
    for rid, r in RESPONSES.items():
        lines.append(asp.fact("response", rid))
        lines.append(asp.fact("sense", rid, r.sense))
        lines.append(asp.fact("power", rid, r.power))
    lines.append(asp.fact("sense_min", 2))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,O,R) :- setting(S), object(O), response(R), risky(O), sense(R,V), sense_min(M), V >= M.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(show="#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, object_id=None, response=None, name=None, gramma=None), random.Random(777)))
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: smoke test generated a story.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


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
    StoryParams("parlor", "music_box_octopus", "wait", "Milo", "Gramma Rose"),
    StoryParams("porch", "crown_octopus", "steady", "June", "Gramma Joy"),
    StoryParams("kitchen", "music_box_octopus", "gentle_touch", "Nina", "Gramma Mae"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program(show="#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
