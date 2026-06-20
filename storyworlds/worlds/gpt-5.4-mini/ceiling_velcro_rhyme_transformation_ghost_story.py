#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/ceiling_velcro_rhyme_transformation_ghost_story.py
===================================================================================

A standalone story world sketch for a small ghost-story domain with two seed
words: **ceiling** and **velcro**.  The world models a child in a spooky room,
a harmless ghost with a sticky problem, a rhyming spell, and a transformation
that turns a scary ceiling moment into a friendly ending.

The story style is ghost-story flavored, but child-safe: the "ghost" is more
lonely than scary, the ceiling is the place where the trouble appears, and
velcro is the strange little helper that causes the change.

The model uses typed entities with physical meters and emotional memes, a small
forward-chained rule engine, a reasonableness gate, an inline ASP twin, and
three separate Q&A sets grounded in simulated world state.
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
    has_velcro: bool = False
    on_ceiling: bool = False
    transformable: bool = False
    transformed: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"ghost"}:
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Setting:
    id: str
    place: str
    sound: str
    light: str
    dark_spot: str


@dataclass
class Spell:
    id: str
    rhyme: str
    twirl: str
    change: str
    effect: str


@dataclass
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
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]


def _r_spook(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    room = world.entities.get("room")
    if not ghost or not room:
        return out
    if ghost.on_ceiling and ghost.memes["lonely"] >= THRESHOLD:
        sig = ("spook", "ghost")
        if sig not in world.fired:
            world.fired.add(sig)
            room.meters["spooky"] += 1
            out.append("__spook__")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    ghost = world.entities.get("ghost")
    if not ghost:
        return out
    if ghost.meters["settled"] >= THRESHOLD and not ghost.transformed:
        sig = ("transform", "ghost")
        if sig not in world.fired:
            world.fired.add(sig)
            ghost.transformed = True
            ghost.type = "friend"
            ghost.label = "the friendly ghost"
            out.append("__change__")
    return out


CAUSAL_RULES = [
    Rule("spook", "mood", _r_spook),
    Rule("transform", "change", _r_transformation),
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


def is_reasonable(setting: Setting, spell: Spell) -> bool:
    return "ceiling" in setting.dark_spot and "rhyme" in spell.id


def predict_change(world: World) -> dict:
    sim = world.copy()
    do_rhyme(sim, narrate=False)
    return {
        "changed": sim.get("ghost").transformed,
        "spooky": sim.get("room").meters["spooky"],
    }


def setup(world: World, child: Entity, ghost: Entity, setting: Setting) -> None:
    child.memes["curious"] += 1
    ghost.memes["lonely"] += 1
    world.say(
        f"On a windy night, {child.id} tiptoed into {setting.place}. "
        f"{setting.light} flickered, and the {setting.dark_spot} looked very long."
    )
    world.say(
        f"Then {child.id} heard a soft rustle near the ceiling, like a sigh in the dark."
    )


def discover_velcro(world: World, child: Entity, ghost: Entity) -> None:
    child.memes["worry"] += 1
    world.say(
        f"Up on the ceiling, {child.id} saw something odd: a strip of velcro held "
        f"the little ghost in place."
    )
    world.say(
        f'"Velcro?," {child.id} whispered. "A sticky trick in the air?"'
    )


def rhyme_spell(world: World, child: Entity, spell: Spell) -> None:
    child.memes["bravery"] += 1
    world.say(f'{child.id} took a breath and spoke a rhyme:')
    world.say(f'"{spell.rhyme}"')
    world.say(f'"{spell.twirl}"')
    world.say(f'"{spell.change}"')
    world.say(f"The words made the room hum with {spell.effect}.")


def do_rhyme(world: World, narrate: bool = True) -> None:
    ghost = world.get("ghost")
    ghost.meters["tugged"] += 1
    ghost.meters["settled"] += 1
    ghost.memes["lonely"] = max(0.0, ghost.memes["lonely"] - 1.0)
    ghost.memes["hope"] += 1
    world.get("room").meters["spooky"] = max(0.0, world.get("room").meters["spooky"] - 1.0)
    propagate(world, narrate=narrate)


def transform(world: World, child: Entity, ghost: Entity, setting: Setting) -> None:
    if ghost.transformed:
        world.say(
            f"The velcro gave a tiny rip, and the ghost drifted down from the ceiling "
            f"like a paper moon coming home."
        )
        world.say(
            f"At once the ghost changed from pale and wobbly into a smiling little friend "
            f"with a bright scarf."
        )


def ending(world: World, child: Entity, ghost: Entity, setting: Setting) -> None:
    child.memes["joy"] += 1
    ghost.memes["joy"] += 1
    world.say(
        f"By the end, the ceiling was only a ceiling again, and the velcro sat quietly "
        f"on the wall like an ordinary strip of tape."
    )
    world.say(
        f"{child.id} waved goodnight, and the friendly ghost waved back before floating "
        f"into the moonlight."
    )


def tell(setting: Setting, spell: Spell, child_name: str = "Mina",
         child_gender: str = "girl") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", role="ghost",
                             label="the ghost", transformable=True, on_ceiling=True))
    room = world.add(Entity(id="room", kind="thing", type="room", label="the room"))
    velcro = world.add(Entity(id="velcro", kind="thing", type="thing", label="velcro",
                              has_velcro=True))
    world.facts["setting"] = setting
    world.facts["spell"] = spell

    setup(world, child, ghost, setting)
    world.para()
    discover_velcro(world, child, ghost)
    rhyme_spell(world, child, spell)
    do_rhyme(world, narrate=True)
    transform(world, child, ghost, setting)
    world.para()
    ending(world, child, ghost, setting)

    world.facts.update(child=child, ghost=ghost, room=room, velcro=velcro,
                       outcome="transformed" if ghost.transformed else "spooky")
    return world


