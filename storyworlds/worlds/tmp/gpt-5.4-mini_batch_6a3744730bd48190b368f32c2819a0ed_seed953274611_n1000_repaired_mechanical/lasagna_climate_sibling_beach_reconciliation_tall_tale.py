#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/lasagna_climate_sibling_beach_reconciliation_tall_tale.py
========================================================================================

A tiny story world in a tall-tale mood: two siblings at the beach, a wild
argument about lasagna and the climate, and a reconciliation that ends with
a strange, sunny peace.

The world is intentionally small and state-driven:
- the beach has meters for warmth, wind, and salt spray;
- each sibling has meters and memes;
- a shared picnic basket, a lasagna pan, and a kite carry the action;
- the ending depends on whether the siblings cool down, share, and repair.

It supports the standard Storyweavers CLI contract, a reasonableness gate,
and an inline ASP twin.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
SIBLING_TRAITS = ["older", "younger", "brash", "patient", "sly", "gentle"]
WEATHER_WORDS = ["hot", "windy", "bright", "foggy", "breezy", "sticky"]


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    def __post_init__(self) -> None:
        self.meters = dict(self.meters)
        self.memes = dict(self.memes)

    def pronoun(self, case: str = "subject") -> str:
        gender = self.type
        if gender in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type
    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or getattr(self, "label_word", None) or getattr(self, "label", None) or getattr(self, "id", self.__class__.__name__.lower()))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)


@dataclass
class Place:
    id: str
    label: str
    scene: str
    heat: int
    wind: int
    salt: int
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    role: str
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
class ActionCfg:
    id: str
    verb: str
    boast: str
    effect: str
    risk: str
    repair: str
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
class ReconcileCfg:
    id: str
    method: str
    apology: str
    shared_move: str
    ending: str
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
    place: str
    action: str
    object: str
    sibling1: str
    sibling1_gender: str
    sibling2: str
    sibling2_gender: str
    climate: str
    reconcile: str
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def is_reasonable(place: Place, action: ActionCfg, obj: ObjectCfg) -> bool:
    return place.id == "beach" and {"beach", "reconcile"} <= (place.tags | action.tags | obj.tags)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for aid, action in ACTIONS.items():
            for oid, obj in OBJECTS.items():
                if is_reasonable(place, action, obj):
                    out.append((pid, aid, oid))
    return out


