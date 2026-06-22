#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T011547Z_seed2023889374_n10/nuisance_special_ize_conflict_bad_ending_rhyming.py
==============================================================================================================================

A tiny storyworld built from the seed prompt:

    Write a story that includes the following words and narrative instruments.
    Words: nuisance, special-ize
    Features: Conflict, Bad Ending
    Style: Rhyming Story

Premise:
A child tries to turn an ordinary market stall into a special-ized rhyme booth.
A noisy nuisance keeps interrupting the performance. The child's partner warns
that the booth is fragile, but the child pushes ahead anyway. The rhyme machine
gets knocked over, the special paint spills, and the booth is ruined. The ending
is sad: the booth is gone, the rhyme show stops, and the children leave with a
hard lesson.

The world is small on purpose:
- typed entities with physical meters and emotional memes
- a causal engine that turns state into prose
- a reasonableness gate
- an inline ASP twin
- three Q&A sets built from world state, not from the rendered story text
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Theme:
    id: str
    scene: str
    setup: str
    stage_name: str
    show_goal: str
    end_image: str


@dataclass
class Nuisance:
    id: str
    label: str
    sound: str
    poke: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Specializer:
    id: str
    label: str
    phrase: str
    dye: str
    tags: set[str] = field(default_factory=set)


@dataclass
class FragileThing:
    id: str
    label: str
    phrase: str
    break_phrase: str
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
    apply: Callable[[World], list[str]]


