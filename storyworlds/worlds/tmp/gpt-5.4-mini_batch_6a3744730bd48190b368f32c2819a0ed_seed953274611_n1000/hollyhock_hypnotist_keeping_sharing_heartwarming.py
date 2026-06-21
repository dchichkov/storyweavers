#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/hollyhock_hypnotist_keeping_sharing_heartwarming.py
====================================================================================

A small, heartwarming storyworld about a child, a dramatic "hypnotist" game, and
a garden-sharing lesson. The seed words are woven into a tiny simulation:
a hollyhock patch, a pretend hypnotist, and the act of keeping / sharing blooms.

Core premise:
- A child wants to keep a lovely hollyhock flower all to themself.
- A friend or sibling wants one too.
- A pretend hypnotist game becomes a playful way to focus attention.
- A gentle grown-up or friend helps them see that sharing the flowers makes the
  garden brighter for everyone.

The world is intentionally tiny and classical:
- typed entities with physical meters and emotional memes,
- a state-driven sequence of beats,
- a reasonableness gate,
- an inline ASP twin,
- and generated Q&A grounded in the simulated world state.

Run it:
    python storyworlds/worlds/gpt-5.4-mini/hollyhock_hypnotist_keeping_sharing_heartwarming.py
    python storyworlds/worlds/gpt-5.4-mini/hollyhock_hypnotist_keeping_sharing_heartwarming.py --qa
    python storyworlds/worlds/gpt-5.4-mini/hollyhock_hypnotist_keeping_sharing_heartwarming.py --verify
    python storyworlds/worlds/gpt-5.4-mini/hollyhock_hypnotist_keeping_sharing_heartwarming.py --all
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
SHARING_MIN = 2
CONTENTMENT_TARGET = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: str = ""
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)


@dataclass
class Garden:
    id: str
    name: str
    place: str
    mood: str
    flowers: str
    shady_spot: str
    celebration: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bloom:
    id: str
    label: str
    phrase: str
    color: str
    delicate: bool = True
    shareable: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Game:
    id: str
    label: str
    phrase: str
    nudge: str
    calm: str
    lift: int
    tags: set[str] = field(default_factory=set)


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


