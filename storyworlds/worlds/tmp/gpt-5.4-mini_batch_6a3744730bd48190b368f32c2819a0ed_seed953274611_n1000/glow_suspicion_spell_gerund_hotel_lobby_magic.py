#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/glow_suspicion_spell_gerund_hotel_lobby_magic.py
=================================================================================

A standalone storyworld for a small slice-of-life magic mishap in a hotel lobby.

Premise
-------
A child spots a strange little glow in the hotel lobby, grows suspicious that a
spell is being cast, and a calm grown-up explains the situation before it turns
into a scene. The story keeps the feeling gentle and ordinary: a bell desk, a
plant, a suitcase, a parent, a child, and a tiny magical trick that is safer
once understood.

The world is built around:
- glow
- suspicion
- spell-gerund
- hotel lobby
- Magic
- Rhyme
- Cautionary
- slice of life

The model uses typed entities with physical meters and emotional memes, a
forward-chained causal simulation, a reasonableness gate, an inline ASP twin,
and story-grounded QA.
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
SUSPICION_MIN = 1.0
MAGIC_MIN = 1
RHYME_MIN = 1

NAMES = ["Mina", "Noah", "Lulu", "Omar", "Ivy", "Ben", "Sage", "Tia"]
PARENT_NAMES = ["Mom", "Dad", "Aunt June", "Uncle Rio"]

LOBBY_OBJECTS = {
    "lamp": {"label": "lamp", "kind": "thing", "glow": True, "spellable": False},
    "potted_plant": {"label": "potted plant", "kind": "thing", "glow": False, "spellable": False},
    "bell_desk": {"label": "bell desk", "kind": "thing", "glow": False, "spellable": False},
    "glass_bowl": {"label": "glass bowl", "kind": "thing", "glow": False, "spellable": True},
}

SPELLS = {
    "glimmering": {
        "id": "glimmering",
        "label": "glimmering",
        "spell_gerund": "glimmering",
        "effect": "a tiny glow",
        "risk": "made the child suspicious",
        "qa": "sparked a tiny glow",
    },
    "shimmering": {
        "id": "shimmering",
        "label": "shimmering",
        "spell_gerund": "shimmering",
        "effect": "a soft shimmer",
        "risk": "looked like a secret spell",
        "qa": "made a soft shimmer",
    },
    "humming": {
        "id": "humming",
        "label": "humming",
        "spell_gerund": "humming",
        "effect": "a warm hum",
        "risk": "felt mysterious",
        "qa": "made a warm hum",
    },
}

REMEDIES = {
    "explain": {
        "id": "explain",
        "sense": 3,
        "power": 3,
        "text": "smiled and explained that the glow came from a little lamp, not a spell",
        "fail": "tried to explain, but the situation had already grown too tangled",
        "qa": "smiled and explained the glow was just from a little lamp",
    },
    "cover_lamp": {
        "id": "cover_lamp",
        "sense": 3,
        "power": 4,
        "text": "reached over, adjusted the lamp shade, and softened the glow at once",
        "fail": "adjusted the lamp shade, but the glow stayed bright and confusing",
        "qa": "adjusted the lamp shade and softened the glow",
    },
    "turn_sign": {
        "id": "turn_sign",
        "sense": 2,
        "power": 2,
        "text": "turned the lobby sign a little so the reflection stopped winking in the glass",
        "fail": "turned the sign, but the reflection kept winking anyway",
        "qa": "turned the sign so the reflection stopped winking",
    },
    "water_bucket": {
        "id": "water_bucket",
        "sense": 1,
        "power": 1,
        "text": "ran for a bucket of water, which was far too much fuss for a harmless glow",
        "fail": "ran for a bucket of water, but it solved nothing useful",
        "qa": "ran for a bucket of water",
    },
}

CAUTIOUS_TRAITS = {"careful", "watchful", "gentle", "quiet"}

