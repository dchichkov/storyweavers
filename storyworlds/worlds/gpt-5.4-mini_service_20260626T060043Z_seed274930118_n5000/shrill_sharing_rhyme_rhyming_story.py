#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shrill_sharing_rhyme_rhyming_story.py
===============================================================================================================

A small story world about a child, a shrill interruption, and a shared rhyme
that turns into a cooperative ending.

The seed story idea:
- A child loves a rhyme/song/chant.
- Another child or a helper wants to share it.
- A shrill sound or voice interrupts.
- The characters negotiate sharing and finish together with a rhyming refrain.

The simulation tracks physical state (meters) and emotional state (memes).
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
    keeper: Optional[str] = None
    shared_with: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        self.meters.setdefault("noise", 0.0)
        self.meters.setdefault("together", 0.0)
        self.meters.setdefault("shiver", 0.0)
        self.memes.setdefault("joy", 0.0)
        self.memes.setdefault("worry", 0.0)
        self.memes.setdefault("share", 0.0)
        self.memes.setdefault("comfort", 0.0)
        self.memes.setdefault("frustration", 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    cozy: bool = True
    echoes: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class RhymeItem:
    id: str
    label: str
    phrase: str
    theme: str
    plural: bool = False
    shareable: bool = True


@dataclass
class Sound:
    id: str
    label: str
    kind: str
    loudness: str
    start: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    item: str
    sound: str
    name: str
    gender: str
    partner: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.sound_level: float = 0.0
        self.rhythm_ok: bool = False

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.sound_level = self.sound_level
        clone.rhythm_ok = self.rhythm_ok
        return clone


def _r_shrill(world: World) -> list[str]:
    out: list[str] = []
    if world.sound_level < THRESHOLD:
        return out
    if ("shrill",) in world.fired:
        return out
    world.fired.add(("shrill",))
    for c in world.characters():
        c.memes["worry"] += 1
        c.meters["shiver"] += 1
    out.append("The shrill sound made everyone flinch.")
    return out


def _r_share(world: World) -> list[str]:
    out: list[str] = []
    for c in world.characters():
        if c.memes["share"] < THRESHOLD:
            continue
        sig = ("share", c.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        c.memes["comfort"] += 1
        c.memes["frustration"] = max(0.0, c.memes["frustration"] - 1.0)
        out.append(f"{c.id} softened and chose to share.")
    return out


def _r_rhyme(world: World) -> list[str]:
    out: list[str] = []
    if not world.rhythm_ok:
        return out
    if ("rhyme",) in world.fired:
        return out
    world.fired.add(("rhyme",))
    for c in world.characters():
        c.meters["together"] += 1
        c.memes["joy"] += 1
    out.append("Their rhyme came out bright and light.")
    return out


CAUSAL_RULES = [
    _r_shrill,
    _r_share,
    _r_rhyme,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def rhyme_pairs() -> list[tuple[str, str]]:
    return [
        ("bright", "light"),
        ("day", "play"),
        ("song", "along"),
        ("near", "clear"),
        ("small", "all"),
    ]


PLACES = {
    "kitchen": Place(name="the kitchen", cozy=True, echoes=True, affords={"sharing", "rhyme"}),
    "playroom": Place(name="the playroom", cozy=True, echoes=False, affords={"sharing", "rhyme"}),
    "porch": Place(name="the porch", cozy=False, echoes=True, affords={"sharing", "rhyme"}),
    "library_corner": Place(name="the library corner", cozy=True, echoes=True, affords={"sharing", "rhyme"}),
}

ITEMS = {
    "book": RhymeItem(id="book", label="picture book", phrase="a picture book of simple rhymes", theme="rhyme", plural=False),
    "cards": RhymeItem(id="cards", label="rhyme cards", phrase="a stack of rhyme cards", theme="sharing", plural=True),
    "bell": RhymeItem(id="bell", label="little bell", phrase="a little bell for the rhyme game", theme="sound", plural=False),
    "drum": RhymeItem(id="drum", label="toy drum", phrase="a tiny toy drum", theme="rhythm", plural=False),
}

SOUNDS = {
    "shriek": Sound(id="shriek", label="shriek", kind="voice", loudness="shrill", start="gave a shrill shriek", tags={"shrill"}),
    "whistle": Sound(id="whistle", label="whistle", kind="sound", loudness="shrill", start="let out a shrill whistle", tags={"shrill"}),
    "squeal": Sound(id="squeal", label="squeal", kind="voice", loudness="shrill", start="made a shrill squeal", tags={"shrill"}),
}

GIRL_NAMES = ["Mia", "Lily", "Ava", "Nora", "Zoe", "Ella", "Maya", "Ivy"]
BOY_NAMES = ["Leo", "Noah", "Ben", "Theo", "Finn", "Max", "Eli", "Sam"]
TRAITS = ["gentle", "curious", "cheerful", "brave", "patient", "playful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, pl in PLACES.items():
        for item in ITEMS:
            for sound in SOUNDS:
                if "rhyme" in pl.affords and item in ITEMS:
                    combos.append((place, item, sound))
    return combos


def explain_rejection(place: str, item: str, sound: str) -> str:
    return f"(No story: the combination of {place}, {item}, and {sound} does not support a sharing-and-rhyme scene.)"


def explain_gender(item: str, gender: str) -> str:
    return f"(No story: the requested {item} story is not constrained by gender, but the explicit choice {gender} was incompatible here.)"


def build_world(params: StoryParams) -> World:
    place = PLACES[params.place]
    item = ITEMS[params.item]
    sound = SOUNDS[params.sound]
    world = World(place)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=["little", params.trait, "rhyming"],
    ))
    partner_name = "Parker" if params.partner == "friend" else "Aunt June"
    partner_type = "boy" if params.partner == "friend" and params.gender == "girl" else "girl"
    if params.partner == "helper":
        partner_type = "woman"
    partner = world.add(Entity(
        id=partner_name,
        kind="character",
        type=partner_type,
        traits=["kind", "helpful"],
    ))
    rhyme = world.add(Entity(
        id=item.id,
        label=item.label,
        phrase=item.phrase,
        kind="thing",
        type="thing",
        owner=hero.id,
        keeper=partner.id,
    ))
    world.facts.update(hero=hero, partner=partner, rhyme=rhyme, sound=sound, place=place, item=item)
    return world


def introduce(world: World) -> None:
    h = world.facts["hero"]
    item = world.facts["item"]
    world.say(f"{h.id} was a little {h.traits[1]} {h.type} who loved a good rhyme.")
    world.say(f"{h.id} had {item.phrase}, and {h.id} liked to share it with a friend.")
    world.say(f"At {world.place.name}, the air felt calm and ready for a sing-along.")


def conflict(world: World) -> None:
    h = world.facts["hero"]
    p = world.facts["partner"]
    s = world.facts["sound"]
    h.memes["frustration"] += 1
    world.sound_level = 1.0
    world.say(f"Then {p.id} {s.start}, and the sound was sharp and shrill.")
    propagate(world, narrate=True)
    world.say(f"{h.id} clapped hands over {h.pronoun('possessive')} ears, because the shrill note felt too loud.")


def share_and_fix(world: World) -> None:
    h = world.facts["hero"]
    p = world.facts["partner"]
    item = world.facts["item"]
    pair = random.choice(rhyme_pairs())
    h.memes["share"] += 1
    world.rhythm_ok = True
    propagate(world, narrate=True)
    world.say(f"{p.id} smiled and said, \"Let's share the {item.label} and sing together.\"")
    world.say(f"{h.id} nodded, and they tried a rhyme: \"{pair[0]}, {pair[1]}!\"")
    world.say(f"Then they answered with another line: \"{pair[2]}, {pair[3]}!\"")
    world.say(f"Their last rhyme was small and sweet: \"{pair[4]}, {pair[1]}!\"")
    h.memes["joy"] += 1
    p.memes["joy"] += 1


def end_scene(world: World) -> None:
    h = world.facts["hero"]
    p = world.facts["partner"]
    item = world.facts["item"]
    world.say(f"In the end, {h.id} and {p.id} shared {item.label} and sang until the room felt calm again.")
    world.say(f"The shrill sound was gone, and the rhyme floated gently through {world.place.name}.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    world.para()
    conflict(world)
    world.para()
    share_and_fix(world)
    world.para()
    end_scene(world)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short rhyming story for a young child about sharing a {f["item"].label} after a shrill interruption.',
        f'Tell a gentle story set in {f["place"].name} where {f["hero"].id} and {f["partner"].id} solve a noisy problem by sharing and rhyme.',
        f'Write a child-friendly story that includes a shrill sound, a shared rhyme, and a happy ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    h = world.facts["hero"]
    p = world.facts["partner"]
    item = world.facts["item"]
    s = world.facts["sound"]
    return [
        QAItem(
            question=f"What did {h.id} love to do with the {item.label}?",
            answer=f"{h.id} loved to share the {item.label} and make up rhymes with {p.id}.",
        ),
        QAItem(
            question=f"What made the moment feel shrill at first?",
            answer=f"{p.id} {s.start}, and the sharp sound made everyone flinch.",
        ),
        QAItem(
            question=f"How did {h.id} and {p.id} fix the problem?",
            answer=f"They shared the {item.label}, spoke kindly, and finished with a rhyme together.",
        ),
        QAItem(
            question=f"Where did the story happen?",
            answer=f"It happened at {world.place.name}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What does shrill mean?", answer="Shrill means a very sharp, high, piercing sound that can feel too loud or squeaky."),
        QAItem(question="What is sharing?", answer="Sharing means letting someone else use, hold, or enjoy something with you."),
        QAItem(question="What is a rhyme?", answer="A rhyme is a word or line that sounds like another one at the end, such as day and play."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(H) :- hero_name(H).
partner(P) :- partner_name(P).
item(I) :- rhyme_item(I).
shrill_event(S) :- sound(S), shrill(S).

shared_scene(H,P,I) :- hero(H), partner(P), item(I).
needs_fix(H,P) :- shrill_event(_), shared_scene(H,P,_).
happy_end(H,P,I) :- shared_scene(H,P,I), shared(I), rhyme_done.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
        for a in sorted(PLACES[pid].affords):
            lines.append(asp.fact("affords", pid, a))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("rhyme_item", iid))
        if item.plural:
            lines.append(asp.fact("plural_item", iid))
    for sid, sound in SOUNDS.items():
        lines.append(asp.fact("sound", sid))
        lines.append(asp.fact("shrill", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show shared_scene/3."))
    return sorted(set(asp.atoms(model, "shared_scene")))


def asp_verify() -> int:
    python_set = {(p, i, s) for p, i, s in valid_combos()}
    asp_set = set(valid_asp())
    if asp_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in ASP:", sorted(asp_set - python_set))
    print("only in Python:", sorted(python_set - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: sharing, rhyme, and a shrill interruption.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--sound", choices=SOUNDS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--partner", choices=["friend", "helper"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if args.place and args.place not in PLACES:
        raise StoryError("(No story: unknown place.)")
    if args.item and args.item not in ITEMS:
        raise StoryError("(No story: unknown item.)")
    if args.sound and args.sound not in SOUNDS:
        raise StoryError("(No story: unknown sound.)")
    combos = valid_combos()
    combos = [c for c in combos
              if args.place is None or c[0] == args.place
              if False else True]
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.item is None or c[1] == args.item)
              and (args.sound is None or c[2] == args.sound)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, item, sound = rng.choice(combos)
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    partner = args.partner or rng.choice(["friend", "helper"])
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, sound=sound, name=name, gender=gender, partner=partner, trait=trait)


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
    StoryParams(place="kitchen", item="book", sound="shriek", name="Mia", gender="girl", partner="friend", trait="curious"),
    StoryParams(place="playroom", item="cards", sound="whistle", name="Leo", gender="boy", partner="helper", trait="playful"),
    StoryParams(place="library_corner", item="drum", sound="squeal", name="Nora", gender="girl", partner="friend", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show shared_scene/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        triples = valid_asp()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print(" ", t)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
