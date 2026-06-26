#!/usr/bin/env python3
"""
A tiny pirate-tale storyworld about a ravenous crew, a spiritual lesson,
and a hard-won choice to share.

Premise:
- A small pirate crew sails with one hungry hero.
- The hero wants treasure, but the bigger need is food.
- A spiritual sign on the sea points the crew toward mercy and sharing.
- The tale ends with a lesson learned: hunger is eased by generosity, not greed.
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
# Domain model
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "brother", "pirate"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the little pirate ship"
    affords: set[str] = field(default_factory=set)


@dataclass
class Want:
    id: str
    verb: str
    gerund: str
    urge: str
    hunger: str
    remedy: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Treasure:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False


@dataclass
class Comfort:
    id: str
    label: str
    helps: set[str]
    prep: str
    tail: str
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "ship": Setting(place="the little pirate ship", affords={"sail", "sing", "share"}),
    "island": Setting(place="the windy island shore", affords={"search", "share"}),
    "harbor": Setting(place="the bright harbor dock", affords={"dock", "share"}),
}

WANTS = {
    "plunder": Want(
        id="plunder",
        verb="plunder the chest",
        gerund="plundering chests",
        urge="rush for the chest",
        hunger="ravenous hunger",
        remedy="a full belly",
        tags={"treasure", "greed"},
    ),
    "feast": Want(
        id="feast",
        verb="eat the stew",
        gerund="eating stew",
        urge="grab the pot",
        hunger="ravenous hunger",
        remedy="warm soup",
        tags={"food", "hunger"},
    ),
    "sing": Want(
        id="sing",
        verb="sing sea songs",
        gerund="singing sea songs",
        urge="start a tune",
        hunger="restless feeling",
        remedy="a calmer heart",
        tags={"music", "hope"},
    ),
}

TREASURES = {
    "gold": Treasure(label="gold coins", phrase="a tin cup of gold coins", type="coins", region="hands", plural=True),
    "bread": Treasure(label="bread", phrase="a loaf of warm bread", type="bread", region="hands"),
    "map": Treasure(label="map", phrase="a folded treasure map", type="map", region="hands"),
}

COMFORTS = [
    Comfort(id="meal", label="a shared meal", helps={"food", "hunger"}, prep="share the stew with the whole crew", tail="shared the stew with the whole crew", plural=False),
    Comfort(id="prayer", label="a prayer", helps={"hope", "greed"}, prep="pause for a quiet prayer and a deep breath", tail="paused for a quiet prayer and a deep breath"),
    Comfort(id="song", label="a sea song", helps={"hope", "music"}, prep="sing a soft sea song together", tail="sang a soft sea song together"),
]

NAMES = ["Mara", "Finn", "Jory", "Tessa", "Nell", "Pip", "Rory", "Sana"]
ROLES = ["captain", "mate", "sailor", "deckhand"]
TRAITS = ["brave", "lively", "stubborn", "kind", "spirited"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    want: str
    treasure: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def want_at_risk(want: Want, treasure: Treasure) -> bool:
    return (want.id == "feast" and treasure.label == "bread") or (want.id == "plunder" and treasure.label == "gold coins") or (want.id == "sing" and treasure.label == "map")


def select_comfort(want: Want, treasure: Treasure) -> Optional[Comfort]:
    if want.id == "feast" and treasure.label == "bread":
        return next(c for c in COMFORTS if c.id == "meal")
    if want.id == "plunder" and treasure.label == "gold coins":
        return next(c for c in COMFORTS if c.id == "prayer")
    if want.id == "sing" and treasure.label == "map":
        return next(c for c in COMFORTS if c.id == "song")
    return None


def explain_rejection(want: Want, treasure: Treasure) -> str:
    return (
        f"(No story: the chosen want and treasure do not make a clear pirate problem. "
        f"Try ravenous hunger with bread, or greedy plundering with gold coins.)"
    )


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def predict_loss(world: World, hero: Entity, want: Want, treasure_id: str) -> bool:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    if want.id == "feast":
        hero2.meters["hunger"] = 0
        return False
    if want.id == "plunder":
        return True
    return False


def tell(setting: Setting, want: Want, treasure_cfg: Treasure, hero_name: str, role: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="pirate", label=role, memes={"hunger": 1.5, "wonder": 1.0}))
    crew = world.add(Entity(id="Crew", kind="character", type="pirate", label="the crew"))
    treasure = world.add(Entity(id="treasure", type=treasure_cfg.type, label=treasure_cfg.label, phrase=treasure_cfg.phrase, owner=hero.id, plural=treasure_cfg.plural))

    # Act 1
    world.say(f"{hero_name} was a {trait} {role} aboard {setting.place}.")
    world.say(f"{hero.pronoun('possessive').capitalize()} belly felt ravenous, and {hero_name} kept thinking about {want.gerund}.")
    world.say(f"That day, the crew had found {treasure.phrase}, and {hero_name} loved its shine.")

    # Act 2
    world.para()
    world.say(f"By afternoon, the ship rocked softly, and {hero_name} wanted to {want.verb}.")
    if want.id == "feast":
        world.say(f"But {hero.pronoun('possessive')} ravenous hunger was louder than manners, and {hero_name} reached for the stew.")
    elif want.id == "plunder":
        world.say(f"But {hero.pronoun('possessive')} ravenous hunger twisted into greed, and {hero_name} reached for the gold.")
    else:
        world.say(f"But a strange stillness came over the deck, as if the sea wanted {hero_name} to listen first.")
    world.say(f"Then the water around the ship flashed bright, like a spiritual sign.")

    if want.id == "plunder":
        world.say(f"The captain said, \"A full chest does not teach a full heart.\"")
    elif want.id == "feast":
        world.say(f"The cook said, \"A hungry crew can grow gentle when the pot is shared.\"")
    else:
        world.say(f"The captain said, \"A quiet heart can hear the sea's lesson.\"")

    # Act 3
    world.para()
    comfort = select_comfort(want, treasure_cfg)
    if comfort is None:
        raise StoryError(explain_rejection(want, treasure_cfg))

    if want.id == "feast":
        hero.meters["hunger"] = 0
        hero.memes["joy"] = 1.0
        world.say(f"{hero_name} paused, and the crew chose to {comfort.tail}.")
        world.say(f"Once they ate together, {hero_name}'s ravenous hunger faded, and {hero_name} smiled at the crumb-free deck.")
    elif want.id == "plunder":
        hero.memes["greed"] = 0.0
        hero.memes["peace"] = 1.0
        world.say(f"{hero_name} paused, and the crew chose to {comfort.tail}.")
        world.say(f"After the prayer, {hero_name} left the gold alone and felt lighter than before.")
    else:
        hero.memes["peace"] = 1.0
        world.say(f"{hero_name} paused, and the crew chose to {comfort.tail}.")
        world.say(f"After the song, {hero_name} remembered the map, the moon, and the kindness in the crew's eyes.")

    world.say(f"That was the lesson learned: on a pirate ship, a spiritual moment can calm a ravenous heart.")
    world.facts.update(hero=hero, crew=crew, treasure=treasure, want=want, setting=setting, comfort=comfort, resolved=True)
    return world


# ---------------------------------------------------------------------------
# Content selection
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for want_id, want in WANTS.items():
            for treasure_id, treasure in TREASURES.items():
                if want_at_risk(want, treasure) and select_comfort(want, treasure):
                    combos.append((place, want_id, treasure_id))
    return combos


def valid_stories() -> list[tuple[str, str, str]]:
    return valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.want and args.treasure:
        want = WANTS[args.want]
        treasure = TREASURES[args.treasure]
        if not (want_at_risk(want, treasure) and select_comfort(want, treasure)):
            raise StoryError(explain_rejection(want, treasure))

    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.want is None or c[1] == args.want)
              and (args.treasure is None or c[2] == args.treasure)]
    if not combos:
        raise StoryError("(No valid pirate story matches the given options.)")

    place, want_id, treasure_id = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    trait = args.trait or rng.choice(TRAITS)
    return StoryParams(place=place, want=want_id, treasure=treasure_id, name=name, role=role, trait=trait)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short pirate tale for a child about a ravenous sailor who learns a spiritual lesson.',
        f"Tell a gentle pirate story where {f['hero'].id} is a {f['hero'].label} on {f['setting'].place} and must choose between {f['want'].verb} and sharing.",
        "Write a small sea adventure that ends with a lesson learned and a kinder choice.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    want = f["want"]
    treasure = f["treasure"]
    comfort = f["comfort"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.label} pirate with a {hero.pronoun('possessive')} {'ravenous' if hero.meters.get('hunger', 0) > 0 else 'calm'} belly.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {want.verb}, because {hero.pronoun('possessive')} hunger and longing for {treasure.label} were pulling hard.",
        ),
        QAItem(
            question=f"What helped {hero.id} make a better choice?",
            answer=f"{comfort.label} helped, and the crew chose a kinder way that matched the spiritual sign on the sea.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn?",
            answer=f"{hero.id} learned that a ravenous heart can settle down when the crew shares, pauses, and listens for a wiser path.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pirate ship?",
            answer="A pirate ship is a boat used by pirates to sail, carry supplies, and search the sea.",
        ),
        QAItem(
            question="What does ravenous mean?",
            answer="Ravenous means very, very hungry.",
        ),
        QAItem(
            question="What does spiritual mean?",
            answer="Spiritual means connected to the spirit, beliefs, or a deep feeling that helps a person think about what is right.",
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
want_at_risk(W, T) :- want(W), treasure(T), risk_pair(W, T).
has_fix(W, T) :- want_at_risk(W, T), comfort(C), fixes(C, W, T).
valid(Place, W, T) :- setting(Place), want(W), treasure(T), want_at_risk(W, T), has_fix(W, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in SETTINGS:
        lines.append(asp.fact("setting", p))
    for wid, want in WANTS.items():
        lines.append(asp.fact("want", wid))
        for tag in sorted(want.tags):
            lines.append(asp.fact("want_tag", wid, tag))
    for tid, tr in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("treasure_label", tid, tr.label))
    for c in COMFORTS:
        lines.append(asp.fact("comfort", c.id))
        for h in sorted(c.helps):
            lines.append(asp.fact("fixes", c.id, "feast" if h == "hunger" else "sing" if h == "hope" else "plunder", "bread" if h == "hunger" else "map" if h == "hope" else "gold"))
    lines.append(asp.fact("risk_pair", "feast", "bread"))
    lines.append(asp.fact("risk_pair", "plunder", "gold"))
    lines.append(asp.fact("risk_pair", "sing", "map"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(cl - py))
    print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Generation / emit
# ---------------------------------------------------------------------------

def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], WANTS[params.want], TREASURES[params.treasure], params.name, params.role, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

CURATED = [
    StoryParams(place="ship", want="feast", treasure="bread", name="Mara", role="captain", trait="kind"),
    StoryParams(place="ship", want="plunder", treasure="gold", name="Finn", role="mate", trait="stubborn"),
    StoryParams(place="harbor", want="sing", treasure="map", name="Tessa", role="sailor", trait="spirited"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale world about ravenous hunger and a spiritual lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible pirate-story combos:")
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
        while len(samples) < args.n and i < max(50, args.n * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
            header = f"### {p.name}: {p.want} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
