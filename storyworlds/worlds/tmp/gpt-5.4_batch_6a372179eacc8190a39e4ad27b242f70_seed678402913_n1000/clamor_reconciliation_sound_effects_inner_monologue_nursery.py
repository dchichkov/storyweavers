#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4/clamor_reconciliation_sound_effects_inner_monologue_nursery.py
==========================================================================================

A standalone story world for a nursery-rhyme-style tale about a noisy quarrel,
a burst of clamor, and a gentle reconciliation.

The tiny domain:
- two small children in the nursery want the same noisemaker
- one grabs, the other cries, and the room fills with clamor
- a grown-up offers a sensible peace method that actually fits the toy
- the children reconcile, and the ending image proves the noise has changed
  into music

The world model uses:
- physical meters: noise, grabbed, shared, waiting, harmony
- emotional memes: joy, jealousy, hurt, regret, relief, love, patience

The declarative ASP twin mirrors the reasonableness gate:
- not every peace method fits every toy
- a fix is valid only when it matches the toy's sharing pattern

Run it
------
python storyworlds/worlds/gpt-5.4/clamor_reconciliation_sound_effects_inner_monologue_nursery.py
python storyworlds/worlds/gpt-5.4/clamor_reconciliation_sound_effects_inner_monologue_nursery.py --toy drum --peace take_turns
python storyworlds/worlds/gpt-5.4/clamor_reconciliation_sound_effects_inner_monologue_nursery.py --toy rattle --peace duet
python storyworlds/worlds/gpt-5.4/clamor_reconciliation_sound_effects_inner_monologue_nursery.py --all
python storyworlds/worlds/gpt-5.4/clamor_reconciliation_sound_effects_inner_monologue_nursery.py -n 5 --seed 7 --qa
python storyworlds/worlds/gpt-5.4/clamor_reconciliation_sound_effects_inner_monologue_nursery.py --verify
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
    phrase: str = ""
    role: str = ""
    owner: str = ""
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "nurse"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mother", "father": "father", "nurse": "nurse"}.get(self.type, self.type)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    effect: str
    cry: str
    pattern: str
    rhyme: str
    tags: set[str] = field(default_factory=set)


@dataclass
class PeaceMethod:
    id: str
    label: str
    fits: set[str] = field(default_factory=set)
    offer: str = ""
    ending: str = ""
    qa_text: str = ""
    tags: set[str] = field(default_factory=set)


