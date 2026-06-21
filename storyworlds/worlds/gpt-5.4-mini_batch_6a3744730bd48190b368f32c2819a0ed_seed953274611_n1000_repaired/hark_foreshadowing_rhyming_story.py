#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hark_foreshadowing_rhyming_story.py
===================================================================

A small standalone storyworld for a rhyming, foreshadowed tiny tale that
features the word "hark". The world simulates a child, a helper, a breezy day,
and a kite whose fate depends on what the characters notice before the wind
changes.

The story is intentionally compact:
- a bright setup,
- a foreshadowed warning,
- a small turn,
- a safe resolution.

The prose engine is state-driven: meters and memes change as the scene unfolds,
and the ending image reflects the final world state rather than a frozen script.
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
BRISK_WIND = 2.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

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
        return self.label or self.type
    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class Scene:
    place: str
    sky: str
    bright_start: str
    smell: str
    foreshadow_line: str
    closing_view: str
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


@dataclass
class ObjectCfg:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    tethered: bool = False
    gives_light: bool = False
    makes_sound: bool = False
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class ResponseCfg:
    id: str
    sense: int
    power: int
    text: str
    fail: str
    qa_text: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes


@dataclass
class StoryParams:
    scene: str
    object: str
    response: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags


def _r_wind_grows(world: World) -> list[str]:
    out: list[str] = []
    sky = world.get("sky")
    if sky.meters["wind"] < BRISK_WIND:
        return out
    sig = ("wind_grows",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kite = world.entities.get("kite")
    if kite:
        kite.meters["tug"] += 1
    child = world.entities.get("child")
    helper = world.entities.get("helper")
    if child:
        child.memes["worry"] += 1
    if helper:
        helper.memes["alert"] += 1
    out.append("__wind__")
    return out


def _r_tether_helps(world: World) -> list[str]:
    out: list[str] = []
    kite = world.entities.get("kite")
    if not kite:
        return out
    if kite.meters["tied"] < THRESHOLD:
        return out
    sig = ("tether_helps",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    kite.meters["safe"] += 1
    out.append("The string stayed snug, so the kite did not dash away.")
    return out


CAUSAL_RULES = [Rule("wind_grows", "weather", _r_wind_grows), Rule("tether_helps", "safety", _r_tether_helps)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
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


def hazard_at_risk(obj: ObjectCfg) -> bool:
    return obj.fragile and obj.tethered


def sensible_responses() -> list[ResponseCfg]:
    return [r for r in RESPONSES.values() if r.sense >= 2]


def choose_sky(scene: Scene) -> str:
    return scene.sky


def predict_break(world: World, obj_id: str) -> dict:
    sim = world.copy()
    obj = sim.get(obj_id)
    obj.meters["tied"] = 0.0
    sim.get("sky").meters["wind"] = 3.0
    propagate(sim, narrate=False)
    return {
        "safe": sim.get("kite").meters["safe"] >= THRESHOLD,
        "worry": sim.get("child").memes["worry"],
    }


def tell(scene: Scene, obj: ObjectCfg, response: ResponseCfg,
         child_name: str = "Mina", child_type: str = "girl",
         helper_name: str = "Papa", helper_type: str = "father") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_type, label=child_name, role="child"))
    helper = world.add(Entity(id="helper", kind="character", type=helper_type, label=helper_name, role="helper"))
    sky = world.add(Entity(id="sky", type="weather", label="the sky"))
    kite = world.add(Entity(id="kite", type="thing", label=obj.label, phrase=obj.phrase, plural=False))
    string = world.add(Entity(id="string", type="thing", label="string", phrase="a red string"))
    sky.meters["wind"] = 1.0

    child.memes["delight"] += 1
    helper.memes["calm"] += 1
    kite.meters["tied"] = 1.0

    world.say(
        f"{scene.bright_start} {child_name} and {helper_name} went out where the grass was green."
    )
    world.say(
        f"{scene.smell} drifted by, and the day felt like a song that could gleam."
    )
    world.say(
        f'"Hark," said {helper_name}, as a far cloud slid in. "{scene.foreshadow_line}"'
    )

    world.para()
    child.memes["curious"] += 1
    world.say(
        f"{child_name} saw the kite sway, and the line gave a tiny ping."
    )
    world.say(
        f'{child_name} said, "If the wind turns brisk, we should not let it spring."'
    )

    helper.memes["warning"] += 1
    world.say(
        f"{helper_name} knelt by the knot and checked the tug of the string."
    )

    if response.sense < 2:
        raise StoryError(f"(Refusing response '{response.id}': it is too weak for this scene.)")

    world.para()
    sky.meters["wind"] = 3.0
    child.memes["worry"] += 1
    world.say(
        f"Then the breeze grew bold, and the trees began to swing."
    )
    world.say(
        f'But {helper_name} {response.text.replace("{target}", obj.label)}.'
    )
    kite.meters["tied"] = 1.0
    propagate(world, narrate=True)
    world.say(
        f"The kite bobbed but stayed close, like a bright little king."
    )

    world.para()
    child.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{scene.closing_view}, and {child_name} laughed, " 
        f'"Hark! We kept our kite and our cheer in one ring."'
    )

    world.facts.update(
        child=child,
        helper=helper,
        sky=sky,
        kite=kite,
        string=string,
        scene=scene,
        obj=obj,
        response=response,
        worried=child.memes["worry"] >= THRESHOLD,
        tethered=kite.meters["tied"] >= THRESHOLD,
    )
    return world