def _r_soften(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.meters["tension"] < THRESHOLD:
            continue
        sig = ("soften", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.memes["guarded"] += 1
        out.append("")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    kid = world.entities.get("child")
    peer = world.entities.get("peer")
    bloom = world.entities.get("bloom")
    if not kid or not peer or not bloom:
        return out
    if kid.memes["sharing"] < THRESHOLD or bloom.meters["picked"] < THRESHOLD:
        return out
    sig = ("sharing",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    peer.memes["joy"] += 1
    kid.memes["joy"] += 1
    out.append("")
    return out


CAUSAL_RULES = [Rule("soften", "emotional", _r_soften), Rule("sharing", "social", _r_sharing)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def reasonableness_gate(game: Game, bloom: Bloom) -> bool:
    return game.lift >= SHARING_MIN and bloom.shareable and bloom.delicate


def valid_combos() -> list[tuple[str, str]]:
    return [("garden", "hypnotist")]


def gentle_gate(game: Game) -> bool:
    return game.lift >= SHARING_MIN


def simulate_hypnosis(world: World, child: Entity, peer: Entity, game: Game, bloom: Bloom) -> dict:
    sim = world.copy()
    sim.get("child").memes["focus"] += 1
    sim.get("peer").memes["hope"] += 1
    sim.get("bloom").meters["desired"] += 1
    return {
        "sharing_possible": gentle_gate(game) and bloom.shareable,
        "tension": sim.get("child").memes["want_keep"] + sim.get("peer").memes["want_share"],
    }


def setup(world: World, garden: Garden, child: Entity, peer: Entity, grownup: Entity) -> None:
    world.say(
        f"In {garden.place}, the {garden.name} felt warm and bright. "
        f"The {garden.flowers} leaned in the sun, and one tall hollyhock stood near {garden.shady_spot}."
    )
    world.say(
        f"{child.id} and {peer.id} wandered in with careful steps, and {grownup.id} smiled from the path."
    )


def want_keep(world: World, child: Entity, bloom: Bloom) -> None:
    child.memes["want_keep"] += 1
    child.meters["clutch"] += 1
    world.say(
        f"{child.id} pointed at the {bloom.label} and whispered, "
        f'"I want to keep the {bloom.label} all to myself."'
    )


def toy_hypnotist(world: World, child: Entity, peer: Entity, game: Game) -> None:
    child.memes["curiosity"] += 1
    peer.memes["curiosity"] += 1
    world.say(
        f"{peer.id} grinned and played the pretend hypnotist, "
        f'waving a hand slowly. "{game.nudge}"'
    )
    world.say(
        f"{child.id} blinked, then giggled, because the silly game made it easier to think about someone else."
    )


def warning(world: World, grownup: Entity, bloom: Bloom) -> None:
    world.say(
        f'{grownup.id} crouched beside them. "{bloom.label}s are loveliest when we leave some for everyone," '
        f"{grownup.pronoun()} said softly."
    )


def choose_share(world: World, child: Entity, peer: Entity, bloom: Bloom) -> None:
    child.memes["sharing"] += 1
    child.meters["clutch"] = 0
    bloom.meters["picked"] = 1
    world.say(
        f"{child.id} took a breath, loosened {child.pronoun('possessive')} hands, and nodded."
    )
    world.say(
        f'"We can share the {bloom.label}," {child.id} said. "You can have one bloom, and I can keep one for looking at."'
    )


def ending(world: World, garden: Garden, child: Entity, peer: Entity, bloom: Bloom) -> None:
    child.memes["joy"] += 1
    peer.memes["joy"] += 1
    world.say(
        f"They picked just one careful bloom and left the others swaying on the stem."
    )
    world.say(
        f"{peer.id} tucked the flower into a little cup of water, and {child.id} kept the bright memory."
    )
    world.say(
        f"By evening, the {garden.name} looked even kinder than before, because sharing had made it feel full."
    )


def tell(garden: Garden, bloom: Bloom, game: Game, child_name: str, child_gender: str,
         peer_name: str, peer_gender: str, grownup_name: str, grownup_gender: str) -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="child"))
    peer = world.add(Entity(id=peer_name, kind="character", type=peer_gender, role="peer"))
    grownup = world.add(Entity(id=grownup_name, kind="character", type=grownup_gender, role="grownup"))
    world.add(Entity(id="garden", type="place", label=garden.name, tags=set(garden.tags)))
    world.add(Entity(id="bloom", type="flower", label=bloom.label, tags=set(bloom.tags)))
    world.add(Entity(id="game", type="game", label=game.label, tags=set(game.tags)))

    child.memes["want_keep"] = 1
    peer.memes["want_share"] = 1
    child.memes["focus"] = 0
    peer.memes["hope"] = 0

    setup(world, garden, child, peer, grownup)
    world.para()
    want_keep(world, child, bloom)
    toy_hypnotist(world, child, peer, game)
    warning(world, grownup, bloom)

    if reasonableness_gate(game, bloom):
        choose_share(world, child, peer, bloom)
        propagate(world, narrate=False)
        world.para()
        ending(world, garden, child, peer, bloom)

    world.facts.update(
        garden=garden, bloom=bloom, game=game, child=child, peer=peer, grownup=grownup,
        shared=child.memes["sharing"] >= THRESHOLD, kept=child.meters["clutch"] > 0,
    )
    return world


GARDENS = {
    "sunny_patch": Garden(
        id="sunny_patch",
        name="sunny patch",
        place="the sunny back garden",
        mood="warm",
        flowers="hollyhocks",
        shady_spot="the fence",
        celebration="bright and kind",
        tags={"garden", "hollyhock", "sharing"},
    ),
    "little_plot": Garden(
        id="little_plot",
        name="little plot",
        place="the little front garden",
        mood="soft",
        flowers="hollyhocks and daisies",
        shady_spot="the porch",
        celebration="gentle",
        tags={"garden", "hollyhock", "sharing"},
    ),
}

BLOOMS = {
    "hollyhock": Bloom(
        id="hollyhock",
        label="hollyhock",
        phrase="a tall hollyhock bloom",
        color="pink",
        delicate=True,
        shareable=True,
        tags={"hollyhock", "flower"},
    )
}

GAMES = {
    "hypnotist": Game(
        id="hypnotist",
        label="pretend hypnotist",
        phrase="a pretend hypnotist game",
        nudge="Look at the flower, and keep what matters in your heart",
        calm="brought their thoughts back to sharing",
        lift=3,
        tags={"hypnotist", "sharing"},
    )
}

NAMES_GIRL = ["Maya", "Lily", "Nora", "Ella", "Ava"]
NAMES_BOY = ["Theo", "Finn", "Ben", "Leo", "Sam"]


@dataclass
class StoryParams:
    garden: str
    bloom: str
    game: str
    child: str
    child_gender: str
    peer: str
    peer_gender: str
    grownup: str
    grownup_gender: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(
        garden="sunny_patch",
        bloom="hollyhock",
        game="hypnotist",
        child="Maya",
        child_gender="girl",
        peer="Finn",
        peer_gender="boy",
        grownup="Grandma",
        grownup_gender="woman",
        seed=1,
    ),
    StoryParams(
        garden="little_plot",
        bloom="hollyhock",
        game="hypnotist",
        child="Theo",
        child_gender="boy",
        peer="Nora",
        peer_gender="girl",
        grownup="Mom",
        grownup_gender="mother",
        seed=2,
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming garden sharing storyworld.")
    ap.add_argument("--garden", choices=GARDENS)
    ap.add_argument("--bloom", choices=BLOOMS)
    ap.add_argument("--game", choices=GAMES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--peer")
    ap.add_argument("--peer-gender", choices=["girl", "boy"])
    ap.add_argument("--grownup")
    ap.add_argument("--grownup-gender", choices=["woman", "man", "mother", "father"])
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
    combos = valid_combos()
    if args.garden and args.garden not in GARDENS:
        raise StoryError("Unknown garden.")
    if args.bloom and args.bloom not in BLOOMS:
        raise StoryError("Unknown bloom.")
    if args.game and args.game not in GAMES:
        raise StoryError("Unknown game.")
    garden = args.garden or rng.choice([c[0] for c in combos])
    bloom = args.bloom or "hollyhock"
    game = args.game or "hypnotist"
    if (garden, game) not in combos:
        raise StoryError("(No valid combination matches the given options.)")
    child_gender = args.child_gender or rng.choice(["girl", "boy"])
    peer_gender = args.peer_gender or ("boy" if child_gender == "girl" else "girl")
    grownup_gender = args.grownup_gender or rng.choice(["woman", "man"])
    child = args.child or rng.choice(NAMES_GIRL if child_gender == "girl" else NAMES_BOY)
    peer_pool = [n for n in (NAMES_BOY if peer_gender == "boy" else NAMES_GIRL) if n != child]
    peer = args.peer or rng.choice(peer_pool)
    grownup = args.grownup or rng.choice(["Mom", "Dad", "Grandma", "Grandpa"])
    return StoryParams(
        garden=garden,
        bloom=bloom,
        game=game,
        child=child,
        child_gender=child_gender,
        peer=peer,
        peer_gender=peer_gender,
        grownup=grownup,
        grownup_gender=grownup_gender,
    )


def generate(params: StoryParams) -> StorySample:
    if params.garden not in GARDENS or params.bloom not in BLOOMS or params.game not in GAMES:
        raise StoryError("Invalid params.")
    world = tell(
        GARDENS[params.garden],
        BLOOMS[params.bloom],
        GAMES[params.game],
        params.child,
        params.child_gender,
        params.peer,
        params.peer_gender,
        params.grownup,
        params.grownup_gender,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a heartwarming story that includes the words "hollyhock" and "hypnotist" and ends with sharing.',
        f"Tell a gentle story where {f['child'].id} wants to keep a hollyhock, but a pretend hypnotist game and a caring grown-up help them share.",
        'Write a warm garden story about keeping something special in your heart instead of keeping it all to yourself.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    child: Entity = f["child"]
    peer: Entity = f["peer"]
    grownup: Entity = f["grownup"]
    bloom: Bloom = f["bloom"]
    qa = [
        ("What flower is in the story?", f"It is a hollyhock. The flower is something the children notice and want to keep."),
        (f"Why did {child.id} hesitate to share?", f"{child.id} wanted to keep the hollyhock all to {child.pronoun('possessive')}self. That made sharing feel hard at first, even though {peer.id} wanted to join in."),
        ("What did the pretend hypnotist game do?", f"It helped the children slow down and look at the flower calmly. That made room for kindness, so the story could turn toward sharing."),
    ]
    if f.get("shared"):
        qa.append((f"How did {child.id} and {peer.id} solve the problem?",
                   f"{child.id} chose to share the hollyhock instead of keeping it alone. Then both children could enjoy the flower, and the garden felt brighter for it."))
        qa.append(("How did the story end?",
                   f"It ended with {child.id} and {peer.id} sharing the bloom and feeling happy. {grownup.id} got to see them make a gentle choice that kept the day warm and kind."))
    return qa


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a hollyhock?", "A hollyhock is a tall garden flower with a long stem and bright blossoms."),
        ("What does a hypnotist do in pretend play?", "In pretend play, a hypnotist is someone who acts as if they can guide attention with a dramatic voice or hand motion."),
        ("Why is sharing important?", "Sharing lets more than one person enjoy something special. It helps people feel cared for and keeps play kind."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if e.memes:
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for gid in GARDENS:
        lines.append(asp.fact("garden", gid))
    for bid in BLOOMS:
        lines.append(asp.fact("bloom", bid))
        lines.append(asp.fact("shareable", bid))
        lines.append(asp.fact("delicate", bid))
    for g in GAMES.values():
        lines.append(asp.fact("game", g.id))
        lines.append(asp.fact("lift", g.id, g.lift))
    lines.append(asp.fact("sharing_min", SHARING_MIN))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(G, B, M) :- garden(G), bloom(B), game(M), shareable(B), delicate(B), lift(M, L), sharing_min(S), L >= S.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py != cl:
        rc = 1
        print("MISMATCH in valid combos:")
        print("python:", sorted(py - cl))
        print("clingo:", sorted(cl - py))
    else:
        print(f"OK: gate matches valid_combos() ({len(py)} combos).")
    try:
        sample = generate(resolve_params(argparse.Namespace(
            garden=None, bloom=None, game=None, child=None, child_gender=None,
            peer=None, peer_gender=None, grownup=None, grownup_gender=None
        ), random.Random(7)))
        _ = sample.story
        print("OK: generate() smoke test passed.")
    except Exception as exc:
        print(f"FAILED: generate() smoke test failed: {exc}")
        return 1
    return rc


def explain_rejection() -> str:
    return "(No story: this tiny world only tells a gentle sharing tale with hollyhocks and a pretend hypnotist.)"


def tell_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    return resolve_params(args, rng)


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
        print(asp_program("#show compatible/3."))
        return
    if args.verify:
        raise SystemExit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible garden stories:")
        for row in combos:
            print(" ", row)
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
            params = tell_from_args(args, random.Random(seed))
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
            header = f"### {p.child} and {p.peer}: {p.bloom} in the {p.garden}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