@dataclass
class Scene:
    id: str
    place: str
    opening: str
    closing: str
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, scene: Scene) -> None:
        self.scene = scene
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def kids(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.role in {"holder", "wanter"}]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.scene)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_clamor(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    toy = world.get("toy")
    a = world.get("a")
    b = world.get("b")
    if toy.meters["grabbed"] >= THRESHOLD and room.meters["noise"] < THRESHOLD:
        sig = ("clamor",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["noise"] += 2
            a.memes["hurt"] += 1
            b.memes["jealousy"] += 1
            out.append("__clamor__")
    return out


def _r_regret(world: World) -> list[str]:
    out: list[str] = []
    room = world.get("room")
    b = world.get("b")
    if room.meters["noise"] >= THRESHOLD and b.memes["jealousy"] >= THRESHOLD:
        sig = ("regret",)
        if sig not in world.fired:
            world.fired.add(sig)
            b.memes["regret"] += 1
            out.append("__regret__")
    return out


def _r_harmony(world: World) -> list[str]:
    out: list[str] = []
    toy = world.get("toy")
    room = world.get("room")
    a = world.get("a")
    b = world.get("b")
    if toy.meters["shared"] >= THRESHOLD and room.meters["harmony"] < THRESHOLD:
        sig = ("harmony",)
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["harmony"] += 1
            room.meters["noise"] = 0.0
            a.memes["relief"] += 1
            b.memes["relief"] += 1
            a.memes["love"] += 1
            b.memes["love"] += 1
            out.append("__harmony__")
    return out


CAUSAL_RULES = [
    Rule(name="clamor", tag="physical", apply=_r_clamor),
    Rule(name="regret", tag="emotional", apply=_r_regret),
    Rule(name="harmony", tag="social", apply=_r_harmony),
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
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def compatible(toy: Toy, peace: PeaceMethod) -> bool:
    return toy.pattern in peace.fits


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for scene_id in SCENES:
        for toy_id, toy in TOYS.items():
            for peace_id, peace in PEACE_METHODS.items():
                if compatible(toy, peace):
                    combos.append((scene_id, toy_id, peace_id))
    return sorted(combos)


def predict_clamor(world: World) -> dict:
    sim = world.copy()
    snatch(sim, sim.get("b"), sim.get("a"), sim.get("toy"), narrate=False)
    return {
        "noise": sim.get("room").meters["noise"],
        "hurt": sim.get("a").memes["hurt"],
        "regret": sim.get("b").memes["regret"],
    }


def introduce(world: World, a: Entity, b: Entity, toy_cfg: Toy) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"In {world.scene.place}, where {world.scene.opening}, sat {a.id} and {b.id} by the quilt."
    )
    world.say(
        f"There was {toy_cfg.phrase}, and it sang {toy_cfg.effect} whenever small hands gave it a shake."
    )


def first_play(world: World, a: Entity, toy_cfg: Toy) -> None:
    toy = world.get("toy")
    toy.owner = a.id
    toy.meters["played"] += 1
    world.say(
        f'{a.id} tapped it first -- "{toy_cfg.effect}!" -- and smiled a sleepy little smile.'
    )
    world.say(
        f'{a.id} thought, "Just one more turn, and then I shall rest a while."'
    )


def wanting(world: World, b: Entity, toy_cfg: Toy) -> None:
    b.memes["desire"] += 1
    world.say(
        f'{b.id} listened to the bright small sound and whispered, "Oh, I want that too."'
    )
    world.say(
        f'{b.id} thought, "If I do not get a turn, my heart will feel askew."'
    )


def warning(world: World, carer: Entity, toy_cfg: Toy) -> None:
    pred = predict_clamor(world)
    world.facts["predicted_noise"] = pred["noise"]
    world.facts["predicted_hurt"] = pred["hurt"]
    world.say(
        f'{carer.label_word.capitalize()} heard the wanting voice and said, "Softly now, soft and slow.'
        f' If hands should grab, a clamor may rise, and little tears may flow."'
    )


def snatch(world: World, b: Entity, a: Entity, toy: Entity, narrate: bool = True) -> None:
    toy.owner = b.id
    toy.meters["grabbed"] += 1
    b.memes["jealousy"] += 1
    a.memes["hurt"] += 1
    propagate(world, narrate=False)
    if narrate:
        sound = world.facts["toy_cfg"].effect
        world.say(
            f"But quick as a mouse, {b.id} snatched the toy. "{sound}! {sound}!" it cried.'
        )
        world.say(
            f'Then up came the clamor -- feet pattered, lips quivered, and both small voices flew high.'
        )
        world.say(
            f'{a.id} thought, "That was mine." {b.id} thought, "Oh dear, why did I not wait and try?"'
        )


def nurse_arrives(world: World, carer: Entity) -> None:
    world.say(
        f'{carer.label_word.capitalize()} came with a hush-hush step and knelt where the blanket lay.'
    )
    world.say(
        f'"No banging hearts and no grabbing hands. We shall mend this now," {carer.pronoun()} said.'
    )


def reconcile(world: World, a: Entity, b: Entity, carer: Entity, toy_cfg: Toy, peace: PeaceMethod) -> None:
    toy = world.get("toy")
    a.memes["patience"] += 1
    b.memes["patience"] += 1
    world.say(
        f'{carer.label_word.capitalize()} said, "{peace.offer}"'
    )
    if peace.id == "take_turns":
        toy.meters["waiting"] += 1
        world.say(
            f'{b.id} gave the toy back and waited for the count: "one, two, three."'
        )
    elif peace.id == "duet":
        world.say(
            f'The children put one hand here and one hand there, and made room side by side.'
        )
    elif peace.id == "echo_game":
        toy.meters["waiting"] += 1
        world.say(
            f'{a.id} tapped a little pattern, and {b.id} answered after, soft as a shadow.'
        )
    toy.meters["shared"] += 1
    toy.meters["grabbed"] = 0.0
    propagate(world, narrate=False)
    b.memes["regret"] += 1
    b.memes["jealousy"] = 0.0
    a.memes["hurt"] = 0.0
    world.say(
        f'{b.id} whispered, "I am sorry I grabbed." {a.id} whispered, "I forgive you."'
    )
    world.say(
        f'Soon the nursery heard {peace.ending} instead of a clamor in the air.'
    )
    if toy_cfg.rhyme:
        world.say(toy_cfg.rhyme)


def closing(world: World, a: Entity, b: Entity, toy_cfg: Toy) -> None:
    for kid in (a, b):
        kid.memes["joy"] += 1
    world.say(
        f"And so {a.id} and {b.id} played on, with gentler hands and brighter eyes."
    )
    world.say(
        f'Where once the room rang rough and loud, now {world.scene.closing} under the nursery skies.'
    )


def tell(scene: Scene, toy_cfg: Toy, peace: PeaceMethod,
         child_a: str = "Molly", child_b: str = "Toby",
         child_a_type: str = "girl", child_b_type: str = "boy",
         carer_type: str = "nurse") -> World:
    world = World(scene)
    a = world.add(Entity(id="a", kind="character", type=child_a_type, label=child_a, phrase=child_a, role="holder"))
    b = world.add(Entity(id="b", kind="character", type=child_b_type, label=child_b, phrase=child_b, role="wanter"))
    carer = world.add(Entity(id="carer", kind="character", type=carer_type, label=carer_type, phrase=carer_type, role="carer"))
    toy = world.add(Entity(id="toy", kind="thing", type="toy", label=toy_cfg.label, phrase=toy_cfg.phrase, tags=set(toy_cfg.tags)))
    room = world.add(Entity(id="room", kind="thing", type="room", label=scene.place, phrase=scene.place, tags=set(scene.tags)))
    world.facts["toy_cfg"] = toy_cfg

    introduce(world, a, b, toy_cfg)
    first_play(world, a, toy_cfg)
    wanting(world, b, toy_cfg)

    world.para()
    warning(world, carer, toy_cfg)
    snatch(world, b, a, toy)
    nurse_arrives(world, carer)

    world.para()
    reconcile(world, a, b, carer, toy_cfg, peace)
    closing(world, a, b, toy_cfg)

    world.facts.update(
        scene=scene,
        toy_cfg=toy_cfg,
        peace=peace,
        a=a,
        b=b,
        carer=carer,
        toy=toy,
        room=room,
        had_clamor=room.meters["harmony"] >= THRESHOLD,
        reconciled=toy.meters["shared"] >= THRESHOLD,
    )
    return world


SCENES = {
    "moon_nursery": Scene(
        id="moon_nursery",
        place="the moonlit nursery",
        opening="the curtains glowed like milk and the cradle shadows swayed",
        closing="the toy sang softly",
        tags={"nursery", "night"},
    ),
    "window_nursery": Scene(
        id="window_nursery",
        place="the nursery by the rainy window",
        opening="rain made silver beads on the pane and the lamp wore a yellow crown",
        closing="the toy chimed in a neat small line",
        tags={"nursery", "rain"},
    ),
    "sun_nursery": Scene(
        id="sun_nursery",
        place="the sunny nursery",
        opening="dust danced in the warm light and the rocking horse watched",
        closing="the toy answered in merry little notes",
        tags={"nursery", "day"},
    ),
}

TOYS = {
    "drum": Toy(
        id="drum",
        label="drum",
        phrase="a round red drum with a blue cord",
        effect="boom-boom",
        cry="boom",
        pattern="solo",
        rhyme="Boom-boom, room to room, kinder hands make kinder tune.",
        tags={"drum", "noise"},
    ),
    "rattle": Toy(
        id="rattle",
        label="rattle",
        phrase="a silver rattle tied with ribbons",
        effect="shake-shake",
        cry="shake",
        pattern="together",
        rhyme="Shake-shake, no mistake, two small smiles for friendship's sake.",
        tags={"rattle", "noise"},
    ),
    "bells": Toy(
        id="bells",
        label="bell strap",
        phrase="a strap of little bells",
        effect="jingle-jing",
        cry="jingle",
        pattern="echo",
        rhyme="Jingle-jing, softly sing, let the other have a swing.",
        tags={"bells", "noise"},
    ),
}

PEACE_METHODS = {
    "take_turns": PeaceMethod(
        id="take_turns",
        label="take turns",
        fits={"solo"},
        offer="One child may play while the other counts, and then the turn shall go round.",
        ending="a neat boom-boom passed back and forth",
        qa_text="they took turns with the toy",
        tags={"sharing", "counting"},
    ),
    "duet": PeaceMethod(
        id="duet",
        label="play together",
        fits={"together"},
        offer="This toy is happiest with two small hands; let us play it together.",
        ending="a bright shake-shake made together",
        qa_text="they played the toy together",
        tags={"sharing", "together"},
    ),
    "echo_game": PeaceMethod(
        id="echo_game",
        label="echo game",
        fits={"echo"},
        offer="One shall make the first small sound, and the other shall answer it after.",
        ending="a gentle jingle-jing and answering jingle",
        qa_text="they made an echo game with the toy",
        tags={"sharing", "listening"},
    ),
}

GIRL_NAMES = ["Molly", "Daisy", "Lucy", "Nell", "Annie", "Flora"]
BOY_NAMES = ["Toby", "Benny", "Robin", "Alfie", "Ned", "Jamie"]


@dataclass
class StoryParams:
    scene: str
    toy: str
    peace: str
    child_a: str
    child_b: str
    child_a_type: str
    child_b_type: str
    carer_type: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        scene="moon_nursery",
        toy="drum",
        peace="take_turns",
        child_a="Molly",
        child_b="Toby",
        child_a_type="girl",
        child_b_type="boy",
        carer_type="nurse",
    ),
    StoryParams(
        scene="window_nursery",
        toy="rattle",
        peace="duet",
        child_a="Lucy",
        child_b="Benny",
        child_a_type="girl",
        child_b_type="boy",
        carer_type="mother",
    ),
    StoryParams(
        scene="sun_nursery",
        toy="bells",
        peace="echo_game",
        child_a="Daisy",
        child_b="Robin",
        child_a_type="girl",
        child_b_type="boy",
        carer_type="nurse",
    ),
]