SCENES = {
    "park": Scene(
        place="the park",
        sky="The sky was blue, but a silver cloud lurked at the rim",
        bright_start="At the park",
        smell="Fresh-cut clover",
        foreshadow_line="That cloud may bring a snap of wind before long.",
        closing_view="By sunset the cloud had drifted on",
    ),
    "hill": Scene(
        place="the hill",
        sky="The sky was clear, yet a gray line hid behind the sun",
        bright_start="On the hill",
        smell="Warm pine scents",
        foreshadow_line="A quick gust could come and make the kite sing.",
        closing_view="When the light turned gold, the last gust lost its sting",
    ),
    "field": Scene(
        place="the field",
        sky="The sky was wide, but a dark curl hid in the blue",
        bright_start="Out in the field",
        smell="Sweet grass and dust",
        foreshadow_line="That little dark curl looked ready to fling a wind-thing.",
        closing_view="As evening came, the air grew soft and slow",
    ),
}

OBJECTS = {
    "kite": ObjectCfg(
        id="kite",
        label="kite",
        phrase="a paper kite with blue and red stripes",
        fragile=True,
        tethered=True,
        tags={"kite", "wind"},
    ),
    "lantern": ObjectCfg(
        id="lantern",
        label="lantern",
        phrase="a tiny lantern",
        gives_light=True,
        tags={"light"},
    ),
}

RESPONSES = {
    "hold_fast": ResponseCfg(
        id="hold_fast",
        sense=3,
        power=4,
        text="held the string fast and tied a better knot",
        fail="held the string too loose, and the kite skittered away",
        qa_text="held the string fast and tied a better knot",
        tags={"knot"},
    ),
    "windbreak": ResponseCfg(
        id="windbreak",
        sense=3,
        power=3,
        text="guided the kite behind a low hedge until the gust passed",
        fail="tried the hedge, but the gust tugged harder than expected",
        qa_text="guided the kite behind a low hedge until the gust passed",
        tags={"hedge"},
    ),
    "basket": ResponseCfg(
        id="basket",
        sense=1,
        power=1,
        text="put the kite in a basket and hoped for the best",
        fail="put the kite in a basket, but the wind still snatched at it",
        qa_text="put the kite in a basket",
        tags={"basket"},
    ),
}