def _r_breeze(world: World) -> list[str]:
    out: list[str] = []
    beach = world.entities.get("beach")
    if not beach:
        return out
    if beach.meters.get("tension", 0.0) < THRESHOLD:
        return out
    sig = ("breeze",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    beach.meters["wind"] = beach.meters.get("wind", 0.0) + 1
    for e in list(world.entities.values()):
        if e.role in {"older", "younger"}:
            e.memes["stubborn"] = e.memes.get("stubborn", 0.0) + 0.5
    out.append("__breeze__")
    return out


def _r_cooldown(world: World) -> list[str]:
    out: list[str] = []
    beach = world.entities.get("beach")
    if not beach:
        return out
    if beach.meters.get("warmth", 0.0) < THRESHOLD:
        return out
    if beach.meters.get("sharing", 0.0) < THRESHOLD:
        return out
    sig = ("cooldown",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    beach.meters["warmth"] = max(0.0, beach.meters.get("warmth", 0.0) - 1)
    beach.meters["salt"] = beach.meters.get("salt", 0.0) + 1
    out.append("The sea air cooled the quarrel like a wet towel over a kettle.")
    return out


CAUSAL_RULES = [_r_breeze, _r_cooldown]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    sayings: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            res = rule(world)
            if res:
                changed = True
                sayings.extend(s for s in res if not s.startswith("__"))
    if narrate:
        for s in sayings:
            world.say(s)


def predict_tone(world: World) -> dict:
    sim = world.copy()
    sim.get("beach").meters["tension"] = sim.get("beach").meters.get("tension", 0.0) + 1
    propagate(sim, narrate=False)
    return {
        "wind": sim.get("beach").meters.get("wind", 0.0),
        "cool": sim.get("beach").meters.get("salt", 0.0),
    }


def tell(place: Place, action: ActionCfg, obj: ObjectCfg, reconcile: ReconcileCfg,
         sibling1: Entity, sibling2: Entity, climate: str) -> World:
    w = World()
    beach = w.add(Entity(id="beach", kind="place", type="place", label=place.label,
                         meters={"warmth": float(place.heat), "wind": float(place.wind),
                                 "salt": float(place.salt), "tension": 0.0, "sharing": 0.0},
                         tags=set(place.tags)))
    a = w.add(copy.deepcopy(sibling1))
    b = w.add(copy.deepcopy(sibling2))
    pan = w.add(Entity(id="lasagna", kind="object", type="object", label=obj.label,
                       attrs={"phrase": obj.phrase}, tags=set(obj.tags)))
    kite = w.add(Entity(id="kite", kind="object", type="object", label="kite",
                        tags={"beach", "climate"}))
    picnic = w.add(Entity(id="picnic", kind="object", type="object", label="picnic basket"))
    a.memes.setdefault("pride", 1.0)
    b.memes.setdefault("care", 1.0)

    w.say(
        f"At the beach, where the climate could turn from bright to wild in a blink, "
        f"{a.id} and {b.id} came walking under a sky as broad as a wagon road."
    )
    w.say(
        f"They had a picnic basket, a kite, and {obj.phrase}; "
        f"the whole day looked like a story trying to outgrow the shore."
    )
    w.say(
        f"{a.id} boasted, \"{action.boast} {obj.label} belongs with the sun and sand!\""
        f" {b.id} frowned and said the {action.effect} would only make matters worse."
    )
    w.para()
    w.say(
        f"That is when the argument began, as tall as a gull on a post. "
        f"{b.id} warned about the {action.risk}, and {a.id} would not listen."
    )
    a.memes["defiance"] = a.memes.get("defiance", 0.0) + 1
    b.memes["worry"] = b.memes.get("worry", 0.0) + 1
    beach.meters["tension"] += 1
    w.facts["tone"] = predict_tone(w)
    propagate(w, narrate=False)
    w.say(
        f"The wind tugged at the kite string, and even the seagulls seemed to wait "
        f"for the quarrel to finish."
    )
    w.para()

    if a.memes["defiance"] >= THRESHOLD:
        w.say(
            f"Then {b.id} took a deep breath, folded {b.pronoun('possessive')} arms, "
            f"and said, \"{reconcile.apology}\""
        )
        beach.meters["sharing"] += 1
        a.memes["soft"] = a.memes.get("soft", 0.0) + 1
        b.memes["soft"] = b.memes.get("soft", 0.0) + 1
        w.say(
            f"{a.id} looked down at the sand, then back at {b.id}, and the stubbornness "
            f"in {a.pronoun('possessive')} face melted like ice cream on a hot rail."
        )
        w.say(
            f"By sunset they chose {reconcile.shared_move}, because the beach had room "
            f"enough for two opinions and one happy plan."
        )
        beach.meters["sharing"] += 1
        propagate(w, narrate=True)
        w.para()
        w.say(
            f"After that, {reconcile.ending} with the lasagna safely shared, the kite flying "
            f"straight, and the siblings laughing so hard the gulls turned their heads."
        )
        w.facts["outcome"] = "reconciled"
    return w


PLACES = {
    "beach": Place(id="beach", label="the beach",
                   scene="a sunstruck shore", heat=3, wind=1, salt=1,
                   tags={"beach", "climate"}),
}

ACTIONS = {
    "heat_lasagna": ActionCfg(
        id="heat_lasagna",
        verb="heat up",
        boast="I can heat up",
        effect="hot lasagna on the beach",
        risk="the pan would get too warm and the cheese would slide",
        repair="cool it with shade and sea breeze",
        tags={"beach", "climate", "lasagna"},
    ),
    "bury_lasagna": ActionCfg(
        id="bury_lasagna",
        verb="bury",
        boast="I can bury",
        effect="lasagna in the sand",
        risk="sand would get all through the noodles",
        repair="brush it off and make a fresh tray",
        tags={"beach", "lasagna"},
    ),
}

OBJECTS = {
    "lasagna": ObjectCfg(id="lasagna", label="lasagna",
                         phrase="a pan of lasagna", role="food",
                         tags={"lasagna", "beach"}),
    "pan": ObjectCfg(id="pan", label="pan",
                     phrase="a big lasagna pan", role="tool",
                     tags={"lasagna", "beach"}),
}

RECONCILES = {
    "apology": ReconcileCfg(
        id="apology",
        method="say sorry",
        apology="I was as stubborn as a shovel in hard clay. Let's share the beach and the lasagna.",
        shared_move="sharing the lasagna under the umbrella",
        ending="They made peace at last",
        tags={"reconcile"},
    ),
}

GIRL_NAMES = ["Luna", "Mara", "Ivy", "Nina", "Zia"]
BOY_NAMES = ["Otis", "Bram", "Jude", "Poe", "Milo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale beach story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--reconcile", choices=RECONCILES)
    ap.add_argument("--climate", choices=WEATHER_WORDS)
    ap.add_argument("--sibling1")
    ap.add_argument("--sibling1-gender", choices=["girl", "boy"])
    ap.add_argument("--sibling2")
    ap.add_argument("--sibling2-gender", choices=["girl", "boy"])
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
    if args.place and args.place != "beach":
        raise StoryError("This tale only opens at the beach.")
    choices = valid_combos()
    if not choices:
        raise StoryError("No valid story combinations are available.")
    place, action, obj = rng.choice(choices)
    climate = args.climate or rng.choice(WEATHER_WORDS)
    s1g = args.sibling1_gender or rng.choice(["girl", "boy"])
    s2g = args.sibling2_gender or ("boy" if s1g == "girl" else "girl")
    s1 = args.sibling1 or rng.choice(GIRL_NAMES if s1g == "girl" else BOY_NAMES)
    s2 = args.sibling2 or rng.choice([n for n in (GIRL_NAMES if s2g == "girl" else BOY_NAMES) if n != s1])
    return StoryParams(place=place, action=action, object=obj, sibling1=s1, sibling1_gender=s1g,
                       sibling2=s2, sibling2_gender=s2g, climate=climate,
                       reconcile=args.reconcile or "apology")


def _make_entities(params: StoryParams) -> tuple[Entity, Entity]:
    return (
        Entity(id=params.sibling1, kind="character", type=params.sibling1_gender, role="older",
               traits=["sibling", "tall-tale"], attrs={"relation": "siblings"}),
        Entity(id=params.sibling2, kind="character", type=params.sibling2_gender, role="younger",
               traits=["sibling", "tall-tale"], attrs={"relation": "siblings"}),
    )


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.action not in ACTIONS or params.object not in OBJECTS or params.reconcile not in RECONCILES:
        raise StoryError("Invalid params.")
    place = PLACES[params.place]
    action = ACTIONS[params.action]
    obj = OBJECTS[params.object]
    rec = RECONCILES[params.reconcile]
    s1, s2 = _make_entities(params)
    world = tell(place, action, obj, rec, s1, s2, params.climate)
    story = world.render()
    prompts = [
        f"Write a tall-tale beach story that includes the words lasagna, climate, and sibling.",
        f"Tell a beach story where sibling trouble starts over lasagna, the climate turns dramatic, and the siblings reconcile.",
        f"Write a child-friendly story with a giant beach argument and a peaceful reconciliation over lasagna.",
    ]
    story_qa = [
        QAItem(
            question="Why did the siblings argue?",
            answer="They argued because one sibling wanted to treat lasagna like a beach-day stunt, and the other knew that the climate and sand would spoil it. The warning came from seeing how the beach conditions would change the food and the mood."
        ),
        QAItem(
            question="How did they make up?",
            answer="They made up by apologizing, cooling their tempers, and choosing to share the lasagna instead of fighting over it. That turned the same beach into a place for peace rather than a quarrel."
        ),
    ]
    world_qa = [
        QAItem(
            question="What does a beach climate often do?",
            answer="A beach climate can be windy, bright, salty, and changeable. That is why things can feel grand one minute and tricky the next."
        ),
        QAItem(
            question="Why is reconciliation helpful?",
            answer="Reconciliation helps people stop fighting and find a way to be kind again. It makes room for sharing, listening, and a better ending."
        ),
        QAItem(
            question="What is lasagna?",
            answer="Lasagna is a layered pasta dish baked in a pan. It is a meal, not a toy, so it belongs at the picnic, not in the sand."
        ),
    ]
    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for section, items in (("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)):
            print(f"== {section} ==")
            for item in items:
                if isinstance(item, QAItem):
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
                else:
                    print(item)
            print()


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(place, action, object) :- place(place), action(action), object(object), place(place), place_id(beach), beach(place).
reconcile_possible(R) :- reconcile(R), tags(R, reconcile).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if pid == "beach":
            lines.append(asp.fact("beach", pid))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tags", aid, t))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        for t in sorted(o.tags):
            lines.append(asp.fact("tags", oid, t))
    for rid, r in RECONCILES.items():
        lines.append(asp.fact("reconcile", rid))
        for t in sorted(r.tags):
            lines.append(asp.fact("tags", rid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    ok = True
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP gate matches Python gate.")
    else:
        ok = False
        print("MISMATCH: ASP gate differs from Python gate.")
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        ok = False
        print(f"FAIL: generate() smoke test crashed: {e}")
    return 0 if ok else 1


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [
            generate(StoryParams(place="beach", action="heat_lasagna", object="lasagna",
                                 sibling1="Mara", sibling1_gender="girl", sibling2="Otis",
                                 sibling2_gender="boy", climate="windy", reconcile="apology")),
            generate(StoryParams(place="beach", action="bury_lasagna", object="pan",
                                 sibling1="Luna", sibling1_gender="girl", sibling2="Milo",
                                 sibling2_gender="boy", climate="bright", reconcile="apology")),
        ]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
