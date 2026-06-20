#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/art_ist_happy_ending_bad_ending_fable.py
==========================================================================

A standalone story world for a tiny fable-like domain about an art-ist who
wants to make a picture for the village.

Seed idea:
- include the word "art-ist"
- support both a Happy Ending and a Bad Ending
- keep the tone close to a fable: simple, concrete, and carrying a small moral

World premise:
A young art-ist wants to paint a picture for the village fair. A wiser helper
warns them about where and how to paint. If the art-ist chooses a proper canvas
and dries the paint well, the ending is happy. If they rush, paint on the wrong
surface, or ignore weather and cleanup, the picture is ruined and the lesson is
painful but clear.

The model is small on purpose: a few typed entities, meters for physical state,
memes for emotional state, a light forward rule engine, a reasonableness gate,
and an ASP twin for parity checks.
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
    traits: list[str] = field(default_factory=list)
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "artist"}
        male = {"boy", "father", "dad", "man", "king", "artist_boy"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Surface:
    id: str
    label: str
    phrase: str
    suited: bool
    durable: bool
    drips: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Medium:
    id: str
    label: str
    phrase: str
    wet: bool
    fast: bool
    messy: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    advice: str
    rescue: str
    qa_text: str
    sense: int
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
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_smear(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.meters["painted"] < THRESHOLD:
            continue
        sig = ("smear", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        surface_id = e.attrs.get("surface")
        if surface_id and surface_id in world.entities:
            surf = world.get(surface_id)
            if surf.attrs.get("outside"):
                surf.meters["weathered"] += 1
        out.append("__smear__")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    if world.facts.get("storm"):
        for e in world.entities.values():
            if e.role == "artist":
                e.memes["worry"] += 1
                out.append("__worry__")
    return out


CAUSAL_RULES = [Rule("smear", "physical", _r_smear), Rule("worry", "social", _r_worry)]


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


def sensible_helpers() -> list[Helper]:
    return [h for h in HELPERS.values() if h.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    if not sensible_helpers():
        return combos
    for sid, surf in SURFACES.items():
        for mid, med in MEDIUMS.items():
            if (surf.suited and med.wet) or (not surf.suited and med.messy):
                combos.append((sid, mid, "share"))
    return combos


def outcome_of(params: "StoryParams") -> str:
    if params.surface == "canvas" and params.medium in {"paint", "ink"} and not params.storm:
        return "happy"
    return "bad"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SURFACES.items():
        lines.append(asp.fact("surface", sid))
        if s.suited:
            lines.append(asp.fact("suited", sid))
        if s.durable:
            lines.append(asp.fact("durable", sid))
        if s.drips:
            lines.append(asp.fact("drips", sid))
    for mid, m in MEDIUMS.items():
        lines.append(asp.fact("medium", mid))
        if m.wet:
            lines.append(asp.fact("wet", mid))
        if m.fast:
            lines.append(asp.fact("fast", mid))
        if m.messy:
            lines.append(asp.fact("messy", mid))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        lines.append(asp.fact("sense", hid, h.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
good(S, M) :- suited(S), wet(M).
bad(S, M) :- not good(S, M), medium(M), surface(S).
sensible(H) :- helper(H), sense(H, X), sense_min(M), X >= M.
outcome(happy) :- chosen_surface(S), chosen_medium(M), good(S, M), not storm.
outcome(bad) :- chosen_surface(S), chosen_medium(M), (bad(S, M); storm).
"""


def asp_program(extra: str, show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1.\n#show outcome/1."))
    sens = sorted(r for (r,) in asp.atoms(model, "sensible"))
    if set(sens) != {h.id for h in sensible_helpers()}:
        print("MISMATCH: sensible helpers differ")
        return 1
    cases = [StoryParams("canvas", "paint", "Milo", "fox", "Aunt", "calm", False, 0)]
    cases += [resolve_params(argparse.Namespace(surface=None, medium=None, seed=None, name=None, kind=None, helper=None, storm=None), random.Random(s)) for s in range(5)]
    if any(outcome_of(p) != asp_outcome(p) for p in cases):
        print("MISMATCH: outcome parity failed")
        return 1
    try:
        sample = generate(cases[0])
        _ = sample.story
        print("OK: smoke generate succeeded.")
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    print("OK: ASP and Python parity verified.")
    return 0


def asp_outcome(params: "StoryParams") -> str:
    import asp
    scenario = "\n".join([
        asp.fact("chosen_surface", params.surface),
        asp.fact("chosen_medium", params.medium),
        asp.fact("storm", int(params.storm)),
    ])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def _render_surface(surf: Surface) -> str:
    return surf.phrase


def _render_medium(med: Medium) -> str:
    return med.phrase


def tell(surface: Surface, medium: Medium, helper: Helper, name: str, kind: str, storm: bool, delay: int) -> World:
    w = World()
    artist = w.add(Entity(id=name, kind="character", type=kind, role="artist", traits=["young", "hopeful"]))
    guide = w.add(Entity(id=helper.label, kind="character", type="woman", role="guide", label=helper.label))
    target = w.add(Entity(id="picture", type="thing", label=surface.label, attrs={"surface": "picture_surface"}))
    surface_ent = w.add(Entity(id="surface", type="thing", label=surface.label, attrs={"outside": storm, "surface": surface.id}))
    medium_ent = w.add(Entity(id="medium", type="thing", label=medium.label))
    w.facts["storm"] = storm

    artist.memes["hope"] += 1
    w.say(f"Once there was a young art-ist named {name} who wanted to make a picture for the village fair.")
    w.say(f"{name} had {medium.phrase} and dreamed of painting on {surface.phrase}.")
    w.say(f"{guide.label.capitalize()} the wise hedgehog watched and said, \"{helper.advice}\"")
    w.para()

    if surface.suited and medium.wet and not storm:
        artist.meters["painted"] += 1
        target.attrs["surface"] = surface.id
        target.meters["finished"] += 1
        w.say(f"{name} listened carefully and worked on the {surface.label} instead of the street.")
        w.say(f"By sunset, the picture shone bright and clean, and the village smiled at the good work.")
        w.say(f"{name} shared the colors with everyone, and the art made the whole fair feel kind.")
    else:
        artist.memes["pride"] += 1
        artist.meters["painted"] += 1
        target.attrs["surface"] = surface.id
        propagate(w, narrate=False)
        w.say(f"{name} did not listen and painted where the helper had warned not to paint.")
        if storm:
            w.say("Then clouds rolled in, rain tapped the ground, and the paint began to run like tears.")
        else:
            w.say("The wrong surface soaked up the paint, and the good picture turned blotchy and dull.")
        w.say(f"At last the village saw that a rushed picture can spoil a fine idea.")
    w.facts.update(artist=artist, guide=guide, surface=surface, medium=medium, delay=delay)
    return w


@dataclass
class StoryParams:
    surface: str
    medium: str
    name: str
    kind: str
    helper: str
    mood: str
    storm: bool
    delay: int = 0
    seed: Optional[int] = None


SURFACES = {
    "canvas": Surface("canvas", "a blank canvas", "a blank canvas on a wooden frame", True, True, False, {"art"}),
    "wall": Surface("wall", "the village wall", "the village wall by the square", False, True, True, {"art"}),
    "stone": Surface("stone", "a smooth stone", "a smooth stone near the fountain", True, True, False, {"art"}),
}

MEDIUMS = {
    "paint": Medium("paint", "paint", "bright paint", True, False, True, {"art"}),
    "ink": Medium("ink", "ink", "dark ink", True, False, True, {"art"}),
    "charcoal": Medium("charcoal", "charcoal", "soft charcoal", False, True, False, {"art"}),
    "mud": Medium("mud", "mud", "muddy finger paint", False, False, True, {"art"}),
}

HELPERS = {
    "Aunt": Helper("aunt", "Aunt Fern", "Paint on the canvas, dear art-ist. The wall is for notices, not pictures.", "helped dry the canvas under a cloth", "She told the art-ist to use the canvas and not the wall.", 3, {"calm"}),
    "Bee": Helper("bee", "Bee Bramble", "If rain is coming, finish quickly on a proper canvas and bring it inside.", "helped carry the canvas under the eaves", "The bee was wise about the weather and the right place to paint.", 2, {"wise"}),
    "Fox": Helper("fox", "Fox Glen", "A picture needs a kind surface, not a busy street.", "pointed to the canvas and waited", "The fox spoke like a fable helper and warned about the wrong place.", 1, {"clever"}),
}

NAMES = ["Mira", "Pip", "Lena", "Ravi", "Nia", "Tomas"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny fable world about an art-ist and the choice between a happy ending and a bad ending.")
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--medium", choices=MEDIUMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=["girl", "boy", "fox", "rabbit"])
    ap.add_argument("--storm", action="store_true")
    ap.add_argument("--delay", type=int, default=0)
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
    if args.surface and args.medium:
        s, m = SURFACES[args.surface], MEDIUMS[args.medium]
        if not ((s.suited and m.wet) or (not s.suited and m.messy)):
            raise StoryError("That surface and medium do not make a fair fable.")
    combos = [c for c in valid_combos()
              if (args.surface is None or c[0] == args.surface)
              and (args.medium is None or c[1] == args.medium)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    surf, med, _ = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    name = args.name or rng.choice(NAMES)
    kind = args.kind or rng.choice(["girl", "boy", "fox", "rabbit"])
    storm = bool(args.storm) if hasattr(args, "storm") and args.storm else rng.choice([False, True])
    return StoryParams(surf, med, name, kind, helper, "calm", storm, args.delay)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story that includes the word "art-ist" and ends either happily or badly depending on the choice of surface and weather.',
        f"Tell a simple moral story about {f['artist'].id} the art-ist, a helper who gives wise advice, and a picture that is either finished well or ruined by rain.",
        f"Write a child-friendly fable where a young art-ist learns that a proper canvas makes a happy ending, but the wrong place or a storm can lead to a bad ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    artist = f["artist"]
    helper = f["guide"]
    surface = f["surface"]
    medium = f["medium"]
    storm = f["storm"]
    if surface.id == "canvas" and medium.id in {"paint", "ink"} and not storm:
        ans1 = f"{artist.id} listened to {helper.label} and used the canvas, so the picture finished bright and neat. The good choice kept the art safe and gave the village a happy ending."
        ans2 = "Yes. The art-ist finished the picture and the fair ended with smiles."
    else:
        ans1 = f"{artist.id} did not follow the warning, and the wrong surface made the picture go bad. If rain came, it washed the colors away; if not, the picture still turned blotchy and weak."
        ans2 = "No. The picture was spoiled, and the ending was bad."
    return [
        QAItem("What did the art-ist want to make?", f"The art-ist wanted to make a picture for the village fair."),
        QAItem("What did the helper warn about?", f"{helper.label.capitalize()} warned that the art-ist should use a proper surface and not rush the work."),
        QAItem("Why did the story end happily or badly?", ans1),
        QAItem("Did the art-ist finish the picture well?", ans2),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a canvas?", "A canvas is a strong cloth surface that artists paint on. It is made for pictures."),
        QAItem("Why can rain ruin wet paint?", "Rain can wash wet paint away before it dries, so the colors run and the picture gets spoiled."),
        QAItem("What does a wise helper do in a fable?", "A wise helper gives advice that helps the main character make a better choice. That is one way a fable teaches a lesson."),
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
        if e.attrs:
            attrs = {k: v for k, v in e.attrs.items() if v}
            if attrs:
                bits.append(f"attrs={attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("canvas", "paint", "Mira", "girl", "Aunt", "calm", False, 0),
    StoryParams("wall", "paint", "Pip", "boy", "Fox", "fox", True, 1),
    StoryParams("stone", "ink", "Lena", "girl", "Bee", "wise", False, 0),
    StoryParams("wall", "mud", "Ravi", "boy", "Aunt", "calm", False, 0),
]


def tell(surface: Surface, medium: Medium, helper: Helper, name: str, kind: str, storm: bool, delay: int) -> World:
    w = World()
    artist = w.add(Entity(id=name, kind="character", type=kind, role="artist", traits=["young", "hopeful"]))
    guide = w.add(Entity(id=helper.label, kind="character", type="woman", role="guide", label=helper.label))
    surf = w.add(Entity(id=surface.label, type="thing", label=surface.label, attrs={"outside": storm}))
    med = w.add(Entity(id=medium.label, type="thing", label=medium.label))
    w.facts["storm"] = storm

    w.say(f"Once there was a young art-ist named {name} who wanted to make a picture for the village fair.")
    w.say(f"{name} had {medium.phrase} and dreamed of painting on {surface.phrase}.")
    w.say(f"{helper.label.capitalize()} the wise helper said, \"{helper.advice}\"")
    w.para()
    if surface.suited and medium.wet and not storm:
        artist.meters["painted"] += 1
        surf.meters["finished"] += 1
        med.meters["used"] += 1
        w.say(f"{name} listened and used the canvas, so the colors stayed bright and neat.")
        w.say("By evening the picture was finished, and the village praised the careful art-ist.")
        w.say("The helper smiled, and the little fable ended with a happy fair.")
    else:
        artist.meters["painted"] += 1
        artist.memes["pride"] += 1
        surf.meters["ruined"] += 1
        if storm:
            surf.meters["wet"] += 1
            w.say("The clouds opened up, rain fell, and the wet paint began to run.")
        else:
            w.say("The wrong surface drank the colors, and the picture looked messy and dull.")
        w.say("At last the art-ist saw that rushing and bragging can spoil a good idea.")
        w.say("So the ending was bad, but the lesson was clear.")
    w.facts.update(artist=artist, guide=guide, surface=surface, medium=medium, delay=delay)
    return w


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import asp
    model = asp.one_model(asp_program("", "#show sensible/1."))
    return sorted(h for (h,) in asp.atoms(model, "sensible"))


def asp_outcome(params: StoryParams) -> str:
    import asp
    scenario = "\n".join([asp.fact("chosen_surface", params.surface), asp.fact("chosen_medium", params.medium), asp.fact("storm", int(params.storm))])
    model = asp.one_model(asp_program(scenario, "#show outcome/1."))
    atoms = asp.atoms(model, "outcome")
    return atoms[0][0] if atoms else "?"


def asp_verify() -> int:
    rc = 0
    if set(asp_sensible()) != {h.id for h in sensible_helpers()}:
        print("MISMATCH: sensible helper gate")
        rc = 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: valid combo gate")
        rc = 1
    sample_params = CURATED[0]
    try:
        sample = generate(sample_params)
        _ = sample.story
        print("OK: smoke generate succeeded.")
    except Exception as exc:
        print(f"SMOKE FAIL: {exc}")
        return 1
    if any(asp_outcome(p) != outcome_of(p) for p in CURATED):
        print("MISMATCH: outcome parity")
        rc = 1
    else:
        print("OK: ASP and Python parity verified.")
    return rc


def explain_rejection(surface: Surface, medium: Medium) -> str:
    if surface.suited and not medium.wet and medium.id != "charcoal":
        return f"(No story: {medium.label} does not make the kind of picture this surface wants.)"
    if not surface.suited and medium.wet:
        return f"(No story: {surface.label} is the wrong kind of place for wet paint in this fable.)"
    return "(No story: this combination does not give a clean fable turn.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable story world about an art-ist and two possible endings.")
    ap.add_argument("--surface", choices=SURFACES)
    ap.add_argument("--medium", choices=MEDIUMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=["girl", "boy", "fox", "rabbit"])
    ap.add_argument("--storm", action="store_true")
    ap.add_argument("--delay", type=int, default=0)
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
    if args.surface and args.medium:
        if not ((SURFACES[args.surface].suited and MEDIUMS[args.medium].wet) or (not SURFACES[args.surface].suited and MEDIUMS[args.medium].messy)):
            raise StoryError(explain_rejection(SURFACES[args.surface], MEDIUMS[args.medium]))
    combos = [c for c in valid_combos() if (args.surface is None or c[0] == args.surface) and (args.medium is None or c[1] == args.medium)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    surf, med, _ = rng.choice(sorted(combos))
    helper = args.helper or rng.choice(sorted(HELPERS))
    name = args.name or rng.choice(NAMES)
    kind = args.kind or rng.choice(["girl", "boy", "fox", "rabbit"])
    storm = bool(args.storm) if args.storm else rng.choice([False, True])
    return StoryParams(surf, med, name, kind, helper, "calm", storm, args.delay)


def generate(params: StoryParams) -> StorySample:
    world = tell(SURFACES[params.surface], MEDIUMS[params.medium], HELPERS[params.helper], params.name, params.kind, params.storm, params.delay)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q.question, answer=q.answer) for q in story_qa(world)],
        world_qa=[QAItem(question=q.question, answer=q.answer) for q in world_knowledge_qa(world)],
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
        print(asp_program("", "#show valid/3.\n#show sensible/1.\n#show outcome/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible helpers: {', '.join(asp_sensible())}")
        print(f"{len(asp_valid_combos())} compatible combos:")
        for surf, med, _ in asp_valid_combos():
            print(f"  {surf:8} {med}")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
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
            s = generate(params)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
