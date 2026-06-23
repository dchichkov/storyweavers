#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260622T042304Z_seed1855084837_n10/occupy_tennis_friendship_happy_ending_fable.py
==============================================================================================================

A small fable-style storyworld about friendship, a shared tennis court, and a
happy ending where two friends learn to occupy space kindly instead of crowding
each other out.

The story premise is simple:
- Two small animal friends want to play tennis.
- One of them tries to occupy the whole court and the game turns sour.
- A gentle warning and a shared plan restore friendship.
- The ending proves the change: they play together, take turns, and leave the
  court happy.

The world is intentionally compact: one Entity model, one World model, a few
registries, a causal rule, and a state-driven renderer. The two required words
("occupy" and "tennis") are part of the prose and the simulation vocabulary.
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
from pathlib import Path
from typing import Optional


def _bootstrap_path() -> None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "results.py").exists():
            sys.path.insert(0, str(parent))
            return
        if (parent / "storyworlds" / "results.py").exists():
            sys.path.insert(0, str(parent / "storyworlds"))
            return


_bootstrap_path()
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
    attrs: dict = field(default_factory=dict)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class Court:
    name: str
    surface: str
    roomy: bool
    tags: set[str] = field(default_factory=set)


@dataclass
class PlayerSpec:
    id: str
    type: str
    label: str
    phrase: str
    trait: str
    tags: set[str] = field(default_factory=set)


@dataclass
class BallSpec:
    id: str
    label: str
    phrase: str
    risk: str
    tags: set[str] = field(default_factory=set)


@dataclass
class NetSpec:
    id: str
    label: str
    phrase: str
    covers: set[str]
    tags: set[str] = field(default_factory=set)


class World:
    def __init__(self, court: Court) -> None:
        self.court = court
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
        clone = World(self.court)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    court: str
    player1: str
    player2: str
    ball: str
    net: str
    seed: Optional[int] = None


COURTS = {
    "meadow": Court(name="the meadow court", surface="grass", roomy=True, tags={"tennis", "meadow", "grass"}),
    "village": Court(name="the village court", surface="packed dirt", roomy=False, tags={"tennis", "village"}),
    "orchard": Court(name="the orchard court", surface="soft earth", roomy=True, tags={"tennis", "orchard"}),
}

PLAYERS = {
    "hare": PlayerSpec(id="hare", type="rabbit", label="a quick hare", phrase="a quick hare", trait="swift", tags={"friendship", "hare"}),
    "tortoise": PlayerSpec(id="tortoise", type="turtle", label="a patient tortoise", phrase="a patient tortoise", trait="steady", tags={"friendship", "tortoise"}),
    "fox": PlayerSpec(id="fox", type="fox", label="a clever fox", phrase="a clever fox", trait="clever", tags={"friendship", "fox"}),
    "deer": PlayerSpec(id="deer", type="deer", label="a gentle deer", phrase="a gentle deer", trait="gentle", tags={"friendship", "deer"}),
}

BALLS = {
    "red_ball": BallSpec(id="red_ball", label="a red tennis ball", phrase="a red tennis ball", risk="rolls away quickly", tags={"tennis", "ball"}),
    "green_ball": BallSpec(id="green_ball", label="a green tennis ball", phrase="a green tennis ball", risk="bounces into flowers", tags={"tennis", "ball"}),
}

NETS = {
    "low_net": NetSpec(id="low_net", label="a low net", phrase="a low net", covers={"center"}, tags={"tennis", "net"}),
    "wide_net": NetSpec(id="wide_net", label="a wide net", phrase="a wide net", covers={"center", "edge"}, tags={"tennis", "net"}),
}