KNOWLEDGE = {
    "clamor": [
        (
            "What is clamor?",
            "Clamor is a loud, messy burst of noise, with many sounds all at once. It can happen when people shout or bang things together.",
        )
    ],
    "sharing": [
        (
            "Why does taking turns help children play peacefully?",
            "Taking turns helps because each child knows a chance is coming. That makes grabbing less likely and gives everyone room to feel calm.",
        )
    ],
    "drum": [
        (
            "What sound does a drum make?",
            "A drum makes a beat when you tap it, often sounding like boom-boom. The sound can be loud or soft depending on how it is played.",
        )
    ],
    "rattle": [
        (
            "What is a rattle?",
            "A rattle is a toy that makes a shaking sound when you move it. Babies and small children often enjoy its bright little noise.",
        )
    ],
    "bells": [
        (
            "What do little bells sound like?",
            "Little bells often sound like jingle-jing or ring-ring. Their sound is light and quick.",
        )
    ],
    "counting": [
        (
            "How can counting help with turns?",
            "Counting makes the wait clear and fair. When children hear the same count, they know when one turn ends and the next begins.",
        )
    ],
    "listening": [
        (
            "What is an echo game?",
            "An echo game is when one person makes a sound first and another person repeats or answers it after. It turns waiting into listening.",
        )
    ],
    "together": [
        (
            "Why can playing together stop a quarrel?",
            "Playing together gives both children a place in the game. When nobody is left out, hard feelings can soften.",
        )
    ],
}
KNOWLEDGE_ORDER = ["clamor", "drum", "rattle", "bells", "sharing", "counting", "together", "listening"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    a = f["a"].label
    b = f["b"].label
    toy = f["toy_cfg"]
    peace = f["peace"]
    scene = f["scene"]
    return [
        f'Write a short nursery-rhyme-style story that includes the word "clamor" and features inner monologue, sound effects, and reconciliation.',
        f"Tell a gentle nursery story set in {scene.place} where {a} and {b} quarrel over {toy.phrase}, the toy goes {toy.effect}, and a grown-up helps them {peace.label}.",
        f"Write a rhyming little story where a noisy quarrel becomes a peaceful game, with lines showing what each child thinks inside.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    a = f["a"]
    b = f["b"]
    toy_cfg = f["toy_cfg"]
    peace = f["peace"]
    carer = f["carer"]
    qa: list[tuple[str, str]] = [
        (
            "Who is the story about?",
            f"It is about {a.label} and {b.label} in the nursery, and the {carer.label_word} who helps them calm down. They quarrel over {toy_cfg.phrase}.",
        ),
        (
            f"Why did the clamor start?",
            f"The clamor started when {b.label} grabbed the {toy_cfg.label} instead of waiting. That hurt {a.label}'s feelings and made both the toy and the room seem loud at once.",
        ),
        (
            "How do we know what the children were thinking inside?",
            f"The story tells their inner thoughts out loud. {a.label} thinks about wanting one more turn, and {b.label} thinks about wanting the toy and then feeling sorry.",
        ),
        (
            f"How did the grown-up help them reconcile?",
            f"The {carer.label_word} did not just hush them; {carer.pronoun()} gave them a plan that fit the toy. They reconciled because {peace.qa_text}, which changed grabbing into sharing.",
        ),
        (
            "How did the story end?",
            f"It ended with the nursery sounding gentle instead of wild. The same toy still made noise, but now its sound was tidy and friendly rather than clamor.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = {"clamor", "sharing"} | set(world.facts["toy_cfg"].tags) | set(world.facts["peace"].tags)
    out: list[tuple[str, str]] = []
    for tag in KNOWLEDGE_ORDER:
        if tag in tags and tag in KNOWLEDGE:
            out.extend(KNOWLEDGE[tag])
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
        if e.role:
            bits.append(f"role={e.role}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(name for name, *_ in world.fired))}")
    return "\n".join(lines)


def explain_rejection(toy: Toy, peace: PeaceMethod) -> str:
    return (
        f"(No story: {peace.label} does not fit {toy.phrase}. "
        f"This world only accepts peace methods that match how the toy can fairly be shared.)"
    )


ASP_RULES = r"""
valid(Scene, Toy, Peace) :- scene(Scene), toy(Toy), peace(Peace), pattern(Toy, P), fits(Peace, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for scene_id in SCENES:
        lines.append(asp.fact("scene", scene_id))
    for toy_id, toy in TOYS.items():
        lines.append(asp.fact("toy", toy_id))
        lines.append(asp.fact("pattern", toy_id, toy.pattern))
    for peace_id, peace in PEACE_METHODS.items():
        lines.append(asp.fact("peace", peace_id))
        for fit in sorted(peace.fits):
            lines.append(asp.fact("fits", peace_id, fit))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    rc = 0
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python valid combos:")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in Python:", sorted(python_set - clingo_set))

    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise StoryError("Smoke test produced an empty story.")
        print("OK: smoke generation succeeded.")
    except Exception as err:
        rc = 1
        print(f"SMOKE TEST FAILED: {err}")

    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Nursery-rhyme story world: clamor, inner thoughts, and reconciliation."
    )
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--peace", choices=PEACE_METHODS)
    ap.add_argument("--carer", choices=["nurse", "mother", "father"])
    ap.add_argument("-n", type=int, default=1, help="number of stories to generate")
    ap.add_argument("--seed", type=int, default=None, help="base seed for reproducible random choices")
    ap.add_argument("--all", action="store_true", help="render the curated set instead")
    ap.add_argument("--trace", action="store_true", help="dump world-model state")
    ap.add_argument("--qa", action="store_true", help="include the three Q&A sets")
    ap.add_argument("--json", action="store_true", help="emit JSON instead of text")
    ap.add_argument("--asp", action="store_true", help="list the compatible-story set derived by clingo")
    ap.add_argument("--verify", action="store_true", help="check the inline ASP gate and smoke-test generation")
    ap.add_argument("--show-asp", action="store_true", help="print the full ASP program")
    return ap


def _pick_kid(rng: random.Random, avoid: str = "") -> tuple[str, str]:
    gender = rng.choice(["girl", "boy"])
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    names = [n for n in pool if n != avoid]
    return rng.choice(names), gender


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.toy and args.peace:
        toy = TOYS[args.toy]
        peace = PEACE_METHODS[args.peace]
        if not compatible(toy, peace):
            raise StoryError(explain_rejection(toy, peace))

    combos = [
        combo for combo in valid_combos()
        if (args.scene is None or combo[0] == args.scene)
        and (args.toy is None or combo[1] == args.toy)
        and (args.peace is None or combo[2] == args.peace)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")

    scene_id, toy_id, peace_id = rng.choice(combos)
    a_name, a_type = _pick_kid(rng)
    b_name, b_type = _pick_kid(rng, avoid=a_name)
    carer_type = args.carer or rng.choice(["nurse", "mother", "father"])
    return StoryParams(
        scene=scene_id,
        toy=toy_id,
        peace=peace_id,
        child_a=a_name,
        child_b=b_name,
        child_a_type=a_type,
        child_b_type=b_type,
        carer_type=carer_type,
    )


def generate(params: StoryParams) -> StorySample:
    if params.scene not in SCENES:
        raise StoryError(f"(Unknown scene: {params.scene})")
    if params.toy not in TOYS:
        raise StoryError(f"(Unknown toy: {params.toy})")
    if params.peace not in PEACE_METHODS:
        raise StoryError(f"(Unknown peace method: {params.peace})")

    scene = SCENES[params.scene]
    toy = TOYS[params.toy]
    peace = PEACE_METHODS[params.peace]
    if not compatible(toy, peace):
        raise StoryError(explain_rejection(toy, peace))

    world = tell(
        scene=scene,
        toy_cfg=toy,
        peace=peace,
        child_a=params.child_a,
        child_b=params.child_b,
        child_a_type=params.child_a_type,
        child_b_type=params.child_b_type,
        carer_type=params.carer_type,
    )

    for ent_id in ("a", "b"):
        ent = world.get(ent_id)
        ent.label = params.child_a if ent_id == "a" else params.child_b
        ent.phrase = ent.label

    story = world.render().replace(" a and ", " ").replace(" b and ", " ")
    story = story.replace("a thought", f"{params.child_a} thought")
    story = story.replace("b thought", f"{params.child_b} thought")
    story = story.replace(" a ", f" {params.child_a} ").replace(" b ", f" {params.child_b} ")
    story = story.replace(" sat a and b ", f" sat {params.child_a} and {params.child_b} ")
    story = story.replace(" a,", f" {params.child_a},").replace(" b,", f" {params.child_b},")
    story = story.replace(" a.", f" {params.child_a}.").replace(" b.", f" {params.child_b}.")
    story = story.replace(" a\"", f" {params.child_a}\"").replace(" b\"", f" {params.child_b}\"")
    story = story.replace(" a's ", f" {params.child_a}'s ").replace(" b's ", f" {params.child_b}'s ")
    story = story.replace(" sat a ", f" sat {params.child_a} ").replace(" and b ", f" and {params.child_b} ")

    return StorySample(
        params=params,
        story=story,
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
        print(f"{len(combos)} compatible (scene, toy, peace) combos:\n")
        for scene_id, toy_id, peace_id in combos:
            print(f"  {scene_id:14} {toy_id:8} {peace_id}")
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
            header = f"### {p.child_a} & {p.child_b}: {p.toy} with {p.peace} in {p.scene}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
