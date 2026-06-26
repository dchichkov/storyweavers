#!/usr/bin/env python3
"""
Storyworld: meym_saber_suspense_whodunit
========================================

A small, self-contained whodunit-style suspense world about a missing saber,
a few plausible suspects, and a careful little investigation that ends with the
truth coming to light.

The seed words "meym" and "saber" are included in the domain vocabulary and
story surface, but the world itself is a fully simulated, state-driven mystery.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"           # character | thing | clue | place
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    hidden_in: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for k in ["dust", "scratches", "doubt", "fear", "calm", "confidence", "relief", "anxiety"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the old museum"
    rooms: list[str] = field(default_factory=lambda: ["front hall", "lamp room", "archive", "gallery"])
    noise_level: str = "quiet"


@dataclass
class Suspect:
    id: str
    label: str
    motive: str
    alibi_room: str
    suspicious: bool = False


@dataclass
class StoryParams:
    room: str
    culprit: str
    hiding_place: str
    witness: str
    name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.suspects: dict[str, Suspect] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.suspects = copy.deepcopy(self.suspects)
        c.fired = set(self.fired)
        return c


# ---------------------------------------------------------------------------
# Content registries
# ---------------------------------------------------------------------------

SETTING = Setting()

ROOMS = {
    "front hall": "the front hall",
    "lamp room": "the lamp room",
    "archive": "the archive",
    "gallery": "the gallery",
}

HIDING_PLACES = {
    "curtain": "behind the heavy curtain",
    "cabinet": "inside the glass cabinet",
    "crate": "under the dusty storage crate",
    "bench": "beneath the long wooden bench",
}

SUSPECTS = {
    "curator": Suspect("curator", "the curator", "wanted the saber returned to its case", "archive"),
    "guard": Suspect("guard", "the night guard", "wanted a quiet shift", "front hall"),
    "restorer": Suspect("restorer", "the restorer", "needed time alone with the metal displays", "lamp room"),
    "meym": Suspect("meym", "meym", "was searching for a lost key ring", "gallery"),
}

# The missing object is always a saber.
SABER_PHRASE = "a silver saber with a carved handle"


@dataclass
class CluePlan:
    room: str
    sign: str
    points_to: str


CLUE_PLANS = {
    "curtain": CluePlan("gallery", "a strip of dark cloth snagged on the hilt", "curator"),
    "cabinet": CluePlan("archive", "a faint polish mark on the floor", "restorer"),
    "crate": CluePlan("front hall", "a boot print beside the crate", "guard"),
    "bench": CluePlan("lamp room", "a scrap of soft paper from a key tag", "meym"),
}


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for room in ROOMS:
        for hiding in HIDING_PLACES:
            for witness in SUSPECTS:
                if hiding == "cabinet" and room != "archive":
                    continue
                if hiding == "curtain" and room != "gallery":
                    continue
                if hiding == "crate" and room != "front hall":
                    continue
                if hiding == "bench" and room != "lamp room":
                    continue
                out.append((room, hiding, witness))
    return out


def explain_invalid(room: str, hiding: str, witness: str) -> str:
    if hiding == "cabinet" and room != "archive":
        return "(No story: the cabinet hiding place only fits the archive room.)"
    if hiding == "curtain" and room != "gallery":
        return "(No story: the curtain hiding place only fits the gallery.)"
    if hiding == "crate" and room != "front hall":
        return "(No story: the crate hiding place only fits the front hall.)"
    if hiding == "bench" and room != "lamp room":
        return "(No story: the bench hiding place only fits the lamp room.)"
    return "(No story: that combination does not make a sensible mystery.)"


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------

def intro_line(hero: Entity) -> str:
    return f"{hero.id} was a careful little investigator who never liked a puzzle left unsolved."


def setting_line(room: str) -> str:
    return f"That evening, the old museum was quiet, and {ROOMS[room]} felt oddly still."


def missing_line(hero: Entity) -> str:
    return f"Then someone noticed the saber was gone, and everyone went quiet at once."


def suspense_line(hero: Entity, witness: str) -> str:
    w = SUSPECTS[witness]
    return f"{hero.id} watched {w.label} closely, because even a small glance can mean something in a whodunit."


def search_line(room: str, hiding: str, clue_text: str) -> str:
    return f"In {ROOMS[room]}, {clue_text} led the search toward {HIDING_PLACES[hiding]}."


def reveal_line(culprit: str, hiding: str) -> str:
    return f"In the end, the saber was found {HIDING_PLACES[hiding]}, and the trail pointed straight to {SUSPECTS[culprit].label}."


def ending_line(hero: Entity) -> str:
    return f"{hero.id} closed the case with a calm smile, and the museum felt safe again."


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(SETTING)
    hero = world.add(Entity(id=params.name, kind="character", type="girl"))
    if params.name.lower() in {"meym"}:
        hero.type = "girl"
    curator = world.add(Entity(id="curator", kind="character", type="woman", label="the curator"))
    guard = world.add(Entity(id="guard", kind="character", type="man", label="the night guard"))
    restorer = world.add(Entity(id="restorer", kind="character", type="woman", label="the restorer"))

    saber = world.add(Entity(
        id="saber",
        kind="thing",
        type="saber",
        label="saber",
        phrase=SABER_PHRASE,
        owner="curator",
        hidden_in=params.hiding_place,
    ))
    clue = world.add(Entity(
        id="clue",
        kind="clue",
        type="clue",
        label="clue",
        phrase=CLUE_PLANS[params.hiding_place].sign,
    ))

    world.suspects = SUSPECTS.copy()

    # Act 1
    world.say(intro_line(hero))
    world.say(f"{hero.id} had heard of the museum's famous saber, and tonight it mattered.")
    world.para()
    world.say(setting_line(params.room))
    world.say(missing_line(hero))

    # Act 2
    world.para()
    world.say(suspense_line(hero, params.witness))
    world.say(f"{hero.id} looked at the floor, the case, and the shadows, one by one.")
    world.say(f"A small clue waited nearby: {clue.phrase}.")
    world.say(search_line(params.room, params.hiding_place, clue.phrase))

    # Suspense meters
    hero.memes["doubt"] += 1
    hero.memes["confidence"] += 1
    world.get(params.culprit).memes["anxiety"] += 1

    # Act 3
    world.para()
    world.say(reveal_line(params.culprit, params.hiding_place))
    world.say(f"The evidence made sense at last: {CLUE_PLANS[params.hiding_place].sign}.")
    world.say(ending_line(hero))

    world.facts = {
        "hero": hero,
        "curator": curator,
        "guard": guard,
        "restorer": restorer,
        "saber": saber,
        "clue": clue,
        "culprit": params.culprit,
        "room": params.room,
        "hiding_place": params.hiding_place,
        "witness": params.witness,
    }
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short whodunit story for a child in a quiet museum with a missing saber.',
        f"Tell a suspenseful mystery where {f['hero'].id} notices the saber is missing in {ROOMS[f['room']]}.",
        f"Write a gentle detective story that includes meym and the word saber, and ends with the truth found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    culprit = SUSPECTS[f["culprit"]]
    room = ROOMS[f["room"]]
    hiding = HIDING_PLACES[f["hiding_place"]]
    witness = SUSPECTS[f["witness"]]

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a careful little investigator who helps solve the missing saber mystery.",
        ),
        QAItem(
            question=f"What was missing in the museum?",
            answer=f"The missing object was {SABER_PHRASE}.",
        ),
        QAItem(
            question=f"Where did the mystery feel most tense?",
            answer=f"It felt most tense in {room}, where the quiet made every clue seem important.",
        ),
        QAItem(
            question=f"Who looked suspicious in the story?",
            answer=f"{culprit.label} looked suspicious because the clue pointed toward {hiding}.",
        ),
        QAItem(
            question=f"What clue helped the search?",
            answer=f"The clue was {CLUE_PLANS[f['hiding_place']].sign}, and it helped lead the search in the right direction.",
        ),
        QAItem(
            question=f"Why did {hero.id} keep watching {witness.label}?",
            answer=f"{hero.id} kept watching {witness.label} because in a whodunit, even a small glance can matter, and {witness.label} was part of the mystery.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a saber?",
            answer="A saber is a curved sword, often used as a ceremonial weapon or in old stories.",
        ),
        QAItem(
            question="What is a clue?",
            answer="A clue is a small piece of information that helps solve a mystery.",
        ),
        QAItem(
            question="What does suspense mean?",
            answer="Suspense is the nervous feeling that something important is about to be revealed.",
        ),
        QAItem(
            question="What is a whodunit?",
            answer="A whodunit is a mystery story where the reader wonders who did the puzzling thing until the end.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== world qa ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
room_valid(R) :- room(R).
hide_valid(H) :- hiding_place(H).

valid(R,H,W) :- room_valid(R), hide_valid(H), witness(W),
                (H = cabinet -> R = archive ; true),
                (H = curtain -> R = gallery ; true),
                (H = crate -> R = front_hall ; true),
                (H = bench -> R = lamp_room ; true).

#show valid/3.
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for room in ROOMS:
        lines.append(asp.fact("room", room.replace(" ", "_")))
    for hid in HIDING_PLACES:
        lines.append(asp.fact("hiding_place", hid))
    for w in SUSPECTS:
        lines.append(asp.fact("witness", w))
    return "\n".join(lines)

def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))

def asp_verify() -> int:
    py = set((r.replace("_", " "), h, w) for r, h, w in valid_combos())
    try:
        cl = set(asp_valid_combos())
    except Exception as e:
        print(f"ASP unavailable or failed: {e}")
        return 1
    if py == cl:
        print(f"OK: ASP parity matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print(" only in python:", sorted(py - cl))
    print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Parameters and generation
# ---------------------------------------------------------------------------

def valid_params() -> list[tuple[str, str, str]]:
    return valid_combos()

def explain_witness(witness: str) -> str:
    return f"(No story: the witness choice '{witness}' does not fit this little mystery.)"

def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.room and args.hiding_place:
        if (args.room, args.hiding_place, args.witness or "meym") not in valid_combos():
            raise StoryError(explain_invalid(args.room, args.hiding_place, args.witness or "meym"))
    combos = valid_combos()
    combos = [c for c in combos if (args.room is None or c[0] == args.room)
                                and (args.hiding_place is None or c[1] == args.hiding_place)
                                and (args.witness is None or c[2] == args.witness)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    room, hiding, witness = rng.choice(sorted(combos))
    name = args.name or "meym"
    return StoryParams(room=room, culprit={"curtain":"curator","cabinet":"restorer","crate":"guard","bench":"meym"}[hiding],
                       hiding_place=hiding, witness=witness, name=name, seed=None)

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Suspenseful whodunit storyworld about a missing saber.")
    ap.add_argument("--room", choices=list(ROOMS))
    ap.add_argument("--hiding-place", choices=list(HIDING_PLACES), dest="hiding_place")
    ap.add_argument("--witness", choices=list(SUSPECTS))
    ap.add_argument("--name")
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
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.kind:7}/{e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(room="gallery", culprit="curator", hiding_place="curtain", witness="meym", name="meym"),
    StoryParams(room="archive", culprit="restorer", hiding_place="cabinet", witness="guard", name="Mina"),
    StoryParams(room="front hall", culprit="guard", hiding_place="crate", witness="curator", name="Nia"),
    StoryParams(room="lamp room", culprit="meym", hiding_place="bench", witness="restorer", name="Meym"),
]


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
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        try:
            import storyworlds.asp as asp
            model = asp.one_model(asp_program())
            print(sorted(set(asp.atoms(model, "valid"))))
        except Exception as e:
            raise SystemExit(str(e))
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
            header = f"### {sample.params.name}: {sample.params.room} / {sample.params.hiding_place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