GREETINGS = [
    "were old friends",
    "liked to share a game",
    "were happy to see each other",
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for court_id, court in COURTS.items():
        for p1 in PLAYERS:
            for p2 in PLAYERS:
                if p1 == p2:
                    continue
                for ball_id in BALLS:
                    for net_id in NETS:
                        if court.roomy or net_id == "wide_net":
                            combos.append((court_id, p1, p2, ball_id, net_id))
    return combos


def reasonableness_gate(court_id: str, p1: str, p2: str, ball_id: str, net_id: str) -> bool:
    return (court_id, p1, p2, ball_id, net_id) in valid_combos()


ASP_RULES = r"""
valid(C, P1, P2, B, N) :- court(C), player(P1), player(P2), P1 != P2, ball(B), net(N), roomy(C).
valid(C, P1, P2, B, N) :- court(C), player(P1), player(P2), P1 != P2, ball(B), net(N), wide_net(N).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for cid, court in COURTS.items():
        lines.append(asp.fact("court", cid))
        if court.roomy:
            lines.append(asp.fact("roomy", cid))
        for tag in sorted(court.tags):
            lines.append(asp.fact("tags", cid, tag))
    for pid in PLAYERS:
        lines.append(asp.fact("player", pid))
    for bid in BALLS:
        lines.append(asp.fact("ball", bid))
    for nid in NETS:
        lines.append(asp.fact("net", nid))
        if nid == "wide_net":
            lines.append(asp.fact("wide_net", nid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/5."))
    return sorted(set(asp.atoms(model, "valid")))


def _setup_world(params: StoryParams) -> tuple[World, Entity, Entity, Entity, Entity]:
    if params.court not in COURTS:
        raise StoryError("Unknown court.")
    if params.player1 not in PLAYERS or params.player2 not in PLAYERS:
        raise StoryError("Unknown player.")
    if params.ball not in BALLS or params.net not in NETS:
        raise StoryError("Unknown equipment.")
    if not reasonableness_gate(params.court, params.player1, params.player2, params.ball, params.net):
        raise StoryError("This court and equipment combination is not reasonable.")

    court = COURTS[params.court]
    world = World(court)
    p1s = PLAYERS[params.player1]
    p2s = PLAYERS[params.player2]
    bs = BALLS[params.ball]
    ns = NETS[params.net]

    p1 = world.add(Entity(id=p1s.id, kind="character", type=p1s.type, label=p1s.label, phrase=p1s.phrase, attrs={"trait": p1s.trait}))
    p2 = world.add(Entity(id=p2s.id, kind="character", type=p2s.type, label=p2s.label, phrase=p2s.phrase, attrs={"trait": p2s.trait}))
    ball = world.add(Entity(id=bs.id, type="thing", label=bs.label, phrase=bs.phrase, attrs={"risk": bs.risk}))
    net = world.add(Entity(id=ns.id, type="thing", label=ns.label, phrase=ns.phrase, attrs={"covers": sorted(ns.covers)}))
    world.facts.update(court=court, player1=p1, player2=p2, ball=ball, net=net)
    return world, p1, p2, ball, net


def _predict_crowding(world: World, p1: Entity, p2: Entity) -> bool:
    sim = world.copy()
    sim.get(p1.id).memes["greed"] += 1
    sim.get(p1.id).memes["occupy"] += 1
    sim.get(p2.id).memes["sadness"] += 1
    return sim.get(p1.id).memes["occupy"] >= THRESHOLD and sim.get(p2.id).memes["sadness"] >= THRESHOLD


def _do_round(world: World, p1: Entity, p2: Entity, ball: Entity, net: Entity) -> None:
    p1.memes["joy"] += 1
    p2.memes["joy"] += 1
    world.say(f"On a bright morning, {p1.id} and {p2.id} met at {world.court.name}.")
    world.say(f"They were friends, and they brought {ball.label} and {net.label} for a game of tennis.")
    world.say(f"At first, the court felt wide and kind, like a place made for shared laughter.")


def _conflict(world: World, p1: Entity, p2: Entity, ball: Entity) -> None:
    p1.memes["occupy"] += 1
    p2.memes["hurt"] += 1
    world.say(f"But {p1.id} tried to occupy the center of the court and would not make room.")
    world.say(f"{p2.id} stepped back, because {ball.label} kept rolling into the same spot again and again.")
    world.say(f"Their friendship grew quiet, and even the tennis ball seemed lonely.")


def _warning(world: World, p1: Entity, p2: Entity) -> None:
    p2.memes["care"] += 1
    p1.memes["listening"] += 1
    world.say(f"Then {p2.id} spoke gently: 'A court is small, but friendship is big.'")
    world.say(f"{p2.id} reminded {p1.id} that a game is better when both friends can reach the ball.")


def _resolution(world: World, p1: Entity, p2: Entity, ball: Entity, net: Entity) -> None:
    p1.memes["occupy"] = 0.0
    p1.memes["joy"] += 1
    p2.memes["joy"] += 1
    p1.memes["friendship"] += 1
    p2.memes["friendship"] += 1
    world.say(f"{p1.id} listened, smiled, and moved aside.")
    world.say(f"The friends placed {net.label} in the middle and took turns serving {ball.label}.")
    world.say(f"By sunset, they were laughing again, and the whole court felt warm with friendship.")


def tell(params: StoryParams) -> World:
    world, p1, p2, ball, net = _setup_world(params)
    _do_round(world, p1, p2, ball, net)
    world.para()
    if _predict_crowding(world, p1, p2):
        _conflict(world, p1, p2, ball)
        _warning(world, p1, p2)
        _resolution(world, p1, p2, ball, net)
    world.para()
    world.say(f"In the end, the two friends left the meadow court together, sharing the ball and the joy.")
    world.facts.update(
        outcome="happy_ending",
        tension=p1.memes.get("occupy", 0.0),
        repaired=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p1, p2 = f["player1"], f["player2"]
    ball, court = f["ball"], f["court"]
    return [
        f"Write a fable about {p1.id} and {p2.id} learning to share {court.name} during a game of tennis.",
        f"Tell a gentle story that uses the word occupy and shows why friends should not occupy the whole tennis court.",
        f"Write a happy-ending fable about friendship, tennis, and a disagreement over space that gets solved kindly.",
        f"Create a child-friendly story where {p1.id} and {p2.id} learn to take turns with {ball.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p1, p2 = f["player1"], f["player2"]
    ball, court, net = f["ball"], f["court"], f["net"]
    qa = [
        QAItem(
            question=f"Who were the two friends in the story?",
            answer=f"The story was about {p1.label} and {p2.label}. They met on {court.name} to play tennis and try to stay friends.",
        ),
        QAItem(
            question=f"Why did {p2.id} feel upset when the tennis game started?",
            answer=f"{p1.id} tried to occupy the center of the court and would not make room. That made it hard for {p2.id} to reach {ball.label}, so the game stopped feeling fair.",
        ),
        QAItem(
            question=f"What changed after the friends talked kindly?",
            answer=f"{p1.id} moved aside and listened to {p2.id}. Then they used {net.label}, took turns, and the friendship came back strong.",
        ),
    ]
    if world.facts.get("repaired"):
        qa.append(
            QAItem(
                question=f"How did the story end?",
                answer=f"It ended happily. The friends left {court.name} together, smiling after their tennis game, and the ending showed that sharing space kept their friendship bright.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does occupy mean?",
            answer="To occupy means to take up a place or space. In the story, one friend learned that occupying the whole tennis court was not kind.",
        ),
        QAItem(
            question="What is tennis?",
            answer="Tennis is a game where friends hit a ball back and forth over a net. It works best when both players have room to move.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship means caring about someone, listening to them, and sharing fairly. Friends try to help each other instead of crowding each other out.",
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
    lines.append("== (3) World knowledge ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(court="meadow", player1="hare", player2="tortoise", ball="red_ball", net="wide_net"),
    StoryParams(court="orchard", player1="fox", player2="deer", ball="green_ball", net="wide_net"),
]


def explain_rejection() -> str:
    return "(No story: that combination would not leave enough room for a fair tennis game.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A friendship fable about tennis, occupy, and a happy ending.")
    ap.add_argument("--court", choices=COURTS)
    ap.add_argument("--player1", choices=PLAYERS)
    ap.add_argument("--player2", choices=PLAYERS)
    ap.add_argument("--ball", choices=BALLS)
    ap.add_argument("--net", choices=NETS)
    ap.add_argument("-n", "--n", type=int, default=1, help="number of stories to generate")
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
              if (args.court is None or c[0] == args.court)
              and (args.player1 is None or c[1] == args.player1)
              and (args.player2 is None or c[2] == args.player2)
              and (args.ball is None or c[3] == args.ball)
              and (args.net is None or c[4] == args.net)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    court, p1, p2, ball, net = rng.choice(sorted(combos))
    return StoryParams(court=court, player1=p1, player2=p2, ball=ball, net=net)


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


def asp_verify() -> int:
    try:
        cset = set(asp_valid_combos())
        pset = set(valid_combos())
    except Exception as exc:
        print(f"ASP verify failed: {exc}")
        return 1
    if cset != pset:
        print("MISMATCH between ASP and Python valid-combos.")
        print("only in asp:", sorted(cset - pset))
        print("only in python:", sorted(pset - cset))
        return 1
    try:
        sample = generate(CURATED[0])
        if not sample.story or "tennis" not in sample.story.lower():
            raise StoryError("Smoke test story missing expected content.")
    except Exception as exc:
        print(f"Story generation smoke test failed: {exc}")
        return 1
    print(f"OK: ASP parity and generation smoke test passed ({len(cset)} combos).")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/5."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible court/player/net combos:\n")
        for row in combos[:50]:
            print("  ", row)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
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
            header = f"### {p.player1} and {p.player2} at {p.court} ({p.ball})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