SETTINGS = {
    "attic": Setting("attic", "the attic", "Dust danced in the lamp glow", "a weak lamp", "ceiling beams"),
    "hall": Setting("hall", "the old hall", "The floorboards gave tiny creaks", "a dim hallway lamp", "the ceiling corner"),
    "bedroom": Setting("bedroom", "the bedroom", "Moonlight slipped through the curtain", "a small night-light", "the ceiling above the bed"),
}

SPELLS = {
    "rhyme": Spell(
        "rhyme",
        "Velcro on the ceiling, ghost no longer fleeing; rhyme the right tune, and the shadows start easing.",
        "Tap the wall and turn once slow,",
        "Lift the ghost where soft winds blow,",
        "a sleepy silver shimmer",
    ),
    "song": Spell(
        "song",
        "Velcro high and ghostly white, come back down into the light; sing a round and gentle line, make the spooky room feel fine.",
        "Hum one note and count to three,",
        "Set the ghost where it can see,",
        "a warm and friendly glimmer",
    ),
    "chant": Spell(
        "chant",
        "Ceiling high, velcro near, let the frightened ghost draw near; rhyme and spin and let it be, a kinder ghost for you and me.",
        "Clap once softly, then again,",
        "Bring the ghost back down in plain,",
        "a little moonlit sparkle",
    ),
}

NAMES = ["Mina", "Lily", "Noah", "Sage", "June", "Theo", "Pia", "Owen"]
GENDERS = ["girl", "boy"]


@dataclass
class StoryParams:
    setting: str
    spell: str
    child_name: str
    child_gender: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for spid, spell in SPELLS.items():
            if is_reasonable(setting, spell):
                combos.append((sid, spid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with ceiling velcro and a rhyming transformation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=GENDERS)
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
              if (args.setting is None or c[0] == args.setting)
              and (args.spell is None or c[1] == args.spell)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, spell = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(GENDERS)
    name = args.name or rng.choice(NAMES)
    return StoryParams(setting, spell, name, gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-safe ghost story that includes the words "ceiling" and "velcro".',
        f"Tell a spooky-but-gentle story where {f['child'].id} sees a ghost stuck near the ceiling and uses a rhyme to help it change.",
        "Write a rhyming ghost story with a transformation at the end, so the scary thing becomes friendly.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child, ghost, setting, spell = f["child"], f["ghost"], f["setting"], f["spell"]
    qa = [
        ("Who is the story about?",
         f"It is about {child.id} and a ghost in {setting.place}. The ghost starts out stuck near the ceiling."),
        ("What did the child notice on the ceiling?",
         f"{child.id} noticed a strip of velcro holding the ghost up on the ceiling. That was the odd thing making the room feel spooky."),
        ("What did the child do to help?",
         f"{child.id} spoke a rhyme and called the ghost down with gentle words. The rhyme helped the ghost settle and change."),
    ]
    if ghost.transformed:
        qa.append((
            "What changed by the end?",
            "The ghost stopped being scary and turned into a friendly little visitor. The ceiling was empty again, so the room felt calm."
        ))
        qa.append((
            "Why did the room feel less spooky at the end?",
            "The ghost settled down, and its lonely feeling got smaller. Once it transformed, the ceiling no longer held a worrying shape."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is velcro?",
         "Velcro is a fastening material that sticks together in a rough-and-loopy way. People use it to hold things in place."),
        ("What is a ceiling?",
         "A ceiling is the top part of a room. It is above your head."),
        ("What is a rhyme?",
         "A rhyme is a pattern of words that sound alike at the ends. Rhymes can make a chant or song feel magical."),
        ("What is a transformation?",
         "A transformation is a change from one form or feeling into another. In stories, it can make something scary become kind."),
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
        if e.has_velcro:
            bits.append("has_velcro=True")
        if e.on_ceiling:
            bits.append("on_ceiling=True")
        if e.transformable:
            bits.append("transformable=True")
        if e.transformed:
            bits.append("transformed=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams("bedroom", "rhyme", "Mina", "girl"),
    StoryParams("attic", "song", "Theo", "boy"),
    StoryParams("hall", "chant", "Sage", "girl"),
]


def explain_rejection() -> str:
    return "(No story: the chosen setting/spell pair does not support the ceiling-velcro transformation.)"


ASP_RULES = r"""
reasonable(S, P) :- setting(S), spell(P), ceiling_story(S), rhymes(P).
on_ceiling(g) :- ghost(g), velcro(v), stuck(v, g), ceiling_scene.
spooky_room :- on_ceiling(g), lonely(g).
transformed(g) :- on_ceiling(g), settled(g).
ending_calm :- transformed(g).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        lines.append(asp.fact("ceiling_story", sid))
    for pid, sp in SPELLS.items():
        lines.append(asp.fact("spell", pid))
        lines.append(asp.fact("rhymes", pid))
    lines.append(asp.fact("ghost", "ghost"))
    lines.append(asp.fact("velcro", "velcro"))
    lines.append(asp.fact("stuck", "velcro", "ghost"))
    lines.append(asp.fact("ceiling_scene"))
    lines.append(asp.fact("lonely", "ghost"))
    return "\n".join(lines)


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonable/2."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    rc = 0
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: gate matches valid_combos() ({len(a)} combos).")
    else:
        print("MISMATCH in gate:")
        print(" only in asp:", sorted(a - b))
        print(" only in python:", sorted(b - a))
        rc = 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}")
        rc = 1
    return rc


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.setting], SPELLS[params.spell], params.child_name, params.child_gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
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
        print(asp_program(show="#show reasonable/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(", ".join(f"{s}/{p}" for s, p in asp_valid_combos()))
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