def _r_crash(world: World) -> list[str]:
    out: list[str] = []
    booth = world.entities.get("booth")
    paint = world.entities.get("paint")
    if booth is None or paint is None:
        return out
    if booth.meters["rocked"] < THRESHOLD:
        return out
    sig = ("crash",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    booth.meters["shaken"] += 1
    booth.meters["ruined"] += 1
    paint.meters["spilled"] += 1
    out.append("__crash__")
    return out


def _r_sad(world: World) -> list[str]:
    out: list[str] = []
    booth = world.entities.get("booth")
    child = world.entities.get("child")
    partner = world.entities.get("partner")
    if booth is None or child is None or partner is None:
        return out
    if booth.meters["ruined"] < THRESHOLD:
        return out
    sig = ("sad",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["sadness"] += 1
    partner.memes["worry"] += 1
    out.append("__sad__")
    return out


CAUSAL_RULES = [Rule("crash", _r_crash), Rule("sad", _r_sad)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            vals = rule.apply(world)
            if vals:
                changed = True
                produced.extend(v for v in vals if not v.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sensible_responses() -> list[Response]:
    return [r for r in RESPONSES.values() if r.sense >= SENSE_MIN]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for theme in THEMES:
        for nuisance in NUISANCES:
            for specializer in SPECIALIZERS:
                for fragile in FRAGILE_THINGS:
                    if nuisance.makes_a_mess and fragile.breakable and specializer.recovers:
                        combos.append((theme, nuisance.id, specializer.id, fragile.id))
    return combos


def reasonableness_check(params: "StoryParams") -> None:
    if params.response not in RESPONSES:
        raise StoryError("Unknown response choice.")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))


def predict_bad(world: World, child: Entity) -> dict:
    sim = world.copy()
    _attempt_specialize(sim, sim.get("child"), sim.get("partner"), sim.get("specializer"), sim.get("fragile"), narrate=False)
    return {
        "ruined": sim.get("booth").meters["ruined"] >= THRESHOLD,
        "sadness": sim.get("child").memes["sadness"],
    }


def _attempt_specialize(world: World, child: Entity, partner: Entity, specializer: Entity, fragile: Entity, narrate: bool = True) -> None:
    child.memes["pride"] += 1
    specializer.meters["painted"] += 1
    specializer.meters["ready"] += 1
    world.say(
        f"{child.id} tried to special-ize the little rhyme booth, "
        f"with {specializer.label_word} bright and neat."
    )
    world.say(
        f"But the booth was a nursery for words, and the work began to feel like a beat."
    )
    world.get("booth").meters["rocked"] += 1
    propagate(world, narrate=narrate)


def setup(world: World, theme: Theme, child: Entity, partner: Entity, nuisance: Entity, specializer: Entity, fragile: Entity) -> None:
    world.say(
        f"On a bright little day in {theme.scene}, {child.id} and {partner.id} "
        f"built {theme.setup}"
    )
    world.say(
        f"{theme.stage_name} had a sign that said {theme.show_goal}, and the plan "
        f"was made to sing and spin."
    )
    child.memes["joy"] += 1
    partner.memes["joy"] += 1
    nuisance.meters["noise"] += 1
    world.say(
        f"But a {nuisance.label} kept buzzing around with a {nuisance.sound}, "
        f"like a stubborn tin grin."
    )


def warn(world: World, partner: Entity, child: Entity, nuisance: Nuisance, fragile: FragileThing) -> None:
    partner.memes["caution"] += 1
    pred = predict_bad(world, child)
    world.facts["predicted"] = pred
    world.say(
        f'{partner.id} frowned and said, "{child.id}, that {nuisance.label} is a nuisance, '
        f'and {fragile.label} is far too light."'
    )
    world.say(
        f'"If we keep on like this, our sweet little show may not end in a sight."'
    )


def defy(world: World, child: Entity, nuisance: Nuisance) -> None:
    child.memes["defiance"] += 1
    world.say(
        f'"Not yet," said {child.id}, "I want it to shine and to special-ize right."'
    )
    world.say(
        f"So {child.id} kept on working, though {nuisance.label} kept hopping in sight."
    )


def crash(world: World, fragile: FragileThing) -> None:
    world.say(
        f"Then the booth gave a wobble and tipped with a thump; the special paint flew."
    )
    world.say(
        f"The words on the sign got muddy and bent, and the {fragile.label} split in two."
    )


def ending_bad(world: World, child: Entity, partner: Entity, theme: Theme) -> None:
    booth = world.get("booth")
    booth.meters["gone"] += 1
    child.memes["sadness"] += 1
    partner.memes["worry"] += 1
    world.say(
        f"The rhyme show went silent; no bright little chorus would start anew."
    )
    world.say(
        f"They walked home with drooping shoes, and the moon looked pale and blue."
    )
    world.say(
        f"{theme.end_image}"
    )


def tell(theme: Theme, nuisance: Nuisance, specializer: Specializer, fragile: FragileThing,
         response: Response, child_name: str = "Milo", child_gender: str = "boy",
         partner_name: str = "Nia", partner_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    partner = world.add(Entity(id=partner_name, kind="character", type=partner_gender, role="partner"))
    booth = world.add(Entity(id="booth", kind="thing", type="stall", label="rhyme booth"))
    spec = world.add(Entity(id="specializer", kind="thing", type="tool", label=specializer.label))
    paint = world.add(Entity(id="paint", kind="thing", type="thing", label="special paint"))
    nu = world.add(Entity(id="nuisance", kind="thing", type="thing", label=nuisance.label))
    frag = world.add(Entity(id="fragile", kind="thing", type="thing", label=fragile.label))

    world.facts.update(
        theme=theme,
        nuisance=nuisance,
        specializer=specializer,
        fragile=fragile,
        response=response,
        child=child,
        partner=partner,
        booth=booth,
        spec=spec,
        paint=paint,
        nu=nu,
        frag=frag,
    )

    setup(world, theme, child, partner, nuisance, specializer, fragile)
    world.para()
    warn(world, partner, child, nuisance, fragile)
    defy(world, child, nuisance)
    world.para()
    _attempt_specialize(world, child, partner, spec, frag)
    crash(world, fragile)
    world.para()
    ending_bad(world, child, partner, theme)

    world.facts["outcome"] = "bad"
    return world


@dataclass
class StoryParams:
    theme: str
    nuisance: str
    specializer: str
    fragile: str
    response: str
    child_name: str
    child_gender: str
    partner_name: str
    partner_gender: str
    seed: Optional[int] = None


THEMES = {
    "market": Theme(
        id="market",
        scene="a little market square",
        setup="a tiny rhyme booth from painted crates",
        stage_name="The Sign",
        show_goal="special-ize the rhyme booth",
        end_image="By dawn the booth was only splinters, but the lesson stayed.",
    ),
    "fair": Theme(
        id="fair",
        scene="a windy county fair",
        setup="a wobble-prone rhyme stand from old boards",
        stage_name="The Banner",
        show_goal="special-ize the rhyme stand",
        end_image="By dawn the stand was only scraps, but the lesson stayed.",
    ),
}

NUISANCES = {
    "bee": Nuisance(id="bee", label="bee", sound="bzz-bzz", poke="buzz", tags={"nuisance"}, makes_a_mess=False),
    "goat": Nuisance(id="goat", label="goat", sound="baaa-baa", poke="nudge", tags={"nuisance"}, makes_a_mess=True),
    "wind": Nuisance(id="wind", label="wind gust", sound="whoosh-woo", poke="buffet", tags={"nuisance"}, makes_a_mess=True),
}

SPECIALIZERS = {
    "paintbrush": Specializer(id="paintbrush", label="paintbrush", phrase="a bright paintbrush", dye="gold", tags={"special"}, recovers=True),
    "sticker": Specializer(id="sticker", label="sticker sheet", phrase="a sticker sheet", dye="sparkle", tags={"special"}, recovers=True),
}

FRAGILE_THINGS = {
    "sign": FragileThing(id="sign", label="sign", phrase="the rhyme sign", break_phrase="split in two", tags={"fragile"}),
    "bowl": FragileThing(id="bowl", label="glass bowl", phrase="the glass bowl", break_phrase="shattered apart", tags={"fragile"}),
}

RESPONSES = {
    "gentle": Response(id="gentle", sense=3, power=3, text="carefully steadied the booth and kept singing", fail="tried to steady it, but the wobble was too strong", qa_text="carefully steadied the booth and kept singing"),
    "skip": Response(id="skip", sense=1, power=1, text="ignored the wobble and kept going", fail="ignored the wobble and made things worse", qa_text="ignored the wobble and kept going"),
}

GIRL_NAMES = ["Nia", "Mina", "Luna", "Tia", "Sora"]
BOY_NAMES = ["Milo", "Otis", "Pip", "Rey", "Jules"]


def valid_choices() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming nuisance-and-special-ize storyworld.")
    ap.add_argument("--theme", choices=THEMES)
    ap.add_argument("--nuisance", choices=NUISANCES)
    ap.add_argument("--specializer", choices=SPECIALIZERS)
    ap.add_argument("--fragile", choices=FRAGILE_THINGS)
    ap.add_argument("--response", choices=RESPONSES)
    ap.add_argument("--name")
    ap.add_argument("--partner")
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
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = valid_combos()
    combos = [c for c in combos
              if (args.theme is None or c[0] == args.theme)
              and (args.nuisance is None or c[1] == args.nuisance)
              and (args.specializer is None or c[2] == args.specializer)
              and (args.fragile is None or c[3] == args.fragile)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, nuisance, specializer, fragile = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = "girl" if rng.random() < 0.5 else "boy"
    child_name = args.name or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    partner_gender = "girl" if child_gender == "boy" else "boy"
    partner_name = args.partner or rng.choice(GIRL_NAMES if partner_gender == "girl" else BOY_NAMES)
    return StoryParams(
        theme=theme,
        nuisance=nuisance,
        specializer=specializer,
        fragile=fragile,
        response=response,
        child_name=child_name,
        child_gender=child_gender,
        partner_name=partner_name,
        partner_gender=partner_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.theme not in THEMES:
        raise StoryError("Unknown theme.")
    if params.nuisance not in NUISANCES:
        raise StoryError("Unknown nuisance.")
    if params.specializer not in SPECIALIZERS:
        raise StoryError("Unknown specializer.")
    if params.fragile not in FRAGILE_THINGS:
        raise StoryError("Unknown fragile thing.")
    if params.response not in RESPONSES:
        raise StoryError("Unknown response.")
    if RESPONSES[params.response].sense < SENSE_MIN:
        raise StoryError(explain_response(params.response))
    world = tell(
        THEMES[params.theme],
        NUISANCES[params.nuisance],
        SPECIALIZERS[params.specializer],
        FRAGILE_THINGS[params.fragile],
        RESPONSES[params.response],
        child_name=params.child_name,
        child_gender=params.child_gender,
        partner_name=params.partner_name,
        partner_gender=params.partner_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a rhyming story for a young child that includes the words "nuisance" and "special-ize".',
        f"Tell a sad little rhyme story where {f['child'].id} tries to special-ize a booth, but a nuisance keeps causing trouble and the ending goes badly.",
        f"Write a conflict story with a bad ending in rhyme, where a booth, a nuisance, and a fragile thing all matter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    partner = f["partner"]
    nuisance = f["nuisance"]
    fragile = f["fragile"]
    return [
        QAItem(
            question=f"What did {child.id} try to do to the booth?",
            answer=f"{child.id} tried to special-ize the booth so the show would feel brighter and more fun. But that made the booth more delicate and easier for trouble to ruin.",
        ),
        QAItem(
            question=f"Why did {partner.id} warn {child.id} about the nuisance?",
            answer=f"{partner.id} warned {child.id} because the {nuisance.label} kept making a nuisance of itself. The noise and bumping could shake the fragile {fragile.label} apart.",
        ),
        QAItem(
            question=f"How did the story end after the booth got ruined?",
            answer="It ended badly. The rhyme show stopped, the booth was broken, and the children went home feeling sad.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a nuisance?",
            answer="A nuisance is something that keeps bothering everyone and makes it hard to work or play in peace.",
        ),
        QAItem(
            question="What does it mean to special-ize something?",
            answer="To special-ize something is to make it fit one special job or style, so it feels made for a certain purpose.",
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
        if e.attrs:
            shown = {k: v for k, v in e.attrs.items() if v}
            if shown:
                bits.append(f"attrs={shown}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        theme="market",
        nuisance="goat",
        specializer="paintbrush",
        fragile="sign",
        response="gentle",
        child_name="Milo",
        child_gender="boy",
        partner_name="Nia",
        partner_gender="girl",
    ),
    StoryParams(
        theme="fair",
        nuisance="wind",
        specializer="sticker",
        fragile="bowl",
        response="gentle",
        child_name="Lina",
        child_gender="girl",
        partner_name="Jude",
        partner_gender="boy",
    ),
]


ASP_RULES = r"""
valid(T,N,S,F) :- theme(T), nuisance(N), specializer(S), fragile(F), makes_mess(N), breakable(F), recovers(S).
sensible(R) :- response(R), sense(R,S), sense_min(M), S >= M.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for t in THEMES:
        lines.append(asp.fact("theme", t))
    for n in NUISANCES.values():
        lines.append(asp.fact("nuisance", n.id))
        if n.makes_a_mess:
            lines.append(asp.fact("makes_mess", n.id))
    for s in SPECIALIZERS.values():
        lines.append(asp.fact("specializer", s.id))
        if getattr(s, "recovers", False):
            lines.append(asp.fact("recovers", s.id))
    for f in FRAGILE_THINGS.values():
        lines.append(asp.fact("fragile", f.id))
        lines.append(asp.fact("breakable", f.id))
    for r in RESPONSES.values():
        lines.append(asp.fact("response", r.id))
        lines.append(asp.fact("sense", r.id, r.sense))
    lines.append(asp.fact("sense_min", SENSE_MIN))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_sensible() -> list[str]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show sensible/1."))
    return sorted(r for (r,) in asp.atoms(model, "sensible"))


def asp_verify() -> int:
    rc = 0
    if set(asp_valid_combos()) == set(valid_combos()):
        print(f"OK: clingo gate matches valid_combos() ({len(valid_combos())} combos).")
    else:
        rc = 1
        print("MISMATCH in valid_combos.")
    if set(asp_sensible()) == {r.id for r in sensible_responses()}:
        print("OK: sensible responses match.")
    else:
        rc = 1
        print("MISMATCH in sensible responses.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: story generation smoke test passed.")
    except Exception as exc:
        rc = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return rc


def explain_response(rid: str) -> str:
    r = RESPONSES[rid]
    return f"(Refusing response '{rid}': it scores too low on common sense (sense={r.sense} < {SENSE_MIN}).)"


def _pick_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def valid_story_params_filters(args: argparse.Namespace, rng: random.Random) -> list[tuple[str, str, str, str]]:
    combos = valid_combos()
    combos = [
        c for c in combos
        if (args.theme is None or c[0] == args.theme)
        and (args.nuisance is None or c[1] == args.nuisance)
        and (args.specializer is None or c[2] == args.specializer)
        and (args.fragile is None or c[3] == args.fragile)
    ]
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.response and RESPONSES[args.response].sense < SENSE_MIN:
        raise StoryError(explain_response(args.response))
    combos = valid_story_params_filters(args, rng)
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    theme, nuisance, specializer, fragile = rng.choice(sorted(combos))
    response = args.response or rng.choice(sorted(r.id for r in sensible_responses()))
    child_gender = "girl" if rng.random() < 0.5 else "boy"
    partner_gender = "boy" if child_gender == "girl" else "girl"
    return StoryParams(
        theme=theme,
        nuisance=nuisance,
        specializer=specializer,
        fragile=fragile,
        response=response,
        child_name=args.name or _pick_name(rng, child_gender),
        child_gender=child_gender,
        partner_name=args.partner or _pick_name(rng, partner_gender),
        partner_gender=partner_gender,
    )


def generate_story_from_params(params: StoryParams) -> StorySample:
    return generate(params)


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
        print(asp_program("#show valid/4.\n#show sensible/1."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"sensible responses: {', '.join(asp_sensible())}\n")
        for t, n, s, f in asp_valid_combos():
            print(f"  {t:8} {n:10} {s:12} {f}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate_story_from_params(p) for p in CURATED]
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
            sample = generate_story_from_params(params)
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
            header = f"### {p.child_name} in {p.theme} ({p.nuisance}, {p.specializer}, {p.fragile})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