TOPICS = {
    "glow": [
        ("What makes a lamp glow?",
         "A lamp glows when it is switched on and the bulb makes light. The light is gentle and helps people see in a room."),
    ],
    "suspicion": [
        ("What is suspicion?",
         "Suspicion is when someone thinks something odd might be happening. It can make a person ask careful questions before jumping to conclusions."),
    ],
    "spell-gerund": [
        ("What does a spell sound like in a story?",
         "A spell in a story often sounds magical and strange, like whispering or humming. In this world, the spell word is the spell-gerund, such as glimmering or shimmering."),
    ],
    "hotel": [
        ("What is a hotel lobby?",
         "A hotel lobby is the first room people enter when they come to a hotel. It usually has a desk, seats, lights, and people passing through."),
    ],
    "magic": [
        ("Is every strange glow a magic spell?",
         "No. Some glows are just from lamps, reflections, or little decorations. It is wise to look carefully before calling it magic."),
    ],
    "rhyme": [
        ("Why do people use rhyme in stories?",
         "Rhyme can make words sound playful and easy to remember. It can also make a story feel like it is singing softly."),
    ],
    "cautionary": [
        ("What does a cautionary story try to teach?",
         "A cautionary story shows what could go wrong and how to stay safe or calm. It helps readers learn by watching the trouble get solved in a sensible way."),
    ],
}

TOPIC_ORDER = ["glow", "suspicion", "spell-gerund", "hotel", "magic", "rhyme", "cautionary"]


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
    luminous: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id


@dataclass
class SceneSpec:
    id: str
    setting: str
    object_id: str
    object_label: str
    glow_source: str
    glow_reason: str
    rhyme: str
    mood: str


@dataclass
class StoryParams:
    scene: str
    spell: str
    remedy: str
    child: str
    child_gender: str
    adult: str
    adult_gender: str
    trait: str = "careful"
    seed: Optional[int] = None


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


