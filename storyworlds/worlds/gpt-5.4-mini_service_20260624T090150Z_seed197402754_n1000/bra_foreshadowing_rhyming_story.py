#!/usr/bin/env python3
"""
storyworlds/worlds/bra_foreshadowing_rhyming_story.py
======================================================

A small storyworld about a child, a first bra, and a foreshadowed fix,
told in a gentle rhyming-story style.

The premise:
- A growing child is getting dressed for a special day.
- A new bra seems promising, but a tiny clue hints it may not fit well.
- The child and parent notice the clue, try a softer alternative, and the
  day ends with comfort and confidence.

This file follows the Storyweavers world contract:
- self-contained stdlib script
- eager imports from storyworlds/results.py
- lazy import of storyworlds/asp.py inside ASP helpers
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    fit: str = ""
    color: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "shy": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)


@dataclass
class Underwear:
    id: str
    label: str
    phrase: str
    size: str
    fit: str
    style: str
    colors: set[str] = field(default_factory=set)
    soft: bool = False
    tags: set[str] = field(default_factory=set)


@dataclass
class Gear:
    id: str
    label: str
    phrase: str
    fit: str
    comfort: str
    covers: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    event: str
    under: str
    name: str
    gender: str
    parent: str
    trait: str
    color: str
    seed: Optional[int] = None


SETTINGS = {
    "bedroom": Setting(place="the bedroom", indoor=True, affords={"dress"}),
    "laundry": Setting(place="the laundry room", indoor=True, affords={"dress"}),
    "closet": Setting(place="the closet", indoor=True, affords={"dress"}),
}

EVENTS = {
    "dress": {
        "verb": "get dressed",
        "gerund": "getting dressed",
        "rush": "dash to the mirror",
        "moment": "the morning song",
        "tags": {"dress", "clothes"},
    }
}

UNDERWEAR = {
    "bra": Underwear(
        id="bra",
        label="bra",
        phrase="a soft little bra",
        size="small",
        fit="snug",
        style="plain",
        colors={"white", "pink", "blue", "lavender"},
        soft=False,
        tags={"bra", "clothes"},
    ),
    "training_bra": Underwear(
        id="training_bra",
        label="training bra",
        phrase="a soft training bra",
        size="small",
        fit="gentle",
        style="simple",
        colors={"white", "pink", "blue", "lavender"},
        soft=True,
        tags={"bra", "clothes", "soft"},
    ),
}

GEAR = [
    Gear(
        id="soft_pad",
        label="soft cotton pads",
        phrase="a pair of soft cotton pads",
        fit="gentle",
        comfort="cozy",
        covers={"chafe"},
        tags={"soft", "comfort"},
    ),
]


GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe", "Ella", "Ruby", "Iris"]
BOY_NAMES = ["Finn", "Noah", "Theo", "Leo", "Max", "Eli"]
TRAITS = ["cheerful", "curious", "shy", "brave", "bright", "gentle"]


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_chafe(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.type not in {"girl", "woman"}:
            continue
        if ent.memes.get("worry", 0.0) < THRESHOLD:
            continue
        if ent.meters.get("chafe", 0.0) >= THRESHOLD:
            continue
        sig = ("chafe", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["chafe"] = 1.0
        out.append(f"{ent.id} felt a tiny pinch that did not feel right.")
    return out


CAUSAL_RULES = [Rule("chafe", _r_chafe)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    if setting.place == "the bedroom":
        return "Sunlight lay in a stripe on the floor, and the dresser stood tidy and sweet."
    if setting.place == "the laundry room":
        return "Warm socks and folded shirts waited nearby, neat and complete."
    return "The closet was still and small, with little rows hanging in a line."


def rhyme_pair(a: str, b: str) -> str:
    return f"{a} {b}"


def predict_fit(world: World, child: Entity, under: Underwear) -> dict:
    sim = world.copy()
    sim.get(child.id).memes["worry"] += 1
    sim.get(child.id).meters["chafe"] = 1.0 if not under.soft else 0.0
    return {"chafe": sim.get(child.id).meters.get("chafe", 0.0) >= THRESHOLD}


def introduce(world: World, child: Entity, under: Underwear, event: str) -> None:
    world.say(
        f"{child.id} was a {child.traits[0]} little {child.type} with a smile like light, "
        f"ready for {EVENTS[event]['gerund']} before breakfast time bright."
    )


def foreshadow(world: World, child: Entity, under: Underwear) -> None:
    world.say(
        f"A tag on the box said, 'Try a soft one if a snug one bites,' "
        f"and {child.id} tucked that clue away like a kite on windy nights."
    )
    world.facts["hint"] = "soft one if a snug one bites"


def wants(world: World, child: Entity, event: str) -> None:
    child.memes["joy"] += 1
    world.say(
        f"{child.id} wanted to {EVENTS[event]['verb']} and twirl in the air, "
        f"with ribbon and rhythm and bouncy gold hair."
    )


def worries(world: World, parent: Entity, child: Entity, under: Underwear) -> None:
    pred = predict_fit(world, child, under)
    if pred["chafe"]:
        parent.memes["worry"] += 1
        world.facts["predicted_chafe"] = True
        world.say(
            f'"Let’s not start with the wrong one," {parent.pronoun("possessive")} {parent.type} said with care, '
            f'"If it pinches or rubs, you’ll feel sad there."'
        )


def try_on(world: World, child: Entity, under: Underwear) -> None:
    child.memes["worry"] += 1
    if under.soft:
        child.memes["joy"] += 1
        child.memes["worry"] = 0.0
        child.meters["chafe"] = 0.0
        world.say(
            f"{child.id} tried the soft training bra and gave a small cheer, "
            f"for it fit like a whisper and felt nice near."
        )
    else:
        child.meters["chafe"] = 1.0
        propagate(world, narrate=False)
        world.say(
            f"{child.id} tried the first bra, and it felt a bit tight, "
            f"so the tiny red mark made the clue seem quite right."
        )


def fix(world: World, parent: Entity, child: Entity, under: Underwear) -> None:
    if under.soft:
        return
    alt = UNDERWEAR["training_bra"]
    world.say(
        f"Then {parent.id} found a softer choice with a calmer seam, "
        f"the kind that could fit like a small, kind dream."
    )
    child.memes["joy"] += 1
    child.memes["pride"] += 1
    child.memes["worry"] = 0.0
    child.meters["chafe"] = 0.0
    world.say(
        f"{child.id} switched to the training bra, and the pinch went away; "
        f"the morning felt sunny, and ready for play."
    )
    world.facts["resolved_with"] = alt.id


def ending(world: World, child: Entity, event: str, under: Underwear) -> None:
    world.say(
        f"So {child.id} {EVENTS[event]['gerund']}, all comfy and proud, "
        f"and the soft little bra stayed hidden in the crowd."
    )
    world.say(
        f"{child.id} spun by the mirror, light as a feather and bright, "
        f"because a small clue led to the right fit at the right time."
    )


def tell(setting: Setting, under: Underwear, event: str, name: str, gender: str, parent_kind: str, trait: str, color: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, traits=[trait, "little"], color=color))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_kind, label="parent"))
    garment = world.add(Entity(id="under", type="thing", label=under.label, phrase=under.phrase, owner=child.id))
    garment.worn_by = child.id

    introduce(world, child, under, event)
    foreshadow(world, child, under)
    world.para()
    world.say(setting_detail(setting))
    wants(world, child, event)
    worries(world, parent, child, under)
    try_on(world, child, under)
    if not under.soft:
        fix(world, parent, child, under)
    world.para()
    ending(world, child, event, under)

    world.facts.update(
        child=child,
        parent=parent,
        garment=garment,
        under=under,
        event=event,
        setting=setting,
    )
    return world


KNOWLEDGE = {
    "bra": [
        ("What is a bra?",
         "A bra is a piece of clothing some people wear under their shirts for support and comfort."),
    ],
    "soft": [
        ("What does soft mean?",
         "Soft means gentle and pleasant to touch, not scratchy or hard."),
    ],
    "fit": [
        ("What does it mean when clothes fit well?",
         "Clothes fit well when they are the right size and feel comfortable to wear."),
    ],
    "clothes": [
        ("Why do people try on clothes?",
         "People try on clothes to see whether they fit and feel good before they wear them out."),
    ],
    "comfort": [
        ("Why is comfort important in clothes?",
         "Comfort matters because clothes that feel good make it easier to move, play, and rest."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    under = f["under"]
    event = EVENTS[f["event"]]
    return [
        f'Write a gentle rhyming story for a young child about {child.id} and a {under.label}.',
        f"Tell a short story where a little {child.type} notices a clue that the {under.label} may not fit right, then finds a softer choice.",
        f'Write a warm bedtime-style story that includes the word "{under.label}" and ends with a comfortable happy finish.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    under = f["under"]
    event = EVENTS[f["event"]]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {child.id}, a {child.traits[0]} little {child.type}, and {parent.id}, who helped with the clothes.",
        ),
        QAItem(
            question=f"What did {child.id} want to do?",
            answer=f"{child.id} wanted to {event['verb']} and feel nice and neat for the day.",
        ),
        QAItem(
            question=f"What was the first clue that the {under.label} might not be the best choice?",
            answer="A tiny note warned that a snug one might bite, and the first try felt a little tight.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} wearing the softer choice, feeling comfy, and getting ready to move and twirl with a happy smile.",
        ),
    ]
    if world.facts.get("resolved_with"):
        qa.append(
            QAItem(
                question="What helped the child feel better?",
                answer="A soft training bra helped because it fit more gently and did not pinch.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = set(world.facts["under"].tags)
    tags.update({"clothes", "comfort"})
    for tag in ["bra", "soft", "fit", "clothes", "comfort"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", event="dress", under="bra", name="Mia", gender="girl", parent="mother", trait="shy", color="pink"),
    StoryParams(place="closet", event="dress", under="bra", name="Nora", gender="girl", parent="mother", trait="brave", color="white"),
    StoryParams(place="laundry", event="dress", under="bra", name="Ava", gender="girl", parent="mother", trait="gentle", color="lavender"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for event in setting.affords:
            for under in UNDERWEAR:
                combos.append((place, event, under))
    return combos


def explain_rejection(place: str, event: str, under: str) -> str:
    return f"(No story: {place}, {event}, and {under} do not form a reasonable little dressing scene here.)"


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("event", eid))
        for t in sorted(e["tags"]):
            lines.append(asp.fact("event_tag", eid, t))
    for uid, u in UNDERWEAR.items():
        lines.append(asp.fact("under", uid))
        lines.append(asp.fact("fit", uid, u.fit))
        if u.soft:
            lines.append(asp.fact("soft", uid))
        for t in sorted(u.tags):
            lines.append(asp.fact("tag", uid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Event, Under) :- affords(Place, Event), under(Under).
soft_fix(Under) :- soft(Under).
reasonably_supported(Place, Event, Under) :- valid(Place, Event, Under), soft_fix(Under).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: bra foreshadowing in a rhyming style.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--under", choices=UNDERWEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--color", choices=["white", "pink", "blue", "lavender"])
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.event is None or c[1] == args.event)
              and (args.under is None or c[2] == args.under)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, event, under = rng.choice(sorted(combos))
    gender = args.gender or "girl"
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or "mother"
    trait = args.trait or rng.choice(TRAITS)
    color = args.color or rng.choice(sorted(UNDERWEAR[under].colors))
    return StoryParams(place=place, event=event, under=under, name=name, gender=gender, parent=parent, trait=trait, color=color)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.place],
        UNDERWEAR[params.under],
        params.event,
        params.name,
        params.gender,
        params.parent,
        params.trait,
        params.color,
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
        print(asp_program("#show valid/3.\n#show reasonably_supported/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3.\n#show reasonably_supported/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible (place, event, under) combos:\n")
        for t in triples:
            print(f"  {t[0]:10} {t[1]:10} {t[2]:12}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)

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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.under} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
