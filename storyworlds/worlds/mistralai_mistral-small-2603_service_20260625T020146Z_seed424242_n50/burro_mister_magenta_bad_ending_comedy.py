#!/usr/bin/env python3
"""
storyworlds/worlds/burro_mister_magenta_bad_ending_comedy.py
===============================================================

A small simulated story domain built from the seed words "burro, mister, magenta"
with a comedic, bad-ending style.  This world models a gentleman (mister) trying
to introduce order through color/magic/magenta, whose project is hilariously
undermined by a playful burro, ending in an unexpectedly messy finale.
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
from results import QAItem, StoryError, StorySample
try:
    import asp
except ImportError:
    asp = None  # type: ignore

# ---------------------------------------------------------------------------
# Enumerations and thresholds
# ---------------------------------------------------------------------------
SETTINGS = {"garden", "workshop", "patio", "stable"}

ACTIVITIES = {
    "splash": "paint with magenta goop",
    "dye": "dip fabric in magenta dye",
}

PROPS = {
    "paint": {"color": "magenta"},
    "coat": {"color": "ivory"},
    "ribbon": {"color": "magenta", "band": True},
    "blanket": {"color": "golden"},
    "trough": {"color": "muddy", "material": "wood"},
}

NAMES_MISTER = ["Mr. Harlan", "Sir Ernest", "Professor Felix",
                "Lord Juniper", "Count Basil"]
NAMES_BURRO = ["Burrito", "Carrot", "Cinnamon", "Tango", "Marmalade"]

THRESHOLD = 0.75
COLORS = {"magenta", "ivory", "golden", "muddy"}
REGIONS = {"feet", "body", "trough"}
GEAR_TYPES = {"hat", "apron", "gloves"}

# ---------------------------------------------------------------------------
# Entities: characters plus props
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = ""
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    protector: Optional[str] = None
    region: str = ""
    mess: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"admired", "beauty", "dame"}
        male = {"gentleman", "professor", "count", "mister", "sir"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

# ---------------------------------------------------------------------------
# World: entity store + narration history
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.color_chain: list[str] = []

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.color_chain = list(self.color_chain)
        clone.paragraphs = [[]]
        return clone

# ---------------------------------------------------------------------------
# Causal rules (forward-chaining) for comedic escalation → messy catastrophe
# ---------------------------------------------------------------------------
@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]

def _r_interfere_with_paint(world: World) -> list[str]:
    """Burro blunders into painting gear, smearing magenta."""
    out: list[str] = []
    for burro in [e for e in world.entities.values() if e.type == "burro"]:
        if burro.meters.get("speed", 0) < THRESHOLD:
            continue
        for thing in world.entities.values():
            if thing.owner != "mister" or thing.id.startswith("burro"):
                continue
            if "magenta" in thing.label.lower() and world.fired:
                continue
            burro.meters["interfere_attempts"] += 1
            if burro.meters["interfere_attempts"] >= 2:
                thing.meters["magenta"] = THRESHOLD + 1
                thing.mess = True
                sig = ("spill", thing.id, "magenta")
                if sig not in world.fired:
                    world.fired.add(sig)
                    out.append(
                        f"{burro.id.capitalize()} swung {burro.pronoun('possessive')} "
                        f"wild tail, flinging a splash of {thing.label.lstrip('the ')} "
                        f"over {world.get('mister').it()} and the garden path!"
                    )
    return out

def _r_magenta_cloud(world: World) -> list[str]:
    """Excess magenta pigment levitates into an airborne cloud."""
    total = sum(e.meters.get("magenta", 0) for e in world.entities.values())
    if total <= THRESHOLD * 3:
        return []
    sig = ("cloud", "magenta")
    if sig in world.fired:
        return []
    world.fired.add(sig)
    world.entities["atmosphere"] = Entity(
        id="atmosphere", kind="cloud", label="a thick cloud",
        mess=True,
    )
    return [
        "An other-worldly magenta mist began swirling above the garden, "
        "glittering in the afternoon light."
    ]

def _r_burro_decoration(world: World) -> list[str]:
    """Burro ends up decorated in absorbed pigments."""
    if world.fired:
        burro = world.get("burro")
        mister = world.get("mister")
        load = sum(e.meters.get("magenta", 0) for e in world.entities.values())
        if load >= THRESHOLD * 4 and "costume" not in {e.id for e in world.entities.values()}:
            sig = ("costume", "burro")
            if sig not in world.fired:
                world.fired.add(sig)
                burro.meters["decoration_score"] = load
                return [
                    f"{burro.id} started to glow an accidental {burro.pronoun('possessive')} "
                    f"coat turned every stray spot of magenta into a shimmering shield "
                    f"covering {burro.it()}."
                ]
    return []

def _r_bad_ending(world: World) -> list[str]:
    """Narrate the climactic comedy failure (bad ending)."""
    if not world.fired:
        return []
    mister = world.get("mister")
    burro = world.get("burro")
    load = sum(e.meters.get("magenta", 0) for e in world.entities.values())
    if load >= THRESHOLD * 5:
        world.facts["ending_ruin"] = "magenta_overload"
        world.say(
            f"Then, tragedy struck: the floating magenta cloud descended, "
            f"coating {mister.id} in a dripping, sticky {burro.pronoun('possessive')} "
            f"accident-fortune.  Sir Ernest stood there, speechless, "
            f"as the realization sank in that today’s project had been a"
            f" magenta *catastrophe*."
        )
        return ["__bad_ending__"]
    return []

CAUSAL_RULES = [
    Rule(name="interfere", tag="physical", apply=_r_interfere_with_paint),
    Rule(name="cloud",   tag="physical", apply=_r_magenta_cloud),
    Rule(name="costume", tag="physical", apply=_r_burro_decoration),
    Rule(name="ending",  tag="plot",     apply=_r_bad_ending),
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
                narrated = [s for s in sents if s != "__bad_ending__"]
                produced.extend(narrated)
    if narrate:
        for s in produced:
            world.say(s)
    return produced

# ---------------------------------------------------------------------------
# Script beats
# ---------------------------------------------------------------------------
def craft_introduction(world: World) -> None:
    mister = world.add(Entity(
        id="mister", kind="character", type="gentleman", label="the mister",
        phrase="a gentleman in crisp linen with a pocket watch chain glinting in the sun",
        traits=["orderly", "faithful"],
        region="body",
    ))
    burro = world.add(Entity(
        id="burro", kind="character", type="burro", label="the burro",
        phrase="a sturdy burro with mischief in each twitching ear",
        traits=["playful", "restless"],
    ))
    world.facts.update(mister=mister.id, burro=burro.id)

def values_magenta(world: World, mister: Entity) -> None:
    mister.memes["color_love"] += 1
    world.say(
        f"{mister.id} believed every disorder could be cured by the right "
        f"shade of magenta. 'Order,’ he’d mutter, ‘is merely color deferred.’"
    )

def select_prop(world: World, mister: Entity) -> Entity:
    """Choose a prop that *should* be magenta."""
    opts = [p for p in PROPS.values() if p.get("color") == "magenta"]
    opt = random.choice(opts) if opts else next(iter(PROPS.values()))
    e = world.add(Entity(
        id="prop", kind="thing", type=opt.get("material", "fabric"),
        label=opt.get("color", "colored") + " " + opt.get("band", ""),
        phrase=f"the {opt.get('color', '')} {world.setting} prop",
        mess=False,
    ))
    return e

def wishes_to_apply(world: World, mister: Entity, prop: Entity) -> None:
    mister.memes["plan"] += 1
    world.say(
        f"{mister.id} reached {mister.pronoun('possessive')} brush toward "
        f"{prop.label}, murmuring about perfecting today’s hue."
    )

def burro_observes(world: World, burro: Entity, mister: Entity) -> None:
    burro.memes["curiosity"] += 0.5
    world.say(
        f"{burro.id} flicked an ear and watched {mister.pronoun('possessive')} "
        f"nectar of creation transform plain linen into a bold statement."
    )

def decides_to_sample(world: World, burro: Entity) -> None:
    burro.memes["appetite"] += 1
    world.say(
        f"{burro.id} decided, quietly, that whatever {mister.id} "
        f"was fussing over might just taste suspiciously interesting."
    )

def burro_interferes(world: World, burro: Entity, mister: Entity, prop: Entity) -> None:
    burro.memes["chaos"] += 1
    world.para()
    world.say(
        f"As {mister.id} leaned close, {burro.id} suddenly lunged—"
        f"{burro.it()} tried to nibble the {prop.label}."
    )
    burro.meters["speed"] += 1
    prop.meters["magenta"] += 0.3
    world.say(
        f"{burro.pronoun().capitalize()} muzzle left a streak of {prop.label} "
        f"across {mister.pronoun('possessive')} sleeve and the garden wall alike!"
    )

def messages_state(world: World, mister: Entity) -> None:
    world.say(
        f"{mister.id} froze: chaos—magenta chaos—was literally "
        f"smeared across a previously *pristine* narrative."
    )

def inglorious_climax(world: World) -> None:
    rule_out = world.get("prop")
    load = sum(e.meters.get("magenta", 0) for e in world.entities.values())
    if load > THRESHOLD * 4:
        world.facts["bad_ending_reason"] = "excessive_magenta"
        world.para()
        world.say(
            "All at once the gathered light turned every surface—"
            "bench, book, bucket—into a glossy magenta slick. "
            "The garden, the path, the tiles; even "
            "{mister.pronoun('possessive')} pocket watch had surrendered to the hue."
        )
        world.say(
            f"Today’s endeavor had become the most famous accident in "
            "garden history—and not the kind that gets passed down "
            "happily over tea."
        )

# ---------------------------------------------------------------------------
# Parameters and registry helpers
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    activity: str
    prop_id: str
    mister_name: str
    burro_name: str
    prop_color: str = "magenta"

def choose_setting(rng: random.Random) -> str:
    return rng.choice(list(SETTINGS))

def choose_activity(rng: random.Random) -> str:
    acts = list(ACTIVITIES.keys())
    return rng.choice(acts)

def choose_prop_variant(rng: random.Random) -> str:
    props = list(PROPS.keys())
    return rng.choice(props)

def resolve_registries(args, rng) -> tuple:
    setting = args.setting or choose_setting(rng)
    activity = args.activity or choose_activity(rng)
    prop_id = args.prop or choose_prop_variant(rng)
    mister_name = args.mr or rng.choice(NAMES_MISTER)
    burro_name = args.burro or rng.choice(NAMES_BURRO)
    return setting, activity, prop_id, mister_name, burro_name

# ---------------------------------------------------------------------------
# Generation entry point: minimal three-act shape driven by the beats
# ---------------------------------------------------------------------------
def generate_story(params: StoryParams) -> World:
    world = World(params.setting)
    craft_introduction(world)
    mister = world.get("mister")
    burro = world.get("burro")

    # Act 1 – The color philosophy & prop
    world.para()
    values_magenta(world, mister)
    prop = select_prop(world, mister)
    wishes_to_apply(world, mister, prop)

    # Act 2 – Rising comedy of errors
    world.para()
    burro_observes(world, burro, mister)
    decides_to_sample(world, burro)
    burro_interferes(world, burro, mister, prop)
    messages_state(world, mister)

    # Act 3 – Bad ending
    inglorious_climax(world)

    # Facts for Q&A
    world.facts.update(
        mister=mister, burro=burro, prop=prop,
        ending=world.facts.pop("bad_ending_reason", "unknown")
    )
    return world

# ---------------------------------------------------------------------------
# Q&A generators (three tiers) – all child-facing, concrete, and grounded
# ---------------------------------------------------------------------------
KNOWLEDGE = {
    "magenta": [
        QAItem(
            question="What color is magenta?",
            answer=("Magenta is a bright purple-pink color made by mixing red and "
                   "blue light; painters and artists often reach for it when they "
                   "want to shout, ‘Look at me!’"),
        ),
    ],
    "burro": [
        QAItem(
            question="What does a burro do all day?",
            answer=("A burro spends sunny hours grazing, flicking away flies with "
                   "an ear, and occasionally sneaking a taste of something "
                   "brightly colored that looks tasty."),
        ),
    ],
    "gentleman": [
        QAItem(
            question="What does a gentleman do with brushes?",
            answer=("A gentleman with a paintbrush tries to turn even plain "
                   "patches—garden walls, coats, feelings—into something "
                   "more orderly, usually by adding exactly the right shade. "
                   "Sometimes life has other plans."),
        ),
    ],
}

STORY_QS = [
    QAItem(
        question="Who was in the garden trying to make order with a paintbrush?",
        answer="A gentleman named {mr} had decided the garden would be *perfect* "
              "if only everything were a precise shade of magenta.",
    ),
    QAItem(
        question="What animal suddenly became very interested in the paintbrush?",
        answer="A sturdy burro named {burro} arrived, flicked an ear, and "
              "decided {mister_pronoun} fussing was worth a taste test.",
    ),
    QAItem(
        question="How did the burro ruin the gentleman’s day?",
        answer=(
            "While {mr} leaned close with brush poised, {burro} lunged. "
            "A muzzle left a magenta streak across {mr_pronoun} sleeve, "
            "the wall, and the afternoon. Soon every surface "
            "turned to a glossy magenta slick—even the pocket watch!"
        ),
    ),
]

def prompts_for(world: World) -> list[str]:
    burro = world.facts["burro"]
    mister = world.facts["mister"]
    return [
        f"Write a short, hilarious three-paragraph story for 4-6-year-olds "
        "about a gentleman trying to bring perfect order to the garden using "
        f"{world.facts['prop_id']} and the color {world.facts['prop_color']}. "
        "Have a playful donkey (burro) make everything go wrong in an "
        "adorably messy way.",
        f"Compose a comedic micro tale starring {mister.label} and {burro.label} "
        "where a simple paint project explodes into a magical, uncontrolled "
        f"{world.facts['prop_color']} disaster ending with no clear way "
        "to fix the situation.",
        "Tell a funny story where a gentleman fails spectacularly at restoring "
        "order using paintbrushes only to discover a cheeky burro had "
        '"helped" by adding every available shade of pigment in town.',
    ]

def story_qa(world: World) -> list[QAItem]:
    burro = world.facts["burro"]
    mister = world.facts["mister"]
    end = world.facts.get("bad_ending_reason", "bad")
    qas = [q.format(
        mr=mister.id,
        burro=burro.id,
        mister_pronoun=mister.pronoun("possessive"),
        mister_it=mister.it(),
        burro_pronoun=burro.pronoun("possessive"),
    ) for q in STORY_QS]
    if end == "excessive_magenta":
        qas.append(QAItem(
            question="Why did today become the most famous accident in garden history?",
            answer=(
                "Because every surface—bench, book, bucket, and even "
                f"{mister.pronoun('possessive')} pocket watch—turned "
                "glossy magenta, leaving {mister.it()} speechless "
                "in a *catastrophe* of color."
            ),
        ))
    return qas

def world_qa(world: World) -> list[QAItem]:
    tag = world.facts.get("prop_color")
    if tag not in KNOWLEDGE:
        tag = "magenta"
    return KNOWLEDGE[tag]

# ---------------------------------------------------------------------------
# ASP twin – inline rules + registry facts emitted via asp_facts()
# ---------------------------------------------------------------------------
if asp is not None:
    ASP_RULES = r"""
    % Props that should be a specific color end up messy when the burro interferes
    should_be_color(P, C) :- prop(P), color(C), needs_color(P, C).
    creates_mess(P) :- should_be_color(P, C), magenta_load(T),
                       T >= 5 @ thresh(0.75).

    % Bad ending when magenta accumulates beyond the threshold
    bad_ending :- magenta_load(T), T >= 5 @ thresh(0.75).

    % --- setting facts split by variant ---
    garden_affords(dye).
    workshop_affords(paint).
    patio_affords(paint).
    stable_affords(paint).
    """

    def asp_facts() -> str:
        import asp
        lines: list[str] = []
        for s in SETTINGS:
            lines.append(asp.fact("setting", s))
            for a in ACTIVITIES:
                lines.append(asp.fact("affords", s, a))
        for p, cfg in PROPS.items():
            lines.append(asp.fact("prop", p))
            if cfg.get("color"):
                lines.append(asp.fact("color_prop", p, cfg["color"]))
        for c in COLORS:
            lines.append(asp.fact("color", c))
        lines.append(asp.fact("thresh", THRESHOLD))
        return "\n".join(lines)

    def asp_program(show: str = "") -> str:
        return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

    def asp_verify() -> int:
        try:
            python_combos = set()
            rules = ["affords(Place,Activity) :- setting(Place), activity(Activity).",
                     "needs_color(Prop,Color) :- prop(Prop), color(Color), color_prop(Prop,Color)."]
            prog = f"{asp_facts()}\n{' '.join(rules)}"
            model = asp.one_model(prog)
            return 0
        except Exception:
            return 1

# ---------------------------------------------------------------------------
# CLI & main
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy world with burro and mister causing magenta mayhem. "
                    "Unspecified options are randomized (seeded).")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prop", choices=list(PROPS))
    ap.add_argument("--mr", "--mister", dest="mr")
    ap.add_argument("--burro")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.verify:
        return StoryParams(setting="workshop", activity="paint", prop_id="paint",
                         mister_name="Mr. Harlan", burro_name="Burrito")
    vals = resolve_registries(args, rng)
    return StoryParams(setting=vals[0], activity=vals[1], prop_id=vals[2],
                     mister_name=vals[3], burro_name=vals[4])

def generate(params: StoryParams) -> StorySample:
    world = generate_story(params)
    sample = StorySample(
        params=params,
        story=world.render(),
        prompts=prompts_for(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )
    return sample

def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("\n---\nworld model state (selected)--")
        for eid, ent in sample.world.entities.items():
            ms = ent.meters.get("magenta", 0)
            if ms > 0:
                print(f"  {eid:8} magenta={ms:+.2f}  {ent.label}")
    if qa:
        print("\n== story Q&A ==")
        for q in sample.story_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")
        print("\n== world knowledge Q&A ==")
        for q in sample.world_qa:
            print(f"Q: {q.question}")
            print(f"A: {q.answer}")

def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show."))
        return
    if args.verify:
        sys.exit(asp_verify() if asp else 0)
    if args.asp:
        if not asp:
            print("clingo not available (--asp skipped)")
            return
        print("compatible (setting, activity, prop) triples via ASP:")
        print(asp_program("#show should_be_color/2, creates_mess/1."))
        return

    rng = random.Random(args.seed)
    base_seed = args.seed or rng.randrange(100, 5000)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in [
            StoryParams("garden", "dye", "coat", "Sir Ernest", "Cinnamon", "magenta"),
            StoryParams("workshop", "paint", "paint", "Professor Felix", "Tango", "magenta"),
            StoryParams("patio", "paint", "paint", "Lord Juniper", "Marmalade", "magenta"),
        ]]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 25, 100):
            seed = base_seed + i
            i += 1
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        prefix = ""
        if args.all:
            p = sample.params
            prefix = f"### {p.mister_name} & {p.burro_name}: {p.activity} in {p.setting}"
        elif len(samples) > 1:
            prefix = f"### variant {idx+1}"
        emit(sample, trace=args.trace, qa=args.qa, header=prefix)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")

if __name__ == "__main__":
    main()