def _r_spread(world: World) -> list[str]:
    out: list[str] = []
    if world.get("glow_source").meters["glow"] < THRESHOLD:
        return out
    sig = ("spread",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("child").memes["suspicion"] += 1
    world.get("child").memes["curiosity"] += 1
    out.append("__suspicion__")
    return out


def _r_calm(world: World) -> list[str]:
    out: list[str] = []
    if world.get("child").memes["suspicion"] < SUSPICION_MIN:
        return out
    sig = ("calm",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("adult").memes["care"] += 1
    out.append("__calm__")
    return out


CAUSAL_RULES = [Rule("spread", _r_spread), Rule("calm", _r_calm)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(x for x in bits if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def best_remedy() -> dict:
    return max(REMEDIES.values(), key=lambda r: r["sense"])


def sensible_remedies() -> list[dict]:
    return [r for r in REMEDIES.values() if r["sense"] >= MAGIC_MIN]


def could_confuse(spell: dict, spec: SceneSpec) -> bool:
    return spell["id"] in {"shimmering", "glimmering", "humming"} and spec.glow_reason != "nothing magical"


def predict(world: World, params: StoryParams) -> dict:
    sim = world.copy()
    _do_scene(sim, narrate=False)
    return {
        "suspicion": sim.get("child").memes["suspicion"],
        "glow": sim.get("glow_source").meters["glow"],
    }


def _do_scene(world: World, narrate: bool = True) -> None:
    world.get("glow_source").meters["glow"] += 1
    world.get("glow_source").meters["shine"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, child: Entity, adult: Entity, spec: SceneSpec) -> None:
    child.memes["curiosity"] += 1
    world.say(
        f"In the hotel lobby, {child.id} stood near the couch and watched the soft {spec.glow_reason}."
    )
    world.say(
        f"The desk lamp gave a little {spec.glow_reason}, and {spec.rhyme}."
    )


def suspicion_beat(world: World, child: Entity, spec: SceneSpec, spell: dict) -> None:
    child.memes["suspicion"] += 1
    world.say(
        f"{child.id} tilted {child.pronoun('possessive')} head. "
        f'"That glow looks like a {spell["spell_gerund"]} spell," {child.pronoun()} said.'
    )
    world.say(
        f'It sounded funny and a little scary, the kind of thing that makes a small suspicion grow.'
    )


def gentle_warning(world: World, adult: Entity, child: Entity, spell: dict) -> None:
    adult.memes["care"] += 1
    world.say(
        f'{adult.id} knelt beside {child.id} and said, '
        f'"Sometimes a glow is just a lamp or a reflection. Let\'s look before we worry."'
    )
    world.say(
        f'{adult.id} promised to help, because caution is kinder than guessing.'
    )


def reveal(world: World, child: Entity, adult: Entity, spec: SceneSpec) -> None:
    world.say(
        f'Together they looked behind the plant and found {spec.object_label}. '
        f'Its shine made the glass bowl near the desk wink back.'
    )
    world.say(
        f'That was the whole trick: no secret spell, just a bright spot and a shiny edge.'
    )


def remedy_beat(world: World, adult: Entity, remedy: dict, spec: SceneSpec) -> None:
    body = remedy["text"]
    world.say(f"{adult.id} {body}.")
    world.say(
        f"The lobby settled down again, and the glow became small and friendly."
    )


def ending(world: World, child: Entity, adult: Entity, spec: SceneSpec) -> None:
    child.memes["suspicion"] = 0.0
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    world.say(
        f"{child.id} laughed, and the funny little worry floated away. "
        f'Now the lobby looked ordinary again: lamp, plant, desk, and a neat little glow.'
    )
    world.say(
        f'"Next time," {child.id} said, "I will look first, then ask."'
    )


def tell(spec: SceneSpec, spell: dict, remedy: dict, child_name: str = "Mina",
         child_gender: str = "girl", adult_name: str = "Mom",
         adult_gender: str = "woman", trait: str = "careful") -> World:
    world = World()
    child = world.add(Entity(id="child", kind="character", type=child_gender,
                             label=child_name, role="child", traits=[trait], attrs={"name": child_name}))
    adult = world.add(Entity(id="adult", kind="character", type=adult_gender,
                             label=adult_name, role="adult", traits=[trait], attrs={"name": adult_name}))
    glow = world.add(Entity(id="glow_source", type="thing", label=spec.object_label, luminous=True))
    lamp = world.add(Entity(id="lamp", type="thing", label="lamp", luminous=True))
    world.facts["scene"] = spec
    world.facts["spell"] = spell
    world.facts["remedy"] = remedy
    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["lamp"] = lamp
    intro(world, child, adult, spec)
    world.para()
    world.say(f'"{spell["label"]}!" {child.id} whispered, half-rhyme and half-warning.')
    suspicion_beat(world, child, spec, spell)
    gentle_warning(world, adult, child, spell)
    _do_scene(world, narrate=True)
    world.para()
    reveal(world, child, adult, spec)
    remedy_beat(world, adult, remedy, spec)
    ending(world, child, adult, spec)
    world.facts.update(outcome="calm", glow=world.get("glow_source").meters["glow"])
    return world


SCENES = {
    "hotel_lobby": SceneSpec(
        id="hotel_lobby",
        setting="hotel lobby",
        object_id="glass_bowl",
        object_label="a glass bowl with a metal key tag inside",
        glow_source="lamp",
        glow_reason="lamp glow",
        rhyme="the desk lamp sang a quiet song",
        mood="slice of life",
    ),
    "hotel_lobby_plant": SceneSpec(
        id="hotel_lobby_plant",
        setting="hotel lobby",
        object_id="potted_plant",
        object_label="a shiny ribbon tied around the potted plant",
        glow_source="reflection",
        glow_reason="little reflection",
        rhyme="the lobby felt calm and the carpet looked long",
        mood="slice of life",
    ),
    "hotel_lobby_sign": SceneSpec(
        id="hotel_lobby_sign",
        setting="hotel lobby",
        object_id="bell_desk",
        object_label="a tiny blinking sign on the bell desk",
        glow_source="sign",
        glow_reason="sign glow",
        rhyme="the sign blinked bright, but nothing was wrong",
        mood="slice of life",
    ),
}

CURATED = [
    StoryParams(scene="hotel_lobby", spell="glimmering", remedy="explain",
                child="Mina", child_gender="girl", adult="Mom", adult_gender="woman",
                trait="careful"),
    StoryParams(scene="hotel_lobby_plant", spell="shimmering", remedy="cover_lamp",
                child="Noah", child_gender="boy", adult="Dad", adult_gender="man",
                trait="watchful"),
    StoryParams(scene="hotel_lobby_sign", spell="humming", remedy="turn_sign",
                child="Lulu", child_gender="girl", adult="Aunt June", adult_gender="woman",
                trait="gentle"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for scene in SCENES:
        for spell in SPELLS:
            for remedy in REMEDIES:
                if remedy != "water_bucket":
                    combos.append((scene, spell, remedy))
    return combos


def explain_rejection(params: StoryParams) -> str:
    return "(No story: this seed combination is too weakly grounded for the lobby glow premise.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    spec: SceneSpec = f["scene"]
    spell = f["spell"]
    return [
        f'Write a slice-of-life story in a hotel lobby that includes the word "glow" and the spell word "{spell["spell_gerund"]}".',
        f"Tell a small cautionary magic story where a child sees {spec.object_label} and worries it is a {spell['label']} spell.",
        f'Write a gentle rhyme-tinged story about a hotel lobby, a glow, and a child who learns to look carefully before making a guess.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    spec: SceneSpec = f["scene"]
    spell = f["spell"]
    child: Entity = f["child"]
    adult: Entity = f["adult"]
    qa = [
        ("Where does the story happen?",
         f"It happens in a hotel lobby, where people come and go and the light can look a little magical. The lobby setting matters because the glow is easy to mistake for a spell."),
        (f"What did {child.label_word} suspect?",
         f"{child.label_word} suspected that the glow was a {spell['spell_gerund']} spell. That suspicion came from seeing a strange shine before understanding what it really was."),
        ("What turned out to be causing the glow?",
         f"It turned out to be {spec.object_label}. The grown-up helped them see that the glow had an ordinary cause."),
        ("How did the adult respond?",
         f"{adult.label_word} answered calmly and explained things instead of laughing at the worry. That gentle caution kept the moment small and safe."),
    ]
    if f.get("outcome") == "calm":
        qa.append((
            "How did the story end?",
            f"The story ended quietly, with the child feeling relieved and a little wiser. The glow stayed in the lobby, but the fear around it disappeared."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"glow", "suspicion", "spell-gerund", "hotel", "magic", "rhyme", "cautionary"}
    out = []
    for tag in TOPIC_ORDER:
        if tag in tags and tag in TOPICS:
            out.extend(TOPICS[tag])
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
        if e.luminous:
            bits.append("luminous=True")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
glow(glow_source) :- luminous(glow_source).
suspicion(child) :- glow(glow_source).
calm(adult) :- suspicion(child).
valid(Scene, Spell, Remedy) :- scene(Scene), spell(Spell), remedy(Remedy), Remedy != water_bucket.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SCENES:
        lines.append(asp.fact("scene", sid))
    for spid in SPELLS:
        lines.append(asp.fact("spell", spid))
    for rid, rem in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("sense", rid, rem["sense"]))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        rc = 1
        print("MISMATCH: ASP and Python valid_combos disagree.")
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generation smoke test passed.")
    except Exception as exc:  # pragma: no cover
        rc = 1
        print(f"FAILED: generation smoke test crashed: {exc}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Hotel lobby glow / suspicion / spell-gerund storyworld.")
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--adult")
    ap.add_argument("--adult-gender", choices=["woman", "man"])
    ap.add_argument("--trait", choices=["careful", "watchful", "gentle", "quiet"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    scene = args.scene or rng.choice(list(SCENES))
    spell = args.spell or rng.choice(list(SPELLS))
    remedy = args.remedy or rng.choice([r for r in REMEDIES if r != "water_bucket"])
    if remedy == "water_bucket":
        raise StoryError("That remedy is too clumsy for this gentle lobby story.")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    adult_gender = args.adult_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(NAMES)
    adult = args.adult or rng.choice(PARENT_NAMES)
    trait = args.trait or rng.choice(["careful", "watchful", "gentle", "quiet"])
    return StoryParams(scene=scene, spell=spell, remedy=remedy, child=child,
                       child_gender=child_gender, adult=adult, adult_gender=adult_gender,
                       trait=trait)


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES or params.spell not in SPELLS or params.remedy not in REMEDIES:
        raise StoryError("Invalid story parameters.")
    if REMEDIES[params.remedy]["sense"] < MAGIC_MIN:
        raise StoryError("Chosen remedy is too unreasonable.")
    world = tell(SCENES[params.scene], SPELLS[params.spell], REMEDIES[params.remedy],
                 child_name=params.child, child_gender=params.child_gender,
                 adult_name=params.adult, adult_gender=params.adult_gender,
                 trait=params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print("  ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
            header = f"### {p.child} in {p.scene} with {p.spell} / {p.remedy}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
