#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/bulletin_kindness_magic_curiosity_tall_tale.py
==============================================================================

A tiny storyworld for a tall-tale style about a bulletin board, a little bit of
magic, and a curious child who chooses kindness instead of a prank.

Premise
-------
A child notices a mysterious bulletin in a town square. The bulletin promises a
lost thing, but the clue is written in a tricky, magical way. Curiosity pulls the
child closer; kindness keeps the child from making a greedy choice; magic helps
the community reunite what was lost.

This world is intentionally small and state-driven:
- typed entities carry physical meters and emotional memes;
- a simple forward-chaining model changes the world before the prose is rendered;
- a Python reasonableness gate matches an inline ASP twin;
- QA is built from world state, not by parsing the final English.

Run it
------
    python storyworlds/worlds/gpt-5.4-mini/bulletin_kindness_magic_curiosity_tall_tale.py
    python storyworlds/worlds/gpt-5.4-mini/bulletin_kindness_magic_curiosity_tall_tale.py --all
    python storyworlds/worlds/gpt-5.4-mini/bulletin_kindness_magic_curiosity_tall_tale.py --qa --json
    python storyworlds/worlds/gpt-5.4-mini/bulletin_kindness_magic_curiosity_tall_tale.py --verify
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MAGIC_MIN = 1
CURIOUS_MIN = 1
KIND_MIN = 1


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    attrs: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {}
        if not self.memes:
            self.memes = {}

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "father", "man", "uncle"}
        female = {"girl", "mother", "woman", "aunt"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Place:
    id: str
    label: str
    setting_line: str
    weather_line: str
    bulletin_line: str
    magic_glow: str
    tall_tale_line: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Bulletin:
    id: str
    label: str
    clue: str
    promise: str
    trick: str
    target: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Charm:
    id: str
    label: str
    method: str
    reveal: str
    power: int
    tags: set[str] = field(default_factory=set)


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

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
        other = World()
        other.entities = copy.deepcopy(self.entities)
        other.fired = set(self.fired)
        other.paragraphs = [[]]
        other.facts = dict(self.facts)
        return other


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_whisper(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meme("curiosity") < CURIOUS_MIN:
            continue
        sig = ("whisper", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        board = world.get("bulletin")
        board.meters["noticed"] = board.meter("noticed") + 1
        out.append("__whisper__")
    return out


def _r_magic(world: World) -> list[str]:
    out = []
    for ent in world.entities.values():
        if ent.meme("kindness") < KIND_MIN:
            continue
        if ent.meme("curiosity") < CURIOUS_MIN:
            continue
        sig = ("magic", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        charm = world.get("charm")
        charm.meters["glow"] = charm.meter("glow") + 1
        world.get("park").meters["wonder"] = world.get("park").meter("wonder") + 1
        out.append("__magic__")
    return out


def _r_mend(world: World) -> list[str]:
    out = []
    note = world.get("bulletin")
    if note.meter("torn") < THRESHOLD:
        return out
    if world.get("lost").meter("found") >= THRESHOLD:
        sig = ("mend", note.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        out.append("__mend__")
    return out


RULES = [Rule("whisper", _r_whisper), Rule("magic", _r_magic), Rule("mend", _r_mend)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in RULES:
            got = rule.apply(world)
            if got:
                changed = True
                produced.extend(g for g in got if not g.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for board in BULLETINS:
            for charm in CHARMS:
                if reasonableness_gate(place, board, charm):
                    combos.append((place, board, charm))
    return combos


def reasonableness_gate(place: Place, bulletin: Bulletin, charm: Charm) -> bool:
    return bulletin.target == "lost_item" and charm.power >= MAGIC_MIN and "town" in place.tags


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("tagged", pid, t))
    for bid, b in BULLETINS.items():
        lines.append(asp.fact("bulletin", bid))
        lines.append(asp.fact("bulletin_target", bid, b.target))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("power", cid, c.power))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, B, C) :- place(P), bulletin(B), charm(C), bulletin_target(B, lost_item), power(C, Pow), Pow >= 1, tagged(P, town).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class StoryParams:
    place: str
    bulletin: str
    charm: str
    child_name: str
    child_type: str
    helper_name: str
    helper_type: str
    seed: Optional[int] = None


PLACES = {
    "square": Place("square", "the town square", "The square sat bright and broad under the sky.", "The wind hummed around the old post.", "A bulletin board stood near the fountain.", "It shimmered like moonlight on a spoon.", "The square looked so wide a wagon could lose itself in a sneeze.", tags={"town"}),
    "market": Place("market", "the market lane", "The market lane was busy with boots and baskets.", "The awnings clicked in the breeze.", "A bulletin board leaned beside the baker's cart.", "It glowed like a firefly in a jar.", "The lane was so lively a penny could get dizzy.", tags={"town"}),
    "dock": Place("dock", "the river dock", "The river dock smelled of rope and rain.", "The water slapped the pilings.", "A bulletin board was nailed to the lamp post.", "It winked like a lantern teaching itself to sing.", "The dock was so long a catfish could take a Sunday walk.", tags={"town", "water"}),
}

BULLETINS = {
    "lost_lamb": Bulletin("lost_lamb", "the lost lamb notice", "lost_item", "a lamb with a blue ribbon", "it had wandered off at dawn", "lost_item", tags={"notice", "lost"}),
    "lost_hat": Bulletin("lost_hat", "the lost hat notice", "lost_item", "a red hat full of seeds", "the hat blew away in a gust", "lost_item", tags={"notice", "lost"}),
    "lost_violin": Bulletin("lost_violin", "the lost violin notice", "lost_item", "a violin with a silver crack", "music missed it terribly", "lost_item", tags={"notice", "lost"}),
}

CHARMS = {
    "glimmer": Charm("glimmer", "a glimmer charm", "touching the corner", "letters floated free like dandelion fluff", 1, tags={"magic"}),
    "mirror": Charm("mirror", "a mirror charm", "holding it to the board", "the clue reflected as plain words", 2, tags={"magic"}),
    "bell": Charm("bell", "a bell charm", "ringing it once", "the board answered with a bright chiming", 1, tags={"magic"}),
}

GIRL_NAMES = ["Mina", "June", "Ivy", "Nora", "Ada"]
BOY_NAMES = ["Otis", "Bram", "Eli", "Wade", "Pip"]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.bulletin and args.bulletin not in BULLETINS:
        raise StoryError("Unknown bulletin.")
    if args.charm and args.charm not in CHARMS:
        raise StoryError("Unknown charm.")
    combos = [c for c in valid_combos()
              if args.place is None or c[0] == args.place
              and args.bulletin is None or c[1] == args.bulletin
              and args.charm is None or c[2] == args.charm]
    # fix precedence with explicit filtering
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.bulletin is None or c[1] == args.bulletin)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, bulletin, charm = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = "girl" if child_type == "boy" else "boy"
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    return StoryParams(place=place, bulletin=bulletin, charm=charm, child_name=child_name, child_type=child_type, helper_name=helper_name, helper_type=helper_type)


def tell(params: StoryParams) -> World:
    world = World()
    child = world.add(Entity(id=params.child_name, kind="character", type=params.child_type, role="child"))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, role="helper"))
    park = world.add(Entity(id="park", kind="place", type="place", label=PLACES[params.place].label))
    note = world.add(Entity(id="bulletin", kind="thing", type="bulletin", label=BULLETINS[params.bulletin].label))
    charm = world.add(Entity(id="charm", kind="thing", type="charm", label=CHARMS[params.charm].label))
    lost = world.add(Entity(id="lost", kind="thing", type="lost_item", label=BULLETINS[params.bulletin].clue))
    child.memes["curiosity"] = 2
    child.memes["kindness"] = 1
    helper.memes["curiosity"] = 1
    helper.memes["kindness"] = 2
    world.say(f"{child.id} came to {PLACES[params.place].label} with eyes wide as a wagon wheel.")
    world.say(f"There, on a bulletin board, hung {BULLETINS[params.bulletin].label}. {PLACES[params.place].setting_line}")
    world.say(f"{PLACES[params.place].weather_line} {PLACES[params.place].bulletin_line} {PLACES[params.place].magic_glow}")

    world.para()
    world.say(f"{child.id}'s curiosity tugged harder than a kite in a storm. {child.id} leaned close and read the clue: {BULLETINS[params.bulletin].clue}.")
    world.say(f"{helper.id} watched with a kind grin, because {helper.id} liked a mystery but liked helping even more.")
    note.meters["noticed"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(f"Then the charm came out. {child.id} tried {CHARMS[params.charm].method}, and the words answered like they had been waiting for a friend.")
    if child.meme("kindness") >= KIND_MIN:
        world.say(f"Instead of taking the clue for themselves, {child.id} chose kindness and shared it with the whole square.")
    world.get("lost").meters["found"] += 1
    note.meters["torn"] += 1
    propagate(world, narrate=False)

    world.para()
    world.say(f"At last, the bulletin stopped being a secret and became a promise kept. {CHARMS[params.charm].reveal}.")
    world.say(f"{BULLETINS[params.bulletin].promise.capitalize()}, and {helper.id} helped carry the news to where it belonged.")
    world.say(f"{PLACES[params.place].tall_tale_line} By sundown, the lost thing was home, and the bulletin board stood proud as a barn on parade.")

    world.facts.update(place=PLACES[params.place], bulletin=BULLETINS[params.bulletin], charm=CHARMS[params.charm], child=child, helper=helper, lost=lost, outcome="reunited")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale style story that includes the word "bulletin" and shows curiosity leading to kindness, with a little magic helping solve a problem.',
        f"Tell a child-friendly tall tale about {f['child'].id} reading a bulletin, being curious, and using {f['charm'].label} to help somebody instead of causing trouble.",
        f'Write a short story where a bulletin board holds a clue, magic reveals it, and kindness makes the ending warm and happy.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, bulletin, charm = f["child"], f["helper"], f["bulletin"], f["charm"]
    return [
        QAItem(question="What did the child notice?", answer=f"{child.id} noticed a bulletin on the board, and the clue on it made {child.pronoun()} curious right away. That curiosity pulled {child.pronoun('object')} close enough to read the message."),
        QAItem(question="How did kindness matter in the story?", answer=f"{child.id} did not keep the clue for {child.pronoun('possessive')}self. {child.pronoun().capitalize()} shared it, and that kind choice let the whole town help instead of turning the mystery into a selfish trick."),
        QAItem(question="What did the magic do?", answer=f"The magic made the clue show itself clearly when {charm.method}. It was a gentle kind of magic, used to help people understand the bulletin rather than to cause a fuss."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a bulletin?", answer="A bulletin is a posted notice that shares news, a warning, or a message for people to read. Towns often pin them on boards where many eyes can find them."),
        QAItem(question="What does curiosity do?", answer="Curiosity makes someone want to look, ask, and learn. It can lead to good discoveries when it is matched with patience and kindness."),
        QAItem(question="Why can magic be useful in a story?", answer="Magic can reveal hidden clues, solve puzzles, or help people understand something they could not see at first. In a tall tale, it often makes the problem feel larger than life and the ending feel marvelous."),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    parts.extend(sample.prompts)
    parts.append("")
    parts.append("== story qa ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(x[0] for x in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="square", bulletin="lost_lamb", charm="glimmer", child_name="Mina", child_type="girl", helper_name="Otis", helper_type="boy"),
    StoryParams(place="market", bulletin="lost_hat", charm="mirror", child_name="Bram", child_type="boy", helper_name="June", helper_type="girl"),
    StoryParams(place="dock", bulletin="lost_violin", charm="bell", child_name="Ivy", child_type="girl", helper_name="Wade", helper_type="boy"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.bulletin not in BULLETINS or params.charm not in CHARMS:
        raise StoryError("Invalid story parameters.")
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
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP.")
        print("only python:", sorted(py - cl))
        print("only asp:", sorted(cl - py))
        return 1
    try:
        sample = generate(CURATED[0])
        _ = sample.story
        _ = sample.to_json()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: ASP parity holds for {len(py)} combos; smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world with a bulletin board, curiosity, kindness, and a little magic.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--bulletin", choices=sorted(BULLETINS))
    ap.add_argument("--charm", choices=sorted(CHARMS))
    ap.add_argument("--child-name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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


def asp_valid() -> list[tuple]:
    return asp_valid_combos()


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.place and args.place not in PLACES:
        raise StoryError("Unknown place.")
    if args.bulletin and args.bulletin not in BULLETINS:
        raise StoryError("Unknown bulletin.")
    if args.charm and args.charm not in CHARMS:
        raise StoryError("Unknown charm.")
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.bulletin is None or c[1] == args.bulletin)
              and (args.charm is None or c[2] == args.charm)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, bulletin, charm = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    child_name = args.child_name or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    helper_type = args.helper_type or ("boy" if child_type == "girl" else "girl")
    helper_name = args.helper_name or rng.choice(GIRL_NAMES if helper_type == "girl" else BOY_NAMES)
    return StoryParams(place=place, bulletin=bulletin, charm=charm, child_name=child_name, child_type=child_type, helper_name=helper_name, helper_type=helper_type, seed=None)


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid()
        print(f"{len(combos)} compatible combos:\n")
        for combo in combos:
            print(combo)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
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
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
