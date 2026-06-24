#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/gristle_whir_real_ist_dialogue_ghost_story.py
===============================================================================================================

A standalone story world in the mood of a gentle ghost story, built from the
seed words: gristle, whir, real-ist.

Premise:
- A child stays up in an old house.
- A small ghost is heard before it is seen.
- The house makes a soft whir at night.
- Something from the supper table (gristle in soup) creates a tiny scare.
- Dialogue untangles the mystery and turns the scare into a calm ending.

The story is state-driven: fear, sound, and a physical object change the
characters' memories and feelings.  Dialogue is used as the main instrument of
the turn, keeping the style close to a classic ghost story without being harsh.
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
# World entities
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    label: str = ""
    type: str = "thing"
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)  # physical measures
    memes: dict[str, float] = field(default_factory=dict)   # emotional measures

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def refers(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the old house"
    room: str = "the attic"
    night_sound: str = "a soft whir"


@dataclass
class StoryParams:
    name: str
    gender: str
    parent: str
    ghost_name: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.sound_whir: float = 0.0
        self.gristle_seen: bool = False

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "label": v.label, "type": v.type,
            "plural": v.plural, "owner": v.owner,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        clone.sound_whir = self.sound_whir
        clone.gristle_seen = self.gristle_seen
        return clone


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    w = World(Setting())
    child = w.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    parent = w.add(Entity(id="parent", kind="character", type=params.parent, label=f"the {params.parent}"))
    ghost = w.add(Entity(id=params.ghost_name, kind="character", type="ghost", label=params.ghost_name))
    soup = w.add(Entity(id="soup", kind="thing", type="soup", label="a bowl of soup", meters={"warm": 1.0}))
    spoon = w.add(Entity(id="spoon", kind="thing", type="spoon", label="a small spoon"))
    w.facts.update(child=child, parent=parent, ghost=ghost, soup=soup, spoon=spoon)
    return w


def whisper_scene(w: World) -> None:
    child: Entity = w.facts["child"]  # type: ignore[assignment]
    parent: Entity = w.facts["parent"]  # type: ignore[assignment]
    ghost: Entity = w.facts["ghost"]  # type: ignore[assignment]
    w.say(f"It was late in {w.setting.place}, and {w.setting.room} held a lonely little {w.setting.night_sound}.")
    w.say(f"{child.id} sat still and said, \"Do you hear that whir?\"")
    w.say(f"{parent.label} listened and answered, \"I do. Old houses make strange sounds.\"")
    w.sound_whir += 1.0
    w.facts["whir"] = True
    ghost.memes["near"] = 1.0
    ghost.meters["seen"] = 0.0


def scare_scene(w: World) -> None:
    child: Entity = w.facts["child"]  # type: ignore[assignment]
    parent: Entity = w.facts["parent"]  # type: ignore[assignment]
    soup: Entity = w.facts["soup"]  # type: ignore[assignment]
    w.para()
    w.say(f"Then the child looked at the bowl on the table and saw a pale little gristle in the soup.")
    w.gristle_seen = True
    child.memes["fear"] = 1.0
    w.say(f'{child.id} whispered, \"What if the whir is a ghost?\"')
    w.say(f'{parent.label} smiled and said, \"Ghosts are only stories until we know the real-ist reason.\"')
    soup.meters["warm"] += 0.0


def reveal_scene(w: World) -> None:
    child: Entity = w.facts["child"]  # type: ignore[assignment]
    parent: Entity = w.facts["parent"]  # type: ignore[assignment]
    ghost: Entity = w.facts["ghost"]  # type: ignore[assignment]
    w.para()
    w.say(f"A tiny laugh came from the dark corner. \"I am the ghost,\" said {ghost.label}, \"but I am not here to frighten you.\"")
    w.say(f'"Then what makes the whir?" asked {child.id}.')
    w.say(f'"The old fan does," said the ghost. \"And I only drift through this room because it feels cozy.\"')
    ghost.meters["seen"] = 1.0
    child.memes["fear"] = 0.0
    child.memes["curiosity"] = 1.0
    parent.memes["relief"] = 1.0


def ending_scene(w: World) -> None:
    child: Entity = w.facts["child"]  # type: ignore[assignment]
    parent: Entity = w.facts["parent"]  # type: ignore[assignment]
    ghost: Entity = w.facts["ghost"]  # type: ignore[assignment]
    w.para()
    w.say(f'{child.id} gave a careful smile and said, \"You are a real-ist ghost.\"')
    w.say(f'{ghost.label} bowed. \"A real ghost, and a friendly one,\" it said. \"Now the whir sounds like a lullaby.\"')
    w.say(f"So {child.id} ate the soup, even the gristle did not seem so scary, and {w.setting.room} felt warm instead of strange.")
    parent.memes["love"] = 1.0
    ghost.memes["welcome"] = 1.0


def tell(params: StoryParams) -> World:
    w = build_world(params)
    whisper_scene(w)
    scare_scene(w)
    reveal_scene(w)
    ending_scene(w)
    return w


# ---------------------------------------------------------------------------
# Registries and validation
# ---------------------------------------------------------------------------
GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Ada"]
BOY_NAMES = ["Milo", "Evan", "Theo", "Finn", "Owen"]


def valid_genders() -> set[str]:
    return {"girl", "boy"}


def resolve_name(gender: str, rng: random.Random) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def explain_gender(gender: str) -> str:
    return f"(No story: gender must be one of {sorted(valid_genders())}, got {gender!r}.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
child_fears(W) :- sees_gristle(W), hears_whir(W).
ghost_revealed(W) :- child_fears(W), friendly_dialogue(W).
ending_warm(W) :- ghost_revealed(W), not haunted(W).

#show child_fears/1.
#show ghost_revealed/1.
#show ending_warm/1.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("world", "base"),
        asp.fact("sees_gristle", "base"),
        asp.fact("hears_whir", "base"),
        asp.fact("friendly_dialogue", "base"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_expected() -> set[tuple[str, tuple]]:
    return {
        ("child_fears", ("base",)),
        ("ghost_revealed", ("base",)),
        ("ending_warm", ("base",)),
    }


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show child_fears/1.\n#show ghost_revealed/1.\n#show ending_warm/1."))
    got = set()
    for pred in ("child_fears", "ghost_revealed", "ending_warm"):
        got.update((pred, args) for args in asp.atoms(model, pred))
    exp = asp_expected()
    if got == exp:
        print(f"OK: clingo gate matches expected facts ({len(got)} atoms).")
        return 0
    print("MISMATCH between clingo and expected facts:")
    print("  got:", sorted(got))
    print("  exp:", sorted(exp))
    return 1


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        f"Write a gentle ghost story for children that includes the words gristle, whir, and real-ist.",
        f'Tell a dialogue-driven story where {p.name} hears a whir in the old house and learns the ghost is friendly.',
        f'Write a small bedtime story with a spooky beginning, a talking ghost, and a calm ending.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {p.name} hear in the old house?",
            answer="The child heard a soft whir, and it made the attic feel spooky for a moment.",
        ),
        QAItem(
            question="Why did the child get scared?",
            answer="The child saw a bit of gristle in the soup and wondered if the whir might be a ghost.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The ghost spoke kindly, the child learned the sound came from an old fan, and everyone felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a ghost story?",
            answer="A ghost story is a tale that feels spooky for a little while, but it can still end safely and kindly.",
        ),
        QAItem(
            question="What does whir mean?",
            answer="A whir is a soft humming sound that a machine or fan can make when it spins.",
        ),
        QAItem(
            question="What is gristle?",
            answer="Gristle is a tough little bit in meat that can feel chewy when someone eats soup or stew.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, q in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {q}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI / serialization
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost story world with dialogue.")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mother", "father"], default="mother")
    ap.add_argument("--ghost-name", default="Murmur")
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
    gender = args.gender or rng.choice(["girl", "boy"])
    if gender not in valid_genders():
        raise StoryError(explain_gender(gender))
    name = args.name or resolve_name(gender, rng)
    return StoryParams(
        name=name,
        gender=gender,
        parent=args.parent,
        ghost_name=args.ghost_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    world.facts["params"] = params
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: kind={e.kind} label={e.label!r} meters={meters} memes={memes}")
    lines.append(f"whir={world.sound_whir} gristle_seen={world.gristle_seen}")
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


def asp_show_program() -> str:
    return asp_program("#show child_fears/1.\n#show ghost_revealed/1.\n#show ending_warm/1.")


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_show_program())
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show child_fears/1.\n#show ghost_revealed/1.\n#show ending_warm/1."))
        for pred in ("child_fears", "ghost_revealed", "ending_warm"):
            print(pred, asp.atoms(model, pred))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    seen: set[str] = set()
    if args.all:
        seeds = [base_seed + i for i in range(5)]
    else:
        seeds = [base_seed + i for i in range(max(1, args.n))]

    for seed in seeds:
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
        if not args.all and len(samples) >= args.n:
            break

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
