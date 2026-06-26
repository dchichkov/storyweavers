#!/usr/bin/env python3
"""
storyworlds/worlds/teensy_reconciliation_mystery_to_solve_rhyme_fairy.py
==========================================================================
A tiny fairy-tale storyworld about a teensy misunderstanding, a mystery to
solve, and a rhyme that helps two friends reconcile.

The domain premise:
- A little fairy helper loses or misplaces a prized object in a magical place.
- A gentle mystery arises: who moved it, and where did it go?
- The search reveals a simple misunderstanding rather than a true theft.
- A rhyme, chant, or song becomes the tool that leads to reconciliation.

The simulated world uses:
- physical meters: distance, hiddenness, glow, dust, wobble, etc.
- emotional memes: worry, curiosity, kindness, hurt, relief, friendship.

The story is child-facing, concrete, and state-driven.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "fairy", "queen"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "elf", "knight"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    magic: str
    cozy: str
    affords: set[str] = field(default_factory=set)


@dataclass
class Clue:
    id: str
    phrase: str
    hint: str
    location: str
    hiddenness: str
    fits_mystery: set[str] = field(default_factory=set)


@dataclass
class Misunderstanding:
    id: str
    source: str
    sign: str
    turn: str
    apology: str
    rhyme: str
    truth: str


@dataclass
class World:
    setting: Setting

    def __post_init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.events: list[str] = []

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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        clone.events = list(self.events)
        return clone


def _add_meter(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amt


def _add_meme(ent: Entity, key: str, amt: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amt


def _story_state_line(hero: Entity, friend: Entity, clue: Entity, obj: Entity) -> str:
    return (
        f"In {hero.id}'s little corner of the {hero.meters.get('home', 0) and 'home' or 'glade'}, "
        f"{hero.id} had a mystery to solve about {obj.phrase}."
    )


def _do_search(world: World, hero: Entity, friend: Entity, clue: Entity, obj: Entity) -> None:
    _add_meme(hero, "curiosity", 1)
    _add_meme(friend, "worry", 1)
    _add_meter(hero, "steps", 1)
    _add_meter(hero, "search", 1)
    world.say(
        f"{hero.id} and {friend.id} tiptoed through the {world.setting.place}, "
        f"looking for {obj.label}."
    )
    world.say(
        f"They peered under toadstools, behind moonlit stones, and beside the dew-bright fern."
    )
    world.events.append("search")


def _reveal(world: World, hero: Entity, friend: Entity, clue: Entity, obj: Entity, mixup: Misunderstanding) -> None:
    _add_meter(clue, "found", 1)
    _add_meme(hero, "relief", 1)
    _add_meme(friend, "relief", 1)
    _add_meme(friend, "kindness", 1)
    world.say(
        f"At last, they found {obj.phrase} where the {mixup.source} had left it, near the {clue.location}."
    )
    world.say(
        f"It was not a taking at all, only a small mix-up: {mixup.sign}."
    )
    world.say(
        f"{hero.id} smiled, and {friend.id} did too, because the truth was gentle."
    )
    world.events.append("reveal")


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("hurt", 0) >= THRESHOLD and e.memes.get("kindness", 0) >= THRESHOLD:
            sig = ("settle", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["hurt"] = 0.0
            e.memes["reconcile"] = 1.0
            out.append(f"{e.id}'s hurt settled like a leaf on still water.")
    return out


def propagate(world: World) -> None:
    changed = True
    while changed:
        changed = False
        for fn in (_r_settle,):
            sents = fn(world)
            if sents:
                changed = True
                for s in sents:
                    world.say(s)


def reasonableness_gate(setting: Setting, clue: Clue, mixup: Misunderstanding) -> bool:
    return clue.id in mixup.truth and clue.location in setting.affords and clue.hiddenness in {"low", "mid", "high"}


def story_at_risk(clue: Clue, obj: Entity) -> bool:
    return clue.location == obj.location or clue.id in clue.fits_mystery


def select_turn(clue: Clue, mixup: Misunderstanding, obj: Entity) -> bool:
    return story_at_risk(clue, obj) and mixup.source in {"pixie", "wind", "brook", "mouse"}


SETTINGS = {
    "glade": Setting(
        place="glade",
        magic="silver fireflies",
        cozy="mossy hollows",
        affords={"search", "sing"},
    ),
    "orchard": Setting(
        place="orchard",
        magic="apple-blossom sparkles",
        cozy="ladder steps and root nooks",
        affords={"search", "sing"},
    ),
    "pond": Setting(
        place="pond",
        magic="moon-ripple glow",
        cozy="reeds and lily pads",
        affords={"search", "sing"},
    ),
}

OBJECTS = {
    "crown": Entity(
        id="crown",
        kind="thing",
        type="crown",
        label="tiny crown",
        phrase="a teensy golden crown",
        location="mossy hollow",
    ),
    "bell": Entity(
        id="bell",
        kind="thing",
        type="bell",
        label="silver bell",
        phrase="a bright silver bell",
        location="lily pad",
    ),
    "stone": Entity(
        id="stone",
        kind="thing",
        type="stone",
        label="song-stone",
        phrase="a small rune-stone",
        location="root nook",
    ),
}

CLUES = {
    "mossy hollow": Clue(
        id="mossy hollow",
        phrase="a tuft of moss",
        hint="soft green fuzz",
        location="mossy hollow",
        hiddenness="low",
        fits_mystery={"crown"},
    ),
    "lily pad": Clue(
        id="lily pad",
        phrase="a flat lily pad",
        hint="round and shiny",
        location="lily pad",
        hiddenness="mid",
        fits_mystery={"bell"},
    ),
    "root nook": Clue(
        id="root nook",
        phrase="a curving root nook",
        hint="shady and snug",
        location="root nook",
        hiddenness="mid",
        fits_mystery={"stone"},
    ),
}

MISUNDERSTANDINGS = {
    "pixie": Misunderstanding(
        id="pixie",
        source="pixie",
        sign="the pixie had borrowed the crown to wear in a dance",
        turn="the crown was only borrowed",
        apology="the pixie fluttered back at once and bowed",
        rhyme="Borrowed bright, returned by night",
        truth="crown",
    ),
    "wind": Misunderstanding(
        id="wind",
        source="wind",
        sign="the wind had blown the bell onto a lily pad",
        turn="the bell had simply blown away",
        apology="the breeze sighed sorry through the reeds",
        rhyme="Wind may play, but it will say",
        truth="bell",
    ),
    "mouse": Misunderstanding(
        id="mouse",
        source="mouse",
        sign="the mouse had tucked the stone beside warm crumbs for safekeeping",
        turn="the stone was kept safe, not stolen",
        apology="the mouse returned with tiny, careful paws",
        rhyme="Safe and near, not gone from here",
        truth="stone",
    ),
}

HERO_NAMES = ["Lina", "Miri", "Pia", "Tessa", "Nola", "Faye", "Wren", "Elin"]
FRIEND_NAMES = ["Pip", "Moss", "Bram", "Lumi", "Tink", "Rue", "Vale", "Clover"]
HERO_TYPES = {"girl": "girl", "boy": "boy", "fairy": "fairy"}
TYPES = ["girl", "boy", "fairy"]


@dataclass
class StoryParams:
    setting: str
    object: str
    misunderstanding: str
    name: str
    friend: str
    kind: str
    seed: Optional[int] = None


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A teensy fairy-tale mystery with rhyme and reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--misunderstanding", choices=MISUNDERSTANDINGS)
    ap.add_argument("--kind", choices=TYPES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for o, obj in OBJECTS.items():
            for m, mix in MISUNDERSTANDINGS.items():
                if o in mix.truth:
                    out.append((s, o, m))
    return out


def explain_rejection(obj: Entity, mix: Misunderstanding) -> str:
    return f"(No story: {mix.source} doesn't plausibly fit the mystery around {obj.label}.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.object and args.misunderstanding:
        if args.object not in MISUNDERSTANDINGS[args.misunderstanding].truth:
            raise StoryError(explain_rejection(OBJECTS[args.object], MISUNDERSTANDINGS[args.misunderstanding]))
    combos = [
        c for c in valid_combos()
        if (args.setting is None or c[0] == args.setting)
        and (args.object is None or c[1] == args.object)
        and (args.misunderstanding is None or c[2] == args.misunderstanding)
    ]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, obj_id, mix_id = rng.choice(sorted(combos))
    kind = args.kind or rng.choice(TYPES)
    name = args.name or rng.choice(HERO_NAMES)
    friend = args.friend or rng.choice(FRIEND_NAMES)
    return StoryParams(setting=setting, object=obj_id, misunderstanding=mix_id, name=name, friend=friend, kind=kind)


def tell(params: StoryParams) -> World:
    setting = SETTINGS[params.setting]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.kind))
    friend = world.add(Entity(id=params.friend, kind="character", type="fairy" if params.kind != "fairy" else "girl"))
    obj_cfg = OBJECTS[params.object]
    obj = world.add(Entity(
        id=params.object,
        kind="thing",
        type=obj_cfg.type,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        location=obj_cfg.location,
        owner=hero.id,
        caretaker=friend.id,
    ))
    clue = world.add(Entity(
        id=f"clue_{params.object}",
        kind="thing",
        type="clue",
        label=CLUES[obj_cfg.location].phrase,
        phrase=CLUES[obj_cfg.location].hint,
        location=CLUES[obj_cfg.location].location,
    ))
    mix = MISUNDERSTANDINGS[params.misunderstanding]

    _add_meme(hero, "love", 1)
    _add_meme(friend, "care", 1)
    _add_meter(obj, "hiddenness", 1)
    world.say(
        f"Once in a teensy fairy place, {hero.id} kept {obj.phrase} and treasured it dearly."
    )
    world.say(
        f"The {setting.place} shimmered with {setting.magic}, and the air felt full of wonder."
    )
    world.para()
    world.say(
        f"Then one quiet evening, {hero.id} could not find {obj.label} at all."
    )
    _add_meme(hero, "worry", 1)
    _add_meme(hero, "hurt", 1)
    _add_meme(friend, "worry", 1)
    world.say(
        f"{hero.id} and {friend.id} began a mystery to solve, with careful eyes and tiny feet."
    )
    _do_search(world, hero, friend, clue, obj)
    world.para()
    _reveal(world, hero, friend, clue, obj, mix)
    world.say(
        f"{mix.apology}, and {hero.id} listened with a soft, still face."
    )
    world.say(
        f"To mend the hurt, {hero.id} sang a rhyme: '{mix.rhyme},' and {friend.id} answered, 'We are friends again.'"
    )
    _add_meme(hero, "kindness", 1)
    _add_meme(friend, "kindness", 1)
    propagate(world)
    world.say(
        f"By the end, the {setting.place} felt warm again, and {obj.label} gleamed safely where it belonged."
    )
    world.facts.update(hero=hero, friend=friend, obj=obj, clue=clue, mix=mix, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale for a child about a teensy mystery involving "{f["obj"].label}".',
        f"Tell a gentle story where {f['hero'].id} and {f['friend'].id} solve a mystery and reconcile with a rhyme.",
        f"Write a magical story set in the {f['setting'].place} that ends with friends making peace.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    friend: Entity = f["friend"]
    obj: Entity = f["obj"]
    mix: Misunderstanding = f["mix"]
    setting: Setting = f["setting"]
    return [
        QAItem(
            question=f"What was the mystery {hero.id} had to solve?",
            answer=f"{hero.id} had to solve the mystery of where {obj.phrase} had gone in the {setting.place}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} look for {obj.label}?",
            answer=f"{friend.id} helped {hero.id} look carefully through the {setting.place}.",
        ),
        QAItem(
            question=f"What did the problem turn out to be?",
            answer=f"It turned out to be a small misunderstanding: {mix.turn}.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} make peace at the end?",
            answer=f"They made peace by speaking kindly and singing a rhyme together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a mystery to solve?",
            answer="A mystery to solve is a question about something unknown, so people look for clues to find the answer.",
        ),
        QAItem(
            question="What does a rhyme do in a fairy tale?",
            answer="A rhyme can make words sound musical and help characters remember a chant, song, or promise.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and become friendly again.",
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
    out = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.location:
            bits.append(f"location={e.location}")
        if e.held_by:
            bits.append(f"held_by={e.held_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id:12} ({e.type:8}) " + " ".join(bits))
    out.append(f"  events: {world.events}")
    return "\n".join(out)


ASP_RULES = r"""
% A mystery is valid when the clue location matches the missing object's place.
mystery_valid(S, O, M) :- setting(S), object(O), misunderstanding(M), truth(M, O).

% A reconciliation story requires a valid mystery plus a rhyme and a peaceful ending.
reconcile_story(S, O, M) :- mystery_valid(S, O, M), rhyme(M), apology(M).

% Show the curated set of valid story combinations.
valid_story(S, O, M) :- reconcile_story(S, O, M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("obj_location", oid, o.location.replace(" ", "_")))
    for mid, m in MISUNDERSTANDINGS.items():
        lines.append(asp.fact("misunderstanding", mid))
        lines.append(asp.fact("truth", mid, m.truth))
        lines.append(asp.fact("rhyme", mid))
        lines.append(asp.fact("apology", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


CURATED = [
    StoryParams(setting="glade", object="crown", misunderstanding="pixie", name="Lina", friend="Pip", kind="girl"),
    StoryParams(setting="orchard", object="bell", misunderstanding="wind", name="Miri", friend="Lumi", kind="fairy"),
    StoryParams(setting="pond", object="stone", misunderstanding="mouse", name="Wren", friend="Clover", kind="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        if args.all:
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.object} / {p.misunderstanding}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