CURATED = [
    StoryParams(scene="park", object="kite", response="hold_fast", child_name="Mina", child_type="girl", helper_name="Papa", helper_type="father"),
    StoryParams(scene="hill", object="kite", response="windbreak", child_name="Nico", child_type="boy", helper_name="Mama", helper_type="mother"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SCENES:
        for o in OBJECTS:
            obj = OBJECTS[o]
            for r in sensible_responses():
                if hazard_at_risk(obj):
                    combos.append((s, o, r.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming tiny storyworld with foreshadowing and a harking warning.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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
    if args.object and args.object in OBJECTS and not hazard_at_risk(OBJECTS[args.object]):
        raise StoryError("That object does not create a good foreshadowed kite story.")
    combos = [c for c in valid_combos()
              if (args.scene is None or c[0] == args.scene)
              and (args.object is None or c[1] == args.object)
              and (args.response is None or c[2] == args.response)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    scene, obj, resp = rng.choice(sorted(combos))
    return StoryParams(
        scene=scene,
        object=obj,
        response=resp,
        child_name=args.name or rng.choice(["Mina", "Nico", "Luna", "Tari"]),
        child_type="girl" if (args.name in {"Mina", "Luna"} if args.name else rng.choice([True, False])) else "boy",
        helper_name=args.helper or rng.choice(["Mama", "Papa", "Auntie", "Uncle"]),
        helper_type="mother" if (args.helper in {"Mama", "Auntie"} if args.helper else rng.choice([True, False])) else "father",
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a rhyming story for a child that uses the word "hark" and hints '
        'that a gust is coming before the ending.',
        f"Tell a small foreshadowing story where {f['child'].label} and {f['helper'].label} "
        f"fly a {f['obj'].label} and the helper notices a warning in the sky.",
        f"Write a gentle, musical story where the line '{f['response'].qa_text}' helps keep the adventure safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, obj = f["child"], f["helper"], f["obj"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {child.label} and {helper.label}, who go out with a {obj.label}. The little scene is built around a warning that comes before the wind.",
        ),
        QAItem(
            question="What did the helper notice before the wind changed?",
            answer=f"{helper.label} noticed the sky first and said to hark, because a gust might come soon. That foreshadowing gave them time to act before the kite got away.",
        ),
        QAItem(
            question="How did they keep the kite safe?",
            answer=f"They {f['response'].qa_text}. That kept the string steady, so the kite stayed with them instead of racing into trouble.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"It ended with the kite still close and the children smiling in the fading light. The warning mattered, so the final picture is calm instead of sad.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does hark mean in a story?",
            answer="Hark is an old-fashioned word that means listen carefully. It is often used to call attention to something important that is about to happen.",
        ),
        QAItem(
            question="What is foreshadowing?",
            answer="Foreshadowing is when a story gives a small clue about what may happen later. It helps the ending feel prepared instead of sudden.",
        ),
        QAItem(
            question="Why does a kite need a string?",
            answer="A kite needs a string so it can stay with the person holding it. The string gives control when the wind gets stronger.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
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
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
scene(S) :- scene_fact(S).
obj(O) :- object_fact(O).
response(R) :- response_fact(R).
valid(S,O,R) :- scene(S), obj(O), response(R), fragile(O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SCENES:
        lines.append(asp.fact("scene_fact", sid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object_fact", oid))
        if obj.fragile:
            lines.append(asp.fact("fragile", oid))
    for rid in RESPONSES:
        lines.append(asp.fact("response_fact", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP gate does not match Python gate.")
        rc = 1
    try:
        sample = generate(CURATED[0])
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print("OK: ASP parity and generation smoke test passed.")
    return rc


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.object not in OBJECTS or params.response not in RESPONSES:
        raise StoryError("Invalid parameters.")
    world = tell(
        SCENES[params.scene],
        OBJECTS[params.object],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_type=params.child_type,
        helper_name=params.helper_name,
        helper_type=params.helper_type,
    )
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
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
